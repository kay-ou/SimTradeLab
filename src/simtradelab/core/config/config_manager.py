# -*- coding: utf-8 -*-
"""
统一配置管理器

消除插件管理器中丑陋的配置验证代码，提供清晰的配置管理接口。
核心设计原则：
1. 编译时验证而非运行时检查
2. 类型安全的配置创建
3. 单一职责：只负责配置管理
4. 零侵入：不改变现有插件API
"""

import logging
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

from ...plugins.config.base_config import BasePluginConfig


class ConfigValidationError(Exception):
    """配置验证异常"""

    def __init__(
        self, plugin_name: str, message: str, original_error: Optional[Exception] = None
    ):
        self.plugin_name = plugin_name
        self.original_error = original_error
        super().__init__(f"插件 '{plugin_name}' 配置验证失败: {message}")


class PluginConfigManager:
    """
    插件配置管理器

    负责统一处理插件配置的创建、验证和转换，
    消除插件管理器中的复杂配置处理逻辑。
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._config_model_cache: Dict[str, Type[BaseModel]] = {}

    def create_validated_config(
        self, plugin_class: Type, config_data: Optional[Any] = None
    ) -> BaseModel:
        """
        创建经过验证的配置对象

        这是E9修复的核心方法，替换插件管理器中的丑陋配置代码。

        Args:
            plugin_class: 插件类
            config_data: 配置数据（字典、BaseModel实例或None）

        Returns:
            验证后的配置对象

        Raises:
            ConfigValidationError: 配置验证失败
        """
        plugin_name = getattr(plugin_class, "METADATA", None)
        if plugin_name and hasattr(plugin_name, "name"):
            plugin_name = plugin_name.name
        else:
            plugin_name = plugin_class.__name__

        try:
            # 获取配置模型类
            config_model_class = self._get_config_model(plugin_class)

            # 如果没有配置数据，创建默认配置
            if config_data is None:
                return config_model_class()

            # 如果已经是正确的配置模型实例，直接返回
            if isinstance(config_data, config_model_class):
                return config_data

            # 从字典或其他格式创建配置对象
            return self._create_config_from_data(
                config_model_class, config_data, plugin_name
            )

        except Exception as e:
            if isinstance(e, ConfigValidationError):
                raise
            raise ConfigValidationError(plugin_name, f"配置创建失败: {str(e)}", e)

    def _get_config_model(self, plugin_class: Type) -> Type[BaseModel]:
        """
        获取插件的配置模型类

        编译时确定配置模型，避免运行时类型检查
        """
        # 检查缓存
        class_name = plugin_class.__name__
        if class_name in self._config_model_cache:
            return self._config_model_cache[class_name]

        # 获取插件定义的配置模型
        if (
            hasattr(plugin_class, "config_model")
            and plugin_class.config_model is not None
        ):
            config_model = plugin_class.config_model

            # 验证是Pydantic模型（编译时验证）
            if not issubclass(config_model, BaseModel):
                raise TypeError(f"配置模型 {config_model.__name__} 必须继承 BaseModel")

            # 缓存结果
            self._config_model_cache[class_name] = config_model
            return config_model

        # 默认使用基础配置
        self._config_model_cache[class_name] = BasePluginConfig
        return BasePluginConfig

    def _create_config_from_data(
        self, config_model_class: Type[BaseModel], config_data: Any, plugin_name: str
    ) -> BaseModel:
        """
        从配置数据创建配置对象

        使用Pydantic的内置机制，避免手动字段过滤
        """
        try:
            # 特殊处理PluginConfig对象
            from ...plugins.base import PluginConfig

            if isinstance(config_data, PluginConfig):
                if config_data.data:
                    # 如果有data字段，使用load_from_dict方法
                    if hasattr(config_model_class, "load_from_dict"):
                        return config_model_class.load_from_dict(config_data.data)
                    else:
                        # 提取data中的default配置或直接使用data
                        if isinstance(config_data.data, dict):
                            default_config = config_data.data.get(
                                "default", config_data.data
                            )
                            return config_model_class.model_validate(default_config)
                        else:
                            return config_model_class.model_validate(config_data.data)
                else:
                    # 如果没有data，创建默认配置
                    return config_model_class()

            elif isinstance(config_data, dict):
                # 使用Pydantic的model_validate，自动处理额外字段
                return config_model_class.model_validate(config_data)

            elif isinstance(config_data, BaseModel):
                # 从其他Pydantic模型转换
                config_dict = config_data.model_dump()
                return config_model_class.model_validate(config_dict)

            else:
                # 尝试直接构造
                return config_model_class(config_data)

        except ValidationError as e:
            # 提供清晰的错误信息
            error_details = []
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                error_details.append(f"{field}: {error['msg']}")

            raise ConfigValidationError(
                plugin_name, f"字段验证失败: {'; '.join(error_details)}", e
            )
        except Exception as e:
            raise ConfigValidationError(plugin_name, f"配置格式错误: {str(e)}", e)

    def get_config_schema(self, plugin_class: Type) -> Dict[str, Any]:
        """
        获取插件配置的JSON Schema

        用于配置验证和文档生成
        """
        config_model = self._get_config_model(plugin_class)
        return config_model.model_json_schema()

    def validate_config_data(
        self, plugin_class: Type, config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        验证配置数据但不创建对象

        用于配置预检查
        """
        config_model = self._get_config_model(plugin_class)

        try:
            # 验证但不创建对象
            validated = config_model.model_validate(config_data)
            return validated.model_dump()
        except ValidationError as e:
            # 获取插件名称
            metadata = getattr(plugin_class, "METADATA", None)
            if metadata and hasattr(metadata, "name"):
                plugin_name = metadata.name
            elif metadata and hasattr(metadata, "__name__"):
                plugin_name = metadata.__name__
            else:
                plugin_name = plugin_class.__name__

            raise ConfigValidationError(plugin_name, f"配置验证失败: {str(e)}", e)

    def clear_cache(self) -> None:
        """清除配置模型缓存"""
        self._config_model_cache.clear()
        self._logger.debug("Configuration model cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cached_models": len(self._config_model_cache),
            "model_names": list(self._config_model_cache.keys()),
        }


# 全局配置管理器实例
_global_config_manager: Optional[PluginConfigManager] = None


def get_config_manager() -> PluginConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = PluginConfigManager()
    return _global_config_manager


def reset_config_manager() -> None:
    """重置全局配置管理器（主要用于测试）"""
    global _global_config_manager
    _global_config_manager = None
