# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
PTrade上下文和模式定义

完全符合PTrade官方API规范的Context对象实现
"""


from __future__ import annotations

import types
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .lifecycle_controller import LifecycleController
from .config_manager import config
from simtradelab.ptrade.object import (
    Blotter,
    Portfolio,
)

class PTradeMode(Enum):
    """PTrade运行模式"""

    RESEARCH = "research"  # 研究模式
    BACKTEST = "backtest"  # 回测模式
    TRADING = "trading"  # 交易模式
    MARGIN_TRADING = "margin_trading"  # 融资融券交易模式


@dataclass
class Context:
    """PTrade策略上下文对象 - 完全符合PTrade规范

    这是策略执行的核心上下文对象，包含了所有策略运行所需的状态信息
    """

    # === 核心必需属性 ===
    portfolio: Portfolio
    mode: PTradeMode = PTradeMode.BACKTEST

    # === PTrade官方Context属性 ===
    capital_base: Optional[float] = None  # 起始资金
    previous_date: Optional[datetime] = None  # 前一个交易日
    initialized: bool = False  # 是否执行初始化
    blotter: Optional[Blotter] = None
    recorded_vars: dict[str, Any] = field(default_factory=dict)  # 收益曲线值

    # === 策略配置属性 ===
    universe: list[str] = field(default_factory=list)  # 股票池
    benchmark: Optional[str] = None  # 基准
    current_dt: Optional[datetime] = None  # 当前时间
    frequency: str = '1d'  # 回测频率 '1d'日线 '1m'分钟线

    # === 生命周期管理 ===
    _lifecycle_controller: Optional[LifecycleController] = None

    def __post_init__(self) -> None:
        """初始化后处理"""
        # === 初始化g全局对象 ===
        self.g = types.SimpleNamespace()  # 全局变量容器

        # === 设置时间 ===
        if self.current_dt is None:
            self.current_dt = datetime.now()

        # === 初始化必需组件 ===
        if self.blotter is None:
            self.blotter = Blotter(self.current_dt)

        # === 初始化生命周期控制器 ===
        if self._lifecycle_controller is None:
            self._lifecycle_controller = LifecycleController(self.mode.value)

        self.blotter.current_dt = self.current_dt

    # ==========================================
    # 生命周期状态查询接口
    # ==========================================

    def get_current_lifecycle_phase(self) -> Optional[str]:
        """获取当前生命周期阶段"""
        return self._lifecycle_controller.current_phase_name

    def get_lifecycle_statistics(self) -> dict[str, Any]:
        """获取生命周期统计信息"""
        return self._lifecycle_controller.get_call_statistics()

    def is_api_allowed(self, api_name: str) -> bool:
        """检查API是否在当前阶段允许调用"""
        result = self._lifecycle_controller.validate_api_call(api_name)
        return result.is_valid

    # ==========================================
    # 工具方法
    # ==========================================

    def log_info(self, message: str) -> None:
        """记录信息日志"""
        print(f"[INFO] {self.current_dt}: {message}")

    def record(self, name: str, value: Any) -> None:
        """记录收益曲线值"""
        self.recorded_vars[name] = value

    def reset_for_new_strategy(self) -> None:
        """为新策略重置上下文状态"""
        self.initialized = False
        self.recorded_vars.clear()
        self._lifecycle_controller.reset()

        # 重置blotter
        self.blotter = Blotter(self.current_dt)
        self.blotter.current_dt = self.current_dt


# ==========================================
# 工厂函数
# ==========================================


def create_research_context(capital_base: float = 1000000) -> Context:
    """创建研究模式上下文"""
    portfolio = Portfolio(initial_capital=capital_base)
    return Context(
        portfolio=portfolio, mode=PTradeMode.RESEARCH, capital_base=capital_base
    )


def create_backtest_context(
    capital_base: float = 1000000,
    commission_rate: float = 0.0003,
    slippage_rate: float = 0.0,
) -> Context:
    """创建回测模式上下文"""
    portfolio = Portfolio(initial_capital=capital_base)
    context = Context(
        portfolio=portfolio, mode=PTradeMode.BACKTEST, capital_base=capital_base
    )
    config.update_trading_config(commission_ratio=commission_rate)
    config.update_trading_config(slippage=slippage_rate)
    return context


def create_trading_context(capital_base: float = 1000000) -> Context:
    """创建实盘交易模式上下文"""
    portfolio = Portfolio(initial_capital=capital_base)
    return Context(
        portfolio=portfolio, mode=PTradeMode.TRADING, capital_base=capital_base
    )
