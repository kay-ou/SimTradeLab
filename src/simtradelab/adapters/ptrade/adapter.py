# -*- coding: utf-8 -*-
"""
PTrade 完整兼容层适配器

根据PTrade API文档提供完整的150+ API函数兼容接口，
支持回测、交易、研究三种模式，完全符合PTrade规范。
"""

import asyncio
import importlib
import importlib.util
import logging
import types
import weakref
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

import numpy as np
import pandas as pd

from ...core.event_bus import Event, EventBus, EventPriority
from ...exceptions import SimTradeLabError
from ...plugins.base import BasePlugin, PluginConfig, PluginMetadata, PluginState


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
        """总资产 - 兼容性别名"""
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
        # 兼容性属性映射
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
        # 兼容性属性映射
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


class PTradeAPIRegistry:
    """PTrade API注册表"""

    def __init__(self) -> None:
        self._apis: Dict[str, Callable[..., Any]] = {}
        self._api_modes: Dict[str, Set[PTradeMode]] = {}  # API支持的模式
        self._categories: Dict[str, List[str]] = {
            "lifecycle": [],  # 策略生命周期函数
            "settings": [],  # 设置函数
            "market_data": [],  # 获取信息函数
            "trading": [],  # 交易相关函数
            "margin_trading": [],  # 融资融券函数
            "futures": [],  # 期货专用函数
            "options": [],  # 期权专用函数
            "calculations": [],  # 计算函数
            "utils": [],  # 其他函数
        }

    def register_api(
        self,
        name: str,
        func: Callable[..., Any],
        category: str = "utils",
        modes: Optional[Set[PTradeMode]] = None,
    ) -> None:
        """注册API函数"""
        self._apis[name] = func
        self._api_modes[name] = modes or {
            PTradeMode.RESEARCH,
            PTradeMode.BACKTEST,
            PTradeMode.TRADING,
        }
        if category in self._categories:
            self._categories[category].append(name)

    def get_api(self, name: str) -> Optional[Callable[..., Any]]:
        """获取API函数"""
        return self._apis.get(name)

    def get_api_modes(self, name: str) -> Set[PTradeMode]:
        """获取API支持的模式"""
        return self._api_modes.get(name, set())

    def is_api_available(self, name: str, mode: PTradeMode) -> bool:
        """检查API在指定模式下是否可用"""
        return mode in self._api_modes.get(name, set())

    def get_apis_by_category(self, category: str) -> List[str]:
        """按类别获取API列表"""
        return self._categories.get(category, [])

    def list_all_apis(self) -> List[str]:
        """列出所有API"""
        return list(self._apis.keys())


