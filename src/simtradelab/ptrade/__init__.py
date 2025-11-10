# -*- coding: utf-8 -*-
"""
PTrade 模块 - 融合 backtest 和 ptrade 的优势

核心功能：
1. 三环境支持 (Research/Backtest/Trading)
2. 生命周期验证 (initialize/handle_data/...)
3. 在 backtest.PtradeAPI 基础上添加模式和生命周期检查

使用方式：
    from simtradelab.backtest.ptrade_api import PtradeAPI
    from simtradelab.ptrade import EnhancedPTradeAPI, PTradeMode

    # 创建底层API（使用backtest的完整实现）
    base_api = PtradeAPI(...)

    # 创建增强API（添加验证）
    api = EnhancedPTradeAPI(base_api, mode=PTradeMode.BACKTEST)

    # 使用
    api.set_phase("initialize")
    api.set_universe(["000001.XSHE"])
"""

# 新的简洁接口
from .mode import PTradeMode, get_mode_description
from .enhanced_api import EnhancedPTradeAPI
from .restrictions import (
    is_api_supported_in_mode,
    is_api_allowed_in_phase,
    ModeNotSupportedError,
    PhaseNotAllowedError,
    LIFECYCLE_PHASES,
)

# 保留旧接口以兼容现有代码
from .context import PTradeContext
from .adapter import PTradeAdapter

__all__ = [
    # === 新接口（推荐使用） ===
    "PTradeMode",
    "EnhancedPTradeAPI",
    "get_mode_description",
    "is_api_supported_in_mode",
    "is_api_allowed_in_phase",
    "ModeNotSupportedError",
    "PhaseNotAllowedError",
    "LIFECYCLE_PHASES",

    # === 旧接口（向后兼容） ===
    "PTradeAdapter",
    "PTradeContext",
]
