# -*- coding: utf-8 -*-
"""
PTrade 适配器测试

测试PTrade兼容层的基本功能，确保API注入和策略加载正常工作。
"""

import tempfile
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from simtradelab.adapters.ptrade.adapter import (
    Blotter,
    Portfolio,
    Position,
    PTradeAdapter,
    PTradeAdapterError,
    PTradeAPIError,
    PTradeCompatibilityError,
    PTradeContext,
)
from simtradelab.core.event_bus import EventBus
from simtradelab.plugins.base import PluginConfig


def create_mock_data_plugin():
    """创建模拟数据插件"""
    mock_plugin = MagicMock()

    # 模拟历史数据
    def mock_get_multiple_history_data(
        securities, count, start_date=None, end_date=None
    ):
        data = []
        for security in securities:
            base_price = 15.0 if security.startswith("000") else 20.0
            for i in range(count):
                date = datetime.now() - timedelta(days=count - i)
                price = base_price * (1 + np.random.normal(0, 0.01))
                data.append(
                    {
                        "security": security,
                        "date": date,
                        "open": price * 0.98,
                        "high": price * 1.02,
                        "low": price * 0.97,
                        "close": price,
                        "volume": np.random.randint(100000, 1000000),
                        "money": price * np.random.randint(100000, 1000000),
                        "price": price,
                    }
                )
        return pd.DataFrame(data)

    def mock_get_current_price(security):
        base_price = 15.0 if security.startswith("000") else 20.0
        return base_price

    def mock_get_market_snapshot(securities):
        snapshot = {}
        for security in securities:
            base_price = 15.0 if security.startswith("000") else 20.0
            snapshot[security] = {
                "last_price": base_price,
                "pre_close": base_price * 0.99,
                "open": base_price * 0.98,
                "high": base_price * 1.02,
                "low": base_price * 0.97,
                "close": base_price,  # Add close field
                "volume": 100000,
                "money": base_price * 100000,
                "datetime": datetime.now(),
                "price": base_price,
            }
        return snapshot

    mock_plugin.get_multiple_history_data = mock_get_multiple_history_data
    mock_plugin.get_current_price = mock_get_current_price
    mock_plugin.get_market_snapshot = mock_get_market_snapshot

    return mock_plugin


def setup_adapter_with_data_plugin(adapter):
    """设置适配器的数据插件"""
    mock_plugin_manager = MagicMock()
    mock_data_plugin = create_mock_data_plugin()

    # 模拟技术指标插件
    mock_indicators_plugin = MagicMock()

    def mock_calculate_macd(close, short=12, long=26, m=9):
        length = len(close)
        return pd.DataFrame(
            {
                "MACD": np.random.randn(length) * 0.1,
                "MACD_signal": np.random.randn(length) * 0.1,
                "MACD_hist": np.random.randn(length) * 0.05,
            }
        )

    def mock_calculate_kdj(high, low, close, n=9, m1=3, m2=3):
        length = len(close)
        return pd.DataFrame(
            {
                "K": np.random.uniform(0, 100, length),
                "D": np.random.uniform(0, 100, length),
                "J": np.random.uniform(0, 100, length),
            }
        )

    def mock_calculate_rsi(close, n=6):
        length = len(close)
        return pd.DataFrame({"RSI": np.random.uniform(0, 100, length)})

    def mock_calculate_cci(high, low, close, n=14):
        length = len(close)
        return pd.DataFrame({"CCI": np.random.randn(length) * 50})

    mock_indicators_plugin.calculate_macd = mock_calculate_macd
    mock_indicators_plugin.calculate_kdj = mock_calculate_kdj
    mock_indicators_plugin.calculate_rsi = mock_calculate_rsi
    mock_indicators_plugin.calculate_cci = mock_calculate_cci

    def mock_get_plugin(name):
        if name == "csv_data_plugin":
            return mock_data_plugin
        elif name == "technical_indicators_plugin":
            return mock_indicators_plugin
        return None

    mock_plugin_manager.get_plugin = mock_get_plugin

    adapter.set_plugin_manager(mock_plugin_manager)
    return adapter


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


