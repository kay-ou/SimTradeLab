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

def get_history(engine, count, frequency='1d', field='close', security_list=None, fq=None, include=False, is_dict=False, start_date=None, end_date=None):
    """
    增强的历史数据获取函数，支持多种时间频率和数据字段

    参数:
        engine: 回测引擎
        count: 获取的数据条数
        frequency: 数据频率 ('1d', '1m', '5m', '15m', '30m', '1h', '1w', '1M')
        field: 需要的字段，可以是字符串或列表
        security_list: 股票代码列表
        fq: 复权类型 ('pre', 'post', None)
        include: 是否包含当前时间点
        is_dict: 是否返回字典格式
        start_date: 开始日期
        end_date: 结束日期

    支持的字段:
        基础: open, high, low, close, volume
        扩展: pre_close, change, pct_change, amplitude, turnover_rate, amount, vwap

    返回:
        dict 或 pandas.DataFrame: 历史数据
    """
    if security_list is None:
        security_list = list(engine.data.keys())

    if isinstance(field, str):
        field = [field]

    # 支持的频率映射
    frequency_mapping = {
        '1d': 'D', 'daily': 'D',
        '1m': 'T', 'minute': 'T',
        '5m': '5T', '5min': '5T',
        '15m': '15T', '15min': '15T',
        '30m': '30T', '30min': '30T',
        '1h': 'H', 'hour': 'H',
        '1w': 'W', 'week': 'W',
        '1M': 'M', 'month': 'M'
    }

    pandas_freq = frequency_mapping.get(frequency, 'D')

    # 支持的扩展字段
    extended_fields = {
        'pre_close', 'change', 'pct_change', 'amplitude',
        'turnover_rate', 'amount', 'vwap', 'high_limit', 'low_limit'
    }

    if is_dict:
        # 策略代码期望一个 {stock: {field: array}} 结构
        result = {}
        for sec in security_list:
            if sec not in engine.data:
                result[sec] = {col: np.array([]) for col in field}
                continue

            hist_df = engine.data[sec].copy()

            # 处理时间范围
            if hasattr(engine, 'context') and engine.context.current_dt:
                if include:
                    valid_hist = hist_df[hist_df.index <= engine.context.current_dt]
                else:
                    valid_hist = hist_df[hist_df.index < engine.context.current_dt]
            else:
                valid_hist = hist_df

            # 应用日期范围过滤
            if start_date:
                valid_hist = valid_hist[valid_hist.index >= pd.to_datetime(start_date)]
            if end_date:
                valid_hist = valid_hist[valid_hist.index <= pd.to_datetime(end_date)]

            # 处理频率转换（如果不是日线）
            if pandas_freq != 'D' and len(valid_hist) > 0:
                # 对于非日线数据，进行重采样模拟
                if pandas_freq in ['T', '5T', '15T', '30T', 'H']:
                    # 分钟级数据：将日线数据拆分为分钟数据
                    expanded_data = []
                    for idx, row in valid_hist.iterrows():
                        # 每天生成对应频率的数据点
                        if pandas_freq == 'T':
                            periods_per_day = 240  # 4小时交易时间
                        elif pandas_freq == '5T':
                            periods_per_day = 48
                        elif pandas_freq == '15T':
                            periods_per_day = 16
                        elif pandas_freq == '30T':
                            periods_per_day = 8
                        elif pandas_freq == 'H':
                            periods_per_day = 4

                        # 生成当天的分钟级时间索引
                        day_start = idx.replace(hour=9, minute=30)
                        time_range = pd.date_range(start=day_start, periods=periods_per_day, freq=pandas_freq)

                        # 模拟分钟级价格波动
                        daily_range = row['high'] - row['low']
                        for i, minute_time in enumerate(time_range):
                            # 基于时间生成价格波动
                            progress = i / periods_per_day
                            noise = np.random.normal(0, daily_range * 0.01)  # 1%的随机波动

                            minute_close = row['low'] + daily_range * progress + noise
                            minute_close = max(row['low'], min(row['high'], minute_close))

                            expanded_data.append({
                                'open': minute_close * (1 + np.random.normal(0, 0.001)),
                                'high': minute_close * (1 + abs(np.random.normal(0, 0.002))),
                                'low': minute_close * (1 - abs(np.random.normal(0, 0.002))),
                                'close': minute_close,
                                'volume': row['volume'] / periods_per_day
                            })

                    if expanded_data:
                        valid_hist = pd.DataFrame(expanded_data)
                        valid_hist.index = pd.date_range(
                            start=valid_hist.index[0].replace(hour=9, minute=30),
                            periods=len(expanded_data),
                            freq=pandas_freq
                        )

                elif pandas_freq in ['W', 'M']:
                    # 周线或月线：对日线数据进行聚合
                    valid_hist = valid_hist.resample(pandas_freq).agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()

            # 获取指定数量的最新数据
            if count and len(valid_hist) > count:
                valid_hist = valid_hist.tail(count)

            if valid_hist.empty:
                result[sec] = {col: np.array([]) for col in field}
                continue

            # 计算扩展字段
            for ext_field in field:
                if ext_field in extended_fields:
                    if ext_field == 'pre_close':
                        valid_hist['pre_close'] = valid_hist['close'].shift(1)
                    elif ext_field == 'change':
                        valid_hist['change'] = valid_hist['close'] - valid_hist['close'].shift(1)
                    elif ext_field == 'pct_change':
                        valid_hist['pct_change'] = (valid_hist['close'] / valid_hist['close'].shift(1) - 1) * 100
                    elif ext_field == 'amplitude':
                        pre_close = valid_hist['close'].shift(1)
                        valid_hist['amplitude'] = ((valid_hist['high'] - valid_hist['low']) / pre_close) * 100
                    elif ext_field == 'turnover_rate':
                        # 基于股票代码生成一致的换手率
                        hash_factor = int(hashlib.md5(sec.encode()).hexdigest()[:8], 16) / 0xffffffff
                        base_turnover = 2.5 + 5.0 * hash_factor
                        valid_hist['turnover_rate'] = base_turnover
                    elif ext_field == 'amount':
                        valid_hist['amount'] = valid_hist['volume'] * valid_hist['close'] / 10000
                    elif ext_field == 'vwap':
                        valid_hist['vwap'] = (valid_hist['high'] + valid_hist['low'] + valid_hist['close'] * 2) / 4
                    elif ext_field == 'high_limit':
                        pre_close = valid_hist['close'].shift(1)
                        valid_hist['high_limit'] = pre_close * 1.1
                    elif ext_field == 'low_limit':
                        pre_close = valid_hist['close'].shift(1)
                        valid_hist['low_limit'] = pre_close * 0.9

            # 将DataFrame转换为策略期望的 {field: numpy_array} 字典
            result[sec] = {}
            for col in field:
                if col in valid_hist.columns:
                    result[sec][col] = valid_hist[col].to_numpy()
                else:
                    log.warning(f"字段 '{col}' 不存在于股票 {sec} 的数据中")
                    result[sec][col] = np.array([])

        return result

    else:
        # 返回DataFrame格式
        result_df = pd.DataFrame()

        for sec in security_list:
            if sec not in engine.data:
                continue

            hist_df = engine.data[sec].copy()

            # 处理时间范围
            if hasattr(engine, 'context') and engine.context.current_dt:
                if include:
                    valid_hist = hist_df[hist_df.index <= engine.context.current_dt]
                else:
                    valid_hist = hist_df[hist_df.index < engine.context.current_dt]
            else:
                valid_hist = hist_df

            # 应用日期范围过滤
            if start_date:
                valid_hist = valid_hist[valid_hist.index >= pd.to_datetime(start_date)]
            if end_date:
                valid_hist = valid_hist[valid_hist.index <= pd.to_datetime(end_date)]

            # 获取指定数量的最新数据
            if count and len(valid_hist) > count:
                valid_hist = valid_hist.tail(count)

            if valid_hist.empty:
                continue

            # 为每个字段创建列
            for f in field:
                if f in valid_hist.columns:
                    result_df[(f, sec)] = valid_hist[f]
                else:
                    log.warning(f"字段 '{f}' 不存在")

        return result_df

