# -*- coding: utf-8 -*-
"""
数据上下文 - 封装所有数据源
"""

from typing import Dict


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
        stock_data_store,
        fundamentals_store,
        index_constituents: Dict,
        stock_status_history: Dict,
        adj_pre_cache,
        dividend_cache=None
    ):
        """初始化数据上下文

        Args:
            stock_data_dict: 股票数据字典（LazyDataDict）
            valuation_dict: 估值数据字典
            fundamentals_dict: 基本面数据字典
            exrights_dict: 除权数据字典
            benchmark_data: 基准数据字典
            stock_metadata: 股票元数据DataFrame
            stock_data_store: 股票数据HDF5存储
            fundamentals_store: 基本面数据HDF5存储
            index_constituents: 指数成份股字典
            stock_status_history: 股票状态历史字典
            adj_pre_cache: 复权因子缓存
            dividend_cache: 分红事件缓存
        """
        self.stock_data_dict = stock_data_dict
        self.valuation_dict = valuation_dict
        self.fundamentals_dict = fundamentals_dict
        self.exrights_dict = exrights_dict
        self.benchmark_data = benchmark_data
        self.stock_metadata = stock_metadata
        self.stock_data_store = stock_data_store
        self.fundamentals_store = fundamentals_store
        self.index_constituents = index_constituents
        self.stock_status_history = stock_status_history
        self.adj_pre_cache = adj_pre_cache
        self.dividend_cache = dividend_cache if dividend_cache is not None else {}
