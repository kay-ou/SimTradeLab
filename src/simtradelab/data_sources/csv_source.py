# -*- coding: utf-8 -*-
"""
CSV文件数据源

从CSV文件加载历史数据，保持与原有功能的兼容性
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union
from .base import BaseDataSource
from ..logger import log


class CSVDataSource(BaseDataSource):
    """CSV文件数据源"""
    
    def __init__(self, data_path: str, **kwargs):
        """
        初始化CSV数据源
        
        Args:
            data_path: CSV文件路径
        """
        super().__init__(**kwargs)
        self.data_path = data_path
        self._data = self._load_csv_data()
    
    def _load_csv_data(self) -> Dict[str, pd.DataFrame]:
        """从CSV文件加载数据"""
        try:
            df = pd.read_csv(self.data_path)
            
            # 查找日期时间列
            datetime_col = next((col for col in ['datetime', 'date', 'timestamp'] if col in df.columns), None)
            if datetime_col is None:
                log.warning("错误：找不到日期时间列（datetime/date/timestamp）")
                return {}
            
            # 设置日期时间索引
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df.set_index(datetime_col, inplace=True)
            
            # 按股票代码分组
            if 'security' not in df.columns:
                log.warning("错误：找不到security列")
                return {}
            
            # 分组并标准化数据
            data_dict = {}
            for security, group_data in df.groupby('security'):
                data_dict[security] = self._normalize_data(group_data, security)
            
            log.info(f"成功加载CSV数据，包含 {len(data_dict)} 只股票")
            return data_dict
            
        except FileNotFoundError:
            log.warning(f"错误：在 {self.data_path} 找不到数据文件")
            return {}
        except Exception as e:
            log.warning(f"错误：加载数据文件失败 - {e}")
            return {}
    
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
        
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        result = {}
        for security in securities:
            if security not in self._data:
                log.warning(f"股票 {security} 的数据不存在")
                continue
            
            # 获取指定时间范围的数据
            data = self._data[security]
            mask = (data.index >= start_dt) & (data.index <= end_dt)
            filtered_data = data.loc[mask]
            
            if filtered_data.empty:
                continue
            
            # 处理频率转换
            if frequency != '1d':
                filtered_data = self._convert_frequency(filtered_data, frequency)
            
            # 选择指定字段
            available_fields = [f for f in fields if f in filtered_data.columns]
            if available_fields:
                result[security] = filtered_data[available_fields].copy()
        
        return result
    
    def get_current_data(self, securities: Union[str, List[str]]) -> Dict[str, Dict]:
        """获取当前数据（模拟实时数据）"""
        if isinstance(securities, str):
            securities = [securities]
        
        current_data = {}
        for security in securities:
            if security not in self._data:
                log.warning(f"股票 {security} 的数据不存在")
                continue
            
            # 获取最新的数据
            latest_data = self._data[security].iloc[-1]
            
            # 模拟实时数据
            current_price = latest_data['close']
            spread = current_price * 0.001
            
            # 使用股票代码生成一致的随机数
            import hashlib
            hash_factor = int(hashlib.md5(security.encode()).hexdigest()[:8], 16) / 0xffffffff
            
            current_data[security] = {
                'last_price': current_price,
                'current_price': current_price,
                'high': latest_data['high'],
                'low': latest_data['low'],
                'open': latest_data['open'],
                'volume': latest_data['volume'],
                'bid1': current_price - spread,
                'bid2': current_price - spread * 2,
                'bid3': current_price - spread * 3,
                'bid4': current_price - spread * 4,
                'bid5': current_price - spread * 5,
                'ask1': current_price + spread,
                'ask2': current_price + spread * 2,
                'ask3': current_price + spread * 3,
                'ask4': current_price + spread * 4,
                'ask5': current_price + spread * 5,
                'bid1_volume': int(1000 + 5000 * hash_factor),
                'bid2_volume': int(800 + 4000 * hash_factor),
                'bid3_volume': int(600 + 3000 * hash_factor),
                'bid4_volume': int(400 + 2000 * hash_factor),
                'bid5_volume': int(200 + 1000 * hash_factor),
                'ask1_volume': int(1200 + 5500 * hash_factor),
                'ask2_volume': int(900 + 4500 * hash_factor),
                'ask3_volume': int(700 + 3500 * hash_factor),
                'ask4_volume': int(500 + 2500 * hash_factor),
                'ask5_volume': int(300 + 1500 * hash_factor),
                'pre_close': current_price * 0.98,
                'change': current_price * 0.02,
                'pct_change': 2.04,
                'amount': latest_data['volume'] * current_price / 10000,
                'turnover_rate': 2.5 + 5.0 * hash_factor,
                'high_limit': current_price * 0.98 * 1.1,
                'low_limit': current_price * 0.98 * 0.9,
                'amplitude': ((latest_data['high'] - latest_data['low']) / (current_price * 0.98)) * 100,
                'vwap': (latest_data['high'] + latest_data['low'] + current_price * 2) / 4,
            }
        
        return current_data
    
    def get_stock_list(self) -> List[str]:
        """获取股票列表"""
        return list(self._data.keys())
    
    def _convert_frequency(self, data: pd.DataFrame, frequency: str) -> pd.DataFrame:
        """转换数据频率（从日线生成分钟线）"""
        if frequency == '1d':
            return data
        
        # 解析频率
        freq_map = {
            '1m': 1, '5m': 5, '15m': 15, '30m': 30, '1h': 60
        }
        
        if frequency not in freq_map:
            log.warning(f"不支持的频率: {frequency}")
            return data
        
        minutes = freq_map[frequency]
        
        # 生成分钟级数据
        minute_data_list = []
        for _, row in data.iterrows():
            date = row.name.date()
            
            # 生成交易时间（9:30-11:30, 13:00-15:00）
            morning_times = pd.date_range(
                start=f"{date} 09:30:00",
                end=f"{date} 11:30:00",
                freq=f"{minutes}min"
            )[:-1]  # 排除11:30

            afternoon_times = pd.date_range(
                start=f"{date} 13:00:00",
                end=f"{date} 15:00:00",
                freq=f"{minutes}min"
            )
            
            minute_times = morning_times.union(afternoon_times)
            periods_per_day = len(minute_times)
            
            if periods_per_day == 0:
                continue
            
            # 生成分钟级OHLCV数据
            daily_range = row['high'] - row['low']
            daily_volume = row['volume']
            
            for i, minute_time in enumerate(minute_times):
                progress = i / periods_per_day
                
                # 使用时间戳生成一致的随机数
                np.random.seed(int(minute_time.timestamp()) % 10000)
                noise = np.random.normal(0, daily_range * 0.01)
                
                minute_close = max(row['low'], min(row['high'], 
                                 row['low'] + daily_range * progress + noise))
                minute_open = minute_close * (1 + np.random.normal(0, 0.001))
                minute_high = max(minute_open, minute_close, 
                                minute_close * (1 + abs(np.random.normal(0, 0.002))))
                minute_low = min(minute_open, minute_close,
                               minute_close * (1 - abs(np.random.normal(0, 0.002))))
                minute_volume = daily_volume / periods_per_day
                
                minute_data_list.append({
                    'open': minute_open,
                    'high': minute_high,
                    'low': minute_low,
                    'close': minute_close,
                    'volume': minute_volume,
                    'security': row['security']
                })
        
        if not minute_data_list:
            return data
        
        minute_df = pd.DataFrame(minute_data_list)
        minute_df.index = pd.to_datetime([item for sublist in 
                                        [morning_times.union(afternoon_times) 
                                         for _ in range(len(data))] 
                                        for item in sublist][:len(minute_data_list)])
        
        return minute_df
