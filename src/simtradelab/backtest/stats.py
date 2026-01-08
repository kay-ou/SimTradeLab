# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
#
"""
回测统计分析模块

包含收益率、风险指标、交易统计等计算函数，以及图表生成函数
"""


import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def _load_index_names():
    """加载指数名称映射

    Returns:
        dict: 指数代码到名称的映射字典
    """
    indices_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'indices.json')
    try:
        with open(indices_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _get_benchmark_name(benchmark_code, use_english=False):
    """获取基准名称

    Args:
        benchmark_code: 基准代码
        use_english: 是否使用英文名称（用于图表显示）

    Returns:
        str: 基准名称，如果找不到则返回代码本身
    """
    if use_english:
        english_names = {
            '000300.SS': 'CSI 300',
            '000905.SZ': 'CSI 500',
            '000001.SZ': 'SZE Component',
            '399001.SZ': 'SZE Component',
            '399006.SZ': 'ChiNext',
            '399101.SZ': 'SME Board',
            '000001.SS': 'SSE Composite'
        }
        return english_names.get(benchmark_code, benchmark_code)

    index_names = _load_index_names()
    return index_names.get(benchmark_code, benchmark_code)


def calculate_returns(portfolio_values):
    """计算收益率指标

    Args:
        portfolio_values: 每日组合价值数组

    Returns:
        dict: 包含total_return, annual_return, daily_returns等
    """
    if len(portfolio_values) == 0:
        return {
            'total_return': 0,
            'annual_return': 0,
            'daily_returns': np.array([]),
            'initial_value': 0,
            'final_value': 0,
            'trading_days': 0
        }

    initial_value = portfolio_values[0]
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_value) / initial_value if initial_value > 0 else 0

    # 每日收益率
    daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

    # 年化收益率（假设252个交易日）
    trading_days = len(portfolio_values)
    annual_return = (final_value / initial_value) ** (252 / trading_days) - 1 if trading_days > 0 and initial_value > 0 else 0

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'daily_returns': daily_returns,
        'initial_value': initial_value,
        'final_value': final_value,
        'trading_days': trading_days
    }


def calculate_risk_metrics(daily_returns, portfolio_values):
    """计算风险指标

    Args:
        daily_returns: 每日收益率数组
        portfolio_values: 每日组合价值数组

    Returns:
        dict: 包含sharpe_ratio, max_drawdown, volatility等
    """
    # 夏普比率
    if len(daily_returns) > 0 and np.std(daily_returns) > 0:
        sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)
    else:
        sharpe_ratio = 0

    # 最大回撤
    cummax = np.maximum.accumulate(portfolio_values)
    drawdown = (portfolio_values - cummax) / cummax
    max_drawdown = np.min(drawdown)

    # 波动率（年化）
    volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 0 else 0

    return {
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'volatility': volatility,
        'drawdown': drawdown
    }


def calculate_benchmark_metrics(daily_returns, benchmark_daily_returns, annual_return, benchmark_annual_return):
    """计算相对基准的指标

    Args:
        daily_returns: 策略每日收益率
        benchmark_daily_returns: 基准每日收益率
        annual_return: 策略年化收益
        benchmark_annual_return: 基准年化收益

    Returns:
        dict: 包含alpha, beta, information_ratio等
    """
    if len(daily_returns) == 0 or len(benchmark_daily_returns) == 0:
        return {
            'alpha': 0,
            'beta': 0,
            'information_ratio': 0,
            'tracking_error': 0
        }

    # 对齐长度
    min_len = min(len(daily_returns), len(benchmark_daily_returns))

    # 协方差计算至少需要2个样本
    if min_len < 2:
        return {
            'alpha': 0,
            'beta': 0,
            'information_ratio': 0,
            'tracking_error': 0
        }

    strategy_returns = daily_returns[:min_len]
    benchmark_returns = benchmark_daily_returns[:min_len]

    # 转换为numpy数组
    strategy_returns = np.array(strategy_returns)
    benchmark_returns = np.array(benchmark_returns)

    # 计算Beta
    covariance = np.cov(strategy_returns, benchmark_returns)[0][1]
    benchmark_variance = np.var(benchmark_returns)
    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

    # 计算Alpha
    alpha = annual_return - (benchmark_annual_return * beta)

    # 计算信息比率
    excess_returns = strategy_returns - benchmark_returns
    tracking_error = np.std(excess_returns) * np.sqrt(252)
    information_ratio = (annual_return - benchmark_annual_return) / tracking_error if tracking_error > 0 else 0

    return {
        'alpha': alpha,
        'beta': beta,
        'information_ratio': information_ratio,
        'tracking_error': tracking_error
    }


