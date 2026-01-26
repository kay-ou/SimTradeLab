# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
数据存储工具函数

提供 Brotli 压缩文件的读写功能
"""

from __future__ import annotations
import json
import brotli
import pandas as pd
from pathlib import Path


def load_brotli_json(file_path):
    """加载 Brotli 压缩的 JSON 文件

    Args:
        file_path: 文件路径

    Returns:
        解析后的 JSON 对象
    """
    with open(file_path, 'rb') as f:
        compressed = f.read()
        decompressed = brotli.decompress(compressed)
        return json.loads(decompressed.decode('utf-8'))


def load_stock(data_dir, symbol):
    """加载股票价格数据

    Args:
        data_dir: 数据根目录
        symbol: 股票代码

    Returns:
        DataFrame，包含 OHLCV 数据
    """
    file_path = Path(data_dir) / 'stocks' / f'{symbol}.br'
    if not file_path.exists():
        return pd.DataFrame()

    data = load_brotli_json(file_path)
    df = pd.DataFrame(data['data'])
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    return df


def load_valuation(data_dir, symbol):
    """加载估值数据

    Args:
        data_dir: 数据根目录
        symbol: 股票代码

    Returns:
        DataFrame，包含估值指标
    """
    file_path = Path(data_dir) / 'valuation' / f'{symbol}.br'
    if not file_path.exists():
        return pd.DataFrame()

    data = load_brotli_json(file_path)
    df = pd.DataFrame(data['data'])
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    return df


def load_fundamentals(data_dir, symbol):
    """加载财务数据

    Args:
        data_dir: 数据根目录
        symbol: 股票代码

    Returns:
        DataFrame，包含财务指标
    """
    file_path = Path(data_dir) / 'fundamentals' / f'{symbol}.br'
    if not file_path.exists():
        return pd.DataFrame()

    data = load_brotli_json(file_path)
    df = pd.DataFrame(data['data'])
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    return df


def load_exrights(data_dir, symbol):
    """加载除权数据

    Args:
        data_dir: 数据根目录
        symbol: 股票代码

    Returns:
        dict，包含除权事件、复权因子、分红信息
    """
    file_path = Path(data_dir) / 'exrights' / f'{symbol}.br'
    if not file_path.exists():
        return {
            'exrights_events': pd.DataFrame(),
            'adj_factors': pd.DataFrame(),
            'dividends': []
        }

    data = load_brotli_json(file_path)
    result = {}

    # 除权事件 (数据文件中key为'exrights')
    exrights_key = 'exrights' if 'exrights' in data else 'exrights_events'
    if exrights_key in data and data[exrights_key]:
        ex_df = pd.DataFrame(data[exrights_key])
        if not ex_df.empty and 'date' in ex_df.columns:
            ex_df['date'] = ex_df['date'].astype(str).str.replace('-', '').astype(int)
            ex_df.set_index('date', inplace=True)
        result['exrights_events'] = ex_df
    else:
        result['exrights_events'] = pd.DataFrame()

    # 预计算的复权因子
    if 'adj_factors' in data and data['adj_factors']:
        adj_df = pd.DataFrame(data['adj_factors'])
        if not adj_df.empty and 'date' in adj_df.columns:
            adj_df['date'] = pd.to_datetime(adj_df['date'])
            adj_df.set_index('date', inplace=True)
        result['adj_factors'] = adj_df
    else:
        result['adj_factors'] = pd.DataFrame()

    # 分红事件
    result['dividends'] = data.get('dividends', [])

    return result


def load_metadata(data_dir, filename):
    """加载元数据文件

    Args:
        data_dir: 数据根目录
        filename: 元数据文件名（如 'metadata.br'）

    Returns:
        解析后的数据
    """
    file_path = Path(data_dir) / 'metadata' / filename
    if not file_path.exists():
        return None
    return load_brotli_json(file_path)


def list_stocks(data_dir):
    """列出所有可用的股票代码

    Args:
        data_dir: 数据根目录

    Returns:
        股票代码列表
    """
    stocks_dir = Path(data_dir) / 'stocks'
    if not stocks_dir.exists():
        return []
    return [f.stem for f in stocks_dir.glob('*.br')]
