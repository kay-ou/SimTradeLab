# -*- coding: utf-8 -*-
"""
Tushare数据源

通过Tushare API获取真实的股票数据
需要安装: pip install tushare
"""

import pandas as pd
from typing import List, Dict, Optional, Union
from .base import BaseDataSource
from ..logger import log

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    TUSHARE_AVAILABLE = False
    ts = None


class TushareDataSource(BaseDataSource):
    """Tushare数据源"""
    
    def __init__(self, token: str, **kwargs):
        """
        初始化Tushare数据源
        
        Args:
            token: Tushare API token
        """
        if not TUSHARE_AVAILABLE:
            raise ImportError("Tushare未安装，请运行: pip install tushare")
        
        super().__init__(**kwargs)
        self.token = token
        
        # 设置token
        ts.set_token(token)
        self.pro = ts.pro_api()
        
        log.info("Tushare数据源初始化成功")
    
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
                # 转换股票代码格式
                ts_code = self._convert_security_code(security)
                
                if frequency == '1d':
                    # 获取日线数据
                    df = self.pro.daily(
                        ts_code=ts_code,
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', '')
                    )
                elif frequency in ['1m', '5m', '15m', '30m']:
                    # 获取分钟线数据
                    freq_map = {'1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min'}
                    df = ts.get_hist_data(
                        ts_code.split('.')[0],
                        start=start_date,
                        end=end_date,
                        ktype=freq_map[frequency]
                    )
                else:
                    log.warning(f"不支持的频率: {frequency}")
                    continue
                
                if df is None or df.empty:
                    log.warning(f"股票 {security} 没有数据")
                    continue
                
                # 标准化数据格式
                df = self._standardize_tushare_data(df, security, frequency)
                
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
        
        try:
            # 转换股票代码
            ts_codes = [self._convert_security_code(sec) for sec in securities]
            
            # 获取实时数据
            df = self.pro.realtime_quote(ts_code=','.join(ts_codes))
            
            if df is None or df.empty:
                log.warning("获取实时数据失败")
                return result
            
            # 转换为标准格式
            for _, row in df.iterrows():
                security = self._convert_ts_code_back(row['ts_code'])
                
                result[security] = {
                    'last_price': row.get('price', 0),
                    'current_price': row.get('price', 0),
                    'high': row.get('high', 0),
                    'low': row.get('low', 0),
                    'open': row.get('open', 0),
                    'volume': row.get('vol', 0),
                    'pre_close': row.get('pre_close', 0),
                    'change': row.get('change', 0),
                    'pct_change': row.get('pct_chg', 0),
                    'amount': row.get('amount', 0),
                    'turnover_rate': row.get('turnover_rate', 0),
                    'bid1': row.get('bid1', 0),
                    'bid2': row.get('bid2', 0),
                    'bid3': row.get('bid3', 0),
                    'bid4': row.get('bid4', 0),
                    'bid5': row.get('bid5', 0),
                    'ask1': row.get('ask1', 0),
                    'ask2': row.get('ask2', 0),
                    'ask3': row.get('ask3', 0),
                    'ask4': row.get('ask4', 0),
                    'ask5': row.get('ask5', 0),
                    'bid1_volume': row.get('bid1_size', 0),
                    'bid2_volume': row.get('bid2_size', 0),
                    'bid3_volume': row.get('bid3_size', 0),
                    'bid4_volume': row.get('bid4_size', 0),
                    'bid5_volume': row.get('bid5_size', 0),
                    'ask1_volume': row.get('ask1_size', 0),
                    'ask2_volume': row.get('ask2_size', 0),
                    'ask3_volume': row.get('ask3_size', 0),
                    'ask4_volume': row.get('ask4_size', 0),
                    'ask5_volume': row.get('ask5_size', 0),
                }
            
            log.info(f"获取 {len(result)} 只股票的实时数据成功")
            
        except Exception as e:
            log.warning(f"获取实时数据失败: {e}")
        
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
                ts_code = self._convert_security_code(security)
                
                # 获取基本信息
                basic_info = self.pro.stock_basic(ts_code=ts_code)
                
                # 获取财务数据
                if date:
                    period = date.replace('-', '')[:6]  # YYYYMM格式
                else:
                    period = None
                
                # 获取利润表
                income = self.pro.income(ts_code=ts_code, period=period)
                # 获取资产负债表  
                balancesheet = self.pro.balancesheet(ts_code=ts_code, period=period)
                # 获取现金流量表
                cashflow = self.pro.cashflow(ts_code=ts_code, period=period)
                
                # 整合数据
                fund_data = {}
                if not basic_info.empty:
                    fund_data.update(basic_info.iloc[0].to_dict())
                if not income.empty:
                    fund_data.update(income.iloc[0].to_dict())
                if not balancesheet.empty:
                    fund_data.update(balancesheet.iloc[0].to_dict())
                if not cashflow.empty:
                    fund_data.update(cashflow.iloc[0].to_dict())
                
                result[security] = fund_data
                
            except Exception as e:
                log.warning(f"获取股票 {security} 基本面数据失败: {e}")
                result[security] = {}
        
        return result
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """获取交易日历"""
        try:
            df = self.pro.trade_cal(
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                is_open='1'
            )
            
            if df is None or df.empty:
                return super().get_trading_calendar(start_date, end_date)
            
            return df['cal_date'].apply(lambda x: f"{x[:4]}-{x[4:6]}-{x[6:8]}").tolist()
            
        except Exception as e:
            log.warning(f"获取交易日历失败: {e}")
            return super().get_trading_calendar(start_date, end_date)
    
    def get_stock_list(self) -> List[str]:
        """获取股票列表"""
        try:
            df = self.pro.stock_basic(exchange='', list_status='L')
            if df is None or df.empty:
                return []
            
            # 转换为标准格式
            return [self._convert_ts_code_back(code) for code in df['ts_code'].tolist()]
            
        except Exception as e:
            log.warning(f"获取股票列表失败: {e}")
            return []
    
    def _convert_security_code(self, security: str) -> str:
        """转换股票代码为Tushare格式"""
        if '.' in security:
            return security
        
        # 根据代码判断交易所
        if security.startswith('00') or security.startswith('30'):
            return f"{security}.SZ"
        elif security.startswith('60') or security.startswith('68'):
            return f"{security}.SH"
        else:
            return f"{security}.SZ"  # 默认深交所
    
    def _convert_ts_code_back(self, ts_code: str) -> str:
        """将Tushare代码转换回标准格式"""
        return ts_code
    
    def _standardize_tushare_data(self, df: pd.DataFrame, security: str, frequency: str) -> pd.DataFrame:
        """标准化Tushare数据格式"""
        # 重命名列
        column_mapping = {
            'trade_date': 'date',
            'ts_code': 'security',
            'vol': 'volume'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 设置日期索引
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        # 确保包含security列
        if 'security' not in df.columns:
            df['security'] = security
        
        # 排序（Tushare数据通常是倒序的）
        df = df.sort_index()
        
        return self._normalize_data(df, security)
