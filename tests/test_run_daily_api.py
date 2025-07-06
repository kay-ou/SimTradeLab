#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试run_daily API的实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import run_daily


def test_run_daily():
    """测试run_daily API"""
    print("\n=== 测试run_daily API ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    class MockContext:
        def __init__(self):
            pass
    
    engine = MockEngine()
    context = MockContext()
    
    # 定义测试函数
    def test_func():
        print("测试函数被调用")
    
    # 测试默认时间（09:30）
    run_daily(engine, context, test_func)
    
    # 验证任务被注册
    assert hasattr(engine, 'daily_tasks'), "应该创建daily_tasks属性"
    assert len(engine.daily_tasks) == 1, "应该有一个每日任务"
    
    task = engine.daily_tasks[0]
    assert task['func'] == test_func, "函数应该匹配"
    assert task['time'] == '09:30', "默认时间应该是09:30"
    assert task['context'] == context, "上下文应该匹配"
    
    print(f"✅ 默认时间任务注册成功: {task['time']}")
    
    # 测试自定义时间
    def test_func2():
        print("测试函数2被调用")
    
    run_daily(engine, context, test_func2, time='15:00')
    
    # 验证第二个任务被注册
    assert len(engine.daily_tasks) == 2, "应该有两个每日任务"
    
    task2 = engine.daily_tasks[1]
    assert task2['func'] == test_func2, "函数应该匹配"
    assert task2['time'] == '15:00', "时间应该是15:00"
    assert task2['context'] == context, "上下文应该匹配"
    
    print(f"✅ 自定义时间任务注册成功: {task2['time']}")
    
    # 测试多个时间点
    def test_func3():
        print("测试函数3被调用")
    
    run_daily(engine, context, test_func3, time='14:30')
    
    assert len(engine.daily_tasks) == 3, "应该有三个每日任务"
    
    task3 = engine.daily_tasks[2]
    assert task3['time'] == '14:30', "时间应该是14:30"
    
    print(f"✅ 多个任务注册成功，总数: {len(engine.daily_tasks)}")
    
    # 验证所有任务的时间
    times = [task['time'] for task in engine.daily_tasks]
    expected_times = ['09:30', '15:00', '14:30']
    assert times == expected_times, f"时间列表应该匹配: {times} vs {expected_times}"
    
    print("✅ run_daily API测试完成")


def test_run_daily_with_lambda():
    """测试run_daily与lambda函数"""
    print("\n=== 测试run_daily与lambda函数 ===")
    
    class MockEngine:
        def __init__(self):
            pass
    
    class MockContext:
        def __init__(self):
            pass
    
    engine = MockEngine()
    context = MockContext()
    
    # 测试lambda函数
    lambda_func = lambda: print("Lambda函数被调用")
    
    run_daily(engine, context, lambda_func, time='11:30')
    
    assert hasattr(engine, 'daily_tasks'), "应该创建daily_tasks属性"
    assert len(engine.daily_tasks) == 1, "应该有一个每日任务"
    
    task = engine.daily_tasks[0]
    assert task['func'] == lambda_func, "Lambda函数应该匹配"
    assert task['time'] == '11:30', "时间应该是11:30"
    
    print("✅ Lambda函数任务注册成功")


def test_run_daily_integration():
    """集成测试：验证run_daily与其他API的协调工作"""
    print("\n=== run_daily集成测试 ===")
    
    from simtradelab import run_interval
    
    class MockEngine:
        def __init__(self):
            pass
    
    class MockContext:
        def __init__(self):
            pass
    
    engine = MockEngine()
    context = MockContext()
    
    # 注册每日任务
    def daily_task():
        print("每日任务执行")
    
    run_daily(engine, context, daily_task, time='09:00')
    
    # 注册间隔任务
    def interval_task():
        print("间隔任务执行")
    
    run_interval(engine, context, interval_task, 60)
    
    # 验证两种任务都被注册
    assert hasattr(engine, 'daily_tasks'), "应该有每日任务"
    assert hasattr(engine, 'interval_tasks'), "应该有间隔任务"
    
    assert len(engine.daily_tasks) == 1, "应该有一个每日任务"
    assert len(engine.interval_tasks) == 1, "应该有一个间隔任务"
    
    # 验证任务内容
    daily_task_info = engine.daily_tasks[0]
    interval_task_info = engine.interval_tasks[0]
    
    assert daily_task_info['func'] == daily_task, "每日任务函数应该匹配"
    assert daily_task_info['time'] == '09:00', "每日任务时间应该匹配"
    
    assert interval_task_info['func'] == interval_task, "间隔任务函数应该匹配"
    assert interval_task_info['seconds'] == 60, "间隔任务秒数应该匹配"
    
    print("✅ run_daily与run_interval集成测试完成")


def test_ptrade_compatibility():
    """测试PTrade兼容性"""
    print("\n=== PTrade兼容性测试 ===")
    
    class MockEngine:
        def __init__(self):
            pass
    
    class MockContext:
        def __init__(self):
            pass
    
    engine = MockEngine()
    context = MockContext()
    
    # 模拟PTrade风格的使用
    def before_market_open():
        """盘前准备函数"""
        print("盘前准备工作")
    
    def after_market_close():
        """盘后处理函数"""
        print("盘后处理工作")
    
    def lunch_break():
        """午休时间函数"""
        print("午休时间处理")
    
    # 注册多个时间点的任务（模拟PTrade的典型用法）
    run_daily(engine, context, before_market_open, time='09:15')  # 盘前
    run_daily(engine, context, lunch_break, time='12:00')         # 午休
    run_daily(engine, context, after_market_close, time='15:30')  # 盘后
    
    # 验证所有任务都被正确注册
    assert len(engine.daily_tasks) == 3, "应该有三个每日任务"
    
    # 验证时间顺序
    times = [task['time'] for task in engine.daily_tasks]
    expected_times = ['09:15', '12:00', '15:30']
    assert times == expected_times, f"时间应该按注册顺序: {times}"
    
    # 验证函数对应关系
    functions = [task['func'] for task in engine.daily_tasks]
    expected_functions = [before_market_open, lunch_break, after_market_close]
    assert functions == expected_functions, "函数应该按注册顺序"
    
    print("✅ PTrade兼容性测试完成")


def main():
    """运行所有测试"""
    print("开始测试run_daily API...")
    
    try:
        test_run_daily()
        test_run_daily_with_lambda()
        test_run_daily_integration()
        test_ptrade_compatibility()
        
        print("\n🎉 所有run_daily API测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
