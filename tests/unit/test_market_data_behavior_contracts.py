import copy

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from simtradelab.backtest.backtest_stats import StatsCollector
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.strategy_engine import StrategyExecutionEngine
from simtradelab.ptrade.config_manager import config


@pytest.mark.parametrize("count", [0, -1])
def test_get_history_rejects_non_positive_count(ptrade_api, count):
    with pytest.raises(ValueError, match="count must be greater than 0"):
        ptrade_api.get_history(
            count,
            frequency="1d",
            field="close",
            security_list="600000.SH",
        )


@pytest.mark.parametrize("api_name", ["get_history", "get_price"])
def test_minute_query_does_not_fallback_to_future_close_bar(ptrade_api, api_name):
    stock = "600000.SH"
    ptrade_api.context.frequency = "1m"
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-02 09:00:00")
    ptrade_api.data_context.stock_data_dict_1m = {
        stock: pd.DataFrame(
            {"close": [10.0]}, index=pd.to_datetime(["2024-01-02 09:31:00"])
        )
    }

    if api_name == "get_history":
        result = ptrade_api.get_history(
            1, frequency="1m", field="close", security_list=stock, include=True
        )
    else:
        result = ptrade_api.get_price(
            stock,
            end_date="2024-01-02 09:00:00",
            frequency="1m",
            fields="close",
            count=1,
        )

    assert result.empty


def test_get_history_sparse_minute_fill_returns_exact_requested_count(ptrade_api):
    stock = "600000.SH"
    ptrade_api.context.frequency = "1m"
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-02 09:35:00")
    ptrade_api.data_context.stock_data_dict_1m = {
        stock: pd.DataFrame(
            {"close": [10.0, 10.5]},
            index=pd.to_datetime(["2024-01-02 09:31:00", "2024-01-02 09:35:00"]),
        )
    }

    result = ptrade_api.get_history(
        2,
        frequency="1m",
        field="close",
        security_list=stock,
        include=True,
        fill="pre",
    )

    assert list(result.index) == list(
        pd.to_datetime(["2024-01-02 09:34:00", "2024-01-02 09:35:00"])
    )
    assert result["close"].tolist() == [10.0, 10.5]


def test_get_history_sparse_minute_include_false_uses_preceding_logical_bars(ptrade_api):
    stock = "600000.SH"
    ptrade_api.context.frequency = "1m"
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-02 09:35:00")
    ptrade_api.data_context.trade_days = pd.DatetimeIndex([pd.Timestamp("2024-01-02")])
    ptrade_api.data_context.stock_data_dict_1m = {
        stock: pd.DataFrame(
            {"close": [10.0, 10.5]},
            index=pd.to_datetime(["2024-01-02 09:31:00", "2024-01-02 09:35:00"]),
        )
    }

    result = ptrade_api.get_history(
        2,
        frequency="1m",
        field="close",
        security_list=stock,
        include=False,
        fill="pre",
    )

    assert list(result.index) == list(
        pd.to_datetime(["2024-01-02 09:33:00", "2024-01-02 09:34:00"])
    )
    assert result["close"].tolist() == [10.0, 10.0]


def test_get_history_multi_day_5m_returns_full_requested_count(ptrade_api):
    stock = "600000.SH"
    trade_days = pd.bdate_range("2024-01-02", periods=12)
    minute_indexes = []
    for day in trade_days:
        minute_indexes.extend(
            [
                pd.date_range(day + pd.Timedelta(hours=9, minutes=31), day + pd.Timedelta(hours=11, minutes=30), freq="1min"),
                pd.date_range(day + pd.Timedelta(hours=13, minutes=1), day + pd.Timedelta(hours=15), freq="1min"),
            ]
        )
    minute_index = minute_indexes[0]
    for part in minute_indexes[1:]:
        minute_index = minute_index.append(part)
    ptrade_api.data_context.trade_days = trade_days
    ptrade_api.data_context.stock_data_dict_1m = {
        stock: pd.DataFrame(
            {"close": range(len(minute_index))}, index=minute_index
        )
    }
    ptrade_api.context.frequency = "1m"
    ptrade_api.context.current_dt = trade_days[-1] + pd.Timedelta(hours=15)

    result = ptrade_api.get_history(
        500,
        frequency="5m",
        field="close",
        security_list=stock,
        include=True,
        fill="pre",
    )

    assert len(result) == 500
    assert result.index[-1] == trade_days[-1] + pd.Timedelta(hours=15)


