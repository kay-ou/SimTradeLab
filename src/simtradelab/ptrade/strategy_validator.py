# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
策略静态验证器 - 在运行前检查生命周期错误和Python 3.5兼容性
"""


from __future__ import annotations

import ast
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.ptrade.lifecycle_config import API_LIFECYCLE_RESTRICTIONS
from simtradelab.utils.py35_compat_checker import check_python35_compatibility


class StrategyValidator:
    """策略静态验证器"""

    # 阶段函数名映射
    PHASE_FUNCTION_MAP = {
        'initialize': LifecyclePhase.INITIALIZE,
        'before_trading_start': LifecyclePhase.BEFORE_TRADING_START,
        'handle_data': LifecyclePhase.HANDLE_DATA,
        'after_trading_end': LifecyclePhase.AFTER_TRADING_END,
    }

    def __init__(self, strategy_code: str, check_py35_compat: bool = True):
        """初始化验证器

        Args:
            strategy_code: 策略源代码
            check_py35_compat: 是否检查Python 3.5兼容性（禁止使用3.6+特性）
        """
        self.strategy_code = strategy_code
        self.tree = None
        self.errors: list[str] = []
        self.check_py35_compat = check_py35_compat

        try:
            self.tree = ast.parse(strategy_code)
        except SyntaxError as e:
            self.errors.append("语法错误: 行 {} - {}".format(e.lineno, e.msg))
        except Exception as e:
            self.errors.append("解析失败: {}".format(str(e)))

    def validate(self) -> bool:
        """验证策略

        Returns:
            是否通过验证
        """
        # 如果解析失败，直接返回
        if self.tree is None:
            return False

        # 提取每个阶段函数中调用的API
        phase_api_calls = self._extract_api_calls()

        # 验证每个API调用是否在正确的阶段
        for phase, api_calls in phase_api_calls.items():
            for api_name, lineno in api_calls:
                if api_name in API_LIFECYCLE_RESTRICTIONS:
                    allowed_phase_names = API_LIFECYCLE_RESTRICTIONS[api_name]

                    # 跳过"all"阶段的API
                    if "all" in allowed_phase_names:
                        continue

                    # 检查当前阶段是否被允许
                    if phase.value not in allowed_phase_names:
                        self.errors.append(
                            "行 {}: API '{}' 不能在 '{}' 阶段调用。"
                            "允许的阶段: {}".format(lineno, api_name, phase.value, allowed_phase_names)
                        )

        # Python 3.5兼容性检查
        if self.check_py35_compat:
            is_compat, compat_errors = check_python35_compatibility(self.strategy_code)
            if not is_compat:
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


def validate_strategy_file(strategy_path: str, check_py35_compat: bool = True, auto_fix: bool = True) -> tuple:
    """验证策略文件

    Args:
        strategy_path: 策略文件路径
        check_py35_compat: 是否检查Python 3.5兼容性
        auto_fix: 是否自动修复f-string等兼容性问题

    Returns:
        (是否通过, 错误列表, 修复后的代码或None)
    """
    try:
        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy_code = f.read()
    except FileNotFoundError:
        return False, ["文件不存在: {}".format(strategy_path)], None
    except PermissionError:
        return False, ["无权限读取文件: {}".format(strategy_path)], None
    except Exception as e:
        return False, ["读取文件失败: {}".format(str(e))], None

    # 如果需要检查兼容性且启用自动修复，先尝试修复
    fixed_code = None
    if check_py35_compat and auto_fix:
        from simtradelab.utils.py35_compat_checker import check_and_fix_file
        is_compat, errors, fixed = check_and_fix_file(strategy_path, auto_fix=True)

        if fixed:
            # 有修复内容，写回文件
            try:
                with open(strategy_path, 'w', encoding='utf-8') as f:
                    f.write(fixed)
                strategy_code = fixed
                fixed_code = fixed
            except Exception as e:
                return False, ["写入修复后的代码失败: {}".format(str(e))], None

    validator = StrategyValidator(strategy_code, check_py35_compat=check_py35_compat)
    is_valid = validator.validate()

    return is_valid, validator.get_errors(), fixed_code
