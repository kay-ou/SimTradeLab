# -*- coding: utf-8 -*-
"""
回测插件基础模块

定义回测系统中可插拔组件的基础接口和抽象类。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from simtradelab.plugins.base import BasePlugin, PluginConfig, PluginMetadata

# 重新导出以供其他模块使用
__all__ = [
    "BaseBacktestPlugin",
    "BaseMatchingEngine",
    "BaseSlippageModel",
    "BaseCommissionModel",
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
]


@dataclass
class Order:
    """订单信息"""

    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: Decimal
    price: Optional[Decimal] = None  # None表示市价单
    order_type: str = "market"  # "market" or "limit"
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # "pending", "filled", "cancelled"
    filled_quantity: Decimal = Decimal("0")
    avg_fill_price: Optional[Decimal] = None


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
        self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None
    ):
        # 转换 Dict 配置为 PluginConfig
        plugin_config = None
        if config is not None:
            plugin_config = PluginConfig(config=config)

        super().__init__(metadata, plugin_config)
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


class BaseMatchingEngine(BaseBacktestPlugin):
    """
    撮合引擎基类

    负责模拟交易订单的撮合过程，决定订单如何成交。
    """

    def get_plugin_type(self) -> str:
        return "matching_engine"

    @abstractmethod
    def match_order(self, order: Order, market_data: MarketData) -> List[Fill]:
        """
        撮合订单

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            成交记录列表（可能部分成交或完全成交）
        """
        pass

    @abstractmethod
    def can_execute_immediately(self, order: Order, market_data: MarketData) -> bool:
        """
        判断订单是否可以立即执行

        Args:
            order: 待判断的订单
            market_data: 当前市场数据

        Returns:
            是否可以立即执行
        """
        pass

    def get_market_impact(self, order: Order, market_data: MarketData) -> Decimal:
        """
        计算市场冲击（默认实现）

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            市场冲击系数
        """
        return Decimal("0")


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

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取滑点率（默认实现）

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            滑点率
        """
        return Decimal("0.001")  # 默认0.1%


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

    def calculate_commission_breakdown(self, fill: Fill) -> Dict[str, Decimal]:
        """
        计算手续费明细（默认实现）

        Args:
            fill: 成交信息

        Returns:
            手续费明细字典
        """
        total_commission = self.calculate_commission(fill)
        return {"total": total_commission}


# 插件类型常量
PLUGIN_TYPE_MATCHING_ENGINE = "matching_engine"
PLUGIN_TYPE_SLIPPAGE_MODEL = "slippage_model"
PLUGIN_TYPE_COMMISSION_MODEL = "commission_model"
