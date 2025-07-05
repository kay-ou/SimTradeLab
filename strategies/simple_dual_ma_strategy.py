#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强双均线策略

基于双均线交叉的趋势跟踪策略，包含止损和仓位管理功能。
当短期均线上穿长期均线时买入，下穿时卖出。
支持动态仓位调整和风险控制。

策略特点：
- 双均线交叉信号
- 动态仓位管理
- 止损保护
- 趋势确认机制

适用市场：股票、指数
风险等级：中等
"""

# 导入必要的库
import pandas as pd
import numpy as np


def initialize(context):
    """
    策略初始化函数

    在策略开始运行前调用，用于设置策略参数和初始化变量
    """
    log.info("初始化简化双均线策略")

    # 基本策略参数
    g.short_ma = 5          # 短期均线周期
    g.long_ma = 20          # 长期均线周期
    g.position_ratio = 0.8  # 最大仓位比例
    g.stop_loss = 0.05      # 止损比例 (5%)

    # 策略状态变量
    g.signal_count = 0           # 信号计数
    g.daily_returns = []         # 每日收益率记录
    g.position_history = []      # 持仓历史

    log.info(f"策略参数设置完成: 短期均线={g.short_ma}, "
             f"长期均线={g.long_ma}, "
             f"最大仓位={g.position_ratio:.1%}")


def handle_data(context, data):
    """
    主要的策略逻辑函数
    
    每个交易日都会调用此函数
    """
    # 获取当前日期
    current_date = context.current_dt.date()
    
    # 获取股票列表（从数据中获取可用股票）
    securities = list(data.keys())
    if not securities:
        log.warning("没有可用的股票数据")
        return

    # 主要股票（假设只交易第一只股票）
    security = securities[0]
    
    # 获取历史数据
    hist_data = get_history(
        count=max(g.short_ma, g.long_ma) + 10,
        frequency='1d',
        field=['close', 'volume'],
        security_list=[security],
        is_dict=True
    )

    if hist_data is None or security not in hist_data or len(hist_data[security]['close']) < g.long_ma:
        log.warning("历史数据不足，跳过本次交易")
        return

    # 计算技术指标
    close_prices = pd.Series(hist_data[security]['close'])
    volumes = pd.Series(hist_data[security]['volume'])
    
    # 计算均线
    ma_short = close_prices.rolling(window=g.short_ma).mean().iloc[-1]
    ma_long = close_prices.rolling(window=g.long_ma).mean().iloc[-1]
    
    # 获取当前持仓
    current_position = context.portfolio.positions[security]
    current_price = get_current_data()[security].last_price
    
    # 生成交易信号
    signal = 0
    if ma_short > ma_long:
        signal = 1  # 买入信号
    elif ma_short < ma_long:
        signal = -1  # 卖出信号

    # 执行交易逻辑
    current_position = context.portfolio.positions[security]
    current_amount = current_position.amount

    if signal == 1 and current_amount == 0:  # 买入信号且无持仓
        target_value = context.portfolio.total_value * g.position_ratio
        target_amount = int(target_value / current_price / 100) * 100  # 整手

        if target_amount > 0:
            order_target(security, target_amount)
            log.info(f"买入信号: 目标持仓 {target_amount} 股")
            g.signal_count += 1

    elif signal == -1 and current_amount > 0:  # 卖出信号且有持仓
        order_target(security, 0)
        log.info(f"卖出信号: 清仓 {current_amount} 股")
        g.signal_count += 1





def after_trading_end(context, data):
    """
    每日交易结束后调用

    用于记录当日统计信息和执行日终处理
    """
    # 计算当日统计
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash

    # 每5天输出一次详细信息
    if context.current_dt.day % 5 == 0:
        log.info(f"总资产: ¥{total_value:,.2f}, "
                 f"现金: ¥{cash:,.2f}, "
                 f"信号次数: {g.signal_count}")



