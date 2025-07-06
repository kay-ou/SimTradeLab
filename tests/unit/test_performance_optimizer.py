# -*- coding: utf-8 -*-
"""
性能优化模块测试
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
import concurrent.futures
from pathlib import Path
from unittest.mock import Mock, patch

from simtradelab.performance_optimizer import (
    DataCache, ConcurrentDataLoader, VectorizedCalculator, MemoryOptimizer,
    get_global_cache
)


class TestDataCache:
    """数据缓存测试类"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """创建临时缓存目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cache(self, temp_cache_dir):
        """创建缓存实例"""
        return DataCache(cache_dir=temp_cache_dir, max_memory_items=3)
    
    def test_cache_set_and_get(self, cache):
        """测试缓存设置和获取"""
        test_data = {"key": "value", "number": 123}
        
        # 设置缓存
        cache.set(test_data, param1="test", param2=456)
        
        # 获取缓存
        result = cache.get(param1="test", param2=456)
        
        assert result == test_data
    
    def test_cache_key_generation(self, cache):
        """测试缓存键生成"""
        # 相同参数应该生成相同键
        cache.set("data1", param1="test", param2=123)
        result1 = cache.get(param1="test", param2=123)
        
        cache.set("data2", param2=123, param1="test")  # 参数顺序不同
        result2 = cache.get(param2=123, param1="test")
        
        assert result1 == "data1"
        assert result2 == "data2"  # 应该覆盖了之前的数据
    
    def test_cache_memory_limit(self, cache):
        """测试内存缓存限制"""
        # 添加超过限制的项目
        for i in range(5):
            cache.set(f"data_{i}", key=f"test_{i}")
        
        # 检查内存缓存大小不超过限制
        assert len(cache._memory_cache) <= 3
    
    def test_cache_disk_persistence(self, cache):
        """测试磁盘缓存持久性"""
        test_data = [1, 2, 3, 4, 5]
        
        # 设置缓存
        cache.set(test_data, test_key="persistence")
        
        # 清空内存缓存
        cache._memory_cache.clear()
        cache._access_count.clear()
        
        # 从磁盘获取
        result = cache.get(test_key="persistence")
        assert result == test_data
    
    def test_cache_clear(self, cache):
        """测试缓存清空"""
        cache.set("test_data", key="test")
        
        cache.clear()
        
        assert len(cache._memory_cache) == 0
        assert len(cache._access_count) == 0
        assert len(list(cache.cache_dir.glob("*.pkl"))) == 0
    
    def test_global_cache(self):
        """测试全局缓存实例"""
        global_cache = get_global_cache()
        assert isinstance(global_cache, DataCache)
        
        # 确保返回同一实例
        global_cache2 = get_global_cache()
        assert global_cache is global_cache2


class TestConcurrentDataLoader:
    """并发数据加载器测试类"""
    
    @pytest.fixture
    def mock_data_source_manager(self):
        """创建模拟数据源管理器"""
        manager = Mock()
        
        def mock_get_history(securities, start_date, end_date, frequency):
            result = {}
            for security in securities:
                dates = pd.date_range(start_date, end_date, freq='D')
                result[security] = pd.DataFrame({
                    'close': np.random.rand(len(dates)) * 100 + 50,
                    'volume': np.random.randint(1000000, 5000000, len(dates))
                }, index=dates)
            return result
        
        manager.get_history.side_effect = mock_get_history
        return manager
    
    def test_concurrent_loading_single_security(self, mock_data_source_manager):
        """测试单只股票并发加载"""
        loader = ConcurrentDataLoader(max_workers=2)
        
        result = loader.load_multiple_securities(
            mock_data_source_manager,
            ['STOCK_A'],
            '2023-01-01',
            '2023-01-10',
            '1d'
        )
        
        assert 'STOCK_A' in result
        assert isinstance(result['STOCK_A'], pd.DataFrame)
        assert len(result['STOCK_A']) > 0
    
    def test_concurrent_loading_multiple_securities(self, mock_data_source_manager):
        """测试多只股票并发加载"""
        loader = ConcurrentDataLoader(max_workers=2)
        
        securities = ['STOCK_A', 'STOCK_B', 'STOCK_C', 'STOCK_D']
        result = loader.load_multiple_securities(
            mock_data_source_manager,
            securities,
            '2023-01-01',
            '2023-01-10',
            '1d'
        )
        
        assert len(result) == len(securities)
        for security in securities:
            assert security in result
            assert isinstance(result[security], pd.DataFrame)
    
    def test_concurrent_loading_with_errors(self):
        """测试并发加载时出现错误"""
        manager = Mock()
        
        def failing_get_history(securities, start_date, end_date, frequency):
            if 'FAIL' in securities[0]:
                raise Exception("Data loading failed")
            return {securities[0]: pd.DataFrame({'close': [100]}, index=[pd.Timestamp('2023-01-01')])}
        
        manager.get_history.side_effect = failing_get_history
        
        loader = ConcurrentDataLoader(max_workers=2)
        
        # 为每个证券单独调用
        result = {}
        securities = ['STOCK_A', 'FAIL_STOCK', 'STOCK_B']
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            for security in securities:
                futures[security] = executor.submit(loader.load_multiple_securities, 
                                                   manager, [security], '2023-01-01', '2023-01-10', '1d')
            
            for security, future in futures.items():
                try:
                    data = future.result()
                    if data:
                        result.update(data)
                except Exception:
                    pass  # 忽略失败的证券
        
        # 应该只返回成功加载的股票
        assert 'STOCK_A' in result
        assert 'STOCK_B' in result
        assert 'FAIL_STOCK' not in result


