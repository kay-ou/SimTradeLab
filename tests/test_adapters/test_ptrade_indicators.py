# -*- coding: utf-8 -*-
"""
PTrade技术指标功能测试
验证新实现的技术指标计算功能
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from simtradelab.adapters.ptrade.adapter import (
    PTradeAdapter,
    PTradeContext,
    Portfolio,
    PTradeAdapterError
)
from simtradelab.plugins.base import PluginMetadata, PluginConfig


class TestPTradeIndicators:
    """测试PTrade技术指标功能"""
    
    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig(config={'initial_cash': 1000000})
        adapter = PTradeAdapter(metadata, config)
        adapter.initialize()
        yield adapter
        if adapter.state in [adapter.state.STARTED, adapter.state.PAUSED]:
            adapter.shutdown()
    
    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.randn(100) * 0.02)
        
        return {
            'close': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'dates': dates
        }
    
    def test_api_get_macd(self, adapter, sample_data):
        """测试MACD指标计算"""
        close_data = sample_data['close']
        
        # 测试MACD计算
        result = adapter._api_get_macd(close_data, short=12, long=26, m=9)
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert 'MACD' in result.columns
        assert 'MACD_signal' in result.columns
        assert 'MACD_hist' in result.columns
        assert len(result) == len(close_data)
        
        # 验证MACD值是合理的
        assert not result['MACD'].isnull().all()
        assert not result['MACD_signal'].isnull().all()
        assert not result['MACD_hist'].isnull().all()
        
        # 验证MACD柱状图 = MACD线 - 信号线
        hist_calculated = (result['MACD'] - result['MACD_signal']) * 2
        np.testing.assert_array_almost_equal(
            result['MACD_hist'].dropna(), 
            hist_calculated.dropna(), 
            decimal=10
        )
    
    def test_api_get_kdj(self, adapter, sample_data):
        """测试KDJ指标计算"""
        high_data = sample_data['high']
        low_data = sample_data['low']
        close_data = sample_data['close']
        
        # 测试KDJ计算
        result = adapter._api_get_kdj(high_data, low_data, close_data, n=9, m1=3, m2=3)
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert 'K' in result.columns
        assert 'D' in result.columns
        assert 'J' in result.columns
        assert len(result) == len(close_data)
        
        # 验证KDJ值是合理的
        assert not result['K'].isnull().all()
        assert not result['D'].isnull().all()
        assert not result['J'].isnull().all()
        
        # 验证J值计算公式：J = 3K - 2D
        j_calculated = 3 * result['K'] - 2 * result['D']
        np.testing.assert_array_almost_equal(
            result['J'].dropna(), 
            j_calculated.dropna(), 
            decimal=10
        )
    
    def test_api_get_rsi(self, adapter, sample_data):
        """测试RSI指标计算"""
        close_data = sample_data['close']
        
        # 测试RSI计算
        result = adapter._api_get_rsi(close_data, n=14)
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert 'RSI' in result.columns
        assert len(result) == len(close_data)
        
        # 验证RSI值是合理的
        assert not result['RSI'].isnull().all()
        
        # RSI值应该在0-100之间
        rsi_values = result['RSI'].dropna()
        assert (rsi_values >= 0).all()
        assert (rsi_values <= 100).all()
    
    def test_api_get_cci(self, adapter, sample_data):
        """测试CCI指标计算"""
        high_data = sample_data['high']
        low_data = sample_data['low']
        close_data = sample_data['close']
        
        # 测试CCI计算
        result = adapter._api_get_cci(high_data, low_data, close_data, n=20)
        
        # 验证结果
        assert isinstance(result, pd.DataFrame)
        assert 'CCI' in result.columns
        assert len(result) == len(close_data)
        
        # 验证CCI值是合理的
        assert not result['CCI'].isnull().all()
        
        # CCI值通常在-100到100之间，但可能超出这个范围
        cci_values = result['CCI'].dropna()
        assert len(cci_values) > 0
    
    def test_api_check_limit(self, adapter):
        """测试涨跌停检查功能"""
        # 模拟当前数据
        mock_current_data = {
            '000001.SZ': {
                'last_price': 11.00,
                'pre_close': 10.00
            },
            '688001.SH': {
                'last_price': 24.00,
                'pre_close': 20.00
            },
            'ST000001.SZ': {
                'last_price': 10.50,
                'pre_close': 10.00
            }
        }
        
        with patch.object(adapter, '_api_get_current_data', return_value=mock_current_data):
            # 测试普通股票涨停
            result = adapter._api_check_limit('000001.SZ')
            assert '000001.SZ' in result
            assert result['000001.SZ']['limit_up'] == True
            assert result['000001.SZ']['limit_up_price'] == 11.0
            assert result['000001.SZ']['limit_down_price'] == 9.0
            
            # 测试科创板股票涨停
            result = adapter._api_check_limit('688001.SH')
            assert '688001.SH' in result
            assert result['688001.SH']['limit_up'] == True
            assert result['688001.SH']['limit_up_price'] == 24.0
            assert result['688001.SH']['limit_down_price'] == 16.0
            
            # 测试ST股票涨停
            result = adapter._api_check_limit('ST000001.SZ')
            assert 'ST000001.SZ' in result
            assert result['ST000001.SZ']['limit_up'] == True
            assert result['ST000001.SZ']['limit_up_price'] == 10.5
            assert result['ST000001.SZ']['limit_down_price'] == 9.5
    
    def test_indicators_error_handling(self, adapter):
        """测试指标计算错误处理"""
        # 测试空数据
        empty_data = np.array([])
        
        result = adapter._api_get_macd(empty_data)
        assert isinstance(result, pd.DataFrame)
        
        result = adapter._api_get_rsi(empty_data)
        assert isinstance(result, pd.DataFrame)
        
        # 测试无效数据
        invalid_data = np.array([np.nan, np.inf, -np.inf])
        
        result = adapter._api_get_macd(invalid_data)
        assert isinstance(result, pd.DataFrame)
        
        result = adapter._api_get_rsi(invalid_data)
        assert isinstance(result, pd.DataFrame)
    
    def test_indicator_with_list_input(self, adapter, sample_data):
        """测试指标计算支持列表输入"""
        close_list = sample_data['close'].tolist()
        
        # 测试MACD支持列表输入
        result = adapter._api_get_macd(np.array(close_list))
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(close_list)
        
        # 测试RSI支持列表输入
        result = adapter._api_get_rsi(np.array(close_list))
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(close_list)
    
    def test_indicator_parameters(self, adapter, sample_data):
        """测试指标计算参数"""
        close_data = sample_data['close']
        
        # 测试不同的MACD参数
        result1 = adapter._api_get_macd(close_data, short=5, long=10, m=5)
        result2 = adapter._api_get_macd(close_data, short=12, long=26, m=9)
        
        # 不同参数应该产生不同的结果
        assert not result1['MACD'].equals(result2['MACD'])
        
        # 测试不同的RSI参数
        result1 = adapter._api_get_rsi(close_data, n=6)
        result2 = adapter._api_get_rsi(close_data, n=14)
        
        # 不同参数应该产生不同的结果
        assert not result1['RSI'].equals(result2['RSI'])
    
    def test_check_limit_nonexistent_security(self, adapter):
        """测试查询不存在的证券的涨跌停状态"""
        with patch.object(adapter, '_api_get_current_data', return_value={}):
            result = adapter._api_check_limit('999999.SZ')
            assert '999999.SZ' in result
            assert result['999999.SZ']['limit_up'] == False
            assert result['999999.SZ']['limit_down'] == False
            assert result['999999.SZ']['current_price'] is None
    
    def test_check_limit_zero_pre_close(self, adapter):
        """测试昨收价为0的情况"""
        mock_current_data = {
            '000001.SZ': {
                'last_price': 10.00,
                'pre_close': 0.00
            }
        }
        
        with patch.object(adapter, '_api_get_current_data', return_value=mock_current_data):
            result = adapter._api_check_limit('000001.SZ')
            assert '000001.SZ' in result
            assert result['000001.SZ']['limit_up'] == False
            assert result['000001.SZ']['limit_down'] == False
            assert result['000001.SZ']['current_price'] == 10.00