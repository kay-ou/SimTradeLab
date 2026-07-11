"""Machine-readable support contracts for documented PTrade backtest APIs."""

from simtradelab.ptrade.lifecycle_config import API_ALLOWED_PHASES_LOOKUP
from simtradelab.ptrade.broker_profile import (
    BROKER_PROFILES,
    BROKER_STRICT_UNSUPPORTED_APIS,
)
from simtradelab.ptrade.api import PtradeAPI

SUPPORTED_PTRADE_APIS = (
    "set_universe",
    "set_benchmark",
    "set_commission",
    "set_slippage",
    "set_fixed_slippage",
    "set_volume_ratio",
    "set_limit_mode",
    "set_yesterday_position",
    "run_daily",
    "get_history",
    "get_price",
    "get_market_list",
    "get_market_detail",
    "get_stock_info",
    "get_stock_name",
    "get_stock_status",
    "get_stock_exrights",
    "get_stock_blocks",
    "get_index_stocks",
    "get_industry_stocks",
    "get_fundamentals",
    "get_Ashares",
    "get_reits_list",
    "get_trend_data",
    "get_trading_day",
    "get_trade_days",
    "get_all_trades_days",
    "get_trading_day_by_date",
    "check_limit",
    "filter_stock_by_status",
    "get_current_kline_count",
    "get_frequency",
    "get_business_type",
    "is_trade",
    "order",
    "order_target",
    "order_value",
    "order_target_value",
    "cancel_order",
    "get_open_orders",
    "get_order",
    "get_orders",
    "get_trades",
    "get_position",
    "get_positions",
    "convert_position_from_csv",
    "get_user_name",
    "get_research_path",
    "get_trades_file",
    "create_dir",
    "get_MACD",
    "get_KDJ",
    "get_RSI",
    "get_CCI",
)

UNSUPPORTED_PTRADE_APIS = (
    "margin_trade",
    "buy_open",
    "sell_close",
    "sell_open",
    "buy_close",
    "set_future_commission",
    "set_margin_rate",
    "get_margin_rate",
    "get_instruments",
    "get_dominant_contract",
)

def _contract(
    category: str,
    support: str,
    *behavior_tests: str,
) -> dict[str, object]:
    return {
        "category": category,
        "support": support,
        "behavior_tests": list(behavior_tests),
    }


