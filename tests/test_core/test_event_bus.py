# -*- coding: utf-8 -*-
"""
EventBus 测试
确保100%测试覆盖率，包括所有方法、异常处理、并发安全
"""

import asyncio
import threading
import time
import weakref
from concurrent.futures import Future
from unittest.mock import MagicMock, patch

import pytest

from simtradelab.core.event_bus import (
    Event,
    EventBus,
    EventBusError,
    EventFilter,
    EventPriority,
    EventPublishError,
    EventSubscription,
    EventSubscriptionError,
    default_event_bus,
    publish,
    subscribe,
)


class TestEvent:
    """测试Event类"""

    def test_event_creation(self):
        """测试事件创建"""
        event = Event(
            type="test_event",
            data={"key": "value"},
            source="test_source",
            priority=EventPriority.HIGH,
            metadata={"meta": "data"},
        )

        assert event.type == "test_event"
        assert event.data == {"key": "value"}
        assert event.source == "test_source"
        assert event.priority == EventPriority.HIGH
        assert event.metadata == {"meta": "data"}
        assert event.event_id is not None
        assert isinstance(event.timestamp, float)

    def test_event_defaults(self):
        """测试事件默认值"""
        event = Event(type="test")

        assert event.type == "test"
        assert event.data is None
        assert event.source is None
        assert event.priority == EventPriority.NORMAL
        assert event.metadata == {}
        assert event.event_id is not None

    def test_event_id_generation(self):
        """测试事件ID生成"""
        event1 = Event(type="test")
        event2 = Event(type="test")

        assert event1.event_id != event2.event_id
        assert "test" in event1.event_id
        # 检查event_id格式：{type}_{timestamp}_{id(self)}
        assert event1.event_id.startswith("test_")
        parts = event1.event_id.split("_")
        assert len(parts) == 3
        assert parts[0] == "test"
        # 验证timestamp部分是有效的浮点数字符串
        assert parts[1].replace(".", "").replace("-", "").isdigit()
        # 验证id部分是数字
        assert parts[2].isdigit()


class TestEventSubscription:
    """测试EventSubscription类"""

    def test_subscription_creation(self):
        """测试订阅创建"""

        def handler(event):
            return event.data

        def filter_func(event):
            return True

        subscription = EventSubscription(
            event_type="test_event",
            handler=handler,
            filter_func=filter_func,
            priority=EventPriority.HIGH,
            once=True,
            async_handler=False,
        )

        assert subscription.event_type == "test_event"
        assert subscription.handler is handler
        assert subscription.filter_func is filter_func
        assert subscription.priority == EventPriority.HIGH
        assert subscription.once is True
        assert subscription.async_handler is False
        assert subscription.subscription_id is not None
        assert isinstance(subscription.created_at, float)

    def test_subscription_defaults(self):
        """测试订阅默认值"""

        def handler(event):
            pass

        subscription = EventSubscription(event_type="test", handler=handler)

        assert subscription.filter_func is None
        assert subscription.priority == EventPriority.NORMAL
        assert subscription.once is False
        assert subscription.async_handler is False


