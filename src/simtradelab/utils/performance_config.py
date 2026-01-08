# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
性能优化全局配置

通过环境变量或代码设置控制多进程行为
"""


import os
from multiprocessing import cpu_count


class PerformanceConfig:
    """性能优化配置单例"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 从环境变量读取（兼容旧方式）
        self.enable_multiprocessing = os.getenv('PTRADE_MULTIPROCESSING', 'true').lower() == 'true'
        self.num_workers = max(1, cpu_count() - 1)
        self.min_batch_size = 100  # 少于此数量不启用多进程

        self._initialized = True

    def set_multiprocessing(self, enabled: bool):
        """设置是否启用多进程

        Args:
            enabled: True启用，False禁用
        """
        self.enable_multiprocessing = enabled

    def set_num_workers(self, num: int):
        """设置worker数量

        Args:
            num: worker数量（必须>=1）
        """
        if num < 1:
            raise ValueError("worker数量必须>=1")
        self.num_workers = num


# 全局单例
_config = PerformanceConfig()


def get_performance_config() -> PerformanceConfig:
    """获取全局性能配置"""
    return _config


def enable_multiprocessing(enabled: bool = True):
    """快捷方法：启用/禁用多进程

    用法：
        from simtradelab.performance_config import enable_multiprocessing
        enable_multiprocessing(False)  # 禁用多进程
    """
    _config.set_multiprocessing(enabled)


def set_num_workers(num: int):
    """快捷方法：设置worker数量

    用法：
        from simtradelab.performance_config import set_num_workers
        set_num_workers(2)  # 使用2个worker
    """
    _config.set_num_workers(num)
