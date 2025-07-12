# -*- coding: utf-8 -*-
"""
Mock数据源插件

专门用于生成模拟数据，支持配置化的加载和移除。
在开发测试阶段使用，生产环境可以通过配置禁用。
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..base import BasePlugin, PluginConfig, PluginMetadata


class MockDataPlugin(BasePlugin):
    """Mock数据源插件"""

    # E4修复：移除AUTO_REGISTER，改为显式注册
    # AUTO_REGISTER = True  # 已移除，现在通过PluginManager显式注册

    # 默认配置
    DEFAULT_CONFIG = {
        "enabled": True,
        "seed": 42,
        "base_prices": {
            "STOCK_A": 10.0,  # 支持策略中的STOCK_A
            "000001.SZ": 15.0,
            "000002.SZ": 12.0,
            "000858.SZ": 25.0,
            "600000.SH": 8.0,
            "600036.SH": 35.0,
            "600519.SH": 1800.0,
            "688001.SH": 50.0,
            "300001.SZ": 30.0,
        },
        "volatility": 0.02,
        "trend": 0.0001,
    }

    METADATA = PluginMetadata(
        name="mock_data_plugin",
        version="1.0.0",
        description="Mock Data Source Plugin for Development and Testing",
        author="SimTradeLab",
        dependencies=[],
        tags=["data", "mock", "testing", "development"],
        category="data_source",
        priority=15,  # 中等优先级，低于CSV插件但高于默认插件
    )

    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)

        # 模拟数据配置
        self._enabled = self._config.config.get("enabled", True)
        self._seed = self._config.config.get("seed", 42)  # 随机种子确保可重复性
        self._base_prices = self._config.config.get(
            "base_prices",
            {
                "000001.SZ": 15.0,
                "000002.SZ": 12.0,
                "000858.SZ": 25.0,
                "600000.SH": 8.0,
                "600036.SH": 35.0,
                "600519.SH": 1800.0,
                "688001.SH": 50.0,
                "300001.SZ": 30.0,
            },
        )
        self._volatility = self._config.config.get("volatility", 0.02)  # 日波动率
        self._trend = self._config.config.get("trend", 0.0001)  # 趋势系数

        # 数据缓存
        self._data_cache: Dict[str, Any] = {}

        # 设置随机种子
        if self._seed is not None:
            np.random.seed(self._seed)
            random.seed(self._seed)

    def _on_initialize(self) -> None:
        """初始化Mock数据插件"""
        if not self._enabled:
            self._logger.info("Mock Data Plugin is disabled by configuration")
            return

        self._logger.info("Initializing Mock Data Plugin")
        self._logger.info(f"Random seed: {self._seed}")
        self._logger.info(
            f"Base prices configured for {len(self._base_prices)} securities"
        )
        self._logger.info(f"Volatility: {self._volatility}, Trend: {self._trend}")

    def is_enabled(self) -> bool:
        """检查插件是否启用"""
        return self._enabled

    def enable(self) -> None:
        """启用Mock数据插件"""
        self._enabled = True
        self._logger.info("Mock Data Plugin enabled")

    def disable(self) -> None:
        """禁用Mock数据插件"""
        self._enabled = False
        self._data_cache.clear()
        self._logger.info("Mock Data Plugin disabled and cache cleared")

    def _get_base_price(self, security: str) -> float:
        """
        根据证券代码获取基础价格

        Args:
            security: 证券代码

        Returns:
            基础价格
        """
        # 如果在配置中有指定价格，使用配置价格
        if security in self._base_prices:
            return self._base_prices[security]

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

    def _generate_price_series(
        self, security: str, days: int, start_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        生成价格序列

        Args:
            security: 证券代码
            days: 天数
            start_date: 起始日期

        Returns:
            价格数据列表
        """
        if not self._enabled:
            raise RuntimeError("Mock Data Plugin is disabled")

        # 生成日期范围
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        else:
            end_date = start_date + timedelta(days=days)

        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        # 过滤掉周末（简单处理）
        date_range = date_range[date_range.dayofweek < 5][:days]

        # 基础价格
        base_price = self._get_base_price(security)

        # 生成价格数据
        data = []
        current_price = base_price

        for i, date in enumerate(date_range):
            # 价格变化（随机游走 + 小趋势）
            price_change = np.random.normal(self._trend, self._volatility)
            current_price *= 1 + price_change

            # 确保价格不会过低
            if current_price < base_price * 0.1:
                current_price = base_price * 0.1

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

        return data

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
        if not self._enabled:
            raise RuntimeError("Mock Data Plugin is disabled")

        # 生成缓存键
        cache_key = f"{security}_{count}_{start_date}_{end_date}"

        # 检查缓存
        if cache_key in self._data_cache:
            return self._data_cache[cache_key].copy()

        # 解析日期
        start_dt = None
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")

        # 生成数据
        data = self._generate_price_series(security, count, start_dt)

        # 转换为DataFrame
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
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

        return df

    def get_current_price(self, security: str) -> float:
        """
        获取当前价格

        Args:
            security: 证券代码

        Returns:
            当前价格
        """
        if not self._enabled:
            raise RuntimeError("Mock Data Plugin is disabled")

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
        if not self._enabled:
            raise RuntimeError("Mock Data Plugin is disabled")

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

    def get_snapshot(self, securities: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取行情快照（PTrade API兼容）

        注意：该函数仅在交易模块可用

        Args:
            securities: 证券代码列表

        Returns:
            行情快照数据字典
        """
        if not self._enabled:
            raise RuntimeError("Mock Data Plugin is disabled")

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
                        "close": float(latest["close"]),  # 添加close字段
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
                    "close": base_price,  # 添加close字段
                    "volume": 100000,
                    "money": base_price * 100000,
                    "datetime": datetime.now(),
                    "price": base_price,
                }

        return snapshot

    def get_fundamentals(
        self, securities: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """
        获取基本面数据

        Args:
            securities: 股票代码列表
            table: 表格名称（如 income, balance_sheet, cash_flow）
            fields: 字段列表
            date: 查询日期

        Returns:
            包含基本面数据的DataFrame
        """
        if not self._enabled:
            raise RuntimeError("Mock Data Plugin is disabled")

        data = []
        for security in securities:
            row = {"code": security, "date": date}

            # 根据不同的表格和字段生成相应的数据
            for field in fields:
                if table == "income":  # 利润表
                    if field in ["revenue", "total_revenue"]:  # 营业收入
                        row[field] = random.uniform(1000000, 10000000)  # 1M-10M
                    elif field in ["net_profit", "net_income"]:  # 净利润
                        row[field] = random.uniform(100000, 1000000)  # 100K-1M
                    elif field in ["operating_profit"]:  # 营业利润
                        row[field] = random.uniform(200000, 1500000)  # 200K-1.5M
                    elif field in ["total_profit"]:  # 利润总额
                        row[field] = random.uniform(150000, 1200000)  # 150K-1.2M
                    elif field in ["operating_cost"]:  # 营业成本
                        row[field] = random.uniform(500000, 8000000)  # 500K-8M
                    else:
                        row[field] = random.uniform(0, 500000)

                elif table == "balance_sheet":  # 资产负债表
                    if field in ["total_assets"]:  # 总资产
                        row[field] = random.uniform(10000000, 100000000)  # 10M-100M
                    elif field in ["total_liab"]:  # 总负债
                        row[field] = random.uniform(5000000, 50000000)  # 5M-50M
                    elif field in ["total_equity"]:  # 股东权益
                        row[field] = random.uniform(3000000, 60000000)  # 3M-60M
                    elif field in ["current_assets"]:  # 流动资产
                        row[field] = random.uniform(2000000, 40000000)  # 2M-40M
                    elif field in ["current_liab"]:  # 流动负债
                        row[field] = random.uniform(1000000, 20000000)  # 1M-20M
                    elif field in ["fixed_assets"]:  # 固定资产
                        row[field] = random.uniform(3000000, 50000000)  # 3M-50M
                    else:
                        row[field] = random.uniform(0, 10000000)

                elif table == "cash_flow":  # 现金流量表
                    if field in ["operating_cash_flow"]:  # 经营现金流
                        row[field] = random.uniform(-1000000, 5000000)  # -1M-5M
                    elif field in ["investing_cash_flow"]:  # 投资现金流
                        row[field] = random.uniform(-3000000, 1000000)  # -3M-1M
                    elif field in ["financing_cash_flow"]:  # 筹资现金流
                        row[field] = random.uniform(-2000000, 2000000)  # -2M-2M
                    elif field in ["net_cash_flow"]:  # 现金净流量
                        row[field] = random.uniform(-1000000, 3000000)  # -1M-3M
                    else:
                        row[field] = random.uniform(-500000, 500000)

                else:  # 其他表格或比率数据
                    if field in ["pe_ratio"]:  # 市盈率
                        row[field] = random.uniform(10, 50)
                    elif field in ["pb_ratio"]:  # 市净率
                        row[field] = random.uniform(1, 10)
                    elif field in ["roe"]:  # 净资产收益率
                        row[field] = random.uniform(0.05, 0.25)
                    elif field in ["eps"]:  # 每股收益
                        row[field] = random.uniform(0.1, 5.0)
                    elif field in ["bps"]:  # 每股净资产
                        row[field] = random.uniform(3.0, 15.0)
                    elif field in ["debt_ratio"]:  # 资产负债率
                        row[field] = random.uniform(0.3, 0.8)
                    elif field in ["current_ratio"]:  # 流动比率
                        row[field] = random.uniform(1.0, 3.0)
                    elif field in ["quick_ratio"]:  # 速动比率
                        row[field] = random.uniform(0.5, 2.0)
                    else:
                        row[field] = random.uniform(0, 1000000)

            data.append(row)

        return pd.DataFrame(data)

    def list_available_securities(self) -> List[str]:
        """
        列出可用的证券代码

        Returns:
            证券代码列表
        """
        if not self._enabled:
            return []

        return list(self._base_prices.keys())

    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._data_cache.clear()
        self._logger.info("Cleared all mock data cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "enabled": self._enabled,
            "cached_items": len(self._data_cache),
            "cache_size_mb": sum(
                df.memory_usage(deep=True).sum() if hasattr(df, "memory_usage") else 0
                for df in self._data_cache.values()
            )
            / (1024 * 1024),
            "seed": self._seed,
            "securities_count": len(self._base_prices),
            "volatility": self._volatility,
            "trend": self._trend,
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        更新插件配置

        Args:
            new_config: 新的配置字典
        """
        self._enabled = new_config.get("enabled", self._enabled)
        self._seed = new_config.get("seed", self._seed)
        self._base_prices.update(new_config.get("base_prices", {}))
        self._volatility = new_config.get("volatility", self._volatility)
        self._trend = new_config.get("trend", self._trend)

        # 重新设置随机种子
        if self._seed is not None:
            np.random.seed(self._seed)
            random.seed(self._seed)

        # 清除缓存以使用新配置
        self.clear_cache()

        self._logger.info(
            f"Mock Data Plugin configuration updated: enabled={self._enabled}"
        )

    def _on_start(self) -> None:
        """启动Mock数据插件"""
        if self._enabled:
            self._logger.info("Mock Data Plugin started")
        else:
            self._logger.info("Mock Data Plugin is disabled, not starting")

    def _on_stop(self) -> None:
        """停止Mock数据插件"""
        self._logger.info("Mock Data Plugin stopped")

    def _on_shutdown(self) -> None:
        """关闭时清理资源"""
        self.clear_cache()
        self._logger.info("Mock Data Plugin shutdown completed")