def calculate_trade_stats(daily_returns):
    """计算交易统计

    Args:
        daily_returns: 每日收益率数组

    Returns:
        dict: 包含win_rate, profit_loss_ratio, win_count, lose_count等
    """
    if len(daily_returns) == 0:
        return {
            'win_rate': 0,
            'profit_loss_ratio': 0,
            'win_count': 0,
            'lose_count': 0,
            'avg_win': 0,
            'avg_lose': 0
        }

    win_days = daily_returns[daily_returns > 0]
    lose_days = daily_returns[daily_returns < 0]

    win_count = len(win_days)
    lose_count = len(lose_days)
    win_rate = win_count / len(daily_returns)

    avg_win = np.mean(win_days) if len(win_days) > 0 else 0
    avg_lose = np.mean(lose_days) if len(lose_days) > 0 else 0
    profit_loss_ratio = abs(avg_win / avg_lose) if avg_lose != 0 else 0

    return {
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'win_count': win_count,
        'lose_count': lose_count,
        'avg_win': avg_win,
        'avg_lose': avg_lose
    }


def generate_backtest_report(backtest_stats, start_date, end_date, benchmark_df, benchmark_code='000300.SS'):
    """生成完整的回测报告

    Args:
        backtest_stats: 回测统计数据字典
        start_date: 回测开始日期
        end_date: 回测结束日期
        benchmark_df: 基准数据DataFrame
        benchmark_code: 基准代码


    Returns:
        dict: 完整的回测报告指标
    """
    portfolio_values = np.array(backtest_stats['portfolio_values'])

    # 基本收益指标
    returns_metrics = calculate_returns(portfolio_values)

    # 风险指标
    risk_metrics = calculate_risk_metrics(returns_metrics['daily_returns'], portfolio_values)

    # 基准对比
    benchmark_slice = benchmark_df.loc[
        (benchmark_df.index >= start_date) &
        (benchmark_df.index <= end_date)
    ]

    if len(benchmark_slice) > 0:
        benchmark_initial = benchmark_slice['close'].iloc[0]
        benchmark_final = benchmark_slice['close'].iloc[-1]
        benchmark_return = (benchmark_final - benchmark_initial) / benchmark_initial
        benchmark_annual_return = (benchmark_final / benchmark_initial) ** (252 / len(benchmark_slice)) - 1
        benchmark_daily_returns = benchmark_slice['close'].pct_change().dropna().values

        excess_return = returns_metrics['total_return'] - benchmark_return

        benchmark_metrics = calculate_benchmark_metrics(
            returns_metrics['daily_returns'],
            benchmark_daily_returns,
            returns_metrics['annual_return'],
            benchmark_annual_return
        )
    else:
        benchmark_return = 0
        benchmark_annual_return = 0
        excess_return = 0
        benchmark_metrics = {'alpha': 0, 'beta': 0, 'information_ratio': 0, 'tracking_error': 0}

    # 交易统计
    trade_stats = calculate_trade_stats(returns_metrics['daily_returns'])

    # 获取基准名称
    benchmark_name = _get_benchmark_name(benchmark_code)

    # 合并所有指标
    report = {
        **returns_metrics,
        **risk_metrics,
        'benchmark_code': benchmark_code,
        'benchmark_name': benchmark_name,
        'benchmark_return': benchmark_return,
        'benchmark_annual_return': benchmark_annual_return,
        'excess_return': excess_return,
        **benchmark_metrics,
        **trade_stats
    }

    return report


