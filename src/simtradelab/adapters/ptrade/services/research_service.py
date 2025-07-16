# -*- coding: utf-8 -*-
"""
研究服务

处理研究模式下的数据查询、分析和技术指标计算等业务逻辑，
从API路由器中分离出来。使用统一的数据源管理器进行数据访问。
"""

from typing import Any, Dict, List, Optional, Union, overload

import numpy as np
import pandas as pd

from ....plugins.data import DataSourceManager
from ..context import PTradeContext
from .base_service import BaseService


class ResearchService(BaseService):
    """研究服务 - 处理研究模式下的数据查询和分析业务逻辑"""

    def __init__(
        self,
        context: "PTradeContext",
        plugin_manager: Optional[Any] = None,
        **kwargs: Any,
    ):
        super().__init__(context=context, plugin_manager=plugin_manager, **kwargs)
        # context 和 plugin_manager 已经在父类中设置，无需重复设置

        # 初始化数据源管理器
        self._data_source_manager = DataSourceManager(plugin_manager)

    def initialize(self) -> None:
        """初始化研究服务"""
        self._logger.info("Initializing ResearchService")

        # 初始化数据源管理器
        self._data_source_manager.initialize()

    def shutdown(self) -> None:
        """关闭研究服务"""
        self._logger.info("Shutting down ResearchService")

        # 关闭数据源管理器
        if self._data_source_manager:
            self._data_source_manager.shutdown()

    # ================================
    # 历史数据查询服务
    # ================================

    @overload
    def get_history_data(
        self,
        count: Optional[int] = None,
        frequency: str = "1d",
        field: Optional[Union[str, List[str]]] = None,
        security_list: Optional[List[str]] = None,
        fq: str = "pre",
        include: bool = True,
        fill: bool = True,
        is_dict: bool = True,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    @overload
    def get_history_data(
        self,
        count: Optional[int] = None,
        frequency: str = "1d",
        field: Optional[Union[str, List[str]]] = None,
        security_list: Optional[List[str]] = None,
        fq: str = "pre",
        include: bool = True,
        fill: bool = True,
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        ...

    def get_history_data(
        self,
        count: Optional[int] = None,
        frequency: str = "1d",
        field: Optional[Union[str, List[str]]] = None,
        security_list: Optional[List[str]] = None,
        fq: str = "pre",
        include: bool = True,
        fill: bool = True,
        is_dict: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """获取历史行情数据"""
        try:
            # 使用数据源管理器获取历史数据
            if security_list and len(security_list) > 1:
                return self._data_source_manager.get_multiple_history_data(
                    security_list=security_list,
                    count=count or 30,
                    frequency=frequency,
                    fields=field
                    if isinstance(field, list)
                    else ([field] if field else None),
                    fq=fq,
                    include_now=include,
                    fill_gaps=fill,
                    as_dict=is_dict,
                    start_date=start_date,
                    end_date=end_date,
                )
            elif security_list and len(security_list) == 1:
                data = self._data_source_manager.get_history_data(
                    security=security_list[0],
                    count=count or 30,
                    frequency=frequency,
                    fields=field
                    if isinstance(field, list)
                    else ([field] if field else None),
                    fq=fq,
                    include_now=include,
                    fill_gaps=fill,
                    start_date=start_date,
                    end_date=end_date,
                )
                if is_dict:
                    return {security_list[0]: data}
                return data
            else:
                # 如果没有指定证券列表，返回空数据
                if is_dict:
                    return {}
                else:
                    return pd.DataFrame()
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_history_data failed: {e}")
            # 如果数据源管理器不可用，返回空数据
            if is_dict:
                return {}
            else:
                return pd.DataFrame()

    @overload
    def get_price_data(
        self,
        security: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> float:
        ...

    @overload
    def get_price_data(
        self,
        security: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> Dict[str, float]:
        ...

    def get_price_data(
        self,
        security: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "1d",
        fields: Optional[Union[str, List[str]]] = None,
        count: Optional[int] = None,
    ) -> Union[float, Dict[str, float]]:
        """获取价格数据"""
        try:
            if security:
                # 处理单个证券的情况
                if isinstance(security, str):
                    prices = self._data_source_manager.get_current_price([security])
                    return prices.get(security, 0.0)
                # 处理多个证券的情况
                elif isinstance(security, list):
                    return self._data_source_manager.get_current_price(security)
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_price_data failed: {e}")

        # 默认返回模拟价格
        if isinstance(security, str):
            return 10.0
        elif isinstance(security, list):
            return {sec: 10.0 for sec in security}
        else:
            return 0.0

    def get_snapshot_data(self, security_list: List[str]) -> pd.DataFrame:
        """获取当前行情快照"""
        try:
            # 使用数据源管理器获取行情快照
            snapshot = self._data_source_manager.get_snapshot(security_list)
            if snapshot:
                # 转换为DataFrame格式
                rows = []
                for security, data_dict in snapshot.items():
                    row = {"security": security}
                    row.update(data_dict)
                    rows.append(row)
                return pd.DataFrame(rows)
            else:
                return pd.DataFrame()
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_snapshot failed: {e}")

        # 返回空DataFrame
        return pd.DataFrame()

    def get_current_data(
        self, security_list: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """获取当前数据 - 策略中data参数的数据源"""
        if security_list is None:
            # 如果没有指定股票列表，使用上下文中的universe
            security_list = list(self.context.universe) if self.context.universe else []

        if not security_list:
            return {}

        try:
            # 使用数据源管理器获取行情快照
            snapshot = self._data_source_manager.get_snapshot(security_list)

            # 转换为策略期望的格式: {security: {field: value}}
            current_data: Dict[str, Dict[str, Any]] = {}
            for security, data_dict in snapshot.items():
                current_data[security] = {
                    "price": data_dict.get("price", data_dict.get("last_price", 0.0)),
                    "close": data_dict.get("last_price", data_dict.get("price", 0.0)),
                    "open": data_dict.get("open", 0.0),
                    "high": data_dict.get("high", 0.0),
                    "low": data_dict.get("low", 0.0),
                    "volume": data_dict.get("volume", 0),
                    "money": data_dict.get("money", 0.0),
                }

            return current_data
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_current_data failed: {e}")

        # 如果数据源管理器不可用，返回空字典
        return {}

    # ================================
    # 技术指标计算服务
    # ================================

    def _get_indicators_plugin(self) -> Optional[Any]:
        """
        通过插件管理器获取技术指标插件
        注意：技术指标插件暂时使用传统的发现方式，未来可以考虑创建IndicatorsManager
        """
        if not self._plugin_manager:
            return None

        # 查找技术指标插件
        all_plugins = self._plugin_manager.get_all_plugins()
        for plugin_name, plugin_instance in all_plugins.items():
            if self._is_indicators_plugin(plugin_instance):
                return plugin_instance
        return None

    def _is_indicators_plugin(self, plugin_instance: Any) -> bool:
        """判断插件是否为技术指标插件"""
        # 通过多种条件识别技术指标插件
        is_indicators_plugin = (
            # 通过名称识别
            (
                hasattr(plugin_instance, "metadata")
                and plugin_instance.metadata.name == "technical_indicators_plugin"
            )
            # 通过category识别
            or (
                hasattr(plugin_instance, "metadata")
                and hasattr(plugin_instance.metadata, "category")
                and plugin_instance.metadata.category in ["indicators", "analysis"]
            )
            # 通过标签识别
            or (
                hasattr(plugin_instance, "metadata")
                and hasattr(plugin_instance.metadata, "tags")
                and "indicators" in plugin_instance.metadata.tags
            )
            # 通过方法识别
            or (
                hasattr(plugin_instance, "calculate_macd")
                and hasattr(plugin_instance, "calculate_kdj")
                and hasattr(plugin_instance, "calculate_rsi")
                and hasattr(plugin_instance, "calculate_cci")
            )
        )
        return is_indicators_plugin

    def calculate_macd(
        self, close: np.ndarray, short: int = 12, long: int = 26, m: int = 9
    ) -> pd.DataFrame:
        """计算MACD指标"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_macd"):
            try:
                # 使用插件计算MACD
                result = indicators_plugin.calculate_macd(close)
                # 确保返回DataFrame
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin MACD calculation failed: {e}")

        # 如果插件不可用，返回模拟数据
        return self._calculate_macd_fallback(close, short, long, m)

    def calculate_kdj(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """计算KDJ指标"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_kdj"):
            try:
                # 使用插件计算KDJ
                result = indicators_plugin.calculate_kdj(high, low, close)
                # 确保返回DataFrame
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin KDJ calculation failed: {e}")

        # 如果插件不可用，返回模拟数据
        return self._calculate_kdj_fallback(high, low, close, n, m1, m2)

    def calculate_rsi(self, close: np.ndarray, n: int = 6) -> pd.DataFrame:
        """计算RSI指标"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_rsi"):
            try:
                # 使用插件计算RSI
                result = indicators_plugin.calculate_rsi(close)
                # 确保返回DataFrame
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin RSI calculation failed: {e}")

        # 如果插件不可用，返回模拟数据
        return self._calculate_rsi_fallback(close, n)

    def calculate_cci(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14
    ) -> pd.DataFrame:
        """计算CCI指标"""
        indicators_plugin = self._get_indicators_plugin()
        if indicators_plugin and hasattr(indicators_plugin, "calculate_cci"):
            try:
                # 使用插件计算CCI
                result = indicators_plugin.calculate_cci(high, low, close)
                # 确保返回DataFrame
                if isinstance(result, pd.DataFrame):
                    return result
            except Exception as e:
                self._logger.warning(f"Indicators plugin CCI calculation failed: {e}")

        # 如果插件不可用，返回模拟数据
        return self._calculate_cci_fallback(high, low, close, n)

    # ================================
    # 股票信息查询服务
    # ================================

    def get_stock_info(self, security_list: List[str]) -> Dict[str, Any]:
        """获取股票基础信息"""
        try:
            return self._data_source_manager.get_security_info(security_list)
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_stock_info failed: {e}")

        # 默认返回模拟信息
        result = {}
        for security in security_list:
            if security.endswith(".XSHE"):
                market = "SZSE"
            elif security.endswith(".XSHG"):
                market = "SSE"
            else:
                market = "UNKNOWN"

            result[security] = {
                "market": market,
                "type": "stock",
                "name": f"股票{security[:6]}",
                "listed_date": "2000-01-01",
                "delist_date": None,
            }
        return result

    def get_trading_day(self, date: str, offset: int = 0) -> str:
        """获取交易日期"""
        try:
            return self._data_source_manager.get_trading_day(date, offset)
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_trading_day failed: {e}")
        # 默认返回原日期
        return date

    def get_all_trading_days(self) -> List[str]:
        """获取全部交易日期"""
        try:
            return self._data_source_manager.get_all_trading_days()
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_all_trading_days failed: {e}")
        # 默认返回模拟数据
        return ["2023-01-03", "2023-01-04", "2023-01-05"]

    def get_trading_days_range(self, start_date: str, end_date: str) -> List[str]:
        """获取指定范围交易日期"""
        try:
            return self._data_source_manager.get_trading_days_range(
                start_date, end_date
            )
        except Exception as e:
            self._logger.warning(
                f"DataSourceManager get_trading_days_range failed: {e}"
            )
        # 默认返回模拟数据
        return ["2023-12-25", "2023-12-26", "2023-12-27", "2023-12-28", "2023-12-29"]

    def check_limit_status(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """检查涨跌停状态"""
        try:
            limit_data = self._data_source_manager.check_limit_status(
                [security], query_date
            )
            if security in limit_data:
                security_limit_data = limit_data[security]
                return {
                    security: {
                        "limit_up": security_limit_data.get("limit_up", False),
                        "limit_down": security_limit_data.get("limit_down", False),
                        "limit_up_price": security_limit_data.get(
                            "limit_up_price", 0.0
                        ),
                        "limit_down_price": security_limit_data.get(
                            "limit_down_price", 0.0
                        ),
                        "current_price": security_limit_data.get("current_price", 0.0),
                    }
                }
        except Exception as e:
            self._logger.warning(f"DataSourceManager check_limit_status failed: {e}")

        # 默认返回模拟数据（无涨跌停）
        return {
            security: {
                "limit_up": False,
                "limit_down": False,
                "limit_up_price": 16.5,
                "limit_down_price": 13.5,
                "current_price": 15.0,
            }
        }

    def get_fundamentals(
        self, stocks: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取财务数据信息"""
        try:
            # 使用数据源管理器获取财务数据
            result = self._data_source_manager.get_fundamentals(
                stocks, table, fields, date
            )
            if not result.empty:
                return result
        except Exception as e:
            self._logger.warning(f"DataSourceManager get_fundamentals failed: {e}")

        # 默认返回模拟基本面数据
        if not stocks:
            # 如果没有股票，返回空DataFrame但包含必要列
            basic_columns = ["code", "date"] + fields
            return pd.DataFrame(columns=basic_columns)

        if not fields:
            # 如果没有字段但有股票，返回只包含基本信息的DataFrame
            rows = []
            for stock in stocks:
                stock_row: Dict[str, Any] = {"code": stock, "date": date}
                rows.append(stock_row)
            return pd.DataFrame(rows)

        # 生成模拟基本面数据
        rows = []
        for stock in stocks:
            row: Dict[str, Any] = {"code": stock, "date": date}
            # 为每个字段生成默认值
            for field in fields:
                if field in ["revenue", "total_assets", "total_liab"]:
                    row[field] = 0.0  # 金额类字段默认为0
                elif field in ["pe_ratio", "pb_ratio", "roe", "eps"]:
                    row[field] = 0.0  # 比率类字段默认为0
                else:
                    row[field] = 0.0  # 其他字段默认为0
            rows.append(row)

        return pd.DataFrame(rows)

    # ================================
    # 私有方法 - 技术指标计算后备实现
    # ================================

    def _calculate_macd_fallback(
        self, close: np.ndarray, short: int, long: int, m: int
    ) -> pd.DataFrame:
        """MACD指标计算后备实现"""
        length = len(close)
        return pd.DataFrame(
            {
                "MACD": np.zeros(length),
                "SIGNAL": np.zeros(length),
                "HISTOGRAM": np.zeros(length),
            }
        )

    def _calculate_kdj_fallback(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        n: int,
        m1: int,
        m2: int,
    ) -> pd.DataFrame:
        """KDJ指标计算后备实现"""
        length = len(close)
        return pd.DataFrame(
            {
                "K": np.full(length, 50.0),
                "D": np.full(length, 50.0),
                "J": np.full(length, 50.0),
            }
        )

    def _calculate_rsi_fallback(self, close: np.ndarray, n: int) -> pd.DataFrame:
        """RSI指标计算后备实现"""
        length = len(close)
        return pd.DataFrame(
            {
                "RSI": np.full(length, 50.0),
            }
        )

    def _calculate_cci_fallback(
        self, high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int
    ) -> pd.DataFrame:
        """CCI指标计算后备实现"""
        length = len(close)
        return pd.DataFrame(
            {
                "CCI": np.zeros(length),
            }
        )
