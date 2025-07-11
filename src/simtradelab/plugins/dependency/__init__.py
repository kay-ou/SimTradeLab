# -*- coding: utf-8 -*-
"""
插件依赖管理系统

提供插件清单、依赖解析、版本管理等功能。
"""

from .manifest import PluginManifest, ManifestValidator
from .resolver import DependencyResolver, DependencyError
from .registry import PluginRegistry

__all__ = [
    "PluginManifest",
    "ManifestValidator", 
    "DependencyResolver",
    "DependencyError",
    "PluginRegistry",
]