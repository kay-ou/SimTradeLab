# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
PTrade 生命周期控制器

负责管理策略的生命周期执行和API调用验证
"""


from __future__ import annotations

import logging
from enum import Enum
from threading import RLock
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

from .lifecycle_config import get_api_allowed_phases, is_api_allowed_in_phase


class LifecycleValidationResult(BaseModel):
    """生命周期验证结果"""

    is_valid: bool
    error_message: Optional[str] = None


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


class APICallRecord(BaseModel):
    """API调用记录"""

    api_name: str
    phase: str
    timestamp: float
    args: tuple = Field(default_factory=tuple)
    kwargs: dict = Field(default_factory=dict)
    success: bool
    error: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


class LifecycleController:
    """PTrade策略生命周期控制器

    功能：
    1. 管理策略执行的当前生命周期阶段
    2. 验证API调用是否符合PTrade生命周期限制
    3. 记录和监控API调用历史
    4. 提供生命周期状态查询接口
    """

    def __init__(self, strategy_mode: str = "backtest"):
        """
        初始化生命周期控制器

        Args:
            strategy_mode: 策略运行模式 (research/backtest/trading)
        """
        self._current_phase: Optional[LifecyclePhase] = None
        self._strategy_mode = strategy_mode
        self._logger = logging.getLogger(self.__class__.__name__)

        # 线程安全锁
        self._lock = RLock()

        # API调用历史记录
        self._call_history: list[APICallRecord] = []
        self._max_history_size = 1000

        # 阶段执行状态
        self._phase_executed: set[LifecyclePhase] = set()
        self._phase_callbacks: dict[LifecyclePhase, list[Callable]] = {
            phase: [] for phase in LifecyclePhase
        }

        # 统计信息
        self._api_call_count: dict[str, int] = {}
        self._phase_duration: dict[LifecyclePhase, float] = {}

        self._logger.debug(f"LifecycleController initialized for {strategy_mode} mode")

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

        Args:
            phase: 新的生命周期阶段

        Raises:
            PTradeLifecycleError: 如果阶段转换不合法
        """
        with self._lock:
            old_phase = self._current_phase

            # 验证阶段转换的合法性
            self._validate_phase_transition(old_phase, phase)

            self._current_phase = phase
            self._phase_executed.add(phase)

            self._logger.debug(f"Lifecycle phase changed: {old_phase} -> {phase}")

            # 执行阶段切换回调
            self._execute_phase_callbacks(phase)

    def validate_api_call(self, api_name: str) -> LifecycleValidationResult:
        """验证API调用是否在当前生命周期阶段允许

        Args:
            api_name: API函数名

        Returns:
            LifecycleValidationResult: 验证结果
        """
        with self._lock:
            # 如果没有设置当前阶段，默认允许（向后兼容）
            if self._current_phase is None:
                self._logger.warning(
                    f"API '{api_name}' called without lifecycle phase set. "
                    "Consider setting phase for proper validation."
                )
                return LifecycleValidationResult(is_valid=True)

            current_phase_name = self._current_phase.value

            # 检查API是否在当前阶段允许调用
            if not is_api_allowed_in_phase(api_name, current_phase_name):
                allowed_phases = get_api_allowed_phases(api_name)
                error_msg = (
                    f"API '{api_name}' cannot be called in phase '{current_phase_name}'. "
                    f"Allowed phases: {allowed_phases}"
                )
                self._logger.error(error_msg)
                return LifecycleValidationResult(
                    is_valid=False, error_message=error_msg
                )

            return LifecycleValidationResult(is_valid=True)

    def record_api_call(
        self,
        api_name: str,
        success: bool,
        args: tuple = (),
        kwargs: dict = {},
        error: Optional[str] = None,
    ) -> None:
        """记录API调用

        Args:
            api_name: API函数名
            success: 调用是否成功
            args: 调用参数
            kwargs: 调用关键字参数
            error: 错误信息（如果失败）
        """
        import time

        with self._lock:
            # 记录调用历史
            record = APICallRecord(
                api_name=api_name,
                phase=self.current_phase_name or "unknown",
                timestamp=time.time(),
                args=args,
                kwargs=kwargs or {},
                success=success,
                error=error,
            )

            self._call_history.append(record)

            # 限制历史记录大小
            if len(self._call_history) > self._max_history_size:
                self._call_history = self._call_history[-self._max_history_size :]

            # 更新统计
            self._api_call_count[api_name] = self._api_call_count.get(api_name, 0) + 1

            if not success:
                self._logger.warning(f"API call failed: {api_name} - {error}")

    def get_phase_apis(self, phase: Optional[LifecyclePhase] = None) -> list[str]:
        """获取指定阶段可调用的API列表

        Args:
            phase: 生命周期阶段，为None时使用当前阶段

        Returns:
            list[str]: 可调用的API列表
        """
        target_phase = phase or self._current_phase
        if target_phase is None:
            return []

        from .lifecycle_config import get_phase_apis

        return get_phase_apis(target_phase.value)

    def is_phase_executed(self, phase: LifecyclePhase) -> bool:
        """检查指定阶段是否已执行过"""
        return phase in self._phase_executed

    def register_phase_callback(
        self, phase: LifecyclePhase, callback: Callable[[], None]
    ) -> None:
        """注册阶段切换回调函数

        Args:
            phase: 生命周期阶段
            callback: 回调函数
        """
        with self._lock:
            self._phase_callbacks[phase].append(callback)
            self._logger.debug(f"Registered callback for phase {phase}")

    def get_call_statistics(self) -> dict[str, Any]:
        """获取API调用统计信息

        Returns:
            dict[str, Any]: 统计信息
        """
        with self._lock:
            total_calls = sum(self._api_call_count.values())
            failed_calls = len([r for r in self._call_history if not r.success])

            return {
                "total_api_calls": total_calls,
                "failed_calls": failed_calls,
                "success_rate": (total_calls - failed_calls) / max(total_calls, 1),
                "api_call_count": self._api_call_count.copy(),
                "phases_executed": [p.value for p in self._phase_executed],
                "current_phase": self.current_phase_name,
                "history_size": len(self._call_history),
            }

    def get_recent_calls(self, limit: int = 10) -> list[APICallRecord]:
        """获取最近的API调用记录

        Args:
            limit: 返回记录数量限制

        Returns:
            list[APICallRecord]: 最近的调用记录
        """
        with self._lock:
            return self._call_history[-limit:] if self._call_history else []

    def reset(self) -> None:
        """重置生命周期控制器状态"""
        with self._lock:
            self._current_phase = None
            self._phase_executed.clear()
            self._call_history.clear()
            self._api_call_count.clear()
            self._phase_duration.clear()

            self._logger.info("LifecycleController reset")

    def _validate_phase_transition(
        self, old_phase: Optional[LifecyclePhase], new_phase: LifecyclePhase
    ) -> None:
        """验证生命周期阶段转换的合法性

        Args:
            old_phase: 当前阶段
            new_phase: 目标阶段

        Raises:
            PTradeLifecycleError: 如果转换不合法
        """
        # 允许的转换规则
        allowed_transitions = {
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
                LifecyclePhase.HANDLE_DATA,  # 可重复执行
                LifecyclePhase.TICK_DATA,
                LifecyclePhase.AFTER_TRADING_END,
                LifecyclePhase.ON_ORDER_RESPONSE,
                LifecyclePhase.ON_TRADE_RESPONSE,
            ],
            LifecyclePhase.TICK_DATA: [
                LifecyclePhase.TICK_DATA,  # 可重复执行
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
                LifecyclePhase.BEFORE_TRADING_START,  # 下一个交易日
                LifecyclePhase.INITIALIZE,  # 重新初始化
            ],
        }

        allowed = allowed_transitions.get(old_phase, [])
        if new_phase not in allowed:
            raise PTradeLifecycleError(
                f"Invalid phase transition: {old_phase} -> {new_phase}. "
                f"Allowed transitions: {allowed}"
            )

    def _execute_phase_callbacks(self, phase: LifecyclePhase) -> None:
        """执行阶段切换回调函数

        Args:
            phase: 当前阶段
        """
        callbacks = self._phase_callbacks.get(phase, [])
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                self._logger.error(f"Phase callback error for {phase}: {e}")


# 全局生命周期控制器实例
_global_controller: Optional[LifecycleController] = None


def get_lifecycle_controller() -> LifecycleController:
    """获取全局生命周期控制器实例"""
    global _global_controller
    if _global_controller is None:
        _global_controller = LifecycleController()
    return _global_controller


def set_global_lifecycle_controller(controller: LifecycleController) -> None:
    """设置全局生命周期控制器实例"""
    global _global_controller
    _global_controller = controller


def validate_api_call(api_name: str) -> LifecycleValidationResult:
    """便捷函数：验证API调用"""
    return get_lifecycle_controller().validate_api_call(api_name)


def record_api_call(api_name: str, success: bool, **kwargs) -> None:
    """便捷函数：记录API调用"""
    return get_lifecycle_controller().record_api_call(api_name, success, **kwargs)


def get_current_phase() -> Optional[str]:
    """便捷函数：获取当前生命周期阶段"""
    return get_lifecycle_controller().current_phase_name
