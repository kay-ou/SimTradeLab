# -*- coding: utf-8 -*-
"""
SimTradeLab 命令行接口 (重构后)
"""

import argparse
import sys
from pathlib import Path
import yaml

from .runner import BacktestRunner


def main() -> None:
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        description="SimTradeLab - 量化交易策略回测平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--strategy", "-s", required=True, help="策略文件路径")
    parser.add_argument("--config", "-c", required=True, help="YAML 配置文件路径")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式，只显示最终结果")

    args = parser.parse_args()

    # 验证文件路径
    strategy_path = Path(args.strategy)
    if not strategy_path.exists():
        print(f"策略文件不存在: {strategy_path}", file=sys.stderr)
        sys.exit(1)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    # 加载配置
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if not args.quiet:
            print("SimTradeLab 命令行启动")
            print(f"策略: {strategy_path.name}")
            print(f"配置: {config_path.name}")
            print("-" * 50)

        # 使用新的 BacktestRunner
        with BacktestRunner(strategy_file=str(strategy_path), config=config) as runner:
            results = runner.run()

        if args.quiet:
            print(f"收益率: {results.get('total_return_pct', 0):+.2f}%")
        else:
            print("\n回测完成!")
            # 可以选择性地打印更多结果
            # import json
            # print(json.dumps(results, indent=2, ensure_ascii=False))

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n用户中断", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"运行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
