# -*- coding: utf-8 -*-
"""
AkShare 数据源插件

基于 AkShare 库提供中国市场金融数据。
"""
from typing import Any

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Union

import akshare as ak
import pandas as pd
from pydantic import Field, field_validator

from simtradelab.plugins.config.base_config import BasePluginConfig
from simtradelab.plugins.data.base_data_source import (
    BaseDataSourcePlugin,
    DataFrequency,
    MarketType,
)

# 设置日志记录器
logger = logging.getLogger(__name__)


class AkShareDataPluginConfig(BasePluginConfig):
    """
    AkShare数据源插件的配置模型。

    此配置模型使用Pydantic进行验证，确保所有配置项的类型和值都符合预期。
    """

    api_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="调用AkShare API的超时时间（秒）。",
    )
    cache_enabled: bool = Field(default=True, description="是否为获取的数据启用本地缓存。")
    start_date: str = Field(..., description="获取历史数据的默认开始日期 (YYYY-MM-DD)。")
    end_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="获取历史数据的默认结束日期 (YYYY-MM-DD)。",
    )

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: str, info) -> str:
        """验证结束日期是否在开始日期之后。"""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("配置错误: end_date 必须在 start_date 之后。")
        return v


class AkShareDataSource(BaseDataSourcePlugin):
    """
    使用 AkShare 作为数据源的插件。

    实现了 BaseDataSourcePlugin 定义的标准接口，提供中国市场的股票数据。
    """

    def __init__(self, metadata, config: AkShareDataPluginConfig):
        super().__init__(metadata, config)
        self.akshare_config: AkShareDataPluginConfig = config

    def _on_initialize(self) -> None:
        """
        初始化插件。
        可以在这里进行一些预加载或连接检查。
        """
        logger.info("AkShare数据源插件已初始化。")
        if not self.is_available():
            logger.warning("AkShare服务当前可能不可用，请检查网络连接。")

    def _on_start(self) -> None:
        """插件启动时调用。"""
        logger.info("AkShare数据源插件已启动。")

    def _on_stop(self) -> None:
        """插件停止时调用。"""
        logger.info("AkShare数据源插件已停止。")
    def get_supported_markets(self) -> Set[MarketType]:
        """返回支持的市场类型。"""
        return {MarketType.STOCK_CN}

    def get_supported_frequencies(self) -> Set[DataFrequency]:
        """返回支持的数据频率。"""
        return {DataFrequency.DAILY, DataFrequency.WEEKLY, DataFrequency.MONTHLY}

    def get_data_delay(self) -> int:
        """返回数据延迟（秒）。对于AkShare，通常是日内延迟。"""
        return 0  # 假设是日线数据，无延迟

    def is_available(self) -> bool:
        """检查AkShare服务是否可用。"""
        # TODO: 找到一个可靠的AkShare API来检查服务状态
        logger.warning("is_available() 暂时返回 True，需要一个可靠的API进行检查。")
        return True

    def get_history_data(
        self,
        security: str,
        count: int = 30,
        frequency: Union[str, DataFrequency] = DataFrequency.DAILY,
        fields: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fq: str = "qfq",
        **kwargs,
    ) -> pd.DataFrame:
        """
        获取单个证券的历史K线数据。

        Args:
            security (str): 证券代码, e.g., '000001'
            frequency (Union[str, DataFrequency]): 数据频率, 支持 'daily', 'weekly', 'monthly'
            start_date (Optional[str]): 开始日期, 格式 'YYYYMMDD'
            end_date (Optional[str]): 结束日期, 格式 'YYYYMMDD'
            fq (str): 复权类型, 'qfq' (前复权), 'hfq' (后复权), '' (不复权)

        Returns:
            pd.DataFrame: 包含历史数据的DataFrame，列已标准化。
        """
        # 参数映射和验证
        period_map = {
            DataFrequency.DAILY: "daily",
            DataFrequency.WEEKLY: "weekly",
            DataFrequency.MONTHLY: "monthly",
        }
        normalized_freq = self._normalize_frequency(frequency)
        if normalized_freq not in period_map:
            raise ValueError(f"不支持的数据频率: {frequency}")

        # 使用配置中的默认日期（如果未提供）
        start = (start_date or self.akshare_config.start_date).replace("-", "")
        end = (end_date or self.akshare_config.end_date).replace("-", "")

        try:
            logger.debug(
                f"正在从AkShare获取数据: security={security}, period={period_map[normalized_freq]}, "
                f"start_date={start}, end_date={end}, fq={fq}"
            )
            hist_df = ak.stock_zh_a_hist(
                symbol=security,
                period=period_map[normalized_freq],
                start_date=start,
                end_date=end,
                adjust=fq,
            )

            if hist_df.empty:
                logger.warning(f"未能获取到证券 {security} 的数据。")
                return pd.DataFrame()

            # 标准化列名
            column_mapping = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "pct_chg",
                "涨跌额": "change",
                "换手率": "turnover",
            }
            hist_df = hist_df.rename(columns=column_mapping)
            hist_df["date"] = pd.to_datetime(hist_df["date"])
            hist_df = hist_df.set_index("date")

            # 选择需要的字段
            if fields:
                return hist_df[[col for col in fields if col in hist_df.columns]]
            return hist_df

        except Exception as e:
            logger.error(f"使用AkShare获取历史数据时出错 (security: {security}): {e}")
            # 可选：在此处发布一个 com.simtradelab.data.error 事件
            return pd.DataFrame()

    def get_multiple_history_data(
        self, security_list: List[str], **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        获取多个证券的历史数据。
        注意：AkShare没有批量接口，所以我们循环调用单个接口。
        """
        all_data = {}
        for security in security_list:
            all_data[security] = self.get_history_data(security, **kwargs)
        return all_data

    def get_snapshot(
        self, security_list: List[str], **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """AkShare主要提供历史数据，实时快照功能有限且可能不稳定。"""
        logger.warning("AkShare插件不完全支持实时快照功能。")
        raise NotImplementedError("AkShare插件不完全支持实时快照功能。")

    def get_current_price(self, security_list: List[str]) -> Dict[str, float]:
        """
        获取证券的当前价格。
        使用stock_zh_a_spot_em接口获取实时行情。
        """
        try:
            spot_df = ak.stock_zh_a_spot_em()
            prices = {}
            for security in security_list:
                price_data = spot_df[spot_df["代码"] == security]
                if not price_data.empty:
                    prices[security] = price_data["最新价"].iloc[0]
                else:
                    logger.warning(f"无法获取证券 {security} 的当前价格。")
            return prices
        except Exception as e:
            logger.error(f"使用AkShare获取当前价格时出错: {e}")
            return {}

    def get_all_trading_days(self, market: Optional[MarketType] = None) -> List[str]:
        """获取所有交易日。"""
        # TODO: 找到一个可靠的AkShare API来获取交易日历
        logger.warning("get_all_trading_days() 暂时返回空列表，需要一个可靠的API进行实现。")
        return []

    # --- 以下为当前版本暂不实现的方法 ---

    def get_trading_day(self, date: str, offset: int = 0, **kwargs) -> str:
        raise NotImplementedError("get_trading_day 方法尚未在AkShare插件中实现。")

    def get_trading_days_range(
        self, start_date: str, end_date: str, **kwargs
    ) -> List[str]:
        raise NotImplementedError("get_trading_days_range 方法尚未在AkShare插件中实现。")

    def is_trading_day(self, date: str, **kwargs) -> bool:
        raise NotImplementedError("is_trading_day 方法尚未在AkShare插件中实现。")

    def check_limit_status(
        self, security_list: List[str], **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        raise NotImplementedError("check_limit_status 方法尚未在AkShare插件中实现。")

    def get_fundamentals(
        self, security_list: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        raise NotImplementedError("get_fundamentals 方法尚未在AkShare插件中实现。")

    def get_security_info(
        self, security_list: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        raise NotImplementedError("get_security_info 方法尚未在AkShare插件中实现。")