def get_price(engine, security, start_date=None, end_date=None, frequency='1d', fields=None, count=None):
    """
    增强的价格数据获取函数，支持更多市场数据字段

    参数:
        engine: 回测引擎
        security: 股票代码或股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        frequency: 数据频率 ('1d', '1m', '5m', '15m', '30m', '1h')
        fields: 需要的字段列表
        count: 返回的数据条数

    支持的字段:
        基础价格: open, high, low, close, volume
        扩展字段: pre_close, change, pct_change, amplitude, turnover_rate,
                 vwap, amount, high_limit, low_limit

    返回:
        pandas.DataFrame: 包含价格数据的DataFrame
    """
    if count is None:
        count = 1

    if isinstance(security, str):
        security = [security]

    if fields is None:
        fields = ['close']

    if isinstance(fields, str):
        fields = [fields]

    # 定义所有支持的字段
    all_supported_fields = {
        'open', 'high', 'low', 'close', 'volume',  # 基础OHLCV
        'pre_close', 'change', 'pct_change', 'amplitude',  # 涨跌数据
        'turnover_rate', 'vwap', 'amount',  # 成交数据
        'high_limit', 'low_limit'  # 涨跌停价格
    }

    result_data = {}

    for sec in security:
        if sec not in engine.data:
            log.warning(f"股票 {sec} 的数据不存在")
            continue

        hist_df = engine.data[sec]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None

        if current_dt:
            valid_hist = hist_df[hist_df.index < current_dt]
        else:
            valid_hist = hist_df

        if valid_hist.empty:
            log.warning(f"股票 {sec} 没有有效的历史数据")
            continue

        # 获取指定数量的最新数据
        recent_data = valid_hist.tail(count)

        # 为每个请求的字段计算数据
        for field in fields:
            if field in recent_data.columns:
                # 直接从数据文件获取的字段
                if sec not in result_data:
                    result_data[sec] = {}
                result_data[sec][field] = recent_data[field].tolist()

            elif field in all_supported_fields:
                # 需要计算的扩展字段
                if sec not in result_data:
                    result_data[sec] = {}

                calculated_values = []
                for i, (idx, row) in enumerate(recent_data.iterrows()):
                    if field == 'pre_close':
                        # 前收盘价
                        if i == 0 and len(valid_hist) > count:
                            # 获取前一天的收盘价
                            prev_data = valid_hist.iloc[-(count+1)]
                            calculated_values.append(prev_data['close'])
                        else:
                            calculated_values.append(row['close'] * 0.98)  # 模拟前收盘价

                    elif field == 'change':
                        # 涨跌额
                        pre_close = row['close'] * 0.98  # 模拟前收盘价
                        calculated_values.append(row['close'] - pre_close)

                    elif field == 'pct_change':
                        # 涨跌幅 (%)
                        pre_close = row['close'] * 0.98  # 模拟前收盘价
                        pct = ((row['close'] - pre_close) / pre_close) * 100
                        calculated_values.append(pct)

                    elif field == 'amplitude':
                        # 振幅 (%)
                        pre_close = row['close'] * 0.98  # 模拟前收盘价
                        amp = ((row['high'] - row['low']) / pre_close) * 100
                        calculated_values.append(amp)

                    elif field == 'turnover_rate':
                        # 换手率 (%)，基于股票代码生成一致的模拟值
                        hash_factor = int(hashlib.md5(sec.encode()).hexdigest()[:8], 16) / 0xffffffff
                        base_turnover = 2.5 + 5.0 * hash_factor  # 2.5%-7.5%范围
                        calculated_values.append(base_turnover)

                    elif field == 'vwap':
                        # 成交量加权平均价
                        vwap = (row['high'] + row['low'] + row['close'] * 2) / 4
                        calculated_values.append(vwap)

                    elif field == 'amount':
                        # 成交额 (万元)
                        amount = row['volume'] * row['close'] / 10000
                        calculated_values.append(amount)

                    elif field == 'high_limit':
                        # 涨停价
                        pre_close = row['close'] * 0.98  # 模拟前收盘价
                        calculated_values.append(pre_close * 1.1)  # 10%涨停

                    elif field == 'low_limit':
                        # 跌停价
                        pre_close = row['close'] * 0.98  # 模拟前收盘价
                        calculated_values.append(pre_close * 0.9)  # 10%跌停

                result_data[sec][field] = calculated_values

            else:
                log.warning(f"不支持的字段: {field}")
                if sec not in result_data:
                    result_data[sec] = {}
                result_data[sec][field] = [None] * count

    # 转换为DataFrame格式
    if not result_data:
        return pd.DataFrame()

    # 构建多级索引的DataFrame
    result_df = pd.DataFrame()

    # 获取时间索引
    if security and security[0] in engine.data:
        sample_data = engine.data[security[0]]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None
        if current_dt:
            valid_hist = sample_data[sample_data.index < current_dt]
        else:
            valid_hist = sample_data
        time_index = valid_hist.tail(count).index
    else:
        time_index = pd.date_range(start='2023-01-01', periods=count, freq='D')

    # 为每个字段和股票组合创建列
    for field in fields:
        for sec in security:
            if sec in result_data and field in result_data[sec]:
                values = result_data[sec][field]
                # 确保值的数量与时间索引匹配
                if len(values) == len(time_index):
                    result_df[(field, sec)] = pd.Series(values, index=time_index)
                else:
                    log.warning(f"数据长度不匹配: {sec}.{field}")

    # 如果只有一个字段，简化列名
    if len(fields) == 1:
        result_df.columns = [col[1] for col in result_df.columns]

    return result_df

