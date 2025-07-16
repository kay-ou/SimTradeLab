# -*- coding: utf-8 -*-
"""
专业性能分析模块

该模块负责在回测结束后，对策略的性能进行全面的分析和可视化。
它利用 pyfolio-reloaded 库来计算和展示一系列专业的性能指标，
包括但不限于夏普比率、最大回撤、Alpha、Beta 等。
"""

import warnings
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd

# 暂时抑制zipline缺失的警告
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        message="Module .* not found; multipliers will not be applied to position notionals.",
    )
    import pyfolio as pf


class PerformanceManager:
    """
    性能管理器

    负责记录、计算和展示策略回测的详细性能指标。
    """

    def __init__(self, initial_capital: Decimal):
        """
        初始化性能管理器。

        Args:
            initial_capital (Decimal): 初始资本。
        """
        self.initial_capital = initial_capital
        self.daily_portfolio_values: Dict[date, Decimal] = {}
        self.returns: Optional[pd.Series] = None

    def record_daily_portfolio_value(self, dt: datetime, value: Decimal) -> None:
        """
        记录每日的投资组合总价值。

        Args:
            dt (datetime): 日期时间戳。
            value (Decimal): 当日投资组合总价值。
        """
        # 确保只记录日期部分，忽略时间
        normalized_date = dt.date()
        self.daily_portfolio_values[normalized_date] = value

    def _calculate_returns(self) -> None:
        """
        根据记录的每日投资组合价值计算每日收益率。
        """
        if not self.daily_portfolio_values:
            self.returns = pd.Series(dtype=float)
            return

        # 将字典转换为按日期排序的 pandas Series
        portfolio_values = pd.Series(self.daily_portfolio_values).sort_index()

        # 计算每日收益率并转换为 float 类型以兼容 pyfolio
        self.returns = portfolio_values.pct_change().fillna(0).astype(float)

    def analyze(
        self,
        benchmark_returns: Optional[pd.Series] = None,
        output_path: Optional[str] = None,
    ) -> None:
        """
        对策略的性能进行全面分析，并生成报告。

        Args:
            benchmark_returns (Optional[pd.Series]): 基准收益率，用于计算 Alpha/Beta 等相对指标。
                                                     索引必须是与策略收益率对齐的 datetime。
            output_path (Optional[str]): 如果提供，则将分析报告保存到指定的 HTML 文件路径。
        """
        self._calculate_returns()

        if self.returns is None or self.returns.empty:
            print("No returns data to analyze.")
            return

        # TODO: 确认 pyfolio-reloaded 的 create_full_tear_sheet 函数的正确参数
        # pf.create_full_tear_sheet(
        #     self.returns,
        #     benchmark_rets=benchmark_returns,
        #     live_start_date=None,
        #     savefig=output_path
        # )

    def get_summary(self) -> Dict[str, float]:
        """
        获取关键性能指标的摘要。

        Returns:
            Dict[str, float]: 包含关键性能指标的字典。
        """
        if self.returns is None:
            self._calculate_returns()

        if self.returns is None or self.returns.empty:
            return {}

        # 使用 pyfolio 的 perf_stats 函数获取摘要
        stats = pf.timeseries.perf_stats(self.returns)
        return stats.to_dict()
