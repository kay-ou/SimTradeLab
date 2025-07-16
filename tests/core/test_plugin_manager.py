# -*- coding: utf-8 -*-
"""
PluginManager 核心功能测试

该测试文件旨在全面验证 PluginManager 的核心功能，确保其在各种场景下的稳定性、
可靠性和可扩展性。测试重点包括：
1.  插件注册与注销的原子性与正确性。
2.  插件完整的生命周期管理（加载、启动、停止、卸载）。
3.  插件热重载及其状态保持能力。
4.  从目录动态发现和加载插件的机制。
5.  强大的错误隔离机制和系统稳定性。
6.  在并发环境下的线程安全性。
7.  与事件总线的集成和事件发布。
"""

import threading
import time
from typing import Optional
from unittest.mock import MagicMock

import pytest
from pydantic import Field

from simtradelab.core.event_bus import EventBus
from simtradelab.core.plugin_manager import (
    PluginLoadError,
    PluginManager,
    PluginRegistrationError,
)
from simtradelab.plugins.base import (
    BasePlugin,
    PluginError,
    PluginMetadata,
    PluginState,
)
from simtradelab.plugins.config.base_config import BasePluginConfig

# region Test Plugin Definitions
# ==============================================================================
# 定义一系列用于测试的模拟插件，覆盖不同场景
# ==============================================================================


class SimplePlugin(BasePlugin):
    """一个最简单的插件，用于基础功能测试"""

    METADATA = PluginMetadata(name="simple_plugin", version="1.0.0")

    def _on_initialize(self):
        self.initialized = True

    def _on_start(self):
        self.started = True

    def _on_stop(self):
        self.stopped = True


class DependentPlugin(BasePlugin):
    """一个依赖于 SimplePlugin 的插件"""

    METADATA = PluginMetadata(
        name="dependent_plugin", version="1.0.0", dependencies=["simple_plugin"]
    )

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass


class StatefulPlugin(BasePlugin):
    """一个有状态的插件，用于测试热重载和状态保持"""

    METADATA = PluginMetadata(name="stateful_plugin", version="1.0.0")

    def __init__(self, metadata, config=None):
        super().__init__(metadata, config)
        self.counter = 0
        self.data = []

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass

    def process(self, item):
        """模拟处理业务"""
        self.counter += 1
        self.data.append(item)

    def get_state(self):
        """获取插件状态，用于持久化"""
        return {"counter": self.counter, "data": self.data}

    def set_state(self, state):
        """恢复插件状态"""
        self.counter = state.get("counter", 0)
        self.data = state.get("data", [])


class FailingPluginConfig(BasePluginConfig):
    """FailingPlugin 的配置模型"""

    fail_on: Optional[str] = Field(None, description="在哪个阶段失败")


class FailingPlugin(BasePlugin):
    """一个在不同生命周期阶段会失败的插件，用于测试错误处理"""

    METADATA = PluginMetadata(name="failing_plugin", version="1.0.0")
    config_model = FailingPluginConfig

    def __init__(self, metadata, config: FailingPluginConfig):
        super().__init__(metadata, config)
        self.fail_on = config.fail_on

    def _on_initialize(self):
        if self.fail_on == "initialize":
            raise RuntimeError("Initialization failed intentionally")

    def _on_start(self):
        if self.fail_on == "start":
            raise RuntimeError("Start failed intentionally")

    def _on_stop(self):
        if self.fail_on == "stop":
            raise RuntimeError("Stop failed intentionally")

    def _on_shutdown(self):
        if self.fail_on == "shutdown":
            raise RuntimeError("Shutdown failed intentionally")


# endregion

# region Fixtures
# ==============================================================================
# Pytest Fixtures，用于准备测试环境
# ==============================================================================


@pytest.fixture
def event_bus():
    """提供一个 EventBus 实例，并在测试结束后自动关闭"""
    bus = EventBus()
    yield bus
    bus.shutdown()


@pytest.fixture
def plugin_manager(event_bus):
    """提供一个 PluginManager 实例，并在测试结束后自动关闭"""
    manager = PluginManager(event_bus=event_bus, register_core_plugins=False)
    yield manager
    manager.shutdown()


