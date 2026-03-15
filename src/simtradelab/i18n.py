# -*- coding: utf-8 -*-
"""
simtradelab i18n — 线程安全的翻译模块

使用方式:
    from simtradelab.i18n import set_locale, t
    set_locale("en")
    log.info(t("bt.start", strategy="my_strategy"))
"""

import json
import threading
from pathlib import Path

_locales: dict[str, dict[str, str]] = {}
_thread_local = threading.local()
_DEFAULT_LOCALE = "zh"


def _load_locales() -> None:
    locales_dir = Path(__file__).parent / "locales"
    for path in locales_dir.glob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            _locales[path.stem] = json.load(f)


def set_locale(locale: str) -> None:
    _thread_local.locale = locale


def get_locale() -> str:
    return getattr(_thread_local, "locale", _DEFAULT_LOCALE)


def t(key: str, **params: object) -> str:
    locale = get_locale()
    translations = _locales.get(locale) or _locales.get(_DEFAULT_LOCALE, {})
    template = translations.get(key)
    if template is None:
        template = _locales.get(_DEFAULT_LOCALE, {}).get(key, key)
    return template.format(**params) if params else template


_load_locales()
