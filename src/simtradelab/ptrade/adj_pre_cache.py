# -*- coding: utf-8 -*-
"""
复权因子缓存模块

负责预计算和缓存所有股票的复权因子，以提升get_history性能
"""
import pandas as pd
import numpy as np
import os
import time
from ..paths import ADJ_PRE_CACHE_PATH
import warnings
from tables import NaturalNameWarning

warnings.filterwarnings("ignore", category=NaturalNameWarning)


def _calculate_cumulative_adj_pre(stock, data_context):
    """计算单只股票的累计复权因子（前复权）

    逻辑：
    - exer_backward_a 是后复权累积因子，最新日期a最大，历史日期a递减
    - 前复权：最新价不变（因子=1），历史价需要调高（因子>1）
    - 前复权因子 = 最新a / 当天a
    """
    try:
        exrights_df = data_context.exrights_dict.get(stock)
        stock_df = data_context.stock_data_dict.get(stock)

        if stock_df is None or stock_df.empty:
            return None

        all_dates = stock_df.index

        if exrights_df is None or exrights_df.empty or 'exer_backward_a' not in exrights_df.columns:
            return pd.Series(1.0, index=all_dates)

        # 将除权日期从int(YYYYMMDD)转换为datetime
        ex_dates_int = exrights_df.index.tolist()
        ex_dates_dt = pd.to_datetime(ex_dates_int, format='%Y%m%d')

        # 获取最新的backward_a（作为基准）
        max_a = exrights_df['exer_backward_a'].max()

        # 创建日期到a值的映射（向后填充）
        ex_df_indexed = pd.DataFrame({
            'date': ex_dates_dt,
            'backward_a': exrights_df['exer_backward_a'].values
        }).set_index('date').sort_index()

        # 将a值向后填充到所有交易日
        a_series = ex_df_indexed['backward_a'].reindex(all_dates, method='ffill', fill_value=1.0)

        # 前复权因子 = max_a / 当天a
        factors = max_a / a_series

        return factors.astype(np.float64)

    except Exception as e:
        print(f"计算 {stock} 复权因子失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_adj_pre_cache(data_context):
    """创建并保存所有股票的复权因子缓存"""
    import time
    from tqdm import tqdm

    print("正在创建复权因子缓存...")
    start_time = time.time()

    all_stocks = list(data_context.stock_data_dict.keys())
    total_stocks = len(all_stocks)
    saved_count = 0

    with pd.HDFStore(ADJ_PRE_CACHE_PATH, 'w', complevel=9, complib='blosc') as store:
        for stock in tqdm(all_stocks, desc='  处理', ncols=80, ascii=True,
                         bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:4d}/{total:4d} [{elapsed}<{remaining}]'):
            adj_pre = _calculate_cumulative_adj_pre(stock, data_context)
            if adj_pre is not None and not adj_pre.empty:
                # 只保存有除权的股票（不是全1.0）
                if adj_pre.nunique() > 1:
                    # 使用float32节省50%空间
                    adj_pre = adj_pre.astype('float32')
                    store.put(stock, adj_pre, format='fixed')
                    saved_count += 1

    elapsed = time.time() - start_time
    print(f"✓ 复权因子缓存创建完成！")
    print(f"  处理: {total_stocks} 只股票")
    print(f"  保存: {saved_count} 只（有除权数据）")
    print(f"  耗时: {elapsed:.2f} 秒")
    print(f"  文件: {ADJ_PRE_CACHE_PATH}")


def load_adj_pre_cache(data_context):
    """加载复权因子缓存"""
    if not os.path.exists(ADJ_PRE_CACHE_PATH):
        create_adj_pre_cache(data_context)

    print("正在加载复权因子缓存...")
    start_time = time.time()

    adj_factors_cache = {}
    with pd.HDFStore(ADJ_PRE_CACHE_PATH, 'r') as store:
        for key in store.keys():
            stock = key.strip('/')
            adj_factors_cache[stock] = store[key]

    elapsed = time.time() - start_time
    print(f"复权因子缓存加载完成！共 {len(adj_factors_cache)} 只股票，耗时 {elapsed:.2f} 秒")
    return adj_factors_cache


def create_dividend_cache(data_context):
    """创建分红事件缓存

    返回格式: {stock_code: {date_str: dividend_amount_before_tax}}

    注意：存储税前分红金额，税率由context.dividend_tax_rate配置
    """
    print("正在创建分红事件缓存...")
    start_time = time.time()

    dividend_cache = {}

    for stock_code, exrights_df in data_context.exrights_dict.items():
        if exrights_df is None or exrights_df.empty:
            continue

        stock_dividends = {}

        for date_int, row in exrights_df.iterrows():
            dividend_per_share_before_tax = row['bonus_ps']

            if dividend_per_share_before_tax > 0:
                date_str = str(date_int)
                stock_dividends[date_str] = dividend_per_share_before_tax

        if stock_dividends:
            dividend_cache[stock_code] = stock_dividends

    elapsed = time.time() - start_time
    print(f"✓ 分红事件缓存创建完成！")
    print(f"  有分红股票: {len(dividend_cache)} 只")
    print(f"  总分红事件: {sum(len(v) for v in dividend_cache.values())} 次")
    print(f"  耗时: {elapsed:.2f} 秒")

    return dividend_cache
