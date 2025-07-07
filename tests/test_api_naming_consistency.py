#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API命名一致性
验证所有API命名与PTrade完全一致
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import simtradelab


def test_ptrade_api_naming_consistency():
    """测试PTrade API命名一致性"""
    print("\n=== 测试PTrade API命名一致性 ===")
    
    # PTrade API文档中的所有API名称
    ptrade_apis = {
        # 设置函数
        'set_universe', 'set_benchmark', 'set_commission', 'set_fixed_slippage', 
        'set_slippage', 'set_volume_ratio', 'set_limit_mode', 'set_yesterday_position', 'set_parameters',
        
        # 定时周期性函数
        'run_daily', 'run_interval',
        
        # 获取信息函数 - 基础信息
        'get_trading_day', 'get_all_trades_days', 'get_trade_days',
        
        # 获取信息函数 - 市场信息
        'get_market_list', 'get_market_detail', 'get_cb_list',
        
        # 获取信息函数 - 行情信息
        'get_history', 'get_price', 'get_individual_entrust', 'get_individual_transaction',
        'get_tick_direction', 'get_sort_msg', 'get_etf_info', 'get_etf_stock_info',
        'get_gear_price', 'get_snapshot', 'get_cb_info',
        
        # 获取信息函数 - 股票信息
        'get_stock_name', 'get_stock_info', 'get_stock_status', 'get_stock_exrights',
        'get_stock_blocks', 'get_index_stocks', 'get_etf_stock_list', 'get_industry_stocks',
        'get_fundamentals', 'get_Ashares', 'get_etf_list', 'get_ipo_stocks',
        
        # 获取信息函数 - 其他信息
        'get_trades_file', 'convert_position_from_csv', 'get_user_name', 'get_deliver',
        'get_fundjour', 'get_research_path', 'get_trade_name',
        
        # 交易相关函数 - 股票交易函数
        'order', 'order_target', 'order_value', 'order_target_value', 'order_market',
        'ipo_stocks_order', 'after_trading_order', 'after_trading_cancel_order',
        'etf_basket_order', 'etf_purchase_redemption', 'get_positions',
        
        # 交易相关函数 - 公共交易函数
        'order_tick', 'cancel_order', 'cancel_order_ex', 'debt_to_stock_order',
        'get_open_orders', 'get_order', 'get_orders', 'get_all_orders',
        'get_trades', 'get_position',
        
        # 融资融券专用函数 - 交易类
        'margin_trade', 'margincash_open', 'margincash_close', 'margincash_direct_refund',
        'marginsec_open', 'marginsec_close', 'marginsec_direct_refund',
        
        # 融资融券专用函数 - 查询类
        'get_margincash_stocks', 'get_marginsec_stocks', 'get_margin_contract',
        'get_margin_contractreal', 'get_margin_assert', 'get_assure_security_list',
        'get_margincash_open_amount', 'get_margincash_close_amount',
        'get_marginsec_open_amount', 'get_marginsec_close_amount',
        'get_margin_entrans_amount', 'get_enslo_security_info',
        
        # 期货专用函数
        'buy_open', 'sell_close', 'sell_open', 'buy_close',
        'get_margin_rate', 'get_instruments', 'set_future_commission', 'set_margin_rate',
        
        # 期权专用函数
        'get_opt_objects', 'get_opt_last_dates', 'get_opt_contracts', 'get_contract_info',
        'get_covered_lock_amount', 'get_covered_unlock_amount', 'open_prepared', 'close_prepared',
        'option_exercise', 'option_covered_lock', 'option_covered_unlock',
        
        # 计算函数
        'get_MACD', 'get_KDJ', 'get_RSI', 'get_CCI',
        
        # 其他函数
        'log', 'is_trade', 'check_limit', 'send_email', 'send_qywx',
        'permission_test', 'create_dir'
    }
    
    # 检查我们实现的API
    simtradelab_apis = set(simtradelab.__all__)
    
    # 找出PTrade中有但我们没有实现的API
    missing_apis = ptrade_apis - simtradelab_apis
    
    # 找出我们有但PTrade中没有的API（可能是扩展功能）
    extra_apis = simtradelab_apis - ptrade_apis
    
    print(f"PTrade API总数: {len(ptrade_apis)}")
    print(f"SimTradeLab API总数: {len(simtradelab_apis)}")
    
    if missing_apis:
        print(f"\n❌ 缺失的PTrade API ({len(missing_apis)}个):")
        for api in sorted(missing_apis):
            print(f"  - {api}")
    else:
        print("\n✅ 所有PTrade API都已实现")
    
    if extra_apis:
        print(f"\n📋 额外的API ({len(extra_apis)}个):")
        for api in sorted(extra_apis):
            print(f"  + {api}")
    
    # 验证关键API的存在
    critical_apis = [
        'run_daily', 'run_interval', 'log', 'order', 'get_history', 'get_price',
        'set_universe', 'set_benchmark', 'get_position', 'get_positions'
    ]
    
    print(f"\n=== 验证关键API ===")
    for api in critical_apis:
        if hasattr(simtradelab, api):
            print(f"✅ {api}")
        else:
            print(f"❌ {api} - 缺失")
    
    # 计算覆盖率
    implemented_ptrade_apis = ptrade_apis & simtradelab_apis
    coverage = len(implemented_ptrade_apis) / len(ptrade_apis) * 100
    
    print(f"\n📊 PTrade API覆盖率: {coverage:.1f}% ({len(implemented_ptrade_apis)}/{len(ptrade_apis)})")
    
    assert len(missing_apis) == 0


