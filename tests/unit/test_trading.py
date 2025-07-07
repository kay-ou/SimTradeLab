# -*- coding: utf-8 -*-
"""
交易模块测试
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from simtradelab.trading import (
    order, order_target, order_value, cancel_order,
    get_positions, get_position, get_open_orders, get_order, get_orders, get_trades
)
from simtradelab.context import Context, Portfolio, Position, Order, OrderStatus
from simtradelab.exceptions import (
    InvalidOrderError, InsufficientFundsError, InsufficientPositionError, TradingError
)


class TestTradingModule:
    """交易模块测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        portfolio = Portfolio(1000000.0)
        context = Context(portfolio)
        
        # 创建完整的blotter mock
        context.blotter = Mock()
        context.blotter.add_order = Mock(return_value="test_order_id")
        context.blotter.fill_order = Mock()
        context.blotter.cancel_order = Mock(return_value=True)
        context.blotter.get_open_orders = Mock(return_value={})
        context.blotter.get_order = Mock(return_value=None)
        context.blotter.get_daily_orders = Mock(return_value={})
        context.blotter.get_trades = Mock(return_value=[])
        
        engine.context = context
        engine.current_data = {
            'STOCK_A': {'close': 100.0, 'open': 99.0, 'high': 101.0, 'low': 98.0},
            'STOCK_B': {'close': 50.0, 'open': 49.5, 'high': 51.0, 'low': 48.0}
        }
        engine.commission_ratio = 0.0003
        engine.min_commission = 5.0
        return engine
    
    def test_order_success_buy(self, mock_engine):
        """测试成功买入订单"""
        order_id = order(mock_engine, 'STOCK_A', 1000)
        
        assert order_id is not None
        assert mock_engine.context.portfolio.cash < 1000000.0
        assert 'STOCK_A' in mock_engine.context.portfolio.positions
        assert mock_engine.context.portfolio.positions['STOCK_A'].amount == 1000
    
    def test_order_success_sell(self, mock_engine):
        """测试成功卖出订单"""
        # 先买入
        order(mock_engine, 'STOCK_A', 1000)
        initial_cash = mock_engine.context.portfolio.cash
        
        # 再卖出
        order_id = order(mock_engine, 'STOCK_A', -500)
        
        assert order_id is not None
        assert mock_engine.context.portfolio.cash > initial_cash
        assert mock_engine.context.portfolio.positions['STOCK_A'].amount == 500
    
    def test_order_invalid_security_empty(self, mock_engine):
        """测试空股票代码"""
        with pytest.raises(InvalidOrderError, match="股票代码不能为空"):
            order(mock_engine, '', 1000)
    
    def test_order_invalid_amount_zero(self, mock_engine):
        """测试零交易数量"""
        with pytest.raises(InvalidOrderError, match="交易数量不能为0"):
            order(mock_engine, 'STOCK_A', 0)
    
    def test_order_invalid_security_no_data(self, mock_engine):
        """测试无市场数据股票"""
        with pytest.raises(InvalidOrderError, match="没有.*的市场数据"):
            order(mock_engine, 'NONEXISTENT', 1000)
    
    def test_order_invalid_price_negative(self, mock_engine):
        """测试负价格"""
        mock_engine.current_data['STOCK_A']['close'] = -10.0
        
        with pytest.raises(InvalidOrderError, match="价格.*无效"):
            order(mock_engine, 'STOCK_A', 1000)
    
    def test_order_invalid_limit_price_negative(self, mock_engine):
        """测试负限价"""
        with pytest.raises(InvalidOrderError, match="限价.*必须大于0"):
            order(mock_engine, 'STOCK_A', 1000, limit_price=-50.0)
    
    def test_order_insufficient_funds(self, mock_engine):
        """测试资金不足"""
        # 设置很高的价格导致资金不足
        mock_engine.current_data['STOCK_A']['close'] = 10000.0
        
        with pytest.raises(InsufficientFundsError, match="现金不足"):
            order(mock_engine, 'STOCK_A', 1000)
    
    def test_order_insufficient_position(self, mock_engine):
        """测试持仓不足"""
        with pytest.raises(InsufficientPositionError, match="持仓不足"):
            order(mock_engine, 'STOCK_A', -1000)  # 尝试卖出但没有持仓
    
    def test_order_limit_buy_above_market(self, mock_engine):
        """测试限价买单价格高于市价"""
        order_id = order(mock_engine, 'STOCK_A', 1000, limit_price=110.0)
        assert order_id is not None
        assert mock_engine.context.portfolio.positions['STOCK_A'].amount == 1000
    
    def test_order_limit_buy_below_market(self, mock_engine):
        """测试限价买单价格低于市价（挂单）"""
        order_id = order(mock_engine, 'STOCK_A', 1000, limit_price=90.0)
        assert order_id is not None
        # 订单应该挂起，不会立即成交
        assert 'STOCK_A' not in mock_engine.context.portfolio.positions
    
    def test_order_target_success(self, mock_engine):
        """测试目标持仓订单"""
        order_id = order_target(mock_engine, 'STOCK_A', 1000)
        assert order_id is not None
        assert mock_engine.context.portfolio.positions['STOCK_A'].amount == 1000
        
        # 调整目标持仓
        order_id = order_target(mock_engine, 'STOCK_A', 500)
        assert order_id is not None
        assert mock_engine.context.portfolio.positions['STOCK_A'].amount == 500
    
    def test_order_value_success(self, mock_engine):
        """测试按金额下单"""
        order_id = order_value(mock_engine, 'STOCK_A', 100000.0)
        assert order_id is not None
        # 应该买入100股（100000 / 100 = 1000，取整百股为1000）
        assert mock_engine.context.portfolio.positions['STOCK_A'].amount == 1000
    
    def test_order_value_invalid_price(self, mock_engine):
        """测试按金额下单但价格无效"""
        mock_engine.current_data['STOCK_A']['close'] = 0
        order_id = order_value(mock_engine, 'STOCK_A', 100000.0)
        assert order_id is None
    
    def test_order_value_insufficient_amount(self, mock_engine):
        """测试按金额下单但金额不足一手"""
        order_id = order_value(mock_engine, 'STOCK_A', 50.0)  # 只能买0.5股，不足一手
        assert order_id is None
    
    def test_cancel_order_success(self, mock_engine):
        """测试取消订单成功"""
        # 创建一个挂单
        order_id = order(mock_engine, 'STOCK_A', 1000, limit_price=90.0)
        
        success = cancel_order(mock_engine, order_id)
        assert success is True
    
    def test_cancel_order_by_object(self, mock_engine):
        """测试通过订单对象取消订单"""
        # 创建订单对象
        order_obj = Order('STOCK_A', 1000, 90.0, 'limit')
        order_obj.order_id = 'test_order_id'
        
        mock_engine.context.blotter.cancel_order = Mock(return_value=True)
        
        success = cancel_order(mock_engine, order_obj)
        assert success is True
    
    def test_cancel_order_invalid_param(self, mock_engine):
        """测试取消订单参数无效"""
        success = cancel_order(mock_engine, 12345)  # 无效参数
        assert success is False
    
    def test_get_positions_all(self, mock_engine):
        """测试获取所有持仓"""
        # 建立一些持仓
        order(mock_engine, 'STOCK_A', 1000)
        order(mock_engine, 'STOCK_B', 500)
        
        positions = get_positions(mock_engine)
        assert len(positions) == 2
        assert 'STOCK_A' in positions
        assert 'STOCK_B' in positions
        assert positions['STOCK_A']['amount'] == 1000
        assert positions['STOCK_B']['amount'] == 500
    
    def test_get_positions_specific(self, mock_engine):
        """测试获取指定股票持仓"""
        order(mock_engine, 'STOCK_A', 1000)
        
        positions = get_positions(mock_engine, ['STOCK_A', 'STOCK_B'])
        assert len(positions) == 2
        assert positions['STOCK_A']['amount'] == 1000
        assert positions['STOCK_B'] is None
    
    def test_get_position_exists(self, mock_engine):
        """测试获取存在的单个持仓"""
        order(mock_engine, 'STOCK_A', 1000)
        
        position = get_position(mock_engine, 'STOCK_A')
        assert position is not None
        assert position['amount'] == 1000
    
    def test_get_position_not_exists(self, mock_engine):
        """测试获取不存在的单个持仓"""
        position = get_position(mock_engine, 'STOCK_A')
        assert position is None
    
    def test_get_open_orders(self, mock_engine):
        """测试获取未完成订单"""
        # 创建挂单
        order(mock_engine, 'STOCK_A', 1000, limit_price=90.0)
        
        mock_engine.context.blotter.get_open_orders = Mock(return_value={
            'order_1': Mock(to_dict=Mock(return_value={'order_id': 'order_1', 'status': 'open'}))
        })
        
        open_orders = get_open_orders(mock_engine)
        assert len(open_orders) == 1
        assert 'order_1' in open_orders
    
    def test_get_order_exists(self, mock_engine):
        """测试获取存在的订单"""
        mock_order = Mock()
        mock_order.to_dict.return_value = {'order_id': 'test_order', 'status': 'filled'}
        
        mock_engine.context.blotter.get_order = Mock(return_value=mock_order)
        
        order_info = get_order(mock_engine, 'test_order')
        assert order_info is not None
        assert order_info['order_id'] == 'test_order'
    
    def test_get_order_not_exists(self, mock_engine):
        """测试获取不存在的订单"""
        mock_engine.context.blotter.get_order = Mock(return_value=None)
        
        order_info = get_order(mock_engine, 'nonexistent_order')
        assert order_info is None
    
    def test_get_orders(self, mock_engine):
        """测试获取当日所有订单"""
        mock_engine.context.blotter.get_daily_orders = Mock(return_value={
            'order_1': Mock(to_dict=Mock(return_value={'order_id': 'order_1'})),
            'order_2': Mock(to_dict=Mock(return_value={'order_id': 'order_2'}))
        })
        
        orders = get_orders(mock_engine)
        assert len(orders) == 2
    
    def test_get_trades(self, mock_engine):
        """测试获取当日成交"""
        mock_engine.context.blotter.get_trades = Mock(return_value=[
            Mock(to_dict=Mock(return_value={'trade_id': 'trade_1'})),
            Mock(to_dict=Mock(return_value={'trade_id': 'trade_2'}))
        ])
        
        trades = get_trades(mock_engine)
        assert len(trades) == 2
    
    def test_order_with_exception_in_execution(self, mock_engine):
        """测试订单执行过程中发生异常"""
        # 模拟blotter.add_order抛出异常
        mock_engine.context.blotter.add_order.side_effect = Exception("Blotter error")
        
        with pytest.raises(TradingError, match="下单失败"):
            order(mock_engine, 'STOCK_A', 1000)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])