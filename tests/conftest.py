# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
pytest配置和测试数据准备
"""

import numpy as np
import pandas as pd
import pytest

from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.cache_manager import cache_manager
from simtradelab.ptrade.config_manager import TradingConfig, config
from simtradelab.ptrade.context import Context, PTradeMode
from simtradelab.ptrade.lifecycle_controller import LifecycleController
from simtradelab.ptrade.object import Portfolio


@pytest.fixture(autouse=True)
def reset_cache():
    """每个测试前重置缓存"""
    cache_manager.clear_all()
    yield
    cache_manager.clear_all()


@pytest.fixture(autouse=True)
def reset_trading_config():
    """每个测试使用独立的默认交易配置。"""
    config.trading = TradingConfig()
    yield
    config.trading = TradingConfig()


@pytest.fixture
def test_dates():
    """生成测试日期序列"""
    start_date = pd.Timestamp('2024-01-01')
    return pd.date_range(start_date, periods=20, freq='D')


@pytest.fixture
def test_stock_data(test_dates):
    """生成测试股票数据"""
    stocks = ['600000.SH', '000001.SZ', '600519.SH']
    stock_data = {}

    np.random.seed(42)
    for i, stock in enumerate(stocks):
        base_price = 10 + i * 5
        data = pd.DataFrame({
            'open': np.random.uniform(base_price, base_price + 2, len(test_dates)),
            'high': np.random.uniform(base_price + 1, base_price + 3, len(test_dates)),
            'low': np.random.uniform(base_price - 2, base_price, len(test_dates)),
            'close': np.random.uniform(base_price, base_price + 2, len(test_dates)),
            'volume': np.random.uniform(1000000, 5000000, len(test_dates)),
            'amount': np.random.uniform(10000000, 50000000, len(test_dates)),
        }, index=test_dates)
        stock_data[stock] = data

    return stock_data


@pytest.fixture
def data_context(test_stock_data, test_dates):
    """创建简化的DataContext"""
    import pandas as pd

    class SimpleDataContext:
        def __init__(self):
            self.stock_data_dict = test_stock_data
            self.stock_status = {}
            self.valuation_dict = {}
            self.fundamentals_dict = {}
            self.exrights_dict = {}
            self.benchmark_data = {}
            # 使用空DataFrame而不是None
            self.stock_metadata = pd.DataFrame()
            self.index_constituents = {}
            self.stock_status_history = {}
            self.adj_pre_cache = None
            self.dividend_cache = {}
            # 添加交易日历（优化后 get_trading_day 需要）
            self.trade_days = test_dates
            # 预解析日期列（优化后 get_Ashares 需要）
            self.listed_date_ts = None
            self.de_listed_date_ts = None
            # 行业索引缓存
            self._industry_index = None

        def get_industry_index(self):
            """获取行业索引（空实现）"""
            if self._industry_index is None:
                self._industry_index = {}
            return self._industry_index

    return SimpleDataContext()


@pytest.fixture
def portfolio():
    """创建真实的Portfolio"""
    return Portfolio(
        initial_capital=1000000.0
    )


@pytest.fixture
def lifecycle_controller():
    """创建生命周期控制器"""
    return LifecycleController(strategy_mode="backtest")


@pytest.fixture
def context(portfolio, lifecycle_controller):
    """创建真实的Context"""
    ctx = Context(
        portfolio=portfolio,
        mode=PTradeMode.BACKTEST,
        capital_base=1000000.0,
        initialized=False
    )
    ctx._lifecycle_controller = lifecycle_controller
    return ctx


@pytest.fixture
def simple_log():
    """简单的日志类"""
    class SimpleLog:
        def debug(self, msg, *args):
            pass

        def info(self, msg, *args):
            print(f"[INFO] {msg % args if args else msg}")

        def warning(self, msg, *args):
            print(f"[WARN] {msg % args if args else msg}")

        def error(self, msg, *args):
            print(f"[ERROR] {msg % args if args else msg}")

    return SimpleLog()


@pytest.fixture
def ptrade_api(data_context, context, simple_log):
    """创建真实的PtradeAPI实例"""
    api = PtradeAPI(
        data_context=data_context,
        context=context,
        log=simple_log
    )
    return api
