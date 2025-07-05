# -*- coding: utf-8 -*-
"""
交易执行接口模块
"""
import uuid
from .context import Position, Order, OrderStatus
from .logger import log

def order(engine, security, amount, limit_price=None):
    """模拟核心下单函数"""
    context = engine.context
    data = engine.current_data

    if security not in data:
        log.warning(f"在 {context.current_dt} 没有 {security} 的市场数据，订单被拒绝")
        return None

    # 获取当前价格
    current_price = data[security]['close']
    if current_price <= 0:
        log.warning(f"{security} 的价格 {current_price} 无效，订单被拒绝")
        return None

    # 使用限价或市价
    price = limit_price if limit_price else current_price

    # 创建订单对象
    order_type = "limit" if limit_price else "market"
    order_obj = Order(security, amount, price, order_type)

    # 添加到订单管理系统
    order_id = context.blotter.add_order(order_obj)

    # 立即执行订单（模拟市场成交）
    success = _execute_order_immediately(engine, order_obj)

    if success:
        action = "买入" if amount > 0 else "卖出"
        log.info(f"生成订单，订单号:{order_id}，股票代码：{security}，数量：{action}{abs(amount)}股")
        return order_id
    else:
        # 订单失败，标记为拒绝
        order_obj.status = OrderStatus.REJECTED
        return None


def _execute_order_immediately(engine, order_obj):
    """立即执行订单（模拟成交）"""
    context = engine.context
    data = engine.current_data
    security = order_obj.security
    amount = order_obj.amount
    order_price = order_obj.price
    order_type = order_obj.order_type

    # 获取当前市价
    current_price = data[security]['close']

    # 检查限价单是否可以成交
    if order_type == "limit":
        if amount > 0:  # 买单：限价 >= 市价才能成交
            if order_price < current_price:
                log.info(f"限价买单价格({order_price})低于市价({current_price})，订单挂起等待成交")
                order_obj.status = OrderStatus.OPEN
                return True  # 订单成功提交，但未成交
        else:  # 卖单：限价 <= 市价才能成交
            if order_price > current_price:
                log.info(f"限价卖单价格({order_price})高于市价({current_price})，订单挂起等待成交")
                order_obj.status = OrderStatus.OPEN
                return True  # 订单成功提交，但未成交

    # 使用市价成交（市价单直接用市价，限价单用限价）
    execution_price = current_price if order_type == "market" else order_price

    # 计算成本和佣金
    cost = amount * execution_price
    commission = max(abs(cost) * engine.commission_ratio, engine.min_commission if amount != 0 else 0)
    total_cost = cost + commission

    # 检查资金是否足够
    if amount > 0 and context.portfolio.cash < total_cost:
        log.warning(f"现金不足，无法买入 {amount} 股 {security}，订单被拒绝")
        return False

    # 检查持仓是否足够卖出
    if amount < 0:
        current_position = context.portfolio.positions.get(security)
        current_shares = current_position.amount if current_position else 0
        if current_shares < abs(amount):
            log.warning(f"持仓不足，无法卖出 {abs(amount)} 股 {security}，当前持仓: {current_shares}")
            return False

    # 扣除资金
    context.portfolio.cash -= total_cost

    # 更新持仓
    if security in context.portfolio.positions:
        position = context.portfolio.positions[security]
        if (position.amount + amount) != 0:
            new_cost_basis = ((position.cost_basis * position.amount) + cost) / (position.amount + amount)
            position.cost_basis = new_cost_basis
        position.amount += amount
        position.enable_amount += amount
        if position.amount == 0:
            del context.portfolio.positions[security]
    else:
        if amount > 0:
            position = Position(security=security, amount=amount, cost_basis=execution_price, last_sale_price=execution_price)
            context.portfolio.positions[security] = position

    # 记录订单成交
    context.blotter.fill_order(order_obj.order_id, amount, execution_price, commission)

    return True