def get_current_data(engine, security=None):
    """
    获取当前实时市场数据

    参数:
        engine: 回测引擎
        security: 股票代码或股票代码列表，如果为None则返回所有股票

    返回:
        dict: 包含实时市场数据的字典
    """
    if security is None:
        security = list(engine.data.keys())
    elif isinstance(security, str):
        security = [security]

    current_data = {}

    for sec in security:
        if sec not in engine.data:
            log.warning(f"股票 {sec} 的数据不存在")
            continue

        hist_df = engine.data[sec]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None

        if current_dt:
            valid_hist = hist_df[hist_df.index <= current_dt]
        else:
            valid_hist = hist_df

        if valid_hist.empty:
            continue

        # 获取最新数据
        latest_data = valid_hist.iloc[-1]

        # 基于股票代码生成一致的模拟实时数据
        hash_factor = int(hashlib.md5(sec.encode()).hexdigest()[:8], 16) / 0xffffffff

        # 模拟买卖盘数据
        current_price = latest_data['close']
        spread = current_price * 0.001  # 0.1%的买卖价差

        current_data[sec] = {
            # 基础价格数据
            'open': latest_data['open'],
            'high': latest_data['high'],
            'low': latest_data['low'],
            'close': current_price,
            'volume': latest_data['volume'],

            # 买卖盘数据 (五档)
            'bid1': current_price - spread,
            'bid2': current_price - spread * 2,
            'bid3': current_price - spread * 3,
            'bid4': current_price - spread * 4,
            'bid5': current_price - spread * 5,
            'ask1': current_price + spread,
            'ask2': current_price + spread * 2,
            'ask3': current_price + spread * 3,
            'ask4': current_price + spread * 4,
            'ask5': current_price + spread * 5,

            # 买卖盘量 (手)
            'bid1_volume': int(1000 + 5000 * hash_factor),
            'bid2_volume': int(800 + 4000 * hash_factor),
            'bid3_volume': int(600 + 3000 * hash_factor),
            'bid4_volume': int(400 + 2000 * hash_factor),
            'bid5_volume': int(200 + 1000 * hash_factor),
            'ask1_volume': int(1200 + 5500 * hash_factor),
            'ask2_volume': int(900 + 4500 * hash_factor),
            'ask3_volume': int(700 + 3500 * hash_factor),
            'ask4_volume': int(500 + 2500 * hash_factor),
            'ask5_volume': int(300 + 1500 * hash_factor),

            # 涨跌数据
            'pre_close': current_price * 0.98,
            'change': current_price * 0.02,
            'pct_change': 2.04,  # 2.04%

            # 成交数据
            'amount': latest_data['volume'] * current_price / 10000,  # 成交额(万元)
            'turnover_rate': 2.5 + 5.0 * hash_factor,  # 换手率(%)

            # 其他数据
            'high_limit': current_price * 0.98 * 1.1,  # 涨停价
            'low_limit': current_price * 0.98 * 0.9,   # 跌停价
            'amplitude': ((latest_data['high'] - latest_data['low']) / (current_price * 0.98)) * 100,  # 振幅(%)
            'vwap': (latest_data['high'] + latest_data['low'] + current_price * 2) / 4,  # 均价
        }

    return current_data

