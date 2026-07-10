from types import SimpleNamespace
from typing import ClassVar

import pandas as pd

from simtradelab.backtest import runner as runner_module
from simtradelab.backtest.backtest_stats import StatsCollector
from simtradelab.backtest.config import BacktestConfig
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.ptrade.market_profile import get_market_profile
from simtradelab.ptrade.strategy_engine import StrategyExecutionEngine


class _NullLog:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


def test_minute_context_uses_minute_stock_data():
    runner = BacktestRunner()
    daily_data = object()
    minute_data = object()
    runner.stock_data_dict = daily_data
    runner.stock_data_dict_1m = minute_data
    runner.valuation_dict = {}
    runner.fundamentals_dict = {}
    runner.exrights_dict = {}
    runner.benchmark_data = {}
    runner.stock_metadata = pd.DataFrame()
    runner._profile = get_market_profile("CN")

    config = SimpleNamespace(
        initial_capital=100_000,
        frequency="1m",
        t_plus_1=None,
        broker_profile="auto",
    )

    context, _ = runner._initialize_context(config, pd.Timestamp("2024-01-02"), _NullLog())

    assert context.portfolio._bt_ctx.stock_data_dict is minute_data


def test_minute_bars_cover_exactly_240_trading_minutes():
    StrategyExecutionEngine._MINUTE_OFFSETS = None
    engine = object.__new__(StrategyExecutionEngine)

    minute_bars = engine._get_minute_bars(pd.Timestamp("2024-01-02"))

    assert len(minute_bars) == 240
    assert minute_bars[0] == pd.Timestamp("2024-01-02 09:31")
    assert minute_bars[119] == pd.Timestamp("2024-01-02 11:30")
    assert minute_bars[120] == pd.Timestamp("2024-01-02 13:01")
    assert minute_bars[-1] == pd.Timestamp("2024-01-02 15:00")


def test_minute_backtest_reads_each_bar_and_marks_position_at_close():
    stock = "600000.SH"
    trade_day = pd.Timestamp("2024-01-02")
    minute_index = pd.date_range(
        "2024-01-02 09:31", "2024-01-02 11:30", freq="min"
    ).append(
        pd.date_range("2024-01-02 13:01", "2024-01-02 15:00", freq="min")
    )
    minute_prices = pd.Series(
        range(len(minute_index)), index=minute_index, dtype=float
    ) / (len(minute_index) - 1) * 10 + 10
    minute_data = pd.DataFrame(
        {
            "open": minute_prices,
            "high": minute_prices,
            "low": minute_prices,
            "close": minute_prices,
            "volume": 1_000,
        },
        index=minute_index,
    )
    daily_data = pd.DataFrame(
        {
            "open": [7.0],
            "high": [7.0],
            "low": [7.0],
            "close": [7.0],
            "volume": [1_000],
        },
        index=pd.DatetimeIndex([trade_day]),
    )

    runner = BacktestRunner()
    runner.stock_data_dict = {stock: daily_data}
    runner.stock_data_dict_1m = {stock: minute_data}
    runner.valuation_dict = {}
    runner.fundamentals_dict = {}
    runner.exrights_dict = {}
    runner.benchmark_data = {}
    runner.stock_metadata = pd.DataFrame()
    runner.trade_days = pd.DatetimeIndex([trade_day])
    runner._profile = get_market_profile("CN")

    config = SimpleNamespace(
        initial_capital=100_000,
        frequency="1m",
        t_plus_1=None,
        broker_profile="auto",
    )
    context, api = runner._initialize_context(config, trade_day, _NullLog())
    stats_collector = StatsCollector()
    api.stats_collector = stats_collector
    engine = StrategyExecutionEngine(
        context=context,
        api=api,
        stats_collector=stats_collector,
        log=_NullLog(),
        frequency="1m",
    )
    observed_times = []
    observed_prices = []

    def initialize(strategy_context):
        strategy_context.portfolio._cash -= 500
        strategy_context.portfolio.add_position(stock, 100, 5.0, trade_day)

    def handle_data(strategy_context, data):
        observed_times.append(strategy_context.current_dt)
        observed_prices.append(data[stock].close)

    engine.register_initialize(initialize)
    engine.register_handle_data(handle_data)

    assert engine.run_backtest(pd.DatetimeIndex([trade_day])) is True
    assert len(observed_times) == 240
    assert observed_times[0] == pd.Timestamp("2024-01-02 09:31")
    assert observed_times[-1] == pd.Timestamp("2024-01-02 15:00")
    assert observed_prices[0] == 10.0
    assert observed_prices[-1] == 20.0
    assert stats_collector.stats.portfolio_values == [101_500.0]
    assert context.portfolio.positions[stock].last_sale_price == 20.0


