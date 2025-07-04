# -*- coding: utf-8 -*-
"""
动量策略
基于价格动量和成交量的趋势跟踪策略
"""

def initialize(context):
    """策略初始化"""
    log.info("初始化动量策略")
    
    # 策略参数
    g.security = 'STOCK_A'
    g.momentum_period = 10    # 动量计算周期
    g.volume_period = 20      # 成交量均线周期
    g.momentum_threshold = 0.02  # 动量阈值（2%）
    g.position_ratio = 0.6    # 最大仓位比例
    
    # 策略状态
    g.last_momentum = 0
    g.trend_direction = None  # 'up', 'down', None
    g.entry_price = None
    g.stop_loss_ratio = 0.05  # 止损比例5%
    
    log.info(f"设置股票池: {g.security}")
    log.info(f"动量周期: {g.momentum_period}日, 动量阈值: {g.momentum_threshold*100}%")
    log.info(f"成交量周期: {g.volume_period}日, 最大仓位: {g.position_ratio*100}%")


def handle_data(context, data):
    """主策略逻辑"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    current_price = data[security]['close']
    current_volume = data[security]['volume']
    
    try:
        # 获取历史数据
        hist_data = get_history(max(g.momentum_period, g.volume_period) + 5, '1d', 
                               ['close', 'volume'], security)
        
        if hist_data.empty or len(hist_data) < max(g.momentum_period, g.volume_period):
            log.warning("历史数据不足，无法计算动量指标")
            return
        
        # 计算动量指标
        momentum = _calculate_momentum(hist_data, security)
        volume_ratio = _calculate_volume_ratio(hist_data, security, current_volume)
        
        log.info(f"当前价格: {current_price:.2f}, 成交量: {current_volume:,.0f}")
        log.info(f"价格动量: {momentum:.2%}, 成交量比率: {volume_ratio:.2f}")
        
        # 获取当前持仓
        current_position = get_position(security)
        current_shares = current_position['amount'] if current_position else 0
        
        # 执行交易逻辑
        if current_shares == 0:
            _check_entry_signals(context, current_price, momentum, volume_ratio)
        else:
            _check_exit_signals(context, current_price, momentum, current_shares)
        
        # 更新状态
        g.last_momentum = momentum
    
    except Exception as e:
        log.error(f"动量策略执行出错: {e}")


def _calculate_momentum(hist_data, security):
    """计算价格动量"""
    prices = hist_data['close'][security] if security in hist_data['close'].columns else hist_data['close'].iloc[:, 0]
    
    if len(prices) < g.momentum_period + 1:
        return 0
    
    # 计算动量：当前价格相对于N日前价格的变化率
    current_price = prices.iloc[-1]
    past_price = prices.iloc[-g.momentum_period-1]
    momentum = (current_price - past_price) / past_price
    
    return momentum


def _calculate_volume_ratio(hist_data, security, current_volume):
    """计算成交量比率"""
    volumes = hist_data['volume'][security] if security in hist_data['volume'].columns else hist_data['volume'].iloc[:, 0]
    
    if len(volumes) < g.volume_period:
        return 1.0
    
    # 计算成交量相对于均值的比率
    avg_volume = volumes.rolling(window=g.volume_period).mean().iloc[-1]
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
    
    return volume_ratio


def _check_entry_signals(context, current_price, momentum, volume_ratio):
    """检查入场信号"""
    # 强势上涨动量 + 放量
    if momentum > g.momentum_threshold and volume_ratio > 1.2:
        max_shares = int(context.portfolio.cash * g.position_ratio / current_price / 100) * 100
        if max_shares > 0:
            order_id = order(g.security, max_shares)
            if order_id:
                g.trend_direction = 'up'
                g.entry_price = current_price
                log.info(f"🚀 动量买入信号: 动量{momentum:.2%}, 放量{volume_ratio:.2f}倍")
                log.info(f"   买入 {max_shares} 股，入场价格: {current_price:.2f}")
    
    # 强势下跌动量 + 放量（做空信号，但这里只做多）
    elif momentum < -g.momentum_threshold and volume_ratio > 1.2:
        log.info(f"⚠️ 检测到下跌动量: {momentum:.2%}, 暂不入场")


def _check_exit_signals(context, current_price, momentum, current_shares):
    """检查出场信号"""
    # 止损检查
    if g.entry_price and current_price < g.entry_price * (1 - g.stop_loss_ratio):
        order_id = order(g.security, -current_shares)
        if order_id:
            loss_ratio = (current_price - g.entry_price) / g.entry_price
            log.info(f"🛑 止损卖出: 价格{g.entry_price:.2f} -> {current_price:.2f}, 亏损{loss_ratio:.2%}")
            _reset_position_state()
        return
    
    # 动量反转信号
    if g.trend_direction == 'up' and momentum < -g.momentum_threshold/2:
        order_id = order(g.security, -current_shares)
        if order_id:
            profit_ratio = (current_price - g.entry_price) / g.entry_price if g.entry_price else 0
            log.info(f"📉 动量反转卖出: 动量转为{momentum:.2%}, 收益{profit_ratio:.2%}")
            _reset_position_state()
        return
    
    # 动量衰减信号
    if momentum < g.momentum_threshold/3 and g.last_momentum > momentum:
        log.info(f"⚠️ 动量衰减: {momentum:.2%}, 考虑减仓")


def _reset_position_state():
    """重置持仓状态"""
    g.trend_direction = None
    g.entry_price = None


def before_trading_start(context, data):
    """盘前处理"""
    log.info("盘前准备 - 动量策略")


def after_trading_end(context, data):
    """盘后处理"""
    # 记录当日状态
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    log.info(f"盘后总结 - 总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
    
    # 显示持仓情况
    position = get_position(g.security)
    if position and position['amount'] > 0:
        current_price = position['last_sale_price']
        unrealized_pnl = 0
        if g.entry_price:
            unrealized_pnl = (current_price - g.entry_price) / g.entry_price
        
        log.info(f"持仓 {g.security}: {position['amount']}股")
        log.info(f"   入场价: {g.entry_price:.2f}, 当前价: {current_price:.2f}")
        log.info(f"   未实现盈亏: {unrealized_pnl:.2%}")
        log.info(f"   当前趋势: {g.trend_direction or '无'}")
    else:
        log.info("当前无持仓，等待动量信号")
    
    # 动量分析
    log.info(f"最新动量: {g.last_momentum:.2%} (阈值: ±{g.momentum_threshold:.2%})")
