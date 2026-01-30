# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
数据上下文 - 封装所有数据源
"""


from __future__ import annotations

import pandas as pd


class DataContext:
    """数据上下文容器"""

    def __init__(
        self,
        stock_data_dict,
        valuation_dict,
        fundamentals_dict,
        exrights_dict,
        benchmark_data,
        stock_metadata,
        index_constituents: dict,
        stock_status_history: dict,
        adj_pre_cache,
        adj_post_cache=None,
        dividend_cache=None,
        trade_days=None
    ):
        """初始化数据上下文

        Args:
            stock_data_dict: 股票数据字典（LazyDataDict）
            valuation_dict: 估值数据字典
            fundamentals_dict: 基本面数据字典
            exrights_dict: 除权数据字典
            benchmark_data: 基准数据字典
            stock_metadata: 股票元数据DataFrame
            index_constituents: 指数成份股字典
            stock_status_history: 股票状态历史字典
            adj_pre_cache: 前复权因子缓存
            adj_post_cache: 后复权因子缓存
            dividend_cache: 分红事件缓存
            trade_days: 交易日历（DatetimeIndex）
        """
        self.stock_data_dict = stock_data_dict
        self.valuation_dict = valuation_dict
        self.fundamentals_dict = fundamentals_dict
        self.exrights_dict = exrights_dict
        self.benchmark_data = benchmark_data
        self.stock_metadata = stock_metadata
        self.index_constituents = index_constituents
        self.stock_status_history = stock_status_history
        self.adj_pre_cache = adj_pre_cache
        self.adj_post_cache = adj_post_cache
        self.dividend_cache = dividend_cache if dividend_cache is not None else {}
        self.trade_days = trade_days

        # 预解析 stock_metadata 日期列为 Timestamp（优化 get_Ashares 性能）
        if stock_metadata is not None and not stock_metadata.empty:
            if 'listed_date' in stock_metadata.columns:
                self.listed_date_ts = pd.to_datetime(stock_metadata['listed_date'], format='mixed', errors='coerce')
            else:
                self.listed_date_ts = None
            if 'de_listed_date' in stock_metadata.columns:
                self.de_listed_date_ts = pd.to_datetime(stock_metadata['de_listed_date'], format='mixed', errors='coerce')
            else:
                self.de_listed_date_ts = None
        else:
            self.listed_date_ts = None
            self.de_listed_date_ts = None

        # 预建行业索引（优化 get_industry_stocks 性能）
        self._industry_index = None
