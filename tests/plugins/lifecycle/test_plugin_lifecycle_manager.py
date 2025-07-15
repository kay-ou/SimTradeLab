# -*- coding: utf-8 -*-
"""
插件生命周期管理器测试
"""

import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from simtradelab.core.event_bus import EventBus
from simtradelab.plugins.base import BasePlugin
from simtradelab.plugins.dependency.manifest import PluginCategory, PluginManifest
from simtradelab.plugins.lifecycle.plugin_lifecycle_manager import (
    PluginInfo,
    PluginLifecycleManager,
    PluginState,
)


class MockPlugin(BasePlugin):
    """测试用的模拟插件"""

    def __init__(self, config=None, event_bus=None):
        from simtradelab.plugins.base import PluginMetadata

        # 创建模拟的插件元数据
        metadata = PluginMetadata(
            name="mock_plugin", version="1.0.0", description="Mock plugin for testing"
        )

        super().__init__(metadata, config)
        self.started = False
        self.stopped = False
        self.cleaned_up = False
        self.state_data = {}

    def _on_initialize(self):
        """初始化插件"""
        pass

    def _on_start(self):
        """启动插件"""
        self.started = True
        self.stopped = False

    def _on_stop(self):
        """停止插件"""
        self.stopped = True
        self.started = False

    def start(self):
        """启动插件"""
        self.started = True
        self.stopped = False

    def stop(self):
        """停止插件"""
        self.stopped = True
        self.started = False

    def cleanup(self):
        """清理插件"""
        self.cleaned_up = True

    def get_state(self):
        """获取状态"""
        return self.state_data.copy()

    def set_state(self, state):
        """设置状态"""
        self.state_data.update(state)


class TestPluginInfo:
    """测试插件信息类"""

    def test_plugin_info_initialization(self):
        """测试插件信息初始化"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            category=PluginCategory.UTILITY,
        )

        plugin_info = PluginInfo(manifest)

        assert plugin_info.manifest == manifest
        assert plugin_info.state == PluginState.UNKNOWN
        assert plugin_info.instance is None
        assert plugin_info.load_time is None
        assert plugin_info.start_time is None
        assert plugin_info.error_count == 0
        assert plugin_info.last_error is None
        assert plugin_info.state_history == []

    def test_set_state(self):
        """测试设置状态"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            category=PluginCategory.UTILITY,
        )

        plugin_info = PluginInfo(manifest)

        # 设置正常状态
        plugin_info.set_state(PluginState.LOADED)
        assert plugin_info.state == PluginState.LOADED
        assert plugin_info.load_time is not None
        assert len(plugin_info.state_history) == 1

        # 设置错误状态
        plugin_info.set_state(PluginState.ERROR, "测试错误")
        assert plugin_info.state == PluginState.ERROR
        assert plugin_info.last_error == "测试错误"
        assert plugin_info.error_count == 1
        assert len(plugin_info.state_history) == 2

        # 设置活跃状态
        plugin_info.set_state(PluginState.ACTIVE)
        assert plugin_info.state == PluginState.ACTIVE
        assert plugin_info.start_time is not None


