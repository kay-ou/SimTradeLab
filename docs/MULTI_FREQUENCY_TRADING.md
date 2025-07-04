# 多频率交易指南

ptradeSim 支持多种交易频率，从分钟级到月线级别，满足不同策略的需求。

## 🕐 支持的交易频率

### 基础频率
- **日线级**: `1d`, `daily` - 默认频率，适合中长期策略
- **分钟级**: `1m`, `minute` - 高频交易，适合日内策略
- **5分钟级**: `5m`, `5min` - 短期交易
- **15分钟级**: `15m`, `15min` - 中短期交易
- **30分钟级**: `30m`, `30min` - 中期交易

### 扩展频率
- **小时级**: `1h`, `hour` - 中期策略
- **周线级**: `1w`, `week` - 长期策略
- **月线级**: `1M`, `month` - 超长期策略

## 🚀 快速开始

### 创建分钟级策略

```python
from ptradeSim.engine import BacktestEngine

# 创建1分钟级回测引擎
engine = BacktestEngine(
    strategy_file='strategies/minute_trading_strategy.py',
    data_path='data/sample_data.csv',
    start_date='2023-01-01',
    end_date='2023-01-03',
    initial_cash=1000000.0,
    frequency='1m'  # 关键：设置为分钟级
)

engine.run()
```

### 分钟级策略示例

```python
# -*- coding: utf-8 -*-
"""
分钟级均线交易策略
"""

def initialize(context):
    """策略初始化"""
    g.security = 'STOCK_A'
    g.short_ma = 5   # 5分钟均线
    g.long_ma = 20   # 20分钟均线
    g.position_ratio = 0.3  # 每次交易30%资金
    
    log.info("分钟级策略初始化完成")

def handle_data(context, data):
    """分钟级交易逻辑"""
    security = g.security
    
    if security not in data:
        return
    
    # 获取分钟级历史数据
    hist_data = get_history(g.long_ma + 5, '1m', 'close', security)
    
    if len(hist_data) < g.long_ma:
        return
    
    # 计算分钟级均线
    prices = hist_data[security]
    ma_short = prices.rolling(g.short_ma).mean().iloc[-1]
    ma_long = prices.rolling(g.long_ma).mean().iloc[-1]
    
    current_position = get_position(security)
    current_shares = current_position['amount'] if current_position else 0
    current_price = data[security]['close']
    
    # 分钟级交易信号
    if ma_short > ma_long and current_shares == 0:
        # 金叉买入
        cash_to_use = context.portfolio.cash * g.position_ratio
        shares_to_buy = int(cash_to_use / current_price)
        
        if shares_to_buy > 0:
            order(security, shares_to_buy)
            log.info(f"分钟级金叉买入: {shares_to_buy}股 @ {current_price:.2f}")
    
    elif ma_short < ma_long and current_shares > 0:
        # 死叉卖出
        order_target(security, 0)
        log.info(f"分钟级死叉卖出: 全部持仓 @ {current_price:.2f}")

def before_trading_start(context, data):
    """盘前准备"""
    log.info(f"开始新的交易日: {context.current_dt.date()}")

def after_trading_end(context, data):
    """盘后总结"""
    total_value = context.portfolio.total_value
    daily_return = (total_value / context.portfolio.starting_cash - 1) * 100
    log.info(f"交易日结束 - 总资产: {total_value:,.2f}, 收益率: {daily_return:.2f}%")
```

## 📊 数据自动生成

### 从日线生成分钟级数据

当使用分钟级频率但数据源是日线时，ptradeSim会自动生成分钟级数据：

```python
# 即使数据文件是日线数据，也可以进行分钟级回测
engine = BacktestEngine(
    strategy_file='strategies/minute_strategy.py',
    data_path='data/sample_data.csv',  # 日线数据
    frequency='1m',  # 分钟级回测
    # 系统会自动生成分钟级数据
)
```

### 数据生成规则

1. **开盘价**: 使用前一日收盘价作为当日开盘价
2. **收盘价**: 使用当日收盘价
3. **最高价/最低价**: 在开盘价和收盘价之间随机生成
4. **成交量**: 将日成交量平均分配到各分钟
5. **时间戳**: 生成标准的分钟级时间戳

## 🔧 高级功能

### 多频率数据获取

```python
def handle_data(context, data):
    security = 'STOCK_A'
    
    # 获取不同频率的数据
    minute_data = get_history(60, '1m', 'close', security)  # 1小时的分钟数据
    hourly_data = get_history(24, '1h', 'close', security)  # 24小时数据
    daily_data = get_history(30, '1d', 'close', security)   # 30天数据
    
    # 多时间框架分析
    minute_trend = minute_data[security].iloc[-1] > minute_data[security].iloc[-10]
    hourly_trend = hourly_data[security].iloc[-1] > hourly_data[security].iloc[-5]
    daily_trend = daily_data[security].iloc[-1] > daily_data[security].iloc[-10]
    
    # 多重时间框架确认
    if minute_trend and hourly_trend and daily_trend:
        log.info("多时间框架上涨趋势确认")
```

