# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
Python 3.5兼容性检查工具

检查代码是否使用了Python 3.6+的特性，确保代码兼容Python 3.5
支持自动修复f-string等兼容性问题
"""


from __future__ import annotations

import ast
import re


class Python35CompatChecker:
    """Python 3.5兼容性检查器

    检查代码是否使用了超过Python 3.5的特性
    """

    # Python 3.6+特性列表（在3.5中不可用）
    PY36_PLUS_FEATURES = {
        'f-string': 'f-string是Python 3.6+特性，请使用.format()',
        'variable_annotations': '变量类型注解(x: int = 1)是Python 3.6+特性',
        'async_generators': 'async生成器是Python 3.6+特性',
        'async_comprehensions': 'async推导式是Python 3.6+特性',
        'underscores_in_numeric_literals': '数字字面量中的下划线(1_000)是Python 3.6+特性',
    }

    # Python 3.7+特性
    PY37_PLUS_FEATURES = {
        'dataclasses': '@dataclass装饰器是Python 3.7+特性',
        'async_keyword': 'async和await作为保留关键字是Python 3.7+特性',
        'postponed_annotations': '延迟注解求值是Python 3.7+特性',
    }

    # Python 3.8+特性
    PY38_PLUS_FEATURES = {
        'walrus_operator': '海象运算符(:=)是Python 3.8+特性',
        'positional_only': '仅位置参数(/)是Python 3.8+特性',
    }

    # 禁用的模块列表
    FORBIDDEN_MODULES = {
        'io': 'io模块在backtest中不可用',
        'sys': 'sys模块在backtest中不可用',
    }

    def __init__(self, code: str):
        """初始化检查器

        Args:
            code: Python源代码字符串
        """
        self.code = code
        self.tree = None
        self.errors = []

        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            self.errors.append("语法错误: 行 {} - {}".format(e.lineno, e.msg))
        except Exception as e:
            self.errors.append("解析失败: {}".format(str(e)))

    def check(self) -> tuple[bool, list[str]]:
        """执行兼容性检查

        Returns:
            (是否兼容, 错误列表)
        """
        if self.tree is None:
            return False, self.errors

        # 清空之前的错误
        self.errors = []

        # 执行各项检查
        self._check_forbidden_imports()
        self._check_fstring_usage()
        self._check_ast_features()

        return len(self.errors) == 0, self.errors

    def _check_forbidden_imports(self):
        """检查禁用的模块导入"""
        if self.tree is None:
            return

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.FORBIDDEN_MODULES:
                        self.errors.append(
                            "行 {}: {}".format(
                                node.lineno,
                                self.FORBIDDEN_MODULES[alias.name]
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.FORBIDDEN_MODULES:
                    self.errors.append(
                        "行 {}: {}".format(
                            node.lineno,
                            self.FORBIDDEN_MODULES[node.module]
                        )
                    )

    def _check_fstring_usage(self):
        """检查f-string使用（Python 3.6+）"""
        lines = self.code.split('\n')
        for lineno, line in enumerate(lines, 1):
            # 跳过注释行
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            # 检查f-string: f"..." 或 f'...'
            if re.search(r'\bf["\']', line):
                self.errors.append(
                    "行 {}: {}".format(lineno, self.PY36_PLUS_FEATURES['f-string'])
                )

    def _check_ast_features(self):
        """检查AST中的Python 3.6+特性"""
        if self.tree is None:
            return

        for node in ast.walk(self.tree):
            # 检查变量类型注解 (PEP 526, Python 3.6+)
            if isinstance(node, ast.AnnAssign):
                self.errors.append(
                    "行 {}: {}".format(node.lineno, self.PY36_PLUS_FEATURES['variable_annotations'])
                )

            # 检查JoinedStr节点（f-string的AST表示，Python 3.6+）
            if isinstance(node, ast.JoinedStr):
                self.errors.append(
                    "行 {}: {}".format(node.lineno, self.PY36_PLUS_FEATURES['f-string'])
                )

            # 检查async生成器 (Python 3.6+)
            if isinstance(node, ast.AsyncFunctionDef):
                for child in ast.walk(node):
                    if isinstance(child, (ast.Yield, ast.YieldFrom)):
                        self.errors.append(
                            "行 {}: {}".format(node.lineno, self.PY36_PLUS_FEATURES['async_generators'])
                        )
                        break

            # 检查async推导式 (Python 3.6+)
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for generator in node.generators:
                    if isinstance(generator, ast.comprehension) and generator.is_async:
                        self.errors.append(
                            "行 {}: {}".format(node.lineno, self.PY36_PLUS_FEATURES['async_comprehensions'])
                        )

            # 检查数字字面量中的下划线 (Python 3.6+)
            # 使用Constant而不是已弃用的Num
            if isinstance(node, (ast.Num, ast.Constant)):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    lines = self.code.split('\n')
                    if node.lineno <= len(lines):
                        line = lines[node.lineno - 1]
                        if re.search(r'\b\d+_\d+\b', line):
                            self.errors.append(
                                "行 {}: {}".format(
                                    node.lineno,
                                    self.PY36_PLUS_FEATURES['underscores_in_numeric_literals']
                                )
                            )

            # 检查海象运算符 := (Python 3.8+)
            if hasattr(ast, 'NamedExpr') and isinstance(node, ast.NamedExpr):
                self.errors.append(
                    "行 {}: {}".format(node.lineno, self.PY38_PLUS_FEATURES['walrus_operator'])
                )

            # 检查仅位置参数 / (Python 3.8+)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node.args, 'posonlyargs') and node.args.posonlyargs:
                    self.errors.append(
                        "行 {}: {}".format(node.lineno, self.PY38_PLUS_FEATURES['positional_only'])
                    )


def check_python35_compatibility(code: str) -> Tuple[bool, List[str]]:
    """检查代码是否兼容Python 3.5

    Args:
        code: Python源代码字符串

    Returns:
        (是否兼容, 错误列表)
    """
    checker = Python35CompatChecker(code)
    return checker.check()


def check_file_python35_compatibility(filepath: str) -> Tuple[bool, List[str]]:
    """检查文件是否兼容Python 3.5

    Args:
        filepath: Python文件路径

    Returns:
        (是否兼容, 错误列表)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    except FileNotFoundError:
        return False, ["文件不存在: {}".format(filepath)]
    except PermissionError:
        return False, ["无权限读取文件: {}".format(filepath)]
    except Exception as e:
        return False, ["读取文件失败: {}".format(str(e))]

    return check_python35_compatibility(code)


def check_and_fix_file(filepath: str, auto_fix: bool = True) -> Tuple[bool, List[str], str]:
    """检查并自动修复文件的Python 3.5兼容性问题

    Args:
        filepath: Python文件路径
        auto_fix: 是否自动修复f-string问题

    Returns:
        (是否兼容, 错误列表, 修复后的代码或空字符串)
    """
    # 先检查
    is_compatible, errors = check_file_python35_compatibility(filepath)

    if is_compatible:
        return True, [], ""

    # 检查是否有f-string错误
    has_fstring_error = any('f-string' in error for error in errors)

    if not has_fstring_error or not auto_fix:
        return False, errors, ""

    # 自动修复f-string
    try:
        from simtradelab.utils.fstring_fixer import fix_fstring_in_file
        success, result = fix_fstring_in_file(filepath)
    except ImportError as e:
        errors.append("导入f-string修复工具失败: {}".format(str(e)))
        return False, errors, ""

    if not success:
        errors.append("自动修复f-string失败: {}".format(result))
        return False, errors, ""

    # 检查修复后的代码
    fixed_is_compatible, fixed_errors = check_python35_compatibility(result)

    return fixed_is_compatible, fixed_errors, result