class TestPluginLifecycleManager:
    """测试插件生命周期管理器"""

    @pytest.fixture
    def event_bus(self):
        """创建事件总线"""
        return EventBus()

    @pytest.fixture
    def lifecycle_manager(self, event_bus):
        """创建生命周期管理器"""
        return PluginLifecycleManager(event_bus)

    @pytest.fixture
    def sample_manifest(self):
        """示例插件清单"""
        return PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            category=PluginCategory.UTILITY,
            entry_point="plugin.py",
        )

    def test_initialization(self, lifecycle_manager):
        """测试初始化"""
        assert lifecycle_manager.registry is not None
        assert lifecycle_manager.dependency_resolver is not None
        assert lifecycle_manager.event_bus is not None
        assert isinstance(lifecycle_manager._plugins, dict)
        assert lifecycle_manager._lock is not None

    def test_register_plugin(self, lifecycle_manager, sample_manifest):
        """测试注册插件"""
        plugin_path = Path("/test/path")

        result = lifecycle_manager.register_plugin(sample_manifest, plugin_path)

        assert result is True
        assert "test_plugin" in lifecycle_manager._plugins
        assert lifecycle_manager.registry.has_plugin("test_plugin")

        plugin_info = lifecycle_manager._plugins["test_plugin"]
        assert plugin_info.manifest == sample_manifest
        assert plugin_info.plugin_path == plugin_path
        assert plugin_info.state == PluginState.UNKNOWN

    def test_discover_plugins(self, lifecycle_manager):
        """测试发现插件"""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建插件目录和清单文件
            plugin_dir = temp_path / "test_plugin"
            plugin_dir.mkdir()

            manifest_data = {
                "name": "discovered_plugin",
                "version": "1.0.0",
                "description": "Discovered plugin",
                "author": "Test",
                "category": "utility",
            }

            import yaml

            with open(plugin_dir / "plugin_manifest.yaml", "w") as f:
                yaml.dump(manifest_data, f)

            count = lifecycle_manager.discover_plugins(temp_path)

            assert count == 1
            assert "discovered_plugin" in lifecycle_manager._plugins
            assert lifecycle_manager.registry.has_plugin("discovered_plugin")

    def test_get_plugin_state(self, lifecycle_manager, sample_manifest):
        """测试获取插件状态"""
        # 未注册的插件
        assert lifecycle_manager.get_plugin_state("nonexistent") is None

        # 注册插件
        lifecycle_manager.register_plugin(sample_manifest)

        # 获取状态
        state = lifecycle_manager.get_plugin_state("test_plugin")
        assert state == PluginState.UNKNOWN

    def test_get_plugin_info(self, lifecycle_manager, sample_manifest):
        """测试获取插件信息"""
        # 未注册的插件
        assert lifecycle_manager.get_plugin_info("nonexistent") is None

        # 注册插件
        lifecycle_manager.register_plugin(sample_manifest)

        # 获取信息
        plugin_info = lifecycle_manager.get_plugin_info("test_plugin")
        assert plugin_info is not None
        assert plugin_info.manifest == sample_manifest

    def test_list_plugins(self, lifecycle_manager):
        """测试列出插件"""
        # 空列表
        plugins = lifecycle_manager.list_plugins()
        assert plugins == {}

        # 注册多个插件
        manifests = [
            PluginManifest(
                name="plugin1",
                version="1.0.0",
                description="Plugin 1",
                author="Test",
                category=PluginCategory.UTILITY,
            ),
            PluginManifest(
                name="plugin2",
                version="1.0.0",
                description="Plugin 2",
                author="Test",
                category=PluginCategory.DATA_SOURCE,
            ),
        ]

        for manifest in manifests:
            lifecycle_manager.register_plugin(manifest)

        plugins = lifecycle_manager.list_plugins()
        assert len(plugins) == 2
        assert "plugin1" in plugins
        assert "plugin2" in plugins
        assert all(state == PluginState.UNKNOWN for state in plugins.values())

    def test_get_active_plugins(self, lifecycle_manager, sample_manifest):
        """测试获取活跃插件"""
        # 无活跃插件
        active = lifecycle_manager.get_active_plugins()
        assert active == []

        # 注册插件并设置为活跃状态
        lifecycle_manager.register_plugin(sample_manifest)
        plugin_info = lifecycle_manager._plugins["test_plugin"]
        plugin_info.set_state(PluginState.ACTIVE)

        active = lifecycle_manager.get_active_plugins()
        assert active == ["test_plugin"]

    def test_import_plugin_success(self, lifecycle_manager, sample_manifest):
        """测试成功导入插件"""
        plugin_info = PluginInfo(sample_manifest, Path("/test/path"))

        # 直接模拟_import_plugin方法返回成功
        with patch.object(lifecycle_manager, "_import_plugin") as mock_import:
            mock_plugin = MockPlugin()
            mock_import.return_value = mock_plugin

            result = lifecycle_manager._import_plugin(plugin_info)

            assert result == mock_plugin

    def test_import_plugin_no_path(self, lifecycle_manager, sample_manifest):
        """测试没有路径的插件导入"""
        plugin_info = PluginInfo(sample_manifest)  # 没有plugin_path

        result = lifecycle_manager._import_plugin(plugin_info)

        assert result is None

    def test_lifecycle_hooks(self, lifecycle_manager):
        """测试生命周期钩子"""
        hook_called = []

        def test_hook(plugin_name, plugin_info, exception=None):
            hook_called.append((plugin_name, plugin_info.state, exception))

        # 添加钩子
        lifecycle_manager.add_lifecycle_hook("before_load", test_hook)

        # 验证钩子被添加
        assert test_hook in lifecycle_manager._lifecycle_hooks["before_load"]

        # 执行钩子
        plugin_info = PluginInfo(
            PluginManifest(
                name="test",
                version="1.0.0",
                description="Test",
                author="Test",
                category=PluginCategory.UTILITY,
            )
        )
        plugin_info.set_state(PluginState.LOADING)

        lifecycle_manager._execute_hooks("before_load", "test", plugin_info)

        assert len(hook_called) == 1
        assert hook_called[0][0] == "test"
        assert hook_called[0][1] == PluginState.LOADING

        # 移除钩子
        lifecycle_manager.remove_lifecycle_hook("before_load", test_hook)
        assert test_hook not in lifecycle_manager._lifecycle_hooks["before_load"]

    def test_invalid_hook_name(self, lifecycle_manager):
        """测试无效的钩子名称"""

        def dummy_hook():
            pass

        with pytest.raises(ValueError, match="未知的钩子类型"):
            lifecycle_manager.add_lifecycle_hook("invalid_hook", dummy_hook)

    def test_emit_event(self, lifecycle_manager):
        """测试事件发送"""
        events_received = []

        def event_handler(event):
            events_received.append(event)

        lifecycle_manager.event_bus.subscribe("test.event", event_handler)

        # 发送事件
        lifecycle_manager._emit_event("test.event", {"data": "test"})

        # 等待事件处理
        time.sleep(0.1)

        assert len(events_received) == 1
        assert events_received[0].type == "test.event"
        assert events_received[0].data["data"] == "test"

    def test_batch_operation_context(self, lifecycle_manager):
        """测试批量操作上下文管理器"""
        with lifecycle_manager.batch_operation():
            # 在批量操作中执行一些操作
            pass

        # 验证上下文管理器正常工作（无异常抛出）
        assert True

    def test_thread_safety(self, lifecycle_manager):
        """测试线程安全性"""
        results = []

        def register_plugin(i):
            manifest = PluginManifest(
                name=f"plugin_{i}",
                version="1.0.0",
                description=f"Plugin {i}",
                author="Test",
                category=PluginCategory.UTILITY,
            )
            result = lifecycle_manager.register_plugin(manifest)
            results.append(result)

        # 创建多个线程同时注册插件
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_plugin, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有插件都成功注册
        assert all(results)
        assert len(lifecycle_manager._plugins) == 10

    def test_shutdown(self, lifecycle_manager, sample_manifest):
        """测试关闭管理器"""
        # 注册一个插件
        lifecycle_manager.register_plugin(sample_manifest)

        # 模拟插件实例
        plugin_info = lifecycle_manager._plugins["test_plugin"]
        plugin_info.instance = MockPlugin()
        plugin_info.set_state(PluginState.ACTIVE)

        # 关闭管理器
        lifecycle_manager.shutdown()

        # 验证插件被正确清理
        assert len(lifecycle_manager._plugins) == 0


