#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ptradeSim.engine import BacktestEngine
from ptradeSim import api as ptrade_api

def test_complete_injection():
    """测试完整的API和log注入机制"""
    
    print("=== 测试完整的API和log注入机制 ===")
    
    # 创建引擎
    engine = BacktestEngine(
        strategy_file='strategies/buy_and_hold.py',
        data_path='data/sample_data.csv',
        start_date='2023-01-13',
        end_date='2023-01-13',
        initial_cash=1000000.0
    )
    
    strategy = engine.strategy
    
    print("1. 检查log对象注入:")
    print(f"   - 策略是否有log: {hasattr(strategy, 'log')}")
    if hasattr(strategy, 'log'):
        print(f"   - log对象类型: {type(strategy.log)}")
        print(f"   - 与ptrade_api.log相同: {strategy.log is ptrade_api.log}")
    
    print("\n2. 检查关键API函数注入:")
    api_functions = [
        'get_Ashares', 'get_stock_status', 'get_stock_info', 'get_stock_name',
        'get_fundamentals', 'get_history', 'get_price',
        'order', 'order_target', 'order_value', 'set_universe',
        'is_trade', 'get_research_path', 'set_commission', 'set_limit_mode',
        'get_initial_cash', 'get_num_of_positions'
    ]
    
    for func_name in api_functions:
        has_func = hasattr(strategy, func_name)
        print(f"   - {func_name}: {'✓' if has_func else '❌'}")
        
        if has_func:
            func = getattr(strategy, func_name)
            # 检查是否是partial对象（说明正确注入了引擎实例）
            is_partial = hasattr(func, 'func') and hasattr(func, 'args')
            print(f"     (partial绑定: {'✓' if is_partial else '❌'})")
    
    print("\n3. 检查g对象:")
    print(f"   - 策略是否有g对象: {hasattr(strategy, 'g')}")
    
    print("\n4. 测试策略初始化和log使用:")
    try:
        # 初始化策略（这会调用log.set_log_level）
        strategy.initialize(engine.context)
        print("   ✓ 策略初始化成功（包含log.set_log_level调用）")
        
        # 测试策略中的log调用
        if hasattr(strategy, 'g') and hasattr(strategy.g, 'state'):
            print("   ✓ g.state已创建")
            
    except Exception as e:
        print(f"   ❌ 策略初始化或log使用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n5. 测试API函数调用:")
    try:
        # 测试一些关键API函数
        stocks = strategy.get_Ashares()
        print(f"   ✓ get_Ashares(): {stocks}")
        
        stock_status = strategy.get_stock_status(stocks, 'ST')
        print(f"   ✓ get_stock_status(): {len(stock_status)} 个结果")
        
        initial_cash = strategy.get_initial_cash(engine.context, 100000)
        print(f"   ✓ get_initial_cash(): {initial_cash}")
        
    except Exception as e:
        print(f"   ❌ API函数调用失败: {e}")
        import traceback
        traceback.print_exc()

def test_log_injection():
    """测试log对象注入是否正常工作"""
    
    print("\n=== 测试log对象注入 ===")
    
    # 创建引擎
    engine = BacktestEngine(
        strategy_file='strategies/buy_and_hold.py',
        data_path='data/sample_data.csv',
        start_date='2023-01-13',
        end_date='2023-01-13',
        initial_cash=1000000.0
    )
    
    # 检查策略中的log对象
    print(f"1. 策略模块是否有log对象: {hasattr(engine.strategy, 'log')}")
    
    if hasattr(engine.strategy, 'log'):
        strategy_log = engine.strategy.log
        ptrade_log = ptrade_api.log
        
        print(f"2. 策略log对象类型: {type(strategy_log)}")
        print(f"3. ptrade_api log对象类型: {type(ptrade_log)}")
        print(f"4. 两个log对象是否相同: {strategy_log is ptrade_log}")
        
        # 检查log对象的属性和方法
        print(f"5. 策略log是否有LEVEL_INFO: {hasattr(strategy_log, 'LEVEL_INFO')}")
        print(f"6. 策略log是否有set_log_level方法: {hasattr(strategy_log, 'set_log_level')}")
        print(f"7. 策略log是否有info方法: {hasattr(strategy_log, 'info')}")
        
        if hasattr(strategy_log, 'LEVEL_INFO'):
            print(f"8. LEVEL_INFO值: {strategy_log.LEVEL_INFO}")
        
        # 测试log方法调用
        print("\n9. 测试log方法调用:")
        try:
            strategy_log.info("这是来自策略log的测试消息")
            print("   ✓ strategy_log.info() 调用成功")
        except Exception as e:
            print(f"   ❌ strategy_log.info() 调用失败: {e}")
        
        try:
            strategy_log.set_log_level(strategy_log.LEVEL_INFO)
            print("   ✓ strategy_log.set_log_level() 调用成功")
        except Exception as e:
            print(f"   ❌ strategy_log.set_log_level() 调用失败: {e}")
    
    # 测试策略初始化
    print("\n10. 测试策略初始化:")
    try:
        engine.strategy.initialize(engine.context)
        print("   ✓ 策略初始化成功")
    except Exception as e:
        print(f"   ❌ 策略初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_injection()
    test_log_injection()
