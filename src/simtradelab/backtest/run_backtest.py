# -*- coding: utf-8 -*-
"""
本地回测入口 - 配置与启动

简化的入口文件，仅保留配置参数
"""

import sys
import os

# 强制无缓冲输出（确保日志实时显示）
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.paths import DATA_PATH, STRATEGIES_PATH


if __name__ == '__main__':
    # ==================== 回测配置 ====================

    # 策略名称
    strategy_name = '5mv'

    # 回测周期
    start_date = '2025-01-01'
    end_date = '2025-10-31'

    # ==================== 启动回测 ====================

    runner = BacktestRunner(data_path=str(DATA_PATH))
    report = runner.run(
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        strategies_path=str(STRATEGIES_PATH)
    )
