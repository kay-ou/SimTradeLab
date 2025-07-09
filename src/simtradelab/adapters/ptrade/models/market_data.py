# -*- coding: utf-8 -*-
"""
PTrade市场数据和配置模型
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SecurityUnitData:
    """单位时间内股票数据对象 - 完全符合PTrade规范"""

    dt: datetime  # 时间
    open: float  # 时间段开始时价格
    close: float  # 时间段结束时价格
    price: float  # 结束时价格
    low: float  # 最低价
    high: float  # 最高价
    volume: int  # 成交的股票数量
    money: float  # 成交的金额


class SimulationParameters:
    """模拟参数对象"""

    def __init__(self, capital_base: float, data_frequency: str = "1d"):
        self.capital_base = capital_base
        self.data_frequency = data_frequency


class VolumeShareSlippage:
    """滑点对象"""

    def __init__(self, volume_limit: float = 0.025, price_impact: float = 0.1):
        self.volume_limit = volume_limit
        self.price_impact = price_impact


class Commission:
    """佣金费用对象"""

    def __init__(
        self, tax: float = 0.001, cost: float = 0.0003, min_trade_cost: float = 5.0
    ):
        self.tax = tax
        self.cost = cost
        self.min_trade_cost = min_trade_cost


class FutureParams:
    """期货参数对象"""

    def __init__(self, margin_rate: float = 0.1, contract_multiplier: int = 1):
        self.margin_rate = margin_rate
        self.contract_multiplier = contract_multiplier
