# -*- coding: utf-8 -*-
"""
PTrade 适配器测试

测试PTrade兼容层的基本功能，确保API注入和策略加载正常工作。
"""

import pytest
import tempfile
import textwrap
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from simtradelab.adapters.ptrade.adapter import (
    PTradeAdapter,
    PTradeContext,
    Portfolio,
    Position,
    Blotter,
    PTradeAPIRegistry,
    PTradeAdapterError,
    PTradeCompatibilityError,
    PTradeAPIError
)
from simtradelab.plugins.base import PluginMetadata, PluginConfig
from simtradelab.core.event_bus import EventBus


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
        assert hasattr(context, 'g')
        assert hasattr(context, 'blotter')


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
        position = Position(sid="000001.SZ", enable_amount=1000, amount=1000, cost_basis=10.0, last_sale_price=12.0)
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
        position = Position(sid="000001.SZ", enable_amount=1000, amount=1000, cost_basis=10.0, last_sale_price=10.0)
        
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
        position = Position(sid="000001.SZ", enable_amount=1000, amount=1000, cost_basis=10.0, last_sale_price=12.0)
        
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
        assert order.status == 'new'
    
    def test_cancel_order(self):
        """测试撤销订单"""
        blotter = Blotter()
        
        order_id = blotter.create_order("000001.SZ", 1000, 10.0)
        success = blotter.cancel_order(order_id)
        
        assert success is True
        
        order = blotter.get_order(order_id)
        assert order.status == 'cancelled'
        
        # 测试撤销不存在的订单
        success = blotter.cancel_order("nonexistent")
        assert success is False


class TestPTradeAPIRegistry:
    """测试API注册表"""
    
    def test_registry_creation(self):
        """测试注册表创建"""
        registry = PTradeAPIRegistry()
        
        assert registry._apis == {}
        assert len(registry._categories) == 9  # 实际有9个类别
        assert registry.list_all_apis() == []
    
    def test_register_api(self):
        """测试注册API"""
        registry = PTradeAPIRegistry()
        
        def test_func():
            return "test"
        
        registry.register_api("test_func", test_func, "utils")
        
        assert "test_func" in registry._apis
        assert registry.get_api("test_func") is test_func
        assert "test_func" in registry.get_apis_by_category("utils")
        assert registry.list_all_apis() == ["test_func"]


