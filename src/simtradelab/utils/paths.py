# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
项目路径管理

提供统一的路径访问，所有代码通过此模块获取项目路径
"""


from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录

    从任何位置调用都能正确返回项目根目录
    优先查找data目录（更可靠），然后查找pyproject.toml

    Returns:
        项目根目录的Path对象
    """
    current = Path(__file__).resolve()

    # 方法1: 向上查找data目录（最可靠的方式）
    for parent in [current] + list(current.parents):
        data_dir = parent / 'data'
        # 检查data目录是否存在且包含HDF5文件（验证是正确的项目目录）
        if data_dir.exists() and data_dir.is_dir():
            # 进一步验证：检查是否有预期的数据文件
            has_data_files = any(data_dir.glob('*.h5'))
            if has_data_files or (parent / 'strategies').exists():
                return parent

    # 方法2: 向上查找pyproject.toml（备选方案）
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists():
            return parent

    # 方法3: 如果都找不到，使用固定层级（当前文件在src/simtradelab/utils/）
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

# 缓存文件路径（使用Parquet格式）
ADJ_PRE_CACHE_PATH = DATA_PATH / 'ptrade_adj_pre.parquet'
ADJ_POST_CACHE_PATH = DATA_PATH / 'ptrade_adj_post.parquet'
