# -*- coding: utf-8 -*-
"""
撮合引擎插件测试 (重构后)
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from simtradelab.backtest.plugins.base import MarketData, Order, PluginMetadata
from simtradelab.backtest.plugins.commission_models import BaseCommissionModel
from simtradelab.backtest.plugins.config import SimpleMatchingEngineConfig
from simtradelab.backtest.plugins.matching_engines import SimpleMatchingEngine
from simtradelab.backtest.plugins.slippage_models import BaseSlippageModel


# 可实例化的具体插件类，用于测试
class ConcreteSimpleMatchingEngine(SimpleMatchingEngine):
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
    mock.calculate_slippage.return_value = Decimal("0.01")  # 模拟滑点为 0.01
    return mock


@pytest.fixture
def mock_commission_model():
    """提供一个模拟的手续费模型"""
    mock = MagicMock(spec=BaseCommissionModel)
    mock.calculate_commission.return_value = Decimal("5.00")  # 模拟手续费为 5.00
    return mock


@pytest.fixture
def simple_matching_engine(mock_slippage_model, mock_commission_model):
    """提供一个配置好的简单撮合引擎实例"""
    metadata = PluginMetadata(
        name="TestSimpleMatchingEngine",
        version="1.0.0",
        description="Test Engine",
        author="Test Author",
        category="matching_engine",
    )
    config = SimpleMatchingEngineConfig()
    engine = ConcreteSimpleMatchingEngine(
        metadata=metadata,
        config=config,
        slippage_model=mock_slippage_model,
        commission_model=mock_commission_model,
    )
    return engine


class TestSimpleMatchingEngine:
    """测试重构后的简单撮合引擎"""

    def test_initialization(self, simple_matching_engine):
        """测试初始化和依赖注入"""
        assert simple_matching_engine.metadata.name == "TestSimpleMatchingEngine"
        assert simple_matching_engine._slippage_model is not None
        assert simple_matching_engine._commission_model is not None

    def test_match_order_with_costs(
        self, simple_matching_engine, mock_slippage_model, mock_commission_model
    ):
        """测试订单撮合是否正确包含了滑点和手续费"""
        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            timestamp=datetime.now(),
        )
        market_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.2"),
            low_price=Decimal("9.8"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        fills = simple_matching_engine.match_order(order, market_data)

        assert len(fills) == 1
        fill = fills[0]

        # 验证模拟的滑点和手续费模型是否被调用
        mock_slippage_model.calculate_slippage.assert_called_once()
        mock_commission_model.calculate_commission.assert_called_once()

        # 验证Fill对象是否包含了成本
        assert fill.slippage == Decimal("0.01")
        assert fill.commission == Decimal("5.00")

        # 验证成交价格是否考虑了滑点
        expected_price = market_data.close_price + (fill.slippage / fill.quantity)
        assert fill.price == expected_price

    def test_limit_order_can_match(self, simple_matching_engine):
        """测试限价单可以匹配的场景"""
        order = Order(
            order_id="limit_buy",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),  # 限价低于市价，但高于最低价
            order_type="limit",
            timestamp=datetime.now(),
        )
        market_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.05"),
            high_price=Decimal("10.2"),
            low_price=Decimal("9.8"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        assert simple_matching_engine._can_execute(order, market_data)
        fills = simple_matching_engine.match_order(order, market_data)
        assert len(fills) == 1
        # 成交价应该是限价和开盘价中对买方有利的那个（更低的）
        assert fills[0].price > Decimal("0")  # 确保价格被计算

    def test_limit_order_cannot_match(self, simple_matching_engine):
        """测试限价单无法匹配的场景"""
        order = Order(
            order_id="limit_buy_fail",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("9.7"),  # 限价低于当日最低价
            order_type="limit",
            timestamp=datetime.now(),
        )
        market_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.05"),
            high_price=Decimal("10.2"),
            low_price=Decimal("9.8"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        assert not simple_matching_engine._can_execute(order, market_data)
        fills = simple_matching_engine.match_order(order, market_data)
        assert len(fills) == 0
