from __future__ import annotations

import pandas as pd
import pytest

from simtradelab.backtest.backtest_stats import StatsCollector
from simtradelab.backtest.config import BacktestConfig
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.stats import generate_backtest_report
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.ptrade.market_profile import get_market_profile
from simtradelab.ptrade.strategy_engine import StrategyExecutionEngine


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


def _build_daily_engine(
    simple_log,
    dates: pd.DatetimeIndex,
    stocks: list[str],
    *,
    frequency: str = "1d",
    minute_data: dict[str, pd.DataFrame] | None = None,
):
    benchmark_dates = dates.insert(0, dates[0] - pd.Timedelta(days=1))
    benchmark = _price_frame(benchmark_dates, close=100.0)

    runner = BacktestRunner()
    runner._profile = get_market_profile("CN")
    runner.stock_data_dict = {stock: _price_frame(dates) for stock in stocks}
    runner.stock_data_dict_1m = minute_data
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
        frequency=frequency,
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
        frequency=frequency,
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


@pytest.mark.parametrize("api_name", ["order", "order_target"])
def test_quantity_orders_round_stock_buys_down_to_board_lots(
    simple_log, api_name
):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)

    def handle_data(_context, _data):
        order_id = getattr(api, api_name)(stock, 250, limit_price=10.0)
        assert order_id is not None

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert context.portfolio.positions[stock].amount == 200
    commission = 2_000.0 * (0.001 + 0.0000487)
    assert context.portfolio.cash == pytest.approx(98_000.0 - commission)
    assert [order.amount for order in api.get_orders(stock)] == [200]
    assert [trade[4] for trade in collector.stats.trades] == [200]


def test_get_trades_returns_only_current_trading_day(simple_log):
    dates = pd.DatetimeIndex(
        [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]
    )
    stocks = ["600000.SH", "000001.SZ"]
    context, api, _collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, stocks
    )
    observed = {}

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)

    def handle_data(_context, _data):
        day_index = dates.get_loc(pd.Timestamp(context.current_dt).normalize())
        if day_index == 1:
            observed["before"] = api.get_trades()
        order_id = api.order(stocks[day_index], 100, limit_price=10.0)
        assert order_id is not None
        observed[day_index] = api.get_trades()

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert observed["before"] == {}
    assert len(observed[0]) == 1
    assert len(observed[1]) == 1
    assert next(iter(observed[0].values()))[0][2] == "600000.XSHG"
    assert next(iter(observed[1].values()))[0][2] == "000001.XSHE"


def _assert_value_order_propagation(simple_log, submit_order):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    observed = {}

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)

    def handle_data(_context, _data):
        order_id = submit_order(api, stock)
        assert order_id is not None
        observed["order_id"] = order_id
        observed["order"] = api.get_order(order_id)
        observed["position"] = api.get_position(stock)
        observed["positions"] = api.get_positions(stock)
        observed["trades"] = api.get_trades()

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    commission = 2_000.0 * (0.001 + 0.0000487)
    assert context.portfolio.cash == pytest.approx(98_000.0 - commission)
    assert observed["position"].amount == 200
    assert observed["positions"][stock].amount == 200
    assert observed["order"][0].id == observed["order_id"]
    assert observed["order"][0].filled == 200
    assert next(iter(observed["trades"].values()))[0][4] == 200.0
    assert [trade[4] for trade in collector.stats.trades] == [200]
    return api, stock, observed["order_id"]


def test_order_value_propagates_to_cash_holdings_and_query_records(simple_log):
    api, stock, order_id = _assert_value_order_propagation(
        simple_log,
        lambda api, stock: api.order_value(stock, 2_500.0, limit_price=10.0),
    )
    assert api.get_order(order_id)[0].filled == 200
    assert api.get_position(stock).amount == 200
    assert api.get_positions(stock)[stock].amount == 200


def test_order_target_value_propagates_to_cash_holdings_and_query_records(
    simple_log,
):
    _assert_value_order_propagation(
        simple_log,
        lambda api, stock: api.order_target_value(
            stock, 2_500.0, limit_price=10.0
        ),
    )


