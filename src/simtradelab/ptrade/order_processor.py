# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
统一订单处理器

整合订单创建、验证、执行的完整流程
"""


from __future__ import annotations

from typing import Optional
import uuid
import pandas as pd

from .config_manager import config
from .object import Order


class OrderProcessor:
    """订单处理器

    统一管理订单的完整生命周期：
    1. 价格获取
    2. 涨跌停检查
    3. 订单创建
    4. 买卖执行
    """

    def __init__(self, context, data_context, get_stock_date_index_func, log):
        """初始化订单处理器

        Args:
            context: 上下文对象
            data_context: 数据上下文对象
            get_stock_date_index_func: 获取股票日期索引的函数
            log: 日志对象
        """
        self.context = context
        self.data_context = data_context
        self.get_stock_date_index = get_stock_date_index_func
        self.log = log

    def get_execution_price(self, stock: str, limit_price: Optional[float] = None, is_buy: bool = True) -> Optional[float]:
        """获取交易执行价格（含滑点）

        Args:
            stock: 股票代码
            limit_price: 限价
            is_buy: 是否买入（True买入向上滑点，False卖出向下滑点）

        Returns:
            执行价格，失败返回None
        """
        if limit_price is not None:
            base_price = limit_price
        else:
            if stock not in self.data_context.stock_data_dict:
                return None

            stock_df = self.data_context.stock_data_dict[stock]
            if not isinstance(stock_df, pd.DataFrame):
                return None

            try:
                date_dict, _ = self.get_stock_date_index(stock)
                idx = date_dict.get(self.context.current_dt)
                if idx is None:
                    idx = stock_df.index.get_loc(self.context.current_dt)
                price = stock_df.iloc[idx]['close']

                # 转换为标量值
                if isinstance(price, pd.Series):
                    price = price.item()

                base_price = float(price)

                if pd.isna(base_price) or base_price <= 0:
                    return None
            except Exception:
                return None

        # 获取滑点配置
        slippage = getattr(self.context, 'slippage', config.trading.slippage)
        fixed_slippage = getattr(self.context, 'fixed_slippage', config.trading.fixed_slippage)

        # 计算滑点金额
        if slippage > 0:
            # 比例滑点：滑点金额 = 委托价格 * slippage / 2
            slippage_amount = base_price * slippage / 2
        elif fixed_slippage > 0:
            # 固定滑点：滑点金额 = fixed_slippage / 2（单位：元）
            slippage_amount = fixed_slippage / 2
        else:
            # 无滑点
            slippage_amount = 0

        # 最终成交价格 = 委托价格 ± 滑点金额
        if is_buy:
            # 买入向上滑点
            final_price = base_price + slippage_amount
        else:
            # 卖出向下滑点
            final_price = base_price - slippage_amount

        return final_price

    def check_limit_status(self, stock: str, delta: int, limit_status: int) -> bool:
        """检查涨跌停限制

        Args:
            stock: 股票代码
            delta: 交易数量变化（正数买入，负数卖出）
            limit_status: 涨跌停状态（1涨停，-1跌停，0正常）

        Returns:
            是否可交易
        """
        if delta > 0 and limit_status == 1:
            self.log.warning("【订单失败】{} | 原因: 涨停买不进".format(stock))
            return False
        elif delta < 0 and limit_status == -1:
            self.log.warning("【订单失败】{} | 原因: 跌停卖不出".format(stock))
            return False
        return True

    def create_order(self, stock: str, amount: int, price: float) -> tuple[str, object]:
        """创建订单对象

        Args:
            stock: 股票代码
            amount: 交易数量
            price: 交易价格

        Returns:
            (order_id, order对象)
        """
        order_id = str(uuid.uuid4()).replace('-', '')
        order = Order(
            id=order_id,
            symbol=stock,
            amount=amount,
            dt=self.context.current_dt,
            limit=price
        )
        return order_id, order

    def calculate_commission(self, amount: int, price: float, is_sell: bool = False) -> float:
        """计算手续费

        Args:
            amount: 交易数量
            price: 交易价格
            is_sell: 是否卖出

        Returns:
            手续费总额
        """
        commission_ratio = getattr(self.context, 'commission_ratio', config.trading.commission_ratio)
        min_commission = getattr(self.context, 'min_commission', config.trading.min_commission)

        # 如果手续费率为0，则完全不收手续费
        if commission_ratio == 0:
            return 0

        value = amount * price
        # 佣金费
        broker_fee = max(value * commission_ratio, min_commission)
        # 经手费率：万分之0.487
        transfer_fee = value * 0.0000487

        commission = broker_fee + transfer_fee

        # 印花税(仅卖出时收取)
        if is_sell:
            tax_rate = getattr(self.context, 'tax_rate', 0.001)
            tax = value * tax_rate
            commission += tax

        return commission

    def execute_buy(self, stock: str, amount: int, price: float) -> bool:
        """执行买入操作

        Args:
            stock: 股票代码
            amount: 买入数量
            price: 买入价格

        Returns:
            是否成功
        """
        cost = amount * price
        commission = self.calculate_commission(amount, price, is_sell=False)
        total_cost = cost + commission

        if total_cost > self.context.portfolio._cash:
            self.log.warning("【买入失败】{} | 原因: 现金不足 (需要{:.2f}, 可用{:.2f})".format(
                stock, total_cost, self.context.portfolio._cash))
            return False

        self.context.portfolio._cash -= total_cost

        # 记录手续费
        if not hasattr(self.context, 'total_commission'):
            self.context.total_commission = 0
        self.context.total_commission += commission

        # 建仓/加仓（含批次追踪）
        self.context.portfolio.add_position(stock, amount, price, self.context.current_dt)

        return True

    def execute_sell(self, stock: str, amount: int, price: float) -> bool:
        """执行卖出操作（FIFO：先进先出）

        Args:
            stock: 股票代码
            amount: 卖出数量（正数）
            price: 卖出价格

        Returns:
            是否成功
        """
        if stock not in self.context.portfolio.positions:
            self.log.warning("【卖出失败】{} | 原因: 无持仓".format(stock))
            return False

        position = self.context.portfolio.positions[stock]

        if position.amount < amount:
            self.log.warning("【卖出失败】{} | 原因: 持仓不足 (持有{}, 尝试卖出{})".format(
                stock, position.amount, amount))
            return False

        # 计算手续费
        revenue = amount * price
        commission = self.calculate_commission(amount, price, is_sell=True)

        # 减仓/清仓（含FIFO分红税调整）
        tax_adjustment = self.context.portfolio.remove_position(stock, amount, self.context.current_dt)

        # 净收入
        net_revenue = revenue - commission - tax_adjustment

        # 记录手续费
        if not hasattr(self.context, 'total_commission'):
            self.context.total_commission = 0
        self.context.total_commission += commission

        # 更新价格（仅当position仍存在时）
        if stock in self.context.portfolio.positions:
            position = self.context.portfolio.positions[stock]
            position.last_sale_price = price
            if position.amount > 0:
                position.market_value = position.amount * price

        # 入账
        self.context.portfolio._cash += net_revenue

        # 日志
        if tax_adjustment > 0:
            self.log.info("📊分红税 | {} | 补税{:.2f}元".format(stock, tax_adjustment))
        elif tax_adjustment < 0:
            self.log.info("📊分红税 | {} | 退税{:.2f}元".format(stock, -tax_adjustment))

        return True

    def process_order(self, stock: str, target_amount: int, limit_price: Optional[float] = None,
                     limit_status: int = 0) -> bool:
        """处理订单的完整流程

        Args:
            stock: 股票代码
            target_amount: 目标数量
            limit_price: 限价
            limit_status: 涨跌停状态

        Returns:
            是否成功
        """
        # 1. 获取执行价格
        price = self.get_execution_price(stock, limit_price)
        if price is None:
            self.log.warning("【订单失败】{} | 原因: 无法获取价格".format(stock))
            return False

        # 2. 计算交易数量
        current_amount = 0
        if stock in self.context.portfolio.positions:
            current_amount = self.context.portfolio.positions[stock].amount

        delta = target_amount - current_amount

        if delta == 0:
            return True  # 无需交易

        # 3. 检查涨跌停
        if not self.check_limit_status(stock, delta, limit_status):
            return False

        # 4. 执行交易
        if delta > 0:
            return self.execute_buy(stock, delta, price)
        else:
            return self.execute_sell(stock, abs(delta), price)
