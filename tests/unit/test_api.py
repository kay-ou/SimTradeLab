# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
测试交易API
"""

import numpy as np
import pandas as pd
import pytest

from simtradelab.ptrade.lifecycle_controller import LifecyclePhase, PTradeLifecycleError


class TestOrderAPI:
    """测试交易订单API"""

    def test_order_lifecycle_validation(self, ptrade_api):
        """测试order函数的生命周期验证"""
        # order只能在handle_data阶段调用
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 在initialize阶段调用order应该报错
        with pytest.raises(PTradeLifecycleError):
            ptrade_api.order('600000.SH', 100)

    def test_order_in_handle_data(self, ptrade_api):
        """测试在handle_data阶段调用order"""
        # 先设置为initialize，再转到handle_data阶段
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 调用order应该成功（返回订单ID或None）
        result = ptrade_api.order('600000.SH', 100)

        # 订单应该被创建（如果有blotter）或返回None
        if ptrade_api.context.blotter:
            assert result is not None
        else:
            assert result is None

    def test_order_target(self, ptrade_api):
        """测试order_target函数"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 目标100股
        result = ptrade_api.order_target('600000.SH', 100)

        # 应该下单100股
        if ptrade_api.context.blotter:
            assert result is not None
        else:
            assert result is None


class TestDataQueryAPI:
    """测试数据查询API"""

    def test_get_price_basic(self, ptrade_api):
        """测试get_price函数基本功能"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询单个股票的价格
        result = ptrade_api.get_price('600000.SH', count=5, fields='close')

        # 应该返回DataFrame
        assert result is None or isinstance(result, pd.DataFrame)

    def test_get_history(self, ptrade_api):
        """测试get_history函数"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询历史数据
        result = ptrade_api.get_history(count=5, field='close', security_list=['600000.SH', '000001.SZ'])

        # 应该返回DataFrame或dict
        assert result is None or isinstance(result, (pd.DataFrame, dict))

    def test_prebuilt_date_index_matches_lazy_contract(self, ptrade_api):
        """预构建索引应与懒加载索引使用相同的 int64 日期契约。"""
        stock = '600000.SH'
        query_dt = pd.Timestamp('2024-01-02 14:30')

        ptrade_api.prebuild_date_index(stocks=[stock])

        date_dict, sorted_i8 = ptrade_api.get_stock_date_index(stock)
        assert isinstance(sorted_i8, np.ndarray)
        assert sorted_i8.dtype == np.dtype('int64')
        assert date_dict[pd.Timestamp('2024-01-02').value] == 1

        stock_df = ptrade_api.data_context.stock_data_dict[stock]
        assert ptrade_api._resolve_daily_index(stock, stock_df, query_dt) == 1


class TestStockStatusAPI:
    """测试股票状态API"""

    def test_get_stock_status(self, ptrade_api):
        """测试get_stock_status函数"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 测试查询ST状态
        result = ptrade_api.get_stock_status('600000.SH', query_type='ST')
        assert isinstance(result, dict)

        # 测试查询多个股票
        result = ptrade_api.get_stock_status(['600000.SH', '000001.SZ'], query_type='ST')
        assert isinstance(result, dict)

    def test_check_limit(self, ptrade_api):
        """测试涨跌停检查"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # check_limit返回dict
        result = ptrade_api.check_limit('600000.SH')
        assert isinstance(result, dict)

        # 检查多个股票
        result = ptrade_api.check_limit(['600000.SH', '000001.SZ'])
        assert isinstance(result, dict)


class TestSetAPI:
    """测试设置API"""

    def test_set_universe(self, ptrade_api):
        """测试set_universe函数"""
        # set_universe可以在initialize调用
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        stocks = ['600000.SH', '000001.SZ', '600519.SH']
        ptrade_api.set_universe(stocks)

        # 检查股票池是否设置
        assert len(ptrade_api.active_universe) == 3
        assert '600000.SH' in ptrade_api.active_universe

    def test_set_benchmark(self, ptrade_api):
        """测试set_benchmark只能在initialize调用"""
        # 在initialize阶段可以调用
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.set_benchmark('000300.SH')

        # 在handle_data阶段应该报错
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        with pytest.raises(PTradeLifecycleError):
            ptrade_api.set_benchmark('000300.SH')
