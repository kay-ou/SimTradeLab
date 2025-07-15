# -*- coding: utf-8 -*-
"""
配置管理器测试

测试统一配置管理器的核心功能
"""

from typing import Optional

import pytest
from pydantic import BaseModel, Field, ValidationError

from simtradelab.core.config.config_manager import (
    ConfigValidationError,
    PluginConfigManager,
    get_config_manager,
    reset_config_manager,
)
from simtradelab.plugins.config.base_config import BasePluginConfig


# 测试用配置模型
class SamplePluginConfig(BaseModel):
    """测试插件配置模型"""

    name: str = Field(default="test", description="插件名称")
    value: int = Field(default=42, ge=0, le=100, description="测试值")
    enabled: bool = Field(default=True, description="是否启用")
    optional_field: Optional[str] = Field(default=None, description="可选字段")


class InvalidConfig:
    """无效的配置类（不继承BaseModel）"""

    pass


# 测试用插件类
class TestPlugin:
    """带有配置模型的测试插件"""

    config_model = SamplePluginConfig

    class METADATA:
        name = "test_plugin"


class TestPluginNoConfig:
    """没有配置模型的测试插件"""

    class METADATA:
        name = "test_plugin_no_config"


class TestPluginInvalidConfig:
    """配置模型无效的测试插件"""

    config_model = InvalidConfig

    class METADATA:
        name = "test_plugin_invalid"


class SamplePluginConfigManager:
    """配置管理器测试类"""

    def setup_method(self):
        """测试前设置"""
        self.manager = PluginConfigManager()

    def teardown_method(self):
        """测试后清理"""
        self.manager.clear_cache()

    def test_create_validated_config_with_none(self):
        """测试使用None配置数据创建配置"""
        config = self.manager.create_validated_config(TestPlugin, None)

        assert isinstance(config, SamplePluginConfig)
        assert config.name == "test"
        assert config.value == 42
        assert config.enabled is True
        assert config.optional_field is None

    def test_create_validated_config_with_dict(self):
        """测试使用字典创建配置"""
        config_data = {
            "name": "custom_plugin",
            "value": 75,
            "enabled": False,
            "optional_field": "test_value",
        }

        config = self.manager.create_validated_config(TestPlugin, config_data)

        assert isinstance(config, SamplePluginConfig)
        assert config.name == "custom_plugin"
        assert config.value == 75
        assert config.enabled is False
        assert config.optional_field == "test_value"

    def test_create_validated_config_with_existing_model(self):
        """测试使用已有配置模型实例创建配置"""
        existing_config = SamplePluginConfig(name="existing", value=99, enabled=True)

        config = self.manager.create_validated_config(TestPlugin, existing_config)

        assert config is existing_config
        assert config.name == "existing"
        assert config.value == 99

    def test_create_validated_config_with_extra_fields(self):
        """测试包含额外字段的配置数据"""
        config_data = {
            "name": "test_plugin",
            "value": 50,
            "extra_field": "should_be_ignored",  # 额外字段应被忽略
            "another_extra": 123,
        }

        # 应该正常工作，额外字段被Pydantic自动忽略
        config = self.manager.create_validated_config(TestPlugin, config_data)

        assert isinstance(config, SamplePluginConfig)
        assert config.name == "test_plugin"
        assert config.value == 50
        assert not hasattr(config, "extra_field")

    def test_create_validated_config_with_invalid_data(self):
        """测试使用无效数据创建配置"""
        config_data = {
            "name": "test",
            "value": 150,  # 超出范围 (0-100)
            "enabled": "not_a_boolean",  # 类型错误
        }

        with pytest.raises(ConfigValidationError) as exc_info:
            self.manager.create_validated_config(TestPlugin, config_data)

        assert "test_plugin" in str(exc_info.value)
        assert "字段验证失败" in str(exc_info.value)

    def test_create_validated_config_no_config_model(self):
        """测试没有配置模型的插件"""
        config = self.manager.create_validated_config(TestPluginNoConfig, None)

        assert isinstance(config, BasePluginConfig)
        assert config.enabled is True

    def test_create_validated_config_invalid_config_model(self):
        """测试配置模型无效的插件"""
        with pytest.raises(ConfigValidationError) as exc_info:
            self.manager.create_validated_config(TestPluginInvalidConfig, None)

        assert "配置创建失败" in str(exc_info.value)

    def test_get_config_model_caching(self):
        """测试配置模型缓存"""
        # 第一次调用
        model1 = self.manager._get_config_model(TestPlugin)

        # 第二次调用应返回相同结果（从缓存）
        model2 = self.manager._get_config_model(TestPlugin)

        assert model1 is model2
        assert model1 == SamplePluginConfig

        # 检查缓存信息
        cache_info = self.manager.get_cache_info()
        assert cache_info["cached_models"] >= 1
        assert "TestPlugin" in cache_info["model_names"]

    def test_get_config_schema(self):
        """测试获取配置Schema"""
        schema = self.manager.get_config_schema(TestPlugin)

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "value" in schema["properties"]
        assert "enabled" in schema["properties"]

    def test_validate_config_data(self):
        """测试配置数据验证"""
        config_data = {"name": "test_validation", "value": 25, "enabled": True}

        validated_data = self.manager.validate_config_data(TestPlugin, config_data)

        assert isinstance(validated_data, dict)
        assert validated_data["name"] == "test_validation"
        assert validated_data["value"] == 25
        assert validated_data["enabled"] is True

    def test_validate_config_data_invalid(self):
        """测试无效配置数据验证"""
        config_data = {
            "name": "",  # 空字符串可能无效，取决于具体验证规则
            "value": -1,  # 超出范围
            "enabled": "invalid",  # 类型错误
        }

        with pytest.raises(ConfigValidationError):
            self.manager.validate_config_data(TestPlugin, config_data)

    def test_clear_cache(self):
        """测试清除缓存"""
        # 先创建一些缓存
        self.manager._get_config_model(TestPlugin)
        self.manager._get_config_model(TestPluginNoConfig)

        assert self.manager.get_cache_info()["cached_models"] >= 2

        # 清除缓存
        self.manager.clear_cache()

        assert self.manager.get_cache_info()["cached_models"] == 0

    def test_config_validation_error_details(self):
        """测试配置验证错误的详细信息"""
        config_data = {"value": 200, "enabled": "not_boolean"}  # 超出范围  # 类型错误

        with pytest.raises(ConfigValidationError) as exc_info:
            self.manager.create_validated_config(TestPlugin, config_data)

        error = exc_info.value
        assert error.plugin_name == "test_plugin"
        assert isinstance(error.original_error, ValidationError)
        assert "字段验证失败" in str(error)