def get_market_snapshot(engine, security=None, fields=None):
    """
    获取市场快照数据

    参数:
        engine: 回测引擎
        security: 股票代码或股票代码列表
        fields: 需要的字段列表

    返回:
        pandas.DataFrame: 包含市场快照数据的DataFrame
    """
    current_data = get_current_data(engine, security)

    if not current_data:
        return pd.DataFrame()

    # 定义所有可用字段
    all_fields = [
        'open', 'high', 'low', 'close', 'volume', 'amount',
        'pre_close', 'change', 'pct_change', 'amplitude', 'turnover_rate',
        'bid1', 'bid2', 'bid3', 'bid4', 'bid5',
        'ask1', 'ask2', 'ask3', 'ask4', 'ask5',
        'bid1_volume', 'bid2_volume', 'bid3_volume', 'bid4_volume', 'bid5_volume',
        'ask1_volume', 'ask2_volume', 'ask3_volume', 'ask4_volume', 'ask5_volume',
        'high_limit', 'low_limit', 'vwap'
    ]

    if fields is None:
        fields = ['open', 'high', 'low', 'close', 'volume', 'change', 'pct_change']
    elif isinstance(fields, str):
        fields = [fields]

    # 构建DataFrame
    data_dict = {}
    for field in fields:
        if field in all_fields:
            data_dict[field] = [current_data[sec].get(field, None) for sec in current_data.keys()]
        else:
            log.warning(f"不支持的字段: {field}")
            data_dict[field] = [None] * len(current_data)

    return pd.DataFrame(data_dict, index=list(current_data.keys()))

