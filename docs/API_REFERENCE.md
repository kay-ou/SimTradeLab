# 文档已升级 📚

> **重要提示**: API参考文档已升级为更完整的统一文档。

请参考最新的完整文档：**[SimTradeLab API 完整参考文档](SIMTRADELAB_API_COMPLETE_REFERENCE.md)**

新的统一文档提供：
- 🎯 **完整API覆盖** - 所有接口的详细说明
- 🔄 **PTrade兼容性** - 与PTrade API的完全兼容说明
- 💡 **丰富示例** - 实际策略开发示例
- ⚙️ **配置指南** - 数据源和系统配置
- 📊 **报告系统** - 回测报告的生成和解读
- ⌨️ **CLI工具** - 命令行工具完整指南

---

## 原有API参考内容

以下内容已整合到新的统一文档中：

# SimTradeLab API 参考文档

本文档详细介绍了 SimTradeLab 提供的所有API接口。

## 📊 数据接口

### 财务数据接口

#### get_fundamentals()
获取基本面财务数据

```python
def get_fundamentals(stocks, table, fields=None, date=None, start_year=None, end_year=None):
    """
    获取财务基本面数据
    
    Args:
        stocks: 股票代码或股票列表
        table: 数据表名（暂时忽略，返回所有数据）
        fields: 字段列表，None表示返回所有字段
        date: 查询日期
        start_year: 开始年份
        end_year: 结束年份
    
    Returns:
        DataFrame: 财务数据
    """
```

**支持的财务指标（30+）：**
- 估值指标：`market_cap`, `pe_ratio`, `pb_ratio`, `ps_ratio`, `pcf_ratio`
- 盈利指标：`revenue`, `net_income`, `eps`, `roe`, `roa`
- 财务健康：`debt_to_equity`, `current_ratio`, `quick_ratio`
- 现金流：`operating_cash_flow`, `free_cash_flow`

#### get_income_statement()
获取损益表数据

```python
def get_income_statement(stocks, fields=None, date=None, count=4):
    """
    获取损益表数据
    
    Args:
        stocks: 股票代码或股票列表
        fields: 字段列表
        date: 查询日期
        count: 返回期数
    
    Returns:
        DataFrame: 损益表数据
    """
```

#### get_balance_sheet()
获取资产负债表数据

```python
def get_balance_sheet(stocks, fields=None, date=None, count=4):
    """
    获取资产负债表数据
    
    Args:
        stocks: 股票代码或股票列表
        fields: 字段列表
        date: 查询日期
        count: 返回期数
    
    Returns:
        DataFrame: 资产负债表数据
    """
```

#### get_cash_flow()
获取现金流量表数据

```python
def get_cash_flow(stocks, fields=None, date=None, count=4):
    """
    获取现金流量表数据
    
    Args:
        stocks: 股票代码或股票列表
        fields: 字段列表
        date: 查询日期
        count: 返回期数
    
    Returns:
        DataFrame: 现金流量表数据
    """
```

#### get_financial_ratios()
获取财务比率数据

```python
def get_financial_ratios(stocks, ratios=None, date=None):
    """
    获取财务比率数据
    
    Args:
        stocks: 股票代码或股票列表
        ratios: 比率列表
        date: 查询日期
    
    Returns:
        DataFrame: 财务比率数据
    """
```

### 市场数据接口

#### get_history()
获取历史数据

```python
def get_history(count, frequency='1d', field='close', security_list=None, 
                fq=None, include=False, is_dict=False, start_date=None, end_date=None):
    """
    获取历史数据
    
    Args:
        count: 数据条数
        frequency: 数据频率 ('1d', '1m', '5m', '15m', '30m', '1h', '1w', '1M')
        field: 数据字段
        security_list: 股票列表
        fq: 复权类型
        include: 是否包含当前数据
        is_dict: 是否返回字典格式
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        DataFrame: 历史数据
    """
```

#### get_price()
获取价格数据

```python
def get_price(security, start_date=None, end_date=None, frequency='1d', fields=None, count=None):
    """
    获取价格数据
    
    Args:
        security: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        frequency: 数据频率
        fields: 字段列表
        count: 数据条数
    
    Returns:
        DataFrame: 价格数据
    """
```

**支持的价格字段（15+）：**
- 基础字段：`open`, `high`, `low`, `close`, `volume`
- 扩展字段：`pre_close`, `change`, `pct_change`, `amplitude`
- 交易字段：`turnover_rate`, `amount`, `vwap`
- 限价字段：`high_limit`, `low_limit`

#### get_current_data()
获取当前实时数据

