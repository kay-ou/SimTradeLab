import numpy as np
from datetime import datetime
from pathlib import Path
from collections import defaultdict, OrderedDict
import pickle

'''
上影线策略：筛选满足特定条件的股票并执行交易操作
筛选条件：上市>1年，收盘价>20日线*0.95，放量上涨，上影线3.5%-8.6%，5日涨幅0%-10%，换手率10%-30%，成交额>5000万，非st，非退市
交易规则：按市值升序选前2支股票，持有8天，下跌7%止损，8天内上涨>20%则持有至高点回撤5%卖出
'''

def initialize(context):
    # 初始化全局变量
    g.isGuoSheng = False # 是否为国盛证券
    g.to_buy = []
    g.to_sell = {}

    # 策略参数
    g.min_position_value = 10000  # 每个持仓的最小金额
    g.max_hold_days = 8  # 最大持有天数
    g.stop_loss_rate = -7  # 止损率
    g.take_profit_rate = 20  # 止盈率
    g.drawdown_rate = -5  # 回撤率
    g.initial_cash_divisor = 2  # 初始资金使用比例的除数，例如2代表使用1/2的资金

    # 选股条件参数
    g.min_listed_days = 365  # 最小上市天数
    g.min_price = 2.0  # 最低股价
    g.ma_discount_rate = 0.95  # MA折扣率，用于计算买入点
    g.volume_increase_ratio = 1.5  # 成交量增长率
    g.upper_shadow_min = 3.5  # 上影线最小百分比
    g.upper_shadow_max = 8.6  # 上影线最大百分比
    g.n_day = 5  # N日
    g.n_day_gain_min = 0  # N日涨幅最小值
    g.n_day_gain_max = 10  # N日涨幅最大值
    g.turnover_rate_min = 10  # 换手率最小值
    g.turnover_rate_max = 30  # 换手率最大值
    g.market_cap_min = 10e8  # 最小市值
    g.market_cap_max = 200e8  # 最大市值
    g.turnover_value_max = 5000e4  # 最大成交额 (与策略描述一致)
    g.base_initial_cash = get_initial_cash(context, 5e4)  # 5e4 表示策略总资金池分配给本策略的额度
    
    # 回撤增资相关参数 (与 README.md 同步)
    g.drawdown_threshold_for_capital_increase = 0.07 / g.initial_cash_divisor  # 回撤增资阈值 (例如 0.07 代表 7%)
    g.capital_increase_ratio_on_drawdown = 0.60 / g.initial_cash_divisor # 回撤增资金额比例 (例如 0.20 代表当前投入基准的 20%)
    
    # 回升减资相关参数 (与 README.md 同步)
    g.rebound_threshold_for_capital_reduction = 0.08 / g.initial_cash_divisor # 回升减资阈值 (例如 0.10 代表 10%)
    g.capital_reduction_ratio_on_rebound = 0.50 / g.initial_cash_divisor # 回升减资金额比例 (例如 0.15 代表当前资产的 15%)

    # 将所有可变状态封装到 g.state 字典中
    g.state = {
        'cash': g.base_initial_cash / g.initial_cash_divisor,
        'standby_cash': g.base_initial_cash - (g.base_initial_cash / g.initial_cash_divisor),
        'stock_info_cache': {},
        'stock_name_cache': {},
        'hold_days': defaultdict(int),
        'highest_prices': defaultdict(float),
        'portfolio_values': [g.base_initial_cash],
        'peak_since_last_reduction': g.base_initial_cash,
        'valley_since_last_increase': g.base_initial_cash,
        'status_cache': {},  # 统一的股票状态缓存
        'status_cache_date': None,  # 状态缓存日期
    }

    log.set_log_level(log.LEVEL_INFO)

    g.commission_ratio = 0.00015  # 券商佣金费率 (例如 0.015%)
    g.min_commission = 5.0       # 最低佣金 (例如 5元)
    g.stamp_duty_rate = 0.0005   # 印花税率 (0.05%，仅卖出时收取)
    g.transfer_fee_rate = 0.00001 # 过户费率 (例如 0.001%，买卖双向收取)
    
    if is_trade():
        pickle_path = get_research_path()+'pickles_trade/'
        run_interval(context, check_order_status, seconds=60)
    else:
        # 回测专用设置
        pickle_path = get_research_path()+'pickles_test/'
        set_commission(commission_ratio=g.commission_ratio, min_commission=g.min_commission, type="STOCK")
        set_limit_mode('UNLIMITED') #回测中不限制成交数量
    
    # 统一的状态文件路径
    g.strategy_state_path = pickle_path + 'shadow_strategy_state.pkl'

    if not is_trade(): 
        clear_file(g.strategy_state_path) # 仅在回测模式下清空统一的状态文件


