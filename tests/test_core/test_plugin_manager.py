# -*- coding: utf-8 -*-
"""
PluginManager 测试
确保100%测试覆盖率，包括所有方法、异常处理、插件发现
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simtradelab.core.event_bus import Event, EventBus
from simtradelab.core.plugin_manager import (
    PluginDiscoveryError,
    PluginLoadError,
    PluginManager,
    PluginRegistrationError,
    PluginRegistry,
)
from simtradelab.plugins.base import (
    BasePlugin,
    PluginConfig,
    PluginMetadata,
    PluginState,
)


@pytest.fixture(scope="function")
def event_bus():
    """A function-scoped event bus fixture."""
    bus = EventBus()
    # 确保EventBus处于运行状态
    assert bus._running is True
    yield bus
    bus.shutdown()


class TestPluginA(BasePlugin):
    """测试插件A"""

    METADATA = PluginMetadata(
        name="test_plugin_a",
        version="1.0.0",
        description="Test Plugin A",
        author="Test Author",
        dependencies=[],
        tags=["test"],
        category="testing",
        priority=50,
    )

    def __init__(self, metadata, config=None):
        super().__init__(metadata, config)
        self.init_called = False
        self.start_called = False
        self.stop_called = False

    def _on_initialize(self):
        self.init_called = True

    def _on_start(self):
        self.start_called = True

    def _on_stop(self):
        self.stop_called = True


class TestPluginB(BasePlugin):
    """测试插件B（无元数据）"""

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass


class FailingPlugin(BasePlugin):
    """会失败的测试插件"""

    METADATA = PluginMetadata(
        name="failing_plugin", version="1.0.0", description="Failing Plugin"
    )

    def _on_initialize(self):
        raise RuntimeError("Initialization failed")

    def _on_start(self):
        raise RuntimeError("Start failed")

    def _on_stop(self):
        raise RuntimeError("Stop failed")


class NotAPlugin:
    """不是插件的类"""

    pass


class StatefulPlugin(BasePlugin):
    """一个有状态的测试插件"""

    METADATA = PluginMetadata(name="stateful_plugin", version="1.0.0")

    def __init__(self, metadata, config=None):
        super().__init__(metadata, config)
        self.counter = 0

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass

    def increment(self):
        self.counter += 1

    def get_state(self):
        return {"counter": self.counter}

    def set_state(self, state):
        self.counter = state.get("counter", 0)


class TestPluginRegistry:
    """测试PluginRegistry"""

    def test_registry_creation(self):
        """测试注册信息创建"""
        metadata = PluginMetadata(name="test", version="1.0.0")
        config = PluginConfig()

        registry = PluginRegistry(
            plugin_class=TestPluginA,
            metadata=metadata,
            config=config,
            load_order=50,
        )

        assert registry.plugin_class is TestPluginA
        assert registry.metadata is metadata
        assert registry.config is config
        assert registry.instance is None
        assert registry.load_order == 50
        assert isinstance(registry.registered_at, float)


class TestPluginManager:
    """测试PluginManager基础功能"""

    @pytest.fixture
    def plugin_manager(self, event_bus):
        """插件管理器fixture"""
        manager = PluginManager(event_bus)
        yield manager
        manager.shutdown()

    def test_plugin_manager_creation(self):
        """测试插件管理器创建"""
        manager = PluginManager()

        assert manager.event_bus is not None
        assert isinstance(manager._plugins, dict)
        assert len(manager._plugins) == 0
        assert manager._stats["registered"] == 0

        manager.shutdown()

    def test_plugin_manager_with_event_bus(self, event_bus):
        """测试使用指定事件总线创建插件管理器"""
        manager = PluginManager(event_bus)

        assert manager.event_bus is event_bus

        manager.shutdown()

    def test_register_plugin_success(self, plugin_manager):
        """测试成功注册插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        assert plugin_name == "test_plugin_a"
        assert plugin_name in plugin_manager._plugins
        assert plugin_manager._stats["registered"] == 1

        registry = plugin_manager._plugins[plugin_name]
        assert registry.plugin_class is TestPluginA
        assert registry.metadata.name == "test_plugin_a"
        assert registry.instance is None

    def test_register_plugin_with_config(self, plugin_manager):
        """测试注册插件时提供配置"""
        config = PluginConfig()
        config.enabled = False
        plugin_name = plugin_manager.register_plugin(TestPluginA, config=config)

        registry = plugin_manager._plugins[plugin_name]
        assert registry.config is config

    def test_register_plugin_without_metadata(self, plugin_manager):
        """测试注册没有元数据的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginB)

        assert plugin_name == "TestPluginB"
        registry = plugin_manager._plugins[plugin_name]
        assert registry.metadata.name == "TestPluginB"
        assert registry.metadata.version == "1.0.0"

    def test_register_non_plugin_class(self, plugin_manager):
        """测试注册非插件类"""
        with pytest.raises(
            PluginRegistrationError, match="is not a BasePlugin subclass"
        ):
            plugin_manager.register_plugin(NotAPlugin)

    def test_register_duplicate_plugin(self, plugin_manager):
        """测试注册重复插件"""
        plugin_manager.register_plugin(TestPluginA)

        with pytest.raises(PluginRegistrationError, match="already registered"):
            plugin_manager.register_plugin(TestPluginA)

    def test_unregister_plugin_success(self, plugin_manager):
        """测试成功取消注册插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        success = plugin_manager.unregister_plugin(plugin_name)

        assert success is True
        assert plugin_name not in plugin_manager._plugins
        assert plugin_manager._stats["registered"] == 0

    def test_unregister_nonexistent_plugin(self, plugin_manager):
        """测试取消注册不存在的插件"""
        success = plugin_manager.unregister_plugin("nonexistent")

        assert success is False

    def test_unregister_loaded_plugin(self, plugin_manager):
        """测试取消注册已加载的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin(plugin_name)

        success = plugin_manager.unregister_plugin(plugin_name)

        assert success is True
        assert plugin_name not in plugin_manager._plugins

    def test_load_plugin_success(self, plugin_manager):
        """测试成功加载插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        instance = plugin_manager.load_plugin(plugin_name)

        assert isinstance(instance, TestPluginA)
        assert instance.init_called is True
        assert instance.state == PluginState.INITIALIZED
        assert plugin_manager._stats["loaded"] == 1

        registry = plugin_manager._plugins[plugin_name]
        assert registry.instance is instance

    def test_load_plugin_with_config(self, plugin_manager):
        """测试加载插件时提供配置"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        config = PluginConfig()
        config.enabled = False

        plugin_manager.load_plugin(plugin_name, config)

        registry = plugin_manager._plugins[plugin_name]
        assert registry.config is config

    def test_load_nonexistent_plugin(self, plugin_manager):
        """测试加载不存在的插件"""
        with pytest.raises(PluginLoadError, match="is not registered"):
            plugin_manager.load_plugin("nonexistent")

    def test_load_already_loaded_plugin(self, plugin_manager):
        """测试加载已加载的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin(plugin_name)

        with pytest.raises(PluginLoadError, match="already loaded"):
            plugin_manager.load_plugin(plugin_name)

    def test_load_failing_plugin(self, plugin_manager):
        """测试加载失败的插件"""
        plugin_name = plugin_manager.register_plugin(FailingPlugin)

        with pytest.raises(PluginLoadError, match="Failed to load plugin"):
            plugin_manager.load_plugin(plugin_name)

        assert plugin_manager._stats["failed"] == 1

    def test_unload_plugin_success(self, plugin_manager):
        """测试成功卸载插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin(plugin_name)
        plugin_manager.start_plugin(plugin_name)

        success = plugin_manager.unload_plugin(plugin_name)

        assert success is True
        registry = plugin_manager._plugins[plugin_name]
        assert registry.instance is None
        assert plugin_manager._stats["loaded"] == 0

    def test_unload_nonexistent_plugin(self, plugin_manager):
        """测试卸载不存在的插件"""
        success = plugin_manager.unload_plugin("nonexistent")

        assert success is False

    def test_unload_not_loaded_plugin(self, plugin_manager):
        """测试卸载未加载的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        success = plugin_manager.unload_plugin(plugin_name)

        assert success is False

    def test_start_plugin_success(self, plugin_manager):
        """测试成功启动插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        instance = plugin_manager.load_plugin(plugin_name)

        success = plugin_manager.start_plugin(plugin_name)

        assert success is True
        assert instance.start_called is True
        assert instance.state == PluginState.STARTED
        assert plugin_manager._stats["active"] == 1

    def test_start_nonexistent_plugin(self, plugin_manager):
        """测试启动不存在的插件"""
        success = plugin_manager.start_plugin("nonexistent")

        assert success is False

    def test_start_not_loaded_plugin(self, plugin_manager):
        """测试启动未加载的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        success = plugin_manager.start_plugin(plugin_name)

        assert success is False

    def test_stop_plugin_success(self, plugin_manager):
        """测试成功停止插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        instance = plugin_manager.load_plugin(plugin_name)
        plugin_manager.start_plugin(plugin_name)

        success = plugin_manager.stop_plugin(plugin_name)

        assert success is True
        assert instance.stop_called is True
        assert instance.state == PluginState.STOPPED
        assert plugin_manager._stats["active"] == 0

    def test_stop_nonexistent_plugin(self, plugin_manager):
        """测试停止不存在的插件"""
        success = plugin_manager.stop_plugin("nonexistent")

        assert success is False

    def test_stop_not_loaded_plugin(self, plugin_manager):
        """测试停止未加载的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        success = plugin_manager.stop_plugin(plugin_name)

        assert success is False

    def test_stop_not_started_plugin(self, plugin_manager):
        """测试停止未启动的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin(plugin_name)

        success = plugin_manager.stop_plugin(plugin_name)

        assert success is True  # 停止未启动的插件应该成功

    def test_get_plugin_success(self, plugin_manager):
        """测试获取插件实例"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        instance = plugin_manager.load_plugin(plugin_name)

        retrieved = plugin_manager.get_plugin(plugin_name)

        assert retrieved is instance

    def test_get_nonexistent_plugin(self, plugin_manager):
        """测试获取不存在的插件"""
        retrieved = plugin_manager.get_plugin("nonexistent")

        assert retrieved is None

    def test_get_not_loaded_plugin(self, plugin_manager):
        """测试获取未加载的插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        retrieved = plugin_manager.get_plugin(plugin_name)

        assert retrieved is None

    def test_get_plugin_info_success(self, plugin_manager):
        """测试获取插件信息"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin(plugin_name)

        info = plugin_manager.get_plugin_info(plugin_name)

        assert info is not None
        assert info["name"] == "test_plugin_a"
        assert info["version"] == "1.0.0"
        assert info["loaded"] is True
        assert info["state"] == "initialized"
        assert "uptime" in info
        assert "status" in info

    def test_get_plugin_info_not_loaded(self, plugin_manager):
        """测试获取未加载插件的信息"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)

        info = plugin_manager.get_plugin_info(plugin_name)

        assert info is not None
        assert info["loaded"] is False
        assert info["state"] == "unloaded"
        assert "uptime" not in info

    def test_get_plugin_info_nonexistent(self, plugin_manager):
        """测试获取不存在插件的信息"""
        info = plugin_manager.get_plugin_info("nonexistent")

        assert info is None

    def test_list_plugins_all(self, plugin_manager):
        """测试列出所有插件"""
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.register_plugin(TestPluginB)

        plugins = plugin_manager.list_plugins()

        assert len(plugins) == 2
        assert "test_plugin_a" in plugins
        assert "TestPluginB" in plugins

    def test_list_plugins_loaded(self, plugin_manager):
        """测试列出已加载的插件"""
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.register_plugin(TestPluginB)
        plugin_manager.load_plugin("test_plugin_a")

        loaded = plugin_manager.list_plugins(filter_loaded=True)
        unloaded = plugin_manager.list_plugins(filter_loaded=False)

        assert loaded == ["test_plugin_a"]
        assert unloaded == ["TestPluginB"]


class TestPluginManagerReloading:
    """测试插件热重载功能"""

    @pytest.fixture
    def plugin_manager(self, event_bus):
        manager = PluginManager(event_bus)
        # 确保EventBus处于运行状态
        assert manager.event_bus._running is True
        manager.register_plugin(StatefulPlugin)
        yield manager
        manager.shutdown()

    def test_reload_plugin_with_state_migration(self, plugin_manager):
        """测试热重载时状态迁移是否成功"""
        plugin_name = "stateful_plugin"

        # 1. 加载插件并修改状态
        instance1 = plugin_manager.load_plugin(plugin_name)
        assert isinstance(instance1, StatefulPlugin)
        instance1.increment()
        instance1.increment()
        assert instance1.counter == 2

        # 2. 热重载插件
        success = plugin_manager.reload_plugin(plugin_name)
        assert success is True

        # 3. 获取新实例并验证状态
        instance2 = plugin_manager.get_plugin(plugin_name)
        assert instance2 is not None
        assert instance2 is not instance1  # 确保是新实例
        assert isinstance(instance2, StatefulPlugin)
        assert instance2.counter == 2  # 状态应该被恢复

    def test_reload_not_loaded_plugin(self, plugin_manager):
        """测试重载一个未加载的插件（应该会直接加载）"""
        plugin_name = "stateful_plugin"
        assert plugin_manager.get_plugin(plugin_name) is None

        success = plugin_manager.reload_plugin(plugin_name)
        assert success is True
        assert plugin_manager.get_plugin(plugin_name) is not None

    def test_reload_plugin_emits_event(self, plugin_manager, event_bus):
        """测试插件重载时是否发出正确的事件"""
        plugin_name = "stateful_plugin"

        # 设置事件监听器
        events_received = []

        def event_handler(event):
            events_received.append(event)

        # 订阅插件重载事件
        event_bus.subscribe("plugin.reloaded", event_handler)

        # 加载插件
        plugin_manager.load_plugin(plugin_name)

        # 重载插件
        success = plugin_manager.reload_plugin(plugin_name)
        assert success is True

        # 验证事件是否被发出
        assert len(events_received) == 1
        event = events_received[0]
        assert event.type == "plugin.reloaded"
        assert event.data["plugin_name"] == plugin_name
        assert "instance" in event.data
        assert event.source == "plugin_manager"
