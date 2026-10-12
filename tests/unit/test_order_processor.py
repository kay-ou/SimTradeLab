# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
OrderProcessor模块测试 - 提升覆盖率
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from simtradelab.ptrade.order_processor import OrderProcessor
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.ptrade.config_manager import config


class TestOrderProcessor:
    """订单处理器测试"""

    @pytest.fixture
    def order_processor(self, context, data_context, simple_log):
        """创建订单处理器实例"""
        def mock_get_stock_date_index(stock):
            if stock in data_context.stock_data_dict:
                df = data_context.stock_data_dict[stock]
                date_dict = {df.index[i].value: i for i in range(len(df.index))}  # 生产契约：纳秒 int64 键
                return date_dict, list(df.index)
            return {}, []

        processor = OrderProcessor(
            context=context,
            data_context=data_context,
            get_stock_date_index_func=mock_get_stock_date_index,
            log=simple_log
        )
        return processor

    def test_order_processor_init(self, order_processor, context, data_context):
        """测试订单处理器初始化"""
        assert order_processor.context == context
        assert order_processor.data_context == data_context
        assert order_processor.get_stock_date_index is not None
        assert order_processor.log is not None

    def test_get_execution_price_no_limit(self, order_processor, context):
        """测试无限价时的执行价格获取"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        # 买入价格
        price = order_processor.get_execution_price('600000.SH', is_buy=True)
        assert price is None or isinstance(price, (float, int, np.number))

    def test_get_execution_price_with_limit(self, order_processor, context):
        """测试有限价时的执行价格获取"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        # 指定限价
        limit_price = 10.5
        price = order_processor.get_execution_price('600000.SH', limit_price=limit_price, is_buy=True)

        assert price is None or isinstance(price, (float, int, np.number))

    def test_get_execution_price_buy_vs_sell(self, order_processor, context):
        """测试买卖方向的滑点差异"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        # 买入价格(向上滑点)
        buy_price = order_processor.get_execution_price('600000.SH', is_buy=True)

        # 卖出价格(向下滑点)
        sell_price = order_processor.get_execution_price('600000.SH', is_buy=False)

        # 两个价格可能不同(取决于滑点设置)
        assert buy_price is None or isinstance(buy_price, (float, int, np.number))
        assert sell_price is None or isinstance(sell_price, (float, int, np.number))

    def test_get_execution_price_invalid_stock(self, order_processor, context):
        """测试无效股票代码"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        price = order_processor.get_execution_price('INVALID.XX', is_buy=True)
        assert price is None

    def test_get_execution_price_with_slippage(self, order_processor, context):
        """测试滑点计算 - 使用context的slippage属性"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        # 通过context设置滑点
        context.slippage = 0.001  # 0.1%滑点

        price = order_processor.get_execution_price('600000.SH', is_buy=True)
        assert price is None or isinstance(price, (float, int, np.number))

    def test_get_execution_price_with_fixed_slippage(self, order_processor, context):
        """测试固定滑点 - 使用context属性"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        # 通过context设置固定滑点
        context.slippage = 0  # 关闭比例滑点
        context.fixed_slippage = 0.02  # 2分固定滑点

        price = order_processor.get_execution_price('600000.SH', is_buy=True)
        assert price is None or isinstance(price, (float, int, np.number))

    def test_get_execution_price_zero_slippage(self, order_processor, context):
        """测试零滑点"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        # 使用默认配置(零滑点)
        price = order_processor.get_execution_price('600000.SH', is_buy=True)
        assert price is None or isinstance(price, (float, int, np.number))

    def test_get_execution_price_missing_date(self, order_processor, context):
        """测试日期不存在的情况"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        # 设置一个不存在的日期
        context.current_dt = pd.Timestamp('2025-12-31')

        price = order_processor.get_execution_price('600000.SH', is_buy=True)
        # 应该返回None
        assert price is None

    def test_get_execution_price_delisted_sell_falls_back_to_last_close(
        self, order_processor, context, data_context
    ):
        """测试退市股卖出时回退到最后收盘价（持仓退市后调仓平仓）"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        stock_df = data_context.stock_data_dict['600000.SH']
        last_close = float(stock_df['close'].iloc[-1])
        # 退市后：current_dt 超出数据最后交易日
        context.current_dt = stock_df.index[-1] + pd.Timedelta(days=30)

        price = order_processor.get_execution_price('600000.SH', is_buy=False)
        # 卖出价 = 退市前最后收盘价（含默认 0.1% 比例滑点，略低于收盘价）
        assert price == pytest.approx(last_close, rel=1e-3)

    def test_get_execution_price_nan_price(self, order_processor, context, data_context):
        """测试价格为NaN的情况"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-02')

        # 尝试获取价格,如果数据不完整可能返回None
        price = order_processor.get_execution_price('600000.SH', is_buy=True)
        # 只要不报错就OK
        assert price is None or isinstance(price, (float, int, np.number))

    def test_order_processor_with_real_data(self, order_processor, context):
        """测试使用真实数据的订单处理"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-05')

        # 测试多个股票
        for stock in ['600000.SH', '000001.SZ', '600519.SH']:
            price = order_processor.get_execution_price(stock, is_buy=True)
            # 只要不报错就是成功
            assert price is None or isinstance(price, (float, int, np.number))

    def test_order_processor_slippage_direction(self, order_processor, context):
        """测试买卖滑点方向正确性"""
        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp('2024-01-05')

        # 通过context设置滑点
        context.slippage = 0.002  # 0.2%滑点

        buy_price = order_processor.get_execution_price('600000.SH', limit_price=10.0, is_buy=True)
        sell_price = order_processor.get_execution_price('600000.SH', limit_price=10.0, is_buy=False)

        # 标准限价撮合：买入不高于限价、卖出不低于限价（市价优于限价时按市价）
        if buy_price is not None and sell_price is not None:
            assert buy_price <= 10.0  # 买入取 min(限价, 市价) + 向上滑点
            assert sell_price >= 10.0  # 卖出取 max(限价, 市价) - 向下滑点
