# -*- coding: utf-8 -*-
"""
PTrade上下文和模式定义

完全符合PTrade官方API规范的Context对象实现
"""

import types
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ...core.plugin_manager import PluginManager
from .lifecycle_controller import LifecycleController, LifecyclePhase
from .models import (
    Blotter,
    Commission,
    FutureParams,
    Portfolio,
    Position,
    SecurityUnitData,
    SimulationParameters,
    VolumeShareSlippage,
)


class PTradeMode(Enum):
    """PTrade运行模式"""

    RESEARCH = "research"  # 研究模式
    BACKTEST = "backtest"  # 回测模式
    TRADING = "trading"  # 交易模式
    MARGIN_TRADING = "margin_trading"  # 融资融券交易模式


class StrategyLifecycleManager:
    """策略生命周期管理器

    负责管理策略的生命周期函数调用和阶段转换
    """

    def __init__(self, lifecycle_controller: LifecycleController):
        self._lifecycle_controller = lifecycle_controller
        self._strategy_functions: Dict[str, Callable] = {}

    def register_strategy_function(self, phase: str, func: Callable) -> None:
        """注册策略生命周期函数"""
        self._strategy_functions[phase] = func

    def execute_lifecycle_phase(
        self, phase: str, context: "PTradeContext", data: Optional[Any] = None
    ) -> Any:
        """执行指定的生命周期阶段"""
        # 设置当前阶段
        phase_enum = LifecyclePhase(phase)
        self._lifecycle_controller.set_phase(phase_enum)

        # 获取并执行策略函数
        strategy_func = self._strategy_functions.get(phase)
        if strategy_func:
            if phase in ["initialize"]:
                return strategy_func(context)
            elif phase in [
                "handle_data",
                "before_trading_start",
                "after_trading_end",
                "tick_data",
            ]:
                return strategy_func(context, data)
            elif phase in ["on_order_response"]:
                return strategy_func(context, data)  # data是Order对象
            elif phase in ["on_trade_response"]:
                return strategy_func(context, data)  # data是Trade对象

        return None