PTRADE_API_CONTRACTS = {
    # Configuration and scheduling
    "set_universe": _contract(
        "configuration",
        "full",
        "tests/unit/test_broker_profile_compat.py::TestBrokerProfileCompat::test_get_history_security_list_none_uses_universe",
    ),
    "set_benchmark": _contract("configuration", "partial"),
    "set_commission": _contract("configuration", "partial"),
    "set_slippage": _contract(
        "configuration",
        "full",
        "tests/unit/test_trading_config_propagation.py::test_set_slippage_controls_buy_and_sell_prices_and_cash",
    ),
    "set_fixed_slippage": _contract(
        "configuration",
        "full",
        "tests/unit/test_trading_config_propagation.py::test_set_fixed_slippage_alone_controls_fill_price_and_cash",
    ),
    "set_volume_ratio": _contract(
        "configuration",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_volume_ratio_limits_daily_buy_fill",
    ),
    "set_limit_mode": _contract(
        "configuration",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_volume_limit_modes_and_ratio_boundaries",
    ),
    "set_yesterday_position": _contract(
        "portfolio",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_t_plus_one_real_orders_and_daily_rollover",
    ),
    "run_daily": _contract(
        "scheduling",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_daily_run_daily_executes_before_after_trading_end_and_fires_callbacks",
    ),
    # Market data and security information
    "get_history": _contract(
        "market_data",
        "full",
        "tests/unit/test_api_date_index_contract.py::test_get_history_include_contract_unchanged_by_prebuild",
        "tests/unit/test_market_data_behavior_contracts.py::test_get_history_minute_fill_mode_is_part_of_cache_contract",
    ),
    "get_price": _contract(
        "market_data",
        "partial",
    ),
    "get_market_list": _contract(
        "market_data",
        "full",
        "tests/unit/test_api_advanced.py::TestMarketAndExrightsAPI::test_get_market_list_uses_documented_codes",
    ),
    "get_market_detail": _contract("market_data", "partial"),
    "get_stock_info": _contract("security_query", "partial"),
    "get_stock_name": _contract("security_query", "partial"),
    "get_stock_status": _contract("security_query", "partial"),
    "get_stock_exrights": _contract(
        "adjustment",
        "full",
        "tests/unit/test_api_advanced.py::TestMarketAndExrightsAPI::test_get_stock_exrights_accepts_int_date",
    ),
    "get_stock_blocks": _contract("security_query", "partial"),
    "get_index_stocks": _contract("security_query", "partial"),
    "get_industry_stocks": _contract("security_query", "partial"),
    "get_fundamentals": _contract(
        "fundamentals",
        "full",
        "tests/unit/test_api_fundamentals_contract.py::test_get_fundamentals_filters_by_publish_date_not_report_period",
    ),
    "get_Ashares": _contract("security_query", "partial"),
    "get_reits_list": _contract("security_query", "pending"),
    "get_trend_data": _contract("market_data", "pending"),
    # Trading-calendar and context helpers
    "get_trading_day": _contract(
        "calendar",
        "full",
        "tests/unit/test_api_date_index_contract.py::test_trade_day_helpers_follow_documented_bounds",
    ),
    "get_trade_days": _contract(
        "calendar",
        "full",
        "tests/unit/test_api_date_index_contract.py::test_trade_day_helpers_follow_documented_bounds",
    ),
    "get_all_trades_days": _contract("calendar", "partial"),
    "get_trading_day_by_date": _contract(
        "calendar",
        "full",
        "tests/unit/test_api_date_index_contract.py::test_trade_day_helpers_follow_documented_bounds",
    ),
    "check_limit": _contract(
        "market_status",
        "full",
        "tests/unit/test_api_date_index_contract.py::test_check_limit_status_contract_unchanged_by_prebuild",
    ),
    "filter_stock_by_status": _contract("market_status", "partial"),
    "get_current_kline_count": _contract("context_query", "partial"),
    "get_frequency": _contract("context_query", "partial"),
    "get_business_type": _contract("context_query", "partial"),
    "is_trade": _contract("context_query", "partial"),
    # Trading, orders, and positions
    "order": _contract(
        "trading",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_t_plus_one_real_orders_and_daily_rollover",
    ),
    "order_target": _contract(
        "trading",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_order_target_rebalances_to_target_after_t_plus_one_rollover",
    ),
    "order_value": _contract(
        "trading",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_order_value_propagates_to_cash_holdings_and_query_records",
    ),
    "order_target_value": _contract(
        "trading",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_order_target_value_propagates_to_cash_holdings_and_query_records",
    ),
    "cancel_order": _contract("order_query", "partial"),
    "get_open_orders": _contract("order_query", "partial"),
    "get_order": _contract(
        "order_query",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_order_value_propagates_to_cash_holdings_and_query_records",
    ),
    "get_orders": _contract(
        "order_query",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_order_target_rebalances_to_target_after_t_plus_one_rollover",
    ),
    "get_trades": _contract(
        "order_query",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_get_trades_returns_only_current_trading_day",
    ),
    "get_position": _contract(
        "portfolio",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_order_value_propagates_to_cash_holdings_and_query_records",
    ),
    "get_positions": _contract(
        "portfolio",
        "full",
        "tests/unit/test_trade_flow_regressions.py::test_order_value_propagates_to_cash_holdings_and_query_records",
    ),
    # Utilities and indicators
    "convert_position_from_csv": _contract(
        "utility",
        "full",
        "tests/unit/test_api_complete.py::TestAdvancedConfigAPI::test_convert_position_from_csv_document_fields",
    ),
    "get_user_name": _contract("utility", "partial"),
    "get_research_path": _contract("utility", "partial"),
    "get_trades_file": _contract("utility", "partial"),
    "create_dir": _contract(
        "utility",
        "full",
        "tests/unit/test_broker_profile_compat.py::TestBrokerProfileCompat::test_create_dir_return_by_broker_profile",
    ),
    "get_MACD": _contract("indicator", "partial"),
    "get_KDJ": _contract("indicator", "partial"),
    "get_RSI": _contract("indicator", "partial"),
    "get_CCI": _contract("indicator", "partial"),
}

