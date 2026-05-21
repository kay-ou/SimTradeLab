# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import pytest


def _set_broker_profile(ptrade_api, profile):
    ptrade_api.broker_profile = profile
    ptrade_api.context.broker_profile = profile
    ptrade_api.context.g.broker_profile = profile


class TestBrokerProfileCompat:
    def test_get_history_1m_context_with_1d_frequency_aligns_trade_day(self, ptrade_api):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.frequency = "1m"
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-04 09:32:00")

        result = ptrade_api.get_history(
            count=2,
            frequency="1d",
            field="close",
            security_list=["600000.SH"],
            fq="pre",
        )
        assert isinstance(result, pd.DataFrame)
        assert "600000.SH" in result.columns
        assert len(result) > 0
        assert not result["600000.SH"].isna().all()

    def test_get_price_1m_context_with_1d_frequency_aligns_trade_day(self, ptrade_api):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.frequency = "1m"
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-04 09:32:00")

        result = ptrade_api.get_price(
            "600000.SH",
            count=2,
            frequency="1d",
            fields="close",
            fq="pre",
        )
        assert isinstance(result, pd.DataFrame)
        assert "close" in result.columns
        assert len(result) > 0
        assert not result["close"].isna().all()

    def test_get_history_default_fields_is_multi_field(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.current_dt = test_dates[-1]

        result = ptrade_api.get_history(
            count=3,
            security_list="600000.SH",
        )
        assert isinstance(result, pd.DataFrame)
        assert "open" in result.columns
        assert "high" in result.columns
        assert "low" in result.columns
        assert "close" in result.columns
        assert "volume" in result.columns
        assert "money" in result.columns
        assert "price" in result.columns

    def test_get_history_guosheng_rejects_is_dict(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "guosheng")
        ptrade_api.context.current_dt = test_dates[-1]
        ptrade_api.set_universe(["600000.SH"])

        with pytest.raises(ValueError, match="is_dict"):
            ptrade_api.get_history(
                count=3,
                field="close",
                security_list=["600000.SH"],
                is_dict=True,
            )

    def test_get_price_guosheng_rejects_is_dict(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "guosheng")
        ptrade_api.context.current_dt = test_dates[-1]

        with pytest.raises(ValueError, match="is_dict"):
            ptrade_api.get_price(
                "600000.SH",
                count=3,
                fields="close",
                is_dict=True,
            )

    def test_get_price_requires_exactly_one_of_start_date_or_count(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.current_dt = test_dates[-1]

        with pytest.raises(ValueError, match="start_date|count"):
            ptrade_api.get_price(
                "600000.SH",
                fields="close",
            )

        with pytest.raises(ValueError, match="start_date|count"):
            ptrade_api.get_price(
                "600000.SH",
                start_date="2024-01-01",
                count=3,
                fields="close",
            )

    def test_get_price_guosheng_rejects_dypre(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "guosheng")
        ptrade_api.context.current_dt = test_dates[-1]

        with pytest.raises(ValueError, match="invalid fq argument"):
            ptrade_api.get_price(
                "600000.SH",
                count=3,
                fields="close",
                fq="dypre",
            )

    def test_get_price_guosheng_rejects_is_open_field(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "guosheng")
        ptrade_api.context.current_dt = test_dates[-1]

        with pytest.raises(ValueError, match="is_open"):
            ptrade_api.get_price(
                "600000.SH",
                count=3,
                fields="is_open",
            )

    def test_get_price_shanxi_supports_dypre(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "shanxi")
        ptrade_api.context.current_dt = test_dates[-1]

        result = ptrade_api.get_price(
            "600000.SH",
            count=3,
            fields="close",
            fq="dypre",
        )
        assert isinstance(result, pd.DataFrame)

    def test_get_price_shanxi_is_dict_empty_returns_none(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "shanxi")
        ptrade_api.context.current_dt = test_dates[-1]

        result = ptrade_api.get_price(
            "999999.SH",
            count=3,
            fields="close",
            is_dict=True,
        )
        assert result is None

    def test_get_history_security_list_none_uses_universe(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.current_dt = test_dates[-1]
        ptrade_api.set_universe(["600000.SH"])

        result = ptrade_api.get_history(
            count=3,
            field="close",
            security_list=None,
        )
        assert isinstance(result, pd.DataFrame)
        assert "600000.SH" in result.columns
        assert "000001.SZ" not in result.columns

    def test_get_history_fill_pre_fills_minute_gap(self, ptrade_api):
        _set_broker_profile(ptrade_api, "auto")
        idx = pd.to_datetime(["2024-01-02 09:31:00", "2024-01-02 09:33:00"])
        ptrade_api.data_context.stock_data_dict_1m = {
            "600000.SH": pd.DataFrame(
                {
                    "open": [10.0, 10.2],
                    "high": [10.1, 10.3],
                    "low": [9.9, 10.1],
                    "close": [10.0, 10.2],
                    "volume": [100.0, 200.0],
                    "money": [1000.0, 2000.0],
                },
                index=idx,
            )
        }
        ptrade_api.context.current_dt = pd.Timestamp("2024-01-02 09:33:00")

        result = ptrade_api.get_history(
            count=3,
            frequency="1m",
            field="close",
            security_list=["600000.SH"],
            include=True,
            fill="pre",
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert float(result["600000.SH"].iloc[1]) == float(result["600000.SH"].iloc[0])

    def test_get_history_invalid_fill_raises(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.current_dt = test_dates[-1]
        with pytest.raises(ValueError, match="invalid fill"):
            ptrade_api.get_history(
                count=3,
                field="close",
                security_list=["600000.SH"],
                fill="forward",
            )

    def test_fill_minute_gaps_skips_lunch_break(self, ptrade_api):
        idx = pd.to_datetime(["2024-01-02 11:30:00", "2024-01-02 13:01:00"])
        df = pd.DataFrame({"close": [10.0, 10.2], "volume": [100.0, 200.0]}, index=idx)
        out = ptrade_api._fill_minute_gaps(df, 1)
        assert pd.Timestamp("2024-01-02 12:00:00") not in out.index

    def test_get_history_supports_multi_frequency_5m_and_1w(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.current_dt = test_dates[-1]

        idx_1m = pd.date_range("2024-01-02 09:31:00", periods=20, freq="min")
        ptrade_api.data_context.stock_data_dict_1m = {
            "600000.SH": pd.DataFrame(
                {
                    "open": np.linspace(10.0, 10.5, len(idx_1m)),
                    "high": np.linspace(10.1, 10.6, len(idx_1m)),
                    "low": np.linspace(9.9, 10.4, len(idx_1m)),
                    "close": np.linspace(10.0, 10.5, len(idx_1m)),
                    "volume": np.ones(len(idx_1m)) * 100.0,
                    "money": np.ones(len(idx_1m)) * 1000.0,
                },
                index=idx_1m,
            )
        }
        ptrade_api.context.current_dt = idx_1m[-1]
        result_5m = ptrade_api.get_history(
            count=3,
            frequency="5m",
            field="close",
            security_list=["600000.SH"],
        )
        assert isinstance(result_5m, pd.DataFrame)
        assert len(result_5m) > 0

        ptrade_api.context.current_dt = test_dates[-1]
        result_1w = ptrade_api.get_history(
            count=3,
            frequency="1w",
            field="close",
            security_list=["600000.SH"],
        )
        assert isinstance(result_1w, pd.DataFrame)
        assert len(result_1w) > 0

    def test_get_history_unlimited_dtype_shanxi(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "shanxi")
        ptrade_api.context.current_dt = test_dates[-1]
        ptrade_api.data_context.stock_data_dict["600000.SH"]["unlimited"] = np.array(
            [0.0] * len(test_dates), dtype=float
        )

        result = ptrade_api.get_history(
            count=5,
            field="unlimited",
            security_list=["600000.SH"],
        )
        assert isinstance(result, pd.DataFrame)
        # shanxi 多股票返回 MultiIndex(field, code) 列
        assert str(result[("unlimited", "600000.SH")].dtype) == "int64"

    def test_get_price_is_dict_structured_auto(self, ptrade_api, test_dates):
        _set_broker_profile(ptrade_api, "auto")
        ptrade_api.context.current_dt = test_dates[-1]

        result = ptrade_api.get_price(
            ["600000.SH", "000001.SZ"],
            count=3,
            fields=["close", "volume"],
            is_dict=True,
        )
        assert isinstance(result, dict)
        assert "600000.SH" in result
        arr = result["600000.SH"]
        assert arr.dtype.names == ("close", "volume")

    def test_documented_kwargs_for_futures_apis(self, ptrade_api):
        _set_broker_profile(ptrade_api, "auto")

        with pytest.raises(NotImplementedError):
            ptrade_api.buy_open(contract="IF88", amount=1)
        with pytest.raises(NotImplementedError):
            ptrade_api.sell_close(contract="IF88", amount=1, close_today=True)
        with pytest.raises(NotImplementedError):
            ptrade_api.margin_trade(security="510300.SH", amount=100, market_type="CASH")
        with pytest.raises(NotImplementedError):
            ptrade_api.get_instruments(contract="IF")

    def test_extra_alias_kwargs_rejected(self, ptrade_api):
        _set_broker_profile(ptrade_api, "auto")

        with pytest.raises(TypeError):
            ptrade_api.buy_open(sid="IF88", amount=1)
        with pytest.raises(TypeError):
            ptrade_api.run_interval(ptrade_api.context, lambda _context: None, unsupported="09:30-10:00")

    def test_strict_broker_guard(self, ptrade_api):
        _set_broker_profile(ptrade_api, "dongguan")
        with pytest.raises(NotImplementedError, match="broker_profile=dongguan"):
            ptrade_api.get_trend_data()

    def test_get_fundamentals_param_restriction_by_broker(self, ptrade_api):
        _set_broker_profile(ptrade_api, "dongguan")
        with pytest.raises(ValueError, match="date_type"):
            ptrade_api.get_fundamentals(
                security="600000.SH",
                table="valuation",
                fields=["pb_ratio"],
                date_type="report_date",
            )

    def test_get_fundamentals_shanxi_default_returns_dict(self, ptrade_api):
        _set_broker_profile(ptrade_api, "shanxi")
        result = ptrade_api.get_fundamentals(
            security="600000.SH",
            table="valuation",
            fields=["pb_ratio"],
        )
        assert isinstance(result, dict)

    def test_get_fundamentals_shanxi_is_dataframe_true_returns_df(self, ptrade_api):
        _set_broker_profile(ptrade_api, "shanxi")
        result = ptrade_api.get_fundamentals(
            security="600000.SH",
            table="valuation",
            fields=["pb_ratio"],
            is_dataframe=True,
        )
        assert isinstance(result, pd.DataFrame)

    def test_create_dir_return_by_broker_profile(self, ptrade_api):
        _set_broker_profile(ptrade_api, "guosheng")
        assert ptrade_api.create_dir() is None

        _set_broker_profile(ptrade_api, "dongguan")
        assert ptrade_api.create_dir("tmp_dg") is None

        _set_broker_profile(ptrade_api, "shanxi")
        with pytest.raises(ValueError, match="user_path"):
            ptrade_api.create_dir()
        assert ptrade_api.create_dir("tmp_sx") is True

        _set_broker_profile(ptrade_api, "auto")
        result = ptrade_api.create_dir("tmp_auto")
        assert isinstance(result, str)
