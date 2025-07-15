# -*- coding: utf-8 -*-
"""
固定延迟模型实现

提供固定延迟时间的简单模型。
"""

from datetime import datetime, timedelta
from typing import Optional

from simtradelab.plugins.base import PluginMetadata
from simtradelab.plugins.config.base_config import BasePluginConfig

from ..base import BaseLatencyModel, MarketData, Order


class FixedLatencyModelConfig(BasePluginConfig):
    """固定延迟模型配置"""

    latency_ms: int = 100  # 固定延迟（毫秒）


class FixedLatencyModel(BaseLatencyModel):
    """
    固定延迟模型

    所有订单使用相同的固定延迟时间。
    """

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[FixedLatencyModelConfig] = None,
    ):
        super().__init__(metadata, config)
        self._config = config or FixedLatencyModelConfig()

    def _on_initialize(self) -> None:
        """插件初始化"""
        pass

    def _on_start(self) -> None:
        """插件启动"""
        pass

    def _on_stop(self) -> None:
        """插件停止"""
        pass

    def calculate_latency(self, order: Order, market_data: MarketData) -> float:
        """
        计算订单处理延迟

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            延迟时间（秒）
        """
        return self._config.latency_ms / 1000.0

    def get_execution_time(self, order: Order, market_data: MarketData) -> datetime:
        """
        获取订单实际执行时间

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            订单实际执行时间
        """
        latency_seconds = self.calculate_latency(order, market_data)
        return order.timestamp + timedelta(seconds=latency_seconds)

    def get_plugin_type(self) -> str:
        return "latency_model"
