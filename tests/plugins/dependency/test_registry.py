# -*- coding: utf-8 -*-
"""
插件注册表测试
"""

import pytest
from pathlib import Path
import tempfile
from typing import Generator

from simtradelab.plugins.dependency.manifest import PluginManifest, PluginCategory
from simtradelab.plugins.dependency.registry import PluginRegistry


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建一个临时目录。"""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def basic_manifest() -> PluginManifest:
    """返回一个基本的插件清单实例。"""
    return PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="A basic test plugin.",
        author="Test Author",
        category=PluginCategory.UTILITY,
    )


class TestPluginRegistry:
    """测试 PluginRegistry"""

    def test_register_plugin_success(self, basic_manifest: PluginManifest):
        """测试成功注册一个插件"""
        registry = PluginRegistry()
        assert registry.register_plugin(basic_manifest)
        assert registry.has_plugin("test_plugin")
        retrieved_manifest = registry.get_manifest("test_plugin")
        assert retrieved_manifest is not None
        assert retrieved_manifest.name == "test_plugin"
        assert "test_plugin" in registry.list_plugins()
        assert "test_plugin" in registry.list_plugins(category=PluginCategory.UTILITY)

    def test_register_plugin_with_invalid_manifest(self):
        """测试注册一个无效的插件清单"""
        registry = PluginRegistry()
        invalid_manifest = PluginManifest(
            name="invalid",
            version="1.0.0",
            description="",  # 描述为空，无效
            author="Test",
            category=PluginCategory.UTILITY,
        )
        assert not registry.register_plugin(invalid_manifest)
        assert not registry.has_plugin("invalid")

    def test_unregister_plugin(self, basic_manifest: PluginManifest):
        """测试注销插件"""
        registry = PluginRegistry()
        registry.register_plugin(basic_manifest)
        assert registry.has_plugin("test_plugin")

        assert registry.unregister_plugin("test_plugin")
        assert not registry.has_plugin("test_plugin")
        assert not registry.unregister_plugin("non_existent_plugin") # 注销不存在的插件

    def test_register_from_directory(self, temp_dir: Path):
        """测试从目录注册插件"""
        registry = PluginRegistry()

        # 创建一个有效的插件目录
        plugin1_dir = temp_dir / "plugin1"
        plugin1_dir.mkdir()
        manifest1_path = plugin1_dir / "plugin_manifest.yaml"
        with open(manifest1_path, "w") as f:
            f.write(
                "name: plugin1\n"
                "version: 1.0.0\n"
                "description: Plugin one.\n"
                "author: Author One\n"
                "category: data_source\n"
            )

        # 创建另一个插件目录
        plugin2_dir = temp_dir / "plugin2"
        plugin2_dir.mkdir()
        manifest2_path = plugin2_dir / "plugin_manifest.json"
        with open(manifest2_path, "w") as f:
            import json
            json.dump({
                "name": "plugin2",
                "version": "2.0.0",
                "description": "Plugin two.",
                "author": "Author Two",
                "category": "strategy",
            }, f)
        
        # 创建一个无效的插件目录
        invalid_dir = temp_dir / "invalid_plugin"
        invalid_dir.mkdir()
        invalid_manifest_path = invalid_dir / "plugin_manifest.yaml"
        with open(invalid_manifest_path, "w") as f:
            f.write("name: invalid\nversion: 1.0.0\n") # 无效清单

        count = registry.register_from_directory(temp_dir)
        assert count == 2
        assert registry.has_plugin("plugin1")
        assert registry.has_plugin("plugin2")
        assert not registry.has_plugin("invalid")
        assert registry.get_plugin_path("plugin1") == plugin1_dir

    def test_search_plugins(self, basic_manifest: PluginManifest):
        """测试搜索插件功能"""
        registry = PluginRegistry()
        registry.register_plugin(basic_manifest)

        # 添加另一个插件用于搜索
        manifest2 = PluginManifest(
            name="another_plugin",
            version="1.0.0",
            description="Another utility plugin.",
            author="Another Author",
            category=PluginCategory.UTILITY,
            tags=["utility", "extra"]
        )
        registry.register_plugin(manifest2)

        # 搜索
        results = registry.search_plugins(keyword="basic")
        assert len(results) == 1
        assert results[0].name == "test_plugin"

        results = registry.search_plugins(category=PluginCategory.UTILITY)
        assert len(results) == 2

        results = registry.search_plugins(author="Another Author")
        assert len(results) == 1
        assert results[0].name == "another_plugin"

        results = registry.search_plugins(tag="extra")
        assert len(results) == 1
        assert results[0].name == "another_plugin"

        results = registry.search_plugins(keyword="plugin", category=PluginCategory.UTILITY)
        assert len(results) == 2


    def test_get_dependencies_and_dependents(self, basic_manifest: PluginManifest):
        """测试获取插件的依赖和被依赖关系"""
        registry = PluginRegistry()

        # 创建一个依赖于 basic_manifest 的插件
        dependent_manifest = PluginManifest(
            name="dependent_plugin",
            version="1.0.0",
            description="A dependent plugin.",
            author="Test Author",
            category=PluginCategory.UTILITY,
            dependencies={"test_plugin": ">=1.0.0"},
        )
        
        registry.register_plugin(basic_manifest)
        registry.register_plugin(dependent_manifest)

        # 测试 get_plugin_dependencies
        deps = registry.get_plugin_dependencies("dependent_plugin")
        assert deps == {"test_plugin": ">=1.0.0"}
        
        # 测试 get_plugin_dependents
        dependents = registry.get_plugin_dependents("test_plugin")
        assert dependents == ["dependent_plugin"]

        # 测试没有依赖和被依赖的情况
        assert registry.get_plugin_dependencies("test_plugin") == {}
        assert registry.get_plugin_dependents("dependent_plugin") == []

    def test_clear_registry(self, basic_manifest: PluginManifest):
        """测试清空注册表"""
        registry = PluginRegistry()
        registry.register_plugin(basic_manifest)
        assert registry.has_plugin("test_plugin")

        registry.clear()
        assert not registry.has_plugin("test_plugin")
        assert registry.list_plugins() == []


    def test_get_statistics(self, basic_manifest: PluginManifest):
        """测试获取注册表统计信息"""
        registry = PluginRegistry()
        registry.register_plugin(basic_manifest)
        
        stats = registry.get_statistics()
        assert stats["total_plugins"] == 1
        assert stats["by_category"]["utility"] == 1
        assert stats["by_author"]["Test Author"] == 1

    def test_validate_registry(self, basic_manifest: PluginManifest):
        """测试验证注册表"""
        registry = PluginRegistry()
        
        # 注册一个依赖不存在插件的清单
        dependent_manifest = PluginManifest(
            name="dependent_plugin",
            version="1.0.0",
            description="A dependent plugin.",
            author="Test Author",
            category=PluginCategory.UTILITY,
            dependencies={"non_existent_plugin": ">=1.0.0"},
        )
        registry.register_plugin(dependent_manifest)
        
        report = registry.validate_registry()
        assert "dependent_plugin" in report
        assert "依赖插件不存在: non_existent_plugin" in report["dependent_plugin"]

    def test_export_registry(self, temp_dir: Path, basic_manifest: PluginManifest):
        """测试导出注册表"""
        registry = PluginRegistry()
        registry.register_plugin(basic_manifest)

        # 测试YAML导出
        yaml_path = temp_dir / "registry.yaml"
        assert registry.export_registry(yaml_path, format="yaml")
        assert yaml_path.exists()

        # 测试JSON导出
        json_path = temp_dir / "registry.json"
        assert registry.export_registry(json_path, format="json")
        assert json_path.exists()
