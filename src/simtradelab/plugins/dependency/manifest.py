# -*- coding: utf-8 -*-
"""
插件清单模型

定义插件的元数据、依赖关系和配置规范。
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class SecurityLevel(str, Enum):
    """安全等级"""

    LOW = "low"  # 1-3: 基础插件，低风险
    MEDIUM = "medium"  # 4-6: 标准插件，中等风险
    HIGH = "high"  # 7-8: 敏感插件，高风险
    CRITICAL = "critical"  # 9-10: 核心插件，极高风险


class PluginCategory(str, Enum):
    """插件类别"""

    DATA_SOURCE = "data_source"
    STRATEGY = "strategy"
    RISK = "risk"
    VISUALIZATION = "visualization"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    UTILITY = "utility"
    BACKTEST = "backtest"


class PluginManifest(BaseModel):
    """
    插件清单模型

    定义插件的完整元数据、依赖关系、资源限制等信息。
    """

    # 基本信息
    name: str = Field(..., description="插件唯一名称", pattern=r"^[a-z][a-z0-9_]*[a-z0-9]$")
    version: str = Field(..., description="插件版本 (语义化版本)")
    description: str = Field(..., description="插件描述")
    author: str = Field(..., description="插件作者")
    license: str = Field(default="MIT", description="许可证")
    homepage: Optional[str] = Field(default=None, description="项目主页")
    repository: Optional[str] = Field(default=None, description="代码仓库")

    # 分类和标签
    category: PluginCategory = Field(..., description="插件类别")
    tags: List[str] = Field(default_factory=list, description="插件标签")
    keywords: List[str] = Field(default_factory=list, description="关键词")

    # 依赖关系
    dependencies: Dict[str, str] = Field(
        default_factory=dict, description="插件依赖 {plugin_name: version_spec}"
    )
    conflicts: List[str] = Field(default_factory=list, description="冲突的插件列表")
    provides: List[str] = Field(default_factory=list, description="提供的服务/功能")
    requires: List[str] = Field(default_factory=list, description="需要的核心服务")

    # 运行环境
    python_version: str = Field(default=">=3.8", description="Python版本要求")
    platform: List[str] = Field(
        default_factory=lambda: ["linux", "windows", "darwin"], description="支持的平台"
    )

    # 安全和资源
    security_level: SecurityLevel = Field(
        default=SecurityLevel.MEDIUM, description="安全等级"
    )
    max_memory_mb: int = Field(default=512, description="最大内存使用(MB)")
    max_cpu_percent: float = Field(default=50.0, description="最大CPU使用率(%)")
    max_disk_mb: int = Field(default=1024, description="最大磁盘使用(MB)")

    # 插件特定配置
    entry_point: str = Field(default="plugin.py", description="插件入口文件")
    config_schema: Optional[Dict[str, Any]] = Field(default=None, description="配置模式定义")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    api_version: str = Field(default="v1", description="API版本")
    min_framework_version: str = Field(default="5.0.0", description="最小框架版本")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """验证插件名称"""
        if len(v) < 3 or len(v) > 50:
            raise ValueError("插件名称长度必须在3-50之间")
        return v

    @field_validator("version")
    @classmethod
    def validate_version(cls, v):
        """验证版本格式"""
        from packaging import version

        try:
            version.parse(v)
        except Exception:
            raise ValueError(f"无效的版本格式: {v}")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v):
        """验证依赖版本规范"""
        from packaging import specifiers

        for dep_name, version_spec in v.items():
            try:
                specifiers.SpecifierSet(version_spec)
            except Exception:
                raise ValueError(f"无效的版本规范 {dep_name}: {version_spec}")
        return v

    @field_validator("max_cpu_percent")
    @classmethod
    def validate_cpu_percent(cls, v):
        """验证CPU使用率"""
        if not 0 < v <= 100:
            raise ValueError("CPU使用率必须在0-100之间")
        return v

    def is_compatible_with(self, other: "PluginManifest") -> bool:
        """检查与另一个插件的兼容性"""
        # 检查冲突
        if other.name in self.conflicts or self.name in other.conflicts:
            return False

        # 检查提供的服务是否冲突
        self_provides = set(self.provides)
        other_provides = set(other.provides)
        if self_provides & other_provides:
            return False

        return True

    def get_resource_footprint(self) -> Dict[str, float]:
        """获取资源占用估算"""
        return {
            "memory_mb": self.max_memory_mb,
            "cpu_percent": self.max_cpu_percent,
            "disk_mb": self.max_disk_mb,
        }


class ManifestValidator:
    """
    插件清单验证器

    提供插件清单的加载、验证和保存功能。
    """

    @staticmethod
    def load_from_file(manifest_path: Path) -> PluginManifest:
        """从文件加载插件清单"""
        if not manifest_path.exists():
            raise FileNotFoundError(f"插件清单文件不存在: {manifest_path}")

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                if (
                    manifest_path.suffix.lower() == ".yaml"
                    or manifest_path.suffix.lower() == ".yml"
                ):
                    data = yaml.safe_load(f)
                elif manifest_path.suffix.lower() == ".json":
                    data = json.load(f)
                else:
                    raise ValueError(f"不支持的清单文件格式: {manifest_path.suffix}")

            return PluginManifest(**data)

        except Exception as e:
            raise ValueError(f"加载插件清单失败 {manifest_path}: {e}")

    @staticmethod
    def save_to_file(
        manifest: PluginManifest, manifest_path: Path, format: str = "yaml"
    ) -> None:
        """保存插件清单到文件"""
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用model_dump()获取纯Python字典，避免Pydantic对象序列化问题
        data = manifest.model_dump()

        # 处理特殊类型对象
        def convert_objects_to_serializable(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, (SecurityLevel, PluginCategory)):
                return obj.value  # 枚举转换为字符串值
            elif isinstance(obj, dict):
                return {k: convert_objects_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_objects_to_serializable(item) for item in obj]
            return obj

        data = convert_objects_to_serializable(data)

        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                if format.lower() == "yaml":
                    yaml.dump(
                        data, f, default_flow_style=False, allow_unicode=True, indent=2
                    )
                elif format.lower() == "json":
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    raise ValueError(f"不支持的保存格式: {format}")

        except Exception as e:
            raise ValueError(f"保存插件清单失败 {manifest_path}: {e}")

    @staticmethod
    def validate_manifest(manifest: PluginManifest) -> List[str]:
        """验证插件清单，返回验证错误列表"""
        errors = []

        # 检查必需字段
        if not manifest.name:
            errors.append("插件名称不能为空")

        if not manifest.version:
            errors.append("插件版本不能为空")

        if not manifest.description:
            errors.append("插件描述不能为空")

        if not manifest.author:
            errors.append("插件作者不能为空")

        # 检查循环依赖（自己依赖自己）
        if manifest.name in manifest.dependencies:
            errors.append("插件不能依赖自己")

        # 检查资源限制的合理性
        if manifest.max_memory_mb <= 0:
            errors.append("内存限制必须大于0")

        if manifest.max_disk_mb <= 0:
            errors.append("磁盘限制必须大于0")

        # 检查安全等级和资源的匹配性
        if (
            manifest.security_level == SecurityLevel.LOW
            and manifest.max_memory_mb > 256
        ):
            errors.append("低安全等级插件的内存使用不应超过256MB")

        if (
            manifest.security_level == SecurityLevel.CRITICAL
            and manifest.max_cpu_percent > 80
        ):
            errors.append("关键插件的CPU使用率不应超过80%")

        return errors

    @staticmethod
    def create_template(plugin_name: str, category: PluginCategory) -> PluginManifest:
        """创建插件清单模板"""
        return PluginManifest(
            name=plugin_name,
            version="1.0.0",
            description=f"{plugin_name} 插件",
            author="SimTradeLab Team",
            category=category,
            tags=[category.value],
            dependencies={},
            provides=[],
            requires=["event_bus", "config_center"],
        )
