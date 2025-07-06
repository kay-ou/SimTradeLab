# -*- coding: utf-8 -*-
"""
辅助工具函数模块
"""
from pathlib import Path
from .logger import log
from .trading import order
from .context import Position
import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime, timedelta

def is_trade(engine):
    """模拟is_trade函数，回测模式下返回False"""
    return False

def get_research_path(engine):
    """模拟get_research_path函数"""
    return './'

def set_commission(engine, commission_ratio=0.0003, min_commission=5.0, type="STOCK"):
    """
    设置交易手续费

    Args:
        engine: 回测引擎实例
        commission_ratio: 佣金费率，默认0.0003 (0.03%)
        min_commission: 最低佣金，默认5.0元
        type: 交易类型，默认"STOCK"
    """
    engine.commission_ratio = commission_ratio
    engine.min_commission = min_commission
    log.info(f"设置手续费 - 费率: {commission_ratio:.4f}, 最低佣金: {min_commission}元, 类型: {type}")

def set_limit_mode(engine, mode):
    """模拟set_limit_mode函数，设置限价模式"""
    engine.limit_mode = bool(mode)
    log.info(f"设置限价模式: {'开启' if engine.limit_mode else '关闭'}")

def set_fixed_slippage(engine, slippage):
    """
    设置固定滑点
    
    Args:
        engine: 回测引擎实例
        slippage: 固定滑点值（绝对值）
    """
    engine.fixed_slippage = float(slippage)
    log.info(f"设置固定滑点: {slippage}")

def set_slippage(engine, slippage):
    """
    设置滑点比例
    
    Args:
        engine: 回测引擎实例
        slippage: 滑点比例，如0.001表示0.1%
    """
    engine.slippage = float(slippage)
    log.info(f"设置滑点比例: {slippage:.4f}")

def set_volume_ratio(engine, ratio):
    """
    设置成交量比例
    
    Args:
        engine: 回测引擎实例
        ratio: 成交量比例，如0.1表示最多成交当日成交量的10%
    """
    engine.volume_ratio = float(ratio)
    log.info(f"设置成交量比例: {ratio:.4f}")

def set_yesterday_position(engine, positions):
    """
    设置初始持仓
    
    Args:
        engine: 回测引擎实例
        positions: 持仓字典，格式为 {股票代码: 持仓数量}
    """
    if not hasattr(engine, 'context') or not engine.context:
        log.warning("上下文未初始化，无法设置初始持仓")
        return
    
    for security, amount in positions.items():
        if amount > 0:
            # 假设初始成本价为100元（实际应该从历史数据获取）
            cost_basis = 100.0
            engine.context.portfolio.positions[security] = Position(
                security=security,
                amount=amount,
                cost_basis=cost_basis
            )
            log.info(f"设置初始持仓: {security} {amount}股")

def set_parameters(engine, **kwargs):
    """
    设置策略参数
    
    Args:
        engine: 回测引擎实例
        **kwargs: 参数字典
    """
    if not hasattr(engine, 'strategy_params'):
        engine.strategy_params = {}
    
    engine.strategy_params.update(kwargs)
    log.info(f"设置策略参数: {kwargs}")

def run_daily(engine, context, func, time='09:30'):
    """
    按日周期处理

    Args:
        engine: 回测引擎实例
        context: 上下文对象
        func: 要执行的函数
        time: 执行时间，格式为'HH:MM'，默认'09:30'

    Returns:
        None
    """
    # 在模拟环境中，我们简单记录这个调用
    # 实际的定时执行在真实环境中由框架处理
    log.info(f"注册每日定时任务: 每天{time}执行函数 {func.__name__ if hasattr(func, '__name__') else str(func)}")
    # 可以将定时任务信息存储到引擎中，供后续使用
    if not hasattr(engine, 'daily_tasks'):
        engine.daily_tasks = []
    engine.daily_tasks.append({
        'func': func,
        'time': time,
        'context': context
    })


def run_interval(engine, context, func, seconds):
    """模拟run_interval函数，定时执行函数"""
    # 在模拟环境中，我们简单记录这个调用
    # 实际的定时执行在真实环境中由框架处理
    log.info(f"注册定时任务: 每{seconds}秒执行函数 {func.__name__ if hasattr(func, '__name__') else str(func)}")
    # 可以将定时任务信息存储到引擎中，供后续使用
    if not hasattr(engine, 'interval_tasks'):
        engine.interval_tasks = []
    engine.interval_tasks.append({
        'func': func,
        'seconds': seconds,
        'context': context
    })

def clear_file(engine, file_path):
    """模拟clear_file函数, 会确保目录存在并删除文件"""
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()

def get_initial_cash(engine, context, max_cash):
    """模拟get_initial_cash函数"""
    return min(context.portfolio.starting_cash, max_cash)

def get_num_of_positions(engine, context):
    """模拟get_num_of_positions函数"""
    return sum(1 for pos in context.portfolio.positions.values() if pos.amount > 0)

def get_Ashares(engine, date=None):
    """模拟get_Ashares函数，返回数据文件中所有可用的股票"""
    return list(engine.data.keys())

def get_stock_status(engine, stocks, query_type='ST', query_date=None):
    """模拟get_stock_status函数，假设所有股票状态正常"""
    if isinstance(stocks, str):
        stocks = [stocks]
    return {s: False for s in stocks}

def get_stock_info(engine, stocks, field=None):
    """模拟get_stock_info函数"""
    if isinstance(stocks, str):
        stocks = [stocks]
    
    all_fields = {
        'stock_name': '默认名称',
        'listed_date': '2020-01-01',
        'de_listed_date': '2900-01-01'
    }
    
    if field is None:
        field = ['stock_name']
    
    if isinstance(field, str):
        field = [field]

    result = {}
    for s in stocks:
        result[s] = {f: all_fields.get(f, 'N/A') for f in field}
    return result

def get_stock_name(engine, stocks):
    """模拟get_stock_name函数"""
    info = get_stock_info(engine, stocks, field='stock_name')
    return {k: v['stock_name'] for k, v in info.items()}

def set_universe(engine, stocks):
    """模拟set_universe函数，设置股票池"""
    if isinstance(stocks, str):
        stocks = [stocks]
    log.info(f"设置股票池: {stocks}")


def set_benchmark(engine, benchmark):
    """
    设置基准指数

    Args:
        engine: 回测引擎实例
        benchmark: 基准指数代码，如 '000001.SH' (上证指数)
    """
    engine.benchmark = benchmark
    log.info(f"设置基准指数: {benchmark}")

    # 如果基准数据在数据文件中，则使用真实数据
    # 否则生成模拟基准数据
    if benchmark not in engine.data:
        log.warning(f"基准指数 {benchmark} 不在数据文件中，将生成模拟基准数据")
        _generate_benchmark_data(engine, benchmark)


