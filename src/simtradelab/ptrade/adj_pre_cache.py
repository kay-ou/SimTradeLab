# -*- coding: utf-8 -*-
"""
复权因子缓存模块

负责预计算和缓存所有股票的复权因子,以提升get_history性能
"""
import pandas as pd
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




def _calculate_cumulative_dividend_single(stock, stock_df, exrights_df):
    """计算单只股票的累计未来分红(joblib worker)

    ptrade前复权逻辑: 前复权价 = 未复权价 - 累计未来分红
    对于日期d，累计未来分红 = 所有严格在d之后发生的分红之和

    Args:
        stock: 股票代码
        stock_df: 股票价格数据
        exrights_df: 除权数据

    Returns:
        cumulative_dividend_series 或 None
    """
    if stock_df is None or stock_df.empty:
        return None

    if exrights_df is None or exrights_df.empty:
        return None

    all_dates = stock_df.index

    try:
        if 'bonus_ps' not in exrights_df.columns:
            return None

        # 筛选有分红的记录
        dividend_mask = exrights_df['bonus_ps'] > 0
        if not dividend_mask.any():
            return None

        # 将除权日期转换为datetime
        dividend_records = exrights_df[dividend_mask]['bonus_ps']
        ex_dates_int = dividend_records.index.tolist()
        ex_dates_dt = pd.to_datetime(ex_dates_int, format='%Y%m%d')
        dividend_amounts = dividend_records.values

        # 对于每个交易日，计算其之后的累计分红
        # 使用向量化方式：对于日期d，累计未来分红 = sum(分红日期 > d 的分红)
        cumsum_future = pd.Series(index=all_dates, dtype='float64')

        for i, trade_date in enumerate(all_dates):
            # 计算trade_date之后的所有分红之和
            future_mask = ex_dates_dt > trade_date
            cumsum_future.iloc[i] = dividend_amounts[future_mask].sum()

        return cumsum_future
    except:
        return None


@timer(threshold=0.1, name="累计分红缓存创建")
def create_adj_pre_cache(data_context):
    """创建并保存所有股票的累计未来分红缓存(使用joblib并行)

    ptrade前复权逻辑: 前复权价 = 未复权价 - 累计未来分红
    """
    print("正在创建累计分红缓存...")

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
        delayed(_calculate_cumulative_dividend_single)(
            stock, stock_data_cache.get(stock), exrights_cache.get(stock)
        ) for stock in all_stocks
    )

    # 保存结果
    print("  正在保存到HDF5...")
    saved_count = 0
    with pd.HDFStore(ADJ_PRE_CACHE_PATH, 'w', complevel=9, complib='blosc') as store:
        for stock, cum_div in zip(all_stocks, results):
            if cum_div is not None:
                cum_div = cum_div.astype('float32')
                store.put(stock, cum_div, format='fixed')
                saved_count += 1

    print(f"✓ 累计分红缓存创建完成！")
    print(f"  处理: {total_stocks} 只股票")
    print(f"  保存: {saved_count} 只（有分红数据）")
    print(f"  文件: {ADJ_PRE_CACHE_PATH}")


@timer(threshold=0.1, name="累计分红缓存加载")
def load_adj_pre_cache(data_context):
    """加载累计分红缓存（支持多进程加速）

    返回的是累计未来分红，运行时用于计算前复权价格。
    前复权价 = 未复权价 - 累计未来分红
    """
    if not os.path.exists(ADJ_PRE_CACHE_PATH):
        create_adj_pre_cache(data_context)

    print("正在加载累计分红缓存...")

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

    print(f"✓ 累计分红缓存加载完成！共 {len(adj_factors_cache)} 只股票")
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
