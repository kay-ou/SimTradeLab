#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分钟级交易综合测试脚本
测试引擎对日线和分钟级交易周期的支持，包括策略测试和功能验证
"""

import pandas as pd
from ptradeSim import BacktestEngine

def test_daily_trading():
    """测试日线交易"""
    print("🧪 测试日线交易")
    print("-" * 40)
    
    try:
        # 创建日线回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2022-11-01',
            end_date='2022-11-03',
            initial_cash=1000000.0,
            frequency='1d'  # 日线频率
        )
        
        print(f"✅ 日线引擎创建成功")
        print(f"   - 数据加载: {len(engine.data)} 只股票")
        print(f"   - 交易频率: {engine.frequency}")
        
        # 检查数据时间间隔
        first_stock = list(engine.data.keys())[0]
        sample_data = engine.data[first_stock]
        print(f"   - 数据时间范围: {sample_data.index[0]} 到 {sample_data.index[-1]}")
        print(f"   - 数据条数: {len(sample_data)}")
        
        # 运行回测
        engine.run()
        
        print(f"✅ 日线回测完成")
        print(f"   - 投资组合历史记录: {len(engine.portfolio_history)} 条")
        print(f"   - 最终资产: {engine.portfolio.total_value:.2f}")
        
        assert True  # 替换 return 为 assert
        
    except Exception as e:
        print(f"❌ 日线交易测试失败: {e}")
        assert False  # 替换 return 为 assert

def test_minute_trading():
    """测试分钟级交易"""
    print("\n🧪 测试分钟级交易")
    print("-" * 40)
    
    try:
        # 创建分钟级回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2022-11-01',
            end_date='2022-11-01',  # 只测试一天
            initial_cash=1000000.0,
            frequency='15m'  # 15分钟频率
        )
        
        print(f"✅ 分钟级引擎创建成功")
        print(f"   - 数据加载: {len(engine.data)} 只股票")
        print(f"   - 交易频率: {engine.frequency}")
        
        # 检查生成的分钟级数据
        first_stock = list(engine.data.keys())[0]
        sample_data = engine.data[first_stock]
        print(f"   - 分钟级数据时间范围: {sample_data.index[0]} 到 {sample_data.index[-1]}")
        print(f"   - 分钟级数据条数: {len(sample_data)}")
        
        # 显示前几条分钟级数据
        print(f"   - 前5条分钟级数据:")
        for i, (time, row) in enumerate(sample_data.head().iterrows()):
            print(f"     {time}: 开={row['open']:.2f}, 收={row['close']:.2f}, 量={row['volume']:.0f}")
        
        # 运行回测
        engine.run()
        
        print(f"✅ 分钟级回测完成")
        print(f"   - 投资组合历史记录: {len(engine.portfolio_history)} 条")
        print(f"   - 最终资产: {engine.portfolio.total_value:.2f}")
        
        assert True  # 替换 return 为 assert
        
    except Exception as e:
        print(f"❌ 分钟级交易测试失败: {e}")
        import traceback
        traceback.print_exc()
        assert False  # 替换 return 为 assert

def test_different_frequencies():
    """测试不同的交易频率"""
    print("\n🧪 测试不同交易频率")
    print("-" * 40)
    
    frequencies = ['1d', '30m', '15m', '5m', '1m']
    results = {}
    
    for freq in frequencies:
        try:
            print(f"测试频率: {freq}")
            
            engine = BacktestEngine(
                strategy_file='strategies/buy_and_hold.py',
                data_path='data/sample_data.csv',
                start_date='2022-11-01',
                end_date='2022-11-01',  # 只测试一天
                initial_cash=1000000.0,
                frequency=freq
            )
            
            # 获取数据统计
            first_stock = list(engine.data.keys())[0]
            data_count = len(engine.data[first_stock])
            
            # 运行回测
            engine.run()
            
            results[freq] = {
                'data_points': data_count,
                'portfolio_records': len(engine.portfolio_history),
                'final_value': engine.portfolio.total_value,
                'status': '✅ 成功'
            }
            
            print(f"   ✅ {freq}: {data_count} 个数据点, 最终资产: {engine.portfolio.total_value:.2f}")
            
        except Exception as e:
            results[freq] = {
                'status': f'❌ 失败: {e}'
            }
            print(f"   ❌ {freq}: 失败 - {e}")
    
    # 显示结果汇总
    print(f"\n📊 频率测试结果汇总:")
    print(f"{'频率':<8} {'数据点':<10} {'记录数':<10} {'最终资产':<15} {'状态'}")
    print("-" * 60)
    
    for freq, result in results.items():
        if 'data_points' in result:
            print(f"{freq:<8} {result['data_points']:<10} {result['portfolio_records']:<10} "
                  f"{result['final_value']:<15.2f} {result['status']}")
        else:
            print(f"{freq:<8} {'N/A':<10} {'N/A':<10} {'N/A':<15} {result['status']}")

def create_minute_sample_data():
    """创建分钟级样本数据文件用于测试"""
    print("\n🔧 创建分钟级样本数据")
    print("-" * 40)
    
    try:
        # 生成一天的分钟级数据
        import numpy as np
        
        # 交易时间：9:30-11:30, 13:00-15:00
        morning_times = pd.date_range('2022-11-01 09:30:00', '2022-11-01 11:30:00', freq='1T')
        afternoon_times = pd.date_range('2022-11-01 13:00:00', '2022-11-01 15:00:00', freq='1T')
        trading_times = morning_times.union(afternoon_times)
        
        minute_data = []
        
        # 为两只股票生成数据
        for security in ['STOCK_A', 'STOCK_B']:
            base_price = 100 if security == 'STOCK_A' else 50
            
            for i, time in enumerate(trading_times):
                # 模拟价格波动
                np.random.seed(int(time.timestamp()) % 10000)
                price_change = np.random.normal(0, 0.5)  # 0.5元的标准差
                
                close_price = base_price + price_change
                open_price = close_price + np.random.normal(0, 0.1)
                high_price = max(open_price, close_price) + abs(np.random.normal(0, 0.2))
                low_price = min(open_price, close_price) - abs(np.random.normal(0, 0.2))
                volume = np.random.randint(10000, 50000)
                
                minute_data.append({
                    'datetime': time,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume,
                    'security': security
                })
        
        # 保存为CSV文件
        minute_df = pd.DataFrame(minute_data)
        minute_df.to_csv('data/minute_sample_data.csv', index=False)
        
        print(f"✅ 分钟级样本数据创建成功")
        print(f"   - 文件: data/minute_sample_data.csv")
        print(f"   - 数据条数: {len(minute_df)}")
        print(f"   - 时间范围: {minute_df['datetime'].min()} 到 {minute_df['datetime'].max()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建分钟级样本数据失败: {e}")
        return False

def test_minute_data_file():
    """测试使用分钟级数据文件"""
    print("\n🧪 测试分钟级数据文件")
    print("-" * 40)
    
    try:
        # 使用分钟级数据文件进行回测
        engine = BacktestEngine(
            strategy_file='strategies/buy_and_hold.py',
            data_path='data/minute_sample_data.csv',
            start_date='2022-11-01 10:00:00',
            end_date='2022-11-01 14:00:00',
            initial_cash=1000000.0,
            frequency='1m'  # 1分钟频率
        )
        
        print(f"✅ 分钟级数据文件加载成功")
        
        # 检查数据
        first_stock = list(engine.data.keys())[0]
        sample_data = engine.data[first_stock]
        print(f"   - 数据条数: {len(sample_data)}")
        print(f"   - 时间范围: {sample_data.index[0]} 到 {sample_data.index[-1]}")
        
        # 运行回测
        engine.run()
        
        print(f"✅ 分钟级数据回测完成")
        print(f"   - 投资组合记录: {len(engine.portfolio_history)} 条")
        print(f"   - 最终资产: {engine.portfolio.total_value:.2f}")
        
        assert True  # 替换 return 为 assert
        
    except Exception as e:
        print(f"❌ 分钟级数据文件测试失败: {e}")
        assert False  # 替换 return 为 assert

def test_minute_strategy():
    """测试分钟级交易策略"""
    print("\n🧪 测试分钟级交易策略")
    print("-" * 40)

    try:
        # 使用分钟级数据和策略
        engine = BacktestEngine(
            strategy_file='strategies/minute_trading_strategy.py',
            data_path='data/minute_sample_data.csv',
            start_date='2022-11-01 10:00:00',
            end_date='2022-11-01 14:00:00',
            initial_cash=1000000.0,
            frequency='5m'  # 5分钟频率
        )

        print(f"✅ 分钟级策略引擎创建成功")
        print(f"   - 交易频率: {engine.frequency}")
        print(f"   - 数据股票数: {len(engine.data)}")

        # 检查数据
        first_stock = list(engine.data.keys())[0]
        sample_data = engine.data[first_stock]
        print(f"   - 数据时间范围: {sample_data.index[0]} 到 {sample_data.index[-1]}")
        print(f"   - 数据条数: {len(sample_data)}")

        # 运行回测
        print("   🚀 开始运行分钟级策略回测...")
        engine.run()

        print(f"✅ 分钟级策略回测完成")
        print(f"   - 投资组合记录: {len(engine.portfolio_history)} 条")
        print(f"   - 最终资产: {engine.portfolio.total_value:.2f}")
        print(f"   - 现金余额: {engine.portfolio.cash:.2f}")

        # 显示持仓情况
        if engine.portfolio.positions:
            print(f"   - 最终持仓:")
            for stock, pos in engine.portfolio.positions.items():
                pnl = pos.value - pos.amount * pos.cost_basis
                pnl_pct = (pnl / (pos.amount * pos.cost_basis)) * 100 if pos.amount > 0 else 0
                print(f"     {stock}: {pos.amount}股, 成本{pos.cost_basis:.2f}, "
                      f"现价{pos.last_sale_price:.2f}, 盈亏{pnl:.2f}({pnl_pct:.2f}%)")
        else:
            print(f"   - 无持仓")

        assert True  # 替换 return 为 assert

    except Exception as e:
        print(f"❌ 分钟级策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        assert False  # 替换 return 为 assert

def test_strategy_comparison():
    """对比日线和分钟级策略效果"""
    print("\n🔍 对比日线和分钟级策略效果")
    print("-" * 40)

    results = {}

    # 测试日线策略
    try:
        print("测试日线策略...")
        daily_engine = BacktestEngine(
            strategy_file='strategies/buy_and_hold.py',
            data_path='data/sample_data.csv',
            start_date='2022-11-01',
            end_date='2022-11-03',
            initial_cash=1000000.0,
            frequency='1d'
        )
        daily_engine.run()

        results['日线'] = {
            'final_value': daily_engine.portfolio.total_value,
            'records': len(daily_engine.portfolio_history),
            'return_pct': (daily_engine.portfolio.total_value - 1000000) / 1000000 * 100
        }
        print(f"✅ 日线策略完成: 最终资产 {daily_engine.portfolio.total_value:.2f}")

    except Exception as e:
        print(f"❌ 日线策略失败: {e}")
        results['日线'] = {'error': str(e)}

    # 测试分钟级策略
    try:
        print("测试分钟级策略...")
        minute_engine = BacktestEngine(
            strategy_file='strategies/minute_trading_strategy.py',
            data_path='data/minute_sample_data.csv',
            start_date='2022-11-01 10:00:00',
            end_date='2022-11-01 14:00:00',
            initial_cash=1000000.0,
            frequency='5m'
        )
        minute_engine.run()

        results['分钟级'] = {
            'final_value': minute_engine.portfolio.total_value,
            'records': len(minute_engine.portfolio_history),
            'return_pct': (minute_engine.portfolio.total_value - 1000000) / 1000000 * 100
        }
        print(f"✅ 分钟级策略完成: 最终资产 {minute_engine.portfolio.total_value:.2f}")

    except Exception as e:
        print(f"❌ 分钟级策略失败: {e}")
        results['分钟级'] = {'error': str(e)}

    # 显示对比结果
    print(f"\n📊 策略对比结果:")
    print(f"{'策略类型':<10} {'最终资产':<15} {'收益率':<10} {'记录数':<10}")
    print("-" * 50)

    for strategy_type, result in results.items():
        if 'error' in result:
            print(f"{strategy_type:<10} {'错误':<15} {'N/A':<10} {'N/A':<10}")
        else:
            print(f"{strategy_type:<10} {result['final_value']:<15.2f} "
                  f"{result['return_pct']:<10.3f}% {result['records']:<10}")

    return len([r for r in results.values() if 'error' not in r]) == len(results)

def main():
    """主测试函数"""
    print("🚀 ptradeSim 分钟级交易综合测试")
    print("=" * 60)

    # 测试计数
    total_tests = 0
    passed_tests = 0

    # 1. 测试日线交易
    total_tests += 1
    if test_daily_trading():
        passed_tests += 1

    # 2. 测试分钟级交易
    total_tests += 1
    if test_minute_trading():
        passed_tests += 1

    # 3. 测试不同频率
    total_tests += 1
    try:
        test_different_frequencies()
        passed_tests += 1
    except:
        print("❌ 不同频率测试失败")

    # 4. 创建分钟级数据文件
    total_tests += 1
    if create_minute_sample_data():
        passed_tests += 1

    # 5. 测试分钟级数据文件
    total_tests += 1
    if test_minute_data_file():
        passed_tests += 1

    # 6. 测试分钟级策略
    total_tests += 1
    if test_minute_strategy():
        passed_tests += 1

    # 7. 策略对比测试
    total_tests += 1
    if test_strategy_comparison():
        passed_tests += 1

    # 显示测试结果
    print("\n" + "=" * 60)
    print(f"🎉 分钟级交易综合测试完成!")
    print(f"📊 测试结果: {passed_tests}/{total_tests} 通过")

    if passed_tests == total_tests:
        print("✅ 所有测试通过! 分钟级交易功能正常工作")
        print("\n📋 测试覆盖范围:")
        print("  ✅ 日线交易功能")
        print("  ✅ 分钟级交易功能")
        print("  ✅ 多频率支持 (1d/30m/15m/5m/1m)")
        print("  ✅ 分钟级数据生成")
        print("  ✅ 分钟级数据文件处理")
        print("  ✅ 分钟级交易策略")
        print("  ✅ 策略效果对比")
    else:
        print(f"⚠️ {total_tests - passed_tests} 个测试失败，需要检查")

if __name__ == "__main__":
    main()
