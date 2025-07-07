#!/usr/bin/env python3
"""
CSV数据源测试 - 测试data_sources/csv_source.py模块
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from unittest.mock import patch, Mock

from simtradelab.data_sources.csv_source import CSVDataSource


class TestCSVDataSource:
    """CSV数据源测试"""
    
    @pytest.fixture
    def sample_csv_data(self):
        """创建示例CSV数据"""
        data = {
            'datetime': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-01', '2023-01-02', '2023-01-03'],
            'security': ['000001.SZ', '000001.SZ', '000001.SZ', '000002.SZ', '000002.SZ', '000002.SZ'],
            'open': [10.0, 10.5, 11.0, 20.0, 20.5, 21.0],
            'high': [10.8, 11.2, 11.5, 20.8, 21.2, 21.5],
            'low': [9.8, 10.2, 10.5, 19.8, 20.2, 20.5],
            'close': [10.5, 11.0, 11.2, 20.5, 21.0, 21.2],
            'volume': [1000000, 1100000, 1200000, 2000000, 2100000, 2200000]
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def csv_file_path(self, sample_csv_data):
        """创建临时CSV文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            yield f.name
        
        # 清理
        if os.path.exists(f.name):
            os.unlink(f.name)
    
    @pytest.fixture
    def csv_source(self, csv_file_path):
        """创建CSV数据源实例"""
        return CSVDataSource(csv_file_path)
    
    def test_init_success(self, csv_file_path):
        """测试成功初始化"""
        source = CSVDataSource(csv_file_path)
        
        assert source.data_path == csv_file_path
        assert isinstance(source._data, dict)
        assert '000001.SZ' in source._data
        assert '000002.SZ' in source._data
        assert len(source._data) == 2
    
    def test_init_file_not_found(self):
        """测试文件不存在的情况"""
        with patch('simtradelab.data_sources.csv_source.log') as mock_log:
            source = CSVDataSource('/nonexistent/file.csv')
            
            assert source._data == {}
            mock_log.warning.assert_called()
    
    def test_init_missing_datetime_column(self):
        """测试缺少日期时间列的情况"""
        # 创建没有日期时间列的CSV
        data = {
            'security': ['000001.SZ'],
            'open': [10.0],
            'close': [10.5]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            with patch('simtradelab.data_sources.csv_source.log') as mock_log:
                source = CSVDataSource(temp_file)
                
                assert source._data == {}
                mock_log.warning.assert_called_with("错误：找不到日期时间列（datetime/date/timestamp）")
        finally:
            os.unlink(temp_file)
    
    def test_init_missing_security_column(self):
        """测试缺少security列的情况"""
        # 创建没有security列的CSV
        data = {
            'datetime': ['2023-01-01'],
            'open': [10.0],
            'close': [10.5]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            with patch('simtradelab.data_sources.csv_source.log') as mock_log:
                source = CSVDataSource(temp_file)
                
                assert source._data == {}
                mock_log.warning.assert_called_with("错误：找不到security列")
        finally:
            os.unlink(temp_file)
    
    def test_get_history_success(self, csv_source):
        """测试成功获取历史数据"""
        result = csv_source.get_history(['000001.SZ'], '2023-01-01', '2023-01-02')
        
        assert '000001.SZ' in result
        data = result['000001.SZ']
        assert len(data) == 2
        assert list(data.columns) == ['open', 'high', 'low', 'close', 'volume']
        assert data.iloc[0]['close'] == 10.5
        assert data.iloc[1]['close'] == 11.0
    
    def test_get_history_string_security(self, csv_source):
        """测试传入单个字符串股票代码"""
        result = csv_source.get_history('000002.SZ', '2023-01-01', '2023-01-03')
        
        assert '000002.SZ' in result
        assert len(result['000002.SZ']) == 3
    
    def test_get_history_multiple_securities(self, csv_source):
        """测试获取多个股票的历史数据"""
        result = csv_source.get_history(['000001.SZ', '000002.SZ'], '2023-01-01', '2023-01-02')
        
        assert '000001.SZ' in result
        assert '000002.SZ' in result
        assert len(result['000001.SZ']) == 2
        assert len(result['000002.SZ']) == 2
    
    def test_get_history_custom_fields(self, csv_source):
        """测试指定字段的历史数据获取"""
        result = csv_source.get_history(['000001.SZ'], '2023-01-01', '2023-01-02', fields=['close', 'volume'])
        
        assert '000001.SZ' in result
        data = result['000001.SZ']
        assert list(data.columns) == ['close', 'volume']
        assert 'open' not in data.columns
    
    def test_get_history_nonexistent_security(self, csv_source):
        """测试获取不存在股票的历史数据"""
        with patch('simtradelab.data_sources.csv_source.log') as mock_log:
            result = csv_source.get_history(['999999.SZ'], '2023-01-01', '2023-01-02')
            
            assert result == {}
            mock_log.warning.assert_called_with("股票 999999.SZ 的数据不存在")
    
    def test_get_history_empty_date_range(self, csv_source):
        """测试空日期范围"""
        result = csv_source.get_history(['000001.SZ'], '2024-01-01', '2024-01-02')
        
        # 应该返回空结果，因为数据中没有2024年的数据
        assert result == {}
    
    def test_get_history_frequency_conversion(self, csv_source):
        """测试频率转换"""
        with patch.object(csv_source, '_convert_frequency') as mock_convert:
            mock_convert.return_value = pd.DataFrame({'close': [10.5]})
            
            result = csv_source.get_history(['000001.SZ'], '2023-01-01', '2023-01-02', frequency='1h')
            
            mock_convert.assert_called()
    
    def test_get_current_data_success(self, csv_source):
        """测试成功获取当前数据"""
        result = csv_source.get_current_data(['000001.SZ'])
        
        assert '000001.SZ' in result
        current = result['000001.SZ']
        
        # 检查必要字段
        required_fields = ['last_price', 'current_price', 'high', 'low', 'open', 'volume']
        for field in required_fields:
            assert field in current
        
        # 检查买卖盘数据
        for i in range(1, 6):
            assert f'bid{i}' in current
            assert f'ask{i}' in current
            assert f'bid{i}_volume' in current
            assert f'ask{i}_volume' in current
    
    def test_get_current_data_string_security(self, csv_source):
        """测试传入单个字符串股票代码获取当前数据"""
        result = csv_source.get_current_data('000002.SZ')
        
        assert '000002.SZ' in result
        assert isinstance(result['000002.SZ'], dict)
    
    def test_get_current_data_multiple_securities(self, csv_source):
        """测试获取多个股票的当前数据"""
        result = csv_source.get_current_data(['000001.SZ', '000002.SZ'])
        
        assert '000001.SZ' in result
        assert '000002.SZ' in result
        assert result['000001.SZ']['current_price'] == 11.2  # 最后收盘价
        assert result['000002.SZ']['current_price'] == 21.2  # 最后收盘价
    
    def test_get_current_data_nonexistent_security(self, csv_source):
        """测试获取不存在股票的当前数据"""
        with patch('simtradelab.data_sources.csv_source.log') as mock_log:
            result = csv_source.get_current_data(['999999.SZ'])
            
            assert result == {}
            mock_log.warning.assert_called_with("股票 999999.SZ 的数据不存在")
    
    def test_get_current_data_consistent_random(self, csv_source):
        """测试当前数据的随机数一致性"""
        # 多次调用应该返回相同的结果（基于股票代码的一致性随机数）
        result1 = csv_source.get_current_data(['000001.SZ'])
        result2 = csv_source.get_current_data(['000001.SZ'])
        
        assert result1['000001.SZ']['bid1_volume'] == result2['000001.SZ']['bid1_volume']
        assert result1['000001.SZ']['turnover_rate'] == result2['000001.SZ']['turnover_rate']
    
    def test_get_stock_list(self, csv_source):
        """测试获取股票列表"""
        result = csv_source.get_stock_list()
        
        assert isinstance(result, list)
        assert '000001.SZ' in result
        assert '000002.SZ' in result
        assert len(result) == 2
    
    def test_get_stock_list_empty_data(self):
        """测试空数据时的股票列表"""
        with patch('simtradelab.data_sources.csv_source.log'):
            source = CSVDataSource('/nonexistent/file.csv')
            result = source.get_stock_list()
            
            assert result == []
    
    def test_convert_frequency_1d(self, csv_source):
        """测试1d频率（无转换）"""
        original_data = pd.DataFrame({'close': [10.0, 11.0]})
        result = csv_source._convert_frequency(original_data, '1d')
        
        assert result is original_data  # 应该返回原数据
    
    def test_convert_frequency_unsupported(self, csv_source):
        """测试不支持的频率"""
        original_data = pd.DataFrame({'close': [10.0, 11.0]})
        
        with patch('simtradelab.data_sources.csv_source.log') as mock_log:
            result = csv_source._convert_frequency(original_data, '2d')
            
            assert result is original_data
            mock_log.warning.assert_called_with("不支持的频率: 2d")
    
    def test_convert_frequency_1m(self, csv_source):
        """测试1分钟频率转换"""
        # 创建包含必要字段的测试数据
        test_data = pd.DataFrame({
            'open': [10.0],
            'high': [10.5],
            'low': [9.8],
            'close': [10.2],
            'volume': [1000000],
            'security': ['000001.SZ']
        })
        test_data.index = pd.to_datetime(['2023-01-01'])
        
        result = csv_source._convert_frequency(test_data, '1m')
        
        # 应该生成分钟级数据
        assert len(result) > len(test_data)
        assert 'open' in result.columns
        assert 'close' in result.columns
    
    def test_convert_frequency_5m(self, csv_source):
        """测试5分钟频率转换"""
        test_data = pd.DataFrame({
            'open': [10.0],
            'high': [10.5],
            'low': [9.8],
            'close': [10.2],
            'volume': [1000000],
            'security': ['000001.SZ']
        })
        test_data.index = pd.to_datetime(['2023-01-01'])
        
        result = csv_source._convert_frequency(test_data, '5m')
        
        # 5分钟数据应该比1分钟数据少
        minute_result = csv_source._convert_frequency(test_data, '1m')
        assert len(result) < len(minute_result)
    
    def test_convert_frequency_empty_data(self, csv_source):
        """测试空数据的频率转换"""
        empty_data = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'security'])
        
        result = csv_source._convert_frequency(empty_data, '1m')
        
        assert result is empty_data  # 应该返回原空数据


