#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ptradeSim 策略执行命令行工具

使用方法:
    python ptradeSim.py --strategy strategies/test_strategy.py --data data/sample_data.csv
    python ptradeSim.py --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ,000002.SZ
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from ptradesim import BacktestEngine
from ptradesim.data_sources import AkshareDataSource, TushareDataSource


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='ptradeSim 策略回测执行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:

1. 使用CSV数据源:
   python ptradeSim.py --strategy strategies/test_strategy.py --data data/sample_data.csv

2. 使用AkShare数据源:
   python ptradeSim.py --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ,000002.SZ,600000.SH

3. 使用Tushare数据源:
   python ptradeSim.py --strategy strategies/real_data_strategy.py --data-source tushare --securities 000001.SZ,000002.SZ

4. 指定时间范围和初始资金:
   python ptradeSim.py --strategy strategies/shadow_strategy.py --data-source akshare --securities 000001.SZ --start-date 2024-12-01 --end-date 2024-12-05 --cash 500000

5. 指定交易频率:
   python ptradeSim.py --strategy strategies/test_strategy.py --data data/sample_data.csv --frequency 1d
        """
    )
    
    # 必需参数
    parser.add_argument('--strategy', '-s', required=True,
                       help='策略文件路径 (例如: strategies/test_strategy.py)')
    
    # 数据源参数 (互斥)
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument('--data', '-d',
                           help='CSV数据文件路径 (例如: data/sample_data.csv)')
    data_group.add_argument('--data-source', choices=['akshare', 'tushare'],
                           help='真实数据源类型 (akshare 或 tushare)')
    
    # 股票列表 (真实数据源必需)
    parser.add_argument('--securities', 
                       help='股票代码列表，逗号分隔 (例如: 000001.SZ,000002.SZ,600000.SH)')
    
    # 时间参数
    parser.add_argument('--start-date', default='2024-12-01',
                       help='回测开始日期 (格式: YYYY-MM-DD, 默认: 2024-12-01)')
    parser.add_argument('--end-date', default='2024-12-05',
                       help='回测结束日期 (格式: YYYY-MM-DD, 默认: 2024-12-05)')
    
    # 其他参数
    parser.add_argument('--cash', type=float, default=1000000.0,
                       help='初始资金 (默认: 1000000.0)')
    parser.add_argument('--frequency', choices=['1d', '1m', '5m', '15m', '30m'], default='1d',
                       help='交易频率 (默认: 1d)')
    
    # 输出参数
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细输出')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='静默模式，只显示结果')
    
    return parser.parse_args()


def validate_arguments(args):
    """验证参数有效性"""
    errors = []
    
    # 检查策略文件是否存在
    if not os.path.exists(args.strategy):
        errors.append(f"策略文件不存在: {args.strategy}")
    
    # 检查CSV数据文件
    if args.data and not os.path.exists(args.data):
        errors.append(f"数据文件不存在: {args.data}")
    
    # 检查真实数据源的股票列表
    if args.data_source and not args.securities:
        errors.append("使用真实数据源时必须指定 --securities 参数")
    
    # 检查日期格式
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError:
        errors.append("日期格式错误，请使用 YYYY-MM-DD 格式")
    
    # 检查日期逻辑
    if args.start_date >= args.end_date:
        errors.append("开始日期必须早于结束日期")
    
    if errors:
        print("❌ 参数验证失败:")
        for error in errors:
            print(f"   {error}")
        sys.exit(1)


def create_data_source(args):
    """根据参数创建数据源"""
    if args.data_source == 'akshare':
        if not args.quiet:
            print("📡 创建AkShare数据源...")
        return AkshareDataSource()
    elif args.data_source == 'tushare':
        if not args.quiet:
            print("📡 创建Tushare数据源...")
        return TushareDataSource()
    else:
        return None


def parse_securities(securities_str):
    """解析股票代码列表"""
    if not securities_str:
        return None
    return [s.strip() for s in securities_str.split(',') if s.strip()]


def run_backtest(args):
    """执行回测"""
    if not args.quiet:
        print("🎯 ptradeSim 策略回测执行")
        print("=" * 50)
        print(f"📋 策略文件: {args.strategy}")
        
    # 创建引擎参数
    engine_kwargs = {
        'strategy_file': args.strategy,
        'start_date': args.start_date,
        'end_date': args.end_date,
        'initial_cash': args.cash,
        'frequency': args.frequency
    }
    
    # 配置数据源
    if args.data:
        # CSV数据源
        engine_kwargs['data_path'] = args.data
        if not args.quiet:
            print(f"📁 数据源: CSV文件 ({args.data})")
    else:
        # 真实数据源
        data_source = create_data_source(args)
        securities = parse_securities(args.securities)
        
        engine_kwargs['data_source'] = data_source
        engine_kwargs['securities'] = securities
        
        if not args.quiet:
            print(f"🌐 数据源: {args.data_source.upper()}")
            print(f"📈 股票列表: {', '.join(securities)}")
    
    if not args.quiet:
        print(f"📅 回测期间: {args.start_date} 到 {args.end_date}")
        print(f"💰 初始资金: ¥{args.cash:,.2f}")
        print(f"⏱️  交易频率: {args.frequency}")
        print()
    
    try:
        # 创建回测引擎
        if not args.quiet:
            print("🔧 创建回测引擎...")
        engine = BacktestEngine(**engine_kwargs)
        
        if not args.quiet:
            print("✅ 引擎创建成功")
            
            if engine.data:
                print(f"📊 成功加载 {len(engine.data)} 只股票数据")
                
                # 显示数据预览
                if args.verbose:
                    print("\n📋 数据预览:")
                    for stock, data in engine.data.items():
                        if len(data) > 0:
                            print(f"   🏢 {stock}: {len(data)} 条数据, "
                                  f"价格范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
            else:
                print("⚠️ 未加载到数据")
                return
        
        # 执行回测
        if not args.quiet:
            print("\n🚀 开始执行回测...")
        
        engine.run()
        
        if not args.quiet:
            print("✅ 回测执行完成")
        
        # 显示结果
        if hasattr(engine, 'portfolio_history') and engine.portfolio_history:
            initial_value = engine.portfolio_history[0]['total_value']
            final_value = engine.portfolio_history[-1]['total_value']
            total_return = (final_value - initial_value) / initial_value
            
            print("\n📊 回测结果:")
            print(f"   💰 初始资金: ¥{initial_value:,.2f}")
            print(f"   💰 最终资金: ¥{final_value:,.2f}")
            print(f"   📈 总收益: ¥{final_value - initial_value:,.2f}")
            print(f"   📊 总收益率: {total_return:.2%}")
            print(f"   📅 交易天数: {len(engine.portfolio_history)} 天")
            
            # 显示持仓信息
            final_cash = engine.portfolio_history[-1]['cash']
            stock_value = final_value - final_cash
            if stock_value > 0:
                print(f"   📈 股票市值: ¥{stock_value:,.2f}")
                print(f"   💵 剩余现金: ¥{final_cash:,.2f}")
        else:
            print("⚠️ 未生成回测历史数据")
            
    except Exception as e:
        print(f"❌ 回测执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    args = parse_arguments()
    validate_arguments(args)
    run_backtest(args)
    
    if not args.quiet:
        print("\n🎉 回测完成")


if __name__ == '__main__':
    main()