def test_order_target_rebalances_to_target_after_t_plus_one_rollover(simple_log):
    dates = pd.DatetimeIndex(
        [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]
    )
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    observed_orders = {}

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)

    def handle_data(_context, _data):
        current_date = pd.Timestamp(context.current_dt).normalize()
        if current_date == dates[1]:
            observed_orders["day_two_before"] = api.get_orders(stock)
        target = 300 if current_date == dates[0] else 100
        assert api.order_target(stock, target, limit_price=10.0) is not None
        observed_orders[current_date] = api.get_orders(stock)

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert context.portfolio.positions[stock].amount == 100
    assert context.portfolio.positions[stock].enable_amount == 100
    assert observed_orders["day_two_before"] == []
    assert [order.amount for order in observed_orders[dates[0]]] == [300]
    assert [order.amount for order in observed_orders[dates[1]]] == [-200]
    assert [trade[4] for trade in collector.stats.trades] == [300, 200]


@pytest.mark.parametrize(
    ("target", "expected_order_amount", "expected_position_amount"),
    [
        (250, None, 250),
        (200, -50, 200),
        (350, 100, 350),
        (300, None, 250),
        (150, -100, 150),
        (0, -250, 0),
    ],
)
def test_order_target_preserves_and_rebalances_seeded_odd_lots(
    simple_log, target, expected_order_amount, expected_position_amount
):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    observed = {}

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.set_yesterday_position(
            [{"sid": stock, "amount": 250, "enable_amount": 250, "cost_basis": 10.0}]
        )

    def handle_data(_context, _data):
        observed["order_id"] = api.order_target(stock, target, limit_price=10.0)

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert (observed["order_id"] is not None) is (expected_order_amount is not None)
    orders = api.get_orders(stock)
    assert [order.amount for order in orders] == (
        [] if expected_order_amount is None else [expected_order_amount]
    )
    position = context.portfolio.positions.get(stock)
    assert (position.amount if position else 0) == expected_position_amount
    assert [trade[4] for trade in collector.stats.trades] == (
        [] if expected_order_amount is None else [abs(expected_order_amount)]
    )


def test_daily_run_daily_executes_before_after_trading_end_and_fires_callbacks(
    simple_log,
):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, _collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    events = []
    observed = {}

    def scheduled(_context):
        events.append(
            ("daily", context._lifecycle_controller.current_phase, context.current_dt)
        )
        order_id = api.order(stock, 100, limit_price=10.0)
        assert order_id is not None
        observed["order_id"] = order_id

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.run_daily(context, scheduled, time="09:31")

    def before_trading_start(_context, _data):
        events.append(("before", context._lifecycle_controller.current_phase, context.current_dt))

    def handle_data(_context, _data):
        events.append(("handle", context._lifecycle_controller.current_phase, context.current_dt))

    def on_order_response(_context, orders):
        events.append(("order", context._lifecycle_controller.current_phase, context.current_dt))
        observed["order_callback"] = orders[0]

    def on_trade_response(_context, trades):
        events.append(("trade", context._lifecycle_controller.current_phase, context.current_dt))
        observed["trade_callback"] = trades[0]

    def after_trading_end(_context, _data):
        events.append(("after", context._lifecycle_controller.current_phase, context.current_dt))

    engine.register_initialize(initialize)
    engine.register_before_trading_start(before_trading_start)
    engine.register_handle_data(handle_data)
    engine.register_on_order_response(on_order_response)
    engine.register_on_trade_response(on_trade_response)
    engine.register_after_trading_end(after_trading_end)

    assert engine.run_backtest(dates) is True
    assert [event[0] for event in events] == [
        "before",
        "handle",
        "daily",
        "order",
        "trade",
        "after",
    ]
    assert events[2][1] is LifecyclePhase.HANDLE_DATA
    assert events[2][2] == pd.Timestamp("2024-01-02 15:00")
    assert events[3][2] == pd.Timestamp("2024-01-02 15:00")
    assert events[4][2] == pd.Timestamp("2024-01-02 15:00")
    assert events[5][2] == pd.Timestamp("2024-01-02 15:30")
    order = api.get_order(observed["order_id"])[0]
    assert order.dt == pd.Timestamp("2024-01-02 15:00")
    assert observed["order_callback"]["order_time"] == "2024-01-02 15:00:00"
    assert observed["trade_callback"]["business_time"] == "2024-01-02 15:00:00"
    assert next(iter(api.get_trades().values()))[0][7] == "2024-01-02 15:00:00"
    assert context.portfolio.positions[stock].amount == 100


