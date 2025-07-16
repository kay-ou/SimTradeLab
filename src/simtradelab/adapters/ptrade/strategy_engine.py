# -*- coding: utf-8 -*-
"""
PTrade 策略执行框架

提供完整的策略执行环境，整合生命周期控制、API验证和Context管理
"""

import logging
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Union

from ...core.event_bus import EventBus
from .api_validator import APIValidator
from .context import (
    PTradeContext,
    PTradeMode,
    create_backtest_context,
    create_research_context,
    create_trading_context,
)
from .lifecycle_controller import LifecycleController
from .models import SecurityUnitData
from .routers import BacktestAPIRouter, ResearchAPIRouter, TradingAPIRouter


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
        mode: PTradeMode = PTradeMode.BACKTEST,
        capital_base: float = 1000000,
        commission_rate: float = 0.0003,
        slippage_rate: float = 0.0,
    ):
        """
        初始化策略执行引擎

        Args:
            mode: 运行模式
            capital_base: 起始资金
            commission_rate: 佣金费率
            slippage_rate: 滑点率
        """
        self.mode = mode
        self.capital_base = capital_base
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

        # 核心组件
        self.event_bus = EventBus()
        self.context: PTradeContext  # 将在_initialize_components中设置
        self.api_router: Optional[Any] = None
        self.lifecycle_controller: LifecycleController  # 将在_initialize_components中设置
        self.api_validator: APIValidator  # 将在_initialize_components中设置

        # 策略相关
        self._strategy_functions: Dict[str, Callable[..., Any]] = {}
        self._strategy_name: Optional[str] = None
        self._is_running = False
        self._current_data: Optional[Dict[str, SecurityUnitData]] = None

        # 日志
        self._logger = logging.getLogger(self.__class__.__name__)

        # 初始化组件
        self._initialize_components()

    def _initialize_components(self) -> None:
        """初始化核心组件"""
        # 创建Context
        if self.mode == PTradeMode.RESEARCH:
            self.context = create_research_context(self.capital_base)
        elif self.mode == PTradeMode.BACKTEST:
            self.context = create_backtest_context(
                self.capital_base, self.commission_rate, self.slippage_rate
            )
        elif self.mode == PTradeMode.TRADING:
            self.context = create_trading_context(self.capital_base)
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

        self.plugin_manager = self.context.plugin_manager
        if self.mode == PTradeMode.RESEARCH:
            self.context = create_research_context(self.capital_base)
        elif self.mode == PTradeMode.BACKTEST:
            self.context = create_backtest_context(
                self.capital_base, self.commission_rate, self.slippage_rate
            )
        elif self.mode == PTradeMode.TRADING:
            self.context = create_trading_context(self.capital_base)
        else:
            raise ValueError(f"Unsupported mode: {self.mode}")

        # 获取生命周期控制器和API验证器
        if self.context._lifecycle_controller is None:
            raise ValueError("Context lifecycle controller is not initialized")
        if self.context._lifecycle_manager is None:
            raise ValueError("Context lifecycle manager is not initialized")

        self.lifecycle_controller = self.context._lifecycle_controller
        self.api_validator = APIValidator(self.lifecycle_controller)
        self.plugin_manager = self.context.plugin_manager

        # 创建API路由器
        if self.mode == PTradeMode.RESEARCH:
            self.api_router = ResearchAPIRouter(
                self.context,
                self.event_bus,
                self.lifecycle_controller,
                self.api_validator,
            )
        elif self.mode == PTradeMode.BACKTEST:
            self.api_router = BacktestAPIRouter(
                self.context,
                self.event_bus,
                self.lifecycle_controller,
                self.api_validator,
                self.plugin_manager,
            )
        elif self.mode == PTradeMode.TRADING:
            self.api_router = TradingAPIRouter(
                self.context,
                self.event_bus,
                self.lifecycle_controller,
                self.api_validator,
            )

        self._logger.info(
            f"Strategy execution engine initialized in {self.mode.value} mode"
        )

    # ==========================================
    # 策略注册接口
    # ==========================================

    def register_strategy(self, strategy_name: str) -> "StrategyBuilder":
        """注册策略并返回策略构建器

        Args:
            strategy_name: 策略名称

        Returns:
            StrategyBuilder: 策略构建器对象
        """
        self._strategy_name = strategy_name
        return StrategyBuilder(self)

    def register_initialize(self, func: Callable[[PTradeContext], None]) -> None:
        """注册initialize函数"""
        self._strategy_functions["initialize"] = func
        self.context.register_initialize(func)

    def register_handle_data(self, func: Callable[[PTradeContext, Any], None]) -> None:
        """注册handle_data函数"""
        self._strategy_functions["handle_data"] = func
        self.context.register_handle_data(func)

    def register_before_trading_start(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> None:
        """注册before_trading_start函数"""
        self._strategy_functions["before_trading_start"] = func
        self.context.register_before_trading_start(func)

    def register_after_trading_end(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> None:
        """注册after_trading_end函数"""
        self._strategy_functions["after_trading_end"] = func
        self.context.register_after_trading_end(func)

    def register_tick_data(self, func: Callable[[PTradeContext, Any], None]) -> None:
        """注册tick_data函数"""
        self._strategy_functions["tick_data"] = func
        self.context.register_tick_data(func)

    def register_on_order_response(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> None:
        """注册on_order_response函数"""
        self._strategy_functions["on_order_response"] = func
        self.context.register_on_order_response(func)

    def register_on_trade_response(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> None:
        """注册on_trade_response函数"""
        self._strategy_functions["on_trade_response"] = func
        self.context.register_on_trade_response(func)

    # ==========================================
    # PTrade API 代理接口
    # ==========================================

    def __getattr__(self, name: str) -> Any:
        """代理PTrade API调用到API路由器"""
        if self.api_router and hasattr(self.api_router, name):
            return getattr(self.api_router, name)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    # ==========================================
    # 策略执行接口
    # ==========================================

    def run_strategy(self, data_source: Optional[Any] = None) -> Dict[str, Any]:
        """运行策略

        Args:
            data_source: 数据源（回测模式需要）

        Returns:
            Dict[str, Any]: 执行结果和统计信息
        """
        if not self._strategy_functions.get("initialize"):
            raise StrategyExecutionError("Strategy must have an initialize function")

        self._is_running = True
        execution_results: Dict[str, Any] = {
            "strategy_name": self._strategy_name,
            "mode": self.mode.value,
            "start_time": datetime.now(),
            "end_time": None,
            "success": False,
            "error": None,
            "lifecycle_stats": {},
            "validation_stats": {},
            "portfolio_performance": {},
        }

        try:
            self._logger.info(f"Starting strategy execution: {self._strategy_name}")

            # 1. 执行初始化
            self._execute_initialize()

            # 2. 根据模式执行策略
            if self.mode in [PTradeMode.RESEARCH]:
                self._run_research_mode()
            elif self.mode == PTradeMode.BACKTEST:
                self._run_backtest_mode(data_source)
            elif self.mode == PTradeMode.TRADING:
                self._run_trading_mode()

            execution_results["success"] = True
            self._logger.info("Strategy execution completed successfully")

        except Exception as e:
            execution_results["error"] = str(e)
            execution_results["traceback"] = traceback.format_exc()
            self._logger.error(f"Strategy execution failed: {e}")

        finally:
            self._is_running = False
            execution_results["end_time"] = datetime.now()

            # 收集统计信息
            execution_results[
                "lifecycle_stats"
            ] = self.lifecycle_controller.get_call_statistics()
            execution_results[
                "validation_stats"
            ] = self.api_validator.get_validation_statistics()
            execution_results[
                "portfolio_performance"
            ] = self._get_portfolio_performance()

        return execution_results

    def _execute_initialize(self) -> None:
        """执行初始化阶段"""
        self._logger.info("Executing initialize phase")
        self.context.execute_initialize()

    def _run_research_mode(self) -> None:
        """运行研究模式"""
        self._logger.info("Running in research mode")

        # 研究模式通常是一次性执行，不需要数据循环
        # 用户可以在initialize中进行所有研究工作
        pass

    def _run_backtest_mode(self, data_source: Optional[Any] = None) -> None:
        """运行回测模式"""
        self._logger.info("Running in backtest mode")

        if not data_source:
            self._logger.warning("No data source provided for backtest mode")
            return

        # 模拟回测数据循环
        if hasattr(data_source, "__iter__"):
            for data_point in data_source:
                self._process_data_point(data_point)
        else:
            # 单次数据处理
            self._process_data_point(data_source)

    def _run_trading_mode(self) -> None:
        """运行实盘交易模式"""
        self._logger.info("Running in trading mode")

        # 实盘交易模式需要实时数据流
        # 这里是简化实现，实际需要连接到实时数据源
        self._logger.warning(
            "Trading mode requires real-time data connection (not implemented)"
        )

    def _process_data_point(self, data: Any) -> None:
        """处理单个数据点"""
        try:
            # 更新Context中的当前数据
            if isinstance(data, dict):
                self.context.set_current_data(data)
                self.context.current_dt = data.get("datetime", datetime.now())

            # 执行盘前处理（如果定义了）
            if self._strategy_functions.get("before_trading_start"):
                self.context.execute_before_trading_start(data)

            # 执行主策略逻辑
            if self._strategy_functions.get("handle_data"):
                self.context.execute_handle_data(data)

            # 执行tick数据处理（如果定义了）
            if self._strategy_functions.get("tick_data"):
                self.context.execute_tick_data(data)

            # 执行盘后处理（如果定义了）
            if self._strategy_functions.get("after_trading_end"):
                self.context.execute_after_trading_end(data)

            # 更新投资组合
            self.context.update_portfolio()

        except Exception as e:
            self._logger.error(f"Error processing data point: {e}")
            raise

    def _get_portfolio_performance(self) -> Dict[str, Any]:
        """获取投资组合性能指标"""
        portfolio = self.context.portfolio

        return {
            "total_value": portfolio.portfolio_value,
            "cash": portfolio.cash,
            "positions_value": portfolio.positions_value,
            "returns": portfolio.returns,
            "pnl": portfolio.pnl,
            "positions_count": len(portfolio.positions),
            "recorded_vars": self.context.recorded_vars.copy(),
        }

    # ==========================================
    # 状态查询接口
    # ==========================================

    def get_execution_status(self) -> Dict[str, Any]:
        """获取执行状态"""
        return {
            "is_running": self._is_running,
            "strategy_name": self._strategy_name,
            "mode": self.mode.value,
            "current_phase": self.context.get_current_lifecycle_phase(),
            "initialized": self.context.initialized,
            "portfolio_value": self.context.portfolio.portfolio_value,
            "registered_functions": list(self._strategy_functions.keys()),
        }

    def get_detailed_statistics(self) -> Dict[str, Any]:
        """获取详细统计信息"""
        return {
            "lifecycle_stats": self.lifecycle_controller.get_call_statistics(),
            "validation_stats": self.api_validator.get_validation_statistics(),
            "portfolio_performance": self._get_portfolio_performance(),
            "execution_status": self.get_execution_status(),
        }

    # ==========================================
    # 重置和清理接口
    # ==========================================

    def reset_strategy(self) -> None:
        """重置策略状态"""
        self._logger.info("Resetting strategy state")

        self._strategy_functions.clear()
        self._strategy_name = None
        self._is_running = False
        self._current_data = None

        # 重置Context
        self.context.reset_for_new_strategy()

        # 重置API验证器
        self.api_validator.reset_statistics()

    def shutdown(self) -> None:
        """关闭执行引擎"""
        self._logger.info("Shutting down strategy execution engine")

        self._is_running = False
        # 清理资源
        if self.event_bus:
            # EventBus的清理逻辑
            pass


class StrategyBuilder:
    """策略构建器

    提供流式API来构建策略
    """

    def __init__(self, engine: StrategyExecutionEngine):
        self.engine = engine

    def initialize(self, func: Callable[[PTradeContext], None]) -> "StrategyBuilder":
        """设置初始化函数"""
        self.engine.register_initialize(func)
        return self

    def handle_data(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> "StrategyBuilder":
        """设置主策略逻辑函数"""
        self.engine.register_handle_data(func)
        return self

    def before_trading_start(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> "StrategyBuilder":
        """设置盘前处理函数"""
        self.engine.register_before_trading_start(func)
        return self

    def after_trading_end(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> "StrategyBuilder":
        """设置盘后处理函数"""
        self.engine.register_after_trading_end(func)
        return self

    def tick_data(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> "StrategyBuilder":
        """设置tick数据处理函数"""
        self.engine.register_tick_data(func)
        return self

    def on_order_response(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> "StrategyBuilder":
        """设置委托回报处理函数"""
        self.engine.register_on_order_response(func)
        return self

    def on_trade_response(
        self, func: Callable[[PTradeContext, Any], None]
    ) -> "StrategyBuilder":
        """设置成交回报处理函数"""
        self.engine.register_on_trade_response(func)
        return self

    def run(self, data_source: Optional[Any] = None) -> Dict[str, Any]:
        """运行策略"""
        return self.engine.run_strategy(data_source)


# ==========================================
# 便捷工厂函数
# ==========================================


def create_strategy_engine(
    mode: Union[str, PTradeMode] = "backtest",
    capital_base: float = 1000000,
    commission_rate: float = 0.0003,
    slippage_rate: float = 0.0,
) -> StrategyExecutionEngine:
    """创建策略执行引擎

    Args:
        mode: 运行模式 ("research", "backtest", "trading")
        capital_base: 起始资金
        commission_rate: 佣金费率
        slippage_rate: 滑点率

    Returns:
        StrategyExecutionEngine: 策略执行引擎实例
    """
    if isinstance(mode, str):
        mode = PTradeMode(mode)

    return StrategyExecutionEngine(
        mode=mode,
        capital_base=capital_base,
        commission_rate=commission_rate,
        slippage_rate=slippage_rate,
    )


def create_research_engine(capital_base: float = 1000000) -> StrategyExecutionEngine:
    """创建研究模式执行引擎"""
    return create_strategy_engine("research", capital_base)


def create_backtest_engine(
    capital_base: float = 1000000,
    commission_rate: float = 0.0003,
    slippage_rate: float = 0.0,
) -> StrategyExecutionEngine:
    """创建回测模式执行引擎"""
    return create_strategy_engine(
        "backtest", capital_base, commission_rate, slippage_rate
    )


def create_trading_engine(capital_base: float = 1000000) -> StrategyExecutionEngine:
    """创建实盘交易模式执行引擎"""
    return create_strategy_engine("trading", capital_base)
