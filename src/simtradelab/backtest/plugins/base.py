# -*- coding: utf-8 -*-
"""
回测插件基础模块

定义回测系统中可插拔组件的基础接口和抽象类。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from simtradelab.plugins.base import BasePlugin, PluginConfig, PluginMetadata
from simtradelab.plugins.config.base_config import BasePluginConfig

# 重新导出以供其他模块使用
__all__ = [
    "BaseBacktestPlugin",
    "BaseMatchingEngine",
    "BaseSlippageModel",
    "BaseCommissionModel",
    "BaseLatencyModel",
    "Order",
    "Fill",
    "MarketData",
    "Position",
    "BacktestContext",
    "PluginMetadata",
    "PluginConfig",
    "PLUGIN_TYPE_MATCHING_ENGINE",
    "PLUGIN_TYPE_SLIPPAGE_MODEL",
    "PLUGIN_TYPE_COMMISSION_MODEL",
    "PLUGIN_TYPE_LATENCY_MODEL",
]


@dataclass
class Order:
    """订单信息"""

    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: Decimal
    price: Optional[Decimal] = None  # None表示市价单
    order_type: str = (
        "market"  # "market", "limit", "stop", "stop_limit", "trailing_stop"
    )
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # "pending", "active", "filled", "cancelled"
    filled_quantity: Decimal = Decimal("0")
    avg_fill_price: Optional[Decimal] = None

    # 高级订单类型参数
    trigger_price: Optional[Decimal] = None  # 止损单的触发价格
    trail_percent: Optional[Decimal] = None  # 跟踪止损单的百分比
    trail_amount: Optional[Decimal] = None  # 跟踪止损单的金额
    time_in_force: str = "gtc"  # "gtc", "ioc", "fok"

    # 跟踪止损单的内部状态
    trailing_reference_price: Optional[Decimal] = None  # 用于跟踪止损的参考价格（高/低水位）


@dataclass
class Fill:
    """成交信息"""

    order_id: str
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    commission: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")


@dataclass
class MarketData:
    """市场数据"""

    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    amount: Optional[Decimal] = None


@dataclass
class Position:
    """持仓信息"""

    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal


@dataclass
class BacktestContext:
    """回测上下文"""

    initial_capital: Decimal
    current_capital: Decimal
    positions: Dict[str, Position]
    orders: List[Order]
    fills: List[Fill]
    current_time: datetime


class BaseBacktestPlugin(BasePlugin, ABC):
    """
    回测插件基类

    所有回测相关插件都应继承此类，提供统一的插件接口。
    """

    def __init__(
        self, metadata: PluginMetadata, config: Optional[BasePluginConfig] = None
    ):
        super().__init__(metadata, config)
        self._backtest_context: Optional[BacktestContext] = None

    @abstractmethod
    def get_plugin_type(self) -> str:
        """
        获取插件类型

        Returns:
            插件类型标识
        """
        pass

    def set_backtest_context(self, context: BacktestContext) -> None:
        """
        设置回测上下文

        Args:
            context: 回测上下文信息
        """
        self._backtest_context = context

    def get_backtest_context(self) -> Optional[BacktestContext]:
        """
        获取回测上下文

        Returns:
            当前回测上下文
        """
        return self._backtest_context


class BaseSlippageModel(BaseBacktestPlugin):
    """
    滑点模型基类

    负责计算交易过程中的滑点成本。
    """

    def get_plugin_type(self) -> str:
        return "slippage_model"

    @abstractmethod
    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算滑点

        Args:
            order: 订单信息
            market_data: 市场数据
            fill_price: 成交价格

        Returns:
            滑点金额（正数表示不利滑点）
        """
        pass


class BaseLatencyModel(BaseBacktestPlugin):
    """
    延迟模型基类

    负责计算订单处理过程中的延迟，影响订单执行的时间。
    """

    def get_plugin_type(self) -> str:
        return "latency_model"

    @abstractmethod
    def calculate_latency(self, order: Order, market_data: MarketData) -> float:
        """
        计算订单处理延迟

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            延迟时间（秒）
        """
        pass

    @abstractmethod
    def get_execution_time(self, order: Order, market_data: MarketData) -> datetime:
        """
        获取订单实际执行时间

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            订单实际执行时间
        """
        pass


class BaseCommissionModel(BaseBacktestPlugin):
    """
    手续费模型基类

    负责计算交易过程中的各种费用。
    """

    def get_plugin_type(self) -> str:
        return "commission_model"

    @abstractmethod
    def calculate_commission(self, fill: Fill) -> Decimal:
        """
        计算手续费

        Args:
            fill: 成交信息

        Returns:
            手续费总额
        """
        pass


class BaseMatchingEngine(BaseBacktestPlugin):
    """
    撮合引擎基类

    负责模拟交易订单的撮合过程，决定订单如何成交。
    """

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[BasePluginConfig] = None,
    ):
        super().__init__(metadata, config)
        self._slippage_model: Optional[BaseSlippageModel] = None
        self._commission_model: Optional[BaseCommissionModel] = None

    def set_models(
        self,
        slippage_model: Optional[BaseSlippageModel],
        commission_model: Optional[BaseCommissionModel],
    ):
        """注入滑点和手续费模型"""
        self._slippage_model = slippage_model
        self._commission_model = commission_model

    def get_plugin_type(self) -> str:
        return "matching_engine"

    @abstractmethod
    def add_order(self, order: Order) -> None:
        """
        将订单添加到内部订单簿

        Args:
            order: 待添加的订单
        """
        pass

    @abstractmethod
    def trigger_matching(
        self, symbol: str, market_data: MarketData
    ) -> Tuple[List[Fill], List[Order]]:
        """
        对指定标的触发撮合

        Args:
            symbol: 待撮合的标的
            market_data: 当前市场数据

        Returns:
            成交记录列表和已完成（成交或取消）的订单列表
        """
        pass


# 插件类型常量
PLUGIN_TYPE_MATCHING_ENGINE = "matching_engine"
PLUGIN_TYPE_SLIPPAGE_MODEL = "slippage_model"
PLUGIN_TYPE_COMMISSION_MODEL = "commission_model"
PLUGIN_TYPE_LATENCY_MODEL = "latency_model"
