# -*- coding: utf-8 -*-
"""
高保真回测引擎的核心投资组合管理器。
"""

from datetime import datetime
from typing import Dict

from simtradelab.adapters.ptrade.models.portfolio import Portfolio, Position
from simtradelab.core.events.contracts import FillEvent, OrderEvent


class PortfolioManager:
    """
    投资组合管理器。

    负责根据交易事件实时跟踪和管理投资组合的状态，包括现金、仓位、
    市值、保证金和浮动盈亏等。
    """

    def __init__(self, initial_cash: float):
        """
        初始化投资组合管理器。

        Args:
            initial_cash (float): 初始资金。
        """
        self.portfolio = Portfolio(cash=initial_cash)

    def on_fill(self, event: FillEvent) -> None:
        """
        处理成交事件，更新投资组合。

        Args:
            event (FillEvent): 成交事件。
        """
        # 1. 更新现金
        self.portfolio.cash -= event.commission
        self.portfolio.cash -= event.quantity * event.price

        # 2. 更新持仓
        if event.symbol not in self.portfolio.positions:
            self.portfolio.positions[event.symbol] = Position(
                sid=event.symbol,
                amount=0,
                cost_basis=0.0,
                last_sale_price=event.price,
                enable_amount=0,
            )

        position = self.portfolio.positions[event.symbol]

        # 更新持仓成本
        total_cost = (
            position.cost_basis * position.amount + event.quantity * event.price
        )
        total_quantity = position.amount + event.quantity
        position.cost_basis = (
            total_cost / total_quantity if total_quantity != 0 else 0.0
        )

        # 更新持仓数量
        # 更新持仓数量
        position.amount += int(event.quantity)
        position.enable_amount += int(event.quantity)
        position.last_sale_price = event.price

        # 3. 更新投资组合价值
        self.portfolio.update_portfolio_value()

    def update_market_value(self, prices: Dict[str, float]) -> None:
        """
        根据最新的市场价格更新所有持仓的市值和整个投资组合的价值。

        Args:
            prices (Dict[str, float]): 包含最新价格的字典，键为symbol，值为价格。
        """
        for symbol, position in self.portfolio.positions.items():
            if symbol in prices:
                position.last_sale_price = prices[symbol]

        self.portfolio.update_portfolio_value()
