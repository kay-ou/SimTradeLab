# -*- coding: utf-8 -*-
"""
PTrade兼容层适配器模块

提供完整的PTrade API兼容性，支持研究、回测、交易三种模式。
"""

from .adapter import PTradeAdapter
from .context import PTradeContext, PTradeMode
from .models import (
    Blotter,
    Commission,
    FutureParams,
    Order,
    Portfolio,
    Position,
    SecurityUnitData,
    SimulationParameters,
    VolumeShareSlippage,
)
from .routers import (
    BacktestAPIRouter,
    BaseAPIRouter,
    ResearchAPIRouter,
    TradingAPIRouter,
)
from .utils import PTradeAdapterError, PTradeAPIError, PTradeCompatibilityError

__all__ = [
    # 主要适配器
    "PTradeAdapter",
    # 上下文和模式
    "PTradeContext",
    "PTradeMode",
    # 数据模型
    "Portfolio",
    "Position",
    "Order",
    "Blotter",
    "SecurityUnitData",
    "SimulationParameters",
    "VolumeShareSlippage",
    "Commission",
    "FutureParams",
    # API路由器
    "BaseAPIRouter",
    "BacktestAPIRouter",
    "TradingAPIRouter",
    "ResearchAPIRouter",
    # 异常类
    "PTradeAdapterError",
    "PTradeCompatibilityError",
    "PTradeAPIError",
]