def test_minute_run_daily_fires_task_order_callbacks_in_scheduled_bar(simple_log):
    trade_date = pd.Timestamp("2024-01-02")
    dates = pd.DatetimeIndex([trade_date])
    stock = "600000.SH"
    minute_index = pd.date_range(
        "2024-01-02 09:31", "2024-01-02 11:30", freq="min"
    ).append(pd.date_range("2024-01-02 13:01", "2024-01-02 15:00", freq="min"))
    minute_data = {stock: _price_frame(minute_index)}
    context, api, _collector, engine, _benchmark = _build_daily_engine(
        simple_log,
        dates,
        [stock],
        frequency="1m",
        minute_data=minute_data,
    )
    events = []

    def scheduled(_context):
        events.append(("daily", context.current_dt))
        assert api.order(stock, 100, limit_price=10.0) is not None

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.run_daily(context, scheduled, time="9:31")

    def handle_data(_context, _data):
        if context.current_dt <= pd.Timestamp("2024-01-02 09:32"):
            events.append(("handle", context.current_dt))

    def on_order_response(_context, _orders):
        events.append(("order", context.current_dt))

    def on_trade_response(_context, _trades):
        events.append(("trade", context.current_dt))

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)
    engine.register_on_order_response(on_order_response)
    engine.register_on_trade_response(on_trade_response)

    assert engine.run_backtest(dates) is True
    assert events[:5] == [
        ("handle", pd.Timestamp("2024-01-02 09:31")),
        ("daily", pd.Timestamp("2024-01-02 09:31")),
        ("order", pd.Timestamp("2024-01-02 09:31")),
        ("trade", pd.Timestamp("2024-01-02 09:31")),
        ("handle", pd.Timestamp("2024-01-02 09:32")),
    ]


def test_minute_run_daily_executes_1300_before_first_afternoon_bar(simple_log):
    trade_date = pd.Timestamp("2024-01-02")
    dates = pd.DatetimeIndex([trade_date])
    stock = "600000.SH"
    minute_index = pd.date_range(
        "2024-01-02 09:31", "2024-01-02 11:30", freq="min"
    ).append(pd.date_range("2024-01-02 13:01", "2024-01-02 15:00", freq="min"))
    minute_data = {stock: _price_frame(minute_index)}
    context, api, _collector, engine, _benchmark = _build_daily_engine(
        simple_log,
        dates,
        [stock],
        frequency="1m",
        minute_data=minute_data,
    )
    events = []
    observed = {}

    def scheduled(_context):
        events.append(("daily", context.current_dt))
        order_id = api.order(stock, 100, limit_price=10.0)
        assert order_id is not None
        observed["order_id"] = order_id

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.run_daily(context, scheduled, time="13:00")

    def handle_data(_context, _data):
        if context.current_dt in {
            pd.Timestamp("2024-01-02 11:30"),
            pd.Timestamp("2024-01-02 13:01"),
        }:
            events.append(("handle", context.current_dt))

    def on_order_response(_context, orders):
        events.append(("order", context.current_dt))
        observed["order_callback"] = orders[0]

    def on_trade_response(_context, trades):
        events.append(("trade", context.current_dt))
        observed["trade_callback"] = trades[0]

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)
    engine.register_on_order_response(on_order_response)
    engine.register_on_trade_response(on_trade_response)

    assert engine.run_backtest(dates) is True
    assert events == [
        ("handle", pd.Timestamp("2024-01-02 11:30")),
        ("daily", pd.Timestamp("2024-01-02 13:00")),
        ("order", pd.Timestamp("2024-01-02 13:00")),
        ("trade", pd.Timestamp("2024-01-02 13:00")),
        ("handle", pd.Timestamp("2024-01-02 13:01")),
    ]
    order = api.get_order(observed["order_id"])[0]
    assert order.dt == pd.Timestamp("2024-01-02 13:00")
    assert observed["order_callback"]["order_time"] == "2024-01-02 13:00:00"
    assert observed["trade_callback"]["business_time"] == "2024-01-02 13:00:00"


def test_volume_ratio_limits_daily_buy_fill(simple_log):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    context.portfolio._bt_ctx.stock_data_dict[stock].loc[dates[0], "volume"] = 1_000
    callbacks = {}

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.set_limit_mode("LIMIT")
        api.set_volume_ratio(0.25)

    def handle_data(_context, _data):
        assert api.order(stock, 1_000, limit_price=10.0) is not None

    def on_order_response(_context, orders):
        callbacks["order"] = orders[0]

    def on_trade_response(_context, trades):
        callbacks["trade"] = trades[0]

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)
    engine.register_on_order_response(on_order_response)
    engine.register_on_trade_response(on_trade_response)

    assert engine.run_backtest(dates) is True

    expected_commission = 2_000.0 * (0.001 + 0.0000487)
    assert context.portfolio.positions[stock].amount == 200
    assert context.portfolio.cash == pytest.approx(100_000.0 - 2_000.0 - expected_commission)
    assert context.total_commission == pytest.approx(expected_commission)
    assert collector.stats.trades[0][4] == 200
    assert context.blotter.filled_orders[0].amount == 200
    assert context.blotter.filled_orders[0].filled == 200
    assert callbacks["order"]["business_amount"] == 200.0
    assert callbacks["trade"]["business_amount"] == 200.0


