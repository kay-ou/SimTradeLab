# -*- coding: utf-8 -*-
"""
PTrade API路由器
"""

from .backtest import BacktestAPIRouter
from .base import BaseAPIRouter
from .research import ResearchAPIRouter
from .trading import TradingAPIRouter

__all__ = [
    "BaseAPIRouter",
    "BacktestAPIRouter",
    "TradingAPIRouter",
    "ResearchAPIRouter",
]