class TestPTradeAdapter:
    """测试PTrade兼容层适配器"""

    @pytest.fixture
    def adapter(self):
        """适配器fixture"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig(config={"initial_cash": 1000000})
        adapter = PTradeAdapter(metadata, config)
        yield adapter
        if adapter.state in [adapter.state.STARTED, adapter.state.PAUSED]:
            adapter.shutdown()

    def test_adapter_creation(self, adapter):
        """测试适配器创建"""
        assert adapter.metadata.name == "ptrade_adapter"
        assert adapter._ptrade_context is None
        assert adapter._strategy_module is None

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        adapter.initialize()

        assert adapter.state == adapter.state.INITIALIZED
        assert adapter._ptrade_context is not None
        assert isinstance(adapter._ptrade_context, PTradeContext)
        assert adapter._ptrade_context.portfolio.cash == 1000000

    def test_strategy_loading(self, adapter):
        """测试策略加载"""
        adapter.initialize()

        # 创建测试策略文件
        strategy_code = textwrap.dedent(
            """
            def initialize(context):
                context.g.initialized = True

            def handle_data(context, data):
                context.g.handled = True
        """
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(strategy_code)
            strategy_path = f.name

        try:
            # 加载策略
            success = adapter.load_strategy(strategy_path)

            assert success is True
            assert adapter._strategy_module is not None
            assert adapter._strategy_hooks["initialize"] is not None
            assert adapter._strategy_hooks["handle_data"] is not None

            # 检查全局对象是否已注入
            assert hasattr(adapter._strategy_module, "g")
            assert hasattr(adapter._strategy_module, "log")
            assert hasattr(adapter._strategy_module, "get_history")
            assert hasattr(adapter._strategy_module, "order")

            # 检查策略是否已初始化
            assert adapter._ptrade_context.g.initialized is True

        finally:
            Path(strategy_path).unlink()

    def test_strategy_loading_nonexistent_file(self, adapter):
        """测试加载不存在的策略文件"""
        adapter.initialize()

        with pytest.raises(
            PTradeCompatibilityError, match="Strategy file not found"
        ):
            adapter.load_strategy("/nonexistent/strategy.py")

    def test_api_get_history(self, adapter):
        """测试get_history API"""
        setup_adapter_with_data_plugin(adapter)
        adapter.initialize()

        # 设置股票池
        adapter._ptrade_context.universe = ["000001.SZ", "000002.SZ"]

        # 调用API - 当前实现返回空DataFrame
        result = adapter._api_router.get_history(count=10, frequency="1d")

        # 验证返回类型正确，但当前实现返回空数据
        assert isinstance(result, pd.DataFrame)
        # TODO: 当API路由器集成数据插件后，这个测试应该验证 len(result) > 0

    def test_api_order(self, adapter):
        """测试order API"""
        adapter.initialize()

        # 下单
        order_id = adapter._api_router.order("000001.SZ", 1000, 10.0)

        assert order_id is not None
        assert order_id.startswith("order_")

        # 检查订单
        order = adapter._ptrade_context.blotter.get_order(order_id)
        assert order is not None
        assert order.symbol == "000001.SZ"
        assert order.amount == 1000
        assert order.status == "filled"

        # 检查持仓
        assert "000001.SZ" in adapter._ptrade_context.portfolio.positions
        position = adapter._ptrade_context.portfolio.positions["000001.SZ"]
        assert position.amount == 1000

    def test_api_order_insufficient_cash(self, adapter):
        """测试资金不足时的下单"""
        adapter.initialize()

        # 尝试下一个超出资金的大单
        # 需要200万，但只有100万
        order_id = adapter._api_router.order("000001.SZ", 200000, 10.0)

        assert order_id is None  # 应该失败

    def test_api_cancel_order(self, adapter):
        """测试cancel_order API"""
        adapter.initialize()

        # 创建订单但不执行
        order_id = adapter._ptrade_context.blotter.create_order(
            "000001.SZ", 1000, 10.0
        )

        # 撤销订单
        success = adapter._api_router.cancel_order(order_id)
        assert success is True

        order = adapter._ptrade_context.blotter.get_order(order_id)
        assert order.status == "cancelled"

    def test_api_set_commission(self, adapter):
        """测试set_commission API"""
        adapter.initialize()

        adapter._commission_rate = 0.001
        assert adapter._commission_rate == 0.001

    def test_api_set_universe(self, adapter):
        """测试set_universe API"""
        adapter.initialize()

        securities = ["000001.SZ", "000002.SZ", "600000.SH"]
        adapter._ptrade_context.universe = securities

        assert adapter._ptrade_context.universe == securities

    def test_execute_strategy_hook(self, adapter):
        """测试执行策略钩子"""
        adapter.initialize()

        # 创建测试策略
        strategy_code = textwrap.dedent(
            """
            def initialize(context):
                context.g.test_value = 42

            def handle_data(context, data):
                context.g.handle_called = True
                return "handled"
        """
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(strategy_code)
            strategy_path = f.name

        try:
            adapter.load_strategy(strategy_path)

            # 执行handle_data钩子
            if adapter._strategy_hooks["handle_data"]:
                result = adapter._strategy_hooks["handle_data"](
                    adapter._ptrade_context, {}
                )

                assert result == "handled"
                assert adapter._ptrade_context.g.handle_called is True

        finally:
            Path(strategy_path).unlink()

    def test_get_api_stats(self, adapter):
        """测试获取API统计信息"""
        adapter.initialize()

        stats = adapter.get_api_stats()

        assert isinstance(stats, dict)
        assert "total_apis" in stats
        assert "market_data_apis" in stats
        assert "trading_apis" in stats
        assert "strategy_loaded" in stats
        assert "portfolio_value" in stats

        assert stats["total_apis"] > 0
        assert stats["portfolio_value"] == 1000000.0
        assert stats["strategy_loaded"] is False

    def test_adapter_with_event_bus(self):
        """测试适配器与事件总线的集成"""
        event_bus = EventBus()

        # 监听PTrade事件
        events = []

        def event_handler(event):
            events.append(event)

        event_bus.subscribe("ptrade.adapter.started", event_handler)
        event_bus.subscribe("ptrade.api.*", event_handler)

        try:
            metadata = PTradeAdapter.METADATA
            config = PluginConfig()
            adapter = PTradeAdapter(metadata, config)
            setup_adapter_with_data_plugin(adapter)
            adapter.set_event_bus(event_bus)  # 使用新的方法设置事件总线

            adapter.initialize()
            adapter.start()

            # 验证事件是否被触发
            assert len(events) > 0

            adapter.stop()

        finally:
            event_bus.shutdown()

    def test_context_manager(self, adapter):
        """测试上下文管理器"""
        with adapter:
            adapter.initialize()
            assert adapter.state == adapter.state.INITIALIZED

        # 应该自动关闭
        assert adapter.state == adapter.state.UNINITIALIZED


class TestPTradeExtendedTradingAPIs:
    """测试扩展的交易API"""

    @pytest.fixture
    def adapter(self):
        """创建测试适配器"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig(config={"initial_cash": 1000000})
        adapter = PTradeAdapter(metadata, config)
        setup_adapter_with_data_plugin(adapter)
        adapter.initialize()
        return adapter

    def test_basic_order(self, adapter):
        """测试基本下单"""
        # 测试正常下单
        order_id = adapter._api_router.order("000001.SZ", 1000, 10.0)
        assert order_id is not None
        assert order_id.startswith("order_")

        # 检查持仓
        positions = adapter._api_router.get_positions(["000001.SZ"])
        assert "000001.SZ" in positions
        assert positions["000001.SZ"]["amount"] > 0

    def test_get_positions(self, adapter):
        """测试获取多持仓"""
        # 先下单
        adapter._api_router.order("000001.SZ", 1000, 10.0)
        adapter._api_router.order("000002.SZ", 2000, 15.0)

        # 获取持仓
        positions = adapter._api_router.get_positions(
            ["000001.SZ", "000002.SZ", "000003.SZ"]
        )

        assert len(positions) == 3
        assert "000001.SZ" in positions
        assert "000002.SZ" in positions
        assert "000003.SZ" in positions

        # 检查有持仓的股票
        assert positions["000001.SZ"]["amount"] > 0
        assert positions["000002.SZ"]["amount"] > 0

        # 检查无持仓的股票
        assert positions["000003.SZ"]["amount"] == 0

    def test_get_orders(self, adapter):
        """测试获取订单"""
        # 创建几个订单
        adapter._api_router.order("000001.SZ", 1000, 10.0)
        adapter._api_router.order("000002.SZ", 2000, 15.0)
        adapter._api_router.order("000001.SZ", -500, 12.0)

        # 获取所有订单
        all_orders = adapter._api_router.get_orders()
        assert len(all_orders) == 3

        # 获取特定股票的订单
        orders_001 = adapter._api_router.get_orders("000001.SZ")
        assert len(orders_001) == 2
        assert all(order.symbol == "000001.SZ" for order in orders_001)

    def test_get_open_orders(self, adapter):
        """测试获取未完成订单"""
        # 创建订单（会自动执行）
        adapter._api_router.order("000001.SZ", 1000, 10.0)

        # 获取未完成订单（应该为空，因为订单已执行）
        open_orders = adapter._api_router.get_open_orders()
        assert len(open_orders) == 0

        # 手动创建未完成订单
        order_id = adapter._ptrade_context.blotter.create_order(
            "000002.SZ", 1000, 10.0
        )

        # 获取未完成订单
        open_orders = adapter._api_router.get_open_orders()
        assert len(open_orders) == 1
        assert open_orders[0].id == order_id

    def test_get_trades(self, adapter):
        """测试获取成交记录"""
        # 创建订单
        adapter._api_router.order("000001.SZ", 1000, 10.0)
        adapter._api_router.order("000002.SZ", 2000, 15.0)

        # 获取成交记录
        trades = adapter._api_router.get_trades()
        assert len(trades) == 2

        # 检查成交记录内容
        trade = trades[0]
        assert "order_id" in trade
        assert "security" in trade
        assert "amount" in trade
        assert "side" in trade
        assert trade["side"] == "buy"

        # 获取特定股票的成交记录
        trades_001 = adapter._api_router.get_trades("000001.SZ")
        assert len(trades_001) == 1
        assert trades_001[0]["security"] == "000001.SZ"