def _generate_benchmark_data(engine, benchmark):
    """生成模拟基准数据"""

    # 检查是否有数据
    if not engine.data:
        log.warning("没有股票数据，无法生成基准数据")
        return

    # 获取第一个股票的时间序列作为基准
    first_security = list(engine.data.keys())[0]
    time_index = engine.data[first_security].index

    # 生成模拟基准数据（年化收益率约8%，波动率约20%）
    np.random.seed(42)  # 固定随机种子，确保结果可重复
    daily_returns = np.random.normal(0.08/252, 0.20/np.sqrt(252), len(time_index))

    # 从100开始，计算累积价格
    prices = [100.0]
    for ret in daily_returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    # 创建基准数据DataFrame
    benchmark_data = pd.DataFrame({
        'open': prices,
        'high': [p * 1.01 for p in prices],  # 高点比收盘价高1%
        'low': [p * 0.99 for p in prices],   # 低点比收盘价低1%
        'close': prices,
        'volume': [1000000] * len(prices)    # 固定成交量
    }, index=time_index)

    engine.data[benchmark] = benchmark_data
    log.info(f"已生成基准指数 {benchmark} 的模拟数据")


def get_benchmark_returns(engine, start_date=None, end_date=None):
    """
    获取基准收益率序列

    Args:
        engine: 回测引擎实例
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        pandas.Series: 基准收益率序列
    """
    if not hasattr(engine, 'benchmark') or not engine.benchmark:
        log.warning("未设置基准指数")
        return None

    benchmark = engine.benchmark
    if benchmark not in engine.data:
        log.warning(f"基准指数 {benchmark} 数据不存在")
        return None

    benchmark_data = engine.data[benchmark]

    # 筛选日期范围
    if start_date:
        benchmark_data = benchmark_data[benchmark_data.index >= start_date]
    if end_date:
        benchmark_data = benchmark_data[benchmark_data.index <= end_date]

    # 计算收益率
    returns = benchmark_data['close'].pct_change().dropna()
    return returns


# ==================== 交易日历功能 ====================

def get_trading_day(engine, date=None, offset=0):
    """
    获取交易日期

    Args:
        engine: 回测引擎实例
        date: 基准日期，None表示当前日期
        offset: 偏移量，0表示当天，1表示下一个交易日，-1表示上一个交易日

    Returns:
        pandas.Timestamp: 交易日期，如果不是交易日则返回None
    """

    # 获取所有交易日
    all_trading_days = get_all_trades_days(engine)

    if all_trading_days.empty:
        log.warning("没有可用的交易日数据")
        return None

    # 确定基准日期
    if date is None:
        if hasattr(engine, 'context') and engine.context.current_dt:
            base_date = engine.context.current_dt
        else:
            base_date = all_trading_days[0]  # 使用第一个交易日作为默认
    else:
        base_date = pd.to_datetime(date)

    # 找到最接近的交易日
    base_date_only = base_date.date() if hasattr(base_date, 'date') else base_date
    trading_days_dates = [d.date() for d in all_trading_days]

    try:
        # 找到基准日期在交易日列表中的位置
        if base_date_only in trading_days_dates:
            current_index = trading_days_dates.index(base_date_only)
        else:
            # 如果基准日期不是交易日，找到最近的交易日
            for i, trading_date in enumerate(trading_days_dates):
                if trading_date >= base_date_only:
                    current_index = i
                    break
            else:
                current_index = len(trading_days_dates) - 1  # 使用最后一个交易日

        # 应用偏移量
        target_index = current_index + offset

        # 检查索引是否有效
        if 0 <= target_index < len(all_trading_days):
            return all_trading_days[target_index]
        else:
            log.warning(f"偏移量 {offset} 超出交易日范围")
            return None

    except Exception as e:
        log.warning(f"获取交易日期失败: {e}")
        return None


def get_all_trades_days(engine):
    """
    获取全部交易日期

    Args:
        engine: 回测引擎实例

    Returns:
        pandas.DatetimeIndex: 所有交易日期的索引
    """
    if not engine.data:
        log.warning("没有可用的数据")
        return pd.DatetimeIndex([])

    # 获取第一个股票的时间索引作为交易日历
    first_security = list(engine.data.keys())[0]
    trading_days = engine.data[first_security].index

    # 确保是日期时间索引并排序
    trading_days = pd.to_datetime(trading_days).sort_values()

    return trading_days


def get_trade_days(engine, start_date=None, end_date=None, count=None):
    """
    获取指定范围的交易日期

    Args:
        engine: 回测引擎实例
        start_date: 开始日期
        end_date: 结束日期
        count: 返回的交易日数量（从start_date开始）

    Returns:
        pandas.DatetimeIndex: 指定范围内的交易日期
    """
    # 获取所有交易日
    all_trading_days = get_all_trades_days(engine)

    if all_trading_days.empty:
        return pd.DatetimeIndex([])

    # 应用日期筛选
    filtered_days = all_trading_days

    if start_date:
        start_date = pd.to_datetime(start_date)
        filtered_days = filtered_days[filtered_days >= start_date]

    if end_date:
        end_date = pd.to_datetime(end_date)
        filtered_days = filtered_days[filtered_days <= end_date]

    # 如果指定了数量，则限制返回的交易日数量
    if count is not None and count > 0:
        filtered_days = filtered_days[:count]

    return filtered_days


# ==================== ETF相关API ====================

def get_etf_info(engine, etf_code):
    """
    获取ETF基本信息
    
    Args:
        engine: 回测引擎实例
        etf_code: ETF代码
        
    Returns:
        dict: ETF基本信息
    """
    # 模拟ETF信息
    etf_info = {
        'etf_code': etf_code,
        'etf_name': f'ETF{etf_code}',
        'tracking_index': '沪深300',
        'management_fee': 0.005,
        'custodian_fee': 0.001,
        'creation_unit': 1000000,
        'status': 'normal'
    }
    
    log.info(f"获取ETF信息: {etf_code}")
    return etf_info


def get_etf_stock_info(engine, etf_code):
    """
    获取ETF成分券信息
    
    Args:
        engine: 回测引擎实例
        etf_code: ETF代码
        
    Returns:
        dict: ETF成分券详细信息
    """
    # 模拟ETF成分券信息
    if engine.data:
        stocks = list(engine.data.keys())[:10]  # 取前10只股票作为成分券
        stock_info = {}
        for i, stock in enumerate(stocks):
            stock_info[stock] = {
                'weight': 0.1,  # 权重10%
                'shares': 1000 * (i + 1),  # 份额
                'market_value': 100000 * (i + 1)  # 市值
            }
    else:
        stock_info = {}
    
    log.info(f"获取ETF成分券信息: {etf_code}")
    return stock_info


def get_etf_stock_list(engine, etf_code):
    """
    获取ETF成分券列表
    
    Args:
        engine: 回测引擎实例
        etf_code: ETF代码
        
    Returns:
        list: ETF成分券代码列表
    """
    stock_info = get_etf_stock_info(engine, etf_code)
    return list(stock_info.keys())


def get_etf_list(engine):
    """
    获取ETF代码列表
    
    Args:
        engine: 回测引擎实例
        
    Returns:
        list: ETF代码列表
    """
    # 模拟ETF列表
    etf_list = ['510300.SH', '159919.SZ', '512880.SH', '159995.SZ']
    log.info(f"获取ETF列表: {len(etf_list)}只")
    return etf_list


