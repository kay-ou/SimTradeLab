# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
回测结果 CSV 导出
"""

from __future__ import annotations

import os
import pandas as pd

from simtradelab.backtest.backtest_stats import BacktestStats


def export_to_csv(report: dict, output_dir: str) -> dict[str, str]:
    """导出回测结果到 CSV

    Args:
        report: generate_backtest_report 返回的报告字典（必须含 _stats 键）
        output_dir: 输出目录

    Returns:
        {'daily_stats': path, 'positions': path}
    """
    stats: BacktestStats = report['_stats']
    os.makedirs(output_dir, exist_ok=True)

    # 推断日期区间用于文件名
    trade_dates = stats.trade_dates
    start_str = _fmt_date(trade_dates[0])
    end_str = _fmt_date(trade_dates[-1])
    suffix = f"{start_str}_{end_str}"

    daily_path = _export_daily_stats(stats, output_dir, suffix)
    positions_path = _export_positions(stats, output_dir, suffix)

    print("CSV 已导出:")
    print(f"  每日统计: {daily_path}")
    print(f"  持仓历史: {positions_path}")

    return {'daily_stats': daily_path, 'positions': positions_path}


def _fmt_date(d) -> str:
    if hasattr(d, 'strftime'):
        return d.strftime('%Y%m%d')
    return str(d)[:10].replace('-', '')


def _export_daily_stats(stats: BacktestStats, output_dir: str, suffix: str) -> str:
    n = len(stats.trade_dates)
    dates = [_fmt_date(d) for d in stats.trade_dates]

    def _pad(lst):
        if len(lst) < n:
            return list(lst) + [0] * (n - len(lst))
        return lst

    df = pd.DataFrame({
        'date': dates,
        'portfolio_value': stats.portfolio_values[:n],
        'daily_pnl': _pad(stats.daily_pnl),
        'buy_amount': _pad(stats.daily_buy_amount),
        'sell_amount': _pad(stats.daily_sell_amount),
        'positions_value': _pad(stats.daily_positions_value),
    })
    path = os.path.join(output_dir, f"daily_stats_{suffix}.csv")
    df.to_csv(path, index=False, encoding='utf-8-sig')
    return path


def _export_positions(stats: BacktestStats, output_dir: str, suffix: str) -> str:
    rows = []
    for date, snapshot in zip(stats.trade_dates, stats.daily_positions_snapshot):
        date_str = _fmt_date(date)
        for pos in snapshot:
            rows.append({
                'date': date_str,
                'stock_code': pos[0],
                'name': pos[1],
                'amount': pos[2],
                'market_value': pos[3],
                'cost_basis': pos[4],
            })
    df = pd.DataFrame(rows, columns=['date', 'stock_code', 'name', 'amount', 'market_value', 'cost_basis'])
    path = os.path.join(output_dir, f"positions_history_{suffix}.csv")
    df.to_csv(path, index=False, encoding='utf-8-sig')
    return path
