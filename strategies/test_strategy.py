#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试策略 - 用于测试ptrade API的完整性
这个策略会调用尽可能多的ptrade API函数来验证系统功能
"""

def initialize(context):
    """策略初始化"""
    log.info("=== 测试策略初始化开始 ===")
    
    # 设置日志级别
    log.set_log_level(log.LEVEL_INFO)
    log.info("设置日志级别为INFO")
    
    # 获取初始资金
    initial_cash = get_initial_cash(context, 100000)
    log.info(f"获取初始资金: {initial_cash:,.2f}")

    # 设置手续费
    set_commission(commission_ratio=0.0003, min_commission=5.0, type="STOCK")
    log.info("设置手续费率: 0.03%, 最低5元")

    # 设置限价模式
    set_limit_mode(True)
    log.info("设置限价模式: 开启")
    
    # 测试其他API
    research_path = get_research_path()
    log.info(f"获取研究路径: {research_path}")

    # 测试文件操作
    test_file = "test_output.txt"
    clear_file(test_file)
    log.info(f"清理测试文件: {test_file}")

    # 初始化全局变量
    g.test_counter = 0
    g.stocks_to_test = []
    g.max_positions = 2
    g.test_orders = []  # 用于测试取消订单

    log.info("=== 测试策略初始化完成 ===")


def before_trading_start(context, data):
    """交易开始前的准备工作"""
    log.info("=== 交易开始前准备 ===")
    
    # 测试获取所有A股
    all_stocks = get_Ashares()
    log.info(f"获取所有A股数量: {len(all_stocks)}")
    
    # 选择前几只股票进行测试
    g.stocks_to_test = all_stocks[:5] if len(all_stocks) >= 5 else all_stocks
    log.info(f"选择测试股票: {g.stocks_to_test}")
    
    # 设置股票池
    set_universe(g.stocks_to_test)
    
    # 测试股票状态查询
    if g.stocks_to_test:
        st_status = get_stock_status(g.stocks_to_test, 'ST')
        log.info(f"ST状态查询结果: {st_status}")
        
        delisted_status = get_stock_status(g.stocks_to_test, 'delisted')
        log.info(f"退市状态查询结果: {delisted_status}")
        
        suspended_status = get_stock_status(g.stocks_to_test, 'suspended')
        log.info(f"停牌状态查询结果: {suspended_status}")
    
    # 测试股票信息查询
    if g.stocks_to_test:
        stock_info = get_stock_info(g.stocks_to_test, ['listed_date', 'industry'])
        log.info(f"股票信息查询: {stock_info}")
    
    # 测试股票名称查询
    if g.stocks_to_test:
        stock_names = get_stock_name(g.stocks_to_test)
        log.info(f"股票名称: {stock_names}")
    
    # 测试基本面数据查询
    if g.stocks_to_test:
        fundamentals = get_fundamentals(g.stocks_to_test, 'valuation',
                                      fields=['market_cap', 'pe_ratio'],
                                      date=context.current_dt.date())
        log.info(f"基本面数据: {fundamentals}")

    # 测试新的财务报表接口
    if g.stocks_to_test:
        log.info("=== 测试新的财务接口 ===")

        # 测试损益表数据
        income_data = get_income_statement(g.stocks_to_test,
                                         fields=['revenue', 'net_income', 'eps_basic'])
        log.info(f"损益表数据: {income_data}")

        # 测试资产负债表数据
        balance_data = get_balance_sheet(g.stocks_to_test,
                                       fields=['total_assets', 'total_liabilities', 'total_equity'])
        log.info(f"资产负债表数据: {balance_data}")

        # 测试现金流量表数据
        cashflow_data = get_cash_flow(g.stocks_to_test,
                                    fields=['operating_cash_flow', 'free_cash_flow'])
        log.info(f"现金流量表数据: {cashflow_data}")

        # 测试财务比率数据
        ratios_data = get_financial_ratios(g.stocks_to_test,
                                         fields=['current_ratio', 'roe', 'debt_to_equity'])
        log.info(f"财务比率数据: {ratios_data}")

        # 测试扩展的基本面数据（更多字段）
        extended_fundamentals = get_fundamentals(g.stocks_to_test, 'income',
                                               fields=['revenue', 'net_income', 'roe', 'roa'])
        log.info(f"扩展基本面数据: {extended_fundamentals}")

    log.info("=== 交易开始前准备完成 ===")


def handle_data(context, data):
    """主要交易逻辑"""
    log.info("=== 开始处理交易数据 ===")
    
    g.test_counter += 1
    log.info(f"交易日计数: {g.test_counter}")
    
    # 测试当前持仓数量
    current_positions = get_num_of_positions(context)
    log.info(f"当前持仓数量: {current_positions}")
    
    # 测试是否为交易日
    is_trading_day = is_trade()
    log.info(f"是否为交易日: {is_trading_day}")
    
    if not g.stocks_to_test:
        log.info("没有测试股票，跳过交易")
        return
    
    # 测试历史数据获取
    test_stock = g.stocks_to_test[0]
    log.info(f"测试股票: {test_stock}")
    
    # 获取历史数据
    history_data = get_history(5, frequency='1d', 
                              field=['close', 'volume', 'high', 'low', 'open'],
                              security_list=[test_stock], 
                              fq='pre', include=True, is_dict=True)
    
    if test_stock in history_data:
        hist = history_data[test_stock]
        log.info(f"获取到{len(hist['close'])}天历史数据")
        log.info(f"最新收盘价: {hist['close'][-1]}")
        log.info(f"最新成交量: {hist['volume'][-1]}")
    
    # 测试当前价格获取（从当前数据中获取）
    if test_stock in data:
        current_price = data[test_stock]['close']
        log.info(f"当前价格: {current_price}")
    else:
        log.info("当前数据中没有测试股票价格")
    
    # 测试交易功能
    if current_positions < g.max_positions:
        # 测试买入
        log.info(f"尝试买入 {test_stock}")
        
        # 测试order函数
        order_result = order(test_stock, 100)
        log.info(f"order函数结果: {order_result}")
        g.test_orders.append(f"order_{test_stock}_100")

        # 测试order_value函数
        if len(g.stocks_to_test) > 1:
            test_stock2 = g.stocks_to_test[1]
            order_value_result = order_value(test_stock2, 10000)
            log.info(f"order_value函数结果: {order_value_result}")
            g.test_orders.append(f"order_value_{test_stock2}_10000")

        # 测试取消订单（模拟）
        if g.test_orders:
            test_order = g.test_orders[0]
            cancel_order(test_order)
            log.info(f"测试取消订单: {test_order}")
    
    else:
        # 测试卖出
        log.info("持仓已满，测试卖出")
        for stock, position in context.portfolio.positions.items():
            if position.amount > 0:
                log.info(f"尝试卖出 {stock}")
                # 测试order_target函数
                order_target_result = order_target(stock, 0)
                log.info(f"order_target函数结果: {order_target_result}")
                break
    
    log.info("=== 交易数据处理完成 ===")


def after_trading_end(context, data):
    """交易结束后的处理"""
    log.info("=== 交易结束后处理 ===")
    
    # 显示当前投资组合状态
    log.info(f"当前现金: {context.portfolio.cash:,.2f}")
    log.info(f"投资组合总价值: {context.portfolio.total_value:,.2f}")
    
    # 显示持仓详情
    active_positions = []
    for stock, position in context.portfolio.positions.items():
        if position.amount > 0:
            active_positions.append(f"{stock}({position.amount}股)")
            log.info(f"持仓 {stock}: {position.amount}股, 成本价: {position.cost_basis:.2f}, "
                    f"当前价: {position.last_sale_price:.2f}, 市值: {position.market_value:.2f}")
    
    if active_positions:
        log.info(f"活跃持仓: {', '.join(active_positions)}")
    else:
        log.info("当前无持仓")
    
    # 计算收益率
    if hasattr(context.portfolio, 'starting_cash'):
        total_return = (context.portfolio.total_value - context.portfolio.starting_cash) / context.portfolio.starting_cash * 100
        log.info(f"总收益率: {total_return:.2f}%")
    
    log.info("=== 交易结束后处理完成 ===")
