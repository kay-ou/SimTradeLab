# -*- coding: utf-8 -*-
"""
PTrade模型对象测试
"""

import pytest
from simtradelab.adapters.ptrade.models import Portfolio, Position, Blotter
from simtradelab.adapters.ptrade.context import PTradeContext


class TestPTradeContext:
    """测试PTrade上下文对象"""

    def test_context_creation(self):
        """测试上下文创建"""
        portfolio = Portfolio(cash=1000000)
        context = PTradeContext(portfolio=portfolio)

        assert context.portfolio is portfolio
        assert context.current_dt is None
        assert context.universe == []
        assert context.benchmark is None
        assert hasattr(context, "g")
        assert hasattr(context, "blotter")


class TestPortfolio:
    """测试投资组合对象"""

    def test_portfolio_creation(self):
        """测试投资组合创建"""
        portfolio = Portfolio(cash=1000000)

        assert portfolio.cash == 1000000
        assert portfolio._starting_cash == 1000000
        assert portfolio.positions == {}
        assert portfolio.total_value == 1000000
        assert portfolio.returns == 0.0
        assert portfolio.pnl == 0.0

    def test_portfolio_with_positions(self):
        """测试有持仓的投资组合"""
        portfolio = Portfolio(cash=500000)
        portfolio._starting_cash = 1000000

        # 添加持仓
        position = Position(
            sid="000001.SZ",
            enable_amount=1000,
            amount=1000,
            cost_basis=10.0,
            last_sale_price=12.0,
        )
        portfolio.positions["000001.SZ"] = position

        # 更新投资组合价值
        portfolio.update_portfolio_value()

        assert portfolio.total_value == 500000 + 12000  # 现金 + 持仓市值
        assert portfolio.returns == (512000 - 1000000) / 1000000
        assert portfolio.pnl == 512000 - 1000000


class TestPosition:
    """测试持仓对象"""

    def test_position_creation(self):
        """测试持仓创建"""
        position = Position(
            sid="000001.SZ",
            enable_amount=1000,
            amount=1000,
            cost_basis=10.0,
            last_sale_price=10.0,
        )

        assert position.sid == "000001.SZ"
        assert position.security == "000001.SZ"  # 兼容性属性
        assert position.amount == 1000
        assert position.cost_basis == 10.0
        assert position.last_sale_price == 10.0
        assert position.market_value == 10000
        assert position.pnl == 0.0
        assert position.returns == 0.0

    def test_position_with_price_change(self):
        """测试价格变化后的持仓"""
        position = Position(
            sid="000001.SZ",
            enable_amount=1000,
            amount=1000,
            cost_basis=10.0,
            last_sale_price=12.0,
        )

        assert position.market_value == 12000
        assert position.pnl == 2000
        assert position.returns == 0.2


class TestBlotter:
    """测试订单管理器"""

    def test_blotter_creation(self):
        """测试订单管理器创建"""
        blotter = Blotter()

        assert blotter.orders == {}
        assert blotter.order_id_counter == 0

    def test_create_order(self):
        """测试创建订单"""
        blotter = Blotter()

        order_id = blotter.create_order("000001.SZ", 1000, 10.0)

        assert order_id == "order_0"
        assert blotter.order_id_counter == 1

        order = blotter.get_order(order_id)
        assert order is not None
        assert order.symbol == "000001.SZ"
        assert order.amount == 1000
        assert order.limit == 10.0
        assert order.status == "new"

    def test_cancel_order(self):
        """测试撤销订单"""
        blotter = Blotter()

        order_id = blotter.create_order("000001.SZ", 1000, 10.0)
        success = blotter.cancel_order(order_id)

        assert success is True

        order = blotter.get_order(order_id)
        assert order.status == "cancelled"

        # 测试撤销不存在的订单
        success = blotter.cancel_order("nonexistent")
        assert success is False

    def test_multiple_orders(self):
        """测试多个订单管理"""
        blotter = Blotter()

        # 创建多个订单
        order_id1 = blotter.create_order("000001.SZ", 1000, 10.0)
        order_id2 = blotter.create_order("000002.SZ", 2000, 15.0)
        order_id3 = blotter.create_order("000001.SZ", -500, 12.0)

        # 验证订单数量
        assert len(blotter.orders) == 3
        assert blotter.order_id_counter == 3

        # 验证订单ID
        assert order_id1 == "order_0"
        assert order_id2 == "order_1"
        assert order_id3 == "order_2"

        # 验证订单内容
        order1 = blotter.get_order(order_id1)
        assert order1.symbol == "000001.SZ"
        assert order1.amount == 1000

        order2 = blotter.get_order(order_id2)
        assert order2.symbol == "000002.SZ"
        assert order2.amount == 2000

        order3 = blotter.get_order(order_id3)
        assert order3.symbol == "000001.SZ"
        assert order3.amount == -500

    def test_order_status_updates(self):
        """测试订单状态更新"""
        blotter = Blotter()

        order_id = blotter.create_order("000001.SZ", 1000, 10.0)
        order = blotter.get_order(order_id)

        # 初始状态
        assert order.status == "new"

        # 更新状态
        order.status = "submitted"
        assert order.status == "submitted"

        order.status = "filled"
        order.filled = 1000
        assert order.status == "filled"
        assert order.filled == 1000

    def test_order_attributes(self):
        """测试订单属性"""
        blotter = Blotter()

        order_id = blotter.create_order("000001.SZ", 1000, 10.0)
        order = blotter.get_order(order_id)

        # 验证基本属性
        assert order.id == order_id
        assert order.symbol == "000001.SZ"
        assert order.amount == 1000
        assert order.limit == 10.0
        assert order.status == "new"
        assert order.filled == 0
        assert order.dt is not None  # 创建时间应该被设置

        # 验证可选属性
        assert hasattr(order, 'dt')
        assert hasattr(order, 'filled')
        assert hasattr(order, 'status')