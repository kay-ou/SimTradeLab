# -*- coding: utf-8 -*-
"""
AI驱动的多因子策略 V3 - 单股票独立管理模式

核心理念：
1. 去除"调仓日"概念：每天独立运行，按需预测
2. 单股票独立管理：每个股票根据自己的持有天数决定生命周期
3. 按需AI预测：只在有空位时运行预测（满仓时零开销）
4. 自然风控：移除强制清仓逻辑，让止损止盈自然处理

模型性能指标（v3）：
- 测试集IC: 0.0879（具有预测能力）
- 测试集多空收益: 1.35%（优秀）
- 预测周期: 5天
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import pickle

# ==================== 因子计算常量（与训练代码保持一致） ====================
SMALL_CAP_THRESHOLD = 50.0      # 小市值阈值（亿元）
SIZE_REFERENCE_CAP = 100.0      # 基准市值（亿元）

# 策略初始化
def initialize(context):
    """策略初始化 - 单股票独立管理模式"""
    # ==================== 策略核心参数 ====================
    g.max_positions = 10             # 最大持仓数量（每只股票 1/10 = 10% 资金）

    # ==================== 风险控制参数 ====================
    g.max_hold_days = 5              # 最大持有天数（从模型元数据加载，默认5天）

    # 止损止盈开关
    g.enable_stop_loss = False       # 是否启用止损（关闭后只靠持有到期卖出）
    g.enable_take_profit = False     # 是否启用移动止盈（关闭后只靠持有到期卖出）

    # 预测驱动的止损止盈参数
    g.stop_loss_negative_pred = -0.01  # 预测为负时止损-1%
    g.stop_loss_positive_pred = -0.03  # 预测为正时止损-3%
    g.take_profit_trigger_buffer = 0.08  # 止盈触发=预测+8%
    g.take_profit_drawdown = 0.03  # 最高点回撤3%触发卖出

    # ==================== 选股参数 ====================
    g.min_market_cap = 50e8          # 最小市值（50亿）
    g.max_market_cap = 1500e8        # 最大市值（1500亿 - 中盘股）

    # ==================== 模型参数 ====================
    g.model_path = get_research_path()+'strategies/ptrade_factor_model.pkl'
    g.model_metadata = {}
    g.feature_order = []  # 从模型属性加载

    # ==================== 策略状态 ====================
    g.state = {
        'hold_days': defaultdict(int),
        'highest_prices': defaultdict(float),
        'entry_prices': defaultdict(float),  # 真实买入价（不受复权影响）
        'in_take_profit_mode': defaultdict(bool),  # 是否进入止盈模式
        'buy_predictions': {},  # 买入时的预测收益
        'model_ready': False,
        'market_regime': 'UNKNOWN',  # 市场状态：震荡市/牛市/熊市
    }

    # 初始化交易列表
    g.to_buy = []
    g.to_sell = {}
    g.stock_scores = {}

    # 设置基准指数
    set_benchmark('000300.SS')

    # 日志记录
    log.info("="*60)
    log.info("AI驱动多因子策略 V3（单股票独立管理模式）")
    log.info("="*60)
    log.info("【策略参数】")
    log.info("  最大持仓数: {} 只".format(g.max_positions))
    log.info("  选股模式: 按需预测（有空位才运行AI）")
    log.info("  仓位管理: 等权重分配（每只 {:.1%}）".format(1.0 / g.max_positions))
    log.info("【风控参数】")
    log.info("  持有策略: 严格持有{}天（与训练逻辑一致）".format(g.max_hold_days))
    log.info("  止损开关: {}".format("开启" if g.enable_stop_loss else "关闭"))
    if g.enable_stop_loss:
        log.info("    预测驱动止损: 负预测{:.1%} | 正预测{:.1%}".format(
            g.stop_loss_negative_pred, g.stop_loss_positive_pred))
    log.info("  止盈开关: {}".format("开启" if g.enable_take_profit else "关闭"))
    if g.enable_take_profit:
        log.info("    移动止盈: 触发阈值=预测+{:.1%} | 回撤止盈{:.1%}".format(
            g.take_profit_trigger_buffer, g.take_profit_drawdown))
        log.info("    止盈模式: 忽略持有天数限制")
    log.info("【选股范围】")
    log.info("  市值范围: {:.0f}亿 - {:.0f}亿".format(
        g.min_market_cap / 1e8, g.max_market_cap / 1e8))
    log.info("="*60)

    # 加载因子模块
    log.info("加载因子计算模块...")
    try:
        load_factor_modules()
    except Exception as e:
        log.error("加载因子模块失败: {}".format(str(e)))
        raise

    # 加载模型
    log.info("尝试加载AI模型...")
    try:
        load_trained_model()
    except Exception as e:
        log.error("加载模型失败: {}".format(str(e)))
        log.warning("将使用备用评分方案")
        g.state['model_ready'] = False

    # 设置状态持久化路径（模仿shadow_strategy）
    if is_trade():
        pickle_path = get_research_path() + 'pickles_trade/'
    else:
        pickle_path = get_research_path() + 'pickles_test/'

    g.strategy_state_path = pickle_path + 'ai_multi_factor_state.pkl'

    # 回测模式下清空状态文件，实盘模式下保留
    if not is_trade():
        clear_file(g.strategy_state_path)

    # ========== 实盘模式：在开盘时买入 ==========
    # 实盘在09:25集合竞价执行买入
    if is_trade():
        run_daily(context, buy_stocks, time='09:25')


def cleanup_pending_orders():
    """清理未完成的待处理订单"""
    if g.to_buy:
        log.info("【清理订单】清空未完成的买入计划: {}".format(g.to_buy))
        g.to_buy = []


def check_stop_loss_take_profit(context, data):
    """检查预测驱动的止损止盈条件"""
    # 如果止损和止盈都关闭，直接返回
    if not g.enable_stop_loss and not g.enable_take_profit:
        return

    for stock, position in context.portfolio.positions.items():
        if position.amount <= 0:
            continue

        # 跳过已经在待卖列表中的股票
        if stock in g.to_sell:
            continue

        entry_price = g.state['entry_prices'].get(stock)
        if entry_price is None:
            continue

        predicted_return = g.state.get('buy_predictions', {}).get(stock, 0)
        current_price = data[stock]['close']
        actual_return = (current_price - entry_price) / entry_price

        # 1. 检查止损（仅当开关开启时）
        if g.enable_stop_loss:
            hold_days = g.state['hold_days'].get(stock, 0)
            if predicted_return < 0 and actual_return <= g.stop_loss_negative_pred:
                reason = "负预测止损(预测{:.2%}, 实际{:.2%}, 持仓{}天)".format(predicted_return, actual_return, hold_days)
                add_to_sell_list(stock, reason, position)
                log.info("【止损】{} | {}".format(stock, reason))
                continue
            elif predicted_return >= 0 and actual_return <= g.stop_loss_positive_pred:
                reason = "正预测止损(预测{:.2%}, 实际{:.2%}, 持仓{}天)".format(predicted_return, actual_return, hold_days)
                add_to_sell_list(stock, reason, position)
                log.info("【止损】{} | {}".format(stock, reason))
                continue

        # 2. 检查止盈触发（仅当开关开启时）
        if g.enable_take_profit:
            take_profit_target = predicted_return + g.take_profit_trigger_buffer
            if actual_return >= take_profit_target and not g.state['in_take_profit_mode'].get(stock, False):
                g.state['in_take_profit_mode'][stock] = True
                update_highest_price(stock, current_price)
                log.info("【进入止盈模式】{} | 预测{:.2%} | 当前{:.2%} | 目标{:.2%}".format(
                    stock, predicted_return, actual_return, take_profit_target))

            # 3. 检查止盈回撤(进入止盈模式后,等待最高点回撤3%)
            if g.state['in_take_profit_mode'].get(stock, False):
                # 更新最高价
                highest = update_highest_price(stock, current_price)
                drawdown = (current_price - highest) / highest

                if drawdown <= -g.take_profit_drawdown:
                    peak_return = (highest - entry_price) / entry_price
                    hold_days = g.state['hold_days'].get(stock, 0)
                    reason = "移动止盈(预测{:.2%}, 最高{:.2%}, 当前{:.2%}, 回撤{:.2%}, 持仓{}天)".format(
                        predicted_return, peak_return, actual_return, drawdown, hold_days)
                    add_to_sell_list(stock, reason, position)
                    log.info("【止盈】{} | {}".format(stock, reason))


def check_and_sell_expired_holdings(context, data):
    """检查并卖出持有到期的股票（≥max_hold_days）"""
    current_positions = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]

    for stock in current_positions:
        hold_days = g.state['hold_days'].get(stock, 0)

        # 跳过已经在待卖列表中的股票
        if stock in g.to_sell:
            continue

        # **关键修改：止盈模式下完全忽略持有天数限制（仅当止盈开关开启时）**
        if g.enable_take_profit and g.state['in_take_profit_mode'].get(stock, False):
            continue

        # 检查持有到期
        if hold_days >= g.max_hold_days:
            position = context.portfolio.positions[stock]
            # 不再计算收益，只记录持有天数
            reason = "持有到期({} 天)".format(hold_days)
            add_to_sell_list(stock, reason, position)
            log.info("【持有到期】{} | {}".format(stock, reason))


def select_stocks_to_buy(current_positions, top_stocks):
    """
    选择需要买入的股票，返回股票列表

    参数:
        current_positions: 当前持仓股票列表
        top_stocks: [(stock, score), ...] 排序后的候选股票
    """
    available_slots = max(0, g.max_positions - len(current_positions) + len(g.to_sell))

    stocks_to_buy = []
    for stock, _ in top_stocks:
        if stock not in current_positions and stock not in g.to_sell:
            stocks_to_buy.append(stock)
            if len(stocks_to_buy) >= available_slots:
                break

    return stocks_to_buy


def before_trading_start(context, data):
    """盘前处理入口 - 按需选股和预测"""
    # 加载策略状态（从硬盘恢复hold_days和highest_prices）
    load_strategy_state(context)

    # ========== 关键修复：将持仓股票加入股票池（确保data[stock]有效） ==========
    current_positions = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]
    if current_positions:
        set_universe(current_positions)
        log.info("【股票池】已将 {} 只持仓股票加入股票池".format(len(current_positions)))

    # ========== 关键修复：盘前检查止损止盈（确保每天都检查） ==========
    if current_positions:
        log.info("【盘前止损检查】开始检查 {} 只持仓股票".format(len(current_positions)))
        check_stop_loss_take_profit(context, data)
        log.info("【盘前止损检查】完成，待卖出: {} 只".format(len(g.to_sell)))

    # 检查持有到期（会跳过止盈模式的股票）
    check_and_sell_expired_holdings(context, data)

    # 清理未完成的订单
    cleanup_pending_orders()

    # 计算可用仓位
    available_slots = g.max_positions - len(current_positions) + len(g.to_sell)

    # 优化：只有空位>=3时才运行AI预测（节省计算资源）
    if available_slots < 3:
        log.info("可用仓位不足3只({}/{}只，待卖{}只)，跳过AI预测".format(
            len(current_positions), g.max_positions, len(g.to_sell)))
        return

    # ========== 检查市场状态（必须是震荡市才能买入） ==========
    try:
        benchmark = '000300.SS'
        benchmark_data = get_history(65, '1d', ['close'], [benchmark],
                                    fq='pre', include=False, is_dict=True)

        if benchmark_data and benchmark in benchmark_data:
            benchmark_closes = np.array(benchmark_data[benchmark]['close'], dtype=float)
            market_return_20d = (benchmark_closes[-1] - benchmark_closes[-21]) / benchmark_closes[-21] if len(benchmark_closes) > 21 else 0
            market_return_60d = (benchmark_closes[-1] - benchmark_closes[-61]) / benchmark_closes[-61] if len(benchmark_closes) > 61 else market_return_20d * 2.5
            benchmark_returns = np.diff(benchmark_closes) / benchmark_closes[:-1]
            market_vol = np.std(benchmark_returns[-20:]) if len(benchmark_returns) >= 20 else 0

            # 使用训练时的逻辑判断市场状态
            if market_return_60d < -0.10 or (market_return_20d < -0.05 and market_vol > 0.025):
                market_trend_state = -1  # 熊市
            elif market_return_60d > 0.15 and market_vol < 0.020:
                market_trend_state = 1   # 牛市
            else:
                market_trend_state = 0   # 震荡市

            # 映射市场状态到中文标签
            market_regime_map = {-1: '熊市', 0: '震荡市', 1: '牛市'}
            g.state['market_regime'] = market_regime_map[market_trend_state]

            # 如果不是震荡市，跳过买入（模型只在震荡市训练）
            if market_trend_state != 0:
                log.info("【市场状态过滤】当前市场: {} (60日: {:.1%}, 20日: {:.1%}, 波动率: {:.4f})".format(
                    g.state['market_regime'], market_return_60d, market_return_20d, market_vol))
                log.info("模型只在震荡市训练，跳过买入")
                return
        else:
            log.warning("无法获取市场数据，跳过买入")
            return
    except Exception as e:
        log.warning("市场状态检查失败: {}，跳过买入".format(str(e)))
        return

    log.info("="*60)
    log.info("开始选股流程 - {} | 可用仓位: {} 只 | 市场: {}".format(
        context.blotter.current_dt.date(), available_slots, g.state['market_regime']))
    log.info("="*60)

    # 获取过滤后的股票池
    stock_pool = get_filtered_stock_pool(context, data)
    if not stock_pool:
        log.warning("无符合条件的股票池")
        return

    log.info("候选股票池: {} 只".format(len(stock_pool)))

    # 使用AI模型预测股票表现
    stock_predictions = predict_stock_performance(stock_pool, context)
    if not stock_predictions:
        log.error("="*60)
        log.error("【AI预测失败】本次跳过买入")
        log.error("  请检查：")
        log.error("    1) 模型文件是否存在: {}".format(g.model_path))
        log.error("    2) 特征顺序是否匹配")
        log.error("    3) 依赖版本是否正确（xgboost, numpy等）")
        log.error("="*60)
        g.stock_scores = {}
        g.to_buy = []
        return

    g.stock_scores = stock_predictions
    log.info("AI模型成功预测 {} 只股票".format(len(g.stock_scores)))

    # 【诊断】输出预测细节
    log.info("【诊断】当前交易日: {}".format(context.blotter.current_dt.date()))
    log.info("【诊断】查询基本面数据日期: {}".format(context.previous_date))

    # ========== 检查预测值分布（仅记录，不过滤） ==========
    pred_values = list(g.stock_scores.values())
    pred_mean = np.mean(pred_values)
    pred_max = np.max(pred_values)

    log.info("预测值分布: min={:.2%}, max={:.2%}, mean={:.2%}".format(
        np.min(pred_values), pred_max, pred_mean))

    # 按预测评分排序
    sorted_stocks = sorted(g.stock_scores.items(), key=lambda x: x[1], reverse=True)

    # ========== 关键优化：从Top20%中随机选股，提高稳定性 ==========
    # 原因：IC=0.12的排序能力对Top20%有效，但对Top10（0.2%）失效
    # 从Top20%随机选择可以获得接近验证集Q5的期望收益
    top_20_percent_count = max(int(len(sorted_stocks) * 0.2), available_slots)
    top_20_percent_stocks = sorted_stocks[:top_20_percent_count]

    if len(top_20_percent_stocks) == 0:
        log.warning("没有预测结果，本次跳过买入")
        g.to_buy = []
        return

    # 从Top20%中随机选择N只（N = 可用仓位数）
    import random
    random.seed(int(context.current_dt.timestamp()))  # 用时间戳做种子，保证可重复
    top_stocks = random.sample(top_20_percent_stocks, min(available_slots, len(top_20_percent_stocks)))

    log.info("【选股策略】从预测值Top20%（{} 只）中随机选择 {} 只".format(
        len(top_20_percent_stocks), len(top_stocks)))

    # 输出实际选中的股票信息
    log.info("本次选中 {} 只股票:".format(len(top_stocks)))
    for i, (stock, score) in enumerate(sorted(top_stocks, key=lambda x: x[1], reverse=True)[:10], 1):
        log.info("  {}. {} - 预测收益: {:.2%}".format(i, stock, score))

    # 选择需要买入的股票
    g.to_buy = select_stocks_to_buy(current_positions, top_stocks)

    # ========== 关键修复：将候选买入股票也加入股票池 ==========
    if g.to_buy:
        # 合并当前持仓和候选买入股票，统一更新股票池
        all_active_stocks = list(set(current_positions + g.to_buy))
        set_universe(all_active_stocks)
        log.info("【股票池】已更新股票池: {} 只持仓 + {} 只候选 = {} 只总计".format(
            len(current_positions), len(g.to_buy), len(all_active_stocks)))

    log.info("【交易计划】")
    log.info("  当前持仓: {} 只".format(len(current_positions)))
    log.info("  计划卖出: {} 只".format(len(g.to_sell)))
    log.info("  计划买入: {} 只".format(len(g.to_buy)))
    log.info("  市场状态: {}".format(g.state['market_regime']))
    log.info("="*60)


def handle_data(context, data):
    """交易逻辑实现"""
    # ========== 盘中再次检查止损（使用当日实时价格，更精确） ==========
    current_positions = [stock for stock, pos in context.portfolio.positions.items() if pos.amount > 0]
    if current_positions:
        check_stop_loss_take_profit(context, data)

    # 再检查持有到期(会跳过止盈模式的股票)
    check_and_sell_expired_holdings(context, data)

    # 处理卖出逻辑
    sell_stocks(context)

    # 处理买入逻辑
    buy_stocks(context)

    # 确认订单状态（取消超时订单、确认买卖成交）
    cancel_stale_orders(context)
    finalize_sells(context, data)
    finalize_buys(context)


# ==================== 模型加载和预测函数 ====================

def load_trained_model():
    """加载预训练的AI模型 - 从 pickle 文件加载（兼容 xgboost 0.6a2）"""
    try:
        import pickle
        log.info("加载模型: {}".format(g.model_path))

        # 从 pickle 加载模型包
        with open(g.model_path, 'rb') as f:
            model_package = pickle.load(f)

        # 提取各个组件
        g.model = model_package.get('model')
        g.feature_order = model_package.get('feature_order', [])
        g.factor_importance = model_package.get('factor_importance', {})
        scaler_params = model_package.get('scaler')
        metadata = model_package.get('metadata', {})

        log.info("✓ 模型加载成功")

        # 加载 RobustScaler 参数（list → numpy array）
        if scaler_params and 'center_' in scaler_params and 'scale_' in scaler_params:
            g.scaler_center = np.array(scaler_params['center_'])
            g.scaler_scale = np.array(scaler_params['scale_'])
            log.info("✓ RobustScaler 参数加载成功")
        else:
            g.scaler_center = None
            g.scaler_scale = None
            log.warning("  警告: 模型中未包含 RobustScaler 参数")

        # 加载元数据并设置策略参数
        metadata = model_package.get('metadata', {})
        g.feature_lookback = metadata.get('feature_lookback', 60)

        # ========== 关键修复：加载归一化元数据 ==========
        normalization = model_package.get('normalization', {'enabled': False})

        g.model_metadata = {
            'predict_days': g.max_hold_days,
            'feature_lookback': g.feature_lookback,
            'save_time': metadata.get('save_time', 'unknown'),
            'xgb_version': metadata.get('xgb_version', 'unknown'),
            'normalization': normalization  # ← 新增
        }

        log.info("✓ 模型元数据加载成功")
        log.info("  预测周期: {} 天（持有到期自动卖出）".format(g.max_hold_days))
        log.info("  特征回看期: {} 天".format(g.feature_lookback))
        log.info("  特征数量: {}".format(len(g.feature_order)))
        log.info("  保存时间: {}".format(g.model_metadata['save_time']))
        log.info("  XGBoost版本: {}".format(g.model_metadata['xgb_version']))

        # 输出归一化信息
        if normalization.get('enabled'):
            log.info("  目标值归一化: {}".format(normalization.get('method')))
            log.info("    全局均值: {:.4f} ({:.2f}%)".format(
                normalization.get('global_mean', 0),
                normalization.get('global_mean', 0) * 100
            ))
            log.info("    全局标准差: {:.4f} ({:.2f}%)".format(
                normalization.get('global_std', 1),
                normalization.get('global_std', 1) * 100
            ))
        else:
            log.info("  目标值归一化: 未启用")

        # 输出Top重要特征
        if g.factor_importance:
            log.info("  Top 5 重要特征:")
            sorted_features = sorted(g.factor_importance.items(),
                                    key=lambda x: x[1], reverse=True)[:5]
            for feat, imp in sorted_features:
                log.info("    - {}: {:.4f}".format(feat, imp))
        else:
            log.warning("  未获取到特征重要性信息")

        # 更新策略状态
        g.state['model_ready'] = True

        log.info("✓ 模型完全加载成功")

    except Exception as e:
        log.error("加载模型失败: {}".format(str(e)))
        import traceback
        log.error("详细错误: {}".format(traceback.format_exc()))
        raise


def predict_stock_performance(stock_list, context):
    """使用AI模型预测股票表现 - 批量优化版"""
    if not g.state['model_ready'] or 'model' not in dir(g):
        return None

    try:
        log.info("开始批量数据准备（候选股票: {} 只）...".format(len(stock_list)))

        # ========== 批量获取基本面数据（一次性查询所有需要的字段） ==========
        fundamentals_cache = {}
        batch_size = 100  # 增加批次大小到100，减少查询次数

        try:
            log.info("批量获取基本面数据（每批{}只）...".format(batch_size))

            # 定义所有需要的字段（根据docs/Ptrade财务数据API.md文档确认）
            valuation_fields = [
                'total_value', 'pe_ttm', 'pb', 'ps_ttm', 'pcf'
            ]

            profit_ability_fields = [
                'roe', 'roe_ttm', 'roa', 'roa_ttm', 'roic', 'roa_ebit_ttm',
                'gross_income_ratio', 'gross_income_ratio_ttm',
                'net_profit_ratio', 'net_profit_ratio_ttm'
            ]

            growth_ability_fields = [
                'operating_revenue_grow_rate', 'net_profit_grow_rate',
                'np_parent_company_yoy', 'basic_eps_yoy', 'total_asset_grow_rate'
            ]

            operating_ability_fields = [
                'total_asset_turnover_rate', 'current_assets_turnover_rate',
                'inventory_turnover_rate', 'accounts_receivables_turnover_rate'
            ]

            debt_paying_ability_fields = [
                'current_ratio', 'quick_ratio', 'debt_equity_ratio', 'interest_cover'
            ]

            # 合并循环：一次遍历批次，查询所有5个表（减少循环开销）
            fundamental_tables = [
                ('valuation', valuation_fields),
                ('profit_ability', profit_ability_fields),
                ('growth_ability', growth_ability_fields),
                ('operating_ability', operating_ability_fields),
                ('debt_paying_ability', debt_paying_ability_fields)
            ]

            for i in range(0, len(stock_list), batch_size):
                batch = stock_list[i:i+batch_size]

                # 对当前批次查询所有5个表
                for table_name, fields in fundamental_tables:
                    batch_data = get_fundamentals(
                        batch, table_name, fields, context.previous_date
                    )

                    if batch_data is not None and not batch_data.empty:
                        for stock in batch:
                            if stock not in fundamentals_cache:
                                fundamentals_cache[stock] = {}
                            if stock in batch_data.index:
                                for field in fields:
                                    fundamentals_cache[stock][field] = batch_data.loc[stock, field]

            log.info("✓ 批量获取基本面数据完成（获取 {} 只股票）".format(len(fundamentals_cache)))
        except Exception as e:
            log.warning("批量获取基本面数据失败: {}，将使用默认值".format(str(e)))

        # ========== 获取市场基准数据（一次性，所有股票共享） ==========
        market_sentiment = None
        try:
            benchmark = '000300.SS'
            benchmark_data = get_history(65, '1d', ['close'], [benchmark],
                                        fq='pre', include=False, is_dict=True)

            if benchmark_data and benchmark in benchmark_data:
                benchmark_closes = np.array(benchmark_data[benchmark]['close'], dtype=float)

                market_return_5d = (benchmark_closes[-1] - benchmark_closes[-6]) / benchmark_closes[-6] if len(benchmark_closes) > 6 else 0
                market_return_20d = (benchmark_closes[-1] - benchmark_closes[-21]) / benchmark_closes[-21] if len(benchmark_closes) > 21 else 0
                market_return_60d = (benchmark_closes[-1] - benchmark_closes[-61]) / benchmark_closes[-61] if len(benchmark_closes) > 61 else market_return_20d * 2.5
                benchmark_returns = np.diff(benchmark_closes) / benchmark_closes[:-1]
                market_volatility = np.std(benchmark_returns[-20:]) if len(benchmark_returns) >= 20 else 0

                market_sentiment = {
                    'market_return_5d': market_return_5d,
                    'market_return_20d': market_return_20d,
                    'market_return_60d': market_return_60d,
                    'market_volatility': market_volatility,
                    'advance_decline_ratio': 0,
                    'market_regime': 1.0 if market_return_20d > 0.05 else (-1.0 if market_return_20d < -0.05 else 0.0),
                    'market_trend_strength': abs(market_return_20d)
                }

            log.info("✓ 获取市场情绪数据完成")
        except Exception:
            log.warning("获取市场情绪数据失败，将使用默认值")

        # ========== 批量获取价格数据（性能优化） ==========
        price_data_cache = {}
        batch_size = 200  # 增加到200，减少查询次数

        try:
            log.info("批量获取价格数据（每批{}只）...".format(batch_size))

            for i in range(0, len(stock_list), batch_size):
                batch = stock_list[i:i+batch_size]

                # 修复：获取额外30天数据，与训练时一致（避免因子计算时数据不足）
                # 训练时使用 FEATURE_LOOKBACK + 30 天，确保60日因子有足够数据
                batch_price_data = get_history(
                    g.feature_lookback + 30, '1d',  # 60 + 30 = 90天
                    ['close', 'volume', 'high', 'low', 'open'],
                    batch, fq='pre', include=False, is_dict=True
                )

                if batch_price_data:
                    # 合并到缓存
                    price_data_cache.update(batch_price_data)

            log.info("✓ 批量获取价格数据完成（获取 {} 只股票）".format(len(price_data_cache)))
        except Exception as e:
            log.warning("批量获取价格数据失败: {}，将跳过预测".format(str(e)))
            return None

        # ========== 第一阶段：收集所有股票的市值并计算排名 ==========
        log.info("开始收集市值数据并计算排名...")
        window_market_caps = {}
        for stock in stock_list:
            if stock in fundamentals_cache:
                fundamentals = fundamentals_cache[stock]
                if 'total_value' in fundamentals and fundamentals['total_value']:
                    market_cap = fundamentals['total_value'] / 1e8  # 转换为亿元
                    if market_cap > 0 and np.isfinite(market_cap):
                        window_market_caps[stock] = market_cap

        # 计算市值排名（百分位，0=最小市值，1=最大市值）
        market_cap_ranks = {}
        if len(window_market_caps) > 1:
            sorted_stocks = sorted(window_market_caps.items(), key=lambda x: x[1])
            for rank_idx, (stock, _) in enumerate(sorted_stocks):
                market_cap_ranks[stock] = rank_idx / (len(sorted_stocks) - 1)  # 0-1之间

        log.info("✓ 市值排名计算完成: {} 只股票".format(len(market_cap_ranks)))

        # ========== 批量获取行业信息（性能优化：避免逐个查询） ==========
        log.info("批量获取行业信息...")
        industry_info_cache = {}
        try:
            # 分批获取行业信息（避免API超时）
            batch_size_industry = 200
            for i in range(0, len(stock_list), batch_size_industry):
                batch = stock_list[i:i+batch_size_industry]
                for stock in batch:
                    try:
                        blocks = get_stock_blocks(stock)
                        if blocks:
                            info = {}
                            if 'ZJHHY' in blocks and blocks['ZJHHY']:
                                zjhhy_code = blocks['ZJHHY'][0][0] if len(blocks['ZJHHY'][0]) > 0 else ''
                                info['zjhhy_code'] = hash(zjhhy_code) % 10000
                            if 'HY' in blocks and blocks['HY']:
                                hy_code = blocks['HY'][0][0] if len(blocks['HY'][0]) > 0 else ''
                                info['hy_code'] = hash(hy_code) % 10000
                            if info:
                                industry_info_cache[stock] = info
                    except Exception:
                        pass
            log.info("✓ 批量获取行业信息完成（获取 {} 只股票）".format(len(industry_info_cache)))
        except Exception as e:
            log.warning("批量获取行业信息失败: {}，将使用默认值".format(str(e)))

        # ========== 第二阶段：逐个股票计算因子和预测 ==========
        log.info("开始计算因子 {} 只股票...".format(len(stock_list)))

        # 收集所有特征
        all_features = []
        stock_order = []
        fail_reasons = defaultdict(int)

        for i, stock in enumerate(stock_list):
            try:
                # 从缓存获取价格数据
                if stock not in price_data_cache:
                    fail_reasons['no_price_data'] += 1
                    continue

                # 检查基本面数据是否存在
                if stock not in fundamentals_cache:
                    fail_reasons['no_fundamentals_data'] += 1
                    continue

                price_data = {stock: price_data_cache[stock]}

                # 获取市值和市值排名
                market_cap = window_market_caps.get(stock, None)
                market_cap_rank = market_cap_ranks.get(stock, None)

                # 从缓存获取行业信息（已提前批量查询）
                industry_info = industry_info_cache.get(stock, None)

                # 计算因子（传入完整参数，与训练代码一致）
                fundamentals = fundamentals_cache[stock]
                features = calculate_factors(
                    stock, price_data[stock],
                    market_cap=market_cap,
                    market_cap_rank=market_cap_rank,
                    market_sentiment=market_sentiment,
                    fundamentals=fundamentals,
                    industry_info=industry_info,  # 传入行业信息
                    current_date=context.current_dt  # 修复：传入当前日期，用于计算基本面时效性权重
                )

                if not features:
                    fail_reasons['calculate_factors_failed'] += 1
                    continue

                # 移除股票代码，保留特征
                X_pred = {k: v for k, v in features.items() if k != 'stock_code'}
                all_features.append(X_pred)
                stock_order.append(stock)

            except Exception as e:
                fail_reasons['exception_' + type(e).__name__] += 1
                if len(stock_order) == 0 and i < 5:
                    log.error("处理股票{}失败: {}".format(stock, str(e)))
                continue

        log.info("因子计算完成: {}/{} 只股票 ({:.1f}%)".format(
            len(all_features), len(stock_list), 100.0 * len(all_features) / len(stock_list) if stock_list else 0))

        # 第二阶段：批量预测
        predictions = {}
        if all_features:
            log.info("开始批量预测 {} 只股票...".format(len(all_features)))
            predictions = batch_predict_with_model(all_features, stock_order)

            if not predictions:
                log.error("批量预测失败")
                return None

        success_count = len(predictions)

        log.info("AI预测完成: {}/{} 只股票 ({:.1f}%)".format(
            success_count, len(stock_list), 100.0 * success_count / len(stock_list)))

        # 输出失败原因统计
        if fail_reasons:
            log.warning("预测失败原因统计:")
            for reason, count in sorted(fail_reasons.items(), key=lambda x: x[1], reverse=True):
                log.warning("  {}: {} 只 ({:.1f}%)".format(
                    reason, count, 100.0 * count / len(stock_list)))

        # 输出数据质量问题统计
        if hasattr(g, 'short_data_count') and g.short_data_count > 0:
            log.warning("数据长度不足的股票: {} 只".format(g.short_data_count))
        if hasattr(g, 'nan_count') and g.nan_count > 0:
            log.warning("包含NaN值的股票: {} 只".format(g.nan_count))

        # 如果成功预测的股票较少，输出预测值的统计信息
        if success_count > 0 and success_count < 10:
            log.info("成功预测的股票及其预测值:")
            for stock, pred in sorted(predictions.items(), key=lambda x: x[1], reverse=True):
                log.info("  {}: {:.4f}".format(stock, pred))
        elif success_count >= 10:
            # 输出预测值分布
            pred_values = list(predictions.values())
            log.info("预测值统计: min={:.4f}, max={:.4f}, mean={:.4f}".format(
                min(pred_values), max(pred_values), np.mean(pred_values)))

        return predictions

    except Exception as e:
        log.error("预测失败: {}".format(str(e)))
        return None


def batch_predict_with_model(all_features, stock_order):
    """
    批量预测多只股票 - 性能优化版

    参数:
        all_features: 特征字典列表 [{feature: value, ...}, ...]
        stock_order: 股票代码列表，与 all_features 一一对应

    返回:
        predictions: {stock: pred_value} 字典
    """
    try:
        if not all_features or not stock_order:
            return {}

        # 1. 构建特征DataFrame
        feature_df = pd.DataFrame(all_features)

        # 2. 确保特征顺序一致
        if g.feature_order:
            for col in g.feature_order:
                if col not in feature_df.columns:
                    feature_df[col] = 0
            feature_df = feature_df[g.feature_order]

        # 3. 应用RobustScaler标准化
        if hasattr(g, 'scaler_center') and hasattr(g, 'scaler_scale') and \
           g.scaler_center is not None and g.scaler_scale is not None:
            feature_array = feature_df.values
            # 避免除以0的警告：将scale中的0替换为1（保持该特征不变）
            safe_scale = np.where(g.scaler_scale == 0, 1, g.scaler_scale)
            feature_scaled = (feature_array - g.scaler_center) / safe_scale
            feature_df_scaled = pd.DataFrame(feature_scaled, columns=feature_df.columns)
        else:
            if not hasattr(g, 'scaler_warning_logged'):
                log.warning("缺少RobustScaler参数，使用未标准化特征（可能影响预测效果）")
                g.scaler_warning_logged = True
            feature_df_scaled = feature_df

        # 4. 批量预测
        try:
            import xgboost as xgb
            if isinstance(g.model, xgb.Booster):
                dtest = xgb.DMatrix(feature_df_scaled.values)
                pred_values = g.model.predict(dtest)
                return dict(zip(stock_order, pred_values))
        except (ImportError, AttributeError) as e:
            log.error("XGBoost批量预测失败: {}".format(str(e)))
            return {}

        # sklearn模型
        if hasattr(g.model, 'predict'):
            pred_values = g.model.predict(feature_df_scaled.values)
            return dict(zip(stock_order, pred_values))

        log.error("模型类型不支持批量预测")
        return {}

    except Exception as e:
        log.error("批量预测异常: {}".format(str(e)))
        return {}


# ==================== 因子计算模块（调用共享代码） ====================
# 导入共享因子模块（从模型目录动态加载，和模型一样是上传过去的）
# ptrade平台限制：不能使用os库和sys库，需要使用pathlib
from pathlib import Path

# 动态加载shared_factors模块
def load_factor_modules():
    """从strategies目录加载因子模块"""

    # 加载shared_factors.py
    shared_factors_path = get_research_path()+'strategies/shared_factors.py'

    # 读取并执行模块代码
    global shared_factors

    # 创建模块命名空间（不使用sys）
    module_namespace = {
        '__name__': 'shared_factors',
        '__file__': shared_factors_path,
    }

    # 使用exec加载模块
    with open(shared_factors_path, 'r', encoding='utf-8') as f:
        shared_factors_code = f.read()
        exec(shared_factors_code, module_namespace)

    # 创建模块对象
    class ModuleType:
        pass

    shared_factors = ModuleType()
    for key, value in module_namespace.items():
        setattr(shared_factors, key, value)

    log.info("✓ 因子模块加载成功")

# 在模块加载时初始化（延迟到initialize()调用）
shared_factors = None


def calculate_factors(stock, price_data, market_cap=None, market_cap_rank=None,
                     market_sentiment=None, fundamentals=None, industry_info=None,
                     current_date=None):
    """计算完整因子（回测用）

    Args:
        stock: 股票代码
        price_data: 价格数据字典（包含close, open, high, low, volume）
        market_cap: 市值（亿元）
        market_cap_rank: 市值在当前时间窗口中的百分位排名 (0-1之间)
        market_sentiment: 市场情绪字典
        fundamentals: 基本面数据字典
        industry_info: 行业信息字典
        current_date: 当前日期（用于计算基本面时效性权重）

    Returns:
        dict: 因子字典，如果计算失败则返回None
    """

    # 调用共享因子计算模块
    return shared_factors.calculate_factors(
        stock=stock,
        price_data=price_data,
        market_cap=market_cap,
        market_cap_rank=market_cap_rank,
        market_sentiment=market_sentiment,
        fundamentals=fundamentals,
        industry_info=industry_info,
        current_date=current_date
    )


def add_to_sell_list(stock, reason, position, predicted_return=None):
    """统一的卖出标记函数，避免重复代码"""
    # 获取真实买入价（从状态中读取，避免使用动态的position.cost_basis）
    entry_price = g.state['entry_prices'].get(stock, None)
    if entry_price is None:
        # 如果没有记录，使用position.cost_basis，但记录警告
        entry_price = position.cost_basis
        log.warning("【警告】{} 没有真实买入价记录，使用position.cost_basis={:.2f}（可能不准确）".format(
            stock, entry_price))

    g.to_sell[stock] = {
        'reason': reason,
        'predicted_return': predicted_return or g.state.get('buy_predictions', {}).get(stock, 0),
        'entry_price': entry_price,  # 保存真实买入价，而不是动态的cost_basis
        'amount': position.amount,
    }


def get_filtered_stock_pool(context, data):
    """获取过滤后的股票池"""
    all_stocks = get_Ashares()
    fundamentals = get_fundamentals(
        all_stocks,
        'valuation',
        ['total_value'],
        context.previous_date
    )

    # 市值筛选
    market_cap_mask = ((fundamentals['total_value'] >= g.min_market_cap) &
                       (fundamentals['total_value'] <= g.max_market_cap))

    # 综合筛选
    selected_stocks = fundamentals[market_cap_mask].index.tolist()

    # 价格筛选：直接用data对象过滤（高效，无需额外查询）
    # selected_stocks = [s for s in selected_stocks if data[s]['close'] >= 1.0]
    # log.info("市值+价格筛选后: {} 只股票".format(len(selected_stocks)))

    update_daily_status_cache(context, selected_stocks)
    filtered_stocks = filter_stock_by_status(selected_stocks)

    return filtered_stocks


def update_daily_status_cache(context, stock_list=None):
    """更新股票状态缓存（分批查询避免超时）"""
    current_date = context.blotter.current_dt.date()
    if hasattr(g, 'status_cache_date') and g.status_cache_date == current_date:
        return

    if stock_list is None:
        stock_list = get_Ashares()

    status_cache = defaultdict(dict)
    batch_size = 100
    query_types = ["ST", "HALT", "DELISTING"]

    # 合并循环：一次遍历批次，查询所有3种状态（减少批次切片开销）
    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i+batch_size]
        # 对当前批次查询所有3种状态
        for query_type in query_types:
            status_result = get_stock_status(batch, query_type=query_type)
            for stock, has_status in status_result.items():
                status_cache[stock][query_type] = has_status

    g.status_cache = status_cache
    g.status_cache_date = current_date


def filter_stock_by_status(stocks):
    """过滤ST、退市、停牌股票"""
    return [stock for stock in stocks
            if not any(g.status_cache.get(stock, {}).get(status, False)
                      for status in ['ST', 'DELISTING', 'HALT'])]


def sell_stocks(context):
    """卖出逻辑（优化版 - 移动止盈策略）"""
    positions = context.portfolio.positions

    # 先处理计划卖出的股票（在before_trading_start中添加到g.to_sell的）
    for stock in list(g.to_sell.keys()):
        if stock in positions and positions[stock].amount > 0:
            order_target(stock, 0)

    # 检查持仓股票的卖出条件
    for stock in list(positions.keys()):
        position = positions[stock]
        # 使用真实买入价计算收益
        hold_days = g.state['hold_days'].get(stock, 0)

        sell_reason = None

        # 检查持有到期（唯一卖出条件）
        if hold_days >= g.max_hold_days:
            sell_reason = "持有到期({} 天)".format(hold_days)

        # 如果检测到新的卖出条件，添加到待卖列表
        if sell_reason and stock not in g.to_sell:
            # 新的卖出信号，先保存cost_basis，再下单
            add_to_sell_list(stock, sell_reason, position)
            order_target(stock, 0)


def buy_stocks(context):
    """买入逻辑 - 等权重分配资金"""
    if not g.to_buy:
        return

    # 修正：只统计amount>0的持仓（context.portfolio.positions包含历史持仓）
    current_positions = sum(1 for p in context.portfolio.positions.values() if p.amount > 0)

    # 确保不超过最大持仓数
    if current_positions >= g.max_positions:
        return

    # 等权重分配：每只股票占 1/max_positions
    equal_weight = 1.0 / g.max_positions

    # 按权重计算每只股票的资金分配
    total_value = context.portfolio.portfolio_value

    for stock in g.to_buy:
        allocation = total_value * equal_weight
        order_value(stock, allocation)


def finalize_buys(context):
    """确认买入成功后更新状态（符合AI策略特点）"""
    if not g.to_buy:
        return

    for stock in g.to_buy[:]:  # 使用副本迭代
        position = context.portfolio.positions.get(stock)
        if position and position.amount > 0:
            # 确认订单成交，初始化状态
            # 买入当天为第1天（与max_hold_days的逻辑一致）
            g.state['hold_days'][stock] = 1
            g.state['entry_prices'][stock] = position.cost_basis  # 记录真实买入价


            score = g.stock_scores.get(stock, 0)
            # 保存买入时的预测收益（用于卖出时对比）
            g.state.setdefault('buy_predictions', {})[stock] = score

            log.info("【买入成功】{} | 成交价: {:.2f} | 数量: {} | 预测收益: {:.2%}".format(
                stock, position.cost_basis, position.amount, score))

            g.to_buy.remove(stock)


def finalize_sells(context, data):
    """确认卖出成功后清理状态"""
    if not g.to_sell:
        return

    log.info("【检查卖出】待确认股票: {}".format(list(g.to_sell.keys())))

    for stock in list(g.to_sell.keys()):
        position = context.portfolio.positions.get(stock)
        sell_info = g.to_sell[stock]
        sell_reason = sell_info['reason']
        predicted_return = sell_info['predicted_return']
        entry_price = sell_info['entry_price']  # 直接使用保存的真实买入价

        # 情况1和2：卖出已完成（position不存在或持仓为0）
        if position is None or position.amount == 0:
            # 获取卖出价格
            if position is None:
                sell_price = data[stock]['close']
            else:
                sell_price = position.last_sale_price

            # 计算真实收益
            actual_return = (sell_price - entry_price) / entry_price

            log.info("【卖出成交】{} | 买入价: {:.2f} | 卖出价: {:.2f} | 实际收益: {:.2%} | 预测: {:.2%} | 原因: {}".format(
                stock, entry_price, sell_price, actual_return, predicted_return, sell_reason))
            cleanup_stock_records(stock)
            g.to_sell.pop(stock)

        # 情况3：持仓还存在且数量>0 - 卖出未完成
        else:
            log.info("【卖出待成交】{} | 持仓: {} | 可用: {} | 原因: {}".format(
                stock, position.amount, position.enable_amount, sell_reason))
            if position.enable_amount <= 0:
                log.warning("【卖出异常】{} 可用数量为0，无法卖出".format(stock))


def cancel_stale_orders(context):
    """取消超时未成交订单"""
    now = datetime.now()

    for order in get_open_orders():
        if (now - order.created).seconds > 60:
            cancel_order(order)


# ==================== 辅助函数 ====================

def update_highest_price(stock, current_price):
    """更新股票的最高价记录"""
    if stock not in g.state['highest_prices']:
        g.state['highest_prices'][stock] = current_price
    elif current_price > g.state['highest_prices'][stock]:
        g.state['highest_prices'][stock] = current_price
    return g.state['highest_prices'][stock]


def cleanup_stock_records(stock):
    """清理股票记录"""
    if stock in g.state['hold_days']:
        del g.state['hold_days'][stock]
    if stock in g.state['highest_prices']:
        del g.state['highest_prices'][stock]
    if stock in g.state['entry_prices']:
        del g.state['entry_prices'][stock]
    if stock in g.state['in_take_profit_mode']:
        del g.state['in_take_profit_mode'][stock]
    # 清理买入时的预测记录
    if 'buy_predictions' in g.state and stock in g.state['buy_predictions']:
        del g.state['buy_predictions'][stock]


def update_hold_days(context):
    """更新持仓天数，清理不再持有的股票（模仿shadow_strategy）"""
    positions = context.portfolio.positions
    for stock in list(g.state['hold_days'].keys()):
        if stock in positions and positions[stock].amount > 0:
            # 对实际持仓的股票 += 1
            g.state['hold_days'][stock] += 1
        else:
            # 自动清理已卖出的股票
            hold_days = g.state['hold_days'][stock]
            log.info("【持仓消失】{} 持有{}天后已不在持仓中".format(stock, hold_days))
            g.state['hold_days'].pop(stock, None)


def after_trading_end(context, data):
    """盘后处理"""
    portfolio_value = context.portfolio.portfolio_value
    # 修正：只统计amount>0的持仓
    positions_count = sum(1 for p in context.portfolio.positions.values() if p.amount > 0)

    log.info("="*60)
    log.info("【日终】总资产: {:.2f} | 持仓: {} 只 | 市场: {}".format(
        portfolio_value, positions_count, g.state['market_regime']))
    log.info("="*60)

    # 更新持有天数（盘后更新，自动清理已卖出的股票）
    update_hold_days(context)

    g.to_buy = []
    g.stock_scores = {}

    save_strategy_state(context)

# ==================== 状态持久化函数 ====================

def load_strategy_state(context):
    """加载策略状态（从硬盘恢复hold_days和highest_prices）"""
    if hasattr(g, 'strategy_state_path') and Path(g.strategy_state_path).exists():
        with open(g.strategy_state_path, 'rb') as f:
            loaded_state = pickle.load(f)
            # 只更新需要持久化的字段
            g.state['hold_days'] = loaded_state.get('hold_days', defaultdict(int))
            g.state['highest_prices'] = loaded_state.get('highest_prices', defaultdict(float))
            g.state['entry_prices'] = loaded_state.get('entry_prices', defaultdict(float))
            g.state['in_take_profit_mode'] = loaded_state.get('in_take_profit_mode', defaultdict(bool))
            g.state['buy_predictions'] = loaded_state.get('buy_predictions', {})

            # 恢复交易计划（只在状态文件确实包含这些键时才恢复，避免覆盖内存中的有效数据）
            if 'to_sell' in loaded_state and loaded_state['to_sell']:
                g.to_sell = loaded_state['to_sell']
                log.info("【状态恢复】恢复待卖出股票: {}".format(list(g.to_sell.keys())))
            if 'to_buy' in loaded_state and loaded_state['to_buy']:
                g.to_buy = loaded_state['to_buy']
                log.info("【状态恢复】恢复待买入股票: {}".format(g.to_buy))
    else:
        # 状态文件不存在时，初始化为空（回测模式第一次运行）
        if 'entry_prices' not in g.state:
            g.state['entry_prices'] = defaultdict(float)
        if 'buy_predictions' not in g.state:
            g.state['buy_predictions'] = {}
        if 'hold_days' not in g.state:
            g.state['hold_days'] = defaultdict(int)
        if 'highest_prices' not in g.state:
            g.state['highest_prices'] = defaultdict(float)
        if 'in_take_profit_mode' not in g.state:
            g.state['in_take_profit_mode'] = defaultdict(bool)


def save_strategy_state(context):
    """保存策略状态到硬盘（持久化hold_days和highest_prices）"""
    # 只保存需要持久化的字段
    state_to_save = {
        'hold_days': dict(g.state['hold_days']),
        'highest_prices': dict(g.state['highest_prices']),
        'entry_prices': dict(g.state['entry_prices']),
        'in_take_profit_mode': dict(g.state['in_take_profit_mode']),
        'buy_predictions': g.state.get('buy_predictions', {}),
        # 保存交易计划（实盘重启后能恢复订单追踪）
        'to_sell': g.to_sell if hasattr(g, 'to_sell') else {},
        'to_buy': g.to_buy if hasattr(g, 'to_buy') else [],
    }
    with open(g.strategy_state_path, 'wb') as f:
        pickle.dump(state_to_save, f, pickle.HIGHEST_PROTOCOL)


def clear_file(file_path):
    """删除指定路径的文件（用于回测模式清空状态）"""
    path = Path(file_path)
    if path.exists():
        path.unlink()