def filter_eligible_stocks(context, stocks, history_data):
    """批量筛选符合条件的股票 (进一步优化向量化计算)"""

    # 1. Pre-filter stocks with early exit optimization
    candidate_stocks = []
    positions_set = set(context.portfolio.positions.keys())  # 转换为set提高查找效率

    for stock in stocks:
        # Basic checks first (使用set查找更快)
        if stock in positions_set:
            continue
        if not is_listed_for_at_least_one_year(stock, context.previous_date):
            continue

        # Check for sufficient data
        hist = history_data.get(stock)
        if hist is None or len(hist['close']) < 20:
            continue

        candidate_stocks.append(stock)

    if not candidate_stocks:
        return []

    # 2. 优化数组构建 - 预分配并使用更高效的数据提取
    num_candidates = len(candidate_stocks)

    # 使用结构化数组一次性分配内存
    data_arrays = np.zeros(num_candidates, dtype=[
        ('close', 'f8'), ('open', 'f8'), ('high', 'f8'),
        ('volume', 'f8'), ('prev_volume', 'f8'),
        ('ma20', 'f8'), ('n_day_ago_close', 'f8')
    ])

    # 批量提取数据，减少重复的字典查找
    for i, stock in enumerate(candidate_stocks):
        hist = history_data[stock]
        close_prices = hist['close']

        data_arrays[i]['close'] = close_prices[-1]
        data_arrays[i]['open'] = hist['open'][-1]
        data_arrays[i]['high'] = hist['high'][-1]
        data_arrays[i]['volume'] = hist['volume'][-1]
        data_arrays[i]['prev_volume'] = hist['volume'][-2]
        data_arrays[i]['ma20'] = np.mean(close_prices[-20:])
        data_arrays[i]['n_day_ago_close'] = close_prices[-(g.n_day + 1)]

    # 3. 优化向量化条件计算 - 减少中间数组创建
    # 基础条件
    basic_mask = (data_arrays['close'] > g.min_price) & \
                 (data_arrays['close'] > data_arrays['ma20'] * g.ma_discount_rate) & \
                 (data_arrays['close'] > data_arrays['open']) & \
                 (data_arrays['volume'] > data_arrays['prev_volume'] * g.volume_increase_ratio)

    # 只对通过基础筛选的股票计算复杂指标
    if not np.any(basic_mask):
        return []

    # 上影线计算 (只计算通过基础筛选的)
    upper_shadows = np.where(
        basic_mask,
        (data_arrays['high'] - np.maximum(data_arrays['open'], data_arrays['close'])) / data_arrays['open'] * 100,
        0
    )
    shadow_mask = basic_mask & (upper_shadows >= g.upper_shadow_min) & (upper_shadows <= g.upper_shadow_max)

    # N日涨幅计算 (只计算通过上影线筛选的)
    n_day_gains = np.where(
        shadow_mask,
        (data_arrays['close'] - data_arrays['n_day_ago_close']) / data_arrays['n_day_ago_close'] * 100,
        0
    )
    gain_mask = shadow_mask & (n_day_gains >= g.n_day_gain_min) & (n_day_gains <= g.n_day_gain_max)

    # 成交额筛选 (最后计算)
    final_mask = gain_mask & ((data_arrays['close'] * data_arrays['volume']) >= g.turnover_value_max)

    # 4. 返回筛选结果
    return [candidate_stocks[i] for i in range(num_candidates) if final_mask[i]]

