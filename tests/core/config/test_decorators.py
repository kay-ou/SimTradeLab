# -*- coding: utf-8 -*-
"""
插件配置装饰器测试

测试装饰器系统的编译时配置绑定功能
"""

from typing import Optional

import pytest
from pydantic import BaseModel, Field

from simtradelab.core.config.decorators import (
    config_required,
    optional_config,
    plugin_config,
)
from simtradelab.plugins.base import BasePlugin, PluginMetadata


# 测试用配置模型
class SimpleConfig(BaseModel):
    """简单配置模型"""

    name: str = Field(default="default", description="名称")
    value: int = Field(default=1, ge=0, description="值")


class ComplexConfig(BaseModel):
    """复杂配置模型"""

    required_field: str = Field(description="必需字段")
    optional_field: Optional[int] = Field(default=None, description="可选字段")


class NonPydanticConfig:
    """非Pydantic配置类"""

    pass


class TestPluginConfigDecorator:
    """插件配置装饰器测试"""

    def test_plugin_config_decorator_basic(self):
        """测试基本插件配置装饰器"""

        @plugin_config(SimpleConfig)
        class TestPlugin(BasePlugin):
            METADATA = PluginMetadata(name="test", version="1.0.0")

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        # 检查配置模型已正确绑定
        assert hasattr(TestPlugin, "config_model")
        assert TestPlugin.config_model == SimpleConfig

    def test_plugin_config_decorator_invalid_model(self):
        """测试使用无效配置模型的装饰器"""

        with pytest.raises(TypeError) as exc_info:

            @plugin_config(NonPydanticConfig)  # type: ignore[arg-type]
            class InvalidPlugin(BasePlugin):  # noqa: F841
                pass

        assert "必须继承 pydantic.BaseModel" in str(exc_info.value)

    def test_optional_config_decorator_with_model(self):
        """测试带配置模型的可选配置装饰器"""

        @optional_config(SimpleConfig)
        class OptionalPlugin(BasePlugin):
            METADATA = PluginMetadata(name="optional", version="1.0.0")

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        assert OptionalPlugin.config_model == SimpleConfig

    def test_optional_config_decorator_without_model(self):
        """测试不带配置模型的可选配置装饰器"""

        @optional_config()
        class NoConfigPlugin(BasePlugin):
            METADATA = PluginMetadata(name="no_config", version="1.0.0")

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        assert NoConfigPlugin.config_model is None

    def test_optional_config_decorator_invalid_model(self):
        """测试可选配置装饰器使用无效模型"""

        with pytest.raises(TypeError):

            @optional_config(NonPydanticConfig)  # type: ignore[arg-type]
            class InvalidOptionalPlugin(BasePlugin):  # noqa: F841
                pass

    def test_config_required_decorator(self):
        """测试强制配置装饰器"""

        @config_required(ComplexConfig)
        class RequiredConfigPlugin(BasePlugin):
            METADATA = PluginMetadata(name="required", version="1.0.0")

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        assert RequiredConfigPlugin.config_model == ComplexConfig

    def test_config_required_decorator_with_config(self):
        """测试强制配置装饰器与有效配置"""

        @config_required(ComplexConfig)
        class RequiredConfigPlugin(BasePlugin):
            METADATA = PluginMetadata(name="required", version="1.0.0")

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        metadata = PluginMetadata(name="test", version="1.0.0")
        config = ComplexConfig(required_field="test_value")

        # 应该正常创建
        plugin = RequiredConfigPlugin(metadata, config)
        assert plugin is not None

    def test_config_required_decorator_without_config(self):
        """测试强制配置装饰器缺少配置时的行为"""

        @config_required(ComplexConfig)
        class RequiredConfigPlugin(BasePlugin):
            METADATA = PluginMetadata(name="required", version="1.0.0")

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        metadata = PluginMetadata(name="test", version="1.0.0")

        # 应该抛出错误
        with pytest.raises(ValueError) as exc_info:
            RequiredConfigPlugin(metadata, None)

        assert "需要配置" in str(exc_info.value)

    def test_config_required_decorator_invalid_model(self):
        """测试强制配置装饰器使用无效模型"""

        with pytest.raises(TypeError):

            @config_required(NonPydanticConfig)  # type: ignore[arg-type]
            class InvalidRequiredPlugin(BasePlugin):  # noqa: F841
                pass

    def test_multiple_decorators_combination(self):
        """测试装饰器的组合使用"""

        # 这种组合在实际中不推荐，但测试装饰器行为
        @plugin_config(SimpleConfig)
        class MultiDecoratorPlugin(BasePlugin):
            METADATA = PluginMetadata(name="multi", version="1.0.0")

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

        # 最后应用的装饰器生效
        assert MultiDecoratorPlugin.config_model == SimpleConfig

    def test_decorator_preserves_class_attributes(self):
        """测试装饰器保持类属性"""

        @plugin_config(SimpleConfig)
        class AttributePlugin(BasePlugin):
            METADATA = PluginMetadata(name="attribute", version="1.0.0")
            custom_attribute = "test_value"

            def _on_initialize(self):
                pass

            def _on_start(self):
                pass

            def _on_stop(self):
                pass

            def custom_method(self):
                return "custom"

        # 检查原有属性和方法都保留
        assert AttributePlugin.custom_attribute == "test_value"
        assert hasattr(AttributePlugin, "custom_method")
        assert AttributePlugin.config_model == SimpleConfig

        # 实例化测试
        plugin = AttributePlugin(
            PluginMetadata(name="test", version="1.0.0"), SimpleConfig()
        )
        assert plugin.custom_method() == "custom"
