# -*- coding: utf-8 -*-
"""
简单双均线测试策略

用于快速验证回测框架功能
- 测试数据加载
- 测试订单执行
- 测试持仓管理
- 测试统计报告生成
"""


def initialize(context):
    """初始化策略"""
    # 设置基准
    set_benchmark('000300.SS')

    # 策略参数
    context.short_window = 5   # 短期均线
    context.long_window = 20   # 长期均线
    context.max_stocks = 5     # 最大持仓数

    # 股票池：选择几只流动性好的股票用于测试
    context.test_stocks = [
        '600519.SS',  # 贵州茅台
        '000858.SZ',  # 五粮液
        '601318.SS',  # 中国平安
        '600036.SS',  # 招商银行
        '000651.SZ',  # 格力电器
    ]

    log.info("=" * 60)
    log.info("简单双均线测试策略")
    log.info("=" * 60)
    log.info(f"短期均线: {context.short_window} 日")
    log.info(f"长期均线: {context.long_window} 日")
    log.info(f"最大持仓: {context.max_stocks} 只")
    log.info(f"测试股票: {context.test_stocks}")
    log.info("=" * 60)


def before_trading_start(context, data):
    """盘前处理"""
    pass


def handle_data(context, data):
    """主策略逻辑"""

    # 获取当前持仓
    positions = context.portfolio.positions
    current_stocks = [stock for stock, pos in positions.items() if pos.amount > 0]

    # 遍历测试股票
    for stock in context.test_stocks:
        # 获取历史数据
        hist = get_history(
            context.long_window + 1,
            '1d',
            'close',
            [stock],
            fq=None,
            is_dict=True
        )

        if stock not in hist or len(hist[stock]) < context.long_window:
            continue

        prices = hist[stock]

        # 计算均线
        short_ma = sum(prices[-context.short_window:]) / context.short_window
        long_ma = sum(prices[-context.long_window:]) / context.long_window

        # 金叉：买入信号
        if short_ma > long_ma and stock not in current_stocks:
            if len(current_stocks) < context.max_stocks:
                # 等权重买入
                target_value = context.portfolio.portfolio_value / context.max_stocks
                order_value(stock, target_value)
                log.info(f"[买入信号] {stock} 短期MA={short_ma:.2f} > 长期MA={long_ma:.2f}")

        # 死叉：卖出信号
        elif short_ma < long_ma and stock in current_stocks:
            order_target(stock, 0)
            log.info(f"[卖出信号] {stock} 短期MA={short_ma:.2f} < 长期MA={long_ma:.2f}")


def after_trading_end(context, data):
    """盘后处理"""
    # 输出每日持仓情况
    positions = context.portfolio.positions
    position_count = sum(1 for pos in positions.values() if pos.amount > 0)

    log.info(f"日终总资产: {context.portfolio.portfolio_value:.2f} | "
             f"持仓数: {position_count} | "
             f"现金: {context.portfolio.cash:.2f}")
