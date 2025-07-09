# -*- coding: utf-8 -*-
"""
SimTradeLab - 开源策略回测框架

基于事件驱动架构的量化交易策略回测平台，完全兼容PTrade API。
"""

from .core.event_bus import EventBus
from .core.plugin_manager import PluginManager

# 异常系统
from .exceptions import (
    ConfigurationError,
    DataLoadError,
    DataSourceError,
    DataValidationError,
    EngineError,
    InsufficientFundsError,
    InsufficientPositionError,
    InvalidOrderError,
    ReportGenerationError,
    SimTradeLabError,
    StrategyError,
    TradingError,
)

# 核心插件系统
from .plugins.base import BasePlugin

# PTrade 兼容层
try:
    from .adapters.ptrade import APIRouter, PTradeAdapter, PTradeMode

    _PTRADE_AVAILABLE = True
except ImportError:
    _PTRADE_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "SimTradeLab Team"

__all__ = [
    # 核心插件系统
    "BasePlugin",
    "EventBus",
    "PluginManager",
    # 异常系统
    "SimTradeLabError",
    "DataSourceError",
    "DataLoadError",
    "DataValidationError",
    "TradingError",
    "InsufficientFundsError",
    "InsufficientPositionError",
    "InvalidOrderError",
    "EngineError",
    "StrategyError",
    "ConfigurationError",
    "ReportGenerationError",
]

# 动态添加PTrade适配器到导出列表
if _PTRADE_AVAILABLE:
    __all__.extend(["PTradeAdapter", "PTradeMode", "APIRouter"])
