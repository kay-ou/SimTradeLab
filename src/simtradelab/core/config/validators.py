# -*- coding: utf-8 -*-
"""
配置验证器

提供专门的配置验证逻辑，分离验证职责。
"""

import logging
from typing import Any, Dict, List, Type

from pydantic import BaseModel, ValidationError

from .config_manager import ConfigValidationError


class ConfigValidator:
    """
    配置验证器

    提供配置验证的辅助方法和批量验证功能。
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def validate_single_config(
        self,
        config_model: Type[BaseModel],
        config_data: Dict[str, Any],
        plugin_name: str = None,
    ) -> Dict[str, Any]:
        """
        验证单个配置

        Args:
            config_model: 配置模型类
            config_data: 配置数据
            plugin_name: 插件名称（用于错误报告）

        Returns:
            验证后的配置数据

        Raises:
            ConfigValidationError: 验证失败
        """
        plugin_name = plugin_name or config_model.__name__

        try:
            validated_config = config_model.model_validate(config_data)
            return validated_config.model_dump()

        except ValidationError as e:
            self._raise_validation_error(plugin_name, e)

    def validate_multiple_configs(
        self, configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量验证配置

        Args:
            configs: 配置列表，每个配置包含 'model', 'data', 'name' 字段

        Returns:
            验证后的配置数据列表

        Raises:
            ConfigValidationError: 任一配置验证失败
        """
        validated_configs = []

        for i, config in enumerate(configs):
            config_model = config.get("model")
            config_data = config.get("data", {})
            plugin_name = config.get("name", f"Config_{i}")

            if not config_model:
                raise ConfigValidationError(plugin_name, "缺少配置模型")

            validated_data = self.validate_single_config(
                config_model, config_data, plugin_name
            )
            validated_configs.append(validated_data)

        return validated_configs

    def check_required_fields(
        self, config_model: Type[BaseModel], config_data: Dict[str, Any]
    ) -> List[str]:
        """
        检查缺失的必需字段

        Args:
            config_model: 配置模型类
            config_data: 配置数据

        Returns:
            缺失的必需字段列表
        """
        try:
            config_model.model_validate(config_data)
            return []
        except ValidationError as e:
            missing_fields = []
            for error in e.errors():
                if error["type"] == "missing":
                    field_name = ".".join(str(loc) for loc in error["loc"])
                    missing_fields.append(field_name)
            return missing_fields

    def check_field_types(
        self, config_model: Type[BaseModel], config_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        检查字段类型错误

        Args:
            config_model: 配置模型类
            config_data: 配置数据

        Returns:
            类型错误列表，每个错误包含 'field', 'expected', 'got' 信息
        """
        try:
            config_model.model_validate(config_data)
            return []
        except ValidationError as e:
            type_errors = []
            for error in e.errors():
                if error["type"] in ["type_error", "value_error"]:
                    field_name = ".".join(str(loc) for loc in error["loc"])
                    type_errors.append(
                        {
                            "field": field_name,
                            "message": error["msg"],
                            "type": error["type"],
                        }
                    )
            return type_errors

    def get_config_schema_info(self, config_model: Type[BaseModel]) -> Dict[str, Any]:
        """
        获取配置模型的结构信息

        Args:
            config_model: 配置模型类

        Returns:
            配置结构信息
        """
        schema = config_model.model_json_schema()

        info = {
            "title": schema.get("title", config_model.__name__),
            "description": schema.get("description", ""),
            "properties": {},
            "required_fields": schema.get("required", []),
        }

        properties = schema.get("properties", {})
        for field_name, field_info in properties.items():
            info["properties"][field_name] = {
                "type": field_info.get("type"),
                "description": field_info.get("description", ""),
                "default": field_info.get("default"),
                "required": field_name in info["required_fields"],
            }

        return info

    def compare_configs(self, config1: BaseModel, config2: BaseModel) -> Dict[str, Any]:
        """
        比较两个配置对象的差异

        Args:
            config1: 第一个配置对象
            config2: 第二个配置对象

        Returns:
            差异信息
        """
        dict1 = config1.model_dump()
        dict2 = config2.model_dump()

        differences = {"added": {}, "removed": {}, "changed": {}}

        # 检查新增和修改的字段
        for key, value in dict2.items():
            if key not in dict1:
                differences["added"][key] = value
            elif dict1[key] != value:
                differences["changed"][key] = {"old": dict1[key], "new": value}

        # 检查删除的字段
        for key, value in dict1.items():
            if key not in dict2:
                differences["removed"][key] = value

        return differences

    def _raise_validation_error(
        self, plugin_name: str, validation_error: ValidationError
    ) -> None:
        """
        格式化并抛出配置验证错误
        """
        error_details = []
        for error in validation_error.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            error_details.append(f"{field}: {error['msg']}")

        raise ConfigValidationError(
            plugin_name, f"配置验证失败: {'; '.join(error_details)}", validation_error
        )
