# -*- coding: utf-8 -*-
"""
插件清单模型测试
"""

import pytest
import yaml
import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from pydantic import ValidationError

from src.simtradelab.plugins.dependency.manifest import (
    PluginManifest,
    ManifestValidator,
    PluginCategory,
    SecurityLevel
)


class TestPluginManifest:
    """测试插件清单模型"""
    
    def test_minimal_manifest(self):
        """测试最小清单创建"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        assert manifest.name == "test_plugin"
        assert manifest.version == "1.0.0"
        assert manifest.category == PluginCategory.UTILITY
        assert manifest.security_level == SecurityLevel.MEDIUM
        assert manifest.dependencies == {}
        assert manifest.conflicts == []
    
    def test_full_manifest(self):
        """测试完整清单创建"""
        manifest = PluginManifest(
            name="complex_plugin",
            version="2.1.0",
            description="Complex test plugin",
            author="Test Team",
            license="Apache-2.0",
            homepage="https://example.com",
            repository="https://github.com/example/plugin",
            category=PluginCategory.DATA_SOURCE,
            tags=["data", "real-time"],
            keywords=["market", "data", "source"],
            dependencies={"base_plugin": ">=1.0.0,<2.0.0"},
            conflicts=["other_plugin"],
            provides=["data_feed", "market_data"],
            requires=["event_bus", "config_center"],
            python_version=">=3.9",
            platform=["linux"],
            security_level=SecurityLevel.HIGH,
            max_memory_mb=1024,
            max_cpu_percent=75.0,
            max_disk_mb=2048,
            entry_point="main.py"
        )
        
        assert manifest.name == "complex_plugin"
        assert manifest.security_level == SecurityLevel.HIGH
        assert "base_plugin" in manifest.dependencies
        assert "other_plugin" in manifest.conflicts
        assert "data_feed" in manifest.provides
        assert "event_bus" in manifest.requires
    
    def test_name_validation(self):
        """测试名称验证"""
        # 有效名称
        valid_names = ["test_plugin", "data_source_v2", "ai_model"]
        for name in valid_names:
            manifest = PluginManifest(
                name=name,
                version="1.0.0",
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY
            )
            assert manifest.name == name
        
        # 无效名称（太短）
        with pytest.raises(ValidationError):
            PluginManifest(
                name="ab",
                version="1.0.0",
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY
            )
        
        # 无效名称（太长）
        with pytest.raises(ValidationError):
            PluginManifest(
                name="a" * 51,
                version="1.0.0",
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY
            )
        
        # 无效名称（格式错误）
        with pytest.raises(ValidationError):
            PluginManifest(
                name="invalid-name",
                version="1.0.0",
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY
            )
    
    def test_version_validation(self):
        """测试版本验证"""
        # 有效版本
        valid_versions = ["1.0.0", "2.1.3", "1.0.0-alpha.1"]
        for version in valid_versions:
            manifest = PluginManifest(
                name="test_plugin",
                version=version,
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY
            )
            assert manifest.version == version
    
    def test_dependencies_validation(self):
        """测试依赖验证"""
        # 有效依赖规范
        valid_deps = {
            "plugin1": ">=1.0.0",
            "plugin2": ">=1.0.0,<2.0.0",
            "plugin3": "==1.5.0",
            "plugin4": "~=1.2.0"
        }
        
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies=valid_deps
        )
        assert manifest.dependencies == valid_deps
        
        # 无效依赖规范
        with pytest.raises(ValidationError):
            PluginManifest(
                name="test_plugin",
                version="1.0.0",
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY,
                dependencies={"plugin1": "invalid_version_spec"}
            )
    
    def test_cpu_percent_validation(self):
        """测试CPU使用率验证"""
        # 有效CPU使用率
        valid_percents = [1.0, 50.0, 100.0]
        for percent in valid_percents:
            manifest = PluginManifest(
                name="test_plugin",
                version="1.0.0",
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY,
                max_cpu_percent=percent
            )
            assert manifest.max_cpu_percent == percent
        
        # 无效CPU使用率
        invalid_percents = [0.0, -10.0, 150.0]
        for percent in invalid_percents:
            with pytest.raises(ValidationError):
                PluginManifest(
                    name="test_plugin",
                    version="1.0.0",
                    description="Test",
                    author="Test",
                    category=PluginCategory.UTILITY,
                    max_cpu_percent=percent
                )
    
    def test_is_compatible_with(self):
        """测试兼容性检查"""
        plugin1 = PluginManifest(
            name="plugin1",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            provides=["service_a"]
        )
        
        plugin2 = PluginManifest(
            name="plugin2",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            provides=["service_b"]
        )
        
        # 兼容的插件
        assert plugin1.is_compatible_with(plugin2)
        assert plugin2.is_compatible_with(plugin1)
        
        # 提供相同服务的插件（不兼容）
        plugin3 = PluginManifest(
            name="plugin3",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            provides=["service_a"]
        )
        
        assert not plugin1.is_compatible_with(plugin3)
        
        # 显式冲突的插件
        plugin4 = PluginManifest(
            name="plugin4",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            conflicts=["plugin1"]
        )
        
        assert not plugin1.is_compatible_with(plugin4)
        assert not plugin4.is_compatible_with(plugin1)
    
    def test_get_resource_footprint(self):
        """测试资源占用估算"""
        manifest = PluginManifest(
            name="resource_heavy_plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            max_memory_mb=2048,
            max_cpu_percent=80.0,
            max_disk_mb=4096
        )
        
        footprint = manifest.get_resource_footprint()
        assert footprint["memory_mb"] == 2048
        assert footprint["cpu_percent"] == 80.0
        assert footprint["disk_mb"] == 4096


class TestManifestValidator:
    """测试清单验证器"""
    
    def test_validate_manifest_success(self):
        """测试成功验证"""
        manifest = PluginManifest(
            name="valid_plugin",
            version="1.0.0",
            description="Valid plugin",
            author="Test Author",
            category=PluginCategory.UTILITY,
            max_memory_mb=512,
            max_disk_mb=1024
        )
        
        errors = ManifestValidator.validate_manifest(manifest)
        assert errors == []
    
    def test_validate_manifest_errors(self):
        """测试验证错误"""
        # 创建有问题的清单
        manifest = PluginManifest(
            name="invalid_plugin",
            version="1.0.0",
            description="Valid description",  # 先用有效值
            author="Valid author",  # 先用有效值
            category=PluginCategory.UTILITY,
            max_memory_mb=256,  # 有效内存限制
            max_disk_mb=512,  # 有效磁盘限制
        )
        
        # 手动设置问题值（绕过Pydantic验证）
        manifest.description = ""
        manifest.author = ""
        manifest.dependencies = {"invalid_plugin": ">=1.0.0"}  # 自依赖
        manifest.max_memory_mb = 0  # 无效内存限制
        manifest.max_disk_mb = 0  # 无效磁盘限制
        
        errors = ManifestValidator.validate_manifest(manifest)
        assert len(errors) > 0
        assert any("描述不能为空" in error for error in errors)
        assert any("作者不能为空" in error for error in errors)
        assert any("不能依赖自己" in error for error in errors)
        assert any("内存限制必须大于0" in error for error in errors)
        assert any("磁盘限制必须大于0" in error for error in errors)
    
    def test_security_level_resource_validation(self):
        """测试安全等级与资源的匹配性验证"""
        # 低安全等级但高内存使用
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            security_level=SecurityLevel.LOW,
            max_memory_mb=512,  # 超过256MB限制
            max_disk_mb=1024
        )
        
        errors = ManifestValidator.validate_manifest(manifest)
        assert any("低安全等级插件的内存使用不应超过256MB" in error for error in errors)
        
        # 关键插件但高CPU使用
        manifest2 = PluginManifest(
            name="test_plugin2",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY,
            security_level=SecurityLevel.CRITICAL,
            max_cpu_percent=90.0,  # 超过80%限制
            max_memory_mb=256,
            max_disk_mb=512
        )
        
        errors2 = ManifestValidator.validate_manifest(manifest2)
        assert any("关键插件的CPU使用率不应超过80%" in error for error in errors2)
    
    def test_load_from_yaml_file(self):
        """测试从YAML文件加载"""
        manifest_data = {
            "name": "yaml_test_plugin",
            "version": "1.0.0",
            "description": "YAML test plugin",
            "author": "Test Author",
            "category": "utility",
            "dependencies": {"base_plugin": ">=1.0.0"},
            "max_memory_mb": 512,
            "max_disk_mb": 1024
        }
        
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(manifest_data, f, default_flow_style=False)
            yaml_path = Path(f.name)
        
        try:
            manifest = ManifestValidator.load_from_file(yaml_path)
            assert manifest.name == "yaml_test_plugin"
            assert manifest.dependencies["base_plugin"] == ">=1.0.0"
        finally:
            yaml_path.unlink()
    
    def test_load_from_json_file(self):
        """测试从JSON文件加载"""
        manifest_data = {
            "name": "json_test_plugin",
            "version": "1.0.0",
            "description": "JSON test plugin",
            "author": "Test Author",
            "category": "utility",
            "max_memory_mb": 512,
            "max_disk_mb": 1024
        }
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(manifest_data, f, indent=2)
            json_path = Path(f.name)
        
        try:
            manifest = ManifestValidator.load_from_file(json_path)
            assert manifest.name == "json_test_plugin"
        finally:
            json_path.unlink()
    
    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            ManifestValidator.load_from_file(Path("/nonexistent/file.yaml"))
    
    def test_load_unsupported_format(self):
        """测试加载不支持的格式"""
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("not a manifest")
            txt_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="不支持的清单文件格式"):
                ManifestValidator.load_from_file(txt_path)
        finally:
            txt_path.unlink()
    
    def test_save_to_yaml_file(self):
        """测试保存到YAML文件"""
        manifest = PluginManifest(
            name="save_test_plugin",
            version="1.0.0",
            description="Save test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        with TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "test_manifest.yaml"
            ManifestValidator.save_to_file(manifest, yaml_path, "yaml")
            
            # 验证文件被创建
            assert yaml_path.exists()
            
            # 验证内容正确
            loaded_manifest = ManifestValidator.load_from_file(yaml_path)
            assert loaded_manifest.name == manifest.name
            assert loaded_manifest.version == manifest.version
    
    def test_save_to_json_file(self):
        """测试保存到JSON文件"""
        manifest = PluginManifest(
            name="save_test_plugin",
            version="1.0.0",
            description="Save test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY
        )
        
        with TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "test_manifest.json"
            ManifestValidator.save_to_file(manifest, json_path, "json")
            
            # 验证文件被创建
            assert json_path.exists()
            
            # 验证内容正确
            loaded_manifest = ManifestValidator.load_from_file(json_path)
            assert loaded_manifest.name == manifest.name
            assert loaded_manifest.version == manifest.version
    
    def test_save_unsupported_format(self):
        """测试保存不支持的格式"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            category=PluginCategory.UTILITY
        )
        
        with TemporaryDirectory() as temp_dir:
            txt_path = Path(temp_dir) / "test.txt"
            
            with pytest.raises(ValueError, match="不支持的保存格式"):
                ManifestValidator.save_to_file(manifest, txt_path, "txt")
    
    def test_create_template(self):
        """测试创建模板"""
        template = ManifestValidator.create_template("my_plugin", PluginCategory.DATA_SOURCE)
        
        assert template.name == "my_plugin"
        assert template.version == "1.0.0"
        assert template.author == "SimTradeLab Team"
        assert template.category == PluginCategory.DATA_SOURCE
        assert "data_source" in template.tags
        assert "event_bus" in template.requires
        assert "config_center" in template.requires