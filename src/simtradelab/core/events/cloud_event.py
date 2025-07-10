# -*- coding: utf-8 -*-
"""
CloudEvent 标准事件模型

实现符合 CNCF CloudEvents v1.0 规范的标准化事件结构，
支持事件优先级、版本控制、关联追踪等v5.0增强特性。
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class CloudEvent(BaseModel):
    """
    标准云事件模型 (遵循 CNCF CloudEvents 规范)

    v5.0 增强版本，支持事件优先级、版本控制和关联追踪。
    提供统一的插件间通信标准，确保事件结构的一致性和可追溯性。

    参考: https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md
    """

    # CNCF CloudEvents 必需字段
    specversion: str = Field(default="1.0", description="CloudEvents规范版本")
    type: str = Field(..., description="事件类型, 如 'com.simtradelab.plugin.loaded'")
    source: str = Field(..., description="事件来源, 如 'PluginLifecycleManager'")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="唯一事件ID")
    time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="事件发生时间"
    )

    # CNCF CloudEvents 可选字段
    datacontenttype: str = Field(default="application/json", description="数据内容类型")
    dataschema: Optional[str] = Field(default=None, description="数据架构URI")
    subject: Optional[str] = Field(default=None, description="事件主题，描述事件关联的上下文")
    data: Optional[Dict[str, Any]] = Field(default=None, description="事件的具体负载数据")

    # v5.0 SimTradeLab 扩展字段
    priority: int = Field(default=5, ge=1, le=10, description="事件优先级，1最高，10最低")
    version: str = Field(default="1.0", description="事件结构版本")
    correlation_id: Optional[str] = Field(default=None, description="关联ID，用于追踪事件链")
    tags: Dict[str, str] = Field(default_factory=dict, description="事件标签，用于分类和过滤")

    # 内部字段
    created_at_internal: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="事件创建时间（内部字段）",
        exclude=True,
    )
    sequence_internal: Optional[int] = Field(
        default=None, description="事件序列号（内部字段）", exclude=True
    )

    # Pydantic V2 配置
    model_config = ConfigDict(
        extra="allow",  # 允许额外字段，兼容CloudEvents扩展
        validate_assignment=True,  # 验证赋值
    )

    @field_serializer("time")
    def serialize_time(self, value: datetime) -> str:
        """序列化时间为ISO格式"""
        return value.isoformat()

    @field_validator("type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """验证事件类型格式"""
        if not v:
            raise ValueError("事件类型不能为空")

        # 建议使用反向DNS命名
        if not v.startswith("com.simtradelab."):
            # 警告但不阻止，允许灵活性
            pass

        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """验证事件源格式"""
        if not v:
            raise ValueError("事件源不能为空")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """验证优先级范围"""
        if v < 1 or v > 10:
            raise ValueError("优先级必须在1-10之间")
        return v

    @field_validator("correlation_id")
    @classmethod
    def validate_correlation_id(cls, v: Optional[str]) -> Optional[str]:
        """验证关联ID格式"""
        if v is not None and not v.strip():
            raise ValueError("关联ID不能为空字符串")
        return v

    def add_tag(self, key: str, value: str) -> None:
        """
        添加事件标签

        Args:
            key: 标签键
            value: 标签值
        """
        self.tags[key] = value

    def remove_tag(self, key: str) -> Optional[str]:
        """
        移除事件标签

        Args:
            key: 标签键

        Returns:
            被移除的标签值，如果不存在则返回None
        """
        return self.tags.pop(key, None)

    def has_tag(self, key: str, value: Optional[str] = None) -> bool:
        """
        检查是否有指定标签

        Args:
            key: 标签键
            value: 标签值，如果为None则只检查键是否存在

        Returns:
            是否存在指定标签
        """
        if key not in self.tags:
            return False

        if value is None:
            return True

        return self.tags[key] == value

    def set_correlation_id(self, correlation_id: str) -> None:
        """
        设置关联ID，用于事件链追踪

        Args:
            correlation_id: 关联ID
        """
        self.correlation_id = correlation_id

    def create_correlated_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> "CloudEvent":
        """
        创建具有相同关联ID的关联事件

        Args:
            event_type: 新事件类型
            data: 新事件数据
            source: 新事件源，如果为None则使用当前事件源

        Returns:
            新的关联事件
        """
        return CloudEvent(
            type=event_type,
            source=source or self.source,
            data=data,
            correlation_id=self.correlation_id,
            priority=self.priority,
            tags=self.tags.copy(),
            version=self.version,
        )

    def get_age_seconds(self) -> float:
        """
        获取事件年龄（秒）

        Returns:
            从事件创建到现在的秒数
        """
        return (datetime.now(timezone.utc) - self.created_at_internal).total_seconds()

    def is_expired(self, max_age_seconds: float) -> bool:
        """
        检查事件是否过期

        Args:
            max_age_seconds: 最大年龄（秒）

        Returns:
            是否过期
        """
        return self.get_age_seconds() > max_age_seconds

    def to_legacy_event(self) -> Dict[str, Any]:
        """
        转换为旧版Event格式，用于向后兼容

        Returns:
            旧版Event格式的字典
        """
        return {
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.time.timestamp(),
            "event_id": self.id,
            "metadata": {
                "priority": self.priority,
                "correlation_id": self.correlation_id,
                "tags": self.tags,
                "version": self.version,
                "specversion": self.specversion,
                "datacontenttype": self.datacontenttype,
                "subject": self.subject,
                "dataschema": self.dataschema,
            },
        }

    @classmethod
    def from_legacy_event(cls, legacy_event: Dict[str, Any]) -> "CloudEvent":
        """
        从旧版Event格式创建CloudEvent

        Args:
            legacy_event: 旧版Event格式的字典

        Returns:
            CloudEvent实例
        """
        metadata = legacy_event.get("metadata", {})

        # 处理时间戳
        time_value = legacy_event.get("timestamp")
        if isinstance(time_value, (int, float)):
            time_value = datetime.fromtimestamp(time_value, tz=timezone.utc)
        elif time_value is None:
            time_value = datetime.now(timezone.utc)

        return cls(
            type=legacy_event.get("type", "unknown"),
            source=legacy_event.get("source", "unknown"),
            id=legacy_event.get("event_id", str(uuid.uuid4())),
            time=time_value,
            data=legacy_event.get("data"),
            priority=metadata.get("priority", 5),
            correlation_id=metadata.get("correlation_id"),
            tags=metadata.get("tags", {}),
            version=metadata.get("version", "1.0"),
            specversion=metadata.get("specversion", "1.0"),
            datacontenttype=metadata.get("datacontenttype", "application/json"),
            subject=metadata.get("subject"),
            dataschema=metadata.get("dataschema"),
        )

    def __str__(self) -> str:
        """字符串表示"""
        return f"CloudEvent(type={self.type}, source={self.source}, id={self.id})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return (
            f"CloudEvent(type='{self.type}', source='{self.source}', "
            f"id='{self.id}', priority={self.priority}, time='{self.time}')"
        )
