# -*- coding: utf-8 -*-
"""
SimTradeLab 命令行接口 (重构后)
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

from .adapters.ptrade.adapter import PTradeAdapter
from .core.plugin_manager import PluginManager


def _print_results(results: Dict[str, Any]) -> None:
    """格式化并打印回测结果。"""
    print("\n--- 回测性能摘要 ---")
    
    display_metrics = {
        "final_portfolio_value": ("最终投资组合价值", "{:,.2f}"),
        "total_return_pct": ("总回报率", "{:+.2%}"),
        "annualized_return": ("年化收益率", "{:+.2%}"),
        "sharpe_ratio": ("夏普比率", "{:.2f}"),
        "max_drawdown": ("最大回撤", "{:.2%}"),
        "annualized_volatility": ("年化波动率", "{:.2%}"),
        "calmar_ratio": ("卡玛比率", "{:.2f}"),
        "total_orders": ("总订单数", "{}"),
        "total_trades": ("总成交数", "{}"),
        "trade_completion_rate": ("成交率", "{:.2%}"),
    }

    for key, (display_name, fmt) in display_metrics.items():
        value = results.get(key)
        if value is not None:
            if isinstance(value, (int, float)):
                print(f"{display_name:<20}: {fmt.format(value)}")
            else:
                print(f"{display_name:<20}: {value}")

    print("-" * 22)


def main() -> None:
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        description="SimTradeLab - 量化交易策略回测平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--strategy", "-s", required=True, help="策略文件路径")
    parser.add_argument("--config", "-c", help="YAML 配置文件路径")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式，只显示最终结果")

    args = parser.parse_args()

    strategy_path = Path(args.strategy)
    if not strategy_path.exists():
        print(f"策略文件不存在: {strategy_path}", file=sys.stderr)
        sys.exit(1)

    config_path = Path(args.config) if args.config else None
    if config_path and not config_path.exists():
        print(f"配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    try:
        if not args.quiet:
            print("SimTradeLab 命令行启动")
            print(f"策略: {strategy_path.name}")
            if config_path:
                print(f"配置: {config_path.name}")
            print("-" * 50)

        # 使用 PTradeAdapter
        plugin_manager = PluginManager()
        
        # TODO: 从配置文件加载适配器配置
        adapter = PTradeAdapter()
        adapter.set_plugin_manager(plugin_manager)
        adapter.initialize()
        
        adapter.load_strategy(str(strategy_path))
        
        # TODO: 实现一个循环来模拟数据和时间流逝，并调用 adapter.run_strategy()
        # 这是一个简化的单次运行示例
        adapter.run_strategy()

        results = adapter.get_strategy_performance()

        if args.quiet:
            cumulative_return = results.get("returns", 0.0)
            print(f"累计收益率: {cumulative_return:+.2%}")
        else:
            _print_results(results)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n用户中断", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"运行失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
