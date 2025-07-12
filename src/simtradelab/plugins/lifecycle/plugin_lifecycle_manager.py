# -*- coding: utf-8 -*-
"""
插件生命周期管理器

实现插件的热插拔、状态管理和依赖管理集成。
"""

import logging
import threading
import traceback
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...core.event_bus import EventBus
from ...core.events.cloud_event import CloudEvent
from ..base import BasePlugin
from ..dependency.manifest import PluginManifest
from ..dependency.registry import PluginRegistry
from ..dependency.resolver import DependencyResolver


class PluginState(str, Enum):
    """插件状态枚举"""

    UNKNOWN = "unknown"  # 未知状态
    LOADING = "loading"  # 加载中
    LOADED = "loaded"  # 已加载
    STARTING = "starting"  # 启动中
    ACTIVE = "active"  # 活跃运行
    STOPPING = "stopping"  # 停止中
    STOPPED = "stopped"  # 已停止
    UNLOADING = "unloading"  # 卸载中
    UNLOADED = "unloaded"  # 已卸载
    ERROR = "error"  # 错误状态


class PluginOperation(str, Enum):
    """插件操作类型"""

    LOAD = "load"
    UNLOAD = "unload"
    START = "start"
    STOP = "stop"
    RELOAD = "reload"
    UPDATE = "update"


class PluginInfo:
    """插件信息类"""

    def __init__(self, manifest: PluginManifest, plugin_path: Optional[Path] = None):
        """
        初始化插件信息

        Args:
            manifest: 插件清单
            plugin_path: 插件路径
        """
        self.manifest = manifest
        self.plugin_path = plugin_path
        self.state = PluginState.UNKNOWN
        self.instance: Optional[BasePlugin] = None
        self.load_time: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
        self.error_count = 0
        self.last_error: Optional[str] = None
        self.state_history: List[tuple] = []  # (timestamp, old_state, new_state)

    def set_state(self, new_state: PluginState, error_msg: Optional[str] = None):
        """设置插件状态"""
        old_state = self.state
        self.state = new_state
        self.state_history.append((datetime.now(), old_state, new_state))

        if error_msg:
            self.last_error = error_msg
            self.error_count += 1

        # 更新时间戳
        if new_state == PluginState.LOADED:
            self.load_time = datetime.now()
        elif new_state == PluginState.ACTIVE:
            self.start_time = datetime.now()


