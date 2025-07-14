# -*- coding: utf-8 -*-
"""
PermissionManager 的单元测试
"""
import pytest

from simtradelab.plugins.security.permission_manager import (
    Permission,
    PermissionManager,
)


@pytest.fixture
def manager():
    """提供一个 PermissionManager 实例"""
    return PermissionManager()


def test_grant_and_has_permission(manager: PermissionManager):
    """
    测试：授予权限后，应能正确检查到该权限。
    """
    assert not manager.has_permission("test_plugin", Permission.FILE_READ)
    manager.grant("test_plugin", Permission.FILE_READ)
    assert manager.has_permission("test_plugin", Permission.FILE_READ)


def test_revoke_permission(manager: PermissionManager):
    """
    测试：撤销权限后，应检查不到该权限。
    """
    manager.grant("test_plugin", Permission.FILE_WRITE)
    assert manager.has_permission("test_plugin", Permission.FILE_WRITE)
    manager.revoke("test_plugin", Permission.FILE_WRITE)
    assert not manager.has_permission("test_plugin", Permission.FILE_WRITE)


def test_multiple_permissions(manager: PermissionManager):
    """
    测试：可以正确处理多个插件和多个权限。
    """
    manager.grant("plugin1", Permission.FILE_READ)
    manager.grant("plugin1", Permission.NETWORK_ACCESS)
    manager.grant("plugin2", Permission.FILE_WRITE)

    assert manager.has_permission("plugin1", Permission.FILE_READ)
    assert manager.has_permission("plugin1", Permission.NETWORK_ACCESS)
    assert not manager.has_permission("plugin1", Permission.FILE_WRITE)

    assert not manager.has_permission("plugin2", Permission.FILE_READ)
    assert manager.has_permission("plugin2", Permission.FILE_WRITE)


def test_revoke_non_existent_permission(manager: PermissionManager):
    """
    测试：撤销一个不存在的权限不应导致错误。
    """
    manager.revoke("test_plugin", Permission.SYSTEM_CALL)
    assert not manager.has_permission("test_plugin", Permission.SYSTEM_CALL)
