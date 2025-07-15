# -*- coding: utf-8 -*-
"""
滑点模型插件实现

提供多种滑点模型，模拟不同的市场滑点成本：
- 线性滑点模型：基础的线性滑点计算
- 基于成交量的滑点模型：考虑成交量影响的滑点

使用统一的Pydantic配置模型进行配置验证
"""

from decimal import Decimal
from typing import List, Optional

import numpy as np

from .base import BaseSlippageModel, MarketData, Order, PluginMetadata
from .config import (
    FixedSlippageModelConfig,
    LinearSlippageModelConfig,
    VolatilityBasedSlippageModelConfig,
    VolumeBasedSlippageModelConfig,
)


class LinearSlippageModel(BaseSlippageModel):
    """
    线性滑点模型

    滑点率根据订单大小线性增加。
    滑点率 = 基础费率 + 斜率 * (订单数量 / 参考规模)

    使用LinearSlippageModelConfig进行类型安全的配置验证
    """

    METADATA = PluginMetadata(
        name="LinearSlippageModel",
        version="1.1.0",  # 版本提升，因为修复了重大bug
        description="线性滑点计算模型",
        author="SimTradeLab",
        category="slippage_model",
        tags=["backtest", "slippage", "linear", "simple"],
    )

    config_model = LinearSlippageModelConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[LinearSlippageModelConfig] = None,
    ):
        super().__init__(metadata, config)

        if config:
            self._base_rate = config.base_rate
            self._slope = config.slope
            self._reference_size = config.reference_size
            self._max_slippage_rate = config.max_slippage_rate
            self._min_slippage = config.min_slippage
            self._max_slippage = config.max_slippage
        else:
            default_config = LinearSlippageModelConfig()
            self._base_rate = default_config.base_rate
            self._slope = default_config.slope
            self._reference_size = default_config.reference_size
            self._max_slippage_rate = default_config.max_slippage_rate
            self._min_slippage = default_config.min_slippage
            self._max_slippage = default_config.max_slippage

    def _on_initialize(self) -> None:
        self.logger.info("LinearSlippageModel initialized")

    def _on_start(self) -> None:
        self.logger.info("LinearSlippageModel started")

    def _on_stop(self) -> None:
        self.logger.info("LinearSlippageModel stopped")

    def _calculate_linear_rate(self, order: Order) -> Decimal:
        """根据订单大小计算线性滑点率。"""
        size_ratio = order.quantity / self._reference_size
        slippage_rate = self._base_rate + self._slope * size_ratio
        return min(slippage_rate, self._max_slippage_rate)

    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算线性滑点。
        """
        slippage_rate = self._calculate_linear_rate(order)
        slippage_amount = fill_price * order.quantity * slippage_rate

        # 应用最小和最大滑点金额限制
        slippage_amount = max(slippage_amount, self._min_slippage)
        slippage_amount = min(slippage_amount, self._max_slippage)

        self.logger.debug(
            f"Linear slippage for order {order.order_id}: {slippage_amount} "
            f"(rate: {slippage_rate:.6f})"
        )

        return slippage_amount

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        """获取动态计算的线性滑点率。"""
        return self._calculate_linear_rate(order)


class VolumeBasedSlippageModel(BaseSlippageModel):
    """
    基于成交量的滑点模型

    根据订单相对于市场成交量的大小计算滑点：
    - 小订单相对较低的滑点
    - 大订单更高的滑点
    - 支持多种冲击曲线

    使用VolumeBasedSlippageModelConfig进行类型安全的配置验证
    """

    METADATA = PluginMetadata(
        name="VolumeBasedSlippageModel",
        version="1.0.0",
        description="基于成交量的动态滑点模型",
        author="SimTradeLab",
        category="slippage_model",
        tags=["backtest", "slippage", "volume", "dynamic"],
    )

    config_model = VolumeBasedSlippageModelConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[VolumeBasedSlippageModelConfig] = None,
    ):
        super().__init__(metadata, config)

        if config:
            self._base_slippage_rate = config.base_slippage_rate
            self._volume_impact_factor = config.volume_impact_factor
            self._min_slippage = config.min_slippage
            self._max_slippage = config.max_slippage
            self._volume_threshold = config.volume_threshold
            self._volume_impact_curve = config.volume_impact_curve
        else:
            default_config = VolumeBasedSlippageModelConfig()
            self._base_slippage_rate = default_config.base_slippage_rate
            self._volume_impact_factor = default_config.volume_impact_factor
            self._min_slippage = default_config.min_slippage
            self._max_slippage = default_config.max_slippage
            self._volume_threshold = default_config.volume_threshold
            self._volume_impact_curve = default_config.volume_impact_curve

    def _on_initialize(self) -> None:
        self.logger.info("VolumeBasedSlippageModel initialized")

    def _on_start(self) -> None:
        self.logger.info("VolumeBasedSlippageModel started")

    def _on_stop(self) -> None:
        self.logger.info("VolumeBasedSlippageModel stopped")

    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算基于成交量的滑点
        """
        base_slippage = fill_price * order.quantity * self._base_slippage_rate
        volume_ratio = float(order.quantity) / float(market_data.volume)
        volume_impact = self._calculate_volume_impact(volume_ratio)
        total_slippage = base_slippage * (Decimal("1") + volume_impact)

        slippage_amount = max(total_slippage, self._min_slippage)
        slippage_amount = min(slippage_amount, self._max_slippage)

        self.logger.debug(
            f"Volume-based slippage for order {order.order_id}: {slippage_amount} "
            f"(volume ratio: {volume_ratio:.4f}, impact: {volume_impact:.4f})"
        )

        return slippage_amount

    def _calculate_volume_impact(self, volume_ratio: float) -> Decimal:
        """
        计算成交量冲击系数
        """
        if volume_ratio <= 0:
            return Decimal("0")

        if self._volume_impact_curve == "linear":
            impact = volume_ratio * float(self._volume_impact_factor)
        elif self._volume_impact_curve == "square_root":
            impact = np.sqrt(volume_ratio) * float(self._volume_impact_factor)
        elif self._volume_impact_curve == "logarithmic":
            impact = np.log1p(volume_ratio) * float(self._volume_impact_factor)
        else:
            impact = np.sqrt(volume_ratio) * float(self._volume_impact_factor)

        return Decimal(str(min(impact, 1.0)))

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取动态滑点率
        """
        volume_ratio = float(order.quantity) / float(market_data.volume)
        volume_impact = self._calculate_volume_impact(volume_ratio)

        return self._base_slippage_rate * (Decimal("1") + volume_impact)


class FixedSlippageModel(BaseSlippageModel):
    """
    固定滑点模型
    """

    METADATA = PluginMetadata(
        name="FixedSlippageModel",
        version="1.0.0",
        description="固定滑点模型",
        author="SimTradeLab",
        category="slippage_model",
        tags=["backtest", "slippage", "fixed", "simple"],
    )

    config_model = FixedSlippageModelConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[FixedSlippageModelConfig] = None,
    ):
        super().__init__(metadata, config)

        if config:
            self._base_slippage_rate = config.base_slippage_rate
            self._min_slippage = config.min_slippage
            self._max_slippage = config.max_slippage
        else:
            default_config = FixedSlippageModelConfig()
            self._base_slippage_rate = default_config.base_slippage_rate
            self._min_slippage = default_config.min_slippage
            self._max_slippage = default_config.max_slippage

    def _on_initialize(self) -> None:
        self.logger.info("FixedSlippageModel initialized")

    def _on_start(self) -> None:
        self.logger.info("FixedSlippageModel started")

    def _on_stop(self) -> None:
        self.logger.info("FixedSlippageModel stopped")

    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算固定滑点
        """
        slippage_amount = fill_price * order.quantity * self._base_slippage_rate

        slippage_amount = max(slippage_amount, self._min_slippage)
        slippage_amount = min(slippage_amount, self._max_slippage)

        self.logger.debug(
            f"Fixed slippage for order {order.order_id}: {slippage_amount} "
            f"(rate: {self._base_slippage_rate:.4f})"
        )
        return slippage_amount

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取固定滑点率
        """
        return self._base_slippage_rate


class DynamicSlippageModel(BaseSlippageModel):
    """
    动态滑点模型
    """

    METADATA = PluginMetadata(
        name="DynamicSlippageModel",
        version="1.0.0",
        description="动态滑点模型，基于市场状况调整",
        author="SimTradeLab",
        category="slippage_model",
        tags=["backtest", "slippage", "dynamic", "adaptive"],
    )

    config_model = VolumeBasedSlippageModelConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[VolumeBasedSlippageModelConfig] = None,
    ):
        super().__init__(metadata, config)

        if config:
            self._base_slippage_rate = config.base_slippage_rate
            self._volume_impact_factor = config.volume_impact_factor
            self._volatility_multiplier = config.volatility_multiplier
            self._min_slippage = config.min_slippage
            self._max_slippage = config.max_slippage
            self._volume_threshold = config.volume_threshold
            self._volume_impact_curve = config.volume_impact_curve
        else:
            default_config = VolumeBasedSlippageModelConfig()
            self._base_slippage_rate = default_config.base_slippage_rate
            self._volume_impact_factor = default_config.volume_impact_factor
            self._volatility_multiplier = default_config.volatility_multiplier
            self._min_slippage = default_config.min_slippage
            self._max_slippage = default_config.max_slippage
            self._volume_threshold = default_config.volume_threshold
            self._volume_impact_curve = default_config.volume_impact_curve

        self._price_history: List[Decimal] = []
        self._max_history_length = 20

    def _on_initialize(self) -> None:
        self.logger.info("DynamicSlippageModel initialized")

    def _on_start(self) -> None:
        self.logger.info("DynamicSlippageModel started")

    def _on_stop(self) -> None:
        self.logger.info("DynamicSlippageModel stopped")

    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算动态滑点
        """
        self._update_price_history(fill_price)
        base_slippage = fill_price * order.quantity * self._base_slippage_rate
        volume_ratio = float(order.quantity) / float(market_data.volume)
        volume_impact = self._calculate_volume_impact(volume_ratio)
        volatility_adjustment = self._calculate_volatility_adjustment()

        total_slippage = (
            base_slippage
            * (Decimal("1") + volume_impact)
            * (Decimal("1") + volatility_adjustment)
        )

        slippage_amount = max(total_slippage, self._min_slippage)
        slippage_amount = min(slippage_amount, self._max_slippage)

        self.logger.debug(
            f"Dynamic slippage for order {order.order_id}: {slippage_amount} "
            f"(volume ratio: {volume_ratio:.4f}, impact: {volume_impact:.4f}, "
            f"volatility adj: {volatility_adjustment:.4f})"
        )

        return slippage_amount

    def _update_price_history(self, price: Decimal) -> None:
        self._price_history.append(price)
        if len(self._price_history) > self._max_history_length:
            self._price_history.pop(0)

    def _calculate_volume_impact(self, volume_ratio: float) -> Decimal:
        if volume_ratio <= 0:
            return Decimal("0")
        if self._volume_impact_curve == "linear":
            impact = volume_ratio * float(self._volume_impact_factor)
        elif self._volume_impact_curve == "square_root":
            impact = np.sqrt(volume_ratio) * float(self._volume_impact_factor)
        elif self._volume_impact_curve == "logarithmic":
            impact = np.log1p(volume_ratio) * float(self._volume_impact_factor)
        else:
            impact = np.sqrt(volume_ratio) * float(self._volume_impact_factor)
        return Decimal(str(min(impact, 1.0)))

    def _calculate_volatility_adjustment(self) -> Decimal:
        if len(self._price_history) < 2:
            return Decimal("0")

        price_array = np.array([float(p) for p in self._price_history])
        returns = np.diff(price_array) / price_array[:-1]
        if returns.size == 0:
            return Decimal("0")

        volatility = np.std(returns)
        volatility_adjustment = volatility * float(self._volatility_multiplier)
        return Decimal(str(min(float(volatility_adjustment), 0.5)))

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        volume_ratio = float(order.quantity) / float(market_data.volume)
        volume_impact = self._calculate_volume_impact(volume_ratio)
        volatility_adjustment = self._calculate_volatility_adjustment()

        return (
            self._base_slippage_rate
            * (Decimal("1") + volume_impact)
            * (Decimal("1") + volatility_adjustment)
        )