class TestPTradeAdapter:
    """测试PTrade兼容层适配器"""
    
    @pytest.fixture
    def adapter(self):
        """适配器fixture"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig(config={'initial_cash': 1000000})
        adapter = PTradeAdapter(metadata, config)
        yield adapter
        if adapter.state in [adapter.state.STARTED, adapter.state.PAUSED]:
            adapter.shutdown()
    
    def test_adapter_creation(self, adapter):
        """测试适配器创建"""
        assert adapter.metadata.name == "ptrade_adapter"
        assert adapter._ptrade_context is None
        assert adapter._strategy_module is None
        assert isinstance(adapter._api_registry, PTradeAPIRegistry)
    
    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        adapter.initialize()
        
        assert adapter.state == adapter.state.INITIALIZED
        assert adapter._ptrade_context is not None
        assert isinstance(adapter._ptrade_context, PTradeContext)
        assert adapter._ptrade_context.portfolio.cash == 1000000
        
        # 检查API是否已注册
        apis = adapter._api_registry.list_all_apis()
        assert len(apis) > 0
        assert "get_history" in apis
        assert "order" in apis
        assert "set_commission" in apis
    
    def test_strategy_loading(self, adapter):
        """测试策略加载"""
        adapter.initialize()
        
        # 创建测试策略文件
        strategy_code = textwrap.dedent("""
            def initialize(context):
                context.g.initialized = True
            
            def handle_data(context, data):
                context.g.handled = True
        """)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_code)
            strategy_path = f.name
        
        try:
            # 加载策略
            success = adapter.load_strategy(strategy_path)
            
            assert success is True
            assert adapter._strategy_module is not None
            assert adapter._strategy_hooks['initialize'] is not None
            assert adapter._strategy_hooks['handle_data'] is not None
            
            # 检查全局对象是否已注入
            assert hasattr(adapter._strategy_module, 'g')
            assert hasattr(adapter._strategy_module, 'log')
            assert hasattr(adapter._strategy_module, 'get_history')
            assert hasattr(adapter._strategy_module, 'order')
            
            # 检查策略是否已初始化
            assert adapter._ptrade_context.g.initialized is True
            
        finally:
            Path(strategy_path).unlink()
    
    def test_strategy_loading_nonexistent_file(self, adapter):
        """测试加载不存在的策略文件"""
        adapter.initialize()
        
        with pytest.raises(PTradeCompatibilityError, match="Strategy file not found"):
            adapter.load_strategy("/nonexistent/strategy.py")
    
    def test_api_get_history(self, adapter):
        """测试get_history API"""
        adapter.initialize()
        
        # 设置股票池
        adapter._api_set_universe(["000001.SZ", "000002.SZ"])
        
        # 调用API
        result = adapter._api_get_history(count=10, frequency='1d')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
    
    def test_api_order(self, adapter):
        """测试order API"""
        adapter.initialize()
        
        # 下单
        order_id = adapter._api_order("000001.SZ", 1000, 10.0)
        
        assert order_id is not None
        assert order_id.startswith("order_")
        
        # 检查订单
        order = adapter._ptrade_context.blotter.get_order(order_id)
        assert order is not None
        assert order.symbol == "000001.SZ"
        assert order.amount == 1000
        assert order.status == 'filled'
        
        # 检查持仓
        assert "000001.SZ" in adapter._ptrade_context.portfolio.positions
        position = adapter._ptrade_context.portfolio.positions["000001.SZ"]
        assert position.amount == 1000
    
    def test_api_order_insufficient_cash(self, adapter):
        """测试资金不足时的下单"""
        adapter.initialize()
        
        # 尝试下一个超出资金的大单
        order_id = adapter._api_order("000001.SZ", 200000, 10.0)  # 需要200万，但只有100万
        
        assert order_id is None  # 应该失败
    
    def test_api_order_target(self, adapter):
        """测试order_target API"""
        adapter.initialize()
        
        # 第一次下单到目标数量
        order_id1 = adapter._api_order_target("000001.SZ", 1000)
        assert order_id1 is not None
        
        # 第二次调整到新的目标数量
        order_id2 = adapter._api_order_target("000001.SZ", 1500)
        assert order_id2 is not None
        
        # 检查最终持仓
        position = adapter._ptrade_context.portfolio.positions["000001.SZ"]
        assert position.amount == 1500
    
    def test_api_cancel_order(self, adapter):
        """测试cancel_order API"""
        adapter.initialize()
        
        # 创建订单但不执行
        order_id = adapter._ptrade_context.blotter.create_order("000001.SZ", 1000, 10.0)
        
        # 撤销订单
        success = adapter._api_cancel_order(order_id)
        assert success is True
        
        order = adapter._ptrade_context.blotter.get_order(order_id)
        assert order.status == 'cancelled'
    
    def test_api_set_commission(self, adapter):
        """测试set_commission API"""
        adapter.initialize()
        
        adapter._api_set_commission(0.001)
        assert adapter._commission_rate == 0.001
    
    def test_api_set_universe(self, adapter):
        """测试set_universe API"""
        adapter.initialize()
        
        securities = ["000001.SZ", "000002.SZ", "600000.SH"]
        adapter._api_set_universe(securities)
        
        assert adapter._ptrade_context.universe == securities
    
    def test_execute_strategy_hook(self, adapter):
        """测试执行策略钩子"""
        adapter.initialize()
        
        # 创建测试策略
        strategy_code = textwrap.dedent("""
            def initialize(context):
                context.g.test_value = 42
                
            def handle_data(context, data):
                context.g.handle_called = True
                return "handled"
        """)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(strategy_code)
            strategy_path = f.name
        
        try:
            adapter.load_strategy(strategy_path)
            
            # 执行handle_data钩子
            if adapter._strategy_hooks['handle_data']:
                result = adapter._strategy_hooks['handle_data'](adapter._ptrade_context, {})
                
                assert result == "handled"
                assert adapter._ptrade_context.g.handle_called is True
            
        finally:
            Path(strategy_path).unlink()
    
    def test_register_custom_api(self, adapter):
        """测试注册自定义API"""
        adapter.initialize()
        
        def custom_func(adapter_ref, param1, param2):
            return param1 + param2
        
        adapter._api_registry.register_api("custom_func", custom_func, "utils")
        
        # 检查API是否已注册
        assert "custom_func" in adapter._api_registry.list_all_apis()
        api_func = adapter._api_registry.get_api("custom_func")
        assert api_func is custom_func
    
    def test_get_api_stats(self, adapter):
        """测试获取API统计信息"""
        adapter.initialize()
        
        stats = adapter.get_api_stats()
        
        assert isinstance(stats, dict)
        assert 'total_apis' in stats
        assert 'market_data_apis' in stats
        assert 'trading_apis' in stats
        assert 'strategy_loaded' in stats
        assert 'portfolio_value' in stats
        
        assert stats['total_apis'] > 0
        assert stats['portfolio_value'] == 1000000.0
        assert stats['strategy_loaded'] is False
    
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
            adapter._event_bus = event_bus  # 手动注入事件总线
            
            adapter.initialize()
            adapter.start()
            
            # 设置股票池并调用API触发事件
            adapter._api_set_universe(["000001.SZ"])
            adapter._api_get_history(count=5)
            
            # 检查事件是否被触发
            assert len(events) >= 1
            
        finally:
            event_bus.shutdown()
    
    def test_context_manager(self, adapter):
        """测试上下文管理器"""
        with adapter:
            adapter.initialize()
            assert adapter.state == adapter.state.INITIALIZED
        
        # 应该自动关闭
        assert adapter.state == adapter.state.UNINITIALIZED


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