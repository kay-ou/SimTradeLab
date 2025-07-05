# SimTradeLab 策略开发指南

## 📖 概述

本指南将帮助您了解如何在SimTradeLab中开发和使用量化交易策略。SimTradeLab提供了完整的策略开发框架，支持多种交易频率和丰富的API接口。

## 🏗️ 策略结构

### 基本策略模板

```python
# -*- coding: utf-8 -*-
"""
策略名称和描述
"""

def initialize(context):
    """
    策略初始化函数
    在回测开始前调用一次，用于设置策略参数
    """
    # 设置股票池
    g.security = 'STOCK_A'
    
    # 策略参数
    g.param1 = value1
    g.param2 = value2
    
    log.info("策略初始化完成")


def handle_data(context, data):
    """
    主策略逻辑函数
    每个交易周期调用一次
    """
    security = g.security
    
    # 检查数据可用性
    if security not in data:
        return
    
    # 获取当前价格
    current_price = data[security]['close']
    
    # 策略逻辑
    # ...
    
    # 执行交易
    # order(security, amount)


def before_trading_start(context, data):
    """
    盘前处理函数（可选）
    每个交易日开始前调用
    """
    log.info("盘前准备")


def after_trading_end(context, data):
    """
    盘后处理函数（可选）
    每个交易日结束后调用
    """
    log.info("盘后总结")
```

## 🔧 核心API接口

### 交易接口

```python
# 下单
order_id = order(security, amount)                    # 市价单
order_id = order(security, amount, limit_price=price) # 限价单

# 目标仓位下单
order_target(security, target_amount)                 # 调整到目标数量
order_value(security, target_value)                   # 调整到目标市值

# 撤单
cancel_order(order_id)
```

### 查询接口

```python
# 持仓查询
positions = get_positions()           # 所有持仓
position = get_position(security)     # 单个股票持仓

# 订单查询
orders = get_orders()                 # 当日所有订单
open_orders = get_open_orders()       # 未完成订单
order_info = get_order(order_id)      # 特定订单信息

# 成交查询
trades = get_trades()                 # 当日成交记录
```

### 数据接口

```python
# 历史数据
hist_data = get_history(days, frequency, fields, security)

# 当前数据
current_data = get_current_data(security)
price = get_price(security)

# 技术指标
macd_data = get_MACD(security, fast=12, slow=26, signal=9)
kdj_data = get_KDJ(security, period=9)
rsi_data = get_RSI(security, period=14)
cci_data = get_CCI(security, period=20)
```

## 📊 内置策略示例

### 1. 买入持有策略

```python
def initialize(context):
    g.security = 'STOCK_A'
    g.has_bought = False

def handle_data(context, data):
    if not g.has_bought:
        # 用90%资金买入
        cash = context.portfolio.cash
        price = data[g.security]['close']
        shares = int(cash * 0.9 / price / 100) * 100
        order(g.security, shares)
        g.has_bought = True
```

### 2. 双均线策略

```python
def initialize(context):
    g.security = 'STOCK_A'
    g.short_window = 5
    g.long_window = 20

def handle_data(context, data):
    # 获取历史数据
    hist_data = get_history(30, '1d', 'close', g.security)
    prices = hist_data[g.security]
    
    # 计算均线
    ma_short = prices.rolling(g.short_window).mean().iloc[-1]
    ma_long = prices.rolling(g.long_window).mean().iloc[-1]
    
    # 交易信号
    position = get_position(g.security)
    current_shares = position['amount'] if position else 0
    
    if ma_short > ma_long and current_shares == 0:
        # 金叉买入
        order(g.security, 1000)
    elif ma_short < ma_long and current_shares > 0:
        # 死叉卖出
        order(g.security, -current_shares)
```

### 3. 技术指标策略

```python
def initialize(context):
    g.security = 'STOCK_A'

def handle_data(context, data):
    # 获取技术指标
    macd_data = get_MACD(g.security)
    rsi_data = get_RSI(g.security)
    
    if macd_data.empty or rsi_data.empty:
        return
    
    macd_hist = macd_data['MACD_HIST'].iloc[-1]
    rsi = rsi_data['RSI'].iloc[-1]
    
    position = get_position(g.security)
    current_shares = position['amount'] if position else 0
    
    # 多重信号确认
    if macd_hist > 0 and rsi < 30 and current_shares == 0:
        # MACD金叉 + RSI超卖
        order(g.security, 1000)
    elif macd_hist < 0 and rsi > 70 and current_shares > 0:
        # MACD死叉 + RSI超买
        order(g.security, -current_shares)
```

