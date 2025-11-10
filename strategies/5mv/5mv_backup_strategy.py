# -*- coding: utf-8 -*-
from collections import defaultdict
from pathlib import Path
import pickle

'''
持仓N日后卖出，仓龄变量每日pickle进行保存，重启策略后可以保证逻辑连贯
'''

def initialize(context): 
    both_settings()
    if is_trade():
        pickle_path = get_research_path()+'pickles_trade/'
    else:
        backtest_only_settings() 
        pickle_path = get_research_path()+'pickles_test/'
          
    g.hold_days_path = pickle_path + '5d_hold_days.pkl'
    g.highest_prices_path = pickle_path + '5d_highest_prices.pkl'
    
    clear_file(g.hold_days_path)
    clear_file(g.highest_prices_path)
    
    # 每天在收盘后（15:30）运行计算收益率的函数
    run_daily(context, buy_stock, time='9:30')


def backtest_only_settings():
    set_commission(commission_ratio =0.00015, min_commission=5.0, type="STOCK")
    set_limit_mode('UNLIMITED') #回测中不限制成交数量


def both_settings():
    """设置通用参数，调整参数以优化策略表现。"""
    g.num_of_stocks = 5  # 持仓股票数量
    g.max_hold_days = 3  # 最大持仓天数
    g.drawdown_rate = 5  # 回撤阈值
    g.take_profit_rate = 8  # 止盈阈值
    g.stop_loss_rate = -5  # 止损阈值
    g.magic_num = 0.95  # 调整魔法数字
    g.security=[]


def buy_stock(context):
    for sid in g.security:
        stock_name = get_stock_name(sid)
        order_id = None
        if is_trade():
            price = get_gear_price(sid)
            log.info(price)
            order_id = order_market(sid, 10000, 4, limit_price=price['offer_grp'][1][0]) # type: ignore
            ''' 0：对手方最优价格；
                1：最优五档即时成交剩余转限价；
                2：本方最优价格；
                3：即时成交剩余撤销；
                4：最优五档即时成交剩余撤销；
                5：全额成交或撤单；
                (上证非科创板股票支持参数1、4，
                 上证科创板股票支持参数0、1、2、4，
                 深证股票支持参数0、2、3、4、5
                 市价委托上证股票时保护限价limit_price为必传字段)
            '''
        else:
            order_id = order_value(sid, 10000, limit_price=None) # 默认用行情快照数据最新价报单
        if order_id and len(context.blotter.open_orders)==0:
            g.hold_days[sid] = 1
            log.info('{} 建仓成功'.format(stock_name))
        else:
            log.warning('{} 建仓失败'.format(stock_name))
                

def filter_stock_by_condition(context, stocks, data):
    """过滤股票的条件函数，增加更多过滤条件以筛选优质股票。"""
    # 过滤创业板股票
    stocks = [sid for sid in stocks if not sid.startswith('3')]
    # 过滤ST、HALT、DELISTING状态的股票
    stocks = filter_stock_by_status(stocks)
    # 获取股票池中对应上市公司的A股总市值(元)、动态市盈率、换手率和市净率数据
    stocks = get_fundamentals(stocks, 'valuation', date = context.blotter.current_dt, fields = ['total_value', 'pe_dynamic', 'turnover_rate', 'pb'])
    # 过滤市盈率大于100的股票
    stocks = stocks[stocks['pe_dynamic'] <= 100]
    # 过滤市净率大于5的股票
    stocks = stocks[stocks['pb'] <= 5]
    # 按换手率降序排序
    stocks = stocks.sort_values(by="turnover_rate", ascending=False).index.tolist()
    return stocks


def before_trading_start(context, data):
    g.hold_days = load_pickle(g.hold_days_path) # 加载仓龄数据
    g.highest_prices = load_pickle(g.highest_prices_path)
    # 检查持仓数量是否等于 num_of_stocks
    num_of_stocks = len(context.portfolio.positions)
    if num_of_stocks >= g.num_of_stocks:
        log.info('持仓股票数量已达到 {} 支，跳过选股。'.format(num_of_stocks))
        g.security=[] # 清空选股池
        set_universe(g.security)
        return

    hs300 = filter_stock_by_status(get_index_stocks('000300.SS'))
    # 过滤掉已持仓的股票
    pos = context.portfolio.positions
    hs300 = [stock for stock in hs300 if stock not in pos.keys()]
    g.security = []

    for sid in filter_stock_by_condition(context, hs300, data):
        if buy_condition(context, data, sid):
            g.security.append(sid)
    g.security = g.security[:(g.num_of_stocks-len(pos))]
    set_universe(g.security)


