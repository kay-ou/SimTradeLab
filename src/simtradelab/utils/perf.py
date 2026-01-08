# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""性能计时工具"""


import time
from functools import wraps
from contextlib import contextmanager


def format_elapsed_time(elapsed: float) -> str:
    """格式化耗时显示

    Args:
        elapsed: 耗时（秒）

    Returns:
        格式化后的字符串（如：3分32秒 或 45.23秒）
    """
    minutes = int(elapsed / 60)
    seconds = int(elapsed % 60)
    if minutes > 0:
        return f"{minutes}分{seconds}秒"
    else:
        return f"{elapsed:.2f}秒"


def timer(threshold=0.1, name=None):
    """性能计时装饰器（智能格式化输出）

    Args:
        threshold: 仅当耗时超过此阈值时才输出（秒）
        name: 自定义操作名称，默认使用函数名

    自动根据类名调整输出格式：
    - PtradeAPI: 显示批量信息
    - BacktestRunner/StrategyExecutionEngine: 显示完成标记

    Example:
        @timer()
        def my_function():
            pass

        @timer(name="数据加载")
        def load_data():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()

            # 保存开始时间（供函数内部访问当前耗时）
            if args and hasattr(args[0], '__class__'):
                instance = args[0]
                if not hasattr(instance, '_timing_start'):
                    instance._timing_start = {}
                instance._timing_start[func.__name__] = start

            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start

            if elapsed > threshold:
                func_name = name or func.__name__
                # 尝试获取第一个参数的类型信息
                if args and hasattr(args[0], '__class__'):
                    class_name = args[0].__class__.__name__
                    if class_name == 'PtradeAPI':
                        # 如果是批量操作，显示批次大小
                        if len(args) > 1 and isinstance(args[1], (list, tuple)):
                            print(f"  [PERF] {func_name}(批量{len(args[1])}只) 耗时: {elapsed:.2f}s", flush=True)
                        else:
                            print(f"  [PERF] {func_name} 耗时: {elapsed:.2f}s", flush=True)
                    elif class_name in ['BacktestRunner', 'StrategyExecutionEngine']:
                        # 回测相关类显示耗时
                        print(f"✓ {func_name} 完成，耗时: {format_elapsed_time(elapsed)}", flush=True)
                    else:
                        # 其他类默认格式
                        print(f"  [PERF] {func_name} 耗时: {elapsed:.2f}s", flush=True)
                else:
                    # 没有实例的情况（模块级函数）
                    print(f"  [PERF] {func_name} 耗时: {elapsed:.2f}s", flush=True)
            return result
        return wrapper
    return decorator


def get_current_elapsed_time(instance, func_name: str) -> str:
    """获取正在执行的函数的当前耗时

    Args:
        instance: 实例对象
        func_name: 函数名

    Returns:
        格式化后的耗时字符串
    """
    if hasattr(instance, '_timing_start'):
        start_time = instance._timing_start.get(func_name, 0)
        if start_time > 0:
            elapsed = time.perf_counter() - start_time
            return format_elapsed_time(elapsed)
    return '0秒'


@contextmanager
def timed(name="操作", threshold=0.1):
    """性能计时上下文管理器

    Args:
        name: 操作名称
        threshold: 仅当耗时超过此阈值时才输出（秒）

    Example:
        with timed("数据处理"):
            process_data()

        with timed("查询", threshold=1.0):
            run_query()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        if elapsed >= threshold:
            print(f"  [PERF] {name} 耗时: {elapsed:.2f}s", flush=True)
