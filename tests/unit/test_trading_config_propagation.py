from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from simtradelab.backtest.backtest_stats import StatsCollector
from simtradelab.backtest.config import BacktestConfig
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.config_manager import TradingConfig, config
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.ptrade.market_profile import get_market_profile

ROOT = Path(__file__).resolve().parents[2]
ORDER_PROCESSOR = "src/simtradelab/ptrade/order_processor.py"

TRADING_CONFIG_PROPAGATION_CONTRACTS = {
    "commission_ratio": {
        "classification": "full",
        "public_setter": "set_commission",
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_set_commission_controls_cash_cost_basis_and_trade_commission",
        "behavior_token": "set_commission",
        "production_consumers": [(ORDER_PROCESSOR, "calculate_commission")],
    },
    "min_commission": {
        "classification": "full",
        "public_setter": "set_commission",
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_set_commission_controls_cash_cost_basis_and_trade_commission",
        "behavior_token": "set_commission",
        "production_consumers": [(ORDER_PROCESSOR, "calculate_commission")],
    },
    "slippage": {
        "classification": "full",
        "public_setter": "set_slippage",
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_set_slippage_controls_buy_and_sell_prices_and_cash",
        "behavior_token": "set_slippage",
        "production_consumers": [(ORDER_PROCESSOR, "get_execution_price")],
    },
    "fixed_slippage": {
        "classification": "full",
        "public_setter": "set_fixed_slippage",
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_set_fixed_slippage_alone_controls_fill_price_and_cash",
        "behavior_token": "set_fixed_slippage",
        "production_consumers": [(ORDER_PROCESSOR, "get_execution_price")],
    },
    "volume_ratio": {
        "classification": "full",
        "public_setter": "set_volume_ratio",
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_volume_ratio_and_limit_mode_control_the_actual_fill",
        "behavior_token": "volume_ratio",
        "production_consumers": [(ORDER_PROCESSOR, "limit_fill_amount")],
    },
    "limit_mode": {
        "classification": "full",
        "public_setter": "set_limit_mode",
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_volume_ratio_and_limit_mode_control_the_actual_fill",
        "behavior_token": "limit_mode",
        "production_consumers": [(ORDER_PROCESSOR, "limit_fill_amount")],
    },
    "transfer_fee_rate": {
        "classification": "market-default-only",
        "public_setter": None,
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_market_fee_defaults_reach_buy_and_sell_commissions",
        "behavior_token": "market_fee_defaults",
        "production_consumers": [(ORDER_PROCESSOR, "calculate_commission")],
        "reason": "No PTrade public setter; selected by BacktestConfig.market.",
    },
    "stamp_tax_rate": {
        "classification": "market-default-only",
        "public_setter": None,
        "behavior_test": "tests/unit/test_trading_config_propagation.py::test_market_fee_defaults_reach_buy_and_sell_commissions",
        "behavior_token": "market_fee_defaults",
        "production_consumers": [(ORDER_PROCESSOR, "calculate_commission")],
        "reason": "No PTrade public setter; selected by BacktestConfig.market.",
    },
    "commission_type": {
        "classification": "pending",
        "public_setter": "set_commission",
        "production_consumers": [],
        "expected_unconsumed": True,
        "reason": (
            "set_commission stores STOCK/ETF/LOF type, but the backtester has no "
            "instrument classifier or per-type commission schedule to consume it."
        ),
    },
}


def _function_node(node_id: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    parts = node_id.split("::")
    path = ROOT / parts[0]
    module = ast.parse(path.read_text(encoding="utf-8"))
    body = module.body
    for container_name in parts[1:-1]:
        container = next(
            node
            for node in body
            if isinstance(node, ast.ClassDef) and node.name == container_name
        )
        body = container.body
    return next(
        node
        for node in body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == parts[-1]
    )


def _calls_public_api(function_node, api_name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Attribute) and node.func.attr == api_name)
            or (isinstance(node.func, ast.Name) and node.func.id == api_name)
        )
        for node in ast.walk(function_node)
    )


def _reads_trading_config_field(node, field: str) -> bool:
    return any(
        isinstance(child, ast.Attribute)
        and child.attr == field
        and isinstance(child.value, ast.Attribute)
        and child.value.attr == "trading"
        and isinstance(child.value.value, ast.Name)
        and child.value.value.id == "config"
        for child in ast.walk(node)
    )


