# -*- coding: utf-8 -*-
"""
SimTradeLab: A Pluggable Quantitative Trading Framework
"""

__author__ = "SimTradeLab"
__version__ = "5.0.0"

# 回测系统
from .backtest.engine import BacktestEngine
from .backtest.plugins.base import (
    BaseCommissionModel,
    BaseMatchingEngine,
    BaseSlippageModel,
)
from .core.config.config_manager import PluginConfigManager

# 核心组件
from .core.event_bus import EventBus
from .core.plugin_manager import PluginManager

# 异常
from .exceptions import (
    DataLoadError,
    DataSourceError,
    DataValidationError,
    EngineError,
    InsufficientFundsError,
    InsufficientPositionError,
    InvalidOrderError,
)
from .exceptions import PluginConfigurationError as ConfigurationError
from .exceptions import (
    PluginError,
    PluginLoadError,
    PluginNotFoundError,
    PluginRegistrationError,
    ReportGenerationError,
    SimTradeLabException,
    StrategyError,
    StrategyNotFoundException,
    StrategySyntaxError,
    TradingError,
)

# 插件系统
from .plugins.base import BasePlugin, PluginMetadata
from .plugins.config.base_config import BasePluginConfig
from .plugins.data.base_data_source import BaseDataSourcePlugin

# 运行器


__all__ = [
    "BacktestEngine",
    # 核心组件
    "EventBus",
    "PluginManager",
    "PluginConfigManager",
    # 插件系统
    "BasePlugin",
    "PluginMetadata",
    "BasePluginConfig",
    "BaseDataSourcePlugin",
    # 回测插件
    "BaseMatchingEngine",
    "BaseSlippageModel",
    "BaseCommissionModel",
    # 异常
    "SimTradeLabException",
    "ConfigurationError",
    "PluginError",
    "PluginNotFoundError",
    "PluginRegistrationError",
    "PluginLoadError",
    "DataSourceError",
    "DataLoadError",
    "DataValidationError",
    "TradingError",
    "InsufficientFundsError",
    "InsufficientPositionError",
    "InvalidOrderError",
    "EngineError",
    "StrategyError",
    "StrategyNotFoundException",
    "StrategySyntaxError",
    "ReportGenerationError",
]