@dataclass
class PTradeContext:
    """PTrade策略上下文对象 - 完全符合PTrade规范

    这是策略执行的核心上下文对象，包含了所有策略运行所需的状态信息
    """

    # === 核心必需属性 ===
    portfolio: Portfolio
    mode: PTradeMode = PTradeMode.BACKTEST

    # === PTrade官方Context属性 ===
    capital_base: Optional[float] = None  # 起始资金
    previous_date: Optional[datetime] = None  # 前一个交易日
    sim_params: Optional[SimulationParameters] = None
    initialized: bool = False  # 是否执行初始化
    slippage: Optional[VolumeShareSlippage] = None
    commission: Optional[Commission] = None
    blotter: Optional[Blotter] = None
    recorded_vars: Dict[str, Any] = field(default_factory=dict)  # 收益曲线值

    # === 策略配置属性 ===
    universe: List[str] = field(default_factory=list)  # 股票池
    benchmark: Optional[str] = None  # 基准
    current_dt: Optional[datetime] = None  # 当前时间

    # === 内部配置属性 ===
    _parameters: Dict[str, Any] = field(default_factory=dict)  # 策略参数
    _volume_ratio: float = 0.25  # 成交比例
    _limit_mode: str = "volume"  # 限制模式
    _yesterday_position: Dict[str, Any] = field(default_factory=dict)  # 底仓

    # === 期货期权专用属性 ===
    _future_params: Optional[FutureParams] = None  # 期货参数
    _margin_rate_overrides: Dict[str, float] = field(default_factory=dict)  # 自定义保证金比例

    # === 生命周期管理属性 ===
    _lifecycle_controller: Optional[LifecycleController] = None
    _lifecycle_manager: Optional[StrategyLifecycleManager] = None

    # === 调度任务属性 ===
    _daily_tasks: List[Dict[str, Any]] = field(default_factory=list)  # 日级任务
    _interval_tasks: List[Dict[str, Any]] = field(default_factory=list)  # 间隔任务
    plugin_manager: Optional[Any] = None

    def __post_init__(self) -> None:
        """初始化后处理"""
        # === 初始化g全局对象 ===
        self.g = types.SimpleNamespace()  # 全局变量容器

        # === 初始化必需组件 ===
        if self.blotter is None:
            self.blotter = Blotter()

        if self.sim_params is None and self.capital_base:
            self.sim_params = SimulationParameters(self.capital_base)

        if self.slippage is None:
            self.slippage = VolumeShareSlippage()

        if self.commission is None:
            self.commission = Commission()

        if self._future_params is None:
            self._future_params = FutureParams()

        # === 初始化生命周期管理 ===
        if self._lifecycle_controller is None:
            self._lifecycle_controller = LifecycleController(self.mode.value)

        if self._lifecycle_manager is None:
            self._lifecycle_manager = StrategyLifecycleManager(
                self._lifecycle_controller
            )

        if self.plugin_manager is None:
            self.plugin_manager = PluginManager()

        # === 设置时间 ===
        if self.current_dt is None:
            self.current_dt = datetime.now()

        self.blotter.current_dt = self.current_dt

    # ==========================================
    # 策略生命周期函数注册接口
    # ==========================================

    def register_initialize(self, func: Callable[["PTradeContext"], None]) -> None:
        """注册initialize函数"""
        self._lifecycle_manager.register_strategy_function("initialize", func)

    def register_handle_data(
        self, func: Callable[["PTradeContext", Any], None]
    ) -> None:
        """注册handle_data函数"""
        self._lifecycle_manager.register_strategy_function("handle_data", func)

    def register_before_trading_start(
        self, func: Callable[["PTradeContext", Any], None]
    ) -> None:
        """注册before_trading_start函数"""
        self._lifecycle_manager.register_strategy_function("before_trading_start", func)

    def register_after_trading_end(
        self, func: Callable[["PTradeContext", Any], None]
    ) -> None:
        """注册after_trading_end函数"""
        self._lifecycle_manager.register_strategy_function("after_trading_end", func)

    def register_tick_data(self, func: Callable[["PTradeContext", Any], None]) -> None:
        """注册tick_data函数"""
        self._lifecycle_manager.register_strategy_function("tick_data", func)

    def register_on_order_response(
        self, func: Callable[["PTradeContext", Any], None]
    ) -> None:
        """注册on_order_response函数"""
        self._lifecycle_manager.register_strategy_function("on_order_response", func)

    def register_on_trade_response(
        self, func: Callable[["PTradeContext", Any], None]
    ) -> None:
        """注册on_trade_response函数"""
        self._lifecycle_manager.register_strategy_function("on_trade_response", func)

    # ==========================================
    # 策略生命周期执行接口
    # ==========================================

    def execute_initialize(self) -> None:
        """执行初始化阶段"""
        result = self._lifecycle_manager.execute_lifecycle_phase("initialize", self)
        self.initialized = True
        return result

    def execute_handle_data(self, data: Any) -> None:
        """执行主策略逻辑阶段"""
        return self._lifecycle_manager.execute_lifecycle_phase(
            "handle_data", self, data
        )

    def execute_before_trading_start(self, data: Any) -> None:
        """执行盘前处理阶段"""
        return self._lifecycle_manager.execute_lifecycle_phase(
            "before_trading_start", self, data
        )

    def execute_after_trading_end(self, data: Any) -> None:
        """执行盘后处理阶段"""
        return self._lifecycle_manager.execute_lifecycle_phase(
            "after_trading_end", self, data
        )

    def execute_tick_data(self, data: Any) -> None:
        """执行tick数据处理阶段"""
        return self._lifecycle_manager.execute_lifecycle_phase("tick_data", self, data)

    def execute_on_order_response(self, order: Any) -> None:
        """执行委托回报处理阶段"""
        return self._lifecycle_manager.execute_lifecycle_phase(
            "on_order_response", self, order
        )

    def execute_on_trade_response(self, trade: Any) -> None:
        """执行成交回报处理阶段"""
        return self._lifecycle_manager.execute_lifecycle_phase(
            "on_trade_response", self, trade
        )

    # ==========================================
    # 策略配置管理接口
    # ==========================================

    def set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        self.universe = securities

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        self.benchmark = benchmark

    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        if self.commission:
            self.commission.cost = commission

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        if self.slippage:
            self.slippage.price_impact = slippage

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        self._volume_ratio = ratio

    def set_limit_mode(self, mode: str) -> None:
        """设置成交限制模式"""
        self._limit_mode = mode

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        self._yesterday_position = positions

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略参数"""
        self._parameters.update(params)

    def set_future_commission(self, commission: float) -> None:
        """设置期货手续费"""
        if self._future_params:
            # 注意：FutureParams没有commission属性，这里需要扩展
            self._future_params.commission = commission

    def set_margin_rate(self, security: str, rate: float) -> None:
        """设置期货保证金比例"""
        self._margin_rate_overrides[security] = rate

    # ==========================================
    # 调度任务管理接口
    # ==========================================

    def run_daily(self, func: Callable, time: str) -> None:
        """注册日级调度任务"""
        task = {"function": func, "time": time, "type": "daily"}
        self._daily_tasks.append(task)

    def run_interval(self, func: Callable, interval: int) -> None:
        """注册间隔调度任务"""
        task = {"function": func, "interval": interval, "type": "interval"}
        self._interval_tasks.append(task)

    # ==========================================
    # 生命周期状态查询接口
    # ==========================================

    def get_current_lifecycle_phase(self) -> Optional[str]:
        """获取当前生命周期阶段"""
        return self._lifecycle_controller.current_phase_name

    def get_lifecycle_statistics(self) -> Dict[str, Any]:
        """获取生命周期统计信息"""
        return self._lifecycle_controller.get_call_statistics()

    def is_api_allowed(self, api_name: str) -> bool:
        """检查API是否在当前阶段允许调用"""
        try:
            self._lifecycle_controller.validate_api_call(api_name)
            return True
        except Exception:
            return False

    # ==========================================
    # 数据访问接口
    # ==========================================

    def get_current_data(self) -> Optional[Dict[str, SecurityUnitData]]:
        """获取当前数据（SecurityUnitData字典）"""
        # 这应该由数据适配器提供，这里返回占位符
        return getattr(self, "_current_data", None)

    def set_current_data(self, data: Dict[str, SecurityUnitData]) -> None:
        """设置当前数据"""
        self._current_data = data

    def get_security_data(self, security: str) -> Optional[SecurityUnitData]:
        """获取指定证券的当前数据"""
        current_data = self.get_current_data()
        if current_data:
            return current_data.get(security)
        return None

    # ==========================================
    # 工具方法
    # ==========================================

    def log_info(self, message: str) -> None:
        """记录信息日志"""
        print(f"[INFO] {self.current_dt}: {message}")

    def record(self, name: str, value: Any) -> None:
        """记录收益曲线值"""
        self.recorded_vars[name] = value

    def get_position(self, security: str) -> Optional[Position]:
        """获取持仓信息"""
        return self.portfolio.positions.get(security)

    def update_portfolio(self) -> None:
        """更新投资组合信息"""
        self.portfolio.update_portfolio_value()

    def reset_for_new_strategy(self) -> None:
        """为新策略重置上下文状态"""
        self.initialized = False
        self.recorded_vars.clear()
        self._daily_tasks.clear()
        self._interval_tasks.clear()
        self._lifecycle_controller.reset()

        # 重置blotter
        self.blotter = Blotter()
        self.blotter.current_dt = self.current_dt


# ==========================================
# 工厂函数
# ==========================================


def create_research_context(capital_base: float = 1000000) -> PTradeContext:
    """创建研究模式上下文"""
    portfolio = Portfolio(cash=capital_base)
    return PTradeContext(
        portfolio=portfolio, mode=PTradeMode.RESEARCH, capital_base=capital_base
    )


def create_backtest_context(
    capital_base: float = 1000000,
    commission_rate: float = 0.0003,
    slippage_rate: float = 0.0,
) -> PTradeContext:
    """创建回测模式上下文"""
    portfolio = Portfolio(cash=capital_base)
    context = PTradeContext(
        portfolio=portfolio, mode=PTradeMode.BACKTEST, capital_base=capital_base
    )
    context.set_commission(commission_rate)
    context.set_slippage(slippage_rate)
    return context


def create_trading_context(capital_base: float = 1000000) -> PTradeContext:
    """创建实盘交易模式上下文"""
    portfolio = Portfolio(cash=capital_base)
    return PTradeContext(
        portfolio=portfolio, mode=PTradeMode.TRADING, capital_base=capital_base
    )