class TestCSVDataSourceIntegration:
    """CSV数据源集成测试"""
    
    def test_real_world_csv_structure(self):
        """测试真实世界CSV结构"""
        # 模拟真实的CSV结构
        data = {
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'security': ['000001.SZ', '000001.SZ', '000001.SZ'],
            'open': [10.0, 10.5, 11.0],
            'high': [10.8, 11.2, 11.5],
            'low': [9.8, 10.2, 10.5],
            'close': [10.5, 11.0, 11.2],
            'volume': [1000000, 1100000, 1200000],
            'amount': [10500000, 12100000, 13440000]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            source = CSVDataSource(temp_file)
            
            # 测试基本功能
            assert '000001.SZ' in source._data
            
            # 测试历史数据获取
            history = source.get_history(['000001.SZ'], '2023-01-01', '2023-01-02')
            assert '000001.SZ' in history
            assert len(history['000001.SZ']) == 2
            
            # 测试当前数据获取
            current = source.get_current_data(['000001.SZ'])
            assert '000001.SZ' in current
            
        finally:
            os.unlink(temp_file)
    
    def test_large_dataset_simulation(self):
        """测试大数据集模拟"""
        # 生成较大的数据集
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        securities = ['000001.SZ', '000002.SZ', '600000.SH']
        
        data_list = []
        for security in securities:
            for i, date in enumerate(dates):
                base_price = 10.0 + hash(security) % 10
                data_list.append({
                    'datetime': date.strftime('%Y-%m-%d'),
                    'security': security,
                    'open': base_price + i * 0.01,
                    'high': base_price + i * 0.01 + 0.5,
                    'low': base_price + i * 0.01 - 0.3,
                    'close': base_price + i * 0.01 + 0.2,
                    'volume': 1000000 + i * 1000
                })
        
        df = pd.DataFrame(data_list)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f.name, index=False)
            temp_file = f.name
        
        try:
            source = CSVDataSource(temp_file)
            
            # 验证数据加载
            assert len(source._data) == 3
            
            # 测试性能
            history = source.get_history(securities, '2023-01-01', '2023-01-10')
            assert len(history) == 3
            for security in securities:
                assert len(history[security]) == 10
                
        finally:
            os.unlink(temp_file)
    
    def test_error_recovery(self):
        """测试错误恢复"""
        # 创建格式错误的CSV
        invalid_csv_content = "invalid,csv,content\nno,proper,headers"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_csv_content)
            temp_file = f.name
        
        try:
            with patch('simtradelab.data_sources.csv_source.log') as mock_log:
                source = CSVDataSource(temp_file)
                
                # 应该优雅地处理错误
                assert source._data == {}
                mock_log.warning.assert_called()
                
                # 其他方法应该正常工作（返回空结果）
                assert source.get_stock_list() == []
                assert source.get_history(['000001.SZ'], '2023-01-01', '2023-01-02') == {}
                assert source.get_current_data(['000001.SZ']) == {}
                
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])