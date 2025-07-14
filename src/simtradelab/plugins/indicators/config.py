# -*- coding: utf-8 -*-
"""
技术指标插件统一配置模型

基于Pydantic的技术指标插件配置类，提供类型安全的配置验证。
修复E8: 配置系统缺乏统一验证问题。
"""

from decimal import Decimal
from typing import Dict

from pydantic import Field, field_validator

from simtradelab.plugins.config.base_config import BasePluginConfig


class TechnicalIndicatorsConfig(BasePluginConfig):
    """技术指标插件配置模型"""

    model_config = {
        "title": "技术指标插件配置",
        "description": "技术指标插件的配置选项",
        "extra": "ignore",
    }

    cache_timeout: int = Field(default=300, description="指标计算缓存超时时间（秒）", ge=0, le=3600)

    # MACD指标参数
    macd_short: int = Field(default=12, description="MACD快线周期", ge=1, le=100)

    macd_long: int = Field(default=26, description="MACD慢线周期", ge=1, le=200)

    macd_signal: int = Field(default=9, description="MACD信号线周期", ge=1, le=50)

    # KDJ指标参数
    kdj_n: int = Field(default=9, description="KDJ周期", ge=1, le=100)

    kdj_m1: int = Field(default=3, description="KDJ K值平滑周期", ge=1, le=20)

    kdj_m2: int = Field(default=3, description="KDJ D值平滑周期", ge=1, le=20)

    # RSI指标参数
    rsi_period: int = Field(default=6, description="RSI周期", ge=1, le=100)

    # CCI指标参数
    cci_period: int = Field(default=14, description="CCI周期", ge=1, le=100)

    # 布林带参数
    bollinger_period: int = Field(default=20, description="布林带周期", ge=5, le=100)

    bollinger_std: Decimal = Field(
        default=Decimal("2.0"), description="布林带标准差倍数", ge=1, le=5
    )

    # 移动平均线参数
    ma_periods: Dict[str, int] = Field(
        default={"ma5": 5, "ma10": 10, "ma20": 20, "ma30": 30, "ma60": 60},
        description="移动平均线周期配置",
    )

    # 性能优化参数
    enable_parallel_calculation: bool = Field(default=False, description="是否启用并行计算")

    max_cache_size: int = Field(default=1000, description="最大缓存条目数", ge=10, le=10000)

    @field_validator("macd_long")
    @classmethod
    def validate_macd_periods(cls, v: int, info) -> int:
        """验证MACD周期参数"""
        if hasattr(info, "data") and "macd_short" in info.data:
            if v <= info.data["macd_short"]:
                raise ValueError("MACD慢线周期必须大于快线周期")
        return v

    @field_validator("ma_periods")
    @classmethod
    def validate_ma_periods(cls, v: Dict[str, int]) -> Dict[str, int]:
        """验证移动平均线周期"""
        for name, period in v.items():
            if period <= 0:
                raise ValueError(f"移动平均线周期 {name} 必须大于0")
        return v


class AdvancedTechnicalIndicatorsConfig(TechnicalIndicatorsConfig):
    """高级技术指标插件配置模型"""

    model_config = {
        "title": "高级技术指标插件配置",
        "description": "高级技术指标插件的配置选项",
        "extra": "ignore",
    }

    # MACD高级参数
    macd_histogram_multiplier: Decimal = Field(
        default=Decimal("2.0"), description="MACD柱状图倍数", ge=1, le=5
    )

    # ATR参数
    atr_period: int = Field(default=14, description="ATR周期", ge=1, le=100)

    # Stochastic参数
    stochastic_k_period: int = Field(default=14, description="随机指标K周期", ge=1, le=100)

    stochastic_d_period: int = Field(default=3, description="随机指标D周期", ge=1, le=20)

    # Williams %R参数
    williams_r_period: int = Field(default=14, description="威廉指标周期", ge=1, le=100)

    # MACD背离检测
    enable_divergence_detection: bool = Field(default=False, description="是否启用背离检测")

    divergence_lookback: int = Field(default=50, description="背离检测回看周期", ge=10, le=200)


class CustomIndicatorConfig(BasePluginConfig):
    """自定义指标配置模型"""

    model_config = {
        "title": "自定义指标配置",
        "description": "自定义指标的配置选项",
        "extra": "ignore",
    }

    formula: str = Field(description="自定义指标计算公式")

    parameters: Dict[str, float] = Field(default={}, description="自定义指标参数")

    lookback_period: int = Field(default=20, description="回看周期", ge=1, le=500)

    output_name: str = Field(description="输出指标名称")

    @field_validator("formula")
    @classmethod
    def validate_formula(cls, v: str) -> str:
        """验证计算公式"""
        if not v.strip():
            raise ValueError("计算公式不能为空")
        return v

    @field_validator("output_name")
    @classmethod
    def validate_output_name(cls, v: str) -> str:
        """验证输出名称"""
        if not v.strip():
            raise ValueError("输出指标名称不能为空")
        return v


# 配置映射字典，用于插件自动配置模型选择
INDICATORS_PLUGIN_CONFIG_MAPPING = {
    "TechnicalIndicatorsPlugin": TechnicalIndicatorsConfig,
    "technical_indicators_plugin": TechnicalIndicatorsConfig,
    "AdvancedTechnicalIndicators": AdvancedTechnicalIndicatorsConfig,
    "CustomIndicator": CustomIndicatorConfig,
}


def get_config_model_for_indicator_plugin(plugin_name: str) -> type:
    """
    根据指标插件名称获取对应的配置模型类

    Args:
        plugin_name: 插件名称

    Returns:
        配置模型类，如果未找到则返回基础配置类
    """
    return INDICATORS_PLUGIN_CONFIG_MAPPING.get(plugin_name, TechnicalIndicatorsConfig)
