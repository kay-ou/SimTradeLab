# -*- coding: utf-8 -*-
"""
数据源模块

提供统一的数据源接口，支持多种数据源：
- CSV文件数据源
- Tushare数据源  
- AkShare数据源
- 其他可扩展数据源
"""

from .base import BaseDataSource
from .csv_source import CSVDataSource
from .manager import DataSourceManager

# 尝试导入可选的数据源
try:
    from .tushare_source import TushareDataSource
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    TushareDataSource = None

try:
    from .akshare_source import AkshareDataSource
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    AkshareDataSource = None


class DataSourceFactory:
    """数据源工厂类"""
    
    _sources = {
        'csv': CSVDataSource,
    }
    
    @classmethod
    def register_source(cls, name, source_class):
        """注册新的数据源"""
        cls._sources[name] = source_class
    
    @classmethod
    def create(cls, source_type, **kwargs):
        """创建数据源实例"""
        if source_type not in cls._sources:
            available = list(cls._sources.keys())
            raise ValueError(f"不支持的数据源类型: {source_type}. 可用类型: {available}")
        
        source_class = cls._sources[source_type]
        return source_class(**kwargs)
    
    @classmethod
    def list_available(cls):
        """列出所有可用的数据源"""
        return list(cls._sources.keys())


# 注册可用的数据源
if TUSHARE_AVAILABLE:
    DataSourceFactory.register_source('tushare', TushareDataSource)

if AKSHARE_AVAILABLE:
    DataSourceFactory.register_source('akshare', AkshareDataSource)


__all__ = [
    'BaseDataSource',
    'CSVDataSource', 
    'DataSourceManager',
    'DataSourceFactory',
    'TUSHARE_AVAILABLE',
    'AKSHARE_AVAILABLE'
]

if TUSHARE_AVAILABLE:
    __all__.append('TushareDataSource')

if AKSHARE_AVAILABLE:
    __all__.append('AkshareDataSource')
