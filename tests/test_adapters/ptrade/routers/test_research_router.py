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
        # 明确设置为研究模式
        context.mode = "research"
        return context

    @pytest.fixture
    def event_bus(self):
        """创建事件总线"""
        return EventBus()

    @pytest.fixture
    def router(self, context, event_bus):
        """创建研究模式路由器实例"""
        # 创建模拟插件管理器
        mock_plugin_manager = MagicMock()

        # 创建模拟数据插件
        mock_data_plugin = MagicMock()

        # 设置数据插件的方法识别
        mock_data_plugin.get_history_data = MagicMock()
        mock_data_plugin.get_current_price = MagicMock()
        mock_data_plugin.get_snapshot = MagicMock()
        mock_data_plugin.get_multiple_history_data = MagicMock()

        # 设置数据插件方法的返回值
        mock_data_plugin.get_history_data.side_effect = self._mock_get_history_data
        mock_data_plugin.get_multiple_history_data.side_effect = (
            self._mock_get_multiple_history_data
        )
        mock_data_plugin.get_snapshot.side_effect = self._mock_get_snapshot
        mock_data_plugin.get_stock_basic_info.side_effect = Exception(
            "Plugin method not available"
        )
        mock_data_plugin.get_fundamentals.side_effect = Exception(
            "Plugin method not available"
        )
        mock_data_plugin.get_trading_day.return_value = "2024-01-01"
        mock_data_plugin.get_trading_days_range.return_value = [
            "2023-12-25",
            "2023-12-26",
            "2023-12-27",
            "2023-12-28",
            "2023-12-29",
        ]
        mock_data_plugin.get_all_trading_days.return_value = ["2023-01-03"] + [
            f"2023-{i:02d}-{j:02d}"
            for i in range(1, 13)
            for j in range(1, 29)
            if j % 7 not in [0, 6]
        ]
        mock_data_plugin.check_limit_status.return_value = {
            "000001.XSHE": {
                "limit_up": False,
                "limit_down": False,
                "limit_up_price": 16.5,
                "limit_down_price": 13.5,
                "current_price": 15.0,
            }
        }

        # 创建模拟技术指标插件
        mock_indicators_plugin = MagicMock()
        mock_indicators_plugin.metadata.name = "technical_indicators_plugin"
        mock_indicators_plugin.metadata.category = "analysis"
        mock_indicators_plugin.metadata.tags = ["indicators", "technical"]

        # 正确设置计算方法 - 使用side_effect来确保返回DataFrame
        def mock_calculate_macd(close):
            periods = len(close)
            return pd.DataFrame(
                {
                    "MACD": np.random.randn(periods) * 0.1,
                    "MACD_signal": np.random.randn(periods) * 0.1,
                    "MACD_hist": np.random.randn(periods) * 0.05,
                }
            )

        def mock_calculate_kdj(high, low, close):
            periods = len(close)
            return pd.DataFrame(
                {
                    "K": np.random.uniform(0, 100, periods),
                    "D": np.random.uniform(0, 100, periods),
                    "J": np.random.uniform(0, 100, periods),
                }
            )

        def mock_calculate_rsi(close):
            periods = len(close)
            return pd.DataFrame({"RSI": np.random.uniform(0, 100, periods)})

        def mock_calculate_cci(high, low, close):
            periods = len(close)
            return pd.DataFrame({"CCI": np.random.randn(periods) * 50})

        # 设置插件管理器返回的插件
        mock_plugin_manager.get_all_plugins.return_value = {
            "mock_data_plugin": mock_data_plugin,
            "technical_indicators_plugin": mock_indicators_plugin,
        }

        # 创建路由器
        router = ResearchAPIRouter(
            context=context, event_bus=event_bus, plugin_manager=mock_plugin_manager
        )

        # 设置技术指标插件的side_effect（必须在路由器创建后）
        indicators_plugin = router._get_indicators_plugin()
        if indicators_plugin:
            indicators_plugin.calculate_macd.side_effect = mock_calculate_macd
            indicators_plugin.calculate_kdj.side_effect = mock_calculate_kdj
            indicators_plugin.calculate_rsi.side_effect = mock_calculate_rsi
            indicators_plugin.calculate_cci.side_effect = mock_calculate_cci

        return router

    def _mock_get_history_data(self, security, count):
        """模拟单个股票历史数据获取"""
        dates = pd.date_range("2023-01-01", periods=count, freq="D")
        return pd.DataFrame({
            "security": [security] * count,
            "date": dates,
            "open": np.random.uniform(10, 20, count),
            "high": np.random.uniform(15, 25, count),
            "low": np.random.uniform(5, 15, count),
            "close": np.random.uniform(10, 20, count),
            "volume": np.random.randint(1000, 10000, count),
        })

    def _mock_get_multiple_history_data(
        self, securities, count, start_date=None, end_date=None
    ):
        """模拟历史数据获取"""
        dates = pd.date_range("2023-01-01", periods=count, freq="D")
        all_data = []
        for security in securities:
            security_data = pd.DataFrame(
                {
                    "security": [security] * count,
                    "date": dates,
                    "open": np.random.rand(count),
                    "high": np.random.rand(count),
                    "low": np.random.rand(count),
                    "close": np.random.rand(count),
                    "volume": np.random.randint(1000, 10000, count),
                }
            )
            all_data.append(security_data)
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            return result.sort_values(["security", "date"])
        return pd.DataFrame()

    def _mock_get_snapshot(self, securities):
        """模拟市场快照获取"""
        snapshot = {}
        for security in securities:
            snapshot[security] = {
                "last_price": 15.0 if security.startswith("000001") else 20.0,
                "volume": 1000 if security.startswith("000001") else 2000,
                "datetime": pd.Timestamp.now(),
            }
        return snapshot

    def _mock_calculate_macd(self, close):
        """模拟MACD计算"""
        periods = len(close)
        return pd.DataFrame(
            {
                "MACD": np.random.randn(periods) * 0.1,
                "MACD_signal": np.random.randn(periods) * 0.1,
                "MACD_hist": np.random.randn(periods) * 0.05,
            }
        )

    def _mock_calculate_kdj(self, high, low, close):
        """模拟KDJ计算"""
        periods = len(close)
        return pd.DataFrame(
            {
                "K": np.random.uniform(0, 100, periods),
                "D": np.random.uniform(0, 100, periods),
                "J": np.random.uniform(0, 100, periods),
            }
        )

    def _mock_calculate_rsi(self, close):
        """模拟RSI计算"""
        periods = len(close)
        return pd.DataFrame({"RSI": np.random.uniform(0, 100, periods)})

    def _mock_calculate_cci(self, high, low, close):
        """模拟CCI计算"""
        periods = len(close)
        return pd.DataFrame({"CCI": np.random.randn(periods) * 50})

    def test_router_initialization(self, router, context):
        """测试路由器初始化"""
        assert router.context is context
        assert router.event_bus is not None
        # 测试路由器具有基本功能而不是具体属性
        assert hasattr(router, 'get_history')
        assert hasattr(router, 'get_price')
        assert hasattr(router, 'is_mode_supported')

    def test_mode_support_check(self, router):
        """测试模式支持检查"""
        # 研究模式支持的API（根据PTrade官方文档）
        assert router.is_mode_supported("get_price") is True  # 支持研究模式
        assert router.is_mode_supported("get_fundamentals") is True  # 支持研究模式
        assert router.is_mode_supported("get_MACD") is True  # 技术指标支持所有模式
        assert router.is_mode_supported("get_stock_info") is True  # 股票信息支持所有模式
        assert router.is_mode_supported("check_limit") is True  # 工具函数支持所有模式

        # 研究模式不支持的API（根据PTrade官方文档）
        assert router.is_mode_supported("get_history") is False  # 仅支持回测/交易
        assert router.is_mode_supported("set_universe") is False  # 仅支持回测/交易
        assert router.is_mode_supported("set_benchmark") is False  # 仅支持回测/交易
        assert router.is_mode_supported("order") is False  # 交易操作
        assert router.is_mode_supported("cancel_order") is False  # 交易操作
        assert router.is_mode_supported("nonexistent_api") is False  # 不存在的API

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

    def test_get_current_data(self, router):
        """测试获取当前数据 - 策略data参数的数据源"""
        # 临时替换mock方法，避免side_effect的干扰
        mock_snapshot = {
            "STOCK_A": {
                "last_price": 10.5,
                "open": 10.0,
                "high": 10.8,
                "low": 9.8,
                "volume": 50000,
                "money": 525000.0,
                "price": 10.5,
            }
        }

        # 直接设置mock返回值，绕过side_effect
        data_plugin = router._get_data_plugin()
        data_plugin.get_snapshot = MagicMock(return_value=mock_snapshot)

        # 测试获取当前数据
        result = router.get_current_data(["STOCK_A"])
        assert isinstance(result, dict)
        assert "STOCK_A" in result
        assert "price" in result["STOCK_A"]
        assert "close" in result["STOCK_A"]
        assert "open" in result["STOCK_A"]
        assert "high" in result["STOCK_A"]
        assert "low" in result["STOCK_A"]
        assert "volume" in result["STOCK_A"]
        assert "money" in result["STOCK_A"]

        # 验证数据格式
        assert result["STOCK_A"]["price"] == 10.5
        assert result["STOCK_A"]["close"] == 10.5
        assert result["STOCK_A"]["volume"] == 50000

    def test_data_plugin_integration(self, router):
        """测试数据插件集成"""
        # 验证数据插件能够被正确发现
        data_plugin = router._get_data_plugin()
        assert data_plugin is not None

        # 验证数据插件具有必要的方法
        assert hasattr(data_plugin, "get_history_data")
        assert hasattr(data_plugin, "get_snapshot")
        assert hasattr(data_plugin, "get_current_price")
        assert hasattr(data_plugin, "get_multiple_history_data")

    def test_data_plugin_fallback(self, router):
        """测试数据插件不可用时的回退机制"""
        # 设置插件管理器返回None（模拟无数据插件）
        router._plugin_manager = None

        # 测试各种数据获取方法的回退
        result = router.get_current_data(["STOCK_A"])
        assert result == {}

    def test_get_history_not_supported_in_research(self, router):
        """测试get_history在研究模式下不被支持"""
        # 根据PTrade官方文档，get_history仅支持[回测/交易]，不支持研究模式
        # 应该通过API验证器被阻止
        with pytest.raises(ValueError, match="API 'get_history' is not supported"):
            router.get_history(count=10, field=["close"])

    def test_set_universe_not_supported_in_research(self, router):
        """测试set_universe在研究模式下不被支持"""
        # 根据PTrade官方文档，set_universe仅支持[回测/交易]，不支持研究模式
        with pytest.raises(ValueError, match="API 'set_universe' is not supported"):
            router.set_universe(["000001.XSHE", "000002.XSHE"])

    def test_set_benchmark_not_supported_in_research(self, router):
        """测试set_benchmark在研究模式下不被支持"""
        # 根据PTrade官方文档，set_benchmark仅支持[回测/交易]，不支持研究模式
        with pytest.raises(ValueError, match="API 'set_benchmark' is not supported"):
            router.set_benchmark("000300.SH")

    def test_get_price(self, router):
        """测试获取价格数据"""
        # 研究模式现在返回实际数据
        # 单个股票返回float价格
        price = router.get_price("000001.XSHE", count=1)
        assert isinstance(price, float)
        assert price > 0
        
        # 多个股票返回字典
        prices = router.get_price(["000001.XSHE", "000002.XSHE"], count=1)
        assert isinstance(prices, dict)
        assert "000001.XSHE" in prices
        assert "000002.XSHE" in prices
        assert isinstance(prices["000001.XSHE"], float)
        assert isinstance(prices["000002.XSHE"], float)

    def test_get_snapshot(self, router):
        """测试获取快照数据"""
        snapshot = router.get_snapshot(["000001.XSHE", "000002.XSHE"])

        assert isinstance(snapshot, pd.DataFrame)
        assert snapshot.shape[0] == 2
        # 检查基本的快照数据结构
        assert "security" in snapshot.columns
        # last_price是mock数据插件提供的字段
        assert "last_price" in snapshot.columns

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

    def test_configuration_apis_not_supported_in_research(self, router):
        """测试配置API在研究模式下不被支持"""
        # 根据PTrade官方文档，这些配置API仅支持[回测/交易]，不支持研究模式
        
        # 这些配置API在研究模式下应该被阻止
        config_apis = [
            ("set_commission", [0.0005]),
            ("set_slippage", [0.002]),
            ("set_fixed_slippage", [0.001]),
            ("set_volume_ratio", [0.8]),
            ("set_limit_mode", ["volume"]),
            ("set_yesterday_position", [{"000001.XSHE": {"amount": 1000, "cost_basis": 10.0}}])
        ]
        
        for api_name, args in config_apis:
            with pytest.raises(ValueError, match=f"API '{api_name}' is not supported"):
                getattr(router, api_name)(*args)

    def test_set_parameters_not_supported_in_research(self, router):
        """测试set_parameters在研究模式下不被支持"""
        # 根据PTrade官方文档，set_parameters仅支持[回测/交易]，不支持研究模式
        with pytest.raises(ValueError, match="API 'set_parameters' is not supported"):
            router.set_parameters({"param": "value"})

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
        assert len(all_days) > 50  # mock数据应该有50+个交易日

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
        # 根据PTrade官方文档，log函数"仅在回测、交易模块可用"
        # 研究模式不支持log功能，调用log方法应该抛出NotImplementedError
        with pytest.raises(
            NotImplementedError, match="log function is not supported in research mode"
        ):
            router.log("test message")

    def test_research_mode_characteristics(self, router):
        """测试研究模式的特征"""
        # 研究模式应该：
        # 1. 支持数据查询（部分）
        # 2. 支持技术指标计算
        # 3. 不支持交易操作
        # 4. 不支持持仓查询
        # 5. 不支持订单查询
        # 6. 不支持配置设置（根据PTrade官方文档）

        # 支持的功能（根据PTrade官方文档）
        assert router.is_mode_supported("get_price")
        assert router.is_mode_supported("get_fundamentals")
        assert router.is_mode_supported("get_MACD")
        assert router.is_mode_supported("get_stock_info")
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
        
        config_apis = [
            "get_history",  # 根据PTrade官方文档，仅支持回测/交易
            "set_universe",
            "set_benchmark",
            "set_commission",
            "set_slippage",
            "set_parameters"
        ]

        for api in trading_apis + config_apis:
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

        # 验证fallback数据的结构正确性（因为mock插件会抛出异常，使用fallback逻辑）
        for _, row in fundamentals.iterrows():
            # fallback实现返回0.0作为默认值，这是合理的行为
            assert row["total_assets"] == 0.0  # fallback默认值
            assert row["total_liab"] == 0.0  # fallback默认值
            assert row["pe_ratio"] == 0.0  # fallback默认值
            assert row["pb_ratio"] == 0.0  # fallback默认值
            assert row["roe"] == 0.0  # fallback默认值
            assert row["eps"] == 0.0  # fallback默认值

            # 验证股票代码正确
            assert row["code"] in ["000001.XSHE", "000002.XSHE"]
            assert row["date"] == "2023-12-31"

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

    def test_universe_and_benchmark_apis_not_supported(self, router):
        """测试股票池和基准设置API在研究模式下不被支持"""
        # 根据PTrade官方文档，set_universe和set_benchmark仅支持[回测/交易]，不支持研究模式
        with pytest.raises(ValueError, match="API 'set_universe' is not supported"):
            router.set_universe(["000001.XSHE", "000002.XSHE"])
            
        with pytest.raises(ValueError, match="API 'set_benchmark' is not supported"):
            router.set_benchmark("000905.SH")