class TestVectorizedCalculator:
    """向量化计算器测试类"""
    
    @pytest.fixture
    def sample_prices(self):
        """创建示例价格数据"""
        dates = pd.date_range('2023-01-01', '2023-01-20', freq='D')
        return pd.Series(np.random.rand(len(dates)) * 10 + 100, index=dates)
    
    @pytest.fixture
    def sample_ohlcv(self):
        """创建示例OHLCV数据"""
        dates = pd.date_range('2023-01-01', '2023-01-30', freq='D')
        close = pd.Series(np.random.rand(len(dates)) * 10 + 100, index=dates)
        high = close + np.random.rand(len(dates)) * 2
        low = close - np.random.rand(len(dates)) * 2
        volume = pd.Series(np.random.randint(1000000, 5000000, len(dates)), index=dates)
        
        return high, low, close, volume
    
    def test_calculate_returns(self, sample_prices):
        """测试收益率计算"""
        returns = VectorizedCalculator.calculate_returns(sample_prices)
        
        assert isinstance(returns, pd.Series)
        assert len(returns) == len(sample_prices)
        assert returns.iloc[0] == 0  # 第一个值应该是0（没有前一个值）
    
    def test_calculate_rolling_metrics(self, sample_prices):
        """测试滚动统计指标计算"""
        metrics = VectorizedCalculator.calculate_rolling_metrics(sample_prices, window=5)
        
        assert 'mean' in metrics
        assert 'std' in metrics
        assert 'max' in metrics
        assert 'min' in metrics
        
        for metric in metrics.values():
            assert isinstance(metric, pd.Series)
            assert len(metric) == len(sample_prices)
    
    def test_calculate_technical_indicators_vectorized(self, sample_ohlcv):
        """测试向量化技术指标计算"""
        high, low, close, volume = sample_ohlcv
        
        indicators = VectorizedCalculator.calculate_technical_indicators_vectorized(
            high, low, close, volume
        )
        
        # 检查移动平均线
        assert 'MA5' in indicators
        assert 'MA10' in indicators
        assert 'EMA5' in indicators
        
        # 检查RSI
        assert 'RSI' in indicators
        
        # 检查MACD
        assert 'MACD_DIF' in indicators
        assert 'MACD_DEA' in indicators
        assert 'MACD_HIST' in indicators
        
        # 检查布林带
        assert 'BOLL_UPPER' in indicators
        assert 'BOLL_MIDDLE' in indicators
        assert 'BOLL_LOWER' in indicators
        
        # 验证数据类型和长度
        for indicator in indicators.values():
            assert isinstance(indicator, pd.Series)
            assert len(indicator) == len(close)


class TestMemoryOptimizer:
    """内存优化器测试类"""
    
    @pytest.fixture
    def sample_dataframe(self):
        """创建示例DataFrame"""
        return pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'large_int': [100000, 200000, 300000, 400000, 500000],
            'string_col': ['A', 'B', 'C', 'D', 'E']
        })
    
    def test_optimize_dataframe_memory(self, sample_dataframe):
        """测试DataFrame内存优化"""
        original_memory = sample_dataframe.memory_usage(deep=True).sum()
        
        optimized_df = MemoryOptimizer.optimize_dataframe_memory(sample_dataframe)
        optimized_memory = optimized_df.memory_usage(deep=True).sum()
        
        # 优化后内存使用应该不增加
        assert optimized_memory <= original_memory
        
        # 数据应该保持一致
        pd.testing.assert_frame_equal(
            sample_dataframe.astype(str), 
            optimized_df.astype(str)
        )
    
    def test_reduce_memory_usage(self, sample_dataframe):
        """测试减少内存使用"""
        data_dict = {
            'STOCK_A': sample_dataframe.copy(),
            'STOCK_B': sample_dataframe.copy()
        }
        
        optimized_dict = MemoryOptimizer.reduce_memory_usage(data_dict)
        
        assert len(optimized_dict) == len(data_dict)
        assert 'STOCK_A' in optimized_dict
        assert 'STOCK_B' in optimized_dict
        
        # 检查数据结构保持一致
        for key in data_dict:
            assert optimized_dict[key].shape == data_dict[key].shape
    
    def test_memory_optimization_with_large_numbers(self):
        """测试大数字的内存优化"""
        # 创建包含大整数的DataFrame
        df = pd.DataFrame({
            'small_int': [1, 2, 3],
            'medium_int': [1000, 2000, 3000], 
            'large_int': [100000000, 200000000, 300000000]
        })
        
        optimized_df = MemoryOptimizer.optimize_dataframe_memory(df)
        
        # 检查数据类型优化
        assert optimized_df['small_int'].dtype in [np.int8, np.int16, np.int32]
        assert optimized_df['medium_int'].dtype in [np.int8, np.int16, np.int32]
        
        # 验证数据一致性
        pd.testing.assert_frame_equal(df.astype(str), optimized_df.astype(str))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])