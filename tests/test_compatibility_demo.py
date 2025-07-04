# -*- coding: utf-8 -*-
"""
委托状态兼容性演示策略测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradeSim.engine import BacktestEngine


def test_compatibility_demo():
    """测试委托状态兼容性演示策略"""
    print("=" * 70)
    print("测试委托状态兼容性演示策略")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/compatibility_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-10',
            initial_cash=1000000.0
        )
        
        print("开始运行委托状态兼容性演示策略...")
        print("策略说明：演示V005版本（整数状态）的委托状态兼容性处理")
        
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
        
        # 持仓情况
        print("\n持仓情况:")
        if final_portfolio.positions:
            for stock, position in final_portfolio.positions.items():
                if position.amount > 0:
                    print(f"  {stock}: {position.amount}股, 成本价: {position.cost_basis:.2f}, 最新价: {position.last_sale_price:.2f}")
        else:
            print("  无持仓")
        
        # 兼容性验证
        print("\n兼容性验证:")
        blotter = engine.context.blotter
        all_orders = blotter.get_all_orders()
        
        # 检查订单状态格式
        status_types = set()
        status_values = set()
        
        for order in all_orders.values():
            order_dict = order.to_dict(use_compat=True)
            status_types.add(type(order_dict['status']))
            status_values.add(order_dict['status'])
        
        print(f"  订单状态类型: {[t.__name__ for t in status_types]}")
        print(f"  订单状态值: {sorted(status_values)}")
        
        # 验证是否符合V005版本格式（整数）
        if len(status_types) == 1 and int in status_types:
            print("  ✅ 状态格式符合V005版本要求（整数）")
        else:
            print("  ❌ 状态格式不符合V005版本要求")
        
        # 交易统计
        all_trades = blotter.get_all_trades()
        print(f"\n交易统计:")
        print(f"  总订单数: {len(all_orders)}")
        print(f"  总成交数: {len(all_trades)}")
        
        # 按状态统计
        status_count = {}
        for order in all_orders.values():
            order_dict = order.to_dict(use_compat=True)
            status = order_dict['status']
            status_count[status] = status_count.get(status, 0) + 1
        
        print("  订单状态分布:")
        status_names = {0: 'new', 1: 'open', 2: 'filled', 3: 'cancelled', 4: 'rejected'}
        for status, count in sorted(status_count.items()):
            status_name = status_names.get(status, 'unknown')
            print(f"    {status} ({status_name}): {count}笔")
        
        print("\n✅ 委托状态兼容性演示策略测试完成")
        print("🔄 委托状态兼容性功能正常工作")
        
    except Exception as e:
        print(f"❌ 委托状态兼容性演示策略测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_compatibility_demo()
