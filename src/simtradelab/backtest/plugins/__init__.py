# -*- coding: utf-8 -*-
"""
回测插件包初始化
"""

from .base import (
    PLUGIN_TYPE_COMMISSION_MODEL,
    PLUGIN_TYPE_MATCHING_ENGINE,
    PLUGIN_TYPE_SLIPPAGE_MODEL,
    BacktestContext,
    BaseBacktestPlugin,
    BaseCommissionModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    Fill,
    MarketData,
    Order,
    Position,
)

# 手续费模型实现
from .commission_models import (
    ChinaAStockCommissionModel,
    ComprehensiveCommissionModel,
    FixedCommissionModel,
    PerShareCommissionModel,
    TieredCommissionModel,
)

# 撮合引擎实现
from .matching_engines import DepthMatchingEngine

# 滑点模型实现
from .slippage_models import LinearSlippageModel, VolumeBasedSlippageModel

__all__ = [
    # 基础类
    "BaseBacktestPlugin",
    "BaseMatchingEngine",
    "BaseSlippageModel",
    "BaseCommissionModel",
    "Order",
    "Fill",
    "MarketData",
    "Position",
    "BacktestContext",
    "PLUGIN_TYPE_MATCHING_ENGINE",
    "PLUGIN_TYPE_SLIPPAGE_MODEL",
    "PLUGIN_TYPE_COMMISSION_MODEL",
    # 撮合引擎实现
    "SimpleMatchingEngine",
    "DepthMatchingEngine",
    "StrictLimitMatchingEngine",
    # 滑点模型实现
    "LinearSlippageModel",
    "VolumeBasedSlippageModel",
    # 手续费模型实现
    "ChinaAStockCommissionModel",
    "FixedCommissionModel",
    "TieredCommissionModel",
    "ComprehensiveCommissionModel",
    "PerShareCommissionModel",
]
