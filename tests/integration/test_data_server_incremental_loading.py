import pandas as pd
import pytest

from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.context import Context
from simtradelab.ptrade.data_context import DataContext
from simtradelab.ptrade.object import Portfolio
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


def test_live_api_cache_invalidates_when_data_server_replaces_data_path(
    tmp_path, simple_log
):
    symbol = "000001.SZ"
    date = pd.Timestamp("2024-01-02")

    def write_price(root, close):
        market_path = root / "cn"
        (market_path / "stocks").mkdir(parents=True)
        pd.DataFrame(
            {
                "date": [date],
                "open": [close],
                "high": [close],
                "low": [close],
                "close": [close],
                "volume": [1000],
                "amount": [close * 1000],
            }
        ).to_parquet(market_path / "stocks" / f"{symbol}.parquet", index=False)

    first_path = tmp_path / "first"
    second_path = tmp_path / "second"
    write_price(first_path, 10.0)
    write_price(second_path, 20.0)

    server = DataServer(required_data={"price"}, data_path=str(first_path))
    data_context = DataContext(
        stock_data_dict=server.stock_data_dict,
        valuation_dict=server.valuation_dict,
        fundamentals_dict=server.fundamentals_dict,
        exrights_dict=server.exrights_dict,
        benchmark_data=server.benchmark_data,
        stock_metadata=server.stock_metadata,
        index_constituents=server.index_constituents,
        stock_status_history=server.stock_status_history,
        adj_pre_cache=server.adj_pre_cache,
        adj_post_cache=server.adj_post_cache,
        dividend_cache=server.dividend_cache,
        trade_days=server.trade_days,
        stock_data_dict_1m=server.stock_data_dict_1m,
        data_server=server,
    )
    context = Context(portfolio=Portfolio(100000.0), current_dt=date)
    api = PtradeAPI(data_context, context, simple_log)

    first = api.get_history(
        1, field="close", security_list=symbol, include=True
    )
    repeated = api.get_history(
        1, field="close", security_list=symbol, include=True
    )
    assert repeated is first
    assert first.iloc[0, 0] == 10.0

    replaced = DataServer(required_data={"price"}, data_path=str(second_path))
    updated = api.get_history(
        1, field="close", security_list=symbol, include=True
    )

    assert replaced is server
    assert updated.iloc[0, 0] == 20.0
    assert updated is not first


def test_live_api_data_caches_invalidate_when_data_server_replaces_data_path(
    tmp_path, simple_log
):
    symbol = "000001.SZ"
    query_date = pd.Timestamp("2024-05-01")

    def write_data(root, *, is_st, fundamentals):
        market_path = root / "cn"
        (market_path / "stocks").mkdir(parents=True)
        (market_path / "fundamentals").mkdir()
        (market_path / "metadata").mkdir()
        pd.DataFrame(
            {
                "date": [query_date],
                "open": [10.0],
                "high": [10.0],
                "low": [10.0],
                "close": [10.0],
                "volume": [1000],
                "amount": [10000.0],
            }
        ).to_parquet(market_path / "stocks" / f"{symbol}.parquet", index=False)
        pd.DataFrame(fundamentals).to_parquet(
            market_path / "fundamentals" / f"{symbol}.parquet", index=False
        )
        pd.DataFrame(
            {
                "date": [query_date.strftime("%Y%m%d")],
                "status_type": ["ST"],
                "symbols": [[symbol] if is_st else []],
            }
        ).to_parquet(market_path / "metadata" / "stock_status.parquet", index=False)

    first_path = tmp_path / "first"
    second_path = tmp_path / "second"
    write_data(
        first_path,
        is_st=True,
        fundamentals={
            "publ_date": [pd.Timestamp("2024-04-20")],
            "end_date": [pd.Timestamp("2024-03-31")],
            "roe": [0.11],
        },
    )
    write_data(
        second_path,
        is_st=False,
        fundamentals={
            "publ_date": [
                pd.Timestamp("2024-04-20"),
                pd.Timestamp("2024-04-25"),
            ],
            "end_date": [
                pd.Timestamp("2024-03-31"),
                pd.Timestamp("2024-06-30"),
            ],
            "roe": [0.11, 0.22],
        },
    )

    server = DataServer(
        required_data={"price", "fundamentals"}, data_path=str(first_path)
    )
    data_context = DataContext(
        stock_data_dict=server.stock_data_dict,
        valuation_dict=server.valuation_dict,
        fundamentals_dict=server.fundamentals_dict,
        exrights_dict=server.exrights_dict,
        benchmark_data=server.benchmark_data,
        stock_metadata=server.stock_metadata,
        index_constituents=server.index_constituents,
        stock_status_history=server.stock_status_history,
        adj_pre_cache=server.adj_pre_cache,
        adj_post_cache=server.adj_post_cache,
        dividend_cache=server.dividend_cache,
        trade_days=server.trade_days,
        stock_data_dict_1m=server.stock_data_dict_1m,
        data_server=server,
    )
    context = Context(portfolio=Portfolio(100000.0), current_dt=query_date)
    api = PtradeAPI(data_context, context, simple_log)

    assert api.get_stock_status(symbol, query_type="ST") == {symbol: True}
    first_fundamentals = api.get_fundamentals(
        symbol,
        "profit_ability",
        fields="roe",
        date=query_date,
    )
    assert first_fundamentals.loc[symbol, "roe"] == pytest.approx(0.11)

    same_server = DataServer(
        required_data={"price", "fundamentals"}, data_path=str(first_path)
    )
    assert same_server is server
    assert len(api._stock_status_cache) == 1
    assert len(api._fundamentals_cache) == 1

    replaced = DataServer(
        required_data={"price", "fundamentals"}, data_path=str(second_path)
    )
    updated_fundamentals = api.get_fundamentals(
        symbol,
        "profit_ability",
        fields="roe",
        date=query_date,
    )

    assert replaced is server
    assert api.get_stock_status(symbol, query_type="ST") == {symbol: False}
    assert updated_fundamentals.loc[symbol, "roe"] == pytest.approx(0.22)
