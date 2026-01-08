# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
复权因子缓存模块

负责预计算和缓存所有股票的复权因子,以提升get_history性能
"""


import pandas as pd
import numpy as np
import os
import pickle
from pathlib import Path
from ..utils.paths import ADJ_PRE_CACHE_PATH, DIVIDEND_CACHE_PATH
from ..utils.perf import timer
from joblib import Parallel, delayed
import warnings
from tables import NaturalNameWarning

warnings.filterwarnings("ignore", category=NaturalNameWarning)


def _get_cached_adj_keys():
    """获取复权缓存文件的keys，优先使用缓存"""
    # 缓存文件路径
    cache_dir = Path(ADJ_PRE_CACHE_PATH).parent / '.keys_cache'
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / 'adj_pre_cache_keys.pkl'

    # H5文件修改时间
    h5_mtime = Path(ADJ_PRE_CACHE_PATH).stat().st_mtime if os.path.exists(ADJ_PRE_CACHE_PATH) else 0

    # 检查缓存是否有效
    if cache_file.exists():
        cache_mtime = cache_file.stat().st_mtime
        if cache_mtime >= h5_mtime:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

    # 重新读取并缓存
    with pd.HDFStore(ADJ_PRE_CACHE_PATH, 'r') as store:
        keys_list = list(store.keys())

    with open(cache_file, 'wb') as f:
        pickle.dump(keys_list, f)

    return keys_list




def _calculate_adj_factors_single(stock, stock_df, exrights_df):
    """计算单只股票的前复权因子序列(joblib worker)

    ptrade前复权逻辑: 前复权价 = 未复权价 * exer_forward_a + exer_forward_b

    对于每个交易日，需要找到该日期之前最近的除权事件对应的因子。
    如果没有除权事件，因子为 (1.0, 0.0) 表示不复权。

    Args:
        stock: 股票代码
        stock_df: 股票价格数据
        exrights_df: 除权数据

    Returns:
        DataFrame with columns ['adj_a', 'adj_b'] 或 None
    """
    if stock_df is None or stock_df.empty:
        return None

    if exrights_df is None or exrights_df.empty:
        return None

    all_dates = stock_df.index

    try:
        if 'exer_forward_a' not in exrights_df.columns or 'exer_forward_b' not in exrights_df.columns:
            return None

        # 将除权日期转换为datetime
        ex_dates_int = exrights_df.index.tolist()
        ex_dates_dt = pd.to_datetime(ex_dates_int, format='%Y%m%d')
        adj_a_values = exrights_df['exer_forward_a'].values
        adj_b_values = exrights_df['exer_forward_b'].values

        # 对于每个交易日，找到其所在的复权区间对应的因子
        # 除权日当天及之后使用该除权事件的因子
        adj_factors = pd.DataFrame(index=all_dates, columns=['adj_a', 'adj_b'], dtype='float32')

        for i, trade_date in enumerate(all_dates):
            # 找到trade_date当天或之前最近的除权事件
            past_or_equal_mask = ex_dates_dt <= trade_date

            if past_or_equal_mask.any():
                # 使用最近的除权因子
                last_idx = np.where(past_or_equal_mask)[0][-1]
                adj_factors.iloc[i] = [adj_a_values[last_idx], adj_b_values[last_idx]]
            else:
                # trade_date早于所有除权事件
                # 如果有未来除权事件，使用第一个
                if len(adj_a_values) > 0:
                    adj_factors.iloc[i] = [adj_a_values[0], adj_b_values[0]]
                else:
                    # 完全没有除权数据，使用单位因子
                    adj_factors.iloc[i] = [1.0, 0.0]

        return adj_factors
    except Exception as e:
        print(f"计算 {stock} 前复权因子失败: {e}")
        import traceback
        traceback.print_exc()
        return None


@timer(threshold=0.1, name="前复权因子缓存创建")
def create_adj_pre_cache(data_context):
    """创建并保存所有股票的前复权因子缓存(使用joblib并行)

    ptrade前复权逻辑: 前复权价 = 未复权价 * exer_forward_a + exer_forward_b
    """
    print("正在创建前复权因子缓存...")

    all_stocks = list(data_context.stock_data_dict.keys())
    total_stocks = len(all_stocks)

    # 预加载数据
    print(f"  预加载数据...")
    stock_data_cache = {s: data_context.stock_data_dict.get(s) for s in all_stocks}
    exrights_cache = {s: data_context.exrights_dict.get(s)
                     for s in all_stocks
                     if data_context.exrights_dict.get(s) is not None}

    # joblib并行计算
    num_workers = int(os.getenv('PTRADE_NUM_WORKERS', '-1'))
    print(f"  并行计算({num_workers if num_workers > 0 else 'auto'}进程)...")

    results = Parallel(n_jobs=num_workers, backend='loky', verbose=0)(
        delayed(_calculate_adj_factors_single)(
            stock, stock_data_cache.get(stock), exrights_cache.get(stock)
        ) for stock in all_stocks
    )

    # 保存结果
    print("  正在保存到HDF5...")
    saved_count = 0
    with pd.HDFStore(ADJ_PRE_CACHE_PATH, 'w', complevel=9, complib='blosc') as store:
        for stock, adj_factors in zip(all_stocks, results):
            if adj_factors is not None:
                store.put(stock, adj_factors, format='fixed')
                saved_count += 1

    print(f"✓ 前复权因子缓存创建完成！")
    print(f"  处理: {total_stocks} 只股票")
    print(f"  保存: {saved_count} 只（有除权数据）")
    print(f"  文件: {ADJ_PRE_CACHE_PATH}")


@timer(threshold=0.1, name="前复权因子缓存加载")
def load_adj_pre_cache(data_context):
    """加载前复权因子缓存（支持多进程加速）

    返回的是前复权因子DataFrame(columns=['adj_a', 'adj_b'])，运行时用于计算前复权价格。
    前复权价 = 未复权价 * adj_a + adj_b
    """
    if not os.path.exists(ADJ_PRE_CACHE_PATH):
        create_adj_pre_cache(data_context)

    print("正在加载前复权因子缓存...")

    # 判断是否使用多进程
    from ..utils.performance_config import get_performance_config
    config = get_performance_config()

    # 使用缓存keys避免重复遍历HDF5
    all_keys = _get_cached_adj_keys()

    if config.enable_multiprocessing and len(all_keys) >= config.min_batch_size:
        # 多进程加载
        num_workers = config.num_workers
        chunk_size = max(50, len(all_keys) // (num_workers * 2))
        chunks = [all_keys[i:i+chunk_size] for i in range(0, len(all_keys), chunk_size)]

        print(f"  使用{num_workers}进程并行加载 {len(all_keys)} 只...")

        results = Parallel(n_jobs=num_workers, backend='loky', verbose=0)(
            delayed(_load_adj_factors_chunk)(ADJ_PRE_CACHE_PATH, chunk)
            for chunk in chunks
        )

        adj_factors_cache = {}
        for chunk_result in results:
            adj_factors_cache.update(chunk_result)
    else:
        # 串行加载
        adj_factors_cache = {}
        with pd.HDFStore(ADJ_PRE_CACHE_PATH, 'r') as store:
            for key in all_keys:
                stock = key.strip('/')
                adj_factors_cache[stock] = store[key]

    print(f"✓ 前复权因子缓存加载完成！共 {len(adj_factors_cache)} 只股票")
    return adj_factors_cache


def _load_adj_factors_chunk(cache_path, keys_chunk):
    """多进程worker：加载一批复权因子"""
    result = {}
    store = pd.HDFStore(cache_path, 'r')
    try:
        for key in keys_chunk:
            stock = key.strip('/')
            result[stock] = store[key]
    finally:
        store.close()
    return result


@timer(threshold=0.1, name="分红缓存加载或创建")
def create_dividend_cache(data_context):
    """创建分红事件缓存（支持持久化）

    返回格式: {stock_code: {date_str: dividend_amount_before_tax}}

    注意：存储税前分红金额，税率由context.dividend_tax_rate配置
    """
    # 检查缓存文件是否存在
    if os.path.exists(DIVIDEND_CACHE_PATH):
        print("正在加载分红缓存...")

        try:
            # 从HDF5加载
            df = pd.read_hdf(DIVIDEND_CACHE_PATH, key='dividends')

            # 重建字典(向量化)
            dividend_cache = {}
            for stock, group in df.groupby('stock'):
                dividend_cache[stock] = dict(zip(group['date'], group['amount']))

            print(f"✓ 分红缓存加载完成！")
            print(f"  有分红股票: {len(dividend_cache)} 只")
            print(f"  总分红事件: {sum(len(v) for v in dividend_cache.values())} 次")
            return dividend_cache
        except Exception as e:
            print(f"警告: 加载分红缓存失败({e}),重新创建...")

    # 缓存不存在,创建新的
    print("正在创建分红事件缓存...")

    all_stocks = list(data_context.exrights_dict.keys())

    # 预加载数据
    print(f"  预加载除权数据...")
    exrights_data = {s: data_context.exrights_dict.get(s)
                    for s in all_stocks
                    if data_context.exrights_dict.get(s) is not None}

    # joblib并行处理
    num_workers = int(os.getenv('PTRADE_NUM_WORKERS', '-1'))
    print(f"  并行计算({num_workers if num_workers > 0 else 'auto'}进程)...")

    results = Parallel(n_jobs=num_workers, backend='loky', verbose=0)(
        delayed(_process_dividend_single)(stock, exrights_data.get(stock))
        for stock in all_stocks
    )

    # 合并结果
    dividend_cache = {}
    for stock, dividends in zip(all_stocks, results):
        if dividends:
            dividend_cache[stock] = dividends

    # 保存到HDF5
    print("  正在保存分红缓存到磁盘...")
    _save_dividend_cache(dividend_cache)

    print(f"✓ 分红事件缓存创建完成！")
    print(f"  有分红股票: {len(dividend_cache)} 只")
    print(f"  总分红事件: {sum(len(v) for v in dividend_cache.values())} 次")

    return dividend_cache


def _save_dividend_cache(dividend_cache):
    """保存分红缓存到HDF5"""
    # 转换为DataFrame
    records = []
    for stock, dividends in dividend_cache.items():
        for date_str, amount in dividends.items():
            records.append({'stock': stock, 'date': date_str, 'amount': amount})

    df = pd.DataFrame(records)

    # 保存到HDF5
    with pd.HDFStore(DIVIDEND_CACHE_PATH, 'w', complevel=9, complib='blosc') as store:
        store.put('dividends', df, format='table')

    print(f"  已保存到: {DIVIDEND_CACHE_PATH}")


def _process_dividend_single(stock, exrights_df):
    """处理单只股票的分红数据(joblib worker)

    Args:
        stock: 股票代码
        exrights_df: 除权数据

    Returns:
        {date_str: amount} 或 None
    """
    if exrights_df is None or exrights_df.empty:
        return None

    # 向量化过滤
    dividend_mask = exrights_df['bonus_ps'] > 0
    if not dividend_mask.any():
        return None

    # 批量提取
    dividend_records = exrights_df[dividend_mask]['bonus_ps']
    return {str(date_int): amount for date_int, amount in dividend_records.items()}
