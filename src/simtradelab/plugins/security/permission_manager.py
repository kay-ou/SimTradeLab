# -*- coding: utf-8 -*-
"""
SimTradeLab 插件权限管理器

本文件定义了权限管理器，用于控制插件对系统资源的访问。
"""

from enum import Enum
from typing import Dict, Set


class Permission(Enum):
    """
    权限枚举
    """

    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    NETWORK_ACCESS = "network.access"
    SYSTEM_CALL = "system.call"


class PermissionManager:
    """
    权限管理器
    """

    def __init__(self):
        self._permissions: Dict[str, Set[Permission]] = {}

    def grant(self, plugin_name: str, permission: Permission):
        """
        授予插件一项权限。

        Args:
            plugin_name: 插件名称。
            permission: 要授予的权限。
        """
        if plugin_name not in self._permissions:
            self._permissions[plugin_name] = set()
        self._permissions[plugin_name].add(permission)

    def revoke(self, plugin_name: str, permission: Permission):
        """
        撤销插件的一项权限。

        Args:
            plugin_name: 插件名称。
            permission: 要撤销的权限。
        """
        if plugin_name in self._permissions:
            self._permissions[plugin_name].discard(permission)

    def has_permission(self, plugin_name: str, permission: Permission) -> bool:
        """
        检查插件是否拥有某项权限。

        Args:
            plugin_name: 插件名称。
            permission: 要检查的权限。

        Returns:
            如果插件拥有该权限，则返回 True，否则返回 False。
        """
        return permission in self._permissions.get(plugin_name, set())
