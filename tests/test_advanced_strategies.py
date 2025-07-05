# -*- coding: utf-8 -*-
"""
高级策略测试
测试新增的实用策略：双均线、网格交易、动量策略
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.engine import BacktestEngine


def test_dual_moving_average_strategy():
    """测试双均线交叉策略"""
    print("=" * 70)
    print("测试双均线交叉策略")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/dual_moving_average_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0
        )
        
        print("开始运行双均线交叉策略...")
        print("策略说明：基于5日和20日移动平均线的金叉死叉信号进行交易")
        
        # 运行回测
        engine.run()
        
        # 输出回测结果
        print("\n" + "=" * 70)
        print("双均线策略回测结果")
        print("=" * 70)
        
        final_portfolio = engine.context.portfolio
        initial_cash = engine.initial_cash
        total_return = (final_portfolio.total_value - initial_cash) / initial_cash
        
        print(f"初始资金: {initial_cash:,.2f}")
        print(f"最终总资产: {final_portfolio.total_value:,.2f}")
        print(f"最终现金: {final_portfolio.cash:,.2f}")
        print(f"总收益: {final_portfolio.total_value - initial_cash:,.2f}")
        print(f"收益率: {total_return:.2%}")
        
        # 策略特定统计
        if hasattr(engine.context, 'g') and hasattr(engine.context.g, 'signal_count'):
            print(f"交易信号次数: {engine.context.g.signal_count}")
            print(f"最后信号类型: {engine.context.g.last_signal or '无'}")
        
        print("\n✅ 双均线交叉策略测试完成")
        
    except Exception as e:
        print(f"❌ 双均线交叉策略测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_grid_trading_strategy():
    """测试网格交易策略"""
    print("\n" + "=" * 70)
    print("测试网格交易策略")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/grid_trading_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0
        )
        
        print("开始运行网格交易策略...")
        print("策略说明：在价格区间内设置5个网格，通过高抛低吸获取收益")
        
        # 运行回测
        engine.run()
        
        # 输出回测结果
        print("\n" + "=" * 70)
        print("网格交易策略回测结果")
        print("=" * 70)
        
        final_portfolio = engine.context.portfolio
        initial_cash = engine.initial_cash
        total_return = (final_portfolio.total_value - initial_cash) / initial_cash
        
        print(f"初始资金: {initial_cash:,.2f}")
        print(f"最终总资产: {final_portfolio.total_value:,.2f}")
        print(f"最终现金: {final_portfolio.cash:,.2f}")
        print(f"总收益: {final_portfolio.total_value - initial_cash:,.2f}")
        print(f"收益率: {total_return:.2%}")
        
        # 网格策略特定统计
        if hasattr(engine.context, 'g'):
            g = engine.context.g
            if hasattr(g, 'total_trades'):
                print(f"网格交易次数: {g.total_trades}")
            if hasattr(g, 'center_price'):
                print(f"网格中心价格: {g.center_price:.2f}")
            if hasattr(g, 'grid_positions'):
                executed_grids = sum(1 for info in g.grid_positions.values() if info['executed'])
                print(f"已执行网格: {executed_grids}/{len(g.grid_positions)}")
        
        print("\n✅ 网格交易策略测试完成")
        
    except Exception as e:
        print(f"❌ 网格交易策略测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_momentum_strategy():
    """测试动量策略"""
    print("\n" + "=" * 70)
    print("测试动量策略")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/momentum_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0
        )
        
        print("开始运行动量策略...")
        print("策略说明：基于价格动量和成交量的趋势跟踪策略，包含止损机制")
        
        # 运行回测
        engine.run()
        
        # 输出回测结果
        print("\n" + "=" * 70)
        print("动量策略回测结果")
        print("=" * 70)
        
        final_portfolio = engine.context.portfolio
        initial_cash = engine.initial_cash
        total_return = (final_portfolio.total_value - initial_cash) / initial_cash
        
        print(f"初始资金: {initial_cash:,.2f}")
        print(f"最终总资产: {final_portfolio.total_value:,.2f}")
        print(f"最终现金: {final_portfolio.cash:,.2f}")
        print(f"总收益: {final_portfolio.total_value - initial_cash:,.2f}")
        print(f"收益率: {total_return:.2%}")
        
        # 动量策略特定统计
        if hasattr(engine.context, 'g'):
            g = engine.context.g
            if hasattr(g, 'last_momentum'):
                print(f"最终动量: {g.last_momentum:.2%}")
            if hasattr(g, 'trend_direction'):
                print(f"当前趋势: {g.trend_direction or '无'}")
            if hasattr(g, 'entry_price') and g.entry_price:
                print(f"入场价格: {g.entry_price:.2f}")
        
        print("\n✅ 动量策略测试完成")
        
    except Exception as e:
        print(f"❌ 动量策略测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_strategy_comparison():
    """策略对比测试"""
    print("\n" + "=" * 70)
    print("策略对比测试")
    print("=" * 70)
    
    strategies = [
        ('买入持有', 'strategies/buy_and_hold_strategy.py'),
        ('双均线', 'strategies/dual_moving_average_strategy.py'),
        ('网格交易', 'strategies/grid_trading_strategy.py'),
        ('动量策略', 'strategies/momentum_strategy.py'),
    ]
    
    results = []
    
    for strategy_name, strategy_file in strategies:
        try:
            print(f"测试 {strategy_name} 策略...")
            
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path='data/sample_data.csv',
                start_date='2023-01-01',
                end_date='2023-01-31',
                initial_cash=1000000.0
            )
            
            engine.run()
            
            final_value = engine.context.portfolio.total_value
            total_return = (final_value - 1000000) / 1000000
            
            results.append({
                'strategy': strategy_name,
                'final_value': final_value,
                'return': total_return
            })
            
        except Exception as e:
            print(f"   ❌ {strategy_name} 策略测试失败: {e}")
            results.append({
                'strategy': strategy_name,
                'final_value': 0,
                'return': -1
            })
    
    # 显示对比结果
    print("\n" + "=" * 70)
    print("策略对比结果")
    print("=" * 70)
    print(f"{'策略名称':<12} {'最终资产':<15} {'收益率':<10}")
    print("-" * 40)
    
    for result in results:
        if result['final_value'] > 0:
            print(f"{result['strategy']:<12} {result['final_value']:>13,.0f} {result['return']:>8.2%}")
        else:
            print(f"{result['strategy']:<12} {'失败':<15} {'N/A':<10}")
    
    # 找出最佳策略
    valid_results = [r for r in results if r['final_value'] > 0]
    if valid_results:
        best_strategy = max(valid_results, key=lambda x: x['return'])
        print(f"\n🏆 最佳策略: {best_strategy['strategy']} (收益率: {best_strategy['return']:.2%})")
    
    print("\n✅ 策略对比测试完成")


def test_strategy_robustness():
    """策略稳健性测试"""
    print("\n" + "=" * 70)
    print("策略稳健性测试")
    print("=" * 70)
    
    # 测试不同时间段的表现
    test_periods = [
        ('短期', '2023-01-01', '2023-01-10'),
        ('中期', '2023-01-01', '2023-01-20'),
        ('长期', '2023-01-01', '2023-01-31'),
    ]
    
    strategy_file = 'strategies/dual_moving_average_strategy.py'
    
    print("测试双均线策略在不同时间段的表现...")
    
    for period_name, start_date, end_date in test_periods:
        try:
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path='data/sample_data.csv',
                start_date=start_date,
                end_date=end_date,
                initial_cash=1000000.0
            )
            
            engine.run()
            
            final_value = engine.context.portfolio.total_value
            total_return = (final_value - 1000000) / 1000000
            
            print(f"{period_name}测试 ({start_date} 到 {end_date}): 收益率 {total_return:.2%}")
            
        except Exception as e:
            print(f"{period_name}测试失败: {e}")
    
    print("\n✅ 策略稳健性测试完成")


if __name__ == "__main__":
    print("🧪 开始高级策略测试")
    print("=" * 70)
    
    test_dual_moving_average_strategy()
    test_grid_trading_strategy()
    test_momentum_strategy()
    test_strategy_comparison()
    test_strategy_robustness()
    
    print("\n" + "=" * 70)
    print("🎉 高级策略测试完成")
    print("=" * 70)
