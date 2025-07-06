# -*- coding: utf-8 -*-
"""
SimTradeLab - 开源策略回测框架

灵感来自PTrade的事件驱动模型，提供轻量、清晰、可插拔的策略验证环境

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
    get_MACD, get_KDJ, get_RSI, get_CCI, get_market_list, 
    get_cash, get_total_value, get_datetime, get_previous_trading_date, get_next_trading_date
)
from .trading import (
    order, order_target, order_value, cancel_order,
    get_positions, get_position, get_open_orders, get_order, get_orders, get_trades,
    order_target_value, order_market, ipo_stocks_order, after_trading_order, etf_basket_order,
    order_percent, order_target_percent
)
from .utils import (
    is_trade, get_research_path, set_commission, set_limit_mode, run_daily, run_interval, clear_file,
    get_initial_cash, get_num_of_positions, get_Ashares, get_stock_status, get_stock_info,
    get_stock_name, set_universe, set_benchmark, get_benchmark_returns,
    get_trading_day, get_all_trades_days, get_trade_days,
    set_fixed_slippage, set_slippage, set_volume_ratio, set_yesterday_position, set_parameters,
    # ETF相关
    get_etf_info, get_etf_stock_info, get_etf_stock_list, get_etf_list, etf_purchase_redemption,
    # 债券相关
    debt_to_stock_order, get_cb_list, get_cb_info,
    # 期货相关
    buy_open, sell_close, sell_open, buy_close, set_future_commission, set_margin_rate,
    get_margin_rate, get_instruments,
    # 期权相关
    get_opt_objects, get_opt_last_dates, get_opt_contracts, option_exercise,
    option_covered_lock, option_covered_unlock,
    # 基础查询
    get_market_detail, get_stock_blocks, get_tick_direction,
    # 高级市场数据
    get_snapshot, get_volume_ratio, get_turnover_rate, get_pe_ratio, get_pb_ratio,
    # 分红配股
    get_dividend_info, get_rights_issue_info,
    # 停复牌
    get_suspend_info, is_suspended,
    # 新增基础工具
    check_limit, create_dir, get_user_name, get_trade_name, permission_test,
    # 股票基础信息补充
    get_stock_exrights, get_index_stocks, get_industry_stocks, get_ipo_stocks,
    # 高级行情数据
    get_individual_entrust, get_individual_transaction, get_gear_price, get_sort_msg,
    # 系统集成功能
    send_email, send_qywx,
    # 期权高级功能
    get_contract_info, get_covered_lock_amount, get_covered_unlock_amount,
    open_prepared, close_prepared,
    # 其他缺失API
    get_trades_file, convert_position_from_csv, get_deliver, get_fundjour,
    order_tick, cancel_order_ex, get_all_orders, after_trading_cancel_order
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
from .config_manager import (
    SimTradeLabConfig, BacktestConfig, LoggingConfig, ReportConfig,
    TushareConfig, AkshareConfig, CSVConfig, 
    load_config as load_modern_config, get_config, save_config as save_modern_config
)
from .exceptions import (
    SimTradeLabError, DataSourceError, DataLoadError, DataValidationError,
    TradingError, InsufficientFundsError, InsufficientPositionError, InvalidOrderError,
    EngineError, StrategyError, ConfigurationError, ReportGenerationError
)

# 融资融券模块
from .margin_trading import (
    # 融资融券交易
    margin_trade, margincash_open, margincash_close, margincash_direct_refund,
    marginsec_open, marginsec_close, marginsec_direct_refund,
    # 融资融券查询
    get_margincash_stocks, get_marginsec_stocks, get_margin_contract,
    get_margin_contractreal, get_margin_assert, get_assure_security_list,
    get_margincash_open_amount, get_margincash_close_amount,
    get_marginsec_open_amount, get_marginsec_close_amount,
    get_margin_entrans_amount, get_enslo_security_info
)


__version__ = "1.0.0"
__author__ = "SimTradeLab Team"

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
    'get_MACD', 'get_KDJ', 'get_RSI', 'get_CCI', 'get_market_list',
    'get_cash', 'get_total_value', 'get_datetime', 'get_previous_trading_date', 'get_next_trading_date',
    
    # trading
    'order', 'order_target', 'order_value', 'cancel_order',
    'get_positions', 'get_position', 'get_open_orders', 'get_order', 'get_orders', 'get_trades',
    'order_target_value', 'order_market', 'ipo_stocks_order', 'after_trading_order', 'etf_basket_order',
    'order_percent', 'order_target_percent',
    
    # utils
    'is_trade', 'get_research_path', 'set_commission', 'set_limit_mode', 'run_daily', 'run_interval', 'clear_file',
    'get_initial_cash', 'get_num_of_positions', 'get_Ashares', 'get_stock_status', 'get_stock_info',
    'get_stock_name', 'set_universe', 'set_benchmark', 'get_benchmark_returns',
    'get_trading_day', 'get_all_trades_days', 'get_trade_days',
    'set_fixed_slippage', 'set_slippage', 'set_volume_ratio', 'set_yesterday_position', 'set_parameters',
    
    # ETF相关
    'get_etf_info', 'get_etf_stock_info', 'get_etf_stock_list', 'get_etf_list', 'etf_purchase_redemption',
    
    # 债券相关
    'debt_to_stock_order', 'get_cb_list', 'get_cb_info',
    
    # 期货相关
    'buy_open', 'sell_close', 'sell_open', 'buy_close', 'set_future_commission', 'set_margin_rate',
    'get_margin_rate', 'get_instruments',
    
    # 期权相关
    'get_opt_objects', 'get_opt_last_dates', 'get_opt_contracts', 'option_exercise',
    'option_covered_lock', 'option_covered_unlock',
    
    # 基础查询
    'get_market_detail', 'get_stock_blocks', 'get_tick_direction',
    
    # 高级市场数据
    'get_snapshot', 'get_volume_ratio', 'get_turnover_rate', 'get_pe_ratio', 'get_pb_ratio',
    
    # 分红配股
    'get_dividend_info', 'get_rights_issue_info',
    
    # 停复牌
    'get_suspend_info', 'is_suspended',

    # 新增基础工具
    'check_limit', 'create_dir', 'get_user_name', 'get_trade_name', 'permission_test',

    # 股票基础信息补充
    'get_stock_exrights', 'get_index_stocks', 'get_industry_stocks', 'get_ipo_stocks',

    # 高级行情数据
    'get_individual_entrust', 'get_individual_transaction', 'get_gear_price', 'get_sort_msg',

    # 系统集成功能
    'send_email', 'send_qywx',

    # 期权高级功能
    'get_contract_info', 'get_covered_lock_amount', 'get_covered_unlock_amount',
    'open_prepared', 'close_prepared',

    # 其他缺失API
    'get_trades_file', 'convert_position_from_csv', 'get_deliver', 'get_fundjour',
    'order_tick', 'cancel_order_ex', 'get_all_orders', 'after_trading_cancel_order',

    # 融资融券交易
    'margin_trade', 'margincash_open', 'margincash_close', 'margincash_direct_refund',
    'marginsec_open', 'marginsec_close', 'marginsec_direct_refund',

    # 融资融券查询
    'get_margincash_stocks', 'get_marginsec_stocks', 'get_margin_contract',
    'get_margin_contractreal', 'get_margin_assert', 'get_assure_security_list',
    'get_margincash_open_amount', 'get_margincash_close_amount',
    'get_marginsec_open_amount', 'get_marginsec_close_amount',
    'get_margin_entrans_amount', 'get_enslo_security_info',

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
    'DataSourceConfig', 'load_config', 'save_config',
    'SimTradeLabConfig', 'BacktestConfig', 'LoggingConfig', 'ReportConfig',
    'TushareConfig', 'AkshareConfig', 'CSVConfig',
    'load_modern_config', 'get_config', 'save_modern_config',

    # exceptions
    'SimTradeLabError', 'DataSourceError', 'DataLoadError', 'DataValidationError',
    'TradingError', 'InsufficientFundsError', 'InsufficientPositionError', 'InvalidOrderError',
    'EngineError', 'StrategyError', 'ConfigurationError', 'ReportGenerationError'
]
