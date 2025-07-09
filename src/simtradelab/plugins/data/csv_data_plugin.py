# -*- coding: utf-8 -*-
"""
CSV数据源插件

负责创建和管理CSV格式的股票数据，提供标准的数据访问接口。
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..base import BasePlugin, PluginConfig, PluginMetadata


class CSVDataPlugin(BasePlugin):
    """CSV数据源插件"""

    METADATA = PluginMetadata(
        name="csv_data_plugin",
        version="1.0.0",
        description="CSV Data Source Plugin for SimTradeLab",
        author="SimTradeLab",
        dependencies=[],
        tags=["data", "csv", "stock"],
        category="data_source",
        priority=20,  # 较高优先级，确保在适配器之前加载
    )

    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)

        # 数据存储目录
        self._data_dir = Path(
            self._config.config.get("data_dir", Path(__file__).parent / "data")
        )
        self._data_dir.mkdir(parents=True, exist_ok=True)

        # 数据缓存
        self._data_cache: Dict[str, pd.DataFrame] = {}
        self._cache_timeout = self._config.config.get("cache_timeout", 300)  # 5分钟
        self._cache_timestamps: Dict[str, datetime] = {}

    def _on_initialize(self) -> None:
        """初始化数据插件"""
        self._logger.info("Initializing CSV Data Plugin")

        # 确保基础数据文件存在
        self._ensure_base_data_files()

        self._logger.info(
            f"CSV Data Plugin initialized with data directory: {self._data_dir}"
        )

    def _ensure_base_data_files(self) -> None:
        """确保基础数据文件存在"""
        # 创建常用股票的历史数据文件
        common_stocks = [
            "000001.SZ",
            "000002.SZ",
            "000858.SZ",
            "600000.SH",
            "600036.SH",
            "600519.SH",
            "688001.SH",
            "300001.SZ",
        ]

        for stock in common_stocks:
            self._create_stock_data_file(stock)

    def _create_stock_data_file(self, security: str, days: int = 365) -> Path:
        """
        创建单个股票的历史数据文件

        Args:
            security: 证券代码
            days: 历史数据天数

        Returns:
            数据文件路径
        """
        file_path = self._data_dir / f"{security}.csv"

        # 如果文件已存在且不为空，不重新创建
        if file_path.exists() and file_path.stat().st_size > 0:
            return file_path

        # 生成日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")

        # 过滤掉周末（简单处理）
        date_range = date_range[date_range.dayofweek < 5]

        # 基础价格（根据股票代码生成）
        base_price = self._get_base_price(security)

        # 生成价格数据
        data = []
        current_price = base_price

        for date in date_range:
            # 价格变化（随机游走）
            price_change = np.random.normal(0, 0.02)  # 2%的日波动率
            current_price *= 1 + price_change

            # 确保价格不会过低
            if current_price < base_price * 0.3:
                current_price = base_price * 0.3

            # 生成OHLC数据
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            high_price = current_price * (1 + abs(np.random.normal(0, 0.01)))
            low_price = current_price * (1 - abs(np.random.normal(0, 0.01)))
            close_price = current_price

            # 确保OHLC关系正确
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            # 生成成交量
            volume = np.random.randint(10000, 1000000)

            data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "security": security,
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": volume,
                    "money": round(volume * close_price, 2),
                    "price": round(close_price, 2),
                }
            )

        # 保存到CSV文件
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)

        self._logger.info(f"Created data file for {security}: {file_path}")
        return file_path

    def _get_base_price(self, security: str) -> float:
        """
        根据证券代码获取基础价格

        Args:
            security: 证券代码

        Returns:
            基础价格
        """
        # 根据不同板块设置不同的基础价格
        if security.startswith("688"):  # 科创板
            return 50.0
        elif security.startswith("300"):  # 创业板
            return 30.0
        elif security.startswith("600"):  # 沪市主板
            return 20.0
        elif security.startswith("000"):  # 深市主板
            return 15.0
        else:
            return 10.0

    def get_history_data(
        self,
        security: str,
        count: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取历史数据

        Args:
            security: 证券代码
            count: 数据条数
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            历史数据DataFrame
        """
        # 检查缓存
        cache_key = f"{security}_{count}_{start_date}_{end_date}"
        if cache_key in self._data_cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if (
                cache_time
                and (datetime.now() - cache_time).seconds < self._cache_timeout
            ):
                return self._data_cache[cache_key].copy()

        file_path = self._data_dir / f"{security}.csv"

        # 如果文件不存在，创建它
        if not file_path.exists():
            self._create_stock_data_file(security)

        # 读取CSV文件
        df = pd.read_csv(file_path)
        df["date"] = pd.to_datetime(df["date"])

        # 按日期排序
        df = df.sort_values("date")

        # 应用日期过滤
        if start_date:
            df = df[df["date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date)]

        # 应用数量限制
        if count and len(df) > count:
            df = df.tail(count)

        # 缓存结果
        self._data_cache[cache_key] = df.copy()
        self._cache_timestamps[cache_key] = datetime.now()

        return df

    def get_current_price(self, security: str) -> float:
        """
        获取当前价格

        Args:
            security: 证券代码

        Returns:
            当前价格
        """
        try:
            df = self.get_history_data(security, count=1)
            if not df.empty:
                return float(df.iloc[-1]["close"])
        except Exception as e:
            self._logger.warning(f"Failed to get current price for {security}: {e}")

        # 如果无法获取历史数据，返回基础价格
        return self._get_base_price(security)

    def get_multiple_history_data(
        self,
        securities: List[str],
        count: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取多个证券的历史数据

        Args:
            securities: 证券代码列表
            count: 数据条数
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            合并的历史数据DataFrame
        """
        all_data = []

        for security in securities:
            df = self.get_history_data(security, count, start_date, end_date)
            if not df.empty:
                all_data.append(df)

        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            result = result.sort_values(["security", "date"])
            return result
        else:
            return pd.DataFrame()

    def get_market_snapshot(self, securities: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取市场快照数据

        Args:
            securities: 证券代码列表

        Returns:
            市场快照数据字典
        """
        snapshot = {}

        for security in securities:
            try:
                df = self.get_history_data(security, count=1)
                if not df.empty:
                    latest = df.iloc[-1]
                    snapshot[security] = {
                        "last_price": float(latest["close"]),
                        "pre_close": float(latest["close"])
                        * (1 + np.random.normal(0, 0.001)),
                        "open": float(latest["open"]),
                        "high": float(latest["high"]),
                        "low": float(latest["low"]),
                        "volume": int(latest["volume"]),
                        "money": float(latest["money"]),
                        "datetime": latest["date"],
                        "price": float(latest["close"]),  # PTrade兼容性
                    }
            except Exception as e:
                self._logger.warning(f"Failed to get snapshot for {security}: {e}")
                # 提供默认值
                base_price = self._get_base_price(security)
                snapshot[security] = {
                    "last_price": base_price,
                    "pre_close": base_price * (1 + np.random.normal(0, 0.001)),
                    "open": base_price,
                    "high": base_price,
                    "low": base_price,
                    "volume": 100000,
                    "money": base_price * 100000,
                    "datetime": datetime.now(),
                    "price": base_price,
                }

        return snapshot

    def create_custom_data_file(self, security: str, data: pd.DataFrame) -> Path:
        """
        创建自定义数据文件

        Args:
            security: 证券代码
            data: 数据DataFrame

        Returns:
            数据文件路径
        """
        file_path = self._data_dir / f"{security}.csv"
        data.to_csv(file_path, index=False)

        # 清除缓存
        self._clear_cache_for_security(security)

        self._logger.info(f"Created custom data file for {security}: {file_path}")
        return file_path

    def list_available_securities(self) -> List[str]:
        """
        列出可用的证券代码

        Returns:
            证券代码列表
        """
        securities = []
        for file_path in self._data_dir.glob("*.csv"):
            security = file_path.stem
            securities.append(security)

        return sorted(securities)

    def get_data_file_path(self, security: str) -> Path:
        """
        获取数据文件路径

        Args:
            security: 证券代码

        Returns:
            数据文件路径
        """
        return self._data_dir / f"{security}.csv"

    def _clear_cache_for_security(self, security: str) -> None:
        """清除指定证券的缓存"""
        keys_to_remove = [
            key for key in self._data_cache.keys() if key.startswith(security)
        ]
        for key in keys_to_remove:
            del self._data_cache[key]
            self._cache_timestamps.pop(key, None)

    def cleanup_old_data(self, days: int = 30) -> None:
        """
        清理旧数据文件

        Args:
            days: 保留天数
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        for file_path in self._data_dir.glob("*.csv"):
            if file_path.stat().st_mtime < cutoff_time.timestamp():
                file_path.unlink()
                self._logger.info(f"Cleaned up old data file: {file_path}")

    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._data_cache.clear()
        self._cache_timestamps.clear()
        self._logger.info("Cleared all data cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cached_items": len(self._data_cache),
            "cache_size_mb": sum(
                df.memory_usage(deep=True).sum() for df in self._data_cache.values()
            )
            / (1024 * 1024),
            "cache_timeout": self._cache_timeout,
            "oldest_cache_time": min(self._cache_timestamps.values())
            if self._cache_timestamps
            else None,
        }

    def _on_shutdown(self) -> None:
        """关闭时清理资源"""
        self.clear_cache()
        self._logger.info("CSV Data Plugin shutdown completed")
