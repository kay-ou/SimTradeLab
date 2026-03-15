# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
批量回测：对同一策略跑多个日期区间，数据只加载一次
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel

from simtradelab.backtest.config import BacktestConfig
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.i18n import t


class BatchConfig(BaseModel):
    """批量回测配置"""
    strategy_name: str
    date_ranges: list[tuple[str, str]]
    initial_capital: float = 100000.0
    frequency: str = '1d'
    benchmark_code: str = '000300.SS'
    enable_charts: bool = False
    enable_export: bool = False
    sandbox: bool = True


class BatchBacktestRunner:
    """批量回测执行器，复用同一 BacktestRunner 实例，数据只加载一次"""

    def __init__(self):
        self._runner = BacktestRunner()

    def run(self, batch_config: BatchConfig) -> list[dict]:
        """对每个日期区间依次执行回测

        Returns:
            每次回测的报告列表
        """
        results = []
        total = len(batch_config.date_ranges)
        for i, (start, end) in enumerate(batch_config.date_ranges, 1):
            print(t("batch.period", i=i, total=total, start=start, end=end))
            config = BacktestConfig(
                strategy_name=batch_config.strategy_name,
                start_date=start,
                end_date=end,
                initial_capital=batch_config.initial_capital,
                frequency=batch_config.frequency,
                benchmark_code=batch_config.benchmark_code,
                enable_charts=batch_config.enable_charts,
                enable_export=batch_config.enable_export,
                sandbox=batch_config.sandbox,
                enable_logging=False,
            )
            report = self._runner.run(config)
            if report:
                report['_period'] = f"{start}~{end}"
                results.append(report)
        return results

    def summary(self, results: list[dict]) -> pd.DataFrame:
        """生成各区间核心指标对比表

        Returns:
            DataFrame，每行一个区间
        """
        _METRICS = [
            ('total_return', '总收益率'),
            ('annual_return', '年化收益'),
            ('sharpe_ratio', '夏普比率'),
            ('sortino_ratio', '索提诺比率'),
            ('calmar_ratio', '卡玛比率'),
            ('max_drawdown', '最大回撤'),
            ('win_rate', '胜率'),
        ]
        rows = []
        for r in results:
            row = {'区间': r.get('_period', '')}
            for key, label in _METRICS:
                val = r.get(key, 0)
                if key in ('total_return', 'annual_return', 'max_drawdown', 'win_rate'):
                    row[label] = f"{val*100:+.2f}%"
                else:
                    row[label] = f"{val:.3f}"
            rows.append(row)
        df = pd.DataFrame(rows)
        print("\n" + "=" * 70)
        print(t("batch.summary"))
        print("=" * 70)
        print(df.to_string(index=False))
        print("=" * 70 + "\n")
        return df
