# -*- coding: utf-8 -*-
"""
SimTradeLab 命令行接口

支持命令行调用：
poetry run simtradelab --strategy strategies/buy_and_hold_strategy.py \\
    --data data/sample_data.csv
poetry run simtradelab --strategy strategies/real_data_strategy.py \\
    --data-source akshare --securities 000001.SZ
"""

import argparse
import sys
from pathlib import Path

from .runner import run_strategy


def main() -> None:
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        description="SimTradeLab - 量化交易策略回测平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            示例用法:
            %(prog)s --strategy strategies/dual_ma_strategy.py
            %(prog)s --strategy strategies/dual_ma_strategy.py \\
                --days 20 --cash 2000000
            %(prog)s --strategy strategies/dual_ma_strategy.py \\
                --data data/stock_data.csv
            %(prog)s --strategy strategies/real_data_strategy.py \\
                --data-source akshare --securities 000001.SZ

            更多信息: https://github.com/kay-ou/SimTradeLab
        """,
    )

    # 必需参数
    parser.add_argument(
        "--strategy", "-s", required=True, help="策略文件路径 (如: strategies/my_strategy.py)"
    )

    # 数据相关参数
    data_group = parser.add_mutually_exclusive_group()
    data_group.add_argument("--data", "-d", help="数据文件路径 (如: data/stock_data.csv)")
    data_group.add_argument(
        "--data-source",
        choices=["akshare", "tushare", "mock"],
        help="数据源类型 (akshare/tushare/mock)",
    )

    # 回测参数
    parser.add_argument("--start-date", help="开始日期 (YYYY-MM-DD格式)")
    parser.add_argument("--end-date", help="结束日期 (YYYY-MM-DD格式)")
    parser.add_argument("--days", type=int, default=10, help="模拟天数 (默认: 10)")
    parser.add_argument(
        "--cash",
        "--initial-cash",
        type=float,
        default=1000000.0,
        help="初始资金 (默认: 1000000)",
    )

    # 交易参数
    parser.add_argument(
        "--commission", type=float, default=0.0003, help="佣金费率 (默认: 0.0003)"
    )
    parser.add_argument("--slippage", type=float, default=0.001, help="滑点率 (默认: 0.001)")

    # 股票代码 (与data-source配合使用)
    parser.add_argument("--securities", help="股票代码列表，逗号分隔 (如: 000001.SZ,000002.SZ)")

    # 输出控制
    parser.add_argument(
        "--show-system-logs", action="store_true", help="显示系统日志（默认只显示策略日志）"
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式，只显示最终结果")
    parser.add_argument("--output", "-o", help="结果输出文件路径")

    # 解析参数
    args = parser.parse_args()

    # 验证策略文件
    strategy_path = Path(args.strategy)
    if not strategy_path.exists():
        print(f"策略文件不存在: {strategy_path}", file=sys.stderr)
        sys.exit(1)
        return

    # 验证数据文件（如果提供）
    if args.data:
        data_path = Path(args.data)
        if not data_path.exists():
            print(f"数据文件不存在: {data_path}", file=sys.stderr)
            sys.exit(1)
            return

    # 准备运行参数
    run_kwargs = {
        "strategy_file": strategy_path,
        "initial_cash": args.cash,
        "days": args.days,
        "commission_rate": args.commission,
        "slippage_rate": args.slippage,
        "show_system_logs": args.show_system_logs,
        "quiet": args.quiet,
    }

    # 添加可选参数
    if args.data:
        run_kwargs["data_path"] = args.data
    if args.start_date:
        run_kwargs["start_date"] = args.start_date
    if args.end_date:
        run_kwargs["end_date"] = args.end_date

    try:
        # 显示启动信息
        if not args.quiet:
            print("SimTradeLab 命令行启动")
            print(f"策略: {strategy_path.name}")
            if args.data:
                print(f"数据: {args.data}")
            elif args.data_source:
                print(f"数据源: {args.data_source}")
                if args.securities:
                    print(f"股票: {args.securities}")
            print(f"资金: ¥{args.cash:,.0f}")
            print("-" * 50)

        # 运行策略
        results = run_strategy(**run_kwargs)

        # 输出结果
        if args.output:
            import json

            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"结果已保存到: {output_path}")

        # 显示核心结果
        if args.quiet:
            print(f"收益率: {results['total_return_pct']:+.2f}%")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n用户中断", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"运行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
