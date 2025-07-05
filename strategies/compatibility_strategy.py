# -*- coding: utf-8 -*-
"""
委托状态兼容性演示策略
展示如何在策略中使用不同版本的ptrade API兼容性功能
"""


# 策略函数
def initialize(context):
    """初始化函数"""
    log.info("初始化委托状态兼容性演示策略")
    
    # 设置股票池
    g.security = 'STOCK_A'
    
    # 设置ptrade版本（演示不同版本的兼容性）
    # 可以设置为 'V005', 'V016', 'V041'
    g.ptrade_version = 'V005'  # 使用V005版本（整数状态）
    set_ptrade_version(g.ptrade_version)
    
    # 获取版本信息
    version_info = get_version_info()
    log.info(f"当前ptrade版本: {version_info['version']}")
    log.info(f"状态类型: {version_info['status_type']}")
    log.info(f"支持的状态: {version_info['supported_statuses']}")
    
    # 策略参数
    g.trade_count = 0
    g.max_trades = 5
    g.order_history = []  # 记录订单历史
    
    log.info(f"设置股票池: {g.security}")


def handle_data(context, data):
    """主策略函数"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    current_price = data[security]['close']
    log.info(f"当前价格: {current_price:.2f}")
    
    # 限制交易次数，演示不同的订单状态
    if g.trade_count >= g.max_trades:
        return
    
    try:
        # 演示不同类型的订单和状态处理
        
        if g.trade_count == 0:
            # 第一笔：市价买单（立即成交）
            log.info("=== 第一笔交易：市价买单 ===")
            order_id = order(security, 1000)
            if order_id:
                g.order_history.append(order_id)
                _analyze_order_status(order_id, "市价买单")
        
        elif g.trade_count == 1:
            # 第二笔：限价买单（可能不成交）
            log.info("=== 第二笔交易：限价买单 ===")
            limit_price = current_price * 0.95  # 低于市价5%
            order_id = order(security, 500, limit_price=limit_price)
            if order_id:
                g.order_history.append(order_id)
                _analyze_order_status(order_id, "限价买单")
        
        elif g.trade_count == 2:
            # 第三笔：撤销之前的限价单
            log.info("=== 第三笔操作：撤销限价单 ===")
            open_orders = get_open_orders()
            for order_id, order_info in open_orders.items():
                if order_info['order_type'] == 'limit':
                    log.info(f"撤销限价单: {order_id}")
                    success = cancel_order(order_id)
                    if success:
                        _analyze_order_status(order_id, "撤销后的限价单")
                    break
        
        elif g.trade_count == 3:
            # 第四笔：市价卖单
            log.info("=== 第四笔交易：市价卖单 ===")
            current_position = get_position(security)
            if current_position and current_position['amount'] > 0:
                sell_amount = min(300, current_position['amount'])
                order_id = order(security, -sell_amount)
                if order_id:
                    g.order_history.append(order_id)
                    _analyze_order_status(order_id, "市价卖单")
        
        elif g.trade_count == 4:
            # 第五笔：限价卖单
            log.info("=== 第五笔交易：限价卖单 ===")
            current_position = get_position(security)
            if current_position and current_position['amount'] > 0:
                limit_price = current_price * 1.05  # 高于市价5%
                sell_amount = min(200, current_position['amount'])
                order_id = order(security, -sell_amount, limit_price=limit_price)
                if order_id:
                    g.order_history.append(order_id)
                    _analyze_order_status(order_id, "限价卖单")
        
        g.trade_count += 1
        
        # 分析所有订单状态
        _analyze_all_orders()
    
    except Exception as e:
        log.error(f"策略执行出错: {e}")


def _analyze_order_status(order_id, order_description):
    """分析单个订单状态"""
    try:
        order_info = get_order(order_id)
        if order_info:
            status = order_info['status']
            status_type = type(status).__name__
            
            log.info(f"{order_description} 状态分析:")
            log.info(f"  订单ID: {order_id}")
            log.info(f"  状态值: {status} (类型: {status_type})")
            
            # 使用兼容性函数验证状态
            is_valid = validate_order_status(status)
            log.info(f"  状态有效性: {'有效' if is_valid else '无效'}")
            
            # 转换状态格式（演示）
            if status_type == 'int':
                # 如果是整数，转换为字符串格式
                str_status = convert_order_status(status, to_external=False)
                log.info(f"  转换为字符串: {str_status}")
            else:
                # 如果是字符串，转换为当前版本的外部格式
                ext_status = convert_order_status(status, to_external=True)
                log.info(f"  外部格式: {ext_status}")
            
            # 状态判断
            from simtradelab.compatibility import get_compat_handler
            handler = get_compat_handler()
            
            is_open = handler.is_open_status(status)
            is_filled = handler.is_filled_status(status)
            is_cancelled = handler.is_cancelled_status(status)
            
            log.info(f"  状态判断: 未完成={is_open}, 已成交={is_filled}, 已撤销={is_cancelled}")
    
    except Exception as e:
        log.warning(f"分析订单状态失败: {e}")


def _analyze_all_orders():
    """分析所有订单状态"""
    try:
        log.info("=== 所有订单状态汇总 ===")
        
        all_orders = get_orders()
        open_orders = get_open_orders()
        
        log.info(f"总订单数: {len(all_orders)}")
        log.info(f"未完成订单数: {len(open_orders)}")
        
        # 按状态分类统计
        status_count = {}
        for order_id, order_info in all_orders.items():
            status = order_info['status']
            status_count[status] = status_count.get(status, 0) + 1
        
        log.info("状态分布:")
        for status, count in status_count.items():
            # 转换为内部格式显示
            internal_status = convert_order_status(status, to_external=False)
            log.info(f"  {status} ({internal_status}): {count}笔")
        
        # 显示版本兼容性信息
        version_info = get_version_info()
        log.info(f"当前版本: {version_info['version']} ({version_info['status_type']})")
    
    except Exception as e:
        log.warning(f"分析所有订单失败: {e}")


def before_trading_start(context, data):
    """盘前处理"""
    log.info("盘前准备 - 委托状态兼容性演示策略")
    
    # 显示版本信息
    version_info = get_version_info()
    log.info(f"当前使用ptrade版本: {version_info['version']}")


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
                log.info(f"持仓 {security}: {position['amount']}股, "
                        f"市值: {position['market_value']:.2f}")
    
    # 最终订单状态汇总
    log.info("=== 最终订单状态汇总 ===")
    all_orders = get_orders()
    trades = get_trades()
    
    log.info(f"当日总订单: {len(all_orders)}笔")
    log.info(f"当日成交: {len(trades)}笔")
    
    # 演示版本切换（仅作演示，实际使用中不建议频繁切换）
    if hasattr(context, 'current_dt') and context.current_dt.day % 2 == 0:
        log.info("演示版本切换功能:")
        
        # 切换到不同版本
        original_version = get_version_info()['version']
        
        if original_version == 'V005':
            demo_version = 'V041'
        else:
            demo_version = 'V005'
        
        set_ptrade_version(demo_version)
        new_version_info = get_version_info()
        log.info(f"切换版本: {original_version} -> {new_version_info['version']}")
        log.info(f"新版本状态类型: {new_version_info['status_type']}")
        
        # 切换回原版本
        set_ptrade_version(original_version)
        log.info(f"恢复版本: {original_version}")
