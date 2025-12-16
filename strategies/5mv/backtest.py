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

    context.max_position = 2  # 最多持仓2只
    context.rotation_period = 2  # 轮换周期（天）
    context.day_count = 0     # 交易日计数

    log.info("=" * 60)
    log.info("简化版5均线策略 - 每日交易测试")
    log.info("股票池: {}".format(context.stocks))
    log.info("最大持仓: {} 只".format(context.max_position))
    log.info("轮换周期: {} 天".format(context.rotation_period))
    log.info("=" * 60)


def before_trading_start(context, data):
    """盘前"""
    pass


def handle_data(context, data):
    """每日交易逻辑 - 保证每天都有交易"""

    context.day_count += 1

    # 获取当前持仓
    positions = context.portfolio.positions
    current_stocks = [stock for stock, pos in positions.items() if pos.amount > 0]

    # 策略：按轮换周期轮换持仓
    if context.day_count % context.rotation_period == 1:
        # 奇数日：清空所有持仓
        if len(current_stocks) > 0:
            log.info("[Day {}] 清空持仓".format(context.day_count))
            for stock in current_stocks:
                order_target(stock, 0)
    else:
        # 偶数日：买入前2只股票
        if len(current_stocks) == 0:
            log.info("[Day {}] 买入股票".format(context.day_count))
            stocks_to_buy = context.stocks[:context.max_position]

            for stock in stocks_to_buy:
                # 每只股票分配相等资金
                target_value = context.portfolio.portfolio_value / context.max_position
                order_value(stock, target_value)
                log.info("  买入 {}".format(stock))


def after_trading_end(context, data):
    """盘后"""
    positions = context.portfolio.positions
    position_count = sum(1 for pos in positions.values() if pos.amount > 0)

    log.info("日终 | 总资产: {:.2f} | 持仓: {} 只 | 现金: {:.2f}".format(
             context.portfolio.portfolio_value, position_count, context.portfolio.cash))
