# -*- coding: utf-8 -*-
"""
回测统计收集器
"""

from typing import Dict, List
from simtradelab.ptrade.context import Context


class StatsCollector:
    """回测统计数据收集器"""

    def __init__(self):
        self._stats: Dict[str, List] = {
            'portfolio_values': [],
            'positions_count': [],
            'daily_pnl': [],
            'daily_buy_amount': [],
            'daily_sell_amount': [],
            'daily_positions_value': [],
            'trade_dates': [],
        }

    @property
    def stats(self) -> Dict[str, List]:
        """获取统计数据"""
        return self._stats

    def collect_pre_trading(self, context: Context, current_date):
        """收集交易前数据"""
        self._stats['portfolio_values'].append(context.portfolio.portfolio_value)
        self._stats['positions_count'].append(
            sum(1 for p in context.portfolio.positions.values() if p.amount > 0)
        )
        self._stats['trade_dates'].append(current_date)

    def collect_trading_amounts(self, prev_cash: float, current_cash: float):
        """收集交易金额"""
        cash_change = current_cash - prev_cash
        self._stats['daily_buy_amount'].append(max(0, -cash_change))
        self._stats['daily_sell_amount'].append(max(0, cash_change))

    def collect_post_trading(self, context: Context, prev_portfolio_value: float):
        """收集交易后数据"""
        current_value = context.portfolio.portfolio_value
        daily_pnl = current_value - prev_portfolio_value
        self._stats['daily_pnl'].append(daily_pnl)
        self._stats['daily_positions_value'].append(context.portfolio.positions_value)
