#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试期权高级功能API的实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import (
    get_contract_info, get_covered_lock_amount, get_covered_unlock_amount,
    open_prepared, close_prepared
)


def test_get_contract_info():
    """测试获取期权合约信息"""
    print("\n=== 测试获取期权合约信息 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试认购期权
    call_option = '10002334.SH'  # 假设的认购期权代码
    call_info = get_contract_info(engine, call_option)
    
    print(f"认购期权信息: {call_info['option_name']}")
    
    # 验证必要字段
    required_fields = [
        'option_code', 'option_name', 'underlying_code', 'underlying_name',
        'option_type', 'exercise_type', 'strike_price', 'contract_unit',
        'expire_date', 'last_trade_date', 'exercise_date', 'delivery_date',
        'min_price_change', 'daily_price_up_limit', 'daily_price_down_limit',
        'margin_ratio1', 'margin_ratio2', 'tick_size'
    ]
    
    for field in required_fields:
        assert field in call_info, f"期权合约信息应该包含字段 {field}"
    
    # 验证数据类型和值
    assert call_info['option_code'] == call_option, "期权代码应该匹配"
    assert isinstance(call_info['strike_price'], (int, float)), "行权价应该是数字"
    assert isinstance(call_info['contract_unit'], int), "合约单位应该是整数"
    assert call_info['option_type'] in ['C', 'P'], "期权类型应该是C或P"
    assert call_info['exercise_type'] in ['E', 'A'], "行权类型应该是E或A"
    
    print(f"  - 标的: {call_info['underlying_name']} ({call_info['underlying_code']})")
    print(f"  - 类型: {'认购' if call_info['option_type'] == 'C' else '认沽'}")
    print(f"  - 行权价: {call_info['strike_price']}")
    print(f"  - 到期日: {call_info['expire_date']}")
    
    # 测试认沽期权
    put_option = '10002335.SH'  # 假设的认沽期权代码
    put_info = get_contract_info(engine, put_option)
    
    assert put_info['option_code'] == put_option, "认沽期权代码应该匹配"
    print(f"认沽期权信息: {put_info['option_name']}")
    
    print("✅ 期权合约信息测试完成")


def test_get_covered_lock_amount():
    """测试获取备兑锁定数量"""
    print("\n=== 测试获取备兑锁定数量 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取备兑锁定数量
    underlying_code = '510050.SH'
    lock_info = get_covered_lock_amount(engine, underlying_code)
    
    print(f"备兑锁定信息: {underlying_code}")
    
    # 验证必要字段
    required_fields = [
        'underlying_code', 'total_amount', 'locked_amount', 
        'available_lock_amount', 'lock_unit', 'max_lock_lots'
    ]
    
    for field in required_fields:
        assert field in lock_info, f"备兑锁定信息应该包含字段 {field}"
    
    # 验证数据类型
    assert lock_info['underlying_code'] == underlying_code, "标的代码应该匹配"
    assert isinstance(lock_info['total_amount'], (int, float)), "总持仓应该是数字"
    assert isinstance(lock_info['locked_amount'], (int, float)), "已锁定数量应该是数字"
    assert isinstance(lock_info['available_lock_amount'], (int, float)), "可锁定数量应该是数字"
    assert isinstance(lock_info['lock_unit'], int), "锁定单位应该是整数"
    assert isinstance(lock_info['max_lock_lots'], int), "最大锁定手数应该是整数"
    
    print(f"  - 总持仓: {lock_info['total_amount']}")
    print(f"  - 已锁定: {lock_info['locked_amount']}")
    print(f"  - 可锁定: {lock_info['available_lock_amount']}")
    print(f"  - 最大锁定手数: {lock_info['max_lock_lots']}")
    
    print("✅ 备兑锁定数量测试完成")


def test_get_covered_unlock_amount():
    """测试获取备兑解锁数量"""
    print("\n=== 测试获取备兑解锁数量 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取备兑解锁数量
    underlying_code = '510050.SH'
    unlock_info = get_covered_unlock_amount(engine, underlying_code)
    
    print(f"备兑解锁信息: {underlying_code}")
    
    # 验证必要字段
    required_fields = [
        'underlying_code', 'locked_amount', 'available_unlock_amount',
        'unlock_unit', 'max_unlock_lots', 'pending_exercise_amount'
    ]
    
    for field in required_fields:
        assert field in unlock_info, f"备兑解锁信息应该包含字段 {field}"
    
    # 验证数据类型
    assert unlock_info['underlying_code'] == underlying_code, "标的代码应该匹配"
    assert isinstance(unlock_info['locked_amount'], (int, float)), "已锁定数量应该是数字"
    assert isinstance(unlock_info['available_unlock_amount'], (int, float)), "可解锁数量应该是数字"
    assert isinstance(unlock_info['unlock_unit'], int), "解锁单位应该是整数"
    assert isinstance(unlock_info['max_unlock_lots'], int), "最大解锁手数应该是整数"
    
    print(f"  - 已锁定: {unlock_info['locked_amount']}")
    print(f"  - 可解锁: {unlock_info['available_unlock_amount']}")
    print(f"  - 最大解锁手数: {unlock_info['max_unlock_lots']}")
    print(f"  - 待行权数量: {unlock_info['pending_exercise_amount']}")
    
    print("✅ 备兑解锁数量测试完成")


def test_open_prepared():
    """测试备兑开仓"""
    print("\n=== 测试备兑开仓 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试备兑开仓
    option_code = '10002334.SH'
    amount = 2  # 2手
    price = 0.2500
    
    result = open_prepared(engine, option_code, amount, price)
    
    print(f"备兑开仓结果: {option_code}")
    
    # 验证必要字段
    required_fields = [
        'success', 'order_id', 'option_code', 'amount', 'price',
        'order_type', 'underlying_code', 'locked_amount'
    ]
    
    for field in required_fields:
        assert field in result, f"备兑开仓结果应该包含字段 {field}"
    
    # 验证结果
    assert result['success'] == True, "备兑开仓应该成功"
    assert result['option_code'] == option_code, "期权代码应该匹配"
    assert result['amount'] == amount, "开仓数量应该匹配"
    assert result['price'] == price, "开仓价格应该匹配"
    assert result['order_type'] == 'covered_open', "委托类型应该是备兑开仓"
    assert result['locked_amount'] == amount * 10000, "锁定数量应该正确计算"
    
    print(f"  - 委托号: {result['order_id']}")
    print(f"  - 开仓数量: {result['amount']}手")
    print(f"  - 开仓价格: {result['price']}")
    print(f"  - 锁定标的: {result['locked_amount']}")
    
    # 测试市价开仓
    market_result = open_prepared(engine, option_code, 1)  # 不指定价格
    assert market_result['success'] == True, "市价备兑开仓应该成功"
    assert market_result['price'] is not None, "市价开仓应该有默认价格"
    
    print("✅ 备兑开仓测试完成")


def test_close_prepared():
    """测试备兑平仓"""
    print("\n=== 测试备兑平仓 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试备兑平仓
    option_code = '10002334.SH'
    amount = 1  # 1手
    price = 0.1500
    
    result = close_prepared(engine, option_code, amount, price)
    
    print(f"备兑平仓结果: {option_code}")
    
    # 验证必要字段
    required_fields = [
        'success', 'order_id', 'option_code', 'amount', 'price',
        'order_type', 'unlock_amount'
    ]
    
    for field in required_fields:
        assert field in result, f"备兑平仓结果应该包含字段 {field}"
    
    # 验证结果
    assert result['success'] == True, "备兑平仓应该成功"
    assert result['option_code'] == option_code, "期权代码应该匹配"
    assert result['amount'] == amount, "平仓数量应该匹配"
    assert result['price'] == price, "平仓价格应该匹配"
    assert result['order_type'] == 'covered_close', "委托类型应该是备兑平仓"
    assert result['unlock_amount'] == amount * 10000, "解锁数量应该正确计算"
    
    print(f"  - 委托号: {result['order_id']}")
    print(f"  - 平仓数量: {result['amount']}手")
    print(f"  - 平仓价格: {result['price']}")
    print(f"  - 解锁标的: {result['unlock_amount']}")
    
    print("✅ 备兑平仓测试完成")


def test_integration():
    """集成测试：验证期权API之间的协调工作"""
    print("\n=== 期权功能集成测试 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 1. 获取期权合约信息
    option_code = '10002334.SH'
    contract_info = get_contract_info(engine, option_code)
    underlying_code = contract_info['underlying_code']
    
    print(f"期权合约: {contract_info['option_name']}")
    print(f"标的证券: {contract_info['underlying_name']}")
    
    # 2. 检查备兑锁定数量
    lock_info = get_covered_lock_amount(engine, underlying_code)
    max_lots = lock_info['max_lock_lots']
    
    print(f"最大可备兑开仓: {max_lots}手")
    
    # 3. 执行备兑开仓（如果有足够的锁定数量）
    if max_lots > 0:
        open_lots = min(2, max_lots)  # 开仓2手或最大可开仓数量
        open_result = open_prepared(engine, option_code, open_lots, 0.2500)
        
        if open_result['success']:
            print(f"备兑开仓成功: {open_lots}手")
            
            # 4. 检查解锁数量
            unlock_info = get_covered_unlock_amount(engine, underlying_code)
            print(f"可解锁数量: {unlock_info['max_unlock_lots']}手")
            
            # 5. 执行备兑平仓
            close_lots = min(1, open_lots)  # 平仓1手
            close_result = close_prepared(engine, option_code, close_lots, 0.1500)
            
            if close_result['success']:
                print(f"备兑平仓成功: {close_lots}手")
    
    print("✅ 期权功能集成测试完成")


def main():
    """运行所有测试"""
    print("开始测试期权高级功能API...")
    
    try:
        test_get_contract_info()
        test_get_covered_lock_amount()
        test_get_covered_unlock_amount()
        test_open_prepared()
        test_close_prepared()
        test_integration()
        
        print("\n🎉 所有期权高级功能API测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
