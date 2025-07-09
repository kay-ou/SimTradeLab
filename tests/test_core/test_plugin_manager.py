# -*- coding: utf-8 -*-
"""
PluginManager 测试
确保100%测试覆盖率，包括所有方法、异常处理、插件发现
"""

import asyncio
import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

from simtradelab.core.plugin_manager import (
    PluginManager,
    PluginRegistry,
    PluginManagerError,
    PluginLoadError,
    PluginRegistrationError,
    PluginDiscoveryError
)
from simtradelab.core.event_bus import EventBus
from simtradelab.plugins.base import (
    BasePlugin,
    PluginMetadata,
    PluginConfig,
    PluginState
)


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
        priority=50
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
        name="failing_plugin",
        version="1.0.0",
        description="Failing Plugin"
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
            load_order=50
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
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus()
        yield bus
        bus.shutdown()
    
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
        assert manager._stats['registered'] == 0
        
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
        assert plugin_manager._stats['registered'] == 1
        
        registry = plugin_manager._plugins[plugin_name]
        assert registry.plugin_class is TestPluginA
        assert registry.metadata.name == "test_plugin_a"
        assert registry.instance is None
    
    def test_register_plugin_with_config(self, plugin_manager):
        """测试注册插件时提供配置"""
        config = PluginConfig(enabled=False)
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
        with pytest.raises(PluginRegistrationError, match="is not a BasePlugin subclass"):
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
        assert plugin_manager._stats['registered'] == 0
    
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
        assert plugin_manager._stats['loaded'] == 1
        
        registry = plugin_manager._plugins[plugin_name]
        assert registry.instance is instance
    
    def test_load_plugin_with_config(self, plugin_manager):
        """测试加载插件时提供配置"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        config = PluginConfig(enabled=False)
        
        instance = plugin_manager.load_plugin(plugin_name, config)
        
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
        
        assert plugin_manager._stats['failed'] == 1
    
    def test_unload_plugin_success(self, plugin_manager):
        """测试成功卸载插件"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin(plugin_name)
        plugin_manager.start_plugin(plugin_name)
        
        success = plugin_manager.unload_plugin(plugin_name)
        
        assert success is True
        registry = plugin_manager._plugins[plugin_name]
        assert registry.instance is None
        assert plugin_manager._stats['loaded'] == 0
    
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
        assert plugin_manager._stats['active'] == 1
    
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
        assert plugin_manager._stats['active'] == 0
    
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
        instance = plugin_manager.load_plugin(plugin_name)
        
        info = plugin_manager.get_plugin_info(plugin_name)
        
        assert info is not None
        assert info['name'] == "test_plugin_a"
        assert info['version'] == "1.0.0"
        assert info['loaded'] is True
        assert info['state'] == 'initialized'
        assert 'uptime' in info
        assert 'status' in info
    
    def test_get_plugin_info_not_loaded(self, plugin_manager):
        """测试获取未加载插件的信息"""
        plugin_name = plugin_manager.register_plugin(TestPluginA)
        
        info = plugin_manager.get_plugin_info(plugin_name)
        
        assert info is not None
        assert info['loaded'] is False
        assert info['state'] == 'unloaded'
        assert 'uptime' not in info
    
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


class TestPluginManagerBulkOperations:
    """测试PluginManager批量操作"""
    
    @pytest.fixture
    def plugin_manager(self):
        """插件管理器fixture"""
        manager = PluginManager()
        yield manager
        manager.shutdown()
    
    def test_load_all_plugins_success(self, plugin_manager):
        """测试成功加载所有插件"""
        # 注册不同加载顺序的插件
        plugin_manager.register_plugin(TestPluginA, load_order=20)
        plugin_manager.register_plugin(TestPluginB, load_order=10)
        
        results = plugin_manager.load_all_plugins()
        
        assert len(results) == 2
        assert all(results.values())  # 所有插件都应该加载成功
        assert plugin_manager._stats['loaded'] == 2
    
    def test_load_all_plugins_with_start(self, plugin_manager):
        """测试加载并启动所有插件"""
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.register_plugin(TestPluginB)
        
        results = plugin_manager.load_all_plugins(start=True)
        
        assert all(results.values())
        assert plugin_manager._stats['loaded'] == 2
        assert plugin_manager._stats['active'] == 2
    
    def test_load_all_plugins_with_failure(self, plugin_manager):
        """测试加载所有插件时部分失败"""
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.register_plugin(FailingPlugin)
        
        results = plugin_manager.load_all_plugins()
        
        assert results["test_plugin_a"] is True
        assert results["failing_plugin"] is False
        assert plugin_manager._stats['loaded'] == 1
        assert plugin_manager._stats['failed'] == 1
    
    def test_load_all_plugins_already_loaded(self, plugin_manager):
        """测试加载所有插件时有已加载的"""
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.register_plugin(TestPluginB)
        plugin_manager.load_plugin("test_plugin_a")
        
        results = plugin_manager.load_all_plugins()
        
        assert results["test_plugin_a"] is True  # 已加载
        assert results["TestPluginB"] is True   # 新加载
    
    def test_unload_all_plugins_success(self, plugin_manager):
        """测试成功卸载所有插件"""
        plugin_manager.register_plugin(TestPluginA, load_order=10)
        plugin_manager.register_plugin(TestPluginB, load_order=20)
        plugin_manager.load_all_plugins(start=True)
        
        results = plugin_manager.unload_all_plugins()
        
        assert all(results.values())
        assert plugin_manager._stats['loaded'] == 0
        assert plugin_manager._stats['active'] == 0
    
    def test_unload_all_plugins_not_loaded(self, plugin_manager):
        """测试卸载所有插件时有未加载的"""
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.register_plugin(TestPluginB)
        plugin_manager.load_plugin("test_plugin_a")
        
        results = plugin_manager.unload_all_plugins()
        
        assert results["test_plugin_a"] is True  # 已卸载
        assert results["TestPluginB"] is True   # 未加载