def test_log_functions():
    """测试日志函数"""
    print("\n=== 测试日志函数 ===")
    
    # 测试log对象
    assert hasattr(simtradelab, 'log'), "应该有log对象"
    
    log = simtradelab.log
    assert hasattr(log, 'info'), "log对象应该有info方法"
    assert hasattr(log, 'warning'), "log对象应该有warning方法"
    assert hasattr(log, 'error'), "log对象应该有error方法"
    assert hasattr(log, 'debug'), "log对象应该有debug方法"
    
    # 测试log对象的使用
    log.info("测试info日志")
    log.warning("测试warning日志")
    log.error("测试error日志")
    log.debug("测试debug日志")
    
    print("✅ log对象测试通过")

    # PTrade主要使用log对象，独立的日志函数是可选的
    # 我们的实现重点支持log对象的使用方式
    print("✅ PTrade兼容的log对象测试完成")


def test_timing_functions():
    """测试定时函数"""
    print("\n=== 测试定时函数 ===")
    
    # 测试run_daily
    assert hasattr(simtradelab, 'run_daily'), "应该有run_daily函数"
    
    # 测试run_interval
    assert hasattr(simtradelab, 'run_interval'), "应该有run_interval函数"
    
    print("✅ 定时函数测试通过")


def test_api_function_signatures():
    """测试API函数签名"""
    print("\n=== 测试API函数签名 ===")
    
    import inspect
    
    # 测试关键函数的签名
    test_functions = {
        'run_daily': ['engine', 'context', 'func'],
        'run_interval': ['engine', 'context', 'func', 'seconds'],
        'order': ['engine', 'security', 'amount'],
        'get_history': ['engine', 'count', 'frequency'],
    }
    
    for func_name, expected_params in test_functions.items():
        if hasattr(simtradelab, func_name):
            func = getattr(simtradelab, func_name)
            sig = inspect.signature(func)
            actual_params = list(sig.parameters.keys())
            
            # 检查必需参数是否存在（允许有额外的可选参数）
            for param in expected_params:
                if param not in actual_params:
                    print(f"❌ {func_name}: 缺少参数 {param}")
                    continue
            
            print(f"✅ {func_name}: 参数签名正确")
        else:
            print(f"❌ {func_name}: 函数不存在")
    
    print("✅ API函数签名测试完成")


def main():
    """运行所有测试"""
    print("开始测试API命名一致性...")
    
    try:
        naming_ok = test_ptrade_api_naming_consistency()
        test_log_functions()
        test_timing_functions()
        test_api_function_signatures()
        
        if naming_ok:
            print("\n🎉 所有API命名一致性测试通过！")
        else:
            print("\n⚠️  存在API命名不一致问题，请检查上述输出")
        
        return naming_ok
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
