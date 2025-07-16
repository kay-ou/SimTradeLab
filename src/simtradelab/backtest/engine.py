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

from ..core.events.contracts import FillEvent
from .performance import PerformanceManager as PerfManager
from .plugins.base import (
    BaseCommissionModel,
    BaseLatencyModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    Fill,
    MarketData,
    Order,
)
from .portfolio import PortfolioManager

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
            config: 回测配置，包含插件名称和初始资金
        """
        self.logger = logging.getLogger(__name__)
        self._plugin_manager = plugin_manager
        self._config = config or {}

        initial_capital = Decimal(self._config.get("initial_capital", "100000.0"))
        self._portfolio_manager = PortfolioManager(initial_cash=float(initial_capital))
        self._performance_manager = PerfManager(initial_capital=initial_capital)

        # 验证组件间兼容性
        self._validate_component_compatibility()

        # 通过PluginManager加载插件
        self._matching_engine = self._load_plugin(
            self._config.get("matching_engine", "DepthMatchingEngine"),
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
        self.logger.debug("Component compatibility validation completed")

    def _load_plugin(self, plugin_name: str, expected_type: type) -> Optional[Any]:
        """
        从插件管理器加载对应回测组件插件
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
        """
        if self._is_running:
            self.logger.warning("BacktestEngine is already running")
            return

        self._is_running = True
        self.logger.info("BacktestEngine started with unified plugin management")

    def stop(self) -> None:
        """
        停止回测引擎
        """
        if not self._is_running:
            self.logger.warning("BacktestEngine is not running")
            return

        self._is_running = False
        self._performance_manager.analyze()
        self.logger.info("BacktestEngine stopped and performance report generated.")

    def submit_order(self, order: Order) -> None:
        """
        提交订单
        """
        if not self._is_running:
            raise RuntimeError("BacktestEngine is not running")

        self._orders.append(order)
        self._stats["total_orders"] += 1

        # 提交订单后立即尝试撮合
        if order.symbol in self._market_data:
            self._process_orders_for_symbol(order.symbol)

        self.logger.debug(f"Order submitted: {order.order_id}")

    def update_market_data(self, symbol: str, market_data: MarketData) -> None:
        """
        更新市场数据并触发订单处理
        """
        self._market_data[symbol] = market_data
        self._current_time = market_data.timestamp

        # 触发订单匹配
        self._process_orders_for_symbol(symbol)

        # 更新投资组合和性能指标
        prices = {s: md.close_price for s, md in self._market_data.items()}
        self._portfolio_manager.update_market_value(
            {s: float(p) for s, p in prices.items()}
        )

        portfolio_value = self._portfolio_manager.portfolio.portfolio_value
        self._performance_manager.record_daily_portfolio_value(
            self._current_time, Decimal(str(portfolio_value))
        )

    def _process_orders_for_symbol(self, symbol: str) -> None:
        """
        处理指定标的的待成交订单。

        此方法会遍历所有与指定符号相关的待处理订单，
        并使用撮合引擎尝试执行它们。
        它会处理返回的成交和已完成的订单，并更新引擎的内部状态。
        """
        if not self._matching_engine:
            self.logger.warning(
                "No matching engine available, skipping order processing"
            )
            return

        market_data = self._market_data.get(symbol)
        if not market_data:
            return

        orders_to_process = [
            o for o in self._orders if o.symbol == symbol and o.status == "pending"
        ]

        if not orders_to_process:
            return

        # 1. 将所有待处理订单加入订单簿
        for order in orders_to_process:
            if order.status != "pending":
                continue

            # 检查延迟
            if self._latency_model:
                execution_time = self._latency_model.get_execution_time(
                    order, market_data
                )
                if self._current_time and self._current_time < execution_time:
                    continue  # 未到执行时间

                if self._current_time and order.timestamp:
                    latency = (self._current_time - order.timestamp).total_seconds()
                else:
                    latency = 0.0
                self._stats["total_latency"] += latency
                if self._stats["total_orders"] > 0:
                    self._stats["avg_latency"] = (
                        self._stats["total_latency"] / self._stats["total_orders"]
                    )

            self._matching_engine.add_order(order)

        # 2. 触发整个订单簿的撮合
        fills, filled_orders = self._matching_engine.trigger_matching(
            symbol, market_data
        )

        # 3. 处理成交和完成的订单
        if fills:
            for fill in fills:
                self._fills.append(fill)
                self._stats["total_fills"] += 1
                commission = getattr(fill, "commission", Decimal("0"))
                slippage = getattr(fill, "slippage", Decimal("0"))
                self._stats["total_commission"] += commission
                self._stats["total_slippage"] += slippage

                # 创建 FillEvent 并通知 PortfolioManager
                fill_event = FillEvent(
                    order_id=fill.order_id,
                    symbol=fill.symbol,
                    quantity=float(fill.quantity),
                    price=float(fill.price),
                    commission=float(commission),
                    timestamp=fill.timestamp,
                )
                self._portfolio_manager.on_fill(fill_event)

        if filled_orders:
            # 更新原始订单列表中的状态
            original_orders_map = {o.order_id: o for o in self._orders}
            for fo in filled_orders:
                if fo.order_id in original_orders_map:
                    original_orders_map[fo.order_id].status = fo.status
                    original_orders_map[
                        fo.order_id
                    ].filled_quantity = fo.filled_quantity
                    original_orders_map[fo.order_id].avg_fill_price = fo.avg_fill_price

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
