# -*- coding: utf-8 -*-
"""
SimTradeLab 事件总线系统
提供事件发布订阅、异步处理、事件过滤等功能
"""

import asyncio
import logging
import threading
import time
import weakref
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from ..exceptions import SimTradeLabError
from .events.cloud_event import CloudEvent


class EventBusError(SimTradeLabError):
    """事件总线相关异常"""

    pass


class EventSubscriptionError(EventBusError):
    """事件订阅异常"""

    pass


class EventPublishError(EventBusError):
    """事件发布异常"""

    pass


class EventPriority(Enum):
    """事件优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """事件数据类"""

    type: str
    data: Any = None
    source: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    priority: EventPriority = EventPriority.NORMAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_id: Optional[str] = None

    def __post_init__(self):
        if self.event_id is None:
            self.event_id = f"{self.type}_{self.timestamp}_{id(self)}"


@dataclass
class EventSubscription:
    """事件订阅信息"""

    event_type: str
    handler: Callable
    filter_func: Optional[Callable[[Event], bool]] = None
    priority: EventPriority = EventPriority.NORMAL
    once: bool = False  # 是否只触发一次
    async_handler: bool = False
    created_at: float = field(default_factory=time.time)
    subscription_id: str = field(
        default_factory=lambda: f"sub_{time.time()}_{id(object())}"
    )


class EventFilter:
    """事件过滤器"""

    def __init__(self):
        self.filters = []

    def add_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """添加过滤函数"""
        self.filters.append(filter_func)

    def remove_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """移除过滤函数"""
        if filter_func in self.filters:
            self.filters.remove(filter_func)

    def apply(self, event: Event) -> bool:
        """应用所有过滤器，返回是否通过"""
        return all(f(event) for f in self.filters)


class EventBus:
    """
    事件总线系统

    提供高性能的事件发布订阅机制，支持：
    - 同步/异步事件处理
    - 事件优先级
    - 事件过滤
    - 弱引用订阅（防止内存泄漏）
    - 并发安全
    - 事件历史记录
    """

    def __init__(self, max_workers: int = 4, max_history: int = 1000):
        """
        初始化事件总线

        Args:
            max_workers: 异步处理的最大工作线程数
            max_history: 最大事件历史记录数
        """
        self._subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self._global_filters = EventFilter()
        self._event_history = deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._logger = logging.getLogger(__name__)
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "subscriptions_count": 0,
        }
        self._running = True

        # 弱引用管理
        self._weak_refs: Dict[str, weakref.ref] = {}

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None,
        once: bool = False,
        weak_ref: bool = True,
    ) -> str:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理函数
            priority: 事件优先级
            filter_func: 事件过滤函数
            once: 是否只触发一次
            weak_ref: 是否使用弱引用

        Returns:
            订阅ID

        Raises:
            EventSubscriptionError: 订阅失败时抛出
        """
        if not callable(handler):
            raise EventSubscriptionError("Handler must be callable")

        try:
            with self._lock:
                # 检查是否是异步处理函数
                is_async = asyncio.iscoroutinefunction(handler)

                subscription = EventSubscription(
                    event_type=event_type,
                    handler=handler,
                    filter_func=filter_func,
                    priority=priority,
                    once=once,
                    async_handler=is_async,
                )

                # 如果使用弱引用，创建弱引用回调
                if weak_ref and hasattr(handler, "__self__"):

                    def cleanup_callback(ref):
                        self._cleanup_dead_subscription(subscription.subscription_id)

                    weak_handler = weakref.ref(handler.__self__, cleanup_callback)
                    self._weak_refs[subscription.subscription_id] = weak_handler

                # 按优先级插入订阅列表
                subscriptions = self._subscriptions[event_type]
                insert_pos = len(subscriptions)

                for i, sub in enumerate(subscriptions):
                    if priority.value > sub.priority.value:
                        insert_pos = i
                        break

                subscriptions.insert(insert_pos, subscription)
                self._stats["subscriptions_count"] += 1

                self._logger.debug(
                    f"Subscribed to {event_type} with ID {subscription.subscription_id}"
                )
                return subscription.subscription_id

        except Exception as e:
            raise EventSubscriptionError(f"Failed to subscribe to {event_type}: {e}")

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅

        Args:
            subscription_id: 订阅ID

        Returns:
            是否成功取消订阅
        """
        with self._lock:
            for event_type, subscriptions in self._subscriptions.items():
                for i, subscription in enumerate(subscriptions):
                    if subscription.subscription_id == subscription_id:
                        subscriptions.pop(i)
                        self._stats["subscriptions_count"] -= 1

                        # 清理弱引用
                        if subscription_id in self._weak_refs:
                            del self._weak_refs[subscription_id]

                        self._logger.debug(
                            f"Unsubscribed {subscription_id} from {event_type}"
                        )
                        return True
            return False

    def unsubscribe_all(self, event_type: str) -> int:
        """
        取消某个事件类型的所有订阅

        Args:
            event_type: 事件类型

        Returns:
            取消的订阅数量
        """
        with self._lock:
            if event_type in self._subscriptions:
                count = len(self._subscriptions[event_type])

                # 清理弱引用
                for subscription in self._subscriptions[event_type]:
                    if subscription.subscription_id in self._weak_refs:
                        del self._weak_refs[subscription.subscription_id]

                del self._subscriptions[event_type]
                self._stats["subscriptions_count"] -= count
                self._logger.debug(
                    f"Unsubscribed all {count} handlers from {event_type}"
                )
                return count
            return 0

    def publish(
        self,
        event_type: str,
        data: Any = None,
        source: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        async_publish: bool = False,
    ) -> Union[List[Any], asyncio.Future]:
        """
        发布事件（向后兼容方法）

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
            priority: 事件优先级
            metadata: 事件元数据
            async_publish: 是否异步发布

        Returns:
            同步模式返回处理结果列表，异步模式返回Future

        Raises:
            EventPublishError: 发布失败时抛出
        """
        # 转换为CloudEvent并发布
        cloud_event = CloudEvent(
            type=event_type,
            source=source or "unknown",
            data=data,
            priority=priority.value,
            tags=metadata or {},
        )

        return self.publish_cloud_event(cloud_event, async_publish=async_publish)

    def publish_cloud_event(
        self,
        cloud_event: CloudEvent,
        async_publish: bool = False,
    ) -> Union[List[Any], asyncio.Future]:
        """
        发布CloudEvent事件

        Args:
            cloud_event: CloudEvent事件实例
            async_publish: 是否异步发布

        Returns:
            同步模式返回处理结果列表，异步模式返回Future

        Raises:
            EventPublishError: 发布失败时抛出
        """
        if not self._running:
            raise EventPublishError("EventBus is not running")

        # 记录事件历史（转换为旧格式兼容）
        legacy_event = Event(
            type=cloud_event.type,
            data=cloud_event.data,
            source=cloud_event.source,
            timestamp=cloud_event.time.timestamp(),
            priority=EventPriority(min(cloud_event.priority, 4)),  # 转换优先级
            metadata=cloud_event.tags,
            event_id=cloud_event.id,
        )

        self._event_history.append(legacy_event)
        self._stats["events_published"] += 1

        try:
            if async_publish:
                return self._executor.submit(self._process_cloud_event, cloud_event)
            else:
                return self._process_cloud_event(cloud_event)
        except Exception as e:
            self._stats["events_failed"] += 1
            raise EventPublishError(
                f"Failed to publish CloudEvent {cloud_event.type}: {e}"
            )

    async def publish_cloud_event_async(
        self,
        cloud_event: CloudEvent,
    ) -> List[Any]:
        """
        异步发布CloudEvent事件

        Args:
            cloud_event: CloudEvent事件实例

        Returns:
            处理结果列表
        """
        # 记录事件历史（转换为旧格式兼容）
        legacy_event = Event(
            type=cloud_event.type,
            data=cloud_event.data,
            source=cloud_event.source,
            timestamp=cloud_event.time.timestamp(),
            priority=EventPriority(min(cloud_event.priority, 4)),
            metadata=cloud_event.tags,
            event_id=cloud_event.id,
        )

        self._event_history.append(legacy_event)
        self._stats["events_published"] += 1

        try:
            return await self._process_cloud_event_async(cloud_event)
        except Exception as e:
            self._stats["events_failed"] += 1
            raise EventPublishError(
                f"Failed to publish async CloudEvent {cloud_event.type}: {e}"
            )

    async def publish_async(
        self,
        event_type: str,
        data: Any = None,
        source: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        异步发布事件（向后兼容方法）

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
            priority: 事件优先级
            metadata: 事件元数据

        Returns:
            处理结果列表
        """
        # 转换为CloudEvent并异步发布
        cloud_event = CloudEvent(
            type=event_type,
            source=source or "unknown",
            data=data,
            priority=priority.value,
            tags=metadata or {},
        )

        return await self.publish_cloud_event_async(cloud_event)

    def _process_cloud_event(self, cloud_event: CloudEvent) -> List[Any]:
        """
        处理CloudEvent事件（同步）

        Args:
            cloud_event: CloudEvent事件实例

        Returns:
            处理结果列表
        """
        results = []

        # 应用全局过滤器（转换为旧格式兼容）
        legacy_event = Event(
            type=cloud_event.type,
            data=cloud_event.data,
            source=cloud_event.source,
            timestamp=cloud_event.time.timestamp(),
            priority=EventPriority(min(cloud_event.priority, 4)),
            metadata=cloud_event.tags,
            event_id=cloud_event.id,
        )

        if not self._global_filters.apply(legacy_event):
            return results

        with self._lock:
            subscriptions = self._subscriptions.get(cloud_event.type, []).copy()

        # 需要移除的一次性订阅
        to_remove = []

        for subscription in subscriptions:
            try:
                # 检查弱引用是否还有效
                if subscription.subscription_id in self._weak_refs:
                    weak_ref = self._weak_refs[subscription.subscription_id]
                    if weak_ref() is None:
                        to_remove.append(subscription.subscription_id)
                        continue

                # 应用订阅级过滤器
                if subscription.filter_func and not subscription.filter_func(
                    legacy_event
                ):
                    continue

                # 处理事件 - 支持CloudEvent和旧Event格式
                if subscription.async_handler:
                    # 异步处理函数在同步模式下跳过
                    self._logger.warning(
                        f"Skipping async handler for {cloud_event.type} in sync mode"
                    )
                    continue
                else:
                    # 检查处理器是否支持CloudEvent
                    if self._handler_supports_cloud_event(subscription.handler):
                        result = subscription.handler(cloud_event)
                    else:
                        # 使用旧格式兼容
                        result = subscription.handler(legacy_event)
                    results.append(result)

                self._stats["events_processed"] += 1

                # 如果是一次性订阅，标记移除
                if subscription.once:
                    to_remove.append(subscription.subscription_id)

            except Exception as e:
                self._stats["events_failed"] += 1
                self._logger.error(
                    f"Handler failed for CloudEvent {cloud_event.type}: {e}"
                )
                results.append(None)

        # 移除一次性订阅和失效的弱引用
        for sub_id in to_remove:
            self.unsubscribe(sub_id)

        return results

    async def _process_cloud_event_async(self, cloud_event: CloudEvent) -> List[Any]:
        """
        处理CloudEvent事件（异步）

        Args:
            cloud_event: CloudEvent事件实例

        Returns:
            处理结果列表
        """
        results = []

        # 应用全局过滤器（转换为旧格式兼容）
        legacy_event = Event(
            type=cloud_event.type,
            data=cloud_event.data,
            source=cloud_event.source,
            timestamp=cloud_event.time.timestamp(),
            priority=EventPriority(min(cloud_event.priority, 4)),
            metadata=cloud_event.tags,
            event_id=cloud_event.id,
        )

        if not self._global_filters.apply(legacy_event):
            return results

        with self._lock:
            subscriptions = self._subscriptions.get(cloud_event.type, []).copy()

        # 需要移除的一次性订阅
        to_remove = []

        # 收集所有任务
        tasks = []
        sync_results = []

        for subscription in subscriptions:
            try:
                # 检查弱引用是否还有效
                if subscription.subscription_id in self._weak_refs:
                    weak_ref = self._weak_refs[subscription.subscription_id]
                    if weak_ref() is None:
                        to_remove.append(subscription.subscription_id)
                        continue

                # 应用订阅级过滤器
                if subscription.filter_func and not subscription.filter_func(
                    legacy_event
                ):
                    continue

                # 处理事件
                if subscription.async_handler:
                    # 检查处理器是否支持CloudEvent
                    if self._handler_supports_cloud_event(subscription.handler):
                        task = asyncio.create_task(subscription.handler(cloud_event))
                    else:
                        task = asyncio.create_task(subscription.handler(legacy_event))
                    tasks.append(task)
                else:
                    # 检查处理器是否支持CloudEvent
                    if self._handler_supports_cloud_event(subscription.handler):
                        result = subscription.handler(cloud_event)
                    else:
                        result = subscription.handler(legacy_event)
                    sync_results.append(result)

                # 如果是一次性订阅，标记移除
                if subscription.once:
                    to_remove.append(subscription.subscription_id)

            except Exception as e:
                self._stats["events_failed"] += 1
                self._logger.error(
                    f"Handler failed for CloudEvent {cloud_event.type}: {e}"
                )
                sync_results.append(None)

        # 等待所有异步任务完成
        if tasks:
            async_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in async_results:
                if isinstance(result, Exception):
                    self._stats["events_failed"] += 1
                    self._logger.error(
                        f"Async handler failed for CloudEvent "
                        f"{cloud_event.type}: {result}"
                    )
                    results.append(None)
                else:
                    results.append(result)
                    self._stats["events_processed"] += 1

        # 添加同步结果
        results.extend(sync_results)
        self._stats["events_processed"] += len(sync_results)

        # 移除一次性订阅和失效的弱引用
        for sub_id in to_remove:
            self.unsubscribe(sub_id)

        return results

    def _handler_supports_cloud_event(self, handler: Callable) -> bool:
        """
        检查处理器是否支持CloudEvent参数

        Args:
            handler: 事件处理器

        Returns:
            是否支持CloudEvent
        """
        import inspect

        try:
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())

            if not params:
                return False

            # 检查第一个参数的类型注解
            first_param = params[0]
            if (
                first_param.annotation
                and first_param.annotation != inspect.Parameter.empty
            ):
                # 检查是否注解为CloudEvent类型
                return first_param.annotation is CloudEvent or (
                    hasattr(first_param.annotation, "__name__")
                    and first_param.annotation.__name__ == "CloudEvent"
                )

            # 如果没有类型注解，默认假设支持旧格式
            return False

        except Exception:
            # 如果检查失败，默认使用旧格式
            return False

    def _process_event(self, event: Event) -> List[Any]:
        """
        处理事件（同步）

        Args:
            event: 事件对象

        Returns:
            处理结果列表
        """
        results = []

        # 应用全局过滤器
        if not self._global_filters.apply(event):
            return results

        with self._lock:
            subscriptions = self._subscriptions.get(event.type, []).copy()

        # 需要移除的一次性订阅
        to_remove = []

        for subscription in subscriptions:
            try:
                # 检查弱引用是否还有效
                if subscription.subscription_id in self._weak_refs:
                    weak_ref = self._weak_refs[subscription.subscription_id]
                    if weak_ref() is None:
                        to_remove.append(subscription.subscription_id)
                        continue

                # 应用订阅级过滤器
                if subscription.filter_func and not subscription.filter_func(event):
                    continue

                # 处理事件
                if subscription.async_handler:
                    # 异步处理函数在同步模式下跳过
                    self._logger.warning(
                        f"Skipping async handler for {event.type} in sync mode"
                    )
                    continue
                else:
                    result = subscription.handler(event)
                    results.append(result)

                self._stats["events_processed"] += 1

                # 如果是一次性订阅，标记移除
                if subscription.once:
                    to_remove.append(subscription.subscription_id)

            except Exception as e:
                self._stats["events_failed"] += 1
                self._logger.error(f"Handler failed for event {event.type}: {e}")
                results.append(None)

        # 移除一次性订阅和失效的弱引用
        for sub_id in to_remove:
            self.unsubscribe(sub_id)

        return results

    async def _process_event_async(self, event: Event) -> List[Any]:
        """
        处理事件（异步）

        Args:
            event: 事件对象

        Returns:
            处理结果列表
        """
        results = []

        # 应用全局过滤器
        if not self._global_filters.apply(event):
            return results

        with self._lock:
            subscriptions = self._subscriptions.get(event.type, []).copy()

        # 需要移除的一次性订阅
        to_remove = []

        # 收集所有任务
        tasks = []
        sync_results = []

        for subscription in subscriptions:
            try:
                # 检查弱引用是否还有效
                if subscription.subscription_id in self._weak_refs:
                    weak_ref = self._weak_refs[subscription.subscription_id]
                    if weak_ref() is None:
                        to_remove.append(subscription.subscription_id)
                        continue

                # 应用订阅级过滤器
                if subscription.filter_func and not subscription.filter_func(event):
                    continue

                # 处理事件
                if subscription.async_handler:
                    task = asyncio.create_task(subscription.handler(event))
                    tasks.append(task)
                else:
                    result = subscription.handler(event)
                    sync_results.append(result)

                # 如果是一次性订阅，标记移除
                if subscription.once:
                    to_remove.append(subscription.subscription_id)

            except Exception as e:
                self._stats["events_failed"] += 1
                self._logger.error(f"Handler failed for event {event.type}: {e}")
                sync_results.append(None)

        # 等待所有异步任务完成
        if tasks:
            async_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in async_results:
                if isinstance(result, Exception):
                    self._stats["events_failed"] += 1
                    self._logger.error(
                        f"Async handler failed for event {event.type}: {result}"
                    )
                    results.append(None)
                else:
                    results.append(result)
                    self._stats["events_processed"] += 1

        # 添加同步结果
        results.extend(sync_results)
        self._stats["events_processed"] += len(sync_results)

        # 移除一次性订阅和失效的弱引用
        for sub_id in to_remove:
            self.unsubscribe(sub_id)

        return results

    def add_global_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """
        添加全局过滤器

        Args:
            filter_func: 过滤函数
        """
        self._global_filters.add_filter(filter_func)
        self._logger.debug("Added global filter")

    def remove_global_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """
        移除全局过滤器

        Args:
            filter_func: 过滤函数
        """
        self._global_filters.remove_filter(filter_func)
        self._logger.debug("Removed global filter")

    def get_subscriptions(
        self, event_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        获取订阅信息

        Args:
            event_type: 事件类型，为None时返回所有订阅

        Returns:
            订阅信息字典
        """
        with self._lock:
            if event_type:
                subscriptions = self._subscriptions.get(event_type, [])
                return {event_type: [sub.subscription_id for sub in subscriptions]}
            else:
                return {
                    et: [sub.subscription_id for sub in subs]
                    for et, subs in self._subscriptions.items()
                }

    def get_event_history(self, count: Optional[int] = None) -> List[Event]:
        """
        获取事件历史

        Args:
            count: 返回的事件数量，为None时返回所有

        Returns:
            事件历史列表
        """
        history = list(self._event_history)
        if count is not None:
            return history[-count:]
        return history

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            return {
                **self._stats,
                "active_subscriptions": sum(
                    len(subs) for subs in self._subscriptions.values()
                ),
                "event_types_count": len(self._subscriptions),
                "history_size": len(self._event_history),
                "weak_refs_count": len(self._weak_refs),
            }

    def clear_history(self) -> None:
        """清空事件历史"""
        self._event_history.clear()
        self._logger.debug("Cleared event history")

    def clear_all_subscriptions(self) -> int:
        """
        清空所有订阅

        Returns:
            清理的订阅数量
        """
        with self._lock:
            total_count = sum(len(subs) for subs in self._subscriptions.values())
            self._subscriptions.clear()
            self._weak_refs.clear()
            self._stats["subscriptions_count"] = 0
            self._logger.debug(f"Cleared all {total_count} subscriptions")
            return total_count

    def _cleanup_dead_subscription(self, subscription_id: str) -> None:
        """
        清理失效的订阅

        Args:
            subscription_id: 订阅ID
        """
        self.unsubscribe(subscription_id)
        self._logger.debug(f"Cleaned up dead subscription {subscription_id}")

    def shutdown(self) -> None:
        """
        关闭事件总线
        """
        self._running = False
        self._executor.shutdown(wait=True)
        self.clear_all_subscriptions()
        self.clear_history()
        self._logger.info("EventBus shutdown completed")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()


# 全局事件总线实例
default_event_bus = EventBus()


def subscribe(event_type: str, **kwargs) -> Callable:
    """
    装饰器：订阅事件

    Args:
        event_type: 事件类型
        **kwargs: 订阅参数

    Returns:
        装饰器函数
    """

    def decorator(func):
        default_event_bus.subscribe(event_type, func, **kwargs)
        return func

    return decorator


def publish_cloud_event(cloud_event: CloudEvent, **kwargs) -> List[Any]:
    """
    发布CloudEvent到默认事件总线

    Args:
        cloud_event: CloudEvent事件实例
        **kwargs: 发布参数

    Returns:
        处理结果列表
    """
    return default_event_bus.publish_cloud_event(cloud_event, **kwargs)


def emit(event_type: str, **kwargs) -> List[Any]:
    """
    发布事件到默认事件总线（emit别名）

    Args:
        event_type: 事件类型
        **kwargs: 发布参数

    Returns:
        处理结果列表
    """
    return default_event_bus.publish(event_type, **kwargs)
