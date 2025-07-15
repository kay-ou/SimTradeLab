# -*- coding: utf-8 -*-
"""
BasePlugin 测试
确保100%测试覆盖率，包括所有方法、异常处理、状态转换
"""

import asyncio
import threading
import time
from unittest.mock import patch

import pytest

from simtradelab.plugins.base import (
    BasePlugin,
    PluginConfig,
    PluginConfigError,
    PluginError,
    PluginMetadata,
    PluginState,
    PluginStateError,
)


class MockPlugin(BasePlugin):
    """测试用插件实现"""

    def __init__(self, metadata, config=None, fail_on=None):
        super().__init__(metadata, config)
        self.fail_on = fail_on or []
        self.call_history = []

    def _on_initialize(self):
        self.call_history.append("initialize")
        if "initialize" in self.fail_on:
            raise RuntimeError("Initialize failed")

    def _on_start(self):
        self.call_history.append("start")
        if "start" in self.fail_on:
            raise RuntimeError("Start failed")

    def _on_stop(self):
        self.call_history.append("stop")
        if "stop" in self.fail_on:
            raise RuntimeError("Stop failed")

    def _on_pause(self):
        self.call_history.append("pause")
        if "pause" in self.fail_on:
            raise RuntimeError("Pause failed")

    def _on_resume(self):
        self.call_history.append("resume")
        if "resume" in self.fail_on:
            raise RuntimeError("Resume failed")

    def _on_shutdown(self):
        self.call_history.append("shutdown")
        if "shutdown" in self.fail_on:
            raise RuntimeError("Shutdown failed")

    def _validate_config(self, config):
        # E9修复：适应Pydantic配置对象
        if hasattr(config, "config") and isinstance(config.config, dict):
            if "invalid_key" in config.config:
                raise PluginConfigError("Invalid configuration")
        elif isinstance(config, dict) and "invalid_key" in config:
            raise PluginConfigError("Invalid configuration")

    def _on_config_changed(self, old_config, new_config):
        self.call_history.append("config_changed")
        if "config_change" in self.fail_on:
            raise RuntimeError("Config change failed")


class MockResource:
    """模拟资源类"""

    def __init__(self, close_method="close"):
        self.closed = False
        self.close_method = close_method

    def close(self):
        self.closed = True

    def cleanup(self):
        self.closed = True


