# -*- coding: utf-8 -*-
"""
AkShare数据源

通过AkShare API获取真实的股票数据
需要安装: pip install akshare
"""

import pandas as pd
from typing import List, Dict, Optional, Union
from .base import BaseDataSource
from ..logger import log

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    ak = None


class AkshareDataSource(BaseDataSource):
    """AkShare数据源"""
    
    def __init__(self, **kwargs):
        """初始化AkShare数据源"""
        if not AKSHARE_AVAILABLE:
            raise ImportError("AkShare未安装，请运行: pip install akshare")
        
        super().__init__(**kwargs)
        log.info("AkShare数据源初始化成功")
    
    def get_history(self, 
                   securities: Union[str, List[str]], 
                   start_date: str, 
                   end_date: str,
                   frequency: str = '1d',
                   fields: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """获取历史数据"""
        if isinstance(securities, str):
            securities = [securities]
        
        if fields is None:
            fields = ['open', 'high', 'low', 'close', 'volume']
        
        # 生成缓存键
        cache_key = self._get_cache_key(
            'get_history',
            securities=securities,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            fields=fields
        )
        
        # 检查缓存
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            log.info("从缓存获取历史数据")
            return cached_data
        
        result = {}
        
        for security in securities:
            try:
                # 转换股票代码
                ak_code = self._convert_security_code(security)
                
                if frequency == '1d':
                    # 获取日线数据
                    df = ak.stock_zh_a_hist(
                        symbol=ak_code,
                        period="daily",
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust=""
                    )
                elif frequency in ['1m', '5m', '15m', '30m']:
                    # 获取分钟线数据
                    period_map = {'1m': '1', '5m': '5', '15m': '15', '30m': '30'}
                    df = ak.stock_zh_a_hist_min_em(
                        symbol=ak_code,
                        period=period_map[frequency],
                        start_date=f"{start_date} 09:30:00",
                        end_date=f"{end_date} 15:00:00"
                    )
                else:
                    log.warning(f"不支持的频率: {frequency}")
                    continue
                
                if df is None or df.empty:
                    log.warning(f"股票 {security} 没有数据")
                    continue
                
                # 标准化数据格式
                df = self._standardize_akshare_data(df, security, frequency)
                
                # 选择指定字段
                available_fields = [f for f in fields if f in df.columns]
                if available_fields:
                    result[security] = df[available_fields].copy()
                
                log.info(f"获取股票 {security} 历史数据成功，共 {len(df)} 条记录")
                
            except Exception as e:
                log.warning(f"获取股票 {security} 历史数据失败: {e}")
                continue
        
        # 缓存结果
        self._set_cache(cache_key, result)
        
        return result
    
    def get_current_data(self, securities: Union[str, List[str]]) -> Dict[str, Dict]:
        """获取实时数据"""
        if isinstance(securities, str):
            securities = [securities]
        
        result = {}
        
        for security in securities:
            try:
                ak_code = self._convert_security_code(security)
                
                # 获取实时数据
                df = ak.stock_zh_a_spot_em()
                
                if df is None or df.empty:
                    log.warning(f"获取股票 {security} 实时数据失败")
                    continue
                
                # 查找对应股票
                stock_data = df[df['代码'] == ak_code]
                if stock_data.empty:
                    log.warning(f"未找到股票 {security} 的实时数据")
                    continue
                
                row = stock_data.iloc[0]
                
                result[security] = {
                    'last_price': row.get('最新价', 0),
                    'current_price': row.get('最新价', 0),
                    'high': row.get('最高', 0),
                    'low': row.get('最低', 0),
                    'open': row.get('今开', 0),
                    'volume': row.get('成交量', 0),
                    'pre_close': row.get('昨收', 0),
                    'change': row.get('涨跌额', 0),
                    'pct_change': row.get('涨跌幅', 0),
                    'amount': row.get('成交额', 0),
                    'turnover_rate': row.get('换手率', 0),
                    'high_limit': row.get('涨停', 0),
                    'low_limit': row.get('跌停', 0),
                    'amplitude': row.get('振幅', 0),
                }
                
                log.info(f"获取股票 {security} 实时数据成功")
                
            except Exception as e:
                log.warning(f"获取股票 {security} 实时数据失败: {e}")
                continue
        
        return result
    
    def get_fundamentals(self, 
                        securities: Union[str, List[str]], 
                        fields: Optional[List[str]] = None,
                        date: Optional[str] = None) -> Dict[str, Dict]:
        """获取基本面数据"""
        if isinstance(securities, str):
            securities = [securities]
        
        result = {}
        
        for security in securities:
            try:
                ak_code = self._convert_security_code(security)
                
                # 获取股票基本信息
                basic_info = ak.stock_individual_info_em(symbol=ak_code)
                
                # 获取财务数据
                try:
                    # 获取利润表
                    income_df = ak.stock_financial_analysis_indicator(symbol=ak_code)
                    
                    fund_data = {}
                    
                    # 处理基本信息
                    if basic_info is not None and not basic_info.empty:
                        for _, row in basic_info.iterrows():
                            fund_data[row['item']] = row['value']
                    
                    # 处理财务指标
                    if income_df is not None and not income_df.empty:
                        latest_data = income_df.iloc[0].to_dict()
                        fund_data.update(latest_data)
                    
                    result[security] = fund_data
                    
                except Exception as e:
                    log.warning(f"获取股票 {security} 财务数据失败: {e}")
                    result[security] = {}
                
            except Exception as e:
                log.warning(f"获取股票 {security} 基本面数据失败: {e}")
                result[security] = {}
        
        return result
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""
        try:
            df = ak.tool_trade_date_hist_sina()
            
            if df is None or df.empty:
                return super().get_trading_calendar(start_date, end_date)
            
            # 筛选日期范围
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            mask = (df['trade_date'] >= start_dt) & (df['trade_date'] <= end_dt)
            filtered_df = df.loc[mask]
            
            return filtered_df['trade_date'].dt.strftime('%Y-%m-%d').tolist()
            
        except Exception as e:
            log.warning(f"获取交易日历失败: {e}")
            return super().get_trading_calendar(start_date, end_date)
    
    def get_stock_list(self) -> List[str]:
        """获取股票列表"""
        try:
            # 获取A股列表
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return []
            
            # 转换为标准格式
            codes = df['代码'].tolist()
            return [self._convert_ak_code_back(code) for code in codes]
            
        except Exception as e:
            log.warning(f"获取股票列表失败: {e}")
            return []
    
    def _convert_security_code(self, security: str) -> str:
        """转换股票代码为AkShare格式"""
        # AkShare通常使用6位数字代码
        if '.' in security:
            return security.split('.')[0]
        return security
    
    def _convert_ak_code_back(self, ak_code: str) -> str:
        """将AkShare代码转换回标准格式"""
        # 根据代码判断交易所
        if ak_code.startswith('00') or ak_code.startswith('30'):
            return f"{ak_code}.SZ"
        elif ak_code.startswith('60') or ak_code.startswith('68'):
            return f"{ak_code}.SH"
        else:
            return f"{ak_code}.SZ"  # 默认深交所
    
    def _standardize_akshare_data(self, df: pd.DataFrame, security: str, frequency: str) -> pd.DataFrame:
        """标准化AkShare数据格式"""
        # AkShare的列名映射
        column_mapping = {
            '日期': 'date',
            '时间': 'date',
            '开盘': 'open',
            '最高': 'high', 
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 设置日期索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        # 确保包含security列
        if 'security' not in df.columns:
            df['security'] = security
        
        # 排序
        df = df.sort_index()
        
        return self._normalize_data(df, security)
