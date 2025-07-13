# -*- coding: utf-8 -*-
"""
数据源插件基类

定义统一的数据源插件接口，所有数据源插件都应该继承此基类
"""

from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

import pandas as pd

from ..base import BasePlugin, PluginMetadata
from ..config.base_config import BasePluginConfig


class DataFrequency(Enum):
    """数据频率枚举"""

    TICK = "tick"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"


class MarketType(Enum):
    """市场类型枚举"""

    STOCK_CN = "stock_cn"  # 中国A股
    STOCK_US = "stock_us"  # 美股
    STOCK_HK = "stock_hk"  # 港股
    FUTURES = "futures"  # 期货
    OPTIONS = "options"  # 期权
    CRYPTO = "crypto"  # 数字货币


class BaseDataSourcePlugin(BasePlugin):
    """
    数据源插件基类

    所有数据源插件都必须继承此类并实现相应的抽象方法
    提供统一的数据访问接口，确保数据格式的一致性
    """

    def __init__(
        self, metadata: PluginMetadata, config: Optional[BasePluginConfig] = None
    ):
        super().__init__(metadata, config)
        self._supported_markets: Set[MarketType] = set()
        self._supported_frequencies: Set[DataFrequency] = set()
        self._data_delay: int = 0  # 数据延迟（秒）

    # ================================
    # 插件元数据方法
    # ================================

    @abstractmethod
    def get_supported_markets(self) -> Set[MarketType]:
        """
        获取支持的市场类型

        Returns:
            支持的市场类型集合
        """
        pass

    @abstractmethod
    def get_supported_frequencies(self) -> Set[DataFrequency]:
        """
        获取支持的数据频率

        Returns:
            支持的数据频率集合
        """
        pass

    @abstractmethod
    def get_data_delay(self) -> int:
        """
        获取数据延迟时间

        Returns:
            数据延迟时间（秒）
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查数据源是否可用

        Returns:
            True如果数据源可用，False否则
        """
        pass

    # ================================
    # 核心数据获取方法
    # ================================

    @abstractmethod
    def get_history_data(
        self,
        security: str,
        count: int = 30,
        frequency: Union[str, DataFrequency] = DataFrequency.DAILY,
        fields: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fq: str = "pre",
        include_now: bool = True,
        fill_gaps: bool = True,
    ) -> pd.DataFrame:
        """
        获取单个证券的历史数据

        Args:
            security: 证券代码
            count: 获取数据条数
            frequency: 数据频率
            fields: 需要获取的字段列表，默认为 ['open', 'high', 'low', 'close', 'volume']
            start_date: 开始日期（YYYY-MM-DD格式）
            end_date: 结束日期（YYYY-MM-DD格式）
            fq: 复权类型，'pre'前复权，'post'后复权，'none'不复权
            include_now: 是否包含当前时间点的数据
            fill_gaps: 是否填充数据缺口

        Returns:
            包含历史数据的DataFrame，索引为时间，列为字段名
            标准列：open, high, low, close, volume, amount
        """
        pass

    @abstractmethod
    def get_multiple_history_data(
        self,
        security_list: List[str],
        count: int = 30,
        frequency: Union[str, DataFrequency] = DataFrequency.DAILY,
        fields: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fq: str = "pre",
        include_now: bool = True,
        fill_gaps: bool = True,
        as_dict: bool = False,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        获取多个证券的历史数据

        Args:
            security_list: 证券代码列表
            count: 获取数据条数
            frequency: 数据频率
            fields: 需要获取的字段列表
            start_date: 开始日期
            end_date: 结束日期
            fq: 复权类型
            include_now: 是否包含当前时间点的数据
            fill_gaps: 是否填充数据缺口
            as_dict: 是否返回字典格式

        Returns:
            如果as_dict=False，返回MultiIndex DataFrame，(field, security)作为列
            如果as_dict=True，返回{security: DataFrame}格式的字典
        """
        pass

    @abstractmethod
    def get_snapshot(
        self,
        security_list: List[str],
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取证券的实时快照数据

        Args:
            security_list: 证券代码列表
            fields: 需要获取的字段列表，默认包含基本价格和成交量信息

        Returns:
            {security: {field: value}}格式的字典
            标准字段：last_price, open, high, low, close, volume, amount, bid1, ask1等
        """
        pass

    @abstractmethod
    def get_current_price(
        self,
        security_list: List[str],
    ) -> Dict[str, float]:
        """
        获取证券的当前价格

        Args:
            security_list: 证券代码列表

        Returns:
            {security: price}格式的字典
        """
        pass

    # ================================
    # 交易日历方法
    # ================================

    @abstractmethod
    def get_trading_day(
        self,
        date: str,
        offset: int = 0,
        market: Optional[MarketType] = None,
    ) -> str:
        """
        获取交易日

        Args:
            date: 基准日期（YYYY-MM-DD格式）
            offset: 偏移量，正数为向后，负数为向前
            market: 市场类型，用于确定交易日历

        Returns:
            交易日期字符串（YYYY-MM-DD格式）
        """
        pass

    @abstractmethod
    def get_all_trading_days(
        self,
        market: Optional[MarketType] = None,
    ) -> List[str]:
        """
        获取所有交易日

        Args:
            market: 市场类型

        Returns:
            交易日期列表
        """
        pass

    @abstractmethod
    def get_trading_days_range(
        self,
        start_date: str,
        end_date: str,
        market: Optional[MarketType] = None,
    ) -> List[str]:
        """
        获取指定日期范围内的交易日

        Args:
            start_date: 开始日期
            end_date: 结束日期
            market: 市场类型

        Returns:
            交易日期列表
        """
        pass

    @abstractmethod
    def is_trading_day(
        self,
        date: str,
        market: Optional[MarketType] = None,
    ) -> bool:
        """
        判断是否为交易日

        Args:
            date: 日期
            market: 市场类型

        Returns:
            True如果是交易日，False否则
        """
        pass

    # ================================
    # 市场状态和基本面数据方法
    # ================================

    @abstractmethod
    def check_limit_status(
        self,
        security_list: List[str],
        date: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        检查证券的涨跌停状态

        Args:
            security_list: 证券代码列表
            date: 查询日期，None表示当前日期

        Returns:
            {security: {limit_up: bool, limit_down: bool, limit_up_price: float,
                       limit_down_price: float, current_price: float}}格式的字典
        """
        pass

    @abstractmethod
    def get_fundamentals(
        self,
        security_list: List[str],
        table: str,
        fields: List[str],
        date: str,
    ) -> pd.DataFrame:
        """
        获取基本面数据

        Args:
            security_list: 证券代码列表
            table: 数据表名（如 'income', 'balance_sheet', 'cash_flow', 'indicator'）
            fields: 字段列表
            date: 查询日期

        Returns:
            包含基本面数据的DataFrame
        """
        pass

    @abstractmethod
    def get_security_info(
        self,
        security_list: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        获取证券基本信息

        Args:
            security_list: 证券代码列表

        Returns:
            {security: {name: str, market: str, type: str, listed_date: str,
                       delist_date: str}}格式的字典
        """
        pass

    # ================================
    # 可选的高级功能方法
    # ================================

    def get_tick_data(
        self,
        security: str,
        start_time: str,
        end_time: str,
    ) -> pd.DataFrame:
        """
        获取tick数据（可选实现）

        Args:
            security: 证券代码
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            tick数据DataFrame
        """
        raise NotImplementedError("Tick data not supported by this data source")

    def get_order_book(
        self,
        security: str,
        depth: int = 5,
    ) -> Dict[str, Any]:
        """
        获取委托单数据（可选实现）

        Args:
            security: 证券代码
            depth: 档位深度

        Returns:
            委托单数据
        """
        raise NotImplementedError("Order book data not supported by this data source")

    # ================================
    # 数据验证和转换辅助方法
    # ================================

    def _validate_security_code(self, security: str) -> bool:
        """验证证券代码格式"""
        # 基本验证，子类可以重写
        return isinstance(security, str) and len(security) > 0

    def _normalize_frequency(
        self, frequency: Union[str, DataFrequency]
    ) -> DataFrequency:
        """标准化频率参数"""
        if isinstance(frequency, str):
            # 尝试匹配常见的频率字符串
            freq_mapping = {
                "1d": DataFrequency.DAILY,
                "1w": DataFrequency.WEEKLY,
                "1M": DataFrequency.MONTHLY,
                "1m": DataFrequency.MINUTE_1,
                "5m": DataFrequency.MINUTE_5,
                "15m": DataFrequency.MINUTE_15,
                "30m": DataFrequency.MINUTE_30,
                "1h": DataFrequency.HOUR_1,
                "tick": DataFrequency.TICK,
            }
            return freq_mapping.get(frequency, DataFrequency.DAILY)
        return frequency

    def _standardize_dataframe_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化DataFrame列名"""
        # 标准化列名为小写
        column_mapping = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Amount": "amount",
            "Vol": "volume",
            "OHLCV": ["open", "high", "low", "close", "volume"],
        }

        df_copy = df.copy()
        for old_col, new_col in column_mapping.items():
            if old_col in df_copy.columns:
                if isinstance(new_col, list):
                    # 处理OHLCV这种复合列的情况
                    continue
                else:
                    df_copy = df_copy.rename(columns={old_col: new_col})

        return df_copy
