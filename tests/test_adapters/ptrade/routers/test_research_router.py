# -*- coding: utf-8 -*-
"""
PTrade研究模式路由器测试
"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Blotter, Portfolio, Position
from simtradelab.adapters.ptrade.routers.research import ResearchAPIRouter
from simtradelab.core.event_bus import EventBus


class TestResearchAPIRouter:
    """测试研究模式API路由器"""

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
        """创建研究模式路由器实例"""
        router = ResearchAPIRouter(context=context, event_bus=event_bus)
        return router

    def test_router_initialization(self, router, context):
        """测试路由器初始化"""
        assert router.context is context
        assert router.event_bus is not None
        assert len(router._supported_apis) > 0

    def test_mode_support_check(self, router):
        """测试模式支持检查"""
        # 研究模式支持的API（只读操作）
        assert router.is_mode_supported("get_history") is True
        assert router.is_mode_supported("get_price") is True
        assert router.is_mode_supported("get_fundamentals") is True
        assert router.is_mode_supported("get_MACD") is True
        assert router.is_mode_supported("set_universe") is True
        assert router.is_mode_supported("set_benchmark") is True

        # 研究模式不支持的API（交易操作）
        assert router.is_mode_supported("order") is False
        assert router.is_mode_supported("cancel_order") is False
        assert router.is_mode_supported("nonexistent_api") is False

    def test_trading_operations_not_supported(self, router):
        """测试交易操作不被支持"""
        # 测试所有交易相关的API都会抛出NotImplementedError

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.order("000001.XSHE", 1000, 10.0)

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.order_value("000001.XSHE", 50000, 10.0)

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.order_target("000001.XSHE", 1500, 10.0)

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.order_target_value("000001.XSHE", 20000, 10.0)

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.order_market("000001.XSHE", 1000)

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.cancel_order("order_123")

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.cancel_order_ex("order_123")

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.ipo_stocks_order(50000)

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.after_trading_order("000001.XSHE", 1000, 10.0)

        with pytest.raises(
            NotImplementedError, match="Trading operations are not supported"
        ):
            router.after_trading_cancel_order("order_123")

    def test_order_queries_not_supported(self, router):
        """测试订单查询不被支持"""
        # 测试所有订单查询相关的API都会抛出NotImplementedError

        with pytest.raises(
            NotImplementedError, match="Order queries are not supported"
        ):
            router.get_all_orders()

        with pytest.raises(
            NotImplementedError, match="Order queries are not supported"
        ):
            router.get_open_orders()

        with pytest.raises(
            NotImplementedError, match="Order queries are not supported"
        ):
            router.get_order("order_123")

        with pytest.raises(
            NotImplementedError, match="Order queries are not supported"
        ):
            router.get_orders()

    def test_position_queries_not_supported(self, router):
        """测试持仓查询不被支持"""
        # 测试所有持仓查询相关的API都会抛出NotImplementedError

        with pytest.raises(
            NotImplementedError, match="Position queries are not supported"
        ):
            router.get_position("000001.XSHE")

        with pytest.raises(
            NotImplementedError, match="Position queries are not supported"
        ):
            router.get_positions(["000001.XSHE", "000002.XSHE"])

    def test_trade_queries_not_supported(self, router):
        """测试交易查询不被支持"""
        # 测试交易查询相关的API都会抛出NotImplementedError

        with pytest.raises(
            NotImplementedError, match="Trade queries are not supported"
        ):
            router.get_trades()

    def test_get_history(self, router):
        """测试获取历史数据"""
        # 测试DataFrame格式 - 研究模式现在返回实际数据
        history = router.get_history(
            count=10, field=["open", "high", "low", "close", "volume"]
        )

        assert isinstance(history, pd.DataFrame)
        assert not history.empty  # 研究模式现在返回实际数据
        assert len(history) > 0  # 应该有数据

        # 检查数据结构
        expected_columns = ["open", "high", "low", "close", "volume"]
        for col in expected_columns:
            assert col in history.columns

        # 测试字典格式
        history_dict = router.get_history(
            count=5, field=["close", "volume"], is_dict=True
        )

        assert isinstance(history_dict, dict)
        assert "000001.XSHE" in history_dict
        assert "000002.XSHE" in history_dict
        assert "close" in history_dict["000001.XSHE"]
        assert "volume" in history_dict["000001.XSHE"]

    def test_get_price(self, router):
        """测试获取价格数据"""
        # 研究模式现在返回实际数据
        price = router.get_price("000001.XSHE", count=5)
        assert isinstance(price, pd.DataFrame)
        assert not price.empty  # 研究模式现在返回实际数据
        assert len(price) > 0  # 应该有数据

        # 检查默认字段
        expected_columns = ["open", "high", "low", "close", "volume"]
        for col in expected_columns:
            assert col in price.columns

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
            date="2023-12-31",
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
        """测试设置佣金费率（研究模式现在支持）"""
        # 研究模式现在支持设置佣金费率用于分析
        router.set_commission(0.0005)
        # 应该设置成功，存储在上下文中
        assert hasattr(router.context, "_commission_rate")
        assert router.context._commission_rate == 0.0005

    def test_set_slippage_not_supported(self, router):
        """测试设置滑点（研究模式现在支持）"""
        # 研究模式现在支持设置滑点用于分析
        router.set_slippage(0.002)
        # 应该设置成功，存储在上下文中
        assert hasattr(router.context, "_slippage_rate")
        assert router.context._slippage_rate == 0.002

    def test_set_fixed_slippage_not_supported(self, router):
        """测试设置固定滑点（研究模式现在支持）"""
        # 研究模式现在支持设置固定滑点用于分析
        router.set_fixed_slippage(0.001)
        # 应该设置成功，存储在上下文中
        assert hasattr(router.context, "_fixed_slippage_rate")
        assert router.context._fixed_slippage_rate == 0.001

    def test_set_volume_ratio_not_supported(self, router):
        """测试设置成交比例（研究模式现在支持）"""
        # 研究模式现在支持设置成交比例用于分析
        router.set_volume_ratio(0.8)
        # 应该设置成功，存储在上下文中
        assert hasattr(router.context, "_volume_ratio")
        assert router.context._volume_ratio == 0.8

    def test_set_limit_mode_not_supported(self, router):
        """测试设置限制模式（研究模式现在支持）"""
        # 研究模式现在支持设置限制模式用于分析
        router.set_limit_mode("volume")
        # 应该设置成功，存储在上下文中
        assert hasattr(router.context, "_limit_mode")
        assert router.context._limit_mode == "volume"

    def test_set_yesterday_position_not_supported(self, router):
        """测试设置底仓（研究模式现在支持）"""
        # 研究模式现在支持设置底仓用于分析
        positions = {"000001.XSHE": {"amount": 1000, "cost_basis": 10.0}}
        router.set_yesterday_position(positions)
        # 应该设置成功，存储在上下文中
        assert hasattr(router.context, "_yesterday_position")
        assert router.context._yesterday_position == positions

    def test_set_parameters(self, router):
        """测试设置参数"""
        params = {"research_param": "research_value"}
        router.set_parameters(params)

        assert router.context._parameters == params

    def test_technical_indicators(self, router):
        """测试技术指标"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 测试MACD
        macd = router.get_MACD(close_data)
        assert isinstance(macd, pd.DataFrame)
        assert list(macd.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(macd) == len(close_data)

        # 测试RSI
        rsi = router.get_RSI(close_data)
        assert isinstance(rsi, pd.DataFrame)
        assert list(rsi.columns) == ["RSI"]
        assert len(rsi) == len(close_data)

        # 测试KDJ
        high_data = np.array(
            [10.2, 10.3, 10.4, 10.1, 10.5, 10.6, 10.3, 10.7, 10.8, 10.2]
        )
        low_data = np.array([9.8, 9.9, 10.0, 9.7, 10.1, 10.2, 9.9, 10.3, 10.4, 9.8])

        kdj = router.get_KDJ(high_data, low_data, close_data)
        assert isinstance(kdj, pd.DataFrame)
        assert list(kdj.columns) == ["K", "D", "J"]
        assert len(kdj) == len(close_data)

        # 测试CCI
        cci = router.get_CCI(high_data, low_data, close_data)
        assert isinstance(cci, pd.DataFrame)
        assert list(cci.columns) == ["CCI"]
        assert len(cci) == len(close_data)

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

        stock_info = info["600000.XSHG"]
        assert stock_info["market"] == "SSE"
        assert stock_info["type"] == "stock"

    def test_check_limit(self, router):
        """测试涨跌停检查"""
        limit_info = router.check_limit("000001.XSHE")

        assert "000001.XSHE" in limit_info
        assert "limit_up" in limit_info["000001.XSHE"]
        assert "limit_down" in limit_info["000001.XSHE"]
        assert "current_price" in limit_info["000001.XSHE"]

        # 研究模式下应该返回False（模拟数据）
        assert limit_info["000001.XSHE"]["limit_up"] is False
        assert limit_info["000001.XSHE"]["limit_down"] is False

    def test_handle_data(self, router):
        """测试数据处理"""
        # 研究模式的数据处理应该是空操作
        data = {"000001.XSHE": {"price": 12.0}}

        # 不应该抛出异常
        router.handle_data(data)

    def test_log_function(self, router):
        """测试日志功能"""
        # 测试不同级别的日志
        router.log("Research mode test info message", "info")
        router.log("Research mode test warning message", "warning")
        router.log("Research mode test error message", "error")

        # 测试无效级别
        router.log("Research mode test invalid level", "invalid")

    def test_research_mode_characteristics(self, router):
        """测试研究模式的特征"""
        # 研究模式应该：
        # 1. 支持数据查询
        # 2. 支持技术指标计算
        # 3. 支持基本设置（股票池、基准）
        # 4. 不支持交易操作
        # 5. 不支持持仓查询
        # 6. 不支持订单查询

        # 支持的功能
        assert router.is_mode_supported("get_history")
        assert router.is_mode_supported("get_price")
        assert router.is_mode_supported("get_fundamentals")
        assert router.is_mode_supported("get_MACD")
        assert router.is_mode_supported("set_universe")
        assert router.is_mode_supported("set_benchmark")
        assert router.is_mode_supported("log")
        assert router.is_mode_supported("check_limit")
        assert router.is_mode_supported("handle_data")

        # 不支持的功能
        trading_apis = [
            "order",
            "order_value",
            "order_target",
            "order_target_value",
            "order_market",
            "cancel_order",
            "cancel_order_ex",
            "ipo_stocks_order",
            "after_trading_order",
            "after_trading_cancel_order",
        ]

        for api in trading_apis:
            assert not router.is_mode_supported(api)

    def test_fundamentals_data_generation(self, router):
        """测试基本面数据生成"""
        # 测试不同的表格和字段
        fundamentals = router.get_fundamentals(
            stocks=["000001.XSHE", "000002.XSHE"],
            table="balance_sheet",
            fields=["total_assets", "total_liab", "pe_ratio", "pb_ratio", "roe", "eps"],
            date="2023-12-31",
        )

        assert isinstance(fundamentals, pd.DataFrame)
        assert fundamentals.shape[0] == 2
        assert "total_assets" in fundamentals.columns
        assert "total_liab" in fundamentals.columns
        assert "pe_ratio" in fundamentals.columns
        assert "pb_ratio" in fundamentals.columns
        assert "roe" in fundamentals.columns
        assert "eps" in fundamentals.columns

        # 验证数据范围合理性
        for _, row in fundamentals.iterrows():
            assert row["total_assets"] > 0
            assert row["total_liab"] > 0
            assert 0 < row["pe_ratio"] < 100
            assert 0 < row["pb_ratio"] < 20
            assert 0 < row["roe"] < 1
            assert row["eps"] > 0

    def test_error_handling(self, router):
        """测试错误处理"""
        # 测试空股票列表
        fundamentals = router.get_fundamentals(
            stocks=[], table="income", fields=["revenue"], date="2023-12-31"
        )
        assert isinstance(fundamentals, pd.DataFrame)
        assert fundamentals.empty

        # 测试空字段列表
        fundamentals = router.get_fundamentals(
            stocks=["000001.XSHE"], table="income", fields=[], date="2023-12-31"
        )
        assert isinstance(fundamentals, pd.DataFrame)
        assert fundamentals.shape[0] == 1
        assert fundamentals.shape[1] == 2  # code + date

    def test_universe_and_benchmark_settings(self, router):
        """测试股票池和基准设置"""
        # 测试设置股票池
        original_universe = router.context.universe.copy()
        new_universe = ["000001.XSHE", "000002.XSHE", "600000.XSHG", "600036.XSHG"]

        router.set_universe(new_universe)
        assert router.context.universe == new_universe

        # 测试设置基准
        original_benchmark = router.context.benchmark
        new_benchmark = "000905.SH"

        router.set_benchmark(new_benchmark)
        assert router.context.benchmark == new_benchmark

        # 验证历史数据查询使用新的股票池
        history_dict = router.get_history(count=5, field=["close"], is_dict=True)
        for security in new_universe:
            assert security in history_dict