## 🎯 策略开发最佳实践

### 1. 参数设置

```python
def initialize(context):
    # 使用有意义的变量名
    g.stock_pool = ['STOCK_A', 'STOCK_B']
    g.position_ratio = 0.8        # 最大仓位比例
    g.stop_loss_ratio = 0.05      # 止损比例
    g.rebalance_frequency = 5     # 调仓频率（天）
    
    # 策略状态变量
    g.last_rebalance_date = None
    g.trade_count = 0
```

### 2. 风险控制

```python
def handle_data(context, data):
    # 资金管理
    available_cash = context.portfolio.cash
    max_position_value = available_cash * g.position_ratio
    
    # 止损检查
    position = get_position(g.security)
    if position and position['pnl_ratio'] < -g.stop_loss_ratio:
        order(g.security, -position['amount'])
        log.info(f"止损卖出: {position['amount']}股")
```

### 3. 日志记录

```python
def handle_data(context, data):
    current_price = data[g.security]['close']
    
    # 详细的日志记录
    log.info(f"当前价格: {current_price:.2f}")
    log.info(f"账户总值: {context.portfolio.total_value:,.2f}")
    
    # 交易日志
    if order_id:
        log.info(f"下单成功: 订单ID {order_id}")
```

### 4. 错误处理

```python
def handle_data(context, data):
    try:
        # 策略逻辑
        pass
    except Exception as e:
        log.error(f"策略执行出错: {e}")
        # 不要让异常中断回测
```

## 📈 高级策略模式

### 1. 多股票策略

```python
def initialize(context):
    g.stock_pool = ['STOCK_A', 'STOCK_B', 'STOCK_C']
    g.weights = [0.4, 0.3, 0.3]  # 权重分配

def handle_data(context, data):
    for i, security in enumerate(g.stock_pool):
        if security in data:
            target_value = context.portfolio.total_value * g.weights[i]
            order_value(security, target_value)
```

### 2. 动态调仓策略

```python
def handle_data(context, data):
    # 只在特定日期调仓
    if context.current_dt.day % g.rebalance_frequency == 0:
        rebalance_portfolio(context, data)

def rebalance_portfolio(context, data):
    # 重新计算权重
    # 执行调仓
    pass
```

### 3. 条件触发策略

```python
def handle_data(context, data):
    # 基于市场条件的策略切换
    volatility = calculate_volatility(data)
    
    if volatility > 0.02:
        # 高波动时使用保守策略
        conservative_strategy(context, data)
    else:
        # 低波动时使用激进策略
        aggressive_strategy(context, data)
```

## 🧪 策略测试

### 1. 单元测试

```python
def test_strategy():
    engine = BacktestEngine(
        strategy_file='strategies/my_strategy.py',
        data_path='data/test_data.csv',
        start_date='2023-01-01',
        end_date='2023-01-31',
        initial_cash=1000000.0
    )
    
    engine.run()
    
    # 验证结果
    assert engine.context.portfolio.total_value > 0
```

### 2. 参数优化

```python
def optimize_parameters():
    best_return = -1
    best_params = None
    
    for short_window in range(3, 8):
        for long_window in range(15, 25):
            # 测试参数组合
            result = test_strategy_with_params(short_window, long_window)
            if result > best_return:
                best_return = result
                best_params = (short_window, long_window)
    
    return best_params
```

## ⚠️ 注意事项

### 1. 数据质量
- 确保数据完整性和准确性
- 处理缺失数据和异常值
- 注意前复权和后复权的影响

### 2. 过拟合风险
- 避免过度优化历史数据
- 使用样本外测试验证策略
- 保持策略的简洁性

### 3. 交易成本
- 考虑手续费和滑点影响
- 避免过度频繁交易
- 合理设置交易数量

### 4. 风险管理
- 设置止损和止盈
- 控制单笔交易风险
- 分散投资降低风险

## 📚 进阶学习

1. **量化投资理论**
   - 现代投资组合理论
   - 资本资产定价模型
   - 有效市场假说

2. **技术分析**
   - 趋势分析
   - 形态识别
   - 技术指标应用

3. **风险管理**
   - VaR计算
   - 最大回撤控制
   - 资金管理策略

4. **机器学习应用**
   - 特征工程
   - 模型训练和验证
   - 信号预测

通过本指南，您应该能够开始开发自己的量化交易策略。记住，成功的策略需要不断的测试、优化和改进。
