# -*- coding: utf-8 -*-
"""
交易查询功能演示策略
展示如何使用各种交易查询接口
"""


# 策略函数
def initialize(context):
    """初始化函数"""
    log.info("初始化交易查询演示策略")
    
    # 设置股票池
    g.security = 'STOCK_A'
    g.trade_count = 0
    g.max_trades = 5
    
    log.info(f"设置股票池: {g.security}")


def handle_data(context, data):
    """主策略函数"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    current_price = data[security]['close']
    log.info(f"当前价格: {current_price:.2f}")
    
    # 限制交易次数，避免过多输出
    if g.trade_count >= g.max_trades:
        return
    
    try:
        # 演示各种交易查询功能
        
        # 1. 查询当前持仓
        log.info("=== 持仓查询 ===")
        positions = get_positions()
        position = get_position(security)
        
        if position:
            log.info(f"当前持仓: {position['amount']}股, 成本价: {position['cost_basis']:.2f}, 市值: {position['market_value']:.2f}")
        else:
            log.info("当前无持仓")
        
        # 2. 查询订单状态
        log.info("=== 订单查询 ===")
        all_orders = get_orders()
        open_orders = get_open_orders()
        
        log.info(f"当日总订单数: {len(all_orders)}")
        log.info(f"未完成订单数: {len(open_orders)}")
        
        # 3. 查询成交记录
        log.info("=== 成交查询 ===")
        trades = get_trades()
        log.info(f"当日成交数: {len(trades)}")
        
        # 4. 执行交易操作
        log.info("=== 执行交易 ===")
        
        if g.trade_count == 0:
            # 第一笔：市价买入
            log.info("执行市价买入1000股")
            order_id = order(security, 1000)
            if order_id:
                order_info = get_order(order_id)
                log.info(f"订单状态: {order_info['status']}, 成交数量: {order_info['filled_amount']}")
        
        elif g.trade_count == 1:
            # 第二笔：限价买入（低于市价，不会立即成交）
            limit_price = current_price * 0.95
            log.info(f"执行限价买入500股，限价: {limit_price:.2f}")
            order_id = order(security, 500, limit_price=limit_price)
            if order_id:
                order_info = get_order(order_id)
                log.info(f"订单状态: {order_info['status']}, 限价: {order_info['price']}")
        
        elif g.trade_count == 2:
            # 第三笔：撤销之前的限价单
            log.info("撤销未成交的限价单")
            open_orders = get_open_orders()
            for order_id, order_info in open_orders.items():
                if order_info['order_type'] == 'limit':
                    success = cancel_order(order_id)
                    log.info(f"撤销订单 {order_id}: {'成功' if success else '失败'}")
                    break
        
        elif g.trade_count == 3:
            # 第四笔：部分卖出
            current_position = get_position(security)
            if current_position and current_position['amount'] > 0:
                sell_amount = min(300, current_position['amount'])
                log.info(f"卖出{sell_amount}股")
                order_id = order(security, -sell_amount)
                if order_id:
                    order_info = get_order(order_id)
                    log.info(f"卖出订单状态: {order_info['status']}")
        
        elif g.trade_count == 4:
            # 第五笔：限价卖出（高于市价，不会立即成交）
            current_position = get_position(security)
            if current_position and current_position['amount'] > 0:
                limit_price = current_price * 1.05
                sell_amount = min(200, current_position['amount'])
                log.info(f"限价卖出{sell_amount}股，限价: {limit_price:.2f}")
                order_id = order(security, -sell_amount, limit_price=limit_price)
                if order_id:
                    order_info = get_order(order_id)
                    log.info(f"限价卖出订单状态: {order_info['status']}")
        
        g.trade_count += 1
        
        # 5. 总结当前状态
        log.info("=== 当前状态总结 ===")
        final_position = get_position(security)
        final_orders = get_orders()
        final_open_orders = get_open_orders()
        final_trades = get_trades()
        
        if final_position:
            log.info(f"最终持仓: {final_position['amount']}股")
            log.info(f"持仓市值: {final_position['market_value']:.2f}")
            log.info(f"盈亏比例: {final_position['pnl_ratio']:.2%}")
        
        log.info(f"累计订单: {len(final_orders)}笔")
        log.info(f"未完成订单: {len(final_open_orders)}笔")
        log.info(f"累计成交: {len(final_trades)}笔")
        
        # 显示未完成订单详情
        if final_open_orders:
            log.info("未完成订单详情:")
            for order_id, order_info in final_open_orders.items():
                log.info(f"  订单{order_id[:8]}: {order_info['order_type']}单, "
                        f"{'买入' if order_info['is_buy'] else '卖出'}{abs(order_info['amount'])}股, "
                        f"价格: {order_info['price']:.2f}")
    
    except Exception as e:
        log.error(f"交易查询演示出错: {e}")


def before_trading_start(context, data):
    """盘前处理"""
    log.info("盘前准备 - 交易查询演示策略")


def after_trading_end(context, data):
    """盘后处理"""
    # 记录当日最终状态
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    log.info(f"盘后总结 - 总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
    
    # 显示最终的交易统计
    final_orders = get_orders()
    final_trades = get_trades()
    final_open_orders = get_open_orders()
    
    log.info(f"当日交易统计:")
    log.info(f"  总订单数: {len(final_orders)}")
    log.info(f"  总成交数: {len(final_trades)}")
    log.info(f"  未完成订单: {len(final_open_orders)}")
    
    # 计算当日交易金额
    total_trade_amount = 0
    for trade in final_trades:
        total_trade_amount += abs(trade['amount'] * trade['price'])
    
    log.info(f"  当日交易金额: {total_trade_amount:,.2f}")
    
    # 显示持仓情况
    positions = get_positions()
    if positions:
        log.info("最终持仓:")
        for security, position in positions.items():
            if position and position['amount'] > 0:
                log.info(f"  {security}: {position['amount']}股, "
                        f"成本价: {position['cost_basis']:.2f}, "
                        f"市值: {position['market_value']:.2f}")
    else:
        log.info("最终无持仓")
