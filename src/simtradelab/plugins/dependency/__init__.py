# -*- coding: utf-8 -*-
"""
插件依赖管理系统

提供插件清单、依赖解析、版本管理等功能。
"""

from .manifest import ManifestValidator, PluginManifest
from .registry import PluginRegistry
from .resolver import DependencyError, DependencyResolver

__all__ = [
    "PluginManifest",
    "ManifestValidator",
    "DependencyResolver",
    "DependencyError",
    "PluginRegistry",
]
