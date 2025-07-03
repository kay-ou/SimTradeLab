# -*- coding: utf-8 -*-
"""
ptradeSim - Python量化交易回测框架

主要组件:
- engine: 回测引擎
- context: 上下文和投资组合管理
"""

from .engine import BacktestEngine
from .context import Context, Portfolio, Position
from .logger import log
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


__version__ = "1.0.0"
__author__ = "ptradeSim Team"

__all__ = [
    'BacktestEngine',
    'Context',
    'Portfolio',
    'Position',
    'log',

    # financials
    'get_fundamentals', 'get_income_statement', 'get_balance_sheet', 'get_cash_flow', 'get_financial_ratios',
    
    # market_data
    'get_history', 'get_price', 'get_current_data', 'get_market_snapshot', 'get_technical_indicators',
    
    # trading
    'order', 'order_target', 'order_value', 'cancel_order',
    
    # utils
    'is_trade', 'get_research_path', 'set_commission', 'set_limit_mode', 'run_interval', 'clear_file',
    'get_initial_cash', 'get_num_of_positions', 'get_Ashares', 'get_stock_status', 'get_stock_info',
    'get_stock_name', 'set_universe',
]
