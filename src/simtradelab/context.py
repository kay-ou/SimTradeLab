# -*- coding: utf-8 -*-
"""
策略上下文、投资组合、持仓和订单的定义。
"""
import uuid
from datetime import datetime
from enum import Enum


class OrderStatus(Enum):
    """订单状态枚举"""
    NEW = "new"                    # 新建
    OPEN = "open"                  # 未成交
    FILLED = "filled"              # 已成交
    CANCELLED = "cancelled"        # 已撤销
    REJECTED = "rejected"          # 已拒绝


class Order:
    """订单对象"""
    def __init__(self, security, amount, price=None, order_type="market", order_id=None):
        self.order_id = order_id or str(uuid.uuid4()).replace('-', '')
        self.security = security
        self.amount = amount  # 正数买入，负数卖出
        self.price = price
        self.order_type = order_type  # market, limit
        self.status = OrderStatus.NEW
        self.filled_amount = 0
        self.avg_fill_price = 0.0
        self.commission = 0.0
        self.add_time = datetime.now()
        self.fill_time = None

    @property
    def is_buy(self):
        """是否为买单"""
        return self.amount > 0

    @property
    def is_sell(self):
        """是否为卖单"""
        return self.amount < 0

    @property
    def remaining_amount(self):
        """剩余未成交数量"""
        return abs(self.amount) - abs(self.filled_amount)

    @property
    def is_open(self):
        """是否为未完成订单"""
        return self.status in [OrderStatus.NEW, OrderStatus.OPEN]

    def to_dict(self, use_compat=True):
        """
        转换为字典格式

        Args:
            use_compat: 是否使用兼容性状态转换
        """
        from .compatibility import convert_order_status

        # 获取状态值
        status_value = self.status.value
        if use_compat:
            status_value = convert_order_status(status_value, to_external=True)

        return {
            'order_id': self.order_id,
            'security': self.security,
            'amount': self.amount,
            'price': self.price,
            'order_type': self.order_type,
            'status': status_value,
            'filled_amount': self.filled_amount,
            'avg_fill_price': self.avg_fill_price,
            'commission': self.commission,
            'add_time': self.add_time,
            'fill_time': self.fill_time,
            'remaining_amount': self.remaining_amount,
            'is_buy': self.is_buy,
            'is_sell': self.is_sell
        }


class Trade:
    """成交记录对象"""
    def __init__(self, order_id, security, amount, price, commission, trade_time=None):
        self.trade_id = str(uuid.uuid4()).replace('-', '')
        self.order_id = order_id
        self.security = security
        self.amount = amount
        self.price = price
        self.commission = commission
        self.trade_time = trade_time or datetime.now()

    @property
    def is_buy(self):
        """是否为买入成交"""
        return self.amount > 0

    @property
    def is_sell(self):
        """是否为卖出成交"""
        return self.amount < 0

    def to_dict(self):
        """转换为字典格式"""
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'security': self.security,
            'amount': self.amount,
            'price': self.price,
            'commission': self.commission,
            'trade_time': self.trade_time,
            'is_buy': self.is_buy,
            'is_sell': self.is_sell
        }


