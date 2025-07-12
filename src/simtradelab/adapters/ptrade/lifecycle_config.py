# -*- coding: utf-8 -*-
"""
PTrade API 生命周期限制配置

根据PTrade_API_Summary.md官方文档定义每个API函数的生命周期使用限制
"""

from typing import Dict, List

# PTrade API 生命周期限制配置
# 基于PTrade_API_Summary.md中的完整API限制规范
API_LIFECYCLE_RESTRICTIONS: Dict[str, List[str]] = {
    # ==========================================
    # 策略生命周期函数 (7个) - 框架级实现
    # ==========================================
    # 这些是框架函数，不是被调用的API
    # ==========================================
    # 设置函数 (12个) - 全部仅限initialize
    # ==========================================
    "set_universe": ["initialize"],
    "set_benchmark": ["initialize"],
    "set_commission": ["initialize"],
    "set_fixed_slippage": ["initialize"],
    "set_slippage": ["initialize"],
    "set_volume_ratio": ["initialize"],
    "set_limit_mode": ["initialize"],
    "set_yesterday_position": ["initialize"],
    "set_parameters": ["initialize"],
    "run_daily": ["initialize"],
    "run_interval": ["initialize"],
    "set_future_commission": ["initialize"],
    "set_margin_rate": ["initialize"],
    # ==========================================
    # 交易相关函数 - 分不同使用场景
    # ==========================================
    # 股票交易函数 (11个)
    "order": ["handle_data", "tick_data"],
    "order_target": ["handle_data", "tick_data"],
    "order_value": ["handle_data", "tick_data"],
    "order_target_value": ["handle_data", "tick_data"],
    "order_market": ["handle_data", "tick_data"],
    "ipo_stocks_order": ["before_trading_start"],
    "after_trading_order": ["after_trading_end"],
    "after_trading_cancel_order": ["after_trading_end"],
    "etf_basket_order": ["handle_data", "tick_data"],
    "etf_purchase_redemption": ["handle_data", "tick_data"],
    "get_positions": ["all"],
    # 公共交易函数 (11个)
    "order_tick": ["tick_data"],
    "cancel_order": ["handle_data", "tick_data", "on_order_response"],
    "cancel_order_ex": ["handle_data", "tick_data", "on_order_response"],
    "debt_to_stock_order": ["handle_data", "tick_data"],
    "get_open_orders": ["all"],
    "get_order": ["all"],
    "get_orders": ["all"],
    "get_all_orders": ["all"],
    "get_trades": ["all"],
    "get_position": ["all"],
    # 融资融券交易函数 (7个)
    "margin_trade": ["handle_data", "tick_data"],
    "margincash_open": ["handle_data", "tick_data"],
    "margincash_close": ["handle_data", "tick_data"],
    "margincash_direct_refund": ["handle_data", "after_trading_end"],
    "marginsec_open": ["handle_data", "tick_data"],
    "marginsec_close": ["handle_data", "tick_data"],
    "marginsec_direct_refund": ["handle_data", "after_trading_end"],
    # 融资融券查询函数 (12个)
    "get_margincash_stocks": ["all"],
    "get_marginsec_stocks": ["all"],
    "get_margin_contract": ["all"],
    "get_margin_contractreal": ["handle_data", "tick_data"],
    "get_margin_assert": ["all"],
    "get_assure_security_list": ["all"],
    "get_margincash_open_amount": ["handle_data", "tick_data"],
    "get_margincash_close_amount": ["handle_data", "tick_data"],
    "get_marginsec_open_amount": ["handle_data", "tick_data"],
    "get_marginsec_close_amount": ["handle_data", "tick_data"],
    "get_margin_entrans_amount": ["handle_data", "tick_data"],
    "get_enslo_security_info": ["all"],
    # 期货交易函数 (4个)
    "buy_open": ["handle_data", "tick_data"],
    "sell_close": ["handle_data", "tick_data"],
    "sell_open": ["handle_data", "tick_data"],
    "buy_close": ["handle_data", "tick_data"],
    # 期货查询函数 (3个)
    "get_margin_rate": ["all"],
    "get_instruments": ["all"],
    # 期权交易函数 (9个)
    "open_prepared": ["handle_data", "tick_data"],
    "close_prepared": ["handle_data", "tick_data"],
    "option_exercise": ["handle_data", "after_trading_end"],
    "option_covered_lock": ["handle_data", "tick_data"],
    "option_covered_unlock": ["handle_data", "tick_data"],
    # 注意：期权的buy_open等与期货同名，在具体实现中需要区分上下文
    # 期权查询函数 (6个)
    "get_opt_objects": ["all"],
    "get_opt_last_dates": ["all"],
    "get_opt_contracts": ["all"],
    "get_contract_info": ["all"],
    "get_covered_lock_amount": ["handle_data", "tick_data"],
    "get_covered_unlock_amount": ["handle_data", "tick_data"],
    # ==========================================
    # 获取信息函数 (73个) - 大部分为通用
    # ==========================================
    # 基础信息 (3个) - 全部通用
    "get_trading_day": ["all"],
    "get_all_trades_days": ["all"],
    "get_trade_days": ["all"],
    # 市场信息 (3个) - 全部通用
    "get_market_list": ["all"],
    "get_market_detail": ["all"],
    "get_cb_list": ["all"],
    # 行情信息 (11个) - 混合限制
    "get_history": ["all"],
    "get_price": ["all"],
    "get_individual_entrust": ["tick_data"],
    "get_individual_transaction": ["tick_data"],
    "get_tick_direction": ["tick_data"],
    "get_sort_msg": ["handle_data", "before_trading_start", "after_trading_end"],
    "get_etf_info": ["all"],
    "get_etf_stock_info": ["all"],
    "get_gear_price": ["handle_data", "tick_data"],
    "get_snapshot": ["handle_data", "tick_data"],
    "get_cb_info": ["all"],
    # 股票信息 (12个) - 大部分通用
    "get_stock_name": ["all"],
    "get_stock_info": ["all"],
    "get_stock_status": ["all"],
    "get_stock_exrights": ["all"],
    "get_stock_blocks": ["all"],
    "get_index_stocks": ["all"],
    "get_etf_stock_list": ["all"],
    "get_industry_stocks": ["all"],
    "get_fundamentals": ["all"],
    "get_Ashares": ["all"],
    "get_etf_list": ["all"],
    "get_ipo_stocks": ["before_trading_start", "handle_data"],
    # 其他信息 (8个) - 混合限制
    "get_trades_file": ["after_trading_end"],
    "convert_position_from_csv": ["initialize"],
    "get_user_name": ["all"],
    "get_deliver": ["after_trading_end"],
    "get_fundjour": ["after_trading_end"],
    "get_research_path": ["initialize"],
    "get_trade_name": ["all"],
    # ==========================================
    # 计算函数 (4个) - 全部通用
    # ==========================================
    "get_MACD": ["all"],
    "get_KDJ": ["all"],
    "get_RSI": ["all"],
    "get_CCI": ["all"],
    # ==========================================
    # 其他函数 (7个) - 混合限制
    # ==========================================
    "log": ["all"],  # 日志记录的所有级别
    "is_trade": ["all"],
    "check_limit": ["all"],
    "send_email": ["after_trading_end", "on_order_response", "on_trade_response"],
    "send_qywx": ["after_trading_end", "on_order_response", "on_trade_response"],
    "permission_test": ["initialize"],
    "create_dir": ["initialize"],
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

# 特殊标记：可在所有阶段调用的API
ALL_PHASES_APIS = {
    api for api, phases in API_LIFECYCLE_RESTRICTIONS.items() if phases == ["all"]
}


def get_api_allowed_phases(api_name: str) -> List[str]:
    """获取API允许调用的生命周期阶段"""
    phases = API_LIFECYCLE_RESTRICTIONS.get(api_name, ["all"])
    if phases == ["all"]:
        return LIFECYCLE_PHASES.copy()
    return phases


def is_api_allowed_in_phase(api_name: str, current_phase: str) -> bool:
    """检查API是否可在指定生命周期阶段调用"""
    allowed_phases = get_api_allowed_phases(api_name)
    return current_phase in allowed_phases


def get_phase_apis(phase: str) -> List[str]:
    """获取指定生命周期阶段可调用的所有API"""
    phase_apis = []
    for api_name, allowed_phases in API_LIFECYCLE_RESTRICTIONS.items():
        if allowed_phases == ["all"] or phase in allowed_phases:
            phase_apis.append(api_name)
    return phase_apis


# 按阶段分组的API统计
PHASE_API_COUNT = {phase: len(get_phase_apis(phase)) for phase in LIFECYCLE_PHASES}

# 专用API统计（仅在该阶段可调用的API）
EXCLUSIVE_PHASE_APIS = {
    phase: [
        api for api, phases in API_LIFECYCLE_RESTRICTIONS.items() if phases == [phase]
    ]
    for phase in LIFECYCLE_PHASES
}


# 验证配置完整性
def validate_config():
    """验证配置的完整性和正确性"""
    errors = []

    # 检查是否有未定义的阶段
    for api_name, phases in API_LIFECYCLE_RESTRICTIONS.items():
        for phase in phases:
            if phase != "all" and phase not in LIFECYCLE_PHASES:
                errors.append(f"API '{api_name}' references undefined phase '{phase}'")

    # 检查重要API是否已配置
    critical_apis = [
        "order",
        "cancel_order",
        "get_price",
        "get_history",
        "set_universe",
        "set_commission",
    ]

    for api in critical_apis:
        if api not in API_LIFECYCLE_RESTRICTIONS:
            errors.append(f"Critical API '{api}' not configured")

    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")

    return True


# 在模块加载时验证配置
validate_config()
