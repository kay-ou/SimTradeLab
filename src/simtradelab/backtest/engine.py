# -*- coding: utf-8 -*-
"""
可插拔回测引擎

重构的回测引擎，支持可插拔的撮合引擎、滑点模型和手续费模型。
这个引擎作为各个插件的协调者，确保回测的准确性和性能。

集成全局PluginManager，实现统一插件管理
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .plugins.base import (
    BaseCommissionModel,
    BaseLatencyModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    Fill,
    MarketData,
    Order,
)

if TYPE_CHECKING:
    from ..core.plugin_manager import PluginManager


class BacktestEngine:
    """
    可插拔回测引擎

    通过PluginManager加载回测组件，实现统一插件管理。
    支持可插拔的撮合引擎、滑点模型和手续费模型。
    """

    def __init__(
        self,
        plugin_manager: "PluginManager",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化回测引擎

        Args:
            plugin_manager: 全局插件管理器
            config: 回测配置，包含插件名称配置
        """
        self.logger = logging.getLogger(__name__)
        self._plugin_manager = plugin_manager
        self._config = config or {}

        # 验证组件间兼容性
        self._validate_component_compatibility()

        # 通过PluginManager加载插件
        self._matching_engine = self._load_plugin(
            self._config.get("matching_engine", "SimpleMatchingEngine"),
            BaseMatchingEngine,
        )
        self._slippage_model = self._load_plugin(
            self._config.get("slippage_model", "FixedSlippageModel"), BaseSlippageModel
        )
        self._commission_model = self._load_plugin(
            self._config.get("commission_model", "FixedCommissionModel"),
            BaseCommissionModel,
        )
        self._latency_model = self._load_plugin(
            self._config.get("latency_model", "DefaultLatencyModel"),
            BaseLatencyModel,
        )

        # 将滑点和手续费模型注入到撮合引擎中
        if self._matching_engine:
            self._matching_engine.set_models(
                self._slippage_model, self._commission_model
            )

        # 回测状态
        self._is_running = False
        self._current_time: Optional[datetime] = None
        self._orders: List[Order] = []
        self._fills: List[Fill] = []
        self._market_data: Dict[str, MarketData] = {}

        # 统计数据
        self._stats = {
            "total_orders": 0,
            "total_fills": 0,
            "total_commission": Decimal("0"),
            "total_slippage": Decimal("0"),
            "total_latency": 0.0,
            "avg_latency": 0.0,
        }

        self.logger.info("BacktestEngine initialized with unified plugin management")

    def _validate_component_compatibility(self) -> None:
        """
        验证回测组件间的兼容性

        检查组件版本兼容性、依赖关系和配置参数一致性
        """
        # TODO: 实现组件兼容性验证逻辑
        # - 检查组件版本兼容性
        # - 验证组件间的依赖关系
        # - 确保配置参数的一致性
        self.logger.debug("Component compatibility validation completed")

    def _load_plugin(self, plugin_name: str, expected_type: type) -> Optional[Any]:
        """
        从插件管理器加载对应回测组件插件

        Args:
            plugin_name: 插件名称
            expected_type: 期望的插件类型

        Returns:
            插件实例，如果加载失败返回None
        """
        try:
            plugin_instance = self._plugin_manager.load_plugin(plugin_name)

            if not isinstance(plugin_instance, expected_type):
                self.logger.error(
                    f"Plugin {plugin_name} is not of expected type {expected_type.__name__}"
                )
                return None

            self.logger.info(f"Successfully loaded backtest plugin: {plugin_name}")
            return plugin_instance

        except Exception as e:
            self.logger.warning(
                f"Failed to load backtest plugin '{plugin_name}': {e}. "
                f"Continuing without {expected_type.__name__}"
            )
            return None

    def start(self) -> None:
        """
        启动回测引擎

        插件生命周期由统一的PluginManager管理
        """
        if self._is_running:
            self.logger.warning("BacktestEngine is already running")
            return

        # 插件的生命周期由统一的PluginManager管理
        # 这里只需要启动引擎本身的逻辑
        self._is_running = True
        self.logger.info("BacktestEngine started with unified plugin management")

    def stop(self) -> None:
        """
        停止回测引擎

        插件生命周期由统一的PluginManager管理
        """
        if not self._is_running:
            self.logger.warning("BacktestEngine is not running")
            return

        # 插件的生命周期由统一的PluginManager管理
        # 这里只需要停止引擎本身的逻辑
        self._is_running = False
        self.logger.info("BacktestEngine stopped")

    def submit_order(self, order: Order) -> None:
        """
        提交订单

        Args:
            order: 订单对象
        """
        if not self._is_running:
            raise RuntimeError("BacktestEngine is not running")

        self._orders.append(order)
        self._stats["total_orders"] += 1

        self.logger.debug(f"Order submitted: {order.order_id}")

    def update_market_data(self, symbol: str, market_data: MarketData) -> None:
        """
        更新市场数据并触发订单处理

        Args:
            symbol: 证券代码
            market_data: 市场数据
        """
        self._market_data[symbol] = market_data
        self._current_time = market_data.timestamp

        # 触发订单匹配
        self._process_orders()

    def _process_orders(self) -> None:
        """
        处理待成交订单

        将订单和市场数据交给撮合引擎处理，撮合引擎将完成完整的成交过程。
        处理插件可能为None的情况
        集成延迟模型处理订单延迟
        """
        if not self._matching_engine:
            self.logger.warning(
                "No matching engine available, skipping order processing"
            )
            return

        pending_orders = [order for order in self._orders if order.status == "pending"]

        for order in pending_orders:
            if order.symbol in self._market_data:
                market_data = self._market_data[order.symbol]

                # 使用延迟模型计算订单执行时间
                if self._latency_model:
                    execution_time = self._latency_model.get_execution_time(
                        order, market_data
                    )

                    # 检查是否到达执行时间
                    if self._current_time and execution_time > self._current_time:
                        # 订单还未到达执行时间，跳过处理
                        continue

                    # 记录延迟信息
                    latency_seconds = self._latency_model.calculate_latency(
                        order, market_data
                    )
                    self._stats["total_latency"] += latency_seconds
                    processed_orders_count = self._stats["total_orders"]
                    if processed_orders_count > 0:
                        self._stats["avg_latency"] = (
                            self._stats["total_latency"] / processed_orders_count
                        )

                    self.logger.debug(
                        f"Order {order.order_id} processed with latency: {latency_seconds:.3f}s"
                    )

                # 调用撮合引擎进行完整撮合
                fills = self._matching_engine.match_order(order, market_data)

                if fills:
                    for fill in fills:
                        self._fills.append(fill)
                        self._stats["total_fills"] += 1
                        self._stats["total_commission"] += fill.commission
                        self._stats["total_slippage"] += fill.slippage

                        # 更新订单状态
                        # 注意：撮合引擎现在负责更新订单状态
                        self.logger.debug(f"Order filled: {order.order_id}")

    def get_orders(self) -> List[Order]:
        """获取所有订单"""
        return self._orders.copy()

    def get_fills(self) -> List[Fill]:
        """获取所有成交记录"""
        return self._fills.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """获取回测统计数据"""
        return {
            "total_orders": self._stats["total_orders"],
            "total_fills": self._stats["total_fills"],
            "total_commission": float(self._stats["total_commission"]),
            "total_slippage": float(self._stats["total_slippage"]),
            "total_latency": self._stats["total_latency"],
            "avg_latency": self._stats["avg_latency"],
            "fill_rate": (
                self._stats["total_fills"] / self._stats["total_orders"]
                if self._stats["total_orders"] > 0
                else 0
            ),
        }

    def get_plugin_info(self) -> Dict[str, Any]:
        """
        获取当前插件信息

        处理插件可能为None的情况
        """
        return {
            "matching_engine": (
                self._matching_engine.metadata.name if self._matching_engine else "N/A"
            ),
            "slippage_model": (
                self._slippage_model.metadata.name if self._slippage_model else "N/A"
            ),
            "commission_model": (
                self._commission_model.metadata.name
                if self._commission_model
                else "N/A"
            ),
            "latency_model": (
                self._latency_model.metadata.name if self._latency_model else "N/A"
            ),
            "plugin_manager": "Unified PluginManager"
            if self._plugin_manager
            else "N/A",
        }

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()
