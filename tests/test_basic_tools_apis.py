#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试基础工具API的实现
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import (
    BacktestEngine, check_limit, create_dir, get_user_name,
    get_trade_name, permission_test
)
from simtradelab.logger import log
from simtradelab.data_sources import CSVDataSource
import pandas as pd


def test_log_functions():
    """测试日志函数"""
    print("\n=== 测试日志函数 ===")
    
    # 测试各种级别的日志
    log.info("这是一条INFO级别的日志")
    log.warning("这是一条WARNING级别的日志")
    log.error("这是一条ERROR级别的日志")
    log.debug("这是一条DEBUG级别的日志")
    
    print("✅ 日志函数测试完成")


def test_check_limit():
    """测试涨跌停判断函数"""
    print("\n=== 测试涨跌停判断函数 ===")

    # 创建一个简单的模拟引擎
    class MockEngine:
        def __init__(self):
            self.current_data = {}
            self.data = {}

    engine = MockEngine()

    # 创建测试数据
    test_data = pd.DataFrame({
        'close': [10.0, 10.5]  # 昨天10.0，今天10.5
    }, index=pd.date_range('2023-01-01', periods=2))

    engine.data = {'STOCK_A': test_data}
    engine.current_data = {'STOCK_A': {'close': 11.0}}  # 今天涨停到11.0

    # 测试涨停股票
    result_a = check_limit(engine, 'STOCK_A')
    print(f"STOCK_A 涨跌停检查结果: {result_a}")

    # 测试跌停股票
    engine.current_data = {'STOCK_A': {'close': 9.0}}  # 今天跌停到9.0
    result_b = check_limit(engine, 'STOCK_A')
    print(f"STOCK_A 跌停检查结果: {result_b}")

    # 验证结果
    assert result_a['current_price'] == 11.0, "当前价格应该是11.0"
    assert result_b['current_price'] == 9.0, "当前价格应该是9.0"

    print("✅ 涨跌停判断函数测试完成")


def test_create_dir():
    """测试目录创建函数"""
    print("\n=== 测试目录创建函数 ===")

    # 创建临时目录作为测试基础
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建简单的模拟引擎
        class MockEngine:
            def __init__(self):
                self.research_path = temp_dir

        engine = MockEngine()

        # 测试创建单级目录
        result1 = create_dir(engine, 'test_dir')
        expected_path1 = Path(temp_dir) / 'test_dir'
        assert expected_path1.exists(), "单级目录应该被创建"
        print(f"创建单级目录: {result1}")

        # 测试创建多级目录
        result2 = create_dir(engine, 'test_dir/sub_dir/deep_dir')
        expected_path2 = Path(temp_dir) / 'test_dir/sub_dir/deep_dir'
        assert expected_path2.exists(), "多级目录应该被创建"
        print(f"创建多级目录: {result2}")

        # 测试重复创建（应该不报错）
        result3 = create_dir(engine, 'test_dir')
        assert result3 is not None, "重复创建目录应该成功"
        print(f"重复创建目录: {result3}")

    print("✅ 目录创建函数测试完成")


def test_user_and_trade_info():
    """测试用户和交易信息函数"""
    print("\n=== 测试用户和交易信息函数 ===")

    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass

    engine = MockEngine()

    # 测试获取用户名
    user_name = get_user_name(engine)
    print(f"用户名: {user_name}")
    assert user_name is not None, "应该返回用户名"

    # 测试获取交易名称
    trade_name = get_trade_name(engine)
    print(f"交易名称: {trade_name}")
    assert trade_name is not None, "应该返回交易名称"

    # 测试自定义用户名和交易名称
    engine.account_id = "TEST_ACCOUNT_123"
    engine.trade_name = "TEST_STRATEGY_001"

    user_name2 = get_user_name(engine)
    trade_name2 = get_trade_name(engine)

    assert user_name2 == "TEST_ACCOUNT_123", "应该返回自定义用户名"
    assert trade_name2 == "TEST_STRATEGY_001", "应该返回自定义交易名称"

    print(f"自定义用户名: {user_name2}")
    print(f"自定义交易名称: {trade_name2}")

    print("✅ 用户和交易信息函数测试完成")


def test_permission_test():
    """测试权限校验函数"""
    print("\n=== 测试权限校验函数 ===")

    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass

    engine = MockEngine()

    # 测试不同类型的权限
    permissions = ['trade', 'query', 'admin', 'data']

    for perm in permissions:
        result = permission_test(engine, perm)
        print(f"权限 {perm}: {'通过' if result else '拒绝'}")
        assert result == True, f"权限 {perm} 应该通过"

    print("✅ 权限校验函数测试完成")


def main():
    """运行所有测试"""
    print("开始测试基础工具API...")
    
    try:
        test_log_functions()
        test_check_limit()
        test_create_dir()
        test_user_and_trade_info()
        test_permission_test()
        
        print("\n🎉 所有基础工具API测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