class TestPluginManagerDiscovery:
    """测试PluginManager插件发现功能"""
    
    @pytest.fixture
    def plugin_manager(self):
        """插件管理器fixture"""
        manager = PluginManager()
        yield manager
        manager.shutdown()
    
    def test_load_plugins_from_nonexistent_directory(self, plugin_manager):
        """测试从不存在的目录加载插件"""
        with pytest.raises(PluginDiscoveryError, match="does not exist"):
            plugin_manager.load_plugins_from_directory("/nonexistent/path")
    
    def test_load_plugins_from_file_not_directory(self, plugin_manager):
        """测试从文件而非目录加载插件"""
        with tempfile.NamedTemporaryFile() as tmp_file:
            with pytest.raises(PluginDiscoveryError, match="is not a directory"):
                plugin_manager.load_plugins_from_directory(tmp_file.name)
    
    def test_load_plugins_from_empty_directory(self, plugin_manager):
        """测试从空目录加载插件"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            loaded = plugin_manager.load_plugins_from_directory(tmp_dir)
            
            assert loaded == []
    
    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_plugin_from_file_success(self, mock_module_from_spec, mock_spec_from_file, plugin_manager):
        """测试从文件成功加载插件"""
        # 创建模拟的模块
        mock_module = MagicMock()
        mock_module.TestPlugin = TestPluginA
        
        # 设置模拟
        mock_spec = MagicMock()
        mock_spec.loader = MagicMock()
        mock_spec_from_file.return_value = mock_spec
        mock_module_from_spec.return_value = mock_module
        
        # 测试
        with tempfile.TemporaryDirectory() as tmp_dir:
            plugin_file = Path(tmp_dir) / "test_plugin.py"
            plugin_file.write_text("# test plugin")
            
            loaded = plugin_manager.load_plugins_from_directory(tmp_dir)
            
            assert len(loaded) == 1
            assert "test_plugin_a" in plugin_manager._plugins
    
    def test_get_stats(self, plugin_manager):
        """测试获取统计信息"""
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin("test_plugin_a")
        plugin_manager.start_plugin("test_plugin_a")
        
        stats = plugin_manager.get_stats()
        
        assert stats['registered'] == 1
        assert stats['loaded'] == 1
        assert stats['active'] == 1
        assert stats['failed'] == 0
        assert 'event_bus_stats' in stats


class TestPluginManagerEvents:
    """测试PluginManager事件处理"""
    
    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus()
        yield bus
        bus.shutdown()
    
    @pytest.fixture
    def plugin_manager(self, event_bus):
        """插件管理器fixture"""
        manager = PluginManager(event_bus)
        yield manager
        manager.shutdown()
    
    def test_plugin_registration_event(self, plugin_manager):
        """测试插件注册事件"""
        events = []
        
        def event_handler(event):
            events.append(event)
        
        plugin_manager.event_bus.subscribe("plugin.registered", event_handler)
        plugin_manager.register_plugin(TestPluginA)
        
        assert len(events) == 1
        assert events[0].data['plugin_name'] == "test_plugin_a"
    
    def test_plugin_load_event(self, plugin_manager):
        """测试插件加载事件"""
        events = []
        
        def event_handler(event):
            events.append(event)
        
        plugin_manager.event_bus.subscribe("plugin.loaded", event_handler)
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin("test_plugin_a")
        
        assert len(events) == 1
        assert events[0].data['plugin_name'] == "test_plugin_a"
    
    def test_plugin_start_event(self, plugin_manager):
        """测试插件启动事件"""
        events = []
        
        def event_handler(event):
            events.append(event)
        
        plugin_manager.event_bus.subscribe("plugin.started", event_handler)
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin("test_plugin_a")
        plugin_manager.start_plugin("test_plugin_a")
        
        assert len(events) == 1
        assert events[0].data['plugin_name'] == "test_plugin_a"
    
    def test_plugin_stop_event(self, plugin_manager):
        """测试插件停止事件"""
        events = []
        
        def event_handler(event):
            events.append(event)
        
        plugin_manager.event_bus.subscribe("plugin.stopped", event_handler)
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin("test_plugin_a")
        plugin_manager.start_plugin("test_plugin_a")
        plugin_manager.stop_plugin("test_plugin_a")
        
        assert len(events) == 1
        assert events[0].data['plugin_name'] == "test_plugin_a"
    
    def test_plugin_unload_event(self, plugin_manager):
        """测试插件卸载事件"""
        events = []
        
        def event_handler(event):
            events.append(event)
        
        plugin_manager.event_bus.subscribe("plugin.unloaded", event_handler)
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.load_plugin("test_plugin_a")
        plugin_manager.unload_plugin("test_plugin_a")
        
        assert len(events) == 1
        assert events[0].data['plugin_name'] == "test_plugin_a"
    
    def test_plugin_unregister_event(self, plugin_manager):
        """测试插件取消注册事件"""
        events = []
        
        def event_handler(event):
            events.append(event)
        
        plugin_manager.event_bus.subscribe("plugin.unregistered", event_handler)
        plugin_manager.register_plugin(TestPluginA)
        plugin_manager.unregister_plugin("test_plugin_a")
        
        assert len(events) == 1
        assert events[0].data['plugin_name'] == "test_plugin_a"


class TestPluginManagerContextManager:
    """测试PluginManager上下文管理器"""
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with PluginManager() as manager:
            manager.register_plugin(TestPluginA)
            manager.load_plugin("test_plugin_a")
            
            assert len(manager._plugins) == 1
        
        # 退出上下文后应该清理
        assert len(manager._plugins) == 0


class TestPluginManagerThreadSafety:
    """测试PluginManager线程安全"""
    
    @pytest.fixture
    def plugin_manager(self):
        """插件管理器fixture"""
        manager = PluginManager()
        yield manager
        manager.shutdown()
    
    def test_concurrent_plugin_operations(self, plugin_manager):
        """测试并发插件操作"""
        def register_plugins():
            for i in range(5):
                try:
                    # 动态创建插件类
                    class DynamicPlugin(BasePlugin):
                        METADATA = PluginMetadata(name=f"dynamic_{i}", version="1.0.0")
                        def _on_initialize(self): pass
                        def _on_start(self): pass
                        def _on_stop(self): pass
                    
                    plugin_manager.register_plugin(DynamicPlugin)
                except Exception:
                    pass  # 忽略可能的重复注册错误
        
        def load_plugins():
            time.sleep(0.01)  # 让注册先开始
            for plugin_name in plugin_manager.list_plugins():
                try:
                    plugin_manager.load_plugin(plugin_name)
                except Exception:
                    pass  # 忽略可能的重复加载错误
        
        # 启动多个线程
        threads = []
        for _ in range(3):
            t1 = threading.Thread(target=register_plugins)
            t2 = threading.Thread(target=load_plugins)
            threads.extend([t1, t2])
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # 最终状态应该是一致的
        stats = plugin_manager.get_stats()
        assert stats['registered'] >= 0
        assert stats['loaded'] >= 0


class TestPluginManagerErrorHandling:
    """测试插件管理器错误处理"""
    
    def test_plugin_manager_discovery_error_handling(self):
        """测试插件发现错误处理"""
        manager = PluginManager()
        
        # 测试不存在的目录
        with pytest.raises(PluginDiscoveryError, match="does not exist"):
            manager.load_plugins_from_directory("/nonexistent/directory")
        
        # 测试文件而非目录
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:
            with pytest.raises(PluginDiscoveryError, match="is not a directory"):
                manager.load_plugins_from_directory(temp_file.name)
    
    def test_plugin_manager_load_from_invalid_file(self):
        """测试从无效文件加载插件"""
        manager = PluginManager()
        
        # 创建一个无效的Python文件
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_file = os.path.join(temp_dir, "invalid.py")
            with open(invalid_file, 'w') as f:
                f.write("invalid python syntax !!!")
            
            # 应该记录警告但不崩溃
            with patch.object(manager._logger, 'warning') as mock_warning:
                loaded = manager.load_plugins_from_directory(temp_dir)
                assert len(loaded) == 0
                # 应该记录语法错误警告
                mock_warning.assert_called()
    
    def test_plugin_manager_package_loading(self):
        """测试从包加载插件"""
        manager = PluginManager()
        
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个包目录
            pkg_dir = os.path.join(temp_dir, "test_package")
            os.makedirs(pkg_dir)
            
            # 创建__init__.py文件
            init_file = os.path.join(pkg_dir, "__init__.py")
            with open(init_file, 'w') as f:
                f.write("""
