# -*- coding: utf-8 -*-
"""
数据源基类

定义统一的数据源接口，所有数据源都应该继承此类
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Optional, Union
from datetime import datetime


class BaseDataSource(ABC):
    """数据源基类"""
    
    def __init__(self, cache_enabled=True, cache_dir="./cache"):
        """
        初始化数据源
        
        Args:
            cache_enabled: 是否启用缓存
            cache_dir: 缓存目录
        """
        self.cache_enabled = cache_enabled
        self.cache_dir = cache_dir
        self._cache = {}
    
    @abstractmethod
    def get_history(self, 
                   securities: Union[str, List[str]], 
                   start_date: str, 
                   end_date: str,
                   frequency: str = '1d',
                   fields: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        获取历史数据
        
        Args:
            securities: 股票代码或代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: 数据频率 ('1d', '1m', '5m', '15m', '30m')
            fields: 字段列表，默认为 ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            Dict[str, pd.DataFrame]: 以股票代码为key的数据字典
        """
        pass
    
    @abstractmethod
    def get_current_data(self, securities: Union[str, List[str]]) -> Dict[str, Dict]:
        """
        获取实时数据
        
        Args:
            securities: 股票代码或代码列表
            
        Returns:
            Dict[str, Dict]: 实时数据字典
        """
        pass
    
    def get_fundamentals(self, 
                        securities: Union[str, List[str]], 
                        fields: Optional[List[str]] = None,
                        date: Optional[str] = None) -> Dict[str, Dict]:
        """
        获取基本面数据
        
        Args:
            securities: 股票代码或代码列表
            fields: 字段列表
            date: 查询日期
            
        Returns:
            Dict[str, Dict]: 基本面数据字典
        """
        # 默认实现返回空数据，子类可以重写
        if isinstance(securities, str):
            securities = [securities]
        return {sec: {} for sec in securities}
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """
        获取交易日历
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[str]: 交易日列表
        """
        # 默认实现，子类可以重写
        return pd.date_range(start_date, end_date, freq='B').strftime('%Y-%m-%d').tolist()
    
    def get_stock_list(self) -> List[str]:
        """
        获取股票列表
        
        Returns:
            List[str]: 股票代码列表
        """
        # 默认实现返回空列表，子类应该重写
        return []
    
    def _normalize_data(self, data: pd.DataFrame, security: str) -> pd.DataFrame:
        """
        标准化数据格式
        
        Args:
            data: 原始数据
            security: 股票代码
            
        Returns:
            pd.DataFrame: 标准化后的数据
        """
        # 确保包含必要的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                if col == 'volume':
                    data[col] = 0  # 如果没有成交量数据，设为0
                else:
                    raise ValueError(f"缺少必要的数据列: {col}")
        
        # 确保数据类型正确
        for col in ['open', 'high', 'low', 'close']:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        data['volume'] = pd.to_numeric(data['volume'], errors='coerce').fillna(0)
        
        # 确保索引是datetime类型
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # 添加security列（如果不存在）
        if 'security' not in data.columns:
            data['security'] = security
            
        return data
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [method]
        for k, v in sorted(kwargs.items()):
            if isinstance(v, list):
                v = ','.join(map(str, v))
            key_parts.append(f"{k}={v}")
        return '|'.join(key_parts)
    
    def _get_from_cache(self, cache_key: str):
        """从缓存获取数据"""
        if not self.cache_enabled:
            return None
        return self._cache.get(cache_key)
    
    def _set_cache(self, cache_key: str, data):
        """设置缓存数据"""
        if self.cache_enabled:
            self._cache[cache_key] = data
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