def get_technical_indicators(engine, security, indicators, period=20, **kwargs):
    """
    计算技术指标

    参数:
        engine: 回测引擎
        security: 股票代码或股票代码列表
        indicators: 指标名称或指标名称列表
        period: 计算周期，默认20
        **kwargs: 其他指标参数

    支持的指标:
        MA: 移动平均线
        EMA: 指数移动平均线
        MACD: 指数平滑移动平均线
        RSI: 相对强弱指标
        BOLL: 布林带
        KDJ: 随机指标
        CCI: 顺势指标
        WR: 威廉指标

    返回:
        pandas.DataFrame: 包含技术指标数据的DataFrame
    """
    if isinstance(security, str):
        security = [security]

    if isinstance(indicators, str):
        indicators = [indicators]

    result_data = {}

    for sec in security:
        if sec not in engine.data:
            log.warning(f"股票 {sec} 的数据不存在")
            continue

        hist_df = engine.data[sec]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None

        if current_dt:
            valid_hist = hist_df[hist_df.index <= current_dt]
        else:
            valid_hist = hist_df

        if len(valid_hist) < period:
            log.warning(f"股票 {sec} 的历史数据不足，需要至少 {period} 条数据")
            continue

        result_data[sec] = {}

        # 获取价格数据
        close_prices = valid_hist['close'].values
        high_prices = valid_hist['high'].values
        low_prices = valid_hist['low'].values
        volume_data = valid_hist['volume'].values

        for indicator in indicators:
            try:
                if indicator.upper() == 'MA':
                    # 移动平均线
                    ma_values = []
                    for i in range(len(close_prices)):
                        if i >= period - 1:
                            ma = np.mean(close_prices[i-period+1:i+1])
                            ma_values.append(ma)
                        else:
                            ma_values.append(None)
                    result_data[sec][f'MA{period}'] = ma_values

                elif indicator.upper() == 'EMA':
                    # 指数移动平均线
                    alpha = 2.0 / (period + 1)
                    ema_values = [close_prices[0]]  # 第一个值用收盘价
                    for i in range(1, len(close_prices)):
                        ema = alpha * close_prices[i] + (1 - alpha) * ema_values[-1]
                        ema_values.append(ema)
                    result_data[sec][f'EMA{period}'] = ema_values

                elif indicator.upper() == 'MACD':
                    # MACD指标
                    fast_period = kwargs.get('fast_period', 12)
                    slow_period = kwargs.get('slow_period', 26)
                    signal_period = kwargs.get('signal_period', 9)

                    # 计算快线EMA
                    alpha_fast = 2.0 / (fast_period + 1)
                    ema_fast = [close_prices[0]]
                    for i in range(1, len(close_prices)):
                        ema = alpha_fast * close_prices[i] + (1 - alpha_fast) * ema_fast[-1]
                        ema_fast.append(ema)

                    # 计算慢线EMA
                    alpha_slow = 2.0 / (slow_period + 1)
                    ema_slow = [close_prices[0]]
                    for i in range(1, len(close_prices)):
                        ema = alpha_slow * close_prices[i] + (1 - alpha_slow) * ema_slow[-1]
                        ema_slow.append(ema)

                    # 计算DIF
                    dif = [ema_fast[i] - ema_slow[i] for i in range(len(close_prices))]

                    # 计算DEA (DIF的EMA)
                    alpha_signal = 2.0 / (signal_period + 1)
                    dea = [dif[0]]
                    for i in range(1, len(dif)):
                        dea_val = alpha_signal * dif[i] + (1 - alpha_signal) * dea[-1]
                        dea.append(dea_val)

                    # 计算MACD柱
                    macd_hist = [(dif[i] - dea[i]) * 2 for i in range(len(dif))]

                    result_data[sec]['MACD_DIF'] = dif
                    result_data[sec]['MACD_DEA'] = dea
                    result_data[sec]['MACD_HIST'] = macd_hist

                elif indicator.upper() == 'RSI':
                    # RSI指标
                    gains = []
                    losses = []

                    for i in range(1, len(close_prices)):
                        change = close_prices[i] - close_prices[i-1]
                        gains.append(max(change, 0))
                        losses.append(max(-change, 0))

                    rsi_values = [None]  # 第一个值为None

                    for i in range(len(gains)):
                        if i >= period - 1:
                            avg_gain = np.mean(gains[i-period+1:i+1])
                            avg_loss = np.mean(losses[i-period+1:i+1])

                            if avg_loss == 0:
                                rsi = 100
                            else:
                                rs = avg_gain / avg_loss
                                rsi = 100 - (100 / (1 + rs))
                            rsi_values.append(rsi)
                        else:
                            rsi_values.append(None)

                    result_data[sec][f'RSI{period}'] = rsi_values

                elif indicator.upper() == 'BOLL':
                    # 布林带
                    std_multiplier = kwargs.get('std_multiplier', 2)

                    upper_band = []
                    middle_band = []
                    lower_band = []

                    for i in range(len(close_prices)):
                        if i >= period - 1:
                            prices_window = close_prices[i-period+1:i+1]
                            ma = np.mean(prices_window)
                            std = np.std(prices_window)

                            upper_band.append(ma + std_multiplier * std)
                            middle_band.append(ma)
                            lower_band.append(ma - std_multiplier * std)
                        else:
                            upper_band.append(None)
                            middle_band.append(None)
                            lower_band.append(None)

                    result_data[sec]['BOLL_UPPER'] = upper_band
                    result_data[sec]['BOLL_MIDDLE'] = middle_band
                    result_data[sec]['BOLL_LOWER'] = lower_band

                elif indicator.upper() == 'KDJ':
                    # KDJ指标
                    k_period = kwargs.get('k_period', 9)
                    d_period = kwargs.get('d_period', 3)

                    rsv_values = []
                    for i in range(len(close_prices)):
                        if i >= k_period - 1:
                            high_max = np.max(high_prices[i-k_period+1:i+1])
                            low_min = np.min(low_prices[i-k_period+1:i+1])

                            if high_max == low_min:
                                rsv = 50
                            else:
                                rsv = (close_prices[i] - low_min) / (high_max - low_min) * 100
                            rsv_values.append(rsv)
                        else:
                            rsv_values.append(50)  # 初始值

                    # 计算K值
                    k_values = [50]  # 初始K值
                    for i in range(1, len(rsv_values)):
                        k = (2/3) * k_values[-1] + (1/3) * rsv_values[i]
                        k_values.append(k)

                    # 计算D值
                    d_values = [50]  # 初始D值
                    for i in range(1, len(k_values)):
                        d = (2/3) * d_values[-1] + (1/3) * k_values[i]
                        d_values.append(d)

                    # 计算J值
                    j_values = [3 * k_values[i] - 2 * d_values[i] for i in range(len(k_values))]

                    result_data[sec]['KDJ_K'] = k_values
                    result_data[sec]['KDJ_D'] = d_values
                    result_data[sec]['KDJ_J'] = j_values

                else:
                    log.warning(f"不支持的技术指标: {indicator}")

            except Exception as e:
                log.warning(f"计算技术指标 {indicator} 时出错: {e}")

    # 转换为DataFrame格式
    if not result_data:
        return pd.DataFrame()

    # 获取时间索引
    if security and security[0] in engine.data:
        sample_data = engine.data[security[0]]
        current_dt = engine.context.current_dt if hasattr(engine, 'context') else None
        if current_dt:
            valid_hist = sample_data[sample_data.index <= current_dt]
        else:
            valid_hist = sample_data
        time_index = valid_hist.index
    else:
        time_index = pd.date_range(start='2023-01-01', periods=len(close_prices), freq='D')

    # 构建DataFrame
    result_df = pd.DataFrame()
    for sec in result_data:
        for indicator_name, values in result_data[sec].items():
            if len(values) == len(time_index):
                result_df[(indicator_name, sec)] = pd.Series(values, index=time_index)

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