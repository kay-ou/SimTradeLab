# -*- coding: utf-8 -*-
"""
滑点模型插件实现

提供多种滑点模型，模拟不同的市场滑点成本：
- 线性滑点模型：基础的线性滑点计算
- 基于成交量的滑点模型：考虑成交量影响的滑点

E8修复：使用统一的Pydantic配置模型进行配置验证
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

import numpy as np

from .base import BaseSlippageModel, MarketData, Order, PluginMetadata
from .config import LinearSlippageModelConfig, VolumeBasedSlippageModelConfig


class LinearSlippageModel(BaseSlippageModel):
    """
    线性滑点模型

    使用线性滑点计算，适用于：
    - 回测初期的简单测试
    - 流动性较好的主流股票
    - 保守的滑点估计
    
    E8修复：使用LinearSlippageModelConfig进行类型安全的配置验证
    """

    METADATA = PluginMetadata(
        name="LinearSlippageModel",
        version="1.0.0",
        description="线性滑点计算模型",
        author="SimTradeLab",
        category="slippage_model",
        tags=["backtest", "slippage", "linear", "simple"],
    )
    
    # E8修复：定义配置模型类
    config_model = LinearSlippageModelConfig

    def __init__(
        self, 
        metadata: PluginMetadata, 
        config: Optional[LinearSlippageModelConfig] = None
    ):
        super().__init__(metadata, config)
        
        # E8修复：通过类型安全的配置对象访问参数
        if config:
            self._base_slippage_rate = config.base_slippage_rate
            self._volume_impact_factor = config.volume_impact_factor
            self._volatility_multiplier = config.volatility_multiplier
            self._min_slippage = config.min_slippage
            self._max_slippage = config.max_slippage
        else:
            # 使用默认配置
            default_config = LinearSlippageModelConfig()
            self._base_slippage_rate = default_config.base_slippage_rate
            self._volume_impact_factor = default_config.volume_impact_factor
            self._volatility_multiplier = default_config.volatility_multiplier
            self._min_slippage = default_config.min_slippage
            self._max_slippage = default_config.max_slippage

    def _on_initialize(self) -> None:
        """初始化线性滑点模型"""
        self.logger.info("LinearSlippageModel initialized")

    def _on_start(self) -> None:
        """启动线性滑点模型"""
        self.logger.info("LinearSlippageModel started")

    def _on_stop(self) -> None:
        """停止线性滑点模型"""
        self.logger.info("LinearSlippageModel stopped")

    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算线性滑点
        
        使用基础滑点率计算，可根据成交量和波动性调整

        Args:
            order: 订单信息
            market_data: 市场数据
            fill_price: 成交价格

        Returns:
            滑点金额（正数表示不利滑点）
        """
        # 基础滑点金额
        base_slippage = fill_price * order.quantity * self._base_slippage_rate
        
        # 应用最小和最大滑点限制
        slippage_amount = max(base_slippage, self._min_slippage)
        slippage_amount = min(slippage_amount, self._max_slippage)

        self.logger.debug(
            f"Linear slippage for order {order.order_id}: {slippage_amount} "
            f"(base rate: {self._base_slippage_rate:.4f})"
        )

        return slippage_amount

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取基础滑点率

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            滑点率
        """
        return self._base_slippage_rate


class VolumeBasedSlippageModel(BaseSlippageModel):
    """
    基于成交量的滑点模型

    根据订单相对于市场成交量的大小计算滑点：
    - 小订单相对较低的滑点
    - 大订单更高的滑点
    - 支持多种冲击曲线
    
    E8修复：使用VolumeBasedSlippageModelConfig进行类型安全的配置验证
    """

    METADATA = PluginMetadata(
        name="VolumeBasedSlippageModel",
        version="1.0.0",
        description="基于成交量的动态滑点模型",
        author="SimTradeLab",
        category="slippage_model",
        tags=["backtest", "slippage", "volume", "dynamic"],
    )
    
    # E8修复：定义配置模型类
    config_model = VolumeBasedSlippageModelConfig

    def __init__(
        self, 
        metadata: PluginMetadata, 
        config: Optional[VolumeBasedSlippageModelConfig] = None
    ):
        super().__init__(metadata, config)
        
        # E8修复：通过类型安全的配置对象访问参数
        if config:
            self._base_slippage_rate = config.base_slippage_rate
            self._volume_impact_factor = config.volume_impact_factor
            self._volatility_multiplier = config.volatility_multiplier
            self._min_slippage = config.min_slippage
            self._max_slippage = config.max_slippage
            self._volume_threshold = config.volume_threshold
            self._volume_impact_curve = config.volume_impact_curve
        else:
            # 使用默认配置
            default_config = VolumeBasedSlippageModelConfig()
            self._base_slippage_rate = default_config.base_slippage_rate
            self._volume_impact_factor = default_config.volume_impact_factor
            self._volatility_multiplier = default_config.volatility_multiplier
            self._min_slippage = default_config.min_slippage
            self._max_slippage = default_config.max_slippage
            self._volume_threshold = default_config.volume_threshold
            self._volume_impact_curve = default_config.volume_impact_curve

    def _on_initialize(self) -> None:
        """初始化基于成交量的滑点模型"""
        self.logger.info("VolumeBasedSlippageModel initialized")

    def _on_start(self) -> None:
        """启动基于成交量的滑点模型"""
        self.logger.info("VolumeBasedSlippageModel started")

    def _on_stop(self) -> None:
        """停止基于成交量的滑点模型"""
        self.logger.info("VolumeBasedSlippageModel stopped")

    def calculate_slippage(
        self, order: Order, market_data: MarketData, fill_price: Decimal
    ) -> Decimal:
        """
        计算基于成交量的滑点
        
        考虑订单大小相对于市场成交量的影响

        Args:
            order: 订单信息
            market_data: 市场数据
            fill_price: 成交价格

        Returns:
            滑点金额（正数表示不利滑点）
        """
        # 基础滑点
        base_slippage = fill_price * order.quantity * self._base_slippage_rate
        
        # 计算成交量冲击
        volume_ratio = float(order.quantity) / float(market_data.volume)
        volume_impact = self._calculate_volume_impact(volume_ratio)
        
        # 总滑点 = 基础滑点 * (1 + 成交量冲击)
        total_slippage = base_slippage * (Decimal("1") + volume_impact)
        
        # 应用限制
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
        
        Args:
            volume_ratio: 订单量/市场成交量比例
            
        Returns:
            冲击系数
        """
        if volume_ratio <= 0:
            return Decimal("0")
            
        # 根据配置的冲击曲线计算
        if self._volume_impact_curve == "linear":
            impact = volume_ratio * float(self._volume_impact_factor)
        elif self._volume_impact_curve == "square_root":
            impact = np.sqrt(volume_ratio) * float(self._volume_impact_factor)
        elif self._volume_impact_curve == "logarithmic":
            impact = np.log(1 + volume_ratio) * float(self._volume_impact_factor)
        else:
            # 默认使用平方根
            impact = np.sqrt(volume_ratio) * float(self._volume_impact_factor)
            
        return Decimal(str(min(impact, 1.0)))  # 限制最大冲击为100%

    def get_slippage_rate(self, order: Order, market_data: MarketData) -> Decimal:
        """
        获取动态滑点率

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            滑点率
        """
        volume_ratio = float(order.quantity) / float(market_data.volume)
        volume_impact = self._calculate_volume_impact(volume_ratio)
        
        return self._base_slippage_rate * (Decimal("1") + volume_impact)