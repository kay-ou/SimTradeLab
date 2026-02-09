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


def _is_project_dir(path: Path) -> bool:
    """检查目录是否为有效的项目根目录"""
    data_dir = path / 'data'
    if not data_dir.is_dir():
        return False
    return (data_dir / 'manifest.json').exists() or (path / 'strategies').is_dir()


def get_project_root() -> Path:
    """获取项目根目录

    从任何位置调用都能正确返回项目根目录
    查找顺序: CWD → __file__ 向上查找 → pyproject.toml → 固定层级

    Returns:
        项目根目录的Path对象
    """
    # 方法1: 检查当前工作目录（支持 pip install 后从项目目录运行）
    cwd = Path.cwd()
    if _is_project_dir(cwd):
        return cwd

    # 方法2: 从源码位置向上查找 data 目录
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if _is_project_dir(parent):
            return parent

    # 方法3: 向上查找pyproject.toml（备选方案）
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists():
            return parent

    # 方法4: 如果都找不到，使用固定层级（当前文件在src/simtradelab/utils/）
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
