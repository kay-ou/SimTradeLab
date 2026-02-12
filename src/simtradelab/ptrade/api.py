# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
ptrade API 模拟层

模拟ptrade平台的所有API函数，用于本地回测

"""

from __future__ import annotations

import numpy as np
import pandas as pd
import json
import bisect
import traceback
from functools import wraps
from typing import Optional, Any, Callable

from .lifecycle_controller import PTradeLifecycleError
from .lifecycle_config import API_ALLOWED_PHASES_LOOKUP, _ALL_PHASES_FROZENSET
from ..utils.paths import get_project_root
from simtradelab.ptrade.object import Position
from .order_processor import OrderProcessor
from .cache_manager import cache_manager
from cachetools import LRUCache
from .config_manager import config
from simtradelab.utils.perf import timer


def _round2(values: np.ndarray) -> np.ndarray:
    """Round to 2 decimal places matching Ptrade behavior.

    np.round(x, 2) internally computes rint(x * 100) / 100. The multiplication
    can shift values exactly onto a .5 boundary (e.g. 22.735 * 100 = 2273.5
    exactly), causing banker's rounding to round UP when the original float
    was actually below x.xx5 (22.7349999...).

    Ptrade uses Python float rounding semantics which respect the true float64
    representation, so 22.7349... rounds DOWN to 22.73.
    """
    return np.array([round(float(v), 2) for v in values])


def validate_lifecycle(func: Callable) -> Callable:
    """生命周期验证装饰器

    优化策略:
    - all-phase API (get_history, get_price 等) 直接返回原函数，零包装开销
    - 受限 API 只做 frozenset in 检查，无 RLock / Pydantic 对象
    """
    api_name = func.__name__
    allowed_phases = API_ALLOWED_PHASES_LOOKUP.get(api_name, _ALL_PHASES_FROZENSET)

    # all-phase API: 直接返回原函数，无任何包装
    if allowed_phases is _ALL_PHASES_FROZENSET:
        return func

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        controller = self.context._lifecycle_controller if self.context else None
        if controller and controller._current_phase:
            if controller._current_phase.value not in allowed_phases:
                raise PTradeLifecycleError(
                    f"API '{api_name}' cannot be called in phase "
                    f"'{controller._current_phase.value}'. Allowed: {allowed_phases}"
                )
        return func(self, *args, **kwargs)
    return wrapper


class PtradeAPI:
    """ptrade API模拟器（面向对象封装）"""

    def __init__(self, data_context: Any, context: Any, log: Any) -> None:
        """初始化API模拟器

        Args:
            data_context: DataContext数据上下文对象
            context: Context上下文对象
            log: 日志对象
        """
        self.data_context = data_context
        self.context = context
        self.log = log

        # 股票池管理
        self.active_universe: set = set()

        # 订单处理器（延迟初始化）
        self._order_processor: Optional[OrderProcessor] = None

        # 缓存 - 使用统一缓存管理器
        self._stock_status_cache = LRUCache(maxsize=50000)
        self._stock_date_index: dict[str, tuple[dict, list]] = {}
        self._prebuilt_index: bool = False
        self._sorted_status_dates: Optional[list[str]] = None
        self._daily_tasks: list[tuple[Callable, str]] = []  # (func, time_str)
        self._history_cache: dict = cache_manager.get_namespace('history')._cache  # 使用LRUCache
        self._fundamentals_cache = LRUCache(maxsize=500)

    @property
    def order_processor(self) -> OrderProcessor:
        """获取订单处理器（延迟初始化）"""
        if self._order_processor is None:
            self._order_processor = OrderProcessor(
                self.context, self.data_context,
                self.get_stock_date_index, self.log
            )
        return self._order_processor

    def prebuild_date_index(self, stocks: Optional[list[str]] = None) -> None:
        """预构建股票日期索引（显著提升性能）"""
        if self._prebuilt_index:
            return

        target_stocks = stocks if stocks else list(self.data_context.stock_data_dict.keys())
        print(f"预构建 {len(target_stocks)} 只股票的日期索引...")

        for i, stock in enumerate(target_stocks):
            if (i + 1) % 1000 == 0:
                print(f"  已构建 {i + 1}/{len(target_stocks)}")
            try:
                stock_df = self.data_context.stock_data_dict[stock]
                if isinstance(stock_df, pd.DataFrame) and isinstance(stock_df.index, pd.DatetimeIndex):
                    date_dict = {date: idx for idx, date in enumerate(stock_df.index)}
                    sorted_dates = list(stock_df.index)
                    self._stock_date_index[stock] = (date_dict, sorted_dates)
            except Exception:
                pass

        self._prebuilt_index = True
        print(f"  完成！已构建 {len(self._stock_date_index)} 只股票的索引")

    def get_stock_date_index(self, stock: str) -> tuple[dict, 'np.ndarray']:
        """获取股票日期索引，返回 (date_dict, sorted_i8) 元组

        date_dict: {int64_nanoseconds: row_index} — 用 ts.value 查找
        sorted_i8: numpy int64 数组 — 用 .searchsorted(ts.value) 做二分查找
        """
        if stock not in self._stock_date_index:
            stock_df = None
            if stock in self.data_context.stock_data_dict:
                stock_df = self.data_context.stock_data_dict[stock]
            elif stock in self.data_context.benchmark_data:
                stock_df = self.data_context.benchmark_data[stock]

            if stock_df is not None and isinstance(stock_df, pd.DataFrame) and isinstance(stock_df.index, pd.DatetimeIndex):
                # int64 nanoseconds 作为 dict key，避免 pd.Timestamp 构造开销
                idx_i8 = stock_df.index.values.view('i8')
                date_dict = dict(zip(idx_i8.tolist(), range(len(idx_i8))))
                self._stock_date_index[stock] = (date_dict, idx_i8)
            else:
                self._stock_date_index[stock] = ({}, np.array([], dtype='i8'))
        return self._stock_date_index[stock]

    def _apply_adj_factors(self, stock_df: pd.DataFrame, stock: str, fq: str) -> pd.DataFrame:
        """对DataFrame应用复权因子（向量化）

        Args:
            stock_df: 股票数据DataFrame
            stock: 股票代码
            fq: 复权类型 ('pre'前复权, 'post'后复权)

        Returns:
            复权后的DataFrame（copy），无复权因子时返回原DataFrame
        """
        if fq == 'pre':
            adj_cache = self.data_context.adj_pre_cache
        elif fq == 'post':
            adj_cache = self.data_context.adj_post_cache
        else:
            return stock_df

        if not adj_cache or stock not in adj_cache:
            return stock_df

        adj_factors = adj_cache[stock]
        common_idx = stock_df.index.intersection(adj_factors.index)
        if len(common_idx) == 0:
            return stock_df

        adjusted_df = stock_df.copy()
        adj_a = adj_factors.loc[common_idx, 'adj_a']
        adj_b = adj_factors.loc[common_idx, 'adj_b']
        price_cols = ['open', 'high', 'low', 'close']

        for col in price_cols:
            if col not in adjusted_df.columns:
                continue
            if fq == 'pre':
                # 前复权: (未复权价 - adj_b) / adj_a
                adjusted_df.loc[common_idx, col] = (
                    (adjusted_df.loc[common_idx, col] - adj_b) / adj_a
                )
            else:
                # 后复权: adj_a * 未复权价 + adj_b
                adjusted_df.loc[common_idx, col] = (
                    adj_a * adjusted_df.loc[common_idx, col] + adj_b
                )

        return adjusted_df

    # ==================== 基础API ====================

    def get_research_path(self) -> str:
        """返回研究目录路径"""
        return str(get_project_root()) + '/research/'

    def get_Ashares(self, date: str = None) -> list[str]:
        """返回A股代码列表，支持历史查询"""
        if date is None:
            target_date = self.context.current_dt
        else:
            target_date = pd.Timestamp(date)

        if self.data_context.stock_metadata.empty:
            return list(self.data_context.stock_data_dict.keys())

        # 使用预解析的 Timestamp 列（避免每次调用都解析日期字符串）
        if self.data_context.listed_date_ts is not None:
            listed = self.data_context.listed_date_ts <= target_date
        else:
            listed = pd.to_datetime(self.data_context.stock_metadata['listed_date'], format='mixed') <= target_date

        if self.data_context.de_listed_date_ts is not None:
            not_delisted = (
                (self.data_context.stock_metadata['de_listed_date'] == '2900-01-01') |
                (self.data_context.de_listed_date_ts > target_date)
            )
        else:
            not_delisted = (
                (self.data_context.stock_metadata['de_listed_date'] == '2900-01-01') |
                (pd.to_datetime(self.data_context.stock_metadata['de_listed_date'], errors='coerce', format='mixed') > target_date)
            )

        return self.data_context.stock_metadata[listed & not_delisted].index.tolist()

    def get_trade_days(self, start_date: str = None, end_date: str = None, count: int = None) -> list[str]:
        """获取指定范围交易日列表

        Args:
            start_date: 开始日期（与count二选一）
            end_date: 结束日期（默认当前回测日期）
            count: 往前count个交易日（与start_date二选一）
        """
        if self.data_context.trade_days is None:
            raise RuntimeError("交易日历数据未加载")
        all_trade_days = self.data_context.trade_days

        if end_date is None:
            end_dt = self.context.current_dt
        else:
            end_dt = pd.Timestamp(end_date)

        if count is not None:
            if start_date is not None:
                raise ValueError("start_date和count不能同时使用")
            # 找到end_date的位置
            valid_days = all_trade_days[all_trade_days <= end_dt]
            if len(valid_days) == 0:
                return []
            # 往前取count个交易日（包含end_date）
            trade_days = valid_days[-count:]
        else:
            # 使用start_date和end_date范围
            trade_days = all_trade_days[all_trade_days <= end_dt]
            if start_date is not None:
                start_dt = pd.Timestamp(start_date)
                trade_days = trade_days[trade_days >= start_dt]

        return [d.strftime('%Y-%m-%d') for d in trade_days]

    def get_all_trades_days(self, date: str = None) -> list[str]:
        """获取某日期之前的所有交易日列表

        Args:
            date: 截止日期（默认当前回测日期）
        """
        return self.get_trade_days(end_date=date)

    def get_trading_day(self, day: int = 0) -> Optional[str]:
        """获取当前时间数天前或数天后的交易日期

        Args:
            day: 偏移天数（正数向后，负数向前，0表示当天或上一交易日，默认0）

        Returns:
            交易日期字符串，如 '2024-01-15'
        """
        base_date = self.context.current_dt

        # 优先使用独立的交易日历数据
        if hasattr(self.data_context, 'trade_days') and self.data_context.trade_days is not None:
            all_trade_days = self.data_context.trade_days
        elif '000300.SS' in self.data_context.benchmark_data:
            # 回退：从 benchmark_data 获取
            all_trade_days = self.data_context.benchmark_data['000300.SS'].index
        else:
            raise RuntimeError("交易日历数据未加载")

        if base_date in all_trade_days:
            base_idx = all_trade_days.get_loc(base_date)
        else:
            valid_days = all_trade_days[all_trade_days <= base_date]
            if len(valid_days) == 0:
                base_idx = 0
            else:
                base_idx = all_trade_days.get_loc(valid_days[-1])

        target_idx = base_idx + day

        if target_idx < 0 or target_idx >= len(all_trade_days):
            return None

        return all_trade_days[target_idx].strftime('%Y-%m-%d')

    # ==================== 基本面API ====================

    # 定义字段所属表的映射
    FUNDAMENTAL_TABLES = {
        'valuation': ['pe_ttm', 'pb', 'ps_ttm', 'pcf', 'total_value', 'float_value'],
        'profit_ability': ['roe', 'roa', 'gross_income_ratio', 'net_profit_ratio',
                           'roe_ttm', 'roa_ttm', 'gross_income_ratio_ttm', 'net_profit_ratio_ttm'],
        'growth_ability': ['operating_revenue_grow_rate', 'net_profit_grow_rate',
                           'total_asset_grow_rate', 'basic_eps_yoy', 'np_parent_company_yoy'],
        'operating_ability': ['total_asset_turnover_rate', 'current_assets_turnover_rate',
                              'accounts_receivables_turnover_rate', 'inventory_turnover_rate', 'turnover_rate'],
        'debt_paying_ability': ['current_ratio', 'quick_ratio', 'debt_equity_ratio',
                                'interest_cover', 'roic', 'roa_ebit_ttm'],
    }

    @timer()
    def get_fundamentals(self, security: str | list[str], table: str, fields: list[str], date: str = None) -> pd.DataFrame:
        """获取基本面数据（优化版：增量缓存）

        重要：对于fundamentals表，使用publ_date（公告日期）进行过滤，而非end_date（报告期）
        这样可以避免未来函数（look-ahead bias）

        Args:
            security: 股票代码或股票代码列表
            table: 表名
            fields: 字段列表
            date: 查询日期（默认为回测当前日期）
        """
        # 统一处理：将单个股票代码转换为列表
        if isinstance(security, str):
            stocks = [security]
        else:
            stocks = security

        if table == 'valuation':
            data_dict = self.data_context.valuation_dict
        else:
            if table not in self.FUNDAMENTAL_TABLES:
                raise ValueError(f"Invalid table: {table}. Valid tables: {list(self.FUNDAMENTAL_TABLES.keys())}")

            valid_fields = self.FUNDAMENTAL_TABLES[table]
            for field in fields:
                if field not in valid_fields:
                    raise ValueError(f"Field '{field}' does not belong to table '{table}'. Valid fields: {valid_fields}")

            data_dict = self.data_context.fundamentals_dict

        # 如果未指定date，使用回测当前日期
        if date is None:
            query_ts = self.context.current_dt
        else:
            query_ts = pd.Timestamp(date)
        cache_key = (table, query_ts)

        # 获取或创建日期索引缓存（LRUCache 自动淘汰）
        if cache_key not in self._fundamentals_cache:
            self._fundamentals_cache[cache_key] = {}

        date_indices = self._fundamentals_cache[cache_key]

        # 只为缓存中不存在的股票计算索引（增量更新）
        stocks_to_index = [s for s in stocks if s not in date_indices and s in data_dict]

        if stocks_to_index:
            for stock in stocks_to_index:
                try:
                    df = data_dict[stock]
                    if df is None or len(df) == 0:
                        continue

                    # 对于fundamentals表，使用publ_date过滤
                    if table != 'valuation' and 'publ_date' in df.columns:
                        # 过滤出查询日期前已公告的财报（不修改原DataFrame）
                        publ_dates = pd.to_datetime(df['publ_date'], errors='coerce')
                        valid_mask = publ_dates <= query_ts
                        valid_indices = df.index[valid_mask]

                        if len(valid_indices) > 0:
                            # 选择最新的财报（最大的end_date）
                            latest_end_date = valid_indices.max()
                            idx = df.index.get_loc(latest_end_date)
                            date_indices[stock] = idx
                        else:
                            # 没有已公告的财报，跳过
                            continue
                    else:
                        # 对于valuation表，返回查询日当天数据
                        # side='right' 找到第一个 > query_ts 的位置，idx-1 即为 <= query_ts 的最新数据
                        idx = df.index.values.view('i8').searchsorted(query_ts.value, side='right')
                        if idx > 0:
                            date_indices[stock] = idx - 1
                        elif len(df.index) > 0:
                            date_indices[stock] = 0
                except Exception as e:
                    # 静默忽略错误，继续处理其他股票
                    continue

        result_data = {}

        # 对于valuation表的total_value/float_value，需要用查询日期的收盘价实时计算
        need_realtime_total_value = (table == 'valuation' and 'total_value' in fields)
        need_realtime_float_value = (table == 'valuation' and 'float_value' in fields)
        need_realtime_market_cap = need_realtime_total_value or need_realtime_float_value

        # 预先获取并缓存当天所查股票的收盘价
        close_prices = {}
        if need_realtime_market_cap:
            price_cache_key = ('_close_prices', query_ts)
            if price_cache_key in self._fundamentals_cache:
                close_prices = self._fundamentals_cache[price_cache_key]
            else:
                close_prices = {}
                self._fundamentals_cache[price_cache_key] = close_prices
            # 增量补充：只获取尚未缓存的股票收盘价
            for stock in stocks:
                if stock in close_prices:
                    continue
                stock_df = self.data_context.stock_data_dict.get(stock)
                if stock_df is not None and isinstance(stock_df, pd.DataFrame) and not stock_df.empty:
                    idx = stock_df.index.values.view('i8').searchsorted(query_ts.value, side='right')
                    if idx > 0:
                        close_prices[stock] = stock_df['close'].values[idx - 1]

        for stock in stocks:
            if stock not in date_indices:
                continue

            try:
                df = data_dict[stock]
                if df is None or len(df) == 0:
                    continue

                idx = date_indices[stock]

                stock_data = {}
                for field in fields:
                    if field == 'total_value' and need_realtime_total_value:
                        col_idx = df.columns.get_loc('total_shares') if 'total_shares' in df.columns else -1
                        total_shares = df.iat[idx, col_idx] if col_idx >= 0 else None
                        if total_shares is not None and not pd.isna(total_shares) and stock in close_prices:
                            stock_data[field] = close_prices[stock] * total_shares
                        elif field in df.columns:
                            stock_data[field] = df[field].values[idx]
                    elif field == 'float_value' and need_realtime_float_value:
                        col_idx = df.columns.get_loc('a_floats') if 'a_floats' in df.columns else -1
                        a_floats = df.iat[idx, col_idx] if col_idx >= 0 else None
                        if a_floats is not None and not pd.isna(a_floats) and stock in close_prices:
                            stock_data[field] = close_prices[stock] * a_floats
                        elif field in df.columns:
                            stock_data[field] = df[field].values[idx]
                    elif field in df.columns:
                        stock_data[field] = df[field].values[idx]

                if stock_data:
                    result_data[stock] = stock_data

            except Exception as e:
                print(f"读取{table}数据失败: stock={stock}, fields={fields}, error={e}")
                traceback.print_exc()
                raise

        return pd.DataFrame.from_dict(result_data, orient='index') if result_data else pd.DataFrame()

    # ==================== 行情API ====================

    class PanelLike(dict):
        """模拟pandas.Panel"""
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self._stock_list: Optional[list[str]] = None

        def __getitem__(self, key: str) -> pd.DataFrame | Any:
            if key in self:
                return super().__getitem__(key)

            if self._stock_list is None and self:
                first_df = next(iter(self.values()))
                self._stock_list = list(first_df.columns)

            if self._stock_list and key in self._stock_list:
                stock_data = {}
                for field, df in self.items():
                    if key in df.columns:
                        stock_data[field] = df[key]
                return pd.DataFrame(stock_data)

            raise KeyError(key)

        @property
        def empty(self) -> bool:
            if not self:
                return True
            return all(df.empty for df in self.values())

        @property
        def columns(self) -> pd.Index:
            if not self:
                return pd.Index([])
            first_df = next(iter(self.values()))
            return first_df.columns

    def _get_data_source(self, frequency: str):
        """根据frequency获取对应的数据源"""
        if frequency == '1m':
            if self.data_context.stock_data_dict_1m is None:
                raise ValueError("分钟数据未加载，请确保data/stocks_1m/目录存在分钟数据")
            return self.data_context.stock_data_dict_1m
        return self.data_context.stock_data_dict

    def get_price(self, security: str | list[str], start_date: str = None, end_date: str = None, frequency: str = '1d', fields: str | list[str] = None, fq: str = None, count: int = None) -> pd.DataFrame | PtradeAPI.PanelLike:
        """获取历史行情数据"""
        # 验证fq参数（get_price不支持dypre，仅get_history支持）
        valid_fq = ['pre', 'post', None]
        if fq not in valid_fq:
            raise ValueError(f"function get_price: invalid fq argument, valid: {valid_fq}, got {fq} (type: {type(fq)})")

        if isinstance(fields, str):
            fields_list = [fields]
        elif fields is None:
            fields_list = ['open', 'high', 'low', 'close', 'volume', 'money']
        else:
            fields_list = fields

        is_single_stock = isinstance(security, str)
        stocks = [security] if is_single_stock else security

        # 根据frequency选择数据源
        data_source = self._get_data_source(frequency)

        if count is not None:
            end_dt = pd.Timestamp(end_date) if end_date else self.context.current_dt
            result = {}
            for stock in stocks:
                if stock not in data_source:
                    continue

                stock_df = data_source[stock]
                if not isinstance(stock_df, pd.DataFrame):
                    continue

                try:
                    if frequency == '1m':
                        # 分钟数据：直接使用index查找
                        idx = stock_df.index.values.view('i8').searchsorted(end_dt.value, side='right') - 1
                        if idx < 0:
                            continue
                        current_idx = idx
                    else:
                        date_dict, _ = self.get_stock_date_index(stock)
                        current_idx = date_dict.get(end_dt.value)
                        if current_idx is None:
                            current_idx = stock_df.index.get_loc(end_dt)
                except (KeyError, IndexError):
                    continue

                # Ptrade API语义: count=N 返回截止到end_date的N条数据（包含end_date）
                slice_df = stock_df.iloc[max(0, current_idx - count + 1):current_idx + 1]
                result[stock] = slice_df
        else:
            start_dt = pd.Timestamp(start_date) if start_date else None
            end_dt = pd.Timestamp(end_date) if end_date else self.context.current_dt

            result = {}
            for stock in stocks:
                if stock not in data_source:
                    continue

                stock_df = data_source[stock]
                if not isinstance(stock_df, pd.DataFrame):
                    continue

                if start_dt:
                    mask = (stock_df.index >= start_dt) & (stock_df.index <= end_dt)
                else:
                    mask = stock_df.index <= end_dt

                slice_df = stock_df[mask]
                result[stock] = slice_df

        # 复权处理（仅日线数据支持）
        if frequency != '1m' and fq in ('pre', 'post'):
            for stock in list(result.keys()):
                stock_df = result[stock]
                if isinstance(stock_df, pd.DataFrame) and not stock_df.empty:
                    result[stock] = self._apply_adj_factors(stock_df, stock, fq)

        if not result:
            self.log.warning("get_price 返回空结果 | stocks=%s, frequency=%s, fq=%s", security, frequency, fq)
            return pd.DataFrame()

        if is_single_stock:
            stock_df = result.get(security)
            if stock_df is None:
                self.log.warning("get_price 单只股票无数据 | stock=%s, frequency=%s, fq=%s", security, frequency, fq)
                return pd.DataFrame()
            return stock_df[fields_list] if len(fields_list) > 0 else stock_df

        if len(fields_list) == 1:
            field_name = fields_list[0]
            data = {stock: stock_df[field_name] for stock, stock_df in result.items() if field_name in stock_df.columns}
            return pd.DataFrame(data) if data else pd.DataFrame()

        panel_data = {}
        for field_name in fields_list:
            data = {stock: stock_df[field_name] for stock, stock_df in result.items() if field_name in stock_df.columns}
            panel_data[field_name] = pd.DataFrame(data)

        return self.PanelLike(panel_data)

    @timer()
    def get_history(self, count: int, frequency: str = '1d', field: str | list[str] = 'close', security_list: str | list[str] = None, fq: str = None, include: bool = False, fill: str = 'nan', is_dict: bool = False) -> pd.DataFrame | dict | PtradeAPI.PanelLike:
        """模拟通用ptrade的get_history（优化批量处理+缓存）"""
        # 验证fq参数
        valid_fq = ['pre', 'post', 'dypre', None]
        if fq not in valid_fq:
            raise ValueError(f"function get_history: invalid fq argument, valid: {valid_fq}, got {fq} (type: {type(fq)})")

        if isinstance(field, str):
            fields = [field]
        else:
            fields = field if field else ['close']

        stocks = security_list if security_list else []
        if isinstance(stocks, str):
            stocks = [stocks]

        # 批量快速返回空结果
        if not stocks:
            return {} if is_dict else pd.DataFrame()

        current_dt = self.context.current_dt

        # 缓存键：frozenset 归一化顺序 O(n)，比 tuple(sorted()) O(n log n) 更快
        field_key = tuple(fields) if len(fields) > 1 else fields[0]
        cache_key = (frozenset(stocks), count, field_key, fq, current_dt, include, is_dict, frequency)

        # 检查缓存
        if cache_key in self._history_cache:
            return self._history_cache[cache_key]

        # 根据frequency选择数据源
        if frequency == '1m':
            stock_data_dict = self._get_data_source(frequency)
        else:
            stock_data_dict = self.data_context.stock_data_dict
        benchmark_data = self.data_context.benchmark_data

        # 优化1: 批量预加载股票数据（减少LazyDataDict的重复加载）
        stock_dfs = {}

        for stock in stocks:
            data_source = stock_data_dict.get(stock) if stock_data_dict else None
            if data_source is None and frequency != '1m':
                data_source = benchmark_data.get(stock)
            if data_source is not None:
                stock_dfs[stock] = data_source

        # 优化2: 批量获取索引位置
        stock_info = {}
        for stock, data_source in stock_dfs.items():
            if not isinstance(data_source, pd.DataFrame):
                continue
            try:
                if frequency == '1m':
                    # 分钟数据：使用searchsorted查找
                    idx = data_source.index.values.view('i8').searchsorted(current_dt.value, side='right') - 1
                    if idx < 0:
                        continue
                    current_idx = idx
                else:
                    date_dict, _ = self.get_stock_date_index(stock)
                    current_idx = date_dict.get(current_dt.value)
                    if current_idx is None:
                        current_idx = data_source.index.get_loc(current_dt)
                stock_info[stock] = (data_source, current_idx)
            except (KeyError, IndexError):
                continue

        # 优化3+4: 批量切片+复权（减少循环开销）
        result = {}
        # 分钟数据不支持复权
        needs_adj_pre = frequency != '1m' and fq == 'pre' and self.data_context.adj_pre_cache
        needs_adj_dypre = frequency != '1m' and fq == 'dypre' and self.data_context.adj_pre_cache
        needs_adj_post = frequency != '1m' and fq == 'post' and self.data_context.adj_post_cache
        price_fields = {'open', 'high', 'low', 'close'}  # 预先构建集合,提升查找速度

        for stock, (data_source, current_idx) in stock_info.items():
            if include:
                start_idx = max(0, current_idx - count + 1)
                end_idx = current_idx + 1
            else:
                start_idx = max(0, current_idx - count)
                end_idx = current_idx

                # 边界检查：如果end_idx == 0，无法获取历史数据，自动包含当前日
                if end_idx == 0 and current_idx == 0:
                    end_idx = 1

            # ── numpy 快路径：所有复权模式统一处理 ──
            # adj 因子与 stock_data_dict 同源生成，长度必然匹配
            adj_factors = None
            adj_a = adj_b = None

            if (needs_adj_pre or needs_adj_dypre) and stock in self.data_context.adj_pre_cache:
                adj_factors = self.data_context.adj_pre_cache[stock]
            elif needs_adj_post and stock in self.data_context.adj_post_cache:
                adj_factors = self.data_context.adj_post_cache[stock]

            if adj_factors is not None:
                adj_a = adj_factors['adj_a'].values[start_idx:end_idx]
                adj_b = adj_factors['adj_b'].values[start_idx:end_idx]

            # dypre 基准日因子（用 numpy 索引替代 pandas .loc）
            if needs_adj_dypre and adj_a is not None:
                adj_a_base = adj_factors['adj_a'].values[current_idx]
                adj_b_base = adj_factors['adj_b'].values[current_idx]

            stock_result = {}
            for field_name in fields:
                if field_name not in data_source.columns:
                    continue
                raw = data_source[field_name].values[start_idx:end_idx]

                if adj_a is not None and field_name in price_fields:
                    if needs_adj_post:
                        stock_result[field_name] = adj_a * raw + adj_b
                    elif needs_adj_dypre:
                        stock_result[field_name] = _round2((raw - adj_b) / adj_a) * adj_a_base + adj_b_base
                    else:
                        stock_result[field_name] = _round2((raw - adj_b) / adj_a)
                else:
                    stock_result[field_name] = raw

            if stock_result:
                result[stock] = stock_result

        # 转换为返回格式并缓存
        if not result:
            self.log.warning("get_history 返回空结果 | stocks=%s, count=%d, frequency=%s, fq=%s",
                           security_list, count, frequency, fq)
            final_result = {} if is_dict else pd.DataFrame()
        elif is_dict:
            # is_dict=True: 返回 {stock: {field: array}} 格式
            final_result = result
        else:
            is_single_stock = isinstance(security_list, str)
            stocks_list = [security_list] if is_single_stock else stocks

            if is_single_stock:
                if stocks_list[0] not in result:
                    final_result = pd.DataFrame()
                else:
                    df_data = {field_name: result[stocks_list[0]][field_name] for field_name in fields if field_name in result[stocks_list[0]]}
                    final_result = pd.DataFrame(df_data)

            elif len(fields) == 1:
                field_name = fields[0]
                df_data = {stock: result[stock][field_name] for stock in stocks_list if stock in result and field_name in result[stock]}
                final_result = pd.DataFrame(df_data)

            else:
                panel_data = {}
                for field_name in fields:
                    df_data = {stock: result[stock][field_name] for stock in stocks_list if stock in result and field_name in result[stock]}
                    panel_data[field_name] = pd.DataFrame(df_data)

                final_result = self.PanelLike(panel_data)

        # 缓存结果 (LRUCache自动管理大小)
        self._history_cache[cache_key] = final_result

        return final_result

    # ==================== 股票信息API ====================

    def get_stock_blocks(self, stock: str) -> dict:
        """获取股票所属板块"""
        if not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
            try:
                blocks_str = self.data_context.stock_metadata.loc[stock, 'blocks']
                if pd.notna(blocks_str) and blocks_str:
                    return json.loads(blocks_str)
            except (KeyError, json.JSONDecodeError):
                pass
        return {}

    def get_stock_info(self, stocks: str | list[str], field: str | list[str] = None) -> dict[str, dict]:
        """获取股票基础信息"""
        if isinstance(stocks, str):
            stocks = [stocks]

        if field is None:
            field = ['stock_name', 'listed_date', 'de_listed_date']
        elif isinstance(field, str):
            field = [field]

        result = {}
        for stock in stocks:
            stock_info = {}

            if not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                meta_row = self.data_context.stock_metadata.loc[stock]
                for f in field:
                    if f in meta_row.index:
                        stock_info[f] = meta_row[f]

            if 'stock_name' in field and 'stock_name' not in stock_info:
                stock_info['stock_name'] = stock
            if 'listed_date' in field and 'listed_date' not in stock_info:
                stock_info['listed_date'] = '2010-01-01'
            if 'de_listed_date' in field and 'de_listed_date' not in stock_info:
                stock_info['de_listed_date'] = '2900-01-01'

            result[stock] = stock_info

        return result

    def get_stock_name(self, stocks: str | list[str]) -> str | dict[str, str]:
        """获取股票名称"""
        is_single = isinstance(stocks, str)
        if is_single:
            stocks = [stocks]

        result = {}
        for stock in stocks:
            if not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                result[stock] = self.data_context.stock_metadata.loc[stock, 'stock_name']
            else:
                result[stock] = stock

        return result[stocks[0]] if is_single else result

    def get_stock_status(self, stocks: str | list[str], query_type: str = 'ST', query_date: str = None) -> dict[str, bool]:
        """获取股票状态（ST/HALT/DELISTING）

        基于日频 stock_status_history 数据，用 bisect 查找当日快照。
        """
        if isinstance(stocks, str):
            stocks = [stocks]

        if query_date is None:
            query_dt = self.context.current_dt if self.context else pd.Timestamp.now()
        else:
            query_dt = pd.Timestamp(query_date)

        dt_value = query_dt.value

        # 查找当日快照
        status_dict = None
        if self.data_context.stock_status_history:
            if self._sorted_status_dates is None:
                self._sorted_status_dates = sorted(self.data_context.stock_status_history.keys())
            query_date_str = query_dt.strftime('%Y%m%d')
            pos = bisect.bisect_right(self._sorted_status_dates, query_date_str)
            if pos > 0:
                history = self.data_context.stock_status_history[self._sorted_status_dates[pos - 1]]
                status_dict = history.get(query_type)

        result = {}
        for stock in stocks:
            cache_key = (dt_value, stock, query_type)
            cached = self._stock_status_cache.get(cache_key)
            if cached is not None:
                result[stock] = cached
                continue

            # 快照路径
            if status_dict is not None:
                is_match = status_dict.get(stock, False) is True
            # fallback: 无快照数据时用 volume=0 判停牌
            elif query_type == 'HALT':
                stock_df = self.data_context.stock_data_dict.get(stock)
                is_match = (stock_df is not None
                            and query_dt in stock_df.index
                            and stock_df.loc[query_dt, 'volume'] == 0)
            else:
                is_match = False

            self._stock_status_cache[cache_key] = is_match
            result[stock] = is_match

        return result

    def get_stock_exrights(self, stock_code: str, date: str = None) -> Optional[pd.DataFrame]:
        """获取股票除权除息信息"""
        exrights_df = self.data_context.exrights_dict.get(stock_code)
        if exrights_df is None or exrights_df.empty:
            return None

        if date is not None:
            query_date = pd.Timestamp(date)
            if query_date in exrights_df.index:
                return exrights_df.loc[[query_date]]
            return None

        return exrights_df

    # ==================== 指数/行业API ====================

    def get_index_stocks(self, index_code: str, date: str = None) -> list[str]:
        """获取指数成份股（支持向前回溯查找）"""
        if not self.data_context.index_constituents:
            return []

        # 缓存排序后的日期列表（避免每次调用重排序）
        if not hasattr(self, '_sorted_index_dates') or self._sorted_index_dates is None:
            self._sorted_index_dates = sorted(self.data_context.index_constituents.keys())
        available_dates = self._sorted_index_dates

        # 如果未指定日期，使用回测当前日期
        if date is None:
            query_date = self.context.current_dt.strftime('%Y%m%d')
        else:
            # 统一日期格式为YYYYMMDD
            query_date = date.replace('-', '')

        # 使用 bisect 找到小于等于 date 的最近日期
        idx = bisect.bisect_right(available_dates, query_date)

        if idx > 0:
            # 向前查找包含该指数数据的最近日期
            for i in range(idx - 1, -1, -1):
                nearest_date = available_dates[i]
                if index_code in self.data_context.index_constituents[nearest_date]:
                    result = self.data_context.index_constituents[nearest_date][index_code]
                    return list(result) if hasattr(result, '__iter__') else []

        return []

    def get_industry_stocks(self, industry_code: str = None) -> dict | list[str]:
        """推导行业成份股（带缓存）"""
        if self.data_context.stock_metadata.empty:
            return {} if industry_code is None else []

        # 使用 DataContext._industry_index 缓存
        if self.data_context._industry_index is None:
            industries = {}
            for stock_code, row in self.data_context.stock_metadata.iterrows():
                try:
                    blocks = json.loads(row['blocks'])
                    if 'HY' in blocks and blocks['HY']:
                        ind_code = blocks['HY'][0][0]
                        ind_name = blocks['HY'][0][1]

                        if ind_code not in industries:
                            industries[ind_code] = {
                                'name': ind_name,
                                'stocks': []
                            }
                        industries[ind_code]['stocks'].append(stock_code)
                except (KeyError, json.JSONDecodeError, IndexError, TypeError):
                    pass
            self.data_context._industry_index = industries

        if industry_code is None:
            return self.data_context._industry_index
        else:
            return self.data_context._industry_index.get(industry_code, {}).get('stocks', [])

    # ==================== 涨跌停API ====================

    def _get_price_limit_ratio(self, stock: str) -> float:
        """获取股票涨跌停幅度"""
        if stock.startswith('688') and stock.endswith('.SS'):
            return 0.20
        elif stock.startswith('30') and stock.endswith('.SZ'):
            return 0.20
        elif stock.endswith('.BJ'):
            return 0.30
        else:
            return 0.10

    def check_limit(self, security: str | list[str], query_date: str = None) -> dict[str, int]:
        """检查涨跌停状态"""
        if isinstance(security, str):
            securities = [security]
        else:
            securities = security

        if query_date is None:
            query_dt = self.context.current_dt if self.context else pd.Timestamp.now()
        else:
            query_dt = pd.Timestamp(query_date)

        result = {}
        for stock in securities:
            status = 0

            if stock not in self.data_context.stock_data_dict:
                result[stock] = status
                continue

            stock_df = self.data_context.stock_data_dict[stock]
            if not isinstance(stock_df, pd.DataFrame):
                result[stock] = status
                continue

            try:
                date_dict, _ = self.get_stock_date_index(stock)
                idx = date_dict.get(query_dt.value)
                if idx is None:
                    idx = stock_df.index.get_loc(query_dt)

                if idx == 0:
                    result[stock] = status
                    continue

                current_close = stock_df['close'].values[idx]
                current_high = stock_df['high'].values[idx]
                current_low = stock_df['low'].values[idx]
                prev_close = stock_df['close'].values[idx-1]

                if np.isnan(prev_close) or prev_close <= 0: # type: ignore
                    result[stock] = status
                    continue

                limit_ratio = self._get_price_limit_ratio(stock)
                limit_up_price = prev_close * (1 + limit_ratio)
                limit_down_price = prev_close * (1 - limit_ratio)

                # 回测中不能使用当天收盘价判断涨停（会产生未来数据泄露）
                # 只检查一字涨停（开盘=最高=最低=涨停价）
                current_open = stock_df['open'].values[idx]

                # 涨停判断：一字涨停（无法买入）
                is_one_word_up_limit = (
                    abs(current_open - limit_up_price) < 0.01 and
                    abs(current_high - limit_up_price) < 0.01 and
                    abs(current_low - limit_up_price) < 0.01
                )

                # 跌停判断：一字跌停（无法卖出）
                is_one_word_down_limit = (
                    abs(current_open - limit_down_price) < 0.01 and
                    abs(current_high - limit_down_price) < 0.01 and
                    abs(current_low - limit_down_price) < 0.01
                )

                if is_one_word_up_limit: # type: ignore
                    status = 1
                elif is_one_word_down_limit: # type: ignore
                    status = -1

                result[stock] = status
            except (KeyError, IndexError, ValueError):
                result[stock] = 0

        return result

    # ==================== 交易API ====================

    def _get_price_and_check_limit(self, security: str, limit_price: Optional[float], amount: int) -> Optional[float]:
        """获取执行价格并检查涨跌停。返回 price 或 None。"""
        is_buy = amount > 0
        price = self.order_processor.get_execution_price(security, limit_price, is_buy)
        if price is None:
            self.log.warning(f"订单失败 {security} | 原因: 无法获取价格")
            return None
        limit_status = self.check_limit(security, self.context.current_dt)[security]
        if not self.order_processor.check_limit_status(security, amount, limit_status):
            return None
        return price

    def _adjust_buy_amount(self, security: str, amount: int, price: float) -> Optional[int]:
        """买入时资金不足自动调整数量（Ptrade行为）。返回调整后的 amount 或 None。"""
        available_cash = self.context.portfolio._cash
        cost = amount * price
        commission = self.order_processor.calculate_commission(amount, price, is_sell=False)
        if cost + commission <= available_cash:
            return amount

        min_lot = 200 if security.startswith('688') else 100
        adjusted = int(available_cash / price / min_lot) * min_lot

        while adjusted >= min_lot:
            test_cost = adjusted * price
            test_commission = self.order_processor.calculate_commission(adjusted, price, is_sell=False)
            if test_cost + test_commission <= available_cash:
                break
            adjusted -= min_lot

        if adjusted < min_lot:
            self.log.warning(f"【买入失败】{security} | 原因: 现金不足")
            return None

        self.log.warning(f"当前账户资金不足，调整{security}下单数量为{adjusted}")
        return adjusted

    def _submit_order(self, security: str, amount: int, price: float) -> Optional[str]:
        """创建订单→注册blotter→执行→更新状态。返回 order_id 或 None。"""
        order_id, order = self.order_processor.create_order(security, amount, price)
        if self.context and self.context.blotter:
            self.context.blotter.all_orders.append(order)

        if amount > 0:
            self.log.info(f"生成订单，订单号:{order_id}，股票代码：{security}，数量：买入{amount}股")
            success = self.order_processor.execute_buy(security, amount, price)
        else:
            self.log.info(f"生成订单，订单号:{order_id}，股票代码：{security}，数量：卖出{abs(amount)}股")
            success = self.order_processor.execute_sell(security, abs(amount), price)

        if success:
            order.status = '8'
            order.filled = amount
            if self.context and self.context.blotter:
                self.context.blotter.filled_orders.append(order)

        return order.id if success else None

    @validate_lifecycle
    def order(self, security: str, amount: int, limit_price: float = None) -> Optional[str]:
        """买卖指定数量的股票

        Args:
            security: 股票代码
            amount: 交易数量，正数表示买入，负数表示卖出
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        if amount == 0:
            return None
        price = self._get_price_and_check_limit(security, limit_price, amount)
        if price is None:
            return None
        if amount > 0:
            amount = self._adjust_buy_amount(security, amount, price)
            if amount is None:
                return None
        return self._submit_order(security, amount, price)

    @validate_lifecycle
    def order_target(self, security: str, amount: int, limit_price: float = None) -> Optional[str]:
        """下单到目标数量

        Args:
            security: 股票代码
            amount: 期望的最终数量
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        current_amount = 0
        if security in self.context.portfolio.positions:
            current_amount = self.context.portfolio.positions[security].amount
        delta = amount - current_amount
        if delta == 0:
            return None
        price = self._get_price_and_check_limit(security, limit_price, delta)
        if price is None:
            return None
        return self._submit_order(security, delta, price)

    @validate_lifecycle
    def order_value(self, security: str, value: float, limit_price: float = None) -> Optional[str]:
        """按金额下单

        Args:
            security: 股票代码
            value: 股票价值，正数买入，负数卖出
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        if abs(value) < 1:
            return None
        is_buy = value > 0
        price = self._get_price_and_check_limit(security, limit_price, 1 if is_buy else -1)
        if price is None:
            return None

        min_lot = 200 if security.startswith('688') else 100

        if is_buy:
            target_amount = int(value / price / min_lot) * min_lot
            if target_amount < min_lot:
                self.log.warning(f"【下单失败】{security} | 原因: 分配金额不足{min_lot}股 (分配{value:.2f}元, 价格{price:.2f}元, 可用现金{self.context.portfolio._cash:.2f}元)")
                return None
            amount = self._adjust_buy_amount(security, target_amount, price)
            if amount is None:
                return None
            return self._submit_order(security, amount, price)
        else:
            sell_value = abs(value)
            target_amount = int(sell_value / price / min_lot) * min_lot

            if security not in self.context.portfolio.positions:
                self.log.warning(f"【卖出失败】{security} | 原因: 无持仓")
                return None

            position = self.context.portfolio.positions[security]
            if target_amount >= position.amount:
                target_amount = position.amount
            elif target_amount < min_lot:
                self.log.warning(f"【下单失败】{security} | 原因: 卖出金额不足{min_lot}股 (金额{sell_value:.2f}元, 价格{price:.2f}元)")
                return None

            return self._submit_order(security, -target_amount, price)

    @validate_lifecycle
    def order_target_value(self, security: str, value: float, limit_price: float = None) -> Optional[str]:
        """调整股票持仓市值到目标价值

        Args:
            security: 股票代码
            value: 期望的股票最终价值
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        current_amount = 0
        if security in self.context.portfolio.positions:
            current_amount = self.context.portfolio.positions[security].amount

        is_buy = value > current_amount * (self.context.portfolio.positions[security].last_sale_price if current_amount > 0 else 0)
        execution_price = self.order_processor.get_execution_price(security, limit_price, is_buy)
        if execution_price is None:
            self.log.warning(f"订单失败 {security} | 原因: 无法获取价格")
            return None

        min_lot = 200 if security.startswith('688') else 100
        if value <= 0:
            target_amount = 0
        else:
            target_amount = int(value / execution_price / min_lot) * min_lot

        delta = target_amount - current_amount
        if delta == 0:
            return None

        # 委托给 order_target 按数量交易
        return self.order_target(security, target_amount, limit_price)

    def get_open_orders(self) -> list:
        """获取未成交订单"""
        if self.context and self.context.blotter:
            return self.context.blotter.open_orders
        return []

    def get_orders(self, security: str = None) -> list:
        """获取当日全部订单

        Args:
            security: 股票代码，None表示获取所有订单

        Returns:
            订单列表
        """
        if not self.context or not self.context.blotter:
            return []

        all_orders = self.context.blotter.all_orders
        if security is None:
            return all_orders
        else:
            return [o for o in all_orders if o.symbol == security]

    def get_order(self, order_id: str) -> Optional[Any]:
        """获取指定订单

        Args:
            order_id: 订单id

        Returns:
            Order对象或None
        """
        if not self.context or not self.context.blotter:
            return None

        for order in self.context.blotter.all_orders:
            if order.id == order_id:
                return order
        return None

    def get_trades(self, security: str = None) -> list:
        """获取当日成交订单

        Args:
            security: 股票代码，None表示获取所有成交

        Returns:
            成交订单列表
        """
        if not self.context or not self.context.blotter:
            return []

        filled = getattr(self.context.blotter, 'filled_orders', [])
        if security is None:
            return filled
        return [o for o in filled if o.symbol == security]

    def get_position(self, security: str) -> Optional[Position]:
        """获取持仓信息

        Args:
            security: 股票代码

        Returns:
            Position对象或None
        """
        if self.context and self.context.portfolio:
            return self.context.portfolio.positions.get(security)
        return None

    def get_positions(self, security_list: list[str] = None) -> dict[str, Position]:
        """获取多支股票持仓信息

        Args:
            security_list: 股票代码列表，None表示获取所有持仓

        Returns:
            dict: {stock: Position对象}
        """
        if not self.context or not self.context.portfolio:
            return {}

        positions = self.context.portfolio.positions
        if security_list is None:
            return positions.copy()

        return {s: positions[s] for s in security_list if s in positions}

    def cancel_order(self, order: Any) -> bool:
        """取消订单"""
        if self.context and self.context.blotter:
            return self.context.blotter.cancel_order(order)
        return False

    # ==================== 配置API ====================

    @validate_lifecycle
    def set_benchmark(self, benchmark: str) -> None:
        """设置基准（支持指数和普通股票）,会自动添加到benchmark_data"""
        # 优先从benchmark_data中查找（指数）
        if benchmark in self.data_context.benchmark_data:
            self.context.benchmark = benchmark
            self.log.info(f"设置基准（指数）: {benchmark}")
            return

        # 如果不在benchmark_data中，检查stock_data_dict（普通股票/指数）
        if benchmark in self.data_context.stock_data_dict:
            self.context.benchmark = benchmark
            # 动态添加到benchmark_data供后续使用
            self.data_context.benchmark_data[benchmark] = self.data_context.stock_data_dict[benchmark]
            self.log.info(f"设置基准（股票/指数）: {benchmark}")
            return

        # 都不存在，警告
        self.log.warning(f"基准 {benchmark} 不存在于指数或股票数据中，保持当前基准")
        return

    @validate_lifecycle
    def set_universe(self, stocks: str | list[str]) -> None:
        """设置股票池并预加载数据"""
        if isinstance(stocks, list):
            new_stocks = set(stocks)
            to_preload = new_stocks - self.active_universe
            if to_preload:
                self.log.debug(f"预加载 {len(to_preload)} 只新股票数据")
                for stock in to_preload:
                    if stock in self.data_context.stock_data_dict:
                        _ = self.data_context.stock_data_dict[stock]
            self.active_universe = new_stocks
            self.log.debug(f"股票池更新: {len(self.active_universe)} 只")
        else:
            self.log.debug(f"设置股票池: {stocks}")

    def is_trade(self) -> bool:
        """是否实盘"""
        return False

    @validate_lifecycle
    def set_commission(self, commission_ratio: float = 0.0003, min_commission: float = 5.0, type: str = "STOCK") -> None:
        """设置交易佣金"""
        # 验证ptrade平台限制：佣金费率和最低交易佣金不能小于或者等于0
        if commission_ratio is not None and commission_ratio <= 0:
            raise ValueError("IQInvalidArgument: 佣金费率和最低交易佣金不能小于或者等于0,请核对后重新输入")
        if min_commission is not None and min_commission <= 0:
            raise ValueError("IQInvalidArgument: 佣金费率和最低交易佣金不能小于或者等于0,请核对后重新输入")

        if commission_ratio is not None:
            kwargs = {'commission_ratio': commission_ratio}
        else:
            kwargs = {}
        if min_commission is not None:
            kwargs['min_commission'] = min_commission
        if type is not None:
            kwargs['commission_type'] = type
        if kwargs:
            config.update_trading_config(**kwargs)

    @validate_lifecycle
    def set_slippage(self, slippage: float = 0.0) -> None:
        """设置滑点"""
        if slippage is not None:
            config.update_trading_config(slippage=slippage)

    @validate_lifecycle
    def set_fixed_slippage(self, fixedslippage: float = 0.001) -> None:
        """设置固定滑点"""
        if fixedslippage is not None:
            config.update_trading_config(fixed_slippage=fixedslippage)

    @validate_lifecycle
    def set_limit_mode(self, limit_mode: str = 'LIMIT') -> None:
        """设置下单限制模式"""
        config.update_trading_config(limit_mode=limit_mode)

    @validate_lifecycle
    def set_volume_ratio(self, volume_ratio: float = 0.25) -> None:
        """设置成交比例

        Args:
            volume_ratio: 成交比例，默认0.25，即单笔最大成交量为当日成交量的1/4
        """
        config.update_trading_config(volume_ratio=volume_ratio)

    @validate_lifecycle
    def set_yesterday_position(self, poslist: list[dict]) -> None:
        """设置底仓（回测用）

        Args:
            poslist: 持仓列表，每个元素为字典 {'security': 股票代码, 'amount': 数量, 'cost_basis': 成本价}
        """
        if not isinstance(poslist, list):
            self.log.warning("set_yesterday_position 参数必须是列表")
            return

        for pos_info in poslist:
            security = pos_info.get('security')
            amount = pos_info.get('amount', 0)
            cost_basis = pos_info.get('cost_basis', 0)

            if security and amount > 0 and cost_basis > 0:
                self.context.portfolio.positions[security] = Position(security, amount, cost_basis)
                self.log.info(f"设置底仓: {security}, 数量:{amount}, 成本价:{cost_basis}")

    def run_interval(self, context: Any, func: Callable, seconds: int = 10) -> None:
        """定时运行函数（秒级，仅实盘）

        Args:
            context: Context对象
            func: 自定义函数，接受context参数
            seconds: 时间间隔（秒），最小3秒
        """
        _ = (context, func, seconds)  # 回测中不执行
        pass

    @validate_lifecycle
    def run_daily(self, context: Any, func: Callable, time: str = '9:31') -> None:
        """注册每日定时任务

        Args:
            context: Context对象
            func: 自定义函数，接受context参数
            time: 触发时间，格式HH:MM
        """
        self._daily_tasks.append((func, time))

    @validate_lifecycle
    def set_parameters(self, params: dict) -> None:
        """设置策略配置参数

        Args:
            params: dict，策略参数字典
        """
        if not hasattr(self.context, 'params'):
            self.context.params = {}
        self.context.params.update(params)

    @validate_lifecycle
    def convert_position_from_csv(self, file_path: str) -> list[dict]:
        """从CSV文件获取设置底仓的参数列表

        Args:
            file_path: CSV文件路径

        Returns:
            list: 持仓列表，格式为 [{'security': 股票代码, 'amount': 数量, 'cost_basis': 成本价}, ...]
        """
        df = pd.read_csv(file_path)
        positions = []
        for _, row in df.iterrows():
            positions.append({
                'security': row.get('security', row.get('stock', row.get('code'))),
                'amount': int(row.get('amount', row.get('qty', 0))),
                'cost_basis': float(row.get('cost_basis', row.get('cost', row.get('price', 0))))
            })
        return positions

    def get_user_name(self) -> str:
        """获取登录终端的资金账号

        Returns:
            str: 资金账号（回测返回模拟账号）
        """
        return 'backtest_user'

    # ==================== 技术指标API ====================

    def get_MACD(self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算MACD指标（异同移动平均线）

        Args:
            close: 收盘价时间序列，numpy.ndarray类型
            short: 短周期，默认12
            long: 长周期，默认26
            m: 移动平均线周期，默认9

        Returns:
            tuple: (dif, dea, macd) 三个numpy.ndarray
                - dif: MACD指标DIF值的时间序列
                - dea: MACD指标DEA值的时间序列
                - macd: MACD指标MACD值的时间序列（柱状图）
        """
        try:
            import talib
        except ImportError:
            raise ImportError("get_MACD需要安装ta-lib库: pip install ta-lib")

        if not isinstance(close, np.ndarray):
            close = np.array(close, dtype=float)

        # 使用talib计算MACD
        dif, dea, macd = talib.MACD(close, fastperiod=short, slowperiod=long, signalperiod=m)

        return dif, dea, macd

    def get_KDJ(self, high: np.ndarray, low: np.ndarray, close: np.ndarray,
                n: int = 9, m1: int = 3, m2: int = 3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算KDJ指标（随机指标）

        Args:
            high: 最高价时间序列，numpy.ndarray类型
            low: 最低价时间序列，numpy.ndarray类型
            close: 收盘价时间序列，numpy.ndarray类型
            n: 周期，默认9
            m1: K值平滑周期，默认3
            m2: D值平滑周期，默认3

        Returns:
            tuple: (k, d, j) 三个numpy.ndarray
                - k: KDJ指标K值的时间序列
                - d: KDJ指标D值的时间序列
                - j: KDJ指标J值的时间序列
        """
        try:
            import talib
        except ImportError:
            raise ImportError("get_KDJ需要安装ta-lib库: pip install ta-lib")

        if not isinstance(high, np.ndarray):
            high = np.array(high, dtype=float)
        if not isinstance(low, np.ndarray):
            low = np.array(low, dtype=float)
        if not isinstance(close, np.ndarray):
            close = np.array(close, dtype=float)

        # 使用talib的STOCH (Stochastic) 计算KD
        # talib.STOCH返回的是slowk和slowd
        k, d = talib.STOCH(high, low, close,
                          fastk_period=n,
                          slowk_period=m1,
                          slowk_matype=0,  # SMA
                          slowd_period=m2,
                          slowd_matype=0)  # SMA

        # 计算J值：J = 3K - 2D
        j = 3 * k - 2 * d

        return k, d, j

    def get_RSI(self, close: np.ndarray, n: int = 6) -> np.ndarray:
        """计算RSI指标（相对强弱指标）

        Args:
            close: 收盘价时间序列，numpy.ndarray类型
            n: 周期，默认6

        Returns:
            np.ndarray: RSI指标值的时间序列
        """
        try:
            import talib
        except ImportError:
            raise ImportError("get_RSI需要安装ta-lib库: pip install ta-lib")

        if not isinstance(close, np.ndarray):
            close = np.array(close, dtype=float)

        # 使用talib计算RSI
        rsi = talib.RSI(close, timeperiod=n)

        return rsi

    def get_CCI(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14) -> np.ndarray:
        """计算CCI指标（顺势指标）

        Args:
            high: 最高价时间序列，numpy.ndarray类型
            low: 最低价时间序列，numpy.ndarray类型
            close: 收盘价时间序列，numpy.ndarray类型
            n: 周期，默认14

        Returns:
            np.ndarray: CCI指标值的时间序列
        """
        try:
            import talib
        except ImportError:
            raise ImportError("get_CCI需要安装ta-lib库: pip install ta-lib")

        if not isinstance(high, np.ndarray):
            high = np.array(high, dtype=float)
        if not isinstance(low, np.ndarray):
            low = np.array(low, dtype=float)
        if not isinstance(close, np.ndarray):
            close = np.array(close, dtype=float)

        # 使用talib计算CCI
        cci = talib.CCI(high, low, close, timeperiod=n)

        return cci
