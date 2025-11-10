import numpy as np
from datetime import datetime
from pathlib import Path
from collections import defaultdict, OrderedDict
import pickle

''' 
此策略是 shadow 策略框架与 5mv 策略核心逻辑的结合体。
框架与风控: 完整保留 shadow 策略的参数管理、动态资金调整、风险控制（仓位大小、动态止损）及数据处理功能。
核心交易逻辑: 采用 5mv 策略的信号生成规则。
  - 买入条件: 收盘价高于5日VWAP和20日均线，且前一日收盘价低于5日均线。
  - 卖出条件: 在原有止盈止损基础上，增加收盘价低于5日VWAP或20日均线的离场规则。
'''

def initialize(context):
    # 初始化全局变量
    g.isGuoSheng = False # 是否为国盛证券
    g.to_buy = []
    g.to_sell = {}

    # 策略参数 (来自 shadow_strategy)
    g.min_position_value = 10000  # 每个持仓的最小金额
    g.max_hold_days = 12  # 最大持有天数
    g.stop_loss_rate = -7  # 止损率
    g.take_profit_rate = 20  # 止盈率
    g.drawdown_rate = -3  # 回撤率
    g.initial_cash_divisor = 2  # 初始资金使用比例的除数

    # 选股条件参数 (部分来自 shadow_strategy, 部分为 5mv 适配)
    g.min_listed_days = 365  # 最小上市天数
    g.min_price = 2.0  # 最低股价
    g.ma_discount_rate = 0.95  # MA折扣率, 在此策略中用作 5mv 的 magic_num
    g.market_cap_min = 10e8  # 最小市值
    g.market_cap_max = 200e8  # 最大市值
    g.turnover_rate_min = 10  # 换手率最小值
    g.turnover_rate_max = 30  # 换手率最大值
    g.base_initial_cash = get_initial_cash(context, 5e4)
    
    # 回撤增资相关参数 (来自 shadow_strategy)
    g.drawdown_threshold_for_capital_increase = 0.07 / g.initial_cash_divisor
    g.capital_increase_ratio_on_drawdown = 0.60 / g.initial_cash_divisor
    
    # 回升减资相关参数 (来自 shadow_strategy)
    g.rebound_threshold_for_capital_reduction = 0.08 / g.initial_cash_divisor
    g.capital_reduction_ratio_on_rebound = 0.50 / g.initial_cash_divisor

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
    

    # 交易费用参数 (来自 shadow_strategy)
    g.commission_ratio = 0.00015
    g.min_commission = 5.0
    g.stamp_duty_rate = 0.0005
    g.transfer_fee_rate = 0.00001
    
    if is_trade():
        pickle_path = get_research_path()+'pickles_trade/'
        run_interval(context, check_order_status, seconds=60)
    else:
        pickle_path = get_research_path()+'pickles_test/'
        set_commission(commission_ratio=g.commission_ratio, min_commission=g.min_commission, type="STOCK")
        set_limit_mode('UNLIMITED')
    
    g.strategy_state_path = pickle_path + '5mv_strategy_state.pkl'

    if not is_trade(): 
        clear_file(g.strategy_state_path)


def is_stock_eligible(context, stock, history_data_for_stock):
    """
    判断股票是否符合筛选条件 (5mv 逻辑)。
    """
    if stock in context.portfolio.positions and context.portfolio.positions[stock].amount > 0:
        return False
    
    if not is_listed_for_at_least_one_year(stock, context.previous_date):
        return False

    if len(history_data_for_stock['close']) < 21:
        return False

    close_price = history_data_for_stock['close'][-1]
    if close_price <= g.min_price:
        return False

    ma5 = np.mean(history_data_for_stock['close'][-5:])
    ma20 = np.mean(history_data_for_stock['close'][-20:])
    
    vol5 = history_data_for_stock['volume'][-5:]
    close5 = history_data_for_stock['close'][-5:]
    vwap5 = np.sum(close5 * vol5) / np.sum(vol5) if np.sum(vol5) > 0 else close_price

    pre_close = history_data_for_stock['close'][-2]

    buy_cond1 = close_price > vwap5 * g.ma_discount_rate
    buy_cond2 = pre_close < ma5
    buy_cond3 = close_price > ma20
    
    return buy_cond1 and buy_cond2 and buy_cond3


