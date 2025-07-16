# -*- coding: utf-8 -*-
"""
撮合引擎插件测试 (重构后)
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from simtradelab.backtest.plugins.base import Fill, MarketData, Order, PluginMetadata
from simtradelab.backtest.plugins.commission_models import BaseCommissionModel
from simtradelab.backtest.plugins.config import DepthMatchingEngineConfig
from simtradelab.backtest.plugins.matching_engines import DepthMatchingEngine
from simtradelab.backtest.plugins.slippage_models import BaseSlippageModel


# 可实例化的具体插件类，用于测试
class ConcreteDepthMatchingEngine(DepthMatchingEngine):
    def _on_initialize(self) -> None:
        pass

    def _on_start(self) -> None:
        pass

    def _on_stop(self) -> None:
        pass


@pytest.fixture
def mock_slippage_model():
    """提供一个模拟的滑点模型"""
    mock = MagicMock(spec=BaseSlippageModel)
    mock.calculate_slippage.return_value = Decimal("0.01")
    return mock


@pytest.fixture
def mock_commission_model():
    """提供一个模拟的手续费模型"""
    mock = MagicMock(spec=BaseCommissionModel)
    mock.calculate_commission.return_value = Decimal("5.00")
    return mock


@pytest.fixture
def depth_matching_engine(mock_slippage_model, mock_commission_model):
    """提供一个配置好的深度撮合引擎实例"""
    metadata = PluginMetadata(
        name="TestDepthMatchingEngine",
        version="1.0.0",
        description="Test Engine",
        author="Test Author",
        category="matching_engine",
    )
    config = DepthMatchingEngineConfig()
    engine = ConcreteDepthMatchingEngine(
        metadata=metadata,
        config=config,
        slippage_model=mock_slippage_model,
        commission_model=mock_commission_model,
    )
    return engine


class TestDepthMatchingEngine:
    """测试重构后的深度撮合引擎"""

    def test_initialization(self, depth_matching_engine):
        """测试初始化和依赖注入"""
        assert depth_matching_engine.metadata.name == "TestDepthMatchingEngine"
        assert depth_matching_engine._slippage_model is not None
        assert depth_matching_engine._commission_model is not None

    @pytest.mark.skip(reason="DepthMatchingEngine暂未集成滑点和手续费模型")
    def test_match_order_with_costs(
        self, depth_matching_engine, mock_slippage_model, mock_commission_model
    ):
        """测试订单撮合是否正确包含了滑点和手续费"""
        pass

    def test_limit_order_can_match(self, depth_matching_engine):
        """测试限价单可以匹配的场景"""
        buy_order = Order(
            order_id="buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("153.0"),
            order_type="limit",
        )
        sell_order = Order(
            order_id="sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("153.0"),
            order_type="limit",
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("153.0"),
            high_price=Decimal("154.0"),
            low_price=Decimal("152.0"),
            close_price=Decimal("153.0"),
            volume=Decimal("10000"),
        )

        depth_matching_engine.add_order(sell_order)
        depth_matching_engine.add_order(buy_order)
        fills, _ = depth_matching_engine.trigger_matching("AAPL", market_data)

        assert len(fills) == 2

    def test_limit_order_cannot_match(self, depth_matching_engine):
        """测试限价单无法匹配的场景"""
        buy_order = Order(
            order_id="buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.0"),
            order_type="limit",
        )
        sell_order = Order(
            order_id="sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("151.0"),
            order_type="limit",
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150.5"),
            high_price=Decimal("151.5"),
            low_price=Decimal("150.2"),
            close_price=Decimal("150.5"),
            volume=Decimal("10000"),
        )

        depth_matching_engine.add_order(buy_order)
        depth_matching_engine.add_order(sell_order)
        fills, _ = depth_matching_engine.trigger_matching("AAPL", market_data)

        assert len(fills) == 0

    def test_stop_buy_order_trigger(self, depth_matching_engine):
        """测试止损买单被触发"""
        stop_order = Order(
            order_id="stop_buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="stop",
            trigger_price=Decimal("155.0"),
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("155.0"),
            high_price=Decimal("156.0"),
            low_price=Decimal("154.0"),
            close_price=Decimal("155.5"),
            volume=Decimal("10000"),
        )

        # 提交一个对手单以确保可以成交
        sell_order = Order(
            order_id="sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("155.5"),
            order_type="limit",
        )
        depth_matching_engine.add_order(sell_order)
        depth_matching_engine.add_order(stop_order)

        fills, _ = depth_matching_engine.trigger_matching("AAPL", market_data)
        assert len(fills) == 2

        fill_order_ids = {fill.order_id for fill in fills}
        assert "sell1" in fill_order_ids
        assert "stop_buy1" in fill_order_ids

    def test_stop_sell_order_trigger(self, depth_matching_engine):
        """测试止损卖单被触发"""
        stop_order = Order(
            order_id="stop_sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            order_type="stop",
            trigger_price=Decimal("150.0"),
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150.0"),
            high_price=Decimal("151.0"),
            low_price=Decimal("149.0"),
            close_price=Decimal("149.5"),
            volume=Decimal("10000"),
        )

        buy_order = Order(
            order_id="buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("149.5"),
            order_type="limit",
        )
        depth_matching_engine.add_order(buy_order)
        depth_matching_engine.add_order(stop_order)

        fills, _ = depth_matching_engine.trigger_matching("AAPL", market_data)
        assert len(fills) == 2

        fill_order_ids = {fill.order_id for fill in fills}
        assert "buy1" in fill_order_ids
        assert "stop_sell1" in fill_order_ids

    def test_stop_order_not_triggered(self, depth_matching_engine):
        """测试止损单未被触发"""
        stop_order = Order(
            order_id="stop_buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="stop",
            trigger_price=Decimal("155.0"),
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("154.0"),
            high_price=Decimal("154.5"),
            low_price=Decimal("153.0"),
            close_price=Decimal("154.0"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.add_order(stop_order)
        fills, _ = depth_matching_engine.trigger_matching("AAPL", market_data)
        assert len(fills) == 0

    def test_ioc_order_partial_fill(self, depth_matching_engine):
        """测试IOC订单部分成交"""
        sell_order = Order(
            order_id="sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("50"),
            price=Decimal("150.0"),
            order_type="limit",
        )
        ioc_buy_order = Order(
            order_id="ioc_buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.0"),
            time_in_force="ioc",
            order_type="limit",
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150.0"),
            high_price=Decimal("150.0"),
            low_price=Decimal("150.0"),
            close_price=Decimal("150.0"),
            volume=Decimal("10000"),
        )

        depth_matching_engine.add_order(sell_order)
        depth_matching_engine.add_order(ioc_buy_order)
        fills, filled_orders = depth_matching_engine.trigger_matching(
            "AAPL", market_data
        )

        assert len(fills) == 2
        assert fills[0].quantity == Decimal("50")
        assert (
            len(filled_orders) == 2
        )  # sell_order is filled, ioc_buy_order is cancelled

        cancelled_order = next(o for o in filled_orders if o.order_id == "ioc_buy1")
        assert cancelled_order.status == "cancelled"

    def test_fok_order_full_fill(self, depth_matching_engine):
        """测试FOK订单完全成交"""
        sell_order = Order(
            order_id="sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("150.0"),
            order_type="limit",
        )
        fok_buy_order = Order(
            order_id="fok_buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.0"),
            time_in_force="fok",
            order_type="limit",
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150.0"),
            high_price=Decimal("150.0"),
            low_price=Decimal("150.0"),
            close_price=Decimal("150.0"),
            volume=Decimal("10000"),
        )

        depth_matching_engine.add_order(sell_order)
        depth_matching_engine.add_order(fok_buy_order)
        fills, filled_orders = depth_matching_engine.trigger_matching(
            "AAPL", market_data
        )

        assert len(fills) == 2
        assert len(filled_orders) == 2
        filled_fok = next(o for o in filled_orders if o.order_id == "fok_buy1")
        assert filled_fok.status == "filled"

    def test_fok_order_no_fill(self, depth_matching_engine):
        """测试FOK订单因无法完全成交而被取消"""
        sell_order = Order(
            order_id="sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("50"),
            price=Decimal("150.0"),
            order_type="limit",
        )
        fok_buy_order = Order(
            order_id="fok_buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("150.0"),
            time_in_force="fok",
            order_type="limit",
        )
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150.0"),
            high_price=Decimal("150.0"),
            low_price=Decimal("150.0"),
            close_price=Decimal("150.0"),
            volume=Decimal("10000"),
        )

        depth_matching_engine.add_order(sell_order)
        depth_matching_engine.add_order(fok_buy_order)
        fills, filled_orders = depth_matching_engine.trigger_matching(
            "AAPL", market_data
        )

        assert len(fills) == 0
        assert len(filled_orders) == 1
        assert filled_orders[0].order_id == "fok_buy1"
        assert filled_orders[0].status == "cancelled"

    def test_trailing_stop_sell_order_trigger(self, depth_matching_engine):
        """测试跟踪止损卖单被触发"""
        trailing_order = Order(
            order_id="trailing_sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            order_type="trailing_stop",
            trail_amount=Decimal("5.0"),
        )

        # 1. 提交订单，价格 150
        market_data1 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150"),
            high_price=Decimal("151"),
            low_price=Decimal("149"),
            close_price=Decimal("150"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.add_order(trailing_order)
        depth_matching_engine.trigger_matching("AAPL", market_data1)

        # 2. 价格上涨到 160, 更新高水位
        market_data2 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("155"),
            high_price=Decimal("160"),
            low_price=Decimal("155"),
            close_price=Decimal("160"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.trigger_matching("AAPL", market_data2)

        # 3. 价格下跌到 155，触发订单
        buy_order = Order(
            order_id="buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("155"),
            order_type="limit",
        )
        depth_matching_engine.add_order(buy_order)
        market_data3 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("156"),
            high_price=Decimal("157"),
            low_price=Decimal("154"),
            close_price=Decimal("155"),
            volume=Decimal("10000"),
        )
        fills, _ = depth_matching_engine.trigger_matching("AAPL", market_data3)

        assert len(fills) == 2
        assert "trailing_sell1" in {f.order_id for f in fills}

    def test_trailing_stop_buy_order_trigger(self, depth_matching_engine):
        """测试跟踪止损买单被触发"""
        trailing_order = Order(
            order_id="trailing_buy1",
            symbol="AAPL",
            side="buy",
            quantity=Decimal("100"),
            order_type="trailing_stop",
            trail_amount=Decimal("5.0"),
        )

        # 1. 提交订单，价格 150
        market_data1 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150"),
            high_price=Decimal("151"),
            low_price=Decimal("149"),
            close_price=Decimal("150"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.add_order(trailing_order)
        depth_matching_engine.trigger_matching("AAPL", market_data1)

        # 2. 价格下跌到 140, 更新低水位
        market_data2 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("145"),
            high_price=Decimal("145"),
            low_price=Decimal("140"),
            close_price=Decimal("140"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.trigger_matching("AAPL", market_data2)

        # 3. 价格上涨到 145，触发订单
        sell_order = Order(
            order_id="sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("145"),
            order_type="limit",
        )
        depth_matching_engine.add_order(sell_order)
        market_data3 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("144"),
            high_price=Decimal("146"),
            low_price=Decimal("143"),
            close_price=Decimal("145"),
            volume=Decimal("10000"),
        )
        fills, _ = depth_matching_engine.trigger_matching("AAPL", market_data3)

        assert len(fills) == 2
        assert "trailing_buy1" in {f.order_id for f in fills}

    def test_trailing_stop_order_price_update(self, depth_matching_engine):
        """测试跟踪止损单的参考价格更新"""
        trailing_order = Order(
            order_id="trailing_sell1",
            symbol="AAPL",
            side="sell",
            quantity=Decimal("100"),
            order_type="trailing_stop",
            trail_amount=Decimal("5.0"),
        )

        # 1. 提交订单，价格 150
        market_data1 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("150"),
            high_price=Decimal("151"),
            low_price=Decimal("149"),
            close_price=Decimal("150"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.add_order(trailing_order)
        depth_matching_engine.trigger_matching("AAPL", market_data1)
        assert trailing_order.trailing_reference_price == Decimal("151")

        # 2. 价格上涨到 160, 更新高水位
        market_data2 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("155"),
            high_price=Decimal("160"),
            low_price=Decimal("155"),
            close_price=Decimal("160"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.trigger_matching("AAPL", market_data2)
        assert trailing_order.trailing_reference_price == Decimal("160")

        # 3. 价格下跌到 158 (高于触发价 155)，不更新高水位
        market_data3 = MarketData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open_price=Decimal("159"),
            high_price=Decimal("159"),
            low_price=Decimal("157"),
            close_price=Decimal("158"),
            volume=Decimal("10000"),
        )
        depth_matching_engine.trigger_matching("AAPL", market_data3)
        assert trailing_order.trailing_reference_price == Decimal("160")
