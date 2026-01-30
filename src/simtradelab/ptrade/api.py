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
from ..utils.paths import get_project_root
from simtradelab.ptrade.object import Position
from .order_processor import OrderProcessor
from .cache_manager import cache_manager
from .config_manager import config
from simtradelab.utils.perf import timer


def validate_lifecycle(func: Callable) -> Callable:
    """生命周期验证装饰器

    自动检查API是否可以在当前生命周期阶段调用
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # 如果context有lifecycle_controller，进行验证
        if hasattr(self, 'context') and self.context and hasattr(self.context, '_lifecycle_controller'):
            controller = self.context._lifecycle_controller
            if controller:
                api_name = func.__name__
                validation_result = controller.validate_api_call(api_name)
                if not validation_result.is_valid:
                    raise PTradeLifecycleError(validation_result.error_message)
                # 记录API调用
                controller.record_api_call(api_name, success=True)

        # 执行原函数
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
        self._stock_status_cache: dict[tuple, bool] = {}
        self._stock_date_index: dict[str, tuple[dict, list]] = {}
        self._prebuilt_index: bool = False
        self._sorted_status_dates: Optional[list[str]] = None
        self._history_cache: dict = cache_manager.get_namespace('history')._cache  # 使用LRUCache
        self._fundamentals_cache: dict = cache_manager.get_namespace('fundamentals')._cache  # 使用全局缓存

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

    def get_stock_date_index(self, stock: str) -> tuple[dict, list]:
        """获取股票日期索引，返回 (date_dict, sorted_dates) 元组"""
        if stock not in self._stock_date_index:
            # 延迟构建单只股票索引
            # 检查stock_data_dict和benchmark_data
            stock_df = None
            if stock in self.data_context.stock_data_dict:
                stock_df = self.data_context.stock_data_dict[stock]
            elif stock in self.data_context.benchmark_data:
                stock_df = self.data_context.benchmark_data[stock]

            if stock_df is not None and isinstance(stock_df, pd.DataFrame) and isinstance(stock_df.index, pd.DatetimeIndex):
                date_dict = {date: idx for idx, date in enumerate(stock_df.index)}
                sorted_dates = list(stock_df.index)
                self._stock_date_index[stock] = (date_dict, sorted_dates)
            else:
                self._stock_date_index[stock] = ({}, [])
        return self._stock_date_index.get(stock, ({}, []))

    def get_adjusted_price(self, stock: str, date: str, price_type: str = 'close', fq: str = None) -> float:
        """获取复权后的价格

        Args:
            stock: 股票代码
            date: 日期
            price_type: 价格类型 (close/open/high/low)
            fq: 复权类型 (None-不复权, 'pre'-前复权, 'post'-后复权)

        Returns:
            复权后价格
        """
        if fq is None or stock not in self.data_context.stock_data_dict:
            # 不复权，直接返回原始价格
            try:
                stock_df = self.data_context.stock_data_dict[stock]
                return stock_df.loc[date, price_type]
            except (KeyError, IndexError, AttributeError):
                return np.nan

        if fq == 'pre':
            # 前复权：使用adj_pre_cache
            try:
                stock_df = self.data_context.stock_data_dict[stock]
                original_price = stock_df.loc[date, price_type]

                # 使用预计算的复权因子缓存
                if self.data_context.adj_pre_cache and stock in self.data_context.adj_pre_cache:
                    adj_factors = self.data_context.adj_pre_cache[stock]
                    date_ts = pd.Timestamp(date)
                    if date_ts in adj_factors.index:
                        adj_a = adj_factors.loc[date_ts, 'adj_a']
                        adj_b = adj_factors.loc[date_ts, 'adj_b']
                        # 前复权公式: 前复权价 = (未复权价 - adj_b) / adj_a
                        return (original_price - adj_b) / adj_a

                # 缓存不存在或无对应日期，返回原始价
                return original_price
            except (KeyError, IndexError, AttributeError):
                return np.nan

        if fq == 'post':
            # 后复权：使用adj_post_cache
            try:
                stock_df = self.data_context.stock_data_dict[stock]
                original_price = stock_df.loc[date, price_type]

                if self.data_context.adj_post_cache and stock in self.data_context.adj_post_cache:
                    adj_factors = self.data_context.adj_post_cache[stock]
                    date_ts = pd.Timestamp(date)
                    if date_ts in adj_factors.index:
                        adj_a = adj_factors.loc[date_ts, 'adj_a']
                        adj_b = adj_factors.loc[date_ts, 'adj_b']
                        # 后复权公式: 后复权价 = adj_a * 未复权价 + adj_b
                        return adj_a * original_price + adj_b

                return original_price
            except (KeyError, IndexError, AttributeError):
                return np.nan

        # 其他情况返回原始价
        try:
            stock_df = self.data_context.stock_data_dict[stock]
            return stock_df.loc[date, price_type]
        except (KeyError, IndexError, AttributeError):
            return np.nan
        
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
        trade_days_df = self.data_context.stock_data_store['/trade_days']
        all_trade_days = trade_days_df.index

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

        # 获取或创建日期索引缓存（增量更新）
        if cache_key not in self._fundamentals_cache:
            self._fundamentals_cache[cache_key] = {}
            # 限制缓存条目数量
            if len(self._fundamentals_cache) > 500:
                self._fundamentals_cache.pop(next(iter(self._fundamentals_cache)))

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
                        # 对于valuation表，返回前一交易日数据（匹配ptrade平台行为）
                        # 使用side='left'排除当日，确保返回的是已确定的前一交易日数据
                        idx = df.index.searchsorted(query_ts, side='left')
                        if idx > 0:
                            date_indices[stock] = idx - 1
                        elif len(df.index) > 0:
                            # 如果查询日期早于所有数据，返回第一条
                            date_indices[stock] = 0
                except Exception as e:
                    # 静默忽略错误，继续处理其他股票
                    continue

        result_data = {}

        # 对于valuation表的total_value/float_value，需要用查询日期的收盘价实时计算
        need_realtime_total_value = (table == 'valuation' and 'total_value' in fields)
        need_realtime_float_value = (table == 'valuation' and 'float_value' in fields)
        need_realtime_market_cap = need_realtime_total_value or need_realtime_float_value

        # 预先获取并缓存当天所有股票的收盘价
        close_prices = {}
        if need_realtime_market_cap:
            price_cache_key = ('_close_prices', query_ts)
            if price_cache_key in self._fundamentals_cache:
                close_prices = self._fundamentals_cache[price_cache_key]
            else:
                for stock, stock_df in self.data_context.stock_data_dict.items():
                    if isinstance(stock_df, pd.DataFrame) and not stock_df.empty:
                        idx = stock_df.index.searchsorted(query_ts, side='right')
                        if idx > 0:
                            close_prices[stock] = stock_df.iloc[idx - 1]['close']
                self._fundamentals_cache[price_cache_key] = close_prices

        for stock in stocks:
            if stock not in date_indices:
                continue

            try:
                df = data_dict[stock]
                if df is None or len(df) == 0:
                    continue

                idx = date_indices[stock]
                nearest_date = df.index[idx]
                row = df.loc[nearest_date]

                stock_data = {}
                for field in fields:
                    if field == 'total_value' and need_realtime_total_value:
                        # 实时计算总市值 = 查询日收盘价 × 总股本
                        total_shares = row.get('total_shares')
                        if total_shares is not None and not pd.isna(total_shares) and stock in close_prices:
                            stock_data[field] = close_prices[stock] * total_shares
                        else:
                            stock_data[field] = row.get(field)
                    elif field == 'float_value' and need_realtime_float_value:
                        # 实时计算流通市值 = 查询日收盘价 × 流通股本
                        a_floats = row.get('a_floats')
                        if a_floats is not None and not pd.isna(a_floats) and stock in close_prices:
                            stock_data[field] = close_prices[stock] * a_floats
                        else:
                            stock_data[field] = row.get(field)
                    else:
                        stock_data[field] = row.get(field)

                if stock_data:
                    result_data[stock] = stock_data

            except Exception as e:
                print("读取{}数据失败: stock={}, fields={}, error={}".format(table, stock, fields, e))
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

    def get_price(self, security: str | list[str], start_date: str = None, end_date: str = None, frequency: str = '1d', fields: str | list[str] = None, fq: str = None, count: int = None) -> pd.DataFrame | PtradeAPI.PanelLike:
        """获取历史行情数据"""
        # 验证fq参数
        valid_fq = ['pre', 'post', 'dypre', None]
        if fq not in valid_fq:
            raise ValueError("function get_price: invalid fq argument, valid: {}, got {} (type: {})".format(
                valid_fq, fq, type(fq)))

        if isinstance(fields, str):
            fields_list = [fields]
        elif fields is None:
            fields_list = ['open', 'high', 'low', 'close', 'volume', 'money']
        else:
            fields_list = fields

        is_single_stock = isinstance(security, str)
        stocks = [security] if is_single_stock else security

        if count is not None:
            end_dt = pd.Timestamp(end_date) if end_date else self.context.current_dt
            result = {}
            for stock in stocks:
                if stock not in self.data_context.stock_data_dict:
                    continue

                stock_df = self.data_context.stock_data_dict[stock]
                if not isinstance(stock_df, pd.DataFrame):
                    continue

                try:
                    date_dict, _ = self.get_stock_date_index(stock)
                    current_idx = date_dict.get(end_dt)
                    if current_idx is None:
                        current_idx = stock_df.index.get_loc(end_dt)
                except (KeyError, IndexError):
                    continue

                # Ptrade API语义: count=N 返回截止到end_date的N天数据（包含end_date）
                slice_df = stock_df.iloc[max(0, current_idx - count + 1):current_idx + 1]
                result[stock] = slice_df
        else:
            start_dt = pd.Timestamp(start_date) if start_date else None
            end_dt = pd.Timestamp(end_date) if end_date else self.context.current_dt

            result = {}
            for stock in stocks:
                if stock not in self.data_context.stock_data_dict:
                    continue

                stock_df = self.data_context.stock_data_dict[stock]
                if not isinstance(stock_df, pd.DataFrame):
                    continue

                if start_dt:
                    mask = (stock_df.index >= start_dt) & (stock_df.index <= end_dt)
                else:
                    mask = stock_df.index <= end_dt

                slice_df = stock_df[mask]
                result[stock] = slice_df

        if fq == 'pre':
            for stock in list(result.keys()):
                stock_df = result[stock]
                if isinstance(stock_df, pd.DataFrame) and not stock_df.empty:
                    # 向量化复权计算
                    if self.data_context.adj_pre_cache and stock in self.data_context.adj_pre_cache:
                        adj_factors = self.data_context.adj_pre_cache[stock]
                        # 找到stock_df中有复权因子的日期
                        common_idx = stock_df.index.intersection(adj_factors.index)
                        if len(common_idx) > 0:
                            adjusted_df = stock_df.copy()
                            adj_a = adj_factors.loc[common_idx, 'adj_a']
                            adj_b = adj_factors.loc[common_idx, 'adj_b']
                            price_cols = ['open', 'high', 'low', 'close']
                            for col in price_cols:
                                if col in adjusted_df.columns:
                                    # 前复权公式: 前复权价 = (未复权价 - adj_b) / adj_a
                                    adjusted_df.loc[common_idx, col] = (
                                        adjusted_df.loc[common_idx, col] - adj_b
                                    ) / adj_a
                            result[stock] = adjusted_df

        if fq == 'post':
            for stock in list(result.keys()):
                stock_df = result[stock]
                if isinstance(stock_df, pd.DataFrame) and not stock_df.empty:
                    # 向量化复权计算
                    if self.data_context.adj_post_cache and stock in self.data_context.adj_post_cache:
                        adj_factors = self.data_context.adj_post_cache[stock]
                        common_idx = stock_df.index.intersection(adj_factors.index)
                        if len(common_idx) > 0:
                            adjusted_df = stock_df.copy()
                            adj_a = adj_factors.loc[common_idx, 'adj_a']
                            adj_b = adj_factors.loc[common_idx, 'adj_b']
                            price_cols = ['open', 'high', 'low', 'close']
                            for col in price_cols:
                                if col in adjusted_df.columns:
                                    # 后复权公式: 后复权价 = adj_a * 未复权价 + adj_b
                                    adjusted_df.loc[common_idx, col] = (
                                        adj_a * adjusted_df.loc[common_idx, col] + adj_b
                                    )
                            result[stock] = adjusted_df

        if not result:
            return pd.DataFrame()

        if is_single_stock:
            stock_df = result.get(security)
            if stock_df is None:
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
            raise ValueError("function get_history: invalid fq argument, valid: {}, got {} (type: {})".format(
                valid_fq, fq, type(fq)))

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

        # 缓存键：使用frozen set避免列表顺序问题，但这里保持tuple更快
        field_key = tuple(fields) if len(fields) > 1 else fields[0]
        cache_key = (tuple(sorted(stocks)), count, field_key, fq, current_dt, include, is_dict)

        # 检查缓存
        if cache_key in self._history_cache:
            return self._history_cache[cache_key]

        # 优化1: 批量预加载股票数据（减少LazyDataDict的重复加载）
        stock_dfs = {}
        stock_data_dict = self.data_context.stock_data_dict
        benchmark_data = self.data_context.benchmark_data

        for stock in stocks:
            data_source = stock_data_dict.get(stock)
            if data_source is None:
                data_source = benchmark_data.get(stock)
            if data_source is not None:
                stock_dfs[stock] = data_source

        # 优化2: 批量获取索引位置
        stock_info = {}
        for stock, data_source in stock_dfs.items():
            if not isinstance(data_source, pd.DataFrame):
                continue
            try:
                date_dict, _ = self.get_stock_date_index(stock)
                current_idx = date_dict.get(current_dt)
                if current_idx is None:
                    current_idx = data_source.index.get_loc(current_dt)
                stock_info[stock] = (data_source, current_idx)
            except (KeyError, IndexError):
                continue

        # 优化3+4: 批量切片+复权（减少循环开销）
        result = {}
        needs_adj_pre = fq == 'pre' and self.data_context.adj_pre_cache
        needs_adj_post = fq == 'post' and self.data_context.adj_post_cache
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

            slice_df = data_source.iloc[start_idx:end_idx]

            if len(slice_df) == 0:
                continue

            # 前复权处理: 前复权价 = (未复权价 - adj_b) / adj_a
            if needs_adj_pre and stock in self.data_context.adj_pre_cache:
                adj_factors = self.data_context.adj_pre_cache[stock]
                slice_adj = adj_factors.iloc[start_idx:end_idx]

                adj_a = slice_adj['adj_a'].values
                adj_b = slice_adj['adj_b'].values

                stock_result = {}
                for field_name in fields:
                    if field_name not in slice_df.columns:
                        continue
                    if field_name in price_fields:
                        # 前复权价 = (未复权价 - adj_b) / adj_a
                        stock_result[field_name] = (slice_df[field_name].values - adj_b) / adj_a
                    else:
                        stock_result[field_name] = slice_df[field_name].values
            # 后复权处理: 后复权价 = adj_a * 未复权价 + adj_b
            elif needs_adj_post and stock in self.data_context.adj_post_cache:
                adj_factors = self.data_context.adj_post_cache[stock]
                slice_adj = adj_factors.iloc[start_idx:end_idx]

                adj_a = slice_adj['adj_a'].values
                adj_b = slice_adj['adj_b'].values

                stock_result = {}
                for field_name in fields:
                    if field_name not in slice_df.columns:
                        continue
                    if field_name in price_fields:
                        # 后复权价 = adj_a * 未复权价 + adj_b
                        stock_result[field_name] = adj_a * slice_df[field_name].values + adj_b
                    else:
                        stock_result[field_name] = slice_df[field_name].values
            else:
                # 不复权: 直接提取
                stock_result = {field_name: slice_df[field_name].values
                              for field_name in fields if field_name in slice_df.columns}

            if stock_result:
                result[stock] = stock_result

        # 转换为返回格式并缓存
        if not result:
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
        """获取股票状态"""
        if isinstance(stocks, str):
            stocks = [stocks]

        if query_date is None:
            query_dt = self.context.current_dt if self.context else pd.Timestamp.now()
        else:
            query_dt = pd.Timestamp(query_date)
        result = {}

        for stock in stocks:
            cache_key = (query_dt, stock, query_type)
            if cache_key in self._stock_status_cache:
                result[stock] = self._stock_status_cache[cache_key]
                continue

            is_problematic = False

            # 统一使用快照数据判定 ST/HALT/DELISTING
            if self.data_context.stock_status_history:
                # 缓存排序后的日期列表（只排序一次）
                if self._sorted_status_dates is None:
                    self._sorted_status_dates = sorted(self.data_context.stock_status_history.keys())

                query_date_str = query_dt.strftime('%Y%m%d')

                # 二分查找最近日期
                pos = bisect.bisect_right(self._sorted_status_dates, query_date_str)
                nearest_date = self._sorted_status_dates[pos - 1] if pos > 0 else None

                # 使用最近的历史快照数据
                if nearest_date and query_type in self.data_context.stock_status_history[nearest_date]:
                    status_dict = self.data_context.stock_status_history[nearest_date][query_type]
                    is_problematic = status_dict.get(stock, False) is True
                    self._stock_status_cache[cache_key] = is_problematic
                    result[stock] = is_problematic
                    continue

            if query_type == 'ST' and not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                stock_name = self.data_context.stock_metadata.loc[stock, 'stock_name']
                is_problematic = 'ST' in str(stock_name)

            elif query_type == 'DELISTING' and not self.data_context.stock_metadata.empty and stock in self.data_context.stock_metadata.index:
                try:
                    de_listed_date = pd.Timestamp(self.data_context.stock_metadata.loc[stock, 'de_listed_date'])
                    is_problematic = (de_listed_date.year < 2900 and de_listed_date <= query_dt)
                except (KeyError, ValueError):
                    pass

            self._stock_status_cache[cache_key] = is_problematic
            result[stock] = is_problematic

        return result

    def get_stock_exrights(self, stock_code: str, date: str = None) -> Optional[pd.DataFrame]:
        """获取股票除权除息信息"""
        try:
            exrights_df = self.data_context.stock_data_store[f'/exrights/{stock_code}']

            if date is not None:
                query_date = pd.Timestamp(date)
                if query_date in exrights_df.index:
                    return exrights_df.loc[[query_date]]
                else:
                    return None
            else:
                return exrights_df
        except KeyError:
            return None
        except Exception:
            return None

    # ==================== 指数/行业API ====================

    def get_index_stocks(self, index_code: str, date: str = None) -> list[str]:
        """获取指数成份股（支持向前回溯查找）"""
        if not self.data_context.index_constituents:
            return []

        # 获取所有可用日期并排序
        available_dates = sorted(self.data_context.index_constituents.keys())

        # 如果未指定日期，使用回测当前日期
        if date is None:
            query_date = str(self.context.current_dt.date())
        else:
            query_date = date

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
        """推导行业成份股"""
        if self.data_context.stock_metadata.empty:
            return {} if industry_code is None else []

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

        if industry_code is None:
            return industries
        else:
            return industries.get(industry_code, {}).get('stocks', [])

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
                idx = date_dict.get(query_dt)
                if idx is None:
                    idx = stock_df.index.get_loc(query_dt)

                if idx == 0:
                    result[stock] = status
                    continue

                current_close = stock_df.iloc[idx]['close']
                current_high = stock_df.iloc[idx]['high']
                current_low = stock_df.iloc[idx]['low']
                prev_close = stock_df.iloc[idx-1]['close']

                if np.isnan(prev_close) or prev_close <= 0: # type: ignore
                    result[stock] = status
                    continue

                limit_ratio = self._get_price_limit_ratio(stock)
                limit_up_price = prev_close * (1 + limit_ratio)
                limit_down_price = prev_close * (1 - limit_ratio)

                # 回测中不能使用当天收盘价判断涨停（会产生未来数据泄露）
                # 只检查一字涨停（开盘=最高=最低=涨停价）
                current_open = stock_df.iloc[idx]['open']

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

        # 使用blotter创建订单
        if self.context and self.context.blotter:
            order = self.context.blotter.create_order(security, amount)
            if limit_price is not None:
                order.limit = limit_price
            return order.id
        return None

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

        # 获取执行价格（根据买卖方向计算滑点）
        is_buy = delta > 0
        execution_price = self.order_processor.get_execution_price(security, limit_price, is_buy)
        if execution_price is None:
            self.log.warning("订单失败 {} | 原因: 无法获取价格".format(security))
            return None

        # 检查涨跌停
        limit_status = self.check_limit(security, self.context.current_dt)[security]
        if not self.order_processor.check_limit_status(security, delta, limit_status):
            return None

        # 创建订单
        order_id, order = self.order_processor.create_order(security, delta, execution_price)

        if delta > 0:
            self.log.info("生成订单，订单号:{}，股票代码：{}，数量：买入{}股".format(order_id, security, delta))
            success = self.order_processor.execute_buy(security, delta, execution_price)
        else:
            self.log.info("生成订单，订单号:{}，股票代码：{}，数量：卖出{}股".format(order_id, security, abs(delta)))
            success = self.order_processor.execute_sell(security, abs(delta), execution_price)

        if success:
            order.status = '8'
            order.filled = delta

        return order.id if success else None

    @validate_lifecycle
    def order_value(self, security: str, value: float, limit_price: float = None) -> Optional[str]:
        """按金额下单

        Args:
            security: 股票代码
            value: 股票价值
            limit_price: 买卖限价

        Returns:
            订单id或None
        """
        # 获取执行价格
        current_price = self.order_processor.get_execution_price(security, limit_price)
        if current_price is None:
            self.log.warning(f"【下单失败】{security} | 原因: 获取价格数据失败")
            return None

        # 检查涨停
        limit_status = self.check_limit(security, self.context.current_dt)[security]
        if limit_status == 1:
            self.log.warning(f"【买入失败】{security} | 原因: 涨停")
            return None

        # 确定最小交易单位
        min_lot = 200 if security.startswith('688') else 100

        # 先按目标value计算数量
        target_amount = int(value / current_price / min_lot) * min_lot
        available_cash = self.context.portfolio._cash

        # 如果目标数量 >= 最小单位，尝试按目标买入
        if target_amount >= min_lot:
            # 检查现金是否足够（含手续费）
            cost = target_amount * current_price
            commission = self.order_processor.calculate_commission(target_amount, current_price, is_sell=False)
            total_cost = cost + commission

            if total_cost <= available_cash:
                # 现金足够，按目标数量买入
                amount = target_amount
            else:
                # 现金不足目标金额，自动调整到可买的最大数量
                max_affordable_amount = int(available_cash / current_price / min_lot) * min_lot

                # 迭代调整，确保包含手续费后不超预算
                while max_affordable_amount >= min_lot:
                    test_cost = max_affordable_amount * current_price
                    test_commission = self.order_processor.calculate_commission(max_affordable_amount, current_price, is_sell=False)
                    test_total = test_cost + test_commission

                    if test_total <= available_cash:
                        break
                    max_affordable_amount -= min_lot

                if max_affordable_amount < min_lot:
                    self.log.warning("【买入失败】{} | 原因: 现金不足 (需要{:.2f}, 可用{:.2f})".format(security, total_cost, available_cash))
                    return None

                self.log.warning("当前账户资金不足，调整{}下单数量为{}股（目标{:.2f}元，实际{:.2f}元）".format(
                    security, max_affordable_amount, value, max_affordable_amount * current_price))
                amount = max_affordable_amount
        else:
            # 目标数量 < 最小单位，直接取消交易（避免资金分配失衡）
            self.log.warning("【下单失败】{} | 原因: 分配金额不足{}股 (分配{:.2f}元, 价格{:.2f}元, 可用现金{:.2f}元)".format(
                security, min_lot, value, current_price, available_cash))
            return None

        # 创建订单
        order_id, order = self.order_processor.create_order(security, amount, current_price)

        self.log.info("生成订单，订单号:{}，股票代码：{}，数量：买入{}股".format(order_id, security, amount))

        # 执行订单
        success = self.order_processor.execute_buy(security, amount, current_price)

        if success:
            order.status = '8'
            order.filled = amount

        return order.id if success else None

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
        # 获取当前持仓市值
        current_value = 0.0
        if security in self.context.portfolio.positions:
            position = self.context.portfolio.positions[security]
            current_value = position.amount * position.last_sale_price

        # 计算需要调整的价值
        delta_value = value - current_value

        if abs(delta_value) < 1:  # 价值差异小于1元，不调整
            return None

        # 使用 order_value 下单
        return self.order_value(security, delta_value, limit_price)

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

        if security is None:
            return self.context.blotter.open_orders
        else:
            return [o for o in self.context.blotter.open_orders if o.symbol == security]

    def get_order(self, order_id: str) -> Optional[Any]:
        """获取指定订单

        Args:
            order_id: 订单id

        Returns:
            Order对象或None
        """
        if not self.context or not self.context.blotter:
            return None

        for order in self.context.blotter.open_orders:
            if order.id == order_id:
                return order
        return None

    def get_trades(self) -> list:
        """获取当日成交订单

        Returns:
            成交订单列表
        """
        # 回测中所有已成交订单都会从open_orders移除，需要单独记录
        # 这里简化实现，返回空列表
        return []

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

    def run_daily(self, context: Any, func: Callable, time: str = '9:31') -> None:
        """定时运行函数

        Args:
            context: Context对象
            func: 自定义函数，接受context参数
            time: 触发时间，格式HH:MM
        """
        _ = (context, func, time)  # 回测中不执行
        pass

    # ==================== 技术指标API ====================

    @validate_lifecycle
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

    @validate_lifecycle
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

    @validate_lifecycle
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

    @validate_lifecycle
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
