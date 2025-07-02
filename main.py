# -*- coding: utf-8 -*-

from ptradeSim.engine import BacktestEngine

def main():
    """
    主函数，配置并运行回测。
    """
    # --- 回测配置 ---
    strategy_file = 'strategies/test_strategy.py'
    data_path = 'data/sample_data.csv'  # 假设数据文件路径
    start_date = '2023-01-13'  # 只测试有数据的日期
    end_date = '2023-01-13'
    initial_cash = 1000000.0

    # --- 启动引擎 ---
    engine = BacktestEngine(
        strategy_file=strategy_file,
        data_path=data_path,
        start_date=start_date,
        end_date=end_date,
        initial_cash=initial_cash
    )
    
    engine.run()

    # 显示详细的最终状态
    print(f"\n=== 详细回测结果 ===")
    print(f"最终现金: {engine.portfolio.cash:,.2f}")
    print(f"最终总价值: {engine.portfolio.total_value:,.2f}")
    print(f"持仓数量: {len([p for p in engine.portfolio.positions.values() if p.amount > 0])}")

    total_position_value = 0
    for stock, position in engine.portfolio.positions.items():
        if position.amount > 0:
            print(f"持仓 {stock}: {position.amount} 股，成本价 {position.cost_basis:.2f}，当前价 {position.last_sale_price:.2f}，市值 {position.market_value:.2f}")
            total_position_value += position.market_value

    print(f"持仓总市值: {total_position_value:,.2f}")
    print(f"现金+持仓: {engine.portfolio.cash + total_position_value:,.2f}")

    # 计算收益
    total_return = (engine.portfolio.total_value - engine.initial_cash) / engine.initial_cash * 100
    print(f"总收益率: {total_return:.2f}%")

if __name__ == "__main__":
    main()