# -*- coding: utf-8 -*-
"""
一个简单的示例插件，用于演示如何使用 BasePluginTest 进行测试。
"""
from simtradelab.core.events.cloud_event import CloudEvent
from simtradelab.plugins.base import BasePlugin, PluginMetadata


class HelloPlugin(BasePlugin):
    """
    一个简单的 “Hello, World” 插件。

    它订阅 "hello" 事件，并在收到该事件时，发布一个 "world" 事件。
    """

    METADATA = PluginMetadata(name="HelloPlugin", version="0.1.0")

    def _on_initialize(self) -> None:
        if self.event_bus:
            self.event_bus.subscribe("hello", self.on_hello_event)

    def _on_start(self) -> None:
        pass

    def _on_stop(self) -> None:
        pass

    def on_hello_event(self, event: CloudEvent):
        """
        处理 "hello" 事件，并发布 "world" 事件。
        """
        if self.event_bus:
            response_event = CloudEvent(
                type="world", source="HelloPlugin", data={"message": "world"}
            )
            self.event_bus.publish(response_event)
