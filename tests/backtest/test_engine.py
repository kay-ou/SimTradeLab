# -*- coding: utf-8 -*-
"""
回测引擎测试 (重构后)
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from simtradelab.backtest.engine import BacktestEngine
from simtradelab.backtest.plugins.base import (
    BaseCommissionModel,
    BaseLatencyModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    Fill,
    MarketData,
    Order,
    PluginMetadata,
)
from simtradelab.core.plugin_manager import PluginManager
from tests.backtest.plugins.test_matching_engines import ConcreteDepthMatchingEngine


@pytest.fixture
def mock_plugin_manager():
    """提供一个模拟的插件管理器"""
    manager = MagicMock(spec=PluginManager)

    # 模拟加载各种插件
    def load_plugin_side_effect(plugin_name):
        metadata = PluginMetadata(
            name=plugin_name,
            version="1.0.0",
            description=f"{plugin_name} instance",
            author="Test",
        )
        if "Slippage" in plugin_name:
            return MagicMock(spec=BaseSlippageModel, metadata=metadata)
        if "Commission" in plugin_name:
            return MagicMock(spec=BaseCommissionModel, metadata=metadata)
        if "Latency" in plugin_name:
            mock_latency = MagicMock(spec=BaseLatencyModel, metadata=metadata)
            # 确保 get_execution_time 返回一个可比较的 datetime 对象
            mock_latency.get_execution_time.side_effect = (
                lambda order, market_data: order.timestamp
            )
            return mock_latency
        # 对于撮合引擎，返回一个具体的、可工作的实例
        if "DepthMatchingEngine" in plugin_name:
            return ConcreteDepthMatchingEngine(metadata=metadata)
        return MagicMock(spec=BaseMatchingEngine, metadata=metadata)

    manager.load_plugin.side_effect = load_plugin_side_effect
    return manager


@pytest.fixture
def engine_config():
    """提供一个标准的回测引擎配置"""
    return {"initial_capital": "100000.0", "matching_engine": "DepthMatchingEngine"}


class TestBacktestEngine:
    """测试重构后的回测引擎"""

    def test_initialization(self, mock_plugin_manager, engine_config):
        """测试引擎初始化"""
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        assert engine._is_running is False
        assert engine._portfolio_manager is not None
        assert engine._performance_manager is not None
        assert engine._matching_engine is not None
        assert isinstance(engine._matching_engine, BaseMatchingEngine)

    def test_start_and_stop(self, mock_plugin_manager, engine_config):
        """测试引擎的启动和停止"""
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        engine.start()
        assert engine._is_running is True
        engine.stop()
        assert engine._is_running is False

    def test_submit_order(self, mock_plugin_manager, engine_config):
        """测试订单提交"""
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        engine.start()
        order = Order("test_order", "TEST.SH", "buy", Decimal("100"), Decimal("10.0"))
        engine.submit_order(order)
        assert len(engine.get_orders()) == 1
        assert engine.get_statistics()["total_orders"] == 1

    def test_update_market_data(self, mock_plugin_manager, engine_config):
        """测试市场数据更新"""
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        engine.start()
        now = datetime.now()
        market_data = MarketData(
            "TEST.SH",
            now,
            Decimal("10"),
            Decimal("11"),
            Decimal("9"),
            Decimal("10.5"),
            Decimal("1000"),
        )
        engine.update_market_data("TEST.SH", market_data)
        assert engine._current_time == now

    def test_complete_order_flow(self, mock_plugin_manager, engine_config):
        """
        测试完整的订单流程
        """
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        engine.start()

        now = datetime.now()
        buy_order = Order(
            order_id="buy_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            order_type="limit",
            timestamp=now,
        )
        sell_order = Order(
            order_id="sell_order",
            symbol="TEST.SH",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            order_type="limit",
            timestamp=now - timedelta(seconds=1),  # 确保卖单先到
        )

        engine.submit_order(sell_order)
        engine.submit_order(buy_order)

        market_data = MarketData(
            symbol="TEST.SH",
            timestamp=now,
            open_price=Decimal("10.0"),
            high_price=Decimal("10.2"),
            low_price=Decimal("9.8"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )
        engine.update_market_data("TEST.SH", market_data)

        fills = engine.get_fills()
        assert len(fills) == 2

    def test_multiple_orders_and_fills(self, mock_plugin_manager, engine_config):
        """
        测试多个订单和成交
        """
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        engine.start()

        buy_orders = [
            Order(
                f"buy_{i}",
                "TEST.SH",
                "buy",
                Decimal("50"),
                Decimal("10.0"),
                order_type="limit",
            )
            for i in range(3)
        ]
        sell_order = Order(
            "sell_1",
            "TEST.SH",
            "sell",
            Decimal("150"),
            Decimal("10.0"),
            order_type="limit",
        )

        engine.submit_order(sell_order)
        for order in buy_orders:
            engine.submit_order(order)

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

        assert len(engine.get_fills()) == 6  # 3个买单和3个卖单的成交记录

    def test_get_statistics(self, mock_plugin_manager, engine_config):
        """测试统计数据获取"""
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        stats = engine.get_statistics()
        assert "total_orders" in stats
        assert "total_fills" in stats
        assert "fill_rate" in stats

    def test_get_plugin_info(self, mock_plugin_manager, engine_config):
        """测试插件信息获取"""
        engine = BacktestEngine(
            plugin_manager=mock_plugin_manager, config=engine_config
        )
        info = engine.get_plugin_info()
        assert "matching_engine" in info
        assert info["matching_engine"] == "DepthMatchingEngine"

    def test_load_plugin_failure(self, caplog):
        """测试插件加载失败"""
        mock_plugin_manager = MagicMock(spec=PluginManager)
        mock_plugin_manager.load_plugin.side_effect = Exception("Load failed")
        config = {"matching_engine": "NonExistentEngine"}

        with caplog.at_level(logging.WARNING):
            engine = BacktestEngine(plugin_manager=mock_plugin_manager, config=config)
            assert engine._matching_engine is None
            assert "Failed to load backtest plugin 'NonExistentEngine'" in caplog.text

    def test_context_manager(self, mock_plugin_manager, engine_config):
        """测试上下文管理器"""
        with patch.object(BacktestEngine, "start") as mock_start, patch.object(
            BacktestEngine, "stop"
        ) as mock_stop:
            with BacktestEngine(
                plugin_manager=mock_plugin_manager, config=engine_config
            ):
                mock_start.assert_called_once()
            mock_stop.assert_called_once()
