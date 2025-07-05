#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimTradeLab 策略执行命令行工具

使用方法:
    simtradelab --strategy strategies/test_strategy.py --data data/sample_data.csv
    simtradelab --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ,000002.SZ
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

from simtradelab import BacktestEngine
from simtradelab.data_sources import AkshareDataSource, TushareDataSource


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='SimTradeLab 策略回测执行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:

1. 使用CSV数据源:
   simtradelab --strategy strategies/test_strategy.py --data data/sample_data.csv

2. 使用AkShare数据源:
   simtradelab --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ,000002.SZ,600000.SH

3. 使用Tushare数据源:
   simtradelab --strategy strategies/real_data_strategy.py --data-source tushare --securities 000001.SZ,000002.SZ

4. 指定时间范围和初始资金:
   simtradelab --strategy strategies/shadow_strategy.py --data-source akshare --securities 000001.SZ --start-date 2024-12-01 --end-date 2024-12-05 --cash 500000

5. 指定交易频率:
   simtradelab --strategy strategies/test_strategy.py --data data/sample_data.csv --frequency 1d

注意事项:
- 使用真实数据源需要先安装相关依赖: poetry install --with data
- AkShare数据源无需配置，Tushare需要在配置文件中设置token
- 股票代码格式: 深交所用.SZ后缀，上交所用.SH后缀
        """
    )

    # 策略文件参数
    parser.add_argument('--strategy', '-s',
                       required=True,
                       help='策略文件路径 (必需)')

    # 数据源参数组
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument('--data', '-d',
                           help='CSV数据文件路径')
    data_group.add_argument('--data-source',
                           choices=['akshare', 'tushare'],
                           help='真实数据源类型 (akshare/tushare)')

    # 股票代码参数 (使用真实数据源时必需)
    parser.add_argument('--securities',
                       help='股票代码列表，用逗号分隔 (如: 000001.SZ,000002.SZ,600000.SH)')

    # 时间范围参数
    parser.add_argument('--start-date',
                       help='回测开始日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--end-date',
                       help='回测结束日期 (格式: YYYY-MM-DD)')

    # 其他参数
    parser.add_argument('--cash', '-c',
                       type=float,
                       default=1000000.0,
                       help='初始资金 (默认: 1000000)')
    parser.add_argument('--frequency', '-f',
                       default='1d',
                       choices=['1d', '1m', '5m', '15m', '30m'],
                       help='交易频率 (默认: 1d)')

    # 输出控制参数
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='详细输出模式')
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='安静模式，只输出关键信息')

    return parser.parse_args()


def validate_arguments(args):
    """验证参数有效性"""
    errors = []

    # 验证策略文件存在
    if not os.path.exists(args.strategy):
        errors.append(f"策略文件不存在: {args.strategy}")

    # 验证CSV数据文件存在
    if args.data and not os.path.exists(args.data):
        errors.append(f"数据文件不存在: {args.data}")

    # 验证真实数据源参数
    if args.data_source:
        if not args.securities:
            errors.append("使用真实数据源时必须指定 --securities 参数")
        else:
            # 验证股票代码格式
            securities = [s.strip() for s in args.securities.split(',')]
            for security in securities:
                if not (security.endswith('.SZ') or security.endswith('.SH')):
                    errors.append(f"股票代码格式错误: {security} (应以.SZ或.SH结尾)")

    # 验证日期格式
    if args.start_date:
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            errors.append(f"开始日期格式错误: {args.start_date} (应为YYYY-MM-DD)")

    if args.end_date:
        try:
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            errors.append(f"结束日期格式错误: {args.end_date} (应为YYYY-MM-DD)")

    # 验证日期逻辑
    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, '%Y-%m-%d')
        end = datetime.strptime(args.end_date, '%Y-%m-%d')
        if start >= end:
            errors.append("开始日期必须早于结束日期")

    # 验证资金数额
    if args.cash <= 0:
        errors.append("初始资金必须大于0")

    return errors


def create_data_source(args):
    """根据参数创建数据源"""
    if args.data:
        # 使用CSV数据源
        return args.data

    elif args.data_source == 'akshare':
        # 使用AkShare数据源
        return AkshareDataSource()

    elif args.data_source == 'tushare':
        # 使用Tushare数据源
        return TushareDataSource()

    else:
        raise ValueError("未指定有效的数据源")


def get_securities_list(args):
    """获取股票代码列表"""
    if args.securities:
        return [s.strip() for s in args.securities.split(',')]
    return None


def get_date_range(args):
    """获取日期范围"""
    start_date = None
    end_date = None

    if args.start_date:
        start_date = args.start_date
    elif args.data_source:
        # 真实数据源默认使用最近30天
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    if args.end_date:
        end_date = args.end_date
    elif args.data_source and not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    return start_date, end_date


def main():
    """主函数"""
    try:
        # 解析参数
        args = parse_arguments()

        # 验证参数
        errors = validate_arguments(args)
        if errors:
            print("❌ 参数验证失败:")
            for error in errors:
                print(f"   {error}")
            sys.exit(1)

        # 设置输出模式
        if not args.quiet:
            print("🎯 SimTradeLab 策略回测执行")
            print("=" * 50)

        # 创建数据源
        data_source = create_data_source(args)

        # 获取股票列表
        securities = get_securities_list(args)

        # 获取日期范围
        start_date, end_date = get_date_range(args)

        # 显示配置信息
        if args.verbose:
            print(f"📋 回测配置:")
            print(f"   策略文件: {args.strategy}")
            if args.data:
                print(f"   数据源: CSV文件 ({args.data})")
            else:
                print(f"   数据源: {args.data_source}")
                print(f"   股票代码: {', '.join(securities)}")
            if start_date:
                print(f"   开始日期: {start_date}")
            if end_date:
                print(f"   结束日期: {end_date}")
            print(f"   初始资金: ¥{args.cash:,.2f}")
            print(f"   交易频率: {args.frequency}")
            print()

        # 创建回测引擎
        if args.data:
            # CSV数据源
            engine = BacktestEngine(
                strategy_file=args.strategy,
                data_path=data_source,
                start_date=start_date,
                end_date=end_date,
                initial_cash=args.cash,
                frequency=args.frequency
            )
        else:
            # 真实数据源
            engine = BacktestEngine(
                strategy_file=args.strategy,
                data_source=data_source,
                securities=securities,
                start_date=start_date,
                end_date=end_date,
                initial_cash=args.cash,
                frequency=args.frequency
            )

        # 运行回测
        if not args.quiet:
            print("🚀 开始执行回测...")

        generated_files = engine.run()

        # 显示结果
        if not args.quiet:
            print("\n✅ 回测执行完成!")
            if generated_files:
                print(f"📊 生成了 {len(generated_files)} 个报告文件")
                if args.verbose:
                    for file_path in generated_files:
                        print(f"   📄 {os.path.basename(file_path)}")

    except KeyboardInterrupt:
        print("\n❌ 用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()