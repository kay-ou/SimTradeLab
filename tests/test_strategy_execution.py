#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from ptradesim import BacktestEngine

def test_strategy_execution():
    """测试策略完整执行流程"""
    
    print("=== 测试策略完整执行流程 ===")
    
    # 创建引擎
    engine = BacktestEngine(
        strategy_file='strategies/buy_and_hold_strategy.py',
        data_path='data/sample_data.csv',
        start_date='2023-01-13',
        end_date='2023-01-13',
        initial_cash=1000000.0
    )
    
    # 初始化策略
    engine.strategy.initialize(engine.context)
    
    # 设置交易日
    day = pd.to_datetime('2023-01-13')
    engine.context.current_dt = day
    engine.context.previous_date = day.date()
    engine.current_data = {sec: df.loc[day] for sec, df in engine.data.items() if day in df.index}
    
    print("1. 检查策略函数存在性:")
    functions_to_check = ['initialize', 'before_trading_start', 'handle_data', 'after_trading_end']
    for func_name in functions_to_check:
        has_func = hasattr(engine.strategy, func_name)
        print(f"   - {func_name}: {'✓' if has_func else '❌'}")
    
    print("\n2. 检查初始状态:")
    print(f"   - 初始现金: {engine.portfolio.cash:,.2f}")
    print(f"   - 初始总价值: {engine.portfolio.total_value:,.2f}")
    print(f"   - 初始持仓数量: {len([p for p in engine.portfolio.positions.values() if p.amount > 0])}")
    
    print("\n3. 运行before_trading_start:")
    try:
        engine.strategy.before_trading_start(engine.context, engine.current_data)
        print("   ✓ before_trading_start执行成功")
    except Exception as e:
        print(f"   ❌ before_trading_start执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n4. 运行handle_data:")
    try:
        engine.strategy.handle_data(engine.context, engine.current_data)
        print("   ✓ handle_data执行成功")
    except Exception as e:
        print(f"   ❌ handle_data执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n5. 检查交易后的状态:")
    print(f"   - 引擎现金: {engine.portfolio.cash:,.2f}")
    print(f"   - 引擎总价值: {engine.portfolio.total_value:,.2f}")
    
    # 更新投资组合价值
    current_prices = {sec: data['close'] for sec, data in engine.current_data.items()}
    engine._update_portfolio_value(current_prices)
    
    print("\n6. 测试Logger:")
    try:
        engine.strategy.log.info("测试Logger是否正常工作")
        print("   ✓ Logger测试成功")
    except Exception as e:
        print(f"   ❌ Logger测试失败: {e}")

    print("\n7. 运行after_trading_end:")
    try:
        print("   调用after_trading_end...")
        engine.strategy.after_trading_end(engine.context, engine.current_data)
        print("   ✓ after_trading_end执行成功")
    except Exception as e:
        print(f"   ❌ after_trading_end执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n8. 检查最终状态:")
    print(f"   - 最终现金: {engine.portfolio.cash:,.2f}")
    print(f"   - 最终总价值: {engine.portfolio.total_value:,.2f}")
    print(f"   - 持仓数量: {len([p for p in engine.portfolio.positions.values() if p.amount > 0])}")
    
    for stock, position in engine.portfolio.positions.items():
        if position.amount > 0:
            print(f"   - 持仓 {stock}: {position.amount} 股，成本价 {position.cost_basis:.2f}，市值 {position.market_value:.2f}")

def test_full_backtest():
    """测试完整回测流程"""
    
    print("\n=== 测试完整回测流程 ===")
    
    # 使用buy_and_hold策略进行短期回测
    engine = BacktestEngine(
        strategy_file='strategies/buy_and_hold_strategy.py',
        data_path='data/sample_data.csv',
        start_date='2023-01-13',
        end_date='2023-01-16',  # 测试几天
        initial_cash=1000000.0
    )
    
    # 检查数据加载
    print("1. 数据加载检查:")
    print(f"   - 可用股票: {list(engine.data.keys())}")
    for stock, data in engine.data.items():
        print(f"   - {stock}: {len(data)} 条记录，日期范围 {data.index.min().date()} 到 {data.index.max().date()}")
    
    # 运行回测
    print("\n2. 开始回测:")
    try:
        engine.run()
        print("   ✓ 回测执行成功")
    except Exception as e:
        print(f"   ❌ 回测执行失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 检查最终状态
    print("\n3. 回测结果:")
    print(f"   - 最终现金: {engine.portfolio.cash:,.2f}")
    print(f"   - 最终总价值: {engine.portfolio.total_value:,.2f}")
    print(f"   - 持仓数量: {len([p for p in engine.portfolio.positions.values() if p.amount > 0])}")
    
    for stock, position in engine.portfolio.positions.items():
        if position.amount > 0:
            print(f"   - 持仓 {stock}: {position.amount} 股，成本价 {position.cost_basis:.2f}，市值 {position.market_value:.2f}")
    
    print(f"   - 投资组合历史长度: {len(engine.portfolio_history)}")

if __name__ == "__main__":
    test_strategy_execution()
    test_full_backtest()
