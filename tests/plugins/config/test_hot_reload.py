# -*- coding: utf-8 -*-
"""
ConfigHotReloader配置热更新测试模块
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from src.simtradelab.plugins.config.base_config import BasePluginConfig
from src.simtradelab.plugins.config.dynamic_config_center import (
    DynamicConfigCenter,
    reset_config_center,
)
from src.simtradelab.plugins.config.hot_reload import (
    ConfigFileHandler,
    ConfigHotReloader,
    EnvironmentWatcher,
    get_config_hot_reloader,
    reset_config_hot_reloader,
)


class TestConfigModel(BasePluginConfig):
    """测试配置模型"""

    api_key: str = "default_key"
    timeout: int = 30
    debug: bool = False


class TestConfigFileHandler:
    """配置文件处理器测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.config_center = DynamicConfigCenter()
        self.config_center.register_plugin_config("test_plugin", TestConfigModel)

    def teardown_method(self):
        """测试后置清理"""
        self.config_center.shutdown()

    def test_file_handler_initialization(self):
        """测试文件处理器初始化"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test_plugin": {"api_key": "test_key"}}')
            file_path = f.name

        try:
            handler = ConfigFileHandler(self.config_center, file_path)

            assert handler._config_center is self.config_center
            assert handler._file_path == file_path
            assert handler._debounce_delay == 0.5
            assert handler._last_modified == 0
        finally:
            os.unlink(file_path)

    def test_file_handler_config_reload(self):
        """测试文件处理器配置重载"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "updated_key", "timeout": 60}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            handler = ConfigFileHandler(self.config_center, file_path)

            # 手动触发重载
            handler._reload_config()

            # 验证配置已更新
            api_key = self.config_center.get_config("test_plugin", "api_key")
            assert api_key == "updated_key"

            timeout = self.config_center.get_config("test_plugin", "timeout")
            assert timeout == 60
        finally:
            os.unlink(file_path)

    def test_file_handler_nonexistent_file(self):
        """测试处理不存在的文件"""
        handler = ConfigFileHandler(self.config_center, "/nonexistent/path.json")

        # 应该不会抛出异常
        handler._reload_config()

    def test_file_handler_invalid_json(self):
        """测试处理无效JSON文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            file_path = f.name

        try:
            handler = ConfigFileHandler(self.config_center, file_path)

            # 应该不会抛出异常，但会记录错误
            handler._reload_config()
        finally:
            os.unlink(file_path)

    def test_file_handler_debounce_mechanism(self):
        """测试防抖机制"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "key1"}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            handler = ConfigFileHandler(self.config_center, file_path)

            # 模拟快速连续调用
            handler.on_modified(
                type("MockEvent", (), {"is_directory": False, "src_path": file_path})()
            )
            handler.on_modified(
                type("MockEvent", (), {"is_directory": False, "src_path": file_path})()
            )
            handler.on_modified(
                type("MockEvent", (), {"is_directory": False, "src_path": file_path})()
            )

            # 验证防抖机制生效（只有一次重载）
            # 这里我们主要验证不会崩溃
            time.sleep(0.1)
        finally:
            os.unlink(file_path)

    def test_file_handler_ignores_directory_events(self):
        """测试忽略目录事件"""
        handler = ConfigFileHandler(self.config_center, "/some/path.json")

        # 模拟目录事件
        event = type(
            "MockEvent", (), {"is_directory": True, "src_path": "/some/directory"}
        )()

        # 应该被忽略
        handler.on_modified(event)

    def test_file_handler_ignores_other_files(self):
        """测试忽略其他文件事件"""
        handler = ConfigFileHandler(self.config_center, "/target/path.json")

        # 模拟其他文件事件
        event = type(
            "MockEvent", (), {"is_directory": False, "src_path": "/other/path.json"}
        )()

        # 应该被忽略
        handler.on_modified(event)


