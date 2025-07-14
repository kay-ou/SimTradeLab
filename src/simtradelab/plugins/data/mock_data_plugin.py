# -*- coding: utf-8 -*-
"""
Mock数据源插件

专门用于生成模拟数据，支持配置化的加载和移除。
在开发测试阶段使用，生产环境可以通过配置禁用。
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np
import pandas as pd

from ..base import PluginMetadata, PluginState
from .base_data_source import BaseDataSourcePlugin, DataFrequency, MarketType
from .config import MockDataPluginConfig


class MockDataPlugin(BaseDataSourcePlugin):
    """Mock数据源插件"""

    # 默认配置
    DEFAULT_CONFIG = {
        "enabled": True,
        "seed": 42,
        "base_prices": {
            "STOCK_A": 10.0,  # 支持策略中的STOCK_A
            "000001.SZ": 15.0,
            "000002.SZ": 12.0,
            "600000.SH": 8.0,
            "600036.SH": 35.0,
        },
        "volatility": 0.02,  # 日波动率
        "trend": 0.0001,  # 趋势系数
    }

    # 插件元数据
    METADATA = PluginMetadata(
        name="mock_data_plugin",
        version="1.0.0",
        description="Mock数据源插件，用于生成模拟数据",
        author="SimTradeLab Team",
        dependencies=[],
        tags=["data", "mock", "testing", "development"],
        category="data_source",
        priority=15,  # 中等优先级，低于CSV插件但高于默认插件
    )

    # E8修复：定义配置模型类
    config_model = MockDataPluginConfig

    def __init__(
        self, metadata: PluginMetadata, config: Optional[MockDataPluginConfig] = None
    ):
        super().__init__(metadata, config)

        # E8修复：通过类型安全的配置对象访问参数
        if config:
            self._enabled = config.enabled
            self._seed = config.seed
            self._base_prices = config.base_prices
            self._volatility = config.volatility
            self._trend = config.trend
            self._daily_volatility_factor = float(config.daily_volatility_factor)
            self._volume_range = config.volume_range
        else:
            # 使用默认配置
            default_config = MockDataPluginConfig()
            self._enabled = default_config.enabled
            self._seed = default_config.seed
            self._base_prices = default_config.base_prices
            self._volatility = float(default_config.volatility)
            self._trend = float(default_config.trend)
            self._daily_volatility_factor = float(
                default_config.daily_volatility_factor
            )
            self._volume_range = default_config.volume_range

        # 设置支持的市场和频率
        self._supported_markets = {MarketType.STOCK_CN}
        self._supported_frequencies = {DataFrequency.DAILY, DataFrequency.MINUTE_1}
        self._data_delay = 0

        # 随机种子
        random.seed(self._seed)
        np.random.seed(self._seed)

        # 数据缓存
        self._data_cache: Dict[str, pd.DataFrame] = {}

        self._logger.info(
            "MockDataPlugin initialized with base prices: %s", self._base_prices
        )

    # ================================
    # BaseDataSourcePlugin 抽象方法实现
    # ================================

    def get_supported_markets(self) -> Set[MarketType]:
        """获取支持的市场类型"""
        return self._supported_markets.copy()

    def get_supported_frequencies(self) -> Set[DataFrequency]:
        """获取支持的数据频率"""
        return self._supported_frequencies.copy()

    def get_data_delay(self) -> int:
        """获取数据延迟时间（秒）"""
        return self._data_delay

    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self._enabled

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
        """获取单个证券的历史数据"""
        if not self._enabled or count <= 0:
            return pd.DataFrame()

        # 标准化频率
        freq = self._normalize_frequency(frequency)

        # 生成模拟数据
        base_price = self._base_prices.get(security, 10.0)

        # 创建日期范围
        if end_date:
            end_dt = pd.to_datetime(end_date)
        else:
            end_dt = datetime.now() if include_now else datetime.now() - timedelta(days=1)

        if freq == DataFrequency.DAILY:
            start_dt = end_dt - timedelta(days=count)
            date_range = pd.date_range(start=start_dt, end=end_dt, freq="D")
        else:
            start_dt = end_dt - timedelta(minutes=count)
            date_range = pd.date_range(start=start_dt, end=end_dt, freq="min")

        # 生成价格序列
        prices = []
        current_price = base_price

        for _ in range(len(date_range)):
            # 随机游走模型
            change = np.random.normal(float(self._trend), float(self._volatility))
            current_price *= 1 + change
            prices.append(current_price)

        # 创建OHLC数据
        df_data = []
        for i, (date, close) in enumerate(zip(date_range, prices)):
            # 模拟日内波动
            daily_volatility = float(self._volatility) * 0.5
            high = close * (1 + abs(np.random.normal(0, daily_volatility)))
            low = close * (1 - abs(np.random.normal(0, daily_volatility)))
            open_price = prices[i - 1] if i > 0 else close
            volume = int(
                np.random.uniform(self._volume_range["min"], self._volume_range["max"])
            )

            df_data.append(
                {
                    "date": date,
                    "open": open_price,
                    "high": max(open_price, close, high),
                    "low": min(open_price, close, low),
                    "close": close,
                    "volume": volume,
                    "amount": volume * close,
                }
            )

        df = pd.DataFrame(df_data)
        df.set_index("date", inplace=True)

        # 只返回最后count条记录
        return df.tail(count)

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
        """获取多个证券的历史数据"""
        if as_dict:
            result = {}
            for security in security_list:
                result[security] = self.get_history_data(
                    security,
                    count,
                    frequency,
                    fields,
                    start_date,
                    end_date,
                    fq,
                    include_now,
                    fill_gaps,
                )
            return result
        else:
            # 返回合并的DataFrame
            all_data = []
            for security in security_list:
                data = self.get_history_data(
                    security,
                    count,
                    frequency,
                    fields,
                    start_date,
                    end_date,
                    fq,
                    include_now,
                    fill_gaps,
                )
                data["security"] = security
                all_data.append(data.reset_index())

            if all_data:
                return pd.concat(all_data, ignore_index=True)
            else:
                return pd.DataFrame()

    def get_current_price(self, security_list: List[str]) -> Dict[str, float]:
        """获取证券的当前价格"""
        if not self._enabled:
            return {}
        prices = {}
        for security in security_list:
            base_price = self._base_prices.get(security, 10.0)
            # 添加少量随机波动
            current_price = base_price * (1 + np.random.normal(0, 0.01))
            prices[security] = round(current_price, 2)
        return prices

    def get_snapshot(
        self, security_list: List[str], fields: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """获取证券的实时快照数据"""
        if not self._enabled:
            return {}
        snapshot = {}
        for security in security_list:
            base_price = self._base_prices.get(security, 10.0)
            current_price = base_price * (1 + np.random.normal(0, 0.01))

            snapshot[security] = {
                "last_price": round(current_price, 2),
                "open": round(current_price * 0.99, 2),
                "high": round(current_price * 1.02, 2),
                "low": round(current_price * 0.98, 2),
                "close": round(current_price, 2),
                "volume": int(np.random.uniform(1000, 10000)),
                "amount": round(current_price * np.random.uniform(1000, 10000), 2),
                "bid1": round(current_price * 0.999, 2),
                "ask1": round(current_price * 1.001, 2),
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        return snapshot

    # ================================
    # 交易日历方法
    # ================================

    def get_trading_day(
        self, date: str, offset: int = 0, market: Optional[MarketType] = None
    ) -> str:
        """获取交易日"""
        dt = datetime.strptime(date, "%Y-%m-%d")
        # 简单实现：跳过周末
        while offset != 0:
            if offset > 0:
                dt += timedelta(days=1)
                if dt.weekday() < 5:  # 周一到周五
                    offset -= 1
            else:
                dt -= timedelta(days=1)
                if dt.weekday() < 5:  # 周一到周五
                    offset += 1
        return dt.strftime("%Y-%m-%d")

    def get_all_trading_days(self, market: Optional[MarketType] = None) -> List[str]:
        """获取所有交易日"""
        # 返回最近一年的交易日
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        trading_days = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 周一到周五
                trading_days.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        return trading_days

    def get_trading_days_range(
        self, start_date: str, end_date: str, market: Optional[MarketType] = None
    ) -> List[str]:
        """获取指定日期范围内的交易日"""
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        trading_days = []
        current_date = start_dt
        while current_date <= end_dt:
            if current_date.weekday() < 5:  # 周一到周五
                trading_days.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        return trading_days

    def is_trading_day(self, date: str, market: Optional[MarketType] = None) -> bool:
        """判断是否为交易日"""
        dt = datetime.strptime(date, "%Y-%m-%d")
        return dt.weekday() < 5  # 周一到周五

    # ================================
    # 市场状态和基本面数据方法
    # ================================

    def check_limit_status(
        self, security_list: List[str], date: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """检查证券的涨跌停状态"""
        limit_status = {}
        for security in security_list:
            current_price = self._base_prices.get(security, 10.0)
            limit_up_price = current_price * 1.1  # 10%涨停
            limit_down_price = current_price * 0.9  # 10%跌停

            limit_status[security] = {
                "limit_up": False,  # 模拟数据通常不涨跌停
                "limit_down": False,
                "limit_up_price": round(limit_up_price, 2),
                "limit_down_price": round(limit_down_price, 2),
                "current_price": round(current_price, 2),
            }
        return limit_status

    def get_fundamentals(
        self, security_list: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取基本面数据"""
        # 生成模拟基本面数据
        data = []
        for security in security_list:
            row: Dict[str, Any] = {"code": security, "date": date}
            for field in fields:
                if field == "revenue":
                    row[field] = np.random.uniform(1e6, 1e9)  # 营收
                elif field == "net_profit":
                    row[field] = np.random.uniform(1e5, 1e8)  # 净利润
                elif field == "total_assets":
                    row[field] = np.random.uniform(1e7, 1e10)  # 总资产
                else:
                    row[field] = np.random.uniform(0, 100)  # 其他指标
            data.append(row)

        return pd.DataFrame(data)

    def get_security_info(self, security_list: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取证券基本信息"""
        info = {}
        for security in security_list:
            if security.endswith(".SZ"):
                market = "SZSE"
            elif security.endswith(".SH"):
                market = "SSE"
            else:
                market = "MOCK"

            info[security] = {
                "name": f"模拟股票{security}",
                "market": market,
                "type": "stock",
                "listed_date": "2020-01-01",
                "delist_date": None,
            }
        return info

    # ================================
    # BasePlugin 抽象方法实现
    # ================================

    def _on_initialize(self) -> None:
        """插件初始化时调用"""
        self._logger.info("MockDataPlugin initializing...")

    def _on_start(self) -> None:
        """插件启动时调用"""
        self._logger.info("MockDataPlugin started")

    def _on_stop(self) -> None:
        """插件停止时调用"""
        self._logger.info("MockDataPlugin stopped")

    # ================================
    # 插件管理方法
    # ================================

    def initialize(self) -> None:
        """初始化插件"""
        super().initialize()  # 调用父类方法来正确管理插件状态
        self._logger.info("MockDataPlugin initialized")

    def shutdown(self) -> None:
        """关闭插件"""
        super().shutdown()
        self._data_cache.clear()
        self._logger.info("MockDataPlugin shutdown")

    def is_enabled(self) -> bool:
        """检查插件是否启用"""
        return self._enabled

    def enable(self) -> None:
        """启用插件"""
        self._enabled = True
        self._logger.info("MockDataPlugin enabled")

    def disable(self) -> None:
        """禁用插件"""
        self._enabled = False
        self._logger.info("MockDataPlugin disabled")
