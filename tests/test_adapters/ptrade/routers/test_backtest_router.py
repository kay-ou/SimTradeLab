# -*- coding: utf-8 -*-
"""
PTrade回测路由器测试
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock

from simtradelab.adapters.ptrade.routers.backtest import BacktestAPIRouter
from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Portfolio, Position, Blotter
from simtradelab.core.event_bus import EventBus


class TestBacktestAPIRouter:
    """测试回测API路由器"""

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
    def router(self, context):
        """创建回测路由器实例"""
        event_bus = EventBus()
        router = BacktestAPIRouter(
            context=context,
            event_bus=event_bus,
            slippage_rate=0.001,
            commission_rate=0.0003
        )
        return router

    def test_router_initialization(self, router, context):
        """测试路由器初始化"""
        assert router.context is context
        assert router._slippage_rate == 0.001
        assert router._commission_rate == 0.0003
        assert len(router._supported_apis) > 0

    def test_mode_support_check(self, router):
        """测试模式支持检查"""
        # 支持的API
        assert router.is_mode_supported("order") is True
        assert router.is_mode_supported("get_history") is True
        assert router.is_mode_supported("get_fundamentals") is True
        
        # 不支持的API（如果存在）
        assert router.is_mode_supported("nonexistent_api") is False

    def test_order_execution(self, router):
        """测试订单执行"""
        # 测试正常下单
        order_id = router.order("000001.XSHE", 1000, 10.0)
        assert order_id is not None
        assert order_id.startswith("order_")
        
        # 检查订单状态
        order = router.context.blotter.get_order(order_id)
        assert order.status == "filled"
        
        # 检查持仓
        assert "000001.XSHE" in router.context.portfolio.positions
        position = router.context.portfolio.positions["000001.XSHE"]
        assert position.amount == 1000

    def test_order_insufficient_funds(self, router):
        """测试资金不足时的订单处理"""
        # 尝试下超出资金的大单
        order_id = router.order("000001.XSHE", 200000, 10.0)
        assert order_id is None  # 应该被拒绝

    def test_order_value(self, router):
        """测试按价值下单"""
        order_id = router.order_value("000001.XSHE", 50000, 10.0)
        assert order_id is not None
        
        # 检查下单数量
        order = router.context.blotter.get_order(order_id)
        assert order.amount == 5000  # 50000 / 10.0

    def test_order_target(self, router):
        """测试目标持仓下单"""
        # 先买入1000股
        router.order("000001.XSHE", 1000, 10.0)
        
        # 目标持仓1500股
        order_id = router.order_target("000001.XSHE", 1500, 10.0)
        assert order_id is not None
        
        order = router.context.blotter.get_order(order_id)
        assert order.amount == 500  # 1500 - 1000

    def test_order_target_value(self, router):
        """测试目标市值下单"""
        # 先买入1000股
        router.order("000001.XSHE", 1000, 10.0)
        
        # 目标市值20000
        order_id = router.order_target_value("000001.XSHE", 20000, 10.0)
        assert order_id is not None
        
        order = router.context.blotter.get_order(order_id)
        assert order.amount == 1000  # 2000 - 1000

    def test_order_market(self, router):
        """测试市价单"""
        order_id = router.order_market("000001.XSHE", 1000)
        assert order_id is not None
        
        order = router.context.blotter.get_order(order_id)
        assert order.amount == 1000

    def test_cancel_order(self, router):
        """测试撤单"""
        # 创建订单但不自动执行
        order_id = router.context.blotter.create_order("000001.XSHE", 1000, 10.0)
        
        # 撤销订单
        success = router.cancel_order(order_id)
        assert success is True
        
        order = router.context.blotter.get_order(order_id)
        assert order.status == "cancelled"

    def test_get_positions(self, router):
        """测试获取持仓"""
        # 建立持仓
        router.order("000001.XSHE", 1000, 10.0)
        router.order("000002.XSHE", 2000, 15.0)
        
        positions = router.get_positions(["000001.XSHE", "000002.XSHE", "000003.XSHE"])
        
        assert len(positions) == 3
        assert positions["000001.XSHE"]["amount"] == 1000
        assert positions["000002.XSHE"]["amount"] == 2000
        assert positions["000003.XSHE"]["amount"] == 0  # 无持仓

    def test_get_orders(self, router):
        """测试获取订单"""
        # 创建多个订单
        router.order("000001.XSHE", 1000, 10.0)
        router.order("000002.XSHE", 2000, 15.0)
        router.order("000001.XSHE", -500, 12.0)
        
        # 获取所有订单
        all_orders = router.get_orders()
        assert len(all_orders) == 3
        
        # 获取特定股票的订单
        orders_001 = router.get_orders("000001.XSHE")
        assert len(orders_001) == 2
        assert all(order.symbol == "000001.XSHE" for order in orders_001)

    def test_get_trades(self, router):
        """测试获取成交记录"""
        # 创建订单
        router.order("000001.XSHE", 1000, 10.0)
        router.order("000002.XSHE", 2000, 15.0)
        
        # 获取成交记录
        trades = router.get_trades()
        assert len(trades) == 2
        
        # 检查成交记录内容
        trade = trades[0]
        assert "order_id" in trade
        assert "security" in trade
        assert "amount" in trade
        assert "side" in trade

    def test_get_history(self, router):
        """测试获取历史数据"""
        # 测试DataFrame格式
        history = router.get_history(count=10, field=["open", "high", "low", "close", "volume"])
        
        assert isinstance(history, pd.DataFrame)
        assert history.shape[0] == 20  # 2个股票 x 10天
        assert list(history.columns) == ["open", "high", "low", "close", "volume"]
        
        # 测试字典格式
        history_dict = router.get_history(count=5, field=["close", "volume"], is_dict=True)
        
        assert isinstance(history_dict, dict)
        assert "000001.XSHE" in history_dict
        assert "000002.XSHE" in history_dict

    def test_get_price(self, router):
        """测试获取价格数据"""
        # 测试单个股票
        price = router.get_price("000001.XSHE", count=5)
        assert isinstance(price, pd.DataFrame)
        assert price.shape[0] == 5
        
        # 测试多个股票
        price_multi = router.get_price(["000001.XSHE", "000002.XSHE"], count=3)
        assert isinstance(price_multi, pd.DataFrame)
        assert price_multi.shape[0] == 6  # 2个股票 x 3天

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

    def test_set_parameters(self, router):
        """测试设置参数"""
        params = {
            "commission": 0.0005,
            "slippage": 0.002,
            "universe": ["000001.XSHE", "000002.XSHE"],
            "benchmark": "000300.SH"
        }
        
        router.set_parameters(params)
        
        assert router._commission_rate == 0.0005
        assert router._slippage_rate == 0.002
        assert router.context.universe == ["000001.XSHE", "000002.XSHE"]
        assert router.context.benchmark == "000300.SH"

    def test_set_volume_ratio(self, router):
        """测试设置成交比例"""
        router.set_volume_ratio(0.8)
        assert router.context._volume_ratio == 0.8
        
        # 测试无效值
        with pytest.raises(ValueError):
            router.set_volume_ratio(1.5)

    def test_set_limit_mode(self, router):
        """测试设置限制模式"""
        router.set_limit_mode("volume")
        assert router.context._limit_mode == "volume"
        
        # 测试无效模式
        with pytest.raises(ValueError):
            router.set_limit_mode("invalid")

    def test_set_yesterday_position(self, router):
        """测试设置底仓"""
        positions = {
            "000001.XSHE": {
                "amount": 1000,
                "cost_basis": 10.0,
                "last_price": 10.0
            }
        }
        
        router.set_yesterday_position(positions)
        
        assert router.context._yesterday_position == positions
        assert "000001.XSHE" in router.context.portfolio.positions

    def test_slippage_and_commission(self, router):
        """测试滑点和手续费计算"""
        # 买入订单
        order_id = router.order("000001.XSHE", 1000, 10.0)
        
        # 验证实际执行价格包含滑点
        order = router.context.blotter.get_order(order_id)
        assert order.status == "filled"
        
        # 验证现金减少包含手续费
        portfolio = router.context.portfolio
        assert portfolio.cash < 1000000 - 10000  # 应该少于原始订单金额

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
        # 先建立持仓
        router.order("000001.XSHE", 1000, 10.0)
        
        # 处理价格数据
        data = {
            "000001.XSHE": {"price": 12.0}
        }
        
        router.handle_data(data)
        
        # 检查持仓价格是否更新
        position = router.context.portfolio.positions["000001.XSHE"]
        assert position.last_sale_price == 12.0

    def test_log_function(self, router):
        """测试日志功能"""
        # 测试不同级别的日志
        router.log("Test info message", "info")
        router.log("Test warning message", "warning")
        router.log("Test error message", "error")
        
        # 测试无效级别
        router.log("Test invalid level", "invalid")