class TestGlobalConfigManager:
    """全局配置管理器测试"""

    def teardown_method(self):
        """测试后重置全局状态"""
        reset_config_manager()

    def test_get_config_manager_singleton(self):
        """测试全局配置管理器单例模式"""
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        assert manager1 is manager2
        assert isinstance(manager1, PluginConfigManager)

    def test_reset_config_manager(self):
        """测试重置全局配置管理器"""
        manager1 = get_config_manager()
        reset_config_manager()
        manager2 = get_config_manager()

        assert manager1 is not manager2
        assert isinstance(manager2, PluginConfigManager)


class TestPluginConfigManagerAdditional:
    """额外的配置管理器测试，提升覆盖率"""

    def setup_method(self):
        """测试前设置"""
        self.manager = PluginConfigManager()

    def teardown_method(self):
        """测试后清理"""
        self.manager.clear_cache()

    def test_create_config_from_data_with_dict(self):
        """测试从字典创建配置"""
        config_data = {"name": "test", "value": 50}
        config = self.manager._create_config_from_data(
            SamplePluginConfig, config_data, "test_plugin"
        )
        
        assert isinstance(config, SamplePluginConfig)
        assert config.name == "test"
        assert config.value == 50

    def test_create_config_from_data_with_invalid_data(self):
        """测试从无效数据创建配置"""
        config_data = {"value": 200}  # 超出范围
        
        with pytest.raises(ConfigValidationError):
            self.manager._create_config_from_data(
                SamplePluginConfig, config_data, "test_plugin"
            )

    def test_create_validated_config_with_string_data(self):
        """测试使用字符串配置数据创建配置（应该失败）"""
        config_data = "invalid_config_string"

        with pytest.raises(ConfigValidationError) as exc_info:
            self.manager.create_validated_config(TestPlugin, config_data)

        assert "配置格式错误" in str(exc_info.value)

    def test_create_validated_config_with_number_data(self):
        """测试使用数字配置数据创建配置（应该失败）"""
        config_data = 12345

        with pytest.raises(ConfigValidationError) as exc_info:
            self.manager.create_validated_config(TestPlugin, config_data)

        assert "配置格式错误" in str(exc_info.value)

    def test_create_validated_config_with_list_data(self):
        """测试使用列表配置数据创建配置（应该失败）"""
        config_data = ["invalid", "config", "list"]

        with pytest.raises(ConfigValidationError) as exc_info:
            self.manager.create_validated_config(TestPlugin, config_data)

        assert "配置格式错误" in str(exc_info.value)

    def test_get_config_model_cache_key_generation(self):
        """测试配置模型缓存键生成"""
        # 确保缓存键是基于类名
        model1 = self.manager._get_config_model(TestPlugin)
        model2 = self.manager._get_config_model(TestPlugin)

        assert model1 is model2  # 应该是相同的对象（从缓存获取）

        # 检查缓存中确实有这个键
        assert "TestPlugin" in self.manager._config_model_cache

    def test_validation_error_with_none_plugin_class(self):
        """测试使用None作为插件类"""
        with pytest.raises(AttributeError):
            self.manager.create_validated_config(None, {})

    def test_get_config_schema_for_plugin_without_config_model(self):
        """测试获取没有配置模型的插件的Schema"""
        schema = self.manager.get_config_schema(TestPluginNoConfig)

        assert isinstance(schema, dict)
        assert "properties" in schema
        # 应该返回BasePluginConfig的schema
        assert "enabled" in schema["properties"]

    def test_validate_config_data_with_none_data(self):
        """测试验证None配置数据"""
        with pytest.raises(ConfigValidationError):
            self.manager.validate_config_data(TestPlugin, None)

    def test_validate_config_data_with_empty_dict(self):
        """测试验证空字典配置数据"""
        validated_data = self.manager.validate_config_data(TestPlugin, {})

        assert isinstance(validated_data, dict)
        # 应该返回默认值
        assert validated_data["name"] == "test"
        assert validated_data["value"] == 42
        assert validated_data["enabled"] is True

    def test_cache_info_structure(self):
        """测试缓存信息结构"""
        # 创建一些缓存条目
        self.manager._get_config_model(TestPlugin)
        self.manager._get_config_model(TestPluginNoConfig)

        cache_info = self.manager.get_cache_info()

        assert isinstance(cache_info, dict)
        assert "cached_models" in cache_info
        assert "model_names" in cache_info
        assert isinstance(cache_info["cached_models"], int)
        assert isinstance(cache_info["model_names"], list)
        assert cache_info["cached_models"] >= 2
        assert len(cache_info["model_names"]) >= 2

    def test_config_validation_error_exception_hierarchy(self):
        """测试配置验证错误异常的层次结构"""
        error = ConfigValidationError("test_plugin", "test message")

        assert isinstance(error, Exception)
        assert error.plugin_name == "test_plugin"
        assert error.original_error is None
        assert "插件 'test_plugin' 配置验证失败: test message" in str(error)

    def test_config_validation_error_with_original_error(self):
        """测试带有原始错误的配置验证错误"""
        original_error = ValueError("original error")
        error = ConfigValidationError("test_plugin", "test message", original_error)

        assert error.plugin_name == "test_plugin"
        assert error.original_error is original_error
        assert "插件 'test_plugin' 配置验证失败: test message" in str(error)

    def test_logger_initialization(self):
        """测试日志记录器初始化"""
        assert hasattr(self.manager, '_logger')
        assert self.manager._logger is not None
        assert self.manager._logger.name == 'simtradelab.core.config.config_manager'

    def test_plugin_name_extraction_from_metadata(self):
        """测试从METADATA中提取插件名称"""
        class PluginWithMetadata:
            class METADATA:
                name = "metadata_plugin"

        config = self.manager.create_validated_config(PluginWithMetadata, None)
        assert isinstance(config, BasePluginConfig)  # 应该使用默认配置

    def test_plugin_name_extraction_from_class_name(self):
        """测试从类名提取插件名称"""
        class PluginWithoutMetadata:
            pass

        config = self.manager.create_validated_config(PluginWithoutMetadata, None)
        assert isinstance(config, BasePluginConfig)  # 应该使用默认配置

    def test_get_config_model_with_invalid_config_model(self):
        """测试获取无效配置模型"""
        with pytest.raises(ConfigValidationError):
            self.manager.create_validated_config(TestPluginInvalidConfig, None)