def etf_purchase_redemption(engine, etf_code, operation, amount):
    """
    ETF申购赎回
    
    Args:
        engine: 回测引擎实例
        etf_code: ETF代码
        operation: 操作类型 'purchase'(申购) 或 'redemption'(赎回)
        amount: 申购/赎回数量
        
    Returns:
        str: 操作结果订单ID
    """
    order_id = str(uuid.uuid4())
    log.info(f"ETF{operation}: {etf_code} {amount}份 订单ID: {order_id}")
    
    return order_id


# ==================== 债券相关API ====================

def debt_to_stock_order(engine, bond_code, amount):
    """
    债转股委托
    
    Args:
        engine: 回测引擎实例
        bond_code: 可转债代码
        amount: 转股数量
        
    Returns:
        str: 订单ID
    """
    order_id = str(uuid.uuid4())
    log.info(f"债转股委托: {bond_code} {amount}张 订单ID: {order_id}")
    
    return order_id


def get_cb_list(engine):
    """
    获取可转债市场代码表
    
    Args:
        engine: 回测引擎实例
        
    Returns:
        list: 可转债代码列表
    """
    # 模拟可转债列表
    cb_list = ['113008.SH', '128035.SZ', '110059.SH', '127011.SZ']
    log.info(f"获取可转债列表: {len(cb_list)}只")
    return cb_list


def get_cb_info(engine, cb_code):
    """
    获取可转债基础信息
    
    Args:
        engine: 回测引擎实例
        cb_code: 可转债代码
        
    Returns:
        dict: 可转债基础信息
    """
    cb_info = {
        'cb_code': cb_code,
        'cb_name': f'转债{cb_code}',
        'stock_code': cb_code.replace('1', '0'),  # 简单模拟对应股票
        'conversion_ratio': 10.0,  # 转股比例
        'conversion_price': 10.0,  # 转股价格
        'maturity_date': '2030-12-31',  # 到期日
        'coupon_rate': 0.02  # 票面利率
    }
    
    log.info(f"获取可转债信息: {cb_code}")
    return cb_info


# ==================== 期货相关API ====================

def buy_open(engine, contract, amount):
    """
    期货多开
    
    Args:
        engine: 回测引擎实例
        contract: 合约代码
        amount: 开仓数量
        
    Returns:
        str: 订单ID
    """
    
    
    # 在期货交易中，这相当于买入开仓
    order_id = order(engine, contract, amount)
    log.info(f"期货多开: {contract} {amount}手")
    
    return order_id


def sell_close(engine, contract, amount):
    """
    期货多平
    
    Args:
        engine: 回测引擎实例
        contract: 合约代码
        amount: 平仓数量
        
    Returns:
        str: 订单ID
    """
    # 在期货交易中，这相当于卖出平仓
    order_id = order(engine, contract, -amount)
    log.info(f"期货多平: {contract} {amount}手")
    
    return order_id


def sell_open(engine, contract, amount):
    """
    期货空开
    
    Args:
        engine: 回测引擎实例
        contract: 合约代码
        amount: 开仓数量
        
    Returns:
        str: 订单ID
    """
    # 在期货交易中，这相当于卖出开仓
    order_id = order(engine, contract, -amount)
    log.info(f"期货空开: {contract} {amount}手")
    
    return order_id


def buy_close(engine, contract, amount):
    """
    期货空平
    
    Args:
        engine: 回测引擎实例
        contract: 合约代码
        amount: 平仓数量
        
    Returns:
        str: 订单ID
    """
    # 在期货交易中，这相当于买入平仓
    order_id = order(engine, contract, amount)
    log.info(f"期货空平: {contract} {amount}手")
    
    return order_id


def set_future_commission(engine, commission_ratio=0.0003, min_commission=5.0):
    """
    设置期货手续费
    
    Args:
        engine: 回测引擎实例
        commission_ratio: 手续费比例
        min_commission: 最低手续费
    """
    engine.future_commission_ratio = commission_ratio
    engine.future_min_commission = min_commission
    log.info(f"设置期货手续费 - 费率: {commission_ratio:.4f}, 最低: {min_commission}元")


def set_margin_rate(engine, margin_rate):
    """
    设置期货保证金比例
    
    Args:
        engine: 回测引擎实例
        margin_rate: 保证金比例
    """
    engine.margin_rate = margin_rate
    log.info(f"设置期货保证金比例: {margin_rate:.4f}")


def get_margin_rate(engine):
    """
    获取用户设置的保证金比例
    
    Args:
        engine: 回测引擎实例
        
    Returns:
        float: 保证金比例
    """
    return getattr(engine, 'margin_rate', 0.1)  # 默认10%


def get_instruments(engine, exchange=None):
    """
    获取合约信息
    
    Args:
        engine: 回测引擎实例
        exchange: 交易所代码，None表示所有交易所
        
    Returns:
        list: 合约信息列表
    """
    # 模拟合约信息
    instruments = [
        {'code': 'IF2312', 'name': '沪深300期货', 'exchange': 'CFFEX', 'multiplier': 300},
        {'code': 'IC2312', 'name': '中证500期货', 'exchange': 'CFFEX', 'multiplier': 200},
        {'code': 'IH2312', 'name': '上证50期货', 'exchange': 'CFFEX', 'multiplier': 300},
        {'code': 'cu2312', 'name': '铜期货', 'exchange': 'SHFE', 'multiplier': 5},
    ]
    
    if exchange:
        instruments = [inst for inst in instruments if inst['exchange'] == exchange]
    
    log.info(f"获取合约信息: {len(instruments)}个")
    return instruments


# ==================== 期权相关API ====================

def get_opt_objects(engine):
    """
    获取期权标的列表
    
    Args:
        engine: 回测引擎实例
        
    Returns:
        list: 期权标的代码列表
    """
    # 模拟期权标的
    opt_objects = ['510050.SH', '510300.SH', '159919.SZ']
    log.info(f"获取期权标的列表: {len(opt_objects)}个")
    return opt_objects


def get_opt_last_dates(engine, underlying):
    """
    获取期权标的到期日列表
    
    Args:
        engine: 回测引擎实例
        underlying: 标的代码
        
    Returns:
        list: 到期日列表
    """
    # 模拟到期日
    base_date = pd.Timestamp('2023-12-31')
    last_dates = []
    for i in range(1, 13):
        last_dates.append((base_date + pd.DateOffset(months=i)).strftime('%Y-%m-%d'))
    
    log.info(f"获取期权到期日: {underlying} {len(last_dates)}个")
    return last_dates


def get_opt_contracts(engine, underlying, last_date):
    """
    获取期权标的对应合约列表
    
    Args:
        engine: 回测引擎实例
        underlying: 标的代码
        last_date: 到期日
        
    Returns:
        list: 期权合约列表
    """
    # 模拟期权合约
    contracts = []
    for strike in [2.5, 3.0, 3.5, 4.0, 4.5]:
        contracts.append({
            'call': f'{underlying}_C_{last_date}_{strike}',
            'put': f'{underlying}_P_{last_date}_{strike}',
            'strike': strike
        })
    
    log.info(f"获取期权合约: {underlying} {last_date} {len(contracts)}个")
    return contracts


