# -*- coding: utf-8 -*-
"""
AkShare 数据源插件

基于 AkShare 库提供中国市场金融数据。
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

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
    def validate_date_range(cls, v: str, info: Any) -> str:
        """验证结束日期是否在开始日期之后。"""
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("配置错误: end_date 必须在 start_date 之后。")
        return v


class AkShareDataSource(BaseDataSourcePlugin):
    """
    使用 AkShare 作为数据源的插件。

    实现了 BaseDataSourcePlugin 定义的标准接口，提供中国市场的股票数据。
    """

    def __init__(self, metadata: Any, config: AkShareDataPluginConfig) -> None:
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
        try:
            # 使用一个轻量级的API调用来检查服务状态
            # 尝试获取一个常用股票的基本信息
            test_df = ak.stock_zh_a_spot_em()
            if test_df is not None and not test_df.empty:
                logger.debug("AkShare服务检查通过。")
                return True
            else:
                logger.warning("AkShare服务返回空数据。")
                return False
        except Exception as e:
            logger.error(f"AkShare服务检查失败: {e}")
            return False

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
        self, security_list: List[str], **kwargs: Any
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
        self, security_list: List[str], **kwargs: Any
    ) -> Dict[str, Dict[str, Any]]:
        """获取证券的实时快照数据。"""
        try:
            # 获取实时行情数据
            spot_df = ak.stock_zh_a_spot_em()
            if spot_df is None or spot_df.empty:
                logger.warning("无法获取实时行情数据。")
                return {}

            snapshot = {}
            for security in security_list:
                # 在AkShare数据中查找对应的证券
                security_data = spot_df[spot_df["代码"] == security]

                if not security_data.empty:
                    row = security_data.iloc[0]
                    snapshot[security] = {
                        "last_price": float(row["最新价"]),
                        "pre_close": float(row["昨收"]),
                        "open": float(row["今开"]),
                        "high": float(row["最高"]),
                        "low": float(row["最低"]),
                        "volume": int(row["成交量"]) if pd.notna(row["成交量"]) else 0,
                        "amount": float(row["成交额"]) if pd.notna(row["成交额"]) else 0.0,
                        "change": float(row["涨跌额"]) if pd.notna(row["涨跌额"]) else 0.0,
                        "pct_change": float(row["涨跌幅"])
                        if pd.notna(row["涨跌幅"])
                        else 0.0,
                        "turnover": float(row["换手率"]) if pd.notna(row["换手率"]) else 0.0,
                        "datetime": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                else:
                    logger.warning(f"未找到证券 {security} 的实时数据。")
                    snapshot[security] = {
                        "last_price": 0.0,
                        "pre_close": 0.0,
                        "open": 0.0,
                        "high": 0.0,
                        "low": 0.0,
                        "volume": 0,
                        "amount": 0.0,
                        "change": 0.0,
                        "pct_change": 0.0,
                        "turnover": 0.0,
                        "datetime": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }

            return snapshot

        except Exception as e:
            logger.error(f"获取实时快照数据时出错: {e}")
            # 返回空数据结构
            return {security: {} for security in security_list}

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
        try:
            # 使用AkShare获取交易日历
            trading_days_df = ak.tool_trade_date_hist_sina()
            # 转换为字符串列表
            trading_days = trading_days_df["trade_date"].astype(str).tolist()
            logger.debug(f"获取到 {len(trading_days)} 个交易日。")
            return trading_days
        except Exception as e:
            logger.error(f"获取交易日历时出错: {e}")
            # 返回空列表作为降级处理
            return []

    # --- 以下为当前版本暂不实现的方法 ---

    def get_trading_day(self, date: str, offset: int = 0, **kwargs: Any) -> str:
        """获取交易日。"""
        try:
            # 获取所有交易日
            trading_days = self.get_all_trading_days()
            if not trading_days:
                return date

            # 查找基准日期在交易日中的位置
            base_date = pd.to_datetime(date).strftime("%Y-%m-%d")

            # 如果基准日期就是交易日，直接使用
            if base_date in trading_days:
                base_index = trading_days.index(base_date)
            else:
                # 如果不是交易日，找到最近的交易日
                base_date_dt = pd.to_datetime(base_date)
                trading_days_dt = pd.to_datetime(trading_days)
                # 找到最近的交易日
                nearest_index = int((trading_days_dt - base_date_dt).abs().argmin())
                base_index = nearest_index

            # 应用偏移量
            target_index = base_index + offset
            if 0 <= target_index < len(trading_days):
                return trading_days[target_index]
            else:
                # 超出范围，返回边界值
                if target_index < 0:
                    return trading_days[0]
                else:
                    return trading_days[-1]

        except Exception as e:
            logger.error(f"获取交易日时出错: {e}")
            return date

    def get_trading_days_range(
        self, start_date: str, end_date: str, **kwargs: Any
    ) -> List[str]:
        """获取指定日期范围内的交易日。"""
        try:
            # 获取所有交易日
            trading_days = self.get_all_trading_days()
            if not trading_days:
                return []

            # 转换为pandas日期时间进行过滤
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)

            # 过滤出指定范围内的交易日
            filtered_days = []
            for trading_day in trading_days:
                trading_day_dt = pd.to_datetime(trading_day)
                if start_dt <= trading_day_dt <= end_dt:
                    filtered_days.append(trading_day)

            logger.debug(
                f"在 {start_date} 至 {end_date} 范围内找到 {len(filtered_days)} 个交易日。"
            )
            return filtered_days

        except Exception as e:
            logger.error(f"获取交易日范围时出错: {e}")
            return []

    def is_trading_day(self, date: str, **kwargs: Any) -> bool:
        """判断是否为交易日。"""
        try:
            # 获取所有交易日
            trading_days = self.get_all_trading_days()
            if not trading_days:
                # 如果无法获取交易日历，使用简单的工作日判断
                date_obj = pd.to_datetime(date)
                return date_obj.weekday() < 5  # 周一到周五

            # 标准化日期格式
            normalized_date = pd.to_datetime(date).strftime("%Y-%m-%d")

            # 检查是否在交易日列表中
            return normalized_date in trading_days

        except Exception as e:
            logger.error(f"判断交易日时出错: {e}")
            # 降级处理：使用简单的工作日判断
            try:
                date_obj = pd.to_datetime(date)
                return date_obj.weekday() < 5
            except Exception:
                return False

    def check_limit_status(
        self, security_list: List[str], **kwargs: Any
    ) -> Dict[str, Dict[str, Any]]:
        """检查证券的涨跌停状态。"""
        try:
            # 获取实时行情数据
            spot_df = ak.stock_zh_a_spot_em()
            if spot_df is None or spot_df.empty:
                logger.warning("无法获取实时行情数据进行涨跌停检查。")
                return {}

            limit_status = {}
            for security in security_list:
                # 在AkShare数据中查找对应的证券
                security_data = spot_df[spot_df["代码"] == security]

                if not security_data.empty:
                    row = security_data.iloc[0]
                    current_price = float(row["最新价"])
                    pre_close = float(row["昨收"])

                    # 根据交易规则计算涨跌停价格
                    # 一般股票涨跌停幅度为10%，ST股票为5%
                    if security.startswith("ST") or security.startswith("*ST"):
                        limit_pct = 0.05  # 5%
                    else:
                        limit_pct = 0.10  # 10%

                    limit_up_price = round(pre_close * (1 + limit_pct), 2)
                    limit_down_price = round(pre_close * (1 - limit_pct), 2)

                    # 判断是否涨跌停（允许小的误差）
                    limit_up = abs(current_price - limit_up_price) < 0.01
                    limit_down = abs(current_price - limit_down_price) < 0.01

                    limit_status[security] = {
                        "limit_up": limit_up,
                        "limit_down": limit_down,
                        "limit_up_price": limit_up_price,
                        "limit_down_price": limit_down_price,
                        "current_price": current_price,
                        "pre_close": pre_close,
                        "pct_change": float(row["涨跌幅"])
                        if pd.notna(row["涨跌幅"])
                        else 0.0,
                    }
                else:
                    logger.warning(f"未找到证券 {security} 的涨跌停数据。")
                    limit_status[security] = {
                        "limit_up": False,
                        "limit_down": False,
                        "limit_up_price": 0.0,
                        "limit_down_price": 0.0,
                        "current_price": 0.0,
                        "pre_close": 0.0,
                        "pct_change": 0.0,
                    }

            return limit_status

        except Exception as e:
            logger.error(f"检查涨跌停状态时出错: {e}")
            return {security: {} for security in security_list}

    def get_fundamentals(
        self, security_list: List[str], table: str, fields: List[str], date: str
    ) -> pd.DataFrame:
        """获取基本面数据。"""
        try:
            # 基本面数据通常按季度或年度报告
            # 由于AkShare的基本面数据接口复杂，这里实现基本的财务指标获取

            result_data = []
            for security in security_list:
                try:
                    # 根据不同的表格类型获取数据
                    if table == "income":  # 利润表
                        # 尝试获取利润表数据
                        df = ak.stock_financial_analysis_indicator(symbol=security)
                        if not df.empty:
                            latest_data = df.iloc[-1]  # 最新数据
                            row_data = {"code": security, "date": date}

                            # 映射字段
                            for field in fields:
                                if field in ["revenue", "total_revenue"]:
                                    row_data[field] = str(latest_data.get("营业收入", 0))
                                elif field in ["net_profit", "net_income"]:
                                    row_data[field] = str(latest_data.get("净利润", 0))
                                elif field in ["operating_profit"]:
                                    row_data[field] = str(latest_data.get("营业利润", 0))
                                else:
                                    row_data[field] = "0"

                            result_data.append(row_data)

                    elif table == "balance_sheet":  # 资产负债表
                        # 获取资产负债表数据
                        df = ak.stock_balance_sheet_by_report_em(symbol=security)
                        if not df.empty:
                            latest_data = df.iloc[-1]
                            row_data = {"code": security, "date": date}

                            for field in fields:
                                if field in ["total_assets"]:
                                    row_data[field] = str(latest_data.get("资产总计", 0))
                                elif field in ["total_liab"]:
                                    row_data[field] = str(latest_data.get("负债合计", 0))
                                elif field in ["total_equity"]:
                                    row_data[field] = str(latest_data.get("所有者权益合计", 0))
                                else:
                                    row_data[field] = "0"

                            result_data.append(row_data)

                    elif table == "cash_flow":  # 现金流量表
                        # 获取现金流量表数据
                        df = ak.stock_cash_flow_sheet_by_report_em(symbol=security)
                        if not df.empty:
                            latest_data = df.iloc[-1]
                            row_data = {"code": security, "date": date}

                            for field in fields:
                                if field in ["operating_cash_flow"]:
                                    row_data[field] = str(
                                        latest_data.get("经营活动产生的现金流量净额", 0)
                                    )
                                elif field in ["investing_cash_flow"]:
                                    row_data[field] = str(
                                        latest_data.get("投资活动产生的现金流量净额", 0)
                                    )
                                elif field in ["financing_cash_flow"]:
                                    row_data[field] = str(
                                        latest_data.get("筹资活动产生的现金流量净额", 0)
                                    )
                                else:
                                    row_data[field] = "0"

                            result_data.append(row_data)

                    else:  # 其他指标
                        # 使用财务分析指标API
                        df = ak.stock_financial_analysis_indicator(symbol=security)
                        if not df.empty:
                            latest_data = df.iloc[-1]
                            row_data = {"code": security, "date": date}

                            for field in fields:
                                if field in ["pe_ratio"]:
                                    row_data[field] = str(latest_data.get("市盈率", 0))
                                elif field in ["pb_ratio"]:
                                    row_data[field] = str(latest_data.get("市净率", 0))
                                elif field in ["roe"]:
                                    row_data[field] = str(latest_data.get("净资产收益率", 0))
                                elif field in ["eps"]:
                                    row_data[field] = str(latest_data.get("每股收益", 0))
                                else:
                                    row_data[field] = "0"

                            result_data.append(row_data)

                except Exception as e:
                    logger.warning(f"获取 {security} 基本面数据时出错: {e}")
                    # 添加空数据行
                    row_data = {"code": security, "date": date}
                    for field in fields:
                        row_data[field] = "0"
                    result_data.append(row_data)

            # 创建DataFrame
            if result_data:
                return pd.DataFrame(result_data)
            else:
                # 返回空DataFrame但包含正确的列结构
                columns = ["code", "date"] + fields
                return pd.DataFrame(columns=columns)

        except Exception as e:
            logger.error(f"获取基本面数据时出错: {e}")
            # 返回空DataFrame
            columns = ["code", "date"] + fields
            return pd.DataFrame(columns=columns)

    def get_security_info(self, security_list: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取证券基本信息。"""
        try:
            # 获取股票基本信息
            info = {}

            # 获取股票基本信息
            stock_info_df = ak.stock_info_a_code_name()

            for security in security_list:
                try:
                    # 查找股票信息
                    stock_data = stock_info_df[stock_info_df["code"] == security]

                    if not stock_data.empty:
                        row = stock_data.iloc[0]

                        # 确定市场
                        if (
                            security.endswith(".SZ")
                            or security.startswith("000")
                            or security.startswith("002")
                            or security.startswith("300")
                        ):
                            market = "SZSE"
                        elif (
                            security.endswith(".SH")
                            or security.startswith("600")
                            or security.startswith("601")
                            or security.startswith("603")
                            or security.startswith("688")
                        ):
                            market = "SSE"
                        else:
                            market = "UNKNOWN"

                        # 确定类型
                        if security.startswith("688"):
                            stock_type = "科创板"
                        elif security.startswith("300"):
                            stock_type = "创业板"
                        elif (
                            security.startswith("600")
                            or security.startswith("601")
                            or security.startswith("603")
                        ):
                            stock_type = "沪市主板"
                        elif security.startswith("000") or security.startswith("001"):
                            stock_type = "深市主板"
                        elif security.startswith("002"):
                            stock_type = "中小板"
                        else:
                            stock_type = "其他"

                        info[security] = {
                            "name": row["name"],
                            "market": market,
                            "type": stock_type,
                            "listed_date": "N/A",  # AkShare股票基本信息中没有上市日期
                            "delist_date": None,
                            "code": security,
                        }
                    else:
                        # 如果找不到股票信息，提供默认信息
                        if (
                            security.endswith(".SZ")
                            or security.startswith("000")
                            or security.startswith("002")
                            or security.startswith("300")
                        ):
                            market = "SZSE"
                        elif (
                            security.endswith(".SH")
                            or security.startswith("600")
                            or security.startswith("601")
                            or security.startswith("603")
                            or security.startswith("688")
                        ):
                            market = "SSE"
                        else:
                            market = "UNKNOWN"

                        info[security] = {
                            "name": f"股票{security}",
                            "market": market,
                            "type": "股票",
                            "listed_date": "N/A",
                            "delist_date": None,
                            "code": security,
                        }

                except Exception as e:
                    logger.warning(f"获取 {security} 股票信息时出错: {e}")
                    # 提供默认信息
                    info[security] = {
                        "name": f"股票{security}",
                        "market": "UNKNOWN",
                        "type": "股票",
                        "listed_date": "N/A",
                        "delist_date": None,
                        "code": security,
                    }

            return info

        except Exception as e:
            logger.error(f"获取证券基本信息时出错: {e}")
            # 返回默认信息
            return {
                security: {
                    "name": f"股票{security}",
                    "market": "UNKNOWN",
                    "type": "股票",
                    "listed_date": "N/A",
                    "delist_date": None,
                    "code": security,
                }
                for security in security_list
            }
