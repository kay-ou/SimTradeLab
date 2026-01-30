# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
复权因子缓存模块 - 使用Parquet格式

前复权公式：前复权价 = (未复权价 - adj_b) / adj_a
后复权公式：后复权价 = adj_a * 未复权价 + adj_b
"""

import pandas as pd
import numpy as np
import os
from ..utils.paths import ADJ_PRE_CACHE_PATH, ADJ_POST_CACHE_PATH
from ..utils.perf import timer
from joblib import Parallel, delayed


def _calculate_adj_factors_from_events(stock, stock_df, exrights_events):
    """从除权除息事件计算前复权因子

    前复权公式: P_adj = (P - adj_b) / adj_a

    前复权的含义: 以最新价格为基准，调整历史价格使其连续可比
    - 最新的价格不变 (adj_a=1, adj_b=0)
    - 越往过去，调整幅度越大

    除权除息调整规则（从最新往历史回推）：
    每遇到一个除权日，该日期之前的价格需要调整:
    - adj_a[旧] = adj_a[新] × (1 + allotted_ps + rationed_ps)
    - adj_b[旧] = adj_b[新] × (1 + allotted_ps + rationed_ps) + bonus_ps - rationed_ps × rationed_px
    """
    if stock_df is None or stock_df.empty:
        return None

    if exrights_events is None or exrights_events.empty:
        adj_factors = pd.DataFrame(
            index=stock_df.index, columns=["adj_a", "adj_b"], dtype="float64"
        )
        adj_factors["adj_a"] = 1.0
        adj_factors["adj_b"] = 0.0
        return adj_factors

    try:
        ex_dates_int = exrights_events.index.tolist()
        ex_dates_dt = pd.to_datetime(ex_dates_int, format="%Y%m%d")

        # 获取除权除息数据
        allotted_ps = exrights_events["allotted_ps"].values  # 送转股比例
        bonus_ps = exrights_events["bonus_ps"].values  # 现金分红(元/股)
        rationed_ps = exrights_events["rationed_ps"].values  # 配股比例
        rationed_px = exrights_events["rationed_px"].values  # 配股价格

        # 计算每个除权日之后的前复权因子
        n_events = len(allotted_ps)
        forward_a_array = np.ones(n_events + 1, dtype="float64")
        forward_b_array = np.zeros(n_events + 1, dtype="float64")

        # 最新时刻(index=n_events): 不调整
        forward_a_array[n_events] = 1.0
        forward_b_array[n_events] = 0.0

        # 从最新往历史回推计算前复权因子
        for i in range(n_events - 1, -1, -1):
            total_ratio = allotted_ps[i] + rationed_ps[i]
            multiplier = 1.0 + total_ratio

            forward_a_array[i] = forward_a_array[i + 1] * multiplier
            forward_b_array[i] = (
                forward_b_array[i + 1] * multiplier
                + bonus_ps[i]
                - rationed_ps[i] * rationed_px[i]
            )

        # 向量化操作
        trade_dates_np = stock_df.index.values
        ex_dates_np = ex_dates_dt.values
        factor_indices = np.searchsorted(ex_dates_np, trade_dates_np, side="right")

        adj_a_array = forward_a_array[factor_indices]
        adj_b_array = forward_b_array[factor_indices]

        adj_factors = pd.DataFrame(
            index=stock_df.index,
            data={
                "adj_a": adj_a_array.astype("float64"),
                "adj_b": adj_b_array.astype("float64"),
            },
        )

        return adj_factors

    except (ValueError, KeyError, IndexError, pd.errors.EmptyDataError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("计算 {} 前复权因子失败: {}".format(stock, e))
        return None
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error("计算 {} 前复权因子失败: {}".format(stock, e))
        logger.debug(traceback.format_exc())
        return None


def _adj_cache_to_parquet(adj_factors_cache, cache_path):
    """将复权因子缓存保存为Parquet格式

    将 dict[str, DataFrame] 转为单个长表格式存储
    """
    if not adj_factors_cache:
        return

    rows = []
    for stock, df in adj_factors_cache.items():
        if df is not None and not df.empty:
            df_copy = df.reset_index()
            df_copy['symbol'] = stock
            rows.append(df_copy)

    if rows:
        combined = pd.concat(rows, ignore_index=True)
        combined.to_parquet(cache_path, index=False)


def _parquet_to_adj_cache(cache_path):
    """从Parquet格式加载复权因子缓存

    Returns:
        dict[str, DataFrame]: {stock: adj_factors_df}
    """
    if not os.path.exists(cache_path):
        return None

    combined = pd.read_parquet(cache_path)
    adj_factors_cache = {}

    for symbol, group in combined.groupby('symbol'):
        df = group.drop(columns=['symbol']).copy()
        if 'date' in df.columns:
            df.set_index('date', inplace=True)
        elif 'index' in df.columns:
            df.set_index('index', inplace=True)
        adj_factors_cache[symbol] = df

    return adj_factors_cache


@timer(threshold=0.1, name="前复权因子缓存创建")
def create_adj_pre_cache(data_context):
    """创建并保存所有股票的前复权因子缓存"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info("正在创建前复权因子缓存...")
    all_stocks = list(data_context.stock_data_dict.keys())
    total_stocks = len(all_stocks)

    logger.info("  预加载股票价格数据...")
    stock_data_cache = {s: data_context.stock_data_dict.get(s) for s in all_stocks}

    logger.info("  加载除权事件数据...")
    from . import storage
    data_dir = data_context.stock_data_dict.data_dir
    num_workers = int(os.getenv("PTRADE_NUM_WORKERS", "-1"))

    try:
        exrights_results = Parallel(n_jobs=num_workers, backend="loky", verbose=0)(
            delayed(storage.load_exrights)(data_dir, stock) for stock in all_stocks
        )

        exrights_cache = {}
        for stock, exrights_full in zip(all_stocks, exrights_results):
            if exrights_full and "exrights_events" in exrights_full:
                ex_df = exrights_full["exrights_events"]
                if not ex_df.empty:
                    exrights_cache[stock] = ex_df

        logger.info("    已加载 {} 只股票的除权数据".format(len(exrights_cache)))

        logger.info("  并行计算前复权因子({} 进程)...".format(
            num_workers if num_workers > 0 else "auto"
        ))

        results = Parallel(n_jobs=num_workers, backend="loky", verbose=0)(
            delayed(_calculate_adj_factors_from_events)(
                stock, stock_data_cache.get(stock), exrights_cache.get(stock)
            )
            for stock in all_stocks
        )

        logger.info("  正在保存到Parquet文件...")
        adj_factors_cache = {}
        saved_count = 0
        failed_stocks = []

        for stock, adj_factors in zip(all_stocks, results):
            if adj_factors is not None:
                adj_factors_cache[stock] = adj_factors
                saved_count += 1
            else:
                failed_stocks.append(stock)

        os.makedirs(os.path.dirname(ADJ_PRE_CACHE_PATH), exist_ok=True)
        _adj_cache_to_parquet(adj_factors_cache, ADJ_PRE_CACHE_PATH)

        file_size = os.path.getsize(ADJ_PRE_CACHE_PATH) / 1024 / 1024

        logger.info("✓ 前复权因子缓存创建完成！")
        logger.info("  处理: {} 只股票".format(total_stocks))
        logger.info("  保存: {} 只（有除权数据或价格数据）".format(saved_count))
        if failed_stocks:
            logger.warning("  失败股票: {} 只".format(len(failed_stocks)))
        logger.info("  文件: {} ({:.1f}MB)".format(ADJ_PRE_CACHE_PATH, file_size))

    except OSError as e:
        logger.error("创建前复权因子缓存失败: {}".format(e))
        raise
    except Exception as e:
        logger.error("创建前复权因子缓存时发生未预期错误: {}".format(e))
        import traceback
        logger.debug(traceback.format_exc())
        raise