def option_exercise(engine, option_code, amount):
    """
    期权行权
    
    Args:
        engine: 回测引擎实例
        option_code: 期权代码
        amount: 行权数量
        
    Returns:
        str: 行权订单ID
    """
    order_id = str(uuid.uuid4())
    log.info(f"期权行权: {option_code} {amount}张 订单ID: {order_id}")
    
    return order_id


def option_covered_lock(engine, underlying, amount):
    """
    期权标的备兑锁定
    
    Args:
        engine: 回测引擎实例
        underlying: 标的代码
        amount: 锁定数量
        
    Returns:
        str: 操作结果ID
    """
    operation_id = str(uuid.uuid4())
    log.info(f"期权备兑锁定: {underlying} {amount}股 操作ID: {operation_id}")
    
    return operation_id


def option_covered_unlock(engine, underlying, amount):
    """
    期权标的备兑解锁
    
    Args:
        engine: 回测引擎实例
        underlying: 标的代码
        amount: 解锁数量
        
    Returns:
        str: 操作结果ID
    """
    operation_id = str(uuid.uuid4())
    log.info(f"期权备兑解锁: {underlying} {amount}股 操作ID: {operation_id}")
    
    return operation_id


# ==================== 基础查询API ====================

def get_market_detail(engine, market):
    """
    获取市场详细信息
    
    Args:
        engine: 回测引擎实例
        market: 市场代码
        
    Returns:
        dict: 市场详细信息
    """
    market_details = {
        'SH': {
            'name': '上海证券交易所',
            'currency': 'CNY',
            'timezone': 'Asia/Shanghai',
            'trading_hours': '09:30-15:00',
            'lunch_break': '11:30-13:00'
        },
        'SZ': {
            'name': '深圳证券交易所', 
            'currency': 'CNY',
            'timezone': 'Asia/Shanghai',
            'trading_hours': '09:30-15:00',
            'lunch_break': '11:30-13:00'
        }
    }
    
    detail = market_details.get(market, {
        'name': f'市场{market}',
        'currency': 'CNY',
        'timezone': 'Asia/Shanghai'
    })
    
    log.info(f"获取市场详情: {market}")
    return detail


def get_stock_blocks(engine, stock):
    """
    获取股票板块信息
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        dict: 板块信息
    """
    # 模拟板块信息
    blocks = {
        'industry': '电子信息',
        'concept': ['5G概念', '人工智能', '芯片概念'],
        'area': '上海',
        'market_cap': 'large'  # large, medium, small
    }
    
    log.info(f"获取股票板块信息: {stock}")
    return blocks


def get_tick_direction(engine, stock):
    """
    获取股票tick方向
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        str: tick方向 ('up', 'down', 'flat')
    """
    # 模拟tick方向
    directions = ['up', 'down', 'flat']
    direction = random.choice(directions)
    
    log.info(f"获取tick方向: {stock} -> {direction}")
    return direction


# ==================== 高级市场数据API ====================

def get_snapshot(engine, stock):
    """
    获取股票快照数据
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        dict: 快照数据
    """
    if stock in engine.data:
        latest_data = engine.data[stock].iloc[-1]
        snapshot = {
            'code': stock,
            'open': latest_data['open'],
            'high': latest_data['high'],
            'low': latest_data['low'],
            'close': latest_data['close'],
            'volume': latest_data['volume'],
            'turnover': latest_data['close'] * latest_data['volume'],
            'bid1': latest_data['close'] * 0.999,
            'ask1': latest_data['close'] * 1.001,
            'bid1_volume': 10000,
            'ask1_volume': 10000
        }
    else:
        snapshot = {'code': stock, 'error': 'No data available'}
    
    log.info(f"获取股票快照: {stock}")
    return snapshot


def get_volume_ratio(engine, stock):
    """
    获取股票量比
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        float: 量比
    """
    if stock in engine.data and len(engine.data[stock]) >= 5:
        recent_volume = engine.data[stock]['volume'].iloc[-1]
        avg_volume = engine.data[stock]['volume'].iloc[-5:].mean()
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
    else:
        volume_ratio = 1.0
    
    log.info(f"获取量比: {stock} -> {volume_ratio:.2f}")
    return volume_ratio


def get_turnover_rate(engine, stock):
    """
    获取股票换手率
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        float: 换手率(%)
    """
    # 模拟换手率计算
    turnover_rate = random.uniform(0.5, 5.0)  # 0.5%-5%
    log.info(f"获取换手率: {stock} -> {turnover_rate:.2f}%")
    return turnover_rate


def get_pe_ratio(engine, stock):
    """
    获取股票市盈率
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        float: 市盈率
    """
    # 模拟市盈率
    pe_ratio = random.uniform(10, 50)
    log.info(f"获取市盈率: {stock} -> {pe_ratio:.2f}")
    return pe_ratio


def get_pb_ratio(engine, stock):
    """
    获取股票市净率
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        float: 市净率
    """
    # 模拟市净率
    pb_ratio = random.uniform(0.5, 8.0)
    log.info(f"获取市净率: {stock} -> {pb_ratio:.2f}")
    return pb_ratio


# ==================== 分红配股API ====================

def get_dividend_info(engine, stock, year=None):
    """
    获取股票分红信息
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        year: 年份，None表示最近一年
        
    Returns:
        dict: 分红信息
    """
    # 模拟分红信息
    dividend_info = {
        'stock': stock,
        'year': year or 2023,
        'dividend_per_share': 0.5,  # 每股分红
        'ex_dividend_date': '2023-06-15',  # 除权日
        'record_date': '2023-06-10',  # 股权登记日
        'payment_date': '2023-06-20'  # 派息日
    }
    
    log.info(f"获取分红信息: {stock} {year or 2023}年")
    return dividend_info


def get_rights_issue_info(engine, stock):
    """
    获取配股信息
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        dict: 配股信息
    """
    # 模拟配股信息
    rights_info = {
        'stock': stock,
        'rights_ratio': 10,  # 每10股配X股
        'rights_shares': 3,  # 配股数量
        'rights_price': 8.5,  # 配股价格
        'ex_rights_date': '2023-08-15',  # 除权日
        'payment_deadline': '2023-09-01'  # 缴款截止日
    }
    
    log.info(f"获取配股信息: {stock}")
    return rights_info


# ==================== 停复牌API ====================

def get_suspend_info(engine, stock):
    """
    获取股票停牌信息
    
    Args:
        engine: 回测引擎实例
        stock: 股票代码
        
    Returns:
        dict: 停牌信息
    """
    suspend_info = {
        'stock': stock,
        'is_suspended': False,  # 是否停牌
        'suspend_date': None,   # 停牌日期
        'suspend_reason': None, # 停牌原因
        'expected_resume_date': None  # 预计复牌日期
    }
    
    log.info(f"获取停牌信息: {stock}")
    return suspend_info


def is_suspended(engine, stock):
    """
    判断股票是否停牌

    Args:
        engine: 回测引擎实例
        stock: 股票代码

    Returns:
        bool: True表示停牌，False表示正常交易
    """
    suspend_info = get_suspend_info(engine, stock)
    return suspend_info['is_suspended']


# ==================== 涨跌停判断API ====================

