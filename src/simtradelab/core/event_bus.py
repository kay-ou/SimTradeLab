# -*- coding: utf-8 -*-
"""
SimTradeLab v5.0 事件总线系统

完全基于CloudEvent标准的事件发布订阅系统，提供：
- 标准化的CloudEvent事件模型
- 同步/异步事件处理
- 事件优先级队列
- 事件过滤和路由
- 弱引用订阅管理
- 事件历史记录
- 并发安全操作
"""

import asyncio
import concurrent.futures
import fnmatch
import logging
import threading
import weakref
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
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


@dataclass
class EventSubscription:
    """事件订阅信息"""

    event_type: str
    handler: Callable[[CloudEvent], Any]  # 只接受CloudEvent
    filter_func: Optional[Callable[[CloudEvent], bool]] = None
    priority: int = field(default=5)  # 使用CloudEvent优先级标准 (1-10)
    once: bool = False  # 是否只触发一次
    async_handler: bool = False
    created_at: float = field(default_factory=lambda: __import__("time").time())
    subscription_id: str = field(
        default_factory=lambda: f"sub_{__import__('time').time()}_{id(object())}"
    )


class EventFilter:
    """CloudEvent事件过滤器"""

    def __init__(self) -> None:
        self.filters: List[Callable[[CloudEvent], bool]] = []

    def add_filter(self, filter_func: Callable[[CloudEvent], bool]) -> None:
        """添加过滤函数"""
        self.filters.append(filter_func)

    def remove_filter(self, filter_func: Callable[[CloudEvent], bool]) -> None:
        """移除过滤函数"""
        if filter_func in self.filters:
            self.filters.remove(filter_func)

    def apply(self, event: CloudEvent) -> bool:
        """应用所有过滤器，返回是否通过"""
        return all(f(event) for f in self.filters)


