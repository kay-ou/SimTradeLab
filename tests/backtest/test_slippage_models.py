# -*- coding: utf-8 -*-
"""
滑点模型插件测试 (v2.2 最终修复版)

本次重构旨在：
1.  遵循 v5.0 架构的测试最佳实践。
2.  为每个滑点模型提供独立的、清晰的测试类。
3.  使用 pytest fixtures 减少代码重复。
4.  提供更精确的断言和对边界条件的覆盖。
5.  验证与 Pydantic 配置模型的集成。
6.  修正因不符合配置验证规则及断言逻辑错误而导致的测试失败。
"""

from datetime import datetime
from decimal import Decimal

import pytest

from simtradelab.backtest.plugins.base import MarketData, Order, PluginMetadata
from simtradelab.backtest.plugins.config import (
    FixedSlippageModelConfig,
    LinearSlippageModelConfig,
    VolatilityBasedSlippageModelConfig,
    VolumeBasedSlippageModelConfig,
)
from simtradelab.backtest.plugins.slippage_models import (
    DynamicSlippageModel,
    FixedSlippageModel,
    LinearSlippageModel,
    VolatilityBasedSlippageModel,
    VolumeBasedSlippageModel,
)

# region Fixtures


@pytest.fixture
def plugin_metadata() -> PluginMetadata:
    """提供一个通用的插件元数据对象。"""
    return PluginMetadata(
        name="TestSlippageModel",
        version="1.0.0",
        description="A test slippage model.",
        author="Test Author",
        category="slippage_model",
        tags=["test"],
    )


@pytest.fixture
def base_order() -> Order:
    """提供一个基础订单对象。"""
    return Order(
        order_id="test_order_123",
        symbol="TEST.SH",
        side="buy",
        quantity=Decimal("100"),
        price=Decimal("10.0"),
        timestamp=datetime.now(),
    )


@pytest.fixture
def base_market_data() -> MarketData:
    """提供一个基础市场数据对象。"""
    return MarketData(
        symbol="TEST.SH",
        timestamp=datetime.now(),
        open_price=Decimal("10.0"),
        high_price=Decimal("10.2"),
        low_price=Decimal("9.8"),
        close_price=Decimal("10.1"),
        volume=Decimal("10000"),
    )


# endregion


class TestFixedSlippageModel:
    """测试固定滑点模型 (FixedSlippageModel)"""

    def test_initialization(self, plugin_metadata):
        """测试默认和自定义配置的初始化。"""
        model_default = FixedSlippageModel(plugin_metadata)
        default_config = FixedSlippageModelConfig()
        assert model_default._base_slippage_rate == default_config.base_slippage_rate

        custom_config = FixedSlippageModelConfig(
            base_slippage_rate=Decimal("0.002"),
            min_slippage=Decimal("0.01"),
            max_slippage=Decimal("0.1"),
        )
        model_custom = FixedSlippageModel(plugin_metadata, custom_config)
        assert model_custom._base_slippage_rate == custom_config.base_slippage_rate

    def test_calculate_slippage(self, plugin_metadata, base_order, base_market_data):
        """测试滑点计算。"""
        model = FixedSlippageModel(plugin_metadata)
        fill_price = Decimal("10.1")
        expected_slippage = fill_price * base_order.quantity * model._base_slippage_rate
        expected_slippage = max(
            model._min_slippage, min(model._max_slippage, expected_slippage)
        )

        slippage = model.calculate_slippage(base_order, base_market_data, fill_price)
        assert slippage == expected_slippage

    def test_slippage_limits(self, plugin_metadata, base_order, base_market_data):
        """测试最小和最大滑点限制。"""
        config = FixedSlippageModelConfig(
            base_slippage_rate=Decimal("0.00001"),
            min_slippage=Decimal("0.02"),
            max_slippage=Decimal("0.03"),
        )
        model = FixedSlippageModel(plugin_metadata, config)
        fill_price = Decimal("10.0")

        # 测试最小滑点
        base_order.quantity = Decimal("100")
        calculated_slippage = (
            fill_price * base_order.quantity * config.base_slippage_rate
        )  # 0.01
        assert calculated_slippage < config.min_slippage
        slippage = model.calculate_slippage(base_order, base_market_data, fill_price)
        assert slippage == config.min_slippage

        # 测试最大滑点
        base_order.quantity = Decimal("4000")
        calculated_slippage = (
            fill_price * base_order.quantity * config.base_slippage_rate
        )  # 0.04
        assert calculated_slippage > config.max_slippage
        slippage = model.calculate_slippage(base_order, base_market_data, fill_price)
        assert slippage == config.max_slippage