class TestPluginMetadata:
    """测试PluginMetadata"""

    def test_metadata_creation(self):
        """测试元数据创建"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            dependencies=["dep1", "dep2"],
            tags=["test", "sample"],
            category="testing",
            priority=50,
        )

        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"
        assert metadata.author == "Test Author"
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.tags == ["test", "sample"]
        assert metadata.category == "testing"
        assert metadata.priority == 50

    def test_metadata_defaults(self):
        """测试元数据默认值"""
        metadata = PluginMetadata(name="test", version="1.0.0")

        assert metadata.description == ""
        assert metadata.author == ""
        assert metadata.dependencies == []
        assert metadata.tags == []
        assert metadata.category == "general"
        assert metadata.priority == 100


class TestPluginConfig:
    """测试PluginConfig"""

    def test_config_creation(self):
        """测试配置创建"""
        config = PluginConfig(
            enabled=True,
            config={"key": "value"},
            auto_start=False,
            restart_on_error=True,
            max_retries=5,
            timeout=30.0,
        )

        assert config.enabled is True
        assert config.config == {"key": "value"}
        assert config.auto_start is False
        assert config.restart_on_error is True
        assert config.max_retries == 5
        assert config.timeout == 30.0

    def test_config_defaults(self):
        """测试配置默认值"""
        config = PluginConfig()

        assert config.enabled is True
        assert config.config == {}
        assert config.auto_start is True
        assert config.restart_on_error is False
        assert config.max_retries == 3
        assert config.timeout is None


class TestBasePlugin:
    """测试BasePlugin基础功能"""

    @pytest.fixture
    def metadata(self):
        """插件元数据fixture"""
        return PluginMetadata(
            name="test_plugin", version="1.0.0", description="Test plugin"
        )

    @pytest.fixture
    def config(self):
        """插件配置fixture"""
        return PluginConfig(enabled=True, config={"test_key": "test_value"})

    @pytest.fixture
    def plugin(self, metadata, config):
        """插件实例fixture"""
        return MockPlugin(metadata, config)

    def test_plugin_creation(self, metadata, config):
        """测试插件创建"""
        plugin = MockPlugin(metadata, config)

        assert plugin.metadata is metadata
        assert plugin.config is config
        assert plugin.state == PluginState.UNINITIALIZED
        assert plugin.logger.name == "plugin.test_plugin"
        assert plugin.is_running is False
        assert plugin.uptime is None

    def test_plugin_creation_with_default_config(self, metadata):
        """测试使用默认配置创建插件"""
        plugin = MockPlugin(metadata)

        assert isinstance(plugin.config, PluginConfig)
        assert plugin.config.enabled is True

    def test_get_status(self, plugin):
        """测试获取状态"""
        status = plugin.get_status()

        assert status["name"] == "test_plugin"
        assert status["version"] == "1.0.0"
        assert status["state"] == "uninitialized"
        assert status["enabled"] is True
        assert status["uptime"] is None
        assert status["error_count"] == 0
        assert status["last_error"] is None
        assert status["start_time"] is None

    def test_initialize_success(self, plugin):
        """测试成功初始化"""
        plugin.initialize()

        assert plugin.state == PluginState.INITIALIZED
        assert "initialize" in plugin.call_history

    def test_initialize_failure(self, metadata):
        """测试初始化失败"""
        plugin = MockPlugin(metadata, fail_on=["initialize"])

        with pytest.raises(PluginError, match="Plugin initialization failed"):
            plugin.initialize()

        assert plugin.state == PluginState.ERROR
        assert plugin._error_count == 1
        assert isinstance(plugin._last_error, RuntimeError)

    def test_initialize_already_initialized(self, plugin):
        """测试重复初始化"""
        plugin.initialize()

        with pytest.raises(PluginStateError, match="already initialized"):
            plugin.initialize()

    def test_start_success(self, plugin):
        """测试成功启动"""
        plugin.initialize()

        start_time_before = time.time()
        plugin.start()
        start_time_after = time.time()

        assert plugin.state == PluginState.STARTED
        assert plugin.is_running is True
        assert plugin.uptime is not None
        assert start_time_before <= plugin._start_time <= start_time_after
        assert "start" in plugin.call_history

    def test_start_disabled_plugin(self, metadata):
        """测试启动禁用的插件"""
        config = PluginConfig(enabled=False)
        plugin = MockPlugin(metadata, config)
        plugin.initialize()

        plugin.start()  # 应该不会抛出异常

        assert plugin.state == PluginState.INITIALIZED  # 状态不变
        assert "start" not in plugin.call_history

    def test_start_failure(self, metadata):
        """测试启动失败"""
        plugin = MockPlugin(metadata, fail_on=["start"])
        plugin.initialize()

        with pytest.raises(PluginError, match="Plugin start failed"):
            plugin.start()

        assert plugin.state == PluginState.ERROR
        assert plugin._error_count == 1

    def test_start_invalid_state(self, plugin):
        """测试从无效状态启动"""
        with pytest.raises(PluginStateError, match="cannot be started"):
            plugin.start()

    def test_stop_success(self, plugin):
        """测试成功停止"""
        plugin.initialize()
        plugin.start()

        plugin.stop()

        assert plugin.state == PluginState.STOPPED
        assert plugin.is_running is False
        assert plugin._start_time is None
        assert "stop" in plugin.call_history

    def test_stop_not_running(self, plugin):
        """测试停止未运行的插件"""
        plugin.initialize()

        plugin.stop()  # 应该不抛出异常，只是警告

        assert plugin.state == PluginState.INITIALIZED

    def test_stop_failure(self, metadata):
        """测试停止失败"""
        plugin = MockPlugin(metadata, fail_on=["stop"])
        plugin.initialize()
        plugin.start()

        with pytest.raises(PluginError, match="Plugin stop failed"):
            plugin.stop()

        assert plugin.state == PluginState.ERROR

    def test_pause_success(self, plugin):
        """测试成功暂停"""
        plugin.initialize()
        plugin.start()

        plugin.pause()

        assert plugin.state == PluginState.PAUSED
        assert "pause" in plugin.call_history

    def test_pause_not_running(self, plugin):
        """测试暂停未运行的插件"""
        plugin.initialize()

        with pytest.raises(PluginStateError, match="is not running"):
            plugin.pause()

    def test_pause_failure(self, metadata):
        """测试暂停失败"""
        plugin = MockPlugin(metadata, fail_on=["pause"])
        plugin.initialize()
        plugin.start()

        with pytest.raises(PluginError, match="Plugin pause failed"):
            plugin.pause()

        assert plugin.state == PluginState.ERROR

    def test_resume_success(self, plugin):
        """测试成功恢复"""
        plugin.initialize()
        plugin.start()
        plugin.pause()

        plugin.resume()

        assert plugin.state == PluginState.STARTED
        assert "resume" in plugin.call_history

    def test_resume_not_paused(self, plugin):
        """测试恢复未暂停的插件"""
        plugin.initialize()
        plugin.start()

        with pytest.raises(PluginStateError, match="is not paused"):
            plugin.resume()

    def test_resume_failure(self, metadata):
        """测试恢复失败"""
        plugin = MockPlugin(metadata, fail_on=["resume"])
        plugin.initialize()
        plugin.start()
        plugin.pause()

        with pytest.raises(PluginError, match="Plugin resume failed"):
            plugin.resume()

        assert plugin.state == PluginState.ERROR

    def test_shutdown_from_running(self, plugin):
        """测试从运行状态关闭"""
        plugin.initialize()
        plugin.start()

        plugin.shutdown()

        assert plugin.state == PluginState.UNINITIALIZED
        assert plugin._start_time is None
        assert plugin._context == {}
        assert "stop" in plugin.call_history
        assert "shutdown" in plugin.call_history

    def test_shutdown_from_paused(self, plugin):
        """测试从暂停状态关闭"""
        plugin.initialize()
        plugin.start()
        plugin.pause()

        plugin.shutdown()

        assert plugin.state == PluginState.UNINITIALIZED
        assert "stop" in plugin.call_history
        assert "shutdown" in plugin.call_history

    def test_shutdown_failure(self, metadata):
        """测试关闭失败"""
        plugin = MockPlugin(metadata, fail_on=["shutdown"])
        plugin.initialize()

        with pytest.raises(PluginError, match="Plugin shutdown failed"):
            plugin.shutdown()

        assert plugin.state == PluginState.ERROR


class TestPluginConfiguration:
    """测试插件配置功能"""

    @pytest.fixture
    def plugin(self):
        metadata = PluginMetadata(name="test", version="1.0.0")
        return MockPlugin(metadata)

    def test_update_config_success(self, plugin):
        """测试成功更新配置"""
        new_config = {"new_key": "new_value"}

        plugin.update_config(new_config)

        assert plugin.config.config["new_key"] == "new_value"
        assert "config_changed" in plugin.call_history

    def test_update_config_validation_failure(self, plugin):
        """测试配置验证失败"""
        invalid_config = {"invalid_key": "value"}

        with pytest.raises(PluginConfigError, match="Invalid configuration"):
            plugin.update_config(invalid_config)

        assert "invalid_key" not in plugin.config.config

    def test_update_config_change_failure(self):
        """测试配置变更处理失败"""
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = MockPlugin(metadata, fail_on=["config_change"])

        old_config = plugin.config.config.copy()

        with pytest.raises(PluginConfigError, match="Failed to apply config changes"):
            plugin.update_config({"test_key": "test_value"})

        # 配置应该回滚
        assert plugin.config.config == old_config


class TestPluginEvents:
    """测试插件事件功能"""

    @pytest.fixture
    def plugin(self):
        metadata = PluginMetadata(name="test", version="1.0.0")
        return MockPlugin(metadata)

    def test_register_event_handler(self, plugin):
        """测试注册事件处理器"""

        def handler(data):
            return data * 2

        plugin.register_event_handler("test_event", handler)

        assert "test_event" in plugin._event_handlers
        assert handler in plugin._event_handlers["test_event"]

    def test_unregister_event_handler(self, plugin):
        """测试取消注册事件处理器"""

        def handler(data):
            return data * 2

        plugin.register_event_handler("test_event", handler)
        plugin.unregister_event_handler("test_event", handler)

        assert handler not in plugin._event_handlers.get("test_event", [])

    @pytest.mark.asyncio
    async def test_handle_event_sync_handler(self, plugin):
        """测试处理同步事件处理器"""

        def sync_handler(data):
            return data * 2

        plugin.register_event_handler("test_event", sync_handler)
        results = await plugin.handle_event("test_event", 5)

        assert results == [10]

    @pytest.mark.asyncio
    async def test_handle_event_async_handler(self, plugin):
        """测试处理异步事件处理器"""

        async def async_handler(data):
            return data * 3

        plugin.register_event_handler("test_event", async_handler)
        results = await plugin.handle_event("test_event", 5)

        assert results == [15]

    @pytest.mark.asyncio
    async def test_handle_event_multiple_handlers(self, plugin):
        """测试处理多个事件处理器"""

        def handler1(data):
            return data + 1

        def handler2(data):
            return data * 2

        plugin.register_event_handler("test_event", handler1)
        plugin.register_event_handler("test_event", handler2)

        results = await plugin.handle_event("test_event", 5)

        assert results == [6, 10]

    @pytest.mark.asyncio
    async def test_handle_event_handler_failure(self, plugin):
        """测试事件处理器失败"""

        def failing_handler(data):
            raise RuntimeError("Handler failed")

        def working_handler(data):
            return data * 2

        plugin.register_event_handler("test_event", failing_handler)
        plugin.register_event_handler("test_event", working_handler)

        results = await plugin.handle_event("test_event", 5)

        assert results == [None, 10]  # 失败的处理器返回None

    @pytest.mark.asyncio
    async def test_handle_event_no_handlers(self, plugin):
        """测试处理没有处理器的事件"""
        results = await plugin.handle_event("nonexistent_event", 5)

        assert results == []


class TestPluginResources:
    """测试插件资源管理"""

    @pytest.fixture
    def plugin(self):
        metadata = PluginMetadata(name="test", version="1.0.0")
        return MockPlugin(metadata)

    def test_add_and_cleanup_resources(self, plugin):
        """测试添加和清理资源"""
        resource1 = MockResource()
        resource2 = MockResource()

        plugin.add_resource(resource1)
        plugin.add_resource(resource2)

        plugin._cleanup_resources()

        assert resource1.closed is True
        assert resource2.closed is True
        assert len(plugin._resources) == 0

    def test_cleanup_resource_with_cleanup_method(self, plugin):
        """测试清理带cleanup方法的资源"""

        class ResourceWithCleanup:
            def __init__(self):
                self.closed = False

            def cleanup(self):
                self.closed = True

        resource = ResourceWithCleanup()
        plugin.add_resource(resource)
        plugin._cleanup_resources()

        assert resource.closed is True

    def test_cleanup_resource_failure(self, plugin):
        """测试资源清理失败"""

        class FailingResource:
            def close(self):
                raise RuntimeError("Close failed")

        resource = FailingResource()
        plugin.add_resource(resource)

        # 应该不抛出异常，只记录警告
        plugin._cleanup_resources()

        # 资源仍在列表中（清理失败）
        assert resource in plugin._resources

    def test_stop_cleanup_resources(self, plugin):
        """测试停止时清理资源"""
        resource = MockResource()
        plugin.add_resource(resource)

        plugin.initialize()
        plugin.start()
        plugin.stop()

        assert resource.closed is True


class TestPluginContext:
    """测试插件上下文功能"""

    @pytest.fixture
    def plugin(self):
        metadata = PluginMetadata(name="test", version="1.0.0")
        return MockPlugin(metadata)

    def test_set_and_get_context(self, plugin):
        """测试设置和获取上下文"""
        plugin.set_context("key1", "value1")
        plugin.set_context("key2", 42)

        assert plugin.get_context("key1") == "value1"
        assert plugin.get_context("key2") == 42

    def test_get_context_default(self, plugin):
        """测试获取不存在的上下文键"""
        assert plugin.get_context("nonexistent") is None
        assert plugin.get_context("nonexistent", "default") == "default"

    def test_context_cleared_on_shutdown(self, plugin):
        """测试关闭时清理上下文"""
        plugin.set_context("key", "value")
        plugin.initialize()

        plugin.shutdown()

        assert plugin._context == {}


class TestPluginThreadSafety:
    """测试插件线程安全"""

    @pytest.fixture
    def plugin(self):
        metadata = PluginMetadata(name="test", version="1.0.0")
        return MockPlugin(metadata)

    def test_concurrent_state_changes(self, plugin):
        """测试并发状态变更"""
        plugin.initialize()

        def start_stop_plugin():
            try:
                plugin.start()
                time.sleep(0.01)  # 短暂睡眠
                plugin.stop()
            except Exception:
                pass  # 忽略预期的状态错误

        threads = []
        for _ in range(5):
            thread = threading.Thread(target=start_stop_plugin)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 最终状态应该是一致的
        assert plugin.state in [
            PluginState.STARTED,
            PluginState.STOPPED,
            PluginState.ERROR,
        ]

    def test_concurrent_config_updates(self, plugin):
        """测试并发配置更新"""

        def update_config(value):
            try:
                plugin.update_config({"test_key": value})
            except Exception:
                pass  # 忽略可能的配置错误

        threads = []
        for i in range(10):
            thread = threading.Thread(target=update_config, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 配置应该包含某个值
        assert "test_key" in plugin.config.config


class TestPluginUptime:
    """测试插件运行时间"""

    @pytest.fixture
    def plugin(self):
        metadata = PluginMetadata(name="test", version="1.0.0")
        return MockPlugin(metadata)

    def test_uptime_calculation(self, plugin):
        """测试运行时间计算"""
        plugin.initialize()

        start_time = time.time()
        plugin.start()

        time.sleep(0.1)  # 等待100ms

        uptime = plugin.uptime
        elapsed = time.time() - start_time

        assert uptime is not None
        assert 0.05 <= uptime <= elapsed + 0.05  # 允许一些误差

    def test_uptime_reset_on_stop(self, plugin):
        """测试停止时重置运行时间"""
        plugin.initialize()
        plugin.start()
        plugin.stop()

        assert plugin.uptime is None


class TestPluginErrorHandling:
    """测试插件错误处理"""

    def test_error_count_increment(self):
        """测试错误计数递增"""
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = MockPlugin(metadata, fail_on=["initialize"])

        assert plugin._error_count == 0

        try:
            plugin.initialize()
        except PluginError:
            pass

        assert plugin._error_count == 1
        assert plugin._last_error is not None

    def test_status_includes_error_info(self):
        """测试状态包含错误信息"""
        metadata = PluginMetadata(name="test", version="1.0.0")
        plugin = MockPlugin(metadata, fail_on=["initialize"])

        try:
            plugin.initialize()
        except PluginError:
            pass

        status = plugin.get_status()
        assert status["error_count"] == 1
        assert status["last_error"] is not None

    def test_plugin_resource_cleanup_failure(self):
        """测试资源清理失败"""
        metadata = PluginMetadata(name="test_plugin", version="1.0.0")
        plugin = MockPlugin(metadata)

        # 创建会抛出异常的资源
        class FailingResource:
            def close(self):
                raise Exception("Cleanup failed")

        resource = FailingResource()
        plugin.add_resource(resource)

        # 清理资源时应该捕获异常并记录警告
        with patch.object(plugin._logger, "warning") as mock_warning:
            plugin._cleanup_resources()
            mock_warning.assert_called_once()

    def test_plugin_event_handler_failure(self):
        """测试事件处理器失败"""
        metadata = PluginMetadata(name="test_plugin", version="1.0.0")
        plugin = MockPlugin(metadata)

        def failing_handler(data):
            raise Exception("Handler failed")

        plugin.register_event_handler("test_event", failing_handler)

        # 事件处理应该捕获异常并记录错误
        with patch.object(plugin._logger, "error") as mock_error:
            results = asyncio.run(plugin.handle_event("test_event", "test_data"))
            mock_error.assert_called_once()
            assert results == [None]  # 失败的处理器返回None

    def test_plugin_mode_reset_on_unsupported_modes(self):
        """测试设置不支持的模式时重置当前模式"""
        from enum import Enum

        class TestMode(Enum):
            MODE1 = "mode1"
            MODE2 = "mode2"

        class OtherMode(Enum):
            OTHER = "other"

        metadata = PluginMetadata(name="test_plugin", version="1.0.0")
        plugin = MockPlugin(metadata)

        # 设置支持的模式
        plugin._set_supported_modes({TestMode.MODE1, TestMode.MODE2})
        plugin.set_mode(TestMode.MODE1)

        # 更新支持的模式，不包括当前模式
        plugin._set_supported_modes({OtherMode.OTHER})

        # 当前模式应该被重置为None
        assert plugin.get_current_mode() is None

    def test_plugin_default_validation_passes(self):
        """测试默认配置验证通过"""
        metadata = PluginMetadata(name="test_plugin", version="1.0.0")
        plugin = MockPlugin(metadata)

        # 默认的_validate_config应该什么都不做
        plugin._validate_config({"any": "config"})  # 应该不抛出异常

    def test_plugin_default_hooks_no_op(self):
        """测试默认钩子方法为空操作"""
        metadata = PluginMetadata(name="test_plugin", version="1.0.0")
        plugin = MockPlugin(metadata)

        # 测试默认钩子方法不抛出异常
        plugin._on_config_changed({}, {})
        plugin._on_mode_changed(None, None)
        plugin._on_pause()
        plugin._on_resume()
        plugin._on_shutdown()

    def test_plugin_resource_without_cleanup_method(self):
        """测试没有清理方法的资源"""
        metadata = PluginMetadata(name="test_plugin", version="1.0.0")
        plugin = MockPlugin(metadata)

        # 创建没有清理方法的资源
        class NoCleanupResource:
            pass

        resource = NoCleanupResource()
        plugin.add_resource(resource)

        # 清理应该尝试删除资源
        plugin._cleanup_resources()

        # 资源应该被移除
        assert len(plugin._resources) == 0
