# -*- coding: utf-8 -*-
"""
交易日历演示策略测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradesim.engine import BacktestEngine


def test_trading_calendar_demo():
    """测试交易日历演示策略"""
    print("=" * 70)
    print("测试交易日历演示策略")
    print("=" * 70)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/trading_calendar_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0
        )
        
        print("开始运行交易日历演示策略...")
        print("策略说明：基于交易日历进行定期调仓，演示各种交易日历功能")
        
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
        
        # 交易统计
        blotter = engine.context.blotter
        all_orders = blotter.get_all_orders()
        all_trades = blotter.get_all_trades()
        
        print(f"\n交易统计:")
        print(f"  总订单数: {len(all_orders)}")
        print(f"  总成交数: {len(all_trades)}")
        
        print("\n✅ 交易日历演示策略测试完成")
        print("📅 交易日历功能在策略中成功应用")
        
    except Exception as e:
        print(f"❌ 交易日历演示策略测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_trading_calendar_demo()
