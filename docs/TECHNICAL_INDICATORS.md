# 技术指标使用指南

SimTradeLab 提供了丰富的技术指标计算功能，支持多种经典的技术分析指标。

## 📊 支持的技术指标

### 趋势指标

#### 移动平均线 (MA)
```python
# 通过 get_technical_indicators 计算
ma_data = get_technical_indicators('STOCK_A', 'MA', period=20)

# 或者通过历史数据计算
hist_data = get_history(30, '1d', 'close', 'STOCK_A')
ma_20 = hist_data['STOCK_A'].rolling(20).mean()
```

#### 指数移动平均线 (EMA)
```python
ema_data = get_technical_indicators('STOCK_A', 'EMA', period=12)
```

#### MACD (异同移动平均线)
```python
# 使用专用函数
macd_data = get_MACD('STOCK_A', fast_period=12, slow_period=26, signal_period=9)

# 返回字段：MACD_DIF, MACD_DEA, MACD_HIST
dif = macd_data['MACD_DIF'].iloc[-1]
dea = macd_data['MACD_DEA'].iloc[-1]
hist = macd_data['MACD_HIST'].iloc[-1]

# 交易信号
if hist > 0 and macd_data['MACD_HIST'].iloc[-2] <= 0:
    log.info("MACD金叉信号")
```

### 动量指标

#### RSI (相对强弱指标)
```python
# 使用专用函数
rsi_data = get_RSI('STOCK_A', period=14)

# 获取最新RSI值
current_rsi = rsi_data['RSI'].iloc[-1]

# 交易信号
if current_rsi < 30:
    log.info("RSI超卖信号")
elif current_rsi > 70:
    log.info("RSI超买信号")
```

#### CCI (商品通道指标)
```python
cci_data = get_CCI('STOCK_A', period=20)
current_cci = cci_data['CCI'].iloc[-1]

# CCI信号判断
if current_cci > 100:
    log.info("CCI超买信号")
elif current_cci < -100:
    log.info("CCI超卖信号")
```

### 摆动指标

#### KDJ (随机指标)
```python
# 使用专用函数
kdj_data = get_KDJ('STOCK_A', period=9, k_period=3, d_period=3)

# 返回字段：K, D, J
k_value = kdj_data['K'].iloc[-1]
d_value = kdj_data['D'].iloc[-1]
j_value = kdj_data['J'].iloc[-1]

# KDJ交易信号
if k_value > d_value and kdj_data['K'].iloc[-2] <= kdj_data['D'].iloc[-2]:
    log.info("KDJ金叉信号")
```

### 波动率指标

#### 布林带 (BOLL)
```python
boll_data = get_technical_indicators('STOCK_A', 'BOLL', period=20, std_dev=2)

# 返回字段：BOLL_UPPER, BOLL_MIDDLE, BOLL_LOWER
upper = boll_data['BOLL_UPPER'].iloc[-1]
middle = boll_data['BOLL_MIDDLE'].iloc[-1]
lower = boll_data['BOLL_LOWER'].iloc[-1]

# 当前价格
current_price = get_current_data('STOCK_A')['close']

# 布林带信号
if current_price <= lower:
    log.info("价格触及布林带下轨，可能反弹")
elif current_price >= upper:
    log.info("价格触及布林带上轨，可能回调")
```

## 🔧 技术指标组合策略

### 多指标确认策略

```python
def handle_data(context, data):
    security = 'STOCK_A'
    
    # 获取多个技术指标
    macd_data = get_MACD(security)
    rsi_data = get_RSI(security, period=14)
    kdj_data = get_KDJ(security)
    
    if macd_data.empty or rsi_data.empty or kdj_data.empty:
        return
    
    # 获取最新指标值
    macd_hist = macd_data['MACD_HIST'].iloc[-1]
    rsi = rsi_data['RSI'].iloc[-1]
    k_value = kdj_data['K'].iloc[-1]
    d_value = kdj_data['D'].iloc[-1]
    
    current_position = get_position(security)
    current_shares = current_position['amount'] if current_position else 0
    
    # 多重买入信号确认
    buy_signals = [
        macd_hist > 0,  # MACD金叉
        rsi < 70,       # RSI未超买
        k_value > d_value  # KDJ金叉
    ]
    
    # 多重卖出信号确认
    sell_signals = [
        macd_hist < 0,  # MACD死叉
        rsi > 30,       # RSI未超卖
        k_value < d_value  # KDJ死叉
    ]
    
    # 买入条件：至少2个买入信号
    if sum(buy_signals) >= 2 and current_shares == 0:
        order_value(security, context.portfolio.cash * 0.3)
        log.info(f"多指标买入信号确认: MACD={macd_hist:.4f}, RSI={rsi:.2f}, KDJ=({k_value:.2f},{d_value:.2f})")
    
    # 卖出条件：至少2个卖出信号
    elif sum(sell_signals) >= 2 and current_shares > 0:
        order_target(security, 0)
        log.info(f"多指标卖出信号确认: MACD={macd_hist:.4f}, RSI={rsi:.2f}, KDJ=({k_value:.2f},{d_value:.2f})")
```

### 趋势跟踪策略

