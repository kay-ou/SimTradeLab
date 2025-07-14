#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置验证器功能
包含环境变量解析、多环境配置、数据验证等核心功能测试
"""

import os
from typing import Any, Dict, Optional

import pytest
from pydantic import Field, ValidationError

from simtradelab.plugins.config.base_config import BasePluginConfig
from simtradelab.plugins.config.validator import ConfigValidator


# 定义测试用的配置模型
class NestedConfig(BasePluginConfig):
    """嵌套配置模型"""

    value: int = 1
    secret: str = "${NESTED_SECRET}"


class SamplePluginConfig(BasePluginConfig):
    """测试插件配置模型"""

    api_key: str = Field(..., description="API密钥")
    api_secret: str = Field(..., description="API密钥")
    timeout: int = Field(default=10, description="超时时间（秒）")
    sub_config: Optional[NestedConfig] = None
    nested_dict: Dict[str, Any] = {}


# 测试数据
VALID_CONFIG_DATA = {
    "default": {
        "api_key": "default_key",
        "api_secret": "default_secret",
        "timeout": 20,
        "nested_dict": {"db_host": "localhost", "db_pass": "${DB_PASSWORD}"},
    },
    "production": {
        "api_key": "prod_key",
        "timeout": 30,
    },
    "development": {
        "api_key": "${DEV_API_KEY}",
    },
}


def test_validate_default_config(monkeypatch):
    """测试验证默认配置"""
    monkeypatch.setenv("DB_PASSWORD", "default_db_pass")

    config = ConfigValidator.validate(
        SamplePluginConfig, VALID_CONFIG_DATA, env="default"
    )

    assert config.api_key == "default_key"
    assert config.api_secret == "default_secret"
    assert config.timeout == 20
    assert config.nested_dict["db_pass"] == "default_db_pass"


def test_validate_production_config_overrides_default(monkeypatch):
    """测试生产环境配置正确覆盖默认值"""
    monkeypatch.setenv("DB_PASSWORD", "prod_db_pass")

    config = ConfigValidator.validate(
        SamplePluginConfig, VALID_CONFIG_DATA, env="production"
    )

    assert config.api_key == "prod_key"  # 被覆盖
    assert config.api_secret == "default_secret"  # 继承自默认配置
    assert config.timeout == 30  # 被覆盖
    assert config.nested_dict["db_pass"] == "prod_db_pass"


def test_validate_development_config_with_env_variable(monkeypatch):
    """测试开发环境配置正确解析环境变量"""
    monkeypatch.setenv("DEV_API_KEY", "dev_key_from_env")
    monkeypatch.setenv("DB_PASSWORD", "dev_db_pass")

    config = ConfigValidator.validate(
        SamplePluginConfig, VALID_CONFIG_DATA, env="development"
    )

    assert config.api_key == "dev_key_from_env"
    assert config.api_secret == "default_secret"  # 继承自默认配置
    assert config.nested_dict["db_pass"] == "dev_db_pass"


def test_validate_missing_env_variable_raises_error(monkeypatch):
    """测试缺失环境变量时抛出错误"""
    monkeypatch.setenv("DB_PASSWORD", "dummy_password")  # 默认配置需要的环境变量
    monkeypatch.delenv("DEV_API_KEY", raising=False)  # 删除开发环境需要的环境变量

    with pytest.raises(ValidationError, match="环境变量 'DEV_API_KEY' 未设置"):
        ConfigValidator.validate(
            SamplePluginConfig, VALID_CONFIG_DATA, env="development"
        )


def test_validate_invalid_data_type_raises_error(monkeypatch):
    """测试错误数据类型时抛出 Pydantic ValidationError"""
    monkeypatch.setenv("DB_PASSWORD", "dummy_pass")

    invalid_data = {
        "default": {
            "api_key": "some_key",
            "api_secret": "some_secret",
            "timeout": "not_an_integer",  # 错误的数据类型
        }
    }

    with pytest.raises(ValidationError):
        ConfigValidator.validate(SamplePluginConfig, invalid_data)


def test_validate_extra_field_raises_error(monkeypatch):
    """测试额外字段时抛出 Pydantic ValidationError"""
    monkeypatch.setenv("DB_PASSWORD", "dummy_pass")

    invalid_data = {
        "default": {
            "api_key": "some_key",
            "api_secret": "some_secret",
            "extra_field": "this_is_not_allowed",  # 额外字段
        }
    }

    with pytest.raises(ValidationError) as exc_info:
        ConfigValidator.validate(SamplePluginConfig, invalid_data)
    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_validate_missing_required_field_raises_error(monkeypatch):
    """测试缺失必需字段时抛出 Pydantic ValidationError"""
    monkeypatch.setenv("DB_PASSWORD", "dummy_pass")

    invalid_data = {
        "default": {
            "api_key": "some_key",
            # 缺失必需字段 api_secret
        }
    }

    with pytest.raises(ValidationError) as exc_info:
        ConfigValidator.validate(SamplePluginConfig, invalid_data)
    assert "Field required" in str(exc_info.value)


def test_nested_config_with_env_var(monkeypatch):
    """测试嵌套 Pydantic 模型中的环境变量解析"""
    monkeypatch.setenv("NESTED_SECRET", "super_secret")
    monkeypatch.setenv("DB_PASSWORD", "dummy_pass")

    data = {
        "default": {
            "api_key": "key",
            "api_secret": "secret",
            "sub_config": {"value": 123, "secret": "${NESTED_SECRET}"},
        }
    }

    config = ConfigValidator.validate(SamplePluginConfig, data)

    assert config.sub_config is not None
    assert config.sub_config.secret == "super_secret"


def test_nested_config_missing_env_var_raises_error(monkeypatch):
    """测试嵌套模型中缺失环境变量时抛出错误"""
    monkeypatch.delenv("NESTED_SECRET", raising=False)
    monkeypatch.setenv("DB_PASSWORD", "dummy_pass")

    data = {
        "default": {
            "api_key": "key",
            "api_secret": "secret",
            "sub_config": {"value": 123, "secret": "${NESTED_SECRET}"},
        }
    }

    with pytest.raises(ValidationError, match="环境变量 'NESTED_SECRET' 未设置"):
        ConfigValidator.validate(SamplePluginConfig, data)


def test_validate_auto_env_detection(monkeypatch):
    """测试自动环境检测功能"""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DB_PASSWORD", "auto_env_pass")

    # 不指定 env 参数，应该自动使用 APP_ENV 环境变量
    config = ConfigValidator.validate(SamplePluginConfig, VALID_CONFIG_DATA)

    assert config.api_key == "prod_key"  # 使用了 production 环境配置
    assert config.timeout == 30


def test_validate_default_env_when_app_env_not_set(monkeypatch):
    """测试当 APP_ENV 未设置时使用默认环境"""
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("DB_PASSWORD", "default_env_pass")

    # 准备不依赖缺失环境变量的测试数据
    simple_config_data = {
        "default": {"api_key": "default_key", "api_secret": "default_secret"},
        "development": {"api_key": "dev_key", "timeout": 15},
    }

    # 不指定 env 参数且 APP_ENV 未设置，应该使用 development 作为默认值
    config = ConfigValidator.validate(SamplePluginConfig, simple_config_data)

    # 应该使用 development 环境配置，并继承默认配置
    assert config.api_key == "dev_key"  # 来自 development 环境
    assert config.api_secret == "default_secret"  # 继承自 default 环境
    assert config.timeout == 15  # 来自 development 环境


def test_validate_deep_merge_functionality(monkeypatch):
    """测试深度合并功能"""
    monkeypatch.setenv("DB_PASSWORD", "deep_merge_pass")

    complex_data = {
        "default": {
            "api_key": "default_key",
            "api_secret": "default_secret",
            "nested_dict": {
                "db_host": "localhost",
                "db_port": 5432,
                "db_pass": "${DB_PASSWORD}",
                "cache": {"enabled": True, "ttl": 300},
            },
        },
        "production": {
            "api_key": "prod_key",
            "nested_dict": {
                "db_host": "prod-db.example.com",
                "cache": {"ttl": 600},  # 只覆盖 ttl，保留 enabled
            },
        },
    }

    config = ConfigValidator.validate(
        SamplePluginConfig, complex_data, env="production"
    )

    assert config.api_key == "prod_key"
    assert config.api_secret == "default_secret"  # 继承
    assert config.nested_dict["db_host"] == "prod-db.example.com"  # 覆盖
    assert config.nested_dict["db_port"] == 5432  # 继承
    assert config.nested_dict["db_pass"] == "deep_merge_pass"  # 继承并解析环境变量
    assert config.nested_dict["cache"]["enabled"] is True  # 继承
    assert config.nested_dict["cache"]["ttl"] == 600  # 覆盖


def test_validate_empty_config_data():
    """测试空配置数据的处理"""
    empty_data = {}

    with pytest.raises(ValidationError):
        ConfigValidator.validate(SamplePluginConfig, empty_data)


def test_validate_only_env_specific_config(monkeypatch):
    """测试只有环境特定配置的情况"""
    monkeypatch.setenv("DB_PASSWORD", "env_only_pass")

    env_only_data = {
        "production": {
            "api_key": "prod_key",
            "api_secret": "prod_secret",
            "nested_dict": {"db_pass": "${DB_PASSWORD}"},
        }
    }

    config = ConfigValidator.validate(
        SamplePluginConfig, env_only_data, env="production"
    )

    assert config.api_key == "prod_key"
    assert config.api_secret == "prod_secret"
    assert config.timeout == 10  # 使用模型默认值
    assert config.nested_dict["db_pass"] == "env_only_pass"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