class PluginLifecycleManager:
    """
    插件生命周期管理器

    负责插件的热插拔、状态管理、依赖解析和生命周期控制。
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        初始化插件生命周期管理器

        Args:
            event_bus: 事件总线
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus or EventBus()

        # 插件注册表和依赖解析器
        self.registry = PluginRegistry()
        self.dependency_resolver = DependencyResolver(self.registry)

        # 插件状态管理
        self._plugins: Dict[str, PluginInfo] = {}
        self._lock = threading.RLock()

        # 生命周期钩子
        self._lifecycle_hooks: Dict[str, List[Callable]] = {
            "before_load": [],
            "after_load": [],
            "before_start": [],
            "after_start": [],
            "before_stop": [],
            "after_stop": [],
            "before_unload": [],
            "after_unload": [],
            "on_error": [],
        }

        self.logger.info("插件生命周期管理器已初始化")

    # 插件注册和发现
    def register_plugin(
        self, manifest: PluginManifest, plugin_path: Optional[Path] = None
    ) -> bool:
        """
        注册插件

        Args:
            manifest: 插件清单
            plugin_path: 插件路径

        Returns:
            注册是否成功
        """
        try:
            # 注册到注册表
            if not self.registry.register_plugin(manifest, plugin_path):
                return False

            # 创建插件信息
            with self._lock:
                plugin_info = PluginInfo(manifest, plugin_path)
                self._plugins[manifest.name] = plugin_info

            # 发送事件
            self._emit_event(
                "plugin.registered",
                {"plugin_name": manifest.name, "manifest": manifest.model_dump()},
            )

            self.logger.info(f"插件 {manifest.name} 注册成功")
            return True

        except Exception as e:
            self.logger.error(f"注册插件 {manifest.name} 失败: {e}")
            return False

    def discover_plugins(self, directory: Path, recursive: bool = True) -> int:
        """
        发现并注册插件

        Args:
            directory: 插件目录
            recursive: 是否递归扫描

        Returns:
            发现的插件数量
        """
        count = self.registry.register_from_directory(directory, recursive)

        # 为注册表中新增的插件创建插件信息
        with self._lock:
            for plugin_name in self.registry.list_plugins():
                if plugin_name not in self._plugins:
                    manifest = self.registry.get_manifest(plugin_name)
                    plugin_path = self.registry.get_plugin_path(plugin_name)
                    if manifest:
                        plugin_info = PluginInfo(manifest, plugin_path)
                        self._plugins[plugin_name] = plugin_info

        self.logger.info(f"发现并注册了 {count} 个插件")
        return count

    # 插件加载和卸载
    def load_plugin(self, plugin_name: str, force: bool = False) -> bool:
        """
        加载插件

        Args:
            plugin_name: 插件名称
            force: 是否强制加载（忽略依赖）

        Returns:
            加载是否成功
        """
        with self._lock:
            plugin_info = self._plugins.get(plugin_name)
            if not plugin_info:
                self.logger.error(f"插件 {plugin_name} 未注册")
                return False

            if plugin_info.state in [PluginState.LOADED, PluginState.ACTIVE]:
                self.logger.warning(f"插件 {plugin_name} 已加载")
                return True

            try:
                plugin_info.set_state(PluginState.LOADING)

                # 执行前置钩子
                self._execute_hooks("before_load", plugin_name, plugin_info)

                # 检查并加载依赖
                if not force:
                    if not self._load_dependencies(plugin_name):
                        plugin_info.set_state(PluginState.ERROR, "依赖加载失败")
                        return False

                # 动态导入插件模块
                plugin_instance = self._import_plugin(plugin_info)
                if not plugin_instance:
                    plugin_info.set_state(PluginState.ERROR, "插件导入失败")
                    return False

                plugin_info.instance = plugin_instance
                plugin_info.set_state(PluginState.LOADED)

                # 执行后置钩子
                self._execute_hooks("after_load", plugin_name, plugin_info)

                # 发送事件
                self._emit_event(
                    "plugin.loaded",
                    {
                        "plugin_name": plugin_name,
                        "load_time": plugin_info.load_time.isoformat(),
                    },
                )

                self.logger.info(f"插件 {plugin_name} 加载成功")
                return True

            except Exception as e:
                error_msg = f"加载插件失败: {e}"
                plugin_info.set_state(PluginState.ERROR, error_msg)
                self._execute_hooks("on_error", plugin_name, plugin_info, e)
                self.logger.error(f"加载插件 {plugin_name} 失败: {e}")
                self.logger.debug(traceback.format_exc())
                return False

    def unload_plugin(self, plugin_name: str, force: bool = False) -> bool:
        """
        卸载插件

        Args:
            plugin_name: 插件名称
            force: 是否强制卸载（忽略依赖检查）

        Returns:
            卸载是否成功
        """
        with self._lock:
            plugin_info = self._plugins.get(plugin_name)
            if not plugin_info:
                self.logger.error(f"插件 {plugin_name} 不存在")
                return False

            if plugin_info.state == PluginState.UNLOADED:
                self.logger.warning(f"插件 {plugin_name} 已卸载")
                return True

            try:
                # 检查是否有其他插件依赖此插件
                if not force:
                    dependents = self.registry.get_plugin_dependents(plugin_name)
                    active_dependents = [
                        dep
                        for dep in dependents
                        if self._plugins.get(dep)
                        and self._plugins[dep].state == PluginState.ACTIVE
                    ]
                    if active_dependents:
                        self.logger.error(
                            f"插件 {plugin_name} 被以下插件依赖: {active_dependents}"
                        )
                        return False

                plugin_info.set_state(PluginState.UNLOADING)

                # 执行前置钩子
                self._execute_hooks("before_unload", plugin_name, plugin_info)

                # 先停止插件
                if plugin_info.state == PluginState.ACTIVE:
                    if not self.stop_plugin(plugin_name):
                        if not force:
                            plugin_info.set_state(PluginState.ERROR, "停止插件失败")
                            return False

                # 清理插件实例
                if plugin_info.instance:
                    try:
                        if hasattr(plugin_info.instance, "cleanup"):
                            plugin_info.instance.cleanup()
                    except Exception as e:
                        self.logger.warning(f"插件 {plugin_name} 清理失败: {e}")

                    plugin_info.instance = None

                plugin_info.set_state(PluginState.UNLOADED)

                # 执行后置钩子
                self._execute_hooks("after_unload", plugin_name, plugin_info)

                # 发送事件
                self._emit_event("plugin.unloaded", {"plugin_name": plugin_name})

                self.logger.info(f"插件 {plugin_name} 卸载成功")
                return True

            except Exception as e:
                error_msg = f"卸载插件失败: {e}"
                plugin_info.set_state(PluginState.ERROR, error_msg)
                self._execute_hooks("on_error", plugin_name, plugin_info, e)
                self.logger.error(f"卸载插件 {plugin_name} 失败: {e}")
                return False

    # 插件启动和停止
    def start_plugin(self, plugin_name: str) -> bool:
        """
        启动插件

        Args:
            plugin_name: 插件名称

        Returns:
            启动是否成功
        """
        with self._lock:
            plugin_info = self._plugins.get(plugin_name)
            if not plugin_info:
                self.logger.error(f"插件 {plugin_name} 不存在")
                return False

            if plugin_info.state == PluginState.ACTIVE:
                self.logger.warning(f"插件 {plugin_name} 已运行")
                return True

            if plugin_info.state != PluginState.LOADED:
                self.logger.error(f"插件 {plugin_name} 未加载，当前状态: {plugin_info.state}")
                return False

            try:
                plugin_info.set_state(PluginState.STARTING)

                # 执行前置钩子
                self._execute_hooks("before_start", plugin_name, plugin_info)

                # 启动插件
                if plugin_info.instance and hasattr(plugin_info.instance, "start"):
                    plugin_info.instance.start()

                plugin_info.set_state(PluginState.ACTIVE)

                # 执行后置钩子
                self._execute_hooks("after_start", plugin_name, plugin_info)

                # 发送事件
                self._emit_event(
                    "plugin.started",
                    {
                        "plugin_name": plugin_name,
                        "start_time": plugin_info.start_time.isoformat(),
                    },
                )

                self.logger.info(f"插件 {plugin_name} 启动成功")
                return True

            except Exception as e:
                error_msg = f"启动插件失败: {e}"
                plugin_info.set_state(PluginState.ERROR, error_msg)
                self._execute_hooks("on_error", plugin_name, plugin_info, e)
                self.logger.error(f"启动插件 {plugin_name} 失败: {e}")
                return False

    def stop_plugin(self, plugin_name: str) -> bool:
        """
        停止插件

        Args:
            plugin_name: 插件名称

        Returns:
            停止是否成功
        """
        with self._lock:
            plugin_info = self._plugins.get(plugin_name)
            if not plugin_info:
                self.logger.error(f"插件 {plugin_name} 不存在")
                return False

            if plugin_info.state == PluginState.STOPPED:
                self.logger.warning(f"插件 {plugin_name} 已停止")
                return True

            if plugin_info.state != PluginState.ACTIVE:
                self.logger.error(f"插件 {plugin_name} 未运行，当前状态: {plugin_info.state}")
                return False

            try:
                plugin_info.set_state(PluginState.STOPPING)

                # 执行前置钩子
                self._execute_hooks("before_stop", plugin_name, plugin_info)

                # 停止插件
                if plugin_info.instance and hasattr(plugin_info.instance, "stop"):
                    plugin_info.instance.stop()

                plugin_info.set_state(PluginState.STOPPED)

                # 执行后置钩子
                self._execute_hooks("after_stop", plugin_name, plugin_info)

                # 发送事件
                self._emit_event("plugin.stopped", {"plugin_name": plugin_name})

                self.logger.info(f"插件 {plugin_name} 停止成功")
                return True

            except Exception as e:
                error_msg = f"停止插件失败: {e}"
                plugin_info.set_state(PluginState.ERROR, error_msg)
                self._execute_hooks("on_error", plugin_name, plugin_info, e)
                self.logger.error(f"停止插件 {plugin_name} 失败: {e}")
                return False

    # 插件热重载
    def reload_plugin(self, plugin_name: str, preserve_state: bool = True) -> bool:
        """
        重载插件

        Args:
            plugin_name: 插件名称
            preserve_state: 是否保持状态

        Returns:
            重载是否成功
        """
        with self._lock:
            plugin_info = self._plugins.get(plugin_name)
            if not plugin_info:
                self.logger.error(f"插件 {plugin_name} 不存在")
                return False

            # 保存当前状态
            old_state = plugin_info.state
            state_data = None

            if preserve_state and plugin_info.instance:
                try:
                    if hasattr(plugin_info.instance, "get_state"):
                        state_data = plugin_info.instance.get_state()
                except Exception as e:
                    self.logger.warning(f"获取插件 {plugin_name} 状态失败: {e}")

            try:
                # 卸载插件
                if not self.unload_plugin(plugin_name, force=True):
                    return False

                # 重新加载插件
                if not self.load_plugin(plugin_name):
                    return False

                # 恢复状态
                if preserve_state and state_data and plugin_info.instance:
                    try:
                        if hasattr(plugin_info.instance, "set_state"):
                            plugin_info.instance.set_state(state_data)
                    except Exception as e:
                        self.logger.warning(f"恢复插件 {plugin_name} 状态失败: {e}")

                # 如果之前是活跃状态，重新启动
                if old_state == PluginState.ACTIVE:
                    return self.start_plugin(plugin_name)

                # 发送事件
                self._emit_event(
                    "plugin.reloaded",
                    {
                        "plugin_name": plugin_name,
                        "state_preserved": preserve_state and state_data is not None,
                    },
                )

                self.logger.info(f"插件 {plugin_name} 重载成功")
                return True

            except Exception as e:
                self.logger.error(f"重载插件 {plugin_name} 失败: {e}")
                return False

    # 状态查询
    def get_plugin_state(self, plugin_name: str) -> Optional[PluginState]:
        """获取插件状态"""
        plugin_info = self._plugins.get(plugin_name)
        return plugin_info.state if plugin_info else None

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> Dict[str, PluginState]:
        """列出所有插件及其状态"""
        return {name: info.state for name, info in self._plugins.items()}

    def get_active_plugins(self) -> List[str]:
        """获取活跃插件列表"""
        return [
            name
            for name, info in self._plugins.items()
            if info.state == PluginState.ACTIVE
        ]

    # 批量操作
    def load_all_plugins(self, force: bool = False) -> Dict[str, bool]:
        """加载所有插件"""
        results = {}

        # 按依赖顺序加载
        try:
            load_order = self.dependency_resolver.resolve_dependencies(
                list(self._plugins.keys())
            )
        except Exception as e:
            self.logger.warning(f"无法解析依赖顺序，使用注册顺序: {e}")
            load_order = list(self._plugins.keys())

        for plugin_name in load_order:
            results[plugin_name] = self.load_plugin(plugin_name, force)

        return results

    def start_all_plugins(self) -> Dict[str, bool]:
        """启动所有已加载的插件"""
        results = {}
        for plugin_name, plugin_info in self._plugins.items():
            if plugin_info.state == PluginState.LOADED:
                results[plugin_name] = self.start_plugin(plugin_name)
        return results

    def stop_all_plugins(self) -> Dict[str, bool]:
        """停止所有活跃插件"""
        results = {}
        # 按依赖关系逆序停止
        active_plugins = self.get_active_plugins()
        try:
            load_order = self.dependency_resolver.resolve_dependencies(active_plugins)
        except Exception as e:
            self.logger.warning(f"无法解析依赖顺序，使用逆序: {e}")
            load_order = active_plugins

        for plugin_name in reversed(load_order):
            results[plugin_name] = self.stop_plugin(plugin_name)

        return results

    # 生命周期钩子管理
    def add_lifecycle_hook(self, hook_name: str, callback: Callable):
        """添加生命周期钩子"""
        if hook_name in self._lifecycle_hooks:
            self._lifecycle_hooks[hook_name].append(callback)
        else:
            raise ValueError(f"未知的钩子类型: {hook_name}")

    def remove_lifecycle_hook(self, hook_name: str, callback: Callable):
        """移除生命周期钩子"""
        if hook_name in self._lifecycle_hooks:
            try:
                self._lifecycle_hooks[hook_name].remove(callback)
            except ValueError:
                pass

    # 内部方法
    def _load_dependencies(self, plugin_name: str) -> bool:
        """加载插件依赖"""
        try:
            # 直接解析依赖，获取加载顺序
            load_order = self.dependency_resolver.resolve_dependencies([plugin_name])

            # 加载依赖插件（排除目标插件本身）
            for dep_plugin in load_order:
                if dep_plugin == plugin_name:
                    continue

                dep_info = self._plugins.get(dep_plugin)
                if dep_info and dep_info.state not in [
                    PluginState.LOADED,
                    PluginState.ACTIVE,
                ]:
                    if not self.load_plugin(dep_plugin):
                        return False

            return True

        except Exception as e:
            self.logger.error(f"加载插件 {plugin_name} 的依赖失败: {e}")
            return False

    def _import_plugin(self, plugin_info: PluginInfo) -> Optional[BasePlugin]:
        """动态导入插件"""
        if not plugin_info.plugin_path:
            self.logger.error(f"插件 {plugin_info.manifest.name} 没有路径信息")
            return None

        try:
            import importlib.util
            import sys

            # 构建模块路径
            module_path = plugin_info.plugin_path / plugin_info.manifest.entry_point
            if not module_path.exists():
                self.logger.error(f"插件入口文件不存在: {module_path}")
                return None

            # 动态导入模块
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_info.manifest.name}", module_path
            )
            if not spec or not spec.loader:
                self.logger.error(f"无法创建模块规范: {module_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr != BasePlugin
                ):
                    plugin_class = attr
                    break

            if not plugin_class:
                self.logger.error(f"插件模块中未找到BasePlugin子类: {module_path}")
                return None

            # 创建插件实例
            plugin_instance = plugin_class(
                config=plugin_info.manifest.model_dump(), event_bus=self.event_bus
            )

            return plugin_instance

        except Exception as e:
            self.logger.error(f"导入插件 {plugin_info.manifest.name} 失败: {e}")
            self.logger.debug(traceback.format_exc())
            return None

    def _execute_hooks(
        self,
        hook_name: str,
        plugin_name: str,
        plugin_info: PluginInfo,
        exception: Optional[Exception] = None,
    ):
        """执行生命周期钩子"""
        try:
            for callback in self._lifecycle_hooks.get(hook_name, []):
                if exception:
                    callback(plugin_name, plugin_info, exception)
                else:
                    callback(plugin_name, plugin_info)
        except Exception as e:
            self.logger.error(f"执行钩子 {hook_name} 失败: {e}")

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """发送事件"""
        try:
            event = CloudEvent(
                type=event_type, source="plugin_lifecycle_manager", data=data
            )
            self.event_bus.publish_cloud_event(event)
        except Exception as e:
            self.logger.warning(f"发送事件失败: {e}")

    # 上下文管理器
    @contextmanager
    def batch_operation(self):
        """批量操作上下文管理器"""
        self.logger.info("开始批量插件操作")
        try:
            yield
        finally:
            self.logger.info("批量插件操作完成")

    # 清理方法
    def shutdown(self):
        """关闭生命周期管理器"""
        self.logger.info("开始关闭插件生命周期管理器")

        # 停止所有插件
        self.stop_all_plugins()

        # 卸载所有插件并清理
        with self._lock:
            for plugin_name in list(self._plugins.keys()):
                self.unload_plugin(plugin_name, force=True)

            # 确保清理完毕
            self._plugins.clear()

        self.logger.info("插件生命周期管理器已关闭")
