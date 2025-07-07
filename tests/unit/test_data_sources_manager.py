#!/usr/bin/env python3
"""
数据源管理器测试 - 测试data_sources/manager.py模块
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from simtradelab.data_sources.manager import DataSourceManager
from simtradelab.data_sources.base import BaseDataSource


class TestDataSourceManager:
    """数据源管理器测试"""
    
    @pytest.fixture
    def mock_primary_source(self):
        """创建模拟主数据源"""
        mock_source = Mock(spec=BaseDataSource)
        type(mock_source).__name__ = 'MockPrimarySource'
        return mock_source
    
    @pytest.fixture
    def mock_fallback_source(self):
        """创建模拟备用数据源"""
        mock_source = Mock(spec=BaseDataSource)
        type(mock_source).__name__ = 'MockFallbackSource'
        return mock_source
    
    @pytest.fixture
    def manager_with_fallback(self, mock_primary_source, mock_fallback_source):
        """创建带备用数据源的管理器"""
        return DataSourceManager(mock_primary_source, [mock_fallback_source])
    
    @pytest.fixture
    def manager_single_source(self, mock_primary_source):
        """创建单数据源的管理器"""
        return DataSourceManager(mock_primary_source)
    
    def test_init_single_source(self, mock_primary_source):
        """测试单数据源初始化"""
        manager = DataSourceManager(mock_primary_source)
        
        assert manager.primary_source == mock_primary_source
        assert manager.fallback_sources == []
        assert manager.all_sources == [mock_primary_source]
    
    def test_init_with_fallback_sources(self, mock_primary_source, mock_fallback_source):
        """测试带备用数据源的初始化"""
        fallback_sources = [mock_fallback_source]
        manager = DataSourceManager(mock_primary_source, fallback_sources)
        
        assert manager.primary_source == mock_primary_source
        assert manager.fallback_sources == fallback_sources
        assert manager.all_sources == [mock_primary_source, mock_fallback_source]
    
    def test_get_history_success_primary(self, manager_single_source, mock_primary_source):
        """测试主数据源成功获取历史数据"""
        # 设置主数据源返回数据
        expected_data = {
            '000001.SZ': pd.DataFrame({
                'date': ['2023-01-01', '2023-01-02'],
                'close': [10.0, 10.5]
            })
        }
        mock_primary_source.get_history.return_value = expected_data
        
        result = manager_single_source.get_history(['000001.SZ'], '2023-01-01', '2023-01-02')
        
        assert result == expected_data
        mock_primary_source.get_history.assert_called_once_with(
            ['000001.SZ'], '2023-01-01', '2023-01-02', '1d', None
        )
    
    def test_get_history_primary_fails_fallback_success(self, manager_with_fallback, 
                                                      mock_primary_source, mock_fallback_source):
        """测试主数据源失败，备用数据源成功"""
        # 主数据源抛出异常
        mock_primary_source.get_history.side_effect = Exception("Primary source failed")
        
        # 备用数据源返回数据
        expected_data = {
            '000001.SZ': pd.DataFrame({
                'date': ['2023-01-01', '2023-01-02'],
                'close': [10.0, 10.5]
            })
        }
        mock_fallback_source.get_history.return_value = expected_data
        
        result = manager_with_fallback.get_history(['000001.SZ'], '2023-01-01', '2023-01-02')
        
        assert result == expected_data
        mock_primary_source.get_history.assert_called_once()
        mock_fallback_source.get_history.assert_called_once_with(
            ['000001.SZ'], '2023-01-01', '2023-01-02', '1d', None
        )
    
    def test_get_history_partial_success(self, manager_with_fallback, 
                                       mock_primary_source, mock_fallback_source):
        """测试部分成功的历史数据获取"""
        # 主数据源只返回部分数据
        primary_data = {
            '000001.SZ': pd.DataFrame({
                'date': ['2023-01-01', '2023-01-02'],
                'close': [10.0, 10.5]
            })
        }
        mock_primary_source.get_history.return_value = primary_data
        
        # 备用数据源返回缺失的数据
        fallback_data = {
            '000002.SZ': pd.DataFrame({
                'date': ['2023-01-01', '2023-01-02'],
                'close': [20.0, 20.5]
            })
        }
        mock_fallback_source.get_history.return_value = fallback_data
        
        result = manager_with_fallback.get_history(['000001.SZ', '000002.SZ'], '2023-01-01', '2023-01-02')
        
        expected_result = {**primary_data, **fallback_data}
        assert result == expected_result
    
    def test_get_history_string_security(self, manager_single_source, mock_primary_source):
        """测试传入单个字符串股票代码"""
        expected_data = {
            '000001.SZ': pd.DataFrame({
                'date': ['2023-01-01'],
                'close': [10.0]
            })
        }
        mock_primary_source.get_history.return_value = expected_data
        
        result = manager_single_source.get_history('000001.SZ', '2023-01-01', '2023-01-02')
        
        assert result == expected_data
        mock_primary_source.get_history.assert_called_once_with(
            ['000001.SZ'], '2023-01-01', '2023-01-02', '1d', None
        )
    
    def test_get_current_data_success(self, manager_single_source, mock_primary_source):
        """测试成功获取实时数据"""
        expected_data = {
            '000001.SZ': {'price': 10.0, 'volume': 1000}
        }
        mock_primary_source.get_current_data.return_value = expected_data
        
        result = manager_single_source.get_current_data(['000001.SZ'])
        
        assert result == expected_data
        mock_primary_source.get_current_data.assert_called_once_with(['000001.SZ'])
    
    def test_get_current_data_fallback(self, manager_with_fallback, 
                                     mock_primary_source, mock_fallback_source):
        """测试实时数据获取备用数据源"""
        # 主数据源失败
        mock_primary_source.get_current_data.side_effect = Exception("Primary failed")
        
        # 备用数据源成功
        expected_data = {
            '000001.SZ': {'price': 10.0, 'volume': 1000}
        }
        mock_fallback_source.get_current_data.return_value = expected_data
        
        result = manager_with_fallback.get_current_data(['000001.SZ'])
        
        assert result == expected_data
        mock_fallback_source.get_current_data.assert_called_once_with(['000001.SZ'])
    
    def test_get_current_data_string_security(self, manager_single_source, mock_primary_source):
        """测试传入单个字符串股票代码获取实时数据"""
        expected_data = {
            '000001.SZ': {'price': 10.0, 'volume': 1000}
        }
        mock_primary_source.get_current_data.return_value = expected_data
        
        result = manager_single_source.get_current_data('000001.SZ')
        
        assert result == expected_data
        mock_primary_source.get_current_data.assert_called_once_with(['000001.SZ'])
    
    def test_get_fundamentals_success(self, manager_single_source, mock_primary_source):
        """测试成功获取基本面数据"""
        expected_data = {
            '000001.SZ': {'pe_ratio': 15.0, 'market_cap': 1000000}
        }
        mock_primary_source.get_fundamentals.return_value = expected_data
        
        result = manager_single_source.get_fundamentals(['000001.SZ'])
        
        assert result == expected_data
        mock_primary_source.get_fundamentals.assert_called_once_with(['000001.SZ'], None, None)
    
    def test_get_fundamentals_filter_empty_data(self, manager_single_source, mock_primary_source):
        """测试过滤空的基本面数据"""
        # 主数据源返回包含空数据的结果
        primary_data = {
            '000001.SZ': {'pe_ratio': 15.0, 'market_cap': 1000000},
            '000002.SZ': {},  # 空数据
            '000003.SZ': None  # None数据
        }
        mock_primary_source.get_fundamentals.return_value = primary_data
        
        result = manager_single_source.get_fundamentals(['000001.SZ', '000002.SZ', '000003.SZ'])
        
        # 只应该返回非空数据
        expected_result = {
            '000001.SZ': {'pe_ratio': 15.0, 'market_cap': 1000000}
        }
        assert result == expected_result
    
    def test_get_fundamentals_with_params(self, manager_single_source, mock_primary_source):
        """测试带参数的基本面数据获取"""
        expected_data = {
            '000001.SZ': {'pe_ratio': 15.0}
        }
        mock_primary_source.get_fundamentals.return_value = expected_data
        
        result = manager_single_source.get_fundamentals(
            '000001.SZ', 
            fields=['pe_ratio'], 
            date='2023-01-01'
        )
        
        assert result == expected_data
        mock_primary_source.get_fundamentals.assert_called_once_with(
            ['000001.SZ'], ['pe_ratio'], '2023-01-01'
        )
    
    def test_get_trading_calendar_success(self, manager_single_source, mock_primary_source):
        """测试成功获取交易日历"""
        expected_calendar = ['2023-01-03', '2023-01-04', '2023-01-05']
        mock_primary_source.get_trading_calendar.return_value = expected_calendar
        
        result = manager_single_source.get_trading_calendar('2023-01-01', '2023-01-07')
        
        assert result == expected_calendar
        mock_primary_source.get_trading_calendar.assert_called_once_with('2023-01-01', '2023-01-07')
    
    def test_get_trading_calendar_fallback_to_default(self, manager_single_source, mock_primary_source):
        """测试交易日历回退到默认实现"""
        # 主数据源失败
        mock_primary_source.get_trading_calendar.side_effect = Exception("Calendar failed")
        
        with patch('pandas.date_range') as mock_date_range:
            mock_dates = pd.DatetimeIndex(['2023-01-02', '2023-01-03'])
            mock_date_range.return_value = mock_dates
            
            result = manager_single_source.get_trading_calendar('2023-01-01', '2023-01-07')
            
            assert result == ['2023-01-02', '2023-01-03']
            mock_date_range.assert_called_once_with('2023-01-01', '2023-01-07', freq='B')
    
    def test_get_stock_list_success(self, manager_single_source, mock_primary_source):
        """测试成功获取股票列表"""
        expected_list = ['000001.SZ', '000002.SZ', '600000.SH']
        mock_primary_source.get_stock_list.return_value = expected_list
        
        result = manager_single_source.get_stock_list()
        
        assert result == expected_list
        mock_primary_source.get_stock_list.assert_called_once()
    
    def test_get_stock_list_fallback(self, manager_with_fallback, 
                                   mock_primary_source, mock_fallback_source):
        """测试股票列表获取回退"""
        # 主数据源失败
        mock_primary_source.get_stock_list.side_effect = Exception("Primary failed")
        
        # 备用数据源成功
        expected_list = ['000001.SZ', '000002.SZ']
        mock_fallback_source.get_stock_list.return_value = expected_list
        
        result = manager_with_fallback.get_stock_list()
        
        assert result == expected_list
        mock_fallback_source.get_stock_list.assert_called_once()
    
    def test_get_stock_list_all_fail(self, manager_single_source, mock_primary_source):
        """测试所有数据源获取股票列表都失败"""
        mock_primary_source.get_stock_list.side_effect = Exception("All failed")
        
        result = manager_single_source.get_stock_list()
        
        assert result == []
    
    def test_add_fallback_source(self, manager_single_source):
        """测试添加备用数据源"""
        new_source = Mock(spec=BaseDataSource)
        type(new_source).__name__ = 'NewSource'
        
        manager_single_source.add_fallback_source(new_source)
        
        assert new_source in manager_single_source.fallback_sources
        assert new_source in manager_single_source.all_sources
        assert len(manager_single_source.fallback_sources) == 1
    
    def test_remove_fallback_source(self, manager_with_fallback, mock_fallback_source):
        """测试移除备用数据源"""
        # 确认初始状态
        assert mock_fallback_source in manager_with_fallback.fallback_sources
        assert mock_fallback_source in manager_with_fallback.all_sources
        
        # 移除数据源
        manager_with_fallback.remove_fallback_source(mock_fallback_source)
        
        # 确认移除成功
        assert mock_fallback_source not in manager_with_fallback.fallback_sources
        assert mock_fallback_source not in manager_with_fallback.all_sources
    
    def test_remove_nonexistent_fallback_source(self, manager_single_source):
        """测试移除不存在的备用数据源"""
        nonexistent_source = Mock(spec=BaseDataSource)
        
        # 不应该抛出异常
        manager_single_source.remove_fallback_source(nonexistent_source)
        
        assert len(manager_single_source.fallback_sources) == 0
    
    def test_clear_cache(self, manager_with_fallback, mock_primary_source, mock_fallback_source):
        """测试清空缓存"""
        manager_with_fallback.clear_cache()
        
        mock_primary_source.clear_cache.assert_called_once()
        mock_fallback_source.clear_cache.assert_called_once()
    
    def test_get_source_status_all_available(self, manager_with_fallback, 
                                           mock_primary_source, mock_fallback_source):
        """测试获取数据源状态 - 所有数据源可用"""
        # 设置所有数据源返回非空股票列表
        mock_primary_source.get_stock_list.return_value = ['000001.SZ']
        mock_fallback_source.get_stock_list.return_value = ['000002.SZ']
        
        status = manager_with_fallback.get_source_status()
        
        assert 'primary' in status
        assert 'fallback_1' in status
        
        assert status['primary']['type'] == 'MockPrimarySource'
        assert status['primary']['available'] is True
        assert status['primary']['error'] is None
        
        assert status['fallback_1']['type'] == 'MockFallbackSource'
        assert status['fallback_1']['available'] is True
        assert status['fallback_1']['error'] is None
    
    def test_get_source_status_with_failures(self, manager_with_fallback, 
                                           mock_primary_source, mock_fallback_source):
        """测试获取数据源状态 - 部分数据源失败"""
        # 主数据源失败
        mock_primary_source.get_stock_list.side_effect = Exception("Connection failed")
        
        # 备用数据源成功但返回空列表
        mock_fallback_source.get_stock_list.return_value = []
        
        status = manager_with_fallback.get_source_status()
        
        assert status['primary']['available'] is False
        assert "Connection failed" in status['primary']['error']
        
        assert status['fallback_1']['available'] is False
        assert status['fallback_1']['error'] is None


class TestDataSourceManagerIntegration:
    """数据源管理器集成测试"""
    
    def test_multi_source_data_aggregation(self):
        """测试多数据源数据聚合"""
        # 创建模拟数据源
        source1 = Mock(spec=BaseDataSource)
        source2 = Mock(spec=BaseDataSource)
        type(source1).__name__ = 'Source1'
        type(source2).__name__ = 'Source2'
        
        # 设置数据源1返回部分数据
        source1_data = {
            '000001.SZ': pd.DataFrame({'close': [10.0, 10.5]}),
            '000002.SZ': pd.DataFrame({'close': [20.0, 20.5]})
        }
        source1.get_history.return_value = source1_data
        
        # 设置数据源2返回其他数据
        source2_data = {
            '000003.SZ': pd.DataFrame({'close': [30.0, 30.5]})
        }
        source2.get_history.return_value = source2_data
        
        # 创建管理器
        manager = DataSourceManager(source1, [source2])
        
        # 获取数据
        result = manager.get_history(['000001.SZ', '000002.SZ', '000003.SZ'], 
                                   '2023-01-01', '2023-01-02')
        
        # 验证结果包含所有数据
        assert '000001.SZ' in result
        assert '000002.SZ' in result
        assert '000003.SZ' in result
        assert len(result) == 3
    
    def test_complete_failure_handling(self):
        """测试完全失败的处理"""
        # 创建都会失败的数据源
        source1 = Mock(spec=BaseDataSource)
        source2 = Mock(spec=BaseDataSource)
        type(source1).__name__ = 'FailSource1'
        type(source2).__name__ = 'FailSource2'
        
        source1.get_history.side_effect = Exception("Source1 failed")
        source2.get_history.side_effect = Exception("Source2 failed")
        
        manager = DataSourceManager(source1, [source2])
        
        # 应该返回空结果而不是抛出异常
        result = manager.get_history(['000001.SZ'], '2023-01-01', '2023-01-02')
        
        assert result == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])