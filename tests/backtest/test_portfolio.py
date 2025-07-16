# -*- coding: utf-8 -*-
"""
高保真回测引擎的核心投资组合管理器测试。
"""

import unittest
from datetime import datetime

from simtradelab.backtest.portfolio import PortfolioManager
from simtradelab.core.events.contracts import FillEvent


class TestPortfolioManager(unittest.TestCase):
    """测试PortfolioManager"""

    def setUp(self):
        """测试初始化"""
        self.initial_cash = 100000.0
        self.pm = PortfolioManager(initial_cash=self.initial_cash)

    def test_initialization(self):
        """测试PortfolioManager初始化"""
        self.assertEqual(self.pm.portfolio.cash, self.initial_cash)
        self.assertEqual(self.pm.portfolio.portfolio_value, self.initial_cash)
        self.assertEqual(len(self.pm.portfolio.positions), 0)

    def test_buy_fill(self):
        """测试买入成交事件"""
        fill_event = FillEvent(
            order_id="order1",
            symbol="AAPL",
            quantity=100,
            price=150.0,
            commission=5.0,
            timestamp=datetime.now(),
        )
        self.pm.on_fill(fill_event)

        # 验证现金
        expected_cash = self.initial_cash - (100 * 150.0) - 5.0
        self.assertAlmostEqual(self.pm.portfolio.cash, expected_cash)

        # 验证持仓
        self.assertEqual(len(self.pm.portfolio.positions), 1)
        aapl_pos = self.pm.portfolio.positions["AAPL"]
        self.assertEqual(aapl_pos.amount, 100)
        self.assertEqual(aapl_pos.cost_basis, 150.0)
        self.assertEqual(aapl_pos.last_sale_price, 150.0)

        # 验证投资组合价值
        expected_portfolio_value = expected_cash + (100 * 150.0)
        self.assertAlmostEqual(
            self.pm.portfolio.portfolio_value, expected_portfolio_value
        )

    def test_multiple_buys(self):
        """测试多次买入同一标的"""
        fill1 = FillEvent(
            order_id="order1", symbol="AAPL", quantity=100, price=150.0, commission=5.0
        )
        self.pm.on_fill(fill1)

        fill2 = FillEvent(
            order_id="order2", symbol="AAPL", quantity=50, price=160.0, commission=2.5
        )
        self.pm.on_fill(fill2)

        # 验证持仓
        aapl_pos = self.pm.portfolio.positions["AAPL"]
        self.assertEqual(aapl_pos.amount, 150)

        # 验证平均成本
        expected_cost_basis = ((100 * 150.0) + (50 * 160.0)) / 150
        self.assertAlmostEqual(aapl_pos.cost_basis, expected_cost_basis)

    def test_sell_fill(self):
        """测试卖出成交事件"""
        # 先买入
        buy_fill = FillEvent(
            order_id="order1", symbol="AAPL", quantity=100, price=150.0, commission=5.0
        )
        self.pm.on_fill(buy_fill)

        # 再卖出
        sell_fill = FillEvent(
            order_id="order2", symbol="AAPL", quantity=-50, price=160.0, commission=2.5
        )
        self.pm.on_fill(sell_fill)

        # 验证现金
        expected_cash = self.initial_cash - (100 * 150.0) - 5.0 + (50 * 160.0) - 2.5
        self.assertAlmostEqual(self.pm.portfolio.cash, expected_cash)

        # 验证持仓
        aapl_pos = self.pm.portfolio.positions["AAPL"]
        self.assertEqual(aapl_pos.amount, 50)

    def test_update_market_value(self):
        """测试市值更新"""
        buy_fill = FillEvent(
            order_id="order1", symbol="AAPL", quantity=100, price=150.0
        )
        self.pm.on_fill(buy_fill)

        # 更新市价
        self.pm.update_market_value({"AAPL": 170.0})

        aapl_pos = self.pm.portfolio.positions["AAPL"]
        self.assertEqual(aapl_pos.last_sale_price, 170.0)

        expected_portfolio_value = self.pm.portfolio.cash + (100 * 170.0)
        self.assertAlmostEqual(
            self.pm.portfolio.portfolio_value, expected_portfolio_value
        )


if __name__ == "__main__":
    unittest.main()
