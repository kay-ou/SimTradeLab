# -*- coding: utf-8 -*-
"""
20日均线选股策略策略

核心逻辑：
1. 从股价同时在5日线和10日线上方的股票中随机选择10支买入
2. 每5天检查持仓，剔除5日收益为负的股票
3. 补入新的满足均线条件的股票，保持10支持仓
"""

import numpy as np
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import pickle
import math


def initialize(context):
    """策略初始化"""
    # ==================== 策略核心参数 ====================
    g.max_positions = 9              # 最大持仓数量
    g.rebalance_days = 5             # 每5天调仓一次

    # ==================== 选股参数 ====================
    g.min_market_cap = 100e8        # 最小市值（2000亿）
    g.max_market_cap = 30000e8       # 最大市值（30000亿）
    g.ma_short = 5                   # 短期均线天数
    g.ma_middle = 10                 # 中期均线天数
    g.ma_long = 20                   # 长期均线天数

    # ==================== 调仓参数 ====================
    g.eliminate_mode = 'fixed'       # 淘汰模式：'fixed' 固定数量 / 'dynamic' 动态调整
    g.eliminate_count = 1            # 固定模式下每次淘汰数量
    g.eliminate_threshold = -0.05    # 固/动态模式：综合评分低于此阈值必淘汰
    g.eliminate_ratio = 0.20         # 动态模式：淘汰最差20%持仓

    # ==================== 个股止损参数 ====================
    g.enable_individual_stop_loss = False      # 是否启用个股止损
    g.individual_stop_loss_threshold = -0.03  # 个股止损阈值（5日内下跌>8%）
    g.individual_stop_loss_days = 5           # 止损观察期（5日内）

    # ==================== 整体止损参数 ====================
    g.enable_portfolio_stop_loss = False       # 是否启用整体止损
    g.portfolio_stop_loss_threshold = -0.05   # 整体止损阈值（80%持仓平均下跌>5%）
    g.portfolio_loss_percentile = 0.80        # 计算跌幅时考虑的持仓比例（80%）

    # ==================== 策略状态 ====================
    g.state = {
        'hold_days': defaultdict(int),         # 持有天数
        'entry_prices': defaultdict(float),    # 买入价
        'highest_returns': defaultdict(float), # 持仓期间最高收益率
        'total_profit': defaultdict(float),    # 累计盈利（绝对金额）
        'last_rebalance_day': 0,               # 上次调仓的交易日计数
        'trading_day_count': 0,                # 交易日计数器
        'is_trading_paused': False,            # 是否暂停交易（进入观察模式）
        'virtual_positions': {},               # 虚拟持仓 {stock: {'entry_price': float, 'hold_days': int, 'highest_return': float}}
        'initial_observation_mode': True,      # 首日虚拟观察模式
    }

    # 初始化交易列表
    g.to_buy = []
    g.to_sell = {}

    # 设置基准指数
    set_benchmark('000300.SS')

    # 日志记录
    log.info("="*60)
    log.info("20日均线选股策略")
    log.info("="*60)
    log.info("【策略参数】")
    log.info("  最大持仓数: {} 只".format(g.max_positions))
    log.info("  调仓周期: {} 天".format(g.rebalance_days))
    log.info("  仓位管理: 等权重分配（每只 {:.1%}）".format(1.0 / g.max_positions))
    log.info("【选股条件】")
    log.info("  短期均线: {} 日".format(g.ma_short))
    log.info("  长期均线: {} 日".format(g.ma_long))
    log.info("  市值范围: {:.0f}亿 - {:.0f}亿".format(
        g.min_market_cap / 1e8, g.max_market_cap / 1e8))
    log.info("【调仓规则】")
    log.info("  调仓周期: {}天".format(g.rebalance_days))
    if g.eliminate_mode == 'fixed':
        log.info("  淘汰模式: 固定淘汰{}只".format(g.eliminate_count))
    else:
        log.info("  淘汰模式: 动态淘汰（最差{:.0%}或评分<{:.2}）".format(
            g.eliminate_ratio, g.eliminate_threshold))
    log.info("  淘汰标准: 综合盈利 + 盈利回撤")
    log.info("【个股止损】")
    log.info("  个股止损开关: {}".format("开启" if g.enable_individual_stop_loss else "关闭"))
    if g.enable_individual_stop_loss:
        log.info("  止损条件: {}日内下跌 > {:.1%}".format(
            g.individual_stop_loss_days, g.individual_stop_loss_threshold))
    log.info("【整体止损】")
    log.info("  整体止损开关: {}".format("开启" if g.enable_portfolio_stop_loss else "关闭"))
    if g.enable_portfolio_stop_loss:
        log.info("  止损阈值: {:.1%}持仓平均跌幅 > {:.1%}".format(
            g.portfolio_loss_percentile, g.portfolio_stop_loss_threshold))
    log.info("="*60)

    # 设置状态持久化路径
    if is_trade():
        pickle_path = get_research_path() + 'pickles_trade/'
    else:
        pickle_path = get_research_path() + 'pickles_test/'

    g.strategy_state_path = pickle_path + 'ma_random_state.pkl'

    # 回测模式下清空状态文件
    if not is_trade():
        clear_file(g.strategy_state_path)

    # 实盘模式：在开盘时买入
    if is_trade():
        run_daily(context, buy_stocks, time='09:25')


