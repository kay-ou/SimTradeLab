# -*- coding: utf-8 -*-
"""
回测统计分析模块

包含收益率、风险指标、交易统计等计算函数，以及图表生成函数
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime


def calculate_returns(portfolio_values):
    """计算收益率指标

    Args:
        portfolio_values: 每日组合价值数组

    Returns:
        dict: 包含total_return, annual_return, daily_returns等
    """
    initial_value = portfolio_values[0]
    final_value = portfolio_values[-1]
    total_return = (final_value - initial_value) / initial_value

    # 每日收益率
    daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

    # 年化收益率（假设252个交易日）
    trading_days = len(portfolio_values)
    annual_return = (final_value / initial_value) ** (252 / trading_days) - 1 if trading_days > 0 else 0

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
            'information_ratio': 0
        }

    # 对齐长度
    min_len = min(len(daily_returns), len(benchmark_daily_returns))
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


def generate_backtest_report(backtest_stats, start_date, end_date, benchmark_df):
    """生成完整的回测报告

    Args:
        backtest_stats: 回测统计数据字典
        start_date: 回测开始日期
        end_date: 回测结束日期
        benchmark_df: 基准数据DataFrame

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

    # 合并所有指标
    report = {
        **returns_metrics,
        **risk_metrics,
        'benchmark_return': benchmark_return,
        'benchmark_annual_return': benchmark_annual_return,
        'excess_return': excess_return,
        **benchmark_metrics,
        **trade_stats
    }

    return report


