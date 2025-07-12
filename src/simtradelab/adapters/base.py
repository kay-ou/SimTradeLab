# -*- coding: utf-8 -*-
"""
SimTradeLab 适配器基类

定义所有平台适配器的通用接口和基础功能。
适配器属于平台适配层，不是插件，直接与核心框架集成。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.event_bus import EventBus


class AdapterError(Exception):
    """适配器基础异常"""

    pass


class AdapterInitializationError(AdapterError):
    """适配器初始化异常"""

    pass


class AdapterConfig:
    """适配器配置类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化适配器配置

        Args:
            config: 配置字典
        """
        self.config = config or {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value

    def update(self, other_config: Dict[str, Any]) -> None:
        """更新配置"""
        self.config.update(other_config)


class BaseAdapter(ABC):
    """
    平台适配器基类

    所有平台适配器都应继承此类。适配器负责将不同平台的API
    统一适配到SimTradeLab的标准接口。

    适配器不是插件，而是核心框架的一部分，位于平台适配层。
    """

    def __init__(self, name: str, config: Optional[AdapterConfig] = None):
        """
        初始化适配器

        Args:
            name: 适配器名称
            config: 适配器配置
        """
        self.name = name
        self.config = config or AdapterConfig()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 事件总线引用 - 由外部注入
        self._event_bus: Optional[EventBus] = None

        # 插件管理器引用 - 由外部注入
        self._plugin_manager: Optional[Any] = None

        # 初始化状态
        self._initialized = False
        self._started = False

    def set_event_bus(self, event_bus: EventBus) -> None:
        """
        设置事件总线引用

        Args:
            event_bus: 事件总线实例
        """
        self._event_bus = event_bus
        self._logger.debug(f"Event bus set for adapter {self.name}")

    def set_plugin_manager(self, plugin_manager: Any) -> None:
        """
        设置插件管理器引用

        Args:
            plugin_manager: 插件管理器实例
        """
        self._plugin_manager = plugin_manager
        self._logger.debug(f"Plugin manager set for adapter {self.name}")

    @abstractmethod
    def initialize(self) -> None:
        """
        初始化适配器

        子类必须实现此方法来完成适配器的初始化工作。
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        启动适配器

        子类必须实现此方法来启动适配器服务。
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        停止适配器

        子类必须实现此方法来停止适配器服务并清理资源。
        """
        pass

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized

    def is_started(self) -> bool:
        """检查是否已启动"""
        return self._started

    def get_status(self) -> Dict[str, Any]:
        """
        获取适配器状态信息

        Returns:
            状态信息字典
        """
        return {
            "name": self.name,
            "initialized": self._initialized,
            "started": self._started,
            "config": self.config.config,
        }

    def _on_initialize(self) -> None:
        """
        内部初始化处理

        调用子类的initialize方法并更新状态
        """
        if self._initialized:
            self._logger.warning(f"Adapter {self.name} already initialized")
            return

        try:
            self._logger.info(f"Initializing adapter {self.name}")
            self.initialize()
            self._initialized = True
            self._logger.info(f"Adapter {self.name} initialized successfully")

            # 发布初始化事件
            if self._event_bus:
                self._event_bus.publish(
                    "adapter.initialized",
                    data={"adapter_name": self.name},
                    source=f"adapter.{self.name}",
                )
        except Exception as e:
            self._logger.error(f"Failed to initialize adapter {self.name}: {e}")
            raise AdapterInitializationError(f"Adapter initialization failed: {e}")

    def _on_start(self) -> None:
        """
        内部启动处理

        调用子类的start方法并更新状态
        """
        if not self._initialized:
            raise AdapterError("Cannot start adapter before initialization")

        if self._started:
            self._logger.warning(f"Adapter {self.name} already started")
            return

        try:
            self._logger.info(f"Starting adapter {self.name}")
            self.start()
            self._started = True
            self._logger.info(f"Adapter {self.name} started successfully")

            # 发布启动事件
            if self._event_bus:
                self._event_bus.publish(
                    "adapter.started",
                    data={"adapter_name": self.name},
                    source=f"adapter.{self.name}",
                )
        except Exception as e:
            self._logger.error(f"Failed to start adapter {self.name}: {e}")
            raise AdapterError(f"Adapter start failed: {e}")

    def _on_stop(self) -> None:
        """
        内部停止处理

        调用子类的stop方法并更新状态
        """
        if not self._started:
            self._logger.warning(f"Adapter {self.name} not started")
            return

        try:
            self._logger.info(f"Stopping adapter {self.name}")
            self.stop()
            self._started = False
            self._logger.info(f"Adapter {self.name} stopped successfully")

            # 发布停止事件
            if self._event_bus:
                self._event_bus.publish(
                    "adapter.stopped",
                    data={"adapter_name": self.name},
                    source=f"adapter.{self.name}",
                )
        except Exception as e:
            self._logger.error(f"Failed to stop adapter {self.name}: {e}")
            raise AdapterError(f"Adapter stop failed: {e}")

    def _on_shutdown(self) -> None:
        """
        关闭适配器并清理所有资源
        """
        if self._started:
            self._on_stop()

        # 清理引用
        self._event_bus = None
        self._plugin_manager = None
        self._initialized = False

        self._logger.info(f"Adapter {self.name} shutdown completed")
