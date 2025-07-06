#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试其他缺失API的实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import (
    get_trades_file, convert_position_from_csv, get_deliver, get_fundjour,
    order_tick, cancel_order_ex, get_all_orders, after_trading_cancel_order
)


def test_get_trades_file():
    """测试获取对账数据文件"""
    print("\n=== 测试获取对账数据文件 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取当日对账文件
    trades_file = get_trades_file(engine)
    print(f"对账文件信息: {trades_file['file_path']}")
    
    assert 'date' in trades_file, "应该包含日期"
    assert 'file_path' in trades_file, "应该包含文件路径"
    assert 'record_count' in trades_file, "应该包含记录数量"
    assert 'status' in trades_file, "应该包含文件状态"
    
    print(f"  - 记录数量: {trades_file['record_count']}")
    print(f"  - 文件大小: {trades_file['file_size']} 字节")
    print(f"  - 生成时间: {trades_file['generated_time']}")
    
    # 测试指定日期的对账文件
    specific_file = get_trades_file(engine, '2023-06-15')
    assert specific_file['date'] == '2023-06-15', "日期应该匹配"
    
    print("✅ 对账数据文件测试完成")


def test_convert_position_from_csv():
    """测试CSV底仓转换"""
    print("\n=== 测试CSV底仓转换 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试CSV底仓转换
    csv_path = "data/positions.csv"
    position_params = convert_position_from_csv(engine, csv_path)
    
    print(f"底仓参数数量: {len(position_params)}")
    
    assert isinstance(position_params, list), "应该返回列表"
    assert len(position_params) > 0, "应该有底仓数据"
    
    # 验证底仓参数格式
    for param in position_params:
        assert 'security' in param, "应该包含证券代码"
        assert 'amount' in param, "应该包含数量"
        assert 'avg_cost' in param, "应该包含平均成本"
        assert 'market_value' in param, "应该包含市值"
        
        print(f"  - {param['security']}: {param['amount']}股, 成本{param['avg_cost']}")
    
    print("✅ CSV底仓转换测试完成")


def test_get_deliver():
    """测试获取交割单"""
    print("\n=== 测试获取交割单 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取默认期间交割单
    deliver_records = get_deliver(engine)
    print(f"交割单记录数量: {len(deliver_records)}")
    
    assert isinstance(deliver_records, list), "应该返回列表"
    assert len(deliver_records) > 0, "应该有交割记录"
    
    # 验证交割单格式
    for record in deliver_records:
        required_fields = [
            'trade_date', 'security', 'security_name', 'operation',
            'amount', 'price', 'total_amount', 'commission',
            'stamp_tax', 'transfer_fee', 'net_amount', 'balance'
        ]
        
        for field in required_fields:
            assert field in record, f"交割单应该包含字段 {field}"
        
        print(f"  - {record['trade_date']} {record['operation']} {record['security']} {record['amount']}股")
    
    # 测试指定日期范围
    specific_records = get_deliver(engine, '2023-06-01', '2023-06-30')
    assert isinstance(specific_records, list), "指定日期范围应该返回列表"
    
    print("✅ 交割单测试完成")


def test_get_fundjour():
    """测试获取资金流水"""
    print("\n=== 测试获取资金流水 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取资金流水
    fund_records = get_fundjour(engine)
    print(f"资金流水记录数量: {len(fund_records)}")
    
    assert isinstance(fund_records, list), "应该返回列表"
    assert len(fund_records) > 0, "应该有资金流水记录"
    
    # 验证资金流水格式
    for record in fund_records:
        required_fields = [
            'date', 'time', 'operation', 'description',
            'amount', 'balance', 'remark'
        ]
        
        for field in required_fields:
            assert field in record, f"资金流水应该包含字段 {field}"
        
        print(f"  - {record['date']} {record['operation']}: {record['amount']}, 余额{record['balance']}")
    
    # 测试指定日期范围
    specific_records = get_fundjour(engine, '2023-06-01', '2023-06-30')
    assert isinstance(specific_records, list), "指定日期范围应该返回列表"
    
    print("✅ 资金流水测试完成")


def test_order_tick():
    """测试tick触发委托"""
    print("\n=== 测试tick触发委托 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试tick触发委托
    tick_condition = {
        'trigger_price': 12.50,
        'condition': 'greater_than',
        'valid_time': '2023-06-15 15:00:00'
    }
    
    result = order_tick(engine, '000001.SZ', 1000, tick_condition)
    print(f"tick委托结果: {result['order_id']}")
    
    assert result['success'] == True, "tick委托应该成功"
    assert result['security'] == '000001.SZ', "证券代码应该匹配"
    assert result['amount'] == 1000, "委托数量应该匹配"
    assert result['order_type'] == 'tick_order', "订单类型应该正确"
    assert result['status'] == 'pending', "初始状态应该是pending"
    
    print(f"  - 触发条件: {tick_condition}")
    print(f"  - 委托状态: {result['status']}")
    
    print("✅ tick触发委托测试完成")


def test_cancel_order_ex():
    """测试扩展撤单"""
    print("\n=== 测试扩展撤单 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试普通撤单
    result1 = cancel_order_ex(engine, 'ORD001', 'normal')
    print(f"普通撤单结果: {result1['order_id']}")
    
    assert result1['success'] == True, "撤单应该成功"
    assert result1['order_id'] == 'ORD001', "订单号应该匹配"
    assert result1['cancel_type'] == 'normal', "撤单类型应该匹配"
    assert result1['status'] == 'cancelled', "状态应该是已撤销"
    
    # 测试强制撤单
    result2 = cancel_order_ex(engine, 'ORD002', 'force')
    assert result2['cancel_type'] == 'force', "强制撤单类型应该正确"
    
    print("✅ 扩展撤单测试完成")


def test_get_all_orders():
    """测试获取全部订单"""
    print("\n=== 测试获取全部订单 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取当日全部订单
    all_orders = get_all_orders(engine)
    print(f"当日全部订单数量: {len(all_orders)}")
    
    assert isinstance(all_orders, list), "应该返回列表"
    assert len(all_orders) > 0, "应该有订单记录"
    
    # 验证订单格式
    for order in all_orders:
        required_fields = [
            'order_id', 'security', 'operation', 'amount',
            'price', 'status', 'order_time'
        ]
        
        for field in required_fields:
            assert field in order, f"订单应该包含字段 {field}"
        
        print(f"  - {order['order_id']}: {order['operation']} {order['security']} {order['amount']}股 状态:{order['status']}")
    
    # 测试指定日期的订单
    specific_orders = get_all_orders(engine, '2023-06-15')
    assert isinstance(specific_orders, list), "指定日期应该返回列表"
    
    print("✅ 全部订单测试完成")


def test_after_trading_cancel_order():
    """测试盘后撤单"""
    print("\n=== 测试盘后撤单 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试盘后撤单
    result = after_trading_cancel_order(engine, 'ORD003')
    print(f"盘后撤单结果: {result['order_id']}")
    
    assert result['success'] == True, "盘后撤单应该成功"
    assert result['order_id'] == 'ORD003', "订单号应该匹配"
    assert result['cancel_type'] == 'after_trading', "撤单类型应该是盘后"
    assert result['status'] == 'cancelled', "状态应该是已撤销"
    
    print(f"  - 撤单类型: {result['cancel_type']}")
    print(f"  - 撤单时间: {result['cancel_time']}")
    
    print("✅ 盘后撤单测试完成")


def test_integration():
    """集成测试：验证API之间的协调工作"""
    print("\n=== 其他API集成测试 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 1. 获取当日全部订单
    all_orders = get_all_orders(engine)
    print(f"当日订单总数: {len(all_orders)}")
    
    # 2. 获取交割单
    deliver_records = get_deliver(engine)
    print(f"交割记录总数: {len(deliver_records)}")
    
    # 3. 获取资金流水
    fund_records = get_fundjour(engine)
    print(f"资金流水总数: {len(fund_records)}")
    
    # 4. 获取对账文件
    trades_file = get_trades_file(engine)
    print(f"对账文件状态: {trades_file['status']}")
    
    # 5. 模拟tick委托和撤单流程
    tick_condition = {'trigger_price': 12.50, 'condition': 'greater_than'}
    tick_order = order_tick(engine, '000001.SZ', 1000, tick_condition)
    
    if tick_order['success']:
        print(f"tick委托成功: {tick_order['order_id']}")
        
        # 撤销tick委托
        cancel_result = cancel_order_ex(engine, tick_order['order_id'], 'normal')
        if cancel_result['success']:
            print(f"tick委托撤销成功")
    
    print("✅ 其他API集成测试完成")


def main():
    """运行所有测试"""
    print("开始测试其他缺失API...")
    
    try:
        test_get_trades_file()
        test_convert_position_from_csv()
        test_get_deliver()
        test_get_fundjour()
        test_order_tick()
        test_cancel_order_ex()
        test_get_all_orders()
        test_after_trading_cancel_order()
        test_integration()
        
        print("\n🎉 所有其他缺失API测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
