# -*- coding: utf-8 -*-
"""
SimTradeLab PTrade API Module

Complete simulation of PTrade platform API interface for local backtesting and research
"""

# Core context and modes
from .context import (
    Context,
    PTradeMode,
    StrategyLifecycleManager,
    create_backtest_context,
    create_research_context,
    create_trading_context,
)

# Lifecycle control
from .lifecycle_controller import (
    LifecycleController,
    LifecyclePhase,
    LifecycleValidationResult,
    PTradeLifecycleError,
    get_current_phase,
    get_lifecycle_controller,
    record_api_call,
    set_global_lifecycle_controller,
    validate_api_call,
)

# Lifecycle configuration
from .lifecycle_config import (
    API_LIFECYCLE_RESTRICTIONS,
    API_MODE_RESTRICTIONS,
    LIFECYCLE_PHASES,
    get_api_allowed_phases,
    get_api_supported_modes,
    is_api_allowed_in_phase,
    is_api_supported_in_mode,
)

# Core objects
from .object import (
    BacktestContext,
    Blotter,
    Data,
    Global,
    LazyDataDict,
    Order,
    Portfolio,
    Position,
    StockData,
)

# API simulator
from .api import PtradeAPI

# Modern infrastructure
from .cache_manager import cache_manager
from .config_manager import config

# Strategy execution engine
from .strategy_engine import (
    StrategyExecutionEngine,
    StrategyExecutionError,
)

__all__ = [
    # Context related
    "Context",
    "PTradeMode",
    "StrategyLifecycleManager",
    "create_backtest_context",
    "create_research_context",
    "create_trading_context",
    # Lifecycle control
    "LifecycleController",
    "LifecyclePhase",
    "LifecycleValidationResult",
    "PTradeLifecycleError",
    "get_current_phase",
    "get_lifecycle_controller",
    "record_api_call",
    "set_global_lifecycle_controller",
    "validate_api_call",
    # Lifecycle configuration
    "API_LIFECYCLE_RESTRICTIONS",
    "API_MODE_RESTRICTIONS",
    "LIFECYCLE_PHASES",
    "get_api_allowed_phases",
    "get_api_supported_modes",
    "is_api_allowed_in_phase",
    "is_api_supported_in_mode",
    # Core objects
    "BacktestContext",
    "Blotter",
    "Data",
    "Global",
    "LazyDataDict",
    "Order",
    "Portfolio",
    "Position",
    "StockData",
    # Modern infrastructure
    "config",
    "cache_manager",
    # API simulator
    "PtradeAPI",
    # Strategy execution engine
    "StrategyExecutionEngine",
    "StrategyExecutionError",
]

__version__ = "0.1.0"
__author__ = "SimTradeLab Team"
