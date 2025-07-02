# 📈 ptradeSim

<div align="center">

**轻量级Python量化交易策略回测框架**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#测试)

*模拟PTrade策略框架的事件驱动回测引擎*

</div>

## 🎯 项目简介

ptradeSim 是一个专为量化交易策略开发设计的轻量级Python回测框架。它精确模拟PTrade的策略框架与事件驱动机制，让用户能够在本地环境中高效地编写、测试和验证交易策略。

### ✨ 核心特性

| 特性 | 描述 | 优势 |
|------|------|------|
| 🚀 **轻量级架构** | 核心代码简洁，易于理解和扩展 | 快速上手，便于定制 |
| ⚡ **事件驱动** | 基于事件循环机制，模拟真实交易环境 | 高度还原实盘交易流程 |
| 🔄 **完整生命周期** | 支持策略从初始化到盘后处理的全流程 | 策略逻辑完整性保证 |
| 💰 **交易仿真** | 内置账户与持仓管理，自动处理订单和资金 | 精确的资金和风险管理 |
| 🛠️ **标准API** | 提供与主流平台一致的API接口 | 无缝迁移现有策略 |
| 🏠 **本地运行** | 无需外部服务依赖，完全本地化 | 快速开发和调试 |

## 🚀 快速开始

### 📦 安装

**方式一：从源码安装（推荐）**
```bash
# 克隆项目
git clone https://github.com/kaykouo/ptradeSim.git
cd ptradeSim

# 使用Poetry安装依赖
poetry install

# 或使用pip安装
pip install -e .
```

**方式二：直接下载**
```bash
# 下载并解压项目文件
wget https://github.com/kaykouo/ptradeSim/archive/main.zip
unzip main.zip && cd ptradeSim-main
poetry install
```

### ✅ 环境要求

- Python 3.8+
- pandas >= 1.3.0
- 推荐使用Poetry进行依赖管理

### 🎯 5分钟上手指南

**1. 运行示例策略**
```bash
# 运行内置的测试策略
poetry run python main.py

# 或运行买入持有策略
poetry run python -c "
from ptradeSim.engine import BacktestEngine
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

**2. 创建你的第一个策略**

创建文件 `my_strategy.py`：

```python
# -*- coding: utf-8 -*-

def initialize(context):
    """策略初始化 - 设置策略参数"""
    log.info("=== 策略初始化开始 ===")

    # 设置股票池
    context.securities = ['STOCK_A', 'STOCK_B']

    # 设置双均线参数
    context.short_ma = 5   # 短期均线
    context.long_ma = 20   # 长期均线

    log.info(f"股票池: {context.securities}")
    log.info(f"双均线参数: 短期{context.short_ma}日, 长期{context.long_ma}日")

def handle_data(context, data):
    """核心交易逻辑 - 每个交易日执行"""

    for stock in context.securities:
        if stock not in data:
            continue

        # 获取历史数据
        hist = get_history(stock, ['close'], context.long_ma, '1d')

        if len(hist) < context.long_ma:
            continue

        # 计算双均线
        ma_short = hist['close'][-context.short_ma:].mean()
        ma_long = hist['close'].mean()

        current_position = context.portfolio.positions[stock].amount
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
from ptradeSim.engine import BacktestEngine
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

## 📚 API参考

### 🔧 核心交易函数

| 函数 | 参数 | 描述 | 示例 |
|------|------|------|------|
| `order(security, amount)` | 股票代码, 股数 | 按指定股数下单 | `order('STOCK_A', 100)` |
| `order_target(security, amount)` | 股票代码, 目标股数 | 调整持仓至目标股数 | `order_target('STOCK_A', 0)` |
| `order_value(security, value)` | 股票代码, 金额 | 按指定金额下单 | `order_value('STOCK_A', 10000)` |

### 📊 数据获取函数

| 函数 | 参数 | 描述 | 示例 |
|------|------|------|------|
| `get_history(security, fields, count, freq)` | 股票, 字段, 天数, 频率 | 获取历史数据 | `get_history('STOCK_A', ['close'], 20, '1d')` |
| `get_price(security)` | 股票代码 | 获取当前价格 | `get_price('STOCK_A')` |
| `get_Ashares()` | 无 | 获取所有A股列表 | `stocks = get_Ashares()` |

