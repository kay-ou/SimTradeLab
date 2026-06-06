# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""Regression tests for PTrade-compatible API behavior around date indexes."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.cache_manager import cache_manager
from simtradelab.ptrade.context import Context, PTradeMode
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.ptrade.object import Portfolio


def _make_api(data_context, simple_log, current_dt: str = "2024-01-05") -> PtradeAPI:
    portfolio = Portfolio(initial_capital=1_000_000.0)
    context = Context(
        portfolio=portfolio,
        mode=PTradeMode.BACKTEST,
        capital_base=1_000_000.0,
        initialized=False,
    )
    portfolio._context = context
    context.current_dt = pd.Timestamp(current_dt)
    context.blotter.current_dt = context.current_dt
    context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    api = PtradeAPI(data_context=data_context, context=context, log=simple_log)
    return api


def _assert_api_result_equal(left, right) -> None:
    if isinstance(left, pd.DataFrame):
        assert isinstance(right, pd.DataFrame)
        assert_frame_equal(left, right)
        return

    if isinstance(left, pd.Series):
        assert isinstance(right, pd.Series)
        assert_series_equal(left, right)
        return

    if isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray)
        np.testing.assert_array_equal(left, right)
        return

    if isinstance(left, dict):
        assert isinstance(right, dict)
        assert type(left) is type(right)
        assert list(left.keys()) == list(right.keys())
        for key in left:
            _assert_api_result_equal(left[key], right[key])
        return

    assert left == right


def _run_lazy_and_prebuilt(data_context, simple_log, callback, stocks=None, current_dt: str = "2024-01-05"):
    lazy_api = _make_api(data_context, simple_log, current_dt=current_dt)
    lazy_result = callback(lazy_api)

    cache_manager.clear_namespace("history")

    prebuilt_api = _make_api(data_context, simple_log, current_dt=current_dt)
    prebuilt_api.prebuild_date_index(stocks=stocks)
    prebuilt_result = callback(prebuilt_api)

    _assert_api_result_equal(lazy_result, prebuilt_result)
    return lazy_result, prebuilt_result


def _source_slice(data_context, stock: str, start: str, end: str, columns: list[str]) -> pd.DataFrame:
    return data_context.stock_data_dict[stock].loc[pd.Timestamp(start) : pd.Timestamp(end), columns]


def _assert_market_frame_equal(left: pd.DataFrame, right: pd.DataFrame, **kwargs) -> None:
    left_plain = pd.DataFrame(left.to_numpy(), index=left.index, columns=left.columns)
    right_plain = pd.DataFrame(right.to_numpy(), index=right.index, columns=right.columns)
    assert_frame_equal(left_plain, right_plain, **kwargs)


def test_daily_date_index_normalizes_non_ns_datetime_index(data_context, simple_log):
    stock = "600000.SH"
    stock_df = data_context.stock_data_dict[stock].copy()
    stock_df.index = pd.DatetimeIndex(stock_df.index.to_numpy(dtype="datetime64[us]"))
    stock_df["close"] = 1.0
    stock_df.iloc[1, stock_df.columns.get_loc("close")] = 12.0
    stock_df.iloc[-1, stock_df.columns.get_loc("close")] = 99.0
    data_context.stock_data_dict[stock] = stock_df

    api = _make_api(data_context, simple_log, current_dt="2024-01-02")
    api.prebuild_date_index(stocks=[stock])

    date_dict, sorted_i8 = api.get_stock_date_index(stock)
    query_value = pd.Timestamp("2024-01-02").value

    assert stock_df.index.dtype == np.dtype("datetime64[us]")
    assert sorted_i8[1] == query_value
    assert date_dict[query_value] == 1
    assert api._resolve_daily_index(stock, stock_df, pd.Timestamp("2024-01-02")) == 1

    result = api.get_price(stock, end_date="2024-01-02", count=1, fields="close")
    assert result["close"].iloc[-1] == 12.0


def test_get_price_count_single_stock_contract_unchanged_by_prebuild(data_context, simple_log):
    result, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_price(
            "600000.SH",
            end_date="2024-01-05",
            count=3,
            fields=["open", "close"],
        ),
        stocks=["600000.SH"],
    )

    assert list(result.columns) == ["open", "close"]
    assert list(result.index) == list(pd.date_range("2024-01-03", periods=3, freq="D"))
    expected = _source_slice(data_context, "600000.SH", "2024-01-03", "2024-01-05", ["open", "close"])
    _assert_market_frame_equal(result, expected)


