# 📈 SimTradeLab

**轻量级量化回测框架 - PTrade API本地实现**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.2.3-orange.svg)](#)

*完整模拟PTrade平台API，策略可无缝迁移*

---

## 🎯 项目简介

SimTradeLab（深测Lab） 是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动架构。它具备完全自主的实现与出色的扩展能力，为策略开发者提供一个轻量级、结构清晰、模块可插拔的策略验证环境。框架无需依赖 PTrade 即可独立运行，但与其语法保持高度兼容。所有在 SimTradeLab 中编写的策略可无缝迁移至 PTrade 平台，反之亦然，两者之间的 API 可直接互通使用。详情参考：https://github.com/kay-ou/ptradeAPI 项目。

### 📊 项目状态

**当前版本**: v1.2.3
**开发状态**: Beta - 核心功能完善，正在策略实战中持续优化

已完成：
- ✅ **52个核心API** - 覆盖股票交易、数据查询、技术指标、配置管理
- ✅ **回测引擎** - 完整的事件驱动回测系统，75%回测场景API完成度
- ✅ **Research模式** - Jupyter Notebook交互式数据分析，60%研究场景API完成度
- ✅ **性能优化** - 多级缓存、数据常驻、智能加载，性能提升20-30倍
- ✅ **生命周期管理** - 严格模拟PTrade的API调用阶段限制
- ✅ **统计报告** - 完整的收益、风险、交易明细、持仓批次分析

正在进行：
- 🔧 在实际策略中发现和修复潜在bug
- 🔧 优化内存使用，探索小内存环境的妥协方案
- 🔧 完善剩余99个PTrade API（融资融券、期货、期权、实时行情等）

### ✨ 核心特性

- ✅ **52个核心API** - 股票交易、数据查询、技术指标完整支持（34% PTrade API完成度）
- ⚡ **极速回测** - 本地回测性能比PTrade平台提升20-30+倍
- 🚀 **数据常驻内存** - 单例模式，首次加载后常驻，二次运行秒级启动
- 💾 **智能缓存系统** - 多级LRU缓存（MA/VWAP/复权/历史数据），命中率>95%
- 🧠 **智能数据加载** - AST静态分析策略代码，按需加载数据，节省内存
- 🔍 **自动兼容检查** - 启动时检查Python 3.5兼容性（f-string/禁用模块）
- 🔧 **生命周期控制** - 7个生命周期阶段，API调用验证
- 📊 **完整统计报告** - 收益、风险、交易明细、持仓批次、FIFO分红税
- 🔌 **模块化设计** - 清晰的代码结构，易于扩展和定制

详细API实现状态：`docs/PTrade_API_Implementation_Status.md`

---

## 🚀 快速开始

### 📦 安装

#### 方式1：PyPI安装（推荐，适合普通用户）

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 安装最新版本
pip install simtradelab

# 安装指定版本
pip install simtradelab==1.2.3

# 包含优化器（可选）
pip install simtradelab[optimizer]
```

**安装后设置工作目录：**

```bash
# 1. 创建工作目录
mkdir -p ~/simtrade_workspace
cd ~/simtrade_workspace

# 2. 创建必要的子目录
mkdir -p data          # 存放数据文件
mkdir -p strategies    # 存放策略文件
mkdir -p research      # 存放Jupyter notebooks

# 3. 下载示例策略（可选）
# 从GitHub获取示例文件
wget https://raw.githubusercontent.com/kay-ou/SimTradeLab/main/strategies/simple/backtest.py -P strategies/simple/
```

**准备数据文件：**

```bash
# 方式A: 使用SimTradeData项目获取数据
# 访问：https://github.com/kay-ou/SimTradeData

# 方式B: 使用自己的数据（HDF5格式）
# 将数据文件放到 data/ 目录：
# - data/ptrade_data.h5
# - data/ptrade_fundamentals.h5
```

**创建并运行策略：**

```python
# strategies/my_strategy/backtest.py
from simtradelab.ptrade.api import *

def initialize(context):
    set_benchmark('000300.SS')
    context.stocks = ['600519.SS', '000858.SZ']

def handle_data(context, data):
    for stock in context.stocks:
        hist = get_history(20, '1d', 'close', [stock], is_dict=True)
        if stock in hist:
            prices = hist[stock]
            ma5 = sum(prices[-5:]) / 5
            ma20 = sum(prices[-20:]) / 20

            if ma5 > ma20 and stock not in context.portfolio.positions:
                order_value(stock, context.portfolio.portfolio_value * 0.3)
            elif ma5 < ma20 and stock in context.portfolio.positions:
                order_target(stock, 0)
```

**运行回测：**

```python
# run_backtest.py
from simtradelab.backtest.runner import BacktestRunner
from pathlib import Path

# 配置路径
data_path = Path.home() / 'simtrade_workspace' / 'data'
strategy_path = Path.home() / 'simtrade_workspace' / 'strategies' / 'my_strategy'

# 运行回测
runner = BacktestRunner(
    data_path=str(data_path),
    strategies_path=str(strategy_path.parent)
)

runner.run(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=1000000.0
)
```

**Research模式（Jupyter Notebook）：**

```python
# notebooks/research.ipynb
from simtradelab.research.api import init_api, get_price, get_history
from pathlib import Path

# 初始化API，指定数据路径
data_path = Path.home() / 'simtrade_workspace' / 'data'
api = init_api(data_path=str(data_path))

# 获取数据
df = get_price('600519.SS', start_date='2024-01-01', end_date='2024-12-31')
print(df.head())
```

**系统依赖：**
- macOS用户需要先安装：
  ```bash
  brew install hdf5 ta-lib
  export HDF5_DIR=$(brew --prefix hdf5)
  ```
- Linux用户需要先安装：
  ```bash
  sudo apt-get install libhdf5-dev
  # ta-lib需要从源码编译（见下方源码安装说明）
  ```

#### 方式2：源码安装（适合开发者）

```bash
# 克隆项目
git clone https://github.com/kay-ou/SimTradeLab.git
cd SimTradeLab

# 安装系统依赖
# macOS:
brew install hdf5 ta-lib
export HDF5_DIR=$(brew --prefix hdf5)

# Linux:
sudo apt-get install libhdf5-dev
# 编译安装ta-lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 安装Python依赖（使用Poetry）
cd SimTradeLab
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

**数据获取方式：**
- 📦 推荐使用 [SimTradeData](https://github.com/kay-ou/SimTradeData) 项目获取A股历史数据
- ⚠️ 注意：SimTradeData项目目前存在性能问题，数据获取速度较慢，后续会持续优化

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
start_date = '2025-01-01'        # 开始日期
end_date = '2025-12-31'          # 结束日期
initial_capital = 1000000.0      # 初始资金
```

**说明：**
- `data_path` 和 `strategies_path` 使用统一路径管理，无需手动指定
- 策略文件自动定位到 `strategies/{strategy_name}/backtest.py`

### 📊 查看结果

回测完成后，在策略目录下生成：
```
strategies/my_strategy/stats/
├── backtest_250101_251231_*.log    # 详细日志
└── backtest_250101_251231_*.png    # 4图可视化
```

**报告包含：**
- 📈 资产曲线 vs 基准对比
- 💰 每日盈亏分布
- 📊 买卖金额统计
- 💼 持仓市值变化

---

## 📚 API文档

已实现52个核心API（34% PTrade API完成度），涵盖股票交易、数据查询、技术指标、策略配置等核心功能。

**完整API列表和实现状态：** 参见 `docs/PTrade_API_Implementation_Status.md`

---

## 🔍 功能对比

### PTrade有的，我们也有 ✅

**核心交易功能**
- ✅ 股票下单：order, order_target, order_value, order_target_value
- ✅ 订单管理：cancel_order, get_order, get_orders, get_open_orders, get_trades
- ✅ 持仓查询：get_position, get_positions

**数据查询功能**
- ✅ 历史行情：get_price, get_history
- ✅ 股票信息：get_stock_name, get_stock_info, get_stock_status, get_stock_exrights
- ✅ 板块信息：get_stock_blocks, get_index_stocks, get_industry_stocks
- ✅ 基本面数据：get_fundamentals（估值、利润、成长、资产负债、现金流）
- ✅ 股票列表：get_Ashares, get_etf_list, get_ipo_stocks, get_all_securities

**技术指标计算**
- ✅ MACD：get_MACD
- ✅ KDJ：get_KDJ
- ✅ RSI：get_RSI
- ✅ CCI：get_CCI

**策略配置**
- ✅ 基准设置：set_benchmark
- ✅ 股票池：set_universe
- ✅ 交易成本：set_commission, set_slippage, set_fixed_slippage
- ✅ 回测参数：set_volume_ratio, set_limit_mode, set_yesterday_position
- ✅ 定时任务：run_daily, run_interval

**生命周期管理**
- ✅ initialize - 策略初始化
- ✅ before_trading_start - 盘前处理
- ✅ handle_data - 主交易逻辑
- ✅ after_trading_end - 盘后处理
- ✅ tick_data - tick级别处理

**工具函数**
- ✅ log - 多级别日志（debug/info/warning/error/critical）
- ✅ is_trade - 业务场景判断
- ✅ check_limit - 涨跌停状态判断
- ✅ get_trade_days - 交易日查询

### PTrade没有的，我们有 🚀

**性能优化**
- ⚡ **数据常驻内存** - 单例模式，首次加载后常驻，二次运行秒级启动（PTrade每次都要重新加载）
- ⚡ **多级LRU缓存** - MA/VWAP/复权/历史数据智能缓存，命中率>95%，大幅减少重复计算
- ⚡ **复权因子预计算** - HDF5持久化缓存，避免每次回测重新计算
- ⚡ **20-30倍性能提升** - 本地回测比PTrade平台快20-30倍以上

**智能功能**
- 🧠 **AST策略分析** - 自动分析策略代码，识别需要的数据类型，按需加载，节省内存
- 🧠 **自动兼容检查** - 启动时检查Python 3.5语法兼容性（f-string、变量注解、海象运算符等）
- 🧠 **禁用模块检测** - 自动检测PTrade不支持的模块导入（io、sys等）

**Research模式**
- 📊 **无生命周期限制** - Research模式下所有API可随时调用，无需initialize等生命周期函数
- 📊 **IPython友好** - Jupyter Notebook自动补全和文档查看
- 📊 **支持现代Python** - Research模式不受PTrade语法限制，可用Python 3.6+特性（f-string等）
- 📊 **延迟加载** - 数据默认延迟加载，首次访问时自动加载相关数据集

**统计分析**
- 📈 **持仓批次管理** - 详细的FIFO批次跟踪，精确计算每笔交易的持有时长
- 📈 **分红税计算** - 差异化税率（≤1个月20%，>1个月≤1年10%，>1年免税）
- 📈 **可视化报告** - 4图报告（资产曲线、每日盈亏、买卖金额、持仓市值）

**开发便利**
- 🔧 **统一路径管理** - 自动定位策略、数据、报告路径，无需手动配置
- 🔧 **性能监控** - @timer装饰器，精准定位性能瓶颈
- 🔧 **详细日志** - 完整的回测日志，方便调试和分析

### PTrade有的，我们还没有 ⏳

**实时交易功能（22%完成度）**
- ❌ 委托/成交回报：on_order_response, on_trade_response
- ❌ 实时行情：get_individual_entrust, get_individual_transaction, get_tick_direction
- ❌ 高级交易：order_market, order_tick, ipo_stocks_order, after_trading_order等
- ❌ ETF相关：etf_basket_order, etf_purchase_redemption, get_etf_info等
- ❌ 市场信息：get_market_list, get_market_detail, get_cb_list

**专业交易功能（0%完成度）**
- ❌ 融资融券：19个API（margin_trade, margincash_open/close等）
- ❌ 期货交易：7个API（buy_open/close, sell_open/close等）
- ❌ 期权交易：15个API（权利/义务仓开平仓、备兑、行权等）

**其他功能**
- ❌ 用户环境：get_user_name, get_deliver, get_fundjour, get_research_path
- ❌ 通知功能：send_email, send_qywx
- ❌ 数据文件：get_trades_file, convert_position_from_csv

**按场景统计完成度：**
- 回测场景：75%（49/65个API）✅ 功能完整
- 研究场景：60%（35/58个API）🎯 基本可用
- 交易场景：22%（15/67个API）🔧 基础可用

详细API实现状态：`docs/PTrade_API_Implementation_Status.md`

---

## 🏗️ 项目结构

```
SimTradeLab/
├── src/simtradelab/
│   ├── ptrade/                      # PTrade API模拟层
│   │   ├── api.py                  # 52个核心API实现
│   │   ├── context.py              # Context上下文对象
│   │   ├── data_context.py         # 数据上下文
│   │   ├── object.py               # Portfolio/Position/Order等
│   │   ├── strategy_engine.py      # 策略执行引擎
│   │   ├── lifecycle_controller.py # 生命周期管理
│   │   ├── lifecycle_config.py     # API阶段限制配置
│   │   ├── order_processor.py      # 订单处理器
│   │   ├── cache_manager.py        # 缓存管理器
│   │   ├── adjustment_calculator.py # 复权计算
│   │   ├── adj_pre_cache.py        # 前复权缓存
│   │   ├── strategy_validator.py   # 策略兼容性验证
│   │   ├── strategy_data_analyzer.py # 策略数据分析
│   │   └── config_manager.py       # 配置管理
│   ├── backtest/                   # 回测引擎
│   │   ├── runner.py               # 回测编排器
│   │   ├── config.py               # 回测配置（Pydantic）
│   │   ├── stats.py                # 统计和图表
│   │   ├── stats_collector.py      # 数据收集
│   │   └── run_backtest.py         # 入口脚本
│   ├── research/                   # Research模式
│   │   └── api.py                  # 无生命周期限制的API
│   ├── service/                    # 核心服务
│   │   └── data_server.py          # 数据常驻服务（单例）
│   └── utils/                      # 工具模块
│       ├── paths.py                # 统一路径管理
│       ├── perf.py                 # 性能监控
│       ├── py35_compat_checker.py  # Python 3.5兼容检查
│       └── performance_config.py   # 性能配置
├── strategies/                     # 策略目录
├── data/                           # 数据目录
│   ├── ptrade_data.h5             # 价格、除权数据
│   └── ptrade_fundamentals.h5     # 基本面数据
├── docs/                           # 文档
│   ├── PTrade_API_Implementation_Status.md
│   └── PTrade_API_Complete_Reference.md
└── extract_sample_data.py         # 数据抽取工具
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
- ✅ **100%兼容PTrade** - API限制配置源自PTrade官方文档（已实现52个核心API）
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

## 🔧 开发指南

### 添加新策略
1. 在 `strategies/` 创建新目录
2. 添加 `backtest.py` 文件，实现生命周期函数（initialize/handle_data等）
3. 修改 `run_backtest.py` 的 `strategy_name`
4. 运行回测

### 扩展API
1. 在 `src/simtradelab/ptrade/api.py` 添加新方法
2. 在 `src/simtradelab/ptrade/lifecycle_config.py` 配置阶段限制
3. 更新文档

**详细开发规范：** 参见 `docs/DEVELOPMENT_RULES.md`

---

## 🚧 待改进与已知问题

### 需要改进的功能

**用户界面**
- ⏳ **命令行工具** - 目前需要修改Python文件配置参数，计划开发友好的CLI工具
- ⏳ **Web UI** - 提供可视化的策略管理、参数配置、回测启动界面
- ⏳ **交互式配置** - 支持命令行交互式输入回测参数

**内存优化**
- ⏳ **大数据集优化** - 当前5000+只股票全量加载占用较大内存（约8-12GB）
- ⏳ **流式加载方案** - 对于小内存环境（<8GB），提供分批加载策略
- ⏳ **智能内存释放** - 回测结束后自动释放不再需要的数据
- ⏳ **按股票池加载** - 仅加载策略实际使用的股票数据，而非全市场

**数据获取**
- ⏳ **SimTradeData性能** - [SimTradeData](https://github.com/kay-ou/SimTradeData)项目数据获取速度慢，需要优化
- ⏳ **增量更新** - 支持数据增量更新，避免每次都完整下载
- ⏳ **多数据源支持** - 接入更多数据源（AkShare、Tushare、Wind等）

**API完善**
- ⏳ **99个待实现API** - PTrade还有99个API未实现（详见`docs/PTrade_API_Implementation_Status.md`）
  - 融资融券：19个API
  - 期货交易：7个API
  - 期权交易：15个API
  - 实时交易：高级交易、盘后交易、IPO申购等
  - 其他功能：市场信息、用户环境、通知等

### 已知问题与限制

**测试覆盖**
- ⚠️ **测试不全面** - 由于时间有限，未进行全面的单元测试和集成测试
- ⚠️ **策略驱动测试** - 目前主要在编写实际策略时发现问题并修复
- ⚠️ **边界情况** - 某些边界情况和异常场景可能未充分测试

**潜在Bug**
- 🐛 **数据边界** - 在数据缺失、停牌、涨跌停等特殊情况下可能存在未发现的bug
- 🐛 **复权计算** - 复杂的送股、配股、分红组合场景下，前复权计算可能存在精度问题
- 🐛 **并发安全** - 虽然使用了单例模式，但多进程并发回测场景未充分测试
- 🐛 **内存泄漏** - 长时间运行或大量回测任务可能存在内存泄漏风险

**功能限制**
- ❌ **不支持分钟线** - 目前仅支持日线数据回测
- ❌ **不支持实盘** - 仅支持历史数据回测，不支持实盘交易
- ❌ **单账户** - 不支持多账户、分仓管理

### 如何参与贡献

我们非常欢迎社区贡献，帮助完善SimTradeLab！

**报告问题**
- 🐛 遇到Bug？请在 [GitHub Issues](https://github.com/kay-ou/SimTradeLab/issues) 提交问题
- 📝 提供详细的错误信息、复现步骤、数据样本
- 🔍 搜索已有Issue，避免重复提交

**贡献代码**
- 💻 实现缺失的API功能
- 🔧 修复已知Bug
- ⚡ 性能优化和内存优化
- 📚 完善文档和示例

**分享策略**
- 📊 分享你的回测策略，帮助发现框架问题
- 💡 提供实际使用反馈和改进建议
- 🎓 编写教程和使用案例

**贡献指南：**
详见 `docs/CONTRIBUTING.md`

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
- 感谢所有贡献者和用户反馈
- 感谢在实际策略开发中帮助发现和修复Bug的用户

**特别说明：**
SimTradeLab是社区驱动的开源项目，我们在实际策略开发中不断完善功能。由于时间和资源有限，测试覆盖还不够全面，难免存在一些未发现的问题。我们非常欢迎社区参与，共同发现和解决问题，让这个项目变得更好。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[🐛 报告问题](https://github.com/kay-ou/SimTradeLab/issues) | [💡 功能请求](https://github.com/kay-ou/SimTradeLab/issues)

</div>

---

<div align="center">

## 💖 赞助支持

如果这个项目对您有帮助，欢迎赞助支持开发！

<img src="docs/sponsor/WechatPay.png?raw=true" alt="微信赞助" width="200">
<img src="docs/sponsor/AliPay.png?raw=true" alt="支付宝赞助" width="200">

**您的支持是我们持续改进的动力！**

</div>