import pandas as pd
import pytest

from simtradelab.ptrade import adj_cache
from simtradelab.service import data_server as data_server_module
from simtradelab.service.data_server import DataServer


class FakeLazyDataDict:
    def __init__(self, data_dir, data_type, all_keys_list, **kwargs):
        self.data_dir = data_dir
        self.data_type = data_type
        self._all_keys = all_keys_list


@pytest.fixture(autouse=True)
def reset_data_server():
    DataServer._instance = None
    DataServer._initialized = False
    yield
    DataServer._instance = None
    DataServer._initialized = False


def test_data_path_expands_user_home_before_resolving(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(data_server_module, "_migrate_legacy_data", lambda path: None)
    monkeypatch.setattr(data_server_module.atexit, "register", lambda callback: None)
    monkeypatch.setattr(DataServer, "_load_data", lambda self, required_data, frequency: None)

    server = DataServer(data_path="~/market-data")

    assert server.data_path == str((tmp_path / "market-data").resolve())


@pytest.mark.parametrize("required_data", [{"price"}, {"exrights"}])
def test_supplementing_adjustment_data_initializes_all_caches(monkeypatch, required_data):
    server = object.__new__(DataServer)
    server.data_path = "/market-data"
    server._loaded_data_types = set()
    server._stock_keys_cache = ["000001.SZ"]
    server._stock_1m_keys_cache = []
    server._valuation_keys_cache = []
    server._fundamentals_keys_cache = []
    server._exrights_keys_cache = ["000001.SZ"]
    server.stock_data_dict = FakeLazyDataDict(server.data_path, "stock", [])
    server.stock_data_dict_1m = None
    server.valuation_dict = FakeLazyDataDict(server.data_path, "valuation", [])
    server.fundamentals_dict = FakeLazyDataDict(server.data_path, "fundamentals", [])
    server.exrights_dict = FakeLazyDataDict(server.data_path, "exrights", [])
    server.benchmark_data = {}
    server.stock_metadata = pd.DataFrame()
    server.index_constituents = {}
    server.stock_status_history = {}
    server.trade_days = None
    server.adj_pre_cache = None
    server.adj_post_cache = None
    server.dividend_cache = None

    monkeypatch.setattr(data_server_module, "LazyDataDict", FakeLazyDataDict)
    monkeypatch.setattr(adj_cache, "load_adj_pre_cache", lambda context: {"pre": context.stock_data_dict})
    monkeypatch.setattr(adj_cache, "load_adj_post_cache", lambda context: {"post": context.exrights_dict})
    monkeypatch.setattr(adj_cache, "create_dividend_cache", lambda context: {"dividend": context.exrights_dict})

    server._ensure_data_loaded(required_data)

    assert server.adj_pre_cache == {"pre": server.stock_data_dict}
    assert server.adj_post_cache == {"post": server.exrights_dict}
    assert server.dividend_cache == {"dividend": server.exrights_dict}