def before_trading_start(context, data):
    """盘前处理入口"""
    # 加载策略状态
    load_strategy_state(context)

    # 交易日计数器+1
    g.state['trading_day_count'] += 1

    # 打印日期标识
    current_date = context.blotter.current_dt.date()
    log.info("")
    log.info("=" * 60)
    log.info("【{}】交易日 #{}".format(current_date, g.state['trading_day_count']))
    log.info("=" * 60)

    # 内存优化：清理过期缓存（非当日）
    if hasattr(g, 'ma_qualified_cache_date') and g.ma_qualified_cache_date != current_date:
        # 清理过期的选股缓存
        del g.ma_qualified_cache
        del g.ma_qualified_cache_date
    if hasattr(g, 'status_cache_date') and g.status_cache_date != current_date:
        # 清理过期的状态缓存
        del g.status_cache
        del g.status_cache_date

    # 将持仓股票加入股票池
    current_positions = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]
    if current_positions:
        set_universe(current_positions)

    # ==================== 虚拟观察模式统一处理 ====================
    # 首日无持仓或整体止损后进入虚拟观察
    in_virtual_mode = (g.state['initial_observation_mode'] and not current_positions) or g.state['is_trading_paused']

    if in_virtual_mode:
        # 虚拟观察期间不执行每日止损检查，只在handle_virtual_trading_mode中评估
        handle_virtual_trading_mode(context, data)
        return  # 虚拟观察期间不执行实际交易

    # 如果已有实际持仓，退出首日观察模式
    if g.state['initial_observation_mode'] and current_positions:
        g.state['initial_observation_mode'] = False
        log.info("【退出首日观察】已有实际持仓，开始正常交易")

    # ==================== 检查整体止损条件 ====================
    if g.enable_portfolio_stop_loss:
        check_portfolio_stop_loss(context, data)
        # 如果触发了整体止损,立即返回,不执行后续调仓逻辑
        if g.state['is_trading_paused']:
            return

    # ==================== 检查个股止损条件 ====================
    if g.enable_individual_stop_loss and not g.state['is_trading_paused']:
        check_individual_stop_loss(context, data)

    # 检查是否需要调仓
    days_since_rebalance = g.state['trading_day_count'] - g.state['last_rebalance_day']

    if days_since_rebalance < g.rebalance_days:
        log.info("距上次调仓 {} 天，跳过本次调仓（调仓周期：{}天）".format(
            days_since_rebalance, g.rebalance_days))
        return

    log.info("开始调仓流程 | 距上次调仓: {} 天".format(days_since_rebalance))

    # 清理待处理订单
    g.to_buy = []
    g.to_sell = {}

    # 第一步：检查持仓，剔除5日收益为负的股票
    check_and_sell_losers(context, data)

    # 第二步：获取符合均线条件的股票池
    stock_pool = get_ma_qualified_stocks(context, data)

    if not stock_pool:
        log.warning("无符合均线条件的股票")
        return

    log.info("符合均线条件的股票: {} 只".format(len(stock_pool)))

    # 第三步：从股票池中随机选择股票补仓
    available_slots = g.max_positions - len(current_positions) + len(g.to_sell)

    if available_slots > 0:
        # 排除已持仓和待卖出的股票
        exclude_list = list(set(current_positions) | set(g.to_sell.keys()))
        g.to_buy = select_stocks_by_distance(context, stock_pool, exclude_list, available_slots)

        log.info("选择距20日线最远的 {} 只股票买入: {}".format(len(g.to_buy), g.to_buy))

    # 更新股票池（包含待买入的股票）
    if g.to_buy:
        all_active_stocks = list(set(current_positions + g.to_buy))
        set_universe(all_active_stocks)

    log.info("【交易计划】")
    log.info(" 当前持仓: {} 只".format(len(current_positions)))
    log.info(" 计划卖出: {} 只".format(len(g.to_sell)))
    log.info(" 计划买入: {} 只".format(len(g.to_buy)))

    # 更新上次调仓日期
    g.state['last_rebalance_day'] = g.state['trading_day_count']


def calculate_position_return(stock, entry_price, current_price, highest_return_dict, stock_key):
    """计算持仓收益率并更新最高收益率

    Args:
        stock: 股票代码
        entry_price: 买入价
        current_price: 当前价
        highest_return_dict: 最高收益率字典引用
        stock_key: 字典中的key(虚拟持仓为stock本身,真实持仓为stock)

    Returns:
        (current_return, highest_return, profit_drawdown)
    """
    current_return = (current_price - entry_price) / entry_price

    # 更新最高收益率
    if current_return > highest_return_dict.get(stock_key, 0):
        highest_return_dict[stock_key] = current_return

    highest_return = highest_return_dict[stock_key]
    profit_drawdown = current_return - highest_return

    return current_return, highest_return, profit_drawdown


def collect_position_info(context, data, is_virtual=False):
    """收集持仓信息（真实或虚拟）

    Args:
        context: 回测上下文
        data: 价格数据
        is_virtual: True=虚拟持仓, False=真实持仓

    Returns:
        持仓信息列表，每个元素包含 stock, entry_price, current_return, highest_return等字段
    """
    current_positions = []

    if is_virtual:
        # 虚拟持仓
        for stock, info in g.state['virtual_positions'].items():
            if info['hold_days'] < g.rebalance_days:
                continue

            try:
                current_price = data[stock]['close']
                entry_price = info['entry_price']

                current_return, highest_return, profit_drawdown = calculate_position_return(
                    stock, entry_price, current_price,
                    g.state['virtual_positions'][stock], 'highest_return'
                )

                current_positions.append({
                    'stock': stock,
                    'entry_price': entry_price,
                    'current_return': current_return,
                    'highest_return': highest_return,
                    'profit_drawdown': profit_drawdown,
                    'hold_days': info['hold_days'],
                })
            except Exception as e:
                log.warning("虚拟持仓 {} 获取价格失败: {}".format(stock, str(e)))
                continue
    else:
        # 真实持仓
        positions = context.portfolio.positions
        for stock, position in positions.items():
            if position.amount <= 0:
                continue

            entry_price = g.state['entry_prices'].get(stock)
            if entry_price is None:
                entry_price = position.cost_basis

            hold_days = g.state['hold_days'].get(stock, 0)

            # 只淘汰持有至少5天的股票
            if hold_days < g.rebalance_days:
                continue

            current_price = data[stock]['close']
            current_return, highest_return, profit_drawdown = calculate_position_return(
                stock, entry_price, current_price,
                g.state['highest_returns'], stock
            )

            current_positions.append({
                'stock': stock,
                'entry_price': entry_price,
                'current_return': current_return,
                'highest_return': highest_return,
                'profit_drawdown': profit_drawdown,
                'hold_days': hold_days,
                'amount': position.amount,
            })

    return current_positions


