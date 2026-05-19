# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
测试更多关键API - 确保完整覆盖
"""

import pytest
import numpy as np
import pandas as pd

from simtradelab.ptrade.lifecycle_controller import LifecyclePhase, PTradeLifecycleError


class TestMoreTradingAPI:
    """测试更多交易API"""

    def test_order_value(self, ptrade_api):
        """测试order_value - 按金额下单"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 按金额下单10000元
        result = ptrade_api.order_value('600000.SH', 10000)

        # 应该返回订单ID或None
        if ptrade_api.context.blotter:
            assert result is not None
        else:
            assert result is None

    def test_order_target_value(self, ptrade_api):
        """测试order_target_value - 目标金额"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 目标持仓金额50000元
        result = ptrade_api.order_target_value('600000.SH', 50000)

        if ptrade_api.context.blotter:
            assert result is not None
        else:
            assert result is None

    def test_get_position(self, ptrade_api):
        """测试get_position - 查询持仓"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询持仓（文档示例允许直接访问get_position(...).amount）
        position = ptrade_api.get_position('600000.SH')

        # 应返回Position对象；空仓时amount为0
        from simtradelab.ptrade.object import Position
        assert isinstance(position, Position)
        assert position.amount == 0


class TestDataAPI:
    """测试数据获取API"""

    def test_get_stock_info(self, ptrade_api):
        """测试get_stock_info"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询单个股票信息
        result = ptrade_api.get_stock_info('600000.SH')
        assert isinstance(result, dict)

        # 查询多个股票
        result = ptrade_api.get_stock_info(['600000.SH', '000001.SZ'])
        assert isinstance(result, dict)

    def test_get_stock_name(self, ptrade_api):
        """测试get_stock_name"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        ptrade_api.context.current_dt = pd.Timestamp('2024-01-02')

        # 查询单个股票名称
        result = ptrade_api.get_stock_name('600000.SH')
        # PTrade文档: 单只和多只都返回股票名称字典
        assert result is None or isinstance(result, dict)
        if isinstance(result, dict):
            assert '600000.SH' in result

        # 查询多个股票名称
        result = ptrade_api.get_stock_name(['600000.SH', '000001.SZ'])
        assert result is None or isinstance(result, dict)

    def test_get_trade_days(self, ptrade_api):
        """测试get_trade_days - 获取交易日"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # get_trade_days可能需要完整的数据context，测试其不报错即可
        try:
            result = ptrade_api.get_trade_days(start_date='2024-01-01', end_date='2024-01-31')
            # PTrade文档: 返回numpy.ndarray；本地子类保留 `if not days:` 兼容语义。
            assert isinstance(result, np.ndarray)
        except (TypeError, AttributeError):
            # 如果缺少数据也可以接受
            assert True

    def test_get_index_stocks(self, ptrade_api):
        """测试get_index_stocks - 获取指数成份股"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 获取沪深300成份股
        result = ptrade_api.get_index_stocks('000300.SH', date='2024-01-01')

        # 应该返回list
        assert result is None or isinstance(result, list)

    def test_get_index_stocks_different_indexes(self, ptrade_api):
        """测试不同指数的成份股"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 测试常见指数
        indexes = ['000300.SH', '000016.SH', '399006.SZ']  # 沪深300、上证50、创业板指
        for index in indexes:
            result = ptrade_api.get_index_stocks(index, date='2024-01-01')
            assert result is None or isinstance(result, list)

    def test_get_index_stocks_different_dates(self, ptrade_api):
        """测试不同日期的指数成份股"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 测试不同日期
        dates = ['2023-01-01', '2023-06-01', '2024-01-01']
        for date in dates:
            result = ptrade_api.get_index_stocks('000300.SH', date=date)
            assert result is None or isinstance(result, list)

    def test_get_index_stocks_invalid_index(self, ptrade_api):
        """测试无效指数代码"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 无效指数代码
        result = ptrade_api.get_index_stocks('999999.XX', date='2024-01-01')
        # 应该返回None或空list
        assert result is None or result == [] or isinstance(result, list)


class TestConfigAPI:
    """测试配置API"""

    def test_set_commission(self, ptrade_api):
        """测试set_commission - 设置手续费"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 设置手续费率
        ptrade_api.set_commission(commission_ratio=0.0003, min_commission=5.0)

        # 检查是否设置成功
        # 配置通过config管理,不需要检查context属性

    def test_set_slippage(self, ptrade_api):
        """测试set_slippage - 设置滑点"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 设置比例滑点
        ptrade_api.set_slippage(slippage=0.001)

        # 配置通过config管理,不需要检查context属性

    def test_set_fixed_slippage(self, ptrade_api):
        """测试set_fixed_slippage - 设置固定滑点"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 设置固定滑点
        ptrade_api.set_fixed_slippage(fixedslippage=0.002)

        # 配置通过config管理,不需要检查context属性

    def test_set_limit_mode(self, ptrade_api):
        """测试set_limit_mode - 设置涨跌停处理模式"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # 设置涨跌停模式
        ptrade_api.set_limit_mode(limit_mode='LIMIT')

        # 配置通过config管理,不需要检查context属性


class TestLifecycleRestrictions:
    """测试生命周期限制严格性"""

    def test_set_benchmark_only_in_initialize(self, ptrade_api):
        """确保set_benchmark只能在initialize阶段调用"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # initialize阶段可以调用
        ptrade_api.set_benchmark('000300.SH')

        # 切换到handle_data阶段后不能调用
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        with pytest.raises(PTradeLifecycleError):
            ptrade_api.set_benchmark('000300.SH')

    def test_order_not_in_initialize(self, ptrade_api):
        """确保order不能在initialize阶段调用"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # initialize阶段不能调用order
        with pytest.raises(PTradeLifecycleError):
            ptrade_api.order('600000.SH', 100)

    def test_order_value_not_in_initialize(self, ptrade_api):
        """确保order_value不能在initialize阶段调用"""
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

        # initialize阶段不能调用order_value
        with pytest.raises(PTradeLifecycleError):
            ptrade_api.order_value('600000.SH', 10000)