@pytest.mark.parametrize(
    ("limit_mode", "volume", "volume_ratio", "expected_amount"),
    [
        ("LIMIT", 1_000, 0.0, 0),
        ("LIMIT", 1_000, 0.25, 200),
        ("LIMIT", 1_000, 1.0, 1_000),
        ("LIMIT", 399, 0.25, 0),
        ("UNLIMITED", 1_000, 0.25, 1_000),
    ],
)
def test_volume_limit_modes_and_ratio_boundaries(
    simple_log, limit_mode, volume, volume_ratio, expected_amount
):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    context.portfolio._bt_ctx.stock_data_dict[stock].loc[dates[0], "volume"] = volume

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.set_limit_mode(limit_mode)
        api.set_volume_ratio(volume_ratio)

    def handle_data(_context, _data):
        order_id = api.order(stock, 1_000, limit_price=10.0)
        assert (order_id is not None) is (expected_amount > 0)

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    actual_amount = context.portfolio.positions.get(stock)
    assert (actual_amount.amount if actual_amount else 0) == expected_amount
    assert sum(trade[4] for trade in collector.stats.trades) == expected_amount
    if expected_amount == 0:
        assert context.portfolio.cash == pytest.approx(100_000.0)
        assert getattr(context, "total_commission", 0.0) == 0.0
        assert context.blotter.all_orders == []
        assert context.blotter.filled_orders == []
        assert api.flush_order_callbacks() == []
        assert api.flush_trade_callbacks() == []


def test_volume_ratio_limits_sell_and_preserves_t_plus_one(simple_log):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    context.portfolio._bt_ctx.stock_data_dict[stock].loc[dates[0], "volume"] = 1_000
    callbacks = {}

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.set_limit_mode("LIMIT")
        api.set_volume_ratio(0.25)
        api.set_yesterday_position(
            [{"sid": stock, "amount": 100, "enable_amount": 100, "cost_basis": 10.0}]
        )

    def handle_data(_context, _data):
        assert api.order(stock, 900, limit_price=10.0) is not None
        assert context.portfolio.positions[stock].enable_amount == 100
        assert api.order(stock, -1_000, limit_price=10.0) is not None

    def on_order_response(_context, orders):
        callbacks["orders"] = orders

    def on_trade_response(_context, trades):
        callbacks["trades"] = trades

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)
    engine.register_on_order_response(on_order_response)
    engine.register_on_trade_response(on_trade_response)

    assert engine.run_backtest(dates) is True
    buy_commission = 2_000.0 * (0.001 + 0.0000487)
    sell_commission = 1_000.0 * (0.001 + 0.0000487 + 0.001)
    assert context.portfolio.positions[stock].amount == 200
    assert context.portfolio.positions[stock].enable_amount == 0
    assert [trade[4] for trade in collector.stats.trades] == [200, 100]
    assert context.portfolio.cash == pytest.approx(
        100_000.0 - 2_000.0 - buy_commission + 1_000.0 - sell_commission
    )
    assert context.total_commission == pytest.approx(buy_commission + sell_commission)
    orders = api.get_orders(stock)
    assert [order.amount for order in orders] == [200, -100]
    assert [order.filled for order in orders] == [200, -100]
    assert [item["business_amount"] for item in callbacks["orders"]] == [200.0, 100.0]
    assert [item["business_amount"] for item in callbacks["trades"]] == [200.0, 100.0]
    trades = api.get_trades()
    assert [rows[0][4] for rows in trades.values()] == [200.0, 100.0]


def test_unlimited_mode_does_not_cap_sell_volume(simple_log):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    context.portfolio._bt_ctx.stock_data_dict[stock].loc[dates[0], "volume"] = 100

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.set_limit_mode("UNLIMITED")
        api.set_volume_ratio(0.0)
        api.set_yesterday_position(
            [{"sid": stock, "amount": 1_000, "enable_amount": 1_000, "cost_basis": 10.0}]
        )

    def handle_data(_context, _data):
        assert api.order(stock, -1_000, limit_price=10.0) is not None

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert stock not in context.portfolio.positions
    assert [trade[4] for trade in collector.stats.trades] == [1_000]
    assert api.get_orders(stock)[0].filled == -1_000


