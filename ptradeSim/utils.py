# -*- coding: utf-8 -*-
"""
辅助工具函数模块
"""
from pathlib import Path
from .logger import log

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
    import pandas as pd
    import numpy as np

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
    import pandas as pd

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
    import pandas as pd

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
    import pandas as pd

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