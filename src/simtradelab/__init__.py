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
from .adapters.ptrade import BaseAPIRouter, PTradeAdapter, PTradeMode

__version__ = "1.0.0"
__author__ = "SimTradeLab Team"

__all__ = [
    # 核心插件系统
    "BasePlugin",
    "EventBus",
    "PluginManager",
    # PTrade 兼容层
    "BaseAPIRouter",
    "PTradeAdapter", 
    "PTradeMode",
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