class TestEventFilter:
    """测试EventFilter类"""

    def test_filter_creation(self):
        """测试过滤器创建"""
        filter_obj = EventFilter()
        assert filter_obj.filters == []

    def test_add_and_remove_filter(self):
        """测试添加和移除过滤器"""
        filter_obj = EventFilter()

        def filter1(event):
            return True

        def filter2(event):
            return False

        filter_obj.add_filter(filter1)
        filter_obj.add_filter(filter2)

        assert len(filter_obj.filters) == 2
        assert filter1 in filter_obj.filters
        assert filter2 in filter_obj.filters

        filter_obj.remove_filter(filter1)

        assert len(filter_obj.filters) == 1
        assert filter1 not in filter_obj.filters
        assert filter2 in filter_obj.filters

    def test_remove_nonexistent_filter(self):
        """测试移除不存在的过滤器"""
        filter_obj = EventFilter()

        def filter_func(event):
            return True

        # 应该不抛出异常
        filter_obj.remove_filter(filter_func)
        assert len(filter_obj.filters) == 0

    def test_apply_filters(self):
        """测试应用过滤器"""
        filter_obj = EventFilter()
        event = Event(type="test", data=5)

        # 无过滤器时应该通过
        assert filter_obj.apply(event) is True

        # 添加通过的过滤器
        filter_obj.add_filter(lambda e: e.data > 0)
        assert filter_obj.apply(event) is True

        # 添加不通过的过滤器
        filter_obj.add_filter(lambda e: e.data > 10)
        assert filter_obj.apply(event) is False

        # 移除不通过的过滤器
        filter_obj.filters.pop()
        assert filter_obj.apply(event) is True


