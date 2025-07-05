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
    get_history, get_price, get_current_data, get_market_snapshot, get_technical_indicators,
    get_MACD, get_KDJ, get_RSI, get_CCI
)
from .trading import (
    order, order_target, order_value, cancel_order,
    get_positions, get_position, get_open_orders, get_order, get_orders, get_trades
)
from .utils import (
    is_trade, get_research_path, set_commission, set_limit_mode, run_interval, clear_file,
    get_initial_cash, get_num_of_positions, get_Ashares, get_stock_status, get_stock_info,
    get_stock_name, set_universe, set_benchmark, get_benchmark_returns,
    get_trading_day, get_all_trades_days, get_trade_days
)
from .performance import (
    calculate_performance_metrics, print_performance_report, get_performance_summary,
    generate_report_file
)
from .report_generator import ReportGenerator
from .compatibility import (
    set_ptrade_version, get_version_info, validate_order_status, convert_order_status,
    PtradeVersion
)
from .data_sources import (
    DataSourceFactory, DataSourceManager, CSVDataSource,
    TUSHARE_AVAILABLE, AKSHARE_AVAILABLE
)
from .config import DataSourceConfig, load_config, save_config


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
    'get_MACD', 'get_KDJ', 'get_RSI', 'get_CCI',
    
    # trading
    'order', 'order_target', 'order_value', 'cancel_order',
    'get_positions', 'get_position', 'get_open_orders', 'get_order', 'get_orders', 'get_trades',
    
    # utils
    'is_trade', 'get_research_path', 'set_commission', 'set_limit_mode', 'run_interval', 'clear_file',
    'get_initial_cash', 'get_num_of_positions', 'get_Ashares', 'get_stock_status', 'get_stock_info',
    'get_stock_name', 'set_universe', 'set_benchmark', 'get_benchmark_returns',
    'get_trading_day', 'get_all_trades_days', 'get_trade_days',

    # performance
    'calculate_performance_metrics', 'print_performance_report', 'get_performance_summary',
    'generate_report_file', 'ReportGenerator',

    # compatibility
    'set_ptrade_version', 'get_version_info', 'validate_order_status', 'convert_order_status',
    'PtradeVersion',

    # data sources
    'DataSourceFactory', 'DataSourceManager', 'CSVDataSource',
    'TUSHARE_AVAILABLE', 'AKSHARE_AVAILABLE',

    # config
    'DataSourceConfig', 'load_config', 'save_config'
]