def check_and_sell_losers(context, data):
    """基于综合表现淘汰最差的N只股票"""
    current_positions = collect_position_info(context, data, is_virtual=False)

    if not current_positions:
        return

    # 使用通用淘汰逻辑
    to_eliminate = calculate_stocks_to_eliminate(current_positions)

    # 执行淘汰
    for pos in to_eliminate:
        stock = pos['stock']
        g.to_sell[stock] = {
            'reason': "综合表现淘汰(收益{:.2%}, 最高{:.2%}, 回撤{:.2%}, 评分{:.4f})".format(
                pos['current_return'], pos['highest_return'],
                pos['profit_drawdown'], pos['综合评分']),
            'entry_price': pos['entry_price'],
            'amount': pos['amount'],
        }
        log.info("【计划淘汰】{} | {}".format(stock, g.to_sell[stock]['reason']))

def score_exp_with_tolerance(current_return: float,
                             profit_drawdown: float,
                             K: float = 0.2,
                             beta: float = 4.0,
                             gamma: float = 5.0) -> float:
    r = float(current_return)
    d = abs(float(profit_drawdown))
    # 当回撤超过收益时，加重指数斜率；否则保持温和
    factor = 1.0 + gamma * max(0.0, d - r)
    penalty = K * (math.exp(beta * d * factor) - 1.0)
    return r - penalty


def calculate_stocks_to_eliminate(positions_list):
    """通用的淘汰股票计算逻辑

    Args:
        positions_list: 持仓列表，每个元素包含 stock, current_return, highest_return, profit_drawdown等字段

    Returns:
        需要淘汰的股票列表
    """
    if not positions_list:
        return []

    # 计算综合评分（越低越差）
    for pos in positions_list:
        # 综合评分 = 当前收益 + 盈利回撤 * 2（对所有股票统一严格对待回撤）
        current_return = pos['current_return']
        profit_drawdown = pos['profit_drawdown'] if pos['profit_drawdown'] < 0 else 0
        #pos['综合评分'] = score_exp_with_tolerance(current_return,profit_drawdown)
        pos['综合评分'] = current_return + profit_drawdown * 4.5


    # 按综合评分排序（从差到好）
    sorted_positions = sorted(positions_list, key=lambda x: x['综合评分'])

    # 动态淘汰逻辑
    to_eliminate = []

    if g.eliminate_mode == 'fixed':
        # 固定模式：最多淘汰1只，且只淘汰得分<g.eliminate_threshold股票
        negative_positions = [pos for pos in sorted_positions if pos['综合评分'] < g.eliminate_threshold]
        if negative_positions:
            to_eliminate = [negative_positions[0]]  # 只淘汰最差的1只
            log.info("【固定淘汰】淘汰<{}分最差股票1只：{} (评分:{:.4f})".format(
                g.eliminate_threshold, to_eliminate[0]['stock'], to_eliminate[0]['综合评分']))
        else:
            log.info("【固定淘汰】无<{}分股票，不淘汰".format(g.eliminate_threshold))

    else:  # dynamic模式
        # 动态模式：最多淘汰g.eliminate_ratio只，且只淘汰得分<g.eliminate_threshold股票
        negative_positions = [pos for pos in sorted_positions if pos['综合评分'] < g.eliminate_threshold]
        max_eliminate_count = int(len(sorted_positions) * g.eliminate_ratio)
        if negative_positions and max_eliminate_count > 0:
            # 取负分股票和最大淘汰数量的较小值
            eliminate_count = min(len(negative_positions), max_eliminate_count)
            to_eliminate = negative_positions[:eliminate_count]
            log.info("【动态淘汰】淘汰<{}分最差{}只股票 (比例{:.1%}, 最大{}只): {}".format(
                g.eliminate_threshold, eliminate_count, g.eliminate_ratio, max_eliminate_count,
                [(pos['stock'], pos['综合评分']) for pos in to_eliminate]))
        else:
            log.info("【动态淘汰】无<{}分股票，不淘汰".format(g.eliminate_threshold))

    return to_eliminate