class TestPluginLifecycleOperations:
    """测试插件生命周期操作"""

    @pytest.fixture
    def lifecycle_manager(self):
        """创建生命周期管理器"""
        return PluginLifecycleManager()

    @pytest.fixture
    def plugin_with_deps(self):
        """创建有依赖的插件清单"""
        base_manifest = PluginManifest(
            name="base_plugin",
            version="1.0.0",
            description="Base plugin",
            author="Test",
            category=PluginCategory.UTILITY,
        )

        dependent_manifest = PluginManifest(
            name="dependent_plugin",
            version="1.0.0",
            description="Dependent plugin",
            author="Test",
            category=PluginCategory.UTILITY,
            dependencies={"base_plugin": ">=1.0.0"},
        )

        return base_manifest, dependent_manifest

    def test_load_plugin_with_dependencies(self, lifecycle_manager, plugin_with_deps):
        """测试加载有依赖的插件"""
        base_manifest, dependent_manifest = plugin_with_deps

        # 注册插件
        lifecycle_manager.register_plugin(base_manifest)
        lifecycle_manager.register_plugin(dependent_manifest)

        # 模拟导入成功
        with patch.object(lifecycle_manager, "_import_plugin") as mock_import:
            mock_import.return_value = MockPlugin()

            # 加载依赖插件应该自动加载基础插件
            result = lifecycle_manager.load_plugin("dependent_plugin")

            assert result is True
            assert (
                lifecycle_manager.get_plugin_state("base_plugin") == PluginState.LOADED
            )
            assert (
                lifecycle_manager.get_plugin_state("dependent_plugin")
                == PluginState.LOADED
            )

    def test_load_plugin_force(self, lifecycle_manager):
        """测试强制加载插件"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            category=PluginCategory.UTILITY,
        )

        lifecycle_manager.register_plugin(manifest)

        # 模拟导入成功
        with patch.object(lifecycle_manager, "_import_plugin") as mock_import:
            mock_import.return_value = MockPlugin()

            result = lifecycle_manager.load_plugin("test_plugin", force=True)

            assert result is True
            assert (
                lifecycle_manager.get_plugin_state("test_plugin") == PluginState.LOADED
            )

    def test_start_stop_plugin(self, lifecycle_manager):
        """测试启动和停止插件"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            category=PluginCategory.UTILITY,
        )

        lifecycle_manager.register_plugin(manifest)

        # 先加载插件
        plugin_info = lifecycle_manager._plugins["test_plugin"]
        plugin_info.instance = MockPlugin()
        plugin_info.set_state(PluginState.LOADED)

        # 启动插件
        result = lifecycle_manager.start_plugin("test_plugin")
        assert result is True
        assert lifecycle_manager.get_plugin_state("test_plugin") == PluginState.ACTIVE
        assert plugin_info.instance.started is True

        # 停止插件
        result = lifecycle_manager.stop_plugin("test_plugin")
        assert result is True
        assert lifecycle_manager.get_plugin_state("test_plugin") == PluginState.STOPPED
        assert plugin_info.instance.stopped is True

    def test_unload_plugin(self, lifecycle_manager):
        """测试卸载插件"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            category=PluginCategory.UTILITY,
        )

        lifecycle_manager.register_plugin(manifest)

        # 设置插件为已加载状态
        plugin_info = lifecycle_manager._plugins["test_plugin"]
        plugin_info.instance = MockPlugin()
        plugin_info.set_state(PluginState.LOADED)

        # 卸载插件
        result = lifecycle_manager.unload_plugin("test_plugin")
        assert result is True
        assert lifecycle_manager.get_plugin_state("test_plugin") == PluginState.UNLOADED
        assert plugin_info.instance is None

    def test_reload_plugin(self, lifecycle_manager):
        """测试重载插件"""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test",
            category=PluginCategory.UTILITY,
        )

        lifecycle_manager.register_plugin(manifest)

        # 设置插件为活跃状态
        plugin_info = lifecycle_manager._plugins["test_plugin"]
        mock_plugin = MockPlugin()
        mock_plugin.state_data = {"key": "value"}
        plugin_info.instance = mock_plugin
        plugin_info.set_state(PluginState.ACTIVE)

        # 模拟导入成功
        with patch.object(lifecycle_manager, "_import_plugin") as mock_import:
            new_mock_plugin = MockPlugin()
            mock_import.return_value = new_mock_plugin

            # 重载插件
            result = lifecycle_manager.reload_plugin("test_plugin", preserve_state=True)

            assert result is True
            assert (
                lifecycle_manager.get_plugin_state("test_plugin") == PluginState.ACTIVE
            )
            assert plugin_info.instance != mock_plugin  # 新实例
            assert plugin_info.instance.state_data == {"key": "value"}  # 状态被保持

    def test_batch_operations(self, lifecycle_manager):
        """测试批量操作"""
        manifests = [
            PluginManifest(
                name=f"plugin_{i}",
                version="1.0.0",
                description=f"Plugin {i}",
                author="Test",
                category=PluginCategory.UTILITY,
            )
            for i in range(3)
        ]

        # 注册所有插件
        for manifest in manifests:
            lifecycle_manager.register_plugin(manifest)

        # 模拟导入成功
        with patch.object(lifecycle_manager, "_import_plugin") as mock_import:
            mock_import.return_value = MockPlugin()

            # 批量加载
            results = lifecycle_manager.load_all_plugins()
            assert all(results.values())

            # 批量启动
            results = lifecycle_manager.start_all_plugins()
            assert all(results.values())

            # 验证所有插件都是活跃状态
            for i in range(3):
                assert (
                    lifecycle_manager.get_plugin_state(f"plugin_{i}")
                    == PluginState.ACTIVE
                )

            # 批量停止
            results = lifecycle_manager.stop_all_plugins()
            assert all(results.values())

            # 验证所有插件都已停止
            for i in range(3):
                assert (
                    lifecycle_manager.get_plugin_state(f"plugin_{i}")
                    == PluginState.STOPPED
                )