def handle_data(context, data):
    for sid in context.portfolio.positions:
        if sell_condition(context, data, sid):
            stock_name = get_stock_name(sid)
            order_id = order_target(sid, 0, limit_price=None) # 卖出所有股票,使这只股票的最终持有量为0
            if order_id and len(context.blotter.open_orders)==0:
                g.hold_days.pop(sid)
                g.highest_prices.pop(sid)
                log.info('{} 清仓成功'.format(stock_name))
            else:
                log.warning('{} 清仓失败'.format(stock_name))


def buy_condition(context, data, sid):
    """优化后的买入条件，增加更多指标判断。"""
    ma5 = data[sid].mavg(5)  # 5日平均价格
    vw5 = data[sid].vwap(5)  # 5日交易量加权平均价格
    ma20 = data[sid].mavg(20)  # 20日平均价格
    
    # 增加20日线判断，要求收盘价高于20日线
    if data[sid].close > vw5 * g.magic_num and data[sid].pre_close < ma5 and data[sid].close > ma20:
        return True
    return False


def sell_condition(context, data, sid):
    """优化后的卖出条件，增加更多指标判断。"""
    stock_name = get_stock_name(sid)
    pos = context.portfolio.positions[sid]
    ma5 = data[sid].mavg(5)
    vw5 = data[sid].vwap(5)
    close = data[sid].close
    
    value = pos.cost_basis * pos.amount
    profit = (pos.market_value - value) / value
    
    # 更新历史最高股价
    g.highest_prices[sid] = max(g.highest_prices[sid], close)
    drawdown = (g.highest_prices[sid] - close) / g.highest_prices[sid]
    
    log.info("{}盈亏：{:>6.2%} 高点回撤：{:.2%}".format(stock_name, profit, drawdown))
    
    # 增加20日线判断，收盘价低于20日线则卖出
    ma20 = data[sid].mavg(20)
    if (profit < g.take_profit_rate and (close < vw5 * g.magic_num or g.hold_days[sid] >= g.max_hold_days or close < ma20) or 
        profit >= g.take_profit_rate and drawdown >= g.drawdown_rate or profit < g.stop_loss_rate):
        return True
    return False


def after_trading_end(context, data):
    update_and_save_hold_days(context, g.hold_days_path) # 仓龄增加一天并持久化
    update_and_save_highest_prices(context, data, g.highest_prices_path)
    calculate_daily_yield(context)


def filter_stock_by_status(stocks, filter_types=["ST", "HALT", "DELISTING"]):
    for filter_type in filter_types:
        stocks_dict = get_stock_status(stocks, query_type=filter_type)
        stocks_with_status = [stock for stock, status in stocks_dict.items() if status]
        #log.info(filter_type+"："+str(stocks_with_status))
        stocks = list(set(stocks) - set(stocks_with_status))
    return stocks


def calculate_daily_yield(context):
    current_value = context.portfolio.portfolio_value # 获取当前总资产
    initial_value = context.portfolio.starting_cash # 获取昨日总资产
    daily_yield = (current_value - initial_value) / initial_value # 计算收益率
    log.info("当前总体仓位收益率：{:.2%}".format(daily_yield))


def clear_file(file_path):
    pkl = Path(file_path)
    # 删除文件
    if pkl.exists():
        pkl.unlink() 


def load_pickle(file_path):
    """ 尝试从指定的pickle文件中加载数据。"""
    try:
        with open(file_path, 'rb') as f:
            p = pickle.load(f)
    except Exception as e:
        log.info("加载pickle失败或内容为空，返回默认值。")
        return defaultdict(int)
    return p


def update_and_save_highest_prices(context, data, file_path):
    if g.highest_prices:
        for sid in list(g.highest_prices.keys()):
            if sid not in context.portfolio.positions:
                # 安全删除记录
                g.highest_prices.pop(sid)
                log.info("清除错误最高价记录：{}".format(get_stock_name(sid)))
    with open(file_path, 'wb') as f:
        pickle.dump(g.highest_prices, f, -1)


def update_and_save_hold_days(context, file_path):
    ''' 增加仓龄, 使用pickle保存仓龄到文件 '''
    if g.hold_days:
        for sid in list(g.hold_days.keys()):
            if sid in context.portfolio.positions:
                g.hold_days[sid] += 1
                #log.info("持有{}共{}天".format(get_stock_name(sid), g.hold_days[sid]))
            else:
                # 安全删除记录
                g.hold_days.pop(sid)
                log.info("清除错误持有天记录：{}".format(get_stock_name(sid)))
    with open(file_path, 'wb') as f:
        pickle.dump(g.hold_days, f, -1)