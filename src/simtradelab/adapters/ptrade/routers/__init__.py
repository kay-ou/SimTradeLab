# -*- coding: utf-8 -*-
"""
PTrade API路由器
"""

from .backtest import BacktestAPIRouter
from .base import BaseAPIRouter
from .trading import TradingAPIRouter
from .research import ResearchAPIRouter

__all__ = [
    "BaseAPIRouter",
    "BacktestAPIRouter",
    "TradingAPIRouter",
    "ResearchAPIRouter",
]
