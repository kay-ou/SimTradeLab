# -*- coding: utf-8 -*-
"""
PTrade实盘交易路由器测试
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock

from simtradelab.adapters.ptrade.routers.live_trading import LiveTradingAPIRouter
from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Portfolio, Position, Blotter
from simtradelab.core.event_bus import EventBus


class TestLiveTradingAPIRouter:
    """测试实盘交易API路由器"""

    @pytest.fixture
    def context(self):
        """创建测试上下文"""
        portfolio = Portfolio(cash=1000000)
        blotter = Blotter()
        context = PTradeContext(portfolio=portfolio, blotter=blotter)
        context.universe = ["000001.XSHE", "000002.XSHE"]
        context.benchmark = "000300.SH"
        return context

    @pytest.fixture
    def event_bus(self):
        """创建事件总线"""
        return EventBus()

    @pytest.fixture
    def router(self, context, event_bus):
        """创建实盘交易路由器实例"""
        router = LiveTradingAPIRouter(context=context, event_bus=event_bus)
        return router

    def test_router_initialization(self, router, context):
        """测试路由器初始化"""
        assert router.context is context
        assert router.event_bus is not None
        assert len(router._supported_apis) > 0

    def test_mode_support_check(self, router):
        """测试模式支持检查"""
        # 实盘交易模式支持的API
        assert router.is_mode_supported("order") is True
        assert router.is_mode_supported("get_history") is True
        assert router.is_mode_supported("ipo_stocks_order") is True
        assert router.is_mode_supported("after_trading_order") is True
        
        # 不支持的API
        assert router.is_mode_supported("nonexistent_api") is False

    def test_order_with_event_bus(self, router, event_bus):
        """测试下单功能及事件发布"""
        # 监听事件
        events = []
        def event_handler(event):
            events.append(event)
        
        event_bus.subscribe("trading.order.request", event_handler)
        
        # 执行下单
        order_id = router.order("000001.XSHE", 1000, 10.0)
        
        # 验证返回值
        assert order_id == "live_order_placeholder"
        
        # 验证事件发布
        assert len(events) == 1
        assert events[0].type == "trading.order.request"
        assert events[0].data["security"] == "000001.XSHE"
        assert events[0].data["amount"] == 1000
        assert events[0].data["limit_price"] == 10.0

    def test_order_value(self, router):
        """测试按价值下单"""
        order_id = router.order_value("000001.XSHE", 50000, 10.0)
        assert order_id == "live_order_placeholder"

    def test_order_target(self, router):
        """测试目标持仓下单"""
        # 先模拟有持仓
        position = Position(
            sid="000001.XSHE",
            amount=1000,
            enable_amount=1000,
            cost_basis=10.0,
            last_sale_price=10.0
        )
        router.context.portfolio.positions["000001.XSHE"] = position
        
        # 目标持仓1500股
        order_id = router.order_target("000001.XSHE", 1500, 10.0)
        assert order_id == "live_order_placeholder"

    def test_order_target_value(self, router):
        """测试目标市值下单"""
        order_id = router.order_target_value("000001.XSHE", 20000, 10.0)
        assert order_id == "live_order_placeholder"

    def test_order_market(self, router):
        """测试市价单"""
        order_id = router.order_market("000001.XSHE", 1000)
        assert order_id == "live_order_placeholder"

    def test_cancel_order(self, router, event_bus):
        """测试撤单功能"""
        # 监听事件
        events = []
        def event_handler(event):
            events.append(event)
        
        event_bus.subscribe("trading.cancel_order.request", event_handler)
        
        # 执行撤单
        success = router.cancel_order("order_123")
        
        # 验证返回值
        assert success is True
        
        # 验证事件发布
        assert len(events) == 1
        assert events[0].type == "trading.cancel_order.request"
        assert events[0].data["order_id"] == "order_123"

    def test_cancel_order_ex(self, router):
        """测试扩展撤单"""
        success = router.cancel_order_ex("order_123")
        assert success is True

    def test_ipo_stocks_order(self, router, event_bus):
        """测试新股申购"""
        # 监听事件
        events = []
        def event_handler(event):
            events.append(event)
        
        event_bus.subscribe("trading.ipo_order.request", event_handler)
        
        # 执行新股申购
        order_ids = router.ipo_stocks_order(50000)
        
        # 验证返回值
        assert order_ids == ["ipo_order_placeholder"]
        
        # 验证事件发布
        assert len(events) == 1
        assert events[0].type == "trading.ipo_order.request"
        assert events[0].data["amount_per_stock"] == 50000

    def test_after_trading_order(self, router, event_bus):
        """测试盘后交易"""
        # 监听事件
        events = []
        def event_handler(event):
            events.append(event)
        
        event_bus.subscribe("trading.after_trading_order.request", event_handler)
        
        # 执行盘后交易
        order_id = router.after_trading_order("000001.XSHE", 1000, 10.0)
        
        # 验证返回值
        assert order_id == "after_trading_order_placeholder"
        
        # 验证事件发布
        assert len(events) == 1
        assert events[0].type == "trading.after_trading_order.request"
        assert events[0].data["security"] == "000001.XSHE"
        assert events[0].data["amount"] == 1000
        assert events[0].data["limit_price"] == 10.0

    def test_after_trading_cancel_order(self, router, event_bus):
        """测试盘后撤单"""
        # 监听事件
        events = []
        def event_handler(event):
            events.append(event)
        
        event_bus.subscribe("trading.after_trading_cancel_order.request", event_handler)
        
        # 执行盘后撤单
        success = router.after_trading_cancel_order("order_123")
        
        # 验证返回值
        assert success is True
        
        # 验证事件发布
        assert len(events) == 1
        assert events[0].type == "trading.after_trading_cancel_order.request"
        assert events[0].data["order_id"] == "order_123"

    def test_get_position(self, router):
        """测试获取持仓"""
        # 模拟持仓
        position = Position(
            sid="000001.XSHE",
            amount=1000,
            enable_amount=1000,
            cost_basis=10.0,
            last_sale_price=12.0
        )
        router.context.portfolio.positions["000001.XSHE"] = position
        
        # 获取持仓
        result = router.get_position("000001.XSHE")
        assert result is position
        
        # 获取不存在的持仓
        result = router.get_position("000002.XSHE")
        assert result is None

    def test_get_positions(self, router):
        """测试获取多个持仓"""
        # 模拟持仓
        position1 = Position(
            sid="000001.XSHE",
            amount=1000,
            enable_amount=1000,
            cost_basis=10.0,
            last_sale_price=12.0
        )
        router.context.portfolio.positions["000001.XSHE"] = position1
        
        # 获取持仓
        positions = router.get_positions(["000001.XSHE", "000002.XSHE"])
        
        assert len(positions) == 2
        assert positions["000001.XSHE"]["amount"] == 1000
        assert positions["000002.XSHE"]["amount"] == 0  # 无持仓

    def test_get_orders(self, router):
        """测试获取订单"""
        # 模拟订单
        order_id1 = router.context.blotter.create_order("000001.XSHE", 1000, 10.0)
        order_id2 = router.context.blotter.create_order("000002.XSHE", 2000, 15.0)
        
        # 获取所有订单
        all_orders = router.get_orders()
        assert len(all_orders) == 2
        
        # 获取特定股票的订单
        orders_001 = router.get_orders("000001.XSHE")
        assert len(orders_001) == 1
        assert orders_001[0].symbol == "000001.XSHE"

    def test_get_open_orders(self, router):
        """测试获取未完成订单"""
        # 创建订单
        order_id = router.context.blotter.create_order("000001.XSHE", 1000, 10.0)
        
        # 获取未完成订单
        open_orders = router.get_open_orders()
        assert len(open_orders) == 1
        assert open_orders[0].id == order_id

    def test_get_trades(self, router):
        """测试获取成交记录"""
        # 创建已成交订单
        order_id = router.context.blotter.create_order("000001.XSHE", 1000, 10.0)
        order = router.context.blotter.get_order(order_id)
        order.status = "filled"
        order.filled = 1000
        
        # 获取成交记录
        trades = router.get_trades()
        assert len(trades) == 1
        
        trade = trades[0]
        assert trade["security"] == "000001.XSHE"
        assert trade["amount"] == 1000
        assert trade["side"] == "buy"

    def test_get_history(self, router):
        """测试获取历史数据"""
        # 实盘交易模式返回空数据（需要实时数据源）
        history = router.get_history(count=10, field=["close", "volume"])
        assert isinstance(history, pd.DataFrame)
        assert history.empty  # 当前实现返回空数据

    def test_get_price(self, router):
        """测试获取价格数据"""
        # 实盘交易模式返回空数据（需要实时数据源）
        price = router.get_price("000001.XSHE", count=5)
        assert isinstance(price, pd.DataFrame)
        assert price.empty  # 当前实现返回空数据

    def test_get_snapshot(self, router):
        """测试获取快照数据"""
        snapshot = router.get_snapshot(["000001.XSHE", "000002.XSHE"])
        
        assert isinstance(snapshot, pd.DataFrame)
        assert snapshot.shape[0] == 2
        assert "current_price" in snapshot.columns
        assert "volume" in snapshot.columns

    def test_get_fundamentals(self, router):
        """测试获取基本面数据"""
        fundamentals = router.get_fundamentals(
            stocks=["000001.XSHE", "000002.XSHE"],
            table="income",
            fields=["revenue", "net_profit"],
            date="2023-12-31"
        )
        
        assert isinstance(fundamentals, pd.DataFrame)
        assert fundamentals.shape[0] == 2
        assert "revenue" in fundamentals.columns
        assert "net_profit" in fundamentals.columns

    def test_set_universe(self, router):
        """测试设置股票池"""
        securities = ["000001.XSHE", "000002.XSHE", "600000.XSHG"]
        router.set_universe(securities)
        
        assert router.context.universe == securities

    def test_set_benchmark(self, router):
        """测试设置基准"""
        benchmark = "000300.SH"
        router.set_benchmark(benchmark)
        
        assert router.context.benchmark == benchmark

    def test_set_commission_not_supported(self, router):
        """测试设置佣金费率（实盘交易不支持）"""
        # 实盘交易模式不支持设置佣金费率
        router.set_commission(0.0005)
        # 应该只记录警告，不抛出异常

    def test_set_slippage_not_supported(self, router):
        """测试设置滑点（实盘交易不支持）"""
        # 实盘交易模式不支持设置滑点
        router.set_slippage(0.002)
        # 应该只记录警告，不抛出异常

    def test_set_volume_ratio_not_supported(self, router):
        """测试设置成交比例（实盘交易不支持）"""
        # 实盘交易模式不支持设置成交比例
        router.set_volume_ratio(0.8)
        # 应该只记录警告，不抛出异常

    def test_set_limit_mode_not_supported(self, router):
        """测试设置限制模式（实盘交易不支持）"""
        # 实盘交易模式不支持设置限制模式
        router.set_limit_mode("volume")
        # 应该只记录警告，不抛出异常

    def test_set_yesterday_position_not_supported(self, router):
        """测试设置底仓（实盘交易不支持）"""
        # 实盘交易模式不支持设置底仓
        positions = {"000001.XSHE": {"amount": 1000, "cost_basis": 10.0}}
        router.set_yesterday_position(positions)
        # 应该只记录警告，不抛出异常

    def test_set_parameters(self, router):
        """测试设置参数"""
        params = {"test_param": "test_value"}
        router.set_parameters(params)
        
        assert hasattr(router.context, '_parameters')
        assert router.context._parameters == params

    def test_technical_indicators(self, router):
        """测试技术指标"""
        close_data = np.array([10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0])
        
        # 测试MACD
        macd = router.get_MACD(close_data)
        assert isinstance(macd, pd.DataFrame)
        assert list(macd.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        
        # 测试RSI
        rsi = router.get_RSI(close_data)
        assert isinstance(rsi, pd.DataFrame)
        assert list(rsi.columns) == ["RSI"]
        
        # 测试KDJ
        high_data = np.array([10.2, 10.3, 10.4, 10.1, 10.5, 10.6, 10.3, 10.7, 10.8, 10.2])
        low_data = np.array([9.8, 9.9, 10.0, 9.7, 10.1, 10.2, 9.9, 10.3, 10.4, 9.8])
        
        kdj = router.get_KDJ(high_data, low_data, close_data)
        assert isinstance(kdj, pd.DataFrame)
        assert list(kdj.columns) == ["K", "D", "J"]
        
        # 测试CCI
        cci = router.get_CCI(high_data, low_data, close_data)
        assert isinstance(cci, pd.DataFrame)
        assert list(cci.columns) == ["CCI"]

    def test_trading_day_functions(self, router):
        """测试交易日相关功能"""
        # 测试get_trading_day
        trading_day = router.get_trading_day("2023-12-29", 1)  # 周五+1天
        assert trading_day == "2024-01-01"  # 应该是下周一
        
        # 测试get_trade_days
        trade_days = router.get_trade_days("2023-12-25", "2023-12-29")
        assert len(trade_days) == 5  # 周一到周五
        
        # 测试get_all_trades_days
        all_days = router.get_all_trades_days()
        assert len(all_days) > 200  # 过去一年应该有200+个交易日

    def test_stock_info(self, router):
        """测试股票信息"""
        info = router.get_stock_info(["000001.XSHE", "600000.XSHG"])
        
        assert len(info) == 2
        assert "000001.XSHE" in info
        assert "600000.XSHG" in info
        
        stock_info = info["000001.XSHE"]
        assert stock_info["market"] == "SZSE"
        assert stock_info["type"] == "stock"

    def test_check_limit(self, router):
        """测试涨跌停检查"""
        limit_info = router.check_limit("000001.XSHE")
        
        assert "000001.XSHE" in limit_info
        assert "limit_up" in limit_info["000001.XSHE"]
        assert "limit_down" in limit_info["000001.XSHE"]
        assert "current_price" in limit_info["000001.XSHE"]

    def test_handle_data(self, router):
        """测试数据处理"""
        # 先模拟持仓
        position = Position(
            sid="000001.XSHE",
            amount=1000,
            enable_amount=1000,
            cost_basis=10.0,
            last_sale_price=10.0
        )
        router.context.portfolio.positions["000001.XSHE"] = position
        
        # 处理价格数据
        data = {
            "000001.XSHE": {"price": 12.0}
        }
        
        router.handle_data(data)
        
        # 检查持仓价格是否更新
        assert position.last_sale_price == 12.0

    def test_log_function(self, router):
        """测试日志功能"""
        # 测试不同级别的日志
        router.log("Test info message", "info")
        router.log("Test warning message", "warning")
        router.log("Test error message", "error")
        
        # 测试无效级别
        router.log("Test invalid level", "invalid")

    def test_get_all_orders(self, router):
        """测试获取所有订单"""
        # 创建订单
        router.context.blotter.create_order("000001.XSHE", 1000, 10.0)
        router.context.blotter.create_order("000002.XSHE", 2000, 15.0)
        
        # 获取所有订单
        all_orders = router.get_all_orders()
        assert len(all_orders) == 2

    def test_get_order(self, router):
        """测试获取指定订单"""
        # 创建订单
        order_id = router.context.blotter.create_order("000001.XSHE", 1000, 10.0)
        
        # 获取订单
        order = router.get_order(order_id)
        assert order is not None
        assert order.id == order_id
        
        # 获取不存在的订单
        order = router.get_order("nonexistent")
        assert order is None