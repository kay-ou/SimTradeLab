# -*- coding: utf-8 -*-
"""
数据源管理器

管理多个数据源插件，提供统一的数据访问接口
支持数据源优先级、故障切换、健康检查等功能
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union

import pandas as pd

from ..base import PluginError
from .base_data_source import BaseDataSourcePlugin, DataFrequency, MarketType


@dataclass
class DataSourceConfig:
    """数据源配置"""

    priority: int = 100  # 优先级，数值越小优先级越高
    enabled: bool = True
    timeout: float = 30.0  # 请求超时时间
    retry_count: int = 3  # 重试次数
    health_check_interval: int = 300  # 健康检查间隔（秒）
    cache_enabled: bool = True
    cache_ttl: int = 60  # 缓存生存时间（秒）


@dataclass
class DataSourceStatus:
    """数据源状态"""

    name: str
    is_available: bool = True
    last_check_time: float = field(default_factory=time.time)
    error_count: int = 0
    last_error: Optional[str] = None
    response_time: float = 0.0  # 平均响应时间（毫秒）


class DataSourceManager:
    """
    数据源管理器

    负责管理多个数据源插件，提供统一的数据访问接口
    支持优先级选择、故障切换、健康检查、数据缓存等功能
    """

    def __init__(self, plugin_manager: Optional[Any] = None):
        self._plugin_manager = plugin_manager
        self._data_sources: Dict[str, BaseDataSourcePlugin] = {}
        self._data_source_configs: Dict[str, DataSourceConfig] = {}
        self._data_source_status: Dict[str, DataSourceStatus] = {}
        self._priority_list: List[str] = []  # 按优先级排序的数据源名称列表

        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

        # 数据缓存
        self._cache_enabled = True
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}

        # 健康检查
        self._health_check_enabled = True
        self._last_health_check = 0.0

    def initialize(self) -> None:
        """初始化数据源管理器"""
        self._logger.info("Initializing DataSourceManager")

        # 自动发现数据源插件
        self._discover_data_sources()

        # 执行初始健康检查
        self._perform_health_check()

        self._logger.info(
            f"DataSourceManager initialized with {len(self._data_sources)} data sources"
        )

    def shutdown(self) -> None:
        """关闭数据源管理器"""
        self._logger.info("Shutting down DataSourceManager")

        with self._lock:
            # 清理缓存
            self._cache.clear()
            self._cache_timestamps.clear()

            # 清理数据源引用
            self._data_sources.clear()
            self._data_source_configs.clear()
            self._data_source_status.clear()
            self._priority_list.clear()

    # ================================
    # 数据源插件管理
    # ================================

    def _discover_data_sources(self) -> None:
        """自动发现数据源插件"""
        if not self._plugin_manager:
            self._logger.warning("No plugin manager available for auto-discovery")
            return

        try:
            all_plugins = self._plugin_manager.get_all_plugins()
            for plugin_name, plugin_instance in all_plugins.items():
                if isinstance(plugin_instance, BaseDataSourcePlugin):
                    self.register_data_source(plugin_name, plugin_instance)
                    self._logger.info(f"Auto-discovered data source: {plugin_name}")
        except Exception as e:
            self._logger.error(f"Error during data source discovery: {e}")

    def register_data_source(
        self,
        name: str,
        data_source: BaseDataSourcePlugin,
        config: Optional[DataSourceConfig] = None,
    ) -> None:
        """
        注册数据源插件

        Args:
            name: 数据源名称
            data_source: 数据源插件实例
            config: 数据源配置
        """
        with self._lock:
            if not isinstance(data_source, BaseDataSourcePlugin):
                raise PluginError(
                    f"Data source {name} must be instance of BaseDataSourcePlugin"
                )

            self._data_sources[name] = data_source
            self._data_source_configs[name] = config or DataSourceConfig()
            self._data_source_status[name] = DataSourceStatus(name=name)

            # 重新排序优先级列表
            self._update_priority_list()

            self._logger.info(f"Registered data source: {name}")

    def unregister_data_source(self, name: str) -> None:
        """注销数据源插件"""
        with self._lock:
            if name in self._data_sources:
                del self._data_sources[name]
                del self._data_source_configs[name]
                del self._data_source_status[name]

                if name in self._priority_list:
                    self._priority_list.remove(name)

                # 清理相关缓存
                cache_keys_to_remove = [
                    k for k in self._cache.keys() if k.startswith(f"{name}:")
                ]
                for key in cache_keys_to_remove:
                    del self._cache[key]
                    del self._cache_timestamps[key]

                self._logger.info(f"Unregistered data source: {name}")

    def _update_priority_list(self) -> None:
        """更新优先级列表"""
        self._priority_list = sorted(
            self._data_source_configs.keys(),
            key=lambda name: self._data_source_configs[name].priority,
        )

    def get_available_data_sources(self) -> List[str]:
        """获取可用的数据源列表"""
        with self._lock:
            return [
                name
                for name, status in self._data_source_status.items()
                if status.is_available and self._data_source_configs[name].enabled
            ]

    def get_data_source_status(
        self, name: Optional[str] = None
    ) -> Union[DataSourceStatus, Dict[str, DataSourceStatus]]:
        """获取数据源状态"""
        with self._lock:
            if name:
                return self._data_source_status.get(name)
            else:
                return self._data_source_status.copy()

    # ================================
    # 数据源选择和健康检查
    # ================================

    def _select_data_source(
        self, required_markets: Optional[Set[MarketType]] = None
    ) -> Optional[str]:
        """
        选择最优的数据源

        Args:
            required_markets: 需要的市场类型

        Returns:
            选中的数据源名称，如果没有可用数据源则返回None
        """
        # 执行健康检查（如果需要）
        if self._should_perform_health_check():
            self._perform_health_check()

        with self._lock:
            for name in self._priority_list:
                config = self._data_source_configs[name]
                status = self._data_source_status[name]
                data_source = self._data_sources[name]

                # 检查是否启用且可用
                if not config.enabled or not status.is_available:
                    continue

                # 检查市场支持
                if required_markets:
                    supported_markets = data_source.get_supported_markets()
                    if not required_markets.issubset(supported_markets):
                        continue

                return name

        return None

    def _should_perform_health_check(self) -> bool:
        """判断是否需要执行健康检查"""
        if not self._health_check_enabled:
            return False

        current_time = time.time()
        min_interval = (
            min(
                config.health_check_interval
                for config in self._data_source_configs.values()
            )
            if self._data_source_configs
            else 300
        )

        return current_time - self._last_health_check > min_interval

    def _perform_health_check(self) -> None:
        """执行健康检查"""
        self._logger.debug("Performing health check on data sources")

        with self._lock:
            for name, data_source in self._data_sources.items():
                try:
                    start_time = time.time()
                    is_available = data_source.is_available()
                    response_time = (time.time() - start_time) * 1000  # 转换为毫秒

                    status = self._data_source_status[name]
                    status.is_available = is_available
                    status.last_check_time = time.time()
                    status.response_time = response_time

                    if is_available:
                        status.error_count = 0
                        status.last_error = None

                except Exception as e:
                    status = self._data_source_status[name]
                    status.is_available = False
                    status.error_count += 1
                    status.last_error = str(e)
                    status.last_check_time = time.time()

                    self._logger.warning(
                        f"Health check failed for data source {name}: {e}"
                    )

        self._last_health_check = time.time()

    # ================================
    # 缓存管理
    # ================================

    def _get_cache_key(
        self, data_source_name: str, method: str, *args, **kwargs
    ) -> str:
        """生成缓存键"""
        # 简单的缓存键生成，实际实现可能需要更复杂的逻辑
        args_str = str(args) + str(sorted(kwargs.items()))
        return f"{data_source_name}:{method}:{hash(args_str)}"

    def _get_from_cache(self, cache_key: str, ttl: int) -> Optional[Any]:
        """从缓存获取数据"""
        if not self._cache_enabled:
            return None

        if cache_key not in self._cache:
            return None

        timestamp = self._cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp > ttl:
            # 缓存过期
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None

        return self._cache[cache_key]

    def _put_to_cache(self, cache_key: str, data: Any) -> None:
        """将数据放入缓存"""
        if not self._cache_enabled:
            return

        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()

    # ================================
    # 统一数据访问接口
    # ================================

    def _execute_with_fallback(
        self,
        method_name: str,
        required_markets: Optional[Set[MarketType]] = None,
        use_cache: bool = True,
        *args,
        **kwargs,
    ) -> Any:
        """
        使用故障切换执行数据源方法

        Args:
            method_name: 要调用的方法名
            required_markets: 需要的市场类型
            use_cache: 是否使用缓存
            *args, **kwargs: 方法参数

        Returns:
            方法执行结果
        """
        attempted_sources = []

        while True:
            # 选择数据源
            data_source_name = self._select_data_source(required_markets)
            if not data_source_name:
                break

            if data_source_name in attempted_sources:
                # 避免无限循环
                break

            attempted_sources.append(data_source_name)

            try:
                data_source = self._data_sources[data_source_name]
                config = self._data_source_configs[data_source_name]

                # 检查缓存
                cache_key = None
                if use_cache and config.cache_enabled:
                    cache_key = self._get_cache_key(
                        data_source_name, method_name, *args, **kwargs
                    )
                    cached_result = self._get_from_cache(cache_key, config.cache_ttl)
                    if cached_result is not None:
                        return cached_result

                # 执行方法
                method = getattr(data_source, method_name)
                result = method(*args, **kwargs)

                # 缓存结果
                if cache_key:
                    self._put_to_cache(cache_key, result)

                return result

            except Exception as e:
                self._logger.warning(
                    f"Data source {data_source_name} failed for {method_name}: {e}"
                )

                # 更新状态
                with self._lock:
                    status = self._data_source_status[data_source_name]
                    status.error_count += 1
                    status.last_error = str(e)

                    # 如果错误次数过多，标记为不可用
                    config = self._data_source_configs[data_source_name]
                    if status.error_count >= config.retry_count:
                        status.is_available = False

                # 继续尝试下一个数据源
                continue

        # 所有数据源都失败了
        raise PluginError(f"All data sources failed for method {method_name}")

    # ================================
    # 具体的数据访问方法
    # ================================

    def get_history_data(
        self,
        security: str,
        count: int = 30,
        frequency: Union[str, DataFrequency] = DataFrequency.DAILY,
        fields: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fq: str = "pre",
        include_now: bool = True,
        fill_gaps: bool = True,
    ) -> pd.DataFrame:
        """获取单个证券的历史数据"""
        return self._execute_with_fallback(
            "get_history_data",
            None,
            True,
            security=security,
            count=count,
            frequency=frequency,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            fq=fq,
            include_now=include_now,
            fill_gaps=fill_gaps,
        )

    def get_multiple_history_data(
        self,
        security_list: List[str],
        count: int = 30,
        frequency: Union[str, DataFrequency] = DataFrequency.DAILY,
        fields: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fq: str = "pre",
        include_now: bool = True,
        fill_gaps: bool = True,
        as_dict: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """获取多个证券的历史数据"""
        return self._execute_with_fallback(
            "get_multiple_history_data",
            None,
            True,
            security_list=security_list,
            count=count,
            frequency=frequency,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            fq=fq,
            include_now=include_now,
            fill_gaps=fill_gaps,
            as_dict=as_dict,
        )

    def get_snapshot(
        self,
        security_list: List[str],
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """获取证券的实时快照数据"""
        return self._execute_with_fallback(
            "get_snapshot",
            None,
            False,  # 实时数据不使用缓存
            security_list=security_list,
            fields=fields,
        )

    def get_current_price(
        self,
        security_list: List[str],
    ) -> Dict[str, float]:
        """获取证券的当前价格"""
        return self._execute_with_fallback(
            "get_current_price",
            None,
            False,  # 实时价格不使用缓存
            security_list=security_list,
        )

    def get_trading_day(
        self,
        date: str,
        offset: int = 0,
        market: Optional[MarketType] = None,
    ) -> str:
        """获取交易日"""
        required_markets = {market} if market else None
        return self._execute_with_fallback(
            "get_trading_day",
            required_markets,
            True,
            date=date,
            offset=offset,
            market=market,
        )

    def get_all_trading_days(
        self,
        market: Optional[MarketType] = None,
    ) -> List[str]:
        """获取所有交易日"""
        required_markets = {market} if market else None
        return self._execute_with_fallback(
            "get_all_trading_days",
            required_markets,
            True,
            market=market,
        )

    def get_trading_days_range(
        self,
        start_date: str,
        end_date: str,
        market: Optional[MarketType] = None,
    ) -> List[str]:
        """获取指定日期范围内的交易日"""
        required_markets = {market} if market else None
        return self._execute_with_fallback(
            "get_trading_days_range",
            required_markets,
            True,
            start_date=start_date,
            end_date=end_date,
            market=market,
        )

    def check_limit_status(
        self,
        security_list: List[str],
        date: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """检查证券的涨跌停状态"""
        return self._execute_with_fallback(
            "check_limit_status",
            None,
            False,  # 涨跌停状态不使用缓存
            security_list=security_list,
            date=date,
        )

    def get_fundamentals(
        self,
        security_list: List[str],
        table: str,
        fields: List[str],
        date: str,
    ) -> pd.DataFrame:
        """获取基本面数据"""
        return self._execute_with_fallback(
            "get_fundamentals",
            None,
            True,
            security_list=security_list,
            table=table,
            fields=fields,
            date=date,
        )

    def get_security_info(
        self,
        security_list: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """获取证券基本信息"""
        return self._execute_with_fallback(
            "get_security_info",
            None,
            True,
            security_list=security_list,
        )

    # ================================
    # 配置管理
    # ================================

    def update_data_source_config(self, name: str, config: DataSourceConfig) -> None:
        """更新数据源配置"""
        with self._lock:
            if name in self._data_source_configs:
                self._data_source_configs[name] = config
                self._update_priority_list()
                self._logger.info(f"Updated config for data source: {name}")

    def enable_data_source(self, name: str) -> None:
        """启用数据源"""
        with self._lock:
            if name in self._data_source_configs:
                self._data_source_configs[name].enabled = True
                self._logger.info(f"Enabled data source: {name}")

    def disable_data_source(self, name: str) -> None:
        """禁用数据源"""
        with self._lock:
            if name in self._data_source_configs:
                self._data_source_configs[name].enabled = False
                self._logger.info(f"Disabled data source: {name}")

    def clear_cache(self, data_source_name: Optional[str] = None) -> None:
        """清理缓存"""
        with self._lock:
            if data_source_name:
                # 清理特定数据源的缓存
                cache_keys_to_remove = [
                    k
                    for k in self._cache.keys()
                    if k.startswith(f"{data_source_name}:")
                ]
                for key in cache_keys_to_remove:
                    del self._cache[key]
                    del self._cache_timestamps[key]
            else:
                # 清理所有缓存
                self._cache.clear()
                self._cache_timestamps.clear()