def before_trading_start(context, data):
    """交易日开始前筛选符合条件的股票 (I/O Optimized)"""
    load_strategy_state(context)

    # 每天动态计算最大持仓数量
    total_available_value = g.state['cash'] + _calculate_strategy_positions_value(context)
    g.max_stock_num = max(1, int(total_available_value / g.min_position_value))

    # 检查持仓限制
    num_of_pos = get_num_of_positions(context)
    if num_of_pos >= g.max_stock_num:
        log.info("持仓已达动态上限 {} 支，跳过选股。".format(g.max_stock_num))
        return

    # 1. 一次性获取所有股票状态并缓存
    update_daily_status_cache(context)

    # 2. 获取股票池并过滤状态
    all_stocks = filter_stock_by_status(get_Ashares())

    # 3. 批量预获取并缓存缺失的股票元数据
    prefetch_stock_metadata(all_stocks)

    # 4. 获取基本面数据
    fundamentals_data = get_fundamentals(all_stocks, 'valuation',
                                         fields=['turnover_rate', 'total_value'],
                                         date=context.previous_date).dropna()
    if fundamentals_data.empty:
        return

    # 市值筛选
    market_cap_mask = ((fundamentals_data['total_value'] > g.market_cap_min) &
                      (fundamentals_data['total_value'] < g.market_cap_max))
    fundamentals_data = fundamentals_data.loc[market_cap_mask]
    if fundamentals_data.empty:
        return

    # 换手率处理和筛选
    if g.isGuoSheng:
        fundamentals_data['turnover_rate'] = fundamentals_data['turnover_rate'].str.rstrip('%').astype(float)

    turnover_mask = ((fundamentals_data['turnover_rate'] >= g.turnover_rate_min) &
                    (fundamentals_data['turnover_rate'] <= g.turnover_rate_max))
    fundamentals_data = fundamentals_data.loc[turnover_mask]
    if fundamentals_data.empty:
        return

    # 按市值排序
    sorted_stocks = fundamentals_data.sort_values(by='total_value').index.tolist()

    # 5. 获取历史数据
    if g.isGuoSheng:
        history_data = get_history(20, frequency='1d',
                                 field=['close', 'high', 'low', 'open', 'volume'],
                                 security_list=sorted_stocks, fq=None, include=False)
        history_data = OrderedDict(
            (stock, OrderedDict(
                (field, np.array(history_data.loc[field, :, stock].values))
                for field in history_data.items
            )) for stock in history_data.minor_axis
        )
    else:
        history_data = get_history(20, frequency='1d',
                                 field=['close', 'high', 'low', 'open', 'volume'],
                                 security_list=sorted_stocks, fq='pre', include=False, is_dict=True)

    # 6. 筛选符合条件的股票
    to_buy = filter_eligible_stocks(context, sorted_stocks, history_data)

    if to_buy:
        g.to_buy = to_buy[:(g.max_stock_num - num_of_pos)]
        set_universe(g.to_buy)
        log.info("今日待选股票: {}".format(get_stock_names(g.to_buy)))


def handle_data(context, data):
    daily_sell_stocks(context)
    daily_buy_stocks(context)