### 💰 账户信息

| 属性 | 描述 | 示例 |
|------|------|------|
| `context.portfolio.cash` | 可用现金 | `cash = context.portfolio.cash` |
| `context.portfolio.total_value` | 总资产价值 | `total = context.portfolio.total_value` |
| `context.portfolio.positions` | 持仓信息 | `pos = context.portfolio.positions['STOCK_A']` |

### 📝 日志函数

| 函数 | 描述 | 示例 |
|------|------|------|
| `log.info(message)` | 记录信息日志 | `log.info("买入成功")` |
| `log.warning(message)` | 记录警告日志 | `log.warning("资金不足")` |
| `log.set_log_level(level)` | 设置日志级别 | `log.set_log_level(log.LEVEL_INFO)` |

## 🧪 测试

项目包含完整的测试套件，确保代码质量和功能正确性。

### 运行测试
```bash
# 一键运行所有测试（推荐）
poetry run python run_tests.py

# 或单独运行测试
poetry run python tests/test_api_injection.py      # API注入测试
poetry run python tests/test_strategy_execution.py # 策略执行测试
```

### 测试覆盖
- ✅ API函数注入验证
- ✅ 策略生命周期测试
- ✅ 交易逻辑验证
- ✅ 投资组合管理测试
- ✅ 日志系统测试

详细测试文档请查看 [tests/README.md](tests/README.md)

## 📁 项目结构

```
ptradeSim/
├── 📁 ptradeSim/           # 核心引擎
│   ├── engine.py          # 回测引擎
│   ├── api.py             # API函数实现
│   └── context.py         # 上下文管理
├── 📁 strategies/         # 策略文件夹
│   ├── buy_and_hold.py    # 买入持有策略
│   └── test_strategy.py   # 测试策略
├── 📁 tests/              # 测试套件
│   ├── test_api_injection.py
│   └── test_strategy_execution.py
├── 📁 data/               # 数据文件
│   └── sample_data.csv    # 示例数据
├── main.py                # 主程序入口
├── run_tests.py           # 测试运行器
└── README.md              # 项目文档
```

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

- **买入持有策略** (`strategies/buy_and_hold.py`)：简单的买入并持有策略
- **测试策略** (`strategies/test_strategy.py`)：全面的API功能测试策略

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 如何贡献

1. 🍴 Fork 本项目
2. 🌿 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 📝 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 📤 推送到分支 (`git push origin feature/AmazingFeature`)
5. 🔄 提交 Pull Request

### 贡献类型

- 🐛 Bug修复
- ✨ 新功能开发
- 📚 文档改进
- 🧪 测试用例
- 🎨 代码优化

### 🎯 改进计划

**优先级高 - 基本面数据增强**
- 扩展 get_fundamentals 接口支持更多财务指标
- 添加财务报表数据接口（损益表、资产负债表、现金流量表）
- 实现财务比率计算功能
**优先级中 - 市场数据完善**
- 增强 get_price 接口支持更多价格字段
- 添加实时报价数据模拟
- 实现技术指标计算接口
**优先级低 - 高级功能**
- 添加内幕交易数据接口
- 实现机构持股数据接口
- 添加新闻和公告数据接口

### 💡 实现方案建议

保持兼容性：在现有接口基础上扩展，不破坏现有策略
数据源选择：
集成真实金融数据API（如Context7中的Financial Datasets API）
或扩展现有CSV数据格式，增加更多字段
渐进式改进：优先实现最常用的财务指标和市场数据


### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/kaykouo/ptradeSim.git
cd ptradeSim

# 安装开发依赖
poetry install

# 运行测试确保环境正常
poetry run python run_tests.py
```

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)。

## 🙏 致谢

感谢所有为ptradeSim项目做出贡献的开发者！

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个Star！**

[🐛 报告Bug](https://github.com/kaykouo/ptradeSim/issues) • [💡 功能建议](https://github.com/kaykouo/ptradeSim/issues) • [📖 文档](https://github.com/kaykouo/ptradeSim/wiki)

</div>
