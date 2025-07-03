# -*- coding: utf-8 -*-
"""
财务数据接口模块
"""
import hashlib
import pandas as pd
from .logger import log

def get_fundamentals(engine, stocks, table, fields=None, date=None, start_year=None, end_year=None, report_types=None, merge_type=None, date_type=None):
    """
    模拟get_fundamentals函数，提供丰富的财务基本面数据
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    all_fundamentals_data = {
        'market_cap': 50e8, 'total_value': 50e8, 'pe_ratio': 25.5, 'pb_ratio': 3.2,
        'ps_ratio': 4.8, 'pcf_ratio': 15.2, 'turnover_rate': 15.0, 'revenue': 120e8,
        'net_income': 8e8, 'gross_profit': 45e8, 'operating_profit': 15e8, 'eps': 2.85,
        'roe': 15.8, 'roa': 8.5, 'gross_margin': 37.5, 'net_margin': 6.7,
        'total_assets': 180e8, 'total_liabilities': 95e8, 'total_equity': 85e8,
        'current_assets': 75e8, 'current_liabilities': 45e8, 'debt_to_equity': 0.45,
        'current_ratio': 1.67, 'quick_ratio': 1.25, 'operating_cash_flow': 12e8,
        'investing_cash_flow': -5e8, 'financing_cash_flow': -3e8, 'free_cash_flow': 7e8,
        'inventory_turnover': 8.5, 'receivables_turnover': 12.3, 'asset_turnover': 1.2,
        'equity_turnover': 2.1,
    }

    table_field_mapping = {
        'valuation': ['market_cap', 'total_value', 'pe_ratio', 'pb_ratio', 'ps_ratio', 'pcf_ratio', 'turnover_rate'],
        'income': ['revenue', 'net_income', 'gross_profit', 'operating_profit', 'eps', 'roe', 'roa', 'gross_margin', 'net_margin'],
        'balance_sheet': ['total_assets', 'total_liabilities', 'total_equity', 'current_assets', 'current_liabilities', 'debt_to_equity', 'current_ratio', 'quick_ratio'],
        'cash_flow': ['operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'free_cash_flow'],
        'indicator': ['inventory_turnover', 'receivables_turnover', 'asset_turnover', 'equity_turnover', 'roe', 'roa']
    }

    if fields is None:
        selected_fields = table_field_mapping.get(table, list(all_fundamentals_data.keys()))
    else:
        selected_fields = [fields] if isinstance(fields, str) else fields

    data = {}
    for field in selected_fields:
        if field in all_fundamentals_data:
            base_value = all_fundamentals_data[field]
            values = []
            for stock in stocks:
                hash_factor = int(hashlib.md5(stock.encode()).hexdigest()[:8], 16) / 0xffffffff
                variation = 0.8 + 0.4 * hash_factor
                values.append(base_value * variation)
            data[field] = values
        else:
            log.warning(f"财务数据字段 '{field}' 不存在，返回None值")
            data[field] = [None] * len(stocks)

    return pd.DataFrame(data, index=stocks)

def get_income_statement(engine, stocks, fields=None, date=None, count=4):
    """
    获取损益表数据
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    income_statement_data = {
        'revenue': 120e8, 'cost_of_revenue': 75e8, 'gross_profit': 45e8,
        'operating_expenses': 30e8, 'operating_profit': 15e8, 'interest_expense': 2e8,
        'other_income': 1e8, 'profit_before_tax': 14e8, 'income_tax': 6e8,
        'net_income': 8e8, 'eps_basic': 2.85, 'eps_diluted': 2.80,
        'shares_outstanding': 2.8e8,
    }

    selected_fields = list(income_statement_data.keys()) if fields is None else ([fields] if isinstance(fields, str) else fields)

    data = {}
    for field in selected_fields:
        if field in income_statement_data:
            base_value = income_statement_data[field]
            values = []
            for stock in stocks:
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
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    balance_sheet_data = {
        'total_assets': 180e8, 'current_assets': 75e8, 'cash_and_equivalents': 25e8,
        'accounts_receivable': 20e8, 'inventory': 15e8, 'other_current_assets': 15e8,
        'non_current_assets': 105e8, 'property_plant_equipment': 80e8,
        'intangible_assets': 15e8, 'goodwill': 10e8, 'total_liabilities': 95e8,
        'current_liabilities': 45e8, 'accounts_payable': 18e8, 'short_term_debt': 12e8,
        'other_current_liabilities': 15e8, 'non_current_liabilities': 50e8,
        'long_term_debt': 35e8, 'other_non_current_liabilities': 15e8,
        'total_equity': 85e8, 'share_capital': 28e8, 'retained_earnings': 45e8,
        'other_equity': 12e8,
    }

    selected_fields = list(balance_sheet_data.keys()) if fields is None else ([fields] if isinstance(fields, str) else fields)

    data = {}
    for field in selected_fields:
        if field in balance_sheet_data:
            base_value = balance_sheet_data[field]
            values = []
            for stock in stocks:
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
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    cash_flow_data = {
        'operating_cash_flow': 12e8, 'net_income_cf': 8e8, 'depreciation': 5e8,
        'working_capital_change': -1e8, 'other_operating_activities': 0,
        'investing_cash_flow': -5e8, 'capital_expenditure': -6e8, 'acquisitions': -2e8,
        'asset_sales': 1e8, 'investment_purchases': -1e8, 'other_investing_activities': 3e8,
        'financing_cash_flow': -3e8, 'debt_issuance': 5e8, 'debt_repayment': -4e8,
        'equity_issuance': 2e8, 'dividends_paid': -3e8, 'share_repurchase': -2e8,
        'other_financing_activities': -1e8, 'free_cash_flow': 7e8, 'net_cash_change': 4e8,
    }

    selected_fields = list(cash_flow_data.keys()) if fields is None else ([fields] if isinstance(fields, str) else fields)

    data = {}
    for field in selected_fields:
        if field in cash_flow_data:
            base_value = cash_flow_data[field]
            values = []
            for stock in stocks:
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
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    financial_ratios_data = {
        'current_ratio': 1.67, 'quick_ratio': 1.25, 'cash_ratio': 0.56,
        'operating_cash_flow_ratio': 0.27, 'debt_to_equity': 0.45, 'debt_to_assets': 0.31,
        'equity_ratio': 0.47, 'interest_coverage': 7.5, 'debt_service_coverage': 2.8,
        'gross_margin': 37.5, 'operating_margin': 12.5, 'net_margin': 6.7, 'roe': 15.8,
        'roa': 8.5, 'roic': 12.3, 'asset_turnover': 1.2, 'inventory_turnover': 8.5,
        'receivables_turnover': 12.3, 'payables_turnover': 6.8, 'equity_turnover': 2.1,
        'working_capital_turnover': 4.2, 'pe_ratio': 25.5, 'pb_ratio': 3.2,
        'ps_ratio': 4.8, 'pcf_ratio': 15.2, 'ev_ebitda': 18.5, 'dividend_yield': 2.8,
        'peg_ratio': 1.5, 'book_value_per_share': 30.4,
        'tangible_book_value_per_share': 28.1, 'sales_per_share': 42.9,
        'cash_per_share': 8.9, 'free_cash_flow_per_share': 2.5,
    }

    selected_fields = list(financial_ratios_data.keys()) if fields is None else ([fields] if isinstance(fields, str) else fields)

    data = {}
    for field in selected_fields:
        if field in financial_ratios_data:
            base_value = financial_ratios_data[field]
            values = []
            for stock in stocks:
                hash_factor = int(hashlib.md5(stock.encode()).hexdigest()[:8], 16) / 0xffffffff
                variation = 0.8 + 0.4 * hash_factor
                values.append(base_value * variation)
            data[field] = values
        else:
            log.warning(f"财务比率字段 '{field}' 不存在，返回None值")
            data[field] = [None] * len(stocks)

    return pd.DataFrame(data, index=stocks)
