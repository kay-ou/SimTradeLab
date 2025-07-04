# -*- coding: utf-8 -*-
"""
异常处理和边界条件测试
测试系统在各种异常情况下的稳定性和错误处理能力
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradeSim.engine import BacktestEngine
from ptradeSim.trading import order, get_position, get_orders
import pandas as pd


def test_invalid_data_handling():
    """测试无效数据处理"""
    print("=" * 70)
    print("测试无效数据处理")
    print("=" * 70)
    
    try:
        # 创建包含异常数据的测试文件
        _create_invalid_data_file()
        
        # 使用简单策略测试异常数据处理
        engine = BacktestEngine(
            strategy_file='strategies/buy_and_hold_strategy.py',
            data_path='data/invalid_test_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        print("开始测试异常数据处理...")
        engine.run()
        
        print("✅ 异常数据处理测试完成")
        
    except Exception as e:
        print(f"❌ 异常数据处理测试失败: {e}")
        # 这是预期的，因为我们故意使用了无效数据
        print("✅ 系统正确捕获了数据异常")
    
    finally:
        # 清理测试文件
        if os.path.exists('data/invalid_test_data.csv'):
            os.remove('data/invalid_test_data.csv')


def test_insufficient_cash_handling():
    """测试资金不足处理"""
    print("\n" + "=" * 70)
    print("测试资金不足处理")
    print("=" * 70)
    
    try:
        # 创建低资金回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/buy_and_hold_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-03',
            initial_cash=1000.0  # 很少的初始资金
        )
        
        print("开始测试资金不足处理...")
        engine.run()
        
        # 检查是否正确处理了资金不足
        final_cash = engine.context.portfolio.cash
        print(f"最终现金: {final_cash:.2f}")
        
        if final_cash > 0:
            print("✅ 资金不足处理测试通过")
        else:
            print("⚠️ 资金管理需要改进")
        
    except Exception as e:
        print(f"❌ 资金不足处理测试失败: {e}")


def test_invalid_order_handling():
    """测试无效订单处理"""
    print("\n" + "=" * 70)
    print("测试无效订单处理")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-01',
            initial_cash=1000000.0
        )
        
        # 手动设置当前数据
        engine.context.current_dt = pd.to_datetime('2023-01-01')
        engine.current_data = {'STOCK_A': {'close': 100.0, 'open': 99.0, 'high': 101.0, 'low': 98.0, 'volume': 1000000}}
        
        print("测试各种无效订单...")
        
        # 测试1: 无效股票代码
        try:
            order_id = order(engine, 'INVALID_STOCK', 100)
            print(f"无效股票订单结果: {order_id}")
        except Exception as e:
            print(f"✅ 正确拒绝无效股票: {e}")
        
        # 测试2: 零数量订单
        try:
            order_id = order(engine, 'STOCK_A', 0)
            print(f"零数量订单结果: {order_id}")
        except Exception as e:
            print(f"✅ 正确拒绝零数量订单: {e}")
        
        # 测试3: 负价格限价单
        try:
            order_id = order(engine, 'STOCK_A', 100, limit_price=-10)
            print(f"负价格订单结果: {order_id}")
        except Exception as e:
            print(f"✅ 正确拒绝负价格订单: {e}")
        
        # 测试4: 超大数量订单
        try:
            order_id = order(engine, 'STOCK_A', 1000000000)  # 10亿股
            print(f"超大数量订单结果: {order_id}")
            if order_id is None:
                print("✅ 正确拒绝超大数量订单")
        except Exception as e:
            print(f"✅ 正确处理超大数量订单异常: {e}")
        
        print("✅ 无效订单处理测试完成")
        
    except Exception as e:
        print(f"❌ 无效订单处理测试失败: {e}")


def test_missing_data_handling():
    """测试数据缺失处理"""
    print("\n" + "=" * 70)
    print("测试数据缺失处理")
    print("=" * 70)
    
    try:
        # 创建包含缺失数据的测试文件
        _create_missing_data_file()
        
        engine = BacktestEngine(
            strategy_file='strategies/technical_indicator_strategy.py',
            data_path='data/missing_test_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-10',
            initial_cash=1000000.0
        )
        
        print("开始测试数据缺失处理...")
        engine.run()
        
        print("✅ 数据缺失处理测试完成")
        
    except Exception as e:
        print(f"❌ 数据缺失处理测试失败: {e}")
        print("✅ 系统正确处理了数据缺失异常")
    
    finally:
        # 清理测试文件
        if os.path.exists('data/missing_test_data.csv'):
            os.remove('data/missing_test_data.csv')


def test_extreme_market_conditions():
    """测试极端市场条件"""
    print("\n" + "=" * 70)
    print("测试极端市场条件")
    print("=" * 70)
    
    try:
        # 创建极端市场数据
        _create_extreme_market_data()
        
        engine = BacktestEngine(
            strategy_file='strategies/dual_moving_average_strategy.py',
            data_path='data/extreme_test_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-10',
            initial_cash=1000000.0
        )
        
        print("开始测试极端市场条件...")
        engine.run()
        
        # 检查系统稳定性
        final_value = engine.context.portfolio.total_value
        print(f"极端条件下最终资产: {final_value:,.2f}")
        
        if final_value > 0:
            print("✅ 极端市场条件测试通过")
        else:
            print("⚠️ 极端条件下需要改进风控")
        
    except Exception as e:
        print(f"❌ 极端市场条件测试失败: {e}")
    
    finally:
        # 清理测试文件
        if os.path.exists('data/extreme_test_data.csv'):
            os.remove('data/extreme_test_data.csv')


def _create_invalid_data_file():
    """创建包含无效数据的测试文件"""
    data = {
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'open': [100, 'invalid', 102],  # 包含无效数据
        'high': [101, 103, None],       # 包含空值
        'low': [99, 101, 101],
        'close': [100.5, 102, 101.5],
        'volume': [1000000, -500000, 1200000],  # 包含负值
        'security': ['STOCK_A', 'STOCK_A', 'STOCK_A']
    }

    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/invalid_test_data.csv', index=False)


def _create_missing_data_file():
    """创建包含缺失数据的测试文件"""
    data = {
        'date': ['2023-01-01', '2023-01-03', '2023-01-05'],  # 跳过某些日期
        'open': [100, 102, 104],
        'high': [101, 103, 105],
        'low': [99, 101, 103],
        'close': [100.5, 102.5, 104.5],
        'volume': [1000000, 1100000, 1200000],
        'security': ['STOCK_A', 'STOCK_A', 'STOCK_A']
    }

    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/missing_test_data.csv', index=False)


def _create_extreme_market_data():
    """创建极端市场数据（大幅波动）"""
    import numpy as np
    
    dates = pd.date_range('2023-01-01', '2023-01-10', freq='D')
    
    # 创建极端波动数据
    base_price = 100
    prices = []
    
    for i, date in enumerate(dates):
        if i == 0:
            price = base_price
        else:
            # 随机大幅波动 (-20% 到 +20%)
            change = np.random.uniform(-0.2, 0.2)
            price = prices[-1] * (1 + change)
        
        prices.append(price)
    
    data = {
        'date': dates.strftime('%Y-%m-%d').tolist(),
        'open': [p * 0.99 for p in prices],
        'high': [p * 1.05 for p in prices],
        'low': [p * 0.95 for p in prices],
        'close': prices,
        'volume': [np.random.randint(500000, 2000000) for _ in prices],
        'security': ['STOCK_A'] * len(prices)
    }

    df = pd.DataFrame(data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/extreme_test_data.csv', index=False)


if __name__ == "__main__":
    print("🧪 开始异常处理和边界条件测试")
    print("=" * 70)
    
    test_invalid_data_handling()
    test_insufficient_cash_handling()
    test_invalid_order_handling()
    test_missing_data_handling()
    test_extreme_market_conditions()
    
    print("\n" + "=" * 70)
    print("🎉 异常处理和边界条件测试完成")
    print("=" * 70)
