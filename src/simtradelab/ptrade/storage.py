# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
数据存储工具函数

仅支持 Parquet 格式
"""

from __future__ import annotations
import pandas as pd
from pathlib import Path


def _date_to_int(dt_series: pd.Series) -> pd.Series:
    """向量化将datetime转为YYYYMMDD整数"""
    return (
        dt_series.dt.year * 10000 +
        dt_series.dt.month * 100 +
        dt_series.dt.day
    ).astype(int)


def _date_to_iso(dt_series: pd.Series) -> pd.Series:
    """向量化将datetime转为YYYY-MM-DD字符串"""
    return (
        dt_series.dt.year.astype(str) + '-' +
        dt_series.dt.month.astype(str).str.zfill(2) + '-' +
        dt_series.dt.day.astype(str).str.zfill(2)
    )


def load_stock(data_dir, symbol):
    """加载股票价格数据"""
    parquet_file = Path(data_dir) / 'stocks' / f'{symbol}.parquet'
    if parquet_file.exists():
        df = pd.read_parquet(parquet_file)
        if not df.empty and 'date' in df.columns:
            df.set_index('date', inplace=True)
        return df
    return pd.DataFrame()


def load_valuation(data_dir, symbol):
    """加载估值数据"""
    parquet_file = Path(data_dir) / 'valuation' / f'{symbol}.parquet'
    if parquet_file.exists():
        df = pd.read_parquet(parquet_file)
        if not df.empty and 'date' in df.columns:
            df.set_index('date', inplace=True)
        return df
    return pd.DataFrame()


def load_fundamentals(data_dir, symbol):
    """加载财务数据"""
    parquet_file = Path(data_dir) / 'fundamentals' / f'{symbol}.parquet'
    if parquet_file.exists():
        df = pd.read_parquet(parquet_file)
        if not df.empty and 'date' in df.columns:
            df.set_index('date', inplace=True)
        return df
    return pd.DataFrame()


def load_exrights(data_dir, symbol):
    """加载除权数据

    Returns:
        dict，包含除权事件、复权因子、分红信息
    """
    empty_result = {
        'exrights_events': pd.DataFrame(),
        'adj_factors': pd.DataFrame(),
        'dividends': []
    }

    parquet_file = Path(data_dir) / 'exrights' / f'{symbol}.parquet'
    if not parquet_file.exists():
        return empty_result

    df = pd.read_parquet(parquet_file)
    if df.empty:
        return empty_result

    # 构建exrights_events
    ex_df = df.copy()
    if 'date' in ex_df.columns:
        ex_df['date'] = _date_to_int(ex_df['date'])
        ex_df.set_index('date', inplace=True)

    # 构建dividends列表
    dividends = []
    if 'dividend' in df.columns:
        valid_mask = df['dividend'].notna()
        if valid_mask.any():
            valid_df = df.loc[valid_mask, ['date', 'dividend']]
            date_strs = _date_to_iso(valid_df['date'])
            dividends = [
                {'date': d, 'dividend': div}
                for d, div in zip(date_strs.values, valid_df['dividend'].values)
            ]

    return {
        'exrights_events': ex_df,
        'adj_factors': pd.DataFrame(),
        'dividends': dividends
    }


def load_metadata(data_dir, filename):
    """加载元数据文件

    Args:
        data_dir: 数据根目录
        filename: 元数据文件名（如 'metadata' 或 'trade_days'）

    Returns:
        解析后的数据（dict或DataFrame）
    """
    data_path = Path(data_dir) / 'metadata'

    # 兼容旧调用：去除.br后缀
    if filename.endswith('.br'):
        filename = filename[:-3]

    # metadata特殊处理：已拆分为index_constituents和stock_status
    if filename == 'metadata':
        ic_file = data_path / 'index_constituents.parquet'
        ss_file = data_path / 'stock_status.parquet'
        if ic_file.exists() or ss_file.exists():
            return _load_metadata_parquet(data_path, filename)

    # 其他元数据
    parquet_file = data_path / f'{filename}.parquet'
    if parquet_file.exists():
        return _load_metadata_parquet(data_path, filename)

    return None


def _load_metadata_parquet(metadata_dir, base_name):
    """加载Parquet格式的元数据"""
    # metadata特殊处理：已拆分为index_constituents和stock_status
    if base_name == 'metadata':
        result = {}

        # index_constituents (预聚合格式: date, index_code, symbols)
        ic_file = metadata_dir / 'index_constituents.parquet'
        if ic_file.exists():
            ic_df = pd.read_parquet(ic_file)
            index_constituents = {}
            for date, group in ic_df.groupby('date'):
                index_constituents[date] = dict(zip(group['index_code'], group['symbols']))
            result['index_constituents'] = index_constituents

        # stock_status_history (预聚合格式: date, status_type, symbols)
        ss_file = metadata_dir / 'stock_status.parquet'
        if ss_file.exists():
            ss_df = pd.read_parquet(ss_file)
            stock_status_history = {}
            for date, group in ss_df.groupby('date'):
                stock_status_history[date] = {'ST': {}, 'HALT': {}, 'DELISTING': {}}
                for st, syms in zip(group['status_type'], group['symbols']):
                    stock_status_history[date][st] = dict.fromkeys(syms, True)
            result['stock_status_history'] = stock_status_history

        return result if result else None

    file_path = metadata_dir / f'{base_name}.parquet'
    if not file_path.exists():
        return None

    df = pd.read_parquet(file_path)

    if base_name == 'trade_days':
        return {'trade_days': _date_to_iso(df['date']).tolist()}

    elif base_name == 'stock_metadata':
        return {'data': df.to_dict('records')}

    elif base_name == 'benchmark':
        if 'date' in df.columns:
            df = df.copy()
            df['date'] = _date_to_iso(df['date'])
        return {'data': df.to_dict('records')}

    elif base_name == 'version':
        return df.iloc[0].to_dict()

    # 默认返回DataFrame
    return df


def list_stocks(data_dir):
    """列出所有可用的股票代码"""
    stocks_dir = Path(data_dir) / 'stocks'
    if not stocks_dir.exists():
        return []

    parquet_files = list(stocks_dir.glob('*.parquet'))
    return [f.stem for f in parquet_files]
