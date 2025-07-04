# -*- coding: utf-8 -*-
"""
双均线交叉策略
经典的技术分析策略，基于短期和长期移动平均线的交叉信号进行交易
"""

def initialize(context):
    """策略初始化"""
    log.info("初始化双均线交叉策略")
    
    # 策略参数
    g.security = 'STOCK_A'
    g.short_window = 5   # 短期均线周期
    g.long_window = 20   # 长期均线周期
    g.position_ratio = 0.8  # 最大仓位比例
    
    # 交易控制
    g.last_signal = None  # 上次交易信号
    g.signal_count = 0    # 信号计数
    
    log.info(f"设置股票池: {g.security}")
    log.info(f"短期均线: {g.short_window}日, 长期均线: {g.long_window}日")
    log.info(f"最大仓位比例: {g.position_ratio*100}%")


def handle_data(context, data):
    """主策略逻辑"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    current_price = data[security]['close']
    
    try:
        # 获取历史价格数据
        hist_data = get_history(max(g.long_window + 5, 30), '1d', 'close', security)
        
        if hist_data.empty or len(hist_data) < g.long_window:
            log.warning("历史数据不足，无法计算均线")
            return
        
        # 计算移动平均线
        prices = hist_data[security] if security in hist_data.columns else hist_data.iloc[:, 0]
        ma_short = prices.rolling(window=g.short_window).mean().iloc[-1]
        ma_long = prices.rolling(window=g.long_window).mean().iloc[-1]
        
        # 计算前一日均线（用于判断交叉）
        ma_short_prev = prices.rolling(window=g.short_window).mean().iloc[-2] if len(prices) > g.short_window else ma_short
        ma_long_prev = prices.rolling(window=g.long_window).mean().iloc[-2] if len(prices) > g.long_window else ma_long
        
        log.info(f"当前价格: {current_price:.2f}")
        log.info(f"MA{g.short_window}: {ma_short:.2f}, MA{g.long_window}: {ma_long:.2f}")
        
        # 获取当前持仓
        current_position = get_position(security)
        current_shares = current_position['amount'] if current_position else 0
        
        # 判断交叉信号
        golden_cross = ma_short > ma_long and ma_short_prev <= ma_long_prev  # 金叉
        death_cross = ma_short < ma_long and ma_short_prev >= ma_long_prev   # 死叉
        
        # 执行交易逻辑
        if golden_cross and current_shares == 0:
            # 金叉买入信号
            max_shares = int(context.portfolio.cash * g.position_ratio / current_price / 100) * 100
            if max_shares > 0:
                order_id = order(security, max_shares)
                if order_id:
                    g.last_signal = 'buy'
                    g.signal_count += 1
                    log.info(f"🟢 金叉买入信号 (第{g.signal_count}次)，买入 {max_shares} 股")
                    log.info(f"   MA{g.short_window}({ma_short:.2f}) 上穿 MA{g.long_window}({ma_long:.2f})")
        
        elif death_cross and current_shares > 0:
            # 死叉卖出信号
            order_id = order(security, -current_shares)
            if order_id:
                g.last_signal = 'sell'
                g.signal_count += 1
                log.info(f"🔴 死叉卖出信号 (第{g.signal_count}次)，卖出 {current_shares} 股")
                log.info(f"   MA{g.short_window}({ma_short:.2f}) 下穿 MA{g.long_window}({ma_long:.2f})")
        
        else:
            # 无交易信号
            if current_shares > 0:
                trend = "看多" if ma_short > ma_long else "看空"
                log.info(f"持仓中 ({current_shares}股)，当前趋势: {trend}")
            else:
                log.info("空仓等待信号")
    
    except Exception as e:
        log.error(f"双均线策略执行出错: {e}")


def before_trading_start(context, data):
    """盘前处理"""
    log.info("盘前准备 - 双均线交叉策略")


def after_trading_end(context, data):
    """盘后处理"""
    # 记录当日状态
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    log.info(f"盘后总结 - 总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
    
    # 显示持仓情况
    position = get_position(g.security)
    if position and position['amount'] > 0:
        log.info(f"持仓 {g.security}: {position['amount']}股, "
                f"成本价: {position['cost_basis']:.2f}, "
                f"市值: {position['market_value']:.2f}, "
                f"盈亏: {position['pnl_ratio']:.2%}")
    else:
        log.info("当前无持仓")
    
    # 策略统计
    log.info(f"累计交易信号: {g.signal_count}次, 最后信号: {g.last_signal or '无'}")
