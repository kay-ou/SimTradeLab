# -*- coding: utf-8 -*-
"""
回测插件统一配置模型

基于Pydantic的回测插件配置类，提供类型安全的配置验证。
修复E8: 配置系统缺乏统一验证问题。
"""

from decimal import Decimal
from typing import Dict, Optional

from pydantic import Field, field_validator

from simtradelab.plugins.config.base_config import BasePluginConfig


class MatchingEngineConfig(BasePluginConfig):
    """撮合引擎配置模型"""
    
    price_tolerance: Decimal = Field(
        default=Decimal("0.01"),
        description="价格容忍度，用于判断限价单是否可以成交",
        ge=0,
        le=1
    )
    
    enable_partial_fill: bool = Field(
        default=True,
        description="是否允许部分成交"
    )
    
    max_order_size: Optional[Decimal] = Field(
        default=None,
        description="单笔订单最大数量限制",
        gt=0
    )
    
    @field_validator('price_tolerance')
    @classmethod
    def validate_price_tolerance(cls, v: Decimal) -> Decimal:
        """验证价格容忍度"""
        if v < 0 or v > 1:
            raise ValueError('价格容忍度必须在0-1之间')
        return v


class SlippageModelConfig(BasePluginConfig):
    """滑点模型配置模型"""
    
    base_slippage_rate: Decimal = Field(
        default=Decimal("0.001"),
        description="基础滑点率（默认0.1%）",
        ge=0,
        le=0.1
    )
    
    volume_impact_factor: Decimal = Field(
        default=Decimal("0.01"),
        description="成交量冲击因子",
        ge=0,
        le=1
    )
    
    volatility_multiplier: Decimal = Field(
        default=Decimal("1.0"),
        description="波动率乘数",
        ge=0.1,
        le=10
    )
    
    min_slippage: Decimal = Field(
        default=Decimal("0.0001"),
        description="最小滑点（0.01%）",
        ge=0
    )
    
    max_slippage: Decimal = Field(
        default=Decimal("0.05"),
        description="最大滑点（5%）",
        ge=0,
        le=0.2
    )
    
    @field_validator('max_slippage')
    @classmethod
    def validate_slippage_range(cls, v: Decimal, info) -> Decimal:
        """验证滑点范围"""
        if hasattr(info, 'data') and 'min_slippage' in info.data and v < info.data['min_slippage']:
            raise ValueError('最大滑点不能小于最小滑点')
        return v


class CommissionModelConfig(BasePluginConfig):
    """手续费模型配置模型"""
    
    commission_rate: Decimal = Field(
        default=Decimal("0.0003"),
        description="手续费率（默认万分之3）",
        ge=0,
        le=0.01
    )
    
    min_commission: Decimal = Field(
        default=Decimal("5.0"),
        description="最低手续费（元）",
        ge=0
    )
    
    stamp_duty_rate: Decimal = Field(
        default=Decimal("0.001"),
        description="印花税率（仅卖出，默认千分之1）",
        ge=0,
        le=0.005
    )
    
    transfer_fee_rate: Decimal = Field(
        default=Decimal("0.00002"),
        description="过户费率（默认万分之0.2）",
        ge=0,
        le=0.001
    )
    
    enable_stamp_duty: bool = Field(
        default=True,
        description="是否启用印花税（A股特有）"
    )
    
    enable_transfer_fee: bool = Field(
        default=True,
        description="是否启用过户费"
    )
    
    @field_validator('min_commission')
    @classmethod
    def validate_min_commission(cls, v: Decimal) -> Decimal:
        """验证最低手续费"""
        if v < 0:
            raise ValueError('最低手续费不能为负数')
        return v


class SimpleMatchingEngineConfig(MatchingEngineConfig):
    """简单撮合引擎配置"""
    
    class Config:
        title = "简单撮合引擎配置"
        description = "基本的价格撮合引擎配置选项"


class DepthMatchingEngineConfig(MatchingEngineConfig):
    """深度撮合引擎配置"""
    
    depth_levels: int = Field(
        default=5,
        description="考虑的市场深度层级数",
        ge=1,
        le=20
    )
    
    liquidity_factor: Decimal = Field(
        default=Decimal("0.1"),
        description="流动性因子，影响大额订单的成交",
        ge=0.01,
        le=1
    )
    
    volume_impact_factor: Decimal = Field(
        default=Decimal("0.001"),
        description="成交量冲击因子",
        ge=0,
        le=0.1
    )
    
    max_fill_ratio: Decimal = Field(
        default=Decimal("0.1"),
        description="最大成交比例（相对于市场成交量）",
        ge=0.01,
        le=1
    )
    
    min_fill_amount: Decimal = Field(
        default=Decimal("100"),
        description="最小成交金额",
        ge=0
    )
    
    min_depth_ratio: Decimal = Field(
        default=Decimal("0.05"),
        description="最小深度比例",
        ge=0,
        le=1
    )
    
    max_spread_ratio: Decimal = Field(
        default=Decimal("0.02"),
        description="最大价差比例",
        ge=0,
        le=1
    )
    
    class Config:
        title = "深度撮合引擎配置"
        description = "考虑订单深度的撮合引擎配置选项"


