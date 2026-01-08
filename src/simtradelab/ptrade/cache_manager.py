# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
PTrade统一缓存管理器

统一管理所有缓存，提供LRU策略和统一清理接口
使用cachetools提供高性能LRU缓存实现
"""


from __future__ import annotations

from typing import Any, Optional
from datetime import datetime
from cachetools import LRUCache


class CacheNamespace:
    """缓存命名空间

    为不同类型的数据提供独立的缓存空间
    使用cachetools.LRUCache作为底层实现
    """

    def __init__(self, name: str, max_size: int):
        self.name = name
        self._cache = LRUCache(maxsize=max_size)
        self._stats = {
            'hits': 0,
            'misses': 0,
            'puts': 0,
            'clears': 0
        }

    def get(self, key: Any) -> Optional[Any]:
        """获取值

        cachetools.LRUCache会自动更新访问顺序
        """
        try:
            value = self._cache[key]
            self._stats['hits'] += 1
            return value
        except KeyError:
            self._stats['misses'] += 1
            return None

    def put(self, key: Any, value: Any) -> None:
        """存入值

        cachetools.LRUCache会自动淘汰最旧项
        """
        self._cache[key] = value
        self._stats['puts'] += 1

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._stats['clears'] += 1

    def size(self) -> int:
        """当前缓存数量"""
        return len(self._cache)

    def maxsize(self) -> int:
        """最大缓存数量"""
        return self._cache.maxsize

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
        return {
            'name': self.name,
            'size': self.size(),
            'maxsize': self.maxsize(),
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'puts': self._stats['puts'],
            'clears': self._stats['clears'],
            'hit_rate': hit_rate
        }

    def __contains__(self, key: Any) -> bool:
        return key in self._cache


class UnifiedCacheManager:
    """统一缓存管理器

    单例模式，管理所有命名空间的缓存
    使用cachetools.LRUCache提供高性能缓存
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        from .config_manager import config

        # 创建各个缓存命名空间，使用cachetools.LRUCache
        self._namespaces: dict[str, CacheNamespace] = {
            'ma_cache': CacheNamespace('MA计算', config.cache.global_ma_vwap_cache_size),
            'vwap_cache': CacheNamespace('VWAP计算', config.cache.global_ma_vwap_cache_size),
            'history': CacheNamespace('历史数据', config.cache.history_cache_size),
            'stock_status': CacheNamespace('股票状态', config.cache.data_cache_size),
            'date_index': CacheNamespace('日期索引', config.cache.data_cache_size),
            'fundamentals': CacheNamespace('基本面数据', config.cache.fundamentals_cache_size),
            'exrights': CacheNamespace('复权数据', config.cache.exrights_cache_size),
        }

        # 当前日期（用于日缓存清理）
        self._current_date: Optional[datetime] = None

        self._initialized = True

    def get_namespace(self, name: str) -> CacheNamespace:
        """获取缓存命名空间"""
        if name not in self._namespaces:
            raise ValueError("未知的缓存命名空间: {}".format(name))
        return self._namespaces[name]

    def get(self, namespace: str, key: Any) -> Optional[Any]:
        """从指定命名空间获取值"""
        return self._namespaces[namespace].get(key)

    def put(self, namespace: str, key: Any, value: Any) -> None:
        """向指定命名空间存入值"""
        self._namespaces[namespace].put(key, value)

    def clear_namespace(self, namespace: str) -> None:
        """清空指定命名空间"""
        if namespace in self._namespaces:
            self._namespaces[namespace].clear()

    def clear_all(self) -> None:
        """清空所有缓存"""
        for ns in self._namespaces.values():
            ns.clear()

    def clear_daily_cache(self, current_date: Optional[datetime] = None) -> None:
        """清理日级缓存

        当日期变化时，清理MA、VWAP等日内计算缓存
        """
        if current_date is None:
            current_date = datetime.now()

        # 如果日期改变，清理日级缓存
        if self._current_date is None or self._current_date.date() != current_date.date():
            self.clear_namespace('ma_cache')
            self.clear_namespace('vwap_cache')
            self._current_date = current_date


# 全局单例实例
cache_manager = UnifiedCacheManager()