def generate_backtest_charts(backtest_stats, start_date, end_date, benchmark_data, strategy_name, output_dir):
    """生成回测图表

    Args:
        backtest_stats: 回测统计数据字典
        start_date: 回测开始日期
        end_date: 回测结束日期
        benchmark_data: 基准数据字典
        strategy_name: 策略名称
        output_dir: 输出目录

    Returns:
        str: 图表文件路径
    """
    # 设置字体（使用英文标签避免中文字体问题）
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 提取数据
    dates = np.array(backtest_stats['trade_dates'])
    portfolio_values = np.array(backtest_stats['portfolio_values'])
    daily_pnl = np.array(backtest_stats['daily_pnl'])
    daily_buy = np.array(backtest_stats['daily_buy_amount'])
    daily_sell = np.array(backtest_stats['daily_sell_amount'])
    daily_positions_val = np.array(backtest_stats['daily_positions_value'])

    # 数据验证：确保所有数组长度一致
    if len(daily_positions_val) < len(dates):
        # 如果positions_value数据不足，填充0
        daily_positions_val = np.pad(daily_positions_val, (0, len(dates) - len(daily_positions_val)), constant_values=0)
    if len(daily_pnl) < len(dates):
        daily_pnl = np.pad(daily_pnl, (0, len(dates) - len(daily_pnl)), constant_values=0)
    if len(daily_buy) < len(dates):
        daily_buy = np.pad(daily_buy, (0, len(dates) - len(daily_buy)), constant_values=0)
    if len(daily_sell) < len(dates):
        daily_sell = np.pad(daily_sell, (0, len(dates) - len(daily_sell)), constant_values=0)

    # 创建图表 - 4行1列布局
    fig, axes = plt.subplots(4, 1, figsize=(16, 20), sharex=True)

    # ========== 图1: 资产曲线 vs 基准 + 买卖点标注 ==========
    ax1 = axes[0]

    # 策略净值曲线
    strategy_nav = portfolio_values / portfolio_values[0]
    ax1.plot(dates, strategy_nav, linewidth=2, label='Strategy NAV', color='#1f77b4')

    # 基准净值曲线
    if '000300.SS' in benchmark_data and not benchmark_data['000300.SS'].empty:
        benchmark_df_data = benchmark_data['000300.SS']
        benchmark_slice = benchmark_df_data.loc[
            (benchmark_df_data.index >= start_date) &
            (benchmark_df_data.index <= end_date)
        ]
        if len(benchmark_slice) > 0:
            benchmark_nav = benchmark_slice['close'] / benchmark_slice['close'].iloc[0]
            ax1.plot(benchmark_slice.index[:len(dates)], benchmark_nav[:len(dates)],
                    linewidth=2, label='CSI 300', color='#ff7f0e', alpha=0.7)

    # 标注买卖点
    buy_dates = dates[daily_buy > 0]
    buy_navs = strategy_nav[daily_buy > 0]
    ax1.scatter(buy_dates, buy_navs, marker='^', color='red', s=50, label='Buy', zorder=5)

    sell_dates = dates[daily_sell > 0]
    sell_navs = strategy_nav[daily_sell > 0]
    ax1.scatter(sell_dates, sell_navs, marker='v', color='green', s=50, label='Sell', zorder=5)

    ax1.set_title('Portfolio Value vs Benchmark', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Net Asset Value', fontsize=12)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)

    # ========== 图2: 每日盈亏柱状图 ==========
    ax2 = axes[1]

    colors = ['red' if pnl >= 0 else 'green' for pnl in daily_pnl]
    ax2.bar(dates, daily_pnl, color=colors, alpha=0.7, width=0.8)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_title('Daily P&L', fontsize=14, fontweight='bold')
    ax2.set_ylabel('P&L (CNY)', fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')

    # ========== 图3: 每日买入/卖出金额 ==========
    ax3 = axes[2]

    width = 0.4
    ax3.bar(dates, daily_buy, color='red', alpha=0.7, width=width, label='Buy Amount')
    ax3.bar(dates, -daily_sell, color='green', alpha=0.7, width=width, label='Sell Amount')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax3.set_title('Daily Buy/Sell Amount', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Amount (CNY)', fontsize=12)
    ax3.legend(loc='best', fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')

    # ========== 图4: 每日持仓市值 ==========
    ax4 = axes[3]

    ax4.fill_between(dates, daily_positions_val, alpha=0.3, color='#9467bd')
    ax4.plot(dates, daily_positions_val, linewidth=2, color='#9467bd', label='Positions Value')
    ax4.set_title('Daily Positions Value', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Date', fontsize=12)
    ax4.set_ylabel('Value (CNY)', fontsize=12)
    ax4.legend(loc='best', fontsize=10)
    ax4.grid(True, alpha=0.3)

    # 设置x轴日期格式
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    # 调整布局
    plt.tight_layout()

    # 保存图表
    chart_filename = f'{output_dir}/{strategy_name}/backtest_{start_date.strftime("%y%m%d")}_{end_date.strftime("%y%m%d")}_{datetime.now().strftime("%y%m%d_%H%M%S")}.png'
    plt.savefig(chart_filename, dpi=150, bbox_inches='tight')
    plt.close()  # 关闭图表，释放内存

    return chart_filename


def print_backtest_report(report, log, start_date, end_date, total_elapsed, positions_count):
    """打印回测报告到日志

    Args:
        report: generate_backtest_report返回的报告字典
        log: 日志对象
        start_date: 回测开始日期
        end_date: 回测结束日期
        total_elapsed: 总用时（秒）
        positions_count: 持仓数量数组
    """
    log.info("")
    log.info("=" * 60)
    log.info(f"回测统计报告 {start_date.strftime('%Y%m%d')} - {end_date.strftime('%Y%m%d')} 总用时: {total_elapsed:.0f}秒 ({total_elapsed/60:.1f}分钟)")
    log.info("=" * 60)

    log.info("")
    log.info("【整体表现】")
    log.info(f"  初始资金: {report['initial_value']:,.2f}")
    log.info(f"  最终资金: {report['final_value']:,.2f}")
    log.info(f"  总收益率: {report['total_return']*100:.2f}%")
    log.info(f"  年化收益率: {report['annual_return']*100:.2f}%")
    log.info(f"  最大回撤: {report['max_drawdown']*100:.2f}%")

    log.info("")
    log.info("【基准对比（沪深300）】")
    log.info(f"  基准总收益: {report['benchmark_return']*100:.2f}%")
    log.info(f"  基准年化收益: {report['benchmark_annual_return']*100:.2f}%")
    log.info(f"  超额收益: {report['excess_return']*100:.2f}%")
    log.info(f"  Alpha（年化）: {report['alpha']*100:.2f}%")
    log.info(f"  Beta: {report['beta']:.3f}")

    log.info("")
    log.info("【风险调整指标】")
    log.info(f"  夏普比率: {report['sharpe_ratio']:.3f}")
    log.info(f"  信息比率: {report['information_ratio']:.3f}")

    log.info("")
    log.info("【交易统计】")
    log.info(f"  回测天数: {report['trading_days']} 天")
    log.info(f"  盈利天数: {report['win_count']} 天")
    log.info(f"  亏损天数: {report['lose_count']} 天")
    log.info(f"  胜率: {report['win_rate']*100:.2f}%")
    log.info(f"  盈亏比: {report['profit_loss_ratio']:.2f}")

    if len(positions_count) > 0:
        log.info(f"  平均持仓数: {np.mean(positions_count):.1f} 只")
        log.info(f"  最大持仓数: {np.max(positions_count)} 只")
    else:
        log.info("  平均持仓数: 0 只")
        log.info("  最大持仓数: 0 只")

    log.info("")
    log.info("【每日收益率统计】")
    if len(report['daily_returns']) > 0:
        log.info(f"  平均: {np.mean(report['daily_returns'])*100:.2f}%")
        log.info(f"  标准差: {np.std(report['daily_returns'])*100:.2f}%")
        log.info(f"  最大单日收益: {np.max(report['daily_returns'])*100:.2f}%")
        log.info(f"  最大单日亏损: {np.min(report['daily_returns'])*100:.2f}%")

        # 计算日胜率
        daily_win_rate = np.sum(report['daily_returns'] > 0) / len(report['daily_returns'])
        log.info(f"  日胜率: {daily_win_rate*100:.2f}%")
    else:
        log.info("  无数据")