```python
def get_current_data(security=None):
    """
    获取当前实时市场数据
    
    Args:
        security: 股票代码，None表示所有股票
    
    Returns:
        dict: 实时数据字典
    """
```

#### get_market_snapshot()
获取市场快照

```python
def get_market_snapshot(securities=None, fields=None):
    """
    获取市场快照数据
    
    Args:
        securities: 股票列表
        fields: 字段列表
    
    Returns:
        DataFrame: 市场快照数据
    """
```

### 技术指标接口

#### get_technical_indicators()
通用技术指标计算

```python
def get_technical_indicators(security, indicators, period=20, **kwargs):
    """
    计算技术指标
    
    Args:
        security: 股票代码
        indicators: 指标名称或列表
        period: 计算周期
        **kwargs: 其他参数
    
    Returns:
        DataFrame: 技术指标数据
    """
```

#### 专用技术指标函数

```python
# MACD指标
def get_MACD(security, fast_period=12, slow_period=26, signal_period=9):
    """计算MACD指标"""

# KDJ指标  
def get_KDJ(security, period=9, k_period=3, d_period=3):
    """计算KDJ指标"""

# RSI指标
def get_RSI(security, period=14):
    """计算RSI指标"""

# CCI指标
def get_CCI(security, period=20):
    """计算CCI指标"""
```

## 🛠️ 交易接口

### 下单接口

#### order()
基础下单函数

```python
def order(security, amount, limit_price=None):
    """
    下单交易
    
    Args:
        security: 股票代码
        amount: 交易数量（正数买入，负数卖出）
        limit_price: 限价，None表示市价单
    
    Returns:
        str: 订单ID
    """
```

#### order_target()
目标仓位下单

```python
def order_target(security, target_amount):
    """
    调整到目标仓位
    
    Args:
        security: 股票代码
        target_amount: 目标持仓数量
    
    Returns:
        str: 订单ID
    """
```

#### order_value()
目标市值下单

```python
def order_value(security, target_value):
    """
    调整到目标市值
    
    Args:
        security: 股票代码
        target_value: 目标持仓市值
    
    Returns:
        str: 订单ID
    """
```

#### cancel_order()
撤单

```python
def cancel_order(order_param):
    """
    撤销订单
    
    Args:
        order_param: 订单ID或订单对象
    
    Returns:
        bool: 撤单是否成功
    """
```

### 查询接口

#### get_positions()
获取持仓信息

```python
def get_positions(securities=None):
    """
    获取持仓信息
    
    Args:
        securities: 股票列表，None表示所有持仓
    
    Returns:
        dict: 持仓信息字典
    """
```

#### get_orders()
获取订单信息

```python
def get_orders(order_id=None):
    """
    获取订单信息
    
    Args:
        order_id: 订单ID，None表示所有订单
    
    Returns:
        dict: 订单信息
    """
```

#### get_trades()
获取成交记录

```python
def get_trades():
    """
    获取当日成交记录
    
    Returns:
        list: 成交记录列表
    """
```

## 🔧 工具接口

### 交易日历

```python
def get_trading_day(date, offset=0):
    """获取交易日"""

def get_all_trades_days():
    """获取所有交易日"""

def get_trade_days(start_date, end_date):
    """获取指定期间的交易日"""
```

### 基准设置

```python
def set_benchmark(security):
    """设置基准股票"""

def get_benchmark_returns():
    """获取基准收益率"""
```

### 版本兼容

```python
def set_ptrade_version(version):
    """设置ptrade版本"""

def get_version_info():
    """获取版本信息"""
```

## 📈 性能分析接口

```python
def calculate_performance_metrics(portfolio_values, benchmark_values=None):
    """计算性能指标"""

def print_performance_report(context):
    """打印性能报告"""

def get_performance_summary(context):
    """获取性能摘要"""
```

## 🔍 使用示例

### 基础数据获取

```python
# 获取财务数据
fundamentals = get_fundamentals(['STOCK_A'], 'fundamentals', ['pe_ratio', 'roe'])

# 获取历史价格
history = get_history(30, '1d', 'close', ['STOCK_A'])

# 获取技术指标
macd_data = get_MACD('STOCK_A', fast_period=12, slow_period=26)
```

### 交易操作

```python
# 市价买入1000股
order_id = order('STOCK_A', 1000)

# 限价卖出500股
order_id = order('STOCK_A', -500, limit_price=10.50)

# 调整到目标仓位
order_target('STOCK_A', 2000)

# 查询持仓
positions = get_positions()
```

---

更多详细示例请参考 [策略开发指南](STRATEGY_GUIDE.md) 和 [策略示例集](STRATEGY_EXAMPLES.md)。
