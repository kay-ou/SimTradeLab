# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
策略数据依赖分析器

通过静态分析策略代码,识别数据API调用,判断需要加载哪些数据
"""


from __future__ import annotations

import ast
from pydantic import BaseModel, Field


class DataDependencies(BaseModel):
    """策略数据依赖项"""
    needs_price_data: bool = False
    needs_valuation: bool = False
    needs_fundamentals: bool = False
    needs_exrights: bool = False

    fundamental_tables: set[str] = Field(default_factory=set)

    model_config = {"arbitrary_types_allowed": True}


class StrategyDataAnalyzer(ast.NodeVisitor):
    """策略代码AST分析器"""

    def __init__(self):
        self.dependencies = DataDependencies()
        self.api_calls: set[str] = set()
        self.fundamental_tables: set[str] = set()

    def visit_Call(self, node):
        """访问函数调用节点"""
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name:
            self.api_calls.add(func_name)

            # 特殊处理get_fundamentals,提取表名参数
            if func_name == 'get_fundamentals' and len(node.args) >= 2:
                table_arg = node.args[1]
                if isinstance(table_arg, ast.Constant) and isinstance(table_arg.value, str):
                    self.fundamental_tables.add(table_arg.value)

        self.generic_visit(node)

    def analyze(self):
        """分析API调用,转换为数据依赖"""
        # 价格数据依赖
        if any(api in self.api_calls for api in [
            'get_price', 'get_history', 'check_limit',
            'order', 'order_target', 'order_value', 'order_target_value'
        ]):
            self.dependencies.needs_price_data = True

        # 除权数据依赖(只要用get_price或get_history就加载)
        if 'get_price' in self.api_calls or 'get_history' in self.api_calls:
            self.dependencies.needs_exrights = True

        # 基本面数据
        if 'get_fundamentals' in self.api_calls:
            # 保守策略：默认加载财务数据（延迟加载，更常用）
            self.dependencies.needs_fundamentals = True
            self.dependencies.fundamental_tables = self.fundamental_tables

            # 明确使用valuation时才加载（全量预加载，占内存）
            if 'valuation' in self.fundamental_tables:
                self.dependencies.needs_valuation = True

        return self.dependencies


def analyze_strategy_data_requirements(strategy_path: str) -> DataDependencies:
    """分析策略代码,识别数据依赖

    Args:
        strategy_path: 策略文件路径

    Returns:
        DataDependencies对象
    """
    try:
        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy_code = f.read()

        tree = ast.parse(strategy_code)
        analyzer = StrategyDataAnalyzer()
        analyzer.visit(tree)
        dependencies = analyzer.analyze()

        return dependencies

    except Exception as e:
        # 分析失败时返回全量依赖
        print("策略分析失败: {}, 加载全部数据".format(e))
        return DataDependencies(
            needs_price_data=True,
            needs_valuation=True,
            needs_fundamentals=True,
            needs_exrights=True
        )


def print_dependencies(deps: DataDependencies):
    """打印数据依赖摘要"""
    items = []
    if deps.needs_price_data:
        items.append("价格")
    if deps.needs_valuation:
        items.append("估值")
    if deps.needs_fundamentals:
        tables = ','.join(deps.fundamental_tables) if deps.fundamental_tables else '全部'
        items.append("财务({})".format(tables))
    if deps.needs_exrights:
        items.append("除权")

    if items:
        print("策略数据依赖: {}".format(' | '.join(items)))
    else:
        print("策略数据依赖: 无")
