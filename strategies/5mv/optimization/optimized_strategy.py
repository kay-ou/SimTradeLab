# -*- coding: utf-8 -*-
"""
简化版5均线策略 - 每日交易测试
保证每天都有交易发生
"""

def initialize(context):
    """初始化"""
    set_benchmark('000300.SS')

    # 简单的股票池（5只流动性好的股票）
    context.stocks = [
        '600519.SS',  # 贵州茅台
        '000858.SZ',  # 五粮液
        '601318.SS',  # 中国平安
        '600036.SS',  # 招商银行
        '000651.SZ',  # 格力电器
    ]

    context.max_position = 3# 最多持仓2只
    context.rotation_period = 6# 轮换周期（天）
    context.day_count = 0     # 交易日计数
    context.last_trade_day = -999  # 上次交易日期

    log.info("=" * 60)
    log.info("简化版5均线策略 - 按周期轮换")
    log.info("股票池: {}".format(context.stocks))
    log.info("最大持仓: {} 只".format(context.max_position))
    log.info("轮换周期: {} 天".format(context.rotation_period))
    log.info("=" * 60)


def before_trading_start(context, data):
    """盘前"""
    pass


def handle_data(context, data):
    """每日交易逻辑 - 按轮换周期持有/清仓"""

    context.day_count += 1

    # 获取当前持仓
    positions = context.portfolio.positions
    current_stocks = [stock for stock, pos in positions.items() if pos.amount > 0]

    # 计算距离上次交易的天数
    days_since_trade = context.day_count - context.last_trade_day

    # 策略：每隔 rotation_period 天完整轮换一次
    if days_since_trade >= context.rotation_period:
        if len(current_stocks) > 0:
            # 有持仓：清仓
            log.info("[Day {}] 轮换周期到达，清仓".format(context.day_count))
            for stock in current_stocks:
                order_target(stock, 0)
        else:
            # 无持仓：买入
            log.info("[Day {}] 轮换周期到达，买入 {} 只".format(context.day_count, context.max_position))
            stocks_to_buy = context.stocks[:context.max_position]
            for stock in stocks_to_buy:
                target_value = context.portfolio.portfolio_value / context.max_position
                order_value(stock, target_value)
                log.info("  买入 {}".format(stock))

        context.last_trade_day = context.day_count


def after_trading_end(context, data):
    """盘后"""
    positions = context.portfolio.positions
    position_count = sum(1 for pos in positions.values() if pos.amount > 0)

    log.info("日终 | 总资产: {:.2f} | 持仓: {} 只 | 现金: {:.2f}".format(
             context.portfolio.portfolio_value, position_count, context.portfolio.cash))
