# SimTradeLab API 完整参考文档

<div align="center">

**开源策略回测框架 - 完整API参考手册**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)](#版本信息)

*灵感来自PTrade的事件驱动模型，提供轻量、清晰、可插拔的策略验证环境*

</div>

## 📖 目录

- [项目概述](#项目概述)
- [快速开始](#快速开始)
- [策略开发框架](#策略开发框架)
- [数据接口API](#数据接口api)
- [交易接口API](#交易接口api)
- [工具函数API](#工具函数api)
- [技术指标API](#技术指标api)
- [高级功能API](#高级功能api)
- [数据结构](#数据结构)
- [配置系统](#配置系统)
- [报告系统](#报告系统)
- [命令行工具](#命令行工具)
- [使用示例](#使用示例)
- [PTrade兼容性](#ptrade兼容性)
- [注意事项](#注意事项)

---

## 📈 项目概述

SimTradeLab（深测Lab）是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动架构。它具备完全自主的实现与出色的扩展能力，为策略开发者提供一个轻量级、结构清晰、模块可插拔的策略验证环境。

### ✨ 核心特性

- 🔧 **事件驱动引擎**: 完整的回测引擎实现，支持 `initialize`、`handle_data`、`before_trading_start`、`after_trading_end` 等事件
- 📊 **多格式报告**: TXT、JSON、CSV、HTML、摘要、图表等6种格式的完整分析报告
- 🌐 **真实数据源**: 支持 AkShare、Tushare、CSV 等多种数据源
- ⚡ **智能CLI**: 集成的 `simtradelab` 命令行工具，快速启动回测
- ✅ **PTrade兼容**: 保持与PTrade语法习惯的高度兼容性
- 📈 **可视化报告**: HTML交互式报告和matplotlib图表

### 🎯 设计理念

框架无需依赖 PTrade 即可独立运行，但与其语法保持高度兼容。**所有在 SimTradeLab 中编写的策略可无缝迁移至 PTrade 平台，反之亦然，两者之间的 API 可直接互通使用。**

---

## 🚀 快速开始

### 📦 安装

```bash
# 克隆项目
git clone https://github.com/kay-ou/SimTradeLab.git
cd SimTradeLab

# 安装依赖
poetry install

# 安装数据源依赖（可选）
poetry install --with data
```

### 🎯 5分钟上手

**1. 使用CSV数据源**
```bash
poetry run simtradelab --strategy strategies/buy_and_hold_strategy.py --data data/sample_data.csv
```

**2. 使用真实数据源**
```bash
poetry run simtradelab --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ
```

**3. 程序化使用**
```python
from simtradelab import BacktestEngine

engine = BacktestEngine(
    strategy_file='strategies/buy_and_hold_strategy.py',
    data_path='data/sample_data.csv',
    start_date='2023-01-03',
    end_date='2023-01-05',
    initial_cash=1000000.0
)
files = engine.run()
```

---

## 🏗️ 策略开发框架

### 业务流程框架

SimTradeLab以事件触发为基础，通过以下事件来完成每个交易日的策略任务：

- **initialize（必选）**: 策略初始化事件
- **before_trading_start（可选）**: 盘前事件  
- **handle_data（必选）**: 盘中事件
- **after_trading_end（可选）**: 盘后事件

### 基本策略结构

```python
def initialize(context):
    """策略初始化 - 必须实现"""
    # 设置股票池
    g.security = '000001.SZ'
    
    # 策略参数
    g.flag = False
    
    log.info("策略初始化完成")

def handle_data(context, data):
    """主策略逻辑 - 必须实现"""
    security = g.security
    
    # 获取当前价格
    current_price = data[security]['close']
    
    # 交易逻辑
    if not g.flag:
        order(security, 1000)
        g.flag = True
        log.info(f"买入 {security}")

def before_trading_start(context, data):
    """盘前处理 - 可选实现"""
    log.info("盘前准备")

def after_trading_end(context, data):
    """盘后处理 - 可选实现"""
    total_value = context.portfolio.total_value
    log.info(f"总资产: ¥{total_value:,.2f}")
```

### 策略运行周期

**频率支持：**
- **日线级别**: 每天运行一次，在盘后执行
- **分钟级别**: 每分钟运行一次，在每根分钟K线结束时执行
- **Tick级别**: 最小频率可达3秒运行一次（交易环境）

**时间划分：**
- **盘前运行**: 9:30之前，执行 `before_trading_start` 和 `run_daily` 指定的盘前函数
- **盘中运行**: 9:31-15:00，执行 `handle_data` 和 `run_interval` 函数
- **盘后运行**: 15:30之后，执行 `after_trading_end` 函数

---

## 📊 数据接口API

### 市场数据接口

#### get_history() - 获取历史数据

```python
get_history(count, frequency='1d', field=['open','high','low','close','volume','money','price'], 
           security_list=None, fq=None, include=False, fill='nan', is_dict=False, 
           start_date=None, end_date=None)
```

**功能说明：** 获取历史K线数据，与PTrade完全兼容

**参数：**
- `count` (int): K线数量，大于0
- `frequency` (str): K线周期，支持 '1d'、'1m'、'5m'、'15m'、'30m'、'60m'、'120m'、'1w'、'1M'
- `field` (str/list): 数据字段，支持 open, high, low, close, volume, money, price 等
- `security_list` (str/list): 股票代码列表，None表示股票池中所有股票
- `fq` (str): 复权类型，支持 'pre'(前复权)、'post'(后复权)、None(不复权)
- `include` (bool): 是否包含当前周期，默认False
- `fill` (str): 数据填充方式，'pre'或'nan'
- `is_dict` (bool): 是否返回字典格式，默认False

**返回值：** DataFrame 或 dict 格式的历史数据

**使用示例：**
```python
def handle_data(context, data):
    # 获取过去5天的收盘价
    df = get_history(5, '1d', 'close', '000001.SZ', fq=None, include=False)
    
    # 获取多字段数据
    df = get_history(10, '1d', ['open', 'high', 'low', 'close'], ['000001.SZ', '000002.SZ'])
    
    # 获取字典格式数据（取数更快）
    data_dict = get_history(20, '1d', 'close', '000001.SZ', is_dict=True)
```

#### get_price() - 获取价格数据

```python
get_price(security, start_date=None, end_date=None, frequency='1d', fields=None, count=None)
```

**功能说明：** 获取指定时间段的价格数据

**参数：**
- `security` (str/list): 股票代码或列表
- `start_date` (str): 开始日期，格式'YYYY-MM-DD'
- `end_date` (str): 结束日期，格式'YYYY-MM-DD'
- `frequency` (str): 数据频率
- `fields` (str/list): 字段列表
- `count` (int): 数据条数

**使用示例：**
```python
# 获取指定时间段的数据
df = get_price('000001.SZ', '2023-01-01', '2023-12-31', '1d', ['open', 'close'])

# 获取最近30天数据
df = get_price('000001.SZ', count=30, fields='close')
```

#### get_current_data() - 获取当前数据

```python
get_current_data(security=None)
```

**功能说明：** 获取当前实时市场数据

**参数：**
- `security` (str/list): 股票代码，None表示所有股票

**返回值：** 包含实时数据的字典

**使用示例：**
```python
# 获取单只股票当前数据
current = get_current_data('000001.SZ')
current_price = current['000001.SZ']['close']

# 获取所有股票当前数据
all_current = get_current_data()
```

### 高级市场数据API

#### get_snapshot() - 获取股票快照

```python
get_snapshot(stock)
```

**功能说明：** 获取股票快照数据，包含买卖五档

**使用示例：**
```python
snapshot = get_snapshot('000001.SZ')
bid1_price = snapshot['bid1']
ask1_price = snapshot['ask1']
```

#### get_individual_entrust() - 获取逐笔委托

```python
get_individual_entrust(stocks, start_time=None, end_time=None)
```

**功能说明：** 获取逐笔委托行情数据

#### get_individual_transaction() - 获取逐笔成交

```python
get_individual_transaction(stocks, start_time=None, end_time=None)
```

**功能说明：** 获取逐笔成交行情数据

#### get_gear_price() - 获取档位行情

```python
get_gear_price(security)
```

**功能说明：** 获取指定代码的档位行情价格，包含买卖五档详细信息

---

## 💼 交易接口API

### 下单接口

#### order() - 基础下单函数

```python
order(security, amount, limit_price=None, style=None)
```

**功能说明：** 按指定数量买卖股票，与PTrade完全兼容

**参数：**
- `security` (str): 股票代码
- `amount` (int): 交易数量，正数买入，负数卖出
- `limit_price` (float): 限价，None表示市价单
- `style`: 交易方式，可选

**返回值：** 订单ID字符串

**使用示例：**
```python
# 市价买入1000股
order_id = order('000001.SZ', 1000)

# 限价卖出500股
order_id = order('000001.SZ', -500, limit_price=12.50)
```

#### order_target() - 目标仓位下单

```python
order_target(security, target_amount, limit_price=None, style=None)
```

**功能说明：** 调整持仓到指定数量

**使用示例：**
```python
# 调整持仓到2000股
order_target('000001.SZ', 2000)

# 清仓
order_target('000001.SZ', 0)
```

#### order_value() - 目标价值下单

```python
order_value(security, target_value, limit_price=None, style=None)
```

**功能说明：** 按指定价值买卖股票

**使用示例：**
```python
# 买入价值10万元的股票
order_value('000001.SZ', 100000)
```

#### order_target_value() - 目标市值下单

```python
order_target_value(security, target_value, limit_price=None, style=None)
```

**功能说明：** 调整持仓到指定市值

### 订单管理

#### cancel_order() - 撤单

```python
cancel_order(order_param)
```

**功能说明：** 撤销订单

**参数：**
- `order_param`: 订单ID或订单对象

**使用示例：**
```python
# 下单后撤单
order_id = order('000001.SZ', 1000)
cancel_order(order_id)
```

#### get_orders() - 获取订单

```python
get_orders(order_id=None)
```

**功能说明：** 获取订单信息

#### get_open_orders() - 获取未完成订单

```python
get_open_orders()
```

**功能说明：** 获取所有未完成的订单

#### get_trades() - 获取成交记录

```python
get_trades()
```

**功能说明：** 获取当日所有成交记录

### 持仓查询

#### get_position() - 获取单只股票持仓

```python
get_position(security)
```

**功能说明：** 获取指定股票的持仓信息

**使用示例：**
```python
position = get_position('000001.SZ')
amount = position.amount
avg_cost = position.avg_cost
market_value = position.market_value
```

#### get_positions() - 获取所有持仓

```python
get_positions(securities=None)
```

**功能说明：** 获取持仓信息

**使用示例：**
```python
# 获取所有持仓
positions = get_positions()

# 获取指定股票持仓
positions = get_positions(['000001.SZ', '000002.SZ'])
```

---

## 🧮 技术指标API

### 通用技术指标接口

#### get_technical_indicators() - 批量技术指标

```python
get_technical_indicators(security, indicators, period=20, **kwargs)
```

**功能说明：** 计算多种技术指标

**参数：**
- `security` (str/list): 股票代码
- `indicators` (str/list): 指标名称列表
- `period` (int): 计算周期
- `**kwargs`: 其他参数

**支持的指标：**
- `MA`: 移动平均线
- `EMA`: 指数移动平均线
- `MACD`: 异同移动平均线
- `RSI`: 相对强弱指标
- `BOLL`: 布林带
- `KDJ`: 随机指标
- `CCI`: 顺势指标

### 专用技术指标函数

#### get_MACD() - MACD指标

```python
get_MACD(security, fast_period=12, slow_period=26, signal_period=9)
```

**功能说明：** 计算MACD技术指标（异同移动平均线）

**返回值：** 包含 MACD_DIF、MACD_DEA、MACD_HIST 的DataFrame

**使用示例：**
```python
def handle_data(context, data):
    # 计算MACD指标
    macd_data = get_MACD('000001.SZ', fast_period=12, slow_period=26)
    dif = macd_data[('MACD_DIF', '000001.SZ')].iloc[-1]
    dea = macd_data[('MACD_DEA', '000001.SZ')].iloc[-1]
    
    # 金叉买入信号
    if dif > dea:
        order_target_percent('000001.SZ', 0.8)
```

#### get_KDJ() - KDJ指标

```python
get_KDJ(security, k_period=9)
```

**功能说明：** 计算KDJ随机指标

**返回值：** 包含 KDJ_K、KDJ_D、KDJ_J 的DataFrame

#### get_RSI() - RSI指标

```python
get_RSI(security, period=14)
```

**功能说明：** 计算RSI相对强弱指标

#### get_CCI() - CCI指标

```python
get_CCI(security, period=20)
```

**功能说明：** 计算CCI顺势指标

---

## 🔧 工具函数API

### 配置设置

#### set_commission() - 设置交易手续费

```python
set_commission(commission_ratio=0.0003, min_commission=5.0, type="STOCK")
```

**功能说明：** 设置交易手续费率

**参数：**
- `commission_ratio` (float): 佣金费率，默认0.0003 (0.03%)
- `min_commission` (float): 最低佣金，默认5.0元
- `type` (str): 交易类型，默认"STOCK"

#### set_slippage() - 设置滑点

```python
set_slippage(slippage)
```

**功能说明：** 设置滑点比例

#### set_benchmark() - 设置基准

```python
set_benchmark(benchmark)
```

**功能说明：** 设置策略基准指数

**使用示例：**
```python
def initialize(context):
    # 设置沪深300为基准
    set_benchmark('000300.SH')
```

### 交易日历

#### get_trading_day() - 获取交易日

```python
get_trading_day(date=None, offset=0)
```

**功能说明：** 获取交易日期，支持偏移

**参数：**
- `date` (str): 基准日期，None表示当前日期
- `offset` (int): 偏移量，0表示当天，1表示下一交易日，-1表示上一交易日

#### get_all_trades_days() - 获取所有交易日

```python
get_all_trades_days()
```

**功能说明：** 获取全部交易日期列表

#### get_trade_days() - 获取指定范围交易日

```python
get_trade_days(start_date=None, end_date=None, count=None)
```

**功能说明：** 获取指定范围内的交易日期

### 股票信息查询

#### get_stock_info() - 获取股票信息

```python
get_stock_info(stocks, field=None)
```

**功能说明：** 获取股票基本信息

#### get_stock_blocks() - 获取股票板块

```python
get_stock_blocks(stock)
```

**功能说明：** 获取股票所属板块信息

#### check_limit() - 涨跌停检查

```python
check_limit(security)
```

**功能说明：** 检查股票涨跌停状态

**返回值：** 包含涨跌停状态的字典
```python
{
    'limit_up': bool,        # 是否涨停
    'limit_down': bool,      # 是否跌停
    'limit_up_price': float, # 涨停价
    'limit_down_price': float, # 跌停价
    'current_price': float,  # 当前价格
    'pct_change': float      # 涨跌幅
}
```

### 日志记录

#### log - 日志接口

```python
log.info(message)
log.warning(message)
log.error(message)
log.debug(message)
```

**功能说明：** 记录策略运行日志，与PTrade兼容

**使用示例：**
```python
def handle_data(context, data):
    log.info('策略开始执行')
    log.warning('资金不足警告')
    log.error('数据获取失败')
```

### 定时任务

#### run_daily() - 按日执行

```python
run_daily(func, time='09:30')
```

**功能说明：** 设置按日执行的定时任务

**参数：**
- `func`: 要执行的函数
- `time` (str): 执行时间，格式'HH:MM'

**使用示例：**
```python
def initialize(context):
    run_daily(before_market_open, time='09:15')

def before_market_open(context):
    log.info('盘前准备工作')
```

#### run_interval() - 按间隔执行

```python
run_interval(func, seconds)
```

**功能说明：** 设置按间隔执行的定时任务

### 文件和目录管理

#### create_dir() - 创建目录

```python
create_dir(user_path)
```

**功能说明：** 创建文件目录路径

#### get_user_name() - 获取账户名

```python
get_user_name()
```

**功能说明：** 获取登录终端的资金账号

#### permission_test() - 权限校验

```python
permission_test(permission_type="trade")
```

**功能说明：** 进行权限校验

---

## 🏦 高级功能API

### 期货交易

#### buy_open() - 期货买入开仓

```python
buy_open(contract, amount, limit_price=None, style=None)
```

#### sell_close() - 期货卖出平仓

```python
sell_close(contract, amount, limit_price=None, style=None)
```

#### sell_open() - 期货卖出开仓

```python
sell_open(contract, amount, limit_price=None, style=None)
```

#### buy_close() - 期货买入平仓

```python
buy_close(contract, amount, limit_price=None, style=None)
```

### 期权交易

#### option_exercise() - 期权行权

```python
option_exercise(option_code, amount)
```

#### get_opt_contracts() - 获取期权合约

```python
get_opt_contracts(underlying, last_date)
```

#### option_covered_lock() - 期权备兑锁定

```python
option_covered_lock(underlying, amount)
```

### ETF相关

#### get_etf_info() - 获取ETF信息

```python
get_etf_info(etf_code)
```

#### get_etf_stock_list() - 获取ETF成分券

```python
get_etf_stock_list(etf_code)
```

#### etf_purchase_redemption() - ETF申购赎回

```python
etf_purchase_redemption(etf_code, operation, amount)
```

### 融资融券

#### margincash_open() - 融资买入

```python
margincash_open(security, amount, limit_price=None, style=None)
```

#### margincash_close() - 卖券还款

```python
margincash_close(security, amount, limit_price=None, style=None)
```

#### marginsec_open() - 融券卖出

```python
marginsec_open(security, amount, limit_price=None, style=None)
```

#### marginsec_close() - 买券还券

```python
marginsec_close(security, amount, limit_price=None, style=None)
```

---

## 📋 数据结构

### Context对象

Context对象包含当前的账户信息和持仓信息，是策略函数的核心参数。

**主要属性：**
- `portfolio`: Portfolio对象，包含账户和持仓信息
- `current_dt`: 当前日期时间

**使用示例：**
```python
def handle_data(context, data):
    # 获取总资产
    total_value = context.portfolio.total_value
    # 获取可用资金
    cash = context.portfolio.cash
    # 获取当前时间
    current_time = context.current_dt
```

### Portfolio对象

Portfolio对象包含账户的资产和持仓信息。

**主要属性：**
- `total_value` (float): 总资产
- `cash` (float): 可用资金
- `positions` (dict): 持仓字典
- `market_value` (float): 持仓市值
- `starting_cash` (float): 初始资金

**使用示例：**
```python
def handle_data(context, data):
    portfolio = context.portfolio
    log.info(f'总资产: {portfolio.total_value}')
    log.info(f'可用资金: {portfolio.cash}')
    log.info(f'持仓市值: {portfolio.market_value}')
```

### Position对象

Position对象包含单个股票的持仓信息。

**主要属性：**
- `security` (str): 股票代码
- `amount` (int): 持仓数量
- `avg_cost` (float): 平均成本
- `cost_basis` (float): 成本基础
- `market_value` (float): 持仓市值

**使用示例：**
```python
def handle_data(context, data):
    position = get_position('000001.SZ')
    if position.amount > 0:
        log.info(f'持仓数量: {position.amount}')
        log.info(f'平均成本: {position.avg_cost}')
        log.info(f'持仓市值: {position.market_value}')
```

### Order对象

Order对象包含订单信息。

**主要属性：**
- `security` (str): 股票代码
- `amount` (int): 订单数量
- `price` (float): 订单价格
- `status` (str): 订单状态
- `order_id` (str): 订单ID

---

## ⚙️ 配置系统

### 配置文件结构

SimTradeLab使用YAML格式的配置文件 `simtradelab_config.yaml`:

```yaml
# 回测配置
backtest:
  initial_cash: 1000000.0
  commission_rate: 0.0003
  min_commission: 5.0
  slippage: 0.001
  frequency: "1d"
  
# 数据源配置
data_sources:
  csv:
    enabled: true
    data_path: "./data/sample_data.csv"
    encoding: "utf-8"
    
  akshare:
    enabled: true
    
  tushare:
    enabled: false
    token: "your_tushare_token_here"
    
default_data_source: "csv"

# 日志配置
logging:
  level: "INFO"
  file_handler: true
  log_dir: "./logs"
  
# 报告配置
reports:
  output_dir: "./reports"
  formats: ["txt", "json", "csv", "html"]
  include_charts: true
```

### 配置管理API

```python
from simtradelab.config_manager import load_config, get_config, save_config

# 加载配置
config = load_config('custom_config.yaml')

# 获取全局配置
config = get_config()

# 保存配置
save_config(config, 'output_config.yaml')
```

---

## 📊 报告系统

### 报告格式

每次回测后自动生成6种格式的报告：

1. **详细文本报告** (`.txt`) - 完整策略分析
2. **结构化数据** (`.json`) - 程序化分析
3. **数据表格** (`.csv`) - Excel分析
4. **交互式网页** (`.html`) - 现代化展示
5. **智能摘要** (`.summary.txt`) - 快速概览
6. **可视化图表** (`.png`) - 直观展示

### 报告内容

**基础信息：**
- 策略名称、运行时间、数据源
- 回测期间、初始资金、最终资产

**收益指标：**
- 总收益率、年化收益率
- 最大回撤、夏普比率
- 胜率、平均持仓天数

**风险指标：**
- 波动率、最大连续亏损
- VaR值、索提诺比率

**交易统计：**
- 总交易次数、盈利交易次数
- 平均盈利、平均亏损
- 手续费总计

---

## ⌨️ 命令行工具

### 基本用法

```bash
# 查看帮助
simtradelab --help

# CSV数据源回测
simtradelab --strategy strategies/test_strategy.py --data data/sample_data.csv

# 真实数据源回测
simtradelab --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ,000002.SZ
```

### 主要参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--strategy` | 策略文件路径 | `strategies/test_strategy.py` |
| `--data` | CSV数据文件 | `data/sample_data.csv` |
| `--data-source` | 真实数据源 | `akshare`, `tushare` |
| `--securities` | 股票代码列表 | `000001.SZ,000002.SZ` |
| `--start-date` | 开始日期 | `2023-01-01` |
| `--end-date` | 结束日期 | `2023-12-31` |
| `--cash` | 初始资金 | `1000000` |
| `--output-dir` | 报告输出目录 | `./custom_reports` |
| `--config` | 配置文件路径 | `custom_config.yaml` |

### 高级用法

```bash
# 指定多个参数
simtradelab \
  --strategy strategies/momentum_strategy.py \
  --data-source akshare \
  --securities 000001.SZ,000002.SZ,600519.SH \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --cash 1000000 \
  --output-dir ./my_reports \
  --config custom_config.yaml

# 批量回测（使用脚本）
for strategy in strategies/*.py; do
  simtradelab --strategy "$strategy" --data data/sample_data.csv
done
```

---

## 💡 使用示例

### 基础买入持有策略

```python
def initialize(context):
    """初始化策略"""
    g.security = '000001.SZ'
    g.bought = False
    log.info("买入持有策略初始化")

def handle_data(context, data):
    """执行策略逻辑"""
    if not g.bought:
        # 全仓买入
        order_target_percent(g.security, 1.0)
        g.bought = True
        log.info(f"买入 {g.security}")

def after_trading_end(context, data):
    """盘后处理"""
    total_value = context.portfolio.total_value
    log.info(f"总资产: ¥{total_value:,.2f}")
```

### 均线交叉策略

```python
def initialize(context):
    """初始化策略"""
    g.security = '000001.SZ'
    g.ma_short = 5
    g.ma_long = 20
    log.info("均线交叉策略初始化")

def handle_data(context, data):
    """执行策略逻辑"""
    security = g.security
    
    # 获取历史数据
    hist = get_history(g.ma_long + 1, '1d', 'close', security)
    if len(hist) < g.ma_long:
        return
    
    # 计算均线
    ma_short = hist['close'].rolling(g.ma_short).mean().iloc[-1]
    ma_long = hist['close'].rolling(g.ma_long).mean().iloc[-1]
    
    current_position = get_position(security).amount
    
    # 交易逻辑
    if ma_short > ma_long and current_position == 0:
        # 金叉买入
        order_target_percent(security, 0.8)
        log.info(f"金叉买入信号: MA{g.ma_short}={ma_short:.2f} > MA{g.ma_long}={ma_long:.2f}")
        
    elif ma_short < ma_long and current_position > 0:
        # 死叉卖出
        order_target_percent(security, 0)
        log.info(f"死叉卖出信号: MA{g.ma_short}={ma_short:.2f} < MA{g.ma_long}={ma_long:.2f}")
```

### 技术指标策略

```python
def initialize(context):
    """初始化策略"""
    g.security = '000001.SZ'
    g.rsi_period = 14
    g.rsi_oversold = 30
    g.rsi_overbought = 70
    log.info("RSI技术指标策略初始化")

def handle_data(context, data):
    """执行策略逻辑"""
    security = g.security
    
    # 计算RSI指标
    rsi_data = get_RSI(security, period=g.rsi_period)
    if rsi_data.empty:
        return
        
    current_rsi = rsi_data[f'RSI{g.rsi_period}'].iloc[-1]
    current_position = get_position(security).amount
    
    # 交易逻辑
    if current_rsi < g.rsi_oversold and current_position == 0:
        # RSI超卖买入
        order_target_percent(security, 0.6)
        log.info(f"RSI超卖买入: RSI={current_rsi:.2f}")
        
    elif current_rsi > g.rsi_overbought and current_position > 0:
        # RSI超买卖出
        order_target_percent(security, 0)
        log.info(f"RSI超买卖出: RSI={current_rsi:.2f}")
```

### 多股票轮动策略

```python
def initialize(context):
    """初始化策略"""
    g.stocks = ['000001.SZ', '000002.SZ', '600519.SH', '600036.SH']
    g.momentum_period = 20
    log.info("多股票动量轮动策略初始化")

def handle_data(context, data):
    """执行策略逻辑"""
    # 计算所有股票的动量
    momentum_scores = {}
    
    for stock in g.stocks:
        hist = get_history(g.momentum_period + 1, '1d', 'close', stock)
        if len(hist) >= g.momentum_period:
            # 计算动量得分（过去N日收益率）
            momentum = (hist['close'].iloc[-1] / hist['close'].iloc[0] - 1) * 100
            momentum_scores[stock] = momentum
    
    if not momentum_scores:
        return
    
    # 选择动量最强的股票
    best_stock = max(momentum_scores, key=momentum_scores.get)
    best_momentum = momentum_scores[best_stock]
    
    # 获取当前持仓
    current_positions = {stock: get_position(stock).amount for stock in g.stocks}
    current_stock = next((stock for stock, amount in current_positions.items() if amount > 0), None)
    
    # 轮动逻辑
    if current_stock != best_stock:
        # 清空所有持仓
        for stock in g.stocks:
            if get_position(stock).amount > 0:
                order_target_percent(stock, 0)
        
        # 买入动量最强的股票
        order_target_percent(best_stock, 0.9)
        log.info(f"轮动到 {best_stock}, 动量得分: {best_momentum:.2f}%")
```

---

## 🔄 PTrade兼容性

### 高度兼容的设计理念

SimTradeLab与PTrade保持语法和API的高度兼容性，确保策略可以在两个平台间无缝迁移。

### 完全兼容的API

**事件函数：**
- `initialize(context)` - 策略初始化
- `handle_data(context, data)` - 主策略逻辑  
- `before_trading_start(context, data)` - 盘前处理
- `after_trading_end(context, data)` - 盘后处理

**交易接口：**
- `order(security, amount, limit_price=None)`
- `order_target(security, target_amount)`
- `order_value(security, target_value)`
- `cancel_order(order_id)`

**数据接口：**
- `get_history(count, frequency, field, security_list, fq, include, fill, is_dict)`
- `get_price(security, start_date, end_date, frequency, fields, count)`
- `get_current_data(security=None)`

**技术指标：**
- `get_MACD(security, fast_period, slow_period, signal_period)`
- `get_KDJ(security, k_period)`
- `get_RSI(security, period)`
- `get_CCI(security, period)`

**查询接口：**
- `get_position(security)` / `get_positions()`
- `get_orders()` / `get_open_orders()` / `get_trades()`

**工具函数：**
- `set_commission()` / `set_slippage()` / `set_benchmark()`
- `get_trading_day()` / `get_all_trades_days()`
- `log.info()` / `log.warning()` / `log.error()`

### 数据结构兼容

**Context对象：**
- `context.portfolio.total_value`
- `context.portfolio.cash`
- `context.portfolio.positions`
- `context.current_dt`

**Position对象：**
- `position.amount`
- `position.avg_cost`
- `position.market_value`

### 策略迁移指南

**从SimTradeLab到PTrade：**
1. 策略代码无需修改，直接复制粘贴
2. 确保使用的API都在PTrade支持范围内
3. 数据格式和参数保持一致

**从PTrade到SimTradeLab：**
1. 策略代码无需修改，直接使用
2. 配置好对应的数据源
3. 运行回测验证结果

### 扩展功能

SimTradeLab在保持兼容性的基础上，还提供了一些增强功能：

- **更丰富的报告格式**（HTML、图表等）
- **更灵活的数据源配置**（CSV、AkShare、Tushare）
- **更便捷的命令行工具**
- **更完整的技术指标库**

---

## ⚠️ 注意事项

### 通用注意事项

1. **股票代码格式**：必须使用标准格式，如 `'000001.SZ'`、`'600519.SH'`
2. **交易时间限制**：交易函数只能在交易时间内调用
3. **数据可用性**：确保策略中使用的股票在数据源中存在
4. **内存管理**：大量历史数据可能占用较多内存
5. **网络连接**：使用在线数据源时需要稳定的网络连接

### 策略开发注意事项

1. **数据准备**：在使用股票数据前先检查数据是否存在
2. **异常处理**：在计算技术指标时注意数据不足的情况
3. **日志记录**：合理使用日志记录重要的策略决策
4. **参数设置**：避免使用过拟合的策略参数

### 性能优化建议

1. **数据获取**：避免在循环中频繁调用数据接口
2. **计算缓存**：对重复计算的指标进行缓存
3. **批量操作**：优先使用批量接口而非单个接口
4. **内存释放**：及时释放不再使用的大数据对象

### 回测局限性

1. **滑点影响**：实际交易中的滑点可能比回测设置更大
2. **流动性限制**：大额交易可能面临流动性不足问题  
3. **交易成本**：实际交易成本可能包含更多隐性费用
4. **市场环境**：历史表现不代表未来收益

### 风险提示

1. **投资风险**：策略回测结果不构成投资建议
2. **数据风险**：数据源可能存在延迟或错误
3. **技术风险**：软件可能存在bug或异常
4. **合规风险**：确保策略符合相关法规要求

---

## 📚 版本信息

**当前版本：** v1.0.0

**更新日期：** 2025年7月6日

**兼容性：** Python 3.10+

**主要特性：**
- 完整的事件驱动回测引擎
- 与PTrade API高度兼容
- 支持多种数据源（CSV、AkShare、Tushare）
- 丰富的技术指标库
- 多格式报告系统
- 便捷的命令行工具

**已知限制：**
- 暂不支持实盘交易
- 部分高级期权功能仍在开发中
- Tick级别数据支持有限

---

## 🤝 贡献与支持

### 贡献指南

欢迎社区贡献代码、报告问题或提出改进建议：

1. **Fork项目** - 在GitHub上fork项目
2. **创建分支** - `git checkout -b feature/新功能`
3. **提交代码** - `git commit -m '添加新功能'`
4. **推送分支** - `git push origin feature/新功能`
5. **提交PR** - 在GitHub上创建Pull Request

### 问题反馈

- **Bug报告**: [GitHub Issues](https://github.com/kay-ou/SimTradeLab/issues)
- **功能请求**: [GitHub Issues](https://github.com/kay-ou/SimTradeLab/issues)
- **使用问题**: [GitHub Discussions](https://github.com/kay-ou/SimTradeLab/discussions)

### 文档资源

- **项目主页**: [GitHub Repository](https://github.com/kay-ou/SimTradeLab)
- **完整文档**: [docs/](docs/)
- **策略示例**: [strategies/](strategies/)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## ⚖️ 免责声明

SimTradeLab是一个开源的策略回测框架，仅用于教育、研究和非商业用途。本项目不提供投资建议，使用者应自行承担使用风险。项目开发者不对任何由使用本项目所引发的直接或间接损失承担责任。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[🏠 项目主页](https://github.com/kay-ou/SimTradeLab) | [📖 完整文档](docs/) | [🐛 报告问题](https://github.com/kay-ou/SimTradeLab/issues) | [💡 功能请求](https://github.com/kay-ou/SimTradeLab/issues)

**感谢您使用 SimTradeLab！**

</div>