def order_target(engine, security, amount):
    """模拟order_target函数"""
    context = engine.context
    current_position = context.portfolio.positions.get(security)
    current_amount = current_position.amount if current_position else 0
    amount_to_order = amount - current_amount
    return order(engine, security, amount_to_order)

def order_value(engine, security, value):
    """模拟order_value函数"""
    data = engine.current_data
    price = data.get(security, {}).get('close')
    if not price or price <= 0:
        log.warning(f"错误：{security} 没有有效价格，无法按金额 {value} 下单")
        return None
    amount = int(value / price / 100) * 100
    if amount == 0:
        return None
    return order(engine, security, amount)

def cancel_order(engine, order_param):
    """模拟cancel_order函数"""
    context = engine.context

    # 支持传入订单ID或订单对象
    if isinstance(order_param, str):
        order_id = order_param
    elif hasattr(order_param, 'order_id'):
        order_id = order_param.order_id
    else:
        log.warning(f"无效的订单参数: {order_param}")
        return False

    success = context.blotter.cancel_order(order_id)
    if success:
        log.info(f"成功取消订单: {order_id}")
    else:
        log.warning(f"取消订单失败: {order_id}")

    return success


# ==================== 交易查询接口 ====================

def get_positions(engine, securities=None):
    """
    获取多支股票持仓信息

    Args:
        engine: 回测引擎实例
        securities: 股票代码列表，None表示获取所有持仓

    Returns:
        dict: {security: position_info}
    """
    context = engine.context
    positions = {}

    if securities is None:
        # 获取所有持仓
        for security, position in context.portfolio.positions.items():
            positions[security] = {
                'security': security,
                'amount': position.amount,
                'enable_amount': position.enable_amount,
                'cost_basis': position.cost_basis,
                'last_sale_price': position.last_sale_price,
                'market_value': position.market_value,
                'pnl_ratio': position.pnl_ratio,
                'value': position.value
            }
    else:
        # 获取指定股票持仓
        if isinstance(securities, str):
            securities = [securities]

        for security in securities:
            if security in context.portfolio.positions:
                position = context.portfolio.positions[security]
                positions[security] = {
                    'security': security,
                    'amount': position.amount,
                    'enable_amount': position.enable_amount,
                    'cost_basis': position.cost_basis,
                    'last_sale_price': position.last_sale_price,
                    'market_value': position.market_value,
                    'pnl_ratio': position.pnl_ratio,
                    'value': position.value
                }
            else:
                positions[security] = None

    return positions


def get_position(engine, security):
    """
    获取单个股票持仓信息

    Args:
        engine: 回测引擎实例
        security: 股票代码

    Returns:
        dict or None: 持仓信息字典，无持仓返回None
    """
    positions = get_positions(engine, [security])
    return positions.get(security)


def get_open_orders(engine):
    """
    获取未完成订单

    Args:
        engine: 回测引擎实例

    Returns:
        dict: {order_id: order_dict}
    """
    context = engine.context
    open_orders = context.blotter.get_open_orders()

    return {order_id: order.to_dict() for order_id, order in open_orders.items()}


def get_order(engine, order_id):
    """
    获取指定订单

    Args:
        engine: 回测引擎实例
        order_id: 订单ID

    Returns:
        dict or None: 订单信息字典，不存在返回None
    """
    context = engine.context
    order = context.blotter.get_order(order_id)

    return order.to_dict() if order else None


def get_orders(engine):
    """
    获取当日全部订单

    Args:
        engine: 回测引擎实例

    Returns:
        dict: {order_id: order_dict}
    """
    context = engine.context
    daily_orders = context.blotter.get_daily_orders()

    return {order_id: order.to_dict() for order_id, order in daily_orders.items()}


def get_trades(engine):
    """
    获取当日成交订单

    Args:
        engine: 回测引擎实例

    Returns:
        list: [trade_dict, ...]
    """
    context = engine.context
    trades = context.blotter.get_trades()

    return [trade.to_dict() for trade in trades]
