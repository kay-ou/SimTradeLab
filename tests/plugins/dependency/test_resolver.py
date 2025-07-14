# -*- coding: utf-8 -*-
"""
插件依赖解析器测试
"""

import pytest

from simtradelab.plugins.dependency.manifest import PluginCategory, PluginManifest
from simtradelab.plugins.dependency.registry import PluginRegistry
from simtradelab.plugins.dependency.resolver import (
    CircularDependencyError,
    DependencyConflictError,
    DependencyResolver,
    MissingDependencyError,
    VersionConflictError,
)


@pytest.fixture
def registry() -> PluginRegistry:
    """返回一个空的插件注册表实例。"""
    return PluginRegistry()


class TestDependencyResolver:
    """测试 DependencyResolver"""

    def test_resolve_simple_dependency(self, registry: PluginRegistry):
        """测试解析简单的依赖关系"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_a": ">=1.0.0"},
        )
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)

        resolver = DependencyResolver(registry)
        load_order = resolver.resolve_dependencies(["plugin_b"])
        assert load_order == ["plugin_a", "plugin_b"]

    def test_resolve_no_dependencies(self, registry: PluginRegistry):
        """测试解析没有依赖的插件"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        registry.register_plugin(plugin_a)
        resolver = DependencyResolver(registry)
        load_order = resolver.resolve_dependencies(["plugin_a"])
        assert load_order == ["plugin_a"]

    def test_circular_dependency(self, registry: PluginRegistry):
        """测试循环依赖"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_b": ">=1.0.0"},
        )
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_a": ">=1.0.0"},
        )
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)
        resolver = DependencyResolver(registry)
        with pytest.raises(CircularDependencyError):
            resolver.resolve_dependencies(["plugin_a", "plugin_b"])

    def test_missing_dependency(self, registry: PluginRegistry):
        """测试缺失依赖"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"non_existent": ">=1.0.0"},
        )
        registry.register_plugin(plugin_a)
        resolver = DependencyResolver(registry)
        with pytest.raises(MissingDependencyError):
            resolver.resolve_dependencies(["plugin_a"])

    def test_version_conflict(self, registry: PluginRegistry):
        """测试版本冲突"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_a": ">=2.0.0"},
        )
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)
        resolver = DependencyResolver(registry)
        with pytest.raises(VersionConflictError):
            resolver.resolve_dependencies(["plugin_b"])

    def test_dependency_conflict(self, registry: PluginRegistry):
        """测试插件冲突"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            conflicts=["plugin_b"],
        )
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)
        resolver = DependencyResolver(registry)
        with pytest.raises(DependencyConflictError):
            resolver.resolve_dependencies(["plugin_a", "plugin_b"])

    def test_check_compatibility(self, registry: PluginRegistry):
        """测试检查插件兼容性"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            conflicts=["plugin_b"],
        )
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        plugin_c = PluginManifest(
            name="plugin_c",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_a": ">=2.0.0"},
        )

        resolver = DependencyResolver()
        report = resolver.check_compatibility([plugin_a, plugin_b, plugin_c])

        assert "与插件 plugin_b 存在冲突" in report["plugin_a"]
        assert "与插件 plugin_a 存在冲突" in report["plugin_b"]
        assert "依赖版本不匹配: 需要 plugin_a >=2.0.0, 但找到 1.0.0" in report["plugin_c"]

    def test_get_dependency_tree(self, registry: PluginRegistry):
        """测试获取依赖树"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_a": ">=1.0.0"},
        )
        plugin_c = PluginManifest(
            name="plugin_c",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_b": ">=1.0.0"},
        )
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)
        registry.register_plugin(plugin_c)

        resolver = DependencyResolver(registry)
        tree = resolver.get_dependency_tree("plugin_c")

        assert tree["name"] == "plugin_c"
        assert len(tree["children"]) == 1

        child_b = tree["children"][0]
        assert child_b["name"] == "plugin_b"
        assert len(child_b["children"]) == 1

        child_a = child_b["children"][0]
        assert child_a["name"] == "plugin_a"
        assert len(child_a["children"]) == 0

    def test_find_update_path(self, registry: PluginRegistry):
        """测试查找更新路径"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        registry.register_plugin(plugin_a)
        registry.register_plugin(plugin_b)

        resolver = DependencyResolver(registry)

        current_plugins = ["plugin_a"]
        target_plugins = ["plugin_b"]

        plan = resolver.find_update_path(current_plugins, target_plugins)

        assert plan["add"] == ["plugin_b"]
        assert plan["remove"] == ["plugin_a"]
        assert plan["keep"] == []

    def test_get_statistics_and_clear_cache(self, registry: PluginRegistry):
        """测试获取统计信息和清除缓存"""
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        registry.register_plugin(plugin_a)

        resolver = DependencyResolver(registry)
        resolver.resolve_dependencies(["plugin_a"])

        stats = resolver.get_statistics()
        assert stats["cached_resolutions"] == 1

        resolver.clear_cache()
        stats = resolver.get_statistics()
        assert stats["cached_resolutions"] == 0
