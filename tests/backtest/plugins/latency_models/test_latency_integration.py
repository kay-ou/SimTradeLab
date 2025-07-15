# -*- coding: utf-8 -*-
"""
测试延迟模型与BacktestEngine的集成
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from simtradelab.backtest.engine import BacktestEngine
from simtradelab.backtest.plugins.base import MarketData, Order
from simtradelab.backtest.plugins.latency_models.default_latency_model import (
    DefaultLatencyModel,
)
from simtradelab.backtest.plugins.latency_models.fixed_latency_model import (
    FixedLatencyModel,
)
from simtradelab.plugins.base import PluginMetadata


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
        from simtradelab.backtest.plugins.matching_engines import SimpleMatchingEngine
        from simtradelab.backtest.plugins.slippage_models import FixedSlippageModel

        mock_matching_engine = SimpleMatchingEngine(metadata)
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
        order = Order(
            order_id="test_order_001",
            symbol="000001",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
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
        engine.submit_order(order)
        engine.update_market_data("000001", market_data)

        # 检查统计信息是否更新
        stats = engine.get_statistics()
        assert stats["total_orders"] == 1
        assert stats["total_latency"] > 0  # 应该有延迟记录
        assert stats["avg_latency"] > 0

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
        from simtradelab.backtest.plugins.matching_engines import SimpleMatchingEngine
        from simtradelab.backtest.plugins.slippage_models import FixedSlippageModel

        mock_matching_engine = SimpleMatchingEngine(metadata)
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