class VolatilityBasedSlippageModel(BaseSlippageModel):
    """
    基于波动率的滑点模型
    """

    METADATA = PluginMetadata(
        name="VolatilityBasedSlippageModel",
        version="1.1.0",  # 版本提升，修复配置bug
        description="基于波动率的滑点模型",
        author="SimTradeLab",
        category="slippage_model",
        tags=["backtest", "slippage", "volatility", "adaptive"],
    )

    config_model = VolatilityBasedSlippageModelConfig

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[VolatilityBasedSlippageModelConfig] = None,
    ):
        super().__init__(metadata, config)

        if config:
            self._base_slippage_rate = config.base_slippage_rate
            self._volatility_multiplier = config.volatility_multiplier
            self._min_slippage = config.min_slippage
            self._max_slippage = config.max_slippage
            self._max_history_length = config.max_history_length
        else:
            default_config = VolatilityBasedSlippageModelConfig()
            self._base_slippage_rate = default_config.base_slippage_rate
            self._volatility_multiplier = default_config.volatility_multiplier
            self._min_slippage = default_config.min_slippage
            self._max_slippage = default_config.max_slippage
            self._max_history_length = default_config.max_history_length

        self._price_history: List[Decimal] = []

    def _on_initialize(self) -> None:
        self.logger.info("VolatilityBasedSlippageModel initialized")

    def _on_start(self) -> None:
        self.logger.info("VolatilityBasedSlippageModel started")

    def _on_stop(self) -> None:
        self.logger.info("VolatilityBasedSlippageModel stopped")

    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算基于波动率的滑点
        """
        self._update_price_history(fill_price)
        base_slippage = fill_price * order.quantity * self._base_slippage_rate
        volatility_factor = self._calculate_volatility_factor()
        total_slippage = base_slippage * volatility_factor

        slippage_amount = max(total_slippage, self._min_slippage)
        slippage_amount = min(slippage_amount, self._max_slippage)

        self.logger.debug(
            f"Volatility-based slippage for order {order.order_id}: {slippage_amount} "
            f"(volatility factor: {volatility_factor:.4f})"
        )

        return slippage_amount

    def _update_price_history(self, price: Decimal) -> None:
        self._price_history.append(price)
        if len(self._price_history) > self._max_history_length:
            self._price_history.pop(0)

    def _calculate_volatility_factor(self) -> Decimal:
        if len(self._price_history) < 2:
            return Decimal("1.0")

        price_array = np.array([float(p) for p in self._price_history])
        returns = np.diff(price_array) / price_array[:-1]
        if returns.size == 0:
            return Decimal("1.0")

        volatility = np.std(returns)
        volatility_factor = 1.0 + float(volatility) * float(self._volatility_multiplier)
        return Decimal(str(max(0.1, min(volatility_factor, 3.0))))

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        volatility_factor = self._calculate_volatility_factor()
        return self._base_slippage_rate * volatility_factor
