# -*- coding: utf-8 -*-
"""
分钟级交易策略示例
演示如何在分钟级频率下进行交易
"""

def initialize(context):
    """策略初始化"""
    log.info("分钟级交易策略初始化")
    
    # 策略参数
    g.stocks = ['STOCK_A', 'STOCK_B']
    g.short_window = 5   # 短期均线周期（5分钟）
    g.long_window = 20   # 长期均线周期（20分钟）
    g.position_size = 0.3  # 单只股票最大仓位30%
    
    # 交易状态
    g.last_prices = {}
    g.price_history = {stock: [] for stock in g.stocks}
    g.trade_count = 0
    
    log.info(f"目标股票: {g.stocks}")
    log.info(f"均线参数: 短期{g.short_window}分钟, 长期{g.long_window}分钟")

def before_trading_start(context, data):
    """盘前准备（每个交易日开始时调用）"""
    current_date = context.current_dt.strftime('%Y-%m-%d')
    log.info(f"开始新的交易日: {current_date}")
    
    # 重置日内交易计数
    g.daily_trade_count = 0
    
    # 显示当前持仓
    positions = context.portfolio.positions
    if positions:
        log.info("当前持仓:")
        for stock, pos in positions.items():
            log.info(f"  {stock}: {pos.amount}股, 价值{pos.value:.2f}元")
    else:
        log.info("当前无持仓")

def handle_data(context, data):
    """分钟级交易逻辑（每分钟调用一次）"""
    current_time = context.current_dt
    
    # 更新价格历史
    for stock in g.stocks:
        if stock in data:
            current_price = data[stock]['close']
            g.price_history[stock].append(current_price)
            g.last_prices[stock] = current_price
            
            # 保持历史数据长度
            if len(g.price_history[stock]) > g.long_window:
                g.price_history[stock] = g.price_history[stock][-g.long_window:]
    
    # 只在有足够历史数据时进行交易决策
    for stock in g.stocks:
        if stock in g.price_history and len(g.price_history[stock]) >= g.long_window:
            if stock in data:
                make_trading_decision(context, data, stock)
    
    # 每10分钟记录一次状态
    if current_time.minute % 10 == 0:
        log_portfolio_status(context)

def make_trading_decision(context, data, stock):
    """为单只股票做交易决策"""
    if stock not in g.price_history or len(g.price_history[stock]) < g.long_window:
        return
    
    prices = g.price_history[stock]
    current_price = prices[-1]
    
    # 计算移动平均线
    short_ma = sum(prices[-g.short_window:]) / g.short_window
    long_ma = sum(prices[-g.long_window:]) / g.long_window
    
    # 获取当前持仓
    current_position = context.portfolio.positions.get(stock)
    current_amount = current_position.amount if current_position else 0
    
    # 交易信号
    buy_signal = short_ma > long_ma and current_amount == 0
    sell_signal = short_ma < long_ma and current_amount > 0
    
    # 执行交易
    if buy_signal:
        # 买入信号
        max_value = context.portfolio.total_value * g.position_size
        target_amount = int(max_value / current_price / 100) * 100  # 整手买入
        
        if target_amount > 0 and context.portfolio.cash >= target_amount * current_price:
            order(stock, target_amount)
            g.trade_count += 1
            g.daily_trade_count += 1
            
            log.info(f"买入信号: {stock}")
            log.info(f"  短期均线: {short_ma:.2f}, 长期均线: {long_ma:.2f}")
            log.info(f"  买入数量: {target_amount}股, 价格: {current_price:.2f}")
    
    elif sell_signal:
        # 卖出信号
        order_target(stock, 0)  # 全部卖出
        g.trade_count += 1
        g.daily_trade_count += 1
        
        log.info(f"卖出信号: {stock}")
        log.info(f"  短期均线: {short_ma:.2f}, 长期均线: {long_ma:.2f}")
        log.info(f"  卖出数量: {current_amount}股, 价格: {current_price:.2f}")

def after_trading_end(context, data):
    """盘后处理（每个交易日结束时调用）"""
    current_date = context.current_dt.strftime('%Y-%m-%d')
    
    # 计算当日收益
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    position_value = total_value - cash
    
    log.info(f"交易日结束: {current_date}")
    log.info(f"当日交易次数: {g.daily_trade_count}")
    log.info(f"总交易次数: {g.trade_count}")
    log.info(f"总资产: {total_value:.2f}元")
    log.info(f"现金: {cash:.2f}元")
    log.info(f"持仓价值: {position_value:.2f}元")
    
    # 显示持仓详情
    positions = context.portfolio.positions
    if positions:
        log.info("持仓详情:")
        for stock, pos in positions.items():
            pnl = pos.value - pos.amount * pos.cost_basis
            pnl_pct = (pnl / (pos.amount * pos.cost_basis)) * 100 if pos.amount > 0 else 0
            log.info(f"  {stock}: {pos.amount}股, 成本{pos.cost_basis:.2f}, "
                    f"现价{pos.last_sale_price:.2f}, 盈亏{pnl:.2f}({pnl_pct:.2f}%)")

def log_portfolio_status(context):
    """记录投资组合状态"""
    current_time = context.current_dt.strftime('%H:%M')
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    # 计算持仓比例
    position_ratio = (total_value - cash) / total_value * 100 if total_value > 0 else 0
    
    log.info(f"[{current_time}] 资产: {total_value:.2f}, 现金: {cash:.2f}, 持仓比例: {position_ratio:.1f}%")
    
    # 显示当前价格和均线
    for stock in g.stocks:  # 修复这里，迭代单个股票
        if stock in g.price_history and len(g.price_history[stock]) >= g.long_window:
            if stock in g.last_prices:
                prices = g.price_history[stock]
                current_price = g.last_prices[stock]
                short_ma = sum(prices[-g.short_window:]) / g.short_window
                long_ma = sum(prices[-g.long_window:]) / g.long_window
                
                log.info(f"  {stock}: 价格{current_price:.2f}, MA{g.short_window}={short_ma:.2f}, "
                        f"MA{g.long_window}={long_ma:.2f}")

# 风险控制函数
def risk_management(context):
    """风险控制"""
    total_value = context.portfolio.total_value
    
    # 单股持仓比例控制
    for stock, position in context.portfolio.positions.items():
        weight = position.value / total_value
        if weight > g.position_size * 1.2:  # 超过目标仓位20%
            # 减仓到目标仓位
            target_value = total_value * g.position_size
            current_price = g.last_prices.get(stock, position.last_sale_price)
            target_amount = int(target_value / current_price / 100) * 100
            
            if target_amount < position.amount:
                order_target(stock, target_amount)
                log.info(f"风控减仓: {stock}, 当前比例{weight:.2%}, 目标比例{g.position_size:.2%}")

# 策略统计函数
def get_strategy_stats(context):
    """获取策略统计信息"""
    total_value = context.portfolio.total_value
    initial_cash = context.portfolio.starting_cash
    total_return = (total_value - initial_cash) / initial_cash * 100
    
    return {
        'total_value': total_value,
        'total_return': total_return,
        'trade_count': g.trade_count,
        'position_count': len(context.portfolio.positions)
    }
