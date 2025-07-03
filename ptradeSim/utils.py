# -*- coding: utf-8 -*-
"""
辅助工具函数模块
"""
from pathlib import Path
from .logger import log

def is_trade(engine):
    """模拟is_trade函数，回测模式下返回False"""
    return False

def get_research_path(engine):
    """模拟get_research_path函数"""
    return './'

def set_commission(engine, commission_ratio, min_commission):
    """模拟set_commission函数"""
    engine.commission_ratio = commission_ratio
    engine.min_commission = min_commission

def set_limit_mode(engine, mode):
    """模拟set_limit_mode函数"""
    pass

def run_interval(engine, context, func, seconds):
    """模拟run_interval函数"""
    pass

def clear_file(engine, file_path):
    """模拟clear_file函数, 会确保目录存在并删除文件"""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()

def get_initial_cash(engine, context, max_cash):
    """模拟get_initial_cash函数"""
    return min(context.portfolio.starting_cash, max_cash)

def get_num_of_positions(engine, context):
    """模拟get_num_of_positions函数"""
    return sum(1 for pos in context.portfolio.positions.values() if pos.amount > 0)

def get_Ashares(engine, date=None):
    """模拟get_Ashares函数，返回数据文件中所有可用的股票"""
    return list(engine.data.keys())

def get_stock_status(engine, stocks, query_type='ST', query_date=None):
    """模拟get_stock_status函数，假设所有股票状态正常"""
    if isinstance(stocks, str):
        stocks = [stocks]
    return {s: False for s in stocks}

def get_stock_info(engine, stocks, field=None):
    """模拟get_stock_info函数"""
    if isinstance(stocks, str):
        stocks = [stocks]
    
    all_fields = {
        'stock_name': '默认名称',
        'listed_date': '2020-01-01',
        'de_listed_date': '2900-01-01'
    }
    
    if field is None:
        field = ['stock_name']
    
    if isinstance(field, str):
        field = [field]

    result = {}
    for s in stocks:
        result[s] = {f: all_fields.get(f, 'N/A') for f in field}
    return result

def get_stock_name(engine, stocks):
    """模拟get_stock_name函数"""
    info = get_stock_info(engine, stocks, field='stock_name')
    return {k: v['stock_name'] for k, v in info.items()}

def set_universe(engine, stocks):
    """模拟set_universe函数，设置股票池"""
    if isinstance(stocks, str):
        stocks = [stocks]
    log.info(f"设置股票池: {stocks}")