@pytest.mark.parametrize(
    "frequency, minutes, bars_per_day",
    [("15m", 15, 16), ("30m", 30, 8), ("60m", 60, 4), ("120m", 120, 2)],
)
def test_get_history_aggregated_minutes_respect_session_boundaries(
    ptrade_api, frequency, minutes, bars_per_day
):
    stock = "600000.SH"
    trade_days = pd.bdate_range("2024-01-02", periods=2)
    parts = []
    for day in trade_days:
        parts.extend(
            [
                pd.date_range(day + pd.Timedelta(hours=9, minutes=31), day + pd.Timedelta(hours=11, minutes=30), freq="1min"),
                pd.date_range(day + pd.Timedelta(hours=13, minutes=1), day + pd.Timedelta(hours=15), freq="1min"),
            ]
        )
    minute_index = parts[0]
    for part in parts[1:]:
        minute_index = minute_index.append(part)
    source = pd.DataFrame(
        {"close": pd.Series(range(len(minute_index)), index=minute_index, dtype=float)}
    )
    ptrade_api.data_context.trade_days = trade_days
    ptrade_api.data_context.stock_data_dict_1m = {stock: source}
    ptrade_api.context.frequency = "1m"
    ptrade_api.context.current_dt = trade_days[-1] + pd.Timedelta(hours=15)
    count = bars_per_day + 1

    result = ptrade_api.get_history(
        count,
        frequency=frequency,
        field="close",
        security_list=stock,
        include=True,
        fill="nan",
    )

    today_labels = list(
        pd.date_range(
            trade_days[-1] + pd.Timedelta(hours=9, minutes=31 + minutes - 1),
            trade_days[-1] + pd.Timedelta(hours=11, minutes=30),
            freq=f"{minutes}min",
        )
    ) + list(
        pd.date_range(
            trade_days[-1] + pd.Timedelta(hours=13, minutes=1 + minutes - 1),
            trade_days[-1] + pd.Timedelta(hours=15),
            freq=f"{minutes}min",
        )
    )
    expected_index = [trade_days[0] + pd.Timedelta(hours=15)] + today_labels
    assert list(result.index) == expected_index
    assert len(result) == count
    assert not result["close"].isna().any()
    assert result["close"].tolist() == source.loc[expected_index, "close"].tolist()


@pytest.mark.parametrize(
    "frequency, minutes, bars_per_day",
    [("15m", 15, 16), ("30m", 30, 8), ("60m", 60, 4), ("120m", 120, 2)],
)
def test_sparse_aggregated_minutes_use_fixed_session_anchor_buckets(
    ptrade_api, frequency, minutes, bars_per_day
):
    stock = "600000.SH"
    day = pd.Timestamp("2024-01-02")
    morning_anchor = day + pd.Timedelta(hours=9, minutes=31)
    afternoon_anchor = day + pd.Timedelta(hours=13, minutes=1)
    if minutes < 120:
        source_index = pd.DatetimeIndex(
            [
                morning_anchor + pd.Timedelta(minutes=minutes - 1),
                morning_anchor + pd.Timedelta(minutes=minutes),
                afternoon_anchor + pd.Timedelta(minutes=minutes - 1),
                afternoon_anchor + pd.Timedelta(minutes=minutes),
            ]
        )
        expected = {
            morning_anchor + pd.Timedelta(minutes=minutes - 1): 1.0,
            morning_anchor + pd.Timedelta(minutes=2 * minutes - 1): 2.0,
            afternoon_anchor + pd.Timedelta(minutes=minutes - 1): 3.0,
            afternoon_anchor + pd.Timedelta(minutes=2 * minutes - 1): 4.0,
        }
    else:
        source_index = pd.DatetimeIndex(
            [morning_anchor + pd.Timedelta(minutes=15), afternoon_anchor + pd.Timedelta(minutes=45)]
        )
        expected = {
            day + pd.Timedelta(hours=11, minutes=30): 1.0,
            day + pd.Timedelta(hours=15): 2.0,
        }
    ptrade_api.data_context.trade_days = pd.DatetimeIndex([day])
    ptrade_api.data_context.stock_data_dict_1m = {
        stock: pd.DataFrame(
            {"close": [float(i + 1) for i in range(len(source_index))]},
            index=source_index,
        )
    }
    ptrade_api.context.frequency = "1m"
    ptrade_api.context.current_dt = day + pd.Timedelta(hours=15)

    result = ptrade_api.get_history(
        bars_per_day,
        frequency=frequency,
        field="close",
        security_list=stock,
        include=True,
        fill="nan",
    )

    for label, value in expected.items():
        assert result.loc[label, "close"] == value

    if minutes < 120:
        ptrade_api.context.current_dt = morning_anchor + pd.Timedelta(minutes=minutes)
        partial = ptrade_api.get_history(
            1,
            frequency=frequency,
            field="close",
            security_list=stock,
            include=True,
            fill="nan",
        )
        assert list(partial.index) == [morning_anchor + pd.Timedelta(minutes=minutes - 1)]
        assert partial.iloc[0, 0] == 1.0
    else:
        ptrade_api.context.current_dt = morning_anchor + pd.Timedelta(minutes=15)
        partial = ptrade_api.get_history(
            1,
            frequency=frequency,
            field="close",
            security_list=stock,
            include=True,
            fill="nan",
        )
        assert partial.empty