def get_ma_qualified_stocks(context, data):
    """获取股价同时在5日线和10日线上方的股票"""
    # 检查缓存
    current_date = context.blotter.current_dt.date()
    if hasattr(g, 'ma_qualified_cache_date') and g.ma_qualified_cache_date == current_date:
        log.info("使用缓存的均线筛选结果: {} 只股票".format(len(g.ma_qualified_cache)))
        return g.ma_qualified_cache

    # 优化：分批处理，避免一次性查询全市场
    # 第一步：获取所有A股（只是代码列表，不加载数据）
    all_stocks = get_Ashares()
    log.info("全市场股票: {} 只".format(len(all_stocks)))

    # 第二步：分批查询市值，避免一次性查询5392只
    selected_stocks = []
    batch_size = 1000  # 较大批次减少API调用次数

    for i in range(0, len(all_stocks), batch_size):
        batch = all_stocks[i:i+batch_size]

        try:
            fundamentals = get_fundamentals(
                batch,
                'valuation',
                ['total_value'],
                context.previous_date
            )

            if fundamentals.empty or 'total_value' not in fundamentals.columns:
                continue

            market_cap_mask = ((fundamentals['total_value'] >= g.min_market_cap) &
                               (fundamentals['total_value'] <= g.max_market_cap))

            selected_stocks.extend(fundamentals[market_cap_mask].index.tolist())

            # 内存优化：立即删除不再需要的数据
            del fundamentals

        except Exception as e:
            log.warning("批次{}市值查询失败: {}".format(i//batch_size + 1, e))
            continue

    log.info("市值筛选后: {} 只股票".format(len(selected_stocks)))

    if not selected_stocks:
        log.warning("市值筛选后无股票")
        return []

    # 第三步：状态筛选（只查询市值符合的股票，减少API调用）
    update_daily_status_cache(context, selected_stocks, force_update=True)
    filtered_stocks = filter_stock_by_status(selected_stocks)

    log.info("状态筛选后: {} 只股票".format(len(filtered_stocks)))

    # 均线筛选（批量获取价格数据）
    # 返回格式: [(stock, distance_to_ma20), ...]
    stock_distances = []
    batch_size = 500  # 较大批次减少API调用次数

    for i in range(0, len(filtered_stocks), batch_size):
        batch = filtered_stocks[i:i+batch_size]

        # 获取足够的历史数据（需要至少20天）
        # 兼容两个版本ptrade: 通用版返回dict, 国盛版返回DataFrame
        price_data = get_history(
            g.ma_long + 5, '1d',
            'close',
            batch, fq='pre', include=False
        )

        # 自动检测并转换格式为dict
        price_dict = {}
        if isinstance(price_data, dict):
            # 通用ptrade格式: {stock: {field: array}}
            price_dict = price_data
        else:
            # 国盛ptrade格式: DataFrame(行=日期, 列=股票)
            for stock in batch:
                if stock in price_data.columns:
                    price_dict[stock] = {'close': price_data[stock].values}

        # 性能优化：预处理数据，分离有效股票
        valid_stocks = []
        closes_list = []

        for stock in batch:
            if stock not in price_dict:
                continue

            closes = price_dict[stock]['close']

            # 数据不足，跳过
            if len(closes) < g.ma_long:
                continue

            valid_stocks.append(stock)
            closes_list.append(np.array(closes, dtype=float))

        if len(valid_stocks) == 0:
            # 内存优化：及时释放
            del price_data
            continue

        # 性能优化：批量计算MA（避免矩阵，使用列表推导）
        ma_short_all = np.array([np.mean(closes[-g.ma_short:]) for closes in closes_list])
        ma_middle_all = np.array([np.mean(closes[-g.ma_middle:]) for closes in closes_list])
        ma_long_all = np.array([np.mean(closes[-g.ma_long:]) for closes in closes_list])
        ma_20_all = np.array([np.mean(closes[-20:]) for closes in closes_list])
        current_prices = np.array([closes[-1] for closes in closes_list])

        # 批量筛选（向量化条件判断）
        mask = (
            (current_prices < ma_20_all) &
            (current_prices > ma_short_all) &
            (current_prices < ma_long_all) &
            (current_prices < ma_middle_all)
        )

        # 提取符合条件的股票
        qualified_indices = np.where(mask)[0]
        for idx in qualified_indices:
            stock = valid_stocks[idx]
            current_price = current_prices[idx]
            ma_20 = ma_20_all[idx]

            # 计算距离20日线的百分比(负数表示在下方)
            distance_pct = (current_price - ma_20) / ma_20
            stock_distances.append((stock, distance_pct))

        # 内存优化：每批处理完立即释放
        del price_data
        del valid_stocks
        del closes_list
        del ma_short_all
        del ma_middle_all
        del ma_long_all
        del ma_20_all
        del current_prices
        del mask

    # 按距离排序：距离越小(越负)排越前(超跌越多)
    stock_distances.sort(key=lambda x: x[1])

    # 只返回股票代码列表
    qualified_stocks = [stock for stock, _ in stock_distances]

    # 缓存结果
    g.ma_qualified_cache = qualified_stocks
    g.ma_qualified_cache_date = current_date
    log.info("均线筛选完成并缓存: {} 只股票".format(len(qualified_stocks)))

    return qualified_stocks


def update_daily_status_cache(context, stock_list=None, force_update=False):
    """更新股票状态缓存

    Args:
        context: 回测上下文
        stock_list: 需要查询的股票列表，None表示全市场
        force_update: 强制更新缓存（调仓日使用）
    """
    current_date = context.blotter.current_dt.date()

    # 如果非强制更新且缓存有效，直接返回
    if not force_update and hasattr(g, 'status_cache_date') and g.status_cache_date == current_date:
        return

    if stock_list is None:
        stock_list = get_Ashares()

    status_cache = defaultdict(dict)
    batch_size = 500
    query_types = ["ST", "HALT", "DELISTING"]

    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i+batch_size]
        for query_type in query_types:
            status_result = get_stock_status(batch, query_type=query_type)
            for stock, has_status in status_result.items():
                status_cache[stock][query_type] = has_status
            # 内存优化：及时释放
            del status_result

    g.status_cache = status_cache
    g.status_cache_date = current_date
    log.info("状态缓存已更新: {} 只股票".format(len(stock_list)))


def filter_stock_by_status(stocks):
    """过滤ST、退市、停牌股票"""
    return [stock for stock in stocks
            if not any(g.status_cache.get(stock, {}).get(status, False)
                      for status in ['ST', 'DELISTING', 'HALT'])]


# ==================== 整体止损与虚拟交易模式 ====================

def check_individual_stop_loss(context, data):
    """检查个股止损条件 - 5日内下跌超过8%立即止损"""
    current_positions = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]

    if not current_positions:
        return

    stop_loss_count = 0
    for stock in current_positions:
        # 跳过已在待卖列表中的股票
        if stock in g.to_sell:
            continue

        hold_days = g.state['hold_days'].get(stock, 0)

        # 只检查持有天数 <= 止损观察期的股票
        if hold_days > g.individual_stop_loss_days:
            continue

        entry_price = g.state['entry_prices'].get(stock)
        if entry_price is None:
            continue

        current_price = data[stock]['close']
        current_return = (current_price - entry_price) / entry_price

        # 触发个股止损
        if current_return <= g.individual_stop_loss_threshold:
            position = context.portfolio.positions[stock]
            reason = "个股止损({}日内跌{:.2%} > {:.2%})".format(
                hold_days, current_return, g.individual_stop_loss_threshold)

            g.to_sell[stock] = {
                'reason': reason,
                'entry_price': entry_price,
                'amount': position.amount,
            }

            log.info("【个股止损】{} | {}".format(stock, reason))
            stop_loss_count += 1

    if stop_loss_count > 0:
        log.info("【个股止损汇总】本次触发 {} 只股票止损".format(stop_loss_count))