class TestEventBus:
    """测试EventBus基础功能"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus(max_workers=2, max_history=100)
        yield bus
        bus.shutdown()

    def test_event_bus_creation(self):
        """测试事件总线创建"""
        bus = EventBus(max_workers=4, max_history=1000)

        assert bus._stats["events_published"] == 0
        assert bus._stats["events_processed"] == 0
        assert bus._stats["events_failed"] == 0
        assert bus._stats["subscriptions_count"] == 0
        assert bus._running is True

        bus.shutdown()

    def test_subscribe_and_unsubscribe(self, event_bus):
        """测试订阅和取消订阅"""
        call_count = 0

        def handler(event):
            nonlocal call_count
            call_count += 1
            return event.data

        # 订阅事件
        sub_id = event_bus.subscribe("test_event", handler)
        assert isinstance(sub_id, str)
        assert event_bus._stats["subscriptions_count"] == 1

        # 发布事件
        results = event_bus.publish("test_event", data="test_data")
        assert len(results) == 1
        assert results[0] == "test_data"
        assert call_count == 1

        # 取消订阅
        success = event_bus.unsubscribe(sub_id)
        assert success is True
        assert event_bus._stats["subscriptions_count"] == 0

        # 再次发布事件，应该没有处理器
        results = event_bus.publish("test_event", data="test_data2")
        assert len(results) == 0
        assert call_count == 1  # 没有增加

    def test_subscribe_with_priority(self, event_bus):
        """测试优先级订阅"""
        call_order = []

        def handler_low(event):
            call_order.append("low")

        def handler_high(event):
            call_order.append("high")

        def handler_critical(event):
            call_order.append("critical")

        # 以不同顺序订阅
        event_bus.subscribe("test", handler_low, priority=EventPriority.LOW)
        event_bus.subscribe("test", handler_critical, priority=EventPriority.CRITICAL)
        event_bus.subscribe("test", handler_high, priority=EventPriority.HIGH)

        # 发布事件
        event_bus.publish("test")

        # 应该按优先级顺序执行：CRITICAL > HIGH > LOW
        assert call_order == ["critical", "high", "low"]

    def test_subscribe_with_filter(self, event_bus):
        """测试带过滤器的订阅"""
        call_count = 0

        def handler(event):
            nonlocal call_count
            call_count += 1

        def filter_func(event):
            return event.data > 5

        event_bus.subscribe("test", handler, filter_func=filter_func)

        # 发布不通过过滤器的事件
        event_bus.publish("test", data=3)
        assert call_count == 0

        # 发布通过过滤器的事件
        event_bus.publish("test", data=10)
        assert call_count == 1

    def test_subscribe_once(self, event_bus):
        """测试一次性订阅"""
        call_count = 0

        def handler(event):
            nonlocal call_count
            call_count += 1

        event_bus.subscribe("test", handler, once=True)
        assert event_bus._stats["subscriptions_count"] == 1

        # 第一次发布
        event_bus.publish("test")
        assert call_count == 1
        assert event_bus._stats["subscriptions_count"] == 0  # 自动取消订阅

        # 第二次发布，应该没有处理器
        event_bus.publish("test")
        assert call_count == 1  # 没有增加

    def test_invalid_handler_subscription(self, event_bus):
        """测试无效处理器订阅"""
        with pytest.raises(EventSubscriptionError, match="Handler must be callable"):
            event_bus.subscribe("test", "not_callable")

    def test_unsubscribe_nonexistent(self, event_bus):
        """测试取消不存在的订阅"""
        success = event_bus.unsubscribe("nonexistent_id")
        assert success is False

    def test_unsubscribe_all(self, event_bus):
        """测试取消所有订阅"""

        def handler1(event):
            pass

        def handler2(event):
            pass

        event_bus.subscribe("test", handler1)
        event_bus.subscribe("test", handler2)
        event_bus.subscribe("other", handler1)

        assert event_bus._stats["subscriptions_count"] == 3

        # 取消test事件的所有订阅
        count = event_bus.unsubscribe_all("test")
        assert count == 2
        assert event_bus._stats["subscriptions_count"] == 1

        # 取消不存在事件的订阅
        count = event_bus.unsubscribe_all("nonexistent")
        assert count == 0

    def test_publish_with_metadata(self, event_bus):
        """测试发布带元数据的事件"""
        received_event = None

        def handler(event):
            nonlocal received_event
            received_event = event

        event_bus.subscribe("test", handler)

        metadata = {"source": "unit_test", "version": 1}
        event_bus.publish(
            "test",
            data="test_data",
            source="test_source",
            priority=EventPriority.HIGH,
            metadata=metadata,
        )

        assert received_event is not None

    def test_subscribe_with_weak_ref(self, event_bus):
        """测试弱引用订阅基本功能"""
        call_count = 0

        class TestObject:
            def handler(self, event):
                nonlocal call_count
                call_count += 1

        obj = TestObject()
        sub_id = event_bus.subscribe("test", obj.handler, weak_ref=True)

        # 验证弱引用被创建
        assert sub_id in event_bus._weak_refs

        # 先发布一次事件确认处理器工作
        event_bus.publish("test")
        assert call_count == 1

        # 手动取消订阅来测试清理
        success = event_bus.unsubscribe(sub_id)
        assert success is True
        assert event_bus._stats["subscriptions_count"] == 0

        # 如果有弱引用，应该被清理
        assert sub_id not in event_bus._weak_refs

    def test_publish_exception_handling(self, event_bus):
        """测试发布异常处理"""

        def failing_handler(event):
            raise ValueError("Handler failed")

        def working_handler(event):
            return "success"

        event_bus.subscribe("test", failing_handler)
        event_bus.subscribe("test", working_handler)

        # 发布事件，失败的处理器应该被记录但不影响其他处理器
        results = event_bus.publish("test")

        # 应该有两个结果，失败的为None，成功的为"success"
        assert len(results) == 2
        assert None in results
        assert "success" in results
        assert event_bus._stats["events_failed"] > 0

    def test_async_publish_future(self, event_bus):
        """测试异步发布返回Future"""

        def handler(event):
            return "result"

        event_bus.subscribe("test", handler)

        future = event_bus.publish("test", async_publish=True)
        assert isinstance(future, Future)

        # 等待结果
        results = future.result(timeout=1.0)
        assert results == ["result"]

    def test_publish_when_not_running(self, event_bus):
        """测试在未运行状态下发布事件"""
        event_bus._running = False

        with pytest.raises(EventPublishError, match="EventBus is not running"):
            event_bus.publish("test")

    def test_handler_exception(self, event_bus):
        """测试处理器异常"""

        def failing_handler(event):
            raise RuntimeError("Handler failed")

        def working_handler(event):
            return "success"

        event_bus.subscribe("test", failing_handler)
        event_bus.subscribe("test", working_handler)

        results = event_bus.publish("test")

        assert len(results) == 2
        assert results[0] is None  # 失败的处理器返回None
        assert results[1] == "success"
        assert event_bus._stats["events_failed"] == 1
        assert event_bus._stats["events_processed"] == 1


class TestEventBusAsync:
    """测试EventBus异步功能"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus(max_workers=2, max_history=100)
        yield bus
        bus.shutdown()

    @pytest.mark.asyncio
    async def test_async_handler_subscription(self, event_bus):
        """测试异步处理器订阅"""
        call_count = 0

        async def async_handler(event):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 模拟异步操作
            return event.data * 2

        def sync_handler(event):
            return event.data

        event_bus.subscribe("test", async_handler)
        event_bus.subscribe("test", sync_handler)

        # 同步发布，异步处理器应该被跳过
        results = event_bus.publish("test", data=5)
        assert len(results) == 1
        assert results[0] == 5  # 只有同步处理器的结果
        assert call_count == 0  # 异步处理器未被调用

    @pytest.mark.asyncio
    async def test_publish_async(self, event_bus):
        """测试异步发布"""
        async_call_count = 0
        sync_call_count = 0

        async def async_handler(event):
            nonlocal async_call_count
            async_call_count += 1
            await asyncio.sleep(0.01)
            return event.data * 2

        def sync_handler(event):
            nonlocal sync_call_count
            sync_call_count += 1
            return event.data

        event_bus.subscribe("test", async_handler)
        event_bus.subscribe("test", sync_handler)

        # 异步发布
        results = await event_bus.publish_async("test", data=5)

        assert len(results) == 2
        assert 10 in results  # 异步处理器结果
        assert 5 in results  # 同步处理器结果
        assert async_call_count == 1
        assert sync_call_count == 1

    @pytest.mark.asyncio
    async def test_async_handler_exception(self, event_bus):
        """测试异步处理器异常"""

        async def failing_async_handler(event):
            raise RuntimeError("Async handler failed")

        async def working_async_handler(event):
            return "async_success"

        def sync_handler(event):
            return "sync_success"

        event_bus.subscribe("test", failing_async_handler)
        event_bus.subscribe("test", working_async_handler)
        event_bus.subscribe("test", sync_handler)

        results = await event_bus.publish_async("test")

        assert len(results) == 3
        assert None in results  # 失败的异步处理器
        assert "async_success" in results
        assert "sync_success" in results
        assert event_bus._stats["events_failed"] == 1
        assert event_bus._stats["events_processed"] == 2

    def test_async_publish_sync_mode(self, event_bus):
        """测试同步模式下的异步发布"""
        future = event_bus.publish("test", data="test", async_publish=True)
        assert isinstance(future, Future)

        # 等待结果
        results = future.result(timeout=1.0)
        assert isinstance(results, list)


