# -*- coding: utf-8 -*-

def initialize(context):
    """
    策略初始化函数。
    """
    context.securities = ['STOCK_A']  # 设置要交易的股票
    context.has_bought = False  # 标记是否已买入

def handle_data(context, data):
    """
    策略的核心逻辑，每个交易日调用一次。
    """
    if not context.has_bought:
        # 在第一个交易日，用90%的资金买入股票
        cash_to_use = context.portfolio.cash * 0.9
        price = data['STOCK_A']['close']
        amount_to_buy = int(cash_to_use / price)

        if amount_to_buy > 0:
            order('STOCK_A', amount_to_buy)
            context.has_bought = True

def before_trading_start(context, data):
    """
    盘前处理函数。
    """
    pass

def after_trading_end(context, data):
    """
    盘后处理函数。
    """
    pass