class EventBus:
    """
    v5.0 标准化事件总线系统

    完全基于CloudEvent标准的高性能事件发布订阅机制，提供：
    - CloudEvent标准事件模型
    - 事件优先级队列 (1-10)
    - 同步/异步事件处理
    - 智能事件过滤和路由
    - 弱引用订阅管理
    - 事件链路追踪
    - 并发安全操作
    - 事件历史记录
    """

    def __init__(self, max_workers: int = 4, max_history: int = 1000):
        """
        初始化v5.0标准化事件总线

        Args:
            max_workers: 异步处理的最大工作线程数
            max_history: 最大CloudEvent历史记录数
        """
        self._subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self._global_filters = EventFilter()
        self._event_history: deque[CloudEvent] = deque(maxlen=max_history)
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
        self._weak_refs: Dict[str, "weakref.ref[Any]"] = {}

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[CloudEvent], Any],
        priority: int = 5,
        filter_func: Optional[Callable[[CloudEvent], bool]] = None,
        once: bool = False,
        weak_ref: bool = True,
    ) -> str:
        """
        订阅CloudEvent事件

        Args:
            event_type: 事件类型
            handler: CloudEvent事件处理函数
            priority: 事件优先级 (1-10, 1最高)
            filter_func: CloudEvent事件过滤函数
            once: 是否只触发一次
            weak_ref: 是否使用弱引用

        Returns:
            订阅ID

        Raises:
            EventSubscriptionError: 订阅失败时抛出
        """
        if not callable(handler):
            raise EventSubscriptionError("Handler must be callable")

        # 验证优先级范围
        if priority < 1 or priority > 10:
            raise EventSubscriptionError("Priority must be between 1 and 10")

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

                    def cleanup_callback(ref: "weakref.ref[Any]") -> None:
                        self._cleanup_dead_subscription(subscription.subscription_id)

                    weak_handler = weakref.ref(handler.__self__, cleanup_callback)
                    self._weak_refs[subscription.subscription_id] = weak_handler

                # 按优先级插入订阅列表（优先级低的数字更高优先级）
                subscriptions = self._subscriptions[event_type]
                insert_pos = len(subscriptions)

                for i, sub in enumerate(subscriptions):
                    if priority < sub.priority:  # 数字越小优先级越高
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

    def publish_cloud_event(
        self,
        cloud_event: CloudEvent,
        async_publish: bool = False,
    ) -> Union[List[Any], "concurrent.futures.Future[List[Any]]"]:  # 使用正确的Future类型
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

        # 记录事件历史
        self._event_history.append(cloud_event)
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
        # 记录事件历史
        self._event_history.append(cloud_event)
        self._stats["events_published"] += 1

        try:
            return await self._process_cloud_event_async(cloud_event)
        except Exception as e:
            self._stats["events_failed"] += 1
            raise EventPublishError(
                f"Failed to publish async CloudEvent {cloud_event.type}: {e}"
            )

    # 为了简化API，提供便捷的发布方法
    def publish(
        self,
        event_type: str,
        data: Any = None,
        source: Optional[str] = None,
        priority: int = 5,
        tags: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        async_publish: bool = False,
    ) -> Union[List[Any], "concurrent.futures.Future[List[Any]]"]:  # 修复类型注解
        """
        便捷的事件发布方法（自动创建CloudEvent）

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
            priority: 事件优先级 (1-10)
            tags: 事件标签
            correlation_id: 关联ID
            async_publish: 是否异步发布

        Returns:
            同步模式返回处理结果列表，异步模式返回Future
        """
        cloud_event = CloudEvent(
            type=event_type,
            source=source or "unknown",
            data=data,
            priority=priority,
            tags=tags or {},
            correlation_id=correlation_id,
        )

        return self.publish_cloud_event(cloud_event, async_publish=async_publish)

    async def publish_async(
        self,
        event_type: str,
        data: Any = None,
        source: Optional[str] = None,
        priority: int = 5,
        tags: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
    ) -> List[Any]:
        """
        异步发布事件（便捷方法）

        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
            priority: 事件优先级 (1-10)
            tags: 事件标签
            correlation_id: 关联ID

        Returns:
            处理结果列表
        """
        cloud_event = CloudEvent(
            type=event_type,
            source=source or "unknown",
            data=data,
            priority=priority,
            tags=tags or {},
            correlation_id=correlation_id,
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
        results: List[Any] = []

        # 应用全局过滤器
        if not self._global_filters.apply(cloud_event):
            return results

        with self._lock:
            # 获取精确匹配的订阅
            subscriptions = self._subscriptions.get(cloud_event.type, []).copy()
            
            # 添加模式匹配的订阅
            for pattern, pattern_subscriptions in self._subscriptions.items():
                if pattern != cloud_event.type and self._match_pattern(pattern, cloud_event.type):
                    subscriptions.extend(pattern_subscriptions)

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
                    cloud_event
                ):
                    continue

                # 处理事件
                if subscription.async_handler:
                    # 异步处理函数在同步模式下跳过
                    self._logger.warning(
                        f"Skipping async handler for {cloud_event.type} in sync mode"
                    )
                    continue
                else:
                    result = subscription.handler(cloud_event)
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
        results: List[Any] = []

        # 应用全局过滤器
        if not self._global_filters.apply(cloud_event):
            return results

        with self._lock:
            # 获取精确匹配的订阅
            subscriptions = self._subscriptions.get(cloud_event.type, []).copy()
            
            # 添加模式匹配的订阅
            for pattern, pattern_subscriptions in self._subscriptions.items():
                if pattern != cloud_event.type and self._match_pattern(pattern, cloud_event.type):
                    subscriptions.extend(pattern_subscriptions)

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
                    cloud_event
                ):
                    continue

                # 处理事件
                if subscription.async_handler:
                    task = asyncio.create_task(subscription.handler(cloud_event))
                    tasks.append(task)
                else:
                    result = subscription.handler(cloud_event)
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

    def add_global_filter(self, filter_func: Callable[[CloudEvent], bool]) -> None:
        """
        添加全局CloudEvent过滤器

        Args:
            filter_func: CloudEvent过滤函数
        """
        self._global_filters.add_filter(filter_func)
        self._logger.debug("Added global CloudEvent filter")

    def remove_global_filter(self, filter_func: Callable[[CloudEvent], bool]) -> None:
        """
        移除全局CloudEvent过滤器

        Args:
            filter_func: CloudEvent过滤函数
        """
        self._global_filters.remove_filter(filter_func)
        self._logger.debug("Removed global CloudEvent filter")

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

    def get_event_history(self, count: Optional[int] = None) -> List[CloudEvent]:
        """
        获取CloudEvent历史

        Args:
            count: 返回的事件数量，为None时返回所有

        Returns:
            CloudEvent历史列表
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
        """清空CloudEvent历史"""
        self._event_history.clear()
        self._logger.debug("Cleared CloudEvent history")

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

    def _match_pattern(self, pattern: str, event_type: str) -> bool:
        """
        检查事件类型是否匹配模式
        
        支持 Unix shell-style wildcards:
        - * 匹配零个或多个字符
        - ? 匹配单个字符
        - [seq] 匹配 seq 中的任意字符
        - [!seq] 匹配不在 seq 中的任意字符
        
        Args:
            pattern: 模式字符串 (e.g., "plugin.*")
            event_type: 事件类型 (e.g., "plugin.registered")
            
        Returns:
            是否匹配
        """
        return fnmatch.fnmatch(event_type, pattern)

    def shutdown(self) -> None:
        """
        关闭事件总线
        """
        self._running = False
        self._executor.shutdown(wait=True)
        self.clear_all_subscriptions()
        self.clear_history()
        self._logger.info("v5.0 CloudEvent EventBus shutdown completed")

    def __enter__(self) -> "EventBus":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口"""
        self.shutdown()


# v5.0 全局CloudEvent事件总线实例
default_event_bus = EventBus()


def subscribe_cloud_event(
    event_type: str, **kwargs: Any
) -> Callable[[Callable[[CloudEvent], Any]], Callable[[CloudEvent], Any]]:
    """
    装饰器：订阅CloudEvent事件

    Args:
        event_type: 事件类型
        **kwargs: 订阅参数

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[[CloudEvent], Any]) -> Callable[[CloudEvent], Any]:
        default_event_bus.subscribe(event_type, func, **kwargs)
        return func

    return decorator


# 为了保持API简洁，保留subscribe别名
subscribe = subscribe_cloud_event


def publish_cloud_event(cloud_event: CloudEvent, **kwargs: Any) -> List[Any]:
    """
    发布CloudEvent到默认事件总线

    Args:
        cloud_event: CloudEvent事件实例
        **kwargs: 发布参数

    Returns:
        处理结果列表
    """
    result = default_event_bus.publish_cloud_event(cloud_event, async_publish=False)
    # 强制使用同步模式
    if isinstance(result, list):
        return result
    else:
        # 如果不意外返回了Future，等待结果
        return result.result()


def emit(event_type: str, **kwargs: Any) -> List[Any]:
    """
    发布事件到默认事件总线（emit别名）

    Args:
        event_type: 事件类型
        **kwargs: 发布参数

    Returns:
        处理结果列表
    """
    result = default_event_bus.publish(event_type, async_publish=False, **kwargs)
    # 强制使用同步模式
    if isinstance(result, list):
        return result
    else:
        # 如果不意外返回了Future，等待结果
        return result.result()
