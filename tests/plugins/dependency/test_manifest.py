# -*- coding: utf-8 -*-
"""
插件清单模型测试
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from pydantic import ValidationError

from simtradelab.plugins.dependency.manifest import (
    ManifestValidator,
    PluginCategory,
    PluginManifest,
)


class TestPluginManifest:
    """测试PluginManifest模型"""

    def test_valid_manifest(self):
        """测试有效的清单"""
        manifest_data = {
            "name": "my_test_plugin",
            "version": "1.2.3",
            "description": "A test plugin.",
            "author": "Test Author",
            "category": PluginCategory.UTILITY,
            "entry_point": "plugin:main",
        }
        manifest = PluginManifest(**manifest_data)
        assert manifest.name == "my_test_plugin"
        assert str(manifest.version) == "1.2.3"
        assert manifest.license == "MIT"  # 检查默认值

    def test_invalid_name(self):
        """测试无效的插件名称"""
        with pytest.raises(ValidationError, match="插件名称长度必须在3-50之间"):
            PluginManifest(
                name="ab",
                version="1.0.0",
                description="d",
                author="a",
                category=PluginCategory.DATA_SOURCE,
            )

    def test_invalid_version(self):
        """测试无效的版本格式"""
        with pytest.raises(ValidationError, match="版本必须遵循 MAJOR.MINOR.PATCH 格式"):
            PluginManifest(
                name="invalid_version_plugin",
                version="1.0",
                description="d",
                author="a",
                category=PluginCategory.STRATEGY,
            )

    def test_invalid_dependency_spec(self):
        """测试无效的依赖版本规范"""
        with pytest.raises(ValidationError, match="无效的版本规范"):
            PluginManifest(
                name="invalid_deps_plugin",
                version="1.0.0",
                description="d",
                author="a",
                category=PluginCategory.RISK,
                dependencies={"core": "invalid-spec"},
            )


class TestManifestValidator:
    """测试ManifestValidator"""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """创建一个临时目录。"""
        with tempfile.TemporaryDirectory() as td:
            yield Path(td)

    def test_load_from_yaml(self, temp_dir: Path):
        """测试从YAML文件加载"""
        manifest_content = """
        name: yaml_plugin
        version: 0.1.0
        description: A plugin from YAML.
        author: YAML Loader
        category: data_source
        """
        manifest_path = temp_dir / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest_content)

        manifest = ManifestValidator.load_from_file(manifest_path)
        assert manifest.name == "yaml_plugin"
        assert manifest.author == "YAML Loader"

    def test_load_from_json(self, temp_dir: Path):
        """测试从JSON文件加载"""
        manifest_content = {
            "name": "json_plugin",
            "version": "0.2.0",
            "description": "A plugin from JSON.",
            "author": "JSON Loader",
            "category": "strategy",
        }
        manifest_path = temp_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            import json

            json.dump(manifest_content, f)

        manifest = ManifestValidator.load_from_file(manifest_path)
        assert manifest.name == "json_plugin"
        assert manifest.category == PluginCategory.STRATEGY

    def test_save_and_load_from_file(self, temp_dir: Path):
        """测试保存到文件和从文件加载。"""
        manifest_data = {
            "name": "testplugin",
            "version": "1.2.3",
            "description": "A test plugin.",
            "author": "Test Author",
            "license": "MIT",
            "category": PluginCategory.UTILITY,
            "entry_point": "test_plugin.main:entry",
            "dependencies": {"core": ">=1.0.0, <2.0.0"},
            "tags": ["test", "example"],
            "homepage": "http://example.com/plugin",
        }
        manifest = PluginManifest(**manifest_data)

        # 测试YAML格式
        yaml_path = temp_dir / "manifest.yaml"
        ManifestValidator.save_to_file(manifest, yaml_path, format="yaml")
        assert yaml_path.exists()

        loaded_manifest_yaml = ManifestValidator.load_from_file(yaml_path)
        assert loaded_manifest_yaml.name == manifest.name
        assert str(loaded_manifest_yaml.version) == str(manifest.version)
        assert loaded_manifest_yaml.dependencies["core"] == ">=1.0.0, <2.0.0"

        # 测试JSON格式
        json_path = temp_dir / "manifest.json"
        ManifestValidator.save_to_file(manifest, json_path, format="json")
        assert json_path.exists()

        loaded_manifest_json = ManifestValidator.load_from_file(json_path)
        assert loaded_manifest_json.name == manifest.name
        assert str(loaded_manifest_json.version) == str(manifest.version)

    def test_load_from_file_not_found(self):
        """测试从不存在的文件加载。"""
        with pytest.raises(FileNotFoundError):
            ManifestValidator.load_from_file(Path("non_existent_file.yaml"))

    def test_unsupported_file_format(self, temp_dir: Path):
        """测试不支持的文件格式。"""
        txt_path = temp_dir / "manifest.txt"
        txt_path.touch()
        with pytest.raises(ValueError, match="不支持的清单文件格式: .txt"):
            ManifestValidator.load_from_file(txt_path)

    def test_is_compatible_with(self):
        """测试插件兼容性检查"""
        manifest1 = PluginManifest(
            name="plugin1",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            conflicts=["plugin2"],
            provides=["service_a"],
        )
        manifest2 = PluginManifest(
            name="plugin2",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )
        manifest3 = PluginManifest(
            name="plugin3",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            provides=["service_a"],
        )
        manifest4 = PluginManifest(
            name="plugin4",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
        )

        assert not manifest1.is_compatible_with(manifest2)
        assert not manifest1.is_compatible_with(manifest3)
        assert manifest1.is_compatible_with(manifest4)
        assert manifest2.is_compatible_with(manifest4)

    def test_get_resource_footprint(self):
        """测试资源占用估算"""
        manifest = PluginManifest(
            name="resource_plugin",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            max_memory_mb=128,
            max_cpu_percent=25.5,
            max_disk_mb=512,
        )
        footprint = manifest.get_resource_footprint()
        assert footprint["memory_mb"] == 128
        assert footprint["cpu_percent"] == 25.5
        assert footprint["disk_mb"] == 512

    def test_validate_manifest_logic(self):
        """测试 validate_manifest 方法的逻辑"""
        # 测试循环依赖
        manifest_self_dep = PluginManifest(
            name="self_dep",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            dependencies={"self_dep": ">=1.0.0"},
        )
        errors = ManifestValidator.validate_manifest(manifest_self_dep)
        assert "插件不能依赖自己" in errors

        # 测试资源限制
        manifest_zero_resource = PluginManifest(
            name="zero_resource",
            version="1.0.0",
            description="d",
            author="a",
            category=PluginCategory.UTILITY,
            max_memory_mb=0,
            max_disk_mb=-1,
        )
        errors = ManifestValidator.validate_manifest(manifest_zero_resource)
        assert "内存限制必须大于0" in errors
        assert "磁盘限制必须大于0" in errors

    def test_create_template(self):
        """测试创建清单模板"""
        template = ManifestValidator.create_template(
            "my_template", PluginCategory.STRATEGY
        )
        assert template.name == "my_template"
        assert template.category == PluginCategory.STRATEGY
        assert template.version == "1.0.0"
        assert "event_bus" in template.requires
