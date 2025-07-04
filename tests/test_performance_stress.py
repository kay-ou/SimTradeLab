# -*- coding: utf-8 -*-
"""
性能压力测试
测试系统在大数据量和长时间运行下的性能表现
"""
import sys
import os
import time
import psutil
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradeSim.engine import BacktestEngine


def test_large_dataset_performance():
    """测试大数据集性能"""
    print("=" * 70)
    print("测试大数据集性能")
    print("=" * 70)
    
    try:
        # 创建大数据集
        print("创建大数据集（1年日线数据）...")
        _create_large_dataset()
        
        # 记录开始时间和内存
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        print(f"开始时间: {time.strftime('%H:%M:%S')}")
        print(f"开始内存: {start_memory:.1f} MB")
        
        # 运行回测
        engine = BacktestEngine(
            strategy_file='strategies/technical_indicator_strategy.py',
            data_path='data/large_test_data.csv',
            start_date='2022-01-01',
            end_date='2022-12-31',
            initial_cash=1000000.0
        )
        
        print("开始大数据集回测...")
        engine.run()
        
        # 记录结束时间和内存
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        print(f"\n性能统计:")
        print(f"执行时间: {execution_time:.2f} 秒")
        print(f"内存增长: {memory_usage:.1f} MB")
        print(f"最终资产: {engine.context.portfolio.total_value:,.2f}")
        
        # 性能评估
        if execution_time < 60:  # 1分钟内完成
            print("✅ 大数据集性能测试通过")
        else:
            print("⚠️ 大数据集处理较慢，需要优化")
        
    except Exception as e:
        print(f"❌ 大数据集性能测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if os.path.exists('data/large_test_data.csv'):
            os.remove('data/large_test_data.csv')


def test_multiple_securities_performance():
    """测试多股票性能"""
    print("\n" + "=" * 70)
    print("测试多股票性能")
    print("=" * 70)
    
    try:
        # 创建多股票数据
        print("创建多股票数据集（10只股票，3个月数据）...")
        _create_multi_stock_dataset()
        
        # 创建多股票策略
        _create_multi_stock_strategy()
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 运行回测
        engine = BacktestEngine(
            strategy_file='strategies/multi_stock_test_strategy.py',
            data_path='data/multi_stock_data.csv',
            start_date='2023-01-01',
            end_date='2023-03-31',
            initial_cash=1000000.0
        )
        
        print("开始多股票回测...")
        engine.run()
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        print(f"\n多股票性能统计:")
        print(f"执行时间: {execution_time:.2f} 秒")
        print(f"内存增长: {memory_usage:.1f} MB")
        print(f"最终资产: {engine.context.portfolio.total_value:,.2f}")
        
        if execution_time < 30:
            print("✅ 多股票性能测试通过")
        else:
            print("⚠️ 多股票处理较慢，需要优化")
        
    except Exception as e:
        print(f"❌ 多股票性能测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        for file in ['data/multi_stock_data.csv', 'strategies/multi_stock_test_strategy.py']:
            if os.path.exists(file):
                os.remove(file)


def test_high_frequency_trading():
    """测试高频交易性能"""
    print("\n" + "=" * 70)
    print("测试高频交易性能")
    print("=" * 70)
    
    try:
        # 创建分钟级数据
        print("创建分钟级数据（1周数据）...")
        _create_minute_data()
        
        # 创建高频策略
        _create_high_frequency_strategy()
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # 运行分钟级回测
        engine = BacktestEngine(
            strategy_file='strategies/high_freq_test_strategy.py',
            data_path='data/minute_test_data.csv',
            start_date='2023-01-02 09:30:00',
            end_date='2023-01-06 15:00:00',
            initial_cash=1000000.0,
            frequency='1m'
        )
        
        print("开始高频交易回测...")
        engine.run()
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        
        print(f"\n高频交易性能统计:")
        print(f"执行时间: {execution_time:.2f} 秒")
        print(f"内存增长: {memory_usage:.1f} MB")
        print(f"最终资产: {engine.context.portfolio.total_value:,.2f}")
        
        if execution_time < 45:
            print("✅ 高频交易性能测试通过")
        else:
            print("⚠️ 高频交易处理较慢，需要优化")
        
    except Exception as e:
        print(f"❌ 高频交易性能测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        for file in ['data/minute_test_data.csv', 'strategies/high_freq_test_strategy.py']:
            if os.path.exists(file):
                os.remove(file)


def test_memory_leak():
    """测试内存泄漏"""
    print("\n" + "=" * 70)
    print("测试内存泄漏")
    print("=" * 70)
    
    try:
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"初始内存: {initial_memory:.1f} MB")
        
        # 连续运行多次回测
        for i in range(5):
            print(f"第 {i+1} 次回测...")
            
            engine = BacktestEngine(
                strategy_file='strategies/buy_and_hold_strategy.py',
                data_path='data/sample_data.csv',
                start_date='2023-01-01',
                end_date='2023-01-10',
                initial_cash=1000000.0
            )
            
            engine.run()
            
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_growth = current_memory - initial_memory
            
            print(f"   当前内存: {current_memory:.1f} MB, 增长: {memory_growth:.1f} MB")
            
            # 强制垃圾回收
            import gc
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        total_growth = final_memory - initial_memory
        
        print(f"\n内存泄漏测试结果:")
        print(f"总内存增长: {total_growth:.1f} MB")
        
        if total_growth < 50:  # 50MB以内认为正常
            print("✅ 内存泄漏测试通过")
        else:
            print("⚠️ 可能存在内存泄漏，需要检查")
        
    except Exception as e:
        print(f"❌ 内存泄漏测试失败: {e}")


def _create_large_dataset():
    """创建大数据集"""
    dates = pd.date_range('2022-01-01', '2022-12-31', freq='D')
    
    # 生成随机价格数据
    np.random.seed(42)  # 固定随机种子
    base_price = 100
    prices = [base_price]
    
    for _ in range(len(dates) - 1):
        change = np.random.normal(0, 0.02)  # 2%标准差
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1))  # 价格不能为负
    
    data = {
        'date': dates.strftime('%Y-%m-%d').tolist(),
        'open': [p * np.random.uniform(0.99, 1.01) for p in prices],
        'high': [p * np.random.uniform(1.00, 1.05) for p in prices],
        'low': [p * np.random.uniform(0.95, 1.00) for p in prices],
        'close': prices,
        'volume': [np.random.randint(500000, 2000000) for _ in prices],
        'security': ['STOCK_A'] * len(prices)
    }

    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/large_test_data.csv', index=False)


