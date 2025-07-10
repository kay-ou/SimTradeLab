# -*- coding: utf-8 -*-
"""
通用工具API混入类

提供通用的工具函数API实现，所有路由器都使用相同的逻辑
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class CommonUtilsMixin:
    """通用工具API混入类"""

    def __init__(self) -> None:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)

    def log(self, content: str, level: str = "info") -> None:
        """日志记录"""
        if hasattr(self._logger, level):
            getattr(self._logger, level)(content)
        else:
            self._logger.info(content)

    def check_limit(
        self, security: str, query_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """代码涨跌停状态判断"""
        return {
            security: {
                "limit_up": False,
                "limit_down": False,
                "limit_up_price": None,
                "limit_down_price": None,
                "current_price": 10.0,
            }
        }

    def get_trading_day(self, date: str, offset: int = 0) -> str:
        """获取交易日期"""
        try:
            # 解析输入日期
            if isinstance(date, str):
                base_date = datetime.strptime(date, "%Y-%m-%d")
            else:
                base_date = date

            # 计算偏移
            target_date = base_date + timedelta(days=offset)

            # 简单的工作日逻辑(忽略节假日)
            while target_date.weekday() > 4:  # 0-6: 周一到周日
                if offset > 0:
                    target_date += timedelta(days=1)
                else:
                    target_date -= timedelta(days=1)

            return target_date.strftime("%Y-%m-%d")
        except Exception as e:
            self._logger.error(f"Error calculating trading day: {e}")
            return date

    def get_all_trades_days(self) -> list[str]:
        """获取全部交易日期"""
        try:
            # 生成过去一年的交易日（简化版）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            trading_days = []
            current_date = start_date

            while current_date <= end_date:
                # 只包含工作日（简化版，忽略节假日）
                if current_date.weekday() < 5:  # 0-4: 周一到周五
                    trading_days.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)

            return trading_days
        except Exception as e:
            self._logger.error(f"Error getting all trading days: {e}")
            return []

    def get_trade_days(self, start_date: str, end_date: str) -> list[str]:
        """获取指定范围交易日期"""
        try:
            # 解析日期
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            trading_days = []
            current_date = start

            while current_date <= end:
                # 只包含工作日（简化版，忽略节假日）
                if current_date.weekday() < 5:  # 0-4: 周一到周五
                    trading_days.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)

            return trading_days
        except Exception as e:
            self._logger.error(
                f"Error getting trade days from {start_date} to {end_date}: {e}"
            )
            return []

    def set_universe(self, securities: list[str]) -> None:
        """设置股票池"""
        context = getattr(self, "context", None)
        if context:
            if hasattr(context, "universe"):
                context.universe = securities
                self._logger.info(f"Universe set to {len(securities)} securities")
            else:
                setattr(context, "universe", securities)
                self._logger.info(
                    f"Universe created and set to {len(securities)} securities"
                )
        else:
            self._logger.warning("No context available to set universe")

    def set_benchmark(self, benchmark: str) -> None:
        """设置基准"""
        context = getattr(self, "context", None)
        if context:
            if hasattr(context, "benchmark"):
                context.benchmark = benchmark
                self._logger.info(f"Benchmark set to {benchmark}")
            else:
                setattr(context, "benchmark", benchmark)
                self._logger.info(f"Benchmark created and set to {benchmark}")
        else:
            self._logger.warning("No context available to set benchmark")
