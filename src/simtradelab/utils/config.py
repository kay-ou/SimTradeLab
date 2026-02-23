# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
全局配置管理
"""

from __future__ import annotations
from pathlib import Path


class Config:
    """全局配置单例"""
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self):
        self._config = {'data_path': './data'}

    @property
    def data_path(self):
        """数据路径（自动转换为绝对路径）"""
        from .paths import get_project_root
        path = Path(self._config['data_path'])
        if not path.is_absolute():
            path = get_project_root() / path
        return str(path)


# 全局配置实例
config = Config()
