# -*- coding: utf-8 -*-
"""
PTrade 策略执行框架

提供完整的策略执行环境，整合生命周期控制、API验证和Context管理
"""

import logging
import traceback
from typing import Any, Callable, Dict, Optional

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
        self._strategy_functions: Dict[str, Callable[..., Any]] = {}
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
        if not self._strategy_functions.get("initialize"):
            raise StrategyExecutionError("Strategy must have an initialize function")

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
        from simtradelab.ptrade.object import clear_daily_cache, Data

        for current_date in date_range:
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
        from simtradelab.ptrade.lifecycle_controller import LifecyclePhase

        # before_trading_start
        if not self._safe_call('before_trading_start', LifecyclePhase.BEFORE_TRADING_START, data):
            return False

        # 处理分红事件
        self._process_dividend_events(data.current_date)

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
        if func_name not in self._strategy_functions:
            return True  # 函数不存在，跳过

        try:
            self.lifecycle_controller.set_phase(phase)
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
        """
        try:
            # 遍历所有持仓股票
            for stock_code, position in self.context.portfolio.positions.items():
                if position.amount <= 0:
                    continue

                # 获取该股票的除权数据
                exrights_data = self.api.get_stock_exrights(stock_code)
                if exrights_data is None or len(exrights_data) == 0:
                    continue

                # 检查是否有分红事件
                date_str = current_date.strftime('%Y%m%d')
                has_dividend = date_str in exrights_data.index.astype(str)

                if has_dividend:
                    dividend_amount = self._calculate_dividend(stock_code, position.amount, current_date)
                    if dividend_amount > 0:
                        # 添加分红到现金
                        old_cash = self.context.portfolio._cash
                        self.context.portfolio._cash += dividend_amount
                        self.context.portfolio._invalidate_cache()
                        self.log.info(f"💰分红 | {stock_code} | {position.amount}股 | 分红金额: {dividend_amount:.2f}元 | 现金: {old_cash:.2f} → {self.context.portfolio._cash:.2f}")

        except Exception as e:
            self.log.warning(f"分红处理失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_dividend(self, stock_code, shares, current_date):
        """计算分红金额
        
        Args:
            stock_code: 股票代码
            shares: 持股数量
            current_date: 分红日期
        
        Returns:
            分红金额
        """
        try:
            # 获取除权数据
            exrights_data = self.api.get_stock_exrights(stock_code)
            if exrights_data is None or len(exrights_data) == 0:
                return 0.0
            
            # 查找当前日期的分红记录
            date_str = current_date.strftime('%Y%m%d')
            current_records = exrights_data[exrights_data.index.astype(str) == date_str]
            if len(current_records) == 0:
                return 0.0
            
            # 获取当前记录的bonus_ps值（当次税前分红）
            current_bonus = current_records['bonus_ps'].iloc[0]

            # bonus_ps直接代表当次分红每股金额（税前）
            # 应用20%红利税
            dividend_tax_rate = 0.20
            dividend_per_share_after_tax = current_bonus * (1 - dividend_tax_rate)
            total_dividend = dividend_per_share_after_tax * shares

            return total_dividend if total_dividend > 0 else 0.0
            
        except Exception as e:
            self.log.warning(f"计算{stock_code}分红失败: {e}")
            return 0.0

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
