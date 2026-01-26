# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
研究模式API - 用于Jupyter Notebook交互式使用

"""

import logging
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.context import Context
from simtradelab.ptrade.object import Portfolio
from simtradelab.service.data_server import DataServer

_global_api = None
_global_data_server = None


def init_api(data_path=None, required_data=None):
    """初始化研究API（延迟加载模式）

    Args:
        data_path: 数据路径，默认None自动查找项目data目录
        required_data: 需要加载的数据类型，默认None（按需加载）
                      可显式指定: {'price', 'exrights', 'valuation', 'fundamentals'}

    Returns:
        PtradeAPI实例

    Note:
        如果required_data=None，数据将在首次访问时按需加载
    """
    global _global_api, _global_data_server

    # 默认不预加载，按需加载（传递空集合，不是None）
    if required_data is None:
        required_data = set()

    logging.basicConfig(level=logging.INFO, format='%(message)s')
    log = logging.getLogger('research_api')

    if required_data:
        print(f"正在加载数据: {', '.join(required_data)}...")
    else:
        print(f"初始化API（按需加载模式）...")

    _global_data_server = DataServer(required_data=required_data)

    # 创建portfolio和context
    portfolio = Portfolio(initial_capital=100000)
    context = Context(portfolio=portfolio)

    # 创建API
    _global_api = PtradeAPI(
        data_context=_global_data_server,
        context=context,
        log=log
    )

    print(f"✓ API初始化完成")
    keys_list = list(_global_data_server.benchmark_data.keys()) # type: ignore
    print(f"✓ 可用基准(共 {len(keys_list)} 个): {', '.join(keys_list[:10])} ...")

    return _global_api


def get_api():
    """获取已初始化的API实例"""
    global _global_api
    if _global_api is None:
        print("API未初始化，自动初始化中...")
        return init_api()
    return _global_api


def get_Ashares(date=None):
    return get_api().get_Ashares(date)
# 便捷函数
def get_index_stocks(index_code, date=None):
    """获取指数成分股"""
    return get_api().get_index_stocks(index_code, date)


def get_stock_info(stocks, field=None):
    """获取股票信息"""
    return get_api().get_stock_info(stocks, field)


def get_stock_name(stocks):
    """获取股票名称"""
    return get_api().get_stock_name(stocks)


def get_stock_exrights(stock_code, date=None):
    """获取除权除息数据"""
    return get_api().get_stock_exrights(stock_code, date)


def get_price(stock, start_date=None, end_date=None, frequency='1d', fields=None, fq='pre', count=None):
    """获取价格数据"""
    return get_api().get_price(stock, start_date, end_date, frequency, fields, fq, count)


def get_history(count, stock, field, end_date=None, fq='pre'):
    """获取历史数据"""
    return get_api().get_history(count, stock, field, end_date, fq)


def get_stock_status(stocks, query_type='ST', query_date=None):
    """获取股票状态"""
    return get_api().get_stock_status(stocks, query_type, query_date)


def get_fundamentals(stocks, table, fields, date=None):
    """获取财务数据

    Args:
        stocks: 股票代码列表
        table: 表名
        fields: 字段列表
        date: 查询日期（默认为当前日期）
    """
    return get_api().get_fundamentals(stocks, table, fields, date)


def get_industry_stocks(industry_code=None):
    """获取行业成分股"""
    return get_api().get_industry_stocks(industry_code)


def check_limit(stocks, date=None):
    """检查涨跌停"""
    return get_api().check_limit(stocks, date)


# 导出所有公开函数
__all__ = [
    'init_api',
    'get_api',
    'get_Ashares',
    'get_index_stocks',
    'get_stock_info',
    'get_stock_name',
    'get_stock_exrights',
    'get_price',
    'get_history',
    'get_stock_status',
    'get_fundamentals',
    'get_industry_stocks',
    'check_limit',
]