def test_get_price_multi_stock_panel_contract_unchanged_by_prebuild(data_context, simple_log):
    result, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_price(
            ["600000.SH", "000001.SZ"],
            start_date="2024-01-02",
            end_date="2024-01-04",
            fields=["open", "close"],
        ),
        stocks=["600000.SH", "000001.SZ"],
    )

    assert isinstance(result, PtradeAPI.PanelLike)
    assert list(result.keys()) == ["open", "close"]
    assert list(result["open"].columns) == ["600000.SH", "000001.SZ"]
    assert list(result["open"].index) == list(pd.date_range("2024-01-02", periods=3, freq="D"))
    expected_open = pd.DataFrame(
        {
            "600000.SH": _source_slice(data_context, "600000.SH", "2024-01-02", "2024-01-04", ["open"])["open"],
            "000001.SZ": _source_slice(data_context, "000001.SZ", "2024-01-02", "2024-01-04", ["open"])["open"],
        }
    )
    _assert_market_frame_equal(result["open"], expected_open)


def test_get_price_multi_stock_single_field_contract_unchanged_by_prebuild(data_context, simple_log):
    result, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_price(
            ["600000.SH", "000001.SZ"],
            start_date="2024-01-02",
            end_date="2024-01-04",
            fields="close",
        ),
        stocks=["600000.SH", "000001.SZ"],
    )

    expected_close = pd.DataFrame(
        {
            "600000.SH": _source_slice(data_context, "600000.SH", "2024-01-02", "2024-01-04", ["close"])["close"],
            "000001.SZ": _source_slice(data_context, "000001.SZ", "2024-01-02", "2024-01-04", ["close"])["close"],
        }
    )
    assert isinstance(result, pd.DataFrame)
    _assert_market_frame_equal(result, expected_close)


def test_get_history_include_contract_unchanged_by_prebuild(data_context, simple_log):
    include_false, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_history(2, "1d", "close", "600000.SH", include=False),
        stocks=["600000.SH"],
        current_dt="2024-01-05",
    )

    cache_manager.clear_namespace("history")

    include_true, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_history(2, "1d", "close", "600000.SH", include=True),
        stocks=["600000.SH"],
        current_dt="2024-01-05",
    )

    assert list(include_false.index) == list(pd.date_range("2024-01-03", periods=2, freq="D"))
    assert list(include_true.index) == list(pd.date_range("2024-01-04", periods=2, freq="D"))
    _assert_market_frame_equal(
        include_false,
        _source_slice(data_context, "600000.SH", "2024-01-03", "2024-01-04", ["close"]),
        check_freq=False,
    )
    _assert_market_frame_equal(
        include_true,
        _source_slice(data_context, "600000.SH", "2024-01-04", "2024-01-05", ["close"]),
        check_freq=False,
    )


def test_get_history_panel_contract_unchanged_by_prebuild(data_context, simple_log):
    result, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_history(
            count=3,
            frequency="1d",
            field=["open", "close"],
            security_list=["600000.SH", "000001.SZ"],
            include=True,
        ),
        stocks=["600000.SH", "000001.SZ"],
        current_dt="2024-01-05",
    )

    assert isinstance(result, PtradeAPI.PanelLike)
    assert list(result.keys()) == ["open", "close"]
    assert list(result["close"].columns) == ["600000.SH", "000001.SZ"]
    assert list(result["close"].index) == list(pd.date_range("2024-01-03", periods=3, freq="D"))
    expected_open = pd.DataFrame(
        {
            "600000.SH": _source_slice(data_context, "600000.SH", "2024-01-03", "2024-01-05", ["open"])["open"],
            "000001.SZ": _source_slice(data_context, "000001.SZ", "2024-01-03", "2024-01-05", ["open"])["open"],
        }
    )
    _assert_market_frame_equal(result["open"], expected_open, check_freq=False)


def test_get_history_multi_stock_single_field_contract_unchanged_by_prebuild(data_context, simple_log):
    result, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_history(
            count=3,
            frequency="1d",
            field="close",
            security_list=["600000.SH", "000001.SZ"],
            include=True,
        ),
        stocks=["600000.SH", "000001.SZ"],
        current_dt="2024-01-05",
    )

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["600000.SH", "000001.SZ"]
    assert list(result.index) == list(pd.date_range("2024-01-03", periods=3, freq="D"))
    expected_close = pd.DataFrame(
        {
            "600000.SH": _source_slice(data_context, "600000.SH", "2024-01-03", "2024-01-05", ["close"])["close"],
            "000001.SZ": _source_slice(data_context, "000001.SZ", "2024-01-03", "2024-01-05", ["close"])["close"],
        }
    )
    _assert_market_frame_equal(result, expected_close, check_freq=False)


def test_get_history_is_dict_contract_unchanged_by_prebuild(data_context, simple_log):
    result, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.get_history(
            count=3,
            frequency="1d",
            field=["close", "volume"],
            security_list=["600000.SH", "000001.SZ"],
            include=True,
            is_dict=True,
        ),
        stocks=["600000.SH", "000001.SZ"],
        current_dt="2024-01-05",
    )

    assert list(result.keys()) == ["600000.SH", "000001.SZ"]
    assert set(result["600000.SH"]) == {"close", "volume"}
    assert len(result["600000.SH"]["close"]) == 3
    np.testing.assert_array_equal(
        result["600000.SH"]["close"],
        _source_slice(data_context, "600000.SH", "2024-01-03", "2024-01-05", ["close"])["close"].values,
    )