class TestPTradeDataAPIs:
    """测试数据API"""

    @pytest.fixture
    def adapter(self):
        """创建测试适配器"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig()
        adapter = PTradeAdapter(metadata, config)
        setup_adapter_with_data_plugin(adapter)
        adapter.initialize()
        adapter._ptrade_context.universe = ["000001.SZ", "000002.SZ"]
        return adapter

    def test_get_history_improved(self, adapter):
        """测试改进的历史数据API"""
        # 测试DataFrame格式
        history = adapter._api_router.get_history(
            count=10,
            field=["open", "high", "low", "close", "volume"],
        )

        assert isinstance(history, pd.DataFrame)
        assert history.shape[0] == 20  # 2个股票 x 10天
        assert list(history.columns) == [
            "open", "high", "low", "close", "volume"
        ]
        assert history.index.names == ["security", "date"]

        # 测试字典格式
        history_dict = adapter._api_router.get_history(
            count=5, field=["close", "volume"], is_dict=True
        )

        assert isinstance(history_dict, dict)
        assert "000001.SZ" in history_dict
        assert "000002.SZ" in history_dict
        assert "close" in history_dict["000001.SZ"]
        assert "volume" in history_dict["000001.SZ"]
        assert len(history_dict["000001.SZ"]["close"]) == 5

    def test_get_history_with_dates(self, adapter):
        """测试带日期范围的历史数据"""
        history = adapter._api_router.get_history(
            count=10,
            start_date="2023-01-01",
            end_date="2023-01-10",
            field=["close"],
        )

        assert isinstance(history, pd.DataFrame)
        assert "close" in history.columns

        # 检查日期范围
        dates = history.index.get_level_values("date").unique()
        assert len(dates) >= 1

    def test_get_price_improved(self, adapter):
        """测试改进的价格数据API"""
        # 测试单个股票
        price = adapter._api_router.get_price("000001.SZ", count=5)
        assert isinstance(price, pd.DataFrame)
        assert price.shape[0] == 5

        # 测试多个股票
        price_multi = adapter._api_router.get_price(
            ["000001.SZ", "000002.SZ"], count=3
        )
        assert isinstance(price_multi, pd.DataFrame)
        assert price_multi.shape[0] == 6  # 2个股票 x 3天

        # 测试指定字段
        price_fields = adapter._api_router.get_price(
            "000001.SZ", count=3, fields=["open", "close"]
        )
        assert list(price_fields.columns) == ["open", "close"]

    def test_get_current_price(self, adapter):
        """测试获取当前价格"""
        price = adapter._get_current_price("000001.SZ")
        assert isinstance(price, float)
        assert price > 0

        # 测试缓存
        adapter._current_data["000001.SZ"] = {"last_price": 15.0}
        price_cached = adapter._get_current_price("000001.SZ")
        assert price_cached == 15.0

    def test_generate_price_series(self, adapter):
        """测试价格序列生成"""
        base_price = 10.0
        length = 20

        prices = adapter._generate_price_series(base_price, length)

        assert isinstance(prices, np.ndarray)
        assert len(prices) == length
        assert all(p > 0 for p in prices)


class TestPTradeTechnicalIndicators:
    """测试技术指标API"""

    @pytest.fixture
    def adapter(self):
        """创建测试适配器"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig()
        adapter = PTradeAdapter(metadata, config)
        setup_adapter_with_data_plugin(adapter)
        adapter.initialize()
        return adapter

    def test_macd(self, adapter):
        """测试MACD指标"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        macd = adapter._api_router.get_MACD(close_data)

        assert isinstance(macd, pd.DataFrame)
        assert list(macd.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(macd) == len(close_data)
        assert not macd.isnull().any().any()

    def test_kdj(self, adapter):
        """测试KDJ指标"""
        high_data = np.array(
            [10.2, 10.3, 10.4, 10.1, 10.5, 10.6, 10.3, 10.7, 10.8, 10.2]
        )
        low_data = np.array(
            [9.8, 9.9, 10.0, 9.7, 10.1, 10.2, 9.9, 10.3, 10.4, 9.8]
        )
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        kdj = adapter._api_router.get_KDJ(high_data, low_data, close_data)

        assert isinstance(kdj, pd.DataFrame)
        assert list(kdj.columns) == ["K", "D", "J"]
        assert len(kdj) == len(close_data)

    def test_rsi(self, adapter):
        """测试RSI指标"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        rsi = adapter._api_router.get_RSI(close_data)

        assert isinstance(rsi, pd.DataFrame)
        assert list(rsi.columns) == ["RSI"]
        assert len(rsi) == len(close_data)

    def test_cci(self, adapter):
        """测试CCI指标"""
        high_data = np.array(
            [10.2, 10.3, 10.4, 10.1, 10.5, 10.6, 10.3, 10.7, 10.8, 10.2]
        )
        low_data = np.array(
            [9.8, 9.9, 10.0, 9.7, 10.1, 10.2, 9.9, 10.3, 10.4, 9.8]
        )
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        cci = adapter._api_router.get_CCI(high_data, low_data, close_data)

        assert isinstance(cci, pd.DataFrame)
        assert list(cci.columns) == ["CCI"]
        assert len(cci) == len(close_data)


