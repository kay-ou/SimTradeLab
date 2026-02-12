# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
回测统计收集器
"""


from __future__ import annotations

from dataclasses import dataclass, field

from simtradelab.ptrade.context import Context


@dataclass
class BacktestStats:
    """回测统计数据——StatsCollector 与 stats.py 之间的显式契约"""
    portfolio_values: list[float] = field(default_factory=list)
    positions_count: list[int] = field(default_factory=list)
    daily_pnl: list[float] = field(default_factory=list)
    daily_buy_amount: list[float] = field(default_factory=list)
    daily_sell_amount: list[float] = field(default_factory=list)
    daily_positions_value: list[float] = field(default_factory=list)
    trade_dates: list = field(default_factory=list)


class StatsCollector:
    """回测统计数据收集器"""

    def __init__(self):
        self._stats = BacktestStats()

    @property
    def stats(self) -> BacktestStats:
        """获取统计数据"""
        return self._stats

    def collect_pre_trading(self, context: Context, current_date):
        """收集交易前数据"""
        self._stats.portfolio_values.append(context.portfolio.portfolio_value)
        self._stats.positions_count.append(
            sum(1 for p in context.portfolio.positions.values() if p.amount > 0)
        )
        self._stats.trade_dates.append(current_date)

    def collect_trading_amounts(self, context: Context):
        """收集交易金额（从OrderProcessor累计的gross金额）"""
        self._stats.daily_buy_amount.append(context._daily_buy_total)
        self._stats.daily_sell_amount.append(context._daily_sell_total)
        context._daily_buy_total = 0.0
        context._daily_sell_total = 0.0

    def collect_post_trading(self, context: Context, prev_portfolio_value: float):
        """收集交易后数据"""
        current_value = context.portfolio.portfolio_value
        daily_pnl = current_value - prev_portfolio_value
        self._stats.daily_pnl.append(daily_pnl)
        self._stats.daily_positions_value.append(context.portfolio.positions_value)
