# -*- coding: utf-8 -*-
"""
策略执行器
"""

from typing import Dict, Any, Callable
from datetime import timedelta
import logging
import traceback

from simtradelab.ptrade.context import Context
from simtradelab.ptrade.object import clear_daily_cache, Data
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.backtest.stats_collector import StatsCollector


class StrategyExecutor:
    """策略每日执行器"""

    def __init__(
        self,
        strategy_namespace: Dict[str, Any],
        context: Context,
        stats_collector: StatsCollector,
        log: logging.Logger
    ):
        self.strategy_namespace = strategy_namespace
        self.context = context
        self.stats_collector = stats_collector
        self.log = log

    def initialize(self):
        """调用策略初始化"""
        self._set_lifecycle_phase(LifecyclePhase.INITIALIZE)
        self.strategy_namespace['initialize'](self.context)

    def run_daily_loop(self, date_range) -> bool:
        """执行每日回测循环

        Args:
            date_range: 交易日序列

        Returns:
            是否成功完成所有交易日
        """
        for current_date in date_range:
            success = self._run_single_day(current_date)
            if not success:
                return False

        return True

    def _run_single_day(self, current_date) -> bool:
        """执行单日回测

        Args:
            current_date: 当前交易日

        Returns:
            是否成功执行
        """
        # 更新日期上下文
        self.context.current_dt = current_date
        self.context.previous_date = (current_date - timedelta(days=1)).date()
        self.context.blotter.current_dt = current_date

        # 清理全局缓存
        clear_daily_cache()

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
        phase: LifecyclePhase,
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
        try:
            self._set_lifecycle_phase(phase)
            self.strategy_namespace[func_name](self.context, data)
            return True
        except Exception as e:
            self.log.error(f"{func_name}执行失败: {e}")
            traceback.print_exc()
            return allow_fail

    def _set_lifecycle_phase(self, phase: LifecyclePhase):
        """设置生命周期阶段"""
        if self.context._lifecycle_controller:
            self.context._lifecycle_controller.set_phase(phase)
