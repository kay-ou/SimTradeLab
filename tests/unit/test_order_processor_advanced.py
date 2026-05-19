# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
"""
OrderProcessor高级场景测试 - 补充覆盖率
"""

import numpy as np
import pandas as pd

from simtradelab.ptrade.lifecycle_controller import LifecyclePhase


class TestOrderProcessorEdgeCases:
    """订单处理器边界情况测试"""

    def test_get_execution_price_non_dataframe_stock_data(
        self, context, data_context, simple_log
    ):
        """测试非DataFrame的股票数据"""
        from simtradelab.ptrade.order_processor import OrderProcessor

        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp("2024-01-02")

        # 模拟非DataFrame数据
        data_context.stock_data_dict["BAD.STOCK"] = "not_a_dataframe"

        def mock_get_index(stock):
            return {}, []

        processor = OrderProcessor(context, data_context, mock_get_index, simple_log)
        price = processor.get_execution_price("BAD.STOCK", is_buy=True)

        assert price is None

    def test_get_execution_price_series_to_scalar(
        self, context, data_context, simple_log
    ):
        """测试Series价格转换为标量"""
        from simtradelab.ptrade.order_processor import OrderProcessor

        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp("2024-01-02")

        def mock_get_index(stock):
            if stock in data_context.stock_data_dict:
                df = data_context.stock_data_dict[stock]
                date_dict = {date: i for i, date in enumerate(df.index)}
                return date_dict, list(df.index)
            return {}, []

        processor = OrderProcessor(context, data_context, mock_get_index, simple_log)
        price = processor.get_execution_price("600000.SH", is_buy=True)

        # 应该成功转换为标量
        assert price is None or isinstance(price, (float, int, np.number))

    def test_get_execution_price_invalid_price(
        self, context, data_context, simple_log
    ):
        """测试无效价格（NaN或负数）"""
        from simtradelab.ptrade.order_processor import OrderProcessor

        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp("2024-01-02")

        # 创建包含无效价格的数据
        bad_data = pd.DataFrame(
            {
                "close": [np.nan, -10.0, 0.0],
                "open": [10.0, 10.0, 10.0],
                "high": [11.0, 11.0, 11.0],
                "low": [9.0, 9.0, 9.0],
            },
            index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
        )
        data_context.stock_data_dict["BAD.PRICE"] = bad_data

        def mock_get_index(stock):
            if stock in data_context.stock_data_dict:
                df = data_context.stock_data_dict[stock]
                date_dict = {date: i for i, date in enumerate(df.index)}
                return date_dict, list(df.index)
            return {}, []

        processor = OrderProcessor(context, data_context, mock_get_index, simple_log)

        # NaN价格应返回None
        context.current_dt = pd.Timestamp("2024-01-02")
        price = processor.get_execution_price("BAD.PRICE", is_buy=True)
        assert price is None

        # 负价格应返回None
        context.current_dt = pd.Timestamp("2024-01-03")
        price = processor.get_execution_price("BAD.PRICE", is_buy=True)
        assert price is None

        # 零价格应返回None
        context.current_dt = pd.Timestamp("2024-01-04")
        price = processor.get_execution_price("BAD.PRICE", is_buy=True)
        assert price is None

    def test_get_execution_price_zero_slippage(
        self, context, data_context, simple_log
    ):
        """测试零滑点场景"""
        from simtradelab.ptrade.order_processor import OrderProcessor
        from simtradelab.ptrade.config_manager import config

        context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
        context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
        context.current_dt = pd.Timestamp("2024-01-02")

        # 通过config设置零滑点
        config.update_trading_config(slippage=0.0, fixed_slippage=0.0)

        def mock_get_index(stock):
            if stock in data_context.stock_data_dict:
                df = data_context.stock_data_dict[stock]
                date_dict = {date: i for i, date in enumerate(df.index)}
                return date_dict, list(df.index)
            return {}, []

        processor = OrderProcessor(context, data_context, mock_get_index, simple_log)

        # 使用限价测试
        base_price = 10.0
        buy_price = processor.get_execution_price(
            "600000.SH", limit_price=base_price, is_buy=True
        )
        sell_price = processor.get_execution_price(
            "600000.SH", limit_price=base_price, is_buy=False
        )

        # 无滑点时买卖价格应该相等
        assert buy_price == base_price
        assert sell_price == base_price


    def test_calculate_commission_minimum_rate(self, context, data_context, simple_log):
        """测试极低手续费率（TradingConfig要求commission_ratio > 0）"""
        from simtradelab.ptrade.order_processor import OrderProcessor
        from simtradelab.ptrade.config_manager import config

        def mock_get_index(stock):
            return {}, []

        processor = OrderProcessor(context, data_context, mock_get_index, simple_log)

        # 设置极低手续费率
        config.update_trading_config(commission_ratio=0.0001)

        commission = processor.calculate_commission(100, 10.0, is_sell=False)
        # 佣金 = max(100*10*0.0001, min_commission) + 经手费
        assert commission > 0