def daily_sell_stocks(context):
    """每日卖出股票处理"""
    positions = context.portfolio.positions
    active_positions = [(stock, pos) for stock, pos in positions.items() if pos.enable_amount > 0]

    for stock, position in active_positions:
        # 跳过已经在卖出队列中的股票
        if stock in g.to_sell:
            continue

        # 停牌股票跳过
        if check_stock_halt_status(stock):
            continue

        current_price = position.last_sale_price
        buy_price = position.cost_basis
        highest_price = g.state['highest_prices'].get(stock, 0)
        hold_days = g.state['hold_days'].get(stock, 0)

        # 检查卖出条件
        sell_reason = get_sell_reason(current_price, buy_price, highest_price, hold_days)
        if sell_reason:
            g.to_sell[stock] = {
                'sell_reason': sell_reason,
                'return_rate': (current_price - buy_price) / buy_price,
                'market_value_at_sell': position.market_value,
                'sold_price': current_price,
                'sold_amount': position.amount
            }
            order_target(stock, 0)
            check_order_status(context)
            continue

        # 更新最高价格
        if current_price > highest_price:
            g.state['highest_prices'][stock] = current_price


def daily_buy_stocks(context):
    """每日买入股票处理"""
    if not g.to_buy:
        return

    num_of_pos = get_num_of_positions(context)
    remaining_slots = g.max_stock_num - num_of_pos
    if remaining_slots <= 0:
        return

    order_amount = g.state['cash'] / remaining_slots
    if order_amount <= 5000:
        return

    # 筛选待买入股票（排除已持有的股票）
    stocks_to_buy = [stock for stock in g.to_buy if g.state['hold_days'].get(stock, 0) == 0]

    # 科创板股票价格获取
    star_market_stocks = [stock for stock in stocks_to_buy if stock.startswith('688')]
    star_market_prices = {}
    if star_market_stocks:
        price_data = get_price(star_market_stocks, frequency='1d', count=1)
        if not price_data.empty:
            for stock in star_market_stocks:
                if stock in price_data.columns:
                    star_market_prices[stock] = price_data[stock]['close'].iloc[-1]

    for stock in stocks_to_buy:
        # 检查停牌状态
        if check_stock_halt_status(stock):
            continue

        # 科创板股票最小200股检查
        if stock.startswith('688'):
            current_price = star_market_prices.get(stock)
            if not current_price or order_amount < current_price * 200:
                continue

        order_value(stock, order_amount)
        check_order_status(context)


def get_sell_reason(current_price, buy_price, highest_price, hold_days):
    """判断是否应该卖出股票"""
    # 止损
    if current_price <= buy_price * (1 + g.stop_loss_rate / 100):
        return '下跌{:.2f}%止损'.format(g.stop_loss_rate)

    # 止盈后回撤
    if (current_price <= highest_price * (1 + g.drawdown_rate / 100) and
        current_price >= buy_price * (1 + g.take_profit_rate / 100)):
        return '涨幅超过{:.2f}%后从高点回撤{:.2f}%卖出'.format(g.take_profit_rate, g.drawdown_rate)

    # 持有期满
    if (hold_days >= g.max_hold_days and
        current_price <= buy_price * (1 + g.take_profit_rate / 100)):
        return '持有{}天且涨幅未超过{:.2f}%卖出'.format(g.max_hold_days, g.take_profit_rate)

    return ''


def check_order_status(context):
    """检查并处理订单状态"""
    cancel_stale_orders(context)
    finalize_sells(context)
    finalize_buys(context)


def cancel_stale_orders(context):
    """取消超时未成交订单"""
    now = datetime.now()
    for order in list(context.blotter.open_orders):
        if (now - order.created).seconds > 60:
            cancel_order(order)


