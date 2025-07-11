# -*- coding: utf-8 -*-
"""
依赖解析引擎测试
"""

import pytest
from unittest.mock import Mock, MagicMock
import networkx as nx

from src.simtradelab.plugins.dependency.resolver import (
    DependencyResolver,
    DependencyError,
    DependencyConflictError,
    CircularDependencyError,
    MissingDependencyError,
    VersionConflictError
)
from src.simtradelab.plugins.dependency.manifest import PluginManifest, PluginCategory, SecurityLevel


class TestDependencyResolver:
    """测试依赖解析引擎"""
    
    @pytest.fixture
    def mock_registry(self):
        """模拟插件注册表"""
        registry = Mock()
        registry.get_manifest = Mock()
        registry.has_plugin = Mock()
        return registry
    
    @pytest.fixture
    def resolver(self, mock_registry):
        """创建依赖解析器"""
        return DependencyResolver(mock_registry)
    
    @pytest.fixture
    def sample_manifests(self):
        """示例插件清单"""
        return {
            "base_plugin": PluginManifest(
                name="base_plugin",
                version="1.0.0",
                description="Base plugin",
                author="Test",
                category=PluginCategory.UTILITY,
                dependencies={}
            ),
            "data_plugin": PluginManifest(
                name="data_plugin",
                version="2.1.0",
                description="Data plugin",
                author="Test",
                category=PluginCategory.DATA_SOURCE,
                dependencies={"base_plugin": ">=1.0.0"}
            ),
            "strategy_plugin": PluginManifest(
                name="strategy_plugin",
                version="1.5.0",
                description="Strategy plugin",
                author="Test",
                category=PluginCategory.STRATEGY,
                dependencies={"data_plugin": ">=2.0.0", "base_plugin": ">=1.0.0"}
            ),
            "conflicting_plugin": PluginManifest(
                name="conflicting_plugin",
                version="1.0.0",
                description="Conflicting plugin",
                author="Test",
                category=PluginCategory.UTILITY,
                conflicts=["data_plugin"]
            ),
            "service_provider1": PluginManifest(
                name="service_provider1",
                version="1.0.0",
                description="Service provider 1",
                author="Test",
                category=PluginCategory.UTILITY,
                provides=["data_service"]
            ),
            "service_provider2": PluginManifest(
                name="service_provider2",
                version="1.0.0",
                description="Service provider 2",
                author="Test",
                category=PluginCategory.UTILITY,
                provides=["data_service"]  # 相同服务，会冲突
            )
        }
    
    def test_resolve_dependencies_simple(self, resolver, mock_registry, sample_manifests):
        """测试简单依赖解析"""
        # 设置注册表返回值
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 解析单个插件（无依赖）
        result = resolver.resolve_dependencies(["base_plugin"])
        assert result == ["base_plugin"]
        
        # 解析有依赖的插件
        result = resolver.resolve_dependencies(["data_plugin"])
        assert "base_plugin" in result
        assert "data_plugin" in result
        assert result.index("base_plugin") < result.index("data_plugin")  # 依赖顺序
    
    def test_resolve_dependencies_complex(self, resolver, mock_registry, sample_manifests):
        """测试复杂依赖解析"""
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 解析复杂依赖链
        result = resolver.resolve_dependencies(["strategy_plugin"])
        
        # 验证所有依赖都包含在内
        assert "base_plugin" in result
        assert "data_plugin" in result
        assert "strategy_plugin" in result
        
        # 验证依赖顺序
        assert result.index("base_plugin") < result.index("data_plugin")
        assert result.index("data_plugin") < result.index("strategy_plugin")
    
    def test_resolve_dependencies_multiple_targets(self, resolver, mock_registry, sample_manifests):
        """测试多目标插件解析"""
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 解析多个目标插件
        result = resolver.resolve_dependencies(["data_plugin", "strategy_plugin"])
        
        # 验证所有插件和依赖都包含
        expected_plugins = ["base_plugin", "data_plugin", "strategy_plugin"]
        for plugin in expected_plugins:
            assert plugin in result
        
        # 验证依赖顺序
        assert result.index("base_plugin") < result.index("data_plugin")
        assert result.index("data_plugin") < result.index("strategy_plugin")
    
    def test_missing_dependency_error(self, resolver, mock_registry, sample_manifests):
        """测试缺失依赖错误"""
        # 设置某个插件不存在
        def has_plugin_side_effect(name):
            return name != "missing_plugin"
        
        def get_manifest_side_effect(name):
            if name == "missing_plugin":
                return None
            return sample_manifests.get(name)
        
        mock_registry.has_plugin.side_effect = has_plugin_side_effect
        mock_registry.get_manifest.side_effect = get_manifest_side_effect
        
        # 创建依赖缺失插件的清单
        dependent_plugin = PluginManifest(
            name="dependent_plugin",
            version="1.0.0",
            description="Dependent plugin",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"missing_plugin": ">=1.0.0"}
        )
        
        sample_manifests["dependent_plugin"] = dependent_plugin
        
        with pytest.raises(MissingDependencyError, match="插件不存在"):
            resolver.resolve_dependencies(["dependent_plugin"])
    
    def test_version_conflict_error(self, resolver, mock_registry, sample_manifests):
        """测试版本冲突错误"""
        mock_registry.has_plugin.return_value = True
        
        # 创建版本不兼容的插件
        incompatible_plugin = PluginManifest(
            name="incompatible_plugin",
            version="1.0.0",
            description="Incompatible plugin",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"data_plugin": ">=3.0.0"}  # 需要3.0.0+，但只有2.1.0
        )
        
        sample_manifests["incompatible_plugin"] = incompatible_plugin
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        with pytest.raises(VersionConflictError, match="版本冲突"):
            resolver.resolve_dependencies(["incompatible_plugin"])
    
    def test_explicit_conflict_error(self, resolver, mock_registry, sample_manifests):
        """测试显式冲突错误"""
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 尝试同时加载冲突的插件
        with pytest.raises(DependencyConflictError, match="插件冲突"):
            resolver.resolve_dependencies(["data_plugin", "conflicting_plugin"])
    
    def test_service_conflict_error(self, resolver, mock_registry, sample_manifests):
        """测试服务冲突错误"""
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 尝试同时加载提供相同服务的插件
        with pytest.raises(DependencyConflictError, match="服务冲突"):
            resolver.resolve_dependencies(["service_provider1", "service_provider2"])
    
    def test_circular_dependency_error(self, resolver, mock_registry):
        """测试循环依赖错误"""
        # 创建循环依赖的插件
        plugin_a = PluginManifest(
            name="plugin_a",
            version="1.0.0",
            description="Plugin A",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_b": ">=1.0.0"}
        )
        
        plugin_b = PluginManifest(
            name="plugin_b",
            version="1.0.0",
            description="Plugin B",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"plugin_a": ">=1.0.0"}
        )
        
        circular_manifests = {"plugin_a": plugin_a, "plugin_b": plugin_b}
        
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: circular_manifests.get(name)
        
        with pytest.raises(CircularDependencyError, match="检测到循环依赖"):
            resolver.resolve_dependencies(["plugin_a"])
    
    def test_caching(self, resolver, mock_registry, sample_manifests):
        """测试结果缓存"""
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 第一次解析
        result1 = resolver.resolve_dependencies(["data_plugin"])
        
        # 第二次解析相同插件（应使用缓存）
        result2 = resolver.resolve_dependencies(["data_plugin"])
        
        assert result1 == result2
        assert len(resolver._resolution_cache) > 0
    
    def test_clear_cache(self, resolver):
        """测试清除缓存"""
        # 添加一些缓存数据
        resolver._resolution_cache["test"] = ["plugin1", "plugin2"]
        resolver._conflict_cache["test"] = True
        
        # 清除缓存
        resolver.clear_cache()
        
        assert len(resolver._resolution_cache) == 0
        assert len(resolver._conflict_cache) == 0
    
    def test_check_compatibility(self, resolver, sample_manifests):
        """测试兼容性检查"""
        manifests = [
            sample_manifests["base_plugin"],
            sample_manifests["data_plugin"],
            sample_manifests["strategy_plugin"]
        ]
        
        compatibility_report = resolver.check_compatibility(manifests)
        
        # 检查报告结构
        assert "base_plugin" in compatibility_report
        assert "data_plugin" in compatibility_report
        assert "strategy_plugin" in compatibility_report
        
        # 基础插件应该没有错误（无依赖）
        assert len(compatibility_report["base_plugin"]) == 0
        
        # 数据插件应该没有错误（依赖满足）
        assert len(compatibility_report["data_plugin"]) == 0
        
        # 策略插件应该没有错误（依赖满足）
        assert len(compatibility_report["strategy_plugin"]) == 0
    
    def test_check_compatibility_with_conflicts(self, resolver, sample_manifests):
        """测试有冲突的兼容性检查"""
        manifests = [
            sample_manifests["data_plugin"],
            sample_manifests["conflicting_plugin"]
        ]
        
        compatibility_report = resolver.check_compatibility(manifests)
        
        # 应该检测到冲突
        assert len(compatibility_report["conflicting_plugin"]) > 0
        assert any("冲突" in error for error in compatibility_report["conflicting_plugin"])
    
    def test_get_dependency_tree(self, resolver, mock_registry, sample_manifests):
        """测试获取依赖树"""
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 获取策略插件的依赖树
        tree = resolver.get_dependency_tree("strategy_plugin")
        
        assert tree["name"] == "strategy_plugin"
        assert tree["version"] == "1.5.0"
        assert len(tree["children"]) == 2  # data_plugin 和 base_plugin
        
        # 检查子依赖
        child_names = [child["name"] for child in tree["children"]]
        assert "data_plugin" in child_names
        assert "base_plugin" in child_names
    
    def test_get_dependency_tree_max_depth(self, resolver, mock_registry, sample_manifests):
        """测试依赖树最大深度限制"""
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        # 设置最大深度为1
        tree = resolver.get_dependency_tree("strategy_plugin", max_depth=1)
        
        assert tree["name"] == "strategy_plugin"
        assert len(tree["children"]) == 2
        
        # 检查子节点是否被截断
        for child in tree["children"]:
            if "children" in child:
                assert "truncated" in child
    
    def test_find_update_path(self, resolver, mock_registry, sample_manifests):
        """测试查找更新路径"""
        mock_registry.has_plugin.return_value = True
        mock_registry.get_manifest.side_effect = lambda name: sample_manifests.get(name)
        
        current_plugins = ["base_plugin", "data_plugin"]
        target_plugins = ["base_plugin", "strategy_plugin"]
        
        update_plan = resolver.find_update_path(current_plugins, target_plugins)
        
        assert "data_plugin" in update_plan["remove"]
        assert "strategy_plugin" in update_plan["add"]
        assert "base_plugin" in update_plan["keep"]
        assert len(update_plan["sequence"]) > 0
    
    def test_get_statistics(self, resolver):
        """测试获取统计信息"""
        # 添加一些缓存和图数据
        resolver._resolution_cache["test1"] = ["plugin1"]
        resolver._resolution_cache["test2"] = ["plugin2"]
        resolver.dependency_graph.add_node("plugin1")
        resolver.dependency_graph.add_node("plugin2")
        resolver.dependency_graph.add_edge("plugin1", "plugin2")
        
        stats = resolver.get_statistics()
        
        assert stats["cached_resolutions"] == 2
        assert stats["graph_nodes"] == 2
        assert stats["graph_edges"] == 1
    
    def test_no_registry_behavior(self):
        """测试无注册表时的行为"""
        resolver = DependencyResolver(None)
        
        # 无注册表时应该能解析，但只是简单返回目标插件
        result = resolver.resolve_dependencies(["plugin1", "plugin2"])
        assert "plugin1" in result
        assert "plugin2" in result
    
    def test_dependency_tree_without_registry(self):
        """测试无注册表时的依赖树"""
        resolver = DependencyResolver(None)
        
        tree = resolver.get_dependency_tree("test_plugin")
        assert tree["name"] == "test_plugin"
        assert "error" in tree
        assert tree["error"] == "No registry"