def test_run_forwards_data_loading_options(tmp_path):
    runner = BacktestRunner()
    runner._cancel_event = SimpleNamespace(is_set=lambda: True)
    captured = {}

    def fake_load_data(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return pd.DataFrame()

    runner._load_data = fake_load_data
    config = BacktestConfig(
        strategy_name="unused",
        start_date="2024-01-01",
        end_date="2024-01-03",
        data_path=str(tmp_path),
        strategies_path=str(tmp_path),
        optimization_mode=True,
        frequency="1m",
        enable_multiprocessing=False,
        num_workers=3,
        use_data_server=False,
    )

    runner.run(config)

    assert captured["kwargs"] == {
        "enable_multiprocessing": False,
        "num_workers": 3,
        "use_data_server": False,
    }


def test_load_data_applies_performance_config_and_disables_caches(monkeypatch, tmp_path):
    fresh_benchmark = pd.DataFrame({"volume": [1]}, index=[pd.Timestamp("2024-01-02")])

    class ExistingServer:
        def __init__(self):
            self.clear_count = 0

        def _clear_all_caches(self):
            self.clear_count += 1

    existing_server = ExistingServer()

    class FakeDataServer:
        _instance = existing_server
        _initialized = True
        calls: ClassVar[list] = []

        def __init__(self, required_data, frequency, data_path, market="CN"):
            self.calls.append((required_data, frequency, data_path, market))
            self.stock_data_dict = {}
            self.stock_data_dict_1m = {}
            self.valuation_dict = {}
            self.fundamentals_dict = {}
            self.exrights_dict = {}
            self.benchmark_data = {"000300.SS": fresh_benchmark}
            self.stock_metadata = pd.DataFrame()
            self.index_constituents = {}
            self.stock_status_history = {}
            self.adj_pre_cache = None
            self.adj_post_cache = None
            self.dividend_cache = None
            self.trade_days = None

        def get_benchmark_data(self):
            return fresh_benchmark

    class FakePerformanceConfig:
        def __init__(self):
            self.enable_multiprocessing = True
            self.num_workers = 1

        def set_multiprocessing(self, enabled):
            self.enable_multiprocessing = enabled

        def set_num_workers(self, num_workers):
            self.num_workers = num_workers

    performance_config = FakePerformanceConfig()
    monkeypatch.setattr(runner_module, "DataServer", FakeDataServer)
    monkeypatch.setattr(
        "simtradelab.utils.performance_config.get_performance_config",
        lambda: performance_config,
    )

    runner = BacktestRunner()
    runner._data_loaded = True
    runner.benchmark_data = {"cached": pd.DataFrame()}

    result = runner._load_data(
        {"price"},
        "1d",
        str(tmp_path),
        "CN",
        enable_multiprocessing=False,
        num_workers=3,
        use_data_server=False,
    )

    assert result is fresh_benchmark
    assert performance_config.enable_multiprocessing is False
    assert performance_config.num_workers == 3
    assert existing_server.clear_count == 1
    assert FakeDataServer.calls == [({"price"}, "1d", str(tmp_path), "CN")]