def finalize_sells(context):
    """处理已卖出股票的后续事宜"""
    for stock in list(g.to_sell.keys()):
        position = context.portfolio.positions.get(stock)
        if not position or position.amount == 0:
            sell_info = g.to_sell[stock]
            value_at_sell = sell_info.get('market_value_at_sell', 0)

            # 计算交易费用
            commission = max(value_at_sell * g.commission_ratio, g.min_commission)
            stamp_duty = value_at_sell * g.stamp_duty_rate
            transfer_fee = value_at_sell * g.transfer_fee_rate
            total_fees = commission + stamp_duty + transfer_fee

            # 更新现金
            g.state['cash'] += (value_at_sell - total_fees)

            # 清理记录
            g.state['hold_days'].pop(stock, None)
            g.state['highest_prices'].pop(stock, None)

            log_stock_action(stock, '卖出',
                           '价格: {:.2f}, 数量: {}, 毛收益率: {:.2%}, 原因: {}'.format(
                               sell_info['sold_price'], sell_info['sold_amount'],
                               sell_info['return_rate'], sell_info['sell_reason']))
            g.to_sell.pop(stock)
        else:
            # 处理卖出失败的情况
            if position.enable_amount <= 0:
                log.warning("股票 {} 卖出失败：可卖数量为0，持仓数量: {}".format(stock, position.amount))
                # 移除失败的卖出记录，避免重复尝试
                g.to_sell.pop(stock)


def finalize_buys(context):
    """处理已买入股票的后续事宜"""
    for stock in g.to_buy[:]:
        position = context.portfolio.positions.get(stock)
        if position and position.amount > 0:
            # 计算总成本
            cost = position.cost_basis * position.amount
            commission = max(cost * g.commission_ratio, g.min_commission)
            transfer_fee = cost * g.transfer_fee_rate
            total_cost = cost + commission + transfer_fee

            # 更新状态
            g.state['cash'] -= total_cost
            g.state['hold_days'][stock] = 1
            g.state['highest_prices'][stock] = position.cost_basis

            log_stock_action(stock, '买入',
                           '价格: {:.2f}, 数量: {}, 金额: {:.2f}'.format(
                               position.cost_basis, position.amount, cost))

            g.to_buy.remove(stock)


def after_trading_end(context, data):
    """交易结束后执行的操作"""
    # 计算当前资产
    current_positions_value = _calculate_strategy_positions_value(context)
    current_total_assets = g.state['cash'] + g.state['standby_cash'] + current_positions_value

    # 计算回撤/回升率
    peak = g.state['peak_since_last_reduction']
    valley = g.state['valley_since_last_increase']
    drawdown_rate = (peak - current_total_assets) / peak if peak > 0 else 0
    rebound_rate = (current_total_assets - valley) / valley if valley > 0 else 0

    # 记录资产历史
    g.state['portfolio_values'].append(current_total_assets)

    # 记录日志
    log_eod_summary(context, current_total_assets, current_positions_value, rebound_rate, drawdown_rate)

    # 调整资金
    adjust_capital_on_drawdown(drawdown_rate, current_total_assets)
    adjust_capital_on_rebound(rebound_rate, current_total_assets)

    # 更新状态
    update_hold_days(context)
    update_highest_prices(context)
    cleanup_caches()
    save_strategy_state(context)
    

def adjust_capital_on_drawdown(drawdown_rate, current_total_assets):
    """回撤增资"""
    if drawdown_rate >= g.drawdown_threshold_for_capital_increase:
        should_add = g.base_initial_cash * g.capital_increase_ratio_on_drawdown
        capital_to_add = min(should_add, g.state['standby_cash'])
        if capital_to_add > 0:
            g.state['cash'] += capital_to_add
            g.state['standby_cash'] -= capital_to_add
            g.state['peak_since_last_reduction'] = current_total_assets

            log.info("++++++ 回撤 ≥{:.1%} ({:.2%})，增资 {:.2f}，应增资 {:.2f} (当前投入基准的 {:.1%})。新基准点: {:.2f} ++++++".format(
                g.drawdown_threshold_for_capital_increase, drawdown_rate, capital_to_add,
                should_add, g.capital_increase_ratio_on_drawdown, current_total_assets))


