# -*- coding: utf-8 -*-
"""
回测插件配置模型测试

测试E8修复：统一的Pydantic配置验证
"""

from decimal import Decimal
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from simtradelab.backtest.plugins.config import (
    BACKTEST_PLUGIN_CONFIG_MAPPING,
    DepthMatchingEngineConfig,
    FixedCommissionModelConfig,
    LimitMatchingEngineConfig,
    LinearSlippageModelConfig,
    SimpleMatchingEngineConfig,
    TieredCommissionModelConfig,
    VolumeBasedSlippageModelConfig,
    get_config_model_for_plugin,
)


class TestSimpleMatchingEngineConfig:
    """简单撮合引擎配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = SimpleMatchingEngineConfig()

        assert config.price_tolerance == Decimal("0.01")
        assert config.enable_partial_fill is True
        assert config.max_order_size is None

    def test_valid_config(self):
        """测试有效配置"""
        data = {
            "price_tolerance": "0.05",
            "enable_partial_fill": False,
            "max_order_size": "10000",
        }

        config = SimpleMatchingEngineConfig(**data)

        assert config.price_tolerance == Decimal("0.05")
        assert config.enable_partial_fill is False
        assert config.max_order_size == Decimal("10000")

    def test_invalid_price_tolerance(self):
        """测试无效价格容忍度"""
        with pytest.raises(ValidationError):
            SimpleMatchingEngineConfig(price_tolerance="-0.01")

        with pytest.raises(ValidationError):
            SimpleMatchingEngineConfig(price_tolerance="1.5")

    def test_invalid_max_order_size(self):
        """测试无效最大订单数量"""
        with pytest.raises(ValidationError):
            SimpleMatchingEngineConfig(max_order_size="-100")


class TestDepthMatchingEngineConfig:
    """深度撮合引擎配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = DepthMatchingEngineConfig()

        assert config.depth_levels == 5
        assert config.liquidity_factor == Decimal("0.1")
        assert config.volume_impact_factor == Decimal("0.001")
        assert config.max_fill_ratio == Decimal("0.1")

    def test_valid_config(self):
        """测试有效配置"""
        data = {
            "depth_levels": 10,
            "liquidity_factor": "0.2",
            "volume_impact_factor": "0.005",
            "max_fill_ratio": "0.15",
            "min_fill_amount": "200",
        }

        config = DepthMatchingEngineConfig(**data)

        assert config.depth_levels == 10
        assert config.liquidity_factor == Decimal("0.2")
        assert config.volume_impact_factor == Decimal("0.005")
        assert config.max_fill_ratio == Decimal("0.15")
        assert config.min_fill_amount == Decimal("200")

    def test_invalid_depth_levels(self):
        """测试无效深度层级"""
        with pytest.raises(ValidationError):
            DepthMatchingEngineConfig(depth_levels=0)

        with pytest.raises(ValidationError):
            DepthMatchingEngineConfig(depth_levels=25)

    def test_invalid_factors(self):
        """测试无效因子值"""
        with pytest.raises(ValidationError):
            DepthMatchingEngineConfig(liquidity_factor="0.005")  # 小于最小值

        with pytest.raises(ValidationError):
            DepthMatchingEngineConfig(volume_impact_factor="0.15")  # 大于最大值