def select_stocks_by_distance(context, stock_pool, exclude_stocks, count):
    """从股票池中选择距20日线最远的前N只股票

    Args:
        context: 回测上下文
        stock_pool: 候选股票池(已按距离排序,从远到近)
        exclude_stocks: 需要排除的股票列表
        count: 需要选择的数量

    Returns:
        选中的股票列表
    """
    candidates = [s for s in stock_pool if s not in exclude_stocks]
    # 直接取前N只(距离20日线最远的超跌股)
    return candidates[:min(count, len(candidates))]


def execute_virtual_rebalance(context, data, log_prefix="虚拟调仓"):
    """虚拟调仓逻辑"""
    if not g.state['virtual_positions']:
        return

    virtual_to_sell = []

    # 收集虚拟持仓信息
    current_positions = collect_position_info(context, data, is_virtual=True)

    if not current_positions:
        log.info("【{}】无符合淘汰条件的股票（持有天数<{}）".format(log_prefix, g.rebalance_days))
    else:
        # 使用通用淘汰逻辑
        to_eliminate = calculate_stocks_to_eliminate(current_positions)

        # 执行虚拟卖出
        for pos in to_eliminate:
            stock = pos['stock']
            virtual_to_sell.append(stock)
            log.info("【虚拟卖出】{} | 收益{:.2%} | 最高{:.2%} | 回撤{:.2%} | 评分{:.4f}".format(
                stock, pos['current_return'], pos['highest_return'],
                pos['profit_drawdown'], pos['综合评分']))
            del g.state['virtual_positions'][stock]

    # 获取符合均线条件的股票池并补仓
    stock_pool = get_ma_qualified_stocks(context, data)
    if not stock_pool:
        log.warning("【{}】无符合均线条件的股票，跳过补仓".format(log_prefix))
        return

    log.info("【{}】符合均线条件: {} 只".format(log_prefix, len(stock_pool)))

    available_slots = g.max_positions - len(g.state['virtual_positions'])
    if available_slots > 0:
        virtual_to_buy = select_stocks_by_distance(
            context, stock_pool,
            list(g.state['virtual_positions'].keys()),
            available_slots
        )

        for stock in virtual_to_buy:
            g.state['virtual_positions'][stock] = {
                'entry_price': data[stock]['close'],
                'hold_days': 0,
                'highest_return': 0.0
            }
            log.info("【虚拟买入】{} | 买入价: {:.2f}".format(stock, data[stock]['close']))

        log.info("【{}完成】卖出{}只 | 买入{}只 | 当前持仓{}只".format(
            log_prefix, len(virtual_to_sell), len(virtual_to_buy), len(g.state['virtual_positions'])))
    else:
        log.info("【{}】已满仓，无需补仓".format(log_prefix))


def calculate_virtual_returns(data, update_highest=True):
    """计算虚拟持仓收益率列表（优化：批量获取价格）

    Args:
        data: 价格数据
        update_highest: 是否更新最高收益率

    Returns:
        收益率列表
    """
    if not g.state['virtual_positions']:
        return []

    # 性能优化：批量获取所有持仓的当前价格
    stocks = list(g.state['virtual_positions'].keys())
    current_prices = {}
    for stock in stocks:
        try:
            current_prices[stock] = data[stock]['close']
        except Exception:
            continue

    returns = []
    for stock, info in g.state['virtual_positions'].items():
        if stock not in current_prices:
            continue

        try:
            current_price = current_prices[stock]
            entry_price = info['entry_price']
            current_return = (current_price - entry_price) / entry_price

            if update_highest:
                # 更新最高收益率
                if current_return > info.get('highest_return', 0):
                    g.state['virtual_positions'][stock]['highest_return'] = current_return

            returns.append(current_return)
        except Exception:
            continue

    return returns


def display_virtual_positions(context, data):
    """显示虚拟持仓收益"""
    if not g.state['virtual_positions']:
        return

    log.info("【虚拟持仓明细】")
    for stock, info in g.state['virtual_positions'].items():
        try:
            current_price = data[stock]['close']
            entry_price = info['entry_price']

            current_return, highest_return, _ = calculate_position_return(
                stock, entry_price, current_price,
                g.state['virtual_positions'][stock], 'highest_return'
            )

            log.info(" {} - 收益:{:>7.2%} | 最高:{:>7.2%} | 持有{}天".format(
                stock, current_return, highest_return, info['hold_days']))
        except Exception as e:
            log.warning(" {} - 获取价格失败: {}".format(stock, str(e)))


