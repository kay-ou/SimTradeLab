# -*- coding: utf-8 -*-
"""
回测配置类
"""

from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class BacktestConfig:
    """回测配置参数"""

    strategy_name: str
    start_date: str
    end_date: str
    data_path: str
    strategies_path: str
    initial_capital: float = 1000000.0
    use_data_server: bool = True

    def __post_init__(self):
        """验证并转换参数"""
        self.start_date = pd.Timestamp(self.start_date)
        self.end_date = pd.Timestamp(self.end_date)

        if self.start_date >= self.end_date:
            raise ValueError("start_date必须早于end_date")

        if self.initial_capital <= 0:
            raise ValueError("initial_capital必须大于0")

    @property
    def strategy_path(self) -> str:
        """策略文件完整路径"""
        return f'{self.strategies_path}/{self.strategy_name}/backtest.py'

    @property
    def log_dir(self) -> str:
        """日志目录"""
        return f'{self.strategies_path}/{self.strategy_name}/stats'

    def get_log_filename(self) -> str:
        """生成日志文件名"""
        return (f'{self.log_dir}/backtest_'
                f'{self.start_date.strftime("%y%m%d")}_'
                f'{self.end_date.strftime("%y%m%d")}_'
                f'{datetime.now().strftime("%y%m%d_%H%M%S")}.log')

    def get_chart_filename(self) -> str:
        """生成图表文件名"""
        return (f'{self.log_dir}/backtest_'
                f'{self.start_date.strftime("%y%m%d")}_'
                f'{self.end_date.strftime("%y%m%d")}_'
                f'{datetime.now().strftime("%y%m%d_%H%M%S")}.png')