### 分钟级技术指标

```python
def handle_data(context, data):
    security = 'STOCK_A'
    
    # 分钟级MACD
    macd_data = get_MACD(security, fast_period=12, slow_period=26)
    
    # 分钟级RSI
    rsi_data = get_RSI(security, period=14)
    
    if macd_data.empty or rsi_data.empty:
        return
    
    macd_hist = macd_data['MACD_HIST'].iloc[-1]
    rsi = rsi_data['RSI'].iloc[-1]
    
    # 分钟级信号组合
    if macd_hist > 0 and rsi < 70:
        log.info(f"分钟级买入信号: MACD={macd_hist:.4f}, RSI={rsi:.2f}")
```

### 日内交易控制

```python
def handle_data(context, data):
    """日内交易策略"""
    current_time = context.current_dt.time()
    
    # 只在特定时间段交易
    if current_time < pd.Timestamp('09:30').time():
        return  # 开盘前不交易
    
    if current_time > pd.Timestamp('14:30').time():
        # 收盘前平仓
        for security in context.portfolio.positions:
            if context.portfolio.positions[security].amount > 0:
                order_target(security, 0)
                log.info(f"收盘前平仓: {security}")
        return
    
    # 正常交易时间的策略逻辑
    execute_trading_logic(context, data)
```

## 📈 性能优化

### 减少计算频率

```python
def initialize(context):
    g.last_calculation_time = None
    g.calculation_interval = 5  # 每5分钟计算一次

def handle_data(context, data):
    current_time = context.current_dt
    
    # 控制计算频率
    if (g.last_calculation_time is None or 
        (current_time - g.last_calculation_time).total_seconds() >= g.calculation_interval * 60):
        
        # 执行计算密集的操作
        perform_heavy_calculations(context, data)
        g.last_calculation_time = current_time
    
    # 执行轻量级的交易逻辑
    execute_simple_logic(context, data)
```

### 数据缓存

```python
def initialize(context):
    g.indicator_cache = {}
    g.cache_expiry = 5  # 缓存5分钟

def get_cached_indicator(security, indicator_type, **kwargs):
    """获取缓存的技术指标"""
    cache_key = f"{security}_{indicator_type}_{kwargs}"
    current_time = context.current_dt
    
    if cache_key in g.indicator_cache:
        cached_data, cache_time = g.indicator_cache[cache_key]
        if (current_time - cache_time).total_seconds() < g.cache_expiry * 60:
            return cached_data
    
    # 计算新的指标
    if indicator_type == 'MACD':
        data = get_MACD(security, **kwargs)
    elif indicator_type == 'RSI':
        data = get_RSI(security, **kwargs)
    
    # 更新缓存
    g.indicator_cache[cache_key] = (data, current_time)
    return data
```

## ⚠️ 注意事项

### 1. 数据质量
- 分钟级数据对质量要求更高
- 注意处理数据缺失和异常值
- 考虑交易时间和非交易时间

### 2. 交易成本
- 分钟级交易频率更高，交易成本影响更大
- 合理设置手续费和滑点
- 避免过度交易

### 3. 风险控制
- 设置止损和止盈
- 控制单笔交易规模
- 监控日内最大回撤

### 4. 系统性能
- 分钟级回测计算量大
- 优化策略逻辑减少计算
- 使用数据缓存提高效率

## 📚 实战案例

### 分钟级动量策略

```python
def initialize(context):
    g.security = 'STOCK_A'
    g.momentum_period = 10  # 10分钟动量
    g.threshold = 0.002     # 0.2%阈值

def handle_data(context, data):
    security = g.security
    
    # 获取分钟级数据
    hist_data = get_history(g.momentum_period + 1, '1m', 'close', security)
    
    if len(hist_data) < g.momentum_period + 1:
        return
    
    # 计算动量
    current_price = hist_data[security].iloc[-1]
    past_price = hist_data[security].iloc[-(g.momentum_period + 1)]
    momentum = (current_price / past_price - 1)
    
    current_position = get_position(security)
    current_shares = current_position['amount'] if current_position else 0
    
    # 动量交易信号
    if momentum > g.threshold and current_shares == 0:
        order_value(security, context.portfolio.cash * 0.5)
        log.info(f"动量买入: 动量={momentum:.4f}")
    
    elif momentum < -g.threshold and current_shares > 0:
        order_target(security, 0)
        log.info(f"动量卖出: 动量={momentum:.4f}")
```

更多分钟级策略示例请参考 [策略示例集](STRATEGY_EXAMPLES.md)。
