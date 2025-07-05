# -*- coding: utf-8 -*-
"""
策略性能分析模块
"""
import pandas as pd
import numpy as np
from .logger import log


def calculate_portfolio_returns(engine):
    """
    计算投资组合收益率序列

    Args:
        engine: 回测引擎实例

    Returns:
        pandas.Series: 投资组合收益率序列
    """
    if not engine.portfolio_history:
        log.warning("没有投资组合历史数据")
        return pd.Series()

    if len(engine.portfolio_history) < 2:
        log.warning(f"投资组合历史数据不足（只有{len(engine.portfolio_history)}个数据点），至少需要2个数据点才能计算收益率")
        return pd.Series()

    # 转换为DataFrame
    portfolio_df = pd.DataFrame(engine.portfolio_history)
    portfolio_df.set_index('datetime', inplace=True)

    # 计算收益率
    returns = portfolio_df['total_value'].pct_change().dropna()

    if returns.empty:
        log.warning("计算出的收益率序列为空，可能是因为投资组合价值没有变化")

    return returns


def calculate_performance_metrics(engine, benchmark_returns=None):
    """
    计算策略性能指标
    
    Args:
        engine: 回测引擎实例
        benchmark_returns: 基准收益率序列
    
    Returns:
        dict: 性能指标字典
    """
    portfolio_returns = calculate_portfolio_returns(engine)

    if portfolio_returns.empty:
        if not engine.portfolio_history:
            log.warning("无法计算性能指标：没有投资组合历史数据")
        elif len(engine.portfolio_history) < 2:
            log.warning(f"无法计算性能指标：数据点不足（{len(engine.portfolio_history)}个），建议增加回测期间")
        else:
            log.warning("无法计算性能指标：投资组合收益率为空")
        return {}
    
    # 基础指标
    total_return = (engine.context.portfolio.total_value / engine.initial_cash) - 1
    trading_days = len(portfolio_returns)
    annualized_return = (1 + total_return) ** (252 / trading_days) - 1 if trading_days > 0 else 0
    
    # 波动率指标
    volatility = portfolio_returns.std() * np.sqrt(252)  # 年化波动率
    
    # 夏普比率（假设无风险利率为3%）
    risk_free_rate = 0.03
    excess_returns = portfolio_returns - risk_free_rate / 252
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0
    
    # 最大回撤
    portfolio_df = pd.DataFrame(engine.portfolio_history)
    portfolio_df.set_index('datetime', inplace=True)
    cumulative_returns = (1 + portfolio_returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # 胜率统计
    positive_days = (portfolio_returns > 0).sum()
    win_rate = positive_days / len(portfolio_returns) if len(portfolio_returns) > 0 else 0
    
    # 基本性能指标
    metrics = {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'trading_days': trading_days,
        'total_trades': len(engine.context.blotter.get_all_trades()),
        'final_value': engine.context.portfolio.total_value,
        'initial_value': engine.initial_cash
    }
    
    # 如果有基准数据，计算相对指标
    if benchmark_returns is not None and not benchmark_returns.empty:
        # 对齐时间序列
        aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join='inner')
        
        if not aligned_portfolio.empty and not aligned_benchmark.empty:
            # 基准指标
            benchmark_total_return = (1 + aligned_benchmark).prod() - 1
            benchmark_annualized_return = (1 + benchmark_total_return) ** (252 / len(aligned_benchmark)) - 1
            benchmark_volatility = aligned_benchmark.std() * np.sqrt(252)
            
            # 相对指标
            alpha = annualized_return - benchmark_annualized_return
            
            # Beta计算
            covariance = np.cov(aligned_portfolio, aligned_benchmark)[0, 1]
            benchmark_variance = np.var(aligned_benchmark)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            
            # 信息比率
            active_returns = aligned_portfolio - aligned_benchmark
            tracking_error = active_returns.std() * np.sqrt(252)
            information_ratio = alpha / tracking_error if tracking_error > 0 else 0
            
            # 更新指标字典
            metrics.update({
                'benchmark_total_return': benchmark_total_return,
                'benchmark_annualized_return': benchmark_annualized_return,
                'benchmark_volatility': benchmark_volatility,
                'alpha': alpha,
                'beta': beta,
                'information_ratio': information_ratio,
                'tracking_error': tracking_error
            })
    
    return metrics


