# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
回测配置类
"""


from __future__ import annotations

from datetime import datetime
from typing import Optional
import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator


def _default_data_path():
    """获取默认数据路径"""
    from ..utils.paths import DATA_PATH
    return str(DATA_PATH)


def _default_strategies_path():
    """获取默认策略路径"""
    from ..utils.paths import STRATEGIES_PATH
    return str(STRATEGIES_PATH)


class BacktestConfig(BaseModel):
    """回测配置参数"""

    strategy_name: str
    start_date: str | pd.Timestamp
    end_date: str | pd.Timestamp
    data_path: str = Field(default_factory=_default_data_path)
    strategies_path: str = Field(default_factory=_default_strategies_path)
    initial_capital: float = Field(default=100000.0, gt=0, description="初始资金必须大于0")
    use_data_server: bool = True

    # 性能优化配置
    enable_multiprocessing: bool = True
    num_workers: Optional[int] = Field(default=None, ge=1, description="多进程worker数量")
    enable_charts: bool = True
    enable_logging: bool = True

    model_config = {"arbitrary_types_allowed": True}

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def convert_to_timestamp(cls, v) -> pd.Timestamp:
        """转换日期为pd.Timestamp"""
        if isinstance(v, str):
            return pd.Timestamp(v)
        if isinstance(v, pd.Timestamp):
            return v
        raise ValueError(f"日期必须是str或pd.Timestamp类型，得到: {type(v)}")

    @model_validator(mode='after')
    def validate_date_range(self):
        """验证日期范围

        此时start_date和end_date已被field_validator转换为pd.Timestamp
        """
        if self.start_date >= self.end_date:  # type: ignore
            raise ValueError("start_date必须早于end_date")
        return self

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
