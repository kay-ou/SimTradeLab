# -*- coding: utf-8 -*-
"""
委托状态兼容性功能测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab.engine import BacktestEngine
from simtradelab.compatibility import (
    set_ptrade_version, get_version_info, validate_order_status, 
    convert_order_status, PtradeVersion
)
from simtradelab.trading import order, get_order, get_orders


def test_compatibility_functions():
    """测试兼容性处理功能"""
    print("=" * 70)
    print("测试委托状态兼容性功能")
    print("=" * 70)
    
    try:
        # 1. 测试版本设置和信息获取
        print("\n1. 测试版本设置和信息获取")
        
        # 测试V005版本（整数状态）
        set_ptrade_version(PtradeVersion.V005)
        v005_info = get_version_info()
        print(f"V005版本信息: {v005_info}")
        
        # 测试V016版本（字符串状态）
        set_ptrade_version(PtradeVersion.V016)
        v016_info = get_version_info()
        print(f"V016版本信息: {v016_info}")
        
        # 测试V041版本（字符串状态）
        set_ptrade_version(PtradeVersion.V041)
        v041_info = get_version_info()
        print(f"V041版本信息: {v041_info}")
        
        # 2. 测试状态转换功能
        print("\n2. 测试状态转换功能")
        
        # 测试V005版本的状态转换
        set_ptrade_version(PtradeVersion.V005)
        print("V005版本状态转换:")
        for status in ['new', 'open', 'filled', 'cancelled', 'rejected']:
            external = convert_order_status(status, to_external=True)
            internal = convert_order_status(external, to_external=False)
            print(f"  {status} -> {external} -> {internal}")
        
        # 测试V041版本的状态转换
        set_ptrade_version(PtradeVersion.V041)
        print("\nV041版本状态转换:")
        for status in ['new', 'open', 'filled', 'cancelled', 'rejected']:
            external = convert_order_status(status, to_external=True)
            internal = convert_order_status(external, to_external=False)
            print(f"  {status} -> {external} -> {internal}")
        
        # 3. 测试状态验证功能
        print("\n3. 测试状态验证功能")
        
        # V005版本验证
        set_ptrade_version(PtradeVersion.V005)
        print("V005版本状态验证:")
        for status in [0, 1, 2, 3, 4, 99]:  # 包含无效状态
            valid = validate_order_status(status)
            print(f"  状态 {status}: {'有效' if valid else '无效'}")
        
        # V041版本验证
        set_ptrade_version(PtradeVersion.V041)
        print("\nV041版本状态验证:")
        for status in ['new', 'open', 'filled', 'cancelled', 'rejected', 'invalid']:
            valid = validate_order_status(status)
            print(f"  状态 '{status}': {'有效' if valid else '无效'}")
        
        print("\n✅ 兼容性处理功能测试通过")
        
    except Exception as e:
        print(f"❌ 兼容性处理功能测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_order_status_compatibility():
    """测试订单状态兼容性"""
    print("\n" + "=" * 70)
    print("测试订单状态兼容性")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        # 设置当前时间和数据
        import pandas as pd
        engine.context.current_dt = pd.to_datetime('2023-01-03')
        test_security = 'STOCK_A'
        engine.current_data = {test_security: {'close': 100.0, 'open': 99.0, 'high': 101.0, 'low': 98.0, 'volume': 1000000}}
        
        print(f"测试股票: {test_security}")
        
        # 测试不同版本下的订单状态
        versions_to_test = [PtradeVersion.V005, PtradeVersion.V016, PtradeVersion.V041]
        
        for version in versions_to_test:
            print(f"\n--- 测试 {version.value} 版本 ---")
            
            # 设置版本
            set_ptrade_version(version)
            
            # 下单
            order_id = order(engine, test_security, 1000)
            print(f"订单ID: {order_id}")
            
            if order_id:
                # 获取订单信息
                order_info = get_order(engine, order_id)
                print(f"订单状态: {order_info['status']} (类型: {type(order_info['status'])})")
                
                # 验证状态格式
                if version == PtradeVersion.V005:
                    expected_type = int
                else:
                    expected_type = str
                
                if isinstance(order_info['status'], expected_type):
                    print(f"✅ 状态格式正确 ({expected_type.__name__})")
                else:
                    print(f"❌ 状态格式错误，期望 {expected_type.__name__}，实际 {type(order_info['status']).__name__}")
                
                # 验证状态值
                valid = validate_order_status(order_info['status'])
                print(f"状态有效性: {'有效' if valid else '无效'}")
        
        # 测试批量订单状态
        print(f"\n--- 测试批量订单状态 ---")
        set_ptrade_version(PtradeVersion.V005)  # 使用V005版本测试
        
        # 下多个订单
        order_ids = []
        for i in range(3):
            oid = order(engine, test_security, 100)
            if oid:
                order_ids.append(oid)
        
        # 获取所有订单
        all_orders = get_orders(engine)
        print(f"总订单数: {len(all_orders)}")
        
        # 检查所有订单的状态格式
        status_types = set()
        for order_id, order_info in all_orders.items():
            status_types.add(type(order_info['status']))
        
        print(f"状态类型: {[t.__name__ for t in status_types]}")
        
        if len(status_types) == 1 and int in status_types:
            print("✅ 所有订单状态格式一致（整数）")
        else:
            print("❌ 订单状态格式不一致")
        
        print("\n✅ 订单状态兼容性测试完成")
        
    except Exception as e:
        print(f"❌ 订单状态兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_version_switching():
    """测试版本切换功能"""
    print("\n" + "=" * 70)
    print("测试版本切换功能")
    print("=" * 70)
    
    try:
        # 测试字符串版本设置
        print("测试字符串版本设置:")
        for version_str in ['v005', 'V016', 'v041', 'invalid']:
            try:
                set_ptrade_version(version_str)
                info = get_version_info()
                print(f"  '{version_str}' -> {info['version']} ✅")
            except Exception as e:
                print(f"  '{version_str}' -> 错误: {e} ❌")
        
        # 测试版本信息对比
        print("\n版本差异对比:")
        versions = [PtradeVersion.V005, PtradeVersion.V016, PtradeVersion.V041]
        
        for version in versions:
            set_ptrade_version(version)
            info = get_version_info()
            print(f"{version.value}:")
            print(f"  状态类型: {info['status_type']}")
            print(f"  支持状态: {info['supported_statuses']}")
            print(f"  未完成状态: {info['open_statuses']}")
            print(f"  已完成状态: {info['closed_statuses']}")
        
        print("\n✅ 版本切换功能测试完成")
        
    except Exception as e:
        print(f"❌ 版本切换功能测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_compatibility_functions()
    test_order_status_compatibility()
    test_version_switching()