@pytest.mark.parametrize("first_fill", ["nan", "pre"])
def test_get_history_minute_fill_mode_is_part_of_cache_contract(
    ptrade_api, first_fill
):
    stock = "600000.SH"
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-02 09:33:00")
    ptrade_api.data_context.stock_data_dict_1m = {
        stock: pd.DataFrame(
            {
                "close": [10.0, 10.2],
                "volume": [1000.0, 1200.0],
            },
            index=pd.to_datetime(["2024-01-02 09:31:00", "2024-01-02 09:33:00"]),
        )
    }

    first = ptrade_api.get_history(
        3,
        frequency="1m",
        field=["close", "volume"],
        security_list=stock,
        include=True,
        fill=first_fill,
    )
    second_fill = "pre" if first_fill == "nan" else "nan"
    second = ptrade_api.get_history(
        3,
        frequency="1m",
        field=["close", "volume"],
        security_list=stock,
        include=True,
        fill=second_fill,
    )

    expected_index = list(
        pd.to_datetime(
            [
                "2024-01-02 09:31:00",
                "2024-01-02 09:32:00",
                "2024-01-02 09:33:00",
            ]
        )
    )
    assert list(first.index) == expected_index
    assert list(second.index) == expected_index

    results = {first_fill: first, second_fill: second}
    assert pd.isna(results["nan"].loc[pd.Timestamp("2024-01-02 09:32:00"), "close"])
    assert pd.isna(results["nan"].loc[pd.Timestamp("2024-01-02 09:32:00"), "volume"])
    assert results["pre"].loc[pd.Timestamp("2024-01-02 09:32:00"), "close"] == 10.0
    assert results["pre"].loc[pd.Timestamp("2024-01-02 09:32:00"), "volume"] == 1000.0


@pytest.mark.parametrize("fq, cache_name", [("pre", "adj_pre_cache"), ("post", "adj_post_cache")])
def test_get_price_and_get_history_share_adjusted_price_contract(
    ptrade_api, fq, cache_name
):
    stock = "600000.SH"
    source = pd.DataFrame(
        {
            "open": [10.001, 11.111, 12.221],
            "high": [10.501, 11.611, 12.721],
            "low": [9.501, 10.611, 11.721],
            "close": [10.201, 11.311, 12.421],
            "volume": [100.0, 200.0, 300.0],
        },
        index=pd.date_range("2024-01-01", periods=3),
    )
    ptrade_api.data_context.stock_data_dict[stock] = source
    ptrade_api.context.current_dt = source.index[-1]
    factors = pd.DataFrame(
        {"adj_a": [0.5, 0.5, 0.5], "adj_b": [1.006, 1.006, 1.006]},
        index=source.index,
    )
    setattr(ptrade_api.data_context, cache_name, {stock: factors})
    if cache_name == "adj_pre_cache":
        ptrade_api.data_context.adj_post_cache = {}
    else:
        ptrade_api.data_context.adj_pre_cache = {}

    history = ptrade_api.get_history(
        3,
        frequency="1d",
        field=["open", "high", "low", "close"],
        security_list=stock,
        fq=fq,
        include=True,
    )
    price = ptrade_api.get_price(
        stock,
        end_date=source.index[-1],
        frequency="1d",
        fields=["open", "high", "low", "close"],
        fq=fq,
        count=3,
    )

    raw = source[["open", "high", "low", "close"]]
    expected = raw * 0.5 + 1.006
    if fq == "pre":
        expected = expected.round(2)
    assert_frame_equal(
        pd.DataFrame(history),
        expected,
        check_freq=False,
    )
    assert_frame_equal(
        pd.DataFrame(price),
        expected,
        check_freq=False,
    )


