# -*- coding: utf-8 -*-
"""
真实数据源策略示例

演示如何使用真实数据源进行回测
"""

def initialize(context):
    """初始化函数"""
    log.info("=== 真实数据源策略初始化开始 ===")

    # 设置基准 - 使用沪深300指数
    set_benchmark('000300.SH')
    log.info("设置基准指数: 000300.SH (沪深300)")

    # 设置手续费
    set_commission(commission_ratio=0.0003, min_commission=5.0, type="STOCK")
    log.info("设置手续费: 万分之3，最低5元")

    # 初始化真实股票池 - 使用真实的A股代码
    g.stock_pool = [
        '000001.SZ',  # 平安银行
        '000002.SZ',  # 万科A
        '600000.SH',  # 浦发银行
        '600036.SH',  # 招商银行
        '600519.SH',  # 贵州茅台
    ]

    # 策略参数
    g.buy_threshold = 0.02  # 买入阈值：2%
    g.sell_threshold = -0.01  # 卖出阈值：-1%
    g.max_positions = 3  # 最大持仓数量
    g.position_size = 0.2  # 每只股票的仓位大小：20%

    log.info(f"真实股票池: {g.stock_pool}")
    log.info(f"买入阈值: {g.buy_threshold*100}%, 卖出阈值: {g.sell_threshold*100}%")
    log.info(f"最大持仓: {g.max_positions}只, 单只仓位: {g.position_size*100}%")
    log.info("=== 真实数据源策略初始化完成 ===")


