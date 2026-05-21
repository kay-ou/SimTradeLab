# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
策略静态验证器 - 在运行前检查生命周期错误和券商 Python 版本兼容性
"""


from __future__ import annotations

import ast
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.ptrade.lifecycle_config import API_LIFECYCLE_RESTRICTIONS
from simtradelab.ptrade.broker_profile import normalize_broker_profile
from simtradelab.utils.py35_compat_checker import check_python35_compatibility

# 仅支持 Python 3.5 的券商（需检查 3.6+ 特性兼容性）
_BROKER_PY35 = frozenset(["guosheng", "dongguan"])


class StrategyValidator:
    """策略静态验证器"""

    PHASE_FUNCTION_MAP = {
        'initialize': LifecyclePhase.INITIALIZE,
        'before_trading_start': LifecyclePhase.BEFORE_TRADING_START,
        'handle_data': LifecyclePhase.HANDLE_DATA,
        'after_trading_end': LifecyclePhase.AFTER_TRADING_END,
    }

    def __init__(self, strategy_code: str, broker_profile: str = "auto"):
        """初始化验证器

        Args:
            strategy_code: 策略源代码
            broker_profile: 券商API口径
        """
        self.strategy_code = strategy_code
        self.tree = None
        self.errors: list[str] = []
        self._check_py35 = normalize_broker_profile(broker_profile) in _BROKER_PY35

        try:
            self.tree = ast.parse(strategy_code)
        except SyntaxError as e:
            self.errors.append(f"语法错误: 行 {e.lineno} - {e.msg}")
        except Exception as e:
            self.errors.append(f"解析失败: {str(e)}")

    def validate(self) -> bool:
        """验证策略"""
        if self.tree is None:
            return False

        phase_api_calls = self._extract_api_calls()

        for phase, api_calls in phase_api_calls.items():
            for api_name, lineno in api_calls:
                if api_name in API_LIFECYCLE_RESTRICTIONS:
                    allowed_phase_names = API_LIFECYCLE_RESTRICTIONS[api_name]

                    if "all" in allowed_phase_names:
                        continue

                    if phase.value not in allowed_phase_names:
                        self.errors.append(
                            f"行 {lineno}: API '{api_name}' 不能在 '{phase.value}' 阶段调用。"
                            f"允许的阶段: {allowed_phase_names}"
                        )

        if self._check_py35:
            _compat, compat_errors = check_python35_compatibility(self.strategy_code)
            self.errors.extend(compat_errors)

        return len(self.errors) == 0

    def _extract_api_calls(self) -> dict[LifecyclePhase, list[tuple]]:
        """提取每个阶段函数中的API调用

        Returns:
            {phase: [(api_name, lineno), ...]}
        """
        result = {}

        if self.tree is None:
            return result

        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in self.PHASE_FUNCTION_MAP:
                    phase = self.PHASE_FUNCTION_MAP[node.name]
                    api_calls = []

                    # 遍历函数体查找函数调用
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            # 提取函数名
                            func_name = self._get_function_name(child.func)
                            if func_name:
                                api_calls.append((func_name, child.lineno))

                    result[phase] = api_calls

        return result

    def _get_function_name(self, node) -> str:
        """获取函数名"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""

    def get_errors(self) -> list[str]:
        """获取验证错误列表"""
        return self.errors


def validate_strategy_file(strategy_path: str, broker_profile: str = "auto") -> tuple:
    """验证策略文件

    Args:
        strategy_path: 策略文件路径
        broker_profile: 券商API口径（guosheng/dongguan 会禁用 f-string）

    Returns:
        (是否通过, 错误列表, None)
    """
    try:
        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy_code = f.read()
    except FileNotFoundError:
        return False, [f"文件不存在: {strategy_path}"], None
    except PermissionError:
        return False, [f"无权限读取文件: {strategy_path}"], None
    except Exception as e:
        return False, [f"读取文件失败: {str(e)}"], None

    validator = StrategyValidator(strategy_code, broker_profile=broker_profile)
    is_valid = validator.validate()

    return is_valid, validator.get_errors(), None
