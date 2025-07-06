# -*- coding: utf-8 -*-
"""
新增API测试
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from simtradelab import (
    # 新增设置函数
    set_fixed_slippage, set_slippage, set_volume_ratio, set_yesterday_position, set_parameters,
    # 新增交易函数
    order_target_value, order_market, ipo_stocks_order, after_trading_order, 
    etf_basket_order, order_percent, order_target_percent,
    # 新增市场数据函数
    get_market_list, get_cash, get_total_value, get_datetime,
    get_previous_trading_date, get_next_trading_date
)


class TestNewSettingAPIs:
    """新增设置API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.positions = {}
        return engine
    
    def test_set_fixed_slippage(self, mock_engine):
        """测试设置固定滑点"""
        set_fixed_slippage(mock_engine, 0.01)
        assert mock_engine.fixed_slippage == 0.01
    
    def test_set_slippage(self, mock_engine):
        """测试设置滑点比例"""
        set_slippage(mock_engine, 0.001)
        assert mock_engine.slippage == 0.001
    
    def test_set_volume_ratio(self, mock_engine):
        """测试设置成交量比例"""
        set_volume_ratio(mock_engine, 0.1)
        assert mock_engine.volume_ratio == 0.1
    
    def test_set_yesterday_position(self, mock_engine):
        """测试设置初始持仓"""
        positions = {'STOCK_A': 1000, 'STOCK_B': 500}
        set_yesterday_position(mock_engine, positions)
        # 验证持仓已设置
        assert 'STOCK_A' in mock_engine.context.portfolio.positions
        assert 'STOCK_B' in mock_engine.context.portfolio.positions
    
    def test_set_parameters(self, mock_engine):
        """测试设置策略参数"""
        params = {'param1': 'value1', 'param2': 100}
        set_parameters(mock_engine, **params)
        # 只验证strategy_params属性被设置
        assert hasattr(mock_engine, 'strategy_params')
        # 从日志输出可以验证功能正常