def handle_data(context, data):
    """主要交易逻辑 - 处理真实A股数据"""
    current_date = context.current_dt.strftime('%Y-%m-%d')
    log.info(f"📊 处理真实A股数据: {current_date}")

    # 显示当前可用的真实股票数据
    available_stocks = list(data.keys())
    log.info(f"可用真实股票: {available_stocks}")

    # 获取当前持仓
    positions = get_positions()
    current_positions = len([stock for stock in g.stock_pool
                           if stock in positions and positions[stock].get('amount', 0) > 0])

    log.info(f"当前持仓数量: {current_positions}/{g.max_positions}")

    # 获取股票池的历史数据进行技术分析
    # 先尝试获取较少的历史数据，适应真实数据源的情况
    hist_data = get_history(5, '1d', ['close', 'volume'], g.stock_pool)

    if hist_data.empty:
        log.warning(f"{current_date}: 无法获取历史数据")
        # 即使没有历史数据，也可以进行简单的交易
        log.info("将使用当前价格进行简单交易决策")
    else:
        log.info(f"成功获取历史数据，数据形状: {hist_data.shape}")

    # 分析每只真实股票
    for stock in g.stock_pool:
        if stock not in data:
            continue

        # 获取当前真实价格和成交量
        current_price = data[stock]['close']
        current_volume = data[stock]['volume']

        log.info(f"🏢 {stock}: 价格¥{current_price:.2f}, 成交量{current_volume:,}手")

        # 获取当前持仓
        current_position = positions.get(stock, {}).get('amount', 0)

        # 尝试获取历史数据进行技术分析
        close_prices = None
        use_technical_analysis = False

        if not hist_data.empty:
            # 处理不同格式的历史数据
            try:
                if hasattr(hist_data.columns, 'levels') and len(hist_data.columns.levels) > 1:
                    # 多级索引格式
                    if stock in hist_data.columns.get_level_values(1):
                        close_prices = hist_data['close'][stock].dropna()
                else:
                    # 单级索引格式，尝试不同的访问方式
                    if ('close', stock) in hist_data.columns:
                        close_prices = hist_data[('close', stock)].dropna()
                    elif f'close_{stock}' in hist_data.columns:
                        close_prices = hist_data[f'close_{stock}'].dropna()
                    elif stock in hist_data.columns:
                        # 如果股票直接作为列名，假设是收盘价
                        close_prices = hist_data[stock].dropna()

                if close_prices is not None and len(close_prices) >= 2:
                    use_technical_analysis = True
            except Exception as e:
                log.warning(f"   ⚠️ 无法获取 {stock} 的历史价格数据: {e}")

        if use_technical_analysis:
            # 有足够历史数据，使用技术分析
            ma5 = close_prices.tail(min(5, len(close_prices))).mean()
            ma20 = close_prices.tail(min(20, len(close_prices))).mean()

            # 计算价格变化率
            price_change = (current_price - close_prices.iloc[-2]) / close_prices.iloc[-2] if len(close_prices) > 1 else 0

            log.info(f"   📈 MA{min(5, len(close_prices))}: ¥{ma5:.2f}, MA{min(20, len(close_prices))}: ¥{ma20:.2f}, 涨跌: {price_change:.2%}")

            # 买入条件：价格上涨超过阈值且短期均线上穿长期均线
            if (current_positions < g.max_positions and
                current_position == 0 and
                price_change > g.buy_threshold and
                ma5 > ma20):

                log.info(f"💰 买入信号: {stock} - 价格上涨{price_change:.2%}, MA5>MA20")
                order_id = order(stock, 100)  # 买入100股
                log.info(f"✅ 买入 {stock} 100股, 订单ID: {order_id}")

            # 卖出条件：价格下跌超过阈值
            elif (current_position > 0 and price_change < g.sell_threshold):
                log.info(f"📉 卖出信号: {stock} - 价格下跌{price_change:.2%}")
                order_id = order(stock, -current_position)  # 全部卖出
                log.info(f"✅ 卖出 {stock} {current_position}股, 订单ID: {order_id}")
        else:
            # 历史数据不足，使用简单的买入持有策略
            log.info(f"   📊 {stock}: 使用简单策略（历史数据不足）")

            if (current_positions < g.max_positions and current_position == 0):
                # 简单买入策略：如果还没有持仓且有空余仓位，就买入
                log.info(f"💰 简单买入: {stock} - 当前价格¥{current_price:.2f}")
                order_id = order(stock, 100)  # 买入100股
                log.info(f"✅ 买入 {stock} 100股, 订单ID: {order_id}")

    # 显示当前持仓状态（真实股票）
    log.info("📋 当前真实股票持仓:")
    total_market_value = 0
    for stock in g.stock_pool:
        if stock in positions and positions[stock].get('amount', 0) > 0:
            pos = positions[stock]
            if stock in data:
                current_price = data[stock]['close']
                market_value = pos['amount'] * current_price
                cost_value = pos['amount'] * pos.get('cost_basis', current_price)
                profit_loss = market_value - cost_value
                profit_rate = profit_loss / cost_value if cost_value > 0 else 0
                total_market_value += market_value

                log.info(f"   🏢 {stock}: {pos['amount']}股, "
                        f"市值¥{market_value:.2f}, "
                        f"盈亏¥{profit_loss:.2f}({profit_rate:.2%})")

    if total_market_value > 0:
        log.info(f"📊 总持仓市值: ¥{total_market_value:.2f}")


def after_trading_end(context, data):
    """交易结束后的处理"""
    current_date = context.current_dt.strftime('%Y-%m-%d')
    log.info(f"📅 {current_date} 交易日结束")

    # 显示当日真实数据统计
    portfolio_value = context.portfolio.total_value
    cash = context.portfolio.cash
    stock_value = portfolio_value - cash

    log.info(f"💰 投资组合总价值: ¥{portfolio_value:.2f}")
    log.info(f"💵 现金: ¥{cash:.2f}")
    log.info(f"📈 股票市值: ¥{stock_value:.2f}")

    # 计算当日收益
    if hasattr(context, 'previous_value'):
        daily_return = (portfolio_value - context.previous_value) / context.previous_value
        log.info(f"📊 当日收益率: {daily_return:.2%}")

    context.previous_value = portfolio_value