# endregion


class TestPluginRegistration:
    """测试插件的注册和注销功能"""

    def test_register_plugin_success(self, plugin_manager):
        """测试成功注册一个插件"""
        plugin_name = plugin_manager.register_plugin(SimplePlugin)
        assert plugin_name == "simple_plugin"
        assert "simple_plugin" in plugin_manager.list_plugins()
        assert plugin_manager.get_plugin("simple_plugin") is None  # 尚未加载

    def test_register_plugin_with_custom_load_order(self, plugin_manager):
        """测试使用自定义加载顺序注册插件"""
        plugin_manager.register_plugin(SimplePlugin, load_order=50)
        plugin_info = plugin_manager.get_plugin_info("simple_plugin")
        assert plugin_info["load_order"] == 50

    def test_register_duplicate_plugin_fails(self, plugin_manager):
        """测试重复注册同一个插件会失败"""
        plugin_manager.register_plugin(SimplePlugin)
        with pytest.raises(
            PluginRegistrationError, match="Plugin simple_plugin is already registered"
        ):
            plugin_manager.register_plugin(SimplePlugin)

    def test_register_invalid_plugin_type_fails(self, plugin_manager):
        """测试注册一个非 BasePlugin 子类会失败"""

        class NotAPlugin:
            pass

        with pytest.raises(
            PluginRegistrationError, match="is not a valid BasePlugin subclass"
        ):
            plugin_manager.register_plugin(NotAPlugin)

    def test_unregister_plugin_success(self, plugin_manager):
        """测试成功注销一个插件"""
        plugin_name = plugin_manager.register_plugin(SimplePlugin)
        assert plugin_name in plugin_manager.list_plugins()

        unregistered = plugin_manager.unregister_plugin(plugin_name)
        assert unregistered is True
        assert plugin_name not in plugin_manager.list_plugins()

    def test_unregister_nonexistent_plugin(self, plugin_manager):
        """测试注销一个不存在的插件"""
        assert plugin_manager.unregister_plugin("nonexistent") is False

    def test_unregister_loaded_plugin(self, plugin_manager):
        """测试注销一个已加载的插件会自动先卸载"""
        plugin_name = plugin_manager.register_plugin(SimplePlugin)
        plugin_manager.load_plugin(plugin_name)
        assert plugin_manager.get_plugin(plugin_name) is not None

        unregistered = plugin_manager.unregister_plugin(plugin_name)
        assert unregistered is True
        assert plugin_name not in plugin_manager.list_plugins()
        assert plugin_manager.get_plugin(plugin_name) is None


class TestPluginLifecycle:
    """测试插件完整的生命周期管理"""

    @pytest.fixture(autouse=True)
    def setup(self, plugin_manager):
        """为本类所有测试注册 SimplePlugin"""
        self.plugin_name = plugin_manager.register_plugin(SimplePlugin)

    def test_load_plugin_success(self, plugin_manager):
        """测试成功加载插件"""
        instance = plugin_manager.load_plugin(self.plugin_name)
        assert isinstance(instance, SimplePlugin)
        assert instance.state == PluginState.INITIALIZED
        assert instance.initialized is True
        assert plugin_manager.get_plugin(self.plugin_name) is instance

    def test_load_non_registered_plugin_fails(self, plugin_manager):
        """测试加载未注册的插件会失败"""
        with pytest.raises(PluginLoadError, match="is not registered"):
            plugin_manager.load_plugin("nonexistent")

    def test_load_already_loaded_plugin_fails(self, plugin_manager):
        """测试重复加载插件会失败"""
        plugin_manager.load_plugin(self.plugin_name)
        with pytest.raises(PluginLoadError, match="is already loaded"):
            plugin_manager.load_plugin(self.plugin_name)

    def test_start_plugin_success(self, plugin_manager):
        """测试成功启动插件"""
        instance = plugin_manager.load_plugin(self.plugin_name)
        plugin_manager.start_plugin(self.plugin_name)
        assert instance.state == PluginState.STARTED
        assert instance.started is True

    def test_stop_plugin_success(self, plugin_manager):
        """测试成功停止插件"""
        instance = plugin_manager.load_plugin(self.plugin_name)
        plugin_manager.start_plugin(self.plugin_name)
        plugin_manager.stop_plugin(self.plugin_name)
        assert instance.state == PluginState.STOPPED
        assert instance.stopped is True

    def test_unload_plugin_success(self, plugin_manager):
        """测试成功卸载插件"""
        plugin_manager.load_plugin(self.plugin_name)
        plugin_manager.start_plugin(self.plugin_name)
        unloaded = plugin_manager.unload_plugin(self.plugin_name)
        assert unloaded is True
        assert plugin_manager.get_plugin(self.plugin_name) is None

    def test_load_all_and_unload_all(self, plugin_manager):
        """测试批量加载和卸载插件"""
        plugin_manager.register_plugin(DependentPlugin)

        # 按加载顺序排序
        load_results = plugin_manager.load_all_plugins(start=True)
        assert load_results["simple_plugin"] is True
        assert load_results["dependent_plugin"] is True
        assert plugin_manager.get_plugin("simple_plugin").state == PluginState.STARTED
        assert (
            plugin_manager.get_plugin("dependent_plugin").state == PluginState.STARTED
        )

        # 按加载顺序逆序卸载
        unload_results = plugin_manager.unload_all_plugins()
        assert unload_results["simple_plugin"] is True
        assert unload_results["dependent_plugin"] is True
        assert plugin_manager.get_plugin("simple_plugin") is None
        assert plugin_manager.get_plugin("dependent_plugin") is None


