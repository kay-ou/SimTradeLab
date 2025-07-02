# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import hashlib
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
    """
    模拟get_fundamentals函数，提供丰富的财务基本面数据

    参数:
        engine: 回测引擎
        stocks: 股票代码或股票代码列表
        table: 数据表类型 ('valuation', 'income', 'balance_sheet', 'cash_flow', 'indicator')
        fields: 需要的字段列表，如果为None则返回所有字段
        date: 查询日期
        其他参数: 兼容性参数

    返回:
        pandas.DataFrame: 包含财务数据的DataFrame
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    # 定义各类财务数据的模拟值，基于真实市场的合理范围
    all_fundamentals_data = {
        # 估值指标 (valuation)
        'market_cap': 50e8,         # 市值 (50亿)
        'total_value': 50e8,        # 总市值 (兼容原有字段)
        'pe_ratio': 25.5,           # 市盈率
        'pb_ratio': 3.2,            # 市净率
        'ps_ratio': 4.8,            # 市销率
        'pcf_ratio': 15.2,          # 市现率
        'turnover_rate': 15.0,      # 换手率 (兼容原有字段)

        # 盈利能力指标 (income/profitability)
        'revenue': 120e8,           # 营业收入 (120亿)
        'net_income': 8e8,          # 净利润 (8亿)
        'gross_profit': 45e8,       # 毛利润 (45亿)
        'operating_profit': 15e8,   # 营业利润 (15亿)
        'eps': 2.85,                # 每股收益
        'roe': 15.8,                # 净资产收益率 (%)
        'roa': 8.5,                 # 总资产收益率 (%)
        'gross_margin': 37.5,       # 毛利率 (%)
        'net_margin': 6.7,          # 净利率 (%)

        # 资产负债指标 (balance_sheet)
        'total_assets': 180e8,      # 总资产 (180亿)
        'total_liabilities': 95e8,  # 总负债 (95亿)
        'total_equity': 85e8,       # 股东权益 (85亿)
        'current_assets': 75e8,     # 流动资产 (75亿)
        'current_liabilities': 45e8, # 流动负债 (45亿)
        'debt_to_equity': 0.45,     # 资产负债率
        'current_ratio': 1.67,      # 流动比率
        'quick_ratio': 1.25,        # 速动比率

        # 现金流指标 (cash_flow)
        'operating_cash_flow': 12e8,    # 经营现金流 (12亿)
        'investing_cash_flow': -5e8,    # 投资现金流 (-5亿)
        'financing_cash_flow': -3e8,    # 筹资现金流 (-3亿)
        'free_cash_flow': 7e8,          # 自由现金流 (7亿)

        # 运营效率指标 (indicator)
        'inventory_turnover': 8.5,      # 存货周转率
        'receivables_turnover': 12.3,   # 应收账款周转率
        'asset_turnover': 1.2,          # 总资产周转率
        'equity_turnover': 2.1,         # 股东权益周转率
    }

    # 根据table参数筛选相关字段
    table_field_mapping = {
        'valuation': ['market_cap', 'total_value', 'pe_ratio', 'pb_ratio', 'ps_ratio', 'pcf_ratio', 'turnover_rate'],
        'income': ['revenue', 'net_income', 'gross_profit', 'operating_profit', 'eps', 'roe', 'roa', 'gross_margin', 'net_margin'],
        'balance_sheet': ['total_assets', 'total_liabilities', 'total_equity', 'current_assets', 'current_liabilities', 'debt_to_equity', 'current_ratio', 'quick_ratio'],
        'cash_flow': ['operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'free_cash_flow'],
        'indicator': ['inventory_turnover', 'receivables_turnover', 'asset_turnover', 'equity_turnover', 'roe', 'roa']
    }

    # 确定要返回的字段
    if fields is None:
        # 如果没有指定fields，根据table返回相应字段
        if table in table_field_mapping:
            selected_fields = table_field_mapping[table]
        else:
            # 如果table不在映射中，返回所有字段
            selected_fields = list(all_fundamentals_data.keys())
    else:
        # 如果指定了fields，使用指定的字段
        if isinstance(fields, str):
            selected_fields = [fields]
        else:
            selected_fields = fields

    # 构建返回数据
    data = {}
    for field in selected_fields:
        if field in all_fundamentals_data:
            # 为每个股票添加一些随机变化，使数据更真实
            base_value = all_fundamentals_data[field]
            values = []
            for i, stock in enumerate(stocks):
                # 基于股票代码生成一致的随机因子，确保同一股票的数据一致
                hash_factor = int(hashlib.md5(stock.encode()).hexdigest()[:8], 16) / 0xffffffff
                # 在基准值的±20%范围内变化
                variation = 0.8 + 0.4 * hash_factor
                values.append(base_value * variation)
            data[field] = values
        else:
            # 如果字段不存在，返回None值
            log.warning(f"财务数据字段 '{field}' 不存在，返回None值")
            data[field] = [None] * len(stocks)

    return pd.DataFrame(data, index=stocks)

def get_income_statement(engine, stocks, fields=None, date=None, count=4):
    """
    获取损益表数据

    参数:
        engine: 回测引擎
        stocks: 股票代码或股票代码列表
        fields: 需要的字段列表，如果为None则返回所有字段
        date: 查询日期
        count: 返回的报告期数量，默认4期

    返回:
        pandas.DataFrame: 包含损益表数据的DataFrame
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    # 损益表数据模拟
    income_statement_data = {
        'revenue': 120e8,                    # 营业收入
        'cost_of_revenue': 75e8,            # 营业成本
        'gross_profit': 45e8,               # 毛利润
        'operating_expenses': 30e8,         # 营业费用
        'operating_profit': 15e8,           # 营业利润
        'interest_expense': 2e8,            # 利息费用
        'other_income': 1e8,                # 其他收益
        'profit_before_tax': 14e8,          # 税前利润
        'income_tax': 6e8,                  # 所得税费用
        'net_income': 8e8,                  # 净利润
        'eps_basic': 2.85,                  # 基本每股收益
        'eps_diluted': 2.80,                # 稀释每股收益
        'shares_outstanding': 2.8e8,        # 流通股本
    }

    # 确定要返回的字段
    if fields is None:
        selected_fields = list(income_statement_data.keys())
    else:
        if isinstance(fields, str):
            selected_fields = [fields]
        else:
            selected_fields = fields

    # 构建返回数据
    data = {}
    for field in selected_fields:
        if field in income_statement_data:
            base_value = income_statement_data[field]
            values = []
            for stock in stocks:
                # 基于股票代码生成一致的随机因子
                hash_factor = int(hashlib.md5(stock.encode()).hexdigest()[:8], 16) / 0xffffffff
                variation = 0.8 + 0.4 * hash_factor
                values.append(base_value * variation)
            data[field] = values
        else:
            log.warning(f"损益表字段 '{field}' 不存在，返回None值")
            data[field] = [None] * len(stocks)

    return pd.DataFrame(data, index=stocks)

