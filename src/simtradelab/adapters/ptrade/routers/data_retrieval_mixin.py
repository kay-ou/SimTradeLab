# -*- coding: utf-8 -*-
"""
数据获取API混入类

提供通用的数据获取API实现，支持时间参数化以适应不同路由器的需求
"""

import logging
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class DataRetrievalMixin:
    """数据获取API混入类"""

    def __init__(self) -> None:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)
        if not hasattr(self, "_data_plugin"):
            self._data_plugin = None

    def get_history(
        self,
        count: int,
        frequency: str = "1d",
        field: Union[str, List[str]] = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "money",
            "price",
        ],
        security_list: Optional[List[str]] = None,
        fq: Optional[str] = None,
        include: bool = False,
        fill: str = "nan",
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """获取历史行情数据"""
        # 获取股票池
        context = getattr(self, "context", None)
        if context and hasattr(context, "universe"):
            securities = (
                security_list or getattr(context, "universe", None) or ["000001.XSHE"]
            )
        else:
            securities = security_list or ["000001.XSHE"]

        if isinstance(field, str):
            field = [field]

        # 必须使用数据插件获取实际数据
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_history")

        try:
            # 使用数据插件获取多股票历史数据
            df = self._data_plugin.get_multiple_history_data(
                securities=securities,
                count=count,
                start_date=start_date,
                end_date=end_date,
            )

            # 如果请求字典格式，转换DataFrame为字典
            if is_dict:
                result = {}
                for security in securities:
                    result[security] = {}
                    security_data = (
                        df[df["security"] == security]
                        if "security" in df.columns
                        else df
                    )

                    for f in field:
                        if f in security_data.columns:
                            result[security][f] = security_data[f].tolist()
                        else:
                            result[security][f] = []
                return result
            else:
                # 过滤请求的字段
                available_fields = [f for f in field if f in df.columns]
                if available_fields:
                    df = (
                        df[["security", "date"] + available_fields]
                        if "security" in df.columns
                        else df[["date"] + available_fields]
                    )
                return df

        except Exception as e:
            # 数据插件失败时抛出异常，不使用fallback
            raise RuntimeError(f"Failed to get history data: {e}")

    def get_price(
        self,
        security: Union[str, List[str]],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> pd.DataFrame:
        """获取价格数据"""
        # 处理输入参数
        if isinstance(security, str):
            securities = [security]
        else:
            securities = security

        # 默认字段
        if fields is None:
            fields = ["open", "high", "low", "close", "volume"]
        elif isinstance(fields, str):
            fields = [fields]

        # 默认获取10个交易日数据
        if count is None:
            count = 10

        # 必须使用数据插件获取价格数据
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_price")

        try:
            # 使用数据插件获取多股票历史数据
            df = self._data_plugin.get_multiple_history_data(
                securities=securities,
                count=count,
                start_date=start_date,
                end_date=end_date,
            )

            # 过滤请求的字段
            available_fields = [f for f in fields if f in df.columns]
            if available_fields:
                columns_to_keep = ["security", "date"] + available_fields
                df = df[columns_to_keep]
                if not df.empty:
                    df.set_index(["security", "date"], inplace=True)
            else:
                # 如果没有请求的字段，创建空的DataFrame
                df = pd.DataFrame(columns=["security", "date"] + fields)
                df.set_index(["security", "date"], inplace=True)

            return df

        except Exception as e:
            # 数据插件失败时抛出异常，不使用fallback
            raise RuntimeError(f"Failed to get price data: {e}")

    def get_snapshot(self, security_list: List[str]) -> pd.DataFrame:
        """获取行情快照"""
        # 必须使用数据插件获取市场快照
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_snapshot")

        try:
            snapshot_data = self._data_plugin.get_market_snapshot(security_list)
            data = []
            for security in security_list:
                if security in snapshot_data:
                    snapshot = snapshot_data[security]
                    data.append(
                        {
                            "security": security,
                            "current_price": snapshot.get("last_price", 10.0),
                            "volume": snapshot.get("volume", 100000),
                            "timestamp": snapshot.get("datetime", pd.Timestamp.now()),
                        }
                    )
                else:
                    # 如果没有数据，抛出异常而不是返回默认值
                    raise ValueError(
                        f"No snapshot data available for security: {security}"
                    )
            return pd.DataFrame(data).set_index("security")
        except Exception as e:
            # 数据插件失败时抛出异常，不使用fallback
            raise RuntimeError(f"Failed to get snapshot data: {e}")

    def get_stock_info(self, security_list: List[str]) -> Dict[str, Any]:
        """获取股票基础信息"""
        stock_info = {}

        for security in security_list:
            # 尝试通过数据插件获取股票信息
            if self._data_plugin and hasattr(self._data_plugin, "get_stock_basic_info"):
                try:
                    info = self._data_plugin.get_stock_basic_info(security)
                    stock_info[security] = info
                    continue
                except Exception as e:
                    self._logger.warning(
                        f"Failed to get stock info from plugin for {security}: {e}"
                    )

            # 回退到基本信息生成
            if security.endswith(".XSHE"):  # 深圳证券交易所
                market = "SZSE"
                name = f"深圳股票{security[:6]}"
            elif security.endswith(".XSHG"):  # 上海证券交易所
                market = "SSE"
                name = f"上海股票{security[:6]}"
            else:
                market = "Unknown"
                name = f"股票{security}"

            stock_info[security] = {
                "symbol": security,
                "display_name": name,
                "name": name,
                "market": market,
                "type": "stock",
                "lot_size": 100,  # 最小交易单位
                "tick_size": 0.01,  # 最小价格变动单位
                "start_date": "2010-01-01",
                "end_date": "2099-12-31",
            }

        return stock_info

    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取财务数据信息"""
        # 尝试使用数据插件获取基本面数据
        if self._data_plugin:
            try:
                df = self._data_plugin.get_fundamentals(stocks, table, fields, date)
                if not df.empty:
                    return df
            except Exception as e:
                self._logger.warning(
                    f"Failed to get fundamentals data from plugin: {e}"
                )

        # 如果数据插件不可用或失败，返回空DataFrame
        columns = ["code", "date"] + fields
        return pd.DataFrame(columns=columns)