def check_limit(engine, security):
    """
    检查股票涨跌停状态

    Args:
        engine: 回测引擎实例
        security: 股票代码

    Returns:
        dict: 涨跌停状态信息
            {
                'limit_up': bool,      # 是否涨停
                'limit_down': bool,    # 是否跌停
                'limit_up_price': float,   # 涨停价
                'limit_down_price': float, # 跌停价
                'current_price': float,    # 当前价格
                'pct_change': float        # 涨跌幅
            }
    """
    try:
        # 获取当前数据
        if hasattr(engine, 'current_data'):
            current_data = engine.current_data.get(security, {})
        else:
            current_data = {}

        if not current_data:
            log.warning(f"无法获取 {security} 的当前数据")
            return {
                'limit_up': False,
                'limit_down': False,
                'limit_up_price': None,
                'limit_down_price': None,
                'current_price': None,
                'pct_change': None
            }

        current_price = current_data.get('close', 0)

        # 获取昨收价
        prev_close = current_price * 0.9  # 默认基准价

        # 尝试从历史数据获取昨收价
        try:
            if hasattr(engine, 'data') and security in engine.data:
                hist_data = engine.data[security]
                if len(hist_data) >= 2:
                    prev_close = hist_data['close'].iloc[-2]
                elif len(hist_data) >= 1:
                    prev_close = hist_data['close'].iloc[-1]
        except Exception:
            pass  # 使用默认基准价

        # 计算涨跌停价格（A股一般为10%）
        limit_up_price = round(prev_close * 1.1, 2)
        limit_down_price = round(prev_close * 0.9, 2)

        # 计算涨跌幅
        pct_change = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0

        # 判断是否涨跌停（允许0.01的误差）
        limit_up = abs(current_price - limit_up_price) <= 0.01
        limit_down = abs(current_price - limit_down_price) <= 0.01

        result = {
            'limit_up': limit_up,
            'limit_down': limit_down,
            'limit_up_price': limit_up_price,
            'limit_down_price': limit_down_price,
            'current_price': current_price,
            'pct_change': round(pct_change, 2)
        }

        log.info(f"涨跌停检查 {security}: 当前价{current_price}, 涨停{limit_up}, 跌停{limit_down}")
        return result

    except Exception as e:
        log.error(f"检查涨跌停状态失败 {security}: {e}")
        return {
            'limit_up': False,
            'limit_down': False,
            'limit_up_price': None,
            'limit_down_price': None,
            'current_price': None,
            'pct_change': None
        }


# ==================== 文件和目录管理API ====================

def create_dir(engine=None, user_path=None):
    """
    创建文件目录路径

    Args:
        engine: 回测引擎实例（可选）
        user_path: 用户指定的路径，相对于研究路径

    Returns:
        str: 创建的完整路径
    """
    try:
        if user_path is None:
            log.warning("create_dir: 未指定路径")
            return None

        # 获取基础路径
        if engine and hasattr(engine, 'research_path'):
            base_path = Path(engine.research_path)
        else:
            base_path = Path('./research')  # 默认研究路径

        # 构建完整路径
        full_path = base_path / user_path

        # 创建目录
        full_path.mkdir(parents=True, exist_ok=True)

        log.info(f"创建目录: {full_path}")
        return str(full_path)

    except Exception as e:
        log.error(f"创建目录失败 {user_path}: {e}")
        return None


def get_user_name(engine):
    """
    获取登录终端的资金账号

    Args:
        engine: 回测引擎实例

    Returns:
        str: 资金账号
    """
    # 在模拟环境中返回模拟账号
    if hasattr(engine, 'account_id'):
        return engine.account_id
    return "SIMULATED_ACCOUNT_001"


def get_trade_name(engine):
    """
    获取交易名称

    Args:
        engine: 回测引擎实例

    Returns:
        str: 交易名称
    """
    # 在模拟环境中返回模拟交易名称
    if hasattr(engine, 'trade_name'):
        return engine.trade_name
    return "SimTradeLab_Backtest"


def permission_test(engine, permission_type="trade"):
    """
    权限校验

    Args:
        engine: 回测引擎实例
        permission_type: 权限类型

    Returns:
        bool: 是否有权限
    """
    # 在模拟环境中总是返回True
    log.info(f"权限校验: {permission_type} - 通过")
    return True


# ==================== 股票基础信息补充API ====================

