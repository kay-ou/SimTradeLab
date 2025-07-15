# -*- coding: utf-8 -*-
"""
回测引擎测试 (重构后)

E10修复：更新测试以使用统一插件管理的BacktestEngine
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from simtradelab.backtest.engine import BacktestEngine
from simtradelab.backtest.plugins.base import MarketData, Order
from simtradelab.backtest.plugins.matching_engines import SimpleMatchingEngine
from simtradelab.backtest.plugins.slippage_models import FixedSlippageModel
from simtradelab.backtest.plugins.commission_models import FixedCommissionModel
from simtradelab.plugins.base import PluginMetadata
from simtradelab.backtest.plugins.config import (
    SimpleMatchingEngineConfig,
    FixedSlippageModelConfig,
    FixedCommissionModelConfig,
)
from simtradelab.core.plugin_manager import PluginManager


# 为了测试，我们需要一个可实例化的 SimpleMatchingEngine
class ConcreteSimpleMatchingEngine(SimpleMatchingEngine):
    def _on_initialize(self) -> None:
        pass

    def _on_start(self) -> None:
        pass

    def _on_stop(self) -> None:
        pass


@pytest.fixture
def mock_plugin_manager():
    """
    E10修复：提供一个模拟的PluginManager，预配置了回测插件
    """
    plugin_manager = MagicMock(spec=PluginManager)

    # 创建模拟插件实例
    mock_matching_engine = ConcreteSimpleMatchingEngine(
        metadata=PluginMetadata(name="TestMatchingEngine", version="1.0"),
        config=SimpleMatchingEngineConfig(),
    )

    mock_slippage_model = FixedSlippageModel(
        metadata=PluginMetadata(name="TestSlippage", version="1.0"),
        config=FixedSlippageModelConfig(base_slippage_rate=Decimal("0.001")),
    )

    mock_commission_model = FixedCommissionModel(
        metadata=PluginMetadata(name="TestCommission", version="1.0"),
        config=FixedCommissionModelConfig(commission_rate=Decimal("0.0003")),
    )

    # 配置load_plugin方法的返回值
    def load_plugin_side_effect(plugin_name):
        if plugin_name == "SimpleMatchingEngine":
            return mock_matching_engine
        elif plugin_name == "FixedSlippageModel":
            return mock_slippage_model
        elif plugin_name == "FixedCommissionModel":
            return mock_commission_model
        else:
            raise ValueError(f"Unknown plugin: {plugin_name}")

    plugin_manager.load_plugin.side_effect = load_plugin_side_effect

    return plugin_manager


@pytest.fixture
def mock_matching_engine():
    """提供一个模拟的撮合引擎实例（向后兼容）"""
    metadata = PluginMetadata(name="TestMatchingEngine", version="1.0")

    return ConcreteSimpleMatchingEngine(
        metadata=metadata, config=SimpleMatchingEngineConfig()
    )


@pytest.fixture
def mock_slippage_model():
    """提供一个模拟的滑点模型实例（向后兼容）"""
    return FixedSlippageModel(
        metadata=PluginMetadata(name="TestSlippage", version="1.0"),
        config=FixedSlippageModelConfig(base_slippage_rate=Decimal("0.001")),
    )


@pytest.fixture
def mock_commission_model():
    """提供一个模拟的手续费模型实例（向后兼容）"""
    return FixedCommissionModel(
        metadata=PluginMetadata(name="TestCommission", version="1.0"),
        config=FixedCommissionModelConfig(commission_rate=Decimal("0.0003")),
    )


class TestBacktestEngine:
    """
    测试重构后的回测引擎

    E10修复：更新测试以使用统一插件管理
    """

    def test_initialization(self, mock_plugin_manager):
        """
        E10修复：测试引擎通过PluginManager初始化
        """
        engine = BacktestEngine(plugin_manager=mock_plugin_manager)
        assert engine is not None
        assert not engine._is_running
        plugin_info = engine.get_plugin_info()
        assert plugin_info["matching_engine"] == "TestMatchingEngine"
        assert plugin_info["plugin_manager"] == "Unified PluginManager"

    def test_start_stop_lifecycle(self, mock_plugin_manager):
        """
        E10修复：测试引擎启动停止生命周期
        """
        engine = BacktestEngine(plugin_manager=mock_plugin_manager)

        assert not engine._is_running
        engine.start()
        assert engine._is_running
        engine.stop()
        assert not engine._is_running

    def test_context_manager(self, mock_plugin_manager):
        """
        E10修复：测试上下文管理器
        """
        engine = BacktestEngine(plugin_manager=mock_plugin_manager)
        with engine as ctx_engine:
            assert ctx_engine is engine
            assert engine._is_running
        assert not engine._is_running

    def test_submit_order_without_running(self, mock_plugin_manager):
        """
        E10修复：测试在未启动引擎时提交订单
        """
        engine = BacktestEngine(plugin_manager=mock_plugin_manager)
        order = Order("test_order", "TEST.SH", "buy", Decimal("100"), Decimal("10.0"))
        with pytest.raises(RuntimeError, match="BacktestEngine is not running"):
            engine.submit_order(order)

    def test_complete_order_flow(self, mock_plugin_manager):
        """
        E10修复：测试完整的订单流程
        """
        engine = BacktestEngine(plugin_manager=mock_plugin_manager)
        engine.start()

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )
        engine.submit_order(order)

        # 提交后，从引擎获取订单列表进行检查
        orders_before_fill = engine.get_orders()
        assert len(orders_before_fill) == 1
        assert orders_before_fill[0].status == "pending"

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

        fills = engine.get_fills()
        assert len(fills) == 1
        fill = fills[0]
        assert fill.order_id == "test_order"
        assert fill.commission > 0
        assert fill.slippage > 0

        # 再次从引擎获取订单列表，检查状态是否已更新
        orders_after_fill = engine.get_orders()
        assert orders_after_fill[0].status == "filled"
        assert orders_after_fill[0].filled_quantity == Decimal("100")

        stats = engine.get_statistics()
        assert stats["total_orders"] == 1
        assert stats["total_fills"] == 1
        assert stats["total_commission"] > 0
        assert stats["total_slippage"] > 0

        engine.stop()

    def test_get_statistics_empty(self, mock_plugin_manager):
        """
        E10修复：测试获取空统计数据
        """
        engine = BacktestEngine(plugin_manager=mock_plugin_manager)
        stats = engine.get_statistics()
        assert stats["total_orders"] == 0
        assert stats["total_fills"] == 0
        assert stats["total_commission"] == 0
        assert stats["total_slippage"] == 0
        assert stats["fill_rate"] == 0

    def test_multiple_orders_and_fills(self, mock_plugin_manager):
        """
        E10修复：测试多个订单和成交
        """
        engine = BacktestEngine(plugin_manager=mock_plugin_manager)
        engine.start()

        orders = [
            Order(f"order_{i}", "TEST.SH", "buy", Decimal("100"), Decimal("10.0"))
            for i in range(3)
        ]
        for order in orders:
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

        assert len(engine.get_orders()) == 3
        assert len(engine.get_fills()) == 3
        stats = engine.get_statistics()
        assert stats["total_orders"] == 3
        assert stats["total_fills"] == 3

        engine.stop()
