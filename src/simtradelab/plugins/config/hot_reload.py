# -*- coding: utf-8 -*-
"""
SimTradeLab 配置热更新模块

提供配置文件监听、环境变量监听、数据库配置监听等多种热更新机制。
支持配置变更的实时检测和自动重新加载。
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Set

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .dynamic_config_center import DynamicConfigCenter


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件监听处理器"""

    def __init__(self, config_center: DynamicConfigCenter, file_path: str):
        super().__init__()
        self._config_center = config_center
        self._file_path = file_path
        self._logger = logging.getLogger(__name__)
        self._last_modified = 0
        self._debounce_delay = 0.5  # 防抖延迟

    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return

        if event.src_path != self._file_path:
            return

        # 防抖处理
        current_time = time.time()
        if current_time - self._last_modified < self._debounce_delay:
            return

        self._last_modified = current_time

        # 延迟处理，避免文件写入过程中的读取
        threading.Timer(self._debounce_delay, self._reload_config).start()

    def _reload_config(self):
        """重新加载配置"""
        try:
            self._logger.info(f"检测到配置文件变更: {self._file_path}")

            if not os.path.exists(self._file_path):
                self._logger.warning(f"配置文件不存在: {self._file_path}")
                return

            with open(self._file_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # 更新配置中心
            self._config_center.import_config(
                config_data, user="system", reason=f"配置文件热更新: {self._file_path}"
            )

            self._logger.info(f"配置文件热更新完成: {self._file_path}")

        except Exception as e:
            self._logger.error(f"配置文件热更新失败: {str(e)}")


class EnvironmentWatcher:
    """环境变量监听器"""

    def __init__(self, config_center: DynamicConfigCenter):
        self._config_center = config_center
        self._logger = logging.getLogger(__name__)
        self._watching = False
        self._watch_thread = None
        self._env_snapshot = {}
        self._watch_interval = 5  # 5秒检查一次

        # 需要监听的环境变量前缀
        self._watch_prefixes = ["SIMTRADELAB_", "STL_", "PLUGIN_", "CONFIG_"]

    def start_watching(self):
        """启动环境变量监听"""
        if self._watching:
            return

        self._watching = True
        self._env_snapshot = self._get_env_snapshot()

        self._watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()

        self._logger.info("环境变量监听器已启动")

    def stop_watching(self):
        """停止环境变量监听"""
        self._watching = False

        if self._watch_thread:
            self._watch_thread.join(timeout=1)

        self._logger.info("环境变量监听器已停止")

    def _get_env_snapshot(self) -> Dict[str, str]:
        """获取当前环境变量快照"""
        snapshot = {}

        for key, value in os.environ.items():
            if any(key.startswith(prefix) for prefix in self._watch_prefixes):
                snapshot[key] = value

        return snapshot

    def _watch_loop(self):
        """环境变量监听循环"""
        while self._watching:
            try:
                current_env = self._get_env_snapshot()

                # 检查变更
                changes = self._detect_changes(self._env_snapshot, current_env)

                if changes:
                    self._handle_env_changes(changes)
                    self._env_snapshot = current_env

                time.sleep(self._watch_interval)

            except Exception as e:
                self._logger.error(f"环境变量监听异常: {str(e)}")
                time.sleep(self._watch_interval)

    def _detect_changes(
        self, old_env: Dict[str, str], new_env: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """检测环境变量变更"""
        changes = {}

        # 检查新增和修改
        for key, new_value in new_env.items():
            if key not in old_env:
                changes[key] = {
                    "type": "added",
                    "old_value": None,
                    "new_value": new_value,
                }
            elif old_env[key] != new_value:
                changes[key] = {
                    "type": "modified",
                    "old_value": old_env[key],
                    "new_value": new_value,
                }

        # 检查删除
        for key in old_env:
            if key not in new_env:
                changes[key] = {
                    "type": "deleted",
                    "old_value": old_env[key],
                    "new_value": None,
                }

        return changes

    def _handle_env_changes(self, changes: Dict[str, Dict[str, Any]]):
        """处理环境变量变更"""
        for env_key, change_info in changes.items():
            try:
                # 解析环境变量到配置映射
                plugin_name, config_key = self._parse_env_key(env_key)

                if plugin_name and config_key:
                    if change_info["type"] == "deleted":
                        self._logger.info(f"环境变量已删除: {env_key}")
                        # 删除时设置为None或默认值
                        # 这里可以根据需要实现更复杂的逻辑
                    else:
                        # 更新配置
                        self._config_center.set_config(
                            plugin_name,
                            config_key,
                            change_info["new_value"],
                            user="system",
                            reason=f"环境变量更新: {env_key}",
                        )

                        self._logger.info(
                            f"环境变量配置已更新: {env_key} -> {plugin_name}.{config_key}"
                        )

            except Exception as e:
                self._logger.error(f"环境变量处理失败 {env_key}: {str(e)}")

    def _parse_env_key(self, env_key: str) -> tuple[Optional[str], Optional[str]]:
        """
        解析环境变量键到插件配置映射

        示例：
        - SIMTRADELAB_AKSHARE_API_KEY -> (akshare, api.key)
        - SIMTRADELAB_TEST_PLUGIN_API_KEY -> (test_plugin, api_key)
        - STL_DATAMANAGER_TIMEOUT -> (datamanager, timeout)
        - PLUGIN_RISK_MAX_POSITION -> (risk, max.position)
        """
        try:
            # 移除前缀
            for prefix in self._watch_prefixes:
                if env_key.startswith(prefix):
                    remaining = env_key[len(prefix) :]
                    break
            else:
                return None, None

            # 解析插件名和配置键
            parts = remaining.split("_")
            if len(parts) < 2:
                return None, None

            # 对于多个下划线的情况，需要智能地确定哪些是插件名，哪些是配置键
            # 通常插件名会在前面1-2个部分，配置键在后面
            # 例如：TEST_PLUGIN_API_KEY -> test_plugin + api_key

            # 尝试不同的分割点
            for i in range(1, len(parts)):
                potential_plugin = "_".join(parts[:i]).lower()
                potential_config_parts = parts[i:]

                # 检查插件是否存在于配置中心
                if potential_plugin in self._config_center._config_cache:
                    # 如果找到了匹配的插件，检查配置字段
                    config_cache = self._config_center._config_cache[potential_plugin]

                    # 先尝试下划线连接的版本（用于直接字段匹配）
                    underscore_config = "_".join(potential_config_parts).lower()
                    if underscore_config in config_cache:
                        return potential_plugin, underscore_config

                    # 如果不存在下划线版本，则使用点号连接（用于嵌套访问）
                    dot_config = (
                        "_".join(potential_config_parts).lower().replace("_", ".")
                    )
                    return potential_plugin, dot_config

            # 如果没有找到匹配的插件，使用默认分割（第一个部分作为插件名）
            plugin_name = parts[0].lower()
            config_key = "_".join(parts[1:]).lower().replace("_", ".")

            return plugin_name, config_key

        except Exception:
            return None, None


class ConfigHotReloader:
    """配置热更新管理器"""

    def __init__(self, config_center: DynamicConfigCenter):
        self._config_center = config_center
        self._logger = logging.getLogger(__name__)

        # 文件系统监听器
        self._file_observer = Observer()
        self._file_handlers: Dict[str, ConfigFileHandler] = {}

        # 环境变量监听器
        self._env_watcher = EnvironmentWatcher(config_center)

        # 状态管理
        self._running = False
        self._watched_files: Set[str] = set()
        self._watched_directories: Set[str] = set()

    def start(self):
        """启动配置热更新"""
        if self._running:
            return

        self._running = True

        # 启动文件系统监听
        self._file_observer.start()

        # 启动环境变量监听
        self._env_watcher.start_watching()

        self._logger.info("配置热更新已启动")

    def stop(self):
        """停止配置热更新"""
        if not self._running:
            return

        self._running = False

        # 停止文件系统监听
        self._file_observer.stop()
        self._file_observer.join()

        # 停止环境变量监听
        self._env_watcher.stop_watching()

        self._logger.info("配置热更新已停止")

    def watch_file(self, file_path: str):
        """
        监听配置文件

        Args:
            file_path: 配置文件路径
        """
        file_path = os.path.abspath(file_path)

        if file_path in self._watched_files:
            return

        if not os.path.exists(file_path):
            self._logger.warning(f"配置文件不存在: {file_path}")
            return

        # 创建文件处理器
        handler = ConfigFileHandler(self._config_center, file_path)
        self._file_handlers[file_path] = handler

        # 监听文件所在目录
        directory = os.path.dirname(file_path)
        if directory not in self._watched_directories:
            self._file_observer.schedule(handler, directory, recursive=False)
            self._watched_directories.add(directory)

        self._watched_files.add(file_path)
        self._logger.info(f"开始监听配置文件: {file_path}")

    def unwatch_file(self, file_path: str):
        """
        停止监听配置文件

        Args:
            file_path: 配置文件路径
        """
        file_path = os.path.abspath(file_path)

        if file_path not in self._watched_files:
            return

        # 移除文件处理器
        if file_path in self._file_handlers:
            del self._file_handlers[file_path]

        self._watched_files.remove(file_path)
        self._logger.info(f"停止监听配置文件: {file_path}")

    def watch_directory(self, directory_path: str, pattern: str = "*.json"):
        """
        监听配置目录

        Args:
            directory_path: 目录路径
            pattern: 文件匹配模式
        """
        directory_path = os.path.abspath(directory_path)

        if not os.path.exists(directory_path):
            self._logger.warning(f"配置目录不存在: {directory_path}")
            return

        # 创建目录处理器
        class DirectoryHandler(FileSystemEventHandler):
            def __init__(self, hot_reloader: ConfigHotReloader):
                self._hot_reloader = hot_reloader
                self._logger = logging.getLogger(__name__)

            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith(".json"):
                    self._hot_reloader.watch_file(event.src_path)

            def on_deleted(self, event):
                if not event.is_directory and event.src_path.endswith(".json"):
                    self._hot_reloader.unwatch_file(event.src_path)

        handler = DirectoryHandler(self)
        self._file_observer.schedule(handler, directory_path, recursive=True)

        # 监听目录中现有的配置文件
        for file_path in Path(directory_path).glob(pattern):
            if file_path.is_file():
                self.watch_file(str(file_path))

        self._watched_directories.add(directory_path)
        self._logger.info(f"开始监听配置目录: {directory_path}")

    def reload_all_configs(self):
        """重新加载所有配置"""
        self._logger.info("开始重新加载所有配置")

        # 重新加载所有监听的文件
        for file_path in self._watched_files:
            if os.path.exists(file_path):
                handler = self._file_handlers.get(file_path)
                if handler:
                    handler._reload_config()

        self._logger.info("所有配置重新加载完成")

    def get_status(self) -> Dict[str, Any]:
        """获取热更新状态"""
        return {
            "running": self._running,
            "watched_files": len(self._watched_files),
            "watched_directories": len(self._watched_directories),
            "file_handlers": len(self._file_handlers),
            "env_watcher_running": self._env_watcher._watching,
            "file_list": list(self._watched_files),
            "directory_list": list(self._watched_directories),
        }


# 全局配置热更新器实例
_global_hot_reloader: Optional[ConfigHotReloader] = None


def get_config_hot_reloader() -> ConfigHotReloader:
    """获取全局配置热更新器实例"""
    global _global_hot_reloader
    if _global_hot_reloader is None:
        from .dynamic_config_center import get_config_center

        _global_hot_reloader = ConfigHotReloader(get_config_center())
    return _global_hot_reloader


def reset_config_hot_reloader() -> None:
    """重置全局配置热更新器（主要用于测试）"""
    global _global_hot_reloader
    if _global_hot_reloader:
        _global_hot_reloader.stop()
    _global_hot_reloader = None
