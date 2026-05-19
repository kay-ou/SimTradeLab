# -*- coding: utf-8 -*-

import pytest

from simtradelab.i18n import get_locale, set_locale
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.lifecycle_config import API_LIFECYCLE_RESTRICTIONS
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase


def test_ptrade_api_exposes_all_configured_callable_apis():
    """生命周期配置中的 PTrade API 都应在模拟层保留入口。"""
    expected = set(API_LIFECYCLE_RESTRICTIONS) - {"log"}
    missing = sorted(name for name in expected if not hasattr(PtradeAPI, name))

    assert missing == []


@pytest.mark.parametrize(
    ("api_name", "args"),
    [
        ("order_market", ("600000.SH", 100, 0)),
        ("get_snapshot", ("600000.SH",)),
        ("get_cb_list", ()),
        ("margincash_open", ("600000.SH", 100)),
        ("get_margin_contract", ()),
        ("get_etf_list", ()),
        ("open_prepared", ("10000001.XSHO", 1)),
        ("option_buy_open", ("10000001.XSHO", 1)),
        ("option_sell_close", ("10000001.XSHO", 1)),
        ("option_sell_open", ("10000001.XSHO", 1)),
        ("option_buy_close", ("10000001.XSHO", 1)),
    ],
)
def test_non_local_backtest_apis_keep_entrypoints_and_raise_not_supported(ptrade_api, api_name, args):
    """非本地回测能力保留 PTrade 入口，但明确报不支持。"""
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    with pytest.raises(NotImplementedError, match=api_name):
        getattr(ptrade_api, api_name)(*args)


def test_permission_test_entrypoint_raises_not_supported_in_allowed_phase(ptrade_api):
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)

    with pytest.raises(NotImplementedError, match="permission_test"):
        ptrade_api.permission_test()


def test_unsupported_api_error_uses_active_locale(ptrade_api):
    old_locale = get_locale()
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    try:
        set_locale("en")
        with pytest.raises(NotImplementedError, match="Local backtesting does not support PTrade API get_snapshot"):
            ptrade_api.get_snapshot("600000.SH")
    finally:
        set_locale(old_locale)
