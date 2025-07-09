# -*- coding: utf-8 -*-
"""
SimTradeLab 插件基类
提供插件接口标准、生命周期钩子、配置管理
"""

import abc
import asyncio
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from ..exceptions import SimTradeLabError


class PluginError(SimTradeLabError):
    """插件相关异常"""
    pass


class PluginStateError(PluginError):
    """插件状态异常"""
    pass


class PluginConfigError(PluginError):
    """插件配置异常"""
    pass


class PluginState(Enum):
    """插件状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    STARTED = "started"
    STOPPED = "stopped"
    ERROR = "error"
    PAUSED = "paused"


class PluginMode(Enum):
    """插件运行模式基础枚举"""
    DEFAULT = "default"
    DEBUG = "debug"
    PRODUCTION = "production"


class ModeAwarePlugin(ABC):
    """模式感知插件接口"""
    
    @abstractmethod
    def get_supported_modes(self) -> Set[Enum]:
        """获取插件支持的运行模式"""
        pass
    
    @abstractmethod
    def set_mode(self, mode: Enum) -> None:
        """设置插件运行模式"""
        pass
    
    @abstractmethod
    def get_current_mode(self) -> Optional[Enum]:
        """获取当前运行模式"""
        pass
    
    @abstractmethod
    def is_mode_available(self, mode: Enum) -> bool:
        """检查指定模式是否可用"""
        pass


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    priority: int = 100  # 插件加载优先级，数值越小优先级越高


@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    auto_start: bool = True
    restart_on_error: bool = False
    max_retries: int = 3
    timeout: Optional[float] = None


class BasePlugin(abc.ABC):
    """
    插件基类
    
    所有插件都必须继承此类并实现相应的抽象方法。
    提供插件生命周期管理、配置管理、事件处理等基础功能。
    同时实现ModeAwarePlugin接口，支持运行模式管理。
    """
    
    METADATA: PluginMetadata = PluginMetadata(name="BasePlugin", version="0.0.0")
    
    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        """
        初始化插件
        
        Args:
            metadata: 插件元数据
            config: 插件配置，如果为None则使用默认配置
        """
        self._metadata = metadata
        self._config = config or PluginConfig()
        self._state = PluginState.UNINITIALIZED
        self._logger = logging.getLogger(f"plugin.{metadata.name}")
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        self._start_time: Optional[float] = None
        self._error_count = 0
        self._last_error: Optional[Exception] = None
        
        # 插件实例变量
        self._context: Dict[str, Any] = {}
        self._resources: List[Any] = []
        
        # 模式相关属性
        self._current_mode: Optional[Enum] = None
        self._supported_modes: Set[Enum] = {PluginMode.DEFAULT}
    
    @property
    def metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return self._metadata
    
    @property
    def config(self) -> PluginConfig:
        """获取插件配置"""
        return self._config
    
    @property
    def state(self) -> PluginState:
        """获取插件状态"""
        return self._state
    
    @property
    def logger(self) -> logging.Logger:
        """获取插件日志记录器"""
        return self._logger
    
    @property
    def is_running(self) -> bool:
        """检查插件是否正在运行"""
        return self._state == PluginState.STARTED
    
    @property
    def uptime(self) -> Optional[float]:
        """获取插件运行时间（秒）"""
        if self._start_time is None:
            return None
        return time.time() - self._start_time
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取插件状态信息
        
        Returns:
            包含插件状态、错误信息等的字典
        """
        return {
            'name': self._metadata.name,
            'version': self._metadata.version,
            'state': self._state.value,
            'enabled': self._config.enabled,
            'uptime': self.uptime,
            'error_count': self._error_count,
            'last_error': str(self._last_error) if self._last_error else None,
            'start_time': self._start_time
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        更新插件配置
        
        Args:
            new_config: 新的配置字典
            
        Raises:
            PluginConfigError: 配置无效时抛出
        """
        try:
            # 验证配置
            self._validate_config(new_config)
            
            # 更新配置
            with self._lock:
                old_config = self._config.config.copy()
                self._config.config.update(new_config)
                
                try:
                    # 调用配置变更处理
                    self._on_config_changed(old_config, self._config.config)
                    self._logger.info(f"Configuration updated for plugin {self._metadata.name}")
                except Exception as e:
                    # 如果配置变更失败，回滚配置
                    self._config.config = old_config
                    raise PluginConfigError(f"Failed to apply config changes: {e}")
                    
        except Exception as e:
            self._logger.error(f"Failed to update config: {e}")
            raise PluginConfigError(f"Invalid configuration: {e}")
    
    def initialize(self) -> None:
        """
        初始化插件
        
        Raises:
            PluginStateError: 插件状态不正确时抛出
            PluginError: 初始化失败时抛出
        """
        with self._lock:
            if self._state != PluginState.UNINITIALIZED:
                raise PluginStateError(f"Plugin {self._metadata.name} is already initialized")
            
            try:
                self._logger.info(f"Initializing plugin {self._metadata.name}")
                
                # 验证配置
                self._validate_config(self._config.config)
                
                # 调用子类初始化方法
                self._on_initialize()
                
                # 更新状态
                self._state = PluginState.INITIALIZED
                self._logger.info(f"Plugin {self._metadata.name} initialized successfully")
                
            except Exception as e:
                self._state = PluginState.ERROR
                self._last_error = e
                self._error_count += 1
                self._logger.error(f"Failed to initialize plugin {self._metadata.name}: {e}")
                raise PluginError(f"Plugin initialization failed: {e}")
    
    def start(self) -> None:
        """
        启动插件
        
        Raises:
            PluginStateError: 插件状态不正确时抛出
            PluginError: 启动失败时抛出
        """
        with self._lock:
            if self._state not in [PluginState.INITIALIZED, PluginState.STOPPED]:
                raise PluginStateError(f"Plugin {self._metadata.name} cannot be started from state {self._state}")
            
            if not self._config.enabled:
                self._logger.warning(f"Plugin {self._metadata.name} is disabled, skipping start")
                return
            
            try:
                self._logger.info(f"Starting plugin {self._metadata.name}")
                
                # 调用子类启动方法
                self._on_start()
                
                # 更新状态和时间
                self._state = PluginState.STARTED
                self._start_time = time.time()
                self._logger.info(f"Plugin {self._metadata.name} started successfully")
                
            except Exception as e:
                self._state = PluginState.ERROR
                self._last_error = e
                self._error_count += 1
                self._logger.error(f"Failed to start plugin {self._metadata.name}: {e}")
                raise PluginError(f"Plugin start failed: {e}")
    
    def stop(self) -> None:
        """
        停止插件
        
        Raises:
            PluginError: 停止失败时抛出
        """
        with self._lock:
            if self._state not in [PluginState.STARTED, PluginState.PAUSED]:
                self._logger.warning(f"Plugin {self._metadata.name} is not running, state: {self._state}")
                return
            
            try:
                self._logger.info(f"Stopping plugin {self._metadata.name}")
                
                # 调用子类停止方法
                self._on_stop()
                
                # 清理资源
                self._cleanup_resources()
                
                # 更新状态
                self._state = PluginState.STOPPED
                self._start_time = None
                self._logger.info(f"Plugin {self._metadata.name} stopped successfully")
                
            except Exception as e:
                self._state = PluginState.ERROR
                self._last_error = e
                self._error_count += 1
                self._logger.error(f"Failed to stop plugin {self._metadata.name}: {e}")
                raise PluginError(f"Plugin stop failed: {e}")
    
    def pause(self) -> None:
        """
        暂停插件
        
        Raises:
            PluginStateError: 插件状态不正确时抛出
            PluginError: 暂停失败时抛出
        """
        with self._lock:
            if self._state != PluginState.STARTED:
                raise PluginStateError(f"Plugin {self._metadata.name} is not running")
            
            try:
                self._logger.info(f"Pausing plugin {self._metadata.name}")
                
                # 调用子类暂停方法
                self._on_pause()
                
                # 更新状态
                self._state = PluginState.PAUSED
                self._logger.info(f"Plugin {self._metadata.name} paused successfully")
                
            except Exception as e:
                self._state = PluginState.ERROR
                self._last_error = e
                self._error_count += 1
                self._logger.error(f"Failed to pause plugin {self._metadata.name}: {e}")
                raise PluginError(f"Plugin pause failed: {e}")
    
    def resume(self) -> None:
        """
        恢复插件
        
        Raises:
            PluginStateError: 插件状态不正确时抛出
            PluginError: 恢复失败时抛出
        """
        with self._lock:
            if self._state != PluginState.PAUSED:
                raise PluginStateError(f"Plugin {self._metadata.name} is not paused")
            
            try:
                self._logger.info(f"Resuming plugin {self._metadata.name}")
                
                # 调用子类恢复方法
                self._on_resume()
                
                # 更新状态
                self._state = PluginState.STARTED
                self._logger.info(f"Plugin {self._metadata.name} resumed successfully")
                
            except Exception as e:
                self._state = PluginState.ERROR
                self._last_error = e
                self._error_count += 1
                self._logger.error(f"Failed to resume plugin {self._metadata.name}: {e}")
                raise PluginError(f"Plugin resume failed: {e}")
    
    def shutdown(self) -> None:
        """
        关闭插件（完全清理）
        
        Raises:
            PluginError: 关闭失败时抛出
        """
        try:
            self._logger.info(f"Shutting down plugin {self._metadata.name}")
            
            # 先停止插件
            if self._state in [PluginState.STARTED, PluginState.PAUSED]:
                self.stop()
            
            # 调用子类关闭方法
            self._on_shutdown()
            
            # 清理所有资源
            self._cleanup_resources()
            
            # 重置状态
            self._state = PluginState.UNINITIALIZED
            self._start_time = None
            self._context.clear()
            
            self._logger.info(f"Plugin {self._metadata.name} shutdown completed")
            
        except Exception as e:
            self._state = PluginState.ERROR
            self._last_error = e
            self._error_count += 1
            self._logger.error(f"Failed to shutdown plugin {self._metadata.name}: {e}")
            raise PluginError(f"Plugin shutdown failed: {e}")
    
    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        self._logger.debug(f"Registered event handler for {event_type}")
    
    def unregister_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        取消注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self._event_handlers:
            if handler in self._event_handlers[event_type]:
                self._event_handlers[event_type].remove(handler)
                self._logger.debug(f"Unregistered event handler for {event_type}")
    
    async def handle_event(self, event_type: str, data: Any = None) -> List[Any]:
        """
        处理事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            事件处理结果列表
        """
        results = []
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(data)
                    else:
                        result = handler(data)
                    results.append(result)
                except Exception as e:
                    self._logger.error(f"Event handler failed for {event_type}: {e}")
                    results.append(None)
        return results
    
    def add_resource(self, resource: Any) -> None:
        """
        添加需要清理的资源
        
        Args:
            resource: 资源对象（需要有close或cleanup方法）
        """
        self._resources.append(resource)
    
    def set_context(self, key: str, value: Any) -> None:
        """
        设置上下文变量
        
        Args:
            key: 键
            value: 值
        """
        self._context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        获取上下文变量
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            上下文值
        """
        return self._context.get(key, default)
    
    def _cleanup_resources(self) -> None:
        """清理资源"""
        for resource in self._resources[:]:
            try:
                if hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
                elif hasattr(resource, '__del__'):
                    del resource
                self._resources.remove(resource)
            except Exception as e:
                self._logger.warning(f"Failed to cleanup resource {resource}: {e}")
    
    # 抽象方法 - 子类必须实现
    
    @abc.abstractmethod
    def _on_initialize(self) -> None:
        """
        插件初始化时调用
        子类必须实现此方法来执行特定的初始化逻辑
        """
        pass
    
    @abc.abstractmethod
    def _on_start(self) -> None:
        """
        插件启动时调用
        子类必须实现此方法来执行特定的启动逻辑
        """
        pass
    
    @abc.abstractmethod
    def _on_stop(self) -> None:
        """
        插件停止时调用
        子类必须实现此方法来执行特定的停止逻辑
        """
        pass
    
    # 可选的钩子方法 - 子类可以选择性重写
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        验证插件配置
        子类可以重写此方法来实现自定义配置验证
        
        Args:
            config: 要验证的配置字典
            
        Raises:
            PluginConfigError: 配置无效时抛出
        """
        pass
    
    def _on_config_changed(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """
        配置变更时调用
        子类可以重写此方法来处理配置变更
        
        Args:
            old_config: 旧配置
            new_config: 新配置
        """
        pass
    
    def _on_pause(self) -> None:
        """
        插件暂停时调用
        子类可以重写此方法来实现暂停逻辑
        """
        pass
    
    def _on_resume(self) -> None:
        """
        插件恢复时调用
        子类可以重写此方法来实现恢复逻辑
        """
        pass
    
    def _on_shutdown(self) -> None:
        """
        插件关闭时调用
        子类可以重写此方法来执行清理逻辑
        """
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """
        获取插件的当前状态，用于持久化或热重载。
        子类应重写此方法以返回需要保存的状态。
        
        Returns:
            一个包含插件状态的字典。
        """
        return {}

    def set_state(self, state: Dict[str, Any]) -> None:
        """
        从给定的状态恢复插件。
        子类应重写此方法以从状态字典中恢复其内部状态。
        
        Args:
            state: 包含插件状态的字典。
        """
        pass
    
    # =========================================
    # ModeAwarePlugin接口实现
    # =========================================
    
    def get_supported_modes(self) -> Set[Enum]:
        """获取插件支持的运行模式"""
        return self._supported_modes.copy()
    
    def set_mode(self, mode: Enum) -> None:
        """设置插件运行模式"""
        if not self.is_mode_available(mode):
            supported_modes = [m.value for m in self._supported_modes]
            raise PluginConfigError(
                f"Mode '{mode.value}' is not supported by plugin '{self._metadata.name}'. "
                f"Supported modes: {', '.join(supported_modes)}"
            )
        
        old_mode = self._current_mode
        self._current_mode = mode
        
        # 调用模式变更钩子
        self._on_mode_changed(old_mode, mode)
        
        self._logger.info(f"Plugin mode changed from {old_mode} to {mode}")
    
    def get_current_mode(self) -> Optional[Enum]:
        """获取当前运行模式"""
        return self._current_mode
    
    def is_mode_available(self, mode: Enum) -> bool:
        """检查指定模式是否可用"""
        return mode in self._supported_modes
    
    def _set_supported_modes(self, modes: Set[Enum]) -> None:
        """设置支持的模式（供子类使用）"""
        self._supported_modes = modes.copy()
        
        # 如果当前模式不在支持列表中，重置为None
        if self._current_mode and self._current_mode not in self._supported_modes:
            old_mode = self._current_mode
            self._current_mode = None
            self._on_mode_changed(old_mode, None)
    
    def _on_mode_changed(self, old_mode: Optional[Enum], new_mode: Optional[Enum]) -> None:
        """
        模式变更时调用的钩子方法
        子类可以重写此方法来处理模式变更
        
        Args:
            old_mode: 旧模式
            new_mode: 新模式
        """
        pass