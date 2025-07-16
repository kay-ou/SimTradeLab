# -*- coding: utf-8 -*-
"""
PTrade回测路由器测试

测试路由器的路由和验证功能
"""

from unittest.mock import MagicMock

import pytest

from simtradelab.adapters.ptrade.context import PTradeContext, PTradeMode
from simtradelab.adapters.ptrade.models.order import Blotter
from simtradelab.adapters.ptrade.models.portfolio import Portfolio
from simtradelab.adapters.ptrade.routers.backtest import BacktestAPIRouter


class TestBacktestAPIRouter:
    """测试回测API路由器的路由功能"""

    @pytest.fixture
    def context(self):
        """创建测试上下文"""
        portfolio = Portfolio(cash=1000000)
        blotter = Blotter()
        context = PTradeContext(
            portfolio=portfolio, blotter=blotter, mode=PTradeMode.BACKTEST
        )
        context.universe = ["000001.XSHE", "000002.XSHE"]
        context.benchmark = "000300.SH"
        return context

    @pytest.fixture
    def service(self):
        return MagicMock()

    @pytest.fixture
    def router(self, context, service):
        router = BacktestAPIRouter(context=context)
        router._service = service
        return router

    def test_order_routing(self, router, service):
        """测试 order API 是否正确路由到服务层"""
        router.order("000001.XSHE", 100, 10.0)
        service.execute_order.assert_called_once_with("000001.XSHE", 100, 10.0)

    def test_cancel_order_routing(self, router, service):
        """测试 cancel_order API 是否正确路由到服务层"""
        router.cancel_order("order_123")
        service.cancel_order.assert_called_once_with("order_123")

    def test_get_position_routing(self, router, service):
        """测试 get_position API 是否正确路由到服务层"""
        router.get_position("000001.XSHE")
        service.get_position.assert_called_once_with("000001.XSHE")
