# -*- coding: utf-8 -*-
"""
撮合引擎插件实现

提供多种撮合引擎插件，模拟不同的交易撮合逻辑：
- 简单撮合引擎：基本的价格撮合
- 深度撮合引擎：考虑订单深度的撮合
- 限价撮合引擎：严格的限价单撮合

E8修复：使用统一的Pydantic配置模型进行配置验证
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from .base import BaseMatchingEngine, Fill, MarketData, Order, PluginMetadata
from .config import (
    DepthMatchingEngineConfig,
    LimitMatchingEngineConfig,
    SimpleMatchingEngineConfig,
)


class SimpleMatchingEngine(BaseMatchingEngine):
    """
    简单撮合引擎

    实现基本的价格撮合逻辑：
    - 市价单按当前价格成交
    - 限价单按限价或更优价格成交
    - 完全成交，不考虑流动性限制

    E8修复：使用SimpleMatchingEngineConfig进行类型安全的配置验证
    """

    METADATA = PluginMetadata(
        name="SimpleMatchingEngine",
        version="1.0.0",
        description="基本的价格撮合引擎",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "simple"],
    )

    # E8修复：定义配置模型类
    config_model = SimpleMatchingEngineConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[SimpleMatchingEngineConfig] = None,
    ):
        super().__init__(metadata, config)

        # E8修复：通过类型安全的配置对象访问参数
        if config:
            self._price_tolerance = config.price_tolerance
            self._enable_partial_fill = config.enable_partial_fill
            self._max_order_size = config.max_order_size
        else:
            # 使用默认配置
            default_config = SimpleMatchingEngineConfig()
            self._price_tolerance = default_config.price_tolerance
            self._enable_partial_fill = default_config.enable_partial_fill
            self._max_order_size = default_config.max_order_size

    def _on_initialize(self) -> None:
        """初始化撮合引擎"""
        self.logger.info("SimpleMatchingEngine initialized")

    def _on_start(self) -> None:
        """启动撮合引擎"""
        self.logger.info("SimpleMatchingEngine started")

    def _on_stop(self) -> None:
        """停止撮合引擎"""
        self.logger.info("SimpleMatchingEngine stopped")

    def match_order(self, order: Order, market_data: MarketData) -> List[Fill]:
        """
        撮合订单

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            成交记录列表
        """
        fills: List[Fill] = []

        # 检查是否可以立即执行
        if not self.can_execute_immediately(order, market_data):
            self.logger.debug(f"Order {order.order_id} cannot be executed immediately")
            return fills

        # 确定成交价格
        fill_price = self._get_fill_price(order, market_data)

        # 创建成交记录
        fill = Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=datetime.now(),
        )

        fills.append(fill)

        self.logger.info(
            f"Order {order.order_id} matched: {order.side} {order.quantity} "
            f"{order.symbol} at {fill_price}"
        )

        return fills

    def can_execute_immediately(self, order: Order, market_data: MarketData) -> bool:
        """
        判断订单是否可以立即执行

        Args:
            order: 待判断的订单
            market_data: 当前市场数据

        Returns:
            是否可以立即执行
        """
        # 市价单总是可以立即执行
        if order.order_type == "market":
            return True

        # 限价单需要检查价格条件
        if order.order_type == "limit" and order.price is not None:
            current_price = market_data.close_price

            if order.side == "buy":
                # 买入限价单：限价 >= 市价
                return order.price >= current_price
            else:
                # 卖出限价单：限价 <= 市价
                return order.price <= current_price

        return False

    def _get_fill_price(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取成交价格

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交价格
        """
        if order.order_type == "market":
            # 市价单使用当前价格
            return market_data.close_price

        elif order.order_type == "limit" and order.price is not None:
            # 限价单使用限价或更优价格
            current_price = market_data.close_price

            if order.side == "buy":
                # 买入：取较小值（更优价格）
                return min(order.price, current_price)
            else:
                # 卖出：取较大值（更优价格）
                return max(order.price, current_price)

        return market_data.close_price

    def can_match(self, order: Order, market_data: MarketData) -> bool:
        """
        判断订单是否可以撮合

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            是否可以撮合
        """
        return self.can_execute_immediately(order, market_data)

    def get_fill_price(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取成交价格

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交价格
        """
        return self._get_fill_price(order, market_data)

    def get_fill_quantity(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取成交数量

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交数量
        """
        # 简单撮合引擎完全成交
        return order.quantity


class DepthMatchingEngine(BaseMatchingEngine):
    """
    深度撮合引擎

    考虑订单深度的撮合逻辑：
    - 大单可能产生价格冲击
    - 根据交易量调整成交价格
    - 支持部分成交
    """

    METADATA = PluginMetadata(
        name="DepthMatchingEngine",
        version="1.0.0",
        description="考虑订单深度的撮合引擎",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "depth", "market_impact"],
    )

    # E8修复：定义配置模型类
    config_model = DepthMatchingEngineConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[DepthMatchingEngineConfig] = None,
    ):
        super().__init__(metadata, config)

        # E8修复：通过类型安全的配置对象访问参数
        if isinstance(config, dict):
            config = DepthMatchingEngineConfig(**config)

        if config:
            self._price_tolerance = config.price_tolerance
            self._enable_partial_fill = config.enable_partial_fill
            self._max_order_size = config.max_order_size
            self._depth_levels = config.depth_levels
            self._liquidity_factor = config.liquidity_factor
            self._volume_impact_factor = config.volume_impact_factor
            self._max_fill_ratio = config.max_fill_ratio
            self._min_fill_amount = config.min_fill_amount
            self._min_depth_ratio = config.min_depth_ratio
            self._max_spread_ratio = config.max_spread_ratio
        else:
            # 使用默认配置
            default_config = DepthMatchingEngineConfig()
            self._price_tolerance = default_config.price_tolerance
            self._enable_partial_fill = default_config.enable_partial_fill
            self._max_order_size = default_config.max_order_size
            self._depth_levels = default_config.depth_levels
            self._liquidity_factor = default_config.liquidity_factor
            self._volume_impact_factor = default_config.volume_impact_factor
            self._max_fill_ratio = default_config.max_fill_ratio
            self._min_fill_amount = default_config.min_fill_amount
            self._min_depth_ratio = default_config.min_depth_ratio
            self._max_spread_ratio = default_config.max_spread_ratio

    def _on_initialize(self) -> None:
        """初始化深度撮合引擎"""
        self.logger.info("DepthMatchingEngine initialized")

    def _on_start(self) -> None:
        """启动深度撮合引擎"""
        self.logger.info("DepthMatchingEngine started")

    def _on_stop(self) -> None:
        """停止深度撮合引擎"""
        self.logger.info("DepthMatchingEngine stopped")

    def match_order(self, order: Order, market_data: MarketData) -> List[Fill]:
        """
        撮合订单（考虑深度）

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            成交记录列表
        """
        fills: List[Fill] = []

        if not self.can_execute_immediately(order, market_data):
            return fills

        # 计算市场冲击
        market_impact = self.get_market_impact(order, market_data)

        # 确定可成交数量
        available_quantity = self._get_available_quantity(order, market_data)
        fill_quantity = min(order.quantity, available_quantity)

        if fill_quantity < self._min_fill_amount:
            self.logger.debug(
                f"Order {order.order_id} quantity too small: {fill_quantity}"
            )
            return fills

        # 计算成交价格（包含市场冲击）
        base_price = self._get_base_price(order, market_data)
        impact_adjustment = base_price * market_impact

        if order.side == "buy":
            fill_price = base_price + impact_adjustment
        else:
            fill_price = base_price - impact_adjustment

        # 创建成交记录
        fill = Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=fill_quantity,
            price=fill_price,
            timestamp=datetime.now(),
        )

        fills.append(fill)

        self.logger.info(
            f"Order {order.order_id} matched with depth: {order.side} {fill_quantity} "
            f"{order.symbol} at {fill_price} (impact: {market_impact:.4f})"
        )

        return fills

    def can_execute_immediately(self, order: Order, market_data: MarketData) -> bool:
        """判断订单是否可以立即执行"""
        # 基本的执行判断逻辑
        if order.order_type == "market":
            return True

        if order.order_type == "limit" and order.price is not None:
            current_price = market_data.close_price

            if order.side == "buy":
                return order.price >= current_price
            else:
                return order.price <= current_price

        return False

    def get_market_impact(self, order: Order, market_data: MarketData) -> Decimal:
        """
        计算市场冲击

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            市场冲击系数
        """
        # 基于交易量占比计算冲击
        volume_ratio = order.quantity / market_data.volume
        impact = volume_ratio * self._volume_impact_factor

        # 限制冲击范围
        return min(impact, Decimal("0.05"))  # 最大5%冲击

    def _get_available_quantity(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取可成交数量

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            可成交数量
        """
        # 基于日均成交量的比例限制
        max_quantity = market_data.volume * self._max_fill_ratio
        return min(order.quantity, max_quantity)

    def _get_base_price(self, order: Order, market_data: MarketData) -> Decimal:
        """获取基础价格"""
        if order.order_type == "market":
            return market_data.close_price
        elif order.order_type == "limit" and order.price is not None:
            return order.price
        return market_data.close_price

    def can_match(self, order: Order, market_data: MarketData) -> bool:
        """
        判断订单是否可以撮合

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            是否可以撮合
        """
        return self.can_execute_immediately(order, market_data)

    def get_fill_price(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取成交价格

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交价格
        """
        # 计算市场冲击
        market_impact = self.get_market_impact(order, market_data)

        # 计算成交价格（包含市场冲击）
        base_price = self._get_base_price(order, market_data)
        impact_adjustment = base_price * market_impact

        if order.side == "buy":
            return base_price + impact_adjustment
        else:
            return base_price - impact_adjustment

    def get_fill_quantity(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取成交数量

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交数量
        """
        # 确定可成交数量
        available_quantity = self._get_available_quantity(order, market_data)
        fill_quantity = min(order.quantity, available_quantity)

        if fill_quantity < self._min_fill_amount:
            return Decimal("0")

        return fill_quantity


class StrictLimitMatchingEngine(BaseMatchingEngine):
    """
    严格限价撮合引擎

    严格的限价单撮合逻辑：
    - 只有满足限价条件的订单才能成交
    - 不允许价格穿透
    - 支持队列优先级
    """

    METADATA = PluginMetadata(
        name="StrictLimitMatchingEngine",
        version="1.0.0",
        description="严格的限价单撮合引擎",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "limit", "strict"],
    )

    # E8修复：定义配置模型类
    config_model = LimitMatchingEngineConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[LimitMatchingEngineConfig] = None,
    ):
        super().__init__(metadata, config)

        # E8修复：通过类型安全的配置对象访问参数
        if isinstance(config, dict):
            config = LimitMatchingEngineConfig(**config)

        if config:
            self._price_tolerance = config.price_tolerance
            self._enable_partial_fill = config.enable_partial_fill
            self._max_order_size = config.max_order_size
            self._strict_limit_check = config.strict_limit_check
            self._order_queue_enabled = config.order_queue_enabled
            self._max_queue_size = config.max_queue_size
            self._allow_market_order = config.allow_market_order
            self._price_precision = config.price_precision
            self._allow_partial_fills = config.allow_partial_fills
        else:
            # 使用默认配置
            default_config = LimitMatchingEngineConfig()
            self._price_tolerance = default_config.price_tolerance
            self._enable_partial_fill = default_config.enable_partial_fill
            self._max_order_size = default_config.max_order_size
            self._strict_limit_check = default_config.strict_limit_check
            self._order_queue_enabled = default_config.order_queue_enabled
            self._max_queue_size = default_config.max_queue_size
            self._allow_market_order = default_config.allow_market_order
            self._price_precision = default_config.price_precision
            self._allow_partial_fills = default_config.allow_partial_fills

    def _on_initialize(self) -> None:
        """初始化严格限价撮合引擎"""
        self.logger.info("StrictLimitMatchingEngine initialized")

    def _on_start(self) -> None:
        """启动严格限价撮合引擎"""
        self.logger.info("StrictLimitMatchingEngine started")

    def _on_stop(self) -> None:
        """停止严格限价撮合引擎"""
        self.logger.info("StrictLimitMatchingEngine stopped")

    def match_order(self, order: Order, market_data: MarketData) -> List[Fill]:
        """
        严格撮合订单

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            成交记录列表
        """
        fills: List[Fill] = []

        if not self.can_execute_immediately(order, market_data):
            self.logger.debug(
                f"Order {order.order_id} does not meet execution criteria"
            )
            return fills

        # 确定成交价格
        fill_price = self._get_execution_price(order, market_data)

        # 创建成交记录
        fill = Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=datetime.now(),
        )

        fills.append(fill)

        self.logger.info(
            f"Order {order.order_id} strictly matched: {order.side} {order.quantity} "
            f"{order.symbol} at {fill_price}"
        )

        return fills

    def can_execute_immediately(self, order: Order, market_data: MarketData) -> bool:
        """
        严格判断订单是否可以立即执行

        Args:
            order: 待判断的订单
            market_data: 当前市场数据

        Returns:
            是否可以立即执行
        """
        # 市价单检查
        if order.order_type == "market":
            return self._allow_market_order

        # 限价单检查
        if order.order_type == "limit" and order.price is not None:
            current_price = market_data.close_price

            if order.side == "buy":
                # 买入限价单：限价必须 >= 当前价格
                return order.price >= current_price
            else:
                # 卖出限价单：限价必须 <= 当前价格
                return order.price <= current_price

        return False

    def _get_execution_price(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取执行价格

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            执行价格
        """
        if order.order_type == "market":
            # 市价单使用当前价格
            return market_data.close_price

        elif order.order_type == "limit" and order.price is not None:
            # 限价单严格使用限价
            return order.price

        return market_data.close_price

    def _round_price(self, price: Decimal) -> Decimal:
        """
        按精度四舍五入价格

        Args:
            price: 原始价格

        Returns:
            四舍五入后的价格
        """
        return price.quantize(Decimal(f"0.{'0' * self._price_precision}"))

    def can_match(self, order: Order, market_data: MarketData) -> bool:
        """
        判断订单是否可以撮合

        Args:
            order: 待撮合的订单
            market_data: 当前市场数据

        Returns:
            是否可以撮合
        """
        return self.can_execute_immediately(order, market_data)

    def get_fill_price(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取成交价格

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交价格
        """
        return self._get_execution_price(order, market_data)

    def get_fill_quantity(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取成交数量

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交数量
        """
        # 严格限价引擎完全成交
        return order.quantity