class TestEnvironmentWatcher:
    """环境变量监听器测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.config_center = DynamicConfigCenter()
        self.config_center.register_plugin_config("test_plugin", TestConfigModel)
        self.env_watcher = EnvironmentWatcher(self.config_center)

    def teardown_method(self):
        """测试后置清理"""
        self.env_watcher.stop_watching()
        self.config_center.shutdown()

    def test_environment_watcher_initialization(self):
        """测试环境变量监听器初始化"""
        assert self.env_watcher._config_center is self.config_center
        assert self.env_watcher._watching is False
        assert self.env_watcher._watch_thread is None
        assert self.env_watcher._env_snapshot == {}
        assert self.env_watcher._watch_interval == 5

        # 检查监听的环境变量前缀
        expected_prefixes = ["SIMTRADELAB_", "STL_", "PLUGIN_", "CONFIG_"]
        assert self.env_watcher._watch_prefixes == expected_prefixes

    def test_env_snapshot_creation(self):
        """测试环境变量快照创建"""
        # 设置一些测试环境变量
        os.environ["SIMTRADELAB_TEST_KEY"] = "test_value"
        os.environ["STL_ANOTHER_KEY"] = "another_value"
        os.environ["UNRELATED_KEY"] = "should_not_appear"

        try:
            snapshot = self.env_watcher._get_env_snapshot()

            assert "SIMTRADELAB_TEST_KEY" in snapshot
            assert "STL_ANOTHER_KEY" in snapshot
            assert "UNRELATED_KEY" not in snapshot

            assert snapshot["SIMTRADELAB_TEST_KEY"] == "test_value"
            assert snapshot["STL_ANOTHER_KEY"] == "another_value"
        finally:
            # 清理环境变量
            os.environ.pop("SIMTRADELAB_TEST_KEY", None)
            os.environ.pop("STL_ANOTHER_KEY", None)
            os.environ.pop("UNRELATED_KEY", None)

    def test_env_change_detection(self):
        """测试环境变量变更检测"""
        old_env = {"SIMTRADELAB_KEY1": "value1", "SIMTRADELAB_KEY2": "value2"}

        new_env = {
            "SIMTRADELAB_KEY1": "updated_value1",  # 修改
            "SIMTRADELAB_KEY3": "value3"  # 新增
            # KEY2被删除
        }

        changes = self.env_watcher._detect_changes(old_env, new_env)

        assert len(changes) == 3

        # 检查修改
        assert changes["SIMTRADELAB_KEY1"]["type"] == "modified"
        assert changes["SIMTRADELAB_KEY1"]["old_value"] == "value1"
        assert changes["SIMTRADELAB_KEY1"]["new_value"] == "updated_value1"

        # 检查新增
        assert changes["SIMTRADELAB_KEY3"]["type"] == "added"
        assert changes["SIMTRADELAB_KEY3"]["old_value"] is None
        assert changes["SIMTRADELAB_KEY3"]["new_value"] == "value3"

        # 检查删除
        assert changes["SIMTRADELAB_KEY2"]["type"] == "deleted"
        assert changes["SIMTRADELAB_KEY2"]["old_value"] == "value2"
        assert changes["SIMTRADELAB_KEY2"]["new_value"] is None

    def test_env_key_parsing(self):
        """测试环境变量键解析"""
        # 测试正常解析
        plugin_name, config_key = self.env_watcher._parse_env_key(
            "SIMTRADELAB_AKSHARE_API_KEY"
        )
        assert plugin_name == "akshare"
        assert config_key == "api.key"

        plugin_name, config_key = self.env_watcher._parse_env_key(
            "STL_DATAMANAGER_TIMEOUT"
        )
        assert plugin_name == "datamanager"
        assert config_key == "timeout"

        plugin_name, config_key = self.env_watcher._parse_env_key(
            "PLUGIN_RISK_MAX_POSITION"
        )
        assert plugin_name == "risk"
        assert config_key == "max.position"

        # 测试无效键
        plugin_name, config_key = self.env_watcher._parse_env_key("INVALID_PREFIX_KEY")
        assert plugin_name is None
        assert config_key is None

        plugin_name, config_key = self.env_watcher._parse_env_key(
            "SIMTRADELAB_INCOMPLETE"
        )
        assert plugin_name is None
        assert config_key is None

    def test_start_stop_watching(self):
        """测试启动和停止监听"""
        # 启动监听
        self.env_watcher.start_watching()

        assert self.env_watcher._watching is True
        assert self.env_watcher._watch_thread is not None
        assert self.env_watcher._watch_thread.is_alive()

        # 停止监听
        self.env_watcher.stop_watching()

        assert self.env_watcher._watching is False

        # 等待线程结束
        time.sleep(0.1)

    def test_start_watching_already_running(self):
        """测试重复启动监听"""
        self.env_watcher.start_watching()
        thread1 = self.env_watcher._watch_thread

        # 再次启动应该不创建新线程
        self.env_watcher.start_watching()
        thread2 = self.env_watcher._watch_thread

        assert thread1 is thread2

    @patch.dict(os.environ, {"SIMTRADELAB_TEST_PLUGIN_API_KEY": "test_key"})
    def test_env_change_handling(self):
        """测试环境变量变更处理"""
        # 注册一个测试插件
        self.config_center.register_plugin_config("test_plugin", TestConfigModel)

        # 创建变更信息
        changes = {
            "SIMTRADELAB_TEST_PLUGIN_API_KEY": {
                "type": "modified",
                "old_value": "old_key",
                "new_value": "new_key",
            }
        }

        # 处理变更
        self.env_watcher._handle_env_changes(changes)

        # 验证配置已更新
        api_key = self.config_center.get_config("test_plugin", "api_key")
        assert api_key == "new_key"


class TestConfigHotReloader:
    """配置热更新管理器测试类"""

    def setup_method(self):
        """测试前置设置"""
        self.config_center = DynamicConfigCenter()
        self.config_center.register_plugin_config("test_plugin", TestConfigModel)
        self.hot_reloader = ConfigHotReloader(self.config_center)

    def teardown_method(self):
        """测试后置清理"""
        self.hot_reloader.stop()
        self.config_center.shutdown()

    def test_hot_reloader_initialization(self):
        """测试热更新管理器初始化"""
        assert self.hot_reloader._config_center is self.config_center
        assert self.hot_reloader._running is False
        assert len(self.hot_reloader._file_handlers) == 0
        assert len(self.hot_reloader._watched_files) == 0
        assert len(self.hot_reloader._watched_directories) == 0

    def test_start_stop_hot_reloader(self):
        """测试启动和停止热更新管理器"""
        # 启动热更新
        self.hot_reloader.start()

        assert self.hot_reloader._running is True
        assert self.hot_reloader._file_observer.is_alive()
        assert self.hot_reloader._env_watcher._watching is True

        # 停止热更新
        self.hot_reloader.stop()

        assert self.hot_reloader._running is False
        assert self.hot_reloader._env_watcher._watching is False

    def test_start_stop_idempotent(self):
        """测试重复启动/停止的幂等性"""
        # 重复启动
        self.hot_reloader.start()
        self.hot_reloader.start()

        assert self.hot_reloader._running is True

        # 重复停止
        self.hot_reloader.stop()
        self.hot_reloader.stop()

        assert self.hot_reloader._running is False

    def test_watch_file(self):
        """测试监听单个文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "file_key"}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            self.hot_reloader.start()

            # 开始监听文件
            self.hot_reloader.watch_file(file_path)

            assert file_path in self.hot_reloader._watched_files
            assert file_path in self.hot_reloader._file_handlers
            assert len(self.hot_reloader._watched_directories) == 1

        finally:
            os.unlink(file_path)

    def test_watch_file_nonexistent(self):
        """测试监听不存在的文件"""
        nonexistent_file = "/nonexistent/path.json"

        self.hot_reloader.start()

        # 应该不会抛出异常，但文件不会被添加到监听列表
        self.hot_reloader.watch_file(nonexistent_file)

        assert nonexistent_file not in self.hot_reloader._watched_files

    def test_watch_file_duplicate(self):
        """测试重复监听同一文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "file_key"}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            self.hot_reloader.start()

            # 重复监听同一文件
            self.hot_reloader.watch_file(file_path)
            self.hot_reloader.watch_file(file_path)

            # 应该只有一个处理器
            assert len(self.hot_reloader._file_handlers) == 1
            assert file_path in self.hot_reloader._watched_files

        finally:
            os.unlink(file_path)

    def test_unwatch_file(self):
        """测试停止监听文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "file_key"}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            self.hot_reloader.start()

            # 开始监听文件
            self.hot_reloader.watch_file(file_path)
            assert file_path in self.hot_reloader._watched_files

            # 停止监听文件
            self.hot_reloader.unwatch_file(file_path)
            assert file_path not in self.hot_reloader._watched_files
            assert file_path not in self.hot_reloader._file_handlers

        finally:
            os.unlink(file_path)

    def test_watch_directory(self):
        """测试监听目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一些配置文件
            config_file1 = Path(temp_dir) / "config1.json"
            config_file2 = Path(temp_dir) / "config2.json"

            config_data = {"test_plugin": {"api_key": "dir_key"}}
            config_file1.write_text(json.dumps(config_data))
            config_file2.write_text(json.dumps(config_data))

            self.hot_reloader.start()

            # 开始监听目录
            self.hot_reloader.watch_directory(temp_dir)

            # 验证目录和文件都被监听
            assert temp_dir in self.hot_reloader._watched_directories
            assert str(config_file1) in self.hot_reloader._watched_files
            assert str(config_file2) in self.hot_reloader._watched_files

    def test_watch_directory_nonexistent(self):
        """测试监听不存在的目录"""
        nonexistent_dir = "/nonexistent/directory"

        self.hot_reloader.start()

        # 应该不会抛出异常，但目录不会被添加到监听列表
        self.hot_reloader.watch_directory(nonexistent_dir)

        assert nonexistent_dir not in self.hot_reloader._watched_directories

    def test_reload_all_configs(self):
        """测试重新加载所有配置"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "original_key"}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            self.hot_reloader.start()
            self.hot_reloader.watch_file(file_path)

            # 修改文件内容
            with open(file_path, "w") as f:
                config_data = {"test_plugin": {"api_key": "reloaded_key"}}
                json.dump(config_data, f)

            # 重新加载所有配置
            self.hot_reloader.reload_all_configs()

            # 验证配置已更新
            api_key = self.config_center.get_config("test_plugin", "api_key")
            assert api_key == "reloaded_key"

        finally:
            os.unlink(file_path)

    def test_get_status(self):
        """测试获取热更新状态"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "status_key"}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            self.hot_reloader.start()
            self.hot_reloader.watch_file(file_path)

            status = self.hot_reloader.get_status()

            assert status["running"] is True
            assert status["watched_files"] == 1
            assert status["watched_directories"] == 1
            assert status["file_handlers"] == 1
            assert status["env_watcher_running"] is True
            assert file_path in status["file_list"]

        finally:
            os.unlink(file_path)

    def test_file_change_integration(self):
        """测试文件变更集成"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_data = {"test_plugin": {"api_key": "integration_key"}}
            json.dump(config_data, f)
            file_path = f.name

        try:
            self.hot_reloader.start()
            self.hot_reloader.watch_file(file_path)

            # 修改文件
            with open(file_path, "w") as f:
                config_data = {"test_plugin": {"api_key": "updated_integration_key"}}
                json.dump(config_data, f)

            # 等待文件监听器处理
            time.sleep(1.5)

            # 验证配置已更新
            api_key = self.config_center.get_config("test_plugin", "api_key")
            assert api_key == "updated_integration_key"

        finally:
            os.unlink(file_path)


class TestGlobalHotReloader:
    """全局热更新管理器测试类"""

    def teardown_method(self):
        """清理全局状态"""
        reset_config_hot_reloader()
        reset_config_center()

    def test_get_config_hot_reloader_singleton(self):
        """测试全局热更新管理器单例"""
        reloader1 = get_config_hot_reloader()
        reloader2 = get_config_hot_reloader()

        assert reloader1 is reloader2

    def test_reset_config_hot_reloader(self):
        """测试重置全局热更新管理器"""
        reloader1 = get_config_hot_reloader()
        reset_config_hot_reloader()
        reloader2 = get_config_hot_reloader()

        assert reloader1 is not reloader2
