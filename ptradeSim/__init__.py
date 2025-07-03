# -*- coding: utf-8 -*-
"""
ptradeSim - Python量化交易回测框架

主要组件:
- engine: 回测引擎
- api: API接口
- context: 上下文和投资组合管理
"""

from .engine import BacktestEngine
from . import api
from .context import Context, Portfolio, Position

__version__ = "1.0.0"
__author__ = "ptradeSim Team"

__all__ = [
    'BacktestEngine',
    'api',
    'Context',
    'Portfolio',
    'Position'
]