@timer(threshold=0.1, name="前复权因子缓存加载")
def load_adj_pre_cache(data_context):
    """加载前复权因子缓存

    前复权价 = (未复权价 - adj_b) / adj_a
    """
    import logging
    logger = logging.getLogger(__name__)

    if not os.path.exists(ADJ_PRE_CACHE_PATH):
        try:
            create_adj_pre_cache(data_context)
        except Exception as e:
            logger.error("创建前复权因子缓存失败: {}".format(e))
            raise

    logger.info("正在加载前复权因子缓存...")

    try:
        adj_factors_cache = _parquet_to_adj_cache(ADJ_PRE_CACHE_PATH)

        if adj_factors_cache is None:
            raise FileNotFoundError("缓存文件为空")

        logger.info("✓ 前复权因子缓存加载完成！共 {} 只股票".format(len(adj_factors_cache)))
        return adj_factors_cache

    except FileNotFoundError:
        logger.error("缓存文件不存在: {}".format(ADJ_PRE_CACHE_PATH))
        create_adj_pre_cache(data_context)
        return load_adj_pre_cache(data_context)
    except Exception as e:
        logger.error("缓存文件损坏或格式错误: {}".format(e))
        try:
            os.remove(ADJ_PRE_CACHE_PATH)
            logger.info("已删除损坏的缓存文件，重新创建...")
            create_adj_pre_cache(data_context)
            return load_adj_pre_cache(data_context)
        except OSError as remove_error:
            logger.error("删除损坏的缓存文件失败: {}".format(remove_error))
            raise


