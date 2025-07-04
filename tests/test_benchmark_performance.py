# -*- coding: utf-8 -*-
"""
基准设置和性能评估功能测试
包含简单模式和双均线模式的测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradeSim.engine import BacktestEngine


def test_benchmark_simple_mode():
    """测试基准功能 - 简单模式"""
    print("=" * 70)
    print("测试基准功能 - 简单模式")
    print("=" * 70)

    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/benchmark_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-10',
            initial_cash=1000000.0
        )

        print("开始运行基准策略（简单模式）...")

        # 运行回测
        engine.run()

        print("\n✅ 基准策略简单模式测试完成")

    except Exception as e:
        print(f"❌ 基准策略简单模式测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_benchmark_ma_cross_mode():
    """测试基准设置和性能评估功能 - 双均线模式"""
    print("\n" + "=" * 70)
    print("测试基准设置和性能评估功能 - 双均线模式")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/benchmark_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-31',  # 运行一个月的数据
            initial_cash=1000000.0
        )
        
        print("开始运行基准设置和性能评估演示策略...")
        print("策略说明：使用双均线策略，设置基准指数进行对比分析")
        
        # 运行回测
        engine.run()
        
        # 手动验证基准设置
        print("\n" + "=" * 70)
        print("基准设置验证")
        print("=" * 70)
        
        if hasattr(engine, 'benchmark'):
            print(f"✅ 基准指数已设置: {engine.benchmark}")
            
            # 检查基准数据是否存在
            if engine.benchmark in engine.data:
                benchmark_data = engine.data[engine.benchmark]
                print(f"✅ 基准数据已生成，数据点数: {len(benchmark_data)}")
                print(f"   基准数据时间范围: {benchmark_data.index[0]} 到 {benchmark_data.index[-1]}")
                print(f"   基准起始价格: {benchmark_data['close'].iloc[0]:.2f}")
                print(f"   基准结束价格: {benchmark_data['close'].iloc[-1]:.2f}")
                
                # 计算基准收益率
                benchmark_return = (benchmark_data['close'].iloc[-1] / benchmark_data['close'].iloc[0]) - 1
                print(f"   基准总收益率: {benchmark_return:.2%}")
            else:
                print("❌ 基准数据未找到")
        else:
            print("❌ 基准指数未设置")
        
        # 验证性能指标计算
        print("\n" + "=" * 70)
        print("性能指标验证")
        print("=" * 70)
        
        from ptradeSim.performance import calculate_performance_metrics
        from ptradeSim.utils import get_benchmark_returns
        
        # 获取基准收益率
        benchmark_returns = get_benchmark_returns(engine, engine.start_date, engine.end_date)
        
        # 计算性能指标
        metrics = calculate_performance_metrics(engine, benchmark_returns)
        
        if metrics:
            print("✅ 性能指标计算成功")
            print(f"   策略总收益率: {metrics['total_return']:.2%}")
            print(f"   策略年化收益率: {metrics['annualized_return']:.2%}")
            print(f"   策略夏普比率: {metrics['sharpe_ratio']:.3f}")
            print(f"   策略最大回撤: {metrics['max_drawdown']:.2%}")
            
            if 'benchmark_total_return' in metrics:
                print(f"   基准总收益率: {metrics['benchmark_total_return']:.2%}")
                print(f"   Alpha: {metrics['alpha']:.2%}")
                print(f"   Beta: {metrics['beta']:.3f}")
                print(f"   信息比率: {metrics['information_ratio']:.3f}")
        else:
            print("❌ 性能指标计算失败")
        
        # 最终结果汇总
        print("\n" + "=" * 70)
        print("最终结果汇总")
        print("=" * 70)
        
        final_portfolio = engine.context.portfolio
        print(f"初始资金: {engine.initial_cash:,.2f}")
        print(f"最终总资产: {final_portfolio.total_value:,.2f}")
        print(f"最终现金: {final_portfolio.cash:,.2f}")
        print(f"总收益: {final_portfolio.total_value - engine.initial_cash:,.2f}")
        print(f"收益率: {((final_portfolio.total_value / engine.initial_cash) - 1) * 100:.2f}%")
        
        # 持仓情况
        print("\n持仓情况:")
        if final_portfolio.positions:
            for stock, position in final_portfolio.positions.items():
                if position.amount > 0:
                    print(f"  {stock}: {position.amount}股, 成本价: {position.cost_basis:.2f}, 最新价: {position.last_sale_price:.2f}")
        else:
            print("  无持仓")
        
        print("\n✅ 基准设置和性能评估功能测试完成")
        print("📊 详细性能分析报告已在上方自动生成")
        
    except Exception as e:
        print(f"❌ 基准设置和性能评估功能测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_benchmark_simple_mode()
    test_benchmark_ma_cross_mode()