def calculate_percentile_avg_return(returns, percentile):
    """计算指定分位数的平均收益率

    Args:
        returns: 收益率列表
        percentile: 分位数 (0-1之间)

    Returns:
        平均收益率
    """
    if not returns:
        return 0.0

    sorted_returns = sorted(returns)
    percentile_idx = int(len(sorted_returns) * percentile)
    worst_pct_returns = sorted_returns[:max(1, percentile_idx)]
    return np.mean(worst_pct_returns)


def check_virtual_recovery(context, data):
    """检查虚拟持仓表现，决定是否恢复实际交易（统一处理首日观察和整体止损）"""
    if not g.state['virtual_positions']:
        return

    # 至少观察5天再判断
    min_hold_days = min(info['hold_days'] for info in g.state['virtual_positions'].values())
    if min_hold_days < g.rebalance_days:
        log.info("【虚拟持仓检查】最短持有{}天 < {}天，继续观察".format(min_hold_days, g.rebalance_days))
        return

    # 计算虚拟持仓收益率
    virtual_returns = calculate_virtual_returns(data, update_highest=True)

    if not virtual_returns:
        return

    # 计算平均收益和80%分位跌幅
    avg_return = np.mean(virtual_returns)
    positive_count = sum(1 for r in virtual_returns if r > 0)
    positive_ratio = positive_count / len(virtual_returns)
    avg_loss_80pct = calculate_percentile_avg_return(virtual_returns, g.portfolio_loss_percentile)

    log.info("【虚拟持仓检查】持仓数: {} | 平均收益: {:.2%} | 盈利比例: {:.1%} | 80%分位: {:.2%}".format(
        len(virtual_returns), avg_return, positive_ratio, avg_loss_80pct))

    # 超过5天且表现不佳：清空重新观察
    if min_hold_days >= g.rebalance_days and avg_loss_80pct < g.portfolio_stop_loss_threshold:
        log.info("【重置虚拟持仓】5天观察期结束，80%分位{:.2%} < {:.2%}，清空重新选股".format(
            avg_loss_80pct, g.portfolio_stop_loss_threshold))
        g.state['virtual_positions'] = {}
        return

    # 达标条件：80%分位跌幅 >= -5% (即表现尚可)
    if avg_loss_80pct >= g.portfolio_stop_loss_threshold:
        # 根据当前状态决定日志内容
        if g.state['initial_observation_mode']:
            log.info("【虚拟持仓达标】开始实际交易")
        else:
            log.info("【恢复交易】虚拟持仓表现改善，恢复实际交易")

        log.info("  平均收益: {:.2%} | 盈利比例: {:.1%} | 80%分位: {:.2%}".format(
            avg_return, positive_ratio, avg_loss_80pct))

        # 恢复交易状态
        g.state['initial_observation_mode'] = False
        g.state['is_trading_paused'] = False
        g.state['virtual_positions'] = {}

        # 重置调仓计数器让第二天立即可以调仓
        g.state['last_rebalance_day'] = g.state['trading_day_count'] - g.rebalance_days


def check_virtual_portfolio_stop_loss(context, data):
    """检查虚拟持仓整体止损条件 - 用于打印虚拟观察期间的状态"""
    if not g.state['virtual_positions']:
        return

    # 计算所有虚拟持仓的收益率
    returns = calculate_virtual_returns(data, update_highest=False)

    if not returns:
        return

    # 计算80%分位数（最差的80%持仓的平均收益）
    avg_loss = calculate_percentile_avg_return(returns, g.portfolio_loss_percentile)

    log.info("【虚拟止损检查】持仓数: {} | 80%分位平均涨幅: {:.2%} | 阈值: {:.2%}".format(
        len(g.state['virtual_positions']), avg_loss, g.portfolio_stop_loss_threshold))


def check_portfolio_stop_loss(context, data):
    """检查整体持仓止损条件 - 80%持仓当日平均下跌>N%"""
    current_positions = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]

    if not current_positions:
        return

    # 计算所有持仓的当日收益率
    daily_returns = []
    for stock in current_positions:
        prev_close = g.state.get('prev_close_prices', {}).get(stock)
        if prev_close is None or prev_close <= 0:
            continue

        current_price = data[stock]['close']
        daily_return = (current_price - prev_close) / prev_close
        daily_returns.append(daily_return)

    if not daily_returns:
        return

    # 计算80%分位数（最差的80%持仓的平均当日收益）
    avg_daily_loss = calculate_percentile_avg_return(daily_returns, g.portfolio_loss_percentile)

    log.info("【整体止损检查】持仓数: {} | 80%分位当日平均涨幅: {:.2%} | 阈值: {:.2%}".format(
        len(current_positions), avg_daily_loss, g.portfolio_stop_loss_threshold))

    # 如果已经暂停，不再重复触发
    if g.state['is_trading_paused']:
        return

    # 触发整体止损：当日平均跌幅超过阈值
    if avg_daily_loss < g.portfolio_stop_loss_threshold:
        log.info("【触发整体止损】80%持仓当日平均下跌 {:.2%} < {:.2%}".format(
            avg_daily_loss, g.portfolio_stop_loss_threshold))
        log.info("【暂停实际交易】进入虚拟观察模式（清空虚拟持仓，等待重新选股）")

        # 进入暂停状态
        g.state['is_trading_paused'] = True

        # 清空虚拟持仓（不继承当前亏损持仓，等待虚拟模式重新选股）
        g.state['virtual_positions'] = {}
        log.info("【虚拟持仓】已清空，将在虚拟模式下重新选股")

        # 标记所有实际持仓待清仓（通过handle_data统一执行）
        for stock in current_positions:
            position = context.portfolio.positions[stock]
            entry_price = g.state['entry_prices'].get(stock, position.cost_basis)
            g.to_sell[stock] = {
                'reason': '整体止损清仓',
                'entry_price': entry_price,
                'amount': position.amount,
            }
        log.info("【整体止损】标记 {} 只股票待清仓".format(len(current_positions)))