def _calculate_adj_post_factors_from_events(stock, stock_df, exrights_events):
    """从除权除息事件计算后复权因子

    后复权公式: P_adj = adj_a * P + adj_b

    后复权的含义: 以上市首日为基准，调整后续价格使其连续可比
    - 上市首日不调整 (adj_a=1, adj_b=0)
    - 越往最新，调整幅度越大
    """
    if stock_df is None or stock_df.empty:
        return None

    if exrights_events is None or exrights_events.empty:
        adj_factors = pd.DataFrame(
            index=stock_df.index, columns=["adj_a", "adj_b"], dtype="float64"
        )
        adj_factors["adj_a"] = 1.0
        adj_factors["adj_b"] = 0.0
        return adj_factors

    try:
        ex_dates_int = exrights_events.index.tolist()
        ex_dates_dt = pd.to_datetime(ex_dates_int, format="%Y%m%d")

        allotted_ps = exrights_events["allotted_ps"].values
        bonus_ps = exrights_events["bonus_ps"].values
        rationed_ps = exrights_events["rationed_ps"].values
        rationed_px = exrights_events["rationed_px"].values

        n_events = len(allotted_ps)
        backward_a_array = np.ones(n_events + 1, dtype="float64")
        backward_b_array = np.zeros(n_events + 1, dtype="float64")

        # 从历史往最新推进计算后复权因子
        for i in range(n_events):
            total_ratio = allotted_ps[i] + rationed_ps[i]
            multiplier = 1.0 + total_ratio

            backward_a_array[i + 1] = backward_a_array[i] * multiplier
            backward_b_array[i + 1] = (
                backward_b_array[i] * multiplier
                + bonus_ps[i]
                - rationed_ps[i] * rationed_px[i]
            )

        trade_dates_np = stock_df.index.values
        ex_dates_np = ex_dates_dt.values
        factor_indices = np.searchsorted(ex_dates_np, trade_dates_np, side="right")

        adj_a_array = backward_a_array[factor_indices]
        adj_b_array = backward_b_array[factor_indices]

        adj_factors = pd.DataFrame(
            index=stock_df.index,
            data={
                "adj_a": adj_a_array.astype("float64"),
                "adj_b": adj_b_array.astype("float64"),
            },
        )

        return adj_factors

    except (ValueError, KeyError, IndexError, pd.errors.EmptyDataError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("计算 {} 后复权因子失败: {}".format(stock, e))
        return None
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error("计算 {} 后复权因子失败: {}".format(stock, e))
        logger.debug(traceback.format_exc())
        return None


@timer(threshold=0.1, name="后复权因子缓存创建")
def create_adj_post_cache(data_context):
    """创建并保存所有股票的后复权因子缓存"""
    import logging
    logger = logging.getLogger(__name__)

    logger.info("正在创建后复权因子缓存...")
    all_stocks = list(data_context.stock_data_dict.keys())
    total_stocks = len(all_stocks)

    logger.info("  预加载股票价格数据...")
    stock_data_cache = {s: data_context.stock_data_dict.get(s) for s in all_stocks}

    logger.info("  加载除权事件数据...")
    from . import storage
    data_dir = data_context.stock_data_dict.data_dir
    num_workers = int(os.getenv("PTRADE_NUM_WORKERS", "-1"))

    try:
        exrights_results = Parallel(n_jobs=num_workers, backend="loky", verbose=0)(
            delayed(storage.load_exrights)(data_dir, stock) for stock in all_stocks
        )

        exrights_cache = {}
        for stock, exrights_full in zip(all_stocks, exrights_results):
            if exrights_full and "exrights_events" in exrights_full:
                ex_df = exrights_full["exrights_events"]
                if not ex_df.empty:
                    exrights_cache[stock] = ex_df

        logger.info("    已加载 {} 只股票的除权数据".format(len(exrights_cache)))

        logger.info("  并行计算后复权因子({} 进程)...".format(
            num_workers if num_workers > 0 else "auto"
        ))

        results = Parallel(n_jobs=num_workers, backend="loky", verbose=0)(
            delayed(_calculate_adj_post_factors_from_events)(
                stock, stock_data_cache.get(stock), exrights_cache.get(stock)
            )
            for stock in all_stocks
        )

        logger.info("  正在保存到Parquet文件...")
        adj_factors_cache = {}
        saved_count = 0
        failed_stocks = []

        for stock, adj_factors in zip(all_stocks, results):
            if adj_factors is not None:
                adj_factors_cache[stock] = adj_factors
                saved_count += 1
            else:
                failed_stocks.append(stock)

        os.makedirs(os.path.dirname(ADJ_POST_CACHE_PATH), exist_ok=True)
        _adj_cache_to_parquet(adj_factors_cache, ADJ_POST_CACHE_PATH)

        file_size = os.path.getsize(ADJ_POST_CACHE_PATH) / 1024 / 1024

        logger.info("✓ 后复权因子缓存创建完成！")
        logger.info("  处理: {} 只股票".format(total_stocks))
        logger.info("  保存: {} 只（有除权数据或价格数据）".format(saved_count))
        if failed_stocks:
            logger.warning("  失败股票: {} 只".format(len(failed_stocks)))
        logger.info("  文件: {} ({:.1f}MB)".format(ADJ_POST_CACHE_PATH, file_size))

    except OSError as e:
        logger.error("创建后复权因子缓存失败: {}".format(e))
        raise
    except Exception as e:
        logger.error("创建后复权因子缓存时发生未预期错误: {}".format(e))
        import traceback
        logger.debug(traceback.format_exc())
        raise


@timer(threshold=0.1, name="后复权因子缓存加载")
def load_adj_post_cache(data_context):
    """加载后复权因子缓存

    后复权价 = adj_a * 未复权价 + adj_b
    """
    import logging
    logger = logging.getLogger(__name__)

    if not os.path.exists(ADJ_POST_CACHE_PATH):
        try:
            create_adj_post_cache(data_context)
        except Exception as e:
            logger.error("创建后复权因子缓存失败: {}".format(e))
            raise

    logger.info("正在加载后复权因子缓存...")

    try:
        adj_factors_cache = _parquet_to_adj_cache(ADJ_POST_CACHE_PATH)

        if adj_factors_cache is None:
            raise FileNotFoundError("缓存文件为空")

        logger.info("✓ 后复权因子缓存加载完成！共 {} 只股票".format(len(adj_factors_cache)))
        return adj_factors_cache

    except FileNotFoundError:
        logger.error("缓存文件不存在: {}".format(ADJ_POST_CACHE_PATH))
        create_adj_post_cache(data_context)
        return load_adj_post_cache(data_context)
    except Exception as e:
        logger.error("缓存文件损坏或格式错误: {}".format(e))
        try:
            os.remove(ADJ_POST_CACHE_PATH)
            logger.info("已删除损坏的缓存文件，重新创建...")
            create_adj_post_cache(data_context)
            return load_adj_post_cache(data_context)
        except OSError as remove_error:
            logger.error("删除损坏的缓存文件失败: {}".format(remove_error))
            raise


def create_dividend_cache(data_context):
    """按需加载分红数据

    返回: DividendLazyLoader对象，支持按需加载
    """
    return DividendLazyLoader(data_context.stock_data_dict.data_dir)


class DividendLazyLoader:
    """延迟加载分红数据 - 按股票代码按需加载"""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self._cache = {}

    def get(self, stock_code, default=None):
        """获取指定股票的分红数据"""
        if stock_code in self._cache:
            return self._cache[stock_code]

        from . import storage
        exrights_data = storage.load_exrights(self.data_dir, stock_code)

        if not exrights_data or "dividends" not in exrights_data:
            self._cache[stock_code] = default
            return default

        dividends_list = exrights_data["dividends"]
        if not dividends_list:
            self._cache[stock_code] = default
            return default

        result = {}
        for event in dividends_list:
            date_str = event["date"].replace("-", "")
            dividend = event["dividend"]
            if dividend > 0:
                result[date_str] = dividend

        self._cache[stock_code] = result if result else default
        return self._cache[stock_code]

    def __contains__(self, stock_code):
        return self.get(stock_code) is not None

    def __getitem__(self, stock_code):
        result = self.get(stock_code)
        if result is None:
            raise KeyError(stock_code)
        return result
