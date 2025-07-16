# -*- coding: utf-8 -*-
"""
测试延迟模型与BacktestEngine的集成
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple
from unittest.mock import Mock

from simtradelab.backtest.engine import BacktestEngine
from simtradelab.backtest.plugins.base import Fill, MarketData, Order
from simtradelab.backtest.plugins.latency_models.default_latency_model import (
    DefaultLatencyModel,
)
from simtradelab.backtest.plugins.latency_models.fixed_latency_model import (
    FixedLatencyModel,
)
from simtradelab.backtest.plugins.matching_engines import DepthMatchingEngine
from simtradelab.plugins.base import PluginMetadata


# 为测试创建一个可实例化的具体类
class ConcreteDepthMatchingEngine(DepthMatchingEngine):
    def add_order(self, order: Order) -> None:
        # 在这个测试中，我们不关心实际的订单添加逻辑
        # 只需满足抽象方法的要求
        if not hasattr(self, "orders"):
            self.orders = []
        self.orders.append(order)

    def trigger_matching(
        self, symbol: str, market_data: MarketData
    ) -> Tuple[List[Fill], List[Order]]:
        # 模拟撮合过程，在这个测试中，我们假设订单总是能成交
        fills = []
        filled_orders = []

        # 这是一个简化的逻辑，仅用于测试延迟集成
        # 假设总是买卖双方匹配
        if hasattr(self, "orders") and len(self.orders) >= 2:
            buy_order = self.orders[0]
            sell_order = self.orders[1]
            fill_qty = min(buy_order.quantity, sell_order.quantity)
            fill_price = market_data.close_price

            fills.append(
                Fill(
                    order_id=buy_order.order_id,
                    symbol=symbol,
                    side="buy",
                    quantity=fill_qty,
                    price=fill_price,
                    timestamp=datetime.now(),
                )
            )
            fills.append(
                Fill(
                    order_id=sell_order.order_id,
                    symbol=symbol,
                    side="sell",
                    quantity=fill_qty,
                    price=fill_price,
                    timestamp=datetime.now(),
                )
            )

            buy_order.status = "filled"
            sell_order.status = "filled"
            filled_orders.extend([buy_order, sell_order])
            self.orders = []  # 清空订单

        return fills, filled_orders

    def _on_initialize(self) -> None:
        pass

    def _on_start(self) -> None:
        pass

    def _on_stop(self) -> None:
        pass


class TestLatencyModelIntegration:
    """测试延迟模型与BacktestEngine的集成"""

    def setup_method(self):
        """设置测试环境"""
        self.mock_plugin_manager = Mock()
        self.config = {
            "matching_engine": "TestMatchingEngine",
            "slippage_model": "TestSlippageModel",
            "commission_model": "TestCommissionModel",
            "latency_model": "TestLatencyModel",
        }

    def test_latency_model_loading(self):
        """测试延迟模型加载"""
        # 创建测试延迟模型
        metadata = PluginMetadata(
            name="TestLatencyModel",
            version="1.0.0",
            description="Test latency model",
            author="TestAuthor",
        )
        test_latency_model = FixedLatencyModel(metadata)

        # 配置mock插件管理器
        def mock_load_plugin(plugin_name):
            if plugin_name == "TestLatencyModel":
                return test_latency_model
            return None

        self.mock_plugin_manager.load_plugin.side_effect = mock_load_plugin

        # 创建BacktestEngine
        engine = BacktestEngine(self.mock_plugin_manager, self.config)

        # 验证延迟模型被正确加载
        assert engine._latency_model is not None
        assert engine._latency_model.get_plugin_type() == "latency_model"

    def test_latency_model_in_plugin_info(self):
        """测试延迟模型在插件信息中显示"""
        metadata = PluginMetadata(
            name="TestLatencyModel",
            version="1.0.0",
            description="Test latency model",
            author="TestAuthor",
        )
        test_latency_model = FixedLatencyModel(metadata)

        def mock_load_plugin(plugin_name):
            if plugin_name == "TestLatencyModel":
                return test_latency_model
            return None

        self.mock_plugin_manager.load_plugin.side_effect = mock_load_plugin

        engine = BacktestEngine(self.mock_plugin_manager, self.config)
        plugin_info = engine.get_plugin_info()

        assert "latency_model" in plugin_info
        assert plugin_info["latency_model"] == "TestLatencyModel"

    def test_latency_statistics(self):
        """测试延迟统计信息"""
        metadata = PluginMetadata(
            name="TestLatencyModel",
            version="1.0.0",
            description="Test latency model",
            author="TestAuthor",
        )
        test_latency_model = FixedLatencyModel(metadata)

        def mock_load_plugin(plugin_name):
            if plugin_name == "TestLatencyModel":
                return test_latency_model
            return None

        self.mock_plugin_manager.load_plugin.side_effect = mock_load_plugin

        engine = BacktestEngine(self.mock_plugin_manager, self.config)

        # 检查统计信息包含延迟相关字段
        stats = engine.get_statistics()
        assert "total_latency" in stats
        assert "avg_latency" in stats
        assert stats["total_latency"] == 0.0
        assert stats["avg_latency"] == 0.0

    def test_order_processing_with_latency(self):
        """测试带延迟的订单处理"""
        # 创建测试组件
        metadata = PluginMetadata(
            name="TestComponent",
            version="1.0.0",
            description="Test component",
            author="TestAuthor",
        )

        test_latency_model = FixedLatencyModel(metadata)

        # 创建真正的插件实例而不是Mock
        from simtradelab.backtest.plugins.commission_models import FixedCommissionModel
        from simtradelab.backtest.plugins.config import (
            FixedCommissionModelConfig,
            FixedSlippageModelConfig,
        )
        from simtradelab.backtest.plugins.slippage_models import FixedSlippageModel

        mock_matching_engine = ConcreteDepthMatchingEngine(metadata)
        mock_slippage_model = FixedSlippageModel(metadata, FixedSlippageModelConfig())
        mock_commission_model = FixedCommissionModel(
            metadata, FixedCommissionModelConfig()
        )

        def mock_load_plugin(plugin_name):
            if plugin_name == "TestLatencyModel":
                return test_latency_model
            elif plugin_name == "TestMatchingEngine":
                return mock_matching_engine
            elif plugin_name == "TestSlippageModel":
                return mock_slippage_model
            elif plugin_name == "TestCommissionModel":
                return mock_commission_model
            return None

        self.mock_plugin_manager.load_plugin.side_effect = mock_load_plugin

        engine = BacktestEngine(self.mock_plugin_manager, self.config)
        engine.start()

        # 创建测试订单和市场数据
        order_time = datetime.now()
        buy_order = Order(
            order_id="test_order_001",
            symbol="000001",
            side="buy",
            quantity=Decimal("100"),
            order_type="limit",
            price=Decimal("10.2"),
            timestamp=order_time,
        )
        sell_order = Order(
            order_id="test_order_002",
            symbol="000001",
            side="sell",
            quantity=Decimal("100"),
            order_type="limit",
            price=Decimal("10.2"),
            timestamp=order_time,
        )

        # 市场数据时间应该晚于订单+延迟时间，这样订单才能被处理
        # FixedLatencyModel的默认延迟是100ms，所以我们设置市场数据时间晚200ms
        market_data_time = order_time + timedelta(milliseconds=200)
        market_data = MarketData(
            symbol="000001",
            timestamp=market_data_time,
            open_price=Decimal("10.0"),
            high_price=Decimal("10.5"),
            low_price=Decimal("9.5"),
            close_price=Decimal("10.2"),
            volume=Decimal("10000"),
        )

        # 提交订单和更新市场数据
        engine.submit_order(sell_order)
        engine.submit_order(buy_order)
        engine.update_market_data("000001", market_data)

        # 检查统计信息是否更新
        stats = engine.get_statistics()
        assert stats["total_orders"] == 2
        assert stats["total_latency"] > 0  # 应该有延迟记录
        assert stats["avg_latency"] > 0
        assert len(engine.get_fills()) == 2

    def test_order_execution_timing(self):
        """测试订单执行时间控制"""
        # 创建带有较长延迟的测试模型
        metadata = PluginMetadata(
            name="TestLatencyModel",
            version="1.0.0",
            description="Test latency model",
            author="TestAuthor",
        )

        # 创建自定义延迟模型，返回较长延迟
        class CustomLatencyModel(FixedLatencyModel):
            def calculate_latency(self, order, market_data):
                return 10.0  # 10秒延迟

            def get_execution_time(self, order, market_data):
                from datetime import timedelta

                return order.timestamp + timedelta(seconds=10)

        test_latency_model = CustomLatencyModel(metadata)

        # 创建真正的插件实例
        from simtradelab.backtest.plugins.commission_models import FixedCommissionModel
        from simtradelab.backtest.plugins.config import (
            FixedCommissionModelConfig,
            FixedSlippageModelConfig,
        )
        from simtradelab.backtest.plugins.slippage_models import FixedSlippageModel

        mock_matching_engine = ConcreteDepthMatchingEngine(metadata)
        mock_slippage_model = FixedSlippageModel(metadata, FixedSlippageModelConfig())
        mock_commission_model = FixedCommissionModel(
            metadata, FixedCommissionModelConfig()
        )

        def mock_load_plugin(plugin_name):
            if plugin_name == "TestLatencyModel":
                return test_latency_model
            elif plugin_name == "TestMatchingEngine":
                return mock_matching_engine
            elif plugin_name == "TestSlippageModel":
                return mock_slippage_model
            elif plugin_name == "TestCommissionModel":
                return mock_commission_model
            return None

        self.mock_plugin_manager.load_plugin.side_effect = mock_load_plugin

        engine = BacktestEngine(self.mock_plugin_manager, self.config)
        engine.start()

        # 创建早于执行时间的市场数据
        order_time = datetime.now()
        early_market_time = order_time  # 同时间

        order = Order(
            order_id="test_order_001",
            symbol="000001",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            timestamp=order_time,
        )

        market_data = MarketData(
            symbol="000001",
            timestamp=early_market_time,
            open_price=Decimal("10.0"),
            high_price=Decimal("10.5"),
            low_price=Decimal("9.5"),
            close_price=Decimal("10.2"),
            volume=Decimal("10000"),
        )

        # 提交订单
        engine.submit_order(order)

        # 更新市场数据（应该因为延迟而不执行）
        engine.update_market_data("000001", market_data)

        # 由于订单还没到执行时间，应该没有成交记录
        fills = engine.get_fills()
        assert len(fills) == 0, "Order should not be filled due to latency"

        # 订单应该仍然是pending状态
        orders = engine.get_orders()
        assert len(orders) == 1
        assert orders[0].status == "pending"

    def test_no_latency_model_fallback(self):
        """测试没有延迟模型时的回退行为"""

        def mock_load_plugin(plugin_name):
            if plugin_name == "TestLatencyModel":
                return None  # 模拟加载失败
            return None

        self.mock_plugin_manager.load_plugin.side_effect = mock_load_plugin

        engine = BacktestEngine(self.mock_plugin_manager, self.config)

        # 应该能正常初始化，延迟模型为None
        assert engine._latency_model is None

        # 插件信息应该显示N/A
        plugin_info = engine.get_plugin_info()
        assert plugin_info["latency_model"] == "N/A"

    def test_default_latency_model_config(self):
        """测试默认延迟模型配置"""
        config = {}  # 空配置，应该使用默认值

        def mock_load_plugin(plugin_name):
            if plugin_name == "DefaultLatencyModel":
                metadata = PluginMetadata(
                    name="DefaultLatencyModel",
                    version="1.0.0",
                    description="Default latency model",
                    author="TestAuthor",
                )
                return DefaultLatencyModel(metadata)
            return None

        self.mock_plugin_manager.load_plugin.side_effect = mock_load_plugin

        engine = BacktestEngine(self.mock_plugin_manager, config)

        # 应该使用默认的延迟模型
        assert engine._latency_model is not None
        assert engine._latency_model.get_plugin_type() == "latency_model"