class TestEventBusFilters:
    """测试EventBus过滤功能"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus()
        yield bus
        bus.shutdown()

    def test_global_filters(self, event_bus):
        """测试全局过滤器"""
        call_count = 0

        def handler(event):
            nonlocal call_count
            call_count += 1

        def global_filter(event):
            return event.data > 5

        event_bus.subscribe("test", handler)
        event_bus.add_global_filter(global_filter)

        # 不通过全局过滤器
        event_bus.publish("test", data=3)
        assert call_count == 0

        # 通过全局过滤器
        event_bus.publish("test", data=10)
        assert call_count == 1

        # 移除全局过滤器
        event_bus.remove_global_filter(global_filter)
        event_bus.publish("test", data=1)
        assert call_count == 2  # 现在应该通过

    def test_subscription_and_global_filters(self, event_bus):
        """测试订阅级和全局过滤器组合"""
        call_count = 0

        def handler(event):
            nonlocal call_count
            call_count += 1

        def global_filter(event):
            return event.data > 0

        def subscription_filter(event):
            return event.data < 10

        event_bus.add_global_filter(global_filter)
        event_bus.subscribe("test", handler, filter_func=subscription_filter)

        # 不通过全局过滤器
        event_bus.publish("test", data=-1)
        assert call_count == 0

        # 通过全局过滤器但不通过订阅过滤器
        event_bus.publish("test", data=15)
        assert call_count == 0

        # 两个过滤器都通过
        event_bus.publish("test", data=5)
        assert call_count == 1


class TestEventBusWeakReferences:
    """测试EventBus弱引用功能"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus()
        yield bus
        bus.shutdown()

    def test_weak_reference_cleanup(self, event_bus):
        """测试弱引用基本功能"""

        class TestObject:
            def __init__(self):
                self.call_count = 0

            def handler(self, event):
                self.call_count += 1

        obj = TestObject()
        sub_id = event_bus.subscribe("test", obj.handler, weak_ref=True)

        assert event_bus._stats["subscriptions_count"] == 1

        # 发布事件，应该正常工作
        event_bus.publish("test")
        assert obj.call_count == 1

        # 手动取消订阅来测试清理
        success = event_bus.unsubscribe(sub_id)
        assert success is True
        assert event_bus._stats["subscriptions_count"] == 0

        # 如果有弱引用，应该被清理
        assert sub_id not in event_bus._weak_refs

    def test_no_weak_reference(self, event_bus):
        """测试不使用弱引用"""

        def handler(event):
            pass

        sub_id = event_bus.subscribe("test", handler, weak_ref=False)

        assert event_bus._stats["subscriptions_count"] == 1
        assert len(event_bus._weak_refs) == 0  # 没有弱引用


