# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
PTrade API 生命周期限制配置

基于PTrade官方各生命周期函数文档中"可调用接口"列表定义，
而非PTrade_API_Summary.md的粗粒度 {all} 标注（该标注不区分initialize）。
"""


from __future__ import annotations

# 执行阶段（不含initialize和回调）
_EXEC = ["before_trading_start", "handle_data", "after_trading_end", "tick_data"]
# 两个主推回调
_CB = ["on_order_response", "on_trade_response"]
# 执行阶段 + 主推回调（账户/持仓查询类函数在回调中也需要）
_EXEC_CB = _EXEC + _CB

# PTrade API 生命周期限制配置
# initialize可调用接口来自官方文档"可调用接口"章节，其余函数限于执行阶段
API_LIFECYCLE_RESTRICTIONS: dict[str, list[str]] = {
    # ==========================================
    # 设置函数 - 仅限initialize
    # ==========================================
    "set_benchmark": ["initialize"],
    "set_commission": ["initialize"],
    "set_fixed_slippage": ["initialize"],
    "set_slippage": ["initialize"],
    "set_volume_ratio": ["initialize"],
    "set_limit_mode": ["initialize"],
    "run_daily": ["initialize"],
    "run_interval": ["initialize"],
    # 设置函数 - initialize + before_trading_start
    "set_universe": ["initialize", "before_trading_start", "tick_data"],
    "set_parameters": ["initialize", "before_trading_start", "handle_data", "after_trading_end", "tick_data",
                       "on_order_response", "on_trade_response"],
    "set_yesterday_position": ["initialize", "before_trading_start"],
    "set_future_commission": ["initialize", "before_trading_start"],
    "set_margin_rate": ["initialize", "before_trading_start"],
    # ==========================================
    # 交易函数
    # ==========================================
    "order": ["handle_data", "tick_data"] + _CB,
    "order_target": ["handle_data", "tick_data"] + _CB,
    "order_value": ["handle_data", "tick_data"] + _CB,
    "order_target_value": ["handle_data", "tick_data"] + _CB,
    "order_market": ["handle_data", "tick_data"] + _CB,
    "ipo_stocks_order": ["before_trading_start", "handle_data", "tick_data"] + _CB,
    "after_trading_order": ["handle_data", "after_trading_end", "tick_data"] + _CB,
    "after_trading_cancel_order": ["handle_data", "after_trading_end", "tick_data"] + _CB,
    "etf_basket_order": ["handle_data", "tick_data"] + _CB,
    "etf_purchase_redemption": ["handle_data", "tick_data"] + _CB,
    "order_tick": ["tick_data"],
    "cancel_order": ["handle_data", "tick_data"] + _CB,
    "cancel_order_ex": ["handle_data", "tick_data", "on_order_response"],
    "debt_to_stock_order": ["handle_data", "tick_data"],
    # 账户/持仓查询 - 执行阶段 + 回调
    "get_positions": _EXEC_CB,
    "get_open_orders": _EXEC_CB,
    "get_order": _EXEC_CB,
    "get_orders": _EXEC_CB,
    "get_all_orders": _EXEC_CB,
    "get_trades": _EXEC_CB,
    "get_position": _EXEC_CB,
    # ==========================================
    # 融资融券
    # ==========================================
    "margin_trade": ["handle_data", "tick_data"] + _CB,
    "margincash_open": ["handle_data", "tick_data"] + _CB,
    "margincash_close": ["handle_data", "tick_data"] + _CB,
    "margincash_direct_refund": ["handle_data", "after_trading_end", "tick_data"] + _CB,
    "marginsec_open": ["handle_data", "tick_data"] + _CB,
    "marginsec_close": ["handle_data", "tick_data"] + _CB,
    "marginsec_direct_refund": ["handle_data", "after_trading_end", "tick_data"] + _CB,
    "get_margincash_stocks": _EXEC,
    "get_marginsec_stocks": _EXEC,
    "get_margin_contract": _EXEC,
    "get_margin_contractreal": ["handle_data", "tick_data"],
    "get_margin_assert": _EXEC,
    "get_assure_security_list": _EXEC,
    "get_margincash_open_amount": ["handle_data", "tick_data"],
    "get_margincash_close_amount": ["handle_data", "tick_data"],
    "get_marginsec_open_amount": ["handle_data", "tick_data"],
    "get_marginsec_close_amount": ["handle_data", "tick_data"],
    "get_margin_entrans_amount": ["handle_data", "tick_data"],
    "get_enslo_security_info": _EXEC_CB,
    # ==========================================
    # 期货
    # ==========================================
    "buy_open": ["handle_data", "tick_data"],
    "sell_close": ["handle_data", "tick_data"],
    "sell_open": ["handle_data", "tick_data"],
    "buy_close": ["handle_data", "tick_data"],
    "get_margin_rate": ["all"],   # initialize文档列出：get_margin_rate(回测(期货))
    "get_instruments": _EXEC_CB,
    # ==========================================
    # 期权
    # ==========================================
    "open_prepared": ["handle_data", "tick_data"],
    "close_prepared": ["handle_data", "tick_data"],
    "option_exercise": ["handle_data", "after_trading_end"],
    "option_covered_lock": ["handle_data", "tick_data"],
    "option_covered_unlock": ["handle_data", "tick_data"],
    "get_opt_objects": _EXEC,
    "get_opt_last_dates": _EXEC,
    "get_opt_contracts": _EXEC_CB,
    "get_contract_info": _EXEC_CB,
    "get_covered_lock_amount": ["handle_data", "tick_data"],
    "get_covered_unlock_amount": ["handle_data", "tick_data"],
    # ==========================================
    # 日期/交易日 - initialize文档列出
    # ==========================================
    "get_trading_day": ["all"],
    "get_all_trades_days": ["all"],
    "get_trade_days": ["all"],
    # ==========================================
    # 行情/数据查询 - 不含initialize
    # ==========================================
    "get_market_list": _EXEC,
    "get_market_detail": _EXEC,
    "get_cb_list": _EXEC_CB,
    "get_history": _EXEC,
    "get_price": _EXEC,
    "get_individual_entrust": ["before_trading_start", "handle_data", "after_trading_end", "tick_data"],
    "get_individual_transaction": ["before_trading_start", "handle_data", "after_trading_end", "tick_data"],
    "get_tick_direction": ["handle_data", "after_trading_end", "tick_data"],
    "get_sort_msg": ["before_trading_start", "handle_data", "after_trading_end", "tick_data"],
    "get_etf_info": _EXEC,
    "get_etf_stock_info": _EXEC,
    "get_gear_price": ["handle_data", "tick_data"],
    "get_snapshot": ["handle_data", "tick_data"],
    "get_cb_info": _EXEC_CB,
    # 股票信息
    "get_stock_name": _EXEC,
    "get_stock_info": _EXEC,
    "get_stock_status": _EXEC,
    "get_stock_exrights": _EXEC,
    "get_stock_blocks": _EXEC,
    "get_index_stocks": _EXEC,
    "get_etf_stock_list": _EXEC,
    "get_industry_stocks": _EXEC,
    "get_fundamentals": _EXEC,
    "get_Ashares": _EXEC,
    "get_etf_list": _EXEC,
    "get_ipo_stocks": ["before_trading_start", "handle_data", "tick_data"],
    # 其他信息
    "get_trades_file": ["after_trading_end"],
    "convert_position_from_csv": ["initialize", "before_trading_start", "handle_data"],
    "get_user_name": ["all"],     # initialize文档列出
    "get_deliver": ["before_trading_start", "after_trading_end"],
    "get_fundjour": ["before_trading_start", "after_trading_end"],
    "get_research_path": ["initialize", "before_trading_start", "handle_data", "after_trading_end", "tick_data"],
    "get_trade_name": _EXEC,
    # ==========================================
    # 技术指标 - 不含initialize
    # ==========================================
    "get_MACD": _EXEC,
    "get_KDJ": _EXEC,
    "get_RSI": _EXEC,
    "get_CCI": _EXEC,
    # ==========================================
    # 其他
    # ==========================================
    "log": ["all"],               # 日志，全阶段可用
    "is_trade": ["all"],          # initialize文档列出
    "check_limit": _EXEC,
    "send_email": ["after_trading_end", "tick_data", "on_order_response", "on_trade_response"],
    "send_qywx": ["after_trading_end", "tick_data", "on_order_response", "on_trade_response"],
    "permission_test": ["initialize", "before_trading_start", "after_trading_end"],
    "create_dir": ["initialize", "before_trading_start", "handle_data", "after_trading_end", "tick_data"],
}

# 生命周期阶段定义
LIFECYCLE_PHASES = [
    "initialize",
    "before_trading_start",
    "handle_data",
    "after_trading_end",
    "tick_data",
    "on_order_response",
    "on_trade_response",
]

# 预计算: API name -> frozenset of allowed phases (供装饰器 O(1) 查找)
_ALL_PHASES_FROZENSET = frozenset(LIFECYCLE_PHASES)
API_ALLOWED_PHASES_LOOKUP: dict[str, frozenset[str]] = {}
for _api, _phases in API_LIFECYCLE_RESTRICTIONS.items():
    if _phases == ["all"]:
        API_ALLOWED_PHASES_LOOKUP[_api] = _ALL_PHASES_FROZENSET
    else:
        API_ALLOWED_PHASES_LOOKUP[_api] = frozenset(_phases)
