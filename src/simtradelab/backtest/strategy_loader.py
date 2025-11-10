# -*- coding: utf-8 -*-
"""
策略加载器
"""

from typing import Dict, Any
import logging

from simtradelab.ptrade.context import Context
from simtradelab.ptrade.object import Global
from simtradelab.ptrade.api import PtradeAPI


class StrategyLoader:
    """策略文件加载和环境构建"""

    def __init__(
        self,
        strategy_path: str,
        g: Global,
        log: logging.Logger,
        context: Context,
        api: PtradeAPI
    ):
        self.strategy_path = strategy_path
        self.g = g
        self.log = log
        self.context = context
        self.api = api

    def load(self) -> Dict[str, Any]:
        """加载策略并构建命名空间

        Returns:
            包含策略函数的命名空间字典
        """
        # 读取策略代码
        with open(self.strategy_path, 'r', encoding='utf-8') as f:
            strategy_code = f.read()

        # 构建基础命名空间
        strategy_namespace = {
            '__name__': '__main__',
            '__file__': self.strategy_path,
            'g': self.g,
            'log': self.log,
            'context': self.context,
        }

        # 注入API方法
        for attr_name in dir(self.api):
            if not attr_name.startswith('_'):
                attr = getattr(self.api, attr_name)
                if callable(attr) or attr_name == 'FUNDAMENTAL_TABLES':
                    strategy_namespace[attr_name] = attr

        # 执行策略代码
        exec(strategy_code, strategy_namespace)

        return strategy_namespace
