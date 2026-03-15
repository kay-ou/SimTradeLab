# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
市场配置文件

定义不同市场（A股、美股等）的交易规则和默认参数
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketProfile:
    code: str
    name: str
    t_plus_1: bool
    has_price_limit: bool
    lot_size: int
    commission_ratio: float
    min_commission: float
    stamp_tax_rate: float
    transfer_fee_rate: float
    default_benchmark: str
    default_slippage: float
    data_dir_name: str


CN_PROFILE = MarketProfile(
    code="CN",
    name="A股",
    t_plus_1=True,
    has_price_limit=True,
    lot_size=100,
    commission_ratio=0.0003,
    min_commission=5.0,
    stamp_tax_rate=0.001,
    transfer_fee_rate=0.0000487,
    default_benchmark="000300.SS",
    default_slippage=0.001,
    data_dir_name="cn",
)

US_PROFILE = MarketProfile(
    code="US",
    name="美股",
    t_plus_1=False,
    has_price_limit=False,
    lot_size=1,
    commission_ratio=0.001,
    min_commission=0.0,
    stamp_tax_rate=0.0,
    transfer_fee_rate=0.0,
    default_benchmark="SPX.US",
    default_slippage=0.001,
    data_dir_name="us",
)

_PROFILES = {"CN": CN_PROFILE, "US": US_PROFILE}


def get_market_profile(market: str) -> MarketProfile:
    profile = _PROFILES.get(market.upper())
    if profile is None:
        raise ValueError("Unknown market: %s (available: %s)" % (market, ", ".join(_PROFILES)))
    return profile
