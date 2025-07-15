# -*- coding: utf-8 -*-
"""
CloudEvent 测试用例

测试 CloudEvent 标准事件模型的功能性、一致性和兼容性。
确保所有功能符合 CNCF CloudEvents v1.0 规范要求。
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from simtradelab.core.events.cloud_event import CloudEvent
from simtradelab.core.events.contracts import (
    CoreEventContracts,
    create_config_changed_event,
    create_order_created_event,
    create_plugin_loaded_event,
    create_risk_alert_event,
    create_system_start_event,
    get_event_priority,
    validate_event_data,
)


class TestCloudEvent:
    """CloudEvent基础功能测试"""

    def test_create_minimal_cloud_event(self):
        """测试创建最小CloudEvent"""
        event = CloudEvent(type="com.simtradelab.test.event", source="TestSource")

        assert event.type == "com.simtradelab.test.event"
        assert event.source == "TestSource"
        assert event.specversion == "1.0"
        assert event.datacontenttype == "application/json"
        assert event.priority == 5
        assert isinstance(event.id, str)
        assert isinstance(event.time, datetime)
        assert event.time.tzinfo is not None

    def test_create_full_cloud_event(self):
        """测试创建完整CloudEvent"""
        test_time = datetime.now(timezone.utc)
        test_data = {"test": "data", "value": 123}
        test_tags = {"category": "test", "environment": "dev"}

        event = CloudEvent(
            type="com.simtradelab.test.full",
            source="FullTestSource",
            id="test-event-id",
            time=test_time,
            data=test_data,
            priority=2,
            correlation_id="test-correlation",
            tags=test_tags,
            subject="test-subject",
            dataschema="https://example.com/schema",
        )

        assert event.type == "com.simtradelab.test.full"
        assert event.source == "FullTestSource"
        assert event.id == "test-event-id"
        assert event.time == test_time
        assert event.data == test_data
        assert event.priority == 2
        assert event.correlation_id == "test-correlation"
        assert event.tags == test_tags
        assert event.subject == "test-subject"
        assert event.dataschema == "https://example.com/schema"

    def test_cloud_event_validation(self):
        """测试CloudEvent字段验证"""
        # 测试空事件类型
        with pytest.raises(ValueError, match="事件类型不能为空"):
            CloudEvent(type="", source="TestSource")

        # 测试空事件源
        with pytest.raises(ValueError, match="事件源不能为空"):
            CloudEvent(type="test.event", source="")

        # 测试优先级范围 - 使用Pydantic ValidationError
        with pytest.raises(ValidationError):
            CloudEvent(type="test.event", source="TestSource", priority=0)

        with pytest.raises(ValidationError):
            CloudEvent(type="test.event", source="TestSource", priority=11)

        # 测试空关联ID
        with pytest.raises(ValueError, match="关联ID不能为空字符串"):
            CloudEvent(type="test.event", source="TestSource", correlation_id="  ")

    def test_tag_management(self):
        """测试标签管理功能"""
        event = CloudEvent(type="test.event", source="TestSource")

        # 添加标签
        event.add_tag("category", "test")
        event.add_tag("environment", "dev")

        assert event.has_tag("category")
        assert event.has_tag("category", "test")
        assert event.has_tag("environment", "dev")
        assert not event.has_tag("nonexistent")
        assert not event.has_tag("category", "wrong_value")

        # 移除标签
        removed_value = event.remove_tag("category")
        assert removed_value == "test"
        assert not event.has_tag("category")

        # 移除不存在的标签
        assert event.remove_tag("nonexistent") is None

    def test_correlation_functionality(self):
        """测试关联功能"""
        parent_event = CloudEvent(
            type="parent.event",
            source="ParentSource",
            correlation_id="parent-correlation",
        )

        # 创建关联事件
        child_event = parent_event.create_correlated_event(
            "child.event", data={"child": "data"}
        )

        assert child_event.type == "child.event"
        assert child_event.source == "ParentSource"  # 继承源
        assert child_event.correlation_id == "parent-correlation"
        assert child_event.data == {"child": "data"}
        assert child_event.priority == parent_event.priority

        # 使用不同源创建关联事件
        child_event2 = parent_event.create_correlated_event(
            "child2.event", source="ChildSource"
        )

        assert child_event2.source == "ChildSource"
        assert child_event2.correlation_id == "parent-correlation"

    def test_age_and_expiration(self):
        """测试事件年龄和过期检查"""
        event = CloudEvent(type="test.event", source="TestSource")

        # 测试年龄计算
        age = event.get_age_seconds()
        assert age >= 0
        assert age < 1  # 应该很快

        # 测试过期检查
        assert not event.is_expired(60)  # 1分钟未过期
        assert event.is_expired(0)  # 0秒已过期

    def test_legacy_conversion(self):
        """测试与旧版Event格式的转换"""
        # 创建CloudEvent
        cloud_event = CloudEvent(
            type="test.event",
            source="TestSource",
            data={"test": "value"},
            priority=3,
            correlation_id="test-correlation",
            tags={"category": "test"},
        )

        # 转换为旧格式
        legacy_dict = cloud_event.to_legacy_event()

        assert legacy_dict["type"] == "test.event"
        assert legacy_dict["source"] == "TestSource"
        assert legacy_dict["data"] == {"test": "value"}
        assert legacy_dict["event_id"] == cloud_event.id
        assert isinstance(legacy_dict["timestamp"], float)
        assert legacy_dict["metadata"]["priority"] == 3
        assert legacy_dict["metadata"]["correlation_id"] == "test-correlation"

        # 从旧格式重建CloudEvent
        rebuilt_event = CloudEvent.from_legacy_event(legacy_dict)

        assert rebuilt_event.type == cloud_event.type
        assert rebuilt_event.source == cloud_event.source
        assert rebuilt_event.data == cloud_event.data
        assert rebuilt_event.priority == cloud_event.priority
        assert rebuilt_event.correlation_id == cloud_event.correlation_id

    def test_string_representation(self):
        """测试字符串表示"""
        event = CloudEvent(type="test.event", source="TestSource", id="test-id")

        str_repr = str(event)
        assert "test.event" in str_repr
        assert "TestSource" in str_repr
        assert "test-id" in str_repr

        repr_str = repr(event)
        assert "CloudEvent" in repr_str
        assert "test.event" in repr_str


class TestCoreEventContracts:
    """核心事件契约测试"""

    def test_system_start_event(self):
        """测试系统启动事件"""
        event = create_system_start_event(version="5.0")

        assert event.type == CoreEventContracts.SYSTEM_START
        assert event.source == "CoreEngine"
        assert event.data["version"] == "5.0"
        assert "startup_time" in event.data
        assert "components" in event.data
        assert (
            event.priority
            == CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.SYSTEM_START]
        )
        assert event.has_tag("category", "system")

    def test_plugin_loaded_event(self):
        """测试插件加载事件"""
        event = create_plugin_loaded_event("TestPlugin", "1.0.0", load_time_ms=150.5)

        assert event.type == CoreEventContracts.PLUGIN_LOADED
        assert event.source == "PluginLifecycleManager"
        assert event.data["plugin_name"] == "TestPlugin"
        assert event.data["version"] == "1.0.0"
        assert event.data["load_time_ms"] == 150.5
        assert event.has_tag("plugin", "TestPlugin")

    def test_config_changed_event(self):
        """测试配置变更事件"""
        event = create_config_changed_event(
            plugin="TestPlugin", key="timeout", old_value=30, new_value=60
        )

        assert event.type == CoreEventContracts.CONFIG_CHANGED
        assert event.source == "DynamicConfigCenter"
        assert event.data["plugin"] == "TestPlugin"
        assert event.data["key"] == "timeout"
        assert event.data["old_value"] == 30
        assert event.data["new_value"] == 60
        assert "changed_at" in event.data

    def test_order_created_event(self):
        """测试订单创建事件"""
        event = create_order_created_event(
            order_id="ORD123",
            symbol="AAPL",
            amount=100.0,
            price=150.0,
            strategy="TestStrategy",
        )

        assert event.type == CoreEventContracts.ORDER_CREATED
        assert event.source == "StrategyPlugin"
        assert event.data["order_id"] == "ORD123"
        assert event.data["symbol"] == "AAPL"
        assert event.data["amount"] == 100.0
        assert event.data["price"] == 150.0
        assert event.data["strategy"] == "TestStrategy"
        assert event.has_tag("symbol", "AAPL")

    def test_risk_alert_event(self):
        """测试风险告警事件"""
        event = create_risk_alert_event(
            rule="max_position",
            current_value=95.0,
            threshold=90.0,
            severity="warning",
            description="Position limit approaching",
        )

        assert event.type == CoreEventContracts.RISK_ALERT
        assert event.source == "RiskControlPlugin"
        assert event.data["rule"] == "max_position"
        assert event.data["current_value"] == 95.0
        assert event.data["threshold"] == 90.0
        assert event.data["severity"] == "warning"
        assert event.data["description"] == "Position limit approaching"
        assert event.has_tag("severity", "warning")

    def test_event_priority_mapping(self):
        """测试事件优先级映射"""
        # 测试系统级事件高优先级
        assert get_event_priority(CoreEventContracts.SYSTEM_ERROR) == 1
        assert get_event_priority(CoreEventContracts.RISK_BREACH) == 1

        # 测试交易事件优先级
        assert get_event_priority(CoreEventContracts.ORDER_FILLED) == 2

        # 测试默认优先级
        assert get_event_priority("unknown.event") == 5

    def test_event_data_validation(self):
        """测试事件数据验证"""
        # 测试插件加载事件验证
        valid_plugin_data = {"plugin_name": "Test", "version": "1.0"}
        assert validate_event_data(CoreEventContracts.PLUGIN_LOADED, valid_plugin_data)

        invalid_plugin_data = {"plugin_name": "Test"}  # 缺少version
        assert not validate_event_data(
            CoreEventContracts.PLUGIN_LOADED, invalid_plugin_data
        )

        # 测试订单创建事件验证
        valid_order_data = {"order_id": "123", "symbol": "AAPL", "amount": 100}
        assert validate_event_data(CoreEventContracts.ORDER_CREATED, valid_order_data)

        invalid_order_data = {"order_id": "123", "symbol": "AAPL"}  # 缺少amount
        assert not validate_event_data(
            CoreEventContracts.ORDER_CREATED, invalid_order_data
        )

        # 测试非字典数据
        assert not validate_event_data(CoreEventContracts.PLUGIN_LOADED, "invalid")


class TestCloudEventSerialization:
    """CloudEvent序列化测试"""

    def test_json_serialization(self):
        """测试JSON序列化"""
        event = CloudEvent(
            type="test.event",
            source="TestSource",
            data={"test": "value"},
            tags={"env": "test"},
        )

        # 测试序列化
        json_data = event.model_dump()

        assert json_data["type"] == "test.event"
        assert json_data["source"] == "TestSource"
        assert json_data["data"] == {"test": "value"}
        assert json_data["tags"] == {"env": "test"}

        # 测试反序列化
        reconstructed = CloudEvent.model_validate(json_data)

        assert reconstructed.type == event.type
        assert reconstructed.source == event.source
        assert reconstructed.data == event.data
        assert reconstructed.tags == event.tags

    def test_json_with_datetime(self):
        """测试包含日期时间的JSON序列化"""
        test_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event = CloudEvent(type="test.event", source="TestSource", time=test_time)

        json_str = event.model_dump_json()
        # 应该包含时间戳（Pydantic V2格式）
        assert "2024-01-01T12:00:00+00:00" in json_str

        # 从JSON重建
        reconstructed = CloudEvent.model_validate_json(json_str)
        assert reconstructed.time == test_time


class TestCloudEventEdgeCases:
    """CloudEvent边界情况测试"""

    def test_unicode_support(self):
        """测试Unicode支持"""
        event = CloudEvent(
            type="测试.事件",
            source="测试源",
            data={"消息": "你好世界", "数值": 123},
            tags={"类别": "测试"},
        )

        assert event.type == "测试.事件"
        assert event.source == "测试源"
        assert event.data["消息"] == "你好世界"
        assert event.tags["类别"] == "测试"

    def test_large_data_payload(self):
        """测试大数据负载"""
        large_data = {"items": [f"item_{i}" for i in range(1000)]}

        event = CloudEvent(type="test.large", source="TestSource", data=large_data)

        assert len(event.data["items"]) == 1000
        assert event.data["items"][0] == "item_0"
        assert event.data["items"][-1] == "item_999"

    def test_none_values(self):
        """测试None值处理"""
        event = CloudEvent(
            type="test.event",
            source="TestSource",
            data=None,
            subject=None,
            dataschema=None,
            correlation_id=None,
        )

        assert event.data is None
        assert event.subject is None
        assert event.dataschema is None
        assert event.correlation_id is None

    def test_extra_fields(self):
        """测试额外字段支持（CloudEvents扩展）"""
        event_data = {
            "type": "test.event",
            "source": "TestSource",
            "custom_field": "custom_value",
            "another_extension": {"nested": "data"},
        }

        event = CloudEvent.model_validate(event_data)

        assert hasattr(event, "custom_field")
        assert event.custom_field == "custom_value"
        assert hasattr(event, "another_extension")
        assert event.another_extension == {"nested": "data"}


class TestCloudEventAdditional:
    """额外的CloudEvent测试用例，提升覆盖率"""

    def test_cloud_event_field_serialization(self):
        """测试CloudEvent字段序列化"""
        event = CloudEvent(
            type="com.simtradelab.test.serialization",
            source="TestSource",
            time=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            priority=3,
            tags={"env": "test", "version": "1.0"},
        )

        # 测试模型转换为字典
        event_dict = event.model_dump()
        assert event_dict["type"] == "com.simtradelab.test.serialization"
        assert event_dict["source"] == "TestSource"
        assert event_dict["priority"] == 3
        assert event_dict["tags"] == {"env": "test", "version": "1.0"}

        # 测试JSON序列化
        json_str = event.model_dump_json()
        assert "com.simtradelab.test.serialization" in json_str
        assert "TestSource" in json_str

    def test_cloud_event_validation_priority_bounds(self):
        """测试priority字段边界值验证"""
        # 测试最小值
        event_min = CloudEvent(
            type="test.priority.min", source="TestSource", priority=1
        )
        assert event_min.priority == 1

        # 测试最大值
        event_max = CloudEvent(
            type="test.priority.max", source="TestSource", priority=10
        )
        assert event_max.priority == 10

        # 测试超出范围的值
        with pytest.raises(ValidationError):
            CloudEvent(
                type="test.priority.invalid", source="TestSource", priority=0  # 小于最小值
            )

        with pytest.raises(ValidationError):
            CloudEvent(
                type="test.priority.invalid", source="TestSource", priority=11  # 大于最大值
            )

    def test_cloud_event_optional_fields(self):
        """测试可选字段的行为"""
        event = CloudEvent(type="com.simtradelab.test.optional", source="TestSource")

        # 验证可选字段的默认值
        assert event.dataschema is None
        assert event.subject is None
        assert event.data is None
        assert event.correlation_id is None
        assert event.tags == {}

        # 设置可选字段
        event.dataschema = "https://schema.example.com/event"
        event.subject = "test-subject"
        event.data = {"key": "value"}
        event.correlation_id = "test-correlation"
        event.tags = {"category": "test"}

        assert event.dataschema == "https://schema.example.com/event"
        assert event.subject == "test-subject"
        assert event.data == {"key": "value"}
        assert event.correlation_id == "test-correlation"
        assert event.tags == {"category": "test"}

    def test_cloud_event_required_fields_validation(self):
        """测试必需字段验证"""
        # 缺少type字段
        with pytest.raises(ValidationError):
            CloudEvent(source="TestSource")

        # 缺少source字段
        with pytest.raises(ValidationError):
            CloudEvent(type="com.simtradelab.test.missing")

    def test_cloud_event_time_field_behavior(self):
        """测试时间字段行为"""
        # 测试默认时间生成
        event1 = CloudEvent(type="test.time.default", source="TestSource")
        event2 = CloudEvent(type="test.time.default", source="TestSource")

        # 两个事件的时间应该不同（虽然可能很接近）
        assert event1.time.tzinfo is not None
        assert event2.time.tzinfo is not None

        # 测试指定时间
        specific_time = datetime(2023, 6, 15, 10, 30, 45, tzinfo=timezone.utc)
        event3 = CloudEvent(
            type="test.time.specific", source="TestSource", time=specific_time
        )
        assert event3.time == specific_time

    def test_cloud_event_id_uniqueness(self):
        """测试ID字段唯一性"""
        event1 = CloudEvent(type="test.id.unique", source="TestSource")
        event2 = CloudEvent(type="test.id.unique", source="TestSource")

        # 两个事件的ID应该不同
        assert event1.id != event2.id
        assert isinstance(event1.id, str)
        assert isinstance(event2.id, str)

        # 测试自定义ID
        custom_id = "custom-event-id-123"
        event3 = CloudEvent(type="test.id.custom", source="TestSource", id=custom_id)
        assert event3.id == custom_id

    def test_cloud_event_model_config(self):
        """测试模型配置"""
        event = CloudEvent(type="test.config", source="TestSource")

        # 验证模型配置存在
        assert hasattr(event, "model_config")

        # 测试模型验证
        assert event.model_validate(
            {"type": "test.validate", "source": "ValidateSource"}
        )

    def test_cloud_event_copy_and_modify(self):
        """测试事件复制和修改"""
        original_event = CloudEvent(
            type="test.original",
            source="OriginalSource",
            priority=5,
            tags={"original": "true"},
        )

        # 复制事件并修改
        modified_event = original_event.model_copy(
            update={
                "type": "test.modified",
                "priority": 8,
                "tags": {"modified": "true"},
            }
        )

        # 验证原事件未被修改
        assert original_event.type == "test.original"
        assert original_event.priority == 5
        assert original_event.tags == {"original": "true"}

        # 验证修改后的事件
        assert modified_event.type == "test.modified"
        assert modified_event.priority == 8
        assert modified_event.tags == {"modified": "true"}
        assert modified_event.source == "OriginalSource"  # 未修改的字段保持不变


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
