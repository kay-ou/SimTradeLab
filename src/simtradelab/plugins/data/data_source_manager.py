# -*- coding: utf-8 -*-
"""
数据源管理器

管理多个数据源插件，提供统一的数据访问接口。
按注册顺序选择数据源，简单高效。
"""

import logging
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Union

import pandas as pd

from ..base import PluginError
from .base_data_source import BaseDataSourcePlugin, DataFrequency, MarketType


@dataclass
class DataSourceConfig:
    """数据源配置（简化）"""

    enabled: bool = True
    timeout: float = 30.0  # 请求超时时间
    cache_enabled: bool = True
    # 移除不必要的复杂配置项（优先级、重试、健康检查等）


class DataSourceManager:
    """
    数据源管理器

    负责管理多个数据源插件，提供统一的数据访问接口。
    按注册顺序选择数据源，简单高效。
    """

    def __init__(self, plugin_manager: Optional[Any] = None):
        self._plugin_manager = plugin_manager
        self._data_sources: Dict[str, BaseDataSourcePlugin] = {}
        self._data_source_configs: Dict[str, DataSourceConfig] = {}
        self._source_order: List[str] = []  # 数据源顺序列表（按注册顺序）

        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

        # 简化的数据缓存
        self._cache_enabled = True
        self._cache: Dict[str, Any] = {}

    def initialize(self) -> None:
        """初始化数据源管理器"""
        self._logger.info("Initializing DataSourceManager")
        self._discover_data_sources()
        self._logger.info(
            f"DataSourceManager initialized with {len(self._data_sources)} data sources"
        )

    def shutdown(self) -> None:
        """关闭数据源管理器"""
        self._logger.info("Shutting down DataSourceManager")
        with self._lock:
            self._cache.clear()
            self._data_sources.clear()
            self._data_source_configs.clear()
            self._source_order.clear()

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

            # 添加到顺序列表
            if name not in self._source_order:
                self._source_order.append(name)

            self._logger.info(f"Registered data source: {name}")

    def unregister_data_source(self, name: str) -> None:
        """注销数据源插件"""
        with self._lock:
            if name in self._data_sources:
                del self._data_sources[name]
                del self._data_source_configs[name]

                if name in self._source_order:
                    self._source_order.remove(name)

                # 清理相关缓存
                cache_keys_to_remove = [
                    k for k in self._cache.keys() if k.startswith(f"{name}:")
                ]
                for key in cache_keys_to_remove:
                    del self._cache[key]

                self._logger.info(f"Unregistered data source: {name}")

    def _update_source_order(self) -> None:
        """更新数据源顺序列表（简化：保持注册顺序）"""
        # 简化：直接使用注册顺序，不需要复杂的排序逻辑
        # 这个方法保留为空，以便可能的未来扩展
        pass

    def get_available_data_sources(self) -> List[str]:
        """获取可用的数据源列表（按注册顺序）"""
        with self._lock:
            available_sources = []
            for name in self._source_order:
                if name in self._data_source_configs:
                    config = self._data_source_configs[name]
                    if config.enabled:
                        try:
                            data_source = self._data_sources[name]
                            if data_source.is_available():
                                available_sources.append(name)
                        except Exception:
                            # 忽略不可用的数据源
                            pass
            return available_sources

    def get_data_source_status(
        self, name: Optional[str] = None
    ) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """获取数据源基本状态"""
        with self._lock:
            if name:
                if name in self._data_source_configs:
                    config = self._data_source_configs[name]
                    return {"enabled": config.enabled}
                return {}
            else:
                return {
                    name: {"enabled": config.enabled}
                    for name, config in self._data_source_configs.items()
                }

    # ================================
    # 简化的数据源选择
    # ================================

    def _select_data_source(
        self, required_markets: Optional[Set[MarketType]] = None
    ) -> Optional[str]:
        """
        选择可用的数据源（按注册顺序）

        Args:
            required_markets: 需要的市场类型

        Returns:
            选中的数据源名称，如果没有可用数据源则返回None
        """
        with self._lock:
            # 简化：按注册顺序遍历，选择第一个可用的数据源
            for name in self._source_order:
                if name not in self._data_source_configs:
                    continue

                config = self._data_source_configs[name]
                data_source = self._data_sources[name]

                # 检查是否启用且可用
                if not config.enabled:
                    continue

                # 检查市场支持
                if required_markets:
                    supported_markets = data_source.get_supported_markets()
                    if not required_markets.issubset(supported_markets):
                        continue

                # 简化可用性检查：直接调用接口检查
                try:
                    if data_source.is_available():
                        return name
                except Exception as e:
                    self._logger.warning(
                        f"Data source {name} availability check failed: {e}"
                    )
                    continue

        return None

    # ================================
    # 简化的缓存管理
    # ================================

    def _get_cache_key(
        self, data_source_name: str, method: str, *args, **kwargs
    ) -> str:
        """生成缓存键"""
        args_str = str(args) + str(sorted(kwargs.items()))
        return f"{data_source_name}:{method}:{hash(args_str)}"

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取数据（移除TTL检查）"""
        if not self._cache_enabled:
            return None
        return self._cache.get(cache_key)

    def _put_to_cache(self, cache_key: str, data: Any) -> None:
        """将数据放入缓存（移除TTL管理）"""
        if not self._cache_enabled:
            return
        self._cache[cache_key] = data

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
        简化的数据源调用方法（按顺序尝试）

        Args:
            method_name: 要调用的方法名
            required_markets: 需要的市场类型
            use_cache: 是否使用缓存
            *args, **kwargs: 方法参数

        Returns:
            方法执行结果
        """
        # 按顺序尝试数据源
        for data_source_name in self._source_order:
            if data_source_name not in self._data_sources:
                continue

            # 检查数据源是否符合要求
            config = self._data_source_configs[data_source_name]
            data_source = self._data_sources[data_source_name]

            if not config.enabled:
                continue

            # 检查市场支持
            if required_markets:
                try:
                    supported_markets = data_source.get_supported_markets()
                    if not required_markets.issubset(supported_markets):
                        continue
                except Exception:
                    continue

            try:
                # 检查缓存
                cache_key = None
                if use_cache and config.cache_enabled:
                    cache_key = self._get_cache_key(
                        data_source_name, method_name, *args, **kwargs
                    )
                    cached_result = self._get_from_cache(cache_key)
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
                # 简化：直接尝试下一个数据源，不做复杂的错误计数
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
                # 简化：不需要重新排序优先级列表
                self._logger.info(f"Updated config for data source: {name}")

    def set_data_source_enabled(self, name: str, enabled: bool) -> None:
        """设置数据源启用状态"""
        with self._lock:
            if name in self._data_source_configs:
                self._data_source_configs[name].enabled = enabled
                status = "enabled" if enabled else "disabled"
                self._logger.info(f"{status.title()} data source: {name}")

    def enable_data_source(self, name: str) -> None:
        """启用数据源（兼容方法）"""
        self.set_data_source_enabled(name, True)

    def disable_data_source(self, name: str) -> None:
        """禁用数据源（兼容方法）"""
        self.set_data_source_enabled(name, False)

    def clear_cache(self, data_source_name: Optional[str] = None) -> None:
        """清理缓存（简化）"""
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
            else:
                # 清理所有缓存
                self._cache.clear()