def before_trading_start(context, data):
    """
    交易日开始前筛选符合条件的股票。
    """
    load_strategy_state(context)

    # 每天动态计算最大持仓数量
    total_available_value = g.state['cash'] + _calculate_strategy_positions_value(context)
    g.max_stock_num = max(1, int(total_available_value / g.min_position_value))

    # 检查持仓限制
    num_of_pos = get_num_of_positions(context)
    if num_of_pos >= g.max_stock_num:
        log.info("持仓已达动态上限 {} 支，跳过选股。".format(g.max_stock_num))
        g.to_buy = []
        set_universe([])
        return

    # 1. 一次性获取所有股票状态并缓存
    update_daily_status_cache(context)

    # 2. 获取股票池并过滤状态
    all_stocks = filter_stock_by_status(get_Ashares())

    # 3. 批量预获取并缓存缺失的股票元数据
    prefetch_stock_metadata(all_stocks)

    fundamentals_data = get_fundamentals(all_stocks, 'valuation',
                                         fields=['turnover_rate', 'total_value'],
                                         date=context.previous_date).dropna()

    if fundamentals_data.empty:
        log.warning("基本面数据为空，跳过选股")
        return

    fundamentals_data = fundamentals_data.loc[(fundamentals_data['total_value'] > g.market_cap_min) & (fundamentals_data['total_value'] < g.market_cap_max)].sort_values(by='total_value')
    fundamentals_data['turnover_rate'] = fundamentals_data['turnover_rate'].apply(
        lambda x: float(x.strip('%')) if g.isGuoSheng else x)

    sorted_stocks = fundamentals_data[(fundamentals_data['turnover_rate'] >= g.turnover_rate_min) &
                                      (fundamentals_data['turnover_rate'] <= g.turnover_rate_max)].index.tolist()

    if not sorted_stocks:
        log.info("没有符合换手率条件的股票")
        return

    if g.isGuoSheng:
        history_data = get_history(21, frequency='1d', field=['close', 'volume'], security_list=sorted_stocks, fq=None, include=False)
        history_data = OrderedDict(
            (stock, OrderedDict(
                (field, np.array(history_data.loc[field, :, stock].values))
                for field in history_data.items
            )) for stock in history_data.minor_axis
        )
    else:
        history_data = get_history(21, frequency='1d', field=['close', 'volume'], security_list=sorted_stocks, fq='pre', include=False, is_dict=True)

    to_buy = [stock for stock in sorted_stocks if stock in history_data and is_stock_eligible(context, stock, history_data[stock])]

    if to_buy:
        g.to_buy = to_buy[:(g.max_stock_num - num_of_pos)]
        set_universe(g.to_buy)
        log.info("今日待选股票: {}".format(get_stock_names(g.to_buy)))
    else:
        g.to_buy = []
        log.info("没有符合筛选条件的股票")


def handle_data(context, data):
    daily_sell_stocks(context, data)
    daily_buy_stocks(context)


def daily_sell_stocks(context, data):
    """每日卖出股票处理"""
    positions = context.portfolio.positions
    active_positions = [(stock, pos) for stock, pos in positions.items() if pos.enable_amount > 0]

    for stock, position in active_positions:
        # 停牌股票跳过
        if check_stock_halt_status(stock):
            continue

        current_price = position.last_sale_price
        buy_price = position.cost_basis
        highest_price = g.state['highest_prices'].get(stock, 0)
        hold_days = g.state['hold_days'].get(stock, 0)

        # 检查卖出条件
        sell_reason = get_sell_reason(current_price, buy_price, highest_price, hold_days, data, stock)
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


def get_sell_reason(current_price, buy_price, highest_price, hold_days, data, stock):
    """
    判断是否应该卖出股票 (结合 shadow 和 5mv 逻辑)。
    """
    if current_price <= buy_price * (1 + g.stop_loss_rate / 100):
        return '下跌{:.2f}%止损'.format(g.stop_loss_rate)
    if current_price <= highest_price * (1 + g.drawdown_rate / 100) and current_price >= buy_price * (1 + g.take_profit_rate / 100):
        return '涨幅超过{:.2f}%后从高点回撤{:.2f}%卖出'.format(g.take_profit_rate, g.drawdown_rate)
    if hold_days >= g.max_hold_days and current_price <= buy_price * (1 + g.take_profit_rate / 100):
        return '持有{}天且涨幅未超过{:.2f}%卖出'.format(g.max_hold_days, g.take_profit_rate)

    ma20 = data[stock].mavg(20)
    if current_price < ma20:
        return '收盘价低于20日均线'
        
    vwap5 = data[stock].vwap(5)
    if current_price < vwap5 * g.ma_discount_rate:
        return '收盘价低于5日VWAP'

    return ''


