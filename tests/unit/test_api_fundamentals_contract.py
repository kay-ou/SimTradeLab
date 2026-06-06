# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""Documented behavior tests for get_fundamentals."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from simtradelab.ptrade.lifecycle_controller import LifecyclePhase


def _activate(api, current_dt: str = "2024-05-01") -> None:
    api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
    api.context.current_dt = pd.Timestamp(current_dt)


def test_get_fundamentals_filters_by_publish_date_not_report_period(ptrade_api, data_context):
    _activate(ptrade_api, "2024-05-01")
    data_context.fundamentals_dict["600000.SH"] = pd.DataFrame(
        {
            "publ_date": [pd.Timestamp("2024-04-20"), pd.Timestamp("2024-05-20")],
            "end_date": [pd.Timestamp("2024-03-31"), pd.Timestamp("2024-06-30")],
            "roe": [0.11, 0.22],
            "secu_abbr": ["浦发银行", "浦发银行"],
        }
    )

    before_announcement = ptrade_api.get_fundamentals(
        "600000.SH",
        "profit_ability",
        fields=["roe", "end_date"],
        date="2024-05-01",
    )
    after_announcement = ptrade_api.get_fundamentals(
        "600000.SH",
        "profit_ability",
        fields=["roe", "end_date"],
        date="2024-05-21",
    )

    assert before_announcement.loc["600000.SH", "roe"] == 0.11
    assert before_announcement.loc["600000.SH", "end_date"] == pd.Timestamp("2024-03-31")
    assert after_announcement.loc["600000.SH", "roe"] == 0.22
    assert after_announcement.loc["600000.SH", "end_date"] == pd.Timestamp("2024-06-30")


def test_get_fundamentals_valuation_total_value_uses_query_date_close(ptrade_api, data_context):
    _activate(ptrade_api, "2024-01-03")
    stock_df = data_context.stock_data_dict["600000.SH"].copy()
    stock_df.index = pd.DatetimeIndex(stock_df.index.to_numpy(dtype="datetime64[us]"))
    stock_df.loc[pd.Timestamp("2024-01-02"), "close"] = 12.0
    stock_df.loc[pd.Timestamp("2024-01-02"), "volume"] = 1_000_000.0
    data_context.stock_data_dict["600000.SH"] = stock_df
    data_context.valuation_dict["600000.SH"] = pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-03")],
            "total_shares": [1000.0, 2000.0],
            "a_floats": [400.0, 800.0],
        }
    )

    result = ptrade_api.get_fundamentals(
        "600000.SH",
        "valuation",
        fields=["trading_day", "total_value", "float_value"],
        date="2024-01-02",
    )

    assert result.loc["600000.SH", "trading_day"] == pd.Timestamp("2024-01-01")
    assert result.loc["600000.SH", "total_value"] == 12_000.0
    assert result.loc["600000.SH", "float_value"] == 4_800.0


def test_get_fundamentals_valuation_datetime_index_uses_nanosecond_search(ptrade_api, data_context):
    _activate(ptrade_api, "2024-01-02")
    data_context.valuation_dict["600000.SH"] = pd.DataFrame(
        {
            "total_shares": [1000.0, 2000.0],
        },
        index=pd.DatetimeIndex(np.array(["2024-01-01", "2024-01-03"], dtype="datetime64[us]")),
    )

    result = ptrade_api.get_fundamentals(
        "600000.SH",
        "valuation",
        fields=["trading_day", "total_shares"],
        date="2024-01-02",
    )

    assert result.loc["600000.SH", "trading_day"] == pd.Timestamp("2024-01-01")
    assert result.loc["600000.SH", "total_shares"] == 1000.0


def test_get_fundamentals_requires_named_date_when_fields_omitted_for_financial_table(ptrade_api, data_context):
    _activate(ptrade_api, "2024-05-01")
    data_context.fundamentals_dict["600000.SH"] = pd.DataFrame(
        {
            "publ_date": [pd.Timestamp("2024-04-20")],
            "end_date": [pd.Timestamp("2024-03-31")],
            "roe": [0.11],
        }
    )

    with pytest.raises(ValueError):
        ptrade_api.get_fundamentals("600000.SH", "profit_ability")


def test_get_fundamentals_rejects_unknown_table(ptrade_api):
    _activate(ptrade_api, "2024-05-01")

    with pytest.raises(ValueError):
        ptrade_api.get_fundamentals("600000.SH", "not_a_table", fields="roe", date="2024-05-01")
