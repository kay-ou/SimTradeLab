# -*- coding: utf-8 -*-
"""
股票信息获取API混入类

提供通用的股票信息获取API实现，可被各种路由器继承使用
"""

import logging
from typing import Any, Dict, List

import pandas as pd


class StockInfoMixin:
    """股票信息获取API混入类"""

    def __init__(self) -> None:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)
        if not hasattr(self, "_data_plugin"):
            self._data_plugin = None

    def get_stock_name(self, security: str) -> str:
        """获取股票名称"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_stock_name")

        try:
            if hasattr(self._data_plugin, "get_stock_name"):
                return self._data_plugin.get_stock_name(security)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_stock_name"
                )
        except Exception as e:
            self._logger.error(f"Error getting stock name for {security}: {e}")
            raise RuntimeError(f"Failed to get stock name for {security}: {e}")

    def get_stock_status(self, security: str) -> Dict[str, Any]:
        """获取股票状态信息"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_stock_status")

        try:
            if hasattr(self._data_plugin, "get_stock_status"):
                return self._data_plugin.get_stock_status(security)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_stock_status"
                )
        except Exception as e:
            self._logger.error(f"Error getting stock status for {security}: {e}")
            raise RuntimeError(f"Failed to get stock status for {security}: {e}")

    def get_stock_exrights(self, security: str) -> pd.DataFrame:
        """获取股票除权除息信息"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_stock_exrights")

        try:
            if hasattr(self._data_plugin, "get_stock_exrights"):
                return self._data_plugin.get_stock_exrights(security)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_stock_exrights"
                )
        except Exception as e:
            self._logger.error(f"Error getting stock exrights for {security}: {e}")
            raise RuntimeError(f"Failed to get stock exrights for {security}: {e}")

    def get_stock_blocks(self, security: str) -> List[str]:
        """获取股票所属板块信息"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_stock_blocks")

        try:
            if hasattr(self._data_plugin, "get_stock_blocks"):
                return self._data_plugin.get_stock_blocks(security)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_stock_blocks"
                )
        except Exception as e:
            self._logger.error(f"Error getting stock blocks for {security}: {e}")
            raise RuntimeError(f"Failed to get stock blocks for {security}: {e}")

    def get_index_stocks(self, index_code: str) -> List[str]:
        """获取指数成份股"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_index_stocks")

        try:
            if hasattr(self._data_plugin, "get_index_stocks"):
                return self._data_plugin.get_index_stocks(index_code)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_index_stocks"
                )
        except Exception as e:
            self._logger.error(f"Error getting index stocks for {index_code}: {e}")
            raise RuntimeError(f"Failed to get index stocks for {index_code}: {e}")

    def get_industry_stocks(self, industry_code: str) -> List[str]:
        """获取行业成份股"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_industry_stocks")

        try:
            if hasattr(self._data_plugin, "get_industry_stocks"):
                return self._data_plugin.get_industry_stocks(industry_code)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_industry_stocks"
                )
        except Exception as e:
            self._logger.error(
                f"Error getting industry stocks for {industry_code}: {e}"
            )
            raise RuntimeError(
                f"Failed to get industry stocks for {industry_code}: {e}"
            )

    def get_Ashares(self, date: str) -> List[str]:
        """获取指定日期A股代码列表"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_Ashares")

        try:
            if hasattr(self._data_plugin, "get_Ashares"):
                return self._data_plugin.get_Ashares(date)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_Ashares"
                )
        except Exception as e:
            self._logger.error(f"Error getting A-shares for date {date}: {e}")
            raise RuntimeError(f"Failed to get A-shares for date {date}: {e}")

    def get_etf_list(self) -> List[str]:
        """获取ETF代码列表"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_etf_list")

        try:
            if hasattr(self._data_plugin, "get_etf_list"):
                return self._data_plugin.get_etf_list()
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_etf_list"
                )
        except Exception as e:
            self._logger.error(f"Error getting ETF list: {e}")
            raise RuntimeError(f"Failed to get ETF list: {e}")

    def get_ipo_stocks(self, date: str) -> List[str]:
        """获取当日IPO申购标的"""
        if not self._data_plugin:
            raise RuntimeError("Data plugin is not available for get_ipo_stocks")

        try:
            if hasattr(self._data_plugin, "get_ipo_stocks"):
                return self._data_plugin.get_ipo_stocks(date)
            else:
                raise NotImplementedError(
                    f"Data plugin {type(self._data_plugin).__name__} "
                    "does not support get_ipo_stocks"
                )
        except Exception as e:
            self._logger.error(f"Error getting IPO stocks for date {date}: {e}")
            raise RuntimeError(f"Failed to get IPO stocks for date {date}: {e}")