class TestLinearSlippageModel:
    """测试线性滑点模型 (LinearSlippageModel)"""

    def test_calculate_slippage_linear_logic(
        self, plugin_metadata, base_order, base_market_data
    ):
        """测试线性滑点计算逻辑。"""
        config = LinearSlippageModelConfig(
            base_rate=Decimal("0.001"),
            slope=Decimal("0.1"),
            reference_size=Decimal("1000"),
            max_slippage_rate=Decimal("0.05"),
            min_slippage=Decimal("0.01"),
            max_slippage=Decimal("0.2"),
        )
        model = LinearSlippageModel(plugin_metadata, config)

        base_order.quantity = Decimal("200")
        fill_price = Decimal("10.1")

        expected_rate = config.base_rate + config.slope * (
            base_order.quantity / config.reference_size
        )
        expected_rate = min(expected_rate, config.max_slippage_rate)
        expected_slippage = fill_price * base_order.quantity * expected_rate
        expected_slippage = max(
            config.min_slippage, min(config.max_slippage, expected_slippage)
        )

        slippage = model.calculate_slippage(base_order, base_market_data, fill_price)
        assert slippage == pytest.approx(expected_slippage)

    def test_get_slippage_rate(self, plugin_metadata, base_order, base_market_data):
        """测试 get_slippage_rate 方法并考虑上限。"""
        config = LinearSlippageModelConfig(
            base_rate=Decimal("0.001"),
            slope=Decimal("0.1"),
            reference_size=Decimal("1000"),
            max_slippage_rate=Decimal("0.01"),
        )
        model = LinearSlippageModel(plugin_metadata, config)

        base_order.quantity = Decimal("50")
        expected_rate_uncapped = config.base_rate + config.slope * (
            base_order.quantity / config.reference_size
        )
        rate_uncapped = model.get_slippage_rate(base_order, base_market_data)
        assert rate_uncapped == pytest.approx(expected_rate_uncapped)

        base_order.quantity = Decimal("500")
        rate_capped = model.get_slippage_rate(base_order, base_market_data)
        assert rate_capped == config.max_slippage_rate


class TestVolumeBasedSlippageModel:
    """测试基于成交量的滑点模型 (VolumeBasedSlippageModel)"""

    def test_calculate_slippage(self, plugin_metadata, base_order, base_market_data):
        """测试完整的滑点计算。"""
        config = VolumeBasedSlippageModelConfig(
            base_slippage_rate=Decimal("0.001"),
            volume_impact_factor=Decimal("0.5"),
            volume_impact_curve="square_root",
            min_slippage=Decimal("0.01"),
            max_slippage=Decimal("0.2"),
        )
        model = VolumeBasedSlippageModel(plugin_metadata, config)

        base_order.quantity = Decimal("100")
        fill_price = Decimal("10.1")

        volume_ratio = float(base_order.quantity / base_market_data.volume)
        volume_impact = model._calculate_volume_impact(volume_ratio)
        base_slippage = fill_price * base_order.quantity * config.base_slippage_rate
        expected_slippage = base_slippage * (Decimal("1") + volume_impact)
        expected_slippage = max(
            config.min_slippage, min(config.max_slippage, expected_slippage)
        )

        slippage = model.calculate_slippage(base_order, base_market_data, fill_price)
        assert slippage == pytest.approx(expected_slippage)


class TestVolatilityBasedSlippageModel:
    """测试基于波动率的滑点模型 (VolatilityBasedSlippageModel)"""

    def test_update_price_history(self, plugin_metadata):
        """测试价格历史记录的更新和长度限制。"""
        config = VolatilityBasedSlippageModelConfig(max_history_length=10)
        model = VolatilityBasedSlippageModel(plugin_metadata, config)

        for i in range(12):
            model._update_price_history(Decimal(str(10 + i)))

        assert len(model._price_history) == 10
        assert model._price_history[0] == Decimal("12")
        assert model._price_history[-1] == Decimal("21")

    def test_calculate_slippage(self, plugin_metadata, base_order, base_market_data):
        """测试基于波动率的滑点计算。"""
        config = VolatilityBasedSlippageModelConfig(
            volatility_multiplier=Decimal("10.0"),  # 修复：符合 le=10 的验证规则
            base_slippage_rate=Decimal("0.0001"),  # 降低基础费率以避免触及上限
            max_slippage=Decimal("0.2"),
        )
        model = VolatilityBasedSlippageModel(plugin_metadata, config)
        fill_price = Decimal("10.1")

        # 模拟高波动
        high_vol_prices = [10, 12, 9, 13, 8] * 2
        for p in high_vol_prices:
            model._update_price_history(Decimal(str(p)))
        high_vol_slippage = model.calculate_slippage(
            base_order, base_market_data, fill_price
        )

        # 重置并模拟低波动
        model._price_history = []
        low_vol_prices = [10.0, 10.01, 9.99, 10.02, 9.98] * 2
        for p in low_vol_prices:
            model._update_price_history(Decimal(str(p)))
        low_vol_slippage = model.calculate_slippage(
            base_order, base_market_data, fill_price
        )

        assert high_vol_slippage > low_vol_slippage


class TestDynamicSlippageModel:
    """测试动态滑点模型 (DynamicSlippageModel)"""

    def test_calculate_slippage_combination(
        self, plugin_metadata, base_order, base_market_data
    ):
        """测试结合了成交量和波动率的滑点计算。"""
        config = VolumeBasedSlippageModelConfig(
            base_slippage_rate=Decimal("0.001"),
            volume_impact_factor=Decimal("0.5"),
            volatility_multiplier=Decimal("10.0"),
            max_slippage=Decimal("0.2"),
        )
        model = DynamicSlippageModel(plugin_metadata, config)

        prices = [10, 10.5, 9.5, 11, 9] * 2
        for p in prices:
            model._update_price_history(Decimal(str(p)))

        base_order.quantity = Decimal("10")
        fill_price = Decimal("10.1")

        base_slippage = fill_price * base_order.quantity * config.base_slippage_rate
        volume_ratio = float(base_order.quantity / base_market_data.volume)
        volume_impact = model._calculate_volume_impact(volume_ratio)
        volatility_adjustment = model._calculate_volatility_adjustment()
        expected_slippage = (
            base_slippage
            * (Decimal("1") + volume_impact)
            * (Decimal("1") + volatility_adjustment)
        )
        expected_slippage = max(
            config.min_slippage, min(config.max_slippage, expected_slippage)
        )

        slippage = model.calculate_slippage(base_order, base_market_data, fill_price)

        assert slippage == pytest.approx(expected_slippage)
        assert slippage > base_slippage
