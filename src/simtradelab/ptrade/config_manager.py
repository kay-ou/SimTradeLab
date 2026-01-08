# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
PTrade统一配置管理器

集中管理所有配置项，消除代码中的魔法数字和重复配置
使用pydantic提供数据验证和类型安全
"""


from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class TradingConfig(BaseModel):
    """交易相关配置

    使用pydantic自动验证配置有效性
    """
    commission_ratio: float = Field(
        default=0.0003,
        gt=0,
        description="佣金费率，必须大于0"
    )
    min_commission: float = Field(
        default=5.0,
        gt=0,
        description="最低佣金，必须大于0"
    )
    slippage: float = Field(
        default=0.001,
        ge=0,
        description="比例滑点"
    )
    fixed_slippage: float = Field(
        default=0.0,
        ge=0,
        description="固定滑点（单位：元）"
    )
    volume_ratio: float = Field(
        default=0.25,
        ge=0,
        le=1,
        description="成交比例，必须在0-1之间"
    )
    limit_mode: str = Field(
        default="LIMIT",
        description="下单限制模式：LIMIT限制成交量，UNLIMITED不限制"
    )
    commission_type: str = Field(
        default="STOCK",
        description="佣金类型"
    )

    model_config = {"frozen": True}  # 配置不可变，确保线程安全


class CacheConfig(BaseModel):
    """缓存相关配置"""
    global_ma_vwap_cache_size: int = Field(
        default=5000,
        gt=0,
        description="全局MA/VWAP缓存大小"
    )
    lazy_dict_cache_size: int = Field(
        default=6000,
        gt=0,
        description="LazyDataDict缓存大小"
    )
    fundamentals_cache_size: int = Field(
        default=800,
        gt=0,
        description="基本面数据缓存大小"
    )
    exrights_cache_size: int = Field(
        default=800,
        gt=0,
        description="复权数据缓存大小"
    )
    data_cache_size: int = Field(
        default=200,
        gt=0,
        description="Data对象缓存大小"
    )
    history_cache_size: int = Field(
        default=10000,
        gt=0,
        description="历史数据缓存大小（单股票粒度，约10000只×25天×8字节≈2MB）"
    )

    model_config = {"frozen": True}


class PerformanceConfig(BaseModel):
    """性能相关配置"""
    use_multiprocessing: bool = Field(
        default=False,
        description="是否启用多进程"
    )
    num_processes: int = Field(
        default=4,
        gt=0,
        description="进程数量"
    )
    enable_tqdm: bool = Field(
        default=True,
        description="是否显示进度条"
    )
    preload_all_stocks: bool = Field(
        default=False,
        description="是否预加载所有股票"
    )

    model_config = {"frozen": True}


class ConfigurationManager:
    """统一配置管理器

    单例模式，全局唯一配置中心
    使用pydantic模型提供类型安全和自动验证
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

        self.trading = TradingConfig()
        self.cache = CacheConfig()
        self.performance = PerformanceConfig()
        self._initialized = True

    def update_trading_config(self, **kwargs) -> None:
        """更新交易配置

        自动验证参数有效性。配置不可变，创建新实例。
        """
        self.trading = TradingConfig(**{**self.trading.model_dump(), **kwargs})

    def update_cache_config(self, **kwargs) -> None:
        """更新缓存配置"""
        self.cache = CacheConfig(**{**self.cache.model_dump(), **kwargs})

    def update_performance_config(self, **kwargs) -> None:
        """更新性能配置"""
        self.performance = PerformanceConfig(**{**self.performance.model_dump(), **kwargs})

    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.trading = TradingConfig()
        self.cache = CacheConfig()
        self.performance = PerformanceConfig()

    def export_config(self) -> dict[str, Any]:
        """导出所有配置为字典

        使用pydantic的model_dump方法
        """
        return {
            'trading': self.trading.model_dump(),
            'cache': self.cache.model_dump(),
            'performance': self.performance.model_dump(),
        }

    def load_config(self, config_dict: dict[str, Any]) -> None:
        """从字典加载配置

        使用pydantic的model_validate方法
        """
        if 'trading' in config_dict:
            self.trading = TradingConfig.model_validate(config_dict['trading'])
        if 'cache' in config_dict:
            self.cache = CacheConfig.model_validate(config_dict['cache'])
        if 'performance' in config_dict:
            self.performance = PerformanceConfig.model_validate(config_dict['performance'])


# 全局单例实例
config = ConfigurationManager()

