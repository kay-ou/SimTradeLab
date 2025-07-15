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
from ..plugins.base import BasePlugin, PluginMetadata, PluginState
from ..plugins.config.base_config import BasePluginConfig
from .config.config_manager import get_config_manager
from .event_bus import EventBus
from .events.cloud_event import CloudEvent


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
    config: Optional[Any] = None  # 可以是BasePluginConfig或任何Pydantic模型
    instance: Optional[BasePlugin] = None
    registered_at: float = field(default_factory=time.time)
    load_order: int = 0


class PluginManager:
    """
    插件管理器

    负责插件的注册、发现、加载、卸载和生命周期管理。
    与EventBus集成，提供插件间通信能力。
    """

    def __init__(
        self, event_bus: Optional[EventBus] = None, auto_register_builtin: bool = False
    ):
        """
        初始化插件管理器

        Args:
            event_bus: 事件总线实例，可选
            auto_register_builtin: 是否自动注册内置插件，默认False（显式注册原则）
        """
        self._event_bus = event_bus  # 不强制创建EventBus
        self._plugins: Dict[str, PluginRegistry] = {}
        self._plugin_paths: Set[Path] = set()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)
        self._auto_register_builtin = auto_register_builtin

        # E9修复：集成统一配置管理器
        self._config_manager = get_config_manager()

        # 插件状态统计
        self._stats = {"registered": 0, "loaded": 0, "active": 0, "failed": 0}

        # 只有在有事件总线时才注册事件处理器
        if self._event_bus:
            self._register_builtin_handlers()

        # E4修复：简化插件注册机制
        # 只有明确启用时才进行自动发现（用于开发模式）
        if self._auto_register_builtin:
            self._auto_discover_builtin_plugins()
        else:
            # 显式注册核心插件
            self._register_core_plugins()

    @property
    def event_bus(self) -> Optional[EventBus]:
        """获取事件总线"""
        return self._event_bus

    def set_event_bus(self, event_bus: EventBus) -> None:
        """
        设置事件总线

        Args:
            event_bus: 事件总线实例
        """
        self._event_bus = event_bus
        self._register_builtin_handlers()

    def register_plugin(
        self,
        plugin_class: Type[BasePlugin],
        config: Optional[BasePluginConfig] = None,
        load_order: int = 100,
        name_override: Optional[str] = None,
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
        # E4修复：验证插件类是否为BasePlugin的子类（处理导入路径不一致问题）
        is_base_plugin_subclass = False

        # 方法1：检查MRO中是否有BasePlugin
        for cls in plugin_class.__mro__:
            if cls.__name__ == "BasePlugin" and "plugins.base" in cls.__module__:
                is_base_plugin_subclass = True
                break

        # 方法2：如果方法1失败，尝试使用当前导入的BasePlugin
        if not is_base_plugin_subclass:
            try:
                is_base_plugin_subclass = issubclass(plugin_class, BasePlugin)
            except Exception:
                pass

        if not is_base_plugin_subclass:
            raise PluginRegistrationError(
                f"{plugin_class} is not a valid BasePlugin subclass"
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
                plugin_name = name_override or metadata.name

                if plugin_name in self._plugins:
                    # 如果是因别名冲突，只记录警告而不是抛出异常
                    if name_override and metadata.name in self._plugins:
                        self._logger.warning(
                            f"Plugin '{plugin_name}' (alias for '{metadata.name}') "
                            f"conflicts with an existing plugin. Skipping registration."
                        )
                        return metadata.name # 返回原始名称
                    
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

                # 发布插件注册事件（如果事件总线可用）
                if self._event_bus:
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

    def register_plugins_from_config(self, plugins_config: Dict[str, Any]) -> None:
        """
        从配置字典中注册插件

        Args:
            plugins_config: 插件配置字典，格式为
                            { "plugin_name": { "class": "path.to.Class", "config": {} } }
        """
        for plugin_name, plugin_info in plugins_config.items():
            class_path = plugin_info.get("class")
            if not class_path:
                self._logger.warning(f"Plugin '{plugin_name}' in config is missing 'class' path.")
                continue

            plugin_class = self._import_plugin_class(class_path)
            if not plugin_class:
                self._logger.warning(f"Failed to import plugin class for '{plugin_name}' from '{class_path}'.")
                continue
            
            # 使用插件自己的元数据名称，而不是配置中的键
            metadata_name = plugin_class.METADATA.name
            if metadata_name in self._plugins:
                self._logger.debug(f"Plugin '{metadata_name}' is already registered. Skipping.")
                continue

            plugin_specific_config = plugin_info.get("config", {})
            
            try:
                self.register_plugin(
                    plugin_class, 
                    plugin_specific_config,
                    name_override=plugin_name  # 使用配置中的键作为名称
                )
                self._logger.info(f"Registered plugin '{plugin_name}' from config.")
            except PluginRegistrationError as e:
                self._logger.error(f"Failed to register plugin '{plugin_name}' from config: {e}")


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

            # 发布插件取消注册事件（如果事件总线可用）
            if self._event_bus:
                self._event_bus.publish(
                    "plugin.unregistered",
                    data={"plugin_name": plugin_name},
                    source="plugin_manager",
                )

            return True

    def load_plugin(self, plugin_name: str, config: Optional[Any] = None) -> BasePlugin:
        """
        加载插件

        Args:
            plugin_name: 插件名称
            config: 插件配置，如果为None则使用注册时的配置或创建默认配置

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
                # E9修复：使用统一配置管理器替换丑陋的配置验证代码
                plugin_config = self._config_manager.create_validated_config(
                    registry.plugin_class, config or registry.config
                )

                self._logger.info(f"插件 {plugin_name} 配置验证成功")

                # 创建插件实例
                instance = registry.plugin_class(registry.metadata, plugin_config)

                # 如果有事件总线，注入到插件中
                if self._event_bus and hasattr(instance, "set_event_bus"):
                    instance.set_event_bus(self._event_bus)

                # 初始化插件
                instance.initialize()

                # 更新注册信息
                registry.instance = instance
                registry.config = plugin_config
                self._stats["loaded"] += 1

                self._logger.info(f"Loaded plugin: {plugin_name}")

                # 发布插件加载事件（如果事件总线可用）
                if self._event_bus:
                    self._event_bus.publish(
                        "plugin.loaded",
                        data={"plugin_name": plugin_name, "instance": instance},
                        source="plugin_manager",
                    )

                return instance

            except Exception as e:
                self._stats["failed"] += 1
                self._logger.error(f"Failed to load plugin {plugin_name}: {e}")
                raise PluginLoadError(
                    f"Failed to load plugin {plugin_name}: {e}"
                ) from e

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

                # 发布插件卸载事件（如果事件总线可用）
                if self._event_bus:
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

            # 发布插件重载事件（如果事件总线可用）
            if self._event_bus:
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

                # 发布插件启动事件（如果事件总线可用）
                if self._event_bus:
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

                    # 发布插件停止事件（如果事件总线可用）
                    if self._event_bus:
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
                # 插件已经加载，但如果需要启动且尚未启动，则启动它
                if start and registry.instance.state != PluginState.STARTED:
                    try:
                        self.start_plugin(plugin_name)
                        results[plugin_name] = True
                    except Exception as e:
                        self._logger.error(f"Failed to start plugin {plugin_name}: {e}")
                        results[plugin_name] = False
                else:
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
                "event_bus_stats": self._event_bus.get_stats()
                if self._event_bus
                else None,
            }

    def shutdown(self) -> None:
        """关闭插件管理器"""
        self._logger.info("Shutting down plugin manager")

        # 卸载所有插件
        self.unload_all_plugins()

        # 关闭事件总线（如果存在）
        if self._event_bus:
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

    def _discover_plugins_in_module(self, module: Any) -> List[str]:
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
        if not self._event_bus:
            return

        # 插件状态变更事件处理
        self._event_bus.subscribe("plugin.loaded", self._on_plugin_loaded)
        self._event_bus.subscribe("plugin.started", self._on_plugin_started)
        self._event_bus.subscribe("plugin.stopped", self._on_plugin_stopped)
        self._event_bus.subscribe("plugin.unloaded", self._on_plugin_unloaded)

    def _on_plugin_loaded(self, event: CloudEvent) -> None:
        """处理插件加载事件"""
        if event.data:
            plugin_name = event.data["plugin_name"]
            self._logger.debug(f"Plugin loaded event: {plugin_name}")

    def _on_plugin_started(self, event: CloudEvent) -> None:
        """处理插件启动事件"""
        if event.data:
            plugin_name = event.data["plugin_name"]
            self._logger.debug(f"Plugin started event: {plugin_name}")

    def _on_plugin_stopped(self, event: CloudEvent) -> None:
        """处理插件停止事件"""
        if event.data:
            plugin_name = event.data["plugin_name"]
            self._logger.debug(f"Plugin stopped event: {plugin_name}")

    def _on_plugin_unloaded(self, event: CloudEvent) -> None:
        """处理插件卸载事件"""
        if event.data:
            plugin_name = event.data["plugin_name"]
            self._logger.debug(f"Plugin unloaded event: {plugin_name}")

    def __enter__(self) -> "PluginManager":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口"""
        _ = exc_type, exc_val, exc_tb  # 避免未使用参数警告
        self.shutdown()

    def _register_core_plugins(self) -> None:
        """
        E4修复：显式注册核心插件

        明确指定需要注册的核心插件，符合v5.0显式注册原则
        """
        try:
            self._logger.info("Starting explicit registration of core plugins...")

            # 定义核心插件映射：插件名 -> 模块路径
            core_plugins = {
                "mock_data_plugin": (
                    "simtradelab.plugins.data.mock_data_plugin.MockDataPlugin"
                ),
                # 可以根据需要添加更多核心插件
            }

            registered_count = 0
            for plugin_name, module_path in core_plugins.items():
                try:
                    plugin_class = self._import_plugin_class(module_path)
                    if plugin_class:
                        # 获取默认配置
                        default_config = getattr(plugin_class, "DEFAULT_CONFIG", {})
                        config = BasePluginConfig(**default_config)

                        # 显式注册插件
                        registered_name = self.register_plugin(plugin_class, config)
                        self._logger.info(
                            f"Explicitly registered core plugin: {registered_name}"
                        )

                        # 立即加载插件实例以确保可用性
                        try:
                            self.load_plugin(registered_name)
                            self._logger.info(
                                f"Loaded core plugin instance: {registered_name}"
                            )
                        except Exception as load_error:
                            self._logger.warning(
                                f"Failed to load core plugin {registered_name}: "
                                f"{load_error}"
                            )

                        registered_count += 1

                except Exception as e:
                    self._logger.warning(
                        f"Failed to register core plugin {plugin_name}: {e}"
                    )

            self._logger.info(
                f"Core plugin registration completed. "
                f"Registered {registered_count} plugins."
            )

        except Exception as e:
            self._logger.error(f"Failed to register core plugins: {e}")

    def _import_plugin_class(self, module_path: str) -> Optional[Type[BasePlugin]]:
        """
        导入插件类

        Args:
            module_path: 模块路径，格式为 "module.path.ClassName"

        Returns:
            插件类，如果导入失败则返回None
        """
        try:
            # 分离模块路径和类名
            parts = module_path.split(".")
            class_name = parts[-1]
            module_name = ".".join(parts[:-1])

            # 动态导入模块
            module = importlib.import_module(module_name)

            # 获取插件类
            plugin_class = getattr(module, class_name)

            # E4修复：从插件类的MRO中查找BasePlugin，确保使用相同的BasePlugin引用
            base_plugin_class = None
            for cls in plugin_class.__mro__:
                if cls.__name__ == "BasePlugin" and "plugins.base" in cls.__module__:
                    base_plugin_class = cls
                    break

            if base_plugin_class is None:
                self._logger.warning(f"{plugin_class} does not inherit from BasePlugin")
                return None

            # 验证是否为BasePlugin子类
            if issubclass(plugin_class, base_plugin_class):
                return plugin_class  # type: ignore[no-any-return]
            else:
                self._logger.warning(f"{plugin_class} is not a BasePlugin subclass")
                return None

        except ImportError as e:
            self._logger.warning(f"Failed to import module {module_name}: {e}")
            return None
        except AttributeError as e:
            self._logger.warning(
                f"Class {class_name} not found in module {module_name}: {e}"
            )
            return None
        except Exception as e:
            self._logger.error(f"Unexpected error importing {module_path}: {e}")
            return None

    def _auto_discover_builtin_plugins(self) -> None:
        """
        自动发现和注册内置插件（开发模式）

        E4修复：保留自动发现作为可选功能，默认禁用
        """
        try:
            # 扫描插件目录，自动发现并注册标记为AUTO_REGISTER的插件
            self._logger.info("Starting auto-discovery of builtin plugins...")
            self._scan_builtin_plugin_directories()

            # 显示已注册的插件
            registered_plugins = list(self._plugins.keys())
            self._logger.info(
                f"Auto-discovery completed. Registered plugins: {registered_plugins}"
            )
        except Exception as e:
            self._logger.error(f"Failed to auto-discover builtin plugins: {e}")
            import traceback

            self._logger.error(f"Traceback: {traceback.format_exc()}")

    def _scan_builtin_plugin_directories(self) -> None:
        """扫描内置插件目录"""
        try:
            # 获取插件根目录
            current_file = Path(__file__)
            plugins_dir = current_file.parent.parent / "plugins"

            if plugins_dir.exists():
                self._logger.debug(f"Scanning plugin directory: {plugins_dir}")
                self._scan_plugin_directory(plugins_dir)
            else:
                self._logger.warning(f"Plugin directory not found: {plugins_dir}")

        except Exception as e:
            self._logger.error(f"Failed to scan plugin directories: {e}")

    def _scan_plugin_directory(self, plugin_dir: Path) -> None:
        """递归扫描插件目录"""
        try:
            # 扫描所有Python文件，查找插件类
            for py_file in plugin_dir.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                # 尝试从文件中发现插件
                self._discover_plugins_in_file(py_file)

        except Exception as e:
            self._logger.error(f"Failed to scan plugin directory {plugin_dir}: {e}")

    def _discover_plugins_in_file(self, py_file: Path) -> None:
        """从Python文件中发现插件"""
        try:
            # 构建模块路径
            relative_path = py_file.relative_to(Path(__file__).parent.parent)
            module_path = str(relative_path.with_suffix("")).replace("/", ".")

            # 动态导入模块
            import importlib

            module = importlib.import_module(f"simtradelab.{module_path}")

            # 查找插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "METADATA")
                    and attr_name.endswith("Plugin")
                ):
                    self._logger.debug(
                        f"Discovered plugin class: {attr_name} in {module_path}"
                    )

                    # 检查是否标记为自动注册
                    if hasattr(attr, "AUTO_REGISTER") and attr.AUTO_REGISTER:
                        self._auto_register_plugin(attr)

        except Exception as e:
            self._logger.debug(f"Could not discover plugins in {py_file}: {e}")

    def _auto_register_plugin(self, plugin_class: type) -> None:
        """自动注册标记为AUTO_REGISTER的插件"""
        try:
            # 获取插件的默认配置
            default_config = getattr(plugin_class, "DEFAULT_CONFIG", {})

            # 创建插件配置
            config = BasePluginConfig(**default_config)

            # 注册、加载并启动插件
            plugin_name = self.register_plugin(plugin_class, config)
            self._logger.info(
                f"Auto-registering plugin: {plugin_class.__name__} as {plugin_name}"
            )

            self.load_plugin(plugin_name, config)
            self._logger.info(f"Loaded plugin: {plugin_name}")

            self.start_plugin(plugin_name)
            self._logger.info(f"Started plugin: {plugin_name}")

        except Exception as e:
            self._logger.error(
                f"Failed to auto-register plugin {plugin_class.__name__}: {e}"
            )
            import traceback

            self._logger.error(f"Traceback: {traceback.format_exc()}")