def get_stock_exrights(engine, stocks, start_date=None, end_date=None):
    """
    获取股票除权除息信息

    Args:
        engine: 回测引擎实例
        stocks: 股票代码或股票列表
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        dict: 除权除息信息
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    result = {}
    for stock in stocks:
        # 模拟除权除息数据
        exrights_data = {
            'dividend_date': '2023-06-15',  # 分红日期
            'ex_dividend_date': '2023-06-16',  # 除息日
            'record_date': '2023-06-14',  # 股权登记日
            'cash_dividend': 0.5,  # 现金分红（每股）
            'stock_dividend': 0.0,  # 股票分红比例
            'rights_ratio': 0.0,  # 配股比例
            'rights_price': 0.0,  # 配股价格
            'split_ratio': 1.0,  # 拆股比例
        }
        result[stock] = exrights_data

    log.info(f"获取除权除息信息: {len(stocks)}只股票")
    return result


def get_index_stocks(engine, index_code):
    """
    获取指数成份股

    Args:
        engine: 回测引擎实例
        index_code: 指数代码

    Returns:
        list: 成份股代码列表
    """
    # 模拟不同指数的成份股
    index_stocks_map = {
        '000001.SH': ['600000.SH', '600036.SH', '600519.SH', '000001.SZ', '000002.SZ'],  # 上证指数
        '000300.SH': ['600000.SH', '600036.SH', '600519.SH', '000001.SZ', '000002.SZ'],  # 沪深300
        '399001.SZ': ['000001.SZ', '000002.SZ', '000858.SZ', '002415.SZ', '300059.SZ'],  # 深证成指
        '399006.SZ': ['000001.SZ', '000002.SZ', '000858.SZ', '002415.SZ', '300059.SZ'],  # 创业板指
    }

    stocks = index_stocks_map.get(index_code, [])
    log.info(f"获取指数成份股 {index_code}: {len(stocks)}只")
    return stocks


def get_industry_stocks(engine, industry):
    """
    获取行业成份股

    Args:
        engine: 回测引擎实例
        industry: 行业名称或代码

    Returns:
        list: 行业成份股代码列表
    """
    # 模拟不同行业的成份股
    industry_stocks_map = {
        '银行': ['600000.SH', '600036.SH', '000001.SZ', '002142.SZ'],
        '白酒': ['600519.SH', '000858.SZ', '002304.SZ'],
        '科技': ['000002.SZ', '002415.SZ', '300059.SZ', '300750.SZ'],
        '医药': ['000001.SZ', '600276.SH', '300015.SZ'],
        '地产': ['000002.SZ', '600048.SH', '000069.SZ'],
    }

    stocks = industry_stocks_map.get(industry, [])
    log.info(f"获取行业成份股 {industry}: {len(stocks)}只")
    return stocks


def get_ipo_stocks(engine, date=None):
    """
    获取当日IPO申购标的

    Args:
        engine: 回测引擎实例
        date: 查询日期，None表示当前日期

    Returns:
        list: IPO申购标的信息列表
    """
    # 模拟IPO申购标的
    ipo_stocks = [
        {
            'stock_code': '301001.SZ',
            'stock_name': '新股A',
            'issue_price': 15.50,
            'issue_date': '2023-06-20',
            'max_purchase_amount': 10000,
            'min_purchase_amount': 500,
            'market': 'SZ'
        },
        {
            'stock_code': '688001.SH',
            'stock_name': '新股B',
            'issue_price': 28.80,
            'issue_date': '2023-06-20',
            'max_purchase_amount': 5000,
            'min_purchase_amount': 500,
            'market': 'SH'
        }
    ]

    log.info(f"获取IPO申购标的: {len(ipo_stocks)}只")
    return ipo_stocks


# ==================== 高级行情数据API ====================

def get_individual_entrust(engine, stocks, start_time=None, end_time=None):
    """
    获取逐笔委托行情

    Args:
        engine: 回测引擎实例
        stocks: 股票代码或股票列表
        start_time: 开始时间
        end_time: 结束时间

    Returns:
        dict: 逐笔委托数据，key为股票代码，value为DataFrame
    """
    

    if isinstance(stocks, str):
        stocks = [stocks]

    result = {}

    for stock in stocks:
        # 模拟逐笔委托数据
        current_time = datetime.now()
        time_range = pd.date_range(
            start=current_time - timedelta(minutes=30),
            end=current_time,
            freq='10S'  # 每10秒一条记录
        )

        n_records = len(time_range)

        # 生成模拟数据
        base_price = 10.0  # 基础价格
        entrust_data = pd.DataFrame({
            'business_time': [int(t.timestamp() * 1000) for t in time_range],  # 毫秒时间戳
            'hq_px': np.round(base_price + np.random.normal(0, 0.1, n_records), 2),  # 委托价格
            'business_amount': np.random.randint(100, 10000, n_records),  # 委托量
            'order_no': [f"ORD{i:06d}" for i in range(n_records)],  # 委托编号
            'business_direction': np.random.choice([0, 1], n_records),  # 0-卖，1-买
            'trans_kind': np.random.choice([1, 2, 3], n_records)  # 1-市价，2-限价，3-本方最优
        })

        result[stock] = entrust_data

    log.info(f"获取逐笔委托数据: {len(stocks)}只股票")
    return result


def get_individual_transaction(engine, stocks, start_time=None, end_time=None):
    """
    获取逐笔成交行情

    Args:
        engine: 回测引擎实例
        stocks: 股票代码或股票列表
        start_time: 开始时间
        end_time: 结束时间

    Returns:
        dict: 逐笔成交数据，key为股票代码，value为DataFrame
    """
    if isinstance(stocks, str):
        stocks = [stocks]

    result = {}

    for stock in stocks:
        # 模拟逐笔成交数据
        current_time = datetime.now()
        time_range = pd.date_range(
            start=current_time - timedelta(minutes=30),
            end=current_time,
            freq='15S'  # 每15秒一条记录
        )

        n_records = len(time_range)

        # 生成模拟数据
        base_price = 10.0  # 基础价格
        transaction_data = pd.DataFrame({
            'business_time': [int(t.timestamp() * 1000) for t in time_range],  # 毫秒时间戳
            'hq_px': np.round(base_price + np.random.normal(0, 0.05, n_records), 2),  # 成交价格
            'business_amount': np.random.randint(100, 5000, n_records),  # 成交量
            'trade_index': [f"TRD{i:06d}" for i in range(n_records)],  # 成交编号
            'business_direction': np.random.choice([0, 1], n_records),  # 0-卖，1-买
            'buy_no': [f"BUY{i:06d}" for i in range(n_records)],  # 叫买方编号
            'sell_no': [f"SELL{i:06d}" for i in range(n_records)],  # 叫卖方编号
            'trans_flag': np.random.choice([0, 1], n_records, p=[0.95, 0.05]),  # 0-普通，1-撤单
            'trans_identify_am': np.random.choice([0, 1], n_records, p=[0.9, 0.1]),  # 0-盘中，1-盘后
            'channel_num': np.random.randint(1, 10, n_records)  # 成交通道信息
        })

        result[stock] = transaction_data

    log.info(f"获取逐笔成交数据: {len(stocks)}只股票")
    return result


def get_gear_price(engine, security):
    """
    获取指定代码的档位行情价格

    Args:
        engine: 回测引擎实例
        security: 股票代码

    Returns:
        dict: 档位行情数据
    """
    # 模拟档位行情数据
    base_price = 10.0

    # 生成买卖五档数据
    bid_prices = []
    ask_prices = []

    for i in range(5):
        bid_price = round(base_price - (i + 1) * 0.01, 2)
        ask_price = round(base_price + (i + 1) * 0.01, 2)
        bid_prices.append(bid_price)
        ask_prices.append(ask_price)

    gear_data = {
        'security': security,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'bid_prices': bid_prices,  # 买一到买五价格
        'bid_volumes': [random.randint(100, 10000) for _ in range(5)],  # 买一到买五量
        'ask_prices': ask_prices,  # 卖一到卖五价格
        'ask_volumes': [random.randint(100, 10000) for _ in range(5)],  # 卖一到卖五量
        'last_price': base_price,  # 最新价
        'total_bid_volume': sum([random.randint(100, 10000) for _ in range(5)]),  # 委买总量
        'total_ask_volume': sum([random.randint(100, 10000) for _ in range(5)]),  # 委卖总量
    }

    log.info(f"获取档位行情: {security}")
    return gear_data


def get_sort_msg(engine, market_type='sector', sort_field='pct_change', ascending=False, count=20):
    """
    获取板块、行业的涨幅排名

    Args:
        engine: 回测引擎实例
        market_type: 市场类型 ('sector'-板块, 'industry'-行业)
        sort_field: 排序字段 ('pct_change'-涨跌幅, 'volume'-成交量, 'amount'-成交额)
        ascending: 是否升序排列
        count: 返回数量

    Returns:
        list: 排名数据列表
    """
    # 模拟板块/行业数据
    if market_type == 'sector':
        sectors = [
            '银行板块', '证券板块', '保险板块', '地产板块', '钢铁板块',
            '煤炭板块', '有色板块', '石油板块', '电力板块', '汽车板块',
            '家电板块', '食品板块', '医药板块', '科技板块', '军工板块'
        ]
        data_source = sectors
    else:  # industry
        industries = [
            '银行业', '证券业', '保险业', '房地产业', '钢铁业',
            '煤炭业', '有色金属', '石油化工', '电力行业', '汽车制造',
            '家用电器', '食品饮料', '医药生物', '计算机', '国防军工'
        ]
        data_source = industries

    # 生成模拟排名数据
    sort_data = []
    for i, name in enumerate(data_source[:count]):
        item = {
            'name': name,
            'code': f"{market_type.upper()}{i:03d}",
            'pct_change': round(random.uniform(-5.0, 8.0), 2),  # 涨跌幅 -5% 到 8%
            'volume': random.randint(1000000, 100000000),  # 成交量
            'amount': random.randint(100000000, 10000000000),  # 成交额
            'up_count': random.randint(0, 50),  # 上涨家数
            'down_count': random.randint(0, 50),  # 下跌家数
            'flat_count': random.randint(0, 10),  # 平盘家数
        }
        sort_data.append(item)

    # 按指定字段排序
    sort_data.sort(key=lambda x: x[sort_field], reverse=not ascending)

    log.info(f"获取{market_type}排名数据: {len(sort_data)}个")
    return sort_data


def send_email(engine, to_email, subject, content, attachments=None):
    """
    发送邮箱信息

    Args:
        engine: 回测引擎实例
        to_email: 收件人邮箱
        subject: 邮件主题
        content: 邮件内容
        attachments: 附件路径列表

    Returns:
        bool: 发送是否成功
    """
    # 在模拟环境中，只记录日志
    log.info(f"发送邮件到 {to_email}")
    log.info(f"主题: {subject}")
    log.info(f"内容: {content[:100]}...")  # 只显示前100个字符

    if attachments:
        log.info(f"附件: {attachments}")

    # 模拟发送成功
    return True


def send_qywx(engine, content, toparty=None, touser=None, totag=None):
    """
    发送企业微信信息

    Args:
        engine: 回测引擎实例
        content: 发送内容
        toparty: 发送对象为部门
        touser: 发送内容为个人
        totag: 发送内容为分组

    Returns:
        bool: 发送是否成功
    """
    # 在模拟环境中，只记录日志
    log.info(f"发送企业微信消息: {content}")

    if toparty:
        log.info(f"发送到部门: {toparty}")
    if touser:
        log.info(f"发送到用户: {touser}")
    if totag:
        log.info(f"发送到标签: {totag}")

    # 模拟发送成功
    return True


# ==================== 期权高级功能API ====================

def get_contract_info(engine, option_code):
    """
    获取期权合约信息

    Args:
        engine: 回测引擎实例
        option_code: 期权合约代码

    Returns:
        dict: 期权合约详细信息
    """
    # 模拟期权合约信息
    contract_info = {
        'option_code': option_code,
        'option_name': f'期权合约{option_code[-4:]}',
        'underlying_code': '510050.SH',  # 标的代码
        'underlying_name': '50ETF',
        'option_type': 'C' if 'C' in option_code else 'P',  # C-认购，P-认沽
        'exercise_type': 'E',  # E-欧式，A-美式
        'strike_price': 2.500,  # 行权价
        'contract_unit': 10000,  # 合约单位
        'expire_date': '2023-12-27',  # 到期日
        'last_trade_date': '2023-12-27',  # 最后交易日
        'exercise_date': '2023-12-27',  # 行权日
        'delivery_date': '2023-12-28',  # 交割日
        'min_price_change': 0.0001,  # 最小价格变动单位
        'price_limit_type': 'P',  # 涨跌幅限制类型
        'daily_price_up_limit': 0.2992,  # 涨停价
        'daily_price_down_limit': 0.0001,  # 跌停价
        'margin_unit': 0.12,  # 保证金单位
        'margin_ratio1': 0.12,  # 保证金比例1
        'margin_ratio2': 0.07,  # 保证金比例2
        'round_lot': 1,  # 整手数
        'lmt_ord_min_floor': 1,  # 限价申报最小数量
        'lmt_ord_max_floor': 10,  # 限价申报最大数量
        'mkt_ord_min_floor': 1,  # 市价申报最小数量
        'mkt_ord_max_floor': 5,  # 市价申报最大数量
        'tick_size': 0.0001,  # 最小报价单位
    }

    log.info(f"获取期权合约信息: {option_code}")
    return contract_info


def get_covered_lock_amount(engine, underlying_code):
    """
    获取期权标的可备兑锁定数量

    Args:
        engine: 回测引擎实例
        underlying_code: 标的代码

    Returns:
        dict: 可备兑锁定数量信息
    """
    # 获取当前持仓（简化处理，在模拟环境中使用默认值）
    try:
        position = get_position(engine, underlying_code)
        available_amount = position.get('available_amount', 0) if position else 0
    except:
        # 在测试环境中使用模拟数据
        available_amount = 100000  # 模拟持仓10万股

    # 模拟可备兑锁定数量计算
    lock_info = {
        'underlying_code': underlying_code,
        'total_amount': available_amount,  # 总持仓数量
        'locked_amount': 0,  # 已锁定数量
        'available_lock_amount': available_amount,  # 可锁定数量
        'lock_unit': 10000,  # 锁定单位（每手期权对应的标的数量）
        'max_lock_lots': available_amount // 10000,  # 最大可锁定手数
    }

    log.info(f"获取备兑锁定数量: {underlying_code}, 可锁定{lock_info['max_lock_lots']}手")
    return lock_info


def get_covered_unlock_amount(engine, underlying_code):
    """
    获取期权标的允许备兑解锁数量

    Args:
        engine: 回测引擎实例
        underlying_code: 标的代码

    Returns:
        dict: 允许备兑解锁数量信息
    """
    # 模拟已锁定的备兑数量
    unlock_info = {
        'underlying_code': underlying_code,
        'locked_amount': 50000,  # 已锁定数量
        'available_unlock_amount': 50000,  # 可解锁数量
        'unlock_unit': 10000,  # 解锁单位
        'max_unlock_lots': 5,  # 最大可解锁手数
        'pending_exercise_amount': 0,  # 待行权数量
    }

    log.info(f"获取备兑解锁数量: {underlying_code}, 可解锁{unlock_info['max_unlock_lots']}手")
    return unlock_info


def open_prepared(engine, option_code, amount, price=None):
    """
    备兑开仓

    Args:
        engine: 回测引擎实例
        option_code: 期权合约代码
        amount: 开仓数量（手）
        price: 开仓价格，None表示市价

    Returns:
        dict: 委托结果
    """
    # 获取标的代码
    underlying_code = '510050.SH'  # 假设是50ETF期权

    # 检查备兑锁定数量
    lock_info = get_covered_lock_amount(engine, underlying_code)
    if amount > lock_info['max_lock_lots']:
        log.error(f"备兑开仓失败: 可锁定数量不足，需要{amount}手，可用{lock_info['max_lock_lots']}手")
        return {
            'success': False,
            'error': '可锁定数量不足',
            'order_id': None
        }

    # 执行备兑开仓
    order_id = f"COVERED_OPEN_{int(datetime.now().timestamp())}"

    # 模拟委托成功
    result = {
        'success': True,
        'order_id': order_id,
        'option_code': option_code,
        'amount': amount,
        'price': price or 0.2500,  # 默认价格
        'order_type': 'covered_open',
        'underlying_code': underlying_code,
        'locked_amount': amount * 10000,  # 锁定的标的数量
    }

    log.info(f"备兑开仓: {option_code}, {amount}手, 委托号{order_id}")
    return result


def close_prepared(engine, option_code, amount, price=None):
    """
    备兑平仓

    Args:
        engine: 回测引擎实例
        option_code: 期权合约代码
        amount: 平仓数量（手）
        price: 平仓价格，None表示市价

    Returns:
        dict: 委托结果
    """
    # 检查备兑持仓
    # 这里应该检查实际的备兑持仓，简化处理

    # 执行备兑平仓
    order_id = f"COVERED_CLOSE_{int(datetime.now().timestamp())}"

    # 模拟委托成功
    result = {
        'success': True,
        'order_id': order_id,
        'option_code': option_code,
        'amount': amount,
        'price': price or 0.2500,  # 默认价格
        'order_type': 'covered_close',
        'unlock_amount': amount * 10000,  # 解锁的标的数量
    }

    log.info(f"备兑平仓: {option_code}, {amount}手, 委托号{order_id}")
    return result


# ==================== 其他缺失的API ====================

def get_trades_file(engine, date=None):
    """
    获取对账数据文件

    Args:
        engine: 回测引擎实例
        date: 查询日期，None表示当前日期

    Returns:
        dict: 对账文件信息
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 模拟对账文件信息
    trades_file = {
        'date': date,
        'file_path': f'/data/trades/{date}_trades.csv',
        'file_size': 1024000,  # 文件大小（字节）
        'record_count': 150,   # 记录数量
        'status': 'ready',     # 文件状态
        'generated_time': f'{date} 18:00:00'
    }

    log.info(f"获取对账文件: {date}, {trades_file['record_count']}条记录")
    return trades_file


