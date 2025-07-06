# -*- coding: utf-8 -*-
"""
双均线交叉策略 - Web界面演示
策略描述：基于短期和长期移动平均线的交叉信号进行交易
"""

def initialize(context):
    """策略初始化"""
    # 设置股票池
    g.security = '000001.SZ'
    
    # 策略参数
    g.ma_short = 5   # 短期均线周期
    g.ma_long = 20   # 长期均线周期
    g.position_pct = 0.8  # 仓位比例
    
    # 初始状态
    g.last_signal = None
    
    log.info(f"双均线交叉策略初始化完成 - 短期MA:{g.ma_short}, 长期MA:{g.ma_long}")

def handle_data(context, data):
    """主策略逻辑"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    # 获取历史数据
    try:
        hist = get_history(g.ma_long + 5, '1d', 'close', security)
        if len(hist) < g.ma_long:
            log.info("历史数据不足，等待更多数据")
            return
    except Exception as e:
        log.error(f"获取历史数据失败: {e}")
        return
    
    # 计算移动平均线
    close_prices = hist['close']
    ma_short = close_prices.rolling(window=g.ma_short).mean().iloc[-1]
    ma_long = close_prices.rolling(window=g.ma_long).mean().iloc[-1]
    
    # 获取当前价格
    current_price = data[security]['close']
    
    # 获取当前持仓
    current_position = get_position(security).amount
    current_value = context.portfolio.total_value
    
    # 交易信号判断
    signal = None
    if ma_short > ma_long:
        signal = 'buy'
    elif ma_short < ma_long:
        signal = 'sell'
    
    # 执行交易逻辑
    if signal != g.last_signal:  # 信号变化时才交易
        if signal == 'buy' and current_position == 0:
            # 买入信号且当前无持仓
            target_value = current_value * g.position_pct
            order_value(security, target_value)
            log.info(f"金叉买入信号 - MA短期:{ma_short:.2f} > MA长期:{ma_long:.2f}, 买入价值:{target_value:.0f}")
            
        elif signal == 'sell' and current_position > 0:
            # 卖出信号且当前有持仓
            order_target(security, 0)
            log.info(f"死叉卖出信号 - MA短期:{ma_short:.2f} < MA长期:{ma_long:.2f}, 清仓")
        
        g.last_signal = signal
    
    # 记录当前状态
    if current_position > 0:
        position_value = current_position * current_price
        log.info(f"当前持仓: {current_position}股, 市值:{position_value:.0f}, 价格:{current_price:.2f}")

def after_trading_end(context, data):
    """盘后处理"""
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    market_value = context.portfolio.market_value
    
    log.info(f"日终总结 - 总资产:{total_value:.2f}, 现金:{cash:.2f}, 持仓市值:{market_value:.2f}")
    
    # 计算收益率
    if hasattr(context.portfolio, 'starting_cash'):
        total_return = (total_value - context.portfolio.starting_cash) / context.portfolio.starting_cash * 100
        log.info(f"累计收益率: {total_return:.2f}%")