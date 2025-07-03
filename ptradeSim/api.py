# -*- coding: utf-8 -*-
"""
API主模块，整合并导出所有API函数。
"""
from .financials import (
    get_fundamentals, get_income_statement, get_balance_sheet, get_cash_flow, get_financial_ratios
)
from .market_data import (
    get_history, get_price, get_current_data, get_market_snapshot, get_technical_indicators
)
from .trading import (
    order, order_target, order_value, cancel_order
)
from .utils import (
    is_trade, get_research_path, set_commission, set_limit_mode, run_interval, clear_file,
    get_initial_cash, get_num_of_positions, get_Ashares, get_stock_status, get_stock_info,
    get_stock_name, set_universe
)
from .logger import log