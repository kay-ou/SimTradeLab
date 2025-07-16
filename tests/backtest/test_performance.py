# -*- coding: utf-8 -*-
"""
性能分析模块测试
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest

from simtradelab.backtest.performance import PerformanceManager


class TestPerformanceManager:
    """
    测试 PerformanceManager 的功能
    """

    def test_initialization(self):
        """测试初始化"""
        pm = PerformanceManager(initial_capital=Decimal("100000"))
        assert pm.initial_capital == Decimal("100000")
        assert isinstance(pm.daily_portfolio_values, dict)
        assert pm.returns is None

    def test_record_daily_portfolio_value(self):
        """测试记录每日投资组合价值"""
        pm = PerformanceManager(initial_capital=Decimal("100000"))

        date1 = datetime(2023, 1, 1, 12, 0, 0)
        value1 = Decimal("101000")
        pm.record_daily_portfolio_value(date1, value1)

        # 验证日期是否被正确规范化
        assert date1.date() in pm.daily_portfolio_values
        assert pm.daily_portfolio_values[date1.date()] == value1

        date2 = datetime(2023, 1, 2)
        value2 = Decimal("100500")
        pm.record_daily_portfolio_value(date2, value2)
        assert pm.daily_portfolio_values[date2.date()] == value2

        assert len(pm.daily_portfolio_values) == 2

    def test_calculate_returns(self):
        """测试收益率计算"""
        pm = PerformanceManager(initial_capital=Decimal("100000"))

        # 准备数据
        dates = [datetime(2023, 1, 1), datetime(2023, 1, 2), datetime(2023, 1, 3)]
        values = [Decimal("100000"), Decimal("101000"), Decimal("100500")]

        for d, v in zip(dates, values):
            pm.record_daily_portfolio_value(d, v)

        pm._calculate_returns()

        assert pm.returns is not None
        assert isinstance(pm.returns, pd.Series)
        assert len(pm.returns) == 3

        # 验证计算结果
        assert pm.returns.iloc[0] == 0.0  # 第一个收益率为0
        assert pytest.approx(pm.returns.iloc[1]) == 0.01  # (101000 - 100000) / 100000
        assert (
            pytest.approx(pm.returns.iloc[2]) == -0.004950495
        )  # (100500 - 101000) / 101000

    def test_calculate_returns_no_data(self):
        """测试没有数据时计算收益率"""
        pm = PerformanceManager(initial_capital=Decimal("100000"))
        pm._calculate_returns()
        assert pm.returns is not None
        assert pm.returns.empty

    def test_get_summary(self):
        """测试获取性能摘要"""
        pm = PerformanceManager(initial_capital=Decimal("100000"))

        # 准备数据
        dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(10)]
        values = [
            Decimal("100000"),
            Decimal("101000"),
            Decimal("100500"),
            Decimal("102000"),
            Decimal("101500"),
            Decimal("103000"),
            Decimal("102500"),
            Decimal("104000"),
            Decimal("103500"),
            Decimal("105000"),
        ]

        for d, v in zip(dates, values):
            pm.record_daily_portfolio_value(d, v)

        summary = pm.get_summary()

        assert isinstance(summary, dict)
        assert "Annual return" in summary
        assert "Cumulative returns" in summary
        assert "Sharpe ratio" in summary
        assert "Max drawdown" in summary
