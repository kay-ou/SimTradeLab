# -*- coding: utf-8 -*-
"""
SimTradeLab 插件管理器
提供插件注册、发现、基础加载卸载功能
"""

import importlib
import importlib.util
import inspect
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union

from ..exceptions import SimTradeLabError
from ..plugins.base import BasePlugin, PluginConfig, PluginMetadata, PluginState
from ..plugins.config.validator import ConfigValidator
from .event_bus import Event, EventBus


class PluginManagerError(SimTradeLabError):
    """插件管理器异常"""

    pass


class PluginLoadError(PluginManagerError):
    """插件加载异常"""

    pass


class PluginRegistrationError(PluginManagerError):
    """插件注册异常"""

    pass


class PluginDiscoveryError(PluginManagerError):
    """插件发现异常"""

    pass


@dataclass
class PluginRegistry:
    """插件注册信息"""

    plugin_class: Type[BasePlugin]
    metadata: PluginMetadata
    config: Optional[PluginConfig] = None
    instance: Optional[BasePlugin] = None
    registered_at: float = field(default_factory=time.time)
    load_order: int = 0


class PluginManager:
    """
    插件管理器

    负责插件的注册、发现、加载、卸载和生命周期管理。
    与EventBus集成，提供插件间通信能力。
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        初始化插件管理器

        Args:
            event_bus: 事件总线实例，如果为None则创建新的
        """
        self._event_bus = event_bus or EventBus()
        self._plugins: Dict[str, PluginRegistry] = {}
        self._plugin_paths: Set[Path] = set()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

        # 插件状态统计
        self._stats = {"registered": 0, "loaded": 0, "active": 0, "failed": 0}

        # 注册内置事件处理器
        self._register_builtin_handlers()

    @property
    def event_bus(self) -> EventBus:
        """获取事件总线"""
        return self._event_bus

    def register_plugin(
        self,
        plugin_class: Type[BasePlugin],
        config: Optional[PluginConfig] = None,
        load_order: int = 100,
    ) -> str:
        """
        注册插件类

        Args:
            plugin_class: 插件类
            config: 插件配置
            load_order: 加载顺序，数值越小越先加载

        Returns:
            插件名称

        Raises:
            PluginRegistrationError: 注册失败时抛出
        """
        if not issubclass(plugin_class, BasePlugin):
            raise PluginRegistrationError(
                f"{plugin_class} is not a BasePlugin subclass"
            )

        try:
            # 获取插件元数据
            # 检查是否有自定义的元数据（不是从BasePlugin继承的）
            if (
                hasattr(plugin_class, "METADATA")
                and "METADATA" in plugin_class.__dict__
            ):
                metadata = plugin_class.METADATA
            else:
                # 如果没有元数据，创建默认的
                metadata = PluginMetadata(
                    name=plugin_class.__name__,
                    version="1.0.0",
                    description=plugin_class.__doc__
                    or f"Plugin {plugin_class.__name__}",
                )

            with self._lock:
                plugin_name = metadata.name

                if plugin_name in self._plugins:
                    raise PluginRegistrationError(
                        f"Plugin {plugin_name} is already registered"
                    )

                # 创建注册信息
                registry = PluginRegistry(
                    plugin_class=plugin_class,
                    metadata=metadata,
                    config=config,
                    load_order=load_order,
                )

                self._plugins[plugin_name] = registry
                self._stats["registered"] += 1

                self._logger.info(f"Registered plugin: {plugin_name}")

                # 发布插件注册事件
                self._event_bus.publish(
                    "plugin.registered",
                    data={
                        "plugin_name": plugin_name,
                        "metadata": metadata,
                        "load_order": load_order,
                    },
                    source="plugin_manager",
                )

                return plugin_name

        except Exception as e:
            raise PluginRegistrationError(
                f"Failed to register plugin {plugin_class}: {e}"
            )

    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        取消注册插件

        Args:
            plugin_name: 插件名称

        Returns:
            是否成功取消注册
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            registry = self._plugins[plugin_name]

            # 如果插件已加载，先卸载
            if registry.instance:
                self.unload_plugin(plugin_name)

            del self._plugins[plugin_name]
            self._stats["registered"] -= 1

            self._logger.info(f"Unregistered plugin: {plugin_name}")

            # 发布插件取消注册事件
            self._event_bus.publish(
                "plugin.unregistered",
                data={"plugin_name": plugin_name},
                source="plugin_manager",
            )

            return True

    def load_plugin(
        self, plugin_name: str, config: Optional[PluginConfig] = None
    ) -> BasePlugin:
        """
        加载插件

        Args:
            plugin_name: 插件名称
            config: 插件配置，如果为None则使用注册时的配置

        Returns:
            插件实例

        Raises:
            PluginLoadError: 加载失败时抛出
        """
        with self._lock:
            if plugin_name not in self._plugins:
                raise PluginLoadError(f"Plugin {plugin_name} is not registered")

            registry = self._plugins[plugin_name]

            if registry.instance:
                raise PluginLoadError(f"Plugin {plugin_name} is already loaded")

            try:
                # 使用提供的配置或注册时的配置
                plugin_config = config or registry.config or PluginConfig()

                # 如果插件定义了配置模型，则进行配置验证
                if hasattr(registry.plugin_class, 'config_model') and registry.plugin_class.config_model is not None:
                    try:
                        # 获取插件配置数据（存储在 PluginConfig.data 中）
                        config_data = getattr(plugin_config, 'data', {})
                        if config_data:
                            # 执行配置验证
                            validated_config = ConfigValidator.validate(
                                registry.plugin_class.config_model,
                                config_data
                            )
                            # 将验证后的配置更新到插件配置对象
                            plugin_config.data = validated_config.model_dump()
                            self._logger.info(f"插件 {plugin_name} 配置验证成功")
                    except Exception as e:
                        self._logger.error(f"插件 {plugin_name} 配置验证失败: {e}")
                        raise PluginLoadError(f"插件 {plugin_name} 配置验证失败: {e}")

                # 创建插件实例
                instance = registry.plugin_class(registry.metadata, plugin_config)

                # 初始化插件
                instance.initialize()

                # 更新注册信息
                registry.instance = instance
                registry.config = plugin_config
                self._stats["loaded"] += 1

                self._logger.info(f"Loaded plugin: {plugin_name}")

                # 发布插件加载事件
                self._event_bus.publish(
                    "plugin.loaded",
                    data={"plugin_name": plugin_name, "instance": instance},
                    source="plugin_manager",
                )

                return instance

            except Exception as e:
                self._stats["failed"] += 1
                self._logger.error(f"Failed to load plugin {plugin_name}: {e}")
                raise PluginLoadError(f"Failed to load plugin {plugin_name}: {e}")

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            是否成功卸载
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            registry = self._plugins[plugin_name]

            if not registry.instance:
                return False

            try:
                # 检查是否为活跃状态
                was_active = registry.instance.state == PluginState.STARTED

                # 停止并关闭插件
                if registry.instance.state in [PluginState.STARTED, PluginState.PAUSED]:
                    registry.instance.stop()

                registry.instance.shutdown()

                # 清除实例引用
                registry.instance = None
                self._stats["loaded"] -= 1

                if was_active:
                    self._stats["active"] -= 1

                self._logger.info(f"Unloaded plugin: {plugin_name}")

                # 发布插件卸载事件
                self._event_bus.publish(
                    "plugin.unloaded",
                    data={"plugin_name": plugin_name},
                    source="plugin_manager",
                )

                return True

            except Exception as e:
                self._logger.error(f"Failed to unload plugin {plugin_name}: {e}")
                return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        热重载插件，并尝试保持其状态。

        Args:
            plugin_name: 插件名称

        Returns:
            是否成功重载
        """
        with self._lock:
            if plugin_name not in self._plugins:
                self._logger.error(
                    f"Cannot reload: Plugin {plugin_name} not registered."
                )
                return False

            registry = self._plugins[plugin_name]

            if not registry.instance:
                self._logger.warning(
                    f"Plugin {plugin_name} is not loaded. Loading it instead."
                )
                try:
                    self.load_plugin(plugin_name)
                    return True
                except PluginLoadError:
                    return False

            # 1. 保存状态
            old_instance = registry.instance
            state_to_restore = None
            if hasattr(old_instance, "get_state") and callable(old_instance.get_state):
                try:
                    state_to_restore = old_instance.get_state()
                    self._logger.info(f"Saved state for plugin {plugin_name}.")
                except Exception as e:
                    self._logger.error(f"Failed to get state from {plugin_name}: {e}")

            # 2. 卸载旧插件
            if not self.unload_plugin(plugin_name):
                self._logger.error(
                    f"Failed to unload plugin {plugin_name} during reload."
                )
                return False

            # 3. 加载新插件
            try:
                new_instance = self.load_plugin(plugin_name, registry.config)
            except PluginLoadError as e:
                self._logger.error(
                    f"Failed to load plugin {plugin_name} during reload: {e}"
                )
                return False

            # 4. 恢复状态
            if (
                state_to_restore
                and hasattr(new_instance, "set_state")
                and callable(new_instance.set_state)
            ):
                try:
                    new_instance.set_state(state_to_restore)
                    self._logger.info(
                        f"Restored state for reloaded plugin {plugin_name}."
                    )
                except Exception as e:
                    self._logger.error(
                        f"Failed to set state for reloaded plugin {plugin_name}: {e}"
                    )

            self._logger.info(f"Plugin {plugin_name} reloaded successfully.")

            # 发布插件重载事件
            self._event_bus.publish(
                "plugin.reloaded",
                data={"plugin_name": plugin_name, "instance": new_instance},
                source="plugin_manager",
            )

            return True

    def start_plugin(self, plugin_name: str) -> bool:
        """
        启动插件

        Args:
            plugin_name: 插件名称

        Returns:
            是否成功启动
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            registry = self._plugins[plugin_name]

            if not registry.instance:
                return False

            try:
                registry.instance.start()
                self._stats["active"] += 1

                self._logger.info(f"Started plugin: {plugin_name}")

                # 发布插件启动事件
                self._event_bus.publish(
                    "plugin.started",
                    data={"plugin_name": plugin_name},
                    source="plugin_manager",
                )

                return True

            except Exception as e:
                self._logger.error(f"Failed to start plugin {plugin_name}: {e}")
                return False

    def stop_plugin(self, plugin_name: str) -> bool:
        """
        停止插件

        Args:
            plugin_name: 插件名称

        Returns:
            是否成功停止
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            registry = self._plugins[plugin_name]

            if not registry.instance:
                return False

            try:
                if registry.instance.state == PluginState.STARTED:
                    registry.instance.stop()
                    self._stats["active"] -= 1

                    self._logger.info(f"Stopped plugin: {plugin_name}")

                    # 发布插件停止事件
                    self._event_bus.publish(
                        "plugin.stopped",
                        data={"plugin_name": plugin_name},
                        source="plugin_manager",
                    )

                return True

            except Exception as e:
                self._logger.error(f"Failed to stop plugin {plugin_name}: {e}")
                return False

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        获取插件实例

        Args:
            plugin_name: 插件名称

        Returns:
            插件实例，如果不存在或未加载则返回None
        """
        with self._lock:
            registry = self._plugins.get(plugin_name)
            return registry.instance if registry else None

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        获取插件信息

        Args:
            plugin_name: 插件名称

        Returns:
            插件信息字典
        """
        with self._lock:
            registry = self._plugins.get(plugin_name)
            if not registry:
                return None

            info = {
                "name": registry.metadata.name,
                "version": registry.metadata.version,
                "description": registry.metadata.description,
                "author": registry.metadata.author,
                "dependencies": registry.metadata.dependencies,
                "tags": registry.metadata.tags,
                "category": registry.metadata.category,
                "priority": registry.metadata.priority,
                "registered_at": registry.registered_at,
                "load_order": registry.load_order,
                "loaded": registry.instance is not None,
                "state": registry.instance.state.value
                if registry.instance
                else "unloaded",
            }

            if registry.instance:
                info.update(
                    {
                        "uptime": registry.instance.uptime,
                        "status": registry.instance.get_status(),
                    }
                )

            return info

    def list_plugins(self, filter_loaded: Optional[bool] = None) -> List[str]:
        """
        列出插件

        Args:
            filter_loaded: 是否过滤已加载的插件，None表示不过滤

        Returns:
            插件名称列表
        """
        with self._lock:
            if filter_loaded is None:
                return list(self._plugins.keys())
            elif filter_loaded:
                return [name for name, reg in self._plugins.items() if reg.instance]
            else:
                return [name for name, reg in self._plugins.items() if not reg.instance]

    def load_plugins_from_directory(self, directory: Union[str, Path]) -> List[str]:
        """
        从目录加载插件

        Args:
            directory: 插件目录路径

        Returns:
            成功加载的插件名称列表

        Raises:
            PluginDiscoveryError: 发现插件失败时抛出
        """
        directory = Path(directory)
        if not directory.exists():
            raise PluginDiscoveryError(f"Directory {directory} does not exist")
        if not directory.is_dir():
            raise PluginDiscoveryError(f"Path {directory} is not a directory")

        self._plugin_paths.add(directory)
        loaded_plugins = []

        try:
            # 查找Python文件
            for py_file in directory.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                try:
                    plugin_names = self._load_plugin_from_file(py_file)
                    loaded_plugins.extend(plugin_names)
                except Exception as e:
                    self._logger.warning(f"Failed to load plugin from {py_file}: {e}")

            # 查找包目录
            for pkg_dir in directory.iterdir():
                if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
                    try:
                        plugin_names = self._load_plugin_from_package(pkg_dir)
                        loaded_plugins.extend(plugin_names)
                    except Exception as e:
                        self._logger.warning(
                            f"Failed to load plugin from {pkg_dir}: {e}"
                        )

            self._logger.info(f"Loaded {len(loaded_plugins)} plugins from {directory}")
            return loaded_plugins

        except Exception as e:
            raise PluginDiscoveryError(f"Failed to load plugins from {directory}: {e}")

    def load_all_plugins(self, start: bool = False) -> Dict[str, bool]:
        """
        加载所有已注册的插件

        Args:
            start: 是否同时启动插件

        Returns:
            插件名称到加载结果的映射
        """
        results = {}

        # 按加载顺序排序
        plugins_by_order = sorted(self._plugins.items(), key=lambda x: x[1].load_order)

        for plugin_name, registry in plugins_by_order:
            if registry.instance:
                results[plugin_name] = True  # 已加载
                continue

            try:
                self.load_plugin(plugin_name)
                if start:
                    self.start_plugin(plugin_name)
                results[plugin_name] = True
            except Exception as e:
                self._logger.error(f"Failed to load plugin {plugin_name}: {e}")
                results[plugin_name] = False

        return results

    def unload_all_plugins(self) -> Dict[str, bool]:
        """
        卸载所有插件

        Returns:
            插件名称到卸载结果的映射
        """
        results = {}

        # 按加载顺序逆序卸载
        plugins_by_order = sorted(
            self._plugins.items(), key=lambda x: x[1].load_order, reverse=True
        )

        for plugin_name, registry in plugins_by_order:
            if not registry.instance:
                results[plugin_name] = True  # 未加载
                continue

            try:
                self.unload_plugin(plugin_name)
                results[plugin_name] = True
            except Exception as e:
                self._logger.error(f"Failed to unload plugin {plugin_name}: {e}")
                results[plugin_name] = False

        return results

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        获取所有已加载的插件实例

        Returns:
            插件名称到插件实例的映射
        """
        with self._lock:
            return {
                name: registry.instance
                for name, registry in self._plugins.items()
                if registry.instance is not None
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取插件管理器统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            return {
                **self._stats,
                "plugin_paths_count": len(self._plugin_paths),
                "event_bus_stats": self._event_bus.get_stats(),
            }

    def shutdown(self) -> None:
        """关闭插件管理器"""
        self._logger.info("Shutting down plugin manager")

        # 卸载所有插件
        self.unload_all_plugins()

        # 关闭事件总线
        self._event_bus.shutdown()

        # 清理资源
        self._plugins.clear()
        self._plugin_paths.clear()

        self._logger.info("Plugin manager shutdown completed")

    def _load_plugin_from_file(self, file_path: Path) -> List[str]:
        """从文件加载插件"""
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            return []

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return self._discover_plugins_in_module(module)

    def _load_plugin_from_package(self, package_path: Path) -> List[str]:
        """从包加载插件"""
        package_name = package_path.name
        spec = importlib.util.spec_from_file_location(
            package_name, package_path / "__init__.py"
        )
        if not spec or not spec.loader:
            return []

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return self._discover_plugins_in_module(module)

    def _discover_plugins_in_module(self, module) -> List[str]:
        """在模块中发现插件类"""
        discovered = []

        for name in dir(module):
            obj = getattr(module, name)

            # 检查是否是BasePlugin的子类
            if (
                inspect.isclass(obj)
                and issubclass(obj, BasePlugin)
                and obj is not BasePlugin
            ):
                try:
                    plugin_name = self.register_plugin(obj)
                    discovered.append(plugin_name)
                except Exception as e:
                    self._logger.warning(f"Failed to register plugin {obj}: {e}")

        return discovered

    def _register_builtin_handlers(self) -> None:
        """注册内置事件处理器"""
        # 插件状态变更事件处理
        self._event_bus.subscribe("plugin.loaded", self._on_plugin_loaded)
        self._event_bus.subscribe("plugin.started", self._on_plugin_started)
        self._event_bus.subscribe("plugin.stopped", self._on_plugin_stopped)
        self._event_bus.subscribe("plugin.unloaded", self._on_plugin_unloaded)

    def _on_plugin_loaded(self, event: Event) -> None:
        """处理插件加载事件"""
        plugin_name = event.data["plugin_name"]
        self._logger.debug(f"Plugin loaded event: {plugin_name}")

    def _on_plugin_started(self, event: Event) -> None:
        """处理插件启动事件"""
        plugin_name = event.data["plugin_name"]
        self._logger.debug(f"Plugin started event: {plugin_name}")

    def _on_plugin_stopped(self, event: Event) -> None:
        """处理插件停止事件"""
        plugin_name = event.data["plugin_name"]
        self._logger.debug(f"Plugin stopped event: {plugin_name}")

    def _on_plugin_unloaded(self, event: Event) -> None:
        """处理插件卸载事件"""
        plugin_name = event.data["plugin_name"]
        self._logger.debug(f"Plugin unloaded event: {plugin_name}")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()
