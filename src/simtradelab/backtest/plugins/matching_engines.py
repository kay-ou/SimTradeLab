# -*- coding: utf-8 -*-
"""
撮合引擎插件实现

提供多种撮合引擎插件，模拟不同的交易撮合逻辑：
- 简单撮合引擎：基本的价格撮合
- 深度撮合引擎：考虑订单深度的撮合
- 限价撮合引擎：严格的限价单撮合
"""

from decimal import Decimal
from typing import List, Optional

from .base import (
    BaseCommissionModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    Fill,
    MarketData,
    Order,
    PluginMetadata,
)
from .config import (
    DepthMatchingEngineConfig,
    LimitMatchingEngineConfig,
    SimpleMatchingEngineConfig,
)


class SimpleMatchingEngine(BaseMatchingEngine):
    """
    简单撮合引擎

    实现基本的价格撮合逻辑，并集成滑点和手续费计算。
    """

    METADATA = PluginMetadata(
        name="SimpleMatchingEngine",
        version="1.1.0",
        description="基本的价格撮合引擎，集成成本计算",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "simple"],
    )

    config_model = SimpleMatchingEngineConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[SimpleMatchingEngineConfig] = None,
        slippage_model: Optional[BaseSlippageModel] = None,
        commission_model: Optional[BaseCommissionModel] = None,
    ):
        super().__init__(metadata, config, slippage_model, commission_model)

        if config:
            self._price_tolerance = config.price_tolerance
            self._enable_partial_fill = config.enable_partial_fill
            self._max_order_size = config.max_order_size
        else:
            default_config = SimpleMatchingEngineConfig()
            self._price_tolerance = default_config.price_tolerance
            self._enable_partial_fill = default_config.enable_partial_fill
            self._max_order_size = default_config.max_order_size

    def _on_initialize(self) -> None:
        """初始化撮合引擎"""
        self.logger.info(f"{self.metadata.name} initialized.")

    def _on_start(self) -> None:
        """启动撮合引擎"""
        self.logger.info(f"{self.metadata.name} started.")

    def _on_stop(self) -> None:
        """停止撮合引擎"""
        self.logger.info(f"{self.metadata.name} stopped.")

    def match_order(self, order: Order, market_data: MarketData) -> List[Fill]:
        """
        撮合订单，并计算滑点和手续费

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            成交记录列表
        """
        fills: List[Fill] = []

        if not self._can_execute(order, market_data):
            self.logger.debug(f"Order {order.order_id} cannot be executed.")
            return fills

        fill_price = self._get_fill_price(order, market_data)
        fill_quantity = order.quantity  # 简单模型，完全成交

        # 创建基础成交记录
        fill = Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=fill_quantity,
            price=fill_price,
            timestamp=market_data.timestamp,
        )

        # 应用滑点模型
        if self._slippage_model:
            slippage_amount = self._slippage_model.calculate_slippage(
                order, market_data, fill.price
            )
            fill.slippage = slippage_amount
            # 根据滑点调整成交价格
            if order.side == "buy":
                fill.price += (
                    slippage_amount / fill.quantity if fill.quantity else Decimal("0")
                )
            else:  # sell
                fill.price -= (
                    slippage_amount / fill.quantity if fill.quantity else Decimal("0")
                )

        # 应用手续费模型
        if self._commission_model:
            fill.commission = self._commission_model.calculate_commission(fill)

        # 更新订单状态
        order.status = "filled"
        order.filled_quantity = fill_quantity
        order.avg_fill_price = fill.price

        fills.append(fill)

        self.logger.info(
            f"Order {order.order_id} matched: {order.side} {fill.quantity} "
            f"{order.symbol} at {fill.price:.2f} (slippage: {fill.slippage:.4f}, "
            f"commission: {fill.commission:.4f})"
        )

        return fills

    def _can_execute(self, order: Order, market_data: MarketData) -> bool:
        """判断订单是否可以执行"""
        if order.order_type == "market":
            return True
        if order.order_type == "limit" and order.price is not None:
            if order.side == "buy":
                return order.price >= market_data.low_price
            else:  # sell
                return order.price <= market_data.high_price
        return False

    def _get_fill_price(self, order: Order, market_data: MarketData) -> Decimal:
        """获取理论成交价格（滑点前）"""
        if order.order_type == "market":
            return market_data.close_price
        if order.order_type == "limit" and order.price is not None:
            if order.side == "buy":
                return min(order.price, market_data.open_price)
            else:  # sell
                return max(order.price, market_data.open_price)
        return market_data.close_price


class DepthMatchingEngine(BaseMatchingEngine):
    """
    深度撮合引擎
    (此处省略后续代码，待SimpleMatchingEngine重构完成后再处理)
    """

    METADATA = PluginMetadata(
        name="DepthMatchingEngine",
        version="1.0.0",
        description="考虑订单深度的撮合引擎",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "depth", "market_impact"],
    )
    config_model = DepthMatchingEngineConfig

    def match_order(self, order: Order, market_data: MarketData) -> List[Fill]:
        raise NotImplementedError("DepthMatchingEngine has not been refactored yet.")


class StrictLimitMatchingEngine(BaseMatchingEngine):
    """
    严格限价撮合引擎
    (此处省略后续代码，待SimpleMatchingEngine重构完成后再处理)
    """

    METADATA = PluginMetadata(
        name="StrictLimitMatchingEngine",
        version="1.0.0",
        description="严格的限价单撮合引擎",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "limit", "strict"],
    )
    config_model = LimitMatchingEngineConfig

    def match_order(self, order: Order, market_data: MarketData) -> List[Fill]:
        raise NotImplementedError(
            "StrictLimitMatchingEngine has not been refactored yet."
        )
