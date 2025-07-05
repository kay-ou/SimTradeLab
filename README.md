# 📈 ptradeSim

<div align="center">

**轻量级Python量化交易策略回测框架**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#测试)
[![Version](https://img.shields.io/badge/Version-2.1.0-orange.svg)](#版本历程)

*模拟PTrade策略框架的事件驱动回测引擎*

</div>

## 🎯 项目简介

ptradeSim 是一个专为量化交易策略开发设计的轻量级Python回测框架。它精确模拟PTrade的策略框架与事件驱动机制，让用户能够在本地环境中高效地编写、测试和验证交易策略。**现已支持真实数据源接入**，包括Tushare、AkShare等主流数据源。

### 🌟 v2.1.0 重大更新

#### 🔌 真实数据源集成
- **AkShare数据源**：支持真实A股数据获取，包含实时价格、成交量等
- **Tushare数据源**：专业级金融数据接口（需要token配置）
- **智能数据源管理**：主数据源失败时自动切换备用数据源
- **配置化管理**：通过 `ptrade_config.yaml` 统一管理数据源设置

#### 🛠️ 引擎优化
- **API注入机制优化**：修复了类对象被错误注入的问题，确保只注入函数
- **性能分析增强**：改进了性能指标计算，提供更友好的错误提示


#### 📊 策略改进
- **真实数据策略**：新增 `real_data_strategy.py` 展示如何使用真实A股数据
- **智能回退机制**：历史数据不足时自动切换到简单交易策略
- **详细交易日志**：提供中文日志输出，便于策略调试和分析

**📖 文档中心：** [docs/README.md](docs/README.md) | **🚀 快速开始：** [5分钟上手](#🚀-快速开始) | **🧪 测试文档：** [tests/README.md](tests/README.md) | **🌐 真实数据源：** [真实数据源使用](#🌐-真实数据源使用) | **⚡ 命令行工具：** [命令行执行](#⚡-命令行执行工具)

### ✨ 核心特性

| 特性 | 描述 | 优势 |
|------|------|------|
| 🚀 **轻量级架构** | 核心代码简洁，易于理解和扩展 | 快速上手，便于定制 |
| ⚡ **事件驱动** | 基于事件循环机制，模拟真实交易环境 | 高度还原实盘交易流程 |
| 🔄 **完整生命周期** | 支持策略从初始化到盘后处理的全流程 | 策略逻辑完整性保证 |
| 💰 **交易仿真** | 内置账户与持仓管理，自动处理订单和资金 | 精确的资金和风险管理 |
| 🛠️ **标准API** | 提供与主流平台一致的API接口 | 无缝迁移现有策略 |
| 🏠 **本地运行** | 无需外部服务依赖，完全本地化 | 快速开发和调试 |
| 📊 **丰富数据** | 30+财务指标、技术指标、实时报价 | 专业级数据支持 |
| ⏱️ **多频率** | 支持日线、分钟级等多种交易频率 | 灵活的策略开发 |
| 📋 **标准格式** | 支持标准CSV长格式数据 | 便于多股票数据处理 |


## 🚀 快速开始

### 📦 安装

**方式一：从源码安装（推荐）**
```bash
# 克隆项目
git clone https://github.com/kaykouo/ptradeSim.git
cd ptradeSim

# 安装核心依赖
poetry install

# 可选：安装真实数据源依赖
poetry install --with data    # 安装所有数据源（推荐）

# 或者单独安装特定数据源
pip install tushare      # Tushare数据源
pip install akshare      # AkShare数据源
```

**方式二：直接下载**
```bash
# 下载并解压项目文件
wget https://github.com/kaykouo/ptradesim/archive/main.zip
unzip main.zip && cd ptradeSim-main
poetry install
```

### ✅ 环境要求

- Python 3.10+
- pandas >= 2.3.0
- matplotlib >= 3.10.3
- 推荐使用Poetry进行依赖管理

### 🎯 5分钟上手指南

**1. 了解数据格式**

ptradeSim 使用标准的CSV长格式数据，包含以下必需列：
```csv
date,open,high,low,close,volume,security
2023-01-01,100.00,102.50,99.50,101.20,1500000,STOCK_A
2023-01-02,101.20,103.80,100.90,102.50,1600000,STOCK_A
```

📖 **详细格式说明**: [docs/DATA_FORMAT.md](docs/DATA_FORMAT.md)

**2. 运行示例策略**

使用CSV数据源（传统方式）：
```bash
# 运行内置的测试策略
poetry run python main.py

# 或运行买入持有策略
poetry run python -c "
from ptradesim.engine import BacktestEngine
engine = BacktestEngine(
    strategy_file='strategies/buy_and_hold.py',
    data_path='data/sample_data.csv',
    start_date='2023-01-13',
    end_date='2023-01-16',
    initial_cash=1000000.0
)
engine.run()
"
```

使用真实数据源（AkShare）：
```bash
# 使用AkShare数据源获取真实A股数据
poetry run python -c "
from ptradesim import BacktestEngine
from ptradesim.data_sources import AkshareDataSource

# 创建AkShare数据源
akshare_source = AkshareDataSource()

# 使用真实数据源进行回测
engine = BacktestEngine(
    strategy_file='strategies/real_data_strategy.py',
    data_source=akshare_source,
    securities=['000001.SZ', '000002.SZ', '600000.SH'],
    start_date='2024-12-01',
    end_date='2024-12-05',
    initial_cash=1000000.0
)
engine.run()
"
```

使用Tushare数据源（需要token）：
```bash
# 配置Tushare token
export TUSHARE_TOKEN=your_token_here

poetry run python -c "
from ptradesim import BacktestEngine
from ptradesim.data_sources import TushareDataSource

tushare_source = TushareDataSource()
engine = BacktestEngine(
    strategy_file='strategies/real_data_strategy.py',
    data_source=tushare_source,
    securities=['000001.SZ', '000002.SZ'],
    start_date='2024-01-01',
    end_date='2024-01-31',
    initial_cash=1000000.0
)
engine.run()
"
```

## ⚡ 命令行执行工具

ptradeSim v2.1.0 新增了专业的命令行执行工具，让策略执行更加便捷和规范。

### 🔧 基本用法

```bash
# 查看帮助信息
poetry run python ptradeSim.py --help

# 使用CSV数据源
poetry run python ptradeSim.py --strategy strategies/test_strategy.py --data data/sample_data.csv

# 使用AkShare真实数据源
poetry run python ptradeSim.py --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ,000002.SZ,600000.SH

# 使用Tushare数据源（需要token）
poetry run python ptradeSim.py --strategy strategies/real_data_strategy.py --data-source tushare --securities 000001.SZ,000002.SZ
```

### 📋 完整参数说明

| 参数 | 简写 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `--strategy` | `-s` | ✅ | 策略文件路径 | `strategies/test_strategy.py` |
| `--data` | `-d` | 🔄 | CSV数据文件路径 | `data/sample_data.csv` |
| `--data-source` | | 🔄 | 真实数据源类型 | `akshare`, `tushare` |
| `--securities` | | ⚠️ | 股票代码列表（逗号分隔） | `000001.SZ,000002.SZ` |
| `--start-date` | | | 回测开始日期 | `2024-12-01` |
| `--end-date` | | | 回测结束日期 | `2024-12-05` |
| `--cash` | | | 初始资金 | `1000000.0` |
| `--frequency` | | | 交易频率 | `1d`, `1m`, `5m` |
| `--verbose` | `-v` | | 显示详细输出 | |
| `--quiet` | `-q` | | 静默模式 | |

> 🔄 `--data` 和 `--data-source` 互斥，必须选择其一
> ⚠️ 使用真实数据源时必须指定 `--securities`

### 🎯 使用示例

**示例1：CSV数据源回测**
```bash
poetry run python ptradeSim.py \
  --strategy strategies/test_strategy.py \
  --data data/sample_data.csv \
  --start-date 2023-01-03 \
  --end-date 2023-01-05 \
  --cash 1000000
```

**示例2：真实数据源回测**
```bash
poetry run python ptradeSim.py \
  --strategy strategies/real_data_strategy.py \
  --data-source akshare \
  --securities 000001.SZ,000002.SZ,600000.SH \
  --start-date 2024-12-01 \
  --end-date 2024-12-05 \
  --cash 500000 \
  --verbose
```

**示例3：静默模式执行**
```bash
poetry run python ptradeSim.py \
  --strategy strategies/shadow_strategy.py \
  --data-source akshare \
  --securities 000001.SZ \
  --quiet
```

**3. 创建你的第一个策略**

创建文件 `my_strategy.py`：

```python
# -*- coding: utf-8 -*-

def initialize(context):
    """策略初始化 - 设置策略参数"""
    log.info("=== 策略初始化开始 ===")

    # 设置股票池
    g.securities = ['STOCK_A', 'STOCK_B']

    # 设置双均线参数
    g.short_ma = 5   # 短期均线
    g.long_ma = 20   # 长期均线

    log.info(f"股票池: {g.securities}")
    log.info(f"双均线参数: 短期{g.short_ma}日, 长期{g.long_ma}日")

def handle_data(context, data):
    """核心交易逻辑 - 每个交易日执行"""

    for stock in g.securities:
        if stock not in data:
            continue

        # 获取历史数据
        hist = get_history(stock, ['close'], g.long_ma, '1d')

        if len(hist) < g.long_ma:
            continue

        # 计算双均线
        ma_short = hist['close'][-g.short_ma:].mean()
        ma_long = hist['close'].mean()

        current_position = g.portfolio.positions[stock].amount
        current_price = data[stock]['close']

        # 金叉买入信号
        if ma_short > ma_long and current_position == 0:
            # 用30%资金买入
            cash_to_use = context.portfolio.cash * 0.3
            shares_to_buy = int(cash_to_use / current_price)

            if shares_to_buy > 0:
                order(stock, shares_to_buy)
                log.info(f"金叉买入 {stock}: {shares_to_buy}股 @ {current_price:.2f}")

        # 死叉卖出信号
        elif ma_short < ma_long and current_position > 0:
            order_target(stock, 0)
            log.info(f"死叉卖出 {stock}: 全部持仓 @ {current_price:.2f}")

def before_trading_start(context, data):
    """盘前处理"""
    pass

def after_trading_end(context, data):
    """盘后处理 - 记录当日状态"""
    total_value = context.portfolio.total_value
    cash = context.portfolio.cash

    log.info(f"当日结束 - 总资产: {total_value:,.2f}, 现金: {cash:,.2f}")
```

**3. 运行你的策略**
```bash
# 创建回测引擎并运行
poetry run python -c "
from ptradesim.engine import BacktestEngine
engine = BacktestEngine(
    strategy_file='my_strategy.py',
    data_path='data/sample_data.csv',
    start_date='2023-01-01',
    end_date='2023-01-31',
    initial_cash=1000000.0
)
engine.run()
"
```

## 🌐 真实数据源使用

ptradeSim v2.1.0 新增了真实数据源支持，让您可以使用真实的市场数据进行回测。

### 📋 支持的数据源

| 数据源 | 描述 | 配置要求 | 支持市场 |
|--------|------|----------|----------|
| **AkShare** | 免费开源金融数据接口 | 无需配置 | A股、港股、美股 |
| **Tushare** | 专业金融数据平台 | 需要token | A股、基金、期货 |
| **CSV** | 本地数据文件 | 无需配置 | 自定义格式 |

### 🔧 配置数据源

**方法1：通过配置文件**

创建 `ptrade_config.yaml`：
```yaml
data_sources:
  tushare:
    token: "your_tushare_token_here"
    priority: 1
  akshare:
    priority: 2
```

**方法2：直接在代码中使用**

```python
from ptradesim import BacktestEngine
from ptradesim.data_sources import AkshareDataSource

# 创建数据源
akshare_source = AkshareDataSource()

# 使用真实数据源
engine = BacktestEngine(
    strategy_file='strategies/real_data_strategy.py',
    data_source=akshare_source,  # 🔥 关键：指定数据源
    securities=['000001.SZ', '000002.SZ'],  # 🔥 关键：指定股票列表
    start_date='2024-12-01',
    end_date='2024-12-05',
    initial_cash=1000000.0
)
```

### 📊 真实数据 vs CSV数据对比

| 特性 | CSV数据源 | 真实数据源 |
|------|-----------|------------|
| **股票代码** | STOCK_A, STOCK_B | 000001.SZ, 600000.SH |
| **价格数据** | 模拟固定价格 | 真实市场价格 |
| **数据来源** | 本地文件 | 网络API |
| **配置方式** | `data_path='data.csv'` | `data_source=AkshareDataSource()` |
| **使用场景** | 策略开发、测试 | 策略验证、实盘前测试 |

### ⚠️ 注意事项

1. **网络连接**：真实数据源需要稳定的网络连接
2. **API限制**：部分数据源有调用频率限制
3. **数据质量**：真实数据可能存在缺失或异常值
4. **时间范围**：不同数据源支持的历史数据范围不同

## 🔧 核心功能

### 📊 数据接口

#### 财务数据
- **基本面数据**: 30+财务指标（市值、PE、ROE等）
- **财务报表**: 损益表、资产负债表、现金流量表
- **财务比率**: 40+专业比率（流动比率、资产负债率等）

#### 市场数据
- **价格数据**: 15+价格字段（OHLCV、涨跌幅、换手率等）
- **实时报价**: 五档买卖盘、市场快照
- **历史数据**: 多频率历史数据获取

#### 技术指标
- **趋势指标**: `MA`, `EMA`, `MACD`
- **动量指标**: `RSI`, `CCI`
- **波动率指标**: `BOLL`
- **摆动指标**: `KDJ`

#### 交易频率
- **日线级**: `1d` (默认)
- **分钟级**: `1m`, `5m`, `15m`, `30m`
- **其他**: `1h`, `1w`, `1M`

### 🛠️ 交易接口

#### 下单接口
- `order()` - 市价/限价下单
- `order_target()` - 目标仓位下单
- `order_value()` - 目标市值下单
- `cancel_order()` - 撤单

#### 查询接口
- `get_positions()` - 持仓查询
- `get_orders()` - 订单查询
- `get_trades()` - 成交查询

### 📈 性能分析
- 策略性能指标计算
- 基准对比分析
- 风险指标评估

## 🧪 测试

项目包含完整的测试套件，确保代码质量和功能正确性。**当前测试通过率：100%** ✅

### 运行测试
```bash
# 一键运行所有测试（推荐）
poetry run python run_tests.py

# 单独运行测试
poetry run python tests/test_api_injection.py      # API注入测试
poetry run python tests/test_strategy_execution.py # 策略执行测试
poetry run python tests/test_financial_apis.py     # 财务接口测试
poetry run python tests/test_market_data_apis.py   # 市场数据测试
poetry run python tests/test_minute_trading.py     # 分钟级交易测试
```

### 测试覆盖
- ✅ **核心功能**: API函数注入、策略生命周期、交易逻辑
- ✅ **财务数据**: 30+财务指标、财务报表、财务比率
- ✅ **市场数据**: 价格数据、技术指标、实时报价
- ✅ **分钟级交易**: 多频率支持、日内交易策略
- ✅ **数据质量**: 一致性验证、错误处理、性能测试
- ✅ **投资组合**: 资金管理、持仓跟踪、订单处理

### 测试性能指标
- **数据获取**: < 1ms
- **技术指标计算**: < 100ms
- **完整测试套件**: < 2分钟
- **测试通过率**: 100%

📖 **详细测试文档**: [tests/README.md](tests/README.md)

## 📁 项目结构

```
ptradeSim/                     # 项目根目录
├── 📦 核心包结构
│   └── src/ptradesim/         # 主要源代码包 (Poetry标准结构)
│       ├── __init__.py        # 包初始化，导出主要API
│       ├── engine.py          # 🚀 回测引擎核心 - BacktestEngine类
│       ├── context.py         # 📊 上下文和投资组合管理
│       ├── trading.py         # 💰 交易执行接口 - order, order_target等
│       ├── market_data.py     # 📈 市场数据接口 - get_history, get_current_data等
│       ├── financials.py      # 💼 财务数据接口 - 30+财务指标
│       ├── utils.py           # 🛠️ 工具函数集合
│       ├── performance.py     # 📊 性能分析模块 - 夏普比率、最大回撤等
│       ├── logger.py          # 📝 日志管理系统
│       ├── compatibility.py   # 🔄 版本兼容性处理
│       ├── cli.py             # ⚡ 命令行接口 - ptradeSim命令
│       ├── config/            # ⚙️ 配置管理模块
│       │   ├── __init__.py
│       │   └── data_config.py # 数据源配置管理
│       └── data_sources/      # 🌐 数据源模块
│           ├── __init__.py
│           ├── base.py        # 数据源基类定义
│           ├── csv_source.py  # CSV文件数据源
│           ├── akshare_source.py  # AkShare真实数据源
│           ├── tushare_source.py  # Tushare专业数据源
│           └── manager.py     # 数据源管理器
├── 📋 策略开发
│   └── strategies/            # 策略文件夹 - 所有交易策略
│       ├── buy_and_hold_strategy.py        # 买入持有策略
│       ├── dual_moving_average_strategy.py # 双均线策略
│       ├── technical_indicator_strategy.py # 技术指标策略
│       ├── minute_trading_strategy.py      # 分钟级交易策略
│       ├── grid_trading_strategy.py        # 网格交易策略
│       ├── momentum_strategy.py            # 动量策略
│       ├── real_data_strategy.py           # 真实数据策略
│       ├── shadow_strategy.py              # 影子策略（状态持久化）
│       └── test_strategy.py                # 综合测试策略
├── 🧪 测试体系
│   └── tests/                 # 完整测试套件 (100%覆盖率)
│       ├── __init__.py
│       ├── conftest.py        # pytest配置和fixtures
│       ├── README.md          # 测试文档说明
│       ├── unit/              # 单元测试
│       │   ├── test_engine.py
│       │   ├── test_api_functions.py
│       │   ├── test_financial_apis.py
│       │   ├── test_market_data_apis.py
│       │   └── test_technical_indicators.py
│       ├── integration/       # 集成测试
│       │   ├── test_data_sources.py
│       │   ├── test_strategy_execution.py
│       │   └── test_minute_trading.py
│       ├── e2e/              # 端到端测试
│       └── performance/       # 性能测试
├── 📚 文档系统
│   └── docs/                  # 完整文档体系
│       ├── README.md          # 文档导航中心
│       ├── STRATEGY_GUIDE.md  # 策略开发指南
│       ├── DATA_FORMAT.md     # 数据格式规范
│       ├── API_REFERENCE.md   # API参考文档
│       ├── TECHNICAL_INDICATORS.md # 技术指标文档
│       ├── REAL_DATA_SOURCES.md    # 真实数据源指南
│       ├── MULTI_FREQUENCY_TRADING.md # 多频率交易指南
│       └── DATA_MIGRATION_GUIDE.md    # 数据迁移指南
├── 📊 数据文件
│   └── data/                  # 示例数据文件
│       ├── sample_data.csv        # 日线示例数据（标准长格式）
│       └── minute_sample_data.csv # 分钟级示例数据
├── 🔧 工具脚本
│   └── scripts/               # 开发和发布工具
│       ├── release.py         # 自动发布脚本
│       ├── test-package.py    # 包测试脚本
│       └── RELEASE_GUIDE.md   # 发布指南
├── 🚀 入口文件
│   ├── main.py                # 主程序入口（兼容性）
│   ├── ptradeSim.py           # CLI入口脚本
│   └── run_tests.py           # 测试运行器
├── ⚙️ 配置文件
│   ├── pyproject.toml         # Poetry项目配置和依赖管理
│   ├── poetry.lock            # 依赖锁定文件
│   └── ptrade_config.yaml     # 数据源配置文件
├── 📄 项目文档
│   ├── README.md              # 项目主文档 (本文件)
│   ├── CHANGELOG.md           # 版本更新日志
│   └── LICENSE                # MIT开源许可证
└── 🗂️ 其他文件
    ├── .gitignore             # Git忽略文件配置
    ├── coverage.xml           # 测试覆盖率报告
    ├── htmlcov/               # HTML格式覆盖率报告
    ├── dist/                  # 构建产物目录
    └── sponsor/               # 赞助支持图片
```

### 📦 包结构说明

ptradeSim采用现代Python包管理最佳实践：

- **Poetry标准结构**: `src/ptradesim/` 布局，便于包管理和分发
- **模块化设计**: 核心功能按职责分离，便于维护和扩展
- **完整测试覆盖**: 单元测试、集成测试、端到端测试全覆盖
- **文档驱动**: 每个模块都有对应的详细文档

## 🎓 策略开发指南

### 策略生命周期

ptradeSim中的策略遵循标准的生命周期：

```python
def initialize(context):
    """策略初始化 - 只在开始时执行一次"""
    pass

def before_trading_start(context, data):
    """盘前处理 - 每个交易日开盘前执行"""
    pass

def handle_data(context, data):
    """核心逻辑 - 每个交易日执行"""
    pass

def after_trading_end(context, data):
    """盘后处理 - 每个交易日收盘后执行"""
    pass
```

### 最佳实践

1. **📊 数据验证**：在使用数据前检查其有效性
2. **💰 资金管理**：合理控制单次交易金额
3. **📝 日志记录**：使用log函数记录关键信息
4. **🔍 异常处理**：添加适当的错误处理逻辑
5. **🧪 充分测试**：编写测试验证策略逻辑

### 示例策略

项目提供了多个示例策略：

- **买入持有策略** (`strategies/buy_and_hold_strategy.py`)：简单的买入并持有策略
- **双均线策略** (`strategies/dual_moving_average_strategy.py`)：经典的双均线交易策略
- **技术指标策略** (`strategies/technical_indicator_strategy.py`)：基于多种技术指标的策略
- **分钟级策略** (`strategies/minute_trading_strategy.py`)：分钟级高频交易策略
- **综合测试策略** (`strategies/test_strategy.py`)：全面的API功能测试策略

## 📖 文档导航

| 文档类型 | 链接 | 描述 |
|---------|------|------|
| 📚 **文档中心** | [docs/README.md](docs/README.md) | 完整文档导航和索引 |
| 🚀 **策略开发** | [docs/STRATEGY_GUIDE.md](docs/STRATEGY_GUIDE.md) | 详细的策略开发教程 |
| 🔧 **API参考** | [docs/API_REFERENCE.md](docs/API_REFERENCE.md) | 完整的API接口文档 |
| 📊 **技术指标** | [docs/TECHNICAL_INDICATORS.md](docs/TECHNICAL_INDICATORS.md) | 技术指标使用指南 |
| ⏱️ **多频率交易** | [docs/MULTI_FREQUENCY_TRADING.md](docs/MULTI_FREQUENCY_TRADING.md) | 分钟级交易指南 |
| 🧪 **测试文档** | [tests/README.md](tests/README.md) | 测试套件说明文档 |

### 高级策略示例 🆕

```python
def initialize(context):
    """使用新增功能的策略示例"""
    g.securities = ['STOCK_A', 'STOCK_B']
    g.rebalance_period = 20  # 20天调仓一次

def before_trading_start(context, data):
    """使用财务数据进行股票筛选"""
    # 获取财务比率数据
    ratios = get_financial_ratios(g.securities,
                                 ['roe', 'current_ratio', 'debt_to_equity'])

    # 筛选优质股票：ROE > 15%, 流动比率 > 1.5, 资产负债率 < 0.5
    good_stocks = []
    for stock in g.securities:
        if (ratios.loc[stock, 'roe'] > 15 and
            ratios.loc[stock, 'current_ratio'] > 1.5 and
            ratios.loc[stock, 'debt_to_equity'] < 0.5):
            good_stocks.append(stock)

    g.target_stocks = good_stocks
    log.info(f"筛选出优质股票: {good_stocks}")

def handle_data(context, data):
    """使用技术指标进行交易决策"""
    for stock in g.target_stocks:
        # 计算技术指标
        macd_data = get_technical_indicators([stock], 'MACD')
        rsi_data = get_technical_indicators([stock], 'RSI', period=14)

        # 获取最新指标值
        latest_macd = macd_data[('MACD_DIF', stock)].iloc[-1]
        latest_rsi = rsi_data[(f'RSI14', stock)].iloc[-1]

        current_position = context.portfolio.positions[stock].amount

        # 买入信号：MACD金叉且RSI < 70
        if latest_macd > 0 and latest_rsi < 70 and current_position == 0:
            order_value(stock, context.portfolio.cash * 0.3)
            log.info(f"技术指标买入 {stock}")

        # 卖出信号：RSI > 80
        elif latest_rsi > 80 and current_position > 0:
            order_target(stock, 0)
            log.info(f"技术指标卖出 {stock}")
```

## 📦 作为Python包使用

ptradeSim可以作为标准Python包安装和使用，支持多种安装和使用方式。

### 🔧 安装方式

**方式一：从PyPI安装（推荐）**
```bash
# 安装核心包
pip install ptradesim

# 或使用Poetry
poetry add ptradesim

# 安装包含数据源的完整版本
pip install ptradesim[data]  # 包含akshare和tushare
```

**方式二：从源码安装**
```bash
# 克隆并安装
git clone https://github.com/kay-ou/ptradeSim.git
cd ptradeSim
pip install -e .  # 开发模式安装

# 或使用Poetry
poetry install --with data
```

**方式三：直接从GitHub安装**
```bash
pip install git+https://github.com/kay-ou/ptradeSim.git
```

### 💻 在代码中使用

**基本使用示例**
```python
# 导入核心组件
from ptradesim import BacktestEngine
from ptradesim.data_sources import AkshareDataSource, CSVDataSource

# 方式1：使用CSV数据源
engine = BacktestEngine(
    strategy_file='my_strategy.py',
    data_path='data/my_data.csv',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_cash=1000000.0
)
engine.run()

# 方式2：使用真实数据源
akshare_source = AkshareDataSource()
engine = BacktestEngine(
    strategy_file='my_strategy.py',
    data_source=akshare_source,
    securities=['000001.SZ', '000002.SZ'],
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_cash=1000000.0
)
engine.run()
```

**高级使用示例**
```python
from ptradesim import BacktestEngine
from ptradesim.data_sources import TushareDataSource
from ptradesim.performance import PerformanceAnalyzer
import os

# 配置Tushare数据源
os.environ['TUSHARE_TOKEN'] = 'your_token_here'
tushare_source = TushareDataSource()

# 创建回测引擎
engine = BacktestEngine(
    strategy_file='strategies/my_advanced_strategy.py',
    data_source=tushare_source,
    securities=['000001.SZ', '000002.SZ', '600000.SH'],
    start_date='2023-01-01',
    end_date='2024-01-01',
    initial_cash=1000000.0,
    frequency='1d',  # 交易频率
    commission_ratio=0.0003,  # 手续费率
    min_commission=5.0  # 最小手续费
)

# 运行回测
results = engine.run()

# 性能分析
analyzer = PerformanceAnalyzer(results)
performance_metrics = analyzer.calculate_metrics()
print(f"夏普比率: {performance_metrics['sharpe_ratio']:.2f}")
print(f"最大回撤: {performance_metrics['max_drawdown']:.2%}")
```

### 🎯 命令行工具

安装后可直接使用命令行工具：

```bash
# 使用ptradesim命令（推荐）
ptradesim --strategy my_strategy.py --data-source akshare --securities 000001.SZ

# 或使用python -m方式
python -m ptradesim.cli --strategy my_strategy.py --data data.csv
```

### 📚 API参考

安装后可以访问完整的API：

```python
# 核心引擎
from ptradesim import BacktestEngine

# 数据源
from ptradesim.data_sources import (
    AkshareDataSource,
    TushareDataSource,
    CSVDataSource
)

# 性能分析
from ptradesim.performance import PerformanceAnalyzer

# 工具函数
from ptradesim.utils import (
    validate_data_format,
    calculate_returns,
    format_currency
)

# 配置管理
from ptradesim.config import DataConfig
```

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 📋 Git提交规范

我们使用[约定式提交](https://www.conventionalcommits.org/zh-hans/)规范，请按以下格式提交：

```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

#### 🏷️ 提交类型说明

| 类型 | 描述 | 示例 |
|------|------|------|
| `feat` | ✨ 新功能 | `feat: 添加AkShare数据源支持` |
| `fix` | 🐛 Bug修复 | `fix: 修复持仓计算错误` |
| `docs` | 📚 文档更新 | `docs: 更新API参考文档` |
| `style` | 🎨 代码格式 | `style: 格式化trading.py代码` |
| `refactor` | ♻️ 代码重构 | `refactor: 重构数据源管理器` |
| `test` | 🧪 测试相关 | `test: 添加财务API单元测试` |
| `chore` | 🔧 构建/工具 | `chore: 更新依赖版本` |
| `perf` | ⚡ 性能优化 | `perf: 优化历史数据查询性能` |
| `ci` | 👷 CI/CD | `ci: 添加GitHub Actions工作流` |
| `build` | 📦 构建系统 | `build: 更新Poetry配置` |
| `revert` | ⏪ 回滚提交 | `revert: 回滚feat: 添加新功能` |

#### 📝 提交示例

```bash
# 新功能
git commit -m "feat(data): 添加Tushare数据源支持"

# Bug修复
git commit -m "fix(engine): 修复回测引擎内存泄漏问题"

# 文档更新
git commit -m "docs: 更新策略开发指南"

# 测试添加
git commit -m "test(api): 添加交易接口集成测试"

# 重构代码
git commit -m "refactor(core): 重构性能分析模块结构"
```

### 🚀 贡献流程

1. 🍴 **Fork项目**: 点击GitHub页面右上角的Fork按钮
2. 🌿 **创建分支**: `git checkout -b feat/your-feature-name`
3. 💻 **开发功能**: 编写代码并确保测试通过
4. 🧪 **运行测试**: `poetry run python run_tests.py`
5. 📝 **提交更改**: 使用规范的提交信息
6. 📤 **推送分支**: `git push origin feat/your-feature-name`
7. 🔄 **创建PR**: 在GitHub上创建Pull Request

### 🎯 贡献类型

| 贡献类型 | 描述 | 优先级 |
|----------|------|--------|
| 🐛 **Bug修复** | 修复现有功能的问题 | 🔴 高 |
| ✨ **新功能** | 添加新的功能特性 | 🟡 中 |
| 📚 **文档改进** | 完善文档和示例 | 🟢 中 |
| 🧪 **测试用例** | 增加测试覆盖率 | 🟢 中 |
| 🎨 **代码优化** | 提升代码质量和性能 | 🔵 低 |
| 🌐 **国际化** | 多语言支持 | 🔵 低 |

### ✅ 贡献要求

- **代码质量**: 遵循PEP 8规范，使用类型提示
- **测试覆盖**: 新功能必须包含相应测试
- **文档更新**: 重要功能需要更新相关文档
- **向后兼容**: 避免破坏现有API接口
- **性能考虑**: 确保不会显著影响性能

## 📋 版本历程

### v2.1.0 - 真实数据源集成与引擎优化 ✅ **已完成** (2025-07-05)

#### 🌐 真实数据源支持
- **AkShare集成**：支持免费获取真实A股数据，包含价格、成交量等完整信息
- **Tushare集成**：支持专业级金融数据接口（需要token配置）
- **智能数据源管理**：主数据源失败时自动切换备用数据源
- **配置化管理**：通过 `ptrade_config.yaml` 统一管理数据源设置

#### 🛠️ 引擎核心优化
- **API注入机制修复**：解决了类对象被错误注入的问题，确保只注入函数对象
- **set_commission函数更新**：支持新签名 `set_commission(commission_ratio=0.0003, min_commission=5.0, type="STOCK")`
- **性能分析增强**：改进性能指标计算，提供更友好的数据不足提示
- **策略兼容性**：移除非标准API函数（如`on_strategy_end`），确保与ptrade完全兼容

#### 📊 策略功能改进
- **真实数据策略**：新增 `real_data_strategy.py` 展示真实A股数据使用
- **智能回退机制**：历史数据不足时自动切换到简单交易策略
- **详细交易日志**：提供中文日志输出，便于策略调试和分析
- **持仓管理优化**：修复了持仓数据格式问题，支持字典格式的持仓信息

#### 🔧 依赖管理优化
- **模块化依赖**：将数据源依赖移至可选组，支持按需安装
- **版本冲突修复**：解决了akshare重复定义的问题
- **安装简化**：支持 `poetry install --with data` 安装数据源依赖

### v2.0.0 - 数据能力大幅增强 ✅ **已完成** (2024-12)
- ✅ **财务数据增强**: 30+财务指标、完整财务报表、40+财务比率
- ✅ **市场数据扩展**: 15+价格字段、实时报价、五档买卖盘
- ✅ **技术指标系统**: MACD、RSI、KDJ、CCI、BOLL等专业指标
- ✅ **多频率支持**: 日线、分钟级等多种交易频率
- ✅ **分钟级交易**: 完整的分钟级交易策略支持
- ✅ **性能分析**: 专业的策略性能评估模块
- ✅ **版本兼容**: 多版本ptrade API兼容性
- ✅ **完整测试**: 100%测试覆盖率，5个测试模块

### v1.0.0 - 核心功能 ✅ **已完成**
- ✅ **轻量级引擎**: 事件驱动的回测引擎
- ✅ **策略框架**: 完整的策略生命周期管理
- ✅ **交易系统**: 订单管理、持仓跟踪、资金管理
- ✅ **API接口**: 标准化的交易和查询接口

## 🚀 未来规划

### 高优先级
- [ ] **真实数据源**: 接入专业金融数据API
- [ ] **更多指标**: CCI、WR、SAR、ATR等技术指标
- [ ] **衍生品支持**: 期货和期权数据支持

### 中优先级
- [ ] **组合回测**: 多策略组合回测功能
- [ ] **风险管理**: VaR、最大回撤等风险指标
- [ ] **报告系统**: 夏普比率、信息比率等性能报告

### 低优先级
- [ ] **实时交易**: 实时交易接口对接
- [ ] **Web界面**: 可视化管理界面
- [ ] **AI因子**: 机器学习因子库


## 📄 许可证

本项目采用 [MIT许可证](LICENSE)。

## 🙏 致谢

感谢所有为ptradeSim项目做出贡献的开发者！

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个Star！**

[🐛 报告Bug](https://github.com/kaykouo/ptradesim/issues) • [💡 功能建议](https://github.com/kaykouo/ptradesim/issues) • [📖 文档中心](docs/README.md) • [🔧 API参考](docs/API_REFERENCE.md) • [📋 数据格式](docs/DATA_FORMAT.md)

<div align="center">
  <img src="sponsor/WechatPay.png" alt="WechatPay" width="200" style="margin-right:20px;" />
  <img src="sponsor/AliPay.png" alt="AliPay" width="200" />
</div>

### ☕ [去 Ko-fi 捐赠支持](https://ko-fi.com/kayou)  

---

感谢你的支持和鼓励！✨每一份助力都让创作更有温度。


</div>