class LimitMatchingEngineConfig(MatchingEngineConfig):
    """限价撮合引擎配置"""
    
    strict_limit_check: bool = Field(
        default=True,
        description="是否严格检查限价条件"
    )
    
    order_queue_enabled: bool = Field(
        default=True,
        description="是否启用订单队列机制"
    )
    
    max_queue_size: int = Field(
        default=1000,
        description="订单队列最大大小",
        ge=10,
        le=10000
    )
    
    allow_market_order: bool = Field(
        default=True,
        description="是否允许市价单"
    )
    
    price_precision: int = Field(
        default=2,
        description="价格精度（小数位数）",
        ge=0,
        le=8
    )
    
    allow_partial_fills: bool = Field(
        default=True,
        description="是否允许部分成交"
    )
    
    class Config:
        title = "限价撮合引擎配置"
        description = "严格限价单撮合引擎配置选项"


class LinearSlippageModelConfig(SlippageModelConfig):
    """线性滑点模型配置"""
    
    class Config:
        title = "线性滑点模型配置"
        description = "线性滑点计算模型配置选项"


class VolumeBasedSlippageModelConfig(SlippageModelConfig):
    """基于成交量的滑点模型配置"""
    
    volume_threshold: Decimal = Field(
        default=Decimal("10000"),
        description="成交量阈值，超过此值会增加滑点",
        gt=0
    )
    
    volume_impact_curve: str = Field(
        default="square_root",
        description="成交量冲击曲线类型",
        pattern="^(linear|square_root|logarithmic)$"
    )
    
    class Config:
        title = "基于成交量的滑点模型配置"
        description = "考虑成交量影响的滑点模型配置选项"


class FixedCommissionModelConfig(CommissionModelConfig):
    """固定手续费模型配置"""
    
    class Config:
        title = "固定手续费模型配置"
        description = "固定费率手续费模型配置选项"


class TieredCommissionModelConfig(CommissionModelConfig):
    """分层手续费模型配置"""
    
    tier_thresholds: Dict[str, Decimal] = Field(
        default={
            "tier1": Decimal("100000"),    # 10万以下
            "tier2": Decimal("1000000"),   # 100万以下
            "tier3": Decimal("10000000")   # 1000万以下
        },
        description="分层阈值设置"
    )
    
    tier_rates: Dict[str, Decimal] = Field(
        default={
            "tier1": Decimal("0.0008"),    # 万8
            "tier2": Decimal("0.0005"),    # 万5
            "tier3": Decimal("0.0003"),    # 万3
            "tier4": Decimal("0.0002")     # 万2
        },
        description="各层级费率设置"
    )
    
    @field_validator('tier_rates')
    @classmethod
    def validate_tier_rates(cls, v: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """验证分层费率"""
        for rate in v.values():
            if rate < 0 or rate > 0.01:
                raise ValueError('费率必须在0-1%之间')
        return v
    
    class Config:
        title = "分层手续费模型配置"
        description = "根据交易金额分层计费的手续费模型配置选项"


# 配置映射字典，用于插件自动配置模型选择
BACKTEST_PLUGIN_CONFIG_MAPPING = {
    "SimpleMatchingEngine": SimpleMatchingEngineConfig,
    "DepthMatchingEngine": DepthMatchingEngineConfig,
    "LimitMatchingEngine": LimitMatchingEngineConfig,
    "LinearSlippageModel": LinearSlippageModelConfig,
    "VolumeBasedSlippageModel": VolumeBasedSlippageModelConfig,
    "FixedCommissionModel": FixedCommissionModelConfig,
    "TieredCommissionModel": TieredCommissionModelConfig,
}


def get_config_model_for_plugin(plugin_name: str) -> type:
    """
    根据插件名称获取对应的配置模型类
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        配置模型类，如果未找到则返回基础配置类
    """
    return BACKTEST_PLUGIN_CONFIG_MAPPING.get(plugin_name, BasePluginConfig)