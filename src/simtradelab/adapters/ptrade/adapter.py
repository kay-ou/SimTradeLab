# -*- coding: utf-8 -*-
"""
PTrade 兼容层适配器

根据PTrade API文档提供标准的API函数兼容接口，
支持回测、交易、研究三种模式，符合PTrade规范。
"""

import importlib
import importlib.util
import types
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

from ...core.event_bus import EventBus
from ...exceptions import SimTradeLabError
from ...plugins.base import BasePlugin, PluginConfig, PluginMetadata
from .api_router import (
    BacktestAPIRouter,
    BaseAPIRouter,
    LiveTradingAPIRouter,
    ResearchAPIRouter,
)


class PTradeAdapterError(SimTradeLabError):
    """PTrade适配器异常"""

    pass


class PTradeCompatibilityError(PTradeAdapterError):
    """PTrade兼容性异常"""

    pass


class PTradeAPIError(PTradeAdapterError):
    """PTrade API调用异常"""

    pass


class PTradeMode(Enum):
    """PTrade运行模式"""

    RESEARCH = "research"  # 研究模式
    BACKTEST = "backtest"  # 回测模式
    TRADING = "trading"  # 交易模式
    MARGIN_TRADING = "margin_trading"  # 融资融券交易模式


@dataclass
class Portfolio:
    """投资组合对象 - 完全符合PTrade规范"""

    # 股票账户基础属性 (8个)
    cash: float  # 当前可用资金（不包含冻结资金）
    portfolio_value: float = 0.0  # 当前持有的标的和现金的总价值
    positions_value: float = 0.0  # 持仓价值
    capital_used: float = 0.0  # 已使用的现金
    returns: float = 0.0  # 当前的收益比例，相对于初始资金
    pnl: float = 0.0  # 当前账户总资产-初始账户总资产
    start_date: Optional[datetime] = None  # 开始时间
    positions: Dict[str, "Position"] = field(default_factory=dict)  # 持仓字典

    # 期权账户额外属性
    margin: Optional[float] = None  # 保证金
    risk_degree: Optional[float] = None  # 风险度

    def __post_init__(self) -> None:
        if self.start_date is None:
            self.start_date = datetime.now()
        # 保存起始资金用于计算收益率
        self._starting_cash = self.cash
        # 初始化时现金就是总资产
        self.portfolio_value = self.cash

    @property
    def total_value(self) -> float:
        """总资产"""
        return self.portfolio_value

    def update_portfolio_value(self) -> None:
        """更新投资组合价值"""
        self.positions_value = sum(pos.market_value for pos in self.positions.values())
        self.portfolio_value = self.cash + self.positions_value
        self.capital_used = self._starting_cash - self.cash
        if self._starting_cash > 0:
            self.returns = (
                self.portfolio_value - self._starting_cash
            ) / self._starting_cash
            self.pnl = self.portfolio_value - self._starting_cash


