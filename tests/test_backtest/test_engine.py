# -*- coding: utf-8 -*-
"""
回测引擎测试
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from simtradelab.backtest.engine import BacktestEngine
from simtradelab.backtest.plugins.base import Fill, MarketData, Order


class TestBacktestEngine:
    """测试回测引擎"""

    def test_initialization(self):
        """测试引擎初始化"""
        engine = BacktestEngine()
        assert engine is not None
        assert not engine._is_running

        # 检查可用插件
        available_plugins = engine.get_available_plugins()
        assert "matching_engines" in available_plugins
        assert "slippage_models" in available_plugins
        assert "commission_models" in available_plugins

        # 检查默认插件类型
        assert "simple" in available_plugins["matching_engines"]
        assert "fixed" in available_plugins["slippage_models"]
        assert "china_astock" in available_plugins["commission_models"]

    def test_configure_plugins(self):
        """测试插件配置"""
        engine = BacktestEngine()

        config = {
            "matching_engine": {"type": "simple", "params": {}},
            "slippage_model": {"type": "fixed", "params": {"buy_slippage_rate": 0.001}},
            "commission_model": {
                "type": "fixed",
                "params": {"buy_commission_rate": 0.0003},
            },
        }

        engine.configure_plugins(config)

        plugin_info = engine.get_plugin_info()
        assert plugin_info["matching_engine"] == "SimpleMatchingEngine"
        assert plugin_info["slippage_model"] == "FixedSlippageModel"
        assert plugin_info["commission_model"] == "FixedCommissionModel"

    def test_configure_unknown_plugin(self):
        """测试配置未知插件"""
        engine = BacktestEngine()

        config = {"matching_engine": {"type": "unknown_engine", "params": {}}}

        with pytest.raises(ValueError, match="Unknown matching engine type"):
            engine.configure_plugins(config)

    def test_start_stop_lifecycle(self):
        """测试引擎启动停止生命周期"""
        engine = BacktestEngine()

        # 配置插件
        config = {
            "matching_engine": {"type": "simple", "params": {}},
            "slippage_model": {"type": "fixed", "params": {}},
            "commission_model": {"type": "fixed", "params": {}},
        }
        engine.configure_plugins(config)

        # 测试启动
        assert not engine._is_running
        engine.start()
        assert engine._is_running

        # 测试重复启动
        engine.start()  # 应该不会报错
        assert engine._is_running

        # 测试停止
        engine.stop()
        assert not engine._is_running

        # 测试重复停止
        engine.stop()  # 应该不会报错
        assert not engine._is_running

    def test_context_manager(self):
        """测试上下文管理器"""
        engine = BacktestEngine()

        # 配置插件
        config = {
            "matching_engine": {"type": "simple", "params": {}},
            "slippage_model": {"type": "fixed", "params": {}},
            "commission_model": {"type": "fixed", "params": {}},
        }
        engine.configure_plugins(config)

        # 测试上下文管理器
        with engine as ctx_engine:
            assert ctx_engine is engine
            assert engine._is_running

        assert not engine._is_running

    def test_submit_order_without_engine(self):
        """测试在未启动引擎时提交订单"""
        engine = BacktestEngine()

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        with pytest.raises(RuntimeError, match="BacktestEngine is not running"):
            engine.submit_order(order)

    def test_submit_order_without_matching_engine(self):
        """测试在未配置撮合引擎时提交订单"""
        engine = BacktestEngine()
        engine._is_running = True

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        with pytest.raises(RuntimeError, match="No matching engine configured"):
            engine.submit_order(order)

    def test_complete_order_flow(self):
        """测试完整的订单流程"""
        engine = BacktestEngine()

        # 配置插件
        config = {
            "matching_engine": {"type": "simple", "params": {}},
            "slippage_model": {
                "type": "fixed",
                "params": {"buy_slippage_rate": 0.001, "sell_slippage_rate": 0.001},
            },
            "commission_model": {
                "type": "fixed",
                "params": {
                    "buy_commission_rate": 0.0003,
                    "sell_commission_rate": 0.0003,
                },
            },
        }
        engine.configure_plugins(config)

        # 启动引擎
        engine.start()

        # 创建订单
        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        # 提交订单
        engine.submit_order(order)

        # 检查订单状态
        orders = engine.get_orders()
        assert len(orders) == 1
        assert orders[0].order_id == "test_order"
        assert orders[0].status == "pending"

        # 更新市场数据
        market_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.2"),
            low_price=Decimal("9.8"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        engine.update_market_data("TEST.SH", market_data)

        # 检查成交记录
        fills = engine.get_fills()
        assert len(fills) == 1

        fill = fills[0]
        assert fill.order_id == "test_order"
        assert fill.symbol == "TEST.SH"
        assert fill.side == "buy"
        assert fill.quantity == Decimal("100")
        assert fill.commission > 0
        assert fill.slippage > 0

        # 检查订单状态更新
        orders = engine.get_orders()
        assert orders[0].status == "filled"
        assert orders[0].filled_quantity == Decimal("100")

        # 检查统计数据
        stats = engine.get_statistics()
        assert stats["total_orders"] == 1
        assert stats["total_fills"] == 1
        assert stats["fill_rate"] == 1.0
        assert stats["total_commission"] > 0
        assert stats["total_slippage"] > 0

        # 停止引擎
        engine.stop()

    def test_register_custom_plugin(self):
        """测试注册自定义插件"""
        engine = BacktestEngine()

        # 创建模拟插件类
        class MockMatchingEngine:
            METADATA = Mock()
            METADATA.name = "MockMatchingEngine"

        # 注册插件
        engine.register_plugin("matching_engines", "mock", MockMatchingEngine)

        # 检查注册结果
        available = engine.get_available_plugins()
        assert "mock" in available["matching_engines"]

    def test_register_unknown_category(self):
        """测试注册未知类别的插件"""
        engine = BacktestEngine()

        class MockPlugin:
            pass

        with pytest.raises(ValueError, match="Unknown plugin category"):
            engine.register_plugin("unknown_category", "mock", MockPlugin)

    def test_get_statistics_empty(self):
        """测试获取空统计数据"""
        engine = BacktestEngine()

        stats = engine.get_statistics()
        assert stats["total_orders"] == 0
        assert stats["total_fills"] == 0
        assert stats["total_commission"] == 0
        assert stats["total_slippage"] == 0
        assert stats["fill_rate"] == 0

    def test_multiple_orders_and_fills(self):
        """测试多个订单和成交"""
        engine = BacktestEngine()

        # 配置插件
        config = {
            "matching_engine": {"type": "simple", "params": {}},
            "slippage_model": {"type": "fixed", "params": {}},
            "commission_model": {"type": "fixed", "params": {}},
        }
        engine.configure_plugins(config)
        engine.start()

        # 创建多个订单
        orders = [
            Order(
                order_id=f"order_{i}",
                symbol="TEST.SH",
                side="buy",
                quantity=Decimal("100"),
                price=Decimal("10.0"),
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]

        # 提交订单
        for order in orders:
            engine.submit_order(order)

        # 更新市场数据
        market_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.2"),
            low_price=Decimal("9.8"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        engine.update_market_data("TEST.SH", market_data)

        # 检查结果
        assert len(engine.get_orders()) == 3
        assert len(engine.get_fills()) == 3

        stats = engine.get_statistics()
        assert stats["total_orders"] == 3
        assert stats["total_fills"] == 3
        assert stats["fill_rate"] == 1.0

        engine.stop()

    @patch("simtradelab.backtest.engine.logging")
    def test_logging(self, mock_logging):
        """测试日志记录"""
        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        engine = BacktestEngine()

        # 验证初始化日志
        mock_logger.info.assert_called_with(
            "BacktestEngine initialized with pluggable components"
        )

        # 配置插件并验证日志
        config = {
            "matching_engine": {"type": "simple", "params": {}},
            "slippage_model": {"type": "fixed", "params": {}},
            "commission_model": {"type": "fixed", "params": {}},
        }
        engine.configure_plugins(config)

        # 验证配置日志
        assert mock_logger.info.call_count >= 4  # 初始化 + 3个插件配置
