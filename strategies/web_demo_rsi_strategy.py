# -*- coding: utf-8 -*-
"""
RSI超买超卖策略 - Web界面演示
策略描述：使用RSI指标判断超买超卖，在极值区域进行反向交易
"""

def initialize(context):
    """策略初始化"""
    # 设置股票池
    g.security = '000001.SZ'
    
    # RSI策略参数
    g.rsi_period = 14      # RSI计算周期
    g.rsi_oversold = 30    # 超卖阈值
    g.rsi_overbought = 70  # 超买阈值
    g.position_pct = 0.6   # 仓位比例
    
    # 交易控制
    g.last_rsi = None
    g.cooldown_days = 0    # 冷却期，避免频繁交易
    
    log.info(f"RSI策略初始化完成 - 周期:{g.rsi_period}, 超卖线:{g.rsi_oversold}, 超买线:{g.rsi_overbought}")

def handle_data(context, data):
    """主策略逻辑"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    # 冷却期控制
    if g.cooldown_days > 0:
        g.cooldown_days -= 1
        return
    
    try:
        # 计算RSI指标
        rsi_data = get_RSI(security, period=g.rsi_period)
        if rsi_data.empty:
            log.info("RSI数据不足，等待更多历史数据")
            return
        
        current_rsi = rsi_data[f'RSI{g.rsi_period}'].iloc[-1]
        if pd.isna(current_rsi):
            return
            
    except Exception as e:
        log.error(f"计算RSI指标失败: {e}")
        return
    
    # 获取当前状态
    current_price = data[security]['close']
    current_position = get_position(security).amount
    current_value = context.portfolio.total_value
    
    # 交易信号判断
    buy_signal = current_rsi < g.rsi_oversold and current_position == 0
    sell_signal = current_rsi > g.rsi_overbought and current_position > 0
    
    # 执行交易
    if buy_signal:
        # RSI超卖，买入信号
        target_value = current_value * g.position_pct
        order_value(security, target_value)
        g.cooldown_days = 3  # 设置3天冷却期
        log.info(f"RSI超卖买入 - RSI:{current_rsi:.2f} < {g.rsi_oversold}, 买入价值:{target_value:.0f}")
        
    elif sell_signal:
        # RSI超买，卖出信号
        order_target(security, 0)
        g.cooldown_days = 3  # 设置3天冷却期
        log.info(f"RSI超买卖出 - RSI:{current_rsi:.2f} > {g.rsi_overbought}, 全部卖出")
    
    # 记录当前RSI值
    g.last_rsi = current_rsi
    
    # 状态日志
    if current_position > 0:
        position_value = current_position * current_price
        log.info(f"持仓状态 - RSI:{current_rsi:.2f}, 持股:{current_position}, 市值:{position_value:.0f}")
    else:
        log.info(f"空仓状态 - RSI:{current_rsi:.2f}, 价格:{current_price:.2f}")

def after_trading_end(context, data):
    """盘后处理"""
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    # 计算收益情况
    if hasattr(context.portfolio, 'starting_cash'):
        total_return = (total_value - context.portfolio.starting_cash) / context.portfolio.starting_cash * 100
        log.info(f"日终总结 - 总资产:{total_value:.2f}, 现金:{cash:.2f}, 收益率:{total_return:.2f}%")
        
        # 记录最后的RSI值
        if g.last_rsi:
            log.info(f"最新RSI: {g.last_rsi:.2f}")
    else:
        log.info(f"日终总结 - 总资产:{total_value:.2f}, 现金:{cash:.2f}")