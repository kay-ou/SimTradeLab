# 📈 SimTradeLab

**轻量级量化回测框架 - PTrade API本地实现**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.2.0-orange.svg)](#)

*完整模拟PTrade平台API，策略可无缝迁移*

---

## 🎯 项目简介

SimTradeLab（深测Lab） 是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动架构。它具备完全自主的实现与出色的扩展能力，为策略开发者提供一个轻量级、结构清晰、模块可插拔的策略验证环境。框架无需依赖 PTrade 即可独立运行，但与其语法保持高度兼容。所有在 SimTradeLab 中编写的策略可无缝迁移至 PTrade 平台，反之亦然，两者之间的 API 可直接互通使用。详情参考：https://github.com/kay-ou/ptradeAPI 项目。项目中使用到的数据可以通过 https://github.com/kay-ou/SimTradeData 项目获取。

### ✨ 核心特性

- ✅ **完整API实现** - 103个PTrade API，完全兼容
- ⚡ **极速回测** - 本地回测性能比PTrade平台提升20-30+倍
- 🚀 **数据常驻内存** - 单例模式，首次加载后常驻，二次运行秒级启动
- 💾 **智能缓存系统** - 多级LRU缓存（MA/VWAP/复权/历史数据），命中率>95%
- 🧠 **智能数据加载** - AST静态分析策略代码，按需加载数据，节省内存
- 🔍 **自动兼容检查** - 启动时检查Python 3.5兼容性（f-string/禁用模块）
- 🔧 **生命周期控制** - 7个生命周期阶段，API调用验证
- 📊 **完整统计报告** - 收益、风险、交易明细、持仓批次、FIFO分红税
- 🔌 **模块化设计** - 清晰的代码结构，易于扩展和定制

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

### 🔬 Research模式（交互式探索）

SimTradeLab提供与PTrade完全兼容的Research模式，支持Jupyter Notebook交互式数据分析。

**启动方式：**

```python
# 在Jupyter Notebook中
from simtradelab.research.api import init_api, get_price, get_history

# 初始化API（按需加载模式，首次调用相关函数时才加载数据）
api = init_api()

# 或显式指定需要加载的数据
api = init_api(required_data={'price', 'exrights'})

# 获取历史价格
df = get_price('600519.SS', start_date='2024-01-01', end_date='2024-12-31')

# 获取历史数据
hist = get_history(20, '600519.SS', 'close')

# 获取指数成分股
stocks = api.get_index_stocks('000300.SS', date='2024-01-01')

# 获取基本面数据
fundamentals = api.get_fundamentals(['600519.SS'], 'valuation', ['pe_ratio', 'pb_ratio'], '2024-01-01')
```

**特点：**
- ✅ **无生命周期限制** - 所有API可随时调用，无需initialize等生命周期函数
- ✅ **智能按需加载** - 默认延迟加载数据，首次访问时自动加载相关数据集
- ✅ **数据常驻** - 单例模式，数据加载后常驻内存，多次运行秒级启动
- ✅ **完整API支持** - 所有PTrade查询类API（get_price/get_history/get_fundamentals等）
- ✅ **IPython友好** - Jupyter Notebook自动补全和文档查看
- ✅ **支持f-string** - Research模式不受PTrade语法限制，可用Python 3.6+特性

**示例Notebook：**
参见 `src/simtradelab/research/notebook.ipynb`

### 📊 Backtest模式（策略回测）

编写策略文件 `strategies/my_strategy/backtest.py`：

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

**注意：Backtest模式严格模拟PTrade限制**
- ❌ 不支持f-string（使用`.format()`或`%`格式化）
- ❌ 不支持io、sys等模块导入
- ✅ 启动时自动检查Python 3.5兼容性
- ✅ 运行时验证生命周期API调用

### 📁 准备数据

将你的PTrade数据文件放到 `data/` 目录：
(可以从 https://github.com/kay-ou/SimTradeData 项目获取)
```
data/
├── ptrade_data.h5           # 股票价格、除权数据
└── ptrade_fundamentals.h5   # 基本面数据
```

**数据文件说明：**
- 使用HDF5格式存储
- 支持5000+只股票的日线数据
- 包含价格、成交量、除权、估值、财务等数据

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

### 🏆 性能优化亮点

**本地回测性能比PTrade平台提升20-30+倍！**

核心优化技术栈：

#### 1. 数据常驻内存（单例模式）
```python
# 首次运行 - 加载数据到内存
DataServer(data_path)  # 约15秒（5392只股票）

# 后续运行 - 直接使用缓存
DataServer(data_path)  # 秒级启动，数据常驻
```

#### 2. 多级智能缓存系统
- **全局MA/VWAP缓存** - cachetools.LRUCache，自动淘汰最旧项
- **复权因子预计算** - 向量化批量计算，HDF5持久化（blosc压缩）
- **分红事件缓存** - joblib并行构建，避免重复解析
- **历史数据缓存** - LazyDataDict延迟加载，LRU策略管理内存
- **日期索引缓存** - 预构建bisect索引，O(log n)查找

#### 3. 并行计算加速
- **数据加载** - joblib多进程并行，充分利用多核CPU
- **复权计算** - 向量化处理，numpy批量运算
- **性能监控** - @timer装饰器，精准定位瓶颈

#### 4. 智能启动优化
- **策略代码AST分析** - 自动识别API调用（get_price/get_history/get_fundamentals）
- **按需数据加载** - 只加载策略实际使用的数据集（价格/估值/财务/除权）
- **Python 3.5兼容检查** - 启动时检测f-string、变量注解、海象运算符等不兼容语法
- **禁用模块检测** - 自动检查io/sys等PTrade不支持的模块导入

**实测数据（5392只股票，1年回测）：**
- PTrade平台：约30-40分钟
- SimTradeLab：约1-2分钟（20-30倍提升）

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

### 严格生命周期管理

**完整模拟PTrade平台的7阶段生命周期控制**

SimTradeLab实现了与PTrade完全一致的生命周期管理，确保策略在本地和平台上行为一致。

#### 生命周期阶段定义

1. `initialize` - 策略初始化（全局仅执行一次）
2. `before_trading_start` - 盘前处理（每个交易日开盘前）
3. `handle_data` - 主交易逻辑（每个交易日收盘时）
4. `after_trading_end` - 盘后处理（每个交易日收盘后）
5. `tick_data` - Tick数据处理（高频，未实现）
6. `on_order_response` - 订单回报（未实现）
7. `on_trade_response` - 成交回报（未实现）

#### 技术实现机制

**1. 阶段转换验证**
```python
# lifecycle_controller.py 实现严格的状态机
允许的转换规则：
- None → initialize （策略启动）
- initialize → before_trading_start 或 handle_data
- before_trading_start → handle_data
- handle_data → after_trading_end （当日结束）
- after_trading_end → before_trading_start （下一交易日）

违规转换抛出 PTradeLifecycleError 异常
```

**2. API调用限制（基于PTrade官方文档）**

| API类型 | 限制阶段 | 示例 |
|---------|---------|------|
| 配置API | 仅initialize | `set_benchmark`, `set_commission`, `set_slippage` |
| 交易API | handle_data/tick_data | `order`, `order_target`, `order_value` |
| 盘前专用 | before_trading_start | `ipo_stocks_order` |
| 盘后专用 | after_trading_end | `after_trading_order`, `get_trades_file` |
| 通用查询 | 所有阶段 | `get_price`, `get_history`, `get_positions` |

**3. 运行时校验**
```python
# 每个API调用前自动验证
result = lifecycle_controller.validate_api_call('order')
if not result.is_valid:
    raise PTradeLifecycleError(result.error_message)

# 错误示例：
# 在 initialize 调用 order → 报错：API 'order' cannot be called in phase 'initialize'
# 在 handle_data 调用 set_commission → 报错：Allowed phases: ['initialize']
```

**4. 调用历史追踪**
- 记录每个API的调用时间、参数、阶段、成功/失败状态
- 提供统计接口：`get_call_statistics()` 查看API调用次数、成功率
- 支持调试：`get_recent_calls(10)` 查看最近10次API调用

**优势：**
- ✅ **100%兼容PTrade** - API限制配置源自PTrade官方文档（103个API）
- ✅ **提前发现错误** - 本地回测时就能发现生命周期违规，无需等到上传平台
- ✅ **线程安全** - 使用RLock确保多线程环境下状态一致性
- ✅ **详细错误提示** - 明确指出当前阶段和允许的阶段列表

### 持仓管理与分红税

**FIFO批次管理：**
- 每次买入创建独立持仓批次（记录买入价、时间、数量）
- 卖出时按先进先出顺序扣减批次
- 自动跟踪每笔持仓的持有时长

**分红税计算：**
- 分红时：记录分红金额和日期到各批次
- 卖出时：根据持有时长计算差异化税率
  - 持有≤1个月：20%
  - 持有>1个月≤1年：10%
  - 持有>1年：免税
- 完整模拟真实交易的税务成本

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

---

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件

---

## ⚖️ 免责声明

SimTradeLab 是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动设计理念，但并未包含 PTrade 的源代码、商标或任何受保护内容。该项目不隶属于 PTrade，也未获得其官方授权。SimTradeLab 的所有实现均为自主构建，仅用于教学研究、策略验证和非商业性用途。

使用本框架构建或测试策略的用户应自行确保符合所在地区的法律法规、交易平台的使用条款及数据源的合规性。项目开发者不对任何由使用本项目所引发的直接或间接损失承担责任。

---

## 🙏 致谢

- 感谢PTrade提供的API设计灵感
- 感谢所有贡献者和用户

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[🐛 报告问题](https://github.com/kay-ou/SimTradeLab/issues) | [💡 功能请求](https://github.com/kay-ou/SimTradeLab/issues)

</div>

---

<div align="center">

## 💖 赞助支持

如果这个项目对您有帮助，欢迎赞助支持开发！

<img src="https://github.com/kay-ou/SimTradeLab/blob/main/sponsor/WechatPay.png?raw=true" alt="微信赞助" width="200">
<img src="https://github.com/kay-ou/SimTradeLab/blob/main/sponsor/AliPay.png?raw=true" alt="支付宝赞助" width="200">

**您的支持是我们持续改进的动力！**

</div>