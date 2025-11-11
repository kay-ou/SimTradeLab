# -*- coding: utf-8 -*-
"""
项目路径管理

提供统一的路径访问，所有代码通过此模块获取项目路径
"""

import os
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录

    从任何位置调用都能正确返回项目根目录

    Returns:
        项目根目录的Path对象
    """
    # 从当前文件向上查找项目根目录（包含pyproject.toml的目录）
    current = Path(__file__).resolve()

    # 向上查找pyproject.toml
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists():
            return parent

    # 如果找不到pyproject.toml，使用固定层级（当前文件在src/simtradelab/）
    return current.parent.parent.parent


def get_data_path() -> Path:
    """获取数据目录路径"""
    return get_project_root() / 'data'


def get_strategies_path() -> Path:
    """获取策略目录路径"""
    return get_project_root() / 'strategies'


# 便捷访问
PROJECT_ROOT = get_project_root()
DATA_PATH = get_data_path()
STRATEGIES_PATH = get_strategies_path()

# HDF5缓存文件路径
ADJ_PRE_CACHE_PATH = DATA_PATH / 'ptrade_adj_pre.h5'
