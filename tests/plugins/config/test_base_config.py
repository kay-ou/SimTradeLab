#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基础配置模块 BasePluginConfig
包含环境变量解析、多环境配置、深度合并等核心功能的详细测试
"""

from typing import Any, Dict, List

import pytest
from pydantic import Field, ValidationError

from simtradelab.plugins.config.base_config import ENV_VAR_PATTERN, BasePluginConfig


class SimpleConfig(BasePluginConfig):
    """简单配置模型"""

    name: str = Field(..., description="配置名称")
    value: int = Field(default=42, description="配置值")


class ComplexConfig(BasePluginConfig):
    """复杂配置模型"""

    database_url: str = Field(..., description="数据库URL")
    api_key: str = Field(..., description="API密钥")
    timeout: int = Field(default=30, description="超时时间")
    debug: bool = Field(default=False, description="调试模式")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    nested_config: Dict[str, Any] = Field(default_factory=dict, description="嵌套配置")


class NestedConfig(BasePluginConfig):
    """嵌套配置模型"""

    server_config: Dict[str, Any] = Field(default_factory=dict)
    cache_config: Dict[str, Any] = Field(default_factory=dict)


class TestEnvVarPattern:
    """测试环境变量模式匹配"""

    def test_env_var_pattern_matches_valid_format(self):
        """测试环境变量模式匹配有效格式"""
        valid_patterns = [
            "${VAR_NAME}",
            "${DATABASE_URL}",
            "${API_KEY_123}",
            "${REDIS_HOST}",
            "${DEBUG_MODE}",
        ]

        for pattern in valid_patterns:
            match = ENV_VAR_PATTERN.match(pattern)
            assert match is not None, f"模式 {pattern} 应该匹配"

    def test_env_var_pattern_extracts_variable_name(self):
        """测试环境变量模式提取变量名"""
        test_cases = [
            ("${VAR_NAME}", "VAR_NAME"),
            ("${DATABASE_URL}", "DATABASE_URL"),
            ("${API_KEY_123}", "API_KEY_123"),
        ]

        for pattern, expected_var in test_cases:
            match = ENV_VAR_PATTERN.match(pattern)
            assert match is not None
            assert match.group(1) == expected_var

    def test_env_var_pattern_rejects_invalid_format(self):
        """测试环境变量模式拒绝无效格式"""
        invalid_patterns = [
            "$VAR_NAME",  # 缺少大括号
            "${VAR-NAME}",  # 包含连字符
            "${VAR.NAME}",  # 包含点号
            "${VAR NAME}",  # 包含空格
            "VAR_NAME",  # 完全没有格式
            "${}",  # 空变量名
        ]

        for pattern in invalid_patterns:
            match = ENV_VAR_PATTERN.match(pattern)
            assert match is None, f"模式 {pattern} 不应该匹配"


class TestBasePluginConfig:
    """测试基础配置模块功能"""

    def test_create_config_with_valid_data(self):
        """测试使用有效数据创建配置"""
        config = SimpleConfig(name="test_config", value=100)

        assert config.name == "test_config"
        assert config.value == 100

    def test_create_config_with_default_values(self):
        """测试使用默认值创建配置"""
        config = SimpleConfig(name="test_config")

        assert config.name == "test_config"
        assert config.value == 42  # 默认值

    def test_create_config_rejects_extra_fields(self):
        """测试创建配置时拒绝额外字段"""
        with pytest.raises(ValidationError) as exc_info:
            SimpleConfig(name="test", value=100, extra_field="not_allowed")

        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_create_config_requires_mandatory_fields(self):
        """测试创建配置时要求必需字段"""
        with pytest.raises(ValidationError) as exc_info:
            SimpleConfig(value=100)  # 缺少必需的 name 字段

        assert "Field required" in str(exc_info.value)

    def test_create_config_validates_field_types(self):
        """测试创建配置时验证字段类型"""
        with pytest.raises(ValidationError):
            SimpleConfig(name="test", value="not_an_integer")

    def test_env_var_resolution_single_variable(self, monkeypatch):
        """测试单个环境变量解析"""
        monkeypatch.setenv("TEST_VAR", "resolved_value")

        config = SimpleConfig(name="${TEST_VAR}", value=100)

        assert config.name == "resolved_value"
        assert config.value == 100

    def test_env_var_resolution_multiple_variables(self, monkeypatch):
        """测试多个环境变量解析"""
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("API_KEY", "secret_key")

        config = ComplexConfig(
            database_url="${DB_HOST}",  # 单个环境变量
            api_key="${API_KEY}",
            timeout=60,
            nested_config={"db_port": "${DB_PORT}"},  # 在嵌套配置中使用
        )

        assert config.database_url == "localhost"
        assert config.api_key == "secret_key"
        assert config.timeout == 60
        assert config.nested_config["db_port"] == "5432"

    def test_env_var_resolution_in_nested_dict(self, monkeypatch):
        """测试嵌套字典中的环境变量解析"""
        monkeypatch.setenv("REDIS_HOST", "redis.example.com")
        monkeypatch.setenv("REDIS_PORT", "6379")

        config = ComplexConfig(
            database_url="postgresql://localhost/test",
            api_key="test_key",
            nested_config={"redis": {"host": "${REDIS_HOST}", "port": "${REDIS_PORT}"}},
        )

        assert config.nested_config["redis"]["host"] == "redis.example.com"
        assert config.nested_config["redis"]["port"] == "6379"

    def test_env_var_resolution_in_list(self, monkeypatch):
        """测试列表中的环境变量解析"""
        monkeypatch.setenv("TAG1", "production")
        monkeypatch.setenv("TAG2", "web")

        config = ComplexConfig(
            database_url="postgresql://localhost/test",
            api_key="test_key",
            tags=["${TAG1}", "${TAG2}", "fixed_tag"],
        )

        assert config.tags == ["production", "web", "fixed_tag"]

    def test_env_var_resolution_missing_variable_raises_error(self, monkeypatch):
        """测试缺失环境变量时抛出错误"""
        monkeypatch.delenv("MISSING_VAR", raising=False)

        with pytest.raises(ValidationError, match="环境变量 'MISSING_VAR' 未设置"):
            SimpleConfig(name="${MISSING_VAR}", value=100)

    def test_env_var_resolution_preserves_non_env_values(self, monkeypatch):
        """测试环境变量解析保留非环境变量值"""
        monkeypatch.setenv("TEST_VAR", "resolved")

        config = ComplexConfig(
            database_url="postgresql://localhost/test",  # 普通字符串
            api_key="${TEST_VAR}",  # 环境变量
            timeout=30,  # 数字
            debug=True,  # 布尔值
        )

        assert config.database_url == "postgresql://localhost/test"
        assert config.api_key == "resolved"
        assert config.timeout == 30
        assert config.debug is True

    def test_load_from_dict_default_only(self):
        """测试从字典加载仅有默认配置"""
        config_data = {"default": {"name": "test_config", "value": 200}}

        config = SimpleConfig.load_from_dict(config_data)

        assert config.name == "test_config"
        assert config.value == 200

    def test_load_from_dict_with_env_override(self):
        """测试从字典加载带环境覆盖"""
        config_data = {
            "default": {"name": "default_name", "value": 100},
            "production": {"name": "prod_name", "value": 500},
        }

        config = SimpleConfig.load_from_dict(config_data, env="production")

        assert config.name == "prod_name"
        assert config.value == 500

    def test_load_from_dict_partial_override(self):
        """测试从字典加载部分覆盖"""
        config_data = {
            "default": {"name": "default_name", "value": 100},
            "development": {
                "name": "dev_name"
                # value 未覆盖，应该使用默认值
            },
        }

        config = SimpleConfig.load_from_dict(config_data, env="development")

        assert config.name == "dev_name"
        assert config.value == 100  # 继承自默认配置

    def test_load_from_dict_deep_merge(self):
        """测试从字典加载深度合并"""
        config_data = {
            "default": {
                "database_url": "postgresql://localhost/test",
                "api_key": "default_key",
                "nested_config": {
                    "server": {"host": "localhost", "port": 8000},
                    "cache": {"enabled": True, "ttl": 300},
                },
            },
            "production": {
                "api_key": "prod_key",
                "nested_config": {
                    "server": {
                        "host": "prod.example.com"
                        # port 未覆盖，应该继承
                    },
                    "cache": {
                        "ttl": 600
                        # enabled 未覆盖，应该继承
                    },
                },
            },
        }

        config = ComplexConfig.load_from_dict(config_data, env="production")

        assert config.database_url == "postgresql://localhost/test"  # 继承
        assert config.api_key == "prod_key"  # 覆盖
        assert config.nested_config["server"]["host"] == "prod.example.com"  # 覆盖
        assert config.nested_config["server"]["port"] == 8000  # 继承
        assert config.nested_config["cache"]["enabled"] is True  # 继承
        assert config.nested_config["cache"]["ttl"] == 600  # 覆盖

    def test_load_from_dict_auto_env_detection(self, monkeypatch):
        """测试自动环境检测"""
        monkeypatch.setenv("APP_ENV", "production")

        config_data = {
            "default": {"name": "default_name", "value": 100},
            "production": {"name": "prod_name", "value": 500},
        }

        # 不指定 env 参数，应该使用 APP_ENV
        config = SimpleConfig.load_from_dict(config_data)

        assert config.name == "prod_name"
        assert config.value == 500

    def test_load_from_dict_default_env_fallback(self, monkeypatch):
        """测试默认环境回退"""
        monkeypatch.delenv("APP_ENV", raising=False)

        config_data = {
            "default": {"name": "default_name", "value": 100},
            "development": {"name": "dev_name"},
        }

        # 不指定 env 且 APP_ENV 未设置，应该使用 development
        config = SimpleConfig.load_from_dict(config_data)

        assert config.name == "dev_name"
        assert config.value == 100

    def test_load_from_dict_with_env_vars(self, monkeypatch):
        """测试从字典加载时解析环境变量"""
        monkeypatch.setenv("DATABASE_HOST", "prod-db.example.com")
        monkeypatch.setenv("API_SECRET", "super_secret_key")

        config_data = {
            "default": {
                "database_url": "${DATABASE_HOST}",  # 单个环境变量
                "api_key": "${API_SECRET}",
                "timeout": 30,
            }
        }

        config = ComplexConfig.load_from_dict(config_data)

        assert config.database_url == "prod-db.example.com"
        assert config.api_key == "super_secret_key"
        assert config.timeout == 30

    def test_load_from_dict_empty_default_config(self):
        """测试空默认配置"""
        config_data = {"production": {"name": "prod_name", "value": 500}}

        config = SimpleConfig.load_from_dict(config_data, env="production")

        assert config.name == "prod_name"
        assert config.value == 500

    def test_load_from_dict_nonexistent_env(self):
        """测试不存在的环境"""
        config_data = {"default": {"name": "default_name", "value": 100}}

        # 请求不存在的环境，应该只使用默认配置
        config = SimpleConfig.load_from_dict(config_data, env="nonexistent")

        assert config.name == "default_name"
        assert config.value == 100

    def test_load_from_dict_empty_config_data(self):
        """测试空配置数据"""
        config_data = {}

        with pytest.raises(ValidationError):
            SimpleConfig.load_from_dict(config_data)

    def test_model_config_forbids_extra_fields(self):
        """测试模型配置禁止额外字段"""
        with pytest.raises(ValidationError):
            SimpleConfig(name="test", value=100, extra="not_allowed")

    def test_model_config_validates_assignment(self):
        """测试模型配置验证赋值"""
        config = SimpleConfig(name="test", value=100)

        # 正常赋值应该成功
        config.name = "new_name"
        assert config.name == "new_name"

        # 错误类型赋值应该失败
        with pytest.raises(ValidationError):
            config.value = "not_an_integer"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