def check_order_status(context):
    cancel_stale_orders(context)
    finalize_sells(context)
    finalize_buys(context)


def cancel_stale_orders(context):
    now = datetime.now()
    for order in list(context.blotter.open_orders):
        if (now - order.created).seconds > 60:
            cancel_order(order)
            log.info("取消超时未成交订单: {}".format(order))


def finalize_sells(context):
    """处理已卖出股票的后续事宜"""
    for stock in list(g.to_sell.keys()):
        position = context.portfolio.positions.get(stock)

        # 检查是否真的卖出了（持仓为0或不存在）
        if not position or position.amount == 0:
            sell_info = g.to_sell[stock]
            value_at_sell = sell_info.get('market_value_at_sell', 0)
            sold_price = sell_info['sold_price']
            sold_amount = sell_info['sold_amount']

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

            log_stock_action(stock, '卖出', '价格: {:.2f}, 数量: {}, 毛收益率: {:.2%}, 原因: {}'.format(
                sold_price, sold_amount, sell_info['return_rate'], sell_info['sell_reason']))

            g.to_sell.pop(stock)
        else:
            # 如果还有持仓，说明卖出可能失败，检查原因
            if position.enable_amount <= 0:
                log.warning("股票 {} 卖出失败：可卖数量为0，持仓数量: {}".format(stock, position.amount))
                # 移除失败的卖出记录，避免重复尝试
                g.to_sell.pop(stock)


def finalize_buys(context):
    for stock in g.to_buy[:]:
        position = context.portfolio.positions.get(stock)
        if position and position.amount > 0:
            cost = position.cost_basis * position.amount
            commission = max(cost * g.commission_ratio, g.min_commission)
            transfer_fee = cost * g.transfer_fee_rate
            total_cost = cost + commission + transfer_fee

            g.state['cash'] -= total_cost
            g.state['hold_days'][stock] = 1
            g.state['highest_prices'][stock] = position.cost_basis
            
            log_stock_action(stock, '买入', '价格: {:.2f}, 数量: {}, 金额: {:.2f}'.format(position.cost_basis, position.amount, cost))
            
            g.to_buy.remove(stock)


def after_trading_end(context, data):
    current_positions_value = _calculate_strategy_positions_value(context)
    current_total_assets = g.state['cash'] + g.state['standby_cash'] + current_positions_value

    drawdown_rate_for_increase = (g.state['peak_since_last_reduction'] - current_total_assets) / g.state['peak_since_last_reduction'] if g.state['peak_since_last_reduction'] > 0 else 0
    rebound_rate_for_reduction = (current_total_assets - g.state['valley_since_last_increase']) / g.state['valley_since_last_increase'] if g.state['valley_since_last_increase'] > 0 else 0

    g.state['portfolio_values'].append(current_total_assets)

    log_eod_summary(context, current_total_assets, current_positions_value, rebound_rate_for_reduction, drawdown_rate_for_increase)

    adjust_capital_on_drawdown(drawdown_rate_for_increase, current_total_assets)
    adjust_capital_on_rebound(rebound_rate_for_reduction, current_total_assets)

    update_hold_days(context)
    update_highest_prices(context)
    cleanup_caches()
    save_strategy_state(context)
    

def adjust_capital_on_drawdown(drawdown_rate, current_total_assets):
    if drawdown_rate >= g.drawdown_threshold_for_capital_increase:
        should_add = g.base_initial_cash * g.capital_increase_ratio_on_drawdown
        capital_to_add = min(should_add, g.state['standby_cash'])
        if capital_to_add > 0:
            g.state['cash'] += capital_to_add
            g.state['standby_cash'] -= capital_to_add
            g.state['peak_since_last_reduction'] = current_total_assets
            log.info("++++++ 回撤 ≥{:.1%} ({:.2%})，增资 {:.2f} ++++++".format(
                g.drawdown_threshold_for_capital_increase, drawdown_rate, capital_to_add))


