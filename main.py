# -*- coding: utf-8 -*-
"""
主程序入口，用于配置和运行回测。
"""

from simtradelab import BacktestEngine


def main():
    """
    主函数，配置并运行回测。
    """
    # --- 回测配置 ---
    # strategy_file = "strategies/simple_dual_ma_strategy.py"
    strategy_file = "strategies/buy_and_hold_strategy.py"
    initial_cash = 1000000.0
    days = 10

    # --- 启动引擎 ---
    print("=== SimTradeLab 回测系统 ===")
    print(f"策略文件: {strategy_file}")
    print(f"初始资金: ¥{initial_cash:,.0f}")
    print(f"模拟天数: {days}天")
    print()

    engine = BacktestEngine(
        strategy_file=strategy_file, initial_cash=initial_cash, days=days
    )

    results = engine.run()

    # 显示详细的最终状态
    print("\n=== 详细回测结果 ===")
    print(f"初始资金: ¥{results['initial_cash']:,.0f}")
    print(f"最终价值: ¥{results['final_value']:,.0f}")
    print(f"现金余额: ¥{results['cash']:,.0f}")
    print(f"持仓价值: ¥{results['positions_value']:,.0f}")
    print(f"总收益率: {results['total_return_pct']:+.2f}%")
    print(f"交易次数: {results['total_trades']}")
    print(f"盈利交易: {results['winning_trades']}")
    print(f"持仓数量: {results['positions_count']}")
    print(f"模拟天数: {results['days_simulated']}天")


if __name__ == "__main__":
    main()