def adjust_capital_on_rebound(rebound_rate, current_total_assets):
    """回升减资"""
    if rebound_rate >= g.rebound_threshold_for_capital_reduction:
        should_reduce = g.base_initial_cash * g.capital_reduction_ratio_on_rebound
        capital_to_reduce = min(should_reduce, g.state['cash'])
        if capital_to_reduce > 0:
            g.state['cash'] -= capital_to_reduce
            g.state['standby_cash'] += capital_to_reduce
            g.state['valley_since_last_increase'] = current_total_assets

            log.info("------ 回升 ≥{:.1%} ({:.2%}), 减资 {:.2f}，应减资 {:.2f} (当前投入基准的 {:.1%})。新基准点: {:.2f} ------".format(
                g.rebound_threshold_for_capital_reduction, rebound_rate, capital_to_reduce,
                should_reduce, g.capital_reduction_ratio_on_rebound, current_total_assets))


def log_eod_summary(context, total_assets, positions_value, rebound_rate, drawdown_rate):
    """记录每日收盘后的策略摘要日志"""
    return_rate = (total_assets - g.base_initial_cash) / g.base_initial_cash
    max_drawdown = calculate_max_drawdown(g.state['portfolio_values'])
    max_rebound = calculate_max_rebound(g.state['portfolio_values'])
    eod_stocks = get_eod_stocks(context)
    current_positions = get_num_of_positions(context)

    log.info("收益率: {:.2%}, 回升率(决策): {:.2%}, 最大回升: {:.2%}, "
             "回撤率(决策): {:.2%}, 最大回撤: {:.2%}, "
             "现金: {:.2f}, 备用资金: {:.2f}, 持仓金额: {:.2f}, "
             "持仓: {} ({}/{}), 总资产: {:.2f}, 初始资金: {:.2f}".format(
                 return_rate, rebound_rate, max_rebound, drawdown_rate, max_drawdown,
                 g.state['cash'], g.state['standby_cash'], positions_value,
                 eod_stocks, current_positions, g.max_stock_num, total_assets, g.base_initial_cash))


def update_daily_status_cache(context):
    """每日更新股票状态缓存"""
    current_date = context.previous_date
    if g.state.get('status_cache_date') == current_date:
        return

    all_stocks = list(set(get_Ashares()) | set(context.portfolio.positions.keys()))
    status_cache = defaultdict(dict)

    for query_type in ["ST", "HALT", "DELISTING"]:
        status_result = get_stock_status(all_stocks, query_type=query_type)
        if status_result:
            for stock, has_status in status_result.items():
                status_cache[stock][query_type] = has_status

    g.state['status_cache'] = status_cache
    g.state['status_cache_date'] = current_date


def check_stock_halt_status(stock):
    """检查股票是否停牌"""
    return g.state.get('status_cache', {}).get(stock, {}).get('HALT', False)


def filter_stock_by_status(stocks):
    """过滤掉ST、退市、停牌股票"""
    status_cache = g.state.get('status_cache', {})
    return [stock for stock in stocks
            if not any(status_cache.get(stock, {}).get(status, False)
                      for status in ['ST', 'DELISTING', 'HALT'])]


def is_listed_for_at_least_one_year(stock, current_date):
    """判断股票上市时间是否大于一年"""
    stock_info = g.state['stock_info_cache'].get(stock)
    if not stock_info:
        return False
    listed_date = datetime.strptime(stock_info['listed_date'], '%Y-%m-%d').date()
    return (current_date - listed_date).days >= g.min_listed_days


def get_stock_names(stocks):
    """获取股票名称列表"""
    return [g.state['stock_name_cache'].get(stock, stock) for stock in stocks]


