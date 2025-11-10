# -*- coding: utf-8 -*-
"""
PTrade投资组合和持仓模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Portfolio:
    """投资组合对象 - 完全符合PTrade规范"""

    # 股票账户基础属性 (8个)
    cash: float  # 当前可用资金（不包含冻结资金）
    portfolio_value: float = 0.0  # 当前持有的标的和现金的总价值
    positions_value: float = 0.0  # 持仓价值
    capital_used: float = 0.0  # 已使用的现金
    returns: float = 0.0  # 当前的收益比例，相对于初始资金
    pnl: float = 0.0  # 当前账户总资产-初始账户总资产
    start_date: Optional[datetime] = None  # 开始时间
    positions: Dict[str, "Position"] = field(default_factory=dict)  # 持仓字典

    # 期权账户额外属性
    margin: Optional[float] = None  # 保证金
    risk_degree: Optional[float] = None  # 风险度

    def __post_init__(self) -> None:
        if self.start_date is None:
            self.start_date = datetime.now()
        # 保存起始资金用于计算收益率
        self._starting_cash = self.cash
        # 初始化时现金就是总资产
        self.portfolio_value = self.cash

    @property
    def total_value(self) -> float:
        """总资产"""
        return self.portfolio_value

    def update_portfolio_value(self) -> None:
        """更新投资组合价值"""
        self.positions_value = sum(pos.market_value for pos in self.positions.values())
        self.portfolio_value = self.cash + self.positions_value
        self.capital_used = self._starting_cash - self.cash
        if self._starting_cash > 0:
            self.returns = (
                self.portfolio_value - self._starting_cash
            ) / self._starting_cash
            self.pnl = self.portfolio_value - self._starting_cash


@dataclass
class Position:
    """持仓对象 - 完全符合PTrade规范"""

    # 股票账户基础属性 (7个)
    sid: str  # 标的代码
    enable_amount: int  # 可用数量
    amount: int  # 总持仓数量
    last_sale_price: float  # 最新价格
    cost_basis: float  # 持仓成本价格
    today_amount: int = 0  # 今日开仓数量（且仅回测有效）
    business_type: str = "stock"  # 持仓类型

    # 期货账户扩展属性 (18个)
    short_enable_amount: Optional[int] = None  # 空头仓可用数量
    long_enable_amount: Optional[int] = None  # 多头仓可用数量
    today_short_amount: Optional[int] = None  # 空头仓今仓数量
    today_long_amount: Optional[int] = None  # 多头仓今仓数量
    long_cost_basis: Optional[float] = None  # 多头仓持仓成本
    short_cost_basis: Optional[float] = None  # 空头仓持仓成本
    long_amount: Optional[int] = None  # 多头仓总持仓量
    short_amount: Optional[int] = None  # 空头仓总持仓量
    long_pnl: Optional[float] = None  # 多头仓浮动盈亏
    short_pnl: Optional[float] = None  # 空头仓浮动盈亏
    delivery_date: Optional[datetime] = None  # 交割日
    margin_rate: Optional[float] = None  # 保证金比例
    contract_multiplier: Optional[int] = None  # 合约乘数

    # 期权账户扩展属性 (17个)
    covered_enable_amount: Optional[int] = None  # 备兑仓可用数量
    covered_cost_basis: Optional[float] = None  # 备兑仓持仓成本
    covered_amount: Optional[int] = None  # 备兑仓总持仓量
    covered_pnl: Optional[float] = None  # 备兑仓浮动盈亏
    margin: Optional[float] = None  # 保证金
    exercise_date: Optional[datetime] = None  # 行权日

    def __post_init__(self) -> None:
        self.security = self.sid

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.amount * self.last_sale_price

    @property
    def pnl(self) -> float:
        """持仓盈亏"""
        return (self.last_sale_price - self.cost_basis) * self.amount

    @property
    def returns(self) -> float:
        """持仓收益率"""
        if self.cost_basis == 0:
            return 0.0
        return (self.last_sale_price - self.cost_basis) / self.cost_basis
