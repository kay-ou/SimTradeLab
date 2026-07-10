from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from simtradelab.backtest.backtest_stats import StatsCollector
from simtradelab.backtest.backtest_stats import BacktestStats
from simtradelab.backtest.optimizer_framework import (
    ParameterSpace,
    ScoringStrategy,
    StrategyOptimizer,
)
from simtradelab.backtest.stats import (
    _plot_nav_curve,
    calculate_benchmark_metrics,
    generate_backtest_report,
)


class _SingleParameterSpace(ParameterSpace):
    period = [5]


class _DefaultScoring(ScoringStrategy):
    pass


class _AlternateScoring(ScoringStrategy):
    @staticmethod
    def calculate_score(metrics):
        return metrics.get("total_return", 0.0)


def _make_optimizer(strategy_path, **overrides):
    kwargs = {
        "strategy_path": str(strategy_path),
        "parameter_space": _SingleParameterSpace(),
        "scoring_strategy": _DefaultScoring(),
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "use_walk_forward": False,
    }
    kwargs.update(overrides)
    return StrategyOptimizer(**kwargs)


def test_stats_collector_reports_single_day_post_trading_return():
    portfolio = SimpleNamespace(
        portfolio_value=100_000.0,
        positions_value=0.0,
        positions={},
    )
    context = SimpleNamespace(portfolio=portfolio)
    collector = StatsCollector()
    trade_date = pd.Timestamp("2024-01-02")

    collector.collect_pre_trading(context, trade_date)
    portfolio.portfolio_value = 99_000.0
    collector.collect_post_trading(context, 100_000.0)

    benchmark = pd.DataFrame({"close": [100.0]}, index=[trade_date])
    report = generate_backtest_report(
        collector.stats,
        trade_date,
        trade_date,
        benchmark,
    )

    assert collector.stats.portfolio_values == [99_000.0]
    assert report["initial_value"] == 100_000.0
    assert report["final_value"] == 99_000.0
    assert report["total_return"] == -0.01
    assert report["max_drawdown"] == -0.01


def test_stats_collector_preserves_seeded_holdings_in_initial_value():
    portfolio = SimpleNamespace(
        portfolio_value=110_000.0,
        positions_value=10_000.0,
        positions={
            "000001.SZ": SimpleNamespace(
                stock="000001.SZ",
                amount=1_000,
                market_value=10_000.0,
                cost_basis=10.0,
            )
        },
    )
    context = SimpleNamespace(portfolio=portfolio)
    collector = StatsCollector()
    trade_date = pd.Timestamp("2024-01-02")

    collector.collect_pre_trading(context, trade_date)
    collector.collect_post_trading(context, 100_000.0)

    benchmark = pd.DataFrame({"close": [100.0]}, index=[trade_date])
    report = generate_backtest_report(
        collector.stats,
        trade_date,
        trade_date,
        benchmark,
    )

    assert report["initial_value"] == 110_000.0
    assert report["total_return"] == 0.0


def test_beta_uses_matching_sample_normalization():
    returns = np.array([0.01, -0.02, 0.03])

    metrics = calculate_benchmark_metrics(returns, returns, 0.2, 0.2)

    assert metrics["beta"] == pytest.approx(1.0)
    assert metrics["alpha"] == pytest.approx(0.0)


def test_report_aligns_first_strategy_day_with_previous_benchmark_close():
    trade_dates = pd.date_range("2024-01-02", periods=3, freq="D")
    portfolio_values = [101_000.0, 103_020.0, 106_110.6]
    stats = BacktestStats(
        portfolio_values=portfolio_values,
        daily_pnl=[1_000.0, 2_020.0, 3_090.6],
        trade_dates=list(trade_dates),
    )
    benchmark = pd.DataFrame(
        {"close": [100.0, 101.0, 103.02, 106.1106]},
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
    )

    report = generate_backtest_report(
        stats,
        trade_dates[0],
        trade_dates[-1],
        benchmark,
    )

    assert report["benchmark_return"] == pytest.approx(0.061106)
    assert report["beta"] == pytest.approx(1.0)
    assert report["alpha"] == pytest.approx(0.0)


def test_nav_curve_uses_initial_capital_as_baseline():
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots()
    dates = np.array([pd.Timestamp("2024-01-02")])
    values = np.array([99_000.0])
    zeros = np.zeros(1)

    _plot_nav_curve(
        axis,
        dates,
        values,
        zeros,
        zeros,
        {},
        dates[0],
        dates[0],
        initial_value=100_000.0,
    )

    assert axis.lines[0].get_ydata()[0] == pytest.approx(0.99)
    plt.close(figure)


def test_walk_forward_windows_use_non_overlapping_closed_intervals(tmp_path):
    strategy_path = tmp_path / "backtest.py"
    strategy_path.write_text("VALUE = 1\n", encoding="utf-8")

    optimizer = StrategyOptimizer(
        strategy_path=str(strategy_path),
        parameter_space=_SingleParameterSpace(),
        scoring_strategy=_DefaultScoring(),
        start_date="2024-01-01",
        end_date="2024-06-30",
        use_walk_forward=True,
        train_months=2,
        test_months=1,
        step_months=1,
    )

    first = optimizer._cached_time_windows[0]
    train_end = datetime.strptime(first[1], "%Y-%m-%d")
    test_start = datetime.strptime(first[2], "%Y-%m-%d")

    assert first == ("2024-01-01", "2024-02-29", "2024-03-01", "2024-03-31")
    assert test_start > train_end


def test_optimizer_cache_key_includes_strategy_and_backtest_configuration(tmp_path):
    strategy_path = tmp_path / "backtest.py"
    strategy_path.write_text("VALUE = 1\n", encoding="utf-8")
    params = {"period": 5}

    optimizer = _make_optimizer(strategy_path, initial_capital=100_000.0)
    optimizer._run_backtest_impl = lambda *args: (1.0, {"marker": "first"})
    assert optimizer.run_backtest_with_params(params)[1]["marker"] == "first"

    strategy_path.write_text("VALUE = 2\n", encoding="utf-8")
    changed_strategy = _make_optimizer(strategy_path, initial_capital=100_000.0)
    changed_strategy._run_backtest_impl = lambda *args: (2.0, {"marker": "strategy"})
    assert changed_strategy.run_backtest_with_params(params)[1]["marker"] == "strategy"

    changed_capital = _make_optimizer(strategy_path, initial_capital=200_000.0)
    changed_capital._run_backtest_impl = lambda *args: (3.0, {"marker": "capital"})
    assert changed_capital.run_backtest_with_params(params)[1]["marker"] == "capital"

    changed_period = _make_optimizer(
        strategy_path,
        initial_capital=200_000.0,
        start_date="2024-02-01",
    )
    changed_period._run_backtest_impl = lambda *args: (3.5, {"marker": "period"})
    assert changed_period.run_backtest_with_params(params)[1]["marker"] == "period"

    changed_scoring = _make_optimizer(
        strategy_path,
        initial_capital=200_000.0,
        start_date="2024-02-01",
        scoring_strategy=_AlternateScoring(),
    )
    changed_scoring._run_backtest_impl = lambda *args: (4.0, {"marker": "scoring"})
    assert changed_scoring.run_backtest_with_params(params)[1]["marker"] == "scoring"
