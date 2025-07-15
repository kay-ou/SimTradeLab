# -*- coding: utf-8 -*-
"""
SimTradeLab 动态配置中心

提供配置热更新、监听和管理功能，支持运行时配置修改而无需重启系统。
这是v5.0架构的重要组成部分，实现了企业级配置管理能力。
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
from uuid import uuid4

from pydantic import BaseModel, Field

from ...core.events.contracts import create_config_changed_event
from ...exceptions import SimTradeLabError


class ConfigChangeEvent(BaseModel):
    """配置变更事件"""

    change_id: str = Field(default_factory=lambda: str(uuid4()))
    plugin_name: str
    key: str
    old_value: Any
    new_value: Any
    timestamp: datetime = Field(default_factory=datetime.now)
    user: Optional[str] = None
    reason: Optional[str] = None


class ConfigSource(BaseModel):
    """配置源信息"""

    source_type: str  # file, env, database, etc.
    source_path: str
    priority: int = 100
    enabled: bool = True
    last_modified: Optional[datetime] = None
    checksum: Optional[str] = None


class DynamicConfigError(SimTradeLabError):
    """动态配置异常"""

    pass


class DynamicConfigCenter:
    """
    动态配置中心

    核心功能：
    1. 配置热更新：运行时修改配置无需重启
    2. 配置监听：支持文件、环境变量等多种配置源监听
    3. 配置历史：记录所有配置变更历史
    4. 配置验证：基于Pydantic模型的强类型验证
    5. 配置回滚：支持配置版本管理和回滚
    6. 配置同步：多实例间的配置同步
    """

    def __init__(self, event_bus=None):
        self._logger = logging.getLogger(__name__)
        self._event_bus = event_bus

        # 配置存储
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._config_models: Dict[str, Type[BaseModel]] = {}
        self._config_sources: Dict[str, List[ConfigSource]] = {}

        # 监听器管理
        self._listeners: Dict[str, List[Callable]] = {}
        self._file_watchers: Dict[str, threading.Thread] = {}
        self._watching = False

        # 配置历史
        self._config_history: List[ConfigChangeEvent] = []
        self._max_history_size = 1000

        # 同步锁
        self._lock = threading.RLock()

        # 启动配置中心
        self._start_config_center()

    def _start_config_center(self):
        """启动配置中心"""
        self._logger.info("动态配置中心启动")
        self._watching = True

        # 加载默认配置源
        self._load_default_config_sources()

    def _load_default_config_sources(self):
        """加载默认配置源"""
        # 加载环境变量配置源
        self._add_config_source(
            "global",
            ConfigSource(
                source_type="env", source_path="ENV", priority=50, enabled=True
            ),
        )

        # 加载配置文件源（如果存在）
        config_file = Path("config.json")
        if config_file.exists():
            self._add_config_source(
                "global",
                ConfigSource(
                    source_type="file",
                    source_path=str(config_file),
                    priority=100,
                    enabled=True,
                    last_modified=datetime.fromtimestamp(config_file.stat().st_mtime),
                ),
            )
            self._start_file_watcher(str(config_file))

    def register_plugin_config(
        self,
        plugin_name: str,
        config_model: Type[BaseModel],
        initial_config: Optional[Dict[str, Any]] = None,
    ):
        """
        注册插件配置

        Args:
            plugin_name: 插件名称
            config_model: 配置模型类
            initial_config: 初始配置数据
        """
        with self._lock:
            self._config_models[plugin_name] = config_model

            if initial_config:
                self._config_cache[plugin_name] = initial_config
                self._logger.info(f"插件 {plugin_name} 配置已注册")
            else:
                # 创建默认配置
                default_config = config_model()
                self._config_cache[plugin_name] = default_config.model_dump()
                self._logger.info(f"插件 {plugin_name} 使用默认配置")

    def get_config(self, plugin_name: str, key: Optional[str] = None) -> Any:
        """
        获取配置值

        Args:
            plugin_name: 插件名称
            key: 配置键（可选，如果为None则返回整个配置）

        Returns:
            配置值
        """
        with self._lock:
            if plugin_name not in self._config_cache:
                raise DynamicConfigError(f"插件 {plugin_name} 配置未找到")

            config = self._config_cache[plugin_name]

            if key is None:
                return config

            # 支持点号分隔的嵌套键
            keys = key.split(".")
            value = config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    raise DynamicConfigError(f"配置键 {key} 在插件 {plugin_name} 中未找到")

            return value

    def set_config(
        self,
        plugin_name: str,
        key: str,
        value: Any,
        user: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """
        设置配置值

        Args:
            plugin_name: 插件名称
            key: 配置键
            value: 配置值
            user: 操作用户
            reason: 变更原因
        """
        with self._lock:
            if plugin_name not in self._config_cache:
                raise DynamicConfigError(f"插件 {plugin_name} 配置未找到")

            # 获取旧值
            old_value = self.get_config(plugin_name, key)

            # 验证新配置
            new_config = self._config_cache[plugin_name].copy()
            self._set_nested_value(new_config, key, value)

            # 使用配置模型验证
            if plugin_name in self._config_models:
                config_model = self._config_models[plugin_name]
                try:
                    validated_config = config_model.model_validate(new_config)
                    new_config = validated_config.model_dump()
                except Exception as e:
                    raise DynamicConfigError(f"配置验证失败: {str(e)}")

            # 更新配置
            self._config_cache[plugin_name] = new_config

            # 记录变更历史
            change_event = ConfigChangeEvent(
                plugin_name=plugin_name,
                key=key,
                old_value=old_value,
                new_value=value,
                user=user,
                reason=reason,
            )
            self._add_to_history(change_event)

            # 触发监听器
            self._notify_listeners(plugin_name, key, old_value, value)

            # 发送事件
            self._send_config_changed_event(plugin_name, key, old_value, value)

            self._logger.info(f"插件 {plugin_name} 配置 {key} 已更新")

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """设置嵌套键值"""
        keys = key.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def add_config_listener(
        self,
        plugin_name: str,
        listener: Callable[[str, Any, Any], None],
        key_pattern: Optional[str] = None,
    ):
        """
        添加配置变更监听器

        Args:
            plugin_name: 插件名称
            listener: 监听器函数 (key, old_value, new_value) -> None
            key_pattern: 键模式（可选，支持通配符）
        """
        with self._lock:
            listener_key = f"{plugin_name}:{key_pattern or '*'}"

            if listener_key not in self._listeners:
                self._listeners[listener_key] = []

            self._listeners[listener_key].append(listener)
            self._logger.debug(f"添加配置监听器: {listener_key}")

    def remove_config_listener(
        self,
        plugin_name: str,
        listener: Callable[[str, Any, Any], None],
        key_pattern: Optional[str] = None,
    ):
        """移除配置变更监听器"""
        with self._lock:
            listener_key = f"{plugin_name}:{key_pattern or '*'}"

            if listener_key in self._listeners:
                try:
                    self._listeners[listener_key].remove(listener)
                    if not self._listeners[listener_key]:
                        del self._listeners[listener_key]
                    self._logger.debug(f"移除配置监听器: {listener_key}")
                except ValueError:
                    self._logger.warning(f"监听器未找到: {listener_key}")

    def _notify_listeners(
        self, plugin_name: str, key: str, old_value: Any, new_value: Any
    ):
        """通知配置变更监听器"""
        with self._lock:
            # 查找匹配的监听器
            for listener_key, listeners in self._listeners.items():
                plugin_pattern, key_pattern = listener_key.split(":", 1)

                # 检查插件名称匹配
                if plugin_pattern != plugin_name and plugin_pattern != "*":
                    continue

                # 检查键模式匹配
                if key_pattern != "*" and key_pattern != key:
                    # 简单的通配符匹配
                    if "*" in key_pattern:
                        import fnmatch

                        if not fnmatch.fnmatch(key, key_pattern):
                            continue
                    else:
                        continue

                # 调用监听器
                for listener in listeners:
                    try:
                        listener(key, old_value, new_value)
                    except Exception as e:
                        self._logger.error(f"配置监听器调用失败: {str(e)}")

    def _send_config_changed_event(
        self, plugin_name: str, key: str, old_value: Any, new_value: Any
    ):
        """发送配置变更事件"""
        if self._event_bus:
            try:
                event = create_config_changed_event(
                    plugin=plugin_name,
                    key=key,
                    old_value=old_value,
                    new_value=new_value,
                )
                self._event_bus.publish(event)
            except Exception as e:
                self._logger.error(f"配置变更事件发送失败: {str(e)}")

    def _add_config_source(self, plugin_name: str, source: ConfigSource):
        """添加配置源"""
        with self._lock:
            if plugin_name not in self._config_sources:
                self._config_sources[plugin_name] = []

            self._config_sources[plugin_name].append(source)
            self._config_sources[plugin_name].sort(key=lambda x: x.priority)

            self._logger.debug(f"添加配置源: {plugin_name} -> {source.source_path}")

    def _start_file_watcher(self, file_path: str):
        """启动文件监听器"""
        if file_path in self._file_watchers:
            return

        def watch_file():
            """文件监听线程"""
            last_modified = None

            while self._watching:
                try:
                    if os.path.exists(file_path):
                        current_modified = os.path.getmtime(file_path)

                        if last_modified is None:
                            last_modified = current_modified
                        elif current_modified > last_modified:
                            last_modified = current_modified
                            self._reload_config_file(file_path)

                    time.sleep(1)  # 每秒检查一次

                except Exception as e:
                    self._logger.error(f"文件监听异常: {str(e)}")
                    time.sleep(5)  # 错误时等待5秒

        watcher_thread = threading.Thread(target=watch_file, daemon=True)
        watcher_thread.start()
        self._file_watchers[file_path] = watcher_thread

        self._logger.info(f"启动文件监听器: {file_path}")

    def _reload_config_file(self, file_path: str):
        """重新加载配置文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # 更新相关插件配置
            for plugin_name, plugin_config in config_data.items():
                if plugin_name in self._config_cache:
                    for key, value in plugin_config.items():
                        self.set_config(
                            plugin_name,
                            key,
                            value,
                            user="system",
                            reason=f"配置文件更新: {file_path}",
                        )

            self._logger.info(f"配置文件已重新加载: {file_path}")

        except Exception as e:
            self._logger.error(f"配置文件重新加载失败: {str(e)}")

    def _add_to_history(self, change_event: ConfigChangeEvent):
        """添加到配置历史"""
        self._config_history.append(change_event)

        # 限制历史记录大小
        if len(self._config_history) > self._max_history_size:
            self._config_history = self._config_history[-self._max_history_size :]

    def get_config_history(
        self,
        plugin_name: Optional[str] = None,
        key: Optional[str] = None,
        limit: int = 100,
    ) -> List[ConfigChangeEvent]:
        """
        获取配置变更历史

        Args:
            plugin_name: 插件名称过滤
            key: 配置键过滤
            limit: 返回数量限制

        Returns:
            配置变更历史列表
        """
        with self._lock:
            history = self._config_history

            # 过滤
            if plugin_name:
                history = [h for h in history if h.plugin_name == plugin_name]

            if key:
                history = [h for h in history if h.key == key]

            # 按时间倒序排列，返回最新的记录
            history.sort(key=lambda x: x.timestamp, reverse=True)

            return history[:limit]

    def rollback_config(self, change_id: str):
        """
        回滚配置到指定变更之前的状态

        Args:
            change_id: 变更ID
        """
        with self._lock:
            # 查找变更记录
            change_event = None
            for event in self._config_history:
                if event.change_id == change_id:
                    change_event = event
                    break

            if not change_event:
                raise DynamicConfigError(f"变更记录未找到: {change_id}")

            # 回滚配置
            self.set_config(
                change_event.plugin_name,
                change_event.key,
                change_event.old_value,
                user="system",
                reason=f"回滚变更: {change_id}",
            )

            self._logger.info(f"配置已回滚: {change_id}")

    def export_config(self, plugin_name: Optional[str] = None) -> Dict[str, Any]:
        """
        导出配置

        Args:
            plugin_name: 插件名称（可选，如果为None则导出所有配置）

        Returns:
            配置数据
        """
        with self._lock:
            if plugin_name:
                if plugin_name not in self._config_cache:
                    raise DynamicConfigError(f"插件 {plugin_name} 配置未找到")
                return {plugin_name: self._config_cache[plugin_name]}
            else:
                return self._config_cache.copy()

    def import_config(
        self,
        config_data: Dict[str, Any],
        user: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        """
        导入配置

        Args:
            config_data: 配置数据
            user: 操作用户
            reason: 导入原因
        """
        for plugin_name, plugin_config in config_data.items():
            if plugin_name in self._config_cache:
                for key, value in plugin_config.items():
                    self.set_config(plugin_name, key, value, user=user, reason=reason)

        self._logger.info(f"配置导入完成: {len(config_data)} 个插件")

    def shutdown(self):
        """关闭动态配置中心"""
        self._watching = False

        # 等待文件监听器结束
        for watcher in self._file_watchers.values():
            watcher.join(timeout=1)

        self._logger.info("动态配置中心已关闭")

    def get_status(self) -> Dict[str, Any]:
        """获取配置中心状态"""
        with self._lock:
            return {
                "running": self._watching,
                "registered_plugins": len(self._config_cache),
                "config_sources": sum(
                    len(sources) for sources in self._config_sources.values()
                ),
                "active_listeners": len(self._listeners),
                "file_watchers": len(self._file_watchers),
                "history_size": len(self._config_history),
                "plugin_names": list(self._config_cache.keys()),
            }


# 全局动态配置中心实例
_global_config_center: Optional[DynamicConfigCenter] = None


def get_config_center() -> DynamicConfigCenter:
    """获取全局动态配置中心实例"""
    global _global_config_center
    if _global_config_center is None:
        _global_config_center = DynamicConfigCenter()
    return _global_config_center


def reset_config_center() -> None:
    """重置全局动态配置中心（主要用于测试）"""
    global _global_config_center
    if _global_config_center:
        _global_config_center.shutdown()
    _global_config_center = None