class Blotter:
    """模拟的Blotter对象，管理订单和成交"""
    def __init__(self):
        self.orders = {}  # 所有订单 {order_id: Order}
        self.trades = []  # 所有成交记录
        self.daily_orders = []  # 当日订单ID列表
        self.daily_trades = []  # 当日成交ID列表

    def add_order(self, order):
        """添加订单"""
        self.orders[order.order_id] = order
        self.daily_orders.append(order.order_id)
        return order.order_id

    def get_order(self, order_id):
        """获取指定订单"""
        return self.orders.get(order_id)

    def get_open_orders(self):
        """获取未完成订单"""
        return {oid: order for oid, order in self.orders.items() if order.is_open}

    def get_all_orders(self):
        """获取所有订单"""
        return self.orders.copy()

    def get_daily_orders(self):
        """获取当日订单"""
        return {oid: self.orders[oid] for oid in self.daily_orders if oid in self.orders}

    def add_trade(self, trade):
        """添加成交记录"""
        self.trades.append(trade)
        self.daily_trades.append(trade.trade_id)
        return trade.trade_id

    def get_trades(self):
        """获取当日成交记录"""
        return [trade for trade in self.trades if trade.trade_id in self.daily_trades]

    def get_all_trades(self):
        """获取所有成交记录"""
        return self.trades.copy()

    def cancel_order(self, order_id):
        """撤销订单"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.is_open:
                order.status = OrderStatus.CANCELLED
                return True
        return False

    def fill_order(self, order_id, fill_amount, fill_price, commission=0.0):
        """订单成交"""
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]
        if not order.is_open:
            return False

        # 更新订单状态
        order.filled_amount += fill_amount
        order.avg_fill_price = ((order.avg_fill_price * (abs(order.filled_amount) - abs(fill_amount))) +
                               (fill_price * abs(fill_amount))) / abs(order.filled_amount)
        order.commission += commission

        if abs(order.filled_amount) >= abs(order.amount):
            order.status = OrderStatus.FILLED
            order.fill_time = datetime.now()
        else:
            order.status = OrderStatus.OPEN

        # 创建成交记录
        trade = Trade(order_id, order.security, fill_amount, fill_price, commission)
        self.add_trade(trade)

        return True

    def reset_daily_data(self):
        """重置当日数据（用于新的交易日）"""
        self.daily_orders = []
        self.daily_trades = []

class Position:
    """
    持仓对象，存储单个证券的持仓信息。
    """
    def __init__(self, security, amount, cost_basis, last_sale_price=0):
        self.security = security  # 证券代码
        self.amount = amount  # 持有数量
        self.cost_basis = cost_basis  # 成本价
        self.enable_amount = amount # 可用数量
        self.last_sale_price = last_sale_price if last_sale_price != 0 else cost_basis # 最新成交价

    @property
    def market_value(self):
        """市场价值"""
        return self.last_sale_price * self.amount

    @property
    def value(self):
        """持仓价值（market_value的别名）"""
        return self.market_value

    @property
    def pnl(self):
        """盈亏金额"""
        return (self.last_sale_price - self.cost_basis) * self.amount

    @property
    def pnl_ratio(self):
        """盈亏比例"""
        if self.amount == 0 or self.cost_basis == 0:
            return 0.0
        return (self.last_sale_price - self.cost_basis) / self.cost_basis

    @property
    def pnl_percent(self):
        """盈亏百分比（pnl_ratio的别名）"""
        return self.pnl_ratio


class Portfolio:
    """
    账户对象，管理账户资产、持仓等。
    """
    def __init__(self, start_cash=1000000.0):
        self.starting_cash = start_cash  # 初始资金
        self.cash = start_cash  # 可用现金
        self.positions = {}  # 持仓信息, dict a stock to a Position object
        self.total_value = start_cash  # 总资产
        self.previous_total_value = start_cash  # 前一日总资产，用于计算日盈亏
        self._daily_pnl = 0.0  # 当日盈亏

    def calculate_total_value(self, current_prices=None):
        """计算总资产价值"""
        if current_prices:
            # 更新持仓的最新价格
            for security, position in self.positions.items():
                if security in current_prices:
                    price_data = current_prices[security]
                    # 支持多种价格字段
                    price = (price_data.get('close') or
                            price_data.get('price') or
                            price_data.get('last_price') or
                            price_data.get('current_price') or
                            position.last_sale_price)
                    position.last_sale_price = price

        positions_value = sum(position.market_value for position in self.positions.values())
        new_total_value = self.cash + positions_value
        
        # 计算当日盈亏
        self._daily_pnl = new_total_value - self.previous_total_value
        self.total_value = new_total_value
        return self.total_value
    
    @property
    def daily_pnl(self):
        """当日盈亏"""
        return self._daily_pnl
    
    def update_daily_start(self):
        """更新交易日开始时的数据"""
        self.previous_total_value = self.total_value
        self._daily_pnl = 0.0


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