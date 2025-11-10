# -*- coding: utf-8 -*-
"""
交易执行辅助函数
"""

import pandas as pd
import uuid
from typing import Optional, Tuple


def get_execution_price(stock: str, context, data_context, get_stock_date_index_func, limit_price: Optional[float] = None) -> Optional[float]:
    """获取交易执行价格

    Args:
        stock: 股票代码
        context: 上下文对象
        data_context: 数据上下文对象
        get_stock_date_index_func: 获取股票日期索引的函数
        limit_price: 限价

    Returns:
        执行价格，失败返回None
    """
    if limit_price is not None:
        return limit_price

    if stock not in data_context.stock_data_dict:
        return None

    stock_df = data_context.stock_data_dict[stock]
    if not isinstance(stock_df, pd.DataFrame):
        return None

    try:
        date_dict, _ = get_stock_date_index_func(stock)
        idx = date_dict.get(context.current_dt) or stock_df.index.get_loc(context.current_dt)
        price = stock_df.iloc[idx]['close']

        # 转换为标量值
        if isinstance(price, pd.Series):
            price = price.item()

        price = float(price)

        if pd.isna(price) or price <= 0:
            return None

        return price
    except:
        return None


def check_order_validity(stock: str, delta: int, limit_status: int, log) -> bool:
    """检查订单有效性（涨跌停限制）

    Args:
        stock: 股票代码
        delta: 交易数量变化（正数买入，负数卖出）
        limit_status: 涨跌停状态（1涨停，-1跌停，0正常）
        log: 日志对象

    Returns:
        是否有效
    """
    if delta > 0 and limit_status == 1:
        log.warning(f"【订单失败】{stock} | 原因: 涨停买不进")
        return False
    elif delta < 0 and limit_status == -1:
        log.warning(f"【订单失败】{stock} | 原因: 跌停卖不出")
        return False
    return True


def create_order(stock: str, amount: int, price: float, context) -> Tuple[str, object]:
    """创建订单对象

    Args:
        stock: 股票代码
        amount: 交易数量
        price: 交易价格
        context: 上下文对象

    Returns:
        (order_id, order对象)
    """
    from simtradelab.ptrade.object import Order

    order_id = str(uuid.uuid4()).replace('-', '')
    order = Order(
        order_id=order_id,
        stock=stock,
        amount=amount,
        created_dt=context.current_dt,
        price=price
    )
    return order_id, order


def execute_buy(stock: str, amount: int, price: float, context, log) -> bool:
    """执行买入操作

    Args:
        stock: 股票代码
        amount: 买入数量
        price: 买入价格
        context: 上下文对象
        log: 日志对象

    Returns:
        是否成功
    """
    from simtradelab.ptrade.object import Position

    cost = amount * price
    if cost > context.portfolio._cash:
        log.warning(f"【买入失败】{stock} | 原因: 现金不足 (需要{cost:.2f}, 可用{context.portfolio._cash:.2f})")
        return False

    context.portfolio._cash -= cost

    if stock not in context.portfolio.positions:
        context.portfolio.positions[stock] = Position(stock, amount, price)
    else:
        old_pos = context.portfolio.positions[stock]
        new_amount = old_pos.amount + amount
        new_cost = (old_pos.amount * old_pos.cost_basis + amount * price) / new_amount
        context.portfolio.positions[stock] = Position(stock, new_amount, new_cost)

    context.portfolio._invalidate_cache()
    return True


def execute_sell(stock: str, amount: int, price: float, context, log) -> bool:
    """执行卖出操作

    Args:
        stock: 股票代码
        amount: 卖出数量（正数）
        price: 卖出价格
        context: 上下文对象
        log: 日志对象

    Returns:
        是否成功
    """
    if stock not in context.portfolio.positions:
        log.warning(f"【卖出失败】{stock} | 原因: 无持仓")
        return False

    position = context.portfolio.positions[stock]

    if position.amount < amount:
        log.warning(f"【卖出失败】{stock} | 原因: 持仓不足 (持有{position.amount}, 尝试卖出{amount})")
        return False

    # 更新持仓
    position.last_sale_price = price

    if position.amount == amount:
        # 全部卖出
        context.portfolio._cash += amount * price
        del context.portfolio.positions[stock]
    else:
        # 部分卖出
        context.portfolio._cash += amount * price
        position.amount -= amount
        position.market_value = position.amount * price

    context.portfolio._invalidate_cache()
    return True
