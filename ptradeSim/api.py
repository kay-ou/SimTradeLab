# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from .context import Position
from pathlib import Path

# --- Logging ---
class Logger:
    """模拟日志记录器，支持ptrade风格的时间戳格式"""
    LEVEL_INFO = "INFO"

    def __init__(self):
        self.current_dt = None  # 由引擎设置当前时间

    def set_log_level(self, level):
        pass

    def _format_timestamp(self):
        """格式化时间戳，模拟ptrade格式"""
        if self.current_dt:
            return self.current_dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            from datetime import datetime
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def info(self, msg):
        timestamp = self._format_timestamp()
        print(f"{timestamp} - INFO - {msg}")

    def warning(self, msg):
        timestamp = self._format_timestamp()
        print(f"{timestamp} - WARNING - {msg}")

log = Logger()

# --- Environment & Config ---
def is_trade(engine):
    """模拟is_trade函数，回测模式下返回False"""
    return False

def get_research_path(engine):
    """模拟get_research_path函数"""
    return './'

def set_commission(engine, commission_ratio, min_commission, type):
    """模拟set_commission函数"""
    pass

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

# --- Account & Position ---
def get_initial_cash(engine, context, max_cash):
    """模拟get_initial_cash函数"""
    return min(context.portfolio.starting_cash, max_cash)

def get_num_of_positions(engine, context):
    """模拟get_num_of_positions函数"""
    return sum(1 for pos in context.portfolio.positions.values() if pos.amount > 0)

# --- Market Data ---
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

def get_fundamentals(engine, stocks, table, fields=None, date=None, start_year=None, end_year=None, report_types=None, merge_type=None, date_type=None):
    """模拟get_fundamentals函数，为shadow_strategy提供所需字段"""
    if isinstance(stocks, str):
        stocks = [stocks]
    
    # 返回固定的、符合策略要求的数据，而不是随机数
    # Return fixed data that meets strategy requirements, not random numbers.
    fixed_data = {
        'turnover_rate': 15.0,  # 在 区间内
        'total_value': 50e8,    # 在 [10e8, 200e8] 区间内
    }
    
    data = {
        'turnover_rate': [fixed_data['turnover_rate']] * len(stocks),
        'total_value': [fixed_data['total_value']] * len(stocks)
    }
    
    return pd.DataFrame(data, index=stocks)

def get_history(engine, count, frequency='1d', field='close', security_list=None, fq=None, include=False, is_dict=False):
    """模拟get_history函数"""
    if security_list is None:
        security_list = list(engine.data.keys())
    
    if isinstance(field, str):
        field = [field]

    if is_dict:
        # 策略代码期望一个 {stock: {field: array}} 结构
        # The strategy code expects a {stock: {field: array}} structure.
        result = {}
        for sec in security_list:
            if sec in engine.data:
                hist_df = engine.data[sec]
                end_date = engine.context.current_dt
                valid_hist = hist_df[hist_df.index <= end_date].tail(count)
                
                if not valid_hist.empty:
                    # 将DataFrame转换为策略期望的 {field: numpy_array} 字典
                    result[sec] = {col: valid_hist[col].to_numpy() for col in valid_hist.columns if col in field}
                else:
                    result[sec] = {col: np.array([]) for col in field}
        return result
    
    # Panel return is not fully implemented for simplicity
    return {}

def get_price(engine, security, start_date=None, end_date=None, frequency='1d', fields=None, count=None):
    """模拟get_price函数"""
    if count is None:
        count = 1
    
    if isinstance(security, str):
        security = [security]
        
    if fields is None:
        fields = ['close']
    
    if isinstance(fields, str):
        fields = [fields]

    result_df = pd.DataFrame()
    for sec in security:
        if sec in engine.data:
            hist_df = engine.data[sec]
            end_date = engine.context.current_dt
            valid_hist = hist_df[hist_df.index < end_date]
            data = valid_hist.tail(count)[fields]
            for f in fields:
                result_df.loc[data.index, sec] = data[f]
    return result_df

# --- Trading ---
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
            
    # 生成模拟订单号
    import uuid
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
    amount = int(value / price)
    amount = int(amount / 100) * 100 # A股以100股为单位
    if amount == 0:
        return None
    return order(engine, security, amount)

def cancel_order(engine, order_param):
    """模拟cancel_order函数"""
    log.info(f"取消订单: {order_param}")

def set_universe(engine, stocks):
    """模拟set_universe函数，设置股票池"""
    if isinstance(stocks, str):
        stocks = [stocks]
    log.info(f"设置股票池: {stocks}")
    # 在模拟环境中，这个函数主要用于日志记录