def adjust_capital_on_rebound(rebound_rate, current_total_assets):
    if rebound_rate >= g.rebound_threshold_for_capital_reduction:
        should_reduce = g.base_initial_cash * g.capital_reduction_ratio_on_rebound
        capital_to_reduce = min(should_reduce, g.state['cash'])
        if capital_to_reduce > 0:
            g.state['cash'] -= capital_to_reduce
            g.state['standby_cash'] += capital_to_reduce
            g.state['valley_since_last_increase'] = current_total_assets
            log.info("------ 回升 ≥{:.1%} ({:.2%}), 减资 {:.2f} ------".format(
                g.rebound_threshold_for_capital_reduction, rebound_rate, capital_to_reduce))


def log_eod_summary(context, total_assets, positions_value, rebound_rate, drawdown_rate):
    return_rate = (total_assets - g.base_initial_cash) / g.base_initial_cash if g.base_initial_cash > 0 else 0.0
    max_drawdown = calculate_max_drawdown(g.state['portfolio_values'])
    max_rebound = calculate_max_rebound(g.state['portfolio_values'])
    
    log.info(
        "收益率: {:.2%}, 回升率(决策): {:.2%}, 最大回升: {:.2%}, "
        "回撤率(决策): {:.2%}, 最大回撤: {:.2%}, "
        "现金: {:.2f}, 备用资金: {:.2f}, 持仓金额: {:.2f}, "
        "持仓: {}, 总资产: {:.2f}, 初始资金: {:.2f}".format(
            return_rate, rebound_rate, max_rebound,
            drawdown_rate, max_drawdown,
            g.state['cash'], g.state['standby_cash'], positions_value,
            get_eod_stocks(context), total_assets, g.base_initial_cash
        )
    )

# =====================================================================================
# 辅助函数
# =====================================================================================

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


def get_eod_stocks(context):
    """获取当前投资组合中的股票名称列表"""
    active_stocks = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]
    return get_stock_names(active_stocks) if active_stocks else []


def get_num_of_positions(context):
    return sum(1 for pos in context.portfolio.positions.values() if pos.amount > 0)


def get_initial_cash(context, max_cash=30e4):
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
    stock_name = g.state['stock_name_cache'].get(stock, stock)
    log.info('{} {}，{}'.format(action, stock_name, extra_info))


def clear_file(file_path):
    """清空文件"""
    path = Path(file_path)
    if path.exists():
        path.unlink()


def update_highest_prices(context):
    """更新最高价格记录"""
    for sid in list(g.state['highest_prices'].keys()):
        if sid not in context.portfolio.positions or context.portfolio.positions[sid].amount == 0:
            g.state['highest_prices'].pop(sid, None)


def update_hold_days(context):
    """更新持有天数"""
    for sid in list(g.state['hold_days'].keys()):
        if sid in context.portfolio.positions and context.portfolio.positions[sid].amount > 0:
            g.state['hold_days'][sid] += 1
        else:
            g.state['hold_days'].pop(sid, None)


def _calculate_strategy_positions_value(context):
    return sum(pos.market_value for pos in context.portfolio.positions.values() if pos.amount > 0)


def load_strategy_state(context):
    """加载策略状态"""
    if hasattr(g, 'strategy_state_path') and Path(g.strategy_state_path).exists():
        with open(g.strategy_state_path, 'rb') as f:
            loaded_state = pickle.load(f)
            g.state.update(loaded_state)


def save_strategy_state(context):
    """保存策略状态"""
    # 确保目录存在
    Path(g.strategy_state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(g.strategy_state_path, 'wb') as f:
        pickle.dump(g.state, f, pickle.HIGHEST_PROTOCOL)


def cleanup_caches():
    """清理缓存"""
    if len(g.state['portfolio_values']) > 1000:
        g.state['portfolio_values'] = g.state['portfolio_values'][-500:]

    if len(g.state['stock_info_cache']) > 1000:
        g.state['stock_info_cache'] = dict(list(g.state['stock_info_cache'].items())[-800:])

    if len(g.state['stock_name_cache']) > 1000:
        g.state['stock_name_cache'] = dict(list(g.state['stock_name_cache'].items())[-800:])