def get_balance_sheet(engine, stocks, fields=None, date=None, count=4):
    """
    获取资产负债表数据

    参数:
        engine: 回测引擎
        stocks: 股票代码或股票代码列表
        fields: 需要的字段列表，如果为None则返回所有字段
        date: 查询日期
        count: 返回的报告期数量，默认4期

    返回:
        pandas.DataFrame: 包含资产负债表数据的DataFrame
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    # 资产负债表数据模拟
    balance_sheet_data = {
        # 资产
        'total_assets': 180e8,              # 总资产
        'current_assets': 75e8,             # 流动资产
        'cash_and_equivalents': 25e8,       # 货币资金
        'accounts_receivable': 20e8,        # 应收账款
        'inventory': 15e8,                  # 存货
        'other_current_assets': 15e8,       # 其他流动资产
        'non_current_assets': 105e8,        # 非流动资产
        'property_plant_equipment': 80e8,   # 固定资产
        'intangible_assets': 15e8,          # 无形资产
        'goodwill': 10e8,                   # 商誉

        # 负债
        'total_liabilities': 95e8,          # 总负债
        'current_liabilities': 45e8,        # 流动负债
        'accounts_payable': 18e8,           # 应付账款
        'short_term_debt': 12e8,            # 短期借款
        'other_current_liabilities': 15e8,  # 其他流动负债
        'non_current_liabilities': 50e8,    # 非流动负债
        'long_term_debt': 35e8,             # 长期借款
        'other_non_current_liabilities': 15e8, # 其他非流动负债

        # 股东权益
        'total_equity': 85e8,               # 股东权益合计
        'share_capital': 28e8,              # 股本
        'retained_earnings': 45e8,          # 留存收益
        'other_equity': 12e8,               # 其他权益工具
    }

    # 确定要返回的字段
    if fields is None:
        selected_fields = list(balance_sheet_data.keys())
    else:
        if isinstance(fields, str):
            selected_fields = [fields]
        else:
            selected_fields = fields

    # 构建返回数据
    data = {}
    for field in selected_fields:
        if field in balance_sheet_data:
            base_value = balance_sheet_data[field]
            values = []
            for stock in stocks:
                # 基于股票代码生成一致的随机因子
                hash_factor = int(hashlib.md5(stock.encode()).hexdigest()[:8], 16) / 0xffffffff
                variation = 0.8 + 0.4 * hash_factor
                values.append(base_value * variation)
            data[field] = values
        else:
            log.warning(f"资产负债表字段 '{field}' 不存在，返回None值")
            data[field] = [None] * len(stocks)

    return pd.DataFrame(data, index=stocks)

def get_cash_flow(engine, stocks, fields=None, date=None, count=4):
    """
    获取现金流量表数据

    参数:
        engine: 回测引擎
        stocks: 股票代码或股票代码列表
        fields: 需要的字段列表，如果为None则返回所有字段
        date: 查询日期
        count: 返回的报告期数量，默认4期

    返回:
        pandas.DataFrame: 包含现金流量表数据的DataFrame
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    # 现金流量表数据模拟
    cash_flow_data = {
        # 经营活动现金流
        'operating_cash_flow': 12e8,        # 经营活动现金流量净额
        'net_income_cf': 8e8,               # 净利润
        'depreciation': 5e8,                # 折旧摊销
        'working_capital_change': -1e8,     # 营运资金变动
        'other_operating_activities': 0,    # 其他经营活动

        # 投资活动现金流
        'investing_cash_flow': -5e8,        # 投资活动现金流量净额
        'capital_expenditure': -6e8,        # 资本支出
        'acquisitions': -2e8,               # 收购支出
        'asset_sales': 1e8,                 # 资产处置收入
        'investment_purchases': -1e8,       # 投资支出
        'other_investing_activities': 3e8,  # 其他投资活动

        # 筹资活动现金流
        'financing_cash_flow': -3e8,        # 筹资活动现金流量净额
        'debt_issuance': 5e8,               # 债务发行
        'debt_repayment': -4e8,             # 债务偿还
        'equity_issuance': 2e8,             # 股权发行
        'dividends_paid': -3e8,             # 股利支付
        'share_repurchase': -2e8,           # 股份回购
        'other_financing_activities': -1e8, # 其他筹资活动

        # 汇总
        'free_cash_flow': 7e8,              # 自由现金流
        'net_cash_change': 4e8,             # 现金净变动
    }

    # 确定要返回的字段
    if fields is None:
        selected_fields = list(cash_flow_data.keys())
    else:
        if isinstance(fields, str):
            selected_fields = [fields]
        else:
            selected_fields = fields

    # 构建返回数据
    data = {}
    for field in selected_fields:
        if field in cash_flow_data:
            base_value = cash_flow_data[field]
            values = []
            for stock in stocks:
                # 基于股票代码生成一致的随机因子
                hash_factor = int(hashlib.md5(stock.encode()).hexdigest()[:8], 16) / 0xffffffff
                variation = 0.8 + 0.4 * hash_factor
                values.append(base_value * variation)
            data[field] = values
        else:
            log.warning(f"现金流量表字段 '{field}' 不存在，返回None值")
            data[field] = [None] * len(stocks)

    return pd.DataFrame(data, index=stocks)