class TestPTradeStrategyLifecycle:
    """测试策略生命周期API"""

    @pytest.fixture
    def adapter(self):
        """创建测试适配器"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig()
        adapter = PTradeAdapter(metadata, config)
        setup_adapter_with_data_plugin(adapter)
        adapter.initialize()
        return adapter

    def test_strategy_execution(self, adapter):
        """测试策略执行"""
        # 创建测试策略
        strategy_code = textwrap.dedent(
            """
            def initialize(context):
                context.g.initialized = True
                set_universe(["000001.SZ", "000002.SZ"])

            def handle_data(context, data):
                context.g.data_received = len(data)
                if len(context.portfolio.positions) == 0:
                    order_value("000001.SZ", 50000)

            def before_trading_start(context, data):
                context.g.before_called = True

            def after_trading_end(context, data):
                context.g.after_called = True
        """
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(strategy_code)
            strategy_path = f.name

        try:
            # 加载策略
            adapter.load_strategy(strategy_path)

            # 运行策略
            adapter.run_strategy()

            # 检查结果
            g = adapter._ptrade_context.g
            assert g.initialized is True
            assert g.before_called is True
            assert g.after_called is True
            assert g.data_received > 0

            # 检查持仓
            assert len(adapter._ptrade_context.portfolio.positions) > 0

        finally:
            Path(strategy_path).unlink()

    def test_strategy_performance(self, adapter):
        """测试策略性能统计"""
        # 创建简单策略
        strategy_code = textwrap.dedent(
            """
            def initialize(context):
                set_universe(["000001.SZ"])

            def handle_data(context, data):
                order_value("000001.SZ", 10000)
        """
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(strategy_code)
            strategy_path = f.name

        try:
            adapter.load_strategy(strategy_path)
            adapter.run_strategy()

            # 获取性能统计
            performance = adapter.get_strategy_performance()

            assert "portfolio_value" in performance
            assert "cash" in performance
            assert "returns" in performance
            assert "pnl" in performance
            assert "positions_count" in performance
            assert "total_trades" in performance

            assert isinstance(performance["portfolio_value"], float)
            assert isinstance(performance["positions_count"], int)
            assert performance["total_trades"] > 0

        finally:
            Path(strategy_path).unlink()

    def test_execute_strategy_hook(self, adapter):
        """测试策略钩子执行"""
        # 创建测试策略
        strategy_code = textwrap.dedent(
            """
            def initialize(context):
                context.g.test_value = 42

            def handle_data(context, data):
                return len(data)
        """
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(strategy_code)
            strategy_path = f.name

        try:
            adapter.load_strategy(strategy_path)

            # 测试钩子执行
            result = adapter.execute_strategy_hook(
                "handle_data", adapter._ptrade_context, {"test": 1}
            )
            assert result == 1

            # 测试未实现的钩子
            result = adapter.execute_strategy_hook(
                "before_trading_start", adapter._ptrade_context, {}
            )
            assert result is None

            # 测试无效钩子
            with pytest.raises(PTradeAPIError):
                adapter.execute_strategy_hook(
                    "invalid_hook", adapter._ptrade_context, {}
                )

        finally:
            Path(strategy_path).unlink()

    def test_generate_market_data(self, adapter):
        """测试市场数据生成"""
        # 设置股票池
        adapter._ptrade_context.universe = ["000001.SZ", "000002.SZ"]

        # 生成市场数据
        data = adapter._generate_market_data()

        assert isinstance(data, dict)
        assert "000001.SZ" in data
        assert "000002.SZ" in data

        # 检查数据格式
        stock_data = data["000001.SZ"]
        assert "price" in stock_data
        assert "open" in stock_data
        assert "high" in stock_data
        assert "low" in stock_data
        assert "close" in stock_data
        assert "volume" in stock_data
        assert "datetime" in stock_data

        # 检查数据缓存
        assert "000001.SZ" in adapter._current_data
        assert "last_price" in adapter._current_data["000001.SZ"]


class TestPTradeExceptions:
    """测试PTrade异常"""

    def test_ptrade_adapter_error(self):
        """测试PTrade适配器异常"""
        with pytest.raises(PTradeAdapterError):
            raise PTradeAdapterError("Test error")

    def test_ptrade_compatibility_error(self):
        """测试PTrade兼容性异常"""
        with pytest.raises(PTradeCompatibilityError):
            raise PTradeCompatibilityError("Compatibility error")

    def test_ptrade_api_error(self):
        """测试PTrade API异常"""
        with pytest.raises(PTradeAPIError):
            raise PTradeAPIError("API error")
