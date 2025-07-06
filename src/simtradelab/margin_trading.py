#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融资融券交易模块

提供完整的融资融券交易功能，包括：
- 融资买入/卖券还款
- 融券卖出/买券还券
- 担保品买卖
- 融资融券查询功能
"""

from datetime import datetime
import pandas as pd
import random
from .logger import log


# ==================== 融资融券交易类API ====================

def margin_trade(engine, security, amount, operation='buy'):
    """
    担保品买卖
    
    Args:
        engine: 回测引擎实例
        security: 证券代码
        amount: 交易数量
        operation: 操作类型 ('buy'-买入, 'sell'-卖出)
        
    Returns:
        dict: 委托结果
    """
    order_id = f"MARGIN_TRADE_{int(datetime.now().timestamp())}"
    
    # 模拟担保品交易
    result = {
        'success': True,
        'order_id': order_id,
        'security': security,
        'amount': amount,
        'operation': operation,
        'order_type': 'margin_trade',
        'timestamp': datetime.now().isoformat()
    }
    
    log.info(f"担保品{operation}: {security}, {amount}股, 委托号{order_id}")
    return result


def margincash_open(engine, security, amount, price=None):
    """
    融资买入
    
    Args:
        engine: 回测引擎实例
        security: 证券代码
        amount: 买入数量
        price: 买入价格，None表示市价
        
    Returns:
        dict: 委托结果
    """
    order_id = f"MARGIN_CASH_OPEN_{int(datetime.now().timestamp())}"
    
    # 检查融资额度
    margin_info = get_margin_assert(engine)
    available_margin = margin_info['available_margin_amount']
    
    # 估算所需资金（简化计算）
    estimated_cost = amount * (price or 10.0)  # 假设价格
    
    if estimated_cost > available_margin:
        log.error(f"融资买入失败: 可用融资额度不足，需要{estimated_cost}，可用{available_margin}")
        return {
            'success': False,
            'error': '可用融资额度不足',
            'order_id': None
        }
    
    result = {
        'success': True,
        'order_id': order_id,
        'security': security,
        'amount': amount,
        'price': price,
        'order_type': 'margincash_open',
        'estimated_cost': estimated_cost,
        'timestamp': datetime.now().isoformat()
    }
    
    log.info(f"融资买入: {security}, {amount}股, 委托号{order_id}")
    return result


def margincash_close(engine, security, amount, price=None):
    """
    卖券还款
    
    Args:
        engine: 回测引擎实例
        security: 证券代码
        amount: 卖出数量
        price: 卖出价格，None表示市价
        
    Returns:
        dict: 委托结果
    """
    order_id = f"MARGIN_CASH_CLOSE_{int(datetime.now().timestamp())}"
    
    result = {
        'success': True,
        'order_id': order_id,
        'security': security,
        'amount': amount,
        'price': price,
        'order_type': 'margincash_close',
        'timestamp': datetime.now().isoformat()
    }
    
    log.info(f"卖券还款: {security}, {amount}股, 委托号{order_id}")
    return result


def margincash_direct_refund(engine, amount):
    """
    直接还款
    
    Args:
        engine: 回测引擎实例
        amount: 还款金额
        
    Returns:
        dict: 还款结果
    """
    transaction_id = f"MARGIN_REFUND_{int(datetime.now().timestamp())}"
    
    result = {
        'success': True,
        'transaction_id': transaction_id,
        'amount': amount,
        'transaction_type': 'margincash_direct_refund',
        'timestamp': datetime.now().isoformat()
    }
    
    log.info(f"直接还款: {amount}元, 交易号{transaction_id}")
    return result


def marginsec_open(engine, security, amount, price=None):
    """
    融券卖出
    
    Args:
        engine: 回测引擎实例
        security: 证券代码
        amount: 卖出数量
        price: 卖出价格，None表示市价
        
    Returns:
        dict: 委托结果
    """
    order_id = f"MARGIN_SEC_OPEN_{int(datetime.now().timestamp())}"
    
    # 检查融券额度
    sec_info = get_marginsec_open_amount(engine, security)
    max_amount = sec_info['max_sell_amount']
    
    if amount > max_amount:
        log.error(f"融券卖出失败: 可融券数量不足，需要{amount}，可用{max_amount}")
        return {
            'success': False,
            'error': '可融券数量不足',
            'order_id': None
        }
    
    result = {
        'success': True,
        'order_id': order_id,
        'security': security,
        'amount': amount,
        'price': price,
        'order_type': 'marginsec_open',
        'timestamp': datetime.now().isoformat()
    }
    
    log.info(f"融券卖出: {security}, {amount}股, 委托号{order_id}")
    return result


def marginsec_close(engine, security, amount, price=None):
    """
    买券还券
    
    Args:
        engine: 回测引擎实例
        security: 证券代码
        amount: 买入数量
        price: 买入价格，None表示市价
        
    Returns:
        dict: 委托结果
    """
    order_id = f"MARGIN_SEC_CLOSE_{int(datetime.now().timestamp())}"
    
    result = {
        'success': True,
        'order_id': order_id,
        'security': security,
        'amount': amount,
        'price': price,
        'order_type': 'marginsec_close',
        'timestamp': datetime.now().isoformat()
    }
    
    log.info(f"买券还券: {security}, {amount}股, 委托号{order_id}")
    return result


def marginsec_direct_refund(engine, security, amount):
    """
    直接还券
    
    Args:
        engine: 回测引擎实例
        security: 证券代码
        amount: 还券数量
        
    Returns:
        dict: 还券结果
    """
    transaction_id = f"MARGIN_SEC_REFUND_{int(datetime.now().timestamp())}"
    
    result = {
        'success': True,
        'transaction_id': transaction_id,
        'security': security,
        'amount': amount,
        'transaction_type': 'marginsec_direct_refund',
        'timestamp': datetime.now().isoformat()
    }
    
    log.info(f"直接还券: {security}, {amount}股, 交易号{transaction_id}")
    return result


# ==================== 融资融券查询类API ====================

def get_margincash_stocks(engine):
    """
    获取融资标的
    
    Args:
        engine: 回测引擎实例
        
    Returns:
        list: 融资标的列表
    """
    # 模拟融资标的列表
    margin_stocks = [
        {
            'security': '000001.SZ',
            'name': '平安银行',
            'margin_ratio': 0.5,  # 融资保证金比例
            'status': 'normal'    # 状态：normal-正常，suspended-暂停
        },
        {
            'security': '000002.SZ', 
            'name': '万科A',
            'margin_ratio': 0.5,
            'status': 'normal'
        },
        {
            'security': '600519.SH',
            'name': '贵州茅台',
            'margin_ratio': 0.5,
            'status': 'normal'
        },
        {
            'security': '600036.SH',
            'name': '招商银行',
            'margin_ratio': 0.5,
            'status': 'normal'
        }
    ]
    
    log.info(f"获取融资标的: {len(margin_stocks)}只")
    return margin_stocks


def get_marginsec_stocks(engine):
    """
    获取融券标的
    
    Args:
        engine: 回测引擎实例
        
    Returns:
        list: 融券标的列表
    """
    # 模拟融券标的列表
    sec_stocks = [
        {
            'security': '000001.SZ',
            'name': '平安银行',
            'sec_ratio': 0.5,     # 融券保证金比例
            'available_amount': 100000,  # 可融券数量
            'status': 'normal'
        },
        {
            'security': '600519.SH',
            'name': '贵州茅台',
            'sec_ratio': 0.5,
            'available_amount': 50000,
            'status': 'normal'
        }
    ]
    
    log.info(f"获取融券标的: {len(sec_stocks)}只")
    return sec_stocks


def get_margin_contract(engine):
    """
    合约查询

    Args:
        engine: 回测引擎实例

    Returns:
        list: 融资融券合约列表
    """
    # 模拟融资融券合约
    contracts = [
        {
            'contract_id': 'MC001',
            'security': '000001.SZ',
            'contract_type': 'margin_cash',  # margin_cash-融资, margin_sec-融券
            'amount': 10000,
            'price': 12.50,
            'interest_rate': 0.068,  # 年利率
            'open_date': '2023-06-01',
            'due_date': '2023-12-01',
            'status': 'active'
        },
        {
            'contract_id': 'MS001',
            'security': '600519.SH',
            'contract_type': 'margin_sec',
            'amount': 1000,
            'price': 1800.00,
            'fee_rate': 0.108,  # 年费率
            'open_date': '2023-06-15',
            'due_date': '2023-12-15',
            'status': 'active'
        }
    ]

    log.info(f"获取融资融券合约: {len(contracts)}个")
    return contracts


def get_margin_contractreal(engine):
    """
    实时合约查询

    Args:
        engine: 回测引擎实例

    Returns:
        list: 实时合约信息
    """
    contracts = get_margin_contract(engine)

    # 添加实时信息
    for contract in contracts:
        contract['current_value'] = contract['amount'] * contract['price']
        contract['profit_loss'] = random.uniform(-1000, 1000)  # 模拟盈亏
        contract['margin_ratio'] = 0.5
        contract['risk_level'] = 'low'  # low, medium, high

    log.info(f"获取实时合约信息: {len(contracts)}个")
    return contracts


def get_margin_assert(engine):
    """
    信用资产查询

    Args:
        engine: 回测引擎实例

    Returns:
        dict: 信用资产信息
    """
    # 模拟信用资产信息
    margin_assert = {
        'total_asset': 2000000.0,        # 总资产
        'total_debt': 500000.0,          # 总负债
        'net_asset': 1500000.0,          # 净资产
        'margin_available': 800000.0,    # 可用保证金
        'margin_ratio': 0.75,            # 维持担保比例
        'available_margin_amount': 300000.0,  # 可融资金额
        'available_sec_amount': 200000.0,     # 可融券金额
        'risk_level': 'safe',            # 风险等级: safe, warning, danger
        'margin_call_line': 1.3,         # 追保线
        'force_close_line': 1.1,         # 平仓线
    }

    log.info(f"信用资产查询: 总资产{margin_assert['total_asset']}, 维持担保比例{margin_assert['margin_ratio']}")
    return margin_assert


def get_assure_security_list(engine):
    """
    担保券查询

    Args:
        engine: 回测引擎实例

    Returns:
        list: 担保券列表
    """
    # 模拟担保券列表
    assure_securities = [
        {
            'security': '000001.SZ',
            'name': '平安银行',
            'assure_ratio': 0.7,     # 担保品折算率
            'status': 'normal',
            'category': 'stock'
        },
        {
            'security': '600519.SH',
            'name': '贵州茅台',
            'assure_ratio': 0.7,
            'status': 'normal',
            'category': 'stock'
        },
        {
            'security': '510050.SH',
            'name': '50ETF',
            'assure_ratio': 0.9,
            'status': 'normal',
            'category': 'etf'
        }
    ]

    log.info(f"获取担保券列表: {len(assure_securities)}只")
    return assure_securities


def get_margincash_open_amount(engine, security):
    """
    融资标的最大可买数量查询

    Args:
        engine: 回测引擎实例
        security: 证券代码

    Returns:
        dict: 最大可买数量信息
    """
    margin_info = get_margin_assert(engine)
    available_amount = margin_info['available_margin_amount']

    # 假设当前价格
    current_price = 10.0  # 简化处理
    margin_ratio = 0.5    # 融资保证金比例

    # 计算最大可买数量
    max_buy_amount = int((available_amount / margin_ratio) / current_price)

    result = {
        'security': security,
        'max_buy_amount': max_buy_amount,
        'available_margin': available_amount,
        'current_price': current_price,
        'margin_ratio': margin_ratio
    }

    log.info(f"融资最大可买: {security}, {max_buy_amount}股")
    return result


def get_margincash_close_amount(engine, security):
    """
    卖券还款标的最大可卖数量查询

    Args:
        engine: 回测引擎实例
        security: 证券代码

    Returns:
        dict: 最大可卖数量信息
    """
    # 模拟持仓信息
    position_amount = 5000  # 假设持仓5000股

    result = {
        'security': security,
        'max_sell_amount': position_amount,
        'position_amount': position_amount,
        'available_amount': position_amount
    }

    log.info(f"卖券还款最大可卖: {security}, {position_amount}股")
    return result


def get_marginsec_open_amount(engine, security):
    """
    融券标的最大可卖数量查询

    Args:
        engine: 回测引擎实例
        security: 证券代码

    Returns:
        dict: 最大可卖数量信息
    """
    # 获取融券标的信息
    sec_stocks = get_marginsec_stocks(engine)
    sec_info = next((s for s in sec_stocks if s['security'] == security), None)

    if not sec_info:
        max_sell_amount = 0
    else:
        max_sell_amount = sec_info['available_amount']

    result = {
        'security': security,
        'max_sell_amount': max_sell_amount,
        'available_sec_amount': max_sell_amount,
        'sec_ratio': sec_info['sec_ratio'] if sec_info else 0.5
    }

    log.info(f"融券最大可卖: {security}, {max_sell_amount}股")
    return result


def get_marginsec_close_amount(engine, security):
    """
    买券还券标的最大可买数量查询

    Args:
        engine: 回测引擎实例
        security: 证券代码

    Returns:
        dict: 最大可买数量信息
    """
    # 模拟融券负债
    sec_debt_amount = 2000  # 假设融券负债2000股

    result = {
        'security': security,
        'max_buy_amount': sec_debt_amount,
        'sec_debt_amount': sec_debt_amount,
        'available_cash': 50000.0  # 可用资金
    }

    log.info(f"买券还券最大可买: {security}, {sec_debt_amount}股")
    return result


def get_margin_entrans_amount(engine, security):
    """
    现券还券数量查询

    Args:
        engine: 回测引擎实例
        security: 证券代码

    Returns:
        dict: 现券还券数量信息
    """
    # 模拟现券持仓
    cash_position = 1000  # 现券持仓
    sec_debt = 2000      # 融券负债

    # 可还券数量为现券持仓和融券负债的较小值
    available_return_amount = min(cash_position, sec_debt)

    result = {
        'security': security,
        'available_return_amount': available_return_amount,
        'cash_position': cash_position,
        'sec_debt_amount': sec_debt
    }

    log.info(f"现券还券可还: {security}, {available_return_amount}股")
    return result


def get_enslo_security_info(engine, security):
    """
    融券头寸信息查询

    Args:
        engine: 回测引擎实例
        security: 证券代码

    Returns:
        dict: 融券头寸信息
    """
    # 模拟融券头寸信息
    enslo_info = {
        'security': security,
        'total_enslo_amount': 1000000,    # 总融券头寸
        'available_enslo_amount': 50000,  # 可融券头寸
        'enslo_rate': 0.108,              # 融券费率
        'min_enslo_amount': 100,          # 最小融券数量
        'max_enslo_amount': 10000,        # 最大融券数量
        'enslo_status': 'normal'          # 融券状态
    }

    log.info(f"融券头寸信息: {security}, 可融券{enslo_info['available_enslo_amount']}股")
    return enslo_info
