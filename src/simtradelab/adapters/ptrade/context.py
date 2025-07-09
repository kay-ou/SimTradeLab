# -*- coding: utf-8 -*-
"""
PTrade上下文和模式定义
"""

import types
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import (
    Blotter,
    Commission,
    Portfolio,
    SimulationParameters,
    VolumeShareSlippage,
)


class PTradeMode(Enum):
    """PTrade运行模式"""

    RESEARCH = "research"  # 研究模式
    BACKTEST = "backtest"  # 回测模式
    TRADING = "trading"  # 交易模式
    MARGIN_TRADING = "margin_trading"  # 融资融券交易模式


@dataclass
class PTradeContext:
    """PTrade策略上下文对象 - 完全符合PTrade规范"""

    portfolio: Portfolio
    capital_base: Optional[float] = None  # 起始资金
    previous_date: Optional[datetime] = None  # 前一个交易日
    sim_params: Optional[SimulationParameters] = None
    initialized: bool = False  # 是否执行初始化
    slippage: Optional[VolumeShareSlippage] = None
    commission: Optional[Commission] = None
    blotter: Optional[Blotter] = None
    recorded_vars: Dict[str, Any] = field(default_factory=dict)  # 收益曲线值
    universe: List[str] = field(default_factory=list)
    benchmark: Optional[str] = None
    current_dt: Optional[datetime] = None
    _parameters: Dict[str, Any] = field(default_factory=dict)  # 策略参数
    _volume_ratio: float = 0.25  # 成交比例
    _limit_mode: str = "volume"  # 限制模式
    _yesterday_position: Dict[str, Any] = field(default_factory=dict)  # 底仓

    def __post_init__(self) -> None:
        self.g = types.SimpleNamespace()  # 全局变量容器

        if self.blotter is None:
            self.blotter = Blotter()

        if self.sim_params is None and self.capital_base:
            self.sim_params = SimulationParameters(self.capital_base)

        if self.slippage is None:
            self.slippage = VolumeShareSlippage()

        if self.commission is None:
            self.commission = Commission()