class TestLimitMatchingEngineConfig:
    """限价撮合引擎配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = LimitMatchingEngineConfig()

        assert config.strict_limit_check is True
        assert config.order_queue_enabled is True
        assert config.max_queue_size == 1000
        assert config.allow_market_order is True
        assert config.price_precision == 2

    def test_valid_config(self):
        """测试有效配置"""
        data = {
            "strict_limit_check": False,
            "max_queue_size": 500,
            "price_precision": 4,
            "allow_partial_fills": False,
        }

        config = LimitMatchingEngineConfig(**data)

        assert config.strict_limit_check is False
        assert config.max_queue_size == 500
        assert config.price_precision == 4
        assert config.allow_partial_fills is False

    def test_invalid_queue_size(self):
        """测试无效队列大小"""
        with pytest.raises(ValidationError):
            LimitMatchingEngineConfig(max_queue_size=5)  # 小于最小值

        with pytest.raises(ValidationError):
            LimitMatchingEngineConfig(max_queue_size=20000)  # 大于最大值

    def test_invalid_price_precision(self):
        """测试无效价格精度"""
        with pytest.raises(ValidationError):
            LimitMatchingEngineConfig(price_precision=-1)

        with pytest.raises(ValidationError):
            LimitMatchingEngineConfig(price_precision=10)


class TestSlippageModelConfigs:
    """滑点模型配置测试"""

    def test_linear_slippage_default(self):
        """测试线性滑点模型默认配置"""
        config = LinearSlippageModelConfig()

        assert config.base_slippage_rate == Decimal("0.001")
        assert config.volume_impact_factor == Decimal("0.01")
        assert config.volatility_multiplier == Decimal("1.0")
        assert config.min_slippage == Decimal("0.0001")
        assert config.max_slippage == Decimal("0.05")

    def test_volume_based_slippage_config(self):
        """测试基于成交量的滑点模型配置"""
        data = {
            "volume_threshold": "20000",
            "volume_impact_curve": "square_root",
            "base_slippage_rate": "0.002",
        }

        config = VolumeBasedSlippageModelConfig(**data)

        assert config.volume_threshold == Decimal("20000")
        assert config.volume_impact_curve == "square_root"
        assert config.base_slippage_rate == Decimal("0.002")

    def test_invalid_slippage_rates(self):
        """测试无效滑点率"""
        with pytest.raises(ValidationError):
            LinearSlippageModelConfig(base_slippage_rate="-0.001")

        with pytest.raises(ValidationError):
            LinearSlippageModelConfig(base_slippage_rate="0.15")  # 大于最大值

    def test_invalid_volume_impact_curve(self):
        """测试无效成交量冲击曲线"""
        with pytest.raises(ValidationError):
            VolumeBasedSlippageModelConfig(volume_impact_curve="invalid_curve")

    def test_slippage_range_validation(self):
        """测试滑点范围验证"""
        # 验证max_slippage < min_slippage应该产生验证错误
        with pytest.raises(ValidationError):
            LinearSlippageModelConfig(
                min_slippage="0.001", max_slippage="0.0005"  # 小于min_slippage
            )


class TestCommissionModelConfigs:
    """手续费模型配置测试"""

    def test_fixed_commission_default(self):
        """测试固定手续费模型默认配置"""
        config = FixedCommissionModelConfig()

        assert config.commission_rate == Decimal("0.0003")
        assert config.min_commission == Decimal("5.0")
        assert config.stamp_duty_rate == Decimal("0.001")
        assert config.transfer_fee_rate == Decimal("0.00002")
        assert config.enable_stamp_duty is True
        assert config.enable_transfer_fee is True

    def test_tiered_commission_config(self):
        """测试分层手续费模型配置"""
        data = {
            "tier_thresholds": {"tier1": "50000", "tier2": "500000"},
            "tier_rates": {"tier1": "0.001", "tier2": "0.0005", "tier3": "0.0003"},
        }

        config = TieredCommissionModelConfig(**data)

        assert config.tier_thresholds["tier1"] == Decimal("50000")
        assert config.tier_rates["tier1"] == Decimal("0.001")

    def test_invalid_commission_rates(self):
        """测试无效手续费率"""
        with pytest.raises(ValidationError):
            FixedCommissionModelConfig(commission_rate="-0.001")

        with pytest.raises(ValidationError):
            FixedCommissionModelConfig(commission_rate="0.02")  # 大于最大值

    def test_invalid_min_commission(self):
        """测试无效最低手续费"""
        with pytest.raises(ValidationError):
            FixedCommissionModelConfig(min_commission="-5")

    def test_invalid_tier_rates(self):
        """测试无效分层费率"""
        with pytest.raises(ValidationError):
            TieredCommissionModelConfig(
                tier_rates={"tier1": "0.02", "tier2": "0.001"}  # 大于最大值1%
            )


class TestConfigMapping:
    """配置映射测试"""

    def test_get_config_model_for_plugin(self):
        """测试根据插件名获取配置模型"""
        # 测试已知插件
        assert (
            get_config_model_for_plugin("SimpleMatchingEngine")
            == SimpleMatchingEngineConfig
        )
        assert (
            get_config_model_for_plugin("DepthMatchingEngine")
            == DepthMatchingEngineConfig
        )
        assert (
            get_config_model_for_plugin("LinearSlippageModel")
            == LinearSlippageModelConfig
        )
        assert (
            get_config_model_for_plugin("FixedCommissionModel")
            == FixedCommissionModelConfig
        )

        # 测试未知插件
        from simtradelab.plugins.config.base_config import BasePluginConfig

        assert get_config_model_for_plugin("UnknownPlugin") == BasePluginConfig

    def test_config_mapping_completeness(self):
        """测试配置映射完整性"""
        expected_plugins = {
            "SimpleMatchingEngine",
            "DepthMatchingEngine",
            "LimitMatchingEngine",
            "LinearSlippageModel",
            "VolumeBasedSlippageModel",
            "FixedCommissionModel",
            "TieredCommissionModel",
        }

        actual_plugins = set(BACKTEST_PLUGIN_CONFIG_MAPPING.keys())
        assert expected_plugins.issubset(actual_plugins)


class TestConfigFromDict:
    """从字典配置测试"""

    def test_load_from_dict(self):
        """测试从字典加载配置"""
        config_data = {
            "default": {"price_tolerance": "0.02", "enable_partial_fill": False}
        }

        config = SimpleMatchingEngineConfig.load_from_dict(config_data)

        assert config.price_tolerance == Decimal("0.02")
        assert config.enable_partial_fill is False

    def test_load_with_invalid_data(self):
        """测试加载无效数据"""
        config_data = {
            "default": {
                "price_tolerance": "2.0",  # 大于最大值
                "enable_partial_fill": "invalid_bool",
            }
        }

        with pytest.raises(ValidationError):
            SimpleMatchingEngineConfig.load_from_dict(config_data)

    def test_load_with_missing_optional_fields(self):
        """测试加载缺少可选字段的配置"""
        config_data = {"default": {"enable_partial_fill": True}}

        config = SimpleMatchingEngineConfig.load_from_dict(config_data)

        # 应该使用默认值
        assert config.price_tolerance == Decimal("0.01")
        assert config.enable_partial_fill is True