@dataclass
class Position:
    """持仓对象 - 完全符合PTrade规范"""

    # 股票账户基础属性 (7个)
    sid: str  # 标的代码
    enable_amount: int  # 可用数量
    amount: int  # 总持仓数量
    last_sale_price: float  # 最新价格
    cost_basis: float  # 持仓成本价格
    today_amount: int = 0  # 今日开仓数量（且仅回测有效）
    business_type: str = "stock"  # 持仓类型

    # 期货账户扩展属性 (18个)
    short_enable_amount: Optional[int] = None  # 空头仓可用数量
    long_enable_amount: Optional[int] = None  # 多头仓可用数量
    today_short_amount: Optional[int] = None  # 空头仓今仓数量
    today_long_amount: Optional[int] = None  # 多头仓今仓数量
    long_cost_basis: Optional[float] = None  # 多头仓持仓成本
    short_cost_basis: Optional[float] = None  # 空头仓持仓成本
    long_amount: Optional[int] = None  # 多头仓总持仓量
    short_amount: Optional[int] = None  # 空头仓总持仓量
    long_pnl: Optional[float] = None  # 多头仓浮动盈亏
    short_pnl: Optional[float] = None  # 空头仓浮动盈亏
    delivery_date: Optional[datetime] = None  # 交割日
    margin_rate: Optional[float] = None  # 保证金比例
    contract_multiplier: Optional[int] = None  # 合约乘数

    # 期权账户扩展属性 (17个)
    covered_enable_amount: Optional[int] = None  # 备兑仓可用数量
    covered_cost_basis: Optional[float] = None  # 备兑仓持仓成本
    covered_amount: Optional[int] = None  # 备兑仓总持仓量
    covered_pnl: Optional[float] = None  # 备兑仓浮动盈亏
    margin: Optional[float] = None  # 保证金
    exercise_date: Optional[datetime] = None  # 行权日

    def __post_init__(self) -> None:
        self.security = self.sid

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.amount * self.last_sale_price

    @property
    def pnl(self) -> float:
        """持仓盈亏"""
        return (self.last_sale_price - self.cost_basis) * self.amount

    @property
    def returns(self) -> float:
        """持仓收益率"""
        if self.cost_basis == 0:
            return 0.0
        return (self.last_sale_price - self.cost_basis) / self.cost_basis


@dataclass
class Order:
    """订单对象 - 完全符合PTrade规范"""

    id: str  # 订单号
    dt: datetime  # 订单产生时间
    symbol: str  # 标的代码（注意：标的代码尾缀为四位，上证为XSHG，深圳为XSHE）
    amount: int  # 下单数量，买入是正数，卖出是负数
    limit: Optional[float] = None  # 指定价格
    status: str = "new"  # 订单状态
    filled: int = 0  # 成交数量

    def __post_init__(self) -> None:
        self.security = self.symbol
        self.limit_price = self.limit
        self.created_at = self.dt


@dataclass
class SecurityUnitData:
    """单位时间内股票数据对象 - 完全符合PTrade规范"""

    dt: datetime  # 时间
    open: float  # 时间段开始时价格
    close: float  # 时间段结束时价格
    price: float  # 结束时价格
    low: float  # 最低价
    high: float  # 最高价
    volume: int  # 成交的股票数量
    money: float  # 成交的金额


class SimulationParameters:
    """模拟参数对象"""

    def __init__(self, capital_base: float, data_frequency: str = "1d"):
        self.capital_base = capital_base
        self.data_frequency = data_frequency


class VolumeShareSlippage:
    """滑点对象"""

    def __init__(self, volume_limit: float = 0.025, price_impact: float = 0.1):
        self.volume_limit = volume_limit
        self.price_impact = price_impact


class Commission:
    """佣金费用对象"""

    def __init__(
        self, tax: float = 0.001, cost: float = 0.0003, min_trade_cost: float = 5.0
    ):
        self.tax = tax
        self.cost = cost
        self.min_trade_cost = min_trade_cost


class Blotter:
    """订单记录管理器"""

    def __init__(self) -> None:
        self.orders: Dict[str, Order] = {}
        self.order_id_counter = 0
        self.current_dt = datetime.now()  # 当前单位时间的开始时间

    def create_order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> str:
        """创建订单"""
        order_id = f"order_{self.order_id_counter}"
        self.order_id_counter += 1

        order = Order(
            id=order_id,
            dt=self.current_dt,
            symbol=security,
            amount=amount,
            limit=limit_price,
        )

        self.orders[order_id] = order
        return order_id

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        if order_id in self.orders:
            self.orders[order_id].status = "cancelled"
            return True
        return False


class FutureParams:
    """期货参数对象"""

    def __init__(self, margin_rate: float = 0.1, contract_multiplier: int = 1):
        self.margin_rate = margin_rate
        self.contract_multiplier = contract_multiplier


