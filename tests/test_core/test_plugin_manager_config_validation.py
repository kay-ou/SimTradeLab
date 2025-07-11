#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试插件管理器配置验证集成
验证配置验证功能是否正确集成到插件生命周期中
"""

import pytest
from typing import Optional
from pydantic import Field

from simtradelab.plugins.base import BasePlugin, PluginConfig, PluginMetadata
from simtradelab.plugins.config.base_config import BasePluginConfig
from simtradelab.core.plugin_manager import PluginManager, PluginLoadError


class SamplePluginConfig(BasePluginConfig):
    """示例插件配置模型"""
    api_key: str = Field(..., description="API密钥")
    timeout: int = Field(default=30, description="超时时间")
    debug: bool = Field(default=False, description="调试模式")
    database_url: str = Field(default="${DATABASE_URL}", description="数据库URL")


class SamplePlugin(BasePlugin):
    """示例插件，包含配置验证"""
    
    # 定义配置模型
    config_model = SamplePluginConfig
    
    def __init__(self, metadata: PluginMetadata, config: PluginConfig):
        super().__init__(metadata, config)
        self.validated_config: Optional[SamplePluginConfig] = None
    
    def _on_initialize(self):
        """初始化插件"""
        if hasattr(self.config, 'data') and self.config.data:
            self.validated_config = SamplePluginConfig(**self.config.data)
    
    def _on_start(self):
        """启动插件"""
        pass
    
    def _on_stop(self):
        """停止插件"""
        pass


class SimplePlugin(BasePlugin):
    """简单插件，无配置模型"""
    
    def _on_initialize(self):
        """初始化插件"""
        pass
    
    def _on_start(self):
        """启动插件"""
        pass
    
    def _on_stop(self):
        """停止插件"""
        pass


def test_plugin_config_validation_success(monkeypatch):
    """测试插件配置验证成功的情况"""
    # 设置环境变量
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 准备有效的配置数据
    config_data = {
        "default": {
            "api_key": "test_key",
            "timeout": 60,
            "debug": True,
            "database_url": "${DATABASE_URL}"
        }
    }
    
    # 创建插件配置
    plugin_config = PluginConfig()
    plugin_config.data = config_data
    
    # 注册并加载插件
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    plugin_instance = manager.load_plugin(plugin_name)
    
    # 验证配置已正确验证和设置
    assert plugin_instance.validated_config is not None
    assert plugin_instance.validated_config.api_key == "test_key"
    assert plugin_instance.validated_config.timeout == 60
    assert plugin_instance.validated_config.debug is True
    assert plugin_instance.validated_config.database_url == "postgresql://localhost/test"


def test_plugin_config_validation_failure(monkeypatch):
    """测试插件配置验证失败的情况"""
    # 设置环境变量
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 准备无效的配置数据（缺少必需字段）
    config_data = {
        "default": {
            "timeout": 60,
            "debug": True
            # 缺少必需的 api_key 字段
        }
    }
    
    # 创建插件配置
    plugin_config = PluginConfig()
    plugin_config.data = config_data
    
    # 注册插件
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    
    # 尝试加载插件，应该失败
    with pytest.raises(PluginLoadError, match="插件 SamplePlugin 配置验证失败"):
        manager.load_plugin(plugin_name)


def test_plugin_config_validation_env_var_missing(monkeypatch):
    """测试环境变量缺失时配置验证失败"""
    # 确保环境变量不存在
    monkeypatch.delenv("DATABASE_URL", raising=False)
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 准备配置数据（包含未设置的环境变量）
    config_data = {
        "default": {
            "api_key": "test_key",
            "database_url": "${DATABASE_URL}"
        }
    }
    
    # 创建插件配置
    plugin_config = PluginConfig()
    plugin_config.data = config_data
    
    # 注册插件
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    
    # 尝试加载插件，应该失败
    with pytest.raises(PluginLoadError, match="插件 SamplePlugin 配置验证失败"):
        manager.load_plugin(plugin_name)


def test_plugin_without_config_model():
    """测试没有配置模型的插件正常工作"""
    # 创建插件管理器
    manager = PluginManager()
    
    # 注册并加载插件（没有配置模型，应该正常工作）
    plugin_name = manager.register_plugin(SimplePlugin)
    plugin_instance = manager.load_plugin(plugin_name)
    
    # 验证插件正常加载
    assert plugin_instance is not None
    assert plugin_name in manager.list_plugins()


def test_plugin_config_validation_with_empty_config():
    """测试配置为空时跳过验证"""
    # 创建插件管理器
    manager = PluginManager()
    
    # 创建空配置
    plugin_config = PluginConfig()
    # 不设置 config.data，保持为空
    
    # 注册并加载插件（空配置应该跳过验证）
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    plugin_instance = manager.load_plugin(plugin_name)
    
    # 验证插件正常加载
    assert plugin_instance is not None
    assert plugin_name in manager.list_plugins()


def test_plugin_config_validation_with_multi_env(monkeypatch):
    """测试多环境配置验证"""
    # 设置环境变量
    monkeypatch.setenv("DATABASE_URL", "postgresql://prod-db/app")
    monkeypatch.setenv("APP_ENV", "production")
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 准备多环境配置数据
    config_data = {
        "default": {
            "api_key": "default_key",
            "timeout": 30,
            "database_url": "${DATABASE_URL}"
        },
        "production": {
            "api_key": "prod_key",
            "timeout": 120,
            "debug": False
        }
    }
    
    # 创建插件配置
    plugin_config = PluginConfig()
    plugin_config.data = config_data
    
    # 注册并加载插件
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    plugin_instance = manager.load_plugin(plugin_name)
    
    # 验证生产环境配置被正确应用
    assert plugin_instance.validated_config is not None
    assert plugin_instance.validated_config.api_key == "prod_key"  # 被覆盖
    assert plugin_instance.validated_config.timeout == 120  # 被覆盖
    assert plugin_instance.validated_config.debug is False  # 被覆盖
    assert plugin_instance.validated_config.database_url == "postgresql://prod-db/app"  # 继承并解析


def test_plugin_config_validation_type_error(monkeypatch):
    """测试类型错误时配置验证失败"""
    # 设置环境变量
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 准备类型错误的配置数据
    config_data = {
        "default": {
            "api_key": "test_key",
            "timeout": "not_an_integer",  # 类型错误
            "database_url": "${DATABASE_URL}"
        }
    }
    
    # 创建插件配置
    plugin_config = PluginConfig()
    plugin_config.data = config_data
    
    # 注册插件
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    
    # 尝试加载插件，应该失败
    with pytest.raises(PluginLoadError, match="插件 SamplePlugin 配置验证失败"):
        manager.load_plugin(plugin_name)


def test_plugin_config_validation_extra_fields(monkeypatch):
    """测试额外字段时配置验证失败"""
    # 设置环境变量
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 准备包含额外字段的配置数据
    config_data = {
        "default": {
            "api_key": "test_key",
            "timeout": 60,
            "database_url": "${DATABASE_URL}",
            "unknown_field": "should_not_be_allowed"  # 额外字段
        }
    }
    
    # 创建插件配置
    plugin_config = PluginConfig()
    plugin_config.data = config_data
    
    # 注册插件
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    
    # 尝试加载插件，应该失败
    with pytest.raises(PluginLoadError, match="插件 SamplePlugin 配置验证失败"):
        manager.load_plugin(plugin_name)


def test_plugin_config_validation_preserves_validated_data(monkeypatch):
    """测试配置验证后数据被正确保存"""
    # 设置环境变量
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    
    # 创建插件管理器
    manager = PluginManager()
    
    # 准备配置数据
    config_data = {
        "default": {
            "api_key": "test_key",
            "database_url": "${DATABASE_URL}"
        }
    }
    
    # 创建插件配置
    plugin_config = PluginConfig()
    plugin_config.data = config_data
    
    # 注册并加载插件
    plugin_name = manager.register_plugin(SamplePlugin, config=plugin_config)
    plugin_instance = manager.load_plugin(plugin_name)
    
    # 验证配置数据被正确保存到 plugin_config.data
    assert plugin_instance.config.data is not None
    assert plugin_instance.config.data["api_key"] == "test_key"
    assert plugin_instance.config.data["database_url"] == "postgresql://localhost/test"
    # 验证默认值被填充
    assert plugin_instance.config.data["timeout"] == 30
    assert plugin_instance.config.data["debug"] is False


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])