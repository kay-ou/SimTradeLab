import pandas as pd
import pytest

from simtradelab.service.data_server import DataServer


@pytest.fixture(autouse=True)
def reset_data_server_singleton():
    DataServer._instance = None
    DataServer._initialized = False
    yield
    DataServer._instance = None
    DataServer._initialized = False


def test_incremental_price_and_exrights_loading_initializes_real_caches(tmp_path):
    symbol = "000001.SZ"
    market_path = tmp_path / "cn"
    (market_path / "stocks").mkdir(parents=True)
    (market_path / "exrights").mkdir()

    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    pd.DataFrame(
        {
            "date": dates,
            "open": [10.0, 10.5],
            "high": [10.5, 11.0],
            "low": [9.8, 10.2],
            "close": [10.2, 10.8],
            "volume": [1000, 1200],
            "amount": [10200.0, 12960.0],
        }
    ).to_parquet(market_path / "stocks" / f"{symbol}.parquet", index=False)
    pd.DataFrame(
        {
            "date": [dates[1]],
            "dividend": [0.25],
            "exer_forward_a": [0.98],
            "exer_forward_b": [0.1],
            "allotted_ps": [0.0],
            "rationed_ps": [0.0],
            "rationed_px": [0.0],
            "bonus_ps": [0.0],
        }
    ).to_parquet(market_path / "exrights" / f"{symbol}.parquet", index=False)

    for kind, factors in {
        "pre": ([0.98, 1.0], [0.1, 0.0]),
        "post": ([1.0, 1.0], [0.0, 0.25]),
    }.items():
        pd.DataFrame(
            {
                "date": dates,
                "adj_a": factors[0],
                "adj_b": factors[1],
                "symbol": symbol,
            }
        ).to_parquet(market_path / f"ptrade_adj_{kind}.parquet", index=False)

    initial_server = DataServer(required_data=set(), data_path=str(tmp_path))

    assert symbol not in initial_server.stock_data_dict
    assert symbol not in initial_server.exrights_dict
    assert initial_server.adj_pre_cache is None
    assert initial_server.adj_post_cache is None
    assert initial_server.dividend_cache is None

    supplemented_server = DataServer(
        required_data={"price", "exrights"},
        data_path=str(tmp_path),
    )

    assert supplemented_server is initial_server
    assert supplemented_server.stock_data_dict[symbol].loc[dates[1], "close"] == pytest.approx(10.8)
    assert supplemented_server.exrights_dict[symbol].loc[20240103, "dividend"] == pytest.approx(0.25)
    assert supplemented_server.adj_pre_cache[symbol].loc[dates[0], "adj_a"] == pytest.approx(0.98)
    assert supplemented_server.adj_post_cache[symbol].loc[dates[1], "adj_b"] == pytest.approx(0.25)
    assert supplemented_server.dividend_cache[symbol] == {"20240103": pytest.approx(0.25)}


def test_incremental_exrights_only_loads_price_before_building_missing_caches(tmp_path):
    symbol = "000001.SZ"
    market_path = tmp_path / "cn"
    (market_path / "stocks").mkdir(parents=True)
    (market_path / "exrights").mkdir()
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])

    pd.DataFrame(
        {
            "date": dates,
            "open": [10.0, 10.5],
            "high": [10.5, 11.0],
            "low": [9.8, 10.2],
            "close": [10.2, 10.8],
            "volume": [1000, 1200],
            "amount": [10200.0, 12960.0],
        }
    ).to_parquet(market_path / "stocks" / f"{symbol}.parquet", index=False)
    pd.DataFrame(
        {
            "date": [dates[1]],
            "dividend": [0.25],
            "exer_forward_a": [0.98],
            "exer_forward_b": [0.1],
            "allotted_ps": [0.0],
            "rationed_ps": [0.0],
            "rationed_px": [0.0],
            "bonus_ps": [0.0],
        }
    ).to_parquet(market_path / "exrights" / f"{symbol}.parquet", index=False)

    server = DataServer(required_data=set(), data_path=str(tmp_path))
    supplemented = DataServer(required_data={"exrights"}, data_path=str(tmp_path))

    assert supplemented is server
    assert supplemented.stock_data_dict[symbol].loc[dates[1], "close"] == pytest.approx(10.8)
    assert supplemented.adj_pre_cache[symbol].index.equals(pd.DatetimeIndex(dates))
    assert supplemented.dividend_cache[symbol] == {"20240103": pytest.approx(0.25)}
