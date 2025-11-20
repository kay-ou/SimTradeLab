# -*- coding: utf-8 -*-
"""
回测配置类
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Union, Optional
import pandas as pd


def _default_data_path():
    """获取默认数据路径"""
    from ..utils.paths import DATA_PATH
    return str(DATA_PATH)


def _default_strategies_path():
    """获取默认策略路径"""
    from ..utils.paths import STRATEGIES_PATH
    return str(STRATEGIES_PATH)


@dataclass
class BacktestConfig:
    """回测配置参数"""

    strategy_name: str
    start_date: Union[str, pd.Timestamp]
    end_date: Union[str, pd.Timestamp]
    data_path: str = field(default_factory=_default_data_path)
    strategies_path: str = field(default_factory=_default_strategies_path)
    initial_capital: float = 100000.0
    use_data_server: bool = True

    # 性能优化配置
    enable_multiprocessing: bool = True  # 是否启用多进程数据加载
    num_workers: Optional[int] = None  # 多进程worker数量（None=自动）
    enable_charts: bool = True  # 是否生成图表（禁用可节省300秒）
    enable_logging: bool = True  # 是否输出日志文件

    def __post_init__(self):
        """验证并转换参数"""
        # 转换日期类型
        if isinstance(self.start_date, str):
            self.start_date = pd.Timestamp(self.start_date)
        if isinstance(self.end_date, str):
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
                f'{self.start_date.strftime("%y%m%d")}_'  # type: ignore
                f'{self.end_date.strftime("%y%m%d")}_'  # type: ignore
                f'{datetime.now().strftime("%y%m%d_%H%M%S")}.log')

    def get_chart_filename(self) -> str:
        """生成图表文件名"""
        return (f'{self.log_dir}/backtest_'
                f'{self.start_date.strftime("%y%m%d")}_'  # type: ignore
                f'{self.end_date.strftime("%y%m%d")}_'  # type: ignore
                f'{datetime.now().strftime("%y%m%d_%H%M%S")}.png')
