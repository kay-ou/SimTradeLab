# -*- coding: utf-8 -*-
"""
SimTradeLab: A Pluggable Quantitative Trading Framework
"""

__author__ = "SimTradeLab"
__version__ = "5.0.0"

# 核心组件
from .core.event_bus import EventBus
from .core.plugin_manager import PluginManager
from .core.config.config_manager import PluginConfigManager

# 插件系统
from .plugins.base import BasePlugin, PluginMetadata
from .plugins.config.base_config import BasePluginConfig
from .plugins.data.base_data_source import BaseDataSourcePlugin

# 回测系统
from .backtest.engine import BacktestEngine
from .backtest.plugins.base import (
    BaseMatchingEngine,
    BaseSlippageModel,
    BaseCommissionModel,
)

# 运行器
from .runner import BacktestRunner

# 异常
from .exceptions import (
    SimTradeLabError,
    ConfigurationError,
)

__all__ = [
    "BacktestRunner",
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
    "SimTradeLabError",
    "ConfigurationError",
]