class TestPluginHotReload:
    """测试插件热重载与状态保持"""

    @pytest.fixture
    def stateful_plugin(self, plugin_manager):
        """提供一个已加载并运行的有状态插件"""
        plugin_name = plugin_manager.register_plugin(StatefulPlugin)
        instance = plugin_manager.load_plugin(plugin_name)
        plugin_manager.start_plugin(plugin_name)
        return instance

    def test_reload_with_state_preservation(self, plugin_manager, stateful_plugin):
        """测试热重载能成功保持和恢复状态"""
        # 1. 模拟业务操作，改变插件状态
        stateful_plugin.process("item1")
        stateful_plugin.process("item2")
        assert stateful_plugin.counter == 2
        assert stateful_plugin.data == ["item1", "item2"]

        # 2. 执行热重载
        reloaded = plugin_manager.reload_plugin("stateful_plugin")
        assert reloaded is True

        # 3. 获取重载后的新实例
        new_instance = plugin_manager.get_plugin("stateful_plugin")
        assert new_instance is not None
        assert new_instance is not stateful_plugin  # 确认是新实例
        assert new_instance.state == PluginState.INITIALIZED  # 重载后回到初始化状态

        # 4. 验证状态已恢复
        assert new_instance.counter == 2
        assert new_instance.data == ["item1", "item2"]

        # 5. 启动新实例并继续业务操作
        plugin_manager.start_plugin("stateful_plugin")
        new_instance.process("item3")
        assert new_instance.counter == 3
        assert new_instance.data == ["item1", "item2", "item3"]


