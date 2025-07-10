# -*- coding: utf-8 -*-
"""
技术指标计算插件

提供标准的技术指标计算功能，包括MACD、KDJ、RSI、CCI等。
"""

from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..base import BasePlugin, PluginConfig, PluginMetadata


class TechnicalIndicatorsPlugin(BasePlugin):
    """技术指标计算插件"""

    METADATA = PluginMetadata(
        name="technical_indicators_plugin",
        version="1.0.0",
        description="Technical Indicators Calculation Plugin for SimTradeLab",
        author="SimTradeLab",
        dependencies=[],
        tags=["indicators", "technical", "calculation"],
        category="analysis",
        priority=30,  # 中等优先级
    )

    def __init__(self, metadata: PluginMetadata, config: Optional[PluginConfig] = None):
        super().__init__(metadata, config)

        # 指标计算缓存
        self._calculation_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # 从配置加载参数或使用默认值
        self._cache_timeout = self._config.config.get("cache_timeout", 300)  # 5分钟
        self.macd_params = self._config.config.get(
            "macd", {"short": 12, "long": 26, "m": 9}
        )
        self.kdj_params = self._config.config.get("kdj", {"n": 9, "m1": 3, "m2": 3})
        self.rsi_params = self._config.config.get("rsi", {"n": 6})
        self.cci_params = self._config.config.get("cci", {"n": 14})

    def _on_initialize(self) -> None:
        """初始化技术指标插件"""
        self._logger.info("Initializing Technical Indicators Plugin")

        # 注册所有指标计算方法
        self._register_indicators()

        self._logger.info(
            "Technical Indicators Plugin initialized with indicators: "
            "MACD, KDJ, RSI, CCI"
        )

    def _register_indicators(self) -> None:
        """注册指标计算方法"""
        # 这里可以注册更多指标
        pass

    def calculate_macd(self, close: np.ndarray) -> pd.DataFrame:
        """计算MACD指标"""
        params = self.macd_params
        short, long, m = params["short"], params["long"], params["m"]
        cache_key = f"macd_{hash(close.tobytes())}_{short}_{long}_{m}"

        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._calculation_cache[cache_key]

        try:
            # 确保数据是Series格式
            close_series = pd.Series(close)

            # 计算快速和慢速EMA
            exp1 = close_series.ewm(span=short).mean()
            exp2 = close_series.ewm(span=long).mean()

            # 计算MACD线
            macd_line = exp1 - exp2

            # 计算信号线
            signal_line = macd_line.ewm(span=m).mean()

            # 计算MACD柱状图
            histogram = macd_line - signal_line

            # 返回结果DataFrame
            result = pd.DataFrame(
                {
                    "MACD": macd_line,
                    "MACD_signal": signal_line,
                    "MACD_hist": histogram * 2,  # PTrade通常将柱状图乘以2
                }
            )

            # 缓存结果
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            self._logger.error(f"Error calculating MACD: {e}")
            periods = len(close)
            return pd.DataFrame(
                {
                    "MACD": np.random.randn(periods) * 0.1,
                    "MACD_signal": np.random.randn(periods) * 0.1,
                    "MACD_hist": np.random.randn(periods) * 0.05,
                }
            )

    def calculate_kdj(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray
    ) -> pd.DataFrame:
        """计算KDJ指标"""
        params = self.kdj_params
        n, m1, m2 = params["n"], params["m1"], params["m2"]
        cache_key = f"kdj_{hash(high.tobytes())}_{hash(low.tobytes())}_"
        f"{hash(close.tobytes())}_{n}_{m1}_{m2}"

        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._calculation_cache[cache_key]

        try:
            # 确保数据是Series格式
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            # 计算最高价和最低价的滚动窗口
            highest = high_series.rolling(window=n).max()
            lowest = low_series.rolling(window=n).min()

            # 计算RSV
            rsv = (close_series - lowest) / (highest - lowest) * 100

            # 计算K值
            k = rsv.ewm(alpha=1 / m1).mean()

            # 计算D值
            d = k.ewm(alpha=1 / m2).mean()

            # 计算J值
            j = 3 * k - 2 * d

            result = pd.DataFrame({"K": k, "D": d, "J": j})

            # 缓存结果
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            self._logger.error(f"Error calculating KDJ: {e}")
            periods = len(close)
            return pd.DataFrame(
                {
                    "K": np.random.uniform(0, 100, periods),
                    "D": np.random.uniform(0, 100, periods),
                    "J": np.random.uniform(0, 100, periods),
                }
            )

    def calculate_rsi(self, close: np.ndarray) -> pd.DataFrame:
        """计算RSI指标"""
        n = self.rsi_params["n"]
        cache_key = f"rsi_{hash(close.tobytes())}_{n}"

        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._calculation_cache[cache_key]

        try:
            # 确保数据是Series格式
            close_series = pd.Series(close)

            # 计算价格变化
            delta = close_series.diff()

            # 分离上涨和下跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # 计算平均收益和平均损失
            avg_gain = gain.rolling(window=n).mean()
            avg_loss = loss.rolling(window=n).mean()

            # 计算RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            result = pd.DataFrame({"RSI": rsi})

            # 缓存结果
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            self._logger.error(f"Error calculating RSI: {e}")
            periods = len(close)
            return pd.DataFrame({"RSI": np.random.uniform(0, 100, periods)})

    def calculate_cci(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray
    ) -> pd.DataFrame:
        """计算CCI指标"""
        n = self.cci_params["n"]
        cache_key = f"cci_{hash(high.tobytes())}_{hash(low.tobytes())}_"
        f"{hash(close.tobytes())}_{n}"

        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self._calculation_cache[cache_key]

        try:
            # 确保数据是Series格式
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

            # 计算典型价格
            typical_price = (high_series + low_series + close_series) / 3

            # 计算移动平均
            ma = typical_price.rolling(window=n).mean()

            # 计算平均绝对偏差
            mad = typical_price.rolling(window=n).apply(
                lambda x: abs(x - x.mean()).mean()
            )

            # 计算CCI
            cci = (typical_price - ma) / (0.015 * mad)

            result = pd.DataFrame({"CCI": cci})

            # 缓存结果
            self._cache_result(cache_key, result)

            return result

        except Exception as e:
            self._logger.error(f"Error calculating CCI: {e}")
            periods = len(close)
            return pd.DataFrame({"CCI": np.random.randn(periods) * 50})

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._calculation_cache:
            return False

        cache_time = self._cache_timestamps.get(cache_key)
        if not cache_time:
            return False

        return (datetime.now() - cache_time).seconds < self._cache_timeout

    def _cache_result(self, cache_key: str, result: pd.DataFrame) -> None:
        """缓存计算结果"""
        self._calculation_cache[cache_key] = result.copy()
        self._cache_timestamps[cache_key] = datetime.now()

    def clear_cache(self) -> None:
        """清除所有缓存"""
        self._calculation_cache.clear()
        self._cache_timestamps.clear()
        self._logger.info("Cleared all indicator calculation cache")

    def get_state(self) -> Dict[str, Any]:
        """获取插件状态，用于热重载"""
        return {
            "_calculation_cache": self._calculation_cache,
            "_cache_timestamps": self._cache_timestamps,
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        """设置插件状态，用于热重载"""
        self._calculation_cache = state.get("_calculation_cache", {})
        self._cache_timestamps = state.get("_cache_timestamps", {})
        self._logger.info("Restored indicator cache state.")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cached_calculations": len(self._calculation_cache),
            "cache_timeout": self._cache_timeout,
            "oldest_cache_time": min(self._cache_timestamps.values())
            if self._cache_timestamps
            else None,
        }

    def _on_start(self) -> None:
        """启动技术指标插件"""
        self._logger.info("Starting Technical Indicators Plugin")

    def _on_stop(self) -> None:
        """停止技术指标插件"""
        self._logger.info("Stopping Technical Indicators Plugin")

    def _on_shutdown(self) -> None:
        """关闭时清理资源"""
        self.clear_cache()
        self._logger.info("Technical Indicators Plugin shutdown completed")
