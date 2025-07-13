# -*- coding: utf-8 -*-
"""
EventBus CloudEvent标准测试

测试完全基于CloudEvent标准的事件总线功能。
"""

import asyncio
import pytest

from simtradelab.core.event_bus import EventBus
from simtradelab.core.events.cloud_event import CloudEvent


class TestCloudEventBus:
    """测试CloudEvent标准事件总线"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus(max_workers=2, max_history=100)
        yield bus
        bus.shutdown()

    def test_cloud_event_publish_and_subscribe(self, event_bus):
        """测试CloudEvent发布和订阅基础功能"""
        received_events = []

        def handler(event: CloudEvent):
            received_events.append(event)

        # 订阅事件
        sub_id = event_bus.subscribe("test.event", handler)
        assert sub_id

        # 创建并发布CloudEvent
        cloud_event = CloudEvent(
            type="test.event",
            source="test_source",
            data={"message": "hello world"},
            priority=5,
            tags={"env": "test"}
        )

        event_bus.publish_cloud_event(cloud_event)

        # 验证事件被处理
        assert len(received_events) == 1
        assert received_events[0].type == "test.event"
        assert received_events[0].data is not None
        assert received_events[0].data["message"] == "hello world"
        assert received_events[0].priority == 5
        assert received_events[0].tags["env"] == "test"

    def test_convenient_publish_method(self, event_bus):
        """测试便捷的publish方法"""
        received_events = []

        def handler(event: CloudEvent):
            received_events.append(event)

        event_bus.subscribe("convenient.test", handler)

        # 使用便捷方法发布
        event_bus.publish(
            "convenient.test",
            data={"value": 42},
            source="test_source",
            priority=3,
            tags={"type": "test"}
        )

        assert len(received_events) == 1
        event = received_events[0]
        assert event.type == "convenient.test"
        assert event.data is not None
        assert event.data["value"] == 42
        assert event.priority == 3
        assert event.tags["type"] == "test"

    def test_event_priority_ordering(self, event_bus):
        """测试事件优先级排序"""
        execution_order = []

        def high_priority_handler(event: CloudEvent):
            execution_order.append("high")

        def normal_priority_handler(event: CloudEvent):
            execution_order.append("normal")

        def low_priority_handler(event: CloudEvent):
            execution_order.append("low")

        # 按不同优先级订阅（数字越小优先级越高）
        event_bus.subscribe("priority.test", low_priority_handler, priority=8)
        event_bus.subscribe("priority.test", high_priority_handler, priority=1)
        event_bus.subscribe("priority.test", normal_priority_handler, priority=5)

        # 发布事件
        event_bus.publish("priority.test", data={"test": "priority"})

        # 验证执行顺序（高优先级先执行）
        assert execution_order == ["high", "normal", "low"]

    def test_event_filtering(self, event_bus):
        """测试事件过滤功能"""
        received_events = []

        def filter_func(event: CloudEvent) -> bool:
            return event.data is not None and event.data.get("important", False)

        def handler(event: CloudEvent):
            received_events.append(event)

        # 订阅带过滤器的事件
        event_bus.subscribe("filtered.test", handler, filter_func=filter_func)

        # 发布两个事件，一个应该被过滤掉
        event_bus.publish("filtered.test", data={"important": False})
        event_bus.publish("filtered.test", data={"important": True})

        # 只有重要的事件被处理
        assert len(received_events) == 1
        assert received_events[0].data["important"] is True

    @pytest.mark.asyncio
    async def test_async_event_handling(self, event_bus):
        """测试异步事件处理"""
        received_events = []

        async def async_handler(event: CloudEvent):
            await asyncio.sleep(0.01)  # 模拟异步操作
            received_events.append(event)

        # 订阅异步处理器
        event_bus.subscribe("async.test", async_handler)

        # 异步发布事件
        await event_bus.publish_cloud_event_async(
            CloudEvent(
                type="async.test",
                source="async_source",
                data={"async": True}
            )
        )

        assert len(received_events) == 1
        assert received_events[0].data is not None
        assert received_events[0].data["async"] is True

    def test_once_subscription(self, event_bus):
        """测试一次性订阅"""
        call_count = 0

        def once_handler(event: CloudEvent):
            nonlocal call_count
            call_count += 1

        # 订阅一次性事件
        event_bus.subscribe("once.test", once_handler, once=True)

        # 发布多次事件
        event_bus.publish("once.test", data={"count": 1})
        event_bus.publish("once.test", data={"count": 2})

        # 只被调用一次
        assert call_count == 1

    def test_global_filter(self, event_bus):
        """测试全局过滤器"""
        received_events = []

        def handler(event: CloudEvent):
            received_events.append(event)

        def global_filter(event: CloudEvent) -> bool:
            return not event.has_tag("blocked")

        # 添加全局过滤器
        event_bus.add_global_filter(global_filter)
        event_bus.subscribe("filter.test", handler)

        # 发布被阻止的事件
        blocked_event = CloudEvent(
            type="filter.test",
            source="test",
            data={"message": "blocked"}
        )
        blocked_event.add_tag("blocked", "true")
        event_bus.publish_cloud_event(blocked_event)

        # 发布正常事件
        normal_event = CloudEvent(
            type="filter.test",
            source="test",
            data={"message": "normal"}
        )
        event_bus.publish_cloud_event(normal_event)

        # 只有正常事件被处理
        assert len(received_events) == 1
        assert received_events[0].data is not None
        assert received_events[0].data["message"] == "normal"

    def test_event_history(self, event_bus):
        """测试事件历史记录"""
        # 发布几个事件
        for i in range(3):
            event_bus.publish(f"history.test.{i}", data={"index": i})

        # 获取历史记录
        history = event_bus.get_event_history()
        assert len(history) == 3

        # 获取最近的事件
        recent = event_bus.get_event_history(count=2)
        assert len(recent) == 2
        assert recent[-1].data["index"] == 2

    def test_correlation_id_tracking(self, event_bus):
        """测试关联ID事件链追踪"""
        received_events = []

        def handler(event: CloudEvent):
            received_events.append(event)

        event_bus.subscribe("chain.test", handler)

        # 创建关联事件链
        parent_event = CloudEvent(
            type="chain.test",
            source="parent",
            data={"step": "parent"},
            correlation_id="test-correlation-123"
        )

        child_event = parent_event.create_correlated_event(
            "chain.test",
            data={"step": "child"},
            source="child"
        )

        # 发布事件链
        event_bus.publish_cloud_event(parent_event)
        event_bus.publish_cloud_event(child_event)

        # 验证关联ID一致
        assert len(received_events) == 2
        assert received_events[0].correlation_id == "test-correlation-123"
        assert received_events[1].correlation_id == "test-correlation-123"
        assert received_events[0].data is not None
        assert received_events[1].data is not None
        assert received_events[0].data["step"] == "parent"
        assert received_events[1].data["step"] == "child"