@dataclass
class PTradeContext:
    """PTrade策略上下文对象 - 完全符合PTrade规范"""

    portfolio: Portfolio
    capital_base: Optional[float] = None  # 起始资金
    previous_date: Optional[datetime] = None  # 前一个交易日
    sim_params: Optional[SimulationParameters] = None
    initialized: bool = False  # 是否执行初始化
    slippage: Optional[VolumeShareSlippage] = None
    commission: Optional[Commission] = None
    blotter: Optional[Blotter] = None
    recorded_vars: Dict[str, Any] = field(default_factory=dict)  # 收益曲线值
    universe: List[str] = field(default_factory=list)
    benchmark: Optional[str] = None
    current_dt: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.g = types.SimpleNamespace()  # 全局变量容器

        if self.blotter is None:
            self.blotter = Blotter()

        if self.sim_params is None and self.capital_base:
            self.sim_params = SimulationParameters(self.capital_base)

        if self.slippage is None:
            self.slippage = VolumeShareSlippage()

        if self.commission is None:
            self.commission = Commission()


class PTradeAdapter(BasePlugin):
    """
    PTrade 兼容层适配器

    提供标准的 PTrade API 兼容性，支持研究、回测、交易三种模式。
    采用 v4.0 架构的模式感知适配器设计，通过 API 路由器实现不同模式的功能。
    """

    METADATA = PluginMetadata(
        name="ptrade_adapter",
        version="2.0.0",
        description="PTrade API Compatibility Adapter",
        author="SimTradeLab",
        dependencies=[
            "csv_data_plugin",
            "technical_indicators_plugin",
        ],  # 依赖CSV数据插件和技术指标插件
        tags=["ptrade", "compatibility", "adapter", "complete"],
        category="adapter",
        priority=10,  # 高优先级，确保早期加载
    )

    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)

        # PTrade 适配器状态
        self._ptrade_context: Optional[PTradeContext] = None
        self._strategy_module: Optional[types.ModuleType] = None
        self._api_router: Optional[BaseAPIRouter] = None  # 核心：API路由器
        self._data_cache: Dict[str, Any] = {}
        self._current_data: Dict[str, Dict[str, float]] = {}

        # 插件引用（在初始化时从插件管理器获取）
        self._data_plugin = None
        self._indicators_plugin = None

        # 设置PTrade支持的模式
        self._set_supported_modes(
            {
                PTradeMode.RESEARCH,
                PTradeMode.BACKTEST,
                PTradeMode.TRADING,
                PTradeMode.MARGIN_TRADING,
            }
        )

        # 默认回测模式
        self._current_mode = PTradeMode.BACKTEST

        # 配置选项
        self._initial_cash = self._config.config.get("initial_cash", 1000000.0)
        self._commission_rate = self._config.config.get("commission_rate", 0.0003)
        self._slippage_rate = self._config.config.get("slippage_rate", 0.001)

        # 策略生命周期钩子
        self._strategy_hooks: Dict[str, Optional[Callable[..., Any]]] = {
            "initialize": None,
            "handle_data": None,
            "before_trading_start": None,
            "after_trading_end": None,
            "tick_data": None,
            "on_order_response": None,
            "on_trade_response": None,
        }

        # 事件监听器列表
        self._event_listeners: List[str] = []

        # 事件总线引用 - 将在插件管理器中设置
        self._event_bus_ref: Optional[EventBus] = None

    def set_event_bus(self, event_bus: EventBus) -> None:
        """
        Set the event bus reference (called by plugin manager)

        Args:
            event_bus: The event bus instance
        """
        self._event_bus_ref = event_bus

    def _init_api_router(self) -> BaseAPIRouter:
        """根据当前模式初始化 API 路由器"""
        current_mode = self.get_current_mode()

        # 确保上下文已初始化
        if self._ptrade_context is None:
            raise PTradeAdapterError(
                "PTrade context must be initialized before API router"
            )

        if current_mode == PTradeMode.BACKTEST:
            return BacktestAPIRouter(
                self._ptrade_context,
                self._event_bus_ref,
                slippage_rate=self._slippage_rate,
                commission_rate=self._commission_rate,
            )
        elif current_mode == PTradeMode.TRADING:
            return LiveTradingAPIRouter(self._ptrade_context, self._event_bus_ref)
        elif current_mode == PTradeMode.RESEARCH:
            return ResearchAPIRouter(self._ptrade_context, self._event_bus_ref)
        else:
            raise PTradeAdapterError(f"Unsupported mode: {current_mode}")

    def _on_mode_change(self, new_mode: PTradeMode) -> None:
        """模式切换时重新初始化API路由器"""
        if self._ptrade_context is not None:
            self._api_router = self._init_api_router()
            self._logger.info(f"API router switched to {new_mode.value} mode")

    def _setup_plugin_proxies(self) -> None:
        """设置插件代理机制"""
        # 为技术指标插件创建代理方法
        if self._indicators_plugin:
            # 自动让PTrade adapter获得插件的所有公共方法
            plugin_methods = [
                name
                for name in dir(self._indicators_plugin)
                if not name.startswith("_")
                and callable(getattr(self._indicators_plugin, name))
            ]

            for method_name in plugin_methods:
                if not hasattr(self, method_name):  # 避免覆盖现有方法
                    plugin_method = getattr(self._indicators_plugin, method_name)
                    # 创建代理方法
                    setattr(self, method_name, plugin_method)

            self._logger.debug(
                "Created proxy methods for technical indicators plugin: "
                f"{plugin_methods}"
            )

    def _cleanup_plugin_proxies(self) -> None:
        """清理插件代理方法"""
        # 这里可以添加清理逻辑，但由于我们是直接设置属性，不需要特别清理
        pass

    def _on_initialize(self) -> None:
        """初始化适配器"""
        self._logger.info("Initializing PTrade Adapter")

        # 初始化PTrade上下文
        portfolio = Portfolio(cash=self._initial_cash)
        self._ptrade_context = PTradeContext(
            portfolio=portfolio, capital_base=self._initial_cash
        )

        # 初始化 API 路由器
        self._api_router = self._init_api_router()

        # 设置插件代理机制
        self._setup_plugin_proxies()

        # 监听插件系统事件
        if self._event_bus_ref is not None:
            self._setup_event_listeners()

        mode_name = self._current_mode.value if self._current_mode else "unknown"
        self._logger.info(f"PTrade Adapter initialized with {mode_name} mode")

    def set_plugin_manager(self, plugin_manager: Any) -> None:
        """设置插件管理器引用"""
        self._plugin_manager = plugin_manager

        # 获取插件
        if self._plugin_manager:
            self._data_plugin = self._plugin_manager.get_plugin("csv_data_plugin")
            if not self._data_plugin:
                self._logger.warning("CSV data plugin not found or not loaded")

            self._indicators_plugin = self._plugin_manager.get_plugin(
                "technical_indicators_plugin"
            )
            if not self._indicators_plugin:
                self._logger.warning(
                    "Technical indicators plugin not found or not loaded"
                )
        else:
            self._logger.warning(
                "No plugin manager available, plugin access may be limited"
            )

    def _on_start(self) -> None:
        """启动适配器"""
        self._logger.info("Starting PTrade Adapter")

        # 发布适配器启动事件
        if self._event_bus_ref is not None:
            self._event_bus_ref.publish(
                "ptrade.adapter.started",
                data={"adapter": self, "context": self._ptrade_context},
                source="ptrade_adapter",
            )

    def _on_stop(self) -> None:
        """停止适配器"""
        self._logger.info("Stopping PTrade Adapter")

        # 清理资源
        self._cleanup_strategy()

        # 清理插件代理
        self._cleanup_plugin_proxies()

        # 清理事件监听器
        self._cleanup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """设置事件监听器"""
        # 监听插件系统事件
        pass

    def _cleanup_event_listeners(self) -> None:
        """清理事件监听器"""
        if self._event_bus_ref is not None:
            for listener_id in self._event_listeners:
                self._event_bus_ref.unsubscribe(listener_id)
        self._event_listeners.clear()

    def _cleanup_strategy(self) -> None:
        """清理策略资源"""
        if self._strategy_module:
            # 清理策略模块引用
            self._strategy_module = None

        # 重置策略钩子
        for hook_name in self._strategy_hooks:
            self._strategy_hooks[hook_name] = None

        # 清理缓存
        self._data_cache.clear()
        self._current_data.clear()

    # =========================================
    # 策略执行和生命周期管理
    # =========================================

    def run_strategy(self, data: Optional[Dict[str, Any]] = None) -> None:
        """
        运行策略主循环

        Args:
            data: 市场数据，如果为None则使用模拟数据
        """
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")

        if not self._strategy_module:
            raise PTradeAPIError("No strategy loaded")

        # 更新当前时间
        self._ptrade_context.current_dt = datetime.now()

        # 如果没有提供数据，生成模拟数据
        if data is None:
            data = self._generate_market_data()

        # 执行盘前处理
        if self._strategy_hooks["before_trading_start"]:
            try:
                self._strategy_hooks["before_trading_start"](self._ptrade_context, data)
            except Exception as e:
                self._logger.error(f"Error in before_trading_start: {e}")

        # 执行主策略逻辑
        if self._strategy_hooks["handle_data"]:
            try:
                self._strategy_hooks["handle_data"](self._ptrade_context, data)
            except Exception as e:
                self._logger.error(f"Error in handle_data: {e}")

        # 执行盘后处理
        if self._strategy_hooks["after_trading_end"]:
            try:
                self._strategy_hooks["after_trading_end"](self._ptrade_context, data)
            except Exception as e:
                self._logger.error(f"Error in after_trading_end: {e}")

        # 更新投资组合价值
        self._ptrade_context.portfolio.update_portfolio_value()

        # 发布策略运行事件
        if self._event_bus_ref is not None:
            self._event_bus_ref.publish(
                "ptrade.strategy.run",
                data={
                    "portfolio_value": self._ptrade_context.portfolio.portfolio_value,
                    "cash": self._ptrade_context.portfolio.cash,
                    "returns": self._ptrade_context.portfolio.returns,
                    "positions_count": len(self._ptrade_context.portfolio.positions),
                },
                source="ptrade_adapter",
            )

    def _generate_market_data(self) -> Dict[str, Any]:
        """生成模拟市场数据"""
        if self._ptrade_context is None or not self._ptrade_context.universe:
            return {}

        # 从数据插件获取市场快照
        if self._data_plugin:
            snapshot = self._data_plugin.get_market_snapshot(
                self._ptrade_context.universe
            )
        else:
            # 如果数据插件不可用，使用默认数据
            snapshot = {}
            for security in self._ptrade_context.universe:
                price = 10.0
                snapshot[security] = {
                    "last_price": price,
                    "pre_close": price,
                    "open": price,
                    "high": price,
                    "low": price,
                    "volume": 100000,
                    "money": price * 100000,
                    "datetime": datetime.now(),
                    "price": price,
                }

        # 更新当前数据缓存
        self._current_data.update(snapshot)  # type: ignore[arg-type]

        return snapshot

    def _get_current_price(self, security: str) -> float:
        """获取股票当前价格"""
        # 先从缓存查找
        if security in self._current_data:
            return self._current_data[security].get("last_price", 10.0)
        
        # 从数据插件获取
        if self._data_plugin:
            try:
                price = self._data_plugin.get_current_price(security)
                if price is not None:
                    return price
            except Exception as e:
                self._logger.warning(f"Failed to get current price for {security}: {e}")
        
        # 使用默认价格
        base_price = 15.0 if security.startswith("000") else 20.0
        return base_price

    def _generate_price_series(self, base_price: float, length: int) -> np.ndarray:
        """生成价格序列"""
        # 生成随机价格序列
        returns = np.random.normal(0, 0.01, length)
        prices = [base_price]
        
        for i in range(1, length):
            new_price = prices[-1] * (1 + returns[i])
            prices.append(max(new_price, 0.01))  # 确保价格为正
        
        return np.array(prices)

    def get_strategy_performance(self) -> Dict[str, Any]:
        """获取策略性能统计"""
        if self._ptrade_context is None:
            return {}

        portfolio = self._ptrade_context.portfolio

        # 计算基本性能指标
        return {
            "portfolio_value": portfolio.portfolio_value,
            "cash": portfolio.cash,
            "positions_value": portfolio.positions_value,
            "returns": portfolio.returns,
            "pnl": portfolio.pnl,
            "positions_count": len(portfolio.positions),
            "total_trades": len(self._ptrade_context.blotter.orders)
            if self._ptrade_context.blotter
            else 0,
            "winning_trades": len(
                [
                    o
                    for o in self._ptrade_context.blotter.orders.values()
                    if o.status == "filled" and o.filled > 0
                ]
            )
            if self._ptrade_context.blotter
            else 0,
            "starting_cash": portfolio._starting_cash,
            "current_datetime": self._ptrade_context.current_dt,
        }

    def execute_strategy_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        执行策略钩子函数

        Args:
            hook_name: 钩子名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            钩子函数返回值
        """
        if hook_name not in self._strategy_hooks:
            raise PTradeAPIError(f"Unknown strategy hook: {hook_name}")

        hook_func = self._strategy_hooks[hook_name]
        if not hook_func:
            self._logger.warning(f"Strategy hook {hook_name} is not implemented")
            return None

        try:
            return hook_func(*args, **kwargs)
        except Exception as e:
            self._logger.error(f"Error executing strategy hook {hook_name}: {e}")
            raise PTradeAPIError(f"Strategy hook {hook_name} failed: {e}")

    # =========================================
    # 策略加载和管理
    # =========================================

    def load_strategy(self, strategy_file: Union[str, Path]) -> bool:
        """
        加载PTrade策略文件

        Args:
            strategy_file: 策略文件路径

        Returns:
            是否成功加载
        """
        try:
            strategy_path = Path(strategy_file)
            if not strategy_path.exists():
                raise PTradeCompatibilityError(
                    f"Strategy file not found: {strategy_path}"
                )

            self._logger.info(f"Loading PTrade strategy: {strategy_path}")

            # 加载策略模块
            spec = importlib.util.spec_from_file_location("strategy", strategy_path)
            if spec is None or spec.loader is None:
                raise PTradeCompatibilityError(
                    f"Failed to load strategy spec: {strategy_path}"
                )

            strategy_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(strategy_module)

            # 注入PTrade API和全局对象
            self._inject_ptrade_apis(strategy_module)

            # 提取策略钩子函数
            self._extract_strategy_hooks(strategy_module)

            # 保存策略模块引用
            self._strategy_module = strategy_module

            # 执行策略初始化
            if self._strategy_hooks["initialize"]:
                self._strategy_hooks["initialize"](self._ptrade_context)
                if self._ptrade_context:
                    self._ptrade_context.initialized = True

            self._logger.info(f"PTrade strategy loaded successfully: {strategy_path}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to load PTrade strategy: {e}")
            raise PTradeCompatibilityError(f"Strategy loading failed: {e}")

    def _inject_ptrade_apis(self, strategy_module: types.ModuleType) -> None:
        """向策略模块注入PTrade API"""

        # 注入全局对象 - 直接设置为context.g的引用
        if self._ptrade_context is not None:
            setattr(strategy_module, "g", self._ptrade_context.g)
        else:
            # 如果上下文不存在，创建一个空的全局对象
            setattr(strategy_module, "g", types.SimpleNamespace())

        # 获取策略钩子函数名称列表
        strategy_hook_names = set(self._strategy_hooks.keys())

        # 通过API路由器注入API方法
        if self._api_router is not None:
            # 获取路由器支持的所有API方法
            api_methods = [
                method_name
                for method_name in dir(self._api_router)
                if not method_name.startswith("_")
                and callable(getattr(self._api_router, method_name))
            ]

            injected_count = 0
            for api_name in api_methods:
                # 如果是策略钩子函数，跳过注入
                if api_name in strategy_hook_names:
                    continue

                # 跳过路由器内部方法
                if api_name in [
                    "validate_and_execute",
                    "is_mode_supported",
                    "handle_data",
                ]:
                    continue

                api_func = getattr(self._api_router, api_name)
                if api_func:
                    # 创建API包装器，自动注入适配器引用
                    wrapped_func = self._create_api_wrapper(api_func, api_name)
                    setattr(strategy_module, api_name, wrapped_func)
                    injected_count += 1

            self._logger.debug(
                f"Injected {injected_count} PTrade APIs via "
                f"{self._api_router.__class__.__name__}"
            )
        else:
            self._logger.warning("No API router available for API injection")

    def _create_api_wrapper(
        self, api_func: Callable[..., Any], api_name: str
    ) -> Callable[..., Any]:
        """创建API包装器函数"""

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # 自动注入适配器引用作为第一个参数
                return api_func(*args, **kwargs)
            except Exception as e:
                self._logger.error(f"PTrade API '{api_name}' failed: {e}")
                raise PTradeAPIError(f"API call failed: {api_name}: {e}")

        # 保留原函数的文档
        wrapper.__name__ = api_name
        wrapper.__doc__ = api_func.__doc__
        return wrapper

    def _extract_strategy_hooks(self, strategy_module: types.ModuleType) -> None:
        """提取策略钩子函数"""
        for hook_name in self._strategy_hooks:
            if hasattr(strategy_module, hook_name):
                hook_func = getattr(strategy_module, hook_name)
                if callable(hook_func):
                    self._strategy_hooks[hook_name] = hook_func
                    self._logger.debug(f"Found strategy hook: {hook_name}")

    # =========================================
    # 公共接口
    # =========================================

    def get_ptrade_context(self) -> Optional[PTradeContext]:
        """获取PTrade上下文"""
        return self._ptrade_context

    def get_portfolio(self) -> Optional[Portfolio]:
        """获取投资组合"""
        return self._ptrade_context.portfolio if self._ptrade_context else None

    def get_api_stats(self) -> Dict[str, Any]:
        """获取API统计信息"""
        current_mode = self.get_current_mode()

        # 通过API路由器获取统计信息
        if self._api_router is not None:
            # 获取路由器支持的所有API方法
            api_methods = [
                method_name
                for method_name in dir(self._api_router)
                if not method_name.startswith("_")
                and callable(getattr(self._api_router, method_name))
                and method_name
                not in ["validate_and_execute", "is_mode_supported", "handle_data"]
            ]

            # 按类别统计API数量（简化版）
            trading_apis = [
                api
                for api in api_methods
                if api.startswith(("order", "cancel", "get_position", "get_trades"))
            ]
            data_apis = [
                api
                for api in api_methods
                if api.startswith(("get_history", "get_price", "get_snapshot"))
            ]
            calc_apis = [
                api
                for api in api_methods
                if api.startswith(("get_MACD", "get_KDJ", "get_RSI", "get_CCI"))
            ]
            util_apis = [api for api in api_methods if api in ["log", "check_limit"]]
            setting_apis = [api for api in api_methods if api.startswith("set_")]

            return {
                "total_apis": len(api_methods),
                "trading_apis": len(trading_apis),
                "market_data_apis": len(data_apis),
                "calculations_apis": len(calc_apis),
                "utils_apis": len(util_apis),
                "settings_apis": len(setting_apis),
                "current_mode": current_mode.value if current_mode else None,
                "api_router_type": self._api_router.__class__.__name__,
                "strategy_loaded": self._strategy_module is not None,
                "portfolio_value": self._ptrade_context.portfolio.portfolio_value
                if self._ptrade_context
                else 0,
            }
        else:
            return {
                "total_apis": 0,
                "trading_apis": 0,
                "market_data_apis": 0,
                "calculations_apis": 0,
                "utils_apis": 0,
                "settings_apis": 0,
                "current_mode": current_mode.value if current_mode else None,
                "api_router_type": "None",
                "strategy_loaded": self._strategy_module is not None,
                "portfolio_value": self._ptrade_context.portfolio.portfolio_value
                if self._ptrade_context
                else 0,
            }

    def __enter__(self) -> "PTradeAdapter":
        """上下文管理器入口"""
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        """上下文管理器出口"""
        self.shutdown()
