# -*- coding: utf-8 -*-
"""
HelloPlugin 的单元测试示例。
"""
from hello_plugin.hello_plugin import HelloPlugin

from simtradelab.core.events.cloud_event import CloudEvent
from tests.support.base_plugin_test import BasePluginTest


class TestHelloPlugin(BasePluginTest):
    """
    测试 HelloPlugin 的功能。
    """

    def test_initialization_subscribes_to_event(self):
        """
        测试：插件初始化时，应正确订阅 "hello" 事件。
        """
        # 实例化插件
        plugin = HelloPlugin(metadata=HelloPlugin.METADATA)
        # 手动注入模拟的 event_bus
        plugin.set_event_bus(self.mocks["event_bus"])

        # 初始化插件
        plugin.initialize()

        # 断言：event_bus.subscribe 方法被以正确的参数调用
        self.mocks["event_bus"].subscribe.assert_called_once_with(
            "hello", plugin.on_hello_event
        )

    def test_on_hello_event_emits_world_event(self):
        """
        测试：当 on_hello_event 被调用时，应发布一个 "world" 事件。
        """
        # 实例化并初始化插件
        plugin = HelloPlugin(metadata=HelloPlugin.METADATA)
        plugin.set_event_bus(self.mocks["event_bus"])
        plugin.initialize()

        # 模拟一个 "hello" 事件
        hello_event = CloudEvent(type="hello", source="test", data={})

        # 调用事件处理函数
        plugin.on_hello_event(hello_event)

        # 断言：event_bus.emit 方法被调用了一次
        self.mocks["event_bus"].publish.assert_called_once()

        # 获取被发布的事件
        emitted_event = self.mocks["event_bus"].publish.call_args[0][0]

        # 断言：发布的事件是我们期望的 "world" 事件
        assert isinstance(emitted_event, CloudEvent)
        assert emitted_event.type == "world"
        assert emitted_event.source == "HelloPlugin"
        assert emitted_event.data == {"message": "world"}