def _validate_chart_data(backtest_stats):
    """验证并对齐图表数据

    Args:
        backtest_stats: 回测统计数据字典

    Returns:
        tuple: (dates, portfolio_values, daily_pnl, daily_buy, daily_sell, daily_positions_val)
    """
    dates = np.array(backtest_stats['trade_dates'])
    portfolio_values = np.array(backtest_stats['portfolio_values'])
    daily_pnl = np.array(backtest_stats['daily_pnl'])
    daily_buy = np.array(backtest_stats['daily_buy_amount'])
    daily_sell = np.array(backtest_stats['daily_sell_amount'])
    daily_positions_val = np.array(backtest_stats['daily_positions_value'])

    # 数据验证：确保所有数组长度一致，空数组填充为0
    expected_len = len(dates)
    if len(daily_positions_val) == 0 or len(daily_positions_val) < expected_len:
        daily_positions_val = np.zeros(expected_len)
    if len(daily_pnl) == 0 or len(daily_pnl) < expected_len:
        daily_pnl = np.zeros(expected_len)
    if len(daily_buy) == 0 or len(daily_buy) < expected_len:
        daily_buy = np.zeros(expected_len)
    if len(daily_sell) == 0 or len(daily_sell) < expected_len:
        daily_sell = np.zeros(expected_len)

    return dates, portfolio_values, daily_pnl, daily_buy, daily_sell, daily_positions_val


def _plot_nav_curve(ax, dates, portfolio_values, daily_buy, daily_sell, benchmark_data, start_date, end_date, benchmark_code='000300.SS'):
    """绘制净值曲线子图

    Args:
        ax: matplotlib axes对象
        dates: 日期数组
        portfolio_values: 组合价值数组
        daily_buy: 每日买入金额
        daily_sell: 每日卖出金额
        benchmark_data: 基准数据字典
        start_date: 开始日期
        end_date: 结束日期
        benchmark_code: 基准代码

    """
    # 策略净值曲线
    strategy_nav = portfolio_values / portfolio_values[0]
    ax.plot(dates, strategy_nav, linewidth=2, label='Strategy NAV', color='#1f77b4')

    # 基准净值曲线
    benchmark_name = _get_benchmark_name(benchmark_code, use_english=True)
    if benchmark_code in benchmark_data and not benchmark_data[benchmark_code].empty:
        benchmark_df_data = benchmark_data[benchmark_code]
        benchmark_slice = benchmark_df_data.loc[
            (benchmark_df_data.index >= start_date) &
            (benchmark_df_data.index <= end_date)
        ]
        if len(benchmark_slice) > 0:
            benchmark_nav = benchmark_slice['close'] / benchmark_slice['close'].iloc[0]
            ax.plot(benchmark_slice.index[:len(dates)], benchmark_nav[:len(dates)],
                   linewidth=2, label=benchmark_name, color='#ff7f0e', alpha=0.7)

    # 标注买卖点
    buy_dates = dates[daily_buy > 0]
    buy_navs = strategy_nav[daily_buy > 0]
    ax.scatter(buy_dates, buy_navs, marker='^', color='red', s=50, label='Buy', zorder=5)

    sell_dates = dates[daily_sell > 0]
    sell_navs = strategy_nav[daily_sell > 0]
    ax.scatter(sell_dates, sell_navs, marker='v', color='green', s=50, label='Sell', zorder=5)

    ax.set_title('Portfolio Value vs Benchmark', fontsize=14, fontweight='bold')
    ax.set_ylabel('Net Asset Value', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)