```python
def handle_data(context, data):
    security = 'STOCK_A'
    
    # 获取移动平均线
    ma_short = get_technical_indicators(security, 'MA', period=5)
    ma_long = get_technical_indicators(security, 'MA', period=20)
    
    if ma_short.empty or ma_long.empty:
        return
    
    # 获取最新均线值
    ma5 = ma_short['MA5'].iloc[-1]
    ma20 = ma_long['MA20'].iloc[-1]
    
    # 获取MACD确认趋势
    macd_data = get_MACD(security)
    macd_dif = macd_data['MACD_DIF'].iloc[-1]
    
    current_position = get_position(security)
    current_shares = current_position['amount'] if current_position else 0
    
    # 上升趋势：短期均线上穿长期均线 + MACD DIF > 0
    if ma5 > ma20 and macd_dif > 0 and current_shares == 0:
        order_value(security, context.portfolio.cash * 0.5)
        log.info(f"趋势跟踪买入: MA5={ma5:.2f} > MA20={ma20:.2f}, MACD_DIF={macd_dif:.4f}")
    
    # 下降趋势：短期均线下穿长期均线 + MACD DIF < 0
    elif ma5 < ma20 and macd_dif < 0 and current_shares > 0:
        order_target(security, 0)
        log.info(f"趋势跟踪卖出: MA5={ma5:.2f} < MA20={ma20:.2f}, MACD_DIF={macd_dif:.4f}")
```

### 超买超卖策略

```python
def handle_data(context, data):
    security = 'STOCK_A'
    
    # 获取RSI和CCI指标
    rsi_data = get_RSI(security, period=14)
    cci_data = get_CCI(security, period=20)
    
    if rsi_data.empty or cci_data.empty:
        return
    
    rsi = rsi_data['RSI'].iloc[-1]
    cci = cci_data['CCI'].iloc[-1]
    
    current_position = get_position(security)
    current_shares = current_position['amount'] if current_position else 0
    
    # 超卖信号：RSI < 30 且 CCI < -100
    if rsi < 30 and cci < -100 and current_shares == 0:
        order_value(security, context.portfolio.cash * 0.4)
        log.info(f"超卖买入信号: RSI={rsi:.2f}, CCI={cci:.2f}")
    
    # 超买信号：RSI > 70 且 CCI > 100
    elif rsi > 70 and cci > 100 and current_shares > 0:
        order_target(security, 0)
        log.info(f"超买卖出信号: RSI={rsi:.2f}, CCI={cci:.2f}")
```

## 📈 技术指标参数优化

### 参数敏感性测试

```python
def test_ma_parameters():
    """测试移动平均线参数的敏感性"""
    results = {}
    
    for short_period in range(3, 10):
        for long_period in range(15, 30):
            if short_period >= long_period:
                continue
                
            # 创建测试策略
            strategy_params = {
                'short_ma': short_period,
                'long_ma': long_period
            }
            
            # 运行回测
            result = run_backtest_with_params(strategy_params)
            results[(short_period, long_period)] = result
    
    # 找出最优参数
    best_params = max(results.items(), key=lambda x: x[1]['total_return'])
    log.info(f"最优MA参数: 短期={best_params[0][0]}, 长期={best_params[0][1]}")
    
    return best_params
```

### RSI参数优化

```python
def optimize_rsi_parameters():
    """优化RSI参数"""
    best_return = -1
    best_params = None
    
    for period in range(10, 25):
        for oversold in range(20, 35):
            for overbought in range(65, 85):
                if oversold >= overbought:
                    continue
                
                params = {
                    'rsi_period': period,
                    'oversold_threshold': oversold,
                    'overbought_threshold': overbought
                }
                
                result = test_rsi_strategy(params)
                if result > best_return:
                    best_return = result
                    best_params = params
    
    return best_params
```

## ⚠️ 使用注意事项

### 1. 数据充足性
```python
# 确保有足够的历史数据计算指标
def check_data_sufficiency(security, indicator_period):
    hist_data = get_history(indicator_period * 2, '1d', 'close', security)
    if len(hist_data) < indicator_period:
        log.warning(f"数据不足，无法计算{indicator_period}期指标")
        return False
    return True
```

### 2. 指标滞后性
```python
# 技术指标都有滞后性，需要结合其他信息
def handle_data(context, data):
    # 获取技术指标
    macd_data = get_MACD('STOCK_A')
    
    # 结合价格行为确认信号
    current_price = data['STOCK_A']['close']
    prev_price = get_history(2, '1d', 'close', 'STOCK_A')['STOCK_A'].iloc[-2]
    
    # 价格突破确认技术信号
    if macd_data['MACD_HIST'].iloc[-1] > 0 and current_price > prev_price:
        log.info("技术指标与价格行为双重确认")
```

### 3. 市场环境适应性
```python
# 不同市场环境下指标效果不同
def adaptive_strategy(context, data):
    # 计算市场波动率
    hist_data = get_history(20, '1d', 'close', 'STOCK_A')
    volatility = hist_data['STOCK_A'].pct_change().std()
    
    if volatility > 0.03:  # 高波动市场
        # 使用更敏感的参数
        rsi_data = get_RSI('STOCK_A', period=10)
    else:  # 低波动市场
        # 使用更稳定的参数
        rsi_data = get_RSI('STOCK_A', period=20)
```

## 📚 进阶学习

1. **技术分析理论基础**
2. **指标组合优化方法**
3. **机器学习在技术指标中的应用**
4. **高频交易中的技术指标**

更多技术指标应用案例请参考 [策略示例集](STRATEGY_EXAMPLES.md)。
