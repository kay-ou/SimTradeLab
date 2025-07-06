#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试融资融券交易API的实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import (
    # 融资融券交易
    margin_trade, margincash_open, margincash_close, margincash_direct_refund,
    marginsec_open, marginsec_close, marginsec_direct_refund,
    # 融资融券查询
    get_margincash_stocks, get_marginsec_stocks, get_margin_contract,
    get_margin_contractreal, get_margin_assert, get_assure_security_list,
    get_margincash_open_amount, get_margincash_close_amount,
    get_marginsec_open_amount, get_marginsec_close_amount,
    get_margin_entrans_amount, get_enslo_security_info
)


def test_margin_trade():
    """测试担保品买卖"""
    print("\n=== 测试担保品买卖 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试担保品买入
    buy_result = margin_trade(engine, '000001.SZ', 1000, 'buy')
    print(f"担保品买入结果: {buy_result['order_id']}")
    
    assert buy_result['success'] == True, "担保品买入应该成功"
    assert buy_result['security'] == '000001.SZ', "证券代码应该匹配"
    assert buy_result['amount'] == 1000, "交易数量应该匹配"
    assert buy_result['operation'] == 'buy', "操作类型应该是买入"
    
    # 测试担保品卖出
    sell_result = margin_trade(engine, '600519.SH', 500, 'sell')
    print(f"担保品卖出结果: {sell_result['order_id']}")
    
    assert sell_result['success'] == True, "担保品卖出应该成功"
    assert sell_result['operation'] == 'sell', "操作类型应该是卖出"
    
    print("✅ 担保品买卖测试完成")


def test_margincash_trading():
    """测试融资交易"""
    print("\n=== 测试融资交易 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试融资买入
    open_result = margincash_open(engine, '000001.SZ', 1000, 12.50)
    print(f"融资买入结果: {open_result['order_id']}")
    
    assert open_result['success'] == True, "融资买入应该成功"
    assert 'estimated_cost' in open_result, "应该包含预估成本"
    
    # 测试卖券还款
    close_result = margincash_close(engine, '000001.SZ', 500, 13.00)
    print(f"卖券还款结果: {close_result['order_id']}")
    
    assert close_result['success'] == True, "卖券还款应该成功"
    assert close_result['order_type'] == 'margincash_close', "订单类型应该正确"
    
    # 测试直接还款
    refund_result = margincash_direct_refund(engine, 5000.0)
    print(f"直接还款结果: {refund_result['transaction_id']}")
    
    assert refund_result['success'] == True, "直接还款应该成功"
    assert refund_result['amount'] == 5000.0, "还款金额应该匹配"
    
    print("✅ 融资交易测试完成")


def test_marginsec_trading():
    """测试融券交易"""
    print("\n=== 测试融券交易 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试融券卖出
    open_result = marginsec_open(engine, '600519.SH', 100, 1800.0)
    print(f"融券卖出结果: {open_result['order_id']}")
    
    assert open_result['success'] == True, "融券卖出应该成功"
    assert open_result['order_type'] == 'marginsec_open', "订单类型应该正确"
    
    # 测试买券还券
    close_result = marginsec_close(engine, '600519.SH', 50, 1750.0)
    print(f"买券还券结果: {close_result['order_id']}")
    
    assert close_result['success'] == True, "买券还券应该成功"
    assert close_result['order_type'] == 'marginsec_close', "订单类型应该正确"
    
    # 测试直接还券
    refund_result = marginsec_direct_refund(engine, '600519.SH', 50)
    print(f"直接还券结果: {refund_result['transaction_id']}")
    
    assert refund_result['success'] == True, "直接还券应该成功"
    assert refund_result['security'] == '600519.SH', "证券代码应该匹配"
    
    print("✅ 融券交易测试完成")


def test_margin_query_apis():
    """测试融资融券查询API"""
    print("\n=== 测试融资融券查询API ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取融资标的
    margin_stocks = get_margincash_stocks(engine)
    print(f"融资标的数量: {len(margin_stocks)}")
    assert len(margin_stocks) > 0, "应该有融资标的"
    assert 'security' in margin_stocks[0], "融资标的应该包含证券代码"
    assert 'margin_ratio' in margin_stocks[0], "融资标的应该包含保证金比例"
    
    # 测试获取融券标的
    sec_stocks = get_marginsec_stocks(engine)
    print(f"融券标的数量: {len(sec_stocks)}")
    assert len(sec_stocks) > 0, "应该有融券标的"
    assert 'available_amount' in sec_stocks[0], "融券标的应该包含可融券数量"
    
    # 测试获取合约信息
    contracts = get_margin_contract(engine)
    print(f"融资融券合约数量: {len(contracts)}")
    assert len(contracts) > 0, "应该有融资融券合约"
    assert 'contract_type' in contracts[0], "合约应该包含类型信息"
    
    # 测试获取信用资产
    margin_assert = get_margin_assert(engine)
    print(f"信用资产信息: 总资产{margin_assert['total_asset']}")
    assert 'margin_ratio' in margin_assert, "应该包含维持担保比例"
    assert 'available_margin_amount' in margin_assert, "应该包含可融资金额"
    
    # 测试获取担保券列表
    assure_list = get_assure_security_list(engine)
    print(f"担保券数量: {len(assure_list)}")
    assert len(assure_list) > 0, "应该有担保券"
    assert 'assure_ratio' in assure_list[0], "担保券应该包含折算率"
    
    print("✅ 融资融券查询API测试完成")


def test_margin_amount_queries():
    """测试融资融券数量查询API"""
    print("\n=== 测试融资融券数量查询API ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试融资最大可买数量
    cash_open = get_margincash_open_amount(engine, '000001.SZ')
    print(f"融资最大可买: {cash_open['max_buy_amount']}股")
    assert 'max_buy_amount' in cash_open, "应该包含最大可买数量"
    assert 'margin_ratio' in cash_open, "应该包含保证金比例"
    
    # 测试卖券还款最大可卖数量
    cash_close = get_margincash_close_amount(engine, '000001.SZ')
    print(f"卖券还款最大可卖: {cash_close['max_sell_amount']}股")
    assert 'max_sell_amount' in cash_close, "应该包含最大可卖数量"
    
    # 测试融券最大可卖数量
    sec_open = get_marginsec_open_amount(engine, '600519.SH')
    print(f"融券最大可卖: {sec_open['max_sell_amount']}股")
    assert 'max_sell_amount' in sec_open, "应该包含最大可卖数量"
    
    # 测试买券还券最大可买数量
    sec_close = get_marginsec_close_amount(engine, '600519.SH')
    print(f"买券还券最大可买: {sec_close['max_buy_amount']}股")
    assert 'max_buy_amount' in sec_close, "应该包含最大可买数量"
    
    # 测试现券还券数量
    entrans = get_margin_entrans_amount(engine, '600519.SH')
    print(f"现券还券可还: {entrans['available_return_amount']}股")
    assert 'available_return_amount' in entrans, "应该包含可还券数量"
    
    # 测试融券头寸信息
    enslo_info = get_enslo_security_info(engine, '600519.SH')
    print(f"融券头寸: 可融券{enslo_info['available_enslo_amount']}股")
    assert 'available_enslo_amount' in enslo_info, "应该包含可融券数量"
    assert 'enslo_rate' in enslo_info, "应该包含融券费率"
    
    print("✅ 融资融券数量查询API测试完成")


def test_integration():
    """集成测试：验证融资融券API之间的协调工作"""
    print("\n=== 融资融券集成测试 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 1. 查询信用资产状态
    margin_assert = get_margin_assert(engine)
    print(f"当前维持担保比例: {margin_assert['margin_ratio']}")
    
    # 2. 检查融资标的
    margin_stocks = get_margincash_stocks(engine)
    target_stock = margin_stocks[0]['security']
    print(f"选择融资标的: {target_stock}")
    
    # 3. 查询最大可融资买入数量
    max_buy_info = get_margincash_open_amount(engine, target_stock)
    max_amount = max_buy_info['max_buy_amount']
    print(f"最大可融资买入: {max_amount}股")
    
    # 4. 执行融资买入
    if max_amount > 0:
        buy_amount = min(1000, max_amount)
        buy_result = margincash_open(engine, target_stock, buy_amount, 12.50)
        
        if buy_result['success']:
            print(f"融资买入成功: {buy_amount}股")
            
            # 5. 查询卖券还款数量
            sell_info = get_margincash_close_amount(engine, target_stock)
            max_sell = sell_info['max_sell_amount']
            
            # 6. 执行部分卖券还款
            if max_sell > 0:
                sell_amount = min(500, max_sell)
                sell_result = margincash_close(engine, target_stock, sell_amount, 13.00)
                
                if sell_result['success']:
                    print(f"卖券还款成功: {sell_amount}股")
    
    # 7. 测试融券流程
    sec_stocks = get_marginsec_stocks(engine)
    if sec_stocks:
        sec_stock = sec_stocks[0]['security']
        sec_amount_info = get_marginsec_open_amount(engine, sec_stock)
        
        if sec_amount_info['max_sell_amount'] > 0:
            sec_result = marginsec_open(engine, sec_stock, 100, 1800.0)
            if sec_result['success']:
                print(f"融券卖出成功: {sec_stock}")
    
    print("✅ 融资融券集成测试完成")


def main():
    """运行所有测试"""
    print("开始测试融资融券交易API...")
    
    try:
        test_margin_trade()
        test_margincash_trading()
        test_marginsec_trading()
        test_margin_query_apis()
        test_margin_amount_queries()
        test_integration()
        
        print("\n🎉 所有融资融券API测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
