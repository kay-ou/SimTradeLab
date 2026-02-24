# -*- coding: utf-8 -*-
"""
5日均线策略
买入条件：收盘价 > 5日均线
卖出条件：收盘价 < 5日均线
"""
def initialize(context):
    set_benchmark('000300.SS')

    context.stocks = [
        '600519.SS',  # 贵州茅台
        '000858.SZ',  # 五粮液
        '601318.SS',  # 中国平安
        '600036.SS',  # 招商银行
        '000651.SZ',  # 格力电器
    ]

    context.max_position = 2  # 最多同时持仓2只
    set_slippage(slippage=0.0)
    set_fixed_slippage(fixedslippage=0.0)
    set_limit_mode('UNLIMITED')


def handle_data(context, data):
    # 获取所有股票近6日收盘价（含今日用于计算均线）
    hist = get_history(6, '1d', 'close', context.stocks, include=True)

    # 过滤掉数据不足的股票
    valid = [s for s in context.stocks if s in hist.columns and hist[s].count() >= 5]

    ma5 = {s: hist[s].iloc[-5:].mean() for s in valid}
    price = {s: hist[s].iloc[-1] for s in valid}

    positions = context.portfolio.positions

    # 卖出：持仓中收盘价跌破5日均线的
    for stock, pos in list(positions.items()):
        if pos.amount > 0 and stock in ma5 and price[stock] < ma5[stock]:
            order_target(stock, 0)
            log.info("卖出 {} price={:.2f} ma5={:.2f}".format(stock, price[stock], ma5[stock]))

    # 买入：价格高于5日均线且未持仓，按持仓上限等比买入
    held = [s for s, p in context.portfolio.positions.items() if p.amount > 0]
    slots = context.max_position - len(held)
    if slots <= 0:
        return

    candidates = [
        s for s in valid
        if s not in held and price[s] > ma5[s]
    ]
    # 按超越均线幅度降序，优先买入强势股
    candidates.sort(key=lambda s: price[s] / ma5[s], reverse=True)

    per_slot = context.portfolio.cash / slots
    for stock in candidates[:slots]:
        order_value(stock, per_slot)
        log.info("买入 {} price={:.2f} ma5={:.2f}".format(stock, price[stock], ma5[stock]))


def after_trading_end(context, data):
    positions = context.portfolio.positions
    held = [(s, p) for s, p in positions.items() if p.amount > 0]
    log.info("日终 | 总资产: {:.2f} | 持仓: {} 只 | 现金: {:.2f}".format(
        context.portfolio.portfolio_value, len(held), context.portfolio.cash))
