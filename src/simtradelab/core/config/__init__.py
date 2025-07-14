# -*- coding: utf-8 -*-
"""
SimTradeLab 配置管理系统

E9修复：提供统一、类型安全的插件配置管理，消除丑陋的运行时验证代码。
"""

from .config_manager import PluginConfigManager
from .decorators import plugin_config
from .factory import ConfigFactory
from .validators import ConfigValidator

__all__ = [
    "PluginConfigManager",
    "plugin_config",
    "ConfigFactory",
    "ConfigValidator",
]
