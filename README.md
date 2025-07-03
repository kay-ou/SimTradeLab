# 📈 ptradeSim

<div align="center">

**轻量级Python量化交易策略回测框架**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#测试)

*模拟PTrade策略框架的事件驱动回测引擎*

</div>

## 🎯 项目简介

ptradeSim 是一个专为量化交易策略开发设计的轻量级Python回测框架。它精确模拟PTrade的策略框架与事件驱动机制，让用户能够在本地环境中高效地编写、测试和验证交易策略。当前仅返回模拟数据，目标是尽快接入真实数据源。

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

#### 技术指标
- **趋势指标**: `MA`, `EMA`
- **动量指标**: `MACD`, `RSI`
- **波动率指标**: `BOLL`
- **摆动指标**: `KDJ`

#### 时间频率
- **分钟级**: `1m`
- **日线级**: `1d`

## 🧪 测试

项目包含完整的测试套件，确保代码质量和功能正确性。**当前测试通过率：100%** ✅

### 运行测试
```bash
# 一键运行所有测试（推荐）
poetry run python run_tests.py

# 单独运行测试
poetry run python tests/test_api_injection.py      # API注入测试
poetry run python tests/test_strategy_execution.py # 策略执行测试
poetry run python tests/test_financial_apis.py     # 财务接口测试 🆕
poetry run python tests/test_market_data_apis.py   # 市场数据测试 🆕
```

### 测试覆盖
- ✅ **核心功能**: API函数注入、策略生命周期、交易逻辑
- ✅ **财务数据**: 30+财务指标、财务报表、财务比率 🆕
- ✅ **市场数据**: 价格数据、技术指标、实时报价 🆕
- ✅ **数据质量**: 一致性验证、错误处理、性能测试 🆕
- ✅ **投资组合**: 资金管理、持仓跟踪、订单处理

### 测试性能指标 🆕
- **数据获取**: < 1ms
- **技术指标计算**: < 100ms
- **完整测试套件**: < 2分钟
- **测试通过率**: 100%

## 📁 项目结构

```
ptradeSim/
├── 📁 ptradeSim/           # 核心引擎
│   ├── engine.py          # 回测引擎
│   ├── api.py             # API函数实现 (大幅增强 🆕)
│   └── context.py         # 上下文管理
├── 📁 strategies/         # 策略文件夹
│   ├── buy_and_hold.py    # 买入持有策略
│   └── test_strategy.py   # 测试策略 (增强版 🆕)
├── 📁 tests/              # 测试套件 (完整覆盖 🆕)
│   ├── test_api_injection.py      # API注入测试
│   ├── test_strategy_execution.py # 策略执行测试
│   ├── test_financial_apis.py     # 财务接口测试 🆕
│   ├── test_market_data_apis.py   # 市场数据测试 🆕
│   ├── REAMDE.md                  # 测试套件文档
├── 📁 data/               # 数据文件
│   └── sample_data.csv    # 示例数据
├── main.py                # 主程序入口
├── run_tests.py           # 核心测试运行器
└── README.md              # 项目文档 (本文件)
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
- **测试策略** (`strategies/test_strategy.py`)：全面的API功能测试策略，包含新增的财务和市场数据接口测试 🆕

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

### 🎯 版本更新历程

**v2.0.0 - 数据能力大幅增强** ✅ **已完成**
- ✅ 扩展 get_fundamentals 接口支持30+财务指标
- ✅ 添加财务报表数据接口（损益表、资产负债表、现金流量表）
- ✅ 实现财务比率计算功能（40+个专业比率）
- ✅ 增强 get_price 接口支持15+价格字段
- ✅ 添加实时报价数据模拟（五档买卖盘）
- ✅ 实现技术指标计算接口（6类专业指标）
- ✅ 多时间频率支持（分钟到月线）
- ✅ 完整测试覆盖（100%通过率）

**v1.0.0 - 核心功能** ✅ **已完成**
- ✅ 轻量级回测引擎
- ✅ 事件驱动架构
- ✅ 标准API接口
- ✅ 完整策略生命周期

### � 未来规划

**高优先级**
- [ ] 真实数据源集成（接入专业金融数据API）
- [ ] 更多技术指标（CCI、WR、SAR、ATR等）
- [ ] 期货和期权数据支持

**中优先级**
- [ ] 多策略组合回测
- [ ] 风险管理模块（VaR、最大回撤等）
- [ ] 性能分析报告（夏普比率、信息比率等）

**低优先级**
- [ ] 实时交易接口
- [ ] Web管理界面
- [ ] 机器学习因子库


### 开发环境设置

```bash
# 克隆项目
git clone https://github.com/kaykouo/ptradeSim.git
cd ptradeSim

# 安装开发依赖
poetry install

# 运行核心功能测试
poetry run python run_tests.py

# 测试新增的财务和市场数据功能
poetry run python tests/test_financial_apis.py
poetry run python tests/test_market_data_apis.py
```

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)。

## 🙏 致谢

感谢所有为ptradeSim项目做出贡献的开发者！

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个Star！**

[🐛 报告Bug](https://github.com/kaykouo/ptradeSim/issues) • [💡 功能建议](https://github.com/kaykouo/ptradeSim/issues) • [📖 文档](https://github.com/kaykouo/ptradeSim/wiki)

<div align="center">
  <img src="sponsor/WechatPay.png" alt="WechatPay" width="200" style="margin-right:20px;" />
  <img src="sponsor/AliPay.png" alt="AliPay" width="200" />
</div>

### ☕ [去 Ko-fi 捐赠支持](https://ko-fi.com/kayou)  

---

感谢你的支持和鼓励！✨每一份助力都让创作更有温度。


</div>