def _plot_daily_pnl(ax, dates, daily_pnl):
    """绘制每日盈亏子图

    Args:
        ax: matplotlib axes对象
        dates: 日期数组
        daily_pnl: 每日盈亏数组
    """
    colors = ['red' if pnl >= 0 else 'green' for pnl in daily_pnl]
    ax.bar(dates, daily_pnl, color=colors, alpha=0.7, width=0.8)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_title('Daily P&L', fontsize=14, fontweight='bold')
    ax.set_ylabel('P&L (CNY)', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')


def _plot_trade_amounts(ax, dates, daily_buy, daily_sell):
    """绘制交易金额子图

    Args:
        ax: matplotlib axes对象
        dates: 日期数组
        daily_buy: 每日买入金额
        daily_sell: 每日卖出金额
    """
    width = 0.4
    ax.bar(dates, daily_buy, color='red', alpha=0.7, width=width, label='Buy Amount')
    ax.bar(dates, -daily_sell, color='green', alpha=0.7, width=width, label='Sell Amount')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_title('Daily Buy/Sell Amount', fontsize=14, fontweight='bold')
    ax.set_ylabel('Amount (CNY)', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')


def _plot_positions_value(ax, dates, daily_positions_val):
    """绘制持仓市值子图

    Args:
        ax: matplotlib axes对象
        dates: 日期数组
        daily_positions_val: 每日持仓市值数组
    """
    ax.fill_between(dates, daily_positions_val, alpha=0.3, color='#9467bd')
    ax.plot(dates, daily_positions_val, linewidth=2, color='#9467bd', label='Positions Value')
    ax.set_title('Daily Positions Value', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Value (CNY)', fontsize=12)
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)


def generate_backtest_charts(backtest_stats, start_date, end_date, benchmark_data, chart_filename, benchmark_code='000300.SS'):
    """生成回测图表

    Args:
        backtest_stats: 回测统计数据字典
        start_date: 回测开始日期
        end_date: 回测结束日期
        benchmark_data: 基准数据字典
        chart_filename: 图表文件完整路径
        benchmark_code: 基准代码

    Returns:
        str: 图表文件路径
    """
    # 设置字体 - 使用系统可用字体
    plt.rcParams['font.sans-serif'] = ['Ubuntu', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 验证并提取数据
    dates, portfolio_values, daily_pnl, daily_buy, daily_sell, daily_positions_val = _validate_chart_data(backtest_stats)

    # 创建图表 - 4行1列布局
    fig, axes = plt.subplots(4, 1, figsize=(16, 20), sharex=True)

    # 绘制4个子图
    _plot_nav_curve(axes[0], dates, portfolio_values, daily_buy, daily_sell, benchmark_data, start_date, end_date, benchmark_code)
    _plot_daily_pnl(axes[1], dates, daily_pnl)
    _plot_trade_amounts(axes[2], dates, daily_buy, daily_sell)
    _plot_positions_value(axes[3], dates, daily_positions_val)

    # 设置x轴日期格式
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    # 调整布局
    plt.tight_layout()

    # 自动创建目录
    chart_dir = os.path.dirname(chart_filename)
    os.makedirs(chart_dir, exist_ok=True)

    # 保存图表
    plt.savefig(chart_filename, dpi=150, bbox_inches='tight')
    plt.close()

    return chart_filename


def print_backtest_report(report, log, start_date, end_date, time_str, positions_count):
    """打印回测报告到日志

    Args:
        report: generate_backtest_report返回的报告字典
        log: 日志对象
        start_date: 回测开始日期
        end_date: 回测结束日期
        time_str: 格式化后的耗时字符串（如：3分32秒）
        positions_count: 持仓数量数组
    """
    log.info("")
    log.info("=" * 70)
    log.info(f"回测报告 {start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')} | "
             f"周期: {report['trading_days']}天 | 耗时: {time_str}")
    log.info("=" * 70)

    # 核心指标
    log.info("")
    log.info(f"总收益率: {report['total_return']*100:+.2f}%  |  "
             f"年化收益: {report['annual_return']*100:+.2f}%  |  "
             f"最大回撤: {report['max_drawdown']*100:.2f}%")
    log.info(f"夏普比率: {report['sharpe_ratio']:.3f}  |  "
             f"信息比率: {report['information_ratio']:.3f}  |  "
             f"本金: {report['initial_value']/10000:.0f}万 → {report['final_value']/10000:.1f}万")

    # 基准对比
    log.info("")
    benchmark_name = report.get('benchmark_name', 'Benchmark')
    log.info(f"vs {benchmark_name}: 超额收益 {report['excess_return']*100:+.2f}% | "
             f"Alpha {report['alpha']*100:+.2f}% | Beta {report['beta']:.3f}")

    # 交易统计
    avg_pos = np.mean(positions_count) if len(positions_count) > 0 else 0
    max_pos = np.max(positions_count) if len(positions_count) > 0 else 0
    log.info("")
    log.info(f"盈利天数: {report['win_count']}/{report['trading_days']}天 ({report['win_rate']*100:.1f}%) | "
             f"盈亏比: {report['profit_loss_ratio']:.2f} | "
             f"持仓: {avg_pos:.1f}只(最大{max_pos}只)")

    log.info("=" * 70)
