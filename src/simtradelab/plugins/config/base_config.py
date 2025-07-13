# -*- coding: utf-8 -*-
"""
SimTradeLab 插件基础配置模块
提供基于 Pydantic 的配置验证机制，支持环境变量解析和多环境配置
"""

import copy
import os
import re
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator

T = TypeVar("T", bound="BasePluginConfig")

# 环境变量匹配模式: ${VAR_NAME}
ENV_VAR_PATTERN = re.compile(r"\${([A-Za-z0-9_]+)}")


class BasePluginConfig(BaseModel):
    """
    所有插件配置的基类

    增强功能包括：
    1. **严格模式验证**：禁止额外字段，防止配置错误
    2. **环境变量解析**：自动解析 "${VAR_NAME}" 格式的环境变量
    3. **多环境配置**：根据 APP_ENV 环境变量加载不同环境的配置
    """

    enabled: bool = True  # 插件是否启用

    @model_validator(mode="before")
    @classmethod
    def _resolve_env_vars(cls, data: Any) -> Any:
        """
        Pydantic 模型验证器，在其他验证执行前递归解析环境变量

        支持在配置值中使用 ${VAR_NAME} 语法引用环境变量

        Args:
            data: 待验证的数据

        Returns:
            解析环境变量后的数据

        Raises:
            ValueError: 当环境变量未设置时抛出
        """
        if not isinstance(data, dict):
            return data

        def _resolve(value: Any) -> Any:
            """递归解析环境变量"""
            if isinstance(value, str):
                match = ENV_VAR_PATTERN.match(value)
                if not match:
                    return value
                env_var_name = match.group(1)
                env_var_value = os.getenv(env_var_name)
                if env_var_value is None:
                    raise ValueError(f"环境变量 '{env_var_name}' 未设置")
                return env_var_value
            elif isinstance(value, dict):
                return {k: _resolve(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_resolve(v) for v in value]
            else:
                return value

        return _resolve(data)

    @classmethod
    def load_from_dict(
        cls: Type[T],
        config_data: Dict[str, Any],
        env: Optional[str] = None,
    ) -> T:
        """
        从字典加载配置，支持环境特定的配置覆盖

        配置结构示例：
        {
            "default": {
                "api_key": "default_key",
                "timeout": 30
            },
            "production": {
                "api_key": "prod_key",
                "timeout": 60
            }
        }

        Args:
            config_data: 配置字典
            env: 目标环境（如 "development", "production"）
                 如果为 None，则使用 os.getenv("APP_ENV", "development")

        Returns:
            配置模型实例
        """
        if env is None:
            env = os.getenv("APP_ENV", "development")

        # 获取基础配置和环境特定配置
        base_config = config_data.get("default", {})
        env_config = config_data.get(env, {})

        def deep_merge(
            base: Dict[str, Any], overrides: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            深度合并两个字典，overrides 中的值会覆盖 base 中的值
            """
            result = copy.deepcopy(base)
            for key, value in overrides.items():
                if (
                    isinstance(value, dict)
                    and key in result
                    and isinstance(result[key], dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        # 合并基础配置和环境配置
        merged_config = deep_merge(base_config, env_config)

        return cls(**merged_config)

    # Pydantic v2 配置
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True  # 禁止额外字段  # 赋值时验证
    )