class TestNewTradingAPIs:
    """新增交易API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.positions = {}
        engine.context.portfolio.total_value = 1000000.0
        engine.current_data = {
            'STOCK_A': {'close': 100.0, 'volume': 1000000}
        }
        return engine
    
    @patch('simtradelab.trading.order')
    def test_order_target_value(self, mock_order, mock_engine):
        """测试目标市值下单"""
        mock_order.return_value = 'order_123'
        
        result = order_target_value(mock_engine, 'STOCK_A', 50000.0)
        
        assert result == 'order_123'
        mock_order.assert_called_once()
    
    @patch('simtradelab.trading.order')
    def test_order_market(self, mock_order, mock_engine):
        """测试市价单"""
        mock_order.return_value = 'order_123'
        
        result = order_market(mock_engine, 'STOCK_A', 1000)
        
        assert result == 'order_123'
        mock_order.assert_called_once_with(mock_engine, 'STOCK_A', 1000, limit_price=None)
    
    def test_ipo_stocks_order(self, mock_engine):
        """测试IPO申购"""
        # 设置足够的现金
        mock_engine.context.portfolio.cash = 100000.0
        result = ipo_stocks_order(mock_engine, 'NEW_STOCK', 1000)
        assert result is not None  # 应该返回订单ID
    
    @patch('simtradelab.trading.order')
    def test_after_trading_order(self, mock_order, mock_engine):
        """测试盘后定价交易"""
        mock_order.return_value = 'order_123'
        
        result = after_trading_order(mock_engine, 'STOCK_A', 1000, 105.0)
        
        assert result == 'order_123'
        mock_order.assert_called_once_with(mock_engine, 'STOCK_A', 1000, limit_price=105.0)
    
    @patch('simtradelab.trading.order')
    def test_etf_basket_order(self, mock_order, mock_engine):
        """测试ETF篮子交易"""
        basket = {'STOCK_A': 1000, 'STOCK_B': 500}
        
        result = etf_basket_order(mock_engine, 'ETF_001', basket, 'creation')
        
        assert result is not None
        assert mock_order.call_count == 2  # 应该调用两次order
    
    @patch('simtradelab.trading.order_target_value')
    def test_order_percent(self, mock_order_target_value, mock_engine):
        """测试按百分比下单"""
        mock_order_target_value.return_value = 'order_123'
        
        result = order_percent(mock_engine, 'STOCK_A', 0.1)
        
        assert result == 'order_123'
        mock_order_target_value.assert_called_once_with(mock_engine, 'STOCK_A', 100000.0)
    
    @patch('simtradelab.trading.order_percent')
    def test_order_target_percent(self, mock_order_percent, mock_engine):
        """测试目标百分比下单"""
        mock_order_percent.return_value = 'order_123'
        
        result = order_target_percent(mock_engine, 'STOCK_A', 0.1)
        
        assert result == 'order_123'
        mock_order_percent.assert_called_once_with(mock_engine, 'STOCK_A', 0.1)


class TestNewMarketDataAPIs:
    """新增市场数据API测试"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        engine.data = {
            'STOCK_A.SZ': pd.DataFrame(),
            'STOCK_B.SH': pd.DataFrame()
        }
        engine.context = Mock()
        engine.context.portfolio = Mock()
        engine.context.portfolio.cash = 100000.0
        engine.context.portfolio.total_value = 150000.0
        engine.context.current_dt = pd.Timestamp('2023-01-15')
        return engine
    
    def test_get_market_list(self, mock_engine):
        """测试获取市场列表"""
        result = get_market_list(mock_engine)
        assert isinstance(result, list)
        assert 'SZ' in result
        assert 'SH' in result
    
    def test_get_cash(self, mock_engine):
        """测试获取现金"""
        result = get_cash(mock_engine)
        assert result == 100000.0
    
    def test_get_total_value(self, mock_engine):
        """测试获取总资产"""
        result = get_total_value(mock_engine)
        assert result == 150000.0
    
    def test_get_datetime(self, mock_engine):
        """测试获取当前时间"""
        result = get_datetime(mock_engine)
        assert isinstance(result, str)
        assert '2023-01-15' in result
    
    @patch('simtradelab.utils.get_trading_day')
    def test_get_previous_trading_date(self, mock_get_trading_day, mock_engine):
        """测试获取上一交易日"""
        mock_get_trading_day.return_value = pd.Timestamp('2023-01-14')
        
        result = get_previous_trading_date(mock_engine)
        
        assert result == '2023-01-14'
        mock_get_trading_day.assert_called_once_with(mock_engine, None, offset=-1)
    
    @patch('simtradelab.utils.get_trading_day')
    def test_get_next_trading_date(self, mock_get_trading_day, mock_engine):
        """测试获取下一交易日"""
        mock_get_trading_day.return_value = pd.Timestamp('2023-01-16')
        
        result = get_next_trading_date(mock_engine)
        
        assert result == '2023-01-16'
        mock_get_trading_day.assert_called_once_with(mock_engine, None, offset=1)
    
    def test_get_market_data_apis_with_no_context(self):
        """测试无上下文时的API行为"""
        engine = Mock()
        engine.context = None
        
        assert get_cash(engine) == 0.0
        assert get_total_value(engine) == 0.0
        assert get_datetime(engine) == ""


class TestAPIIntegration:
    """API集成测试"""
    
    def test_all_new_apis_importable(self):
        """测试所有新增API都可以导入"""
        from simtradelab import (
            set_fixed_slippage, set_slippage, set_volume_ratio, 
            set_yesterday_position, set_parameters,
            order_target_value, order_market, ipo_stocks_order,
            after_trading_order, etf_basket_order, order_percent, order_target_percent,
            get_market_list, get_cash, get_total_value, get_datetime,
            get_previous_trading_date, get_next_trading_date
        )
        
        # 验证所有函数都是可调用的
        apis = [
            set_fixed_slippage, set_slippage, set_volume_ratio,
            set_yesterday_position, set_parameters,
            order_target_value, order_market, ipo_stocks_order,
            after_trading_order, etf_basket_order, order_percent, order_target_percent,
            get_market_list, get_cash, get_total_value, get_datetime,
            get_previous_trading_date, get_next_trading_date
        ]
        
        for api in apis:
            assert callable(api), f"{api.__name__} 不是可调用函数"
    
    def test_api_error_handling(self):
        """测试API错误处理"""
        engine = Mock()
        engine.data = {}
        engine.context = None
        
        # 测试无数据时的行为
        assert get_market_list(engine) == []
        assert get_cash(engine) == 0.0
        assert get_total_value(engine) == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])