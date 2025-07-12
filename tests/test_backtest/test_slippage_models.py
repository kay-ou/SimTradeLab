# -*- coding: utf-8 -*-
"""
滑点模型插件测试
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from simtradelab.backtest.plugins.base import MarketData, Order, PluginMetadata
from simtradelab.backtest.plugins.slippage_models import (
    DynamicSlippageModel,
    FixedSlippageModel,
    LinearSlippageModel,
    VolatilityBasedSlippageModel,
)


class TestFixedSlippageModel:
    """测试固定滑点模型"""

    def test_initialization(self):
        """测试初始化"""
        metadata = PluginMetadata(
            name="FixedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = FixedSlippageModel(metadata)
        assert model.metadata == metadata
        assert hasattr(model, "_buy_slippage_rate")
        assert hasattr(model, "_sell_slippage_rate")

    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        metadata = PluginMetadata(
            name="FixedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        config = {
            "buy_slippage_rate": 0.002,
            "sell_slippage_rate": 0.003,
            "min_slippage": 0.02,
            "max_slippage": 200.0,
        }

        model = FixedSlippageModel(metadata, config)
        assert model._buy_slippage_rate == Decimal("0.002")
        assert model._sell_slippage_rate == Decimal("0.003")
        assert model._min_slippage == Decimal("0.02")
        assert model._max_slippage == Decimal("200.0")

    def test_calculate_slippage_buy(self):
        """测试计算买入滑点"""
        metadata = PluginMetadata(
            name="FixedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = FixedSlippageModel(metadata)

        order = Order(
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

        fill_price = Decimal("10.1")
        slippage = model.calculate_slippage(order, market_data, fill_price)

        # 计算期望滑点：10.1 * 100 * 0.001 = 1.01
        expected_slippage = fill_price * order.quantity * model._buy_slippage_rate
        assert slippage == max(expected_slippage, model._min_slippage)

    def test_calculate_slippage_sell(self):
        """测试计算卖出滑点"""
        metadata = PluginMetadata(
            name="FixedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = FixedSlippageModel(metadata)

        order = Order(
            order_id="sell_order",
            symbol="TEST.SH",
            side="sell",
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

        fill_price = Decimal("10.1")
        slippage = model.calculate_slippage(order, market_data, fill_price)

        # 使用卖出滑点率
        expected_slippage = fill_price * order.quantity * model._sell_slippage_rate
        assert slippage == max(expected_slippage, model._min_slippage)

    def test_get_slippage_rate(self):
        """测试获取滑点率"""
        metadata = PluginMetadata(
            name="FixedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = FixedSlippageModel(metadata)

        buy_order = Order(
            order_id="buy_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        sell_order = Order(
            order_id="sell_order",
            symbol="TEST.SH",
            side="sell",
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

        buy_rate = model.get_slippage_rate(buy_order, market_data)
        sell_rate = model.get_slippage_rate(sell_order, market_data)

        assert buy_rate == model._buy_slippage_rate
        assert sell_rate == model._sell_slippage_rate


class TestDynamicSlippageModel:
    """测试动态滑点模型"""

    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        metadata = PluginMetadata(
            name="DynamicSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        config = {
            "base_slippage_rate": 0.0008,
            "volume_impact_factor": 0.002,
            "volatility_factor": 0.8,
            "time_factor": 0.3,
        }

        model = DynamicSlippageModel(metadata, config)
        assert model._base_slippage_rate == Decimal("0.0008")
        assert model._volume_impact_factor == Decimal("0.002")
        assert model._volatility_factor == Decimal("0.8")
        assert model._time_factor == Decimal("0.3")

    def test_calculate_slippage_dynamic(self):
        """测试计算动态滑点"""
        metadata = PluginMetadata(
            name="DynamicSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = DynamicSlippageModel(metadata)

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

        fill_price = Decimal("10.1")
        slippage = model.calculate_slippage(order, market_data, fill_price)

        # 动态滑点应该大于0
        assert slippage > 0

        # 动态滑点应该考虑多个因素
        static_slippage = fill_price * order.quantity * model._base_slippage_rate
        assert slippage != static_slippage  # 应该不等于纯粹的基础滑点

    def test_volume_impact_calculation(self):
        """测试交易量冲击计算"""
        metadata = PluginMetadata(
            name="DynamicSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = DynamicSlippageModel(metadata)

        # 大订单
        large_order = Order(
            order_id="large_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("5000"),  # 50%的市场量
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        # 小订单
        small_order = Order(
            order_id="small_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),  # 1%的市场量
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

        fill_price = Decimal("10.1")

        large_slippage = model.calculate_slippage(large_order, market_data, fill_price)
        small_slippage = model.calculate_slippage(small_order, market_data, fill_price)

        # 大订单的滑点应该比小订单大
        assert large_slippage > small_slippage

    def test_volatility_impact_calculation(self):
        """测试波动性影响计算"""
        metadata = PluginMetadata(
            name="DynamicSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = DynamicSlippageModel(metadata)

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        # 高波动性市场数据
        high_volatility_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("12.0"),  # 高波动
            low_price=Decimal("8.0"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        # 低波动性市场数据
        low_volatility_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.05"),  # 低波动
            low_price=Decimal("9.95"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        fill_price = Decimal("10.1")

        high_vol_slippage = model.calculate_slippage(
            order, high_volatility_data, fill_price
        )
        low_vol_slippage = model.calculate_slippage(
            order, low_volatility_data, fill_price
        )

        # 高波动性时滑点应该更大
        assert high_vol_slippage > low_vol_slippage


class TestVolatilityBasedSlippageModel:
    """测试基于波动性的滑点模型"""

    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        metadata = PluginMetadata(
            name="VolatilityBasedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        config = {
            "base_slippage_rate": 0.0008,
            "volatility_multiplier": 15.0,
            "lookback_period": 30,
            "min_volatility": 0.002,
        }

        model = VolatilityBasedSlippageModel(metadata, config)
        assert model._base_slippage_rate == Decimal("0.0008")
        assert model._volatility_multiplier == Decimal("15.0")
        assert model._lookback_period == 30
        assert model._min_volatility == Decimal("0.002")

    def test_price_history_update(self):
        """测试价格历史更新"""
        metadata = PluginMetadata(
            name="VolatilityBasedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = VolatilityBasedSlippageModel(metadata)

        # 更新价格历史
        model._update_price_history("TEST.SH", Decimal("10.0"))
        model._update_price_history("TEST.SH", Decimal("10.1"))
        model._update_price_history("TEST.SH", Decimal("10.2"))

        assert len(model._price_history["TEST.SH"]) == 3
        assert model._price_history["TEST.SH"][0] == 10.0
        assert model._price_history["TEST.SH"][1] == 10.1
        assert model._price_history["TEST.SH"][2] == 10.2

    def test_price_history_limit(self):
        """测试价格历史长度限制"""
        metadata = PluginMetadata(
            name="VolatilityBasedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        config = {"lookback_period": 3}
        model = VolatilityBasedSlippageModel(metadata, config)

        # 添加超过限制的价格数据
        for i in range(10):
            model._update_price_history("TEST.SH", Decimal(str(10.0 + i * 0.1)))

        # 应该只保留最近的3个价格
        assert len(model._price_history["TEST.SH"]) == 3
        assert model._price_history["TEST.SH"][-1] == 10.9  # 最新价格

    def test_volatility_calculation(self):
        """测试波动性计算"""
        metadata = PluginMetadata(
            name="VolatilityBasedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = VolatilityBasedSlippageModel(metadata)

        # 添加一些价格历史
        prices = [10.0, 10.1, 9.9, 10.2, 9.8, 10.3]
        for price in prices:
            model._update_price_history("TEST.SH", Decimal(str(price)))

        market_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.3"),
            low_price=Decimal("9.8"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        volatility = model._calculate_volatility("TEST.SH", market_data)

        # 波动性应该大于0
        assert volatility > 0

        # 波动性应该至少等于最小波动性
        assert volatility >= model._min_volatility

    def test_calculate_slippage_with_volatility(self):
        """测试基于波动性的滑点计算"""
        metadata = PluginMetadata(
            name="VolatilityBasedSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = VolatilityBasedSlippageModel(metadata)

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        # 高波动性市场数据
        high_vol_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("12.0"),
            low_price=Decimal("8.0"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        # 低波动性市场数据
        low_vol_data = MarketData(
            symbol="TEST.SH",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.05"),
            low_price=Decimal("9.95"),
            close_price=Decimal("10.1"),
            volume=Decimal("10000"),
        )

        fill_price = Decimal("10.1")

        high_vol_slippage = model.calculate_slippage(order, high_vol_data, fill_price)
        low_vol_slippage = model.calculate_slippage(order, low_vol_data, fill_price)

        # 高波动性时滑点应该更大
        assert high_vol_slippage > low_vol_slippage


class TestLinearSlippageModel:
    """测试线性滑点模型"""

    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        metadata = PluginMetadata(
            name="LinearSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        config = {
            "base_rate": 0.0003,
            "slope": 0.000002,
            "reference_size": 5000,
            "max_slippage_rate": 0.02,
        }

        model = LinearSlippageModel(metadata, config)
        assert model._base_rate == Decimal("0.0003")
        assert model._slope == Decimal("0.000002")
        assert model._reference_size == Decimal("5000")
        assert model._max_slippage_rate == Decimal("0.02")

    def test_calculate_linear_rate(self):
        """测试线性滑点率计算"""
        metadata = PluginMetadata(
            name="LinearSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = LinearSlippageModel(metadata)

        # 小订单
        small_order = Order(
            order_id="small_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        # 大订单
        large_order = Order(
            order_id="large_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("50000"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        small_rate = model._calculate_linear_rate(small_order)
        large_rate = model._calculate_linear_rate(large_order)

        # 大订单的滑点率应该更高
        assert large_rate > small_rate

        # 小订单的滑点率应该接近基础费率
        assert small_rate >= model._base_rate

    def test_calculate_slippage_linear(self):
        """测试线性滑点计算"""
        metadata = PluginMetadata(
            name="LinearSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        model = LinearSlippageModel(metadata)

        order = Order(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("20000"),  # 2倍参考规模
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

        fill_price = Decimal("10.1")
        slippage = model.calculate_slippage(order, market_data, fill_price)

        # 滑点应该大于0
        assert slippage > 0

        # 计算期望的滑点率
        expected_rate = model._base_rate + (
            (order.quantity / model._reference_size) * model._slope
        )
        expected_slippage = fill_price * order.quantity * expected_rate

        # 应该不超过最大滑点率
        max_slippage = fill_price * order.quantity * model._max_slippage_rate
        assert slippage <= max_slippage

    def test_max_slippage_rate_limit(self):
        """测试最大滑点率限制"""
        metadata = PluginMetadata(
            name="LinearSlippageModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="slippage_model",
            tags=["test"],
        )

        config = {"max_slippage_rate": 0.005}  # 0.5%限制
        model = LinearSlippageModel(metadata, config)

        # 超大订单
        huge_order = Order(
            order_id="huge_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("1000000"),  # 100倍参考规模
            price=Decimal("10.0"),
            timestamp=datetime.now(),
        )

        calculated_rate = model._calculate_linear_rate(huge_order)

        # 应该被限制在最大滑点率
        assert calculated_rate == model._max_slippage_rate