PTRADE_API_CONTRACTS.update(
    {api_name: _contract("unsupported", "unsupported") for api_name in UNSUPPORTED_PTRADE_APIS}
)


def _applicability_for(api_name: str, category: str) -> dict[str, object]:
    market_data_categories = {
        "market_data",
        "security_query",
        "adjustment",
        "fundamentals",
        "market_status",
    }
    method_parameters = PtradeAPI.__dict__[api_name].__dict__.get("__wrapped__", PtradeAPI.__dict__[api_name])
    import inspect

    has_frequency = "frequency" in inspect.signature(method_parameters).parameters
    supported_profiles = [
        profile
        for profile in sorted(BROKER_PROFILES)
        if profile == "auto"
        or api_name not in BROKER_STRICT_UNSUPPORTED_APIS.get(profile, frozenset())
    ]
    return {
        "lifecycle": sorted(API_ALLOWED_PHASES_LOOKUP[api_name]),
        "market": ["CN"] if category in market_data_categories else ["not_applicable"],
        "frequency": (
            ["1m", "5m", "15m", "30m", "60m", "120m", "1d", "1w", "mo", "1q", "1y"]
            if has_frequency
            else ["not_applicable"]
        ),
        "profile": supported_profiles,
    }


def _observable_contract_for(api_name: str, support: str) -> str:
    exact = {
        "get_history": "get_history: returns count-bounded historical bars with documented fill, adjustment, and container semantics",
        "get_price": "get_price: returns date/count selected historical bars in the broker-profile container shape",
        "run_daily": "run_daily: schedules the callback for execution at the requested trading-session time",
        "set_yesterday_position": "set_yesterday_position: seeds cash, holdings, sellable amount, cost, and position lots",
        "convert_position_from_csv": "convert_position_from_csv: parses documented CSV position fields into position records",
        "create_dir": "create_dir: creates the requested research subdirectory and returns the broker-specific result",
    }
    if api_name in exact:
        return exact[api_name]
    if support == "unsupported":
        return f"{api_name}: raises NotImplementedError instead of returning fabricated local-backtest data"
    if api_name.startswith("set_"):
        return f"{api_name}: updates the corresponding strategy configuration consumed by backtest execution"
    if api_name.startswith("get_"):
        subject = api_name.removeprefix("get_").replace("_", " ")
        return f"{api_name}: returns the documented {subject} query result with its public container and value types"
    if api_name.startswith("order"):
        return f"{api_name}: changes portfolio cash/holdings and exposes the resulting order and trade records"
    if api_name == "cancel_order":
        return "cancel_order: changes an eligible order from open to cancelled state"
    if api_name.startswith("is_") or api_name.startswith("check_") or api_name.startswith("filter_"):
        return f"{api_name}: returns the documented market/context predicate or filtered security result"
    return f"{api_name}: produces its documented public return value or named operational side effect"


for _api_name, _api_contract in PTRADE_API_CONTRACTS.items():
    _api_contract["applicability"] = _applicability_for(
        _api_name, str(_api_contract["category"])
    )
    _api_contract["observable_contract"] = _observable_contract_for(
        _api_name, str(_api_contract["support"])
    )
