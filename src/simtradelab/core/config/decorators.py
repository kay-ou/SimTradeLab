# -*- coding: utf-8 -*-
"""
插件配置装饰器系统

提供优雅的配置绑定机制，在编译时确立配置模型关系。
"""

import functools
import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

# 类型变量用于保持装饰器的类型安全
PluginType = TypeVar("PluginType")


def plugin_config(config_model: Type[BaseModel]):
    """
    插件配置装饰器

    在插件类定义时绑定配置模型，避免运行时类型检查。

    使用示例:
        @plugin_config(MyPluginConfig)
        class MyPlugin(BasePlugin):
            pass

    Args:
        config_model: Pydantic配置模型类

    Returns:
        装饰后的插件类

    Raises:
        TypeError: 如果config_model不是BaseModel子类
    """

    def decorator(plugin_class: Type[PluginType]) -> Type[PluginType]:
        # 编译时验证配置模型
        if not issubclass(config_model, BaseModel):
            raise TypeError(f"配置模型 {config_model.__name__} 必须继承 pydantic.BaseModel")

        # 绑定配置模型到插件类
        plugin_class.config_model = config_model  # type: ignore[attr-defined]

        # 添加日志记录
        logger = logging.getLogger(__name__)
        logger.debug(
            f"Plugin {plugin_class.__name__} bound to config model {config_model.__name__}"
        )

        return plugin_class

    return decorator


def optional_config(config_model: Optional[Type[BaseModel]] = None):
    """
    可选配置装饰器

    允许插件在没有特定配置模型时使用默认配置。

    使用示例:
        @optional_config(MyPluginConfig)  # 有配置模型
        class MyPlugin(BasePlugin):
            pass

        @optional_config()  # 使用默认配置
        class SimplePlugin(BasePlugin):
            pass

    Args:
        config_model: 可选的Pydantic配置模型类

    Returns:
        装饰后的插件类
    """

    def decorator(plugin_class: Type[PluginType]) -> Type[PluginType]:
        if config_model is not None:
            # 有配置模型时进行验证
            if not issubclass(config_model, BaseModel):
                raise TypeError(f"配置模型 {config_model.__name__} 必须继承 pydantic.BaseModel")
            plugin_class.config_model = config_model  # type: ignore[attr-defined]
        else:
            # 明确设置为None，使用默认配置
            plugin_class.config_model = None  # type: ignore[attr-defined]

        return plugin_class

    return decorator


def config_required(config_model: Type[BaseModel]):
    """
    强制配置装饰器

    确保插件必须有有效的配置才能初始化。

    Args:
        config_model: 必需的Pydantic配置模型类

    Returns:
        装饰后的插件类
    """

    def decorator(plugin_class: Type[PluginType]) -> Type[PluginType]:
        # 编译时验证
        if not issubclass(config_model, BaseModel):
            raise TypeError(f"配置模型 {config_model.__name__} 必须继承 pydantic.BaseModel")

        # 绑定配置模型
        plugin_class.config_model = config_model  # type: ignore[attr-defined]

        # 包装初始化方法以强制配置验证
        original_init = plugin_class.__init__

        @functools.wraps(original_init)
        def wrapped_init(self, metadata, config=None):  # type: ignore[no-untyped-def]
            if config is None:
                raise ValueError(f"插件 {plugin_class.__name__} 需要配置，但未提供配置数据")
            original_init(self, metadata, config)

        plugin_class.__init__ = wrapped_init  # type: ignore[method-assign]

        return plugin_class

    return decorator