def _production_symbol(path: str, symbol: str):
    module = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    return next(
        node
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == symbol
    )


def _production_reads_field_anywhere(field: str) -> bool:
    for path in (ROOT / "src/simtradelab/ptrade").rglob("*.py"):
        module = ast.parse(path.read_text(encoding="utf-8"))
        if _reads_trading_config_field(module, field):
            return True
    return False


def _trading_config_contract_errors(contracts):
    errors = []
    if set(contracts) != set(TradingConfig.model_fields):
        errors.append("contract fields do not match TradingConfig fields")
    for field, contract in contracts.items():
        setter = contract.get("public_setter")
        if setter is None:
            if "No PTrade public setter" not in contract.get("reason", ""):
                errors.append(f"{field}: missing explicit no-setter reason")
        elif not hasattr(PtradeAPI, setter):
            errors.append(f"{field}: missing public setter {setter}")

        if behavior_test := contract.get("behavior_test"):
            try:
                function_node = _function_node(behavior_test)
            except (FileNotFoundError, StopIteration):
                errors.append(f"{field}: missing behavior test {behavior_test}")
            else:
                if contract.get("behavior_token") not in function_node.name:
                    errors.append(f"{field}: unrelated behavior evidence {behavior_test}")
                if setter is not None and not _calls_public_api(function_node, setter):
                    errors.append(f"{field}: behavior test does not call {setter}")
        elif contract["classification"] != "pending" or not contract.get("reason"):
            errors.append(f"{field}: missing behavior evidence or pending reason")

        consumers = contract.get("production_consumers", [])
        if contract.get("expected_unconsumed"):
            if consumers or _production_reads_field_anywhere(field):
                errors.append(f"{field}: pending field unexpectedly has a production consumer")
            continue
        if not consumers:
            errors.append(f"{field}: missing production consumer")
            continue
        for path, symbol in consumers:
            try:
                consumer_node = _production_symbol(path, symbol)
            except (FileNotFoundError, StopIteration):
                errors.append(f"{field}: missing production consumer {path}:{symbol}")
            else:
                if not _reads_trading_config_field(consumer_node, field):
                    errors.append(
                        f"{field}: production consumer {path}:{symbol} does not read field"
                    )
    return errors


@pytest.fixture
def trading_api(ptrade_api):
    trade_date = pd.Timestamp("2024-01-02")
    stock = "600000.SH"
    ptrade_api.data_context.stock_data_dict = {
        stock: pd.DataFrame(
            {
                "open": [10.0],
                "high": [10.0],
                "low": [10.0],
                "close": [10.0],
                "volume": [100_000.0],
                "amount": [1_000_000.0],
            },
            index=pd.DatetimeIndex([trade_date]),
        )
    }
    ptrade_api.context.current_dt = trade_date
    ptrade_api.context.t_plus_1 = False
    ptrade_api.stats_collector = StatsCollector()
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    ptrade_api.set_limit_mode("UNLIMITED")
    return ptrade_api, stock


def _build_market_api(simple_log, market: str):
    trade_date = pd.Timestamp("2024-01-02")
    stock = "600000.SH" if market == "CN" else "AAPL.US"
    stock_data = {
        stock: pd.DataFrame(
            {
                "open": [10.0],
                "high": [10.0],
                "low": [10.0],
                "close": [10.0],
                "volume": [100_000.0],
                "amount": [1_000_000.0],
            },
            index=pd.DatetimeIndex([trade_date]),
        )
    }
    runner = BacktestRunner()
    runner._profile = get_market_profile(market)
    runner.stock_data_dict = stock_data
    runner.stock_data_dict_1m = None
    runner.valuation_dict = {}
    runner.fundamentals_dict = {}
    runner.exrights_dict = {}
    runner.benchmark_data = {}
    runner.stock_metadata = pd.DataFrame()
    runner.index_constituents = {}
    runner.stock_status_history = {}
    runner.adj_pre_cache = {}
    runner.adj_post_cache = {}
    runner.dividend_cache = {}
    runner.trade_days = pd.DatetimeIndex([trade_date])
    backtest_config = BacktestConfig(
        strategy_name="trading_config_propagation",
        start_date=trade_date,
        end_date=trade_date + pd.Timedelta(days=1),
        initial_capital=1_000_000.0,
        market=market,
        t_plus_1=False,
    )
    context, api = runner._initialize_context(backtest_config, trade_date, simple_log)
    api.stats_collector = StatsCollector()
    context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    api.set_limit_mode("UNLIMITED")
    api.set_slippage(0.0)
    api.set_commission(commission_ratio=0.001, min_commission=1.0)
    context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
    return api, stock


