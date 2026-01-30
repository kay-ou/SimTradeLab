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
import yaml
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
        """加载配置文件"""
        from .paths import get_project_root

        project_root = get_project_root()
        config_path = project_root / 'config.yaml'

        if not config_path.exists():
            # 使用默认配置
            self._config = {
                'data_path': './data',
            }
            self._project_root = project_root
            return

        with open(str(config_path), 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        self._project_root = project_root

    @property
    def data_path(self):
        """数据路径（自动转换为绝对路径）"""
        path_str = self._config.get('data_path', None)

        # 如果没有配置 data_path，使用默认路径
        if path_str is None:
            path_str = './data'

        path = Path(path_str)

        # 如果是相对路径，相对于项目根目录
        if not path.is_absolute():
            path = self._project_root / path

        return str(path)


# 全局配置实例
config = Config()
