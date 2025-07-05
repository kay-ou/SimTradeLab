# -*- coding: utf-8 -*-
"""
交易日历功能测试
"""
import sys
import os
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradesim.engine import BacktestEngine
from ptradesim.utils import get_trading_day, get_all_trades_days, get_trade_days


def test_trading_calendar():
    """测试交易日历功能"""
    print("=" * 60)
    print("测试交易日历功能")
    print("=" * 60)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0
        )
        
        print("回测引擎创建成功，开始测试交易日历功能...")
        
        # 1. 测试获取所有交易日
        print("\n1. 测试 get_all_trades_days()")
        all_trading_days = get_all_trades_days(engine)
        print(f"总交易日数量: {len(all_trading_days)}")
        if len(all_trading_days) > 0:
            print(f"第一个交易日: {all_trading_days[0]}")
            print(f"最后一个交易日: {all_trading_days[-1]}")
            print(f"前5个交易日: {all_trading_days[:5].tolist()}")
        
        # 2. 测试获取指定范围的交易日
        print("\n2. 测试 get_trade_days()")
        
        # 测试日期范围筛选
        start_date = '2023-01-01'
        end_date = '2023-01-15'
        range_days = get_trade_days(engine, start_date=start_date, end_date=end_date)
        print(f"日期范围 {start_date} 到 {end_date} 的交易日数量: {len(range_days)}")
        if len(range_days) > 0:
            print(f"范围内交易日: {range_days.tolist()}")
        
        # 测试数量限制
        count_days = get_trade_days(engine, start_date='2023-01-01', count=5)
        print(f"从 2023-01-01 开始的前5个交易日: {count_days.tolist()}")
        
        # 测试只指定开始日期
        from_start_days = get_trade_days(engine, start_date='2023-01-10')
        print(f"从 2023-01-10 开始的所有交易日数量: {len(from_start_days)}")
        
        # 3. 测试获取特定交易日
        print("\n3. 测试 get_trading_day()")
        
        # 设置当前日期上下文
        engine.context.current_dt = pd.to_datetime('2023-01-05')
        
        # 测试当前交易日
        current_day = get_trading_day(engine)
        print(f"当前交易日: {current_day}")
        
        # 测试下一个交易日
        next_day = get_trading_day(engine, offset=1)
        print(f"下一个交易日: {next_day}")
        
        # 测试上一个交易日
        prev_day = get_trading_day(engine, offset=-1)
        print(f"上一个交易日: {prev_day}")
        
        # 测试指定日期的交易日
        specific_date = '2023-01-10'
        specific_day = get_trading_day(engine, date=specific_date)
        print(f"指定日期 {specific_date} 的交易日: {specific_day}")
        
        # 测试指定日期的前后交易日
        before_specific = get_trading_day(engine, date=specific_date, offset=-1)
        after_specific = get_trading_day(engine, date=specific_date, offset=1)
        print(f"指定日期 {specific_date} 的前一个交易日: {before_specific}")
        print(f"指定日期 {specific_date} 的后一个交易日: {after_specific}")
        
        # 4. 测试边界情况
        print("\n4. 测试边界情况")
        
        # 测试超出范围的偏移
        out_of_range_future = get_trading_day(engine, offset=1000)
        out_of_range_past = get_trading_day(engine, offset=-1000)
        print(f"超出范围的未来交易日: {out_of_range_future}")
        print(f"超出范围的过去交易日: {out_of_range_past}")
        
        # 测试非交易日
        non_trading_date = '2023-01-01'  # 假设这是非交易日
        non_trading_day = get_trading_day(engine, date=non_trading_date)
        print(f"非交易日 {non_trading_date} 对应的交易日: {non_trading_day}")
        
        # 5. 测试实际应用场景
        print("\n5. 测试实际应用场景")
        
        # 场景1：获取最近N个交易日
        recent_days = get_trade_days(engine, count=10)
        print(f"最近10个交易日: {recent_days.tolist()}")
        
        # 场景2：获取本月交易日
        month_start = '2023-01-01'
        month_end = '2023-01-31'
        month_days = get_trade_days(engine, start_date=month_start, end_date=month_end)
        print(f"2023年1月交易日数量: {len(month_days)}")
        
        # 场景3：计算交易日间隔
        if len(all_trading_days) >= 2:
            day1 = all_trading_days[0]
            day2 = all_trading_days[1]
            interval = (day2 - day1).days
            print(f"相邻交易日间隔: {interval}天")
        
        print("\n" + "=" * 60)
        print("交易日历功能测试完成")
        print("=" * 60)
        print("✅ 所有交易日历功能正常工作")
        
    except Exception as e:
        print(f"❌ 交易日历功能测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_trading_calendar()
