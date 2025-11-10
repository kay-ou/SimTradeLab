# -*- coding: utf-8 -*-
"""
本地回测入口 - 配置与启动

简化的入口文件，仅保留配置参数
"""

import sys
import os

# 强制无缓冲输出（确保日志实时显示）
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

from backtest_runner import BacktestRunner


if __name__ == '__main__':
    # ==================== 回测配置 ====================

    # 策略名称
    strategy_name = '20mv'

    # 回测周期
    start_date = '2024-01-01'
    end_date = '2024-06-30'

    # 数据路径
    data_path = '/home/kay/dev/ptrade/data'

    # 策略路径
    strategies_path = '/home/kay/dev/ptrade/strategies'

    # ==================== 启动回测 ====================

    runner = BacktestRunner(data_path=data_path)
    report = runner.run(
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        strategies_path=strategies_path
    )
