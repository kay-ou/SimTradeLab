# -*- coding: utf-8 -*-
"""
PTrade适配器核心功能测试
"""

import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from simtradelab.adapters.ptrade.adapter import PTradeAdapter
from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.utils import (
    PTradeAdapterError,
    PTradeAPIError,
    PTradeCompatibilityError,
)
from simtradelab.core.event_bus import EventBus
from simtradelab.plugins.base import PluginConfig


def create_mock_data_plugin():
    """创建模拟数据插件"""
    mock_plugin = MagicMock()

    def mock_get_multiple_history_data(
        securities, count, start_date=None, end_date=None
    ):
        # 返回模拟数据
        return MagicMock()

    def mock_get_current_price(security):
        base_price = 15.0 if security.startswith("000") else 20.0
        return base_price

    def mock_get_market_snapshot(securities):
        return {}

    mock_plugin.get_multiple_history_data = mock_get_multiple_history_data
    mock_plugin.get_current_price = mock_get_current_price
    mock_plugin.get_market_snapshot = mock_get_market_snapshot

    return mock_plugin


def setup_adapter_with_data_plugin(adapter):
    """设置适配器的数据插件"""
    mock_plugin_manager = MagicMock()
    mock_data_plugin = create_mock_data_plugin()

    def mock_get_plugin(name):
        if name == "csv_data_plugin":
            return mock_data_plugin
        return None

    mock_plugin_manager.get_plugin = mock_get_plugin
    adapter.set_plugin_manager(mock_plugin_manager)
    return adapter


class TestPTradeAdapter:
    """测试PTrade兼容层适配器核心功能"""

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

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
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

        with pytest.raises(PTradeCompatibilityError, match="Strategy file not found"):
            adapter.load_strategy("/nonexistent/strategy.py")

    def test_api_basic_functionality(self, adapter):
        """测试基本API功能"""
        setup_adapter_with_data_plugin(adapter)
        adapter.initialize()

        # 设置股票池
        adapter._ptrade_context.universe = ["000001.SZ", "000002.SZ"]

        # 测试下单
        order_id = adapter._api_router.order("000001.SZ", 1000, 10.0)
        assert order_id is not None
        assert order_id.startswith("order_")

        # 测试撤单
        success = adapter._api_router.cancel_order(order_id)
        assert success is True

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

        try:
            metadata = PTradeAdapter.METADATA
            config = PluginConfig()
            adapter = PTradeAdapter(metadata, config)
            setup_adapter_with_data_plugin(adapter)
            adapter.set_event_bus(event_bus)

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

    def test_strategy_execution(self, adapter):
        """测试策略执行"""
        setup_adapter_with_data_plugin(adapter)
        adapter.initialize()

        # 创建测试策略
        strategy_code = textwrap.dedent(
            """
            def initialize(context):
                context.g.initialized = True
                set_universe(["000001.SZ", "000002.SZ"])

            def handle_data(context, data):
                context.g.data_received = len(data)
        """
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(strategy_code)
            strategy_path = f.name

        try:
            # 加载策略
            adapter.load_strategy(strategy_path)

            # 检查结果
            g = adapter._ptrade_context.g
            assert g.initialized is True

        finally:
            Path(strategy_path).unlink()

    def test_error_handling(self, adapter):
        """测试错误处理"""
        adapter.initialize()

        # 测试无效的策略文件
        with pytest.raises(PTradeCompatibilityError):
            adapter.load_strategy("/nonexistent/file.py")

        # 测试资金不足的下单
        order_id = adapter._api_router.order("000001.SZ", 200000, 10.0)
        assert order_id is None  # 应该失败

    def test_portfolio_operations(self, adapter):
        """测试投资组合操作"""
        adapter.initialize()

        # 初始状态
        portfolio = adapter._ptrade_context.portfolio
        assert portfolio.cash == 1000000
        assert len(portfolio.positions) == 0

        # 下单后
        order_id = adapter._api_router.order("000001.SZ", 1000, 10.0)
        assert order_id is not None

        # 检查持仓
        assert "000001.SZ" in portfolio.positions
        position = portfolio.positions["000001.SZ"]
        assert position.amount == 1000
        # 成交价格可能包含滑点，所以使用近似检查
        assert abs(position.cost_basis - 10.0) < 0.1

    def test_multiple_orders(self, adapter):
        """测试多个订单"""
        adapter.initialize()

        # 创建多个订单
        order1 = adapter._api_router.order("000001.SZ", 1000, 10.0)
        order2 = adapter._api_router.order("000002.SZ", 2000, 15.0)
        order3 = adapter._api_router.order("000001.SZ", -500, 12.0)

        assert order1 is not None
        assert order2 is not None
        assert order3 is not None

        # 检查订单记录
        blotter = adapter._ptrade_context.blotter
        assert len(blotter.orders) == 3

    def test_api_router_selection(self, adapter):
        """测试API路由器选择"""
        adapter.initialize()

        # 默认应该使用回测路由器
        from simtradelab.adapters.ptrade.routers.backtest import BacktestAPIRouter

        assert isinstance(adapter._api_router, BacktestAPIRouter)

        # 测试路由器功能
        assert adapter._api_router.is_mode_supported("order")
        assert adapter._api_router.is_mode_supported("get_history")


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
