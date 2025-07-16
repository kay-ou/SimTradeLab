# -*- coding: utf-8 -*-
"""
网络延迟模型实现

模拟网络延迟和交易所处理时间。
"""

import random
from datetime import datetime, timedelta
from typing import Optional

from simtradelab.plugins.base import PluginMetadata
from simtradelab.plugins.config.base_config import BasePluginConfig

from ..base import BaseLatencyModel, MarketData, Order


class NetworkLatencyModelConfig(BasePluginConfig):
    """网络延迟模型配置"""

    base_network_latency_ms: int = 20  # 基础网络延迟（毫秒）
    exchange_processing_ms: int = 50  # 交易所处理时间（毫秒）
    variance_factor: float = 0.3  # 延迟变异因子
    peak_hours_multiplier: float = 1.5  # 高峰时段延迟倍数
    peak_start_hour: int = 9  # 高峰时段开始时间
    peak_end_hour: int = 15  # 高峰时段结束时间


class NetworkLatencyModel(BaseLatencyModel):
    """
    网络延迟模型

    模拟真实的网络延迟和交易所处理时间，包含随机性和时间段影响。
    """

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[NetworkLatencyModelConfig] = None,
    ):
        super().__init__(metadata, config)
        self._config = config or NetworkLatencyModelConfig()

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
        # 基础延迟
        base_latency = (
            self._config.base_network_latency_ms + self._config.exchange_processing_ms
        ) / 1000.0

        # 添加随机变异
        variance = base_latency * self._config.variance_factor
        random_factor = random.uniform(-variance, variance)  # nosec B311

        # 检查是否在高峰时段
        current_hour = order.timestamp.hour
        if self._config.peak_start_hour <= current_hour <= self._config.peak_end_hour:
            peak_multiplier = self._config.peak_hours_multiplier
        else:
            peak_multiplier = 1.0

        # 计算总延迟
        total_latency = (base_latency + random_factor) * peak_multiplier

        # 确保延迟不为负数
        return max(0.001, total_latency)  # 最小1毫秒

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
