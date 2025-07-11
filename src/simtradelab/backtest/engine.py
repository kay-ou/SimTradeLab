# -*- coding: utf-8 -*-
"""
可插拔回测引擎

重构的回测引擎，支持可插拔的撮合引擎、滑点模型和手续费模型。
这个引擎作为各个插件的协调者，确保回测的准确性和性能。
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
import logging

from .plugins.base import (
    BaseMatchingEngine,
    BaseSlippageModel,
    BaseCommissionModel,
    Order,
    Fill,
    MarketData,
)
from .plugins.matching_engines import (
    SimpleMatchingEngine,
    DepthMatchingEngine,
    StrictLimitMatchingEngine,
)
from .plugins.slippage_models import (
    FixedSlippageModel,
    DynamicSlippageModel,
    VolatilityBasedSlippageModel,
)
from .plugins.commission_models import (
    ChinaAStockCommissionModel,
    FixedCommissionModel,
    TieredCommissionModel,
)


class BacktestEngine:
    """
    可插拔回测引擎
    
    支持动态配置不同的撮合引擎、滑点模型和手续费模型，
    实现灵活的回测策略组合。
    """
    
    def __init__(
        self,
        matching_engine: Optional[BaseMatchingEngine] = None,
        slippage_model: Optional[BaseSlippageModel] = None,
        commission_model: Optional[BaseCommissionModel] = None,
    ):
        """
        初始化回测引擎
        
        Args:
            matching_engine: 撮合引擎插件
            slippage_model: 滑点模型插件
            commission_model: 手续费模型插件
        """
        self.logger = logging.getLogger(__name__)
        
        # 插件实例
        self._matching_engine = matching_engine
        self._slippage_model = slippage_model
        self._commission_model = commission_model
        
        # 注册可用的插件类
        self._available_plugins = {
            "matching_engines": {
                "simple": SimpleMatchingEngine,
                "depth": DepthMatchingEngine,
                "strict_limit": StrictLimitMatchingEngine,
            },
            "slippage_models": {
                "fixed": FixedSlippageModel,
                "dynamic": DynamicSlippageModel,
                "volatility": VolatilityBasedSlippageModel,
            },
            "commission_models": {
                "china_astock": ChinaAStockCommissionModel,
                "fixed": FixedCommissionModel,
                "tiered": TieredCommissionModel,
            },
        }
        
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
        
        self.logger.info("BacktestEngine initialized with pluggable components")
    
    def configure_plugins(self, config: Dict[str, Any]) -> None:
        """
        根据配置创建和设置插件
        
        Args:
            config: 插件配置字典
        """
        # 配置撮合引擎
        if "matching_engine" in config:
            engine_config = config["matching_engine"]
            engine_type = engine_config.get("type", "simple")
            engine_params = engine_config.get("params", {})
            
            if engine_type in self._available_plugins["matching_engines"]:
                engine_class = self._available_plugins["matching_engines"][engine_type]
                metadata = engine_class.METADATA
                self._matching_engine = engine_class(metadata, engine_params)
                self.logger.info(f"Configured matching engine: {engine_type}")
            else:
                raise ValueError(f"Unknown matching engine type: {engine_type}")
        
        # 配置滑点模型
        if "slippage_model" in config:
            slippage_config = config["slippage_model"]
            slippage_type = slippage_config.get("type", "fixed")
            slippage_params = slippage_config.get("params", {})
            
            if slippage_type in self._available_plugins["slippage_models"]:
                slippage_class = self._available_plugins["slippage_models"][slippage_type]
                metadata = slippage_class.METADATA
                self._slippage_model = slippage_class(metadata, slippage_params)
                self.logger.info(f"Configured slippage model: {slippage_type}")
            else:
                raise ValueError(f"Unknown slippage model type: {slippage_type}")
        
        # 配置手续费模型
        if "commission_model" in config:
            commission_config = config["commission_model"]
            commission_type = commission_config.get("type", "fixed")
            commission_params = commission_config.get("params", {})
            
            if commission_type in self._available_plugins["commission_models"]:
                commission_class = self._available_plugins["commission_models"][commission_type]
                metadata = commission_class.METADATA
                self._commission_model = commission_class(metadata, commission_params)
                self.logger.info(f"Configured commission model: {commission_type}")
            else:
                raise ValueError(f"Unknown commission model type: {commission_type}")
    
    def start(self) -> None:
        """启动回测引擎"""
        if self._is_running:
            self.logger.warning("BacktestEngine is already running")
            return
        
        # 初始化并启动所有插件
        if self._matching_engine:
            self._matching_engine.initialize()
            self._matching_engine.start()
        if self._slippage_model:
            self._slippage_model.initialize()
            self._slippage_model.start()
        if self._commission_model:
            self._commission_model.initialize()
            self._commission_model.start()
        
        self._is_running = True
        self.logger.info("BacktestEngine started")
    
    def stop(self) -> None:
        """停止回测引擎"""
        if not self._is_running:
            self.logger.warning("BacktestEngine is not running")
            return
        
        # 停止所有插件
        if self._matching_engine:
            self._matching_engine.stop()
        if self._slippage_model:
            self._slippage_model.stop()
        if self._commission_model:
            self._commission_model.stop()
        
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
        
        if not self._matching_engine:
            raise RuntimeError("No matching engine configured")
        
        self._orders.append(order)
        self._stats["total_orders"] += 1
        
        self.logger.debug(f"Order submitted: {order.order_id}")
    
    def update_market_data(self, symbol: str, market_data: MarketData) -> None:
        """
        更新市场数据
        
        Args:
            symbol: 证券代码
            market_data: 市场数据
        """
        self._market_data[symbol] = market_data
        self._current_time = market_data.timestamp
        
        # 触发订单匹配
        self._process_orders()
    
    def _process_orders(self) -> None:
        """处理待成交订单"""
        if not self._matching_engine:
            return
        
        pending_orders = [order for order in self._orders if order.status == "pending"]
        
        for order in pending_orders:
            if order.symbol in self._market_data:
                market_data = self._market_data[order.symbol]
                
                # 尝试匹配订单
                if self._matching_engine.can_match(order, market_data):
                    fill_price = self._matching_engine.get_fill_price(order, market_data)
                    fill_quantity = self._matching_engine.get_fill_quantity(order, market_data)
                    
                    # 创建成交记录
                    fill = Fill(
                        order_id=order.order_id,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=fill_quantity,
                        price=fill_price,
                        timestamp=self._current_time or datetime.now(),
                        commission=Decimal("0"),  # 将在后面计算
                        slippage=Decimal("0"),    # 将在后面计算
                    )
                    
                    # 计算滑点
                    if self._slippage_model:
                        slippage = self._slippage_model.calculate_slippage(
                            order, market_data, fill_price
                        )
                        fill.slippage = slippage
                        self._stats["total_slippage"] += slippage
                    
                    # 计算手续费
                    if self._commission_model:
                        commission = self._commission_model.calculate_commission(fill)
                        fill.commission = commission
                        self._stats["total_commission"] += commission
                    
                    # 记录成交
                    self._fills.append(fill)
                    self._stats["total_fills"] += 1
                    
                    # 更新订单状态
                    order.status = "filled"
                    order.filled_quantity = fill_quantity
                    order.avg_fill_price = fill_price
                    
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
                self._matching_engine.metadata.name if self._matching_engine else None
            ),
            "slippage_model": (
                self._slippage_model.metadata.name if self._slippage_model else None
            ),
            "commission_model": (
                self._commission_model.metadata.name if self._commission_model else None
            ),
        }
    
    def get_available_plugins(self) -> Dict[str, List[str]]:
        """获取可用的插件列表"""
        return {
            "matching_engines": list(self._available_plugins["matching_engines"].keys()),
            "slippage_models": list(self._available_plugins["slippage_models"].keys()),
            "commission_models": list(self._available_plugins["commission_models"].keys()),
        }
    
    def register_plugin(
        self,
        category: str,
        name: str,
        plugin_class: Type[BaseMatchingEngine | BaseSlippageModel | BaseCommissionModel],
    ) -> None:
        """
        注册新的插件类
        
        Args:
            category: 插件类别 (matching_engines, slippage_models, commission_models)
            name: 插件名称
            plugin_class: 插件类
        """
        if category not in self._available_plugins:
            raise ValueError(f"Unknown plugin category: {category}")
        
        self._available_plugins[category][name] = plugin_class
        self.logger.info(f"Registered plugin: {category}.{name}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()