def _create_multi_stock_dataset():
    """创建多股票数据集"""
    dates = pd.date_range('2023-01-01', '2023-03-31', freq='D')
    stocks = [f'STOCK_{chr(65+i)}' for i in range(10)]  # STOCK_A to STOCK_J

    all_data = []

    for stock in stocks:
        np.random.seed(hash(stock) % 1000)  # 每只股票不同的随机种子
        base_price = np.random.uniform(50, 200)
        prices = [base_price]

        for _ in range(len(dates) - 1):
            change = np.random.normal(0, 0.015)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1))

        for i, date in enumerate(dates):
            all_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': prices[i] * np.random.uniform(0.99, 1.01),
                'high': prices[i] * np.random.uniform(1.00, 1.03),
                'low': prices[i] * np.random.uniform(0.97, 1.00),
                'close': prices[i],
                'volume': np.random.randint(100000, 1000000),
                'security': stock
            })

    df = pd.DataFrame(all_data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/multi_stock_data.csv', index=False)


def _create_minute_data():
    """创建分钟级数据"""
    # 创建一周的分钟级数据（交易时间）
    dates = pd.date_range('2023-01-02 09:30:00', '2023-01-06 15:00:00', freq='1min')
    # 过滤交易时间
    dates = dates[(dates.hour >= 9) & (dates.hour < 15) | 
                  ((dates.hour == 9) & (dates.minute >= 30)) |
                  ((dates.hour == 15) & (dates.minute == 0))]
    
    np.random.seed(42)
    base_price = 100
    prices = [base_price]
    
    for _ in range(len(dates) - 1):
        change = np.random.normal(0, 0.001)  # 0.1%标准差
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1))
    
    data = {
        'datetime': dates.strftime('%Y-%m-%d %H:%M:%S').tolist(),
        'open': [p * np.random.uniform(0.999, 1.001) for p in prices],
        'high': [p * np.random.uniform(1.000, 1.002) for p in prices],
        'low': [p * np.random.uniform(0.998, 1.000) for p in prices],
        'close': prices,
        'volume': [np.random.randint(1000, 10000) for _ in prices],
        'security': ['STOCK_A'] * len(prices)
    }

    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/minute_test_data.csv', index=False)


def _create_multi_stock_strategy():
    """创建多股票测试策略"""
    strategy_code = '''# -*- coding: utf-8 -*-
"""多股票测试策略"""

def initialize(context):
    g.stocks = ['STOCK_A', 'STOCK_B', 'STOCK_C', 'STOCK_D', 'STOCK_E']
    g.trade_count = 0

def handle_data(context, data):
    if g.trade_count < 10:
        for stock in g.stocks:
            if stock in data and g.trade_count < 10:
                order(stock, 100)
                g.trade_count += 1

def before_trading_start(context, data):
    pass

def after_trading_end(context, data):
    pass
'''
    
    os.makedirs('strategies', exist_ok=True)
    with open('strategies/multi_stock_test_strategy.py', 'w', encoding='utf-8') as f:
        f.write(strategy_code)


def _create_high_frequency_strategy():
    """创建高频测试策略"""
    strategy_code = '''# -*- coding: utf-8 -*-
"""高频测试策略"""

def initialize(context):
    g.security = 'STOCK_A'
    g.last_price = None
    g.trade_count = 0

def handle_data(context, data):
    if g.security not in data:
        return
    
    current_price = data[g.security]['close']
    
    if g.last_price and g.trade_count < 50:
        price_change = (current_price - g.last_price) / g.last_price
        
        if price_change > 0.001:  # 0.1%上涨
            order(g.security, 100)
            g.trade_count += 1
        elif price_change < -0.001:  # 0.1%下跌
            position = get_position(g.security)
            if position and position['amount'] > 0:
                order(g.security, -min(100, position['amount']))
                g.trade_count += 1
    
    g.last_price = current_price

def before_trading_start(context, data):
    pass

def after_trading_end(context, data):
    pass
'''
    
    os.makedirs('strategies', exist_ok=True)
    with open('strategies/high_freq_test_strategy.py', 'w', encoding='utf-8') as f:
        f.write(strategy_code)


if __name__ == "__main__":
    print("🚀 开始性能压力测试")
    print("=" * 70)
    
    test_large_dataset_performance()
    test_multiple_securities_performance()
    test_high_frequency_trading()
    test_memory_leak()
    
    print("\n" + "=" * 70)
    print("🎉 性能压力测试完成")
    print("=" * 70)
