# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
PTrade 生命周期控制器

管理策略的生命周期阶段转换
"""


from __future__ import annotations

import logging
from enum import Enum
from typing import Optional


class LifecyclePhase(Enum):
    """PTrade策略生命周期阶段枚举"""

    INITIALIZE = "initialize"
    BEFORE_TRADING_START = "before_trading_start"
    HANDLE_DATA = "handle_data"
    AFTER_TRADING_END = "after_trading_end"
    TICK_DATA = "tick_data"
    ON_ORDER_RESPONSE = "on_order_response"
    ON_TRADE_RESPONSE = "on_trade_response"


class PTradeLifecycleError(Exception):
    """PTrade生命周期违规错误"""

    pass


# 允许的阶段转换规则
_ALLOWED_TRANSITIONS: dict[Optional[LifecyclePhase], list[LifecyclePhase]] = {
    None: [LifecyclePhase.INITIALIZE],
    LifecyclePhase.INITIALIZE: [
        LifecyclePhase.BEFORE_TRADING_START,
        LifecyclePhase.HANDLE_DATA,
    ],
    LifecyclePhase.BEFORE_TRADING_START: [
        LifecyclePhase.HANDLE_DATA,
        LifecyclePhase.TICK_DATA,
    ],
    LifecyclePhase.HANDLE_DATA: [
        LifecyclePhase.HANDLE_DATA,
        LifecyclePhase.TICK_DATA,
        LifecyclePhase.AFTER_TRADING_END,
        LifecyclePhase.ON_ORDER_RESPONSE,
        LifecyclePhase.ON_TRADE_RESPONSE,
    ],
    LifecyclePhase.TICK_DATA: [
        LifecyclePhase.TICK_DATA,
        LifecyclePhase.HANDLE_DATA,
        LifecyclePhase.ON_ORDER_RESPONSE,
        LifecyclePhase.ON_TRADE_RESPONSE,
    ],
    LifecyclePhase.ON_ORDER_RESPONSE: [
        LifecyclePhase.HANDLE_DATA,
        LifecyclePhase.TICK_DATA,
        LifecyclePhase.ON_TRADE_RESPONSE,
    ],
    LifecyclePhase.ON_TRADE_RESPONSE: [
        LifecyclePhase.HANDLE_DATA,
        LifecyclePhase.TICK_DATA,
    ],
    LifecyclePhase.AFTER_TRADING_END: [
        LifecyclePhase.BEFORE_TRADING_START,
        LifecyclePhase.INITIALIZE,
    ],
}


class LifecycleController:
    """PTrade策略生命周期控制器

    管理策略执行的当前生命周期阶段和阶段转换验证
    """

    def __init__(self, strategy_mode: str = "backtest"):
        self._current_phase: Optional[LifecyclePhase] = None
        self._strategy_mode = strategy_mode
        self._logger = logging.getLogger(self.__class__.__name__)
        self._phase_executed: set[LifecyclePhase] = set()

    @property
    def current_phase(self) -> Optional[LifecyclePhase]:
        """获取当前生命周期阶段"""
        return self._current_phase

    @property
    def current_phase_name(self) -> Optional[str]:
        """获取当前生命周期阶段名称"""
        return self._current_phase.value if self._current_phase else None

    def set_phase(self, phase: LifecyclePhase) -> None:
        """设置当前生命周期阶段

        Raises:
            PTradeLifecycleError: 如果阶段转换不合法
        """
        old_phase = self._current_phase
        self._validate_phase_transition(old_phase, phase)
        self._current_phase = phase
        self._phase_executed.add(phase)

    def is_phase_executed(self, phase: LifecyclePhase) -> bool:
        """检查指定阶段是否已执行过"""
        return phase in self._phase_executed

    def reset(self) -> None:
        """重置生命周期控制器状态"""
        self._current_phase = None
        self._phase_executed.clear()

    @staticmethod
    def _validate_phase_transition(
        old_phase: Optional[LifecyclePhase], new_phase: LifecyclePhase
    ) -> None:
        """验证生命周期阶段转换的合法性"""
        allowed = _ALLOWED_TRANSITIONS.get(old_phase, [])
        if new_phase not in allowed:
            raise PTradeLifecycleError(
                f"Invalid phase transition: {old_phase} -> {new_phase}. "
                f"Allowed transitions: {allowed}"
            )
