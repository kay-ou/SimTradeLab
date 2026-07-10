from simtradelab.backtest import config as config_module
from simtradelab.backtest.config import BacktestConfig


def _make_config(**overrides):
    values = {
        "strategy_name": "example",
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
    }
    values.update(overrides)
    return BacktestConfig(**values)


def test_locale_auto_uses_chinese_for_cn_market():
    config = _make_config(market="CN", locale="auto")

    assert config.locale == "zh"


def test_locale_auto_uses_detected_locale_for_non_cn_market():
    config = _make_config(market="US", locale="auto")

    assert config.locale == config_module._DEFAULT_LOCALE
