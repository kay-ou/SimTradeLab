# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
f-string自动修复工具

将Python 3.6+的f-string转换为Python 3.5兼容的.format()调用
"""


import ast

try:
    import astor
except ImportError:
    astor = None


class FStringFixer(ast.NodeTransformer):
    """f-string转换为.format()的AST转换器"""

    def visit_JoinedStr(self, node):
        """将f-string节点转换为.format()调用"""
        parts = []
        format_args = []

        for value in node.values:
            if isinstance(value, ast.Str):
                # 普通字符串片段
                parts.append(value.s)
            elif isinstance(value, ast.FormattedValue):
                # f-string中的表达式
                if isinstance(value.value, ast.Name):
                    # 简单变量名
                    var_name = value.value.id
                    parts.append("{" + var_name + "}")
                    format_args.append(ast.keyword(arg=var_name, value=value.value))
                else:
                    # 复杂表达式
                    if astor is None:
                        raise RuntimeError("需要安装astor库来修复f-string: pip install astor")
                    expr_src = astor.to_source(value.value).strip()
                    placeholder = "{" + expr_src + "}"
                    parts.append(placeholder)
                    format_args.append(ast.keyword(arg=expr_src, value=value.value))

        # 构造 "字符串".format() 调用
        new_str = ast.Str("".join(parts))
        new_node = ast.Call(
            func=ast.Attribute(value=new_str, attr="format", ctx=ast.Load()),
            args=[],
            keywords=format_args
        )
        return ast.copy_location(new_node, node)


def fix_fstring_in_code(code):
    """修复代码中的f-string

    Args:
        code: Python源代码字符串

    Returns:
        修复后的代码

    Raises:
        RuntimeError: 如果未安装astor库
        SyntaxError: 如果代码有语法错误
    """
    if astor is None:
        raise RuntimeError("需要安装astor库: pip install astor")

    tree = ast.parse(code)
    fixer = FStringFixer()
    new_tree = fixer.visit(tree)
    ast.fix_missing_locations(new_tree)

    return astor.to_source(new_tree)


def fix_fstring_in_file(filepath):
    """修复文件中的f-string

    Args:
        filepath: Python文件路径

    Returns:
        tuple: (是否成功, 修复后的代码或错误信息)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        return False, "读取文件失败: {}".format(str(e))

    try:
        fixed_code = fix_fstring_in_code(code)
        return True, fixed_code
    except Exception as e:
        return False, "修复失败: {}".format(str(e))
