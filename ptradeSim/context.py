# -*- coding: utf-8 -*-

class Blotter:
    """模拟的Blotter对象"""
    def __init__(self):
        self.open_orders = []

class Position:
    """
    持仓对象，存储单个证券的持仓信息。
    """
    def __init__(self, security, amount, cost_basis, last_sale_price=0):
        self.security = security  # 证券代码
        self.amount = amount  # 持有数量
        self.cost_basis = cost_basis  # 成本价
        self.enable_amount = amount # 可用数量
        self.last_sale_price = last_sale_price # 最新成交价

    @property
    def market_value(self):
        """市场价值"""
        return self.last_sale_price * self.amount

    @property
    def value(self):
        """持仓价值（market_value的别名）"""
        return self.market_value

    @property
    def pnl_ratio(self):
        """盈亏比例"""
        if self.amount == 0 or self.cost_basis == 0:
            return 0.0
        return (self.last_sale_price - self.cost_basis) / self.cost_basis


class Portfolio:
    """
    账户对象，管理账户资产、持仓等。
    """
    def __init__(self, start_cash=1000000.0):
        self.starting_cash = start_cash  # 初始资金
        self.cash = start_cash  # 可用现金
        self.positions = {}  # 持仓信息, dict a stock to a Position object
        self.total_value = start_cash  # 总资产


class Context:
    """
    策略上下文对象，策略可通过此对象访问账户、数据等。
    """
    def __init__(self, portfolio):
        self.portfolio = portfolio  # 账户对象
        self.current_dt = None  # 当前时间
        self.previous_date = None # 前一个交易日
        self.securities = []  # 证券列表
        self.blotter = Blotter() # 模拟的 blotter