def test_get_history_cache_preserves_requested_stock_order(ptrade_api):
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-03")
    first_order = ["600000.SH", "000001.SZ"]
    second_order = list(reversed(first_order))

    first = ptrade_api.get_history(2, field="close", security_list=first_order)
    second = ptrade_api.get_history(2, field="close", security_list=second_order)

    assert list(first.columns) == first_order
    assert list(second.columns) == second_order


def test_get_history_cache_isolated_by_data_context(ptrade_api, simple_log):
    stock = "600000.SH"
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-03")
    first = ptrade_api.get_history(1, field="close", security_list=stock, include=True)

    other_data_context = copy.copy(ptrade_api.data_context)
    other_data_context.stock_data_dict = dict(ptrade_api.data_context.stock_data_dict)
    changed = other_data_context.stock_data_dict[stock].copy()
    changed.loc[pd.Timestamp("2024-01-03"), "close"] = 999.0
    other_data_context.stock_data_dict[stock] = changed
    other_api = PtradeAPI(other_data_context, ptrade_api.context, simple_log)
    second = other_api.get_history(1, field="close", security_list=stock, include=True)

    assert first.iloc[0, 0] != second.iloc[0, 0]
    assert second.iloc[0, 0] == 999.0


def test_get_history_cache_isolated_by_broker_profile(ptrade_api):
    stocks = ["600000.SH", "000001.SZ"]
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-03")
    ptrade_api.broker_profile = "auto"
    auto_result = ptrade_api.get_history(
        2, field=["open", "close"], security_list=stocks
    )

    ptrade_api.broker_profile = "shanxi"
    shanxi_result = ptrade_api.get_history(
        2, field=["open", "close"], security_list=stocks
    )

    assert not isinstance(auto_result.columns, pd.MultiIndex)
    assert isinstance(shanxi_result.columns, pd.MultiIndex)


def test_engine_applies_dividend_to_cash_and_position_lot(ptrade_api, simple_log):
    stock = "600000.SH"
    event_date = pd.Timestamp("2024-01-03")
    portfolio = ptrade_api.context.portfolio
    portfolio.add_position(stock, 100, 10.0, event_date - pd.Timedelta(days=1))
    ptrade_api.data_context.dividend_cache = {stock: {"20240103": 1.0}}
    cash_before = portfolio.cash
    collector = StatsCollector()
    engine = StrategyExecutionEngine(
        ptrade_api.context, ptrade_api, stats_collector=collector, log=simple_log
    )
    observed_cash = []
    engine.register_initialize(lambda _context: None)
    engine.register_handle_data(
        lambda context, _data: observed_cash.append((context.current_dt, context.portfolio.cash))
    )

    assert engine.run_backtest(pd.DatetimeIndex([event_date])) is True

    assert portfolio.cash == cash_before + 80.0
    assert observed_cash == [(event_date, cash_before + 80.0)]
    assert portfolio._position_lots[stock][0]["dividends"] == [100.0]
    assert portfolio._position_lots[stock][0]["dividends_total"] == 100.0


