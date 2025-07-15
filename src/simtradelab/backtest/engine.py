# -*- coding: utf-8 -*-
"""
可插拔回测引擎

重构的回测引擎，支持可插拔的撮合引擎、滑点模型和手续费模型。
这个引擎作为各个插件的协调者，确保回测的准确性和性能。
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .plugins.base import (
    BaseCommissionModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    Fill,
    MarketData,
    Order,
)


class BacktestEngine:
    """
    可插拔回测引擎

    通过依赖注入接收已经实例化好的撮合引擎、滑点模型和手续费模型插件，
    实现灵活的回测策略组合。
    """

    def __init__(
        self,
        matching_engine: BaseMatchingEngine,
        slippage_model: Optional[BaseSlippageModel] = None,
        commission_model: Optional[BaseCommissionModel] = None,
    ):
        """
        初始化回测引擎

        Args:
            matching_engine: 撮合引擎插件实例
            slippage_model: 滑点模型插件实例
            commission_model: 手续费模型插件实例
        """
        self.logger = logging.getLogger(__name__)

        # 插件实例通过依赖注入传入
        if not isinstance(matching_engine, BaseMatchingEngine):
            raise TypeError("matching_engine must be an instance of BaseMatchingEngine")
        self._matching_engine = matching_engine
        self._slippage_model = slippage_model
        self._commission_model = commission_model
        
        # 将滑点和手续费模型注入到撮合引擎中
        self._matching_engine.set_models(self._slippage_model, self._commission_model)

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
        }

        self.logger.info("BacktestEngine initialized with injected pluggable components")

    def start(self) -> None:
        """启动回测引擎"""
        if self._is_running:
            self.logger.warning("BacktestEngine is already running")
            return

        # 插件的生命周期由外部的PluginManager管理，这里不再调用
        self._is_running = True
        self.logger.info("BacktestEngine started")

    def stop(self) -> None:
        """停止回测引擎"""
        if not self._is_running:
            self.logger.warning("BacktestEngine is not running")
            return
        
        # 插件的生命周期由外部的PluginManager管理
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
        """
        pending_orders = [order for order in self._orders if order.status == "pending"]

        for order in pending_orders:
            if order.symbol in self._market_data:
                market_data = self._market_data[order.symbol]

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
            "fill_rate": (
                self._stats["total_fills"] / self._stats["total_orders"]
                if self._stats["total_orders"] > 0
                else 0
            ),
        }

    def get_plugin_info(self) -> Dict[str, Any]:
        """获取当前插件信息"""
        return {
            "matching_engine": (
                self._matching_engine.metadata.name if self._matching_engine else "N/A"
            ),
            "slippage_model": (
                self._slippage_model.metadata.name if self._slippage_model else "N/A"
            ),
            "commission_model": (
                self._commission_model.metadata.name if self._commission_model else "N/A"
            ),
        }

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()