def convert_position_from_csv(engine, csv_file_path):
    """
    获取设置底仓的参数列表(股票)

    Args:
        engine: 回测引擎实例
        csv_file_path: CSV文件路径

    Returns:
        list: 底仓参数列表
    """
    # 模拟从CSV文件读取底仓信息
    position_params = [
        {
            'security': '000001.SZ',
            'amount': 10000,
            'avg_cost': 12.50,
            'market_value': 125000.0
        },
        {
            'security': '600519.SH',
            'amount': 100,
            'avg_cost': 1800.0,
            'market_value': 180000.0
        }
    ]

    log.info(f"从CSV转换底仓参数: {len(position_params)}只股票")
    return position_params


def get_deliver(engine, start_date=None, end_date=None):
    """
    获取历史交割单信息

    Args:
        engine: 回测引擎实例
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        list: 交割单列表
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # 模拟交割单数据
    deliver_records = [
        {
            'trade_date': '2023-06-15',
            'security': '000001.SZ',
            'security_name': '平安银行',
            'operation': 'buy',
            'amount': 1000,
            'price': 12.50,
            'total_amount': 12500.0,
            'commission': 3.75,
            'stamp_tax': 0.0,
            'transfer_fee': 0.63,
            'net_amount': 12504.38,
            'balance': 987495.62
        },
        {
            'trade_date': '2023-06-16',
            'security': '600519.SH',
            'security_name': '贵州茅台',
            'operation': 'sell',
            'amount': 100,
            'price': 1850.0,
            'total_amount': 185000.0,
            'commission': 5.55,
            'stamp_tax': 185.0,
            'transfer_fee': 0.93,
            'net_amount': 184808.52,
            'balance': 1172304.14
        }
    ]

    log.info(f"获取交割单: {start_date}到{end_date}, {len(deliver_records)}条记录")
    return deliver_records


def get_fundjour(engine, start_date=None, end_date=None):
    """
    获取历史资金流水信息

    Args:
        engine: 回测引擎实例
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        list: 资金流水列表
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # 模拟资金流水数据
    fund_records = [
        {
            'date': '2023-06-15',
            'time': '09:30:00',
            'operation': 'buy_stock',
            'description': '买入000001.SZ',
            'amount': -12504.38,
            'balance': 987495.62,
            'remark': '股票买入'
        },
        {
            'date': '2023-06-16',
            'time': '14:30:00',
            'operation': 'sell_stock',
            'description': '卖出600519.SH',
            'amount': 184808.52,
            'balance': 1172304.14,
            'remark': '股票卖出'
        },
        {
            'date': '2023-06-17',
            'time': '15:00:00',
            'operation': 'dividend',
            'description': '000001.SZ分红',
            'amount': 500.0,
            'balance': 1172804.14,
            'remark': '现金分红'
        }
    ]

    log.info(f"获取资金流水: {start_date}到{end_date}, {len(fund_records)}条记录")
    return fund_records


