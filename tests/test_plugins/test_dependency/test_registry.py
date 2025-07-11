# -*- coding: utf-8 -*-
"""
插件注册表测试
"""

import pytest
import yaml
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from src.simtradelab.plugins.dependency.registry import PluginRegistry
from src.simtradelab.plugins.dependency.manifest import (
    PluginManifest,
    ManifestValidator,
    PluginCategory,
    SecurityLevel
)


class TestPluginRegistry:
    """测试插件注册表"""
    
    @pytest.fixture
    def registry(self):
        """创建插件注册表"""
        return PluginRegistry()
    
    @pytest.fixture
    def sample_manifest(self):
        """示例插件清单"""
        return PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY,
            tags=["test", "utility"],
            dependencies={"base_plugin": ">=1.0.0"},
            provides=["test_service"],
            requires=["event_bus"]
        )
    
    def test_register_plugin_success(self, registry, sample_manifest):
        """测试成功注册插件"""
        plugin_path = Path("/test/path")
        
        result = registry.register_plugin(sample_manifest, plugin_path)
        
        assert result is True
        assert registry.has_plugin("test_plugin")
        assert registry.get_manifest("test_plugin") == sample_manifest
        assert registry.get_plugin_path("test_plugin") == plugin_path
    
    def test_register_plugin_validation_failure(self, registry):
        """测试注册插件验证失败"""
        # 创建无效清单
        invalid_manifest = PluginManifest(
            name="invalid_plugin",
            version="1.0.0",
            description="",  # 空描述
            author="Test",
            category=PluginCategory.UTILITY
        )
        
        # 手动设置无效值
        invalid_manifest.description = ""
        
        result = registry.register_plugin(invalid_manifest)
        
        assert result is False
        assert not registry.has_plugin("invalid_plugin")
    
    def test_register_plugin_replacement(self, registry, sample_manifest):
        """测试插件替换"""
        # 注册第一个版本
        result1 = registry.register_plugin(sample_manifest)
        assert result1 is True
        
        # 创建新版本
        new_manifest = PluginManifest(
            name="test_plugin",  # 同名
            version="2.0.0",     # 新版本
            description="Updated test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        # 注册新版本（应该替换旧版本）
        result2 = registry.register_plugin(new_manifest)
        assert result2 is True
        
        # 验证新版本已注册
        registered_manifest = registry.get_manifest("test_plugin")
        assert registered_manifest.version == "2.0.0"
    
    def test_unregister_plugin_success(self, registry, sample_manifest):
        """测试成功注销插件"""
        # 先注册插件
        registry.register_plugin(sample_manifest)
        assert registry.has_plugin("test_plugin")
        
        # 注销插件
        result = registry.unregister_plugin("test_plugin")
        
        assert result is True
        assert not registry.has_plugin("test_plugin")
        assert registry.get_manifest("test_plugin") is None
    
    def test_unregister_nonexistent_plugin(self, registry):
        """测试注销不存在的插件"""
        result = registry.unregister_plugin("nonexistent_plugin")
        assert result is False
    
    def test_list_plugins_all(self, registry):
        """测试列出所有插件"""
        # 注册多个插件
        manifests = [
            PluginManifest(
                name="plugin1",
                version="1.0.0",
                description="Plugin 1",
                author="Test",
                category=PluginCategory.UTILITY
            ),
            PluginManifest(
                name="plugin2",
                version="1.0.0",
                description="Plugin 2",
                author="Test",
                category=PluginCategory.DATA_SOURCE
            )
        ]
        
        for manifest in manifests:
            registry.register_plugin(manifest)
        
        plugins = registry.list_plugins()
        assert "plugin1" in plugins
        assert "plugin2" in plugins
        assert len(plugins) == 2
    
    def test_list_plugins_by_category(self, registry):
        """测试按类别列出插件"""
        # 注册不同类别的插件
        utility_plugin = PluginManifest(
            name="utility_plugin",
            version="1.0.0",
            description="Utility plugin",
            author="Test",
            category=PluginCategory.UTILITY
        )
        
        data_plugin = PluginManifest(
            name="data_plugin",
            version="1.0.0",
            description="Data plugin",
            author="Test",
            category=PluginCategory.DATA_SOURCE
        )
        
        registry.register_plugin(utility_plugin)
        registry.register_plugin(data_plugin)
        
        # 按类别筛选
        utility_plugins = registry.list_plugins(PluginCategory.UTILITY)
        data_plugins = registry.list_plugins(PluginCategory.DATA_SOURCE)
        
        assert "utility_plugin" in utility_plugins
        assert "utility_plugin" not in data_plugins
        assert "data_plugin" in data_plugins
        assert "data_plugin" not in utility_plugins
    
    def test_search_plugins_by_keyword(self, registry):
        """测试按关键词搜索插件"""
        # 注册测试插件
        manifests = [
            PluginManifest(
                name="data_source_plugin",
                version="1.0.0",
                description="Provides market data",
                author="Test",
                category=PluginCategory.DATA_SOURCE,
                keywords=["market", "data", "source"]
            ),
            PluginManifest(
                name="strategy_plugin",
                version="1.0.0",
                description="Trading strategy implementation",
                author="Test",
                category=PluginCategory.STRATEGY,
                keywords=["trading", "strategy"]
            )
        ]
        
        for manifest in manifests:
            registry.register_plugin(manifest)
        
        # 搜索包含"data"的插件
        results = registry.search_plugins(keyword="data")
        result_names = [m.name for m in results]
        
        assert "data_source_plugin" in result_names
        assert "strategy_plugin" not in result_names
    
    def test_search_plugins_by_author(self, registry):
        """测试按作者搜索插件"""
        manifests = [
            PluginManifest(
                name="plugin_by_alice",
                version="1.0.0",
                description="Plugin by Alice",
                author="Alice",
                category=PluginCategory.UTILITY
            ),
            PluginManifest(
                name="plugin_by_bob",
                version="1.0.0",
                description="Plugin by Bob",
                author="Bob",
                category=PluginCategory.UTILITY
            )
        ]
        
        for manifest in manifests:
            registry.register_plugin(manifest)
        
        # 按作者搜索
        results = registry.search_plugins(author="Alice")
        result_names = [m.name for m in results]
        
        assert "plugin_by_alice" in result_names
        assert "plugin_by_bob" not in result_names
    
    def test_search_plugins_by_tag(self, registry):
        """测试按标签搜索插件"""
        manifests = [
            PluginManifest(
                name="real_time_plugin",
                version="1.0.0",
                description="Real-time plugin",
                author="Test",
                category=PluginCategory.DATA_SOURCE,
                tags=["real-time", "streaming"]
            ),
            PluginManifest(
                name="batch_plugin",
                version="1.0.0",
                description="Batch plugin",
                author="Test",
                category=PluginCategory.DATA_SOURCE,
                tags=["batch", "historical"]
            )
        ]
        
        for manifest in manifests:
            registry.register_plugin(manifest)
        
        # 按标签搜索
        results = registry.search_plugins(tag="real-time")
        result_names = [m.name for m in results]
        
        assert "real_time_plugin" in result_names
        assert "batch_plugin" not in result_names
    
    def test_search_plugins_combined_filters(self, registry):
        """测试组合搜索条件"""
        manifest = PluginManifest(
            name="specific_plugin",
            version="1.0.0",
            description="Specific data plugin",
            author="Test Author",
            category=PluginCategory.DATA_SOURCE,
            tags=["specific"],
            keywords=["data"]
        )
        
        other_manifest = PluginManifest(
            name="other_plugin",
            version="1.0.0",
            description="Other plugin",
            author="Other Author",
            category=PluginCategory.UTILITY,
            tags=["other"]
        )
        
        registry.register_plugin(manifest)
        registry.register_plugin(other_manifest)
        
        # 组合搜索：类别 + 作者 + 标签
        results = registry.search_plugins(
            category=PluginCategory.DATA_SOURCE,
            author="Test Author",
            tag="specific"
        )
        
        assert len(results) == 1
        assert results[0].name == "specific_plugin"
    
    def test_get_plugins_by_service(self, registry):
        """测试获取提供特定服务的插件"""
        manifests = [
            PluginManifest(
                name="data_provider1",
                version="1.0.0",
                description="Data provider 1",
                author="Test",
                category=PluginCategory.DATA_SOURCE,
                provides=["market_data", "real_time_data"]
            ),
            PluginManifest(
                name="data_provider2",
                version="1.0.0",
                description="Data provider 2",
                author="Test",
                category=PluginCategory.DATA_SOURCE,
                provides=["market_data", "historical_data"]
            ),
            PluginManifest(
                name="other_plugin",
                version="1.0.0",
                description="Other plugin",
                author="Test",
                category=PluginCategory.UTILITY,
                provides=["utility_service"]
            )
        ]
        
        for manifest in manifests:
            registry.register_plugin(manifest)
        
        # 获取提供market_data服务的插件
        providers = registry.get_plugins_by_service("market_data")
        
        assert "data_provider1" in providers
        assert "data_provider2" in providers
        assert "other_plugin" not in providers
    
    def test_get_plugin_dependencies(self, registry, sample_manifest):
        """测试获取插件依赖"""
        registry.register_plugin(sample_manifest)
        
        dependencies = registry.get_plugin_dependencies("test_plugin")
        
        assert dependencies == {"base_plugin": ">=1.0.0"}
    
    def test_get_plugin_dependents(self, registry):
        """测试获取插件的依赖者"""
        # 创建依赖关系链
        base_manifest = PluginManifest(
            name="base_plugin",
            version="1.0.0",
            description="Base plugin",
            author="Test",
            category=PluginCategory.UTILITY
        )
        
        dependent1 = PluginManifest(
            name="dependent1",
            version="1.0.0",
            description="Dependent 1",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"base_plugin": ">=1.0.0"}
        )
        
        dependent2 = PluginManifest(
            name="dependent2",
            version="1.0.0",
            description="Dependent 2",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"base_plugin": ">=1.0.0"}
        )
        
        independent = PluginManifest(
            name="independent",
            version="1.0.0",
            description="Independent plugin",
            author="Test",
            category=PluginCategory.UTILITY
        )
        
        for manifest in [base_manifest, dependent1, dependent2, independent]:
            registry.register_plugin(manifest)
        
        # 获取base_plugin的依赖者
        dependents = registry.get_plugin_dependents("base_plugin")
        
        assert "dependent1" in dependents
        assert "dependent2" in dependents
        assert "independent" not in dependents
    
    def test_get_statistics(self, registry):
        """测试获取统计信息"""
        # 注册多个插件
        manifests = [
            PluginManifest(
                name="plugin1",
                version="1.0.0",
                description="Plugin 1",
                author="Alice",
                category=PluginCategory.UTILITY,
                tags=["tag1", "common"]
            ),
            PluginManifest(
                name="plugin2",
                version="1.0.0",
                description="Plugin 2",
                author="Bob",
                category=PluginCategory.DATA_SOURCE,
                tags=["tag2", "common"],
                provides=["service1"]
            ),
            PluginManifest(
                name="plugin3",
                version="1.0.0",
                description="Plugin 3",
                author="Alice",
                category=PluginCategory.UTILITY,
                tags=["tag1"],
                provides=["service2"]
            )
        ]
        
        for manifest in manifests:
            registry.register_plugin(manifest)
        
        stats = registry.get_statistics()
        
        assert stats["total_plugins"] == 3
        assert stats["by_category"]["utility"] == 2
        assert stats["by_category"]["data_source"] == 1
        assert stats["by_author"]["Alice"] == 2
        assert stats["by_author"]["Bob"] == 1
        assert stats["services_provided"] == 2
        
        # 检查标签统计
        top_tags = dict(stats["top_tags"])
        assert top_tags["common"] == 2
        assert top_tags["tag1"] == 2
    
    def test_validate_registry(self, registry):
        """测试验证注册表"""
        # 注册有效插件
        valid_manifest = PluginManifest(
            name="valid_plugin",
            version="1.0.0",
            description="Valid plugin",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"existing_plugin": ">=1.0.0"}
        )
        
        existing_manifest = PluginManifest(
            name="existing_plugin",
            version="1.0.0",
            description="Existing plugin",
            author="Test",
            category=PluginCategory.UTILITY
        )
        
        # 注册有冲突的插件
        conflicted_manifest = PluginManifest(
            name="conflicted_plugin",
            version="1.0.0",
            description="Conflicted plugin",
            author="Test",
            category=PluginCategory.UTILITY,
            conflicts=["existing_plugin"]
        )
        
        registry.register_plugin(valid_manifest)
        registry.register_plugin(existing_manifest)
        registry.register_plugin(conflicted_manifest)
        
        validation_report = registry.validate_registry()
        
        # valid_plugin应该没有错误（依赖存在）
        assert "valid_plugin" not in validation_report or len(validation_report["valid_plugin"]) == 0
        
        # conflicted_plugin应该有冲突错误
        assert "conflicted_plugin" in validation_report
        assert any("冲突插件" in error for error in validation_report["conflicted_plugin"])
    
    def test_register_from_directory(self, registry):
        """测试从目录注册插件"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建插件目录结构
            plugin1_dir = temp_path / "plugin1"
            plugin2_dir = temp_path / "plugin2"
            plugin1_dir.mkdir()
            plugin2_dir.mkdir()
            
            # 创建插件清单文件
            manifest1 = {
                "name": "directory_plugin1",
                "version": "1.0.0",
                "description": "Directory plugin 1",
                "author": "Test",
                "category": "utility"
            }
            
            manifest2 = {
                "name": "directory_plugin2",
                "version": "1.0.0",
                "description": "Directory plugin 2",
                "author": "Test",
                "category": "data_source"
            }
            
            # 保存YAML格式清单
            with open(plugin1_dir / "plugin_manifest.yaml", 'w') as f:
                yaml.dump(manifest1, f)
            
            # 保存JSON格式清单
            with open(plugin2_dir / "plugin_manifest.json", 'w') as f:
                json.dump(manifest2, f)
            
            # 从目录注册插件
            count = registry.register_from_directory(temp_path)
            
            assert count == 2
            assert registry.has_plugin("directory_plugin1")
            assert registry.has_plugin("directory_plugin2")
    
    def test_register_from_nonexistent_directory(self, registry):
        """测试从不存在的目录注册插件"""
        nonexistent_path = Path("/nonexistent/directory")
        count = registry.register_from_directory(nonexistent_path)
        assert count == 0
    
    def test_export_registry_yaml(self, registry, sample_manifest):
        """测试导出注册表为YAML"""
        registry.register_plugin(sample_manifest)
        
        with TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "registry_export.yaml"
            
            # Mock datetime to ensure consistent output
            with patch.object(registry, 'get_current_time') as mock_time:
                mock_time.return_value = "2024-01-01T00:00:00"
                result = registry.export_registry(export_path, "yaml")
            
            assert result is True
            assert export_path.exists()
            
            # 验证导出内容
            with open(export_path, 'r') as f:
                exported_data = yaml.safe_load(f)
            
            assert "registry_version" in exported_data
            assert "plugins" in exported_data
            assert "test_plugin" in exported_data["plugins"]
    
    def test_export_registry_json(self, registry, sample_manifest):
        """测试导出注册表为JSON"""
        registry.register_plugin(sample_manifest)
        
        with TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "registry_export.json"
            
            with patch.object(registry, 'get_current_time') as mock_time:
                mock_time.return_value = "2024-01-01T00:00:00"
                result = registry.export_registry(export_path, "json")
            
            assert result is True
            assert export_path.exists()
            
            # 验证导出内容
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            assert "registry_version" in exported_data
            assert "plugins" in exported_data
            assert "test_plugin" in exported_data["plugins"]
    
    def test_export_registry_unsupported_format(self, registry, sample_manifest):
        """测试导出不支持的格式"""
        registry.register_plugin(sample_manifest)
        
        with TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "registry_export.txt"
            result = registry.export_registry(export_path, "txt")
            
            assert result is False
    
    def test_clear_registry(self, registry, sample_manifest):
        """测试清空注册表"""
        # 注册插件
        registry.register_plugin(sample_manifest)
        assert registry.has_plugin("test_plugin")
        
        # 清空注册表
        registry.clear()
        
        # 验证已清空
        assert not registry.has_plugin("test_plugin")
        assert len(registry.list_plugins()) == 0
        assert len(registry.get_statistics()["by_category"]) == 0
    
    def test_index_management(self, registry):
        """测试索引管理"""
        manifest = PluginManifest(
            name="index_test_plugin",
            version="1.0.0",
            description="Index test plugin",
            author="Index Author",
            category=PluginCategory.DATA_SOURCE,
            tags=["index", "test"],
            provides=["index_service"]
        )
        
        # 注册插件
        registry.register_plugin(manifest)
        
        # 验证各索引已更新
        assert "index_test_plugin" in registry._by_category[PluginCategory.DATA_SOURCE]
        assert "index_test_plugin" in registry._by_author["Index Author"]
        assert "index_test_plugin" in registry._by_tag["index"]
        assert "index_test_plugin" in registry._by_tag["test"]
        assert "index_test_plugin" in registry._providers["index_service"]
        
        # 注销插件
        registry.unregister_plugin("index_test_plugin")
        
        # 验证索引已清理
        assert "index_test_plugin" not in registry._by_category.get(PluginCategory.DATA_SOURCE, set())
        assert "index_test_plugin" not in registry._by_author.get("Index Author", set())
        assert "index_test_plugin" not in registry._by_tag.get("index", set())
        assert "index_test_plugin" not in registry._providers.get("index_service", set())