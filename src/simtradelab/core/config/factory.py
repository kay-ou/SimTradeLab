# -*- coding: utf-8 -*-
"""
配置工厂

提供标准化的配置对象创建方法，支持多种数据源。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Type, Union

import yaml
from pydantic import BaseModel, ValidationError

from .config_manager import ConfigValidationError


class ConfigFactory:
    """
    配置工厂类

    提供从不同数据源创建配置对象的标准化方法。
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def create_from_dict(
        self,
        config_model: Type[BaseModel],
        config_dict: Dict[str, Any],
        strict: bool = False,
    ) -> BaseModel:
        """
        从字典创建配置对象

        Args:
            config_model: 配置模型类
            config_dict: 配置字典
            strict: 是否启用严格模式（不允许额外字段）

        Returns:
            配置对象

        Raises:
            ConfigValidationError: 配置验证失败
        """
        try:
            if strict:
                return config_model.model_validate(config_dict, strict=True)
            else:
                return config_model.model_validate(config_dict)

        except ValidationError as e:
            raise ConfigValidationError(config_model.__name__, f"字典配置验证失败: {str(e)}", e)

    def create_from_json_file(
        self, config_model: Type[BaseModel], file_path: Union[str, Path]
    ) -> BaseModel:
        """
        从JSON文件创建配置对象

        Args:
            config_model: 配置模型类
            file_path: JSON文件路径

        Returns:
            配置对象

        Raises:
            ConfigValidationError: 配置验证失败
            FileNotFoundError: 文件不存在
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)

            return self.create_from_dict(config_model, config_dict)

        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        except json.JSONDecodeError as e:
            raise ConfigValidationError(
                config_model.__name__, f"JSON文件格式错误: {str(e)}", e
            )
        except Exception as e:
            raise ConfigValidationError(
                config_model.__name__, f"读取JSON配置文件失败: {str(e)}", e
            )

    def create_from_yaml_file(
        self, config_model: Type[BaseModel], file_path: Union[str, Path]
    ) -> BaseModel:
        """
        从YAML文件创建配置对象

        Args:
            config_model: 配置模型类
            file_path: YAML文件路径

        Returns:
            配置对象

        Raises:
            ConfigValidationError: 配置验证失败
            FileNotFoundError: 文件不存在
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)

            if config_dict is None:
                config_dict = {}

            return self.create_from_dict(config_model, config_dict)

        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {file_path}")
        except yaml.YAMLError as e:
            raise ConfigValidationError(
                config_model.__name__, f"YAML文件格式错误: {str(e)}", e
            )
        except Exception as e:
            raise ConfigValidationError(
                config_model.__name__, f"读取YAML配置文件失败: {str(e)}", e
            )

    def create_from_env(
        self, config_model: Type[BaseModel], env_prefix: str = ""
    ) -> BaseModel:
        """
        从环境变量创建配置对象

        Args:
            config_model: 配置模型类
            env_prefix: 环境变量前缀

        Returns:
            配置对象
        """
        try:
            # 使用Pydantic的环境变量解析
            return config_model(_env_prefix=env_prefix)

        except ValidationError as e:
            raise ConfigValidationError(
                config_model.__name__, f"环境变量配置验证失败: {str(e)}", e
            )

    def create_merged_config(
        self, config_model: Type[BaseModel], *config_sources: Dict[str, Any]
    ) -> BaseModel:
        """
        合并多个配置源创建配置对象

        后面的配置源会覆盖前面的同名字段。

        Args:
            config_model: 配置模型类
            *config_sources: 配置字典列表

        Returns:
            配置对象
        """
        merged_config = {}

        for config_dict in config_sources:
            if config_dict:
                merged_config.update(config_dict)

        return self.create_from_dict(config_model, merged_config)

    def save_config_to_file(
        self, config: BaseModel, file_path: Union[str, Path], format: str = "json"
    ) -> None:
        """
        保存配置对象到文件

        Args:
            config: 配置对象
            file_path: 文件路径
            format: 文件格式 ('json' 或 'yaml')
        """
        file_path = Path(file_path)
        config_dict = config.model_dump()

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if format.lower() == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            elif format.lower() == "yaml":
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        config_dict, f, default_flow_style=False, allow_unicode=True
                    )
            else:
                raise ValueError(f"不支持的文件格式: {format}")

            self._logger.info(f"配置已保存到文件: {file_path}")

        except Exception as e:
            raise ConfigValidationError(
                config.__class__.__name__, f"保存配置文件失败: {str(e)}", e
            )