def get_financial_ratios(engine, stocks, fields=None, date=None):
    """
    获取财务比率数据

    参数:
        engine: 回测引擎
        stocks: 股票代码或股票代码列表
        fields: 需要的字段列表，如果为None则返回所有字段
        date: 查询日期

    返回:
        pandas.DataFrame: 包含财务比率数据的DataFrame
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    # 财务比率数据模拟
    financial_ratios_data = {
        # 流动性比率
        'current_ratio': 1.67,              # 流动比率 = 流动资产/流动负债
        'quick_ratio': 1.25,                # 速动比率 = (流动资产-存货)/流动负债
        'cash_ratio': 0.56,                 # 现金比率 = 现金/流动负债
        'operating_cash_flow_ratio': 0.27,  # 经营现金流比率 = 经营现金流/流动负债

        # 杠杆比率
        'debt_to_equity': 0.45,             # 资产负债率 = 总负债/股东权益
        'debt_to_assets': 0.31,             # 负债资产比 = 总负债/总资产
        'equity_ratio': 0.47,               # 股东权益比率 = 股东权益/总资产
        'interest_coverage': 7.5,           # 利息保障倍数 = 息税前利润/利息费用
        'debt_service_coverage': 2.8,       # 偿债保障比率

        # 盈利能力比率
        'gross_margin': 37.5,               # 毛利率 = 毛利润/营业收入
        'operating_margin': 12.5,           # 营业利润率 = 营业利润/营业收入
        'net_margin': 6.7,                  # 净利率 = 净利润/营业收入
        'roe': 15.8,                        # 净资产收益率 = 净利润/股东权益
        'roa': 8.5,                         # 总资产收益率 = 净利润/总资产
        'roic': 12.3,                       # 投入资本回报率

        # 效率比率
        'asset_turnover': 1.2,              # 总资产周转率 = 营业收入/总资产
        'inventory_turnover': 8.5,          # 存货周转率 = 营业成本/存货
        'receivables_turnover': 12.3,       # 应收账款周转率 = 营业收入/应收账款
        'payables_turnover': 6.8,           # 应付账款周转率 = 营业成本/应付账款
        'equity_turnover': 2.1,             # 股东权益周转率 = 营业收入/股东权益
        'working_capital_turnover': 4.2,    # 营运资金周转率

        # 估值比率
        'pe_ratio': 25.5,                   # 市盈率 = 股价/每股收益
        'pb_ratio': 3.2,                    # 市净率 = 股价/每股净资产
        'ps_ratio': 4.8,                    # 市销率 = 市值/营业收入
        'pcf_ratio': 15.2,                  # 市现率 = 市值/经营现金流
        'ev_ebitda': 18.5,                  # 企业价值倍数
        'dividend_yield': 2.8,              # 股息收益率
        'peg_ratio': 1.5,                   # PEG比率 = PE/增长率

        # 市场表现比率
        'book_value_per_share': 30.4,       # 每股净资产
        'tangible_book_value_per_share': 28.1, # 每股有形净资产
        'sales_per_share': 42.9,            # 每股销售额
        'cash_per_share': 8.9,              # 每股现金
        'free_cash_flow_per_share': 2.5,    # 每股自由现金流
    }

    # 确定要返回的字段
    if fields is None:
        selected_fields = list(financial_ratios_data.keys())
    else:
        if isinstance(fields, str):
            selected_fields = [fields]
        else:
            selected_fields = fields

    # 构建返回数据
    data = {}
    for field in selected_fields:
        if field in financial_ratios_data:
            base_value = financial_ratios_data[field]
            values = []
            for stock in stocks:
                # 基于股票代码生成一致的随机因子
                hash_factor = int(hashlib.md5(stock.encode()).hexdigest()[:8], 16) / 0xffffffff
                variation = 0.8 + 0.4 * hash_factor
                values.append(base_value * variation)
            data[field] = values
        else:
            log.warning(f"财务比率字段 '{field}' 不存在，返回None值")
            data[field] = [None] * len(stocks)

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