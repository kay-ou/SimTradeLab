# -*- coding: utf-8 -*-
"""
PTrade实盘交易路由器测试
"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Blotter, Portfolio, Position
from simtradelab.adapters.ptrade.routers.trading import TradingAPIRouter
from simtradelab.core.event_bus import EventBus


class TestTradingAPIRouter:
    """测试实盘交易API路由器"""

    @pytest.fixture
    def context(self):
        """创建测试上下文"""
        from simtradelab.adapters.ptrade.context import PTradeMode

        portfolio = Portfolio(cash=1000000)
        blotter = Blotter()
        context = PTradeContext(
            portfolio=portfolio, blotter=blotter, mode=PTradeMode.TRADING
        )
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

        import numpy as np
        import pandas as pd

        # 创建模拟插件管理器
        mock_plugin_manager = MagicMock()

        # 创建模拟数据插件
        mock_data_plugin = MagicMock()

        # 设置数据插件的方法识别
        mock_data_plugin.get_history_data = MagicMock()
        mock_data_plugin.get_current_price = MagicMock()
        mock_data_plugin.get_snapshot = MagicMock()
        mock_data_plugin.get_multiple_history_data = MagicMock()

        # 模拟get_multiple_history_data方法
        def mock_get_multiple_history_data(
            securities, count, start_date=None, end_date=None
        ):
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
            else:
                return pd.DataFrame()

        mock_data_plugin.get_multiple_history_data.side_effect = (
            mock_get_multiple_history_data
        )

        # 设置单个历史数据方法
        def mock_get_history_data(security, count):
            dates = pd.date_range("2023-01-01", periods=count, freq="D")
            return pd.DataFrame(
                {
                    "security": [security] * count,
                    "date": dates,
                    "open": np.random.uniform(10, 20, count),
                    "high": np.random.uniform(15, 25, count),
                    "low": np.random.uniform(5, 15, count),
                    "close": np.random.uniform(10, 20, count),
                    "volume": np.random.randint(1000, 10000, count),
                }
            )

        mock_data_plugin.get_history_data.side_effect = mock_get_history_data

        # 模拟get_snapshot方法
        def mock_get_snapshot(securities):
            snapshot = {}
            for security in securities:
                snapshot[security] = {
                    "last_price": 15.0 if security.startswith("000001") else 20.0,
                    "volume": 1000 if security.startswith("000001") else 2000,
                    "datetime": pd.Timestamp.now(),
                }
            return snapshot

        mock_data_plugin.get_snapshot.side_effect = mock_get_snapshot

        # 模拟get_stock_basic_info方法 (回退到基本信息生成)
        mock_data_plugin.get_stock_basic_info.side_effect = Exception(
            "Plugin method not available"
        )

        # 模拟get_fundamentals方法 (返回基本面数据)
        def mock_get_fundamentals(stocks, table, fields, date):
            rows = []
            for stock in stocks:
                row = {"code": stock, "date": date}
                for field in fields:
                    if field == "revenue":
                        row[field] = 1000000.0  # 模拟营收
                    elif field == "net_profit":
                        row[field] = 100000.0  # 模拟净利润
                    else:
                        row[field] = 0.0
                rows.append(row)
            return pd.DataFrame(rows)

        mock_data_plugin.get_fundamentals.side_effect = mock_get_fundamentals

        # 模拟交易日相关方法
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
        ]  # 模拟250个工作日

        # 模拟涨跌停检查方法
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

        # 创建路由器，传入插件管理器
        router = TradingAPIRouter(
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
            last_sale_price=10.0,
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
            last_sale_price=12.0,
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
            last_sale_price=12.0,
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
        # 实盘交易模式现在通过数据插件返回实际数据
        history = router.get_history(count=10, field=["close", "volume"])
        assert isinstance(history, pd.DataFrame)
        assert not history.empty  # 现在返回实际数据
        assert history.shape[0] == 20  # 2个股票 x 10天
        assert list(history.columns) == ["close", "volume"]

    def test_get_price(self, router):
        """测试获取价格数据"""
        # 实盘交易模式现在通过数据插件返回实际数据
        price = router.get_price("000001.XSHE", count=5)
        assert isinstance(price, pd.DataFrame)
        assert not price.empty  # 现在返回实际数据
        assert price.shape[0] == 5

    def test_get_snapshot(self, router):
        """测试获取快照数据"""
        snapshot = router.get_snapshot(["000001.XSHE", "000002.XSHE"])

        assert isinstance(snapshot, pd.DataFrame)
        assert snapshot.shape[0] == 2
        assert "last_price" in snapshot.columns
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

        assert hasattr(router.context, "_parameters")
        assert router.context._parameters == params

    def test_technical_indicators(self, router):
        """测试技术指标"""
        # 生成足够多的数据点以满足技术指标计算要求（至少35个数据点）

        data_length = 40
        base_price = 10.0
        noise = np.random.normal(0, 0.1, data_length)
        close_data = np.array(
            [base_price + i * 0.01 + noise[i] for i in range(data_length)]
        )

        # 测试MACD
        macd = router.get_MACD(close_data)
        assert isinstance(macd, pd.DataFrame)
        if not macd.empty:  # 只有在有数据时才检查列
            assert list(macd.columns) == ["MACD", "MACD_signal", "MACD_hist"]

        # 测试RSI (只需要n+1=7个数据点)
        rsi = router.get_RSI(close_data)
        assert isinstance(rsi, pd.DataFrame)
        if not rsi.empty:
            assert list(rsi.columns) == ["RSI"]

        # 测试KDJ (需要9个数据点)
        high_data = close_data + np.random.uniform(0, 0.2, data_length)
        low_data = close_data - np.random.uniform(0, 0.2, data_length)

        kdj = router.get_KDJ(high_data, low_data, close_data)
        assert isinstance(kdj, pd.DataFrame)
        if not kdj.empty:
            assert list(kdj.columns) == ["K", "D", "J"]

        # 测试CCI (需要14个数据点)
        cci = router.get_CCI(high_data, low_data, close_data)
        assert isinstance(cci, pd.DataFrame)
        if not cci.empty:
            assert list(cci.columns) == ["CCI"]

    def test_trading_day_functions(self, router):
        """测试交易日相关功能"""
        # 测试get_trading_day - 基础实现只是返回输入日期
        trading_day = router.get_trading_day("2023-12-29", 1)  # 周五+1天
        # 基础实现返回原始日期，不做真实的交易日计算
        assert trading_day == "2023-12-29"  # 基础实现返回输入日期

        # 测试get_trade_days - 基础实现返回空列表
        trade_days = router.get_trade_days("2023-12-25", "2023-12-29")
        assert isinstance(trade_days, list)  # 基础实现返回空列表

        # 测试get_all_trades_days - 基础实现返回空列表
        all_days = router.get_all_trades_days()
        assert isinstance(all_days, list)  # 基础实现返回空列表

    def test_stock_info(self, router):
        """测试股票信息"""
        info = router.get_stock_info(["000001.XSHE", "600000.XSHG"])

        # 基础实现返回空字典，验证调用不出错
        assert isinstance(info, dict)
        # 基础实现可能返回空字典，这是正常的
        # 实际实现会由具体的数据插件提供数据

    def test_check_limit(self, router):
        """测试涨跌停检查"""
        limit_info = router.check_limit("000001.XSHE")

        # 基础实现返回通用的涨跌停状态
        assert isinstance(limit_info, dict)
        assert "is_up_limit" in limit_info
        assert "is_down_limit" in limit_info
        assert isinstance(limit_info["is_up_limit"], bool)
        assert isinstance(limit_info["is_down_limit"], bool)

    def test_handle_data(self, router):
        """测试数据处理"""
        # 先模拟持仓
        position = Position(
            sid="000001.XSHE",
            amount=1000,
            enable_amount=1000,
            cost_basis=10.0,
            last_sale_price=10.0,
        )
        router.context.portfolio.positions["000001.XSHE"] = position

        # 处理价格数据
        data = {"000001.XSHE": {"price": 12.0}}

        router.handle_data(data)

        # 检查持仓价格是否更新
        assert position.last_sale_price == 12.0

    def test_log_function(self, router):
        """测试日志功能"""
        # 在当前实现中，log 是一个普通方法，可以直接调用
        router.log("Test info message")  # 基础log方法调用

        # 测试多参数日志
        router.log("Test", "multiple", "arguments")

        # 测试空参数
        router.log()

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