def test_volume_ratio_uses_current_minute_bar_volume(simple_log):
    trade_date = pd.Timestamp("2024-01-02")
    dates = pd.DatetimeIndex([trade_date])
    stock = "600000.SH"
    minute_dt = trade_date.replace(hour=9, minute=31)
    minute_data = {stock: _price_frame(pd.DatetimeIndex([minute_dt]))}
    minute_data[stock].loc[minute_dt, "volume"] = 1_000
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log,
        dates,
        [stock],
        frequency="1m",
        minute_data=minute_data,
    )
    api.data_context.stock_data_dict[stock].loc[trade_date, "volume"] = 100_000

    def initialize(_context):
        api.set_slippage(0.0)
        api.set_commission(commission_ratio=0.001, min_commission=1.0)
        api.set_limit_mode("LIMIT")
        api.set_volume_ratio(0.25)

    def handle_data(_context, _data):
        if context.current_dt == minute_dt:
            assert api.order_processor._get_current_bar_volume(stock) == 1_000
            assert api.order(stock, 1_000, limit_price=10.0) is not None

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert context.portfolio.positions[stock].amount == 200
    assert [trade[4] for trade in collector.stats.trades] == [200]


def test_zero_volume_rejects_order_without_mutating_trade_state(simple_log):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    context.portfolio._bt_ctx.stock_data_dict[stock].loc[dates[0], "volume"] = 0

    def initialize(_context):
        api.set_limit_mode("LIMIT")
        api.set_volume_ratio(1.0)

    def handle_data(_context, _data):
        assert api.order(stock, 100) is None

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert stock not in context.portfolio.positions
    assert context.portfolio.cash == pytest.approx(100_000.0)
    assert collector.stats.trades == []
    assert context.blotter.filled_orders == []


def test_suspension_rejects_unlimited_order_with_explicit_limit_price(simple_log):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    context.portfolio._bt_ctx.stock_data_dict[stock].loc[dates[0], "volume"] = 0

    def initialize(_context):
        api.set_limit_mode("UNLIMITED")
        api.set_volume_ratio(1.0)

    def handle_data(_context, _data):
        assert api.order(stock, 100, limit_price=10.0) is None

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(dates) is True
    assert stock not in context.portfolio.positions
    assert context.portfolio.cash == pytest.approx(100_000.0)
    assert getattr(context, "total_commission", 0.0) == 0.0
    assert collector.stats.trades == []
    assert context.blotter.all_orders == []
    assert context.blotter.filled_orders == []
    assert api.flush_order_callbacks() == []
    assert api.flush_trade_callbacks() == []


def test_pre_first_minute_bar_rejects_order_without_using_future_volume(simple_log):
    trade_date = pd.Timestamp("2024-01-02")
    dates = pd.DatetimeIndex([trade_date])
    stock = "600000.SH"
    first_bar = trade_date.replace(hour=9, minute=31)
    minute_data = {stock: _price_frame(pd.DatetimeIndex([first_bar]))}
    context, api, collector, _engine, _benchmark = _build_daily_engine(
        simple_log,
        dates,
        [stock],
        frequency="1m",
        minute_data=minute_data,
    )
    context.current_dt = trade_date.replace(hour=9, minute=30)
    context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    api.set_limit_mode("LIMIT")
    api.set_volume_ratio(1.0)
    context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    assert api.order(stock, 100, limit_price=10.0) is None
    assert stock not in context.portfolio.positions
    assert context.portfolio.cash == pytest.approx(100_000.0)
    assert getattr(context, "total_commission", 0.0) == 0.0
    assert collector.stats.trades == []
    assert context.blotter.all_orders == []
    assert api.flush_order_callbacks() == []
    assert api.flush_trade_callbacks() == []


def test_missing_daily_bar_rejects_order_without_crashing(simple_log):
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    stock = "600000.SH"
    context, api, collector, _engine, _benchmark = _build_daily_engine(
        simple_log, dates, [stock]
    )
    context.current_dt = pd.Timestamp("2024-01-03")
    context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    api.set_limit_mode("LIMIT")
    api.set_volume_ratio(1.0)
    context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    assert api.order(stock, 100, limit_price=10.0) is None
    assert stock not in context.portfolio.positions
    assert context.portfolio.cash == pytest.approx(100_000.0)
    assert getattr(context, "total_commission", 0.0) == 0.0
    assert collector.stats.trades == []
    assert context.blotter.all_orders == []
    assert api.flush_order_callbacks() == []
    assert api.flush_trade_callbacks() == []
