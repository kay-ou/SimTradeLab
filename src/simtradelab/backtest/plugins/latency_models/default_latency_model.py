# -*- coding: utf-8 -*-
"""
默认延迟模型实现

提供基础的延迟模型实现，考虑市场条件和订单类型。
"""

from datetime import datetime, timedelta
from typing import Optional

from simtradelab.backtest.plugins.base import BaseLatencyModel, MarketData, Order
from simtradelab.plugins.base import PluginMetadata
from simtradelab.plugins.config.base_config import BasePluginConfig


class DefaultLatencyModelConfig(BasePluginConfig):
    """默认延迟模型配置"""

    base_latency_ms: int = 50  # 基础延迟（毫秒）
    market_order_latency_ms: int = 30  # 市价单延迟（毫秒）
    limit_order_latency_ms: int = 100  # 限价单延迟（毫秒）
    volume_impact_factor: float = 0.1  # 成交量影响因子
    max_latency_ms: int = 1000  # 最大延迟（毫秒）


class DefaultLatencyModel(BaseLatencyModel):
    config_model = DefaultLatencyModelConfig
    """
    默认延迟模型

    根据订单类型、市场条件和成交量计算延迟时间。
    """

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[DefaultLatencyModelConfig] = None,
    ):
        super().__init__(metadata, config)
        self._config = config or DefaultLatencyModelConfig()

    METADATA = PluginMetadata(
        name="default_latency_model",
        version="1.0.0",
        description="默认延迟模型",
        author="SimTradeLab",
        category="latency_model",
        tags=["backtest", "latency", "default"],
    )

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
        base_latency = self._config.base_latency_ms / 1000.0

        # 根据订单类型调整延迟
        if order.order_type == "market":
            type_latency = self._config.market_order_latency_ms / 1000.0
        else:
            type_latency = self._config.limit_order_latency_ms / 1000.0

        # 根据成交量影响延迟
        volume_impact = (
            float(order.quantity)
            / float(market_data.volume)
            * self._config.volume_impact_factor
        )

        # 计算总延迟
        total_latency = base_latency + type_latency + volume_impact

        # 限制最大延迟
        max_latency = self._config.max_latency_ms / 1000.0
        return min(total_latency, max_latency)

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