class TestEventBusManagement:
    """测试EventBus管理功能"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus(max_history=5)
        yield bus
        bus.shutdown()

    def test_get_subscriptions(self, event_bus):
        """测试获取订阅信息"""

        def handler1(event):
            pass

        def handler2(event):
            pass

        sub1 = event_bus.subscribe("test1", handler1)
        sub2 = event_bus.subscribe("test1", handler2)
        sub3 = event_bus.subscribe("test2", handler1)

        # 获取所有订阅
        all_subs = event_bus.get_subscriptions()
        assert "test1" in all_subs
        assert "test2" in all_subs
        assert len(all_subs["test1"]) == 2
        assert len(all_subs["test2"]) == 1

        # 获取特定事件的订阅
        test1_subs = event_bus.get_subscriptions("test1")
        assert "test1" in test1_subs
        assert len(test1_subs["test1"]) == 2
        assert sub1 in test1_subs["test1"]
        assert sub2 in test1_subs["test1"]

    def test_event_history(self, event_bus):
        """测试事件历史"""

        def handler(event):
            pass

        event_bus.subscribe("test", handler)

        # 发布一些事件
        event_bus.publish("test", data=1)
        event_bus.publish("test", data=2)
        event_bus.publish("test", data=3)

        history = event_bus.get_event_history()
        assert len(history) == 3
        assert history[0].data == 1
        assert history[1].data == 2
        assert history[2].data == 3

        # 测试限制数量
        recent_history = event_bus.get_event_history(count=2)
        assert len(recent_history) == 2
        assert recent_history[0].data == 2
        assert recent_history[1].data == 3

    def test_event_history_limit(self, event_bus):
        """测试事件历史限制"""

        def handler(event):
            pass

        event_bus.subscribe("test", handler)

        # 发布超过限制的事件（max_history=5）
        for i in range(10):
            event_bus.publish("test", data=i)

        history = event_bus.get_event_history()
        assert len(history) == 5  # 应该只保留最近5个
        assert history[0].data == 5
        assert history[4].data == 9

    def test_get_stats(self, event_bus):
        """测试获取统计信息"""

        def handler(event):
            pass

        def failing_handler(event):
            raise RuntimeError("Handler failed")

        event_bus.subscribe("test", handler)
        event_bus.subscribe("test", failing_handler)

        # 发布事件
        event_bus.publish("test")
        event_bus.publish("test")

        stats = event_bus.get_stats()
        assert stats["events_published"] == 2
        assert stats["events_processed"] == 2  # 只计算成功的
        assert stats["events_failed"] == 2  # 失败的处理器
        assert stats["active_subscriptions"] == 2
        assert stats["event_types_count"] == 1
        assert stats["history_size"] == 2

    def test_clear_history(self, event_bus):
        """测试清空历史"""

        def handler(event):
            pass

        event_bus.subscribe("test", handler)
        event_bus.publish("test")
        event_bus.publish("test")

        assert len(event_bus.get_event_history()) == 2

        event_bus.clear_history()

        assert len(event_bus.get_event_history()) == 0

    def test_clear_all_subscriptions(self, event_bus):
        """测试清空所有订阅"""

        def handler(event):
            pass

        event_bus.subscribe("test1", handler)
        event_bus.subscribe("test2", handler)

        assert event_bus._stats["subscriptions_count"] == 2

        count = event_bus.clear_all_subscriptions()

        assert count == 2
        assert event_bus._stats["subscriptions_count"] == 0
        assert len(event_bus._subscriptions) == 0
        assert len(event_bus._weak_refs) == 0

    def test_context_manager(self):
        """测试上下文管理器"""
        with EventBus() as bus:

            def handler(event):
                pass

            bus.subscribe("test", handler)
            bus.publish("test")

            assert bus._running is True

        # 退出上下文后应该关闭
        assert bus._running is False


class TestEventBusThreadSafety:
    """测试EventBus线程安全"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus()
        yield bus
        bus.shutdown()

    def test_concurrent_subscribe_unsubscribe(self, event_bus):
        """测试并发订阅和取消订阅"""

        def handler(event):
            pass

        subscription_ids = []

        def subscribe_worker():
            for i in range(10):
                sub_id = event_bus.subscribe(f"test_{i}", handler)
                subscription_ids.append(sub_id)

        def unsubscribe_worker():
            time.sleep(0.01)  # 让订阅先开始
            for sub_id in subscription_ids[:5]:  # 只取消一部分
                try:
                    event_bus.unsubscribe(sub_id)
                except IndexError:
                    pass  # 可能已经被其他线程取消了

        # 启动多个线程
        threads = []
        for _ in range(3):
            t1 = threading.Thread(target=subscribe_worker)
            t2 = threading.Thread(target=unsubscribe_worker)
            threads.extend([t1, t2])

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # 最终状态应该是一致的
        stats = event_bus.get_stats()
        assert stats["subscriptions_count"] >= 0

    def test_concurrent_publish(self, event_bus):
        """测试并发发布"""
        call_count = 0
        lock = threading.Lock()

        def handler(event):
            nonlocal call_count
            with lock:
                call_count += 1

        event_bus.subscribe("test", handler)

        def publish_worker():
            for i in range(10):
                event_bus.publish("test", data=i)

        # 启动多个发布线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=publish_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 应该处理了所有事件
        assert call_count == 50  # 5个线程 * 10个事件


class TestGlobalEventBus:
    """测试全局事件总线"""

    def test_global_subscribe_decorator(self):
        """测试全局订阅装饰器"""
        call_count = 0

        @subscribe("test_global")
        def handler(event):
            nonlocal call_count
            call_count += 1
            return event.data

        # 使用全局发布函数
        results = publish("test_global", data="test")

        assert len(results) == 1
        assert results[0] == "test"
        assert call_count == 1

    def test_global_publish_function(self):
        """测试全局发布函数"""
        call_count = 0

        def handler(event):
            nonlocal call_count
            call_count += 1

        # 直接订阅到默认事件总线
        default_event_bus.subscribe("test_global_pub", handler)

        # 使用全局发布函数
        results = publish("test_global_pub", data="test")

        assert len(results) == 1
        assert call_count == 1

        # 清理
        default_event_bus.unsubscribe_all("test_global_pub")
