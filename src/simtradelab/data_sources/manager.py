# -*- coding: utf-8 -*-
"""
数据源管理器

管理多个数据源，提供统一的数据访问接口
"""

import pandas as pd
from typing import List, Dict, Optional, Union, Any
from .base import BaseDataSource
from ..logger import log


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self, primary_source: BaseDataSource, fallback_sources: Optional[List[BaseDataSource]] = None):
        """
        初始化数据源管理器
        
        Args:
            primary_source: 主数据源
            fallback_sources: 备用数据源列表
        """
        self.primary_source = primary_source
        self.fallback_sources = fallback_sources or []
        self.all_sources = [primary_source] + self.fallback_sources
        
        log.info(f"数据源管理器初始化完成，主数据源: {type(primary_source).__name__}, "
                f"备用数据源: {len(self.fallback_sources)} 个")
    
    def get_history(self, 
                   securities: Union[str, List[str]], 
                   start_date: str, 
                   end_date: str,
                   frequency: str = '1d',
                   fields: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        获取历史数据，支持多数据源回退
        
        Args:
            securities: 股票代码或代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            fields: 字段列表
            
        Returns:
            Dict[str, pd.DataFrame]: 历史数据
        """
        if isinstance(securities, str):
            securities = [securities]
        
        result = {}
        failed_securities = set(securities)
        
        # 尝试从主数据源获取
        try:
            primary_result = self.primary_source.get_history(
                securities, start_date, end_date, frequency, fields
            )
            result.update(primary_result)
            failed_securities -= set(primary_result.keys())
            
            if not failed_securities:
                return result
                
        except Exception as e:
            log.warning(f"主数据源获取历史数据失败: {e}")
        
        # 尝试从备用数据源获取失败的股票
        for i, fallback_source in enumerate(self.fallback_sources):
            if not failed_securities:
                break
                
            try:
                fallback_result = fallback_source.get_history(
                    list(failed_securities), start_date, end_date, frequency, fields
                )
                result.update(fallback_result)
                failed_securities -= set(fallback_result.keys())
                
                log.info(f"备用数据源 {i+1} 获取了 {len(fallback_result)} 只股票的数据")
                
            except Exception as e:
                log.warning(f"备用数据源 {i+1} 获取历史数据失败: {e}")
        
        if failed_securities:
            log.warning(f"以下股票无法获取历史数据: {failed_securities}")
        
        return result
    
    def get_current_data(self, securities: Union[str, List[str]]) -> Dict[str, Dict]:
        """
        获取实时数据，支持多数据源回退
        
        Args:
            securities: 股票代码或代码列表
            
        Returns:
            Dict[str, Dict]: 实时数据
        """
        if isinstance(securities, str):
            securities = [securities]
        
        result = {}
        failed_securities = set(securities)
        
        # 尝试从主数据源获取
        try:
            primary_result = self.primary_source.get_current_data(securities)
            result.update(primary_result)
            failed_securities -= set(primary_result.keys())
            
            if not failed_securities:
                return result
                
        except Exception as e:
            log.warning(f"主数据源获取实时数据失败: {e}")
        
        # 尝试从备用数据源获取失败的股票
        for i, fallback_source in enumerate(self.fallback_sources):
            if not failed_securities:
                break
                
            try:
                fallback_result = fallback_source.get_current_data(list(failed_securities))
                result.update(fallback_result)
                failed_securities -= set(fallback_result.keys())
                
                log.info(f"备用数据源 {i+1} 获取了 {len(fallback_result)} 只股票的实时数据")
                
            except Exception as e:
                log.warning(f"备用数据源 {i+1} 获取实时数据失败: {e}")
        
        if failed_securities:
            log.warning(f"以下股票无法获取实时数据: {failed_securities}")
        
        return result
    
    def get_fundamentals(self, 
                        securities: Union[str, List[str]], 
                        fields: Optional[List[str]] = None,
                        date: Optional[str] = None) -> Dict[str, Dict]:
        """
        获取基本面数据，支持多数据源回退
        
        Args:
            securities: 股票代码或代码列表
            fields: 字段列表
            date: 查询日期
            
        Returns:
            Dict[str, Dict]: 基本面数据
        """
        if isinstance(securities, str):
            securities = [securities]
        
        result = {}
        failed_securities = set(securities)
        
        # 尝试从主数据源获取
        try:
            primary_result = self.primary_source.get_fundamentals(securities, fields, date)
            # 过滤掉空数据
            for sec, data in primary_result.items():
                if data:  # 只保留非空数据
                    result[sec] = data
                    failed_securities.discard(sec)
                    
        except Exception as e:
            log.warning(f"主数据源获取基本面数据失败: {e}")
        
        # 尝试从备用数据源获取失败的股票
        for i, fallback_source in enumerate(self.fallback_sources):
            if not failed_securities:
                break
                
            try:
                fallback_result = fallback_source.get_fundamentals(
                    list(failed_securities), fields, date
                )
                # 过滤掉空数据
                for sec, data in fallback_result.items():
                    if data:  # 只保留非空数据
                        result[sec] = data
                        failed_securities.discard(sec)
                
                if fallback_result:
                    log.info(f"备用数据源 {i+1} 获取了基本面数据")
                
            except Exception as e:
                log.warning(f"备用数据源 {i+1} 获取基本面数据失败: {e}")
        
        return result
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""
        for i, source in enumerate(self.all_sources):
            try:
                calendar = source.get_trading_calendar(start_date, end_date)
                if calendar:
                    if i > 0:
                        log.info(f"使用数据源 {i+1} 获取交易日历")
                    return calendar
            except Exception as e:
                log.warning(f"数据源 {i+1} 获取交易日历失败: {e}")
        
        # 如果所有数据源都失败，返回默认的交易日历
        log.warning("所有数据源获取交易日历失败，使用默认日历")
        return pd.date_range(start_date, end_date, freq='B').strftime('%Y-%m-%d').tolist()
    
    def get_stock_list(self) -> List[str]:
        """获取股票列表"""
        for i, source in enumerate(self.all_sources):
            try:
                stock_list = source.get_stock_list()
                if stock_list:
                    if i > 0:
                        log.info(f"使用数据源 {i+1} 获取股票列表")
                    return stock_list
            except Exception as e:
                log.warning(f"数据源 {i+1} 获取股票列表失败: {e}")
        
        log.warning("所有数据源获取股票列表失败")
        return []
    
    def add_fallback_source(self, source: BaseDataSource):
        """添加备用数据源"""
        self.fallback_sources.append(source)
        self.all_sources.append(source)
        log.info(f"添加备用数据源: {type(source).__name__}")
    
    def remove_fallback_source(self, source: BaseDataSource):
        """移除备用数据源"""
        if source in self.fallback_sources:
            self.fallback_sources.remove(source)
            self.all_sources.remove(source)
            log.info(f"移除备用数据源: {type(source).__name__}")
    
    def clear_cache(self):
        """清空所有数据源的缓存"""
        for source in self.all_sources:
            source.clear_cache()
        log.info("已清空所有数据源缓存")
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据源的状态"""
        status = {}
        
        for i, source in enumerate(self.all_sources):
            source_name = f"{'primary' if i == 0 else f'fallback_{i}'}"
            source_type = type(source).__name__
            
            try:
                # 尝试获取一个简单的测试数据来检查连接状态
                test_result = source.get_stock_list()
                is_available = len(test_result) > 0
                error_msg = None
            except Exception as e:
                is_available = False
                error_msg = str(e)
            
            status[source_name] = {
                'type': source_type,
                'available': is_available,
                'error': error_msg
            }
        
        return status
