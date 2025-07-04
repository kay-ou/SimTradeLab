# -*- coding: utf-8 -*-
"""
交易日历功能演示策略
展示如何使用交易日历相关函数
"""

import pandas as pd

# 策略函数
def initialize(context):
    """初始化函数"""
    log.info("初始化交易日历功能演示策略")
    
    # 设置股票池
    g.security = 'STOCK_A'
    
    # 获取所有交易日信息
    all_days = get_all_trades_days()
    log.info(f"数据包含交易日数量: {len(all_days)}")
    log.info(f"交易日期范围: {all_days[0].date()} 到 {all_days[-1].date()}")
    
    # 获取本月交易日
    month_days = get_trade_days(start_date='2023-01-01', end_date='2023-01-31')
    log.info(f"2023年1月交易日数量: {len(month_days)}")
    
    # 策略参数
    g.trade_interval = 3  # 每3个交易日进行一次操作
    g.last_trade_day = None
    g.position_target = 0.6  # 目标仓位比例
    
    log.info(f"策略参数 - 交易间隔: {g.trade_interval}个交易日")


def handle_data(context, data):
    """主策略函数"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    current_price = data[security]['close']
    current_date = context.current_dt
    
    log.info(f"当前交易日: {current_date.date()}, 价格: {current_price:.2f}")
    
    try:
        # 演示交易日历功能的使用
        
        # 1. 获取当前交易日信息
        today = get_trading_day()
        next_trading_day = get_trading_day(offset=1)
        prev_trading_day = get_trading_day(offset=-1)
        
        log.info(f"今日: {today.date() if today else 'None'}")
        log.info(f"下一交易日: {next_trading_day.date() if next_trading_day else 'None'}")
        log.info(f"上一交易日: {prev_trading_day.date() if prev_trading_day else 'None'}")
        
        # 2. 检查是否应该进行交易（基于交易日间隔）
        should_trade = False
        
        if g.last_trade_day is None:
            # 第一次交易
            should_trade = True
            log.info("首次交易日，执行交易")
        else:
            # 计算距离上次交易的交易日数量
            days_since_last_trade = _count_trading_days_between(g.last_trade_day, current_date)
            log.info(f"距离上次交易已过 {days_since_last_trade} 个交易日")
            
            if days_since_last_trade >= g.trade_interval:
                should_trade = True
                log.info(f"达到交易间隔({g.trade_interval}个交易日)，执行交易")
        
        # 3. 执行交易逻辑
        if should_trade:
            current_position = get_position(security)
            current_shares = current_position['amount'] if current_position else 0
            current_value = current_position['market_value'] if current_position else 0
            
            # 计算目标持仓
            total_value = context.portfolio.total_value
            target_value = total_value * g.position_target
            target_shares = int(target_value / current_price / 100) * 100
            
            log.info(f"当前持仓: {current_shares}股 (市值: {current_value:.2f})")
            log.info(f"目标持仓: {target_shares}股 (市值: {target_value:.2f})")
            
            # 执行调仓
            if target_shares != current_shares:
                trade_amount = target_shares - current_shares
                order_id = order(security, trade_amount)
                
                if order_id:
                    action = "买入" if trade_amount > 0 else "卖出"
                    log.info(f"执行调仓: {action} {abs(trade_amount)} 股")
                    g.last_trade_day = current_date
                else:
                    log.warning("调仓订单失败")
            else:
                log.info("持仓已达目标，无需调仓")
                g.last_trade_day = current_date
        
        # 4. 演示其他交易日历功能
        if current_date.day % 5 == 0:  # 每5天演示一次
            _demonstrate_calendar_functions(current_date)
    
    except Exception as e:
        log.error(f"策略执行出错: {e}")


def _count_trading_days_between(start_date, end_date):
    """计算两个日期之间的交易日数量"""
    try:
        # 获取指定范围内的交易日
        trading_days = get_trade_days(start_date=start_date, end_date=end_date)
        # 排除起始日期，只计算中间的交易日
        return max(0, len(trading_days) - 1)
    except Exception as e:
        log.warning(f"计算交易日间隔失败: {e}")
        return 0


def _demonstrate_calendar_functions(current_date):
    """演示交易日历功能"""
    log.info("=== 交易日历功能演示 ===")
    
    try:
        # 获取最近5个交易日
        recent_days = get_trade_days(count=5)
        log.info(f"最近5个交易日: {[d.date() for d in recent_days]}")
        
        # 获取未来3个交易日（如果存在）
        future_days = []
        for i in range(1, 4):
            future_day = get_trading_day(offset=i)
            if future_day:
                future_days.append(future_day.date())
        
        if future_days:
            log.info(f"未来3个交易日: {future_days}")
        else:
            log.info("没有更多未来交易日")
        
        # 获取本周交易日（简单示例）
        week_start = current_date - pd.Timedelta(days=current_date.weekday())
        week_end = week_start + pd.Timedelta(days=6)
        week_days = get_trade_days(start_date=week_start, end_date=week_end)
        log.info(f"本周交易日数量: {len(week_days)}")
        
    except Exception as e:
        log.warning(f"交易日历功能演示失败: {e}")


def before_trading_start(context, data):
    """盘前处理"""
    current_date = context.current_dt
    log.info(f"盘前准备 - 当前交易日: {current_date.date()}")
    
    # 检查是否是月初第一个交易日
    month_start = current_date.replace(day=1)
    month_first_trading_day = get_trading_day(date=month_start)
    
    if month_first_trading_day and current_date.date() == month_first_trading_day.date():
        log.info("今日是本月第一个交易日")
        
        # 获取本月所有交易日
        month_end = (current_date.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(days=1)
        month_trading_days = get_trade_days(start_date=month_start, end_date=month_end)
        log.info(f"本月预计交易日数量: {len(month_trading_days)}")


def after_trading_end(context, data):
    """盘后处理"""
    current_date = context.current_dt
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    log.info(f"盘后总结 - 交易日: {current_date.date()}")
    log.info(f"总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
    
    # 显示持仓情况
    positions = get_positions()
    if positions:
        for security, position in positions.items():
            if position and position['amount'] > 0:
                log.info(f"持仓 {security}: {position['amount']}股, "
                        f"市值: {position['market_value']:.2f}")
    
    # 检查是否是月末最后一个交易日
    next_trading_day = get_trading_day(offset=1)
    if not next_trading_day or next_trading_day.month != current_date.month:
        log.info("今日是本月最后一个交易日")
        
        # 月末总结
        month_start = current_date.replace(day=1)
        month_trading_days = get_trade_days(start_date=month_start, end_date=current_date)
        log.info(f"本月实际交易日数量: {len(month_trading_days)}")
        
        if g.last_trade_day:
            days_since_last = _count_trading_days_between(g.last_trade_day, current_date)
            log.info(f"距离上次交易已过 {days_since_last} 个交易日")
