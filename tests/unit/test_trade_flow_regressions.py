from __future__ import annotations

import pandas as pd
import pytest

from simtradelab.backtest.backtest_stats import StatsCollector
from simtradelab.backtest.config import BacktestConfig
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.stats import generate_backtest_report
from simtradelab.ptrade.config_manager import config as ptrade_config
from simtradelab.ptrade.market_profile import get_market_profile
from simtradelab.ptrade.strategy_engine import StrategyExecutionEngine


@pytest.fixture(autouse=True)
def reset_ptrade_config():
    ptrade_config.reset_to_defaults()
    yield
    ptrade_config.reset_to_defaults()


def _price_frame(dates: pd.DatetimeIndex, close: float = 10.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 100_000.0,
            "amount": close * 100_000.0,
        },
        index=dates,
    )


def _build_daily_engine(simple_log, dates: pd.DatetimeIndex, stocks: list[str]):
    benchmark_dates = dates.insert(0, dates[0] - pd.Timedelta(days=1))
    benchmark = _price_frame(benchmark_dates, close=100.0)

    runner = BacktestRunner()
    runner._profile = get_market_profile("CN")
    runner.stock_data_dict = {stock: _price_frame(dates) for stock in stocks}
    runner.stock_data_dict_1m = None
    runner.valuation_dict = {}
    runner.fundamentals_dict = {}
    runner.exrights_dict = {}
    runner.benchmark_data = {"000300.SS": benchmark}
    runner.stock_metadata = pd.DataFrame()
    runner.index_constituents = {}
    runner.stock_status_history = {}
    runner.adj_pre_cache = {}
    runner.adj_post_cache = {}
    runner.dividend_cache = {}
    runner.trade_days = dates

    backtest_config = BacktestConfig(
        strategy_name="trade_flow_regression",
        start_date=dates[0],
        end_date=dates[-1] + pd.Timedelta(days=1),
        initial_capital=100_000.0,
        frequency="1d",
        market="CN",
        t_plus_1=True,
    )
    context, api = runner._initialize_context(backtest_config, dates[0], simple_log)
    collector = StatsCollector()
    api.stats_collector = collector
    engine = StrategyExecutionEngine(
        context=context,
        api=api,
        stats_collector=collector,
        log=simple_log,
        frequency="1d",
    )
    return context, api, collector, engine, benchmark


def test_single_day_report_includes_real_buy_commission(simple_log):
    trade_date = pd.Timestamp("2024-01-02")
    dates = pd.DatetimeIndex([trade_date])
    stock = "600000.SH"
    context, api, collector, engine, benchmark = _build_daily_engine(simple_log, dates, [stock])

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)

    def handle_data(_context, _data):
        assert api.order(stock, 100, limit_price=10.0) is not None

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True

    commission = 1_000.0 * (0.001 + 0.0000487)
    expected_cash = 100_000.0 - 1_000.0 - commission
    expected_final_value = expected_cash + 1_000.0
    expected_return = (expected_final_value - 100_000.0) / 100_000.0
    report = generate_backtest_report(
        collector.stats,
        trade_date,
        trade_date,
        benchmark,
    )

    assert context.total_commission == pytest.approx(commission)
    assert context.portfolio.cash == pytest.approx(expected_cash)
    assert collector.stats.portfolio_values == pytest.approx([expected_final_value])
    assert collector.stats.daily_pnl == pytest.approx([-commission])
    assert report["final_value"] == pytest.approx(expected_final_value)
    assert report["total_return"] == pytest.approx(expected_return)
    assert report["max_drawdown"] == pytest.approx(expected_return)


def test_t_plus_one_real_orders_and_daily_rollover(simple_log):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")])
    truncated_stock = "600000.SH"
    rollover_stock = "000001.SZ"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log,
        dates,
        [truncated_stock, rollover_stock],
    )
    observed = {}

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.set_yesterday_position(
            [
                {"sid": truncated_stock, "amount": 100, "enable_amount": 100, "cost_basis": 10.0},
                {"sid": rollover_stock, "amount": 100, "enable_amount": 100, "cost_basis": 10.0},
            ]
        )

    def handle_data(_context, _data):
        current_date = pd.Timestamp(context.current_dt).normalize()
        if current_date == dates[0]:
            assert api.order(truncated_stock, 100, limit_price=10.0) is not None
            assert api.order(rollover_stock, 100, limit_price=10.0) is not None

            observed["day_one_after_add"] = {
                stock: (
                    context.portfolio.positions[stock].amount,
                    context.portfolio.positions[stock].enable_amount,
                )
                for stock in (truncated_stock, rollover_stock)
            }

            assert api.order(truncated_stock, -200, limit_price=10.0) is not None
            position = context.portfolio.positions[truncated_stock]
            observed["day_one_after_sell"] = (position.amount, position.enable_amount)
        else:
            rollover_position = context.portfolio.positions[rollover_stock]
            observed["day_two_before_sell"] = (
                rollover_position.amount,
                rollover_position.enable_amount,
            )
            assert api.order(rollover_stock, -200, limit_price=10.0) is not None
            observed["day_two_position_removed"] = rollover_stock not in context.portfolio.positions

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True

    assert observed["day_one_after_add"] == {
        truncated_stock: (200, 100),
        rollover_stock: (200, 100),
    }
    assert observed["day_one_after_sell"] == (100, 0)
    assert observed["day_two_before_sell"] == (200, 200)
    assert observed["day_two_position_removed"] is True
    assert collector.stats.daily_buy_amount == pytest.approx([2_000.0, 0.0])
    assert collector.stats.daily_sell_amount == pytest.approx([1_000.0, 2_000.0])