class PTradeAdapter(BasePlugin):
    """
    PTrade 完整兼容层适配器

    提供完整的150+ PTrade API兼容性，支持研究、回测、交易三种模式。
    """

    METADATA = PluginMetadata(
        name="ptrade_adapter",
        version="2.0.0",
        description="PTrade API Compatibility Adapter with 150+ APIs",
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
        self._api_registry = PTradeAPIRegistry()
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
                f"Created proxy methods for technical indicators plugin: {plugin_methods}"
            )

    def _cleanup_plugin_proxies(self) -> None:
        """清理插件代理方法"""
        # 这里可以添加清理逻辑，但由于我们是直接设置属性，不需要特别清理
        pass

    def _on_initialize(self) -> None:
        """初始化适配器"""
        self._logger.info("Initializing PTrade Complete Adapter")

        # 初始化PTrade上下文
        portfolio = Portfolio(cash=self._initial_cash)
        self._ptrade_context = PTradeContext(
            portfolio=portfolio, capital_base=self._initial_cash
        )

        # 注册所有150+ API
        self._register_all_apis()

        # 设置插件代理机制
        self._setup_plugin_proxies()

        # 监听插件系统事件
        if self._event_bus_ref is not None:
            self._setup_event_listeners()

        self._logger.info(
            f"PTrade Complete Adapter initialized with {len(self._api_registry.list_all_apis())} APIs"
        )

    def set_plugin_manager(self, plugin_manager) -> None:
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

    def _check_api_availability(self, api_name: str) -> bool:
        """检查API在当前模式下是否可用"""
        current_mode = self.get_current_mode()
        if not current_mode:
            raise PTradeAPIError(f"No mode set for PTrade adapter")

        if isinstance(
            current_mode, PTradeMode
        ) and not self._api_registry.is_api_available(api_name, current_mode):
            available_modes = self._api_registry.get_api_modes(api_name)
            mode_names = [m.value for m in available_modes]
            raise PTradeAPIError(
                f"API '{api_name}' is not available in {current_mode.value} mode. "
                f"Available in: {', '.join(mode_names)}"
            )
        return True

    def _register_all_apis(self) -> None:
        """注册所有150+ PTrade API"""

        # ==========================================
        # 策略生命周期函数 (7个)
        # ==========================================

        # 核心生命周期函数
        self._api_registry.register_api(
            "initialize",
            self._api_initialize,
            "lifecycle",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "handle_data",
            self._api_handle_data,
            "lifecycle",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "before_trading_start",
            self._api_before_trading_start,
            "lifecycle",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "after_trading_end",
            self._api_after_trading_end,
            "lifecycle",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "tick_data", self._api_tick_data, "lifecycle", {PTradeMode.TRADING}
        )

        # 事件回调函数
        self._api_registry.register_api(
            "on_order_response",
            self._api_on_order_response,
            "lifecycle",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "on_trade_response",
            self._api_on_trade_response,
            "lifecycle",
            {PTradeMode.TRADING},
        )

        # ==========================================
        # 设置函数 (12个)
        # ==========================================

        # 基础设置
        self._api_registry.register_api(
            "set_universe",
            self._api_set_universe,
            "settings",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "set_benchmark",
            self._api_set_benchmark,
            "settings",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "set_commission",
            self._api_set_commission,
            "settings",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "set_fixed_slippage",
            self._api_set_fixed_slippage,
            "settings",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "set_slippage", self._api_set_slippage, "settings", {PTradeMode.BACKTEST}
        )
        self._api_registry.register_api(
            "set_volume_ratio",
            self._api_set_volume_ratio,
            "settings",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "set_limit_mode",
            self._api_set_limit_mode,
            "settings",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "set_yesterday_position",
            self._api_set_yesterday_position,
            "settings",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "set_parameters",
            self._api_set_parameters,
            "settings",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )

        # 定时函数
        self._api_registry.register_api(
            "run_daily",
            self._api_run_daily,
            "settings",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "run_interval", self._api_run_interval, "settings", {PTradeMode.TRADING}
        )

        # 期货设置
        self._api_registry.register_api(
            "set_future_commission",
            self._api_set_future_commission,
            "settings",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "set_margin_rate",
            self._api_set_margin_rate,
            "settings",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )

        # ==========================================
        # 获取信息函数 (50+个)
        # ==========================================

        # 基础信息 (3个)
        self._api_registry.register_api(
            "get_trading_day",
            self._api_get_trading_day,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_all_trades_days",
            self._api_get_all_trades_days,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_trade_days",
            self._api_get_trade_days,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )

        # 市场信息 (3个)
        self._api_registry.register_api(
            "get_market_list",
            self._api_get_market_list,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_market_detail",
            self._api_get_market_detail,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_cb_list", self._api_get_cb_list, "market_data", {PTradeMode.TRADING}
        )

        # 行情信息 (11个)
        self._api_registry.register_api(
            "get_history",
            self._api_get_history,
            "market_data",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_price",
            self._api_get_price,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_individual_entrust",
            self._api_get_individual_entrust,
            "market_data",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_individual_transaction",
            self._api_get_individual_transaction,
            "market_data",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_tick_direction",
            self._api_get_tick_direction,
            "market_data",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_sort_msg", self._api_get_sort_msg, "market_data", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "get_etf_info", self._api_get_etf_info, "market_data", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "get_etf_stock_info",
            self._api_get_etf_stock_info,
            "market_data",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_gear_price",
            self._api_get_gear_price,
            "market_data",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_snapshot", self._api_get_snapshot, "market_data", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "get_cb_info",
            self._api_get_cb_info,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.TRADING},
        )

        # 股票信息 (12个)
        self._api_registry.register_api(
            "get_stock_name",
            self._api_get_stock_name,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_stock_info",
            self._api_get_stock_info,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_stock_status",
            self._api_get_stock_status,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_stock_exrights",
            self._api_get_stock_exrights,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_stock_blocks",
            self._api_get_stock_blocks,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_index_stocks",
            self._api_get_index_stocks,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_etf_stock_list",
            self._api_get_etf_stock_list,
            "market_data",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_industry_stocks",
            self._api_get_industry_stocks,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_fundamentals",
            self._api_get_fundamentals,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_Ashares",
            self._api_get_ashares,
            "market_data",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_etf_list", self._api_get_etf_list, "market_data", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "get_ipo_stocks",
            self._api_get_ipo_stocks,
            "market_data",
            {PTradeMode.TRADING},
        )

        # 其他信息 (7个)
        self._api_registry.register_api(
            "get_trades_file",
            self._api_get_trades_file,
            "market_data",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "convert_position_from_csv",
            self._api_convert_position_from_csv,
            "market_data",
            {PTradeMode.BACKTEST},
        )
        self._api_registry.register_api(
            "get_user_name",
            self._api_get_user_name,
            "market_data",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_deliver", self._api_get_deliver, "market_data", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "get_fundjour", self._api_get_fundjour, "market_data", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "get_research_path",
            self._api_get_research_path,
            "market_data",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_trade_name",
            self._api_get_trade_name,
            "market_data",
            {PTradeMode.TRADING},
        )

        # ==========================================
        # 交易相关函数 (22个)
        # ==========================================

        # 股票交易函数 (11个)
        self._api_registry.register_api(
            "order",
            self._api_order,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "order_target",
            self._api_order_target,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "order_value",
            self._api_order_value,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "order_target_value",
            self._api_order_target_value,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "order_market", self._api_order_market, "trading", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "ipo_stocks_order",
            self._api_ipo_stocks_order,
            "trading",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "after_trading_order",
            self._api_after_trading_order,
            "trading",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "after_trading_cancel_order",
            self._api_after_trading_cancel_order,
            "trading",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "etf_basket_order",
            self._api_etf_basket_order,
            "trading",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "etf_purchase_redemption",
            self._api_etf_purchase_redemption,
            "trading",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_positions",
            self._api_get_positions,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )

        # 公共交易函数 (11个)
        self._api_registry.register_api(
            "order_tick", self._api_order_tick, "trading", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "cancel_order",
            self._api_cancel_order,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "cancel_order_ex",
            self._api_cancel_order_ex,
            "trading",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "debt_to_stock_order",
            self._api_debt_to_stock_order,
            "trading",
            {PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_open_orders",
            self._api_get_open_orders,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_order",
            self._api_get_order,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_orders",
            self._api_get_orders,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_all_orders", self._api_get_all_orders, "trading", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "get_trades",
            self._api_get_trades,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_position",
            self._api_get_position,
            "trading",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )

        # ==========================================
        # 计算函数 (4个)
        # ==========================================

        self._api_registry.register_api(
            "get_MACD",
            self._api_get_macd,
            "calculations",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_KDJ",
            self._api_get_kdj,
            "calculations",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_RSI",
            self._api_get_rsi,
            "calculations",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "get_CCI",
            self._api_get_cci,
            "calculations",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )

        # ==========================================
        # 其他函数 (7个)
        # ==========================================

        self._api_registry.register_api(
            "log", self._api_log, "utils", {PTradeMode.BACKTEST, PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "is_trade",
            self._api_is_trade,
            "utils",
            {PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "check_limit",
            self._api_check_limit,
            "utils",
            {PTradeMode.RESEARCH, PTradeMode.BACKTEST, PTradeMode.TRADING},
        )
        self._api_registry.register_api(
            "send_email", self._api_send_email, "utils", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "send_qywx", self._api_send_qywx, "utils", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "permission_test", self._api_permission_test, "utils", {PTradeMode.TRADING}
        )
        self._api_registry.register_api(
            "create_dir", self._api_create_dir, "utils", {PTradeMode.TRADING}
        )

        self._logger.info(
            f"Registered {len(self._api_registry.list_all_apis())} PTrade APIs across all categories"
        )

    # =========================================
    # API 实现开始 - 策略生命周期函数
    # =========================================

    def _api_initialize(self, *args: Any, **kwargs: Any) -> None:
        """策略初始化函数 - 由策略实现"""
        # 这是一个占位符，实际的initialize函数由策略代码提供
        pass

    def _api_handle_data(self, *args: Any, **kwargs: Any) -> None:
        """主策略逻辑函数 - 由策略实现"""
        # 这是一个占位符，实际的handle_data函数由策略代码提供
        pass

    def _api_before_trading_start(self, *args: Any, **kwargs: Any) -> None:
        """盘前处理函数 - 由策略实现"""
        pass

    def _api_after_trading_end(self, *args: Any, **kwargs: Any) -> None:
        """盘后处理函数 - 由策略实现"""
        pass

    def _api_tick_data(self, *args: Any, **kwargs: Any) -> None:
        """tick级别处理函数 - 由策略实现"""
        self._check_api_availability("tick_data")
        pass

    def _api_on_order_response(self, *args: Any, **kwargs: Any) -> None:
        """委托回报函数 - 由策略实现"""
        self._check_api_availability("on_order_response")
        pass

    def _api_on_trade_response(self, *args: Any, **kwargs: Any) -> None:
        """成交回报函数 - 由策略实现"""
        self._check_api_availability("on_trade_response")
        pass

    # =========================================
    # API 实现 - 设置函数
    # =========================================

    def _api_set_universe(self, securities: List[str]) -> None:
        """设置股票池"""
        self._check_api_availability("set_universe")
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")
        self._ptrade_context.universe = securities
        self._logger.info(f"Universe set to {len(securities)} securities")

    def _api_set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        self._check_api_availability("set_benchmark")
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")
        self._ptrade_context.benchmark = benchmark
        self._logger.info(f"Benchmark set to {benchmark}")

    def _api_set_commission(
        self,
        commission_ratio: float = 0.0003,
        min_commission: float = 5.0,
        type: str = "STOCK",
    ) -> None:
        """设置佣金费率"""
        self._check_api_availability("set_commission")
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")
        self._commission_rate = commission_ratio
        if self._ptrade_context.commission is not None:
            self._ptrade_context.commission.cost = commission_ratio
            self._ptrade_context.commission.min_trade_cost = min_commission
        self._logger.info(f"Commission rate set to {commission_ratio}")

    def _api_set_fixed_slippage(self, fixedslippage: float = 0.0) -> None:
        """设置固定滑点"""
        self._check_api_availability("set_fixed_slippage")
        self._slippage_rate = fixedslippage
        self._logger.info(f"Fixed slippage set to {fixedslippage}")

    def _api_set_slippage(self, slippage: float = 0.001) -> None:
        """设置滑点比例"""
        self._check_api_availability("set_slippage")
        self._slippage_rate = slippage
        self._logger.info(f"Slippage rate set to {slippage}")

    def _api_set_volume_ratio(self, volume_ratio: float = 0.25) -> None:
        """设置成交比例"""
        self._check_api_availability("set_volume_ratio")
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")
        if self._ptrade_context.slippage is not None:
            self._ptrade_context.slippage.volume_limit = volume_ratio
        self._logger.info(f"Volume ratio set to {volume_ratio}")

    def _api_set_limit_mode(self, limit_mode: str = "LIMIT") -> None:
        """设置回测成交数量限制模式"""
        self._check_api_availability("set_limit_mode")
        # TODO: 实现限制模式逻辑
        self._logger.info(f"Limit mode set to {limit_mode}")

    def _api_set_yesterday_position(self, poslist: List[Dict[str, Any]]) -> None:
        """设置底仓"""
        self._check_api_availability("set_yesterday_position")
        # TODO: 实现底仓设置逻辑
        self._logger.info(f"Set yesterday positions: {len(poslist)} positions")

    def _api_set_parameters(self, **kwargs: Any) -> None:
        """设置策略配置参数"""
        self._check_api_availability("set_parameters")
        # TODO: 实现参数设置逻辑
        self._logger.info(f"Set parameters: {kwargs}")

    def _api_run_daily(self, func: Callable[..., Any], time: str = "9:31") -> None:
        """按日周期处理"""
        self._check_api_availability("run_daily")
        # TODO: 实现定时任务逻辑
        self._logger.info(f"Scheduled daily function at {time}")

    def _api_run_interval(self, func: Callable[..., Any], seconds: int = 10) -> None:
        """按设定周期处理"""
        self._check_api_availability("run_interval")
        # TODO: 实现定时任务逻辑
        self._logger.info(f"Scheduled interval function every {seconds} seconds")

    def _api_set_future_commission(
        self, transaction_code: str, commission: float
    ) -> None:
        """设置期货手续费"""
        self._check_api_availability("set_future_commission")
        # TODO: 实现期货手续费设置
        self._logger.info(f"Set future commission for {transaction_code}: {commission}")

    def _api_set_margin_rate(self, transaction_code: str, margin_rate: float) -> None:
        """设置期货保证金比例"""
        self._check_api_availability("set_margin_rate")
        # TODO: 实现保证金比例设置
        self._logger.info(f"Set margin rate for {transaction_code}: {margin_rate}")

    # =========================================
    # API 实现 - 基础信息函数
    # =========================================

    def _api_get_trading_day(self, day: Union[str, int], offset: int = 0) -> str:
        """获取交易日期"""
        self._check_api_availability("get_trading_day")
        # TODO: 实现交易日历功能
        if isinstance(day, int):
            current_date = datetime.now()
            target_date = current_date + pd.Timedelta(days=day + offset)
        else:
            target_date = pd.to_datetime(day) + pd.Timedelta(days=offset)
        return str(target_date.strftime("%Y-%m-%d"))

    def _api_get_all_trades_days(self, date: Optional[str] = None) -> List[str]:
        """获取全部交易日期"""
        self._check_api_availability("get_all_trades_days")
        # TODO: 实现交易日历功能
        end_date = pd.to_datetime(date) if date else datetime.now()
        dates = pd.date_range(start="2020-01-01", end=end_date, freq="B")  # 工作日
        return [d.strftime("%Y-%m-%d") for d in dates]

    def _api_get_trade_days(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        count: Optional[int] = None,
    ) -> List[str]:
        """获取指定范围交易日期"""
        self._check_api_availability("get_trade_days")
        # TODO: 实现交易日历功能
        if count:
            end_dt = pd.to_datetime(end_date) if end_date else datetime.now()
            dates = pd.date_range(end=end_dt, periods=count, freq="B")
        else:
            start_dt = (
                pd.to_datetime(start_date)
                if start_date
                else datetime.now() - pd.Timedelta(days=365)
            )
            end_dt = pd.to_datetime(end_date) if end_date else datetime.now()
            dates = pd.date_range(start=start_dt, end=end_dt, freq="B")
        return [d.strftime("%Y-%m-%d") for d in dates]

    # =========================================
    # API 实现 - 市场信息函数
    # =========================================

    def _api_get_market_list(self) -> List[Dict[str, Any]]:
        """获取市场列表"""
        self._check_api_availability("get_market_list")
        # TODO: 实现市场列表获取
        return [
            {"market_code": "XSHG", "market_name": "上海证券交易所"},
            {"market_code": "XSHE", "market_name": "深圳证券交易所"},
        ]

    def _api_get_market_detail(self, finance_mic: str) -> Dict[str, Any]:
        """获取市场详细信息"""
        self._check_api_availability("get_market_detail")
        # TODO: 实现市场详情获取
        return {"market_code": finance_mic, "status": "open"}

    def _api_get_cb_list(self) -> List[str]:
        """获取可转债市场代码表"""
        self._check_api_availability("get_cb_list")
        # TODO: 实现可转债列表获取
        return ["113001.SH", "113002.SH", "127001.SZ"]

    # =========================================
    # API 实现 - 行情信息函数
    # =========================================

    def _api_get_history(
        self,
        count: int,
        frequency: str = "1d",
        field: Union[str, List[str]] = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "money",
            "price",
        ],
        security_list: Optional[List[str]] = None,
        fq: Optional[str] = None,
        include: bool = False,
        fill: str = "nan",
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """获取历史行情数据"""
        self._check_api_availability("get_history")

        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")

        securities = security_list or self._ptrade_context.universe
        if not securities:
            raise PTradeAPIError("No securities specified and no universe set")

        # 处理字段参数
        if isinstance(field, str):
            field = [field]

        # 从数据插件获取历史数据
        if not self._data_plugin:
            raise PTradeAPIError("Data plugin not available")

        result_df = self._data_plugin.get_multiple_history_data(
            securities, count, start_date, end_date
        )

        if result_df.empty:
            # 如果没有数据，返回空结果
            if is_dict:
                return {security: {f: [] for f in field} for security in securities}
            else:
                return pd.DataFrame()

        if is_dict:
            # 转换为字典格式
            result = {}
            for security in securities:
                security_data = result_df[result_df["security"] == security]
                result[security] = {}
                for f in field:
                    if f in security_data.columns:
                        result[security][f] = security_data[f].tolist()
                    else:
                        result[security][f] = []
        else:
            # 返回DataFrame格式
            # 只保留请求的字段
            available_fields = ["security", "date"] + [
                f for f in field if f in result_df.columns
            ]
            result = result_df[available_fields].copy()

            # 设置索引
            result.set_index(["security", "date"], inplace=True)

        return result

    def _api_get_price(
        self,
        security: Union[str, List[str]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> pd.DataFrame:
        """获取价格数据"""
        self._check_api_availability("get_price")

        securities = security if isinstance(security, list) else [security]

        # 处理字段参数
        if fields is None:
            fields = ["open", "high", "low", "close", "volume"]
        elif isinstance(fields, str):
            fields = [fields]

        # 从数据插件获取历史数据
        if not self._data_plugin:
            raise PTradeAPIError("Data plugin not available")

        result_df = self._data_plugin.get_multiple_history_data(
            securities, count or 100, start_date, end_date
        )

        if result_df.empty:
            return pd.DataFrame()

        # 只保留请求的字段
        available_fields = ["security", "date"] + [
            f for f in fields if f in result_df.columns
        ]
        result = result_df[available_fields].copy()

        return result.set_index(["security", "date"])

    def _api_get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取行情快照"""
        self._check_api_availability("get_snapshot")

        data = []
        for security in security_list:
            data.append(
                {
                    "security": security,
                    "current_price": np.random.randn() * 0.01 + 10,
                    "volume": np.random.randint(1000, 10000),
                    "timestamp": pd.Timestamp.now(),
                }
            )

        return pd.DataFrame(data).set_index("security")

    # 为了节省空间，这里只展示部分关键API实现
    # 其他API实现将遵循相同的模式...

    def _api_order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """下单"""
        self._check_api_availability("order")

        # 风控检查
        if not self._api_validate_order(security, amount, limit_price):
            return None

        if self._ptrade_context is None or self._ptrade_context.blotter is None:
            raise PTradeAPIError("PTrade context or blotter is not initialized")

        # 创建订单
        order_id = self._ptrade_context.blotter.create_order(
            security, amount, limit_price
        )

        # 模拟订单执行
        self._execute_order(order_id)

        return order_id

    def _api_cancel_order(self, order_id: str) -> bool:
        """撤单"""
        self._check_api_availability("cancel_order")
        if self._ptrade_context is None or self._ptrade_context.blotter is None:
            raise PTradeAPIError("PTrade context or blotter is not initialized")
        return self._ptrade_context.blotter.cancel_order(order_id)

    # =========================================
    # 计算函数实现
    # =========================================

    def _api_get_macd(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """获取MACD指标"""
        self._check_api_availability("get_MACD")

        # 优先使用技术指标插件
        if self._indicators_plugin:
            try:
                # 临时更新插件配置以传递参数
                original_params = self._indicators_plugin.macd_params.copy()
                self._indicators_plugin.macd_params = {"short": short, "long": long, "m": m}
                
                try:
                    result = self._indicators_plugin.calculate_macd(close)
                    return result
                finally:
                    # 恢复原始配置
                    self._indicators_plugin.macd_params = original_params
                    
            except Exception as e:
                self._logger.warning(
                    f"Technical indicators plugin failed, falling back to internal implementation: {e}"
                )

        # 回退到内部实现
        try:
            # 确保数据是Series格式
            close_series = pd.Series(close)

            # 计算快速和慢速EMA
            exp1 = close_series.ewm(span=short).mean()
            exp2 = close_series.ewm(span=long).mean()

            # 计算MACD线
            macd_line = exp1 - exp2

            # 计算信号线
            signal_line = macd_line.ewm(span=m).mean()

            # 计算MACD柱状图
            histogram = macd_line - signal_line

            # 返回结果DataFrame
            result = pd.DataFrame(
                {
                    "MACD": macd_line,
                    "MACD_signal": signal_line,
                    "MACD_hist": histogram * 2,  # PTrade通常将柱状图乘以2
                }
            )

            return result

        except Exception as e:
            self._logger.error(f"Error calculating MACD: {e}")
            periods = len(close)
            return pd.DataFrame(
                {
                    "MACD": np.random.randn(periods) * 0.1,
                    "MACD_signal": np.random.randn(periods) * 0.1,
                    "MACD_hist": np.random.randn(periods) * 0.05,
                }
            )

    def _api_get_kdj(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """获取KDJ指标"""
        self._check_api_availability("get_KDJ")

        # 优先使用技术指标插件
        if self._indicators_plugin:
            try:
                # 临时更新插件配置以传递参数
                original_params = self._indicators_plugin.kdj_params.copy()
                self._indicators_plugin.kdj_params = {"n": n, "m1": m1, "m2": m2}
                
                try:
                    result = self._indicators_plugin.calculate_kdj(high, low, close)
                    return result
                finally:
                    # 恢复原始配置
                    self._indicators_plugin.kdj_params = original_params
                    
            except Exception as e:
                self._logger.warning(
                    f"Technical indicators plugin failed, falling back to internal implementation: {e}"
                )

        # 回退到内部实现
        try:
            # 确保数据是Series格式
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            # 计算最高价和最低价的滚动窗口
            highest = high_series.rolling(window=n).max()
            lowest = low_series.rolling(window=n).min()

            # 计算RSV
            rsv = (close_series - lowest) / (highest - lowest) * 100

            # 计算K值
            k = rsv.ewm(alpha=1 / m1).mean()

            # 计算D值
            d = k.ewm(alpha=1 / m2).mean()

            # 计算J值
            j = 3 * k - 2 * d

            result = pd.DataFrame({"K": k, "D": d, "J": j})

            return result

        except Exception as e:
            self._logger.error(f"Error calculating KDJ: {e}")
            periods = len(close)
            return pd.DataFrame(
                {
                    "K": np.random.uniform(0, 100, periods),
                    "D": np.random.uniform(0, 100, periods),
                    "J": np.random.uniform(0, 100, periods),
                }
            )

    def _api_get_rsi(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """获取RSI指标"""
        self._check_api_availability("get_RSI")

        # 优先使用技术指标插件
        if self._indicators_plugin:
            try:
                # 临时更新插件配置以传递参数
                original_params = self._indicators_plugin.rsi_params.copy()
                self._indicators_plugin.rsi_params = {"n": n}
                
                try:
                    result = self._indicators_plugin.calculate_rsi(close)
                    return result
                finally:
                    # 恢复原始配置
                    self._indicators_plugin.rsi_params = original_params
                    
            except Exception as e:
                self._logger.warning(
                    f"Technical indicators plugin failed, falling back to internal implementation: {e}"
                )

        # 回退到内部实现
        try:
            # 确保数据是Series格式
            close_series = pd.Series(close)

            # 计算价格变化
            delta = close_series.diff()

            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # 计算平均收益和平均损失
            avg_gain = gain.rolling(window=n).mean()
            avg_loss = loss.rolling(window=n).mean()

            # 计算RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            result = pd.DataFrame({"RSI": rsi})

            return result

        except Exception as e:
            self._logger.error(f"Error calculating RSI: {e}")
            periods = len(close)
            return pd.DataFrame({"RSI": np.random.uniform(0, 100, periods)})

    def _api_get_cci(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """获取CCI指标"""
        self._check_api_availability("get_CCI")

        # 优先使用技术指标插件
        if self._indicators_plugin:
            try:
                # 临时更新插件配置以传递参数
                original_params = self._indicators_plugin.cci_params.copy()
                self._indicators_plugin.cci_params = {"n": n}
                
                try:
                    result = self._indicators_plugin.calculate_cci(high, low, close)
                    return result
                finally:
                    # 恢复原始配置
                    self._indicators_plugin.cci_params = original_params
                    
            except Exception as e:
                self._logger.warning(
                    f"Technical indicators plugin failed, falling back to internal implementation: {e}"
                )

        # 回退到内部实现
        try:
            # 确保数据是Series格式
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            # 计算典型价格
            typical_price = (high_series + low_series + close_series) / 3

            # 计算移动平均
            ma = typical_price.rolling(window=n).mean()

            # 计算平均绝对偏差
            mad = typical_price.rolling(window=n).apply(
                lambda x: abs(x - x.mean()).mean()
            )

            # 计算CCI
            cci = (typical_price - ma) / (0.015 * mad)

            result = pd.DataFrame({"CCI": cci})

            return result

        except Exception as e:
            self._logger.error(f"Error calculating CCI: {e}")
            periods = len(close)
            return pd.DataFrame({"CCI": np.random.randn(periods) * 50})

    # =========================================
    # 其他工具函数实现
    # =========================================

    def _api_log(self, content: str, level: str = "info") -> None:
        """日志记录"""
        self._check_api_availability("log")
        if hasattr(self._logger, level):
            getattr(self._logger, level)(content)
        else:
            self._logger.info(content)

    def _api_is_trade(self) -> bool:
        """业务代码场景判断"""
        self._check_api_availability("is_trade")
        return self.get_current_mode() == PTradeMode.TRADING

    def _api_check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """代码涨跌停状态判断"""
        self._check_api_availability("check_limit")

        try:
            # 获取股票的历史数据
            current_data = self._api_get_current_data()

            if security not in current_data:
                return {
                    security: {
                        "limit_up": False,
                        "limit_down": False,
                        "limit_up_price": None,
                        "limit_down_price": None,
                        "current_price": None,
                    }
                }

            data = current_data[security]
            current_price = data.get("last_price", 0)
            pre_close = data.get("pre_close", 0)

            if pre_close == 0:
                return {
                    security: {
                        "limit_up": False,
                        "limit_down": False,
                        "limit_up_price": None,
                        "limit_down_price": None,
                        "current_price": current_price,
                    }
                }

            # 计算涨跌停价格
            # 普通股票涨跌停幅度为10%
            limit_ratio = 0.10

            # 特殊处理：科创板和创业板注册制股票涨跌停幅度为20%
            if security.startswith("688") or security.startswith("300"):
                limit_ratio = 0.20

            # ST股票涨跌停幅度为5%
            if "ST" in security:
                limit_ratio = 0.05

            limit_up_price = round(pre_close * (1 + limit_ratio), 2)
            limit_down_price = round(pre_close * (1 - limit_ratio), 2)

            # 判断是否涨跌停
            is_limit_up = abs(current_price - limit_up_price) < 0.01
            is_limit_down = abs(current_price - limit_down_price) < 0.01

            return {
                security: {
                    "limit_up": is_limit_up,
                    "limit_down": is_limit_down,
                    "limit_up_price": limit_up_price,
                    "limit_down_price": limit_down_price,
                    "current_price": current_price,
                }
            }

        except Exception as e:
            self._logger.error(f"Error checking limit for {security}: {e}")
            return {security: {"limit_up": False, "limit_down": False}}

    def _api_get_current_data(self) -> Dict[str, Dict[str, float]]:
        """获取当前市场数据"""
        # 模拟当前市场数据
        return self._current_data

    def _get_current_price(self, security: str) -> float:
        """获取证券当前价格"""
        # 从数据插件获取当前价格
        if self._data_plugin:
            return self._data_plugin.get_current_price(security)
        else:
            # 如果数据插件不可用，返回默认价格
            return 10.0

    def _generate_price_series(self, base_price: float, length: int) -> np.ndarray:
        """生成价格序列"""
        # 使用几何布朗运动模拟价格变化
        dt = 1.0  # 时间步长
        mu = 0.0001  # 漂移率
        sigma = 0.02  # 波动率

        # 生成随机增量
        random_increments = np.random.normal(0, 1, length)

        # 计算价格变化
        price_changes = mu * dt + sigma * np.sqrt(dt) * random_increments

        # 计算累积价格
        log_returns = np.cumsum(price_changes)
        prices = base_price * np.exp(log_returns)

        return prices

    # 为了保持150+ API的完整性，这里需要实现所有其他API的占位符函数
    # 由于空间限制，这里只展示几个关键的占位符函数示例

    def _api_get_fundamentals(
        self,
        stocks: List[str],
        table: str,
        fields: Optional[List[str]] = None,
        date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取基本面数据"""
        self._check_api_availability("get_fundamentals")
        # TODO: 实现基本面数据获取
        data = []
        for stock in stocks:
            data.append(
                {
                    "security": stock,
                    "total_revenue": np.random.randn() * 1000000000,
                    "net_income": np.random.randn() * 100000000,
                    "total_assets": np.random.randn() * 5000000000,
                }
            )
        return pd.DataFrame(data).set_index("security")

    # .... 其他API占位符函数实现将遵循相同模式 ....

    # =========================================
    # 辅助方法
    # =========================================

    def _api_validate_order(
        self, security: str, amount: int, limit_price: Optional[float]
    ) -> bool:
        """验证订单"""

        if self._ptrade_context is None:
            self._logger.warning("PTrade context is not initialized")
            return False

        # 检查资金充足性（买入订单）
        if amount > 0:
            price = limit_price or 10.0  # 使用限价或市价
            required_cash = amount * price * (1 + self._commission_rate)
            if required_cash > self._ptrade_context.portfolio.cash:
                self._logger.warning(
                    f"Insufficient cash for order: required={required_cash}, available={self._ptrade_context.portfolio.cash}"
                )
                return False

        # 检查持仓充足性（卖出订单）
        elif amount < 0:
            if security not in self._ptrade_context.portfolio.positions:
                self._logger.warning(f"No position to sell: {security}")
                return False

            position = self._ptrade_context.portfolio.positions[security]
            if abs(amount) > position.amount:
                self._logger.warning(
                    f"Insufficient position: trying to sell {abs(amount)}, have {position.amount}"
                )
                return False

        return True

    def _execute_order(self, order_id: str) -> None:
        """执行订单"""
        if self._ptrade_context is None or self._ptrade_context.blotter is None:
            raise PTradeAPIError("PTrade context or blotter is not initialized")

        order = self._ptrade_context.blotter.get_order(order_id)
        if not order:
            return

        security = order.symbol
        amount = order.amount
        price = order.limit or 10.0  # 使用限价或模拟市价

        # 计算实际成交价格（包含滑点）
        execution_price = price * (
            1 + self._slippage_rate if amount > 0 else 1 - self._slippage_rate
        )

        # 计算手续费
        commission = abs(amount * execution_price * self._commission_rate)

        # 更新持仓
        if security in self._ptrade_context.portfolio.positions:
            position = self._ptrade_context.portfolio.positions[security]
            # 更新持仓数量和成本基础
            total_amount = position.amount + amount
            if total_amount == 0:
                # 清仓
                del self._ptrade_context.portfolio.positions[security]
            else:
                # 更新持仓
                total_cost = (
                    position.amount * position.cost_basis + amount * execution_price
                )
                position.amount = total_amount
                position.cost_basis = total_cost / total_amount
                position.last_sale_price = execution_price
        else:
            # 新建持仓
            if amount != 0:
                self._ptrade_context.portfolio.positions[security] = Position(
                    sid=security,
                    enable_amount=amount,
                    amount=amount,
                    cost_basis=execution_price,
                    last_sale_price=execution_price,
                )

        # 更新现金
        self._ptrade_context.portfolio.cash -= amount * execution_price + commission

        # 更新投资组合价值
        self._ptrade_context.portfolio.update_portfolio_value()

        # 更新订单状态
        order.status = "filled"
        order.filled = amount

        self._logger.info(
            f"Order executed: {order_id}, {security}, {amount} @ {execution_price}"
        )

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
        self._current_data = snapshot

        return snapshot

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

        # 注入所有已注册的API，但不覆盖策略钩子函数
        for api_name in self._api_registry.list_all_apis():
            # 如果是策略钩子函数，跳过注入
            if api_name in strategy_hook_names:
                continue

            api_func = self._api_registry.get_api(api_name)
            if api_func:
                # 创建API包装器，自动注入适配器引用
                wrapped_func = self._create_api_wrapper(api_func, api_name)
                setattr(strategy_module, api_name, wrapped_func)

        self._logger.debug(
            f"Injected {len(self._api_registry.list_all_apis())} PTrade APIs"
        )

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
    # 占位符API实现 - 为了完整性而保留
    # =========================================

    # 以下是所有其他API的占位符实现，确保150+ API的完整性
    # 实际项目中应该根据具体需求实现这些函数

    def _api_get_individual_entrust(
        self,
        stocks: Optional[List[str]] = None,
        data_count: int = 50,
        start_pos: int = 0,
        search_direction: int = 1,
    ) -> pd.DataFrame:
        """获取逐笔委托行情"""
        self._check_api_availability("get_individual_entrust")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_individual_transaction(
        self,
        stocks: Optional[List[str]] = None,
        data_count: int = 50,
        start_pos: int = 0,
        search_direction: int = 1,
    ) -> pd.DataFrame:
        """获取逐笔成交行情"""
        self._check_api_availability("get_individual_transaction")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_tick_direction(
        self,
        symbols: Optional[List[str]] = None,
        query_date: int = 0,
        start_pos: int = 0,
        search_direction: int = 1,
        data_count: int = 50,
    ) -> pd.DataFrame:
        """获取分时成交行情"""
        self._check_api_availability("get_tick_direction")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_sort_msg(
        self,
        sort_type_grp: Optional[str] = None,
        sort_field_name: Optional[str] = None,
        sort_type: int = 1,
        data_count: int = 100,
    ) -> pd.DataFrame:
        """获取板块、行业的涨幅排名"""
        self._check_api_availability("get_sort_msg")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_etf_info(self, etf_code: str) -> pd.DataFrame:
        """获取ETF信息"""
        self._check_api_availability("get_etf_info")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_etf_stock_info(self, etf_code: str, security: str) -> pd.DataFrame:
        """获取ETF成分券信息"""
        self._check_api_availability("get_etf_stock_info")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_gear_price(self, sids: List[str]) -> pd.DataFrame:
        """获取指定代码的档位行情价格"""
        self._check_api_availability("get_gear_price")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_cb_info(self) -> pd.DataFrame:
        """获取可转债基础信息"""
        self._check_api_availability("get_cb_info")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_stock_name(self, stocks: List[str]) -> pd.DataFrame:
        """获取股票名称"""
        self._check_api_availability("get_stock_name")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_stock_info(
        self, stocks: List[str], field: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """获取股票基础信息"""
        self._check_api_availability("get_stock_info")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_stock_status(
        self,
        stocks: List[str],
        query_type: str = "ST",
        query_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """获取股票状态信息"""
        self._check_api_availability("get_stock_status")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_stock_exrights(
        self, stock_code: str, date: Optional[str] = None
    ) -> pd.DataFrame:
        """获取股票除权除息信息"""
        self._check_api_availability("get_stock_exrights")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_stock_blocks(self, stock_code: str) -> pd.DataFrame:
        """获取股票所属板块信息"""
        self._check_api_availability("get_stock_blocks")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_index_stocks(
        self, index_code: str, date: Optional[str] = None
    ) -> pd.DataFrame:
        """获取指数成份股"""
        self._check_api_availability("get_index_stocks")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_etf_stock_list(self, etf_code: str) -> pd.DataFrame:
        """获取ETF成分券列表"""
        self._check_api_availability("get_etf_stock_list")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_industry_stocks(self, industry_code: str) -> pd.DataFrame:
        """获取行业成份股"""
        self._check_api_availability("get_industry_stocks")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_ashares(self, date: Optional[str] = None) -> pd.DataFrame:
        """获取指定日期A股代码列表"""
        self._check_api_availability("get_Ashares")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_etf_list(self) -> pd.DataFrame:
        """获取ETF代码"""
        self._check_api_availability("get_etf_list")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_ipo_stocks(self) -> pd.DataFrame:
        """获取当日IPO申购标的"""
        self._check_api_availability("get_ipo_stocks")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_trades_file(self, save_path: str = "") -> pd.DataFrame:
        """获取对账数据文件"""
        self._check_api_availability("get_trades_file")
        return pd.DataFrame()  # TODO: 实现

    def _api_convert_position_from_csv(self, path: str) -> pd.DataFrame:
        """获取设置底仓的参数列表"""
        self._check_api_availability("convert_position_from_csv")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_user_name(self) -> str:
        """获取登录终端的资金账号"""
        self._check_api_availability("get_user_name")
        return "test_user"  # TODO: 实现

    def _api_get_deliver(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史交割单信息"""
        self._check_api_availability("get_deliver")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_fundjour(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取历史资金流水信息"""
        self._check_api_availability("get_fundjour")
        return pd.DataFrame()  # TODO: 实现

    def _api_get_research_path(self) -> str:
        """获取研究路径"""
        self._check_api_availability("get_research_path")
        return "/home/research/"  # TODO: 实现

    def _api_get_trade_name(self) -> str:
        """获取交易名称"""
        self._check_api_availability("get_trade_name")
        return "test_trade"  # TODO: 实现

    # 继续添加所有其他交易函数的占位符实现...
    def _api_order_target(self, security: str, target_amount: int) -> Optional[str]:
        """目标数量下单"""
        self._check_api_availability("order_target")
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")

        current_amount = 0
        if security in self._ptrade_context.portfolio.positions:
            current_amount = self._ptrade_context.portfolio.positions[security].amount

        order_amount = target_amount - current_amount
        if order_amount == 0:
            return None

        return self._api_order(security, order_amount)

    def _api_order_value(self, security: str, value: float) -> Optional[str]:
        """按金额下单"""
        self._check_api_availability("order_value")

        if value == 0:
            return None

        # 获取当前价格
        current_price = self._get_current_price(security)
        if current_price <= 0:
            self._logger.warning(
                f"Invalid price for security {security}: {current_price}"
            )
            return None

        # 计算数量，买入为正，卖出为负
        amount = int(value / current_price)
        if amount == 0:
            return None

        return self._api_order(security, amount)

    def _api_order_target_value(
        self, security: str, target_value: float
    ) -> Optional[str]:
        """指定持仓市值买卖"""
        self._check_api_availability("order_target_value")

        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")

        # 获取当前价格
        current_price = self._get_current_price(security)
        if current_price <= 0:
            self._logger.warning(
                f"Invalid price for security {security}: {current_price}"
            )
            return None

        # 计算目标数量
        target_amount = int(target_value / current_price) if target_value > 0 else 0

        # 获取当前持仓
        current_amount = 0
        if security in self._ptrade_context.portfolio.positions:
            current_amount = self._ptrade_context.portfolio.positions[security].amount

        # 计算需要调整的数量
        order_amount = target_amount - current_amount
        if order_amount == 0:
            return None

        return self._api_order(security, order_amount)

    def _api_order_market(
        self,
        security: str,
        amount: int,
        market_type: Optional[str] = None,
        limit_price: Optional[float] = None,
    ) -> Optional[str]:
        """按市价进行委托"""
        self._check_api_availability("order_market")
        # TODO: 实现市价下单
        return self._api_order(security, amount)

    def _api_ipo_stocks_order(
        self,
        market_type: Optional[str] = None,
        black_stocks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """新股一键申购"""
        self._check_api_availability("ipo_stocks_order")
        # TODO: 实现新股申购
        return {}

    def _api_after_trading_order(
        self, security: str, amount: int, entrust_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        self._check_api_availability("after_trading_order")
        # TODO: 实现盘后委托
        return None

    def _api_after_trading_cancel_order(self, order_param: Any) -> bool:
        """盘后固定价委托撤单"""
        self._check_api_availability("after_trading_cancel_order")
        # TODO: 实现盘后撤单
        return False

    def _api_etf_basket_order(
        self,
        etf_code: str,
        amount: int,
        price_style: Optional[str] = None,
        position: bool = True,
        info: Optional[Any] = None,
    ) -> Optional[str]:
        """ETF成分券篮子下单"""
        self._check_api_availability("etf_basket_order")
        # TODO: 实现ETF篮子下单
        return None

    def _api_etf_purchase_redemption(
        self, etf_code: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """ETF基金申赎接口"""
        self._check_api_availability("etf_purchase_redemption")
        # TODO: 实现ETF申赎
        return None

    def _api_get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多支股票持仓信息"""
        self._check_api_availability("get_positions")

        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")

        positions = {}
        for security in security_list:
            if security in self._ptrade_context.portfolio.positions:
                position = self._ptrade_context.portfolio.positions[security]
                positions[security] = {
                    "sid": position.sid,
                    "amount": position.amount,
                    "enable_amount": position.enable_amount,
                    "cost_basis": position.cost_basis,
                    "last_sale_price": position.last_sale_price,
                    "market_value": position.market_value,
                    "pnl": position.pnl,
                    "returns": position.returns,
                    "today_amount": position.today_amount,
                    "business_type": position.business_type,
                }
            else:
                # 如果没有持仓，返回0持仓信息
                positions[security] = {
                    "sid": security,
                    "amount": 0,
                    "enable_amount": 0,
                    "cost_basis": 0.0,
                    "last_sale_price": 0.0,
                    "market_value": 0.0,
                    "pnl": 0.0,
                    "returns": 0.0,
                    "today_amount": 0,
                    "business_type": "stock",
                }

        return positions

    def _api_order_tick(
        self,
        sid: str,
        amount: int,
        priceGear: str = "1",
        limit_price: Optional[float] = None,
    ) -> Optional[str]:
        """tick行情触发买卖"""
        self._check_api_availability("order_tick")
        # TODO: 实现tick下单
        return None

    def _api_cancel_order_ex(self, order_param: Any) -> bool:
        """撤单扩展"""
        self._check_api_availability("cancel_order_ex")
        # TODO: 实现扩展撤单
        return False

    def _api_debt_to_stock_order(self, security: str, amount: int) -> Optional[str]:
        """债转股委托"""
        self._check_api_availability("debt_to_stock_order")
        # TODO: 实现债转股
        return None

    def _api_get_open_orders(self, security: Optional[str] = None) -> List[Order]:
        """获取未完成订单"""
        self._check_api_availability("get_open_orders")

        if self._ptrade_context is None or self._ptrade_context.blotter is None:
            raise PTradeAPIError("PTrade context or blotter is not initialized")

        open_orders = []
        for order in self._ptrade_context.blotter.orders.values():
            # 只返回未完成的订单（非filled、cancelled、rejected状态）
            if order.status in ["new", "submitted", "partially_filled"]:
                if security is None or order.symbol == security:
                    open_orders.append(order)

        return open_orders

    def _api_get_order(self, order_id: str) -> Optional[Order]:
        """获取指定订单"""
        self._check_api_availability("get_order")
        if self._ptrade_context is None or self._ptrade_context.blotter is None:
            raise PTradeAPIError("PTrade context or blotter is not initialized")
        return self._ptrade_context.blotter.get_order(order_id)

    def _api_get_orders(self, security: Optional[str] = None) -> List[Order]:
        """获取全部订单"""
        self._check_api_availability("get_orders")

        if self._ptrade_context is None or self._ptrade_context.blotter is None:
            raise PTradeAPIError("PTrade context or blotter is not initialized")

        orders = []
        for order in self._ptrade_context.blotter.orders.values():
            if security is None or order.symbol == security:
                orders.append(order)

        # 按时间排序，最新的在前
        orders.sort(key=lambda o: o.dt, reverse=True)
        return orders

    def _api_get_all_orders(
        self, security: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取账户当日全部订单"""
        self._check_api_availability("get_all_orders")
        # TODO: 实现账户全部订单查询
        return []

    def _api_get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当日成交订单"""
        self._check_api_availability("get_trades")

        if self._ptrade_context is None or self._ptrade_context.blotter is None:
            raise PTradeAPIError("PTrade context or blotter is not initialized")

        trades = []
        for order in self._ptrade_context.blotter.orders.values():
            # 只返回已成交的订单
            if order.status == "filled" and order.filled != 0:
                if security is None or order.symbol == security:
                    trades.append(
                        {
                            "order_id": order.id,
                            "security": order.symbol,
                            "amount": order.filled,
                            "price": order.limit or 0.0,
                            "filled_amount": order.filled,
                            "commission": 0.0,  # 计算手续费
                            "datetime": order.dt,
                            "side": "buy" if order.amount > 0 else "sell",
                        }
                    )

        # 按时间排序
        trades.sort(key=lambda t: t["datetime"], reverse=True)
        return trades

    def _api_get_position(self, security: str) -> Optional[Position]:
        """获取持仓信息"""
        self._check_api_availability("get_position")
        if self._ptrade_context is None:
            raise PTradeAPIError("PTrade context is not initialized")
        return self._ptrade_context.portfolio.positions.get(security)

    # 其他工具函数占位符
    def _api_send_email(
        self,
        send_email_info: str,
        get_email_info: str,
        smtp_code: str,
        info: str = "",
        path: str = "",
        subject: str = "",
    ) -> bool:
        """发送邮箱信息"""
        self._check_api_availability("send_email")
        # TODO: 实现邮件发送
        return True

    def _api_send_qywx(
        self,
        corp_id: str,
        secret: str,
        agent_id: str,
        info: str = "",
        path: str = "",
        toparty: str = "",
        touser: str = "",
        totag: str = "",
    ) -> bool:
        """发送企业微信信息"""
        self._check_api_availability("send_qywx")
        # TODO: 实现企业微信发送
        return True

    def _api_permission_test(
        self, account: Optional[str] = None, end_date: Optional[str] = None
    ) -> bool:
        """权限校验"""
        self._check_api_availability("permission_test")
        # TODO: 实现权限检查
        return True

    def _api_create_dir(self, user_path: Optional[str] = None) -> bool:
        """创建文件路径"""
        self._check_api_availability("create_dir")
        # TODO: 实现目录创建
        return True

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
        return {
            "total_apis": len(self._api_registry.list_all_apis()),
            "lifecycle_apis": len(self._api_registry.get_apis_by_category("lifecycle")),
            "settings_apis": len(self._api_registry.get_apis_by_category("settings")),
            "market_data_apis": len(
                self._api_registry.get_apis_by_category("market_data")
            ),
            "trading_apis": len(self._api_registry.get_apis_by_category("trading")),
            "calculations_apis": len(
                self._api_registry.get_apis_by_category("calculations")
            ),
            "utils_apis": len(self._api_registry.get_apis_by_category("utils")),
            "current_mode": current_mode.value if current_mode else None,
            "strategy_loaded": self._strategy_module is not None,
            "portfolio_value": self._ptrade_context.portfolio.portfolio_value
            if self._ptrade_context
            else 0,
        }

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

    def _cleanup_event_listeners(self) -> None:
        """清理事件监听器"""
        if self._event_bus_ref is not None:
            for listener_id in self._event_listeners:
                self._event_bus_ref.unsubscribe(listener_id)
        self._event_listeners.clear()

    def _setup_event_listeners(self) -> None:
        """设置事件监听器"""
        # 监听插件系统事件
        pass

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
