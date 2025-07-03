# -*- coding: utf-8 -*-
"""
交易执行接口模块
"""
import uuid
from .context import Position
from .logger import log

def order(engine, security, amount):
    """模拟核心下单函数"""
    context = engine.context
    data = engine.current_data

    if security not in data:
        log.warning(f"在 {context.current_dt} 没有 {security} 的市场数据，订单被拒绝")
        return None

    price = data[security]['close']
    if price <= 0:
        log.warning(f"{security} 的价格 {price} 无效，订单被拒绝")
        return None

    cost = amount * price

    if amount > 0 and context.portfolio.cash < cost:
        log.warning(f"现金不足，无法买入 {amount} 股 {security}，订单被拒绝")
        return None

    context.portfolio.cash -= cost

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
            position = Position(security=security, amount=amount, cost_basis=price, last_sale_price=price)
            context.portfolio.positions[security] = position
        else:
            log.warning(f"无法卖出不在投资组合中的 {security}，订单被拒绝")
            context.portfolio.cash += cost
            return None

    order_id = str(uuid.uuid4()).replace('-', '')
    action = "买入" if amount > 0 else "卖出"
    log.info(f"生成订单，订单号:{order_id}，股票代码：{security}，数量：{action}{abs(amount)}股")
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
    log.info(f"取消订单: {order_param}")