def handle_virtual_trading_mode(context, data):
    """虚拟交易观察模式 - 不实际下单，只观察虚拟持仓表现"""
    if not g.state['virtual_positions']:
        # 虚拟持仓为空，初始化虚拟选股
        log.info("【虚拟观察】初始化虚拟持仓")
        stock_pool = get_ma_qualified_stocks(context, data)
        if stock_pool:
            virtual_stocks = select_stocks_by_distance(context, stock_pool, [], g.max_positions)

            for stock in virtual_stocks:
                g.state['virtual_positions'][stock] = {
                    'entry_price': data[stock]['close'],
                    'hold_days': 0,
                    'highest_return': 0.0
                }
            log.info("【虚拟买入】{} 只股票: {}".format(len(virtual_stocks), virtual_stocks))
        return  # 初始化当天直接返回，不显示也不检查

    # 显示虚拟持仓明细
    display_virtual_positions(context, data)

    # 虚拟观察期间不调仓,只检查是否达到恢复条件
    check_virtual_recovery(context, data)


def handle_data(context, data):
    """交易逻辑实现"""
    # 处理卖出（暂停交易时也要执行，确保止损清仓生效）
    sell_stocks(context)

    # 暂停交易时跳过买入
    if g.state['is_trading_paused']:
        finalize_sells(context, data)  # 确认卖出
        return

    # 处理买入
    buy_stocks(context)

    # 确认订单状态
    cancel_stale_orders(context)
    finalize_sells(context, data)
    finalize_buys(context)


def sell_stocks(context):
    """卖出逻辑"""
    for stock in list(g.to_sell.keys()):
        if stock in context.portfolio.positions and context.portfolio.positions[stock].amount > 0:
            order_target(stock, 0)


def buy_stocks(context):
    """买入逻辑 - 等权重分配资金"""
    if not g.to_buy:
        return

    current_positions = sum(1 for p in context.portfolio.positions.values() if p.amount > 0)

    if current_positions >= g.max_positions:
        return

    # 等权重分配
    equal_weight = 1.0 / g.max_positions
    total_value = context.portfolio.portfolio_value

    for stock in g.to_buy:
        allocation = total_value * equal_weight
        order_value(stock, allocation)


def finalize_buys(context):
    """确认买入成功后更新状态"""
    if not g.to_buy:
        return

    bought_stocks = []
    for stock in g.to_buy:
        position = context.portfolio.positions.get(stock)
        if position and position.amount > 0:
            g.state['hold_days'][stock] = 0
            g.state['entry_prices'][stock] = position.cost_basis
            g.state['highest_returns'][stock] = 0.0  # 初始化最高收益率

            log.info("【买入成功】{} | 成交价: {:.2f} | 数量: {}".format(
                stock, position.cost_basis, position.amount))

            bought_stocks.append(stock)

    # 清空买入列表
    g.to_buy = []


def finalize_sells(context, data):
    """确认卖出成功后清理状态"""
    if not g.to_sell:
        return

    for stock in list(g.to_sell.keys()):
        position = context.portfolio.positions.get(stock)
        sell_info = g.to_sell[stock]
        sell_reason = sell_info['reason']
        entry_price = sell_info['entry_price']

        if position is None or position.amount == 0:
            # 获取卖出价格
            if position is None:
                sell_price = data[stock]['close']
            else:
                sell_price = position.last_sale_price

            # 计算收益
            actual_return = (sell_price - entry_price) / entry_price

            log.info("【卖出成交】{} | 买入价: {:.2f} | 卖出价: {:.2f} | 实际收益: {:.2%} | 原因: {}".format(
                stock, entry_price, sell_price, actual_return, sell_reason))

            cleanup_stock_records(stock)
            g.to_sell.pop(stock)


def cancel_stale_orders(context):
    """取消超时未成交订单"""
    now = datetime.now()

    for order in get_open_orders():
        if (now - order.created).seconds > 60:
            cancel_order(order)


def cleanup_stock_records(stock):
    """清理股票记录"""
    if stock in g.state['hold_days']:
        del g.state['hold_days'][stock]
    if stock in g.state['entry_prices']:
        del g.state['entry_prices'][stock]
    if stock in g.state['highest_returns']:
        del g.state['highest_returns'][stock]
    if stock in g.state['total_profit']:
        del g.state['total_profit'][stock]


def update_hold_days(context):
    """更新持仓天数（真实持仓 + 虚拟持仓）"""
    # 更新真实持仓天数
    positions = context.portfolio.positions
    for stock in list(g.state['hold_days'].keys()):
        if stock in positions and positions[stock].amount > 0:
            g.state['hold_days'][stock] += 1
        else:
            log.info("【持仓消失】{} 持有{}天后已不在持仓中".format(
                stock, g.state['hold_days'][stock]))
            g.state['hold_days'].pop(stock, None)

    # 更新虚拟持仓天数
    for stock in g.state['virtual_positions']:
        g.state['virtual_positions'][stock]['hold_days'] += 1


