# -*- coding: utf-8 -*-
"""
基准设置和性能评估策略
展示基准对比和性能分析功能，包含简单交易和双均线两种模式
"""

# 策略函数
def initialize(context):
    """初始化函数"""
    log.info("初始化基准设置和性能评估策略")

    # 设置股票池
    g.security = 'STOCK_A'

    # 设置基准指数
    set_benchmark('BENCHMARK_INDEX')  # 将生成模拟基准数据

    # 策略模式选择：'simple' 或 'ma_cross'
    g.strategy_mode = 'simple'  # 可以改为 'ma_cross' 测试双均线策略

    if g.strategy_mode == 'simple':
        # 简单交易模式参数
        g.trade_count = 0
        g.max_trades = 3
        log.info("使用简单交易模式")
    else:
        # 双均线模式参数
        g.ma_short = 5   # 短期均线
        g.ma_long = 20   # 长期均线
        g.position_ratio = 0.8  # 最大仓位比例
        log.info(f"使用双均线模式 - 短期均线: {g.ma_short}, 长期均线: {g.ma_long}")

    log.info(f"设置股票池: {g.security}")
    log.info(f"设置基准指数: BENCHMARK_INDEX")


def handle_data(context, data):
    """主策略函数 - 支持简单交易和双均线两种模式"""
    security = g.security

    # 检查数据可用性
    if security not in data:
        return

    current_price = data[security]['close']
    log.info(f"当前价格: {current_price:.2f}")

    try:
        if g.strategy_mode == 'simple':
            _handle_simple_trading(context, data, security, current_price)
        else:
            _handle_ma_cross_trading(context, data, security, current_price)
    except Exception as e:
        log.error(f"策略执行出错: {e}")


def _handle_simple_trading(context, data, security, current_price):
    """简单交易模式"""
    # 限制交易次数
    if g.trade_count >= g.max_trades:
        return

    current_position = get_position(security)
    current_shares = current_position['amount'] if current_position else 0

    if g.trade_count == 0:
        # 第一天：买入50%仓位
        target_value = context.portfolio.cash * 0.5
        shares = int(target_value / current_price / 100) * 100
        if shares > 0:
            order_id = order(security, shares)
            if order_id:
                log.info(f"买入 {shares} 股，建立50%仓位")
                g.trade_count += 1

    elif g.trade_count == 1:
        # 第二天：再买入30%仓位
        target_value = context.portfolio.cash * 0.6  # 剩余现金的60%
        shares = int(target_value / current_price / 100) * 100
        if shares > 0:
            order_id = order(security, shares)
            if order_id:
                log.info(f"加仓 {shares} 股，增加30%仓位")
                g.trade_count += 1

    elif g.trade_count == 2 and current_shares > 0:
        # 第三天：卖出部分仓位
        sell_shares = min(500, current_shares)
        order_id = order(security, -sell_shares)
        if order_id:
            log.info(f"减仓 {sell_shares} 股")
            g.trade_count += 1


def _handle_ma_cross_trading(context, data, security, current_price):
    """双均线交叉策略"""
    # 获取历史价格数据计算均线
    hist_data = get_history(max(g.ma_long + 5, 30), '1d', 'close', security)

    if hist_data.empty or len(hist_data) < g.ma_long:
        log.warning("历史数据不足，无法计算均线")
        return

    # 计算移动平均线
    prices = hist_data[security] if security in hist_data.columns else hist_data.iloc[:, 0]
    ma_short = prices.rolling(window=g.ma_short).mean().iloc[-1]
    ma_long = prices.rolling(window=g.ma_long).mean().iloc[-1]

    log.info(f"MA{g.ma_short}: {ma_short:.2f}, MA{g.ma_long}: {ma_long:.2f}")

    # 获取当前持仓
    current_position = get_position(security)
    current_shares = current_position['amount'] if current_position else 0

    # 交易信号判断
    if ma_short > ma_long and current_shares == 0:
        # 金叉买入信号
        max_shares = int(context.portfolio.cash * g.position_ratio / current_price / 100) * 100
        if max_shares > 0:
            order_id = order(security, max_shares)
            if order_id:
                log.info(f"金叉买入信号，买入 {max_shares} 股")

    elif ma_short < ma_long and current_shares > 0:
        # 死叉卖出信号
        order_id = order(security, -current_shares)
        if order_id:
            log.info(f"死叉卖出信号，卖出 {current_shares} 股")


def show_performance_summary(context):
    """显示性能摘要"""
    try:
        # 获取基准收益率
        benchmark_returns = get_benchmark_returns()
        
        # 获取性能摘要
        summary = get_performance_summary(benchmark_returns)
        
        if summary:
            log.info("=== 当前性能摘要 ===")
            log.info(f"总收益率: {summary['total_return']:.2%}")
            log.info(f"年化收益率: {summary['annualized_return']:.2%}")
            log.info(f"夏普比率: {summary['sharpe_ratio']:.3f}")
            log.info(f"最大回撤: {summary['max_drawdown']:.2%}")
            log.info(f"胜率: {summary['win_rate']:.2%}")
            
            if 'alpha' in summary:
                log.info(f"Alpha: {summary['alpha']:.2%}")
                log.info(f"Beta: {summary['beta']:.3f}")
    
    except Exception as e:
        log.warning(f"性能摘要显示失败: {e}")


def before_trading_start(context, data):
    """盘前处理"""
    log.info("盘前准备 - 基准设置和性能评估演示策略")


def after_trading_end(context, data):
    """盘后处理"""
    # 记录当日状态
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    log.info(f"盘后总结 - 总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
    
    # 显示持仓情况
    positions = get_positions()
    if positions:
        for security, position in positions.items():
            if position and position['amount'] > 0:
                pnl_ratio = position['pnl_ratio']
                log.info(f"持仓 {security}: {position['amount']}股, "
                        f"成本价: {position['cost_basis']:.2f}, "
                        f"市值: {position['market_value']:.2f}, "
                        f"盈亏: {pnl_ratio:.2%}")
    else:
        log.info("当前无持仓")
    
    # 在最后一个交易日显示详细性能分析
    # 注意：这里只是演示，实际的详细报告会在回测结束后自动生成
    if hasattr(context, 'current_dt'):
        # 简单判断是否接近结束（这里用日期判断）
        if context.current_dt.month == 1 and context.current_dt.day >= 25:
            log.info("即将完成回测，详细性能报告将在回测结束后自动生成")
