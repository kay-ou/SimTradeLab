# -*- coding: utf-8 -*-
"""
网格交易策略
在价格区间内设置多个买卖网格，通过高抛低吸获取收益
"""

def initialize(context):
    """策略初始化"""
    log.info("初始化网格交易策略")
    
    # 策略参数
    g.security = 'STOCK_A'
    g.grid_count = 5      # 网格数量
    g.grid_spacing = 0.02  # 网格间距（2%）
    g.base_amount = 200   # 每格交易数量
    
    # 网格状态
    g.center_price = None  # 中心价格
    g.grid_levels = []     # 网格价位
    g.grid_positions = {}  # 各网格持仓状态
    g.total_trades = 0     # 总交易次数
    
    log.info(f"设置股票池: {g.security}")
    log.info(f"网格数量: {g.grid_count}, 网格间距: {g.grid_spacing*100}%")
    log.info(f"每格交易数量: {g.base_amount}股")


def handle_data(context, data):
    """主策略逻辑"""
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    current_price = data[security]['close']
    
    try:
        # 初始化网格（首次运行）
        if g.center_price is None:
            _initialize_grid(current_price)
            log.info(f"初始化网格完成，中心价格: {g.center_price:.2f}")
            _log_grid_levels()
        
        log.info(f"当前价格: {current_price:.2f}")
        
        # 检查网格交易机会
        _check_grid_trading(context, current_price)
        
        # 显示当前网格状态
        _log_grid_status(current_price)
    
    except Exception as e:
        log.error(f"网格交易策略执行出错: {e}")


def _initialize_grid(current_price):
    """初始化网格"""
    g.center_price = current_price
    g.grid_levels = []
    g.grid_positions = {}
    
    # 计算网格价位
    for i in range(-g.grid_count//2, g.grid_count//2 + 1):
        if i == 0:
            continue  # 跳过中心价格
        
        grid_price = g.center_price * (1 + i * g.grid_spacing)
        g.grid_levels.append(grid_price)
        g.grid_positions[grid_price] = {
            'level': i,
            'price': grid_price,
            'is_buy_level': i < 0,  # 负数为买入网格，正数为卖出网格
            'executed': False,
            'amount': 0
        }
    
    # 按价格排序
    g.grid_levels.sort()


def _check_grid_trading(context, current_price):
    """检查网格交易机会"""
    current_position = get_position(g.security)
    current_shares = current_position['amount'] if current_position else 0
    
    for grid_price in g.grid_levels:
        grid_info = g.grid_positions[grid_price]
        
        if grid_info['is_buy_level'] and not grid_info['executed']:
            # 买入网格：价格跌到网格线以下
            if current_price <= grid_price:
                if context.portfolio.cash >= grid_price * g.base_amount:
                    order_id = order(g.security, g.base_amount)
                    if order_id:
                        grid_info['executed'] = True
                        grid_info['amount'] = g.base_amount
                        g.total_trades += 1
                        log.info(f"🟢 网格买入: 价格 {grid_price:.2f}, 数量 {g.base_amount}股 (第{g.total_trades}次交易)")
        
        elif not grid_info['is_buy_level'] and not grid_info['executed']:
            # 卖出网格：价格涨到网格线以上
            if current_price >= grid_price and current_shares >= g.base_amount:
                order_id = order(g.security, -g.base_amount)
                if order_id:
                    grid_info['executed'] = True
                    grid_info['amount'] = -g.base_amount
                    g.total_trades += 1
                    log.info(f"🔴 网格卖出: 价格 {grid_price:.2f}, 数量 {g.base_amount}股 (第{g.total_trades}次交易)")


def _log_grid_levels():
    """显示网格价位"""
    log.info("网格价位设置:")
    for grid_price in sorted(g.grid_levels, reverse=True):
        grid_info = g.grid_positions[grid_price]
        action = "卖出" if not grid_info['is_buy_level'] else "买入"
        log.info(f"  {action}网格: {grid_price:.2f}")


def _log_grid_status(current_price):
    """显示网格状态"""
    executed_grids = sum(1 for info in g.grid_positions.values() if info['executed'])
    total_grids = len(g.grid_positions)
    
    # 找到当前价格所在区间
    current_zone = "中心区域"
    for grid_price in g.grid_levels:
        if current_price <= grid_price:
            grid_info = g.grid_positions[grid_price]
            if grid_info['is_buy_level']:
                current_zone = f"买入区域 (网格{grid_price:.2f})"
            else:
                current_zone = f"卖出区域 (网格{grid_price:.2f})"
            break
    
    log.info(f"网格状态: {executed_grids}/{total_grids}已执行, 当前位置: {current_zone}")


def before_trading_start(context, data):
    """盘前处理"""
    log.info("盘前准备 - 网格交易策略")


def after_trading_end(context, data):
    """盘后处理"""
    # 记录当日状态
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash
    
    log.info(f"盘后总结 - 总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
    
    # 显示持仓情况
    position = get_position(g.security)
    if position and position['amount'] > 0:
        log.info(f"持仓 {g.security}: {position['amount']}股, "
                f"成本价: {position['cost_basis']:.2f}, "
                f"市值: {position['market_value']:.2f}")
    else:
        log.info("当前无持仓")
    
    # 网格交易统计
    executed_count = sum(1 for info in g.grid_positions.values() if info['executed'])
    buy_executed = sum(1 for info in g.grid_positions.values() 
                      if info['executed'] and info['is_buy_level'])
    sell_executed = sum(1 for info in g.grid_positions.values() 
                       if info['executed'] and not info['is_buy_level'])
    
    log.info(f"网格交易统计: 总交易{g.total_trades}次, "
            f"已执行网格{executed_count}个 (买入{buy_executed}个, 卖出{sell_executed}个)")
    
    # 显示价格偏离度
    if g.center_price:
        current_position = get_position(g.security)
        if current_position:
            current_price = current_position['last_sale_price']
            deviation = (current_price - g.center_price) / g.center_price
            log.info(f"价格偏离中心: {deviation:.2%} (中心价{g.center_price:.2f} -> 当前价{current_price:.2f})")
