# -*- coding: utf-8 -*-
"""
主程序入口，用于配置和运行回测。

根据 v5.0 架构，此文件已重构为使用 BacktestRunner 和外部配置文件。
推荐的生产环境启动方式是使用命令行工具：
`poetry run python -m simtradelab.cli --strategy <策略文件> --config <配置文件>`
"""

import sys
from pathlib import Path

import yaml

from src.simtradelab.runner import BacktestRunner


def main():
    """
    主函数，配置并运行回测。
    """
    # --- 默认配置 ---
    # 策略文件可以通过命令行参数覆盖，或在此处修改
    strategy_file = "strategies/simple_dual_ma_strategy.py"
    config_file = "simtradelab_config.yaml"

    # --- 验证文件路径 ---
    strategy_path = Path(strategy_file)
    if not strategy_path.exists():
        print(f"错误: 策略文件不存在 -> {strategy_path}", file=sys.stderr)
        sys.exit(1)

    config_path = Path(config_file)
    if not config_path.exists():
        print(f"错误: 配置文件不存在 -> {config_path}", file=sys.stderr)
        sys.exit(1)

    # --- 加载配置 ---
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"错误: 加载配置文件失败 -> {e}", file=sys.stderr)
        sys.exit(1)

    # --- 启动引擎 ---
    print("=== SimTradeLab 回测系统 (v5.0 Runner) ===")
    print(f"策略文件: {strategy_path.name}")
    print(f"配置文件: {config_path.name}")
    print("-" * 50)

    try:
        # 使用 BacktestRunner 运行回测
        with BacktestRunner(strategy_file=str(strategy_path), config=config) as runner:
            results = runner.run()

        # 显示回测结果
        print("\n=== 回测完成 ===")
        if results:
            print(f"初始资金: ¥{results.get('initial_cash', 0):,.0f}")
            print(f"最终价值: ¥{results.get('final_value', 0):,.0f}")
            print(f"总收益率: {results.get('total_return_pct', 0):+.2f}%")
            print(f"交易次数: {results.get('total_trades', 0)}")
        else:
            print("未能获取回测结果。")

    except Exception as e:
        print(f"\n运行时发生错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
