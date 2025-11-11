# 📈 SimTradeLab

**轻量级量化回测框架 - PTrade API本地实现**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.2.0-orange.svg)](#)

*完整模拟PTrade平台API，策略可无缝迁移*

---

## 🎯 项目简介

SimTradeLab 是一个轻量级的本地量化回测框架，完整实现了PTrade平台的103个API接口。在SimTradeLab中编写的策略可以**零修改**迁移到PTrade平台运行，反之亦然。

### ✨ 核心特性

- ✅ **完整API实现** - 103个PTrade API，完全兼容
- 🚀 **数据常驻内存** - 单例模式，首次加载后常驻，大幅提升性能
- 🔧 **生命周期控制** - 7个生命周期阶段，API调用验证
- 📊 **统计报告** - 自动生成收益、风险、交易统计和图表
- ⚡ **性能优化** - 多级缓存、预构建索引、向量化计算
- 🔌 **模块化设计** - 清晰的代码结构，易于扩展

---

## 🚀 快速开始

### 📦 安装

```bash
# 克隆项目
git clone https://github.com/kay-ou/SimTradeLab.git
cd SimTradeLab

# 安装依赖（使用Poetry）
poetry install
```

### 📁 准备数据

将你的PTrade数据文件放到 `data/` 目录：
```
data/
├── ptrade_data.h5           # 股票价格、除权数据
└── ptrade_fundamentals.h5   # 基本面数据
```

**数据文件说明：**
- 使用HDF5格式存储
- 支持5000+只股票的日线数据
- 包含价格、成交量、除权、估值、财务等数据

### ✍️ 编写策略

创建策略文件 `strategies/my_strategy/backtest.py`：

```python
def initialize(context):
    """策略初始化"""
    set_benchmark('000300.SS')  # 设置基准
    context.stocks = ['600519.SS', '000858.SZ']  # 股票池

def before_trading_start(context, data):
    """盘前处理"""
    pass

def handle_data(context, data):
    """每日交易逻辑"""
    for stock in context.stocks:
        # 获取历史数据
        hist = get_history(20, '1d', 'close', [stock], is_dict=True)

        if stock not in hist:
            continue

        prices = hist[stock]
        ma5 = sum(prices[-5:]) / 5
        ma20 = sum(prices[-20:]) / 20

        # 金叉买入
        if ma5 > ma20 and stock not in context.portfolio.positions:
            order_value(stock, context.portfolio.portfolio_value * 0.3)

        # 死叉卖出
        elif ma5 < ma20 and stock in context.portfolio.positions:
            order_target(stock, 0)

def after_trading_end(context, data):
    """盘后处理"""
    log.info(f"总资产: {context.portfolio.portfolio_value:.2f}")
```

### ▶️ 运行回测

```bash
# 使用Poetry运行
poetry run python -m simtradelab.backtest.run_backtest

# 或者直接运行
cd src/simtradelab/backtest
poetry run python run_backtest.py
```

**配置参数** (`run_backtest.py`)：
```python
strategy_name = 'my_strategy'    # 策略目录名
start_date = '2024-01-01'        # 开始日期
end_date = '2024-12-31'          # 结束日期
initial_capital = 1000000.0      # 初始资金
```

**说明：**
- `data_path` 和 `strategies_path` 使用统一路径管理，无需手动指定
- 策略文件自动定位到 `strategies/{strategy_name}/backtest.py`

### 📊 查看结果

回测完成后，在策略目录下生成：
```
strategies/my_strategy/stats/
├── backtest_240101_241231_*.log    # 详细日志
└── backtest_240101_241231_*.png    # 4图可视化
```

**报告包含：**
- 📈 资产曲线 vs 基准对比
- 💰 每日盈亏分布
- 📊 买卖金额统计
- 💼 持仓市值变化

---

## 📚 API文档

### 支持的PTrade API（103个）

#### 交易API
```python
order(stock, amount)                      # 买卖股票
order_target(stock, amount)               # 调整到目标数量
order_value(stock, value)                 # 按金额下单
order_target_value(stock, value)          # 调整到目标金额
order_target_percent(stock, percent)      # 调整到目标比例
```

#### 行情API
```python
get_price(stock, start_date, end_date, fields, fq)  # 获取历史行情
get_history(count, frequency, field, stocks)        # 获取历史数据
get_current_data()                                  # 获取当前数据
```

#### 基本面API
```python
get_fundamentals(query, date)             # 查询基本面数据
# 支持表：valuation（估值）、profit（利润）、growth（成长）
#         balance（资产负债）、cash_flow（现金流）
```

#### 股票筛选API
```python
get_all_securities(types, date)           # 获取所有股票列表
get_stock_blocks(stock, date)             # 获取股票所属板块
get_stock_status(stock, date)             # 获取股票状态
```

#### 配置API
```python
set_benchmark(benchmark)                  # 设置基准
set_commission(commission)                # 设置佣金
set_slippage(slippage)                    # 设置滑点
set_universe(securities)                  # 设置股票池
```

#### 交易日API
```python
get_trade_days(start_date, end_date, count)  # 获取交易日
get_previous_trading_date(date, count)        # 获取前N个交易日
get_next_trading_date(date, count)            # 获取后N个交易日
```

**完整API列表：** 参见 `src/simtradelab/ptrade/api.py`

---

## 🏗️ 项目结构

```
SimTradeLab/
├── src/simtradelab/
│   ├── ptrade/              # PTrade API模拟层
│   │   ├── api.py          # 103个API实现
│   │   ├── context.py      # Context上下文对象
│   │   ├── object.py       # Portfolio/Position/Order等核心对象
│   │   ├── strategy_engine.py      # 策略执行引擎
│   │   ├── lifecycle_controller.py # 生命周期管理
│   │   └── lifecycle_config.py     # API阶段限制配置
│   ├── backtest/           # 回测引擎
│   │   ├── runner.py       # 回测编排器
│   │   ├── config.py       # 回测配置管理
│   │   ├── stats.py        # 统计和图表
│   │   ├── stats_collector.py  # 统计数据收集
│   │   └── run_backtest.py # 入口脚本
│   ├── service/
│   │   └── data_server.py  # 数据常驻服务
│   └── paths.py            # 统一路径管理
├── strategies/             # 策略目录
│   ├── simple/            # 简单测试策略
│   └── 20mv/              # 20日均线策略示例
├── data/                  # 数据目录
│   ├── ptrade_data.h5
│   └── ptrade_fundamentals.h5
└── extract_sample_data.py # 数据抽取工具
```

---

## 🛠️ 工具脚本

### 数据抽取工具

从完整数据中抽取指定时间段的样本数据：

```bash
# 编辑 extract_sample_data.py 设置时间范围
start_date = pd.Timestamp('2025-01-01')
end_date = pd.Timestamp('2025-10-31')

# 运行抽取
poetry run python extract_sample_data.py
```

生成文件：
- `data/ptrade_data_sample.h5` - 样本价格数据
- `data/ptrade_fundamentals_sample.h5` - 样本基本面数据

---

## ⚙️ 核心设计

### 策略执行引擎

`StrategyExecutionEngine` 负责策略的完整生命周期管理：

**核心功能：**
- 🔄 **策略加载** - 从文件加载PTrade标准策略，自动注册生命周期函数
- 🎯 **生命周期管理** - 统一管理7个生命周期阶段的函数调用
- 📊 **统计收集** - 集成统计收集器，实时记录交易数据
- 🛡️ **错误处理** - 安全的函数调用，异常隔离不中断回测

**架构优势：**
```python
# BacktestRunner 负责：数据加载、环境初始化、报告生成
# StrategyExecutionEngine 负责：策略加载、生命周期执行、统计收集
# 职责清晰，易于扩展
```

### 数据常驻内存

使用单例模式的 `DataServer`，数据首次加载后常驻内存：

```python
# 首次运行 - 加载数据
DataServer(data_path)  # 加载数据到内存

# 后续运行 - 直接使用缓存
DataServer(data_path)  # 无需重新加载，秒级启动
```

**性能对比：**
- 首次加载：约15秒（5392只股票）
- 后续运行：即时启动

### 生命周期管理

策略生命周期的7个阶段：

1. `initialize` - 策略初始化（仅一次）
2. `before_trading_start` - 盘前处理（每日）
3. `handle_data` - 主策略逻辑（每日）
4. `after_trading_end` - 盘后处理（每日）
5. `tick_data` - Tick数据处理（高频，未实现）
6. `on_order_response` - 订单回报（未实现）
7. `on_trade_response` - 成交回报（未实现）

每个API调用都会验证是否在允许的阶段调用。

### 性能优化

- **预构建索引** - 股票日期索引预先构建
- **多级缓存** - 全局MA缓存、LRU缓存、日内缓存
- **向量化计算** - numpy批量处理复权因子
- **LazyDataDict** - 延迟加载+LRU淘汰策略

---

## 📝 示例策略

### 简单双均线策略

参见 `strategies/simple/backtest.py` - 5只股票，双均线交易

### 每日轮换策略

参见 `strategies/5mv/backtest.py` - 每2天轮换持仓，保证每日有交易

---

## 🔧 开发指南

### 添加新策略

1. 在 `strategies/` 创建新目录
2. 添加 `backtest.py` 文件
3. 实现生命周期函数
4. 修改 `run_backtest.py` 的 `strategy_name`
5. 运行回测

### 扩展API

1. 在 `src/simtradelab/ptrade/api.py` 添加新方法
2. 在 `src/simtradelab/ptrade/lifecycle_config.py` 配置阶段限制
3. 更新文档

---

## ⚠️ 注意事项

### PTrade限制模拟

- ❌ 不支持f-string（PTrade限制）
- ❌ 不支持io、sys导入（PTrade限制）
- ✅ `research/run_local_backtest.py` 不受限制

### 数据要求

- HDF5格式（pandas HDFStore）
- 日线数据（不支持分钟线）
- 包含：open, high, low, close, volume, money等字段

---

## 🐛 常见问题

**Q: 如何修改初始资金？**
```python
# 在 run_backtest.py 中修改
runner.run(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=2000000.0  # 修改这里
)
```

**Q: 回测太慢怎么办？**
- 减少股票数量
- 缩短回测时间
- 使用数据服务器模式（默认已启用）

**Q: 如何查看更多日志？**
日志文件位于 `strategies/{strategy_name}/stats/*.log`

**Q: 策略在PTrade上运行出错？**
检查是否使用了f-string或禁止的导入（io、sys）

---

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

---

## ⚖️ 免责声明

SimTradeLab 是独立开发的开源项目，不隶属于PTrade平台。本框架仅用于教学研究和策略验证，不提供投资建议。使用本框架产生的任何损失，开发者不承担责任。

---

## 🙏 致谢

- 感谢PTrade提供的API设计灵感
- 感谢所有贡献者和用户

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[🐛 报告问题](https://github.com/kay-ou/SimTradeLab/issues) | [💡 功能请求](https://github.com/kay-ou/SimTradeLab/issues)

</div>