def test_every_trading_config_field_has_behavior_evidence_or_an_explicit_gap():
    assert _trading_config_contract_errors(TRADING_CONFIG_PROPAGATION_CONTRACTS) == []


def test_trading_config_guard_rejects_unrelated_behavior_test():
    mutated = deepcopy(TRADING_CONFIG_PROPAGATION_CONTRACTS)
    mutated["commission_ratio"]["behavior_test"] = (
        "tests/unit/test_trading_config_propagation.py::test_set_fixed_slippage_alone_controls_fill_price_and_cash"
    )

    errors = _trading_config_contract_errors(mutated)

    assert any("commission_ratio: unrelated behavior evidence" in error for error in errors)


def test_trading_config_guard_rejects_unrelated_production_consumer():
    mutated = deepcopy(TRADING_CONFIG_PROPAGATION_CONTRACTS)
    mutated["commission_ratio"]["production_consumers"] = [
        (ORDER_PROCESSOR, "get_execution_price")
    ]

    errors = _trading_config_contract_errors(mutated)

    assert any(
        "commission_ratio: production consumer" in error
        and "does not read field" in error
        for error in errors
    )


def test_each_test_starts_with_fresh_trading_config():
    assert config.trading == TradingConfig()


def test_set_fixed_slippage_alone_controls_fill_price_and_cash(trading_api):
    api, stock = trading_api
    api.set_fixed_slippage(fixedslippage=0.2)
    api.set_commission(commission_ratio=0.001, min_commission=1.0)
    api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    assert api.order(stock, 100, limit_price=10.0) is not None

    expected_price = 10.1
    expected_commission = 100 * expected_price * (0.001 + 0.0000487)
    order = api.get_orders(stock)[0]
    trade = next(iter(api.get_trades().values()))[0]
    position = api.context.portfolio.positions[stock]
    assert order.limit == pytest.approx(expected_price)
    assert trade[5] == pytest.approx(expected_price)
    assert api.stats_collector.stats.trades[0][5] == pytest.approx(expected_price)
    assert api.context.total_commission == pytest.approx(expected_commission)
    assert api.context.portfolio.cash == pytest.approx(
        1_000_000.0 - 100 * expected_price - expected_commission
    )
    assert position.amount == 100
    assert position.cost_basis == pytest.approx(
        expected_price + expected_commission / 100
    )


def test_set_slippage_zero_disables_previous_fixed_slippage(trading_api):
    api, stock = trading_api
    api.set_fixed_slippage(fixedslippage=0.2)
    api.set_slippage(slippage=0.0)
    api.set_commission(commission_ratio=0.001, min_commission=1.0)
    api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    assert api.order(stock, 100, limit_price=10.0) is not None

    expected_price = 10.0
    order = api.get_orders(stock)[0]
    trade = next(iter(api.get_trades().values()))[0]
    assert order.limit == pytest.approx(expected_price)
    assert trade[5] == pytest.approx(expected_price)
    assert api.stats_collector.stats.trades[0][5] == pytest.approx(expected_price)


@pytest.mark.parametrize(
    ("price", "expected_broker_fee"),
    [
        (10.0, 2.0),
        (100.0, 10.0),
    ],
)
def test_set_commission_controls_cash_cost_basis_and_trade_commission(
    trading_api, price, expected_broker_fee
):
    api, stock = trading_api
    api.set_slippage(0.0)
    api.set_commission(commission_ratio=0.001, min_commission=2.0)
    api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    assert api.order(stock, 100, limit_price=price) is not None

    value = 100 * price
    expected_commission = expected_broker_fee + value * 0.0000487
    position = api.context.portfolio.positions[stock]
    assert api.context.total_commission == pytest.approx(expected_commission)
    assert api.context.portfolio.cash == pytest.approx(
        1_000_000.0 - value - expected_commission
    )
    assert position.amount == 100
    assert position.cost_basis == pytest.approx(
        price + expected_commission / 100
    )
    assert api.stats_collector.stats.trades[0][6] == pytest.approx(value)
    assert api.stats_collector.stats.trades[0][7] == pytest.approx(
        round(expected_commission, 2)
    )