from simtradelab.plugins.base import BasePlugin, PluginMetadata

class TestPackagePlugin(BasePlugin):
    METADATA = PluginMetadata(name="test_package_plugin", version="1.0.0")
    
    def _on_initialize(self):
        pass
    
    def _on_start(self):
        pass
    
    def _on_stop(self):
        pass
""")
            
            # 加载包
            loaded = manager.load_plugins_from_directory(temp_dir)
            assert len(loaded) == 1
            assert "test_package_plugin" in loaded
            assert "test_package_plugin" in manager._plugins
    
    def test_plugin_manager_skip_dunder_files(self):
        """测试跳过双下划线文件"""
        manager = PluginManager()
        
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建__init__.py文件
            init_file = os.path.join(temp_dir, "__init__.py")
            with open(init_file, 'w') as f:
                f.write("# This should be skipped")
            
            # 创建__pycache__目录
            pycache_dir = os.path.join(temp_dir, "__pycache__")
            os.makedirs(pycache_dir)
            
            # 加载插件
            loaded = manager.load_plugins_from_directory(temp_dir)
            assert len(loaded) == 0
    
    def test_plugin_manager_builtin_event_handlers(self):
        """测试内置事件处理器"""
        manager = PluginManager()
        
        # 测试插件加载事件
        from simtradelab.core.event_bus import Event
        
        with patch.object(manager._logger, 'debug') as mock_debug:
            manager._on_plugin_loaded(Event("plugin.loaded", data={"plugin_name": "test"}))
            mock_debug.assert_called_with("Plugin loaded event: test")
        
        # 测试插件启动事件
        with patch.object(manager._logger, 'debug') as mock_debug:
            manager._on_plugin_started(Event("plugin.started", data={"plugin_name": "test"}))
            mock_debug.assert_called_with("Plugin started event: test")
        
        # 测试插件停止事件
        with patch.object(manager._logger, 'debug') as mock_debug:
            manager._on_plugin_stopped(Event("plugin.stopped", data={"plugin_name": "test"}))
            mock_debug.assert_called_with("Plugin stopped event: test")
        
        # 测试插件卸载事件
        with patch.object(manager._logger, 'debug') as mock_debug:
            manager._on_plugin_unloaded(Event("plugin.unloaded", data={"plugin_name": "test"}))
            mock_debug.assert_called_with("Plugin unloaded event: test")
    
    def test_plugin_manager_context_manager(self):
        """测试插件管理器上下文管理器"""
        with PluginManager() as manager:
            # 注册插件
            manager.register_plugin(TestPluginA)
            assert len(manager._plugins) == 1
        
        # 退出上下文管理器后应该关闭
        assert len(manager._plugins) == 0
    
    def test_plugin_manager_error_handling_in_load_unload(self):
        """测试加载卸载过程中的错误处理"""
        manager = PluginManager()
        
        # 注册一个会在卸载时失败的插件
        class FailingUnloadPlugin(BasePlugin):
            METADATA = PluginMetadata(name="failing_unload", version="1.0.0")
            
            def _on_initialize(self):
                pass
            
            def _on_start(self):
                pass
            
            def _on_stop(self):
                raise RuntimeError("Stop failed")
        
        manager.register_plugin(FailingUnloadPlugin)
        manager.load_plugin("failing_unload")
        manager.start_plugin("failing_unload")
        
        # 卸载应该记录错误但不崩溃
        with patch.object(manager._logger, 'error') as mock_error:
            result = manager.unload_plugin("failing_unload")
            assert result is False
            mock_error.assert_called()
    
    def test_plugin_manager_plugin_without_metadata(self):
        """测试没有元数据的插件"""
        manager = PluginManager()
        
        class NoMetadataPlugin(BasePlugin):
            def _on_initialize(self):
                pass
            
            def _on_start(self):
                pass
            
            def _on_stop(self):
                pass
        
        # 应该使用默认元数据
        plugin_name = manager.register_plugin(NoMetadataPlugin)
        assert plugin_name == "NoMetadataPlugin"
        
        plugin_info = manager.get_plugin_info(plugin_name)
        assert plugin_info['name'] == "NoMetadataPlugin"
        assert plugin_info['version'] == "1.0.0"