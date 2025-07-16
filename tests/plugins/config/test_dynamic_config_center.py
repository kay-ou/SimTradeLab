# -*- coding: utf-8 -*-
"""
DynamicConfigCenter动态配置中心测试模块
"""

import json
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.simtradelab.plugins.config.base_config import BasePluginConfig
from src.simtradelab.plugins.config.dynamic_config_center import (
    ConfigChangeEvent,
    ConfigSource,
    DynamicConfigCenter,
    DynamicConfigError,
    get_config_center,
    reset_config_center,
)


class _ConfigModel(BasePluginConfig):
    """测试配置模型"""

    api_key: str = "default_key"
    timeout: int = 30
    debug: bool = False


class TestDynamicConfigCenter:
    """DynamicConfigCenter测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.config_center = DynamicConfigCenter()
        self.mock_event_bus = Mock()

    def teardown_method(self):
        """测试后置清理"""
        self.config_center.shutdown()

    def test_init_creates_default_config_sources(self):
        """测试初始化时创建默认配置源"""
        # 检查环境变量配置源
        assert "global" in self.config_center._config_sources
        sources = self.config_center._config_sources["global"]

        # 应该有环境变量源
        env_sources = [s for s in sources if s.source_type == "env"]
        assert len(env_sources) == 1
        assert env_sources[0].source_path == "ENV"
        assert env_sources[0].priority == 50

    def test_register_plugin_config_with_initial_config(self):
        """测试注册插件配置并提供初始配置"""
        initial_config = {"api_key": "test_key", "timeout": 60, "debug": True}

        self.config_center.register_plugin_config(
            "test_plugin", _ConfigModel, initial_config
        )

        # 检查配置是否正确注册
        assert "test_plugin" in self.config_center._config_cache
        assert "test_plugin" in self.config_center._config_models

        # 检查配置值
        config = self.config_center.get_config("test_plugin")
        assert config["api_key"] == "test_key"
        assert config["timeout"] == 60
        assert config["debug"] is True

    def test_register_plugin_config_with_default_config(self):
        """测试注册插件配置使用默认配置"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 检查使用默认配置
        config = self.config_center.get_config("test_plugin")
        assert config["api_key"] == "default_key"
        assert config["timeout"] == 30
        assert config["debug"] is False

    def test_get_config_full_and_partial(self):
        """测试获取完整配置和部分配置"""
        self.config_center.register_plugin_config(
            "test_plugin", _ConfigModel, {"api_key": "test_key", "timeout": 60}
        )

        # 获取完整配置
        full_config = self.config_center.get_config("test_plugin")
        assert isinstance(full_config, dict)
        assert "api_key" in full_config
        assert "timeout" in full_config

        # 获取单个配置项
        api_key = self.config_center.get_config("test_plugin", "api_key")
        assert api_key == "test_key"

        # 获取嵌套配置（点号分隔）
        timeout = self.config_center.get_config("test_plugin", "timeout")
        assert timeout == 60

    def test_get_config_nested_keys(self):
        """测试获取嵌套配置键"""
        nested_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "credentials": {"username": "admin", "password": "secret"},
            }
        }

        # 注册一个支持嵌套配置的模型
        class NestedTestModel(BasePluginConfig):
            database: dict = {}

        self.config_center.register_plugin_config(
            "nested_plugin", NestedTestModel, nested_config
        )

        # 测试嵌套键访问
        host = self.config_center.get_config("nested_plugin", "database.host")
        assert host == "localhost"

        username = self.config_center.get_config(
            "nested_plugin", "database.credentials.username"
        )
        assert username == "admin"

    def test_get_config_nonexistent_plugin(self):
        """测试获取不存在插件的配置"""
        with pytest.raises(DynamicConfigError, match="插件 nonexistent 配置未找到"):
            self.config_center.get_config("nonexistent")

    def test_get_config_nonexistent_key(self):
        """测试获取不存在的配置键"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        with pytest.raises(
            DynamicConfigError, match="配置键 nonexistent 在插件 test_plugin 中未找到"
        ):
            self.config_center.get_config("test_plugin", "nonexistent")

    def test_set_config_valid_change(self):
        """测试设置有效的配置变更"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 设置配置
        self.config_center.set_config(
            "test_plugin", "api_key", "new_key", user="admin", reason="测试更新"
        )

        # 验证配置已更新
        api_key = self.config_center.get_config("test_plugin", "api_key")
        assert api_key == "new_key"

        # 验证历史记录
        history = self.config_center.get_config_history("test_plugin", "api_key")
        assert len(history) == 1
        assert history[0].new_value == "new_key"
        assert history[0].user == "admin"
        assert history[0].reason == "测试更新"

    def test_set_config_nested_value(self):
        """测试设置嵌套配置值"""

        class NestedTestModel(BasePluginConfig):
            database: dict = {"host": "localhost", "port": 5432}

        self.config_center.register_plugin_config(
            "nested_plugin",
            NestedTestModel,
            {"database": {"host": "localhost", "port": 5432}},
        )

        # 设置嵌套值
        self.config_center.set_config("nested_plugin", "database.host", "newhost")

        # 验证嵌套值已更新
        host = self.config_center.get_config("nested_plugin", "database.host")
        assert host == "newhost"

        # 验证其他值未变
        port = self.config_center.get_config("nested_plugin", "database.port")
        assert port == 5432

    def test_set_config_validation_error(self):
        """测试配置验证失败"""

        class StrictTestModel(BasePluginConfig):
            count: int = 0

        self.config_center.register_plugin_config("strict_plugin", StrictTestModel)

        # 尝试设置错误类型的值
        with pytest.raises(DynamicConfigError, match="配置验证失败"):
            self.config_center.set_config("strict_plugin", "count", "invalid_int")

    def test_set_config_nonexistent_plugin(self):
        """测试设置不存在插件的配置"""
        with pytest.raises(DynamicConfigError, match="插件 nonexistent 配置未找到"):
            self.config_center.set_config("nonexistent", "key", "value")

    def test_config_listeners(self):
        """测试配置变更监听器"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 创建监听器
        listener_calls = []

        def config_listener(key, old_value, new_value):
            listener_calls.append((key, old_value, new_value))

        # 添加监听器
        self.config_center.add_config_listener("test_plugin", config_listener)

        # 更改配置
        self.config_center.set_config("test_plugin", "api_key", "new_key")

        # 验证监听器被调用
        assert len(listener_calls) == 1
        assert listener_calls[0] == ("api_key", "default_key", "new_key")

    def test_config_listeners_with_pattern(self):
        """测试带模式的配置监听器"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 创建监听器
        api_listener_calls = []
        all_listener_calls = []

        def api_listener(key, old_value, new_value):
            api_listener_calls.append((key, old_value, new_value))

        def all_listener(key, old_value, new_value):
            all_listener_calls.append((key, old_value, new_value))

        # 添加监听器
        self.config_center.add_config_listener("test_plugin", api_listener, "api_*")
        self.config_center.add_config_listener("test_plugin", all_listener, "*")

        # 更改匹配的配置
        self.config_center.set_config("test_plugin", "api_key", "new_key")

        # 验证监听器调用
        assert len(api_listener_calls) == 1
        assert len(all_listener_calls) == 1

        # 更改不匹配的配置
        self.config_center.set_config("test_plugin", "timeout", 60)

        # 验证只有通配符监听器被调用
        assert len(api_listener_calls) == 1  # 没有增加
        assert len(all_listener_calls) == 2  # 增加了1个

    def test_remove_config_listener(self):
        """测试移除配置监听器"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        listener_calls = []

        def config_listener(key, old_value, new_value):
            listener_calls.append((key, old_value, new_value))

        # 添加监听器
        self.config_center.add_config_listener("test_plugin", config_listener)

        # 更改配置
        self.config_center.set_config("test_plugin", "api_key", "new_key")
        assert len(listener_calls) == 1

        # 移除监听器
        self.config_center.remove_config_listener("test_plugin", config_listener)

        # 再次更改配置
        self.config_center.set_config("test_plugin", "api_key", "newer_key")
        assert len(listener_calls) == 1  # 没有增加

    def test_config_history_tracking(self):
        """测试配置历史追踪"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 进行多次配置变更
        self.config_center.set_config("test_plugin", "api_key", "key1", user="user1")
        self.config_center.set_config("test_plugin", "api_key", "key2", user="user2")
        self.config_center.set_config("test_plugin", "timeout", 60, user="user3")

        # 获取所有历史
        all_history = self.config_center.get_config_history()
        assert len(all_history) == 3

        # 获取特定插件历史
        plugin_history = self.config_center.get_config_history("test_plugin")
        assert len(plugin_history) == 3

        # 获取特定键历史
        key_history = self.config_center.get_config_history("test_plugin", "api_key")
        assert len(key_history) == 2

        # 验证历史记录按时间倒序
        assert key_history[0].new_value == "key2"
        assert key_history[1].new_value == "key1"

    def test_config_rollback(self):
        """测试配置回滚"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 进行配置变更
        self.config_center.set_config("test_plugin", "api_key", "new_key")

        # 获取变更记录
        history = self.config_center.get_config_history("test_plugin", "api_key")
        change_id = history[0].change_id

        # 执行回滚
        self.config_center.rollback_config(change_id)

        # 验证配置已回滚
        api_key = self.config_center.get_config("test_plugin", "api_key")
        assert api_key == "default_key"

    def test_config_rollback_nonexistent_change(self):
        """测试回滚不存在的变更"""
        with pytest.raises(DynamicConfigError, match="变更记录未找到"):
            self.config_center.rollback_config("nonexistent_id")

    def test_export_config(self):
        """测试配置导出"""
        self.config_center.register_plugin_config("plugin1", _ConfigModel)
        self.config_center.register_plugin_config("plugin2", _ConfigModel)

        # 导出所有配置
        all_config = self.config_center.export_config()
        assert "plugin1" in all_config
        assert "plugin2" in all_config

        # 导出特定插件配置
        plugin_config = self.config_center.export_config("plugin1")
        assert "plugin1" in plugin_config
        assert "plugin2" not in plugin_config

    def test_export_config_nonexistent_plugin(self):
        """测试导出不存在插件的配置"""
        with pytest.raises(DynamicConfigError, match="插件 nonexistent 配置未找到"):
            self.config_center.export_config("nonexistent")

    def test_import_config(self):
        """测试配置导入"""
        self.config_center.register_plugin_config("plugin1", _ConfigModel)
        self.config_center.register_plugin_config("plugin2", _ConfigModel)

        # 准备导入数据
        import_data = {
            "plugin1": {"api_key": "imported_key1", "timeout": 120},
            "plugin2": {"api_key": "imported_key2", "debug": True},
        }

        # 导入配置
        self.config_center.import_config(import_data, user="admin", reason="批量导入")

        # 验证配置已导入
        assert self.config_center.get_config("plugin1", "api_key") == "imported_key1"
        assert self.config_center.get_config("plugin1", "timeout") == 120
        assert self.config_center.get_config("plugin2", "api_key") == "imported_key2"
        assert self.config_center.get_config("plugin2", "debug") is True

    def test_event_bus_integration(self):
        """测试事件总线集成"""
        config_center = DynamicConfigCenter(event_bus=self.mock_event_bus)
        config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 更改配置
        config_center.set_config("test_plugin", "api_key", "new_key")

        # 验证事件总线被调用
        self.mock_event_bus.publish.assert_called_once()

        # 清理
        config_center.shutdown()

    def test_file_watcher_integration(self):
        """测试文件监听器集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_config.json"

            # 创建初始配置文件
            config_data = {"test_plugin": {"api_key": "file_key", "timeout": 45}}
            config_file.write_text(json.dumps(config_data))

            # 创建配置中心并添加文件监听
            config_center = DynamicConfigCenter()
            config_center.register_plugin_config("test_plugin", _ConfigModel)
            config_center._start_file_watcher(str(config_file))

            # 等待一下让文件监听器启动
            time.sleep(0.1)

            # 修改配置文件
            new_config_data = {
                "test_plugin": {"api_key": "updated_file_key", "timeout": 90}
            }
            config_file.write_text(json.dumps(new_config_data))

            # 等待文件监听器处理
            time.sleep(2)

            # 验证配置已更新
            api_key = config_center.get_config("test_plugin", "api_key")
            assert api_key == "updated_file_key"

            # 清理
            config_center.shutdown()

    def test_get_status(self):
        """测试获取配置中心状态"""
        self.config_center.register_plugin_config("plugin1", _ConfigModel)
        self.config_center.register_plugin_config("plugin2", _ConfigModel)

        status = self.config_center.get_status()

        assert status["running"] is True
        assert status["registered_plugins"] == 2
        assert status["config_sources"] >= 1  # 至少有环境变量源
        assert status["active_listeners"] == 0
        assert status["file_watchers"] == 0
        assert status["history_size"] == 0
        assert "plugin1" in status["plugin_names"]
        assert "plugin2" in status["plugin_names"]

    def test_shutdown(self):
        """测试关闭配置中心"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        # 关闭配置中心
        self.config_center.shutdown()

        # 验证状态
        status = self.config_center.get_status()
        assert status["running"] is False

    def test_thread_safety(self):
        """测试线程安全性"""
        self.config_center.register_plugin_config("test_plugin", _ConfigModel)

        results = []
        errors = []

        def config_updater(thread_id):
            try:
                for i in range(10):
                    self.config_center.set_config(
                        "test_plugin", "api_key", f"key_{thread_id}_{i}"
                    )
                    time.sleep(0.01)
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")

        # 启动多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=config_updater, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(results) == 5
        assert len(errors) == 0

        # 验证历史记录
        history = self.config_center.get_config_history("test_plugin", "api_key")
        assert len(history) == 50  # 5个线程 * 10次更新


class TestGlobalConfigCenter:
    """全局配置中心测试类"""

    def teardown_method(self):
        """清理全局状态"""
        reset_config_center()

    def test_get_config_center_singleton(self):
        """测试全局配置中心单例"""
        center1 = get_config_center()
        center2 = get_config_center()

        assert center1 is center2

    def test_reset_config_center(self):
        """测试重置全局配置中心"""
        center1 = get_config_center()
        reset_config_center()
        center2 = get_config_center()

        assert center1 is not center2


class TestConfigModels:
    """配置模型测试类"""

    def test_config_change_event(self):
        """测试配置变更事件"""
        event = ConfigChangeEvent(
            plugin_name="test_plugin",
            key="api_key",
            old_value="old_key",
            new_value="new_key",
            user="admin",
            reason="测试变更",
        )

        assert event.plugin_name == "test_plugin"
        assert event.key == "api_key"
        assert event.old_value == "old_key"
        assert event.new_value == "new_key"
        assert event.user == "admin"
        assert event.reason == "测试变更"
        assert event.change_id is not None
        assert isinstance(event.timestamp, datetime)

    def test_config_source(self):
        """测试配置源"""
        source = ConfigSource(
            source_type="file",
            source_path="/path/to/config.json",
            priority=100,
            enabled=True,
        )

        assert source.source_type == "file"
        assert source.source_path == "/path/to/config.json"
        assert source.priority == 100
        assert source.enabled is True
        assert source.last_modified is None
        assert source.checksum is None
