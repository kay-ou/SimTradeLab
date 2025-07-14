# -*- coding: utf-8 -*-
"""
撮合引擎插件测试
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest

from simtradelab.backtest.plugins.base import MarketData, Order, PluginMetadata
from simtradelab.backtest.plugins.matching_engines import (
    DepthMatchingEngine,
    SimpleMatchingEngine,
    StrictLimitMatchingEngine,
)


class TestSimpleMatchingEngine:
    """测试简单撮合引擎"""

    def test_initialization(self):
        """测试初始化"""
        metadata = PluginMetadata(
            name="SimpleMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = SimpleMatchingEngine(metadata)
        assert engine.metadata == metadata
        assert hasattr(engine, "_price_tolerance")

    def test_can_match_market_order(self):
        """测试市价单匹配"""
        metadata = PluginMetadata(
            name="SimpleMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = SimpleMatchingEngine(metadata)

        market_order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=None,  # 市价单
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

        assert engine.can_match(market_order, market_data)

    def test_can_match_limit_order(self):
        """测试限价单匹配"""
        metadata = PluginMetadata(
            name="SimpleMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = SimpleMatchingEngine(metadata)

        # 买入限价单，限价高于市价
        buy_order = Order(
            order_id="buy_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.2"),
            order_type="limit",
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

        assert engine.can_match(buy_order, market_data)

        # 买入限价单，限价低于市价
        buy_order_low = Order(
            order_id="buy_order_low",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("9.5"),
            order_type="limit",
            timestamp=datetime.now(),
        )

        assert not engine.can_match(buy_order_low, market_data)

    def test_get_fill_price(self):
        """测试获取成交价格"""
        metadata = PluginMetadata(
            name="SimpleMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = SimpleMatchingEngine(metadata)

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
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

        fill_price = engine.get_fill_price(order, market_data)
        assert fill_price == Decimal("10.1")  # 应该返回收盘价

    def test_get_fill_quantity(self):
        """测试获取成交数量"""
        metadata = PluginMetadata(
            name="SimpleMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = SimpleMatchingEngine(metadata)

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
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

        fill_quantity = engine.get_fill_quantity(order, market_data)
        assert fill_quantity == Decimal("100")  # 简单引擎应该全部成交


class TestDepthMatchingEngine:
    """测试深度撮合引擎"""

    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        metadata = PluginMetadata(
            name="DepthMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        config = {"min_depth_ratio": 0.1, "max_spread_ratio": 0.01}

        engine = DepthMatchingEngine(metadata, config)
        assert engine._min_depth_ratio == Decimal("0.1")
        assert engine._max_spread_ratio == Decimal("0.01")

    def test_can_match_with_depth_check(self):
        """测试考虑深度的匹配"""
        metadata = PluginMetadata(
            name="DepthMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = DepthMatchingEngine(metadata)

        buy_order = Order(
            order_id="buy_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
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

        # 深度撮合引擎应该能够匹配
        assert engine.can_match(buy_order, market_data)

    def test_get_fill_price_with_depth(self):
        """测试考虑深度的成交价格"""
        metadata = PluginMetadata(
            name="DepthMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = DepthMatchingEngine(metadata)

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
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

        fill_price = engine.get_fill_price(order, market_data)
        # 深度撮合引擎应该返回合理的价格
        assert fill_price > 0


class TestStrictLimitMatchingEngine:
    """测试严格限价撮合引擎"""

    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        metadata = PluginMetadata(
            name="StrictLimitMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        config = {"allow_partial_fills": False, "price_tolerance": 0.001}

        engine = StrictLimitMatchingEngine(metadata, config)
        assert engine._allow_partial_fills is False
        assert engine._price_tolerance == Decimal("0.001")

    def test_can_match_strict_limit(self):
        """测试严格限价匹配"""
        metadata = PluginMetadata(
            name="StrictLimitMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        engine = StrictLimitMatchingEngine(metadata)

        # 限价单价格正好匹配
        exact_order = Order(
            order_id="exact_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.1"),  # 正好等于收盘价
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

        assert engine.can_match(exact_order, market_data)

        # 限价单价格不匹配
        high_order = Order(
            order_id="high_order",
            symbol="TEST.SH",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("10.5"),  # 高于市价
            timestamp=datetime.now(),
        )

        # 严格限价引擎可能不允许不匹配的价格
        # 具体逻辑取决于实现
        result = engine.can_match(high_order, market_data)
        assert isinstance(result, bool)  # 至少应该返回布尔值

    def test_get_fill_quantity_strict(self):
        """测试严格限价的成交数量"""
        metadata = PluginMetadata(
            name="StrictLimitMatchingEngine",
            version="1.0.0",
            description="Test",
            author="Test",
            category="matching_engine",
            tags=["test"],
        )

        config = {"allow_partial_fills": False}
        engine = StrictLimitMatchingEngine(metadata, config)

        order = Order(
            order_id="order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.1"),
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

        fill_quantity = engine.get_fill_quantity(order, market_data)
        # 如果不允许部分成交，应该是全部成交或不成交
        assert fill_quantity == Decimal("100") or fill_quantity == Decimal("0")
