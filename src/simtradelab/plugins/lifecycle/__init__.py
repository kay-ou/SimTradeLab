# -*- coding: utf-8 -*-
"""
插件生命周期管理模块

负责插件的热插拔、状态管理和生命周期控制。
"""

from .plugin_lifecycle_manager import PluginLifecycleManager

__all__ = [
    "PluginLifecycleManager"
]