def test_legacy_ptrade_series_integer_access_does_not_warn(data_context, simple_log):
    api = _make_api(data_context, simple_log, current_dt="2024-01-05")
    expected_close = data_context.stock_data_dict["600000.SH"].loc[pd.Timestamp("2024-01-05"), "close"]
    expected_open = data_context.stock_data_dict["600000.SH"].loc[pd.Timestamp("2024-01-05"), "open"]

    history_multi_stock = api.get_history(3, "1d", "close", ["600000.SH"], include=True)
    history_single_stock = api.get_history(3, "1d", "close", "600000.SH", include=True)
    price_single_stock = api.get_price("600000.SH", end_date="2024-01-05", count=3, fields="close")
    price_panel = api.get_price(
        ["600000.SH", "000001.SZ"],
        end_date="2024-01-05",
        count=3,
        fields=["open", "close"],
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        assert history_multi_stock["600000.SH"][-1] == expected_close
        assert history_single_stock["close"][-1] == expected_close
        assert price_single_stock["close"][-1] == expected_close
        assert price_panel["open"]["600000.SH"][-1] == expected_open


def test_check_limit_status_contract_unchanged_by_prebuild(data_context, simple_log):
    up_stock = "600000.SH"
    down_stock = "000001.SZ"
    data_context.stock_data_dict[up_stock].loc[pd.Timestamp("2024-01-01"), "close"] = 10.0
    data_context.stock_data_dict[up_stock].loc[pd.Timestamp("2024-01-02"), ["open", "high", "low"]] = 11.0
    data_context.stock_data_dict[down_stock].loc[pd.Timestamp("2024-01-01"), "close"] = 10.0
    data_context.stock_data_dict[down_stock].loc[pd.Timestamp("2024-01-02"), ["open", "high", "low"]] = 9.0

    result, _ = _run_lazy_and_prebuilt(
        data_context,
        simple_log,
        lambda api: api.check_limit([up_stock, down_stock], query_date="2024-01-02"),
        stocks=[up_stock, down_stock],
        current_dt="2024-01-02",
    )

    assert result == {up_stock: 1, down_stock: -1}


def test_order_market_price_contract_unchanged_by_prebuild(data_context, simple_log):
    stock = "600000.SH"
    data_context.stock_data_dict[stock].loc[pd.Timestamp("2024-01-02"), "close"] = 20.0
    data_context.stock_data_dict[stock].loc[pd.Timestamp("2024-01-02"), "volume"] = 1_000_000.0

    lazy_api = _make_api(data_context, simple_log, current_dt="2024-01-02")
    lazy_order_id = lazy_api.order(stock, 100)

    prebuilt_api = _make_api(data_context, simple_log, current_dt="2024-01-02")
    prebuilt_api.prebuild_date_index(stocks=[stock])
    prebuilt_order_id = prebuilt_api.order(stock, 100)

    assert lazy_order_id is not None
    assert prebuilt_order_id is not None
    assert lazy_api.context.blotter.filled_orders[-1].amount == prebuilt_api.context.blotter.filled_orders[-1].amount
    assert lazy_api.context.blotter.filled_orders[-1].limit == prebuilt_api.context.blotter.filled_orders[-1].limit
    assert lazy_api.context.portfolio.positions[stock].amount == prebuilt_api.context.portfolio.positions[stock].amount
    assert lazy_api.context.portfolio.cash == prebuilt_api.context.portfolio.cash


def test_partial_prebuild_does_not_block_later_full_prebuild(data_context, simple_log):
    api = _make_api(data_context, simple_log)

    api.prebuild_date_index(stocks=["600000.SH"])
    assert set(api._stock_date_index) == {"600000.SH"}

    api.prebuild_date_index()

    assert set(data_context.stock_data_dict).issubset(api._stock_date_index)
    assert api._prebuilt_index is True


def test_trade_day_helpers_follow_documented_bounds(data_context, simple_log):
    api = _make_api(data_context, simple_log, current_dt="2024-01-05")

    assert api.get_trade_days(count=3).tolist() == ["2024-01-03", "2024-01-04", "2024-01-05"]
    assert api.get_trade_days(start_date="2024-01-02", end_date="2024-01-04").tolist() == [
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
    ]
    assert api.get_all_trades_days("2024-01-03").tolist() == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert bool(api.get_trade_days(count=1))

    with pytest.raises(ValueError):
        api.get_trade_days(start_date="2024-01-02", count=2)

    assert api.get_trading_day(0) == pd.Timestamp("2024-01-05").date()
    assert api.get_trading_day(-1) == pd.Timestamp("2024-01-04").date()
    assert api.get_trading_day(1) == pd.Timestamp("2024-01-06").date()

    api.context.current_dt = pd.Timestamp("2024-01-05 14:30")
    assert api.get_trading_day(0) == pd.Timestamp("2024-01-05").date()
    assert api.get_trading_day_by_date("2024-01-05", -2) == pd.Timestamp("2024-01-03").date()