class TestErrorHandling:
    """测试插件管理器的错误处理和隔离机制"""

    def test_load_fail_on_initialize(self, plugin_manager):
        """测试插件在初始化阶段失败"""
        plugin_name = plugin_manager.register_plugin(FailingPlugin)
        config = {"fail_on": "initialize"}

        # 捕获异常并检查其 cause
        with pytest.raises(PluginLoadError) as excinfo:
            plugin_manager.load_plugin(plugin_name, config=config)

        # 在 with 块之外进行断言
        # BasePlugin.initialize() 方法会将 RuntimeError 包装成 PluginError
        assert isinstance(excinfo.value.__cause__, PluginError)
        assert "Initialization failed intentionally" in str(excinfo.value.__cause__)

        # 验证失败的插件未被加载
        assert plugin_manager.get_plugin(plugin_name) is None
        stats = plugin_manager.get_stats()
        assert stats["failed"] == 1

    def test_start_fail_on_start(self, plugin_manager):
        """测试插件在启动阶段失败"""
        plugin_name = plugin_manager.register_plugin(FailingPlugin)
        # 提供一个在启动时会失败的配置
        config = {"fail_on": "start"}
        # 加载应该成功
        plugin_manager.load_plugin(plugin_name, config=config)

        # 启动应该失败并返回 False
        assert plugin_manager.start_plugin(plugin_name) is False

        # 验证插件状态为 ERROR
        instance = plugin_manager.get_plugin(plugin_name)
        assert instance.state == PluginState.ERROR

    def test_error_isolation(self, plugin_manager):
        """测试一个插件的失败不影响其他插件"""
        # 注册一个会失败的插件和一个正常的插件
        plugin_manager.register_plugin(FailingPlugin)
        plugin_manager.register_plugin(SimplePlugin)

        # 批量加载和启动
        # 注意：load_all_plugins 会使用注册时的配置，这里我们需要在加载时提供配置
        # 因此我们手动加载
        plugin_manager.load_plugin("simple_plugin")
        plugin_manager.start_plugin("simple_plugin")

        with pytest.raises(PluginLoadError):
            plugin_manager.load_plugin(
                "failing_plugin", config={"fail_on": "initialize"}
            )

        # 验证正常插件的状态
        simple_plugin = plugin_manager.get_plugin("simple_plugin")
        assert simple_plugin is not None
        assert simple_plugin.state == PluginState.STARTED

        # 验证失败的插件未被加载
        assert plugin_manager.get_plugin("failing_plugin") is None


class TestConcurrency:
    """测试插件管理器在多线程环境下的线程安全性"""

    def test_concurrent_register_and_load(self, plugin_manager):
        """测试多线程并发注册和加载插件"""
        num_threads = 10
        errors = []

        def worker(plugin_id):
            try:
                # 每个线程定义自己独特的插件
                class ThreadPlugin(BasePlugin):
                    METADATA = PluginMetadata(
                        name=f"thread_plugin_{plugin_id}", version="1.0.0"
                    )

                    def _on_initialize(self):
                        pass

                    def _on_start(self):
                        pass

                    def _on_stop(self):
                        pass

                plugin_name = plugin_manager.register_plugin(ThreadPlugin)
                time.sleep(0.01)  # 增加并发冲突的可能性
                plugin_manager.load_plugin(plugin_name)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(i,)) for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent operations failed with errors: {errors}"
        assert len(plugin_manager.list_plugins(filter_loaded=True)) == num_threads


class TestEventBusIntegration:
    """测试插件管理器与事件总线的集成"""

    def test_plugin_lifecycle_events_are_published(self):
        """验证插件生命周期事件被正确发布"""
        # 手动创建实例以完全控制生命周期
        bus = EventBus()
        # 关键：先创建不带 event_bus 的 manager
        manager = PluginManager(register_core_plugins=False)

        mock_handler = MagicMock()
        bus.subscribe("plugin.*", mock_handler)

        # 关键：在所有操作之前，将带有订阅者的 bus 设置给 manager
        manager.set_event_bus(bus)

        # 1. 触发所有生命周期事件
        plugin_name = manager.register_plugin(SimplePlugin)
        instance = manager.load_plugin(plugin_name)
        assert instance is not None
        assert isinstance(instance, SimplePlugin)
        manager.start_plugin(plugin_name)
        manager.stop_plugin(plugin_name)
        manager.unload_plugin(plugin_name)
        manager.unregister_plugin(plugin_name)

        # 2. 手动关闭总线以确保所有事件都被处理
        bus.shutdown()

        # 3. 验证总调用次数
        assert mock_handler.call_count == 6

        # 4. 验证事件类型顺序
        expected_event_types = [
            "plugin.registered",
            "plugin.loaded",
            "plugin.started",
            "plugin.stopped",
            "plugin.unloaded",
            "plugin.unregistered",
        ]
        called_event_types = [call.args[0].type for call in mock_handler.call_args_list]
        assert called_event_types == expected_event_types

        # 5. 详细验证某个事件的内容
        reg_event = mock_handler.call_args_list[0].args[0]
        assert reg_event.source == "plugin_manager"
        assert reg_event.data["plugin_name"] == "simple_plugin"