def print_performance_report(engine, benchmark_returns=None):
    """
    打印性能分析报告
    
    Args:
        engine: 回测引擎实例
        benchmark_returns: 基准收益率序列
    """
    metrics = calculate_performance_metrics(engine, benchmark_returns)
    
    if not metrics:
        log.warning("无法生成性能报告")
        return
    
    print("\n" + "=" * 60)
    print("策略性能分析报告")
    print("=" * 60)
    
    # 基础收益指标
    print("\n📈 收益指标:")
    print(f"  总收益率:     {metrics['total_return']:.2%}")
    print(f"  年化收益率:   {metrics['annualized_return']:.2%}")
    print(f"  初始资金:     {metrics['initial_value']:,.2f}")
    print(f"  最终资金:     {metrics['final_value']:,.2f}")
    
    # 风险指标
    print("\n📊 风险指标:")
    print(f"  年化波动率:   {metrics['volatility']:.2%}")
    print(f"  夏普比率:     {metrics['sharpe_ratio']:.3f}")
    print(f"  最大回撤:     {metrics['max_drawdown']:.2%}")
    print(f"  胜率:         {metrics['win_rate']:.2%}")
    
    # 交易统计
    print("\n📋 交易统计:")
    print(f"  交易天数:     {metrics['trading_days']}天")
    print(f"  总交易次数:   {metrics['total_trades']}次")
    
    # 基准对比（如果有基准数据）
    if 'benchmark_total_return' in metrics:
        print("\n📊 基准对比:")
        print(f"  基准总收益率: {metrics['benchmark_total_return']:.2%}")
        print(f"  基准年化收益: {metrics['benchmark_annualized_return']:.2%}")
        print(f"  基准波动率:   {metrics['benchmark_volatility']:.2%}")
        print(f"  Alpha:        {metrics['alpha']:.2%}")
        print(f"  Beta:         {metrics['beta']:.3f}")
        print(f"  信息比率:     {metrics['information_ratio']:.3f}")
        print(f"  跟踪误差:     {metrics['tracking_error']:.2%}")
        
        # 超额收益
        excess_return = metrics['total_return'] - metrics['benchmark_total_return']
        print(f"  超额收益:     {excess_return:.2%}")
    
    print("\n" + "=" * 60)


def get_performance_summary(engine, benchmark_returns=None):
    """
    获取性能摘要（用于策略中调用）

    Args:
        engine: 回测引擎实例
        benchmark_returns: 基准收益率序列

    Returns:
        dict: 性能摘要字典
    """
    metrics = calculate_performance_metrics(engine, benchmark_returns)

    # 返回关键指标的简化版本
    summary = {
        'total_return': metrics.get('total_return', 0),
        'annualized_return': metrics.get('annualized_return', 0),
        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
        'max_drawdown': metrics.get('max_drawdown', 0),
        'win_rate': metrics.get('win_rate', 0)
    }

    if 'alpha' in metrics:
        summary['alpha'] = metrics['alpha']
        summary['beta'] = metrics['beta']

    return summary


# 全局引擎引用（用于策略中的无参数调用）
_current_engine = None


def _set_current_engine(engine):
    """设置当前引擎（内部使用）"""
    global _current_engine
    _current_engine = engine


def get_performance_summary_standalone(benchmark_returns=None):
    """
    获取性能摘要（策略中无参数调用版本）

    Args:
        benchmark_returns: 基准收益率序列

    Returns:
        dict: 性能摘要字典
    """
    if _current_engine is None:
        log.warning("引擎未设置，无法获取性能摘要")
        return {}

    return get_performance_summary(_current_engine, benchmark_returns)
