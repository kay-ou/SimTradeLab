# -*- coding: utf-8 -*-
"""
技术指标策略示例
使用MACD、KDJ、RSI等技术指标进行交易决策
"""


# 策略函数
def initialize(context):
    """初始化函数"""
    log.info("初始化技术指标策略")
    
    # 设置股票池
    g.security = 'STOCK_A'
    g.stocks = [g.security]
    
    # 技术指标参数
    g.macd_fast = 12
    g.macd_slow = 26
    g.macd_signal = 9
    g.rsi_period = 14
    g.kdj_period = 9
    g.cci_period = 20
    
    # 交易控制参数
    g.max_position_ratio = 0.8  # 最大仓位比例
    g.trade_amount = 1000       # 每次交易股数
    
    log.info(f"设置股票池: {g.stocks}")
    log.info(f"MACD参数: 快线{g.macd_fast}, 慢线{g.macd_slow}, 信号线{g.macd_signal}")
    log.info(f"RSI周期: {g.rsi_period}, KDJ周期: {g.kdj_period}, CCI周期: {g.cci_period}")


def handle_data(context, data):
    """主策略函数"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    current_price = data[security]['close']
    log.info(f"当前价格: {current_price:.2f}")
    
    # 获取技术指标
    try:
        # 获取MACD指标
        macd_data = get_MACD(security, g.macd_fast, g.macd_slow, g.macd_signal)
        if macd_data.empty:
            log.warning("MACD数据为空，跳过交易")
            return
        
        # 获取最新的MACD值
        macd_dif = macd_data[('MACD_DIF', security)].iloc[-1]
        macd_dea = macd_data[('MACD_DEA', security)].iloc[-1]
        macd_hist = macd_data[('MACD_HIST', security)].iloc[-1]
        
        # 获取RSI指标
        rsi_data = get_RSI(security, g.rsi_period)
        rsi_value = rsi_data[(f'RSI{g.rsi_period}', security)].iloc[-1] if not rsi_data.empty else 50
        
        # 获取KDJ指标
        kdj_data = get_KDJ(security, g.kdj_period)
        if not kdj_data.empty:
            kdj_k = kdj_data[('KDJ_K', security)].iloc[-1]
            kdj_d = kdj_data[('KDJ_D', security)].iloc[-1]
            kdj_j = kdj_data[('KDJ_J', security)].iloc[-1]
        else:
            kdj_k = kdj_d = kdj_j = 50
        
        # 获取CCI指标
        cci_data = get_CCI(security, g.cci_period)
        cci_value = cci_data[(f'CCI{g.cci_period}', security)].iloc[-1] if not cci_data.empty else 0
        
        # 记录技术指标值
        log.info(f"技术指标 - MACD_DIF: {macd_dif:.4f}, MACD_DEA: {macd_dea:.4f}, MACD_HIST: {macd_hist:.4f}")
        log.info(f"技术指标 - RSI: {rsi_value:.2f}, KDJ_K: {kdj_k:.2f}, KDJ_D: {kdj_d:.2f}, KDJ_J: {kdj_j:.2f}")
        log.info(f"技术指标 - CCI: {cci_value:.2f}")
        
        # 获取当前持仓
        current_position = context.portfolio.positions.get(security)
        current_shares = current_position.amount if current_position else 0
        
        # 交易信号判断
        buy_signals = 0
        sell_signals = 0
        
        # MACD信号
        if macd_dif > macd_dea and macd_hist > 0:
            buy_signals += 1
            log.info("MACD买入信号: DIF上穿DEA且HIST为正")
        elif macd_dif < macd_dea and macd_hist < 0:
            sell_signals += 1
            log.info("MACD卖出信号: DIF下穿DEA且HIST为负")
        
        # RSI信号
        if rsi_value < 30:
            buy_signals += 1
            log.info(f"RSI买入信号: RSI({rsi_value:.2f}) < 30，超卖")
        elif rsi_value > 70:
            sell_signals += 1
            log.info(f"RSI卖出信号: RSI({rsi_value:.2f}) > 70，超买")
        
        # KDJ信号
        if kdj_k < 20 and kdj_d < 20 and kdj_k > kdj_d:
            buy_signals += 1
            log.info(f"KDJ买入信号: K({kdj_k:.2f})和D({kdj_d:.2f})均小于20且K上穿D")
        elif kdj_k > 80 and kdj_d > 80 and kdj_k < kdj_d:
            sell_signals += 1
            log.info(f"KDJ卖出信号: K({kdj_k:.2f})和D({kdj_d:.2f})均大于80且K下穿D")
        
        # CCI信号
        if cci_value < -100:
            buy_signals += 1
            log.info(f"CCI买入信号: CCI({cci_value:.2f}) < -100，超卖")
        elif cci_value > 100:
            sell_signals += 1
            log.info(f"CCI卖出信号: CCI({cci_value:.2f}) > 100，超买")
        
        # 执行交易决策
        if buy_signals >= 2 and current_shares < g.max_position_ratio * context.portfolio.total_value / current_price:
            # 买入信号
            order_id = order(security, g.trade_amount)
            if order_id:
                log.info(f"买入信号确认({buy_signals}个)，买入 {g.trade_amount} 股 {security}")
            else:
                log.warning("买入订单失败")
        
        elif sell_signals >= 2 and current_shares > 0:
            # 卖出信号
            sell_amount = min(g.trade_amount, current_shares)
            order_id = order(security, -sell_amount)
            if order_id:
                log.info(f"卖出信号确认({sell_signals}个)，卖出 {sell_amount} 股 {security}")
            else:
                log.warning("卖出订单失败")
        
        else:
            log.info(f"无明确交易信号 - 买入信号: {buy_signals}, 卖出信号: {sell_signals}")
    
    except Exception as e:
        log.error(f"技术指标计算或交易执行出错: {e}")


def before_trading_start(context, data):
    """盘前处理"""
    log.info("盘前准备 - 技术指标策略")


def after_trading_end(context, data):
    """盘后处理"""
    # 记录当日状态
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    # 计算持仓情况
    positions_info = []
    for stock, position in context.portfolio.positions.items():
        if position.amount > 0:
            positions_info.append(f"{stock}: {position.amount}股")
    
    positions_str = ", ".join(positions_info) if positions_info else "空仓"
    
    log.info(f"盘后总结 - 总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
    log.info(f"持仓情况: {positions_str}")
