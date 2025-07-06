# -*- coding: utf-8 -*-
"""
市场数据模块测试
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from simtradelab.market_data import (
    get_history, get_price, get_current_data, get_market_snapshot,
    get_technical_indicators, get_MACD, get_KDJ, get_RSI, get_CCI
)


class TestMarketDataModule:
    """市场数据模块测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟引擎"""
        engine = Mock()
        
        # 创建足够多的测试数据（30天数据，确保技术指标计算正常）
        dates = pd.date_range('2023-01-01', '2023-01-30', freq='D')
        test_data = {
            'STOCK_A': pd.DataFrame({
                'open': np.random.rand(len(dates)) * 10 + 100,
                'high': np.random.rand(len(dates)) * 10 + 105,
                'low': np.random.rand(len(dates)) * 10 + 95,
                'close': np.random.rand(len(dates)) * 10 + 100,
                'volume': np.random.randint(1000000, 2000000, len(dates)),
            }, index=dates),
            'STOCK_B': pd.DataFrame({
                'open': np.random.rand(len(dates)) * 10 + 50,
                'high': np.random.rand(len(dates)) * 10 + 55,
                'low': np.random.rand(len(dates)) * 10 + 45,
                'close': np.random.rand(len(dates)) * 10 + 50,
                'volume': np.random.randint(500000, 1000000, len(dates)),
            }, index=dates)
        }
        
        engine.data = test_data
        engine.context = Mock()
        engine.context.current_dt = dates[20]  # 设置为第20天，确保有足够历史数据
        
        return engine
    
    def test_get_history_basic(self, mock_engine):
        """测试基本历史数据获取"""
        result = get_history(mock_engine, count=5, security_list=['STOCK_A'])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 1
        assert ('close', 'STOCK_A') in result.columns
    
    def test_get_history_multiple_fields(self, mock_engine):
        """测试获取多个字段的历史数据"""
        result = get_history(
            mock_engine, 
            count=5, 
            field=['open', 'close'], 
            security_list=['STOCK_A']
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 2
        assert ('open', 'STOCK_A') in result.columns
        assert ('close', 'STOCK_A') in result.columns
    
    def test_get_history_dict_format(self, mock_engine):
        """测试字典格式返回"""
        result = get_history(
            mock_engine, 
            count=5, 
            field=['close'], 
            security_list=['STOCK_A'], 
            is_dict=True
        )
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'close' in result['STOCK_A']
        assert isinstance(result['STOCK_A']['close'], np.ndarray)
    
    def test_get_history_with_dates(self, mock_engine):
        """测试指定日期范围的历史数据"""
        result = get_history(
            mock_engine,
            count=10,
            start_date='2023-01-03',
            end_date='2023-01-07',
            security_list=['STOCK_A']
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) <= 5  # 最多5个交易日
    
    def test_get_history_extended_fields(self, mock_engine):
        """测试扩展字段计算"""
        result = get_history(
            mock_engine,
            count=5,
            field=['close', 'pct_change', 'amplitude'],
            security_list=['STOCK_A'],
            is_dict=True
        )
        
        assert 'STOCK_A' in result
        assert 'pct_change' in result['STOCK_A']
        assert 'amplitude' in result['STOCK_A']
    
    def test_get_history_nonexistent_security(self, mock_engine):
        """测试不存在的股票"""
        result = get_history(
            mock_engine,
            count=5,
            security_list=['NONEXISTENT'],
            is_dict=True
        )
        
        assert 'NONEXISTENT' in result
        assert len(result['NONEXISTENT']['close']) == 0
    
    def test_get_price_single_security(self, mock_engine):
        """测试获取单只股票价格"""
        result = get_price(mock_engine, 'STOCK_A', count=3)
        
        assert isinstance(result, pd.DataFrame)
        assert 'STOCK_A' in result.columns
        assert len(result) == 3
    
    def test_get_price_multiple_securities(self, mock_engine):
        """测试获取多只股票价格"""
        result = get_price(mock_engine, ['STOCK_A', 'STOCK_B'], fields='close', count=3)
        
        assert isinstance(result, pd.DataFrame)
        assert 'STOCK_A' in result.columns
        assert 'STOCK_B' in result.columns
    
    def test_get_price_multiple_fields(self, mock_engine):
        """测试获取多个字段价格"""
        result = get_price(mock_engine, 'STOCK_A', fields=['open', 'close'], count=3)
        
        assert isinstance(result, pd.DataFrame)
        assert ('open', 'STOCK_A') in result.columns
        assert ('close', 'STOCK_A') in result.columns
    
    def test_get_price_calculated_fields(self, mock_engine):
        """测试计算字段"""
        result = get_price(
            mock_engine, 
            'STOCK_A', 
            fields=['close', 'pct_change', 'vwap'], 
            count=3
        )
        
        assert isinstance(result, pd.DataFrame)
        assert ('pct_change', 'STOCK_A') in result.columns
        assert ('vwap', 'STOCK_A') in result.columns
    
    def test_get_current_data_all_securities(self, mock_engine):
        """测试获取所有股票当前数据"""
        result = get_current_data(mock_engine)
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' in result
        assert 'close' in result['STOCK_A']
        assert 'bid1' in result['STOCK_A']
        assert 'ask1' in result['STOCK_A']
    
    def test_get_current_data_specific_security(self, mock_engine):
        """测试获取指定股票当前数据"""
        result = get_current_data(mock_engine, 'STOCK_A')
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' not in result
    
    def test_get_current_data_multiple_securities(self, mock_engine):
        """测试获取多只股票当前数据"""
        result = get_current_data(mock_engine, ['STOCK_A', 'STOCK_B'])
        
        assert isinstance(result, dict)
        assert 'STOCK_A' in result
        assert 'STOCK_B' in result
    
    def test_get_market_snapshot_default(self, mock_engine):
        """测试默认市场快照"""
        result = get_market_snapshot(mock_engine)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # STOCK_A 和 STOCK_B
        assert 'open' in result.columns
        assert 'close' in result.columns
    
    def test_get_market_snapshot_specific_fields(self, mock_engine):
        """测试指定字段市场快照"""
        result = get_market_snapshot(mock_engine, fields=['close', 'volume'])
        
        assert isinstance(result, pd.DataFrame)
        assert 'close' in result.columns
        assert 'volume' in result.columns
        assert 'open' not in result.columns
    
    def test_get_market_snapshot_specific_security(self, mock_engine):
        """测试指定股票市场快照"""
        result = get_market_snapshot(mock_engine, security='STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.index[0] == 'STOCK_A'
    
    def test_get_technical_indicators_ma(self, mock_engine):
        """测试移动平均线指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'MA', period=5)
        
        assert isinstance(result, pd.DataFrame)
        assert ('MA5', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_multiple(self, mock_engine):
        """测试多个技术指标"""
        result = get_technical_indicators(
            mock_engine, 
            'STOCK_A', 
            ['MA', 'EMA', 'RSI'], 
            period=5
        )
        
        assert isinstance(result, pd.DataFrame)
        assert ('MA5', 'STOCK_A') in result.columns
        assert ('EMA5', 'STOCK_A') in result.columns
        assert ('RSI5', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_macd(self, mock_engine):
        """测试MACD指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'MACD')
        
        assert isinstance(result, pd.DataFrame)
        assert ('MACD_DIF', 'STOCK_A') in result.columns
        assert ('MACD_DEA', 'STOCK_A') in result.columns
        assert ('MACD_HIST', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_boll(self, mock_engine):
        """测试布林带指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'BOLL')
        
        assert isinstance(result, pd.DataFrame)
        assert ('BOLL_UPPER', 'STOCK_A') in result.columns
        assert ('BOLL_MIDDLE', 'STOCK_A') in result.columns
        assert ('BOLL_LOWER', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_kdj(self, mock_engine):
        """测试KDJ指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'KDJ')
        
        assert isinstance(result, pd.DataFrame)
        assert ('KDJ_K', 'STOCK_A') in result.columns
        assert ('KDJ_D', 'STOCK_A') in result.columns
        assert ('KDJ_J', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_cci(self, mock_engine):
        """测试CCI指标"""
        result = get_technical_indicators(mock_engine, 'STOCK_A', 'CCI', period=14)
        
        assert isinstance(result, pd.DataFrame)
        assert ('CCI14', 'STOCK_A') in result.columns
    
    def test_get_technical_indicators_insufficient_data(self, mock_engine):
        """测试数据不足的情况"""
        # 创建只有很少数据的引擎
        short_engine = Mock()
        dates = pd.date_range('2023-01-01', '2023-01-02', freq='D')
        short_engine.data = {
            'STOCK_A': pd.DataFrame({
                'close': [100.0, 101.0],
            }, index=dates)
        }
        short_engine.context = Mock()
        short_engine.context.current_dt = dates[1]
        
        result = get_technical_indicators(short_engine, 'STOCK_A', 'MA', period=20)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
    
    def test_get_macd_function(self, mock_engine):
        """测试MACD独立函数"""
        result = get_MACD(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('MACD_DIF', 'STOCK_A') in result.columns
    
    def test_get_kdj_function(self, mock_engine):
        """测试KDJ独立函数"""
        result = get_KDJ(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('KDJ_K', 'STOCK_A') in result.columns
    
    def test_get_rsi_function(self, mock_engine):
        """测试RSI独立函数"""
        result = get_RSI(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('RSI14', 'STOCK_A') in result.columns
    
    def test_get_cci_function(self, mock_engine):
        """测试CCI独立函数"""
        result = get_CCI(mock_engine, 'STOCK_A')
        
        assert isinstance(result, pd.DataFrame)
        assert ('CCI20', 'STOCK_A') in result.columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])