def after_trading_end(context, data):
    """盘后处理"""
    portfolio_value = context.portfolio.portfolio_value
    positions_count = sum(1 for p in context.portfolio.positions.values() if p.amount > 0)

    # 显示交易状态
    if g.state['initial_observation_mode']:
        trading_status = "首日虚拟观察"
    elif g.state['is_trading_paused']:
        trading_status = "暂停交易观察"
    else:
        trading_status = "正常交易"

    log.info("【日终】总资产: {:.2f} | 持仓: {} 只 | 状态: {}".format(
        portfolio_value, positions_count, trading_status))

    # 首日观察模式下，虚拟持仓更新已在before_trading_start中完成，这里只需显示状态
    if g.state['initial_observation_mode'] and g.state['virtual_positions']:
        log.info("【虚拟持仓状态】{} 只股票".format(len(g.state['virtual_positions'])))

    # 如果处于暂停交易观察模式，显示虚拟持仓
    if g.state['is_trading_paused'] and g.state['virtual_positions']:
        log.info("【虚拟持仓】{} 只股票".format(len(g.state['virtual_positions'])))

    # 正常交易模式下，显示实际持仓明细
    if trading_status == "正常交易" and positions_count > 0:
        log.info("【实际持仓明细】")
        current_positions = [(stock, pos) for stock, pos in context.portfolio.positions.items() if pos.amount > 0]

        total_daily_return = 0
        daily_return_count = 0

        for stock, position in current_positions:
            entry_price = g.state['entry_prices'].get(stock, position.cost_basis)
            current_price = data[stock]['close']
            current_return = (current_price - entry_price) / entry_price
            hold_days = g.state['hold_days'].get(stock, 0)

            # 只显示持有天数>0的持仓（跳过买入当天）
            if hold_days == 0:
                continue

            # 更新并获取最高收益率
            if current_return > g.state['highest_returns'].get(stock, 0):
                g.state['highest_returns'][stock] = current_return
            highest_return = g.state['highest_returns'][stock]

            # 计算当日涨跌（相对于前一日收盘价）
            prev_close = g.state.get('prev_close_prices', {}).get(stock)
            if prev_close and prev_close > 0:
                daily_return = (current_price - prev_close) / prev_close
                total_daily_return += daily_return
                daily_return_count += 1
                log.info(" {} - 累计:{:>7.2%} | 最高:{:>7.2%} | 今日:{:>6.2%} | 持有{}天".format(
                    stock, current_return, highest_return, daily_return, hold_days))
            else:
                log.info(" {} - 累计:{:>7.2%} | 最高:{:>7.2%} | 持有{}天".format(
                    stock, current_return, highest_return, hold_days))

        # 显示平均当日涨跌
        if daily_return_count > 0:
            avg_daily_return = total_daily_return / daily_return_count
            log.info("【平均今日涨跌】 {:.2%}".format(avg_daily_return))

    # 更新持有天数
    update_hold_days(context)

    # 保存当日收盘价（用于明天计算当日涨跌）
    if 'prev_close_prices' not in g.state:
        g.state['prev_close_prices'] = {}

    current_positions = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]
    for stock in current_positions:
        try:
            g.state['prev_close_prices'][stock] = data[stock]['close']
        except:
            pass

    g.to_buy = []
    g.to_sell = {}

    save_strategy_state(context)


# ==================== 状态持久化函数 ====================

def load_strategy_state(context):
    """加载策略状态"""
    if hasattr(g, 'strategy_state_path') and Path(g.strategy_state_path).exists():
        with open(g.strategy_state_path, 'rb') as f:
            loaded_state = pickle.load(f)
            g.state['hold_days'] = loaded_state.get('hold_days', defaultdict(int))
            g.state['entry_prices'] = loaded_state.get('entry_prices', defaultdict(float))
            g.state['highest_returns'] = loaded_state.get('highest_returns', defaultdict(float))
            g.state['total_profit'] = loaded_state.get('total_profit', defaultdict(float))
            g.state['last_rebalance_day'] = loaded_state.get('last_rebalance_day', 0)
            g.state['trading_day_count'] = loaded_state.get('trading_day_count', 0)
            g.state['is_trading_paused'] = loaded_state.get('is_trading_paused', False)
            g.state['virtual_positions'] = loaded_state.get('virtual_positions', {})
            g.state['initial_observation_mode'] = loaded_state.get('initial_observation_mode', True)

            if 'to_sell' in loaded_state and loaded_state['to_sell']:
                g.to_sell = loaded_state['to_sell']
            if 'to_buy' in loaded_state and loaded_state['to_buy']:
                g.to_buy = loaded_state['to_buy']
    else:
        if 'entry_prices' not in g.state:
            g.state['entry_prices'] = defaultdict(float)
        if 'hold_days' not in g.state:
            g.state['hold_days'] = defaultdict(int)
        if 'highest_returns' not in g.state:
            g.state['highest_returns'] = defaultdict(float)
        if 'total_profit' not in g.state:
            g.state['total_profit'] = defaultdict(float)
        if 'is_trading_paused' not in g.state:
            g.state['is_trading_paused'] = False
        if 'virtual_positions' not in g.state:
            g.state['virtual_positions'] = {}
        if 'initial_observation_mode' not in g.state:
            g.state['initial_observation_mode'] = True


def save_strategy_state(context):
    """保存策略状态"""
    state_to_save = {
        'hold_days': dict(g.state['hold_days']),
        'entry_prices': dict(g.state['entry_prices']),
        'highest_returns': dict(g.state['highest_returns']),
        'total_profit': dict(g.state['total_profit']),
        'last_rebalance_day': g.state['last_rebalance_day'],
        'trading_day_count': g.state['trading_day_count'],
        'is_trading_paused': g.state['is_trading_paused'],
        'virtual_positions': g.state['virtual_positions'],
        'initial_observation_mode': g.state['initial_observation_mode'],
        'to_sell': g.to_sell if hasattr(g, 'to_sell') else {},
        'to_buy': g.to_buy if hasattr(g, 'to_buy') else [],
    }
    with open(g.strategy_state_path, 'wb') as f:
        pickle.dump(state_to_save, f, pickle.HIGHEST_PROTOCOL)


def clear_file(file_path):
    """删除指定路径的文件"""
    path = Path(file_path)
    if path.exists():
        path.unlink()