def test_set_slippage_controls_buy_and_sell_prices_and_cash(trading_api):
    api, stock = trading_api
    api.set_slippage(slippage=0.02)
    api.set_commission(commission_ratio=0.001, min_commission=1.0)
    api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    assert api.order(stock, 100, limit_price=10.0) is not None
    assert api.order(stock, -100, limit_price=10.0) is not None

    buy_price = 10.1
    sell_price = 9.9
    buy_value = 100 * buy_price
    sell_value = 100 * sell_price
    buy_commission = max(buy_value * 0.001, 1.0) + buy_value * 0.0000487
    sell_commission = (
        max(sell_value * 0.001, 1.0)
        + sell_value * (0.0000487 + 0.001)
    )
    orders = api.get_orders(stock)
    trades = api.stats_collector.stats.trades
    assert [order.limit for order in orders] == pytest.approx([buy_price, sell_price])
    assert [trade[3] for trade in trades] == ["buy", "sell"]
    assert [trade[5] for trade in trades] == pytest.approx([buy_price, sell_price])
    assert api.context.total_commission == pytest.approx(
        buy_commission + sell_commission
    )
    assert api.context.portfolio.cash == pytest.approx(
        1_000_000.0
        - 100 * buy_price
        - buy_commission
        + 100 * sell_price
        - sell_commission
    )
    assert stock not in api.context.portfolio.positions


@pytest.mark.parametrize(
    ("limit_mode", "expected_amount"),
    [
        ("LIMIT", 200),
        ("UNLIMITED", 1_000),
    ],
)
def test_volume_ratio_and_limit_mode_control_the_actual_fill(
    trading_api, limit_mode, expected_amount
):
    api, stock = trading_api
    api.data_context.stock_data_dict[stock].loc[api.context.current_dt, "volume"] = 1_000
    api.set_slippage(0.0)
    api.set_commission(commission_ratio=0.001, min_commission=1.0)
    api.set_limit_mode(limit_mode)
    api.set_volume_ratio(0.25)
    api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    assert api.order(stock, 1_000, limit_price=10.0) is not None

    expected_value = expected_amount * 10.0
    expected_commission = expected_value * (0.001 + 0.0000487)
    order = api.get_orders(stock)[0]
    trade = next(iter(api.get_trades().values()))[0]
    assert order.amount == expected_amount
    assert order.filled == expected_amount
    assert trade[4] == expected_amount
    assert api.context.portfolio.positions[stock].amount == expected_amount
    assert api.context.portfolio.cash == pytest.approx(
        1_000_000.0 - expected_value - expected_commission
    )


@pytest.mark.parametrize(
    ("market", "transfer_fee_rate", "stamp_tax_rate"),
    [
        ("CN", 0.0000487, 0.001),
        ("US", 0.0, 0.0),
    ],
)
def test_market_fee_defaults_reach_buy_and_sell_commissions(
    simple_log, market, transfer_fee_rate, stamp_tax_rate
):
    api, stock = _build_market_api(simple_log, market)

    assert api.order(stock, 100, limit_price=10.0) is not None
    assert api.order(stock, -100, limit_price=10.0) is not None

    value = 1_000.0
    buy_commission = max(value * 0.001, 1.0) + value * transfer_fee_rate
    sell_commission = buy_commission + value * stamp_tax_rate
    assert [trade[7] for trade in api.stats_collector.stats.trades] == pytest.approx(
        [round(buy_commission, 2), round(sell_commission, 2)]
    )
    assert api.context.total_commission == pytest.approx(
        buy_commission + sell_commission
    )
    assert api.context.portfolio.cash == pytest.approx(
        1_000_000.0 - buy_commission - sell_commission
    )
