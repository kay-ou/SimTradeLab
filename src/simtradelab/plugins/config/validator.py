# -*- coding: utf-8 -*-
"""
SimTradeLab 插件配置验证器
提供统一的配置验证入口点，集成 Pydantic 验证机制
"""

from typing import Any, Dict, Optional, Type

from pydantic import ValidationError

from .base_config import T


class ConfigValidator:
    """
    插件配置验证器

    提供统一的配置验证入口点，负责处理和验证插件配置数据
    """

    @staticmethod
    def validate(
        config_model: Type[T],
        config_data: Dict[str, Any],
        env: Optional[str] = None,
    ) -> T:
        """
        根据指定的 Pydantic 模型验证原始配置数据

        此方法协调 BasePluginConfig 中定义的加载和验证流程

        Args:
            config_model: 用于验证的 Pydantic 模型类（BasePluginConfig 的子类）
            config_data: 原始配置字典
            env: 目标环境（如 "development", "production"）
                 如果为 None，则使用环境变量 APP_ENV

        Returns:
            验证后的配置对象，具有完整的类型信息

        Raises:
            ValidationError: 当数据验证失败时抛出
            ValueError: 当环境变量设置不正确时抛出
        """
        try:
            # 使用配置模型的 load_from_dict 方法加载和验证配置
            validated_config = config_model.load_from_dict(config_data, env=env)
            return validated_config
        except ValidationError as e:
            # 重新抛出 ValidationError，保持 Pydantic 原生错误信息
            raise e
        except ValueError as e:
            # 重新抛出 ValueError，处理环境变量解析错误
            raise e