def test_get_history_daily_suspension_keeps_calendar_and_zero_volume(ptrade_api):
    stock = "600000.SH"
    dates = pd.date_range("2024-01-02", periods=3)
    ptrade_api.data_context.stock_data_dict[stock] = pd.DataFrame(
        {
            "close": [10.0, 10.0, 10.2],
            "volume": [1000.0, 0.0, 1200.0],
        },
        index=dates,
    )
    ptrade_api.context.current_dt = dates[-1]

    result = ptrade_api.get_history(
        3,
        frequency="1d",
        field=["close", "volume"],
        security_list=stock,
        include=True,
    )

    assert list(result.index) == list(dates)
    assert result.loc[dates[1], "close"] == 10.0
    assert result.loc[dates[1], "volume"] == 0.0


def test_get_history_daily_suspension_fills_date_omitted_from_stock_source(ptrade_api):
    stock = "600000.SH"
    calendar = pd.date_range("2024-01-02", periods=3)
    ptrade_api.data_context.trade_days = calendar
    ptrade_api.data_context.stock_data_dict[stock] = pd.DataFrame(
        {"close": [10.0, 10.2], "volume": [1000.0, 1200.0]},
        index=calendar[[0, 2]],
    )
    ptrade_api.context.current_dt = calendar[-1]

    result = ptrade_api.get_history(
        3,
        frequency="1d",
        field=["close", "volume"],
        security_list=stock,
        include=True,
    )

    assert list(result.index) == list(calendar)
    assert result.loc[calendar[1], "close"] == 10.0
    assert result.loc[calendar[1], "volume"] == 0.0


def test_get_history_daily_suspension_uses_price_before_requested_window(ptrade_api):
    stock = "600000.SH"
    calendar = pd.date_range("2024-01-02", periods=4)
    ptrade_api.data_context.trade_days = calendar
    ptrade_api.data_context.stock_data_dict[stock] = pd.DataFrame(
        {"close": [9.8, 10.2], "volume": [900.0, 1200.0]},
        index=calendar[[0, 3]],
    )
    ptrade_api.context.current_dt = calendar[-1]

    result = ptrade_api.get_history(
        3,
        frequency="1d",
        field=["close", "volume"],
        security_list=stock,
        include=True,
    )

    assert list(result.index) == list(calendar[-3:])
    assert result["close"].tolist() == [9.8, 9.8, 10.2]
    assert result["volume"].tolist() == [0.0, 0.0, 1200.0]


def test_get_price_uses_ptrade_compatible_pre_adjustment_for_high_low(ptrade_api):
    stock = "600000.SH"
    dates = pd.date_range("2024-01-01", periods=20)
    source = pd.DataFrame(
        {
            "open": [5.0] * 20,
            "high": [5.79] + [5.0] * 19,
            "low": [4.5] * 19 + [4.07],
            "close": [5.0] * 20,
        },
        index=dates,
    )
    ptrade_api.data_context.stock_data_dict[stock] = source
    ptrade_api.data_context.adj_pre_cache = {
        stock: pd.DataFrame(
            {"adj_a": [1.0] * 20, "adj_b": [-1.506] * 20}, index=dates
        )
    }
    ptrade_api.context.current_dt = dates[-1]

    history = ptrade_api.get_history(
        20,
        field=["high", "low"],
        security_list=stock,
        fq="pre",
        include=True,
    )
    price = ptrade_api.get_price(
        stock,
        end_date=dates[-1],
        fields=["high", "low"],
        fq="pre",
        count=20,
    )

    assert history.iloc[0]["high"] == 5.79 - 1.506
    assert history.iloc[-1]["low"] == 4.07 - 1.506
    assert_frame_equal(price, history, check_freq=False)


def test_get_history_adjustment_factors_align_by_date_with_missing_factor_day(ptrade_api):
    stock = "600000.SH"
    dates = pd.date_range("2024-01-01", periods=3)
    ptrade_api.data_context.trade_days = dates
    ptrade_api.data_context.stock_data_dict[stock] = pd.DataFrame(
        {"close": [10.0, 11.0, 12.0]}, index=dates
    )
    ptrade_api.data_context.adj_pre_cache = {
        stock: pd.DataFrame(
            {"adj_a": [1.0, 2.0], "adj_b": [0.0, 1.0]},
            index=dates[[0, 2]],
        )
    }
    ptrade_api.context.current_dt = dates[-1]

    result = ptrade_api.get_history(
        3,
        field="close",
        security_list=stock,
        fq="pre",
        include=True,
    )

    assert result["close"].tolist() == [10.0, 11.0, 25.0]


