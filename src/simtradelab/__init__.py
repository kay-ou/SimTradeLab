# -*- coding: utf-8 -*-
"""
SimTradeLab - 开源策略回测框架

=======================
PTrade 完全兼容框架  
=======================

SimTradeLab 致力于与 PTrade 保持 100% API 兼容性，确保：

🔄 **无缝迁移**
- 所有在 SimTradeLab 中编写的策略可直接在 PTrade 平台运行
- PTrade 策略可无需修改直接在 SimTradeLab 中运行
- API 函数名称、参数、返回值格式完全一致

📦 **完整功能覆盖**
- 数据获取：历史数据、实时行情、基本面数据
- 交易执行：下单、撤单、持仓管理、风控
- 高级功能：期货、期权、ETF、可转债交易
- 系统功能：配置管理、日志记录、性能分析

🛠 **配置兼容性**  
- 支持 PTrade 配置文件格式
- 环境变量配置方式一致
- 数据源配置参数完全兼容

主要组件:
- engine: 回测引擎，兼容PTrade策略执行模式
- context: 上下文和投资组合管理，API与PTrade一致
- market_data: 市场数据接口，支持PTrade所有数据类型
- trading: 交易接口，完全兼容PTrade交易API
- config: 配置管理，支持PTrade配置格式
- utils: 工具函数，提供PTrade兼容的辅助功能

使用示例:
```python
# PTrade策略代码可直接运行，无需修改
def initialize(context):
    # 设置基准和股票池
    set_benchmark('000300.SH')
    set_universe(['000001.SZ', '000002.SZ'])
    
def handle_data(context, data):
    # 获取历史数据
    hist = get_history(context, count=20, field='close')
    
    # 执行交易
    order_target_percent('000001.SZ', 0.5)
```

PTrade 迁移指南:
1. 配置文件：直接使用现有PTrade配置文件
2. 策略代码：无需任何修改
3. 数据格式：保持一致的DataFrame格式
4. API调用：所有函数签名完全相同
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
    get_cash, get_total_value, get_datetime, get_previous_trading_date, get_next_trading_date,
    # 高级市场数据API（从utils.py迁移而来）
    get_snapshot, get_volume_ratio, get_turnover_rate, get_pe_ratio, get_pb_ratio,
    get_individual_entrust, get_individual_transaction, get_gear_price, get_sort_msg
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
    # 分红配股
    get_dividend_info, get_rights_issue_info,
    # 停复牌
    get_suspend_info, is_suspended,
    # 新增基础工具
    check_limit, create_dir, get_user_name, get_trade_name, permission_test,
    # 股票基础信息补充
    get_stock_exrights, get_index_stocks, get_industry_stocks, get_ipo_stocks,
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
# 配置管理 - 现代配置系统
from .config_manager import (
    SimTradeLabConfig, BacktestConfig, LoggingConfig, ReportConfig,
    TushareConfig, AkshareConfig, CSVConfig, DataSourceConfig,
    load_config, get_config, save_config
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
    # 高级市场数据（从utils.py迁移而来）
    'get_snapshot', 'get_volume_ratio', 'get_turnover_rate', 'get_pe_ratio', 'get_pb_ratio',
    'get_individual_entrust', 'get_individual_transaction', 'get_gear_price', 'get_sort_msg',
    
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
    
    # 分红配股
    'get_dividend_info', 'get_rights_issue_info',
    
    # 停复牌
    'get_suspend_info', 'is_suspended',

    # 新增基础工具
    'check_limit', 'create_dir', 'get_user_name', 'get_trade_name', 'permission_test',

    # 股票基础信息补充
    'get_stock_exrights', 'get_index_stocks', 'get_industry_stocks', 'get_ipo_stocks',

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

    # config - 现代配置系统
    'SimTradeLabConfig', 'BacktestConfig', 'LoggingConfig', 'ReportConfig',
    'TushareConfig', 'AkshareConfig', 'CSVConfig', 'DataSourceConfig',
    'load_config', 'get_config', 'save_config',

    # exceptions
    'SimTradeLabError', 'DataSourceError', 'DataLoadError', 'DataValidationError',
    'TradingError', 'InsufficientFundsError', 'InsufficientPositionError', 'InvalidOrderError',
    'EngineError', 'StrategyError', 'ConfigurationError', 'ReportGenerationError'
]
