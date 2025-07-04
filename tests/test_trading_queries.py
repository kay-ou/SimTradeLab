# -*- coding: utf-8 -*-
"""
交易查询接口测试
包含API接口测试和策略演示测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradeSim.engine import BacktestEngine
from ptradeSim.trading import (
    order, get_positions, get_position, get_open_orders,
    get_order, get_orders, get_trades, cancel_order
)


def test_trading_queries():
    """测试交易查询接口功能"""
    print("=" * 60)
    print("测试交易查询接口功能")
    print("=" * 60)
    
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
        print(f"当前价格: {engine.current_data[test_security]['close']}")
        
        # 1. 测试初始状态查询
        print("\n1. 测试初始状态查询")
        
        # 查询初始持仓
        positions = get_positions(engine)
        print(f"初始持仓: {positions}")
        
        # 查询初始订单
        orders = get_orders(engine)
        print(f"初始订单: {orders}")
        
        # 查询初始成交
        trades = get_trades(engine)
        print(f"初始成交: {trades}")
        
        # 2. 测试下单和查询
        print("\n2. 测试下单和查询")
        
        # 下买单
        order_id1 = order(engine, test_security, 1000)
        print(f"买单订单ID: {order_id1}")
        
        # 查询订单
        if order_id1:
            order_info = get_order(engine, order_id1)
            print(f"订单详情: {order_info}")
        
        # 查询所有订单
        all_orders = get_orders(engine)
        print(f"所有订单数量: {len(all_orders)}")
        
        # 查询成交记录
        trades = get_trades(engine)
        print(f"成交记录数量: {len(trades)}")
        if trades:
            print(f"最新成交: {trades[-1]}")
        
        # 查询持仓
        positions = get_positions(engine)
        print(f"当前持仓: {positions}")
        
        # 查询单个股票持仓
        position = get_position(engine, test_security)
        print(f"{test_security}持仓: {position}")
        
        # 3. 测试多笔交易
        print("\n3. 测试多笔交易")
        
        # 再下一笔买单
        order_id2 = order(engine, test_security, 500)
        print(f"第二笔买单ID: {order_id2}")
        
        # 下卖单
        order_id3 = order(engine, test_security, -300)
        print(f"卖单ID: {order_id3}")
        
        # 查询最终状态
        final_positions = get_positions(engine)
        final_orders = get_orders(engine)
        final_trades = get_trades(engine)
        
        print(f"最终持仓: {final_positions}")
        print(f"最终订单数量: {len(final_orders)}")
        print(f"最终成交数量: {len(final_trades)}")
        
        # 4. 测试未完成订单查询
        print("\n4. 测试未完成订单查询")
        
        open_orders = get_open_orders(engine)
        print(f"未完成订单数量: {len(open_orders)}")
        
        # 5. 测试撤单功能
        print("\n5. 测试撤单功能")
        
        # 下一个限价单（不会立即成交）
        limit_order_id = order(engine, test_security, 100, limit_price=90.0)  # 低于市价的买单
        if limit_order_id:
            print(f"限价单ID: {limit_order_id}")
            
            # 查询未完成订单
            open_orders_before = get_open_orders(engine)
            print(f"撤单前未完成订单: {len(open_orders_before)}")
            
            # 撤销订单
            cancel_success = cancel_order(engine, limit_order_id)
            print(f"撤单结果: {cancel_success}")
            
            # 查询撤单后状态
            open_orders_after = get_open_orders(engine)
            print(f"撤单后未完成订单: {len(open_orders_after)}")
            
            # 查询被撤销的订单状态
            cancelled_order = get_order(engine, limit_order_id)
            print(f"被撤销订单状态: {cancelled_order['status'] if cancelled_order else 'None'}")
        
        print("\n" + "=" * 60)
        print("交易查询接口测试完成")
        print("=" * 60)
        print("✅ 所有交易查询功能正常工作")
        
    except Exception as e:
        print(f"❌ 交易查询接口测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_trading_query_strategy():
    """测试交易查询演示策略"""
    print("\n" + "=" * 70)
    print("测试交易查询演示策略")
    print("=" * 70)

    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/trading_query_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-10',
            initial_cash=1000000.0
        )

        print("开始运行交易查询演示策略...")
        print("策略说明：演示各种交易查询接口的使用")

        # 运行回测
        engine.run()

        # 输出回测结果
        print("\n" + "=" * 70)
        print("回测结果汇总")
        print("=" * 70)

        final_portfolio = engine.context.portfolio
        print(f"初始资金: {engine.initial_cash:,.2f}")
        print(f"最终总资产: {final_portfolio.total_value:,.2f}")
        print(f"最终现金: {final_portfolio.cash:,.2f}")
        print(f"总收益: {final_portfolio.total_value - engine.initial_cash:,.2f}")
        print(f"收益率: {((final_portfolio.total_value / engine.initial_cash) - 1) * 100:.2f}%")

        # 交易统计
        blotter = engine.context.blotter
        all_orders = blotter.get_all_orders()
        all_trades = blotter.get_all_trades()

        print(f"\n交易统计:")
        print(f"  总订单数: {len(all_orders)}")
        print(f"  总成交数: {len(all_trades)}")

        print("\n✅ 交易查询演示策略测试完成")

    except Exception as e:
        print(f"❌ 交易查询演示策略测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_trading_queries()
    test_trading_query_strategy()