def test_get_history_data_version_invalidates_instance_cache(ptrade_api):
    stock = "600000.SH"
    date = pd.Timestamp("2024-01-03")
    ptrade_api.context.current_dt = date
    ptrade_api.data_context.data_version = 1
    first = ptrade_api.get_history(1, field="close", security_list=stock, include=True)

    ptrade_api.data_context.stock_data_dict[stock].loc[date, "close"] = 777.0
    ptrade_api.data_context.data_version = 2
    second = ptrade_api.get_history(1, field="close", security_list=stock, include=True)

    assert first.iloc[0, 0] != second.iloc[0, 0]
    assert second.iloc[0, 0] == 777.0


def test_get_history_cache_hits_same_day_and_clears_on_date_change(
    ptrade_api, monkeypatch
):
    stock = "600000.SH"
    calls = 0
    original = ptrade_api._get_stock_df_by_frequency

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(ptrade_api, "_get_stock_df_by_frequency", counted)
    ptrade_api.context.current_dt = pd.Timestamp("2024-01-03")
    first = ptrade_api.get_history(2, field="close", security_list=stock, include=True)
    repeated = ptrade_api.get_history(2, field="close", security_list=stock, include=True)

    assert repeated is first
    assert calls == 1
    assert len(ptrade_api._history_cache) == 1
    assert ptrade_api._history_cache.maxsize == config.cache.history_cache_size

    ptrade_api.context.current_dt = pd.Timestamp("2024-01-04")
    ptrade_api.get_history(2, field="close", security_list=stock, include=True)

    assert calls == 2
    assert len(ptrade_api._history_cache) == 1
    assert ptrade_api._history_cache_date == pd.Timestamp("2024-01-04")


def test_get_history_complete_daily_window_avoids_reindex_allocations(
    ptrade_api, monkeypatch
):
    stock = "600000.SH"
    dates = pd.date_range("2024-01-01", periods=5)
    ptrade_api.data_context.trade_days = dates
    ptrade_api.data_context.stock_data_dict[stock] = pd.DataFrame(
        {"close": [10.0, 11.0, 12.0, 13.0, 14.0]}, index=dates
    )
    ptrade_api.data_context.adj_pre_cache = {
        stock: pd.DataFrame(
            {"adj_a": [1.0] * 5, "adj_b": [0.0] * 5}, index=dates
        )
    }
    ptrade_api.context.current_dt = dates[-1]
    reindex_calls = 0
    original_reindex = pd.DataFrame.reindex

    def counted_reindex(frame, *args, **kwargs):
        nonlocal reindex_calls
        reindex_calls += 1
        return original_reindex(frame, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "reindex", counted_reindex)

    result = ptrade_api.get_history(
        5,
        field="close",
        security_list=stock,
        fq="pre",
        include=True,
    )

    assert result["close"].tolist() == [10.0, 11.0, 12.0, 13.0, 14.0]
    assert reindex_calls == 0


def test_get_history_factor_alignment_check_is_cached_across_dates(ptrade_api):
    stock = "600000.SH"
    dates = pd.date_range("2024-01-01", periods=6)
    ptrade_api.data_context.trade_days = dates
    ptrade_api.data_context.stock_data_dict[stock] = pd.DataFrame(
        {
            "close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            "price": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        },
        index=dates,
    )
    ptrade_api.data_context.adj_pre_cache = {
        stock: pd.DataFrame(
            {"adj_a": [1.0] * 6, "adj_b": [0.0] * 6}, index=dates
        )
    }
    ptrade_api.context.current_dt = dates[-2]
    ptrade_api.get_history(3, field="close", security_list=stock, fq="pre", include=True)
    assert len(ptrade_api._adj_alignment_cache) == 1

    ptrade_api.context.current_dt = dates[-1]
    result = ptrade_api.get_history(
        3, field="close", security_list=stock, fq="pre", include=True
    )

    assert result["close"].tolist() == [13.0, 14.0, 15.0]
    assert len(ptrade_api._adj_alignment_cache) == 1
