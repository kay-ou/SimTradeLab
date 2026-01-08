# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
PTrade 策略执行框架

提供完整的策略执行环境，整合生命周期控制、API验证和Context管理
"""


from __future__ import annotations

import logging
import traceback
from typing import Any, Callable, Optional

from .context import Context


class StrategyExecutionError(Exception):
    """策略执行错误"""
    pass


class StrategyExecutionEngine:
    """PTrade策略执行引擎

    功能：
    1. 管理策略的完整生命周期
    2. 提供PTrade API接口
    3. 集成生命周期控制和API验证
    4. 支持多种运行模式（研究/回测/交易）
    """

    def __init__(
        self,
        context: Context,
        api: Any,
        stats_collector: Any,
        g: Any,
        log: logging.Logger,
    ):
        """
        初始化策略执行引擎

        Args:
            context: PTrade Context对象
            api: PtradeAPI对象
            stats_collector: 统计收集器
            g: Global对象
            log: 日志对象
        """
        # 核心组件（外部注入）
        self.context = context
        self.api = api
        self.stats_collector = stats_collector
        self.g = g
        self.log = log

        # 获取生命周期控制器
        if self.context._lifecycle_controller is None:
            raise ValueError("Context lifecycle controller is not initialized")
        self.lifecycle_controller = self.context._lifecycle_controller

        # 策略相关
        self._strategy_functions: dict[str, Callable[..., Any]] = {}
        self._strategy_name: Optional[str] = None
        self._is_running = False
    # ==========================================
    # 策略注册接口
    # ==========================================

    def load_strategy_from_file(self, strategy_path: str) -> None:
        """从文件加载策略并自动注册所有生命周期函数

        Args:
            strategy_path: 策略文件路径
        """
        # 读取策略代码
        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy_code = f.read()

        # 构建命名空间
        strategy_namespace = {
            '__name__': '__main__',
            '__file__': strategy_path,
            'g': self.g,
            'log': self.log,
            'context': self.context,
        }

        # 注入API方法
        for attr_name in dir(self.api):
            if not attr_name.startswith('_'):
                attr = getattr(self.api, attr_name)
                if callable(attr) or attr_name == 'FUNDAMENTAL_TABLES':
                    strategy_namespace[attr_name] = attr

        # 执行策略代码
        exec(strategy_code, strategy_namespace)

        # 自动注册所有生命周期函数
        if 'initialize' in strategy_namespace:
            self.register_initialize(strategy_namespace['initialize'])
        if 'handle_data' in strategy_namespace:
            self.register_handle_data(strategy_namespace['handle_data'])
        if 'before_trading_start' in strategy_namespace:
            self.register_before_trading_start(strategy_namespace['before_trading_start'])
        if 'after_trading_end' in strategy_namespace:
            self.register_after_trading_end(strategy_namespace['after_trading_end'])
        if 'tick_data' in strategy_namespace:
            self.register_tick_data(strategy_namespace['tick_data'])
        if 'on_order_response' in strategy_namespace:
            self.register_on_order_response(strategy_namespace['on_order_response'])
        if 'on_trade_response' in strategy_namespace:
            self.register_on_trade_response(strategy_namespace['on_trade_response'])

    def set_strategy_name(self, strategy_name: str) -> None:
        """设置策略名称

        Args:
            strategy_name: 策略名称
        """
        self._strategy_name = strategy_name

    def register_initialize(self, func: Callable[[Context], None]) -> None:
        """注册initialize函数"""
        self._strategy_functions["initialize"] = func
        self.context.register_initialize(func)

    def register_handle_data(self, func: Callable[[Context, Any], None]) -> None:
        """注册handle_data函数"""
        self._strategy_functions["handle_data"] = func
        self.context.register_handle_data(func)

    def register_before_trading_start(
        self, func: Callable[[Context, Any], None]
    ) -> None:
        """注册before_trading_start函数"""
        self._strategy_functions["before_trading_start"] = func
        self.context.register_before_trading_start(func)

    def register_after_trading_end(
        self, func: Callable[[Context, Any], None]
    ) -> None:
        """注册after_trading_end函数"""
        self._strategy_functions["after_trading_end"] = func
        self.context.register_after_trading_end(func)

    def register_tick_data(self, func: Callable[[Context, Any], None]) -> None:
        """注册tick_data函数"""
        self._strategy_functions["tick_data"] = func
        self.context.register_tick_data(func)

    def register_on_order_response(
        self, func: Callable[[Context, Any], None]
    ) -> None:
        """注册on_order_response函数"""
        self._strategy_functions["on_order_response"] = func
        self.context.register_on_order_response(func)

    def register_on_trade_response(
        self, func: Callable[[Context, Any], None]
    ) -> None:
        """注册on_trade_response函数"""
        self._strategy_functions["on_trade_response"] = func
        self.context.register_on_trade_response(func)

    # ==========================================
    # PTrade API 代理接口
    # ==========================================

    def __getattr__(self, name: str) -> Any:
        """代理PTrade API调用"""
        if hasattr(self.api, name):
            return getattr(self.api, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    # ==========================================
    # 策略执行接口
    # ==========================================

    def run_backtest(self, date_range) -> bool:
        """运行回测策略

        Args:
            date_range: 交易日序列

        Returns:
            bool: 是否成功完成
        """
        # 验证必选函数
        if not self._strategy_functions.get("initialize"):
            raise StrategyExecutionError("Strategy must have an initialize function")
        if not self._strategy_functions.get("handle_data"):
            raise StrategyExecutionError("Strategy must have a handle_data function")

        self._is_running = True

        try:
            self.log.info(f"Starting strategy execution: {self._strategy_name}")

            # 1. 执行初始化
            self._execute_initialize()

            # 2. 执行每日循环
            success = self._run_daily_loop(date_range)

            if success:
                self.log.info("Strategy execution completed successfully")

            return success

        except Exception as e:
            self.log.error(f"Strategy execution failed: {e}")
            traceback.print_exc()
            return False

        finally:
            self._is_running = False

    def _execute_initialize(self) -> None:
        """执行初始化阶段"""
        self.log.info("Executing initialize phase")
        self.context.execute_initialize()

    def _run_daily_loop(self, date_range) -> bool:
        """执行每日回测循环

        Args:
            date_range: 交易日序列

        Returns:
            是否成功完成所有交易日
        """
        from datetime import timedelta
        from simtradelab.ptrade.object import Data
        from simtradelab.ptrade.cache_manager import cache_manager

        for current_date in date_range:
            # 更新日期上下文
            self.context.current_dt = current_date
            self.context.blotter.current_dt = current_date

            # 使用API获取真正的前一交易日（而非简单减1天）
            prev_trade_day = self.api.get_trading_day(-1)
            if prev_trade_day:
                self.context.previous_date = prev_trade_day
            else:
                # 回退方案：简单减1天
                self.context.previous_date = (current_date - timedelta(days=1)).date()

            # 清理全局缓存
            cache_manager.clear_daily_cache(current_date)

            # 记录交易前状态
            prev_portfolio_value = self.context.portfolio.portfolio_value
            prev_cash = self.context.portfolio._cash

            # 收集交易前统计
            self.stats_collector.collect_pre_trading(self.context, current_date)

            # 构造data对象
            data = Data(current_date, self.context.portfolio._bt_ctx)

            # 执行策略生命周期
            if not self._execute_lifecycle(data):
                return False

            # 处理分红事件（在生命周期执行完、订单成交后）
            self._process_dividend_events(current_date)

            # 收集交易金额
            current_cash = self.context.portfolio._cash
            self.stats_collector.collect_trading_amounts(prev_cash, current_cash)

            # 收集交易后统计
            self.stats_collector.collect_post_trading(self.context, prev_portfolio_value)

        return True

    def _execute_lifecycle(self, data) -> bool:
        """执行策略生命周期方法

        Args:
            data: Data对象

        Returns:
            是否成功执行
        """
        from simtradelab.ptrade.lifecycle_controller import LifecyclePhase

        # before_trading_start
        if not self._safe_call('before_trading_start', LifecyclePhase.BEFORE_TRADING_START, data):
            return False

        # handle_data
        if not self._safe_call('handle_data', LifecyclePhase.HANDLE_DATA, data):
            return False

        # after_trading_end（允许失败）
        self._safe_call('after_trading_end', LifecyclePhase.AFTER_TRADING_END, data, allow_fail=True)

        return True

    def _safe_call(
        self,
        func_name: str,
        phase,
        data,
        allow_fail: bool = False
    ) -> bool:
        """安全调用策略方法

        Args:
            func_name: 函数名
            phase: 生命周期阶段
            data: Data对象
            allow_fail: 是否允许失败

        Returns:
            是否成功执行
        """
        # 始终设置生命周期阶段，即使函数不存在
        try:
            self.lifecycle_controller.set_phase(phase)
        except Exception as e:
            self.log.error(f"设置生命周期阶段 {phase} 失败: {e}")
            return False

        # 如果函数不存在，阶段已设置，直接返回成功
        if func_name not in self._strategy_functions:
            return True

        # 执行策略函数
        try:
            self._strategy_functions[func_name](self.context, data)
            return True
        except Exception as e:
            self.log.error(f"{func_name}执行失败: {e}")
            traceback.print_exc()
            return allow_fail

    def _process_dividend_events(self, current_date):
        """处理分红事件

        Args:
            current_date: 当前交易日

        分红处理逻辑：
        1. 分红到账时全额到账（不扣税）
        2. 记录每批次的分红金额
        3. 卖出时根据持股时间（FIFO）计算并扣除分红税
        """
        try:
            date_str = current_date.strftime('%Y%m%d')

            # 遍历所有持仓股票
            for stock_code, position in self.context.portfolio.positions.items():
                if position.amount <= 0:
                    continue

                # 从缓存中查找分红
                if stock_code not in self.api.data_context.dividend_cache:
                    continue

                stock_dividends = self.api.data_context.dividend_cache[stock_code]
                if date_str not in stock_dividends:
                    continue

                # 获取税前分红金额（每股）
                dividend_per_share_before_tax = stock_dividends[date_str]

                # 预扣税率20%（保守估计）
                pre_tax_rate = 0.20
                dividend_per_share_after_tax = dividend_per_share_before_tax * (1 - pre_tax_rate)
                total_dividend_after_tax = dividend_per_share_after_tax * position.amount

                if total_dividend_after_tax > 0:
                    # 税后金额到账
                    old_cash = self.context.portfolio._cash
                    self.context.portfolio._cash += total_dividend_after_tax
                    self.context.portfolio._invalidate_cache()

                    # 记录分红到批次（用于卖出时税务调整）
                    self.context.portfolio.add_dividend(stock_code, dividend_per_share_before_tax)

                    self.log.info(
                        f"💰分红 | {stock_code} | {position.amount}股 | "
                        f"税前{dividend_per_share_before_tax:.4f}元/股 | 预扣税率{pre_tax_rate:.0%} | "
                        f"到账{total_dividend_after_tax:.2f}元 | "
                        f"现金: {old_cash:.2f} → {self.context.portfolio._cash:.2f}"
                    )

        except Exception as e:
            self.log.warning(f"分红处理失败: {e}")
            import traceback
            traceback.print_exc()

    # ==========================================
    # 重置和清理接口
    # ==========================================

    def reset_strategy(self) -> None:
        """重置策略状态"""
        self.log.info("Resetting strategy state")

        self._strategy_functions.clear()
        self._strategy_name = None
        self._is_running = False

        # 重置Context
        self.context.reset_for_new_strategy()