def prefetch_stock_metadata(stocks):
    """批量预获取并缓存股票元数据"""
    if not stocks:
        return

    info_to_fetch = [s for s in stocks if s not in g.state['stock_info_cache']]
    names_to_fetch = [s for s in stocks if s not in g.state['stock_name_cache']]

    if info_to_fetch:
        fetched_info = get_stock_info(info_to_fetch, ['listed_date'])
        if fetched_info:
            g.state['stock_info_cache'].update(fetched_info)

    if names_to_fetch:
        fetched_names = get_stock_name(names_to_fetch)
        if fetched_names:
            g.state['stock_name_cache'].update(fetched_names)


def get_eod_stocks(context):
    """获取当前投资组合中的股票名称列表"""
    active_stocks = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]
    return get_stock_names(active_stocks) if active_stocks else []


def get_num_of_positions(context):
    """获取当前投资组合中的股票数量"""
    return sum(1 for pos in context.portfolio.positions.values() if pos.amount > 0)


def get_initial_cash(context, max_cash=30e4):
    """设置初始资金"""
    return min(context.portfolio.starting_cash, max_cash)


def calculate_max_rebound(prices):
    """计算最大回升率"""
    prices = np.asarray(prices, dtype=np.float64)
    if prices.size < 2 or np.ptp(prices) == 0:
        return 0.0
    running_min = np.minimum.accumulate(prices)
    rebounds = np.divide(prices - running_min, running_min,
                        out=np.zeros_like(prices), where=running_min > 0)
    return float(np.max(rebounds))


def calculate_max_drawdown(prices):
    """计算最大回撤率"""
    prices = np.asarray(prices, dtype=np.float64)
    if prices.size < 2 or np.ptp(prices) == 0:
        return 0.0
    running_max = np.maximum.accumulate(prices)
    drawdowns = np.divide(running_max - prices, running_max,
                         out=np.zeros_like(prices), where=running_max > 0)
    return float(np.max(drawdowns))


def log_stock_action(stock, action, extra_info=''):
    """记录股票操作信息"""
    stock_name = get_stock_names([stock])[0]
    log.info('{} {}，{}'.format(action, stock_name, extra_info))


def clear_file(file_path):
    """删除指定路径的文件"""
    path = Path(file_path)
    if path.exists():
        path.unlink()


def update_highest_prices(context):
    """更新最高价格记录，清理不再持有的股票"""
    positions = context.portfolio.positions
    for sid in list(g.state['highest_prices'].keys()):
        if sid not in positions or positions[sid].amount == 0:
            g.state['highest_prices'].pop(sid, None)


def update_hold_days(context):
    """更新持仓天数，清理不再持有的股票"""
    positions = context.portfolio.positions
    for sid in list(g.state['hold_days'].keys()):
        if sid in positions and positions[sid].amount > 0:
            g.state['hold_days'][sid] += 1
        else:
            g.state['hold_days'].pop(sid, None)


def _calculate_strategy_positions_value(context):
    """计算策略持仓的总市值"""
    return sum(pos_obj.market_value for pos_obj in context.portfolio.positions.values()
              if pos_obj.amount > 0)


def load_strategy_state(context):
    """加载策略状态"""
    if hasattr(g, 'strategy_state_path') and Path(g.strategy_state_path).exists():
        with open(g.strategy_state_path, 'rb') as f:
            loaded_state = pickle.load(f)
            g.state.update(loaded_state)


def cleanup_caches():
    """清理缓存"""
    if len(g.state['portfolio_values']) > 1000:
        g.state['portfolio_values'] = g.state['portfolio_values'][-500:]

    if len(g.state['stock_info_cache']) > 1000:
        g.state['stock_info_cache'] = dict(list(g.state['stock_info_cache'].items())[-800:])

    if len(g.state['stock_name_cache']) > 1000:
        g.state['stock_name_cache'] = dict(list(g.state['stock_name_cache'].items())[-800:])


def save_strategy_state(context):
    """保存策略状态"""
    if hasattr(g, 'strategy_state_path'):
        with open(g.strategy_state_path, 'wb') as f:
            pickle.dump(g.state, f, pickle.HIGHEST_PROTOCOL)