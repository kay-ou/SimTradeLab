# -*- coding: utf-8 -*-
"""
EventBus CloudEvent 支持测试用例

测试增强版EventBus对CloudEvent的支持，包括：
- CloudEvent发布和处理
- 向后兼容性
- 事件类型自动检测
- 优先级处理
- 异步事件处理
"""

import asyncio

import pytest

from simtradelab.core.event_bus import Event, EventBus, EventPriority
from simtradelab.core.events.cloud_event import CloudEvent
from simtradelab.core.events.contracts import (
    CoreEventContracts,
    create_plugin_loaded_event,
    create_system_start_event,
)


class TestEventBusCloudEventSupport:
    """EventBus CloudEvent支持测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.event_bus = EventBus(max_workers=2, max_history=100)
        self.received_events = []
        self.cloud_event_handler_called = False
        self.legacy_handler_called = False

    def teardown_method(self):
        """每个测试方法后的清理"""
        self.event_bus.shutdown()

    def test_publish_cloud_event_basic(self):
        """测试基本CloudEvent发布"""

        # 创建处理器
        def handler(event: CloudEvent):
            self.received_events.append(event)
            return "cloud_result"

        # 订阅事件
        self.event_bus.subscribe("test.cloud.event", handler)

        # 创建并发布CloudEvent
        cloud_event = CloudEvent(
            type="test.cloud.event", source="TestSource", data={"message": "test"}
        )

        results = self.event_bus.publish_cloud_event(cloud_event)

        assert len(results) == 1
        assert results[0] == "cloud_result"
        assert len(self.received_events) == 1
        assert isinstance(self.received_events[0], CloudEvent)
        assert self.received_events[0].type == "test.cloud.event"
        assert self.received_events[0].data["message"] == "test"

    def test_legacy_publish_creates_cloud_event(self):
        """测试旧版publish方法创建CloudEvent"""

        def handler(event: CloudEvent):
            self.received_events.append(event)
            return "converted_result"

        self.event_bus.subscribe("test.legacy.event", handler)

        # 使用旧版publish方法
        results = self.event_bus.publish(
            "test.legacy.event",
            data={"legacy": "data"},
            source="LegacySource",
            priority=EventPriority.HIGH,
        )

        assert len(results) == 1
        assert results[0] == "converted_result"
        assert len(self.received_events) == 1

        received = self.received_events[0]
        assert isinstance(received, CloudEvent)
        assert received.type == "test.legacy.event"
        assert received.source == "LegacySource"
        assert received.data["legacy"] == "data"
        assert received.priority == 3  # EventPriority.HIGH.value

    def test_handler_type_detection(self):
        """测试处理器类型自动检测"""

        # CloudEvent处理器
        def cloud_handler(event: CloudEvent):
            self.cloud_event_handler_called = True
            assert isinstance(event, CloudEvent)
            return "cloud"

        # 旧版Event处理器
        def legacy_handler(event: Event):
            self.legacy_handler_called = True
            assert isinstance(event, Event)
            return "legacy"

        # 无类型注解处理器（默认使用旧版）
        def untyped_handler(event):
            assert isinstance(event, Event)
            return "untyped"

        # 订阅相同事件类型
        self.event_bus.subscribe("test.mixed.event", cloud_handler)
        self.event_bus.subscribe("test.mixed.event", legacy_handler)
        self.event_bus.subscribe("test.mixed.event", untyped_handler)

        # 发布CloudEvent
        cloud_event = CloudEvent(type="test.mixed.event", source="TestSource")

        results = self.event_bus.publish_cloud_event(cloud_event)

        assert len(results) == 3
        assert "cloud" in results
        assert "legacy" in results
        assert "untyped" in results
        assert self.cloud_event_handler_called
        assert self.legacy_handler_called

    def test_event_priority_handling(self):
        """测试事件优先级处理"""
        call_order = []

        def high_priority_handler(event):
            call_order.append("high")
            return "high"

        def normal_priority_handler(event):
            call_order.append("normal")
            return "normal"

        def low_priority_handler(event):
            call_order.append("low")
            return "low"

        # 以不同优先级订阅
        self.event_bus.subscribe(
            "test.priority", high_priority_handler, EventPriority.HIGH
        )
        self.event_bus.subscribe(
            "test.priority", normal_priority_handler, EventPriority.NORMAL
        )
        self.event_bus.subscribe(
            "test.priority", low_priority_handler, EventPriority.LOW
        )

        # 发布高优先级CloudEvent
        cloud_event = CloudEvent(
            type="test.priority", source="TestSource", priority=2  # 高优先级
        )

        results = self.event_bus.publish_cloud_event(cloud_event)

        # 验证调用顺序（高优先级先执行）
        assert call_order == ["high", "normal", "low"]
        assert len(results) == 3

    def test_event_history_compatibility(self):
        """测试事件历史兼容性"""
        # 发布CloudEvent
        cloud_event = CloudEvent(
            type="test.history", source="TestSource", data={"test": "data"}
        )

        self.event_bus.publish_cloud_event(cloud_event)

        # 检查历史记录
        history = self.event_bus.get_event_history()
        assert len(history) == 1

        # 历史中应该是转换后的旧格式Event
        historical_event = history[0]
        assert isinstance(historical_event, Event)
        assert historical_event.type == "test.history"
        assert historical_event.source == "TestSource"
        assert historical_event.data["test"] == "data"
        assert historical_event.event_id == cloud_event.id

    def test_event_filtering_with_cloud_events(self):
        """测试CloudEvent的事件过滤"""
        filtered_events = []

        def handler(event):
            filtered_events.append(event)
            return "handled"

        def filter_func(event: Event) -> bool:
            # 只接受包含特定数据的事件
            return event.data and event.data.get("allowed") is True

        self.event_bus.subscribe("test.filter", handler, filter_func=filter_func)

        # 发布不符合过滤条件的事件
        cloud_event1 = CloudEvent(
            type="test.filter", source="TestSource", data={"allowed": False}
        )

        results1 = self.event_bus.publish_cloud_event(cloud_event1)
        assert len(results1) == 0
        assert len(filtered_events) == 0

        # 发布符合过滤条件的事件
        cloud_event2 = CloudEvent(
            type="test.filter", source="TestSource", data={"allowed": True}
        )

        results2 = self.event_bus.publish_cloud_event(cloud_event2)
        assert len(results2) == 1
        assert results2[0] == "handled"
        assert len(filtered_events) == 1

    def test_once_subscription_with_cloud_events(self):
        """测试CloudEvent的一次性订阅"""
        call_count = 0

        def once_handler(event):
            nonlocal call_count
            call_count += 1
            return f"call_{call_count}"

        self.event_bus.subscribe("test.once", once_handler, once=True)

        # 第一次发布
        cloud_event1 = CloudEvent(type="test.once", source="TestSource")
        results1 = self.event_bus.publish_cloud_event(cloud_event1)

        assert len(results1) == 1
        assert results1[0] == "call_1"
        assert call_count == 1

        # 第二次发布，应该不被处理
        cloud_event2 = CloudEvent(type="test.once", source="TestSource")
        results2 = self.event_bus.publish_cloud_event(cloud_event2)

        assert len(results2) == 0
        assert call_count == 1  # 没有增加

    @pytest.mark.asyncio
    async def test_async_cloud_event_publishing(self):
        """测试异步CloudEvent发布"""
        async_results = []
        sync_results = []

        async def async_handler(event: CloudEvent):
            await asyncio.sleep(0.01)  # 模拟异步操作
            async_results.append("async_result")
            return "async_handled"

        def sync_handler(event: CloudEvent):
            sync_results.append("sync_result")
            return "sync_handled"

        self.event_bus.subscribe("test.async", async_handler)
        self.event_bus.subscribe("test.async", sync_handler)

        cloud_event = CloudEvent(type="test.async", source="TestSource")

        # 使用异步发布方法
        results = await self.event_bus.publish_cloud_event_async(cloud_event)

        assert len(results) == 2
        assert "async_handled" in results
        assert "sync_handled" in results
        assert len(async_results) == 1
        assert len(sync_results) == 1

    def test_cloud_event_with_contracts(self):
        """测试CloudEvent与事件契约的集成"""
        received_events = []

        def system_handler(event: CloudEvent):
            received_events.append(event)
            return "system_handled"

        def plugin_handler(event: CloudEvent):
            received_events.append(event)
            return "plugin_handled"

        # 订阅系统和插件事件
        self.event_bus.subscribe(CoreEventContracts.SYSTEM_START, system_handler)
        self.event_bus.subscribe(CoreEventContracts.PLUGIN_LOADED, plugin_handler)

        # 使用契约工厂创建事件
        system_event = create_system_start_event(version="5.0")
        plugin_event = create_plugin_loaded_event("TestPlugin", "1.0.0")

        # 发布事件
        results1 = self.event_bus.publish_cloud_event(system_event)
        results2 = self.event_bus.publish_cloud_event(plugin_event)

        assert len(results1) == 1
        assert results1[0] == "system_handled"
        assert len(results2) == 1
        assert results2[0] == "plugin_handled"
        assert len(received_events) == 2

        # 验证事件内容
        system_received = received_events[0]
        assert system_received.type == CoreEventContracts.SYSTEM_START
        assert system_received.data["version"] == "5.0"
        assert system_received.priority == 1  # 系统事件高优先级

        plugin_received = received_events[1]
        assert plugin_received.type == CoreEventContracts.PLUGIN_LOADED
        assert plugin_received.data["plugin_name"] == "TestPlugin"

    def test_error_handling_in_cloud_event_processing(self):
        """测试CloudEvent处理中的错误处理"""
        successful_calls = []

        def failing_handler(event: CloudEvent):
            raise ValueError("Handler error")

        def successful_handler(event: CloudEvent):
            successful_calls.append("success")
            return "success"

        self.event_bus.subscribe("test.error", failing_handler)
        self.event_bus.subscribe("test.error", successful_handler)

        cloud_event = CloudEvent(type="test.error", source="TestSource")

        # 发布事件，一个处理器失败，一个成功
        results = self.event_bus.publish_cloud_event(cloud_event)

        assert len(results) == 2
        assert None in results  # 失败的处理器返回None
        assert "success" in results
        assert len(successful_calls) == 1

        # 检查统计信息
        stats = self.event_bus.get_stats()
        assert stats["events_failed"] > 0
        assert stats["events_processed"] > 0

    def test_mixed_event_format_compatibility(self):
        """测试混合事件格式兼容性"""
        cloud_events = []
        legacy_events = []

        def cloud_handler(event: CloudEvent):
            cloud_events.append(event)
            return "cloud"

        def legacy_handler(event: Event):
            legacy_events.append(event)
            return "legacy"

        self.event_bus.subscribe("mixed.event", cloud_handler)
        self.event_bus.subscribe("mixed.event", legacy_handler)

        # 发布CloudEvent
        cloud_event = CloudEvent(
            type="mixed.event", source="CloudSource", data={"format": "cloud"}
        )

        results = self.event_bus.publish_cloud_event(cloud_event)

        assert len(results) == 2
        assert "cloud" in results
        assert "legacy" in results

        # 验证两种处理器都被调用
        assert len(cloud_events) == 1
        assert len(legacy_events) == 1

        # CloudEvent处理器收到原始CloudEvent
        assert isinstance(cloud_events[0], CloudEvent)
        assert cloud_events[0].data["format"] == "cloud"

        # Legacy处理器收到转换后的Event
        assert isinstance(legacy_events[0], Event)
        assert legacy_events[0].data["format"] == "cloud"
        assert legacy_events[0].type == "mixed.event"


class TestEventBusCloudEventEdgeCases:
    """EventBus CloudEvent边界情况测试"""

    def setup_method(self):
        self.event_bus = EventBus(max_workers=1, max_history=10)

    def teardown_method(self):
        self.event_bus.shutdown()

    def test_cloud_event_with_none_data(self):
        """测试数据为None的CloudEvent"""
        received_events = []

        def handler(event: CloudEvent):
            received_events.append(event)
            return "handled"

        self.event_bus.subscribe("test.none.data", handler)

        cloud_event = CloudEvent(type="test.none.data", source="TestSource", data=None)

        results = self.event_bus.publish_cloud_event(cloud_event)

        assert len(results) == 1
        assert results[0] == "handled"
        assert len(received_events) == 1
        assert received_events[0].data is None

    def test_cloud_event_with_complex_data(self):
        """测试复杂数据结构的CloudEvent"""
        complex_data = {
            "nested": {
                "array": [1, 2, 3],
                "dict": {"key": "value"},
                "null": None,
                "boolean": True,
            },
            "list": [{"item": i} for i in range(5)],
        }

        received_data = []

        def handler(event: CloudEvent):
            received_data.append(event.data)
            return "complex_handled"

        self.event_bus.subscribe("test.complex", handler)

        cloud_event = CloudEvent(
            type="test.complex", source="TestSource", data=complex_data
        )

        results = self.event_bus.publish_cloud_event(cloud_event)

        assert len(results) == 1
        assert len(received_data) == 1
        assert received_data[0] == complex_data

    def test_cloud_event_shutdown_handling(self):
        """测试EventBus关闭时的CloudEvent处理"""
        # 关闭EventBus
        self.event_bus.shutdown()

        cloud_event = CloudEvent(type="test.shutdown", source="TestSource")

        # 尝试发布事件应该抛出异常
        with pytest.raises(Exception):
            self.event_bus.publish_cloud_event(cloud_event)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