def order_tick(engine, security, amount, tick_condition):
    """
    tick行情触发买卖

    Args:
        engine: 回测引擎实例
        security: 证券代码
        amount: 交易数量
        tick_condition: tick触发条件

    Returns:
        dict: 委托结果
    """
    order_id = f"TICK_ORDER_{int(datetime.now().timestamp())}"

    result = {
        'success': True,
        'order_id': order_id,
        'security': security,
        'amount': amount,
        'tick_condition': tick_condition,
        'order_type': 'tick_order',
        'status': 'pending',
        'timestamp': datetime.now().isoformat()
    }

    log.info(f"tick触发委托: {security}, {amount}股, 委托号{order_id}")
    return result


def cancel_order_ex(engine, order_id, cancel_type='normal'):
    """
    撤单（扩展版本）

    Args:
        engine: 回测引擎实例
        order_id: 委托编号
        cancel_type: 撤单类型

    Returns:
        dict: 撤单结果
    """

    result = {
        'success': True,
        'order_id': order_id,
        'cancel_type': cancel_type,
        'cancel_time': datetime.now().isoformat(),
        'status': 'cancelled'
    }

    log.info(f"撤单: {order_id}, 类型{cancel_type}")
    return result


def get_all_orders(engine, date=None):
    """
    获取账户当日全部订单

    Args:
        engine: 回测引擎实例
        date: 查询日期，None表示当前日期

    Returns:
        list: 全部订单列表
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 模拟当日全部订单
    all_orders = [
        {
            'order_id': 'ORD001',
            'security': '000001.SZ',
            'operation': 'buy',
            'amount': 1000,
            'price': 12.50,
            'status': 'filled',
            'order_time': f'{date} 09:30:00',
            'fill_time': f'{date} 09:30:15'
        },
        {
            'order_id': 'ORD002',
            'security': '600519.SH',
            'operation': 'sell',
            'amount': 100,
            'price': 1850.0,
            'status': 'filled',
            'order_time': f'{date} 14:30:00',
            'fill_time': f'{date} 14:30:20'
        },
        {
            'order_id': 'ORD003',
            'security': '000002.SZ',
            'operation': 'buy',
            'amount': 500,
            'price': 25.0,
            'status': 'cancelled',
            'order_time': f'{date} 15:00:00',
            'cancel_time': f'{date} 15:00:30'
        }
    ]

    log.info(f"获取当日全部订单: {date}, {len(all_orders)}笔")
    return all_orders


def after_trading_cancel_order(engine, order_id):
    """
    盘后固定价委托撤单

    Args:
        engine: 回测引擎实例
        order_id: 委托编号

    Returns:
        dict: 撤单结果
    """
    result = {
        'success': True,
        'order_id': order_id,
        'cancel_type': 'after_trading',
        'cancel_time': datetime.now().isoformat(),
        'status': 'cancelled'
    }

    log.info(f"盘后撤单: {order_id}")
    return result