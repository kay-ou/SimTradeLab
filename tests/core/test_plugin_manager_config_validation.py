#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试插件管理器与配置验证的集成

核心关注点：
1. PluginManager是否正确调用ConfigManager。
2. 当ConfigManager验证成功或失败时，PluginManager是否能正确处理。
"""
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from simtradelab.core.plugin_manager import PluginLoadError, PluginManager
from simtradelab.plugins.base import BasePlugin, PluginConfig, PluginMetadata
from simtradelab.plugins.config.base_config import BasePluginConfig


class SimpleConfig(BasePluginConfig):
    """一个简单的Pydantic配置模型用于测试"""

    value: str = "default"


class PluginWithConfig(BasePlugin):
    """一个需要配置的示例插件"""

    config_model = SimpleConfig

    def __init__(self, metadata: PluginMetadata, config: SimpleConfig):
        super().__init__(metadata, config)
        self.final_config = config

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass


class PluginWithoutConfig(BasePlugin):
    """一个不需要配置的示例插件"""

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass


@pytest.fixture
def mock_config_manager():
    """模拟ConfigManager，用于控制配置验证的行为"""
    # 使用patch来模拟get_config_manager函数，使其返回一个MagicMock实例
    with patch("simtradelab.core.plugin_manager.get_config_manager") as mock_get:
        mock_manager = MagicMock()
        mock_get.return_value = mock_manager
        yield mock_manager


def test_load_plugin_with_valid_config_successfully(mock_config_manager):
    """
    测试场景：ConfigManager验证成功。
    预期行为：PluginManager成功加载插件，并且插件接收到正确的配置对象。
    """
    # 1. 准备
    manager = PluginManager(register_core_plugins=False)
    plugin_name = manager.register_plugin(PluginWithConfig)

    # 模拟ConfigManager成功返回一个已验证的配置对象
    validated_config_instance = SimpleConfig(value="validated_value")
    mock_config_manager.create_validated_config.return_value = validated_config_instance

    # 2. 执行
    plugin_instance = manager.load_plugin(plugin_name)

    # 3. 断言
    # 验证ConfigManager的create_validated_config被正确调用
    mock_config_manager.create_validated_config.assert_called_once_with(
        PluginWithConfig, None
    )
    # 验证插件已加载
    assert isinstance(plugin_instance, PluginWithConfig)
    # 验证插件收到了由ConfigManager返回的、经过验证的配置实例
    assert plugin_instance.final_config is validated_config_instance
    assert plugin_instance.final_config.value == "validated_value"


def test_load_plugin_wraps_validation_error_in_plugin_load_error(mock_config_manager):
    """
    测试场景：ConfigManager在验证配置时抛出异常。
    预期行为：PluginManager捕获该异常，并将其包装成一个PluginLoadError抛出。
    """
    # 1. 准备
    manager = PluginManager(register_core_plugins=False)
    plugin_name = manager.register_plugin(PluginWithConfig)

    # 模拟ConfigManager在验证时抛出ValidationError
    validation_error = ValidationError.from_exception_data(
        title="SimpleConfig", line_errors=[]
    )
    mock_config_manager.create_validated_config.side_effect = validation_error

    # 2. 执行 & 3. 断言
    with pytest.raises(
        PluginLoadError, match=f"Failed to load plugin {plugin_name}"
    ) as excinfo:
        manager.load_plugin(plugin_name)

    # 验证原始的ValidationError是导致PluginLoadError的原因
    assert excinfo.getrepr(style="short") is not None
    assert isinstance(excinfo.value.__cause__, ValidationError)

    # 验证ConfigManager的create_validated_config被调用
    mock_config_manager.create_validated_config.assert_called_once_with(
        PluginWithConfig, None
    )


def test_load_plugin_without_config_model_successfully(mock_config_manager):
    """
    测试场景：加载一个没有定义config_model的插件。
    预期行为：插件应能成功加载，ConfigManager会返回一个默认的空配置。
    """
    # 1. 准备
    manager = PluginManager(register_core_plugins=False)
    plugin_name = manager.register_plugin(PluginWithoutConfig)

    # 模拟ConfigManager为无配置模型的插件返回一个默认的PluginConfig实例
    default_config = PluginConfig()
    mock_config_manager.create_validated_config.return_value = default_config

    # 2. 执行
    plugin_instance = manager.load_plugin(plugin_name)

    # 3. 断言
    assert isinstance(plugin_instance, PluginWithoutConfig)
    # 验证插件的配置是ConfigManager返回的默认配置
    assert plugin_instance.config is default_config
    # 验证ConfigManager被正确调用
    mock_config_manager.create_validated_config.assert_called_once_with(
        PluginWithoutConfig, None
    )


def test_load_plugin_with_explicit_config_object(mock_config_manager):
    """
    测试场景：在加载插件时，显式传入一个配置对象。
    预期行为：该配置对象被传递给ConfigManager进行处理。
    """
    # 1. 准备
    manager = PluginManager(register_core_plugins=False)
    plugin_name = manager.register_plugin(PluginWithConfig)

    # 准备一个在load_plugin时传入的配置对象
    explicit_config = PluginConfig(enabled=True)

    # 模拟ConfigManager返回一个验证后的配置实例
    validated_config_instance = SimpleConfig(value="from_explicit_config")
    mock_config_manager.create_validated_config.return_value = validated_config_instance

    # 2. 执行
    plugin_instance = manager.load_plugin(plugin_name, config=explicit_config)

    # 3. 断言
    # 验证传递给ConfigManager的是我们显式提供的配置对象
    mock_config_manager.create_validated_config.assert_called_once_with(
        PluginWithConfig, explicit_config
    )
    assert isinstance(plugin_instance, PluginWithConfig)
    assert plugin_instance.final_config.value == "from_explicit_config"
