# -*- coding: utf-8 -*-
"""
数据缓存和性能优化模块
"""
import hashlib
import pickle
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache
import concurrent.futures
import threading
import pandas as pd
import numpy as np
from .logger import log


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "./cache", max_memory_items: int = 100):
        """
        初始化数据缓存
        
        Args:
            cache_dir: 缓存目录
            max_memory_items: 内存缓存最大条目数
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_memory_items = max_memory_items
        self._memory_cache: Dict[str, Any] = {}
        self._access_count: Dict[str, int] = {}
        self._lock = threading.RLock()
        
    def _generate_key(self, **kwargs) -> str:
        """生成缓存键"""
        key_data = sorted(kwargs.items())
        key_str = str(key_data)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{key}.pkl"
    
    def get(self, **kwargs) -> Optional[Any]:
        """获取缓存数据"""
        key = self._generate_key(**kwargs)
        
        with self._lock:
            # 首先检查内存缓存
            if key in self._memory_cache:
                self._access_count[key] = self._access_count.get(key, 0) + 1
                return self._memory_cache[key]
            
            # 检查磁盘缓存
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    # 加载到内存缓存
                    self._add_to_memory_cache(key, data)
                    return data
                except Exception as e:
                    log.warning(f"读取缓存文件失败: {e}")
                    
        return None
    
    def set(self, data: Any, **kwargs) -> None:
        """设置缓存数据"""
        key = self._generate_key(**kwargs)
        
        with self._lock:
            # 保存到内存缓存
            self._add_to_memory_cache(key, data)
            
            # 保存到磁盘缓存
            cache_file = self._get_cache_file(key)
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
            except Exception as e:
                log.warning(f"保存缓存文件失败: {e}")
    
    def _add_to_memory_cache(self, key: str, data: Any) -> None:
        """添加到内存缓存"""
        # 如果缓存已满，移除最少使用的项
        if len(self._memory_cache) >= self.max_memory_items:
            lru_key = min(self._access_count.keys(), key=lambda k: self._access_count[k])
            del self._memory_cache[lru_key]
            del self._access_count[lru_key]
        
        self._memory_cache[key] = data
        self._access_count[key] = 1
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._memory_cache.clear()
            self._access_count.clear()
            
            # 清空磁盘缓存
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    log.warning(f"删除缓存文件失败: {e}")


class ConcurrentDataLoader:
    """并发数据加载器"""
    
    def __init__(self, max_workers: int = 4):
        """
        初始化并发数据加载器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers
        
    def load_multiple_securities(
        self, 
        data_source_manager, 
        securities: list, 
        start_date: str, 
        end_date: str, 
        frequency: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        并发加载多只股票数据
        
        Args:
            data_source_manager: 数据源管理器
            securities: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            
        Returns:
            股票数据字典
        """
        def load_single_security(security):
            """加载单只股票数据"""
            try:
                data = data_source_manager.get_history(
                    securities=[security],
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency
                )
                return security, data.get(security)
            except Exception as e:
                log.warning(f"加载股票 {security} 数据失败: {e}")
                return security, None
        
        result_data = {}
        
        # 使用线程池并发加载
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_security = {
                executor.submit(load_single_security, security): security 
                for security in securities
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_security):
                security, data = future.result()
                if data is not None:
                    result_data[security] = data
                    
        log.info(f"并发加载完成，成功加载 {len(result_data)}/{len(securities)} 只股票数据")
        return result_data


class VectorizedCalculator:
    """向量化计算器"""
    
    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """计算收益率（向量化）"""
        return prices.pct_change().fillna(0)
    
    @staticmethod
    def calculate_rolling_metrics(
        prices: pd.Series, 
        window: int = 20
    ) -> Dict[str, pd.Series]:
        """计算滚动统计指标（向量化）"""
        return {
            'mean': prices.rolling(window=window).mean(),
            'std': prices.rolling(window=window).std(),
            'max': prices.rolling(window=window).max(),
            'min': prices.rolling(window=window).min(),
        }
    
    @staticmethod
    def calculate_technical_indicators_vectorized(
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        volume: pd.Series,
        periods: Tuple[int, ...] = (5, 10, 20, 60)
    ) -> Dict[str, pd.Series]:
        """向量化计算技术指标"""
        indicators = {}
        
        # 移动平均线
        for period in periods:
            indicators[f'MA{period}'] = close.rolling(window=period).mean()
            indicators[f'EMA{period}'] = close.ewm(span=period).mean()
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        indicators['MACD_DIF'] = ema_12 - ema_26
        indicators['MACD_DEA'] = indicators['MACD_DIF'].ewm(span=9).mean()
        indicators['MACD_HIST'] = (indicators['MACD_DIF'] - indicators['MACD_DEA']) * 2
        
        # 布林带
        ma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        indicators['BOLL_UPPER'] = ma20 + 2 * std20
        indicators['BOLL_MIDDLE'] = ma20
        indicators['BOLL_LOWER'] = ma20 - 2 * std20
        
        return indicators


class MemoryOptimizer:
    """内存优化器"""
    
    @staticmethod
    def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
        """优化DataFrame内存使用"""
        optimized_df = df.copy()
        
        for col in optimized_df.columns:
            col_type = optimized_df[col].dtype
            
            if col_type != 'object':
                c_min = optimized_df[col].min()
                c_max = optimized_df[col].max()
                
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        optimized_df[col] = optimized_df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        optimized_df[col] = optimized_df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        optimized_df[col] = optimized_df[col].astype(np.int32)
                else:
                    if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        optimized_df[col] = optimized_df[col].astype(np.float32)
        
        return optimized_df
    
    @staticmethod
    def reduce_memory_usage(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """减少内存使用"""
        optimized_dict = {}
        original_memory = 0
        optimized_memory = 0
        
        for security, df in data_dict.items():
            original_memory += df.memory_usage(deep=True).sum()
            optimized_df = MemoryOptimizer.optimize_dataframe_memory(df)
            optimized_memory += optimized_df.memory_usage(deep=True).sum()
            optimized_dict[security] = optimized_df
        
        memory_reduction = (original_memory - optimized_memory) / original_memory * 100
        log.info(f"内存优化完成，减少内存使用 {memory_reduction:.1f}%")
        
        return optimized_dict


# 全局缓存实例
_global_cache = DataCache()

def get_global_cache() -> DataCache:
    """获取全局缓存实例"""
    return _global_cache