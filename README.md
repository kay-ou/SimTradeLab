# 📈 SimTradeLab

**轻量级量化回测框架 - PTrade API本地实现**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![License: Commercial](https://img.shields.io/badge/License-Commercial--Available-red)](licenses/LICENSE-COMMERCIAL.md)
[![Version](https://img.shields.io/badge/Version-2.6.1-orange.svg)](#)
[![PyPI](https://img.shields.io/pypi/v/simtradelab.svg)](https://pypi.org/project/simtradelab/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/simtradelab.svg)](https://pypi.org/project/simtradelab/)

*完整模拟PTrade平台API，策略可无缝迁移*

---

## 🎯 项目简介

SimTradeLab（深测Lab） 是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动架构。它具备完全自主的实现与出色的扩展能力，为策略开发者提供一个轻量级、结构清晰、模块可插拔的策略验证环境。框架无需依赖 PTrade 即可独立运行，但与其语法保持高度兼容。所有在 SimTradeLab 中编写的策略可无缝迁移至 PTrade 平台，反之亦然，两者之间的 API 可直接互通使用。详情参考：https://github.com/kay-ou/ptradeAPI 项目。

**核心特性：**
- ✅ **46个回测/研究API** - 股票日/分钟线回测场景100%覆盖
- ⚡ **100-160倍性能提升** - 本地回测比PTrade平台快100-160倍
- 🚀 **数据常驻内存** - 单例模式，首次加载后常驻，二次运行秒级启动
- 💾 **多级智能缓存** - LRU缓存（MA/VWAP/复权/历史数据），命中率>95%
- 🧠 **智能数据加载** - AST静态分析策略代码，按需加载数据，节省内存
- 🔧 **生命周期控制** - 7个生命周期阶段，严格模拟PTrade的API调用限制
- 📊 **完整统计报告** - 收益、风险（夏普/索提诺/卡玛）、交易明细、持仓批次、FIFO分红税，支持 CSV 导出
- 🔌 **模块化设计** - 清晰的代码结构，易于扩展和定制

**当前版本：** v2.6.1 | **开发状态：** 核心功能完善，正在策略实战中持续优化

---

## 🚀 快速开始

### 📦 安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 安装最新版本
pip install simtradelab

# 包含技术指标（需要系统级ta-lib，可选）
pip install simtradelab[indicators]

# 包含优化器（可选）
pip install simtradelab[optimizer]

# 安装全部可选依赖
pip install simtradelab[all]
```

**系统依赖（仅使用技术指标API时需要）：**
- macOS: `brew install ta-lib`
- Linux: ta-lib 需从源码编译，参考 [ta-lib 官方文档](https://github.com/ta-lib/ta-lib-python)
- Windows: 从 [ta-lib releases](https://github.com/ta-lib/ta-lib-python) 下载预编译包

### 📁 准备数据

将数据文件放到 `data/` 目录：
```
data/
├── stocks/              # 股票日线数据
├── stocks_1m/           # 股票分钟数据（分钟回测需要）
├── valuation/           # 估值数据
├── fundamentals/        # 财务数据
├── exrights/            # 除权数据
└── metadata/            # 元数据
```

**数据获取：** 推荐使用 [SimTradeData](https://github.com/kay-ou/SimTradeData) 项目获取A股历史数据

### ✍️ 编写策略

创建策略文件 `strategies/my_strategy/backtest.py`：

```python
def initialize(context):
    """策略初始化"""
    set_benchmark('000300.SS')
    context.stocks = ['600519.SS', '000858.SZ']

def handle_data(context, data):
    """交易逻辑（日线每日调用，分钟线每分钟调用）"""
    for stock in context.stocks:
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
```

**注意：Backtest模式严格模拟PTrade限制**
- ❌ 不支持f-string（使用 `.format()` 或 `%` 格式化）
- ❌ 不支持io、sys等模块导入
- ✅ 启动时自动检查Python 3.5兼容性

### ▶️ 运行回测

```python
# run_backtest.py
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig

config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=1000000.0,
    frequency='1d',       # '1d' 日线回测（默认），'1m' 分钟回测
    benchmark_code='000300.SS',  # 基准指数（默认沪深300）
    enable_logging=True,  # 生成 .log 日志文件（默认开启）
    enable_charts=True,   # 生成 .png 可视化图表（默认开启）
    enable_export=False,  # 生成 .csv 每日统计和持仓快照（默认关闭）
    sandbox=True,         # PTrade 兼容模式，限制 f-string 等语法（默认开启）
)

runner = BacktestRunner()
report = runner.run(config=config)
```

```bash
poetry run python run_backtest.py
```

### 📊 查看结果

回测完成后，在策略目录下生成：
```
strategies/my_strategy/stats/
├── backtest_*.log                     # 详细日志（enable_logging=True）
├── backtest_*.png                     # 4图可视化（enable_charts=True）
├── daily_stats_*.csv                  # 每日组合价值/盈亏/买卖金额（enable_export=True）
└── positions_history_*.csv            # 每日持仓快照（enable_export=True）
```

**开启 CSV 导出：**
```python
config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    enable_export=True   # 自动导出 CSV
)
```

**批量回测多个时间段：**
```python
from simtradelab.backtest.batch import BatchBacktestRunner, BatchConfig

runner = BatchBacktestRunner()
results = runner.run(BatchConfig(
    strategy_name='my_strategy',
    date_ranges=[('2023-01-01', '2023-06-30'), ('2023-07-01', '2023-12-31')],
))
runner.summary(results)  # 打印各区间夏普/索提诺/卡玛等指标对比表
```

---

## 📚 API文档

已实现46个回测/研究API，股票回测场景100%覆盖。

**核心API分类：**

| 类别 | 完成度 | 说明 |
|------|--------|------|
| 交易API | ✅ | order, order_target, order_value, order_target_value, cancel_order, get_positions, get_trades |
| 数据查询 | ✅ | get_price, get_history, get_fundamentals, get_stock_info |
| 板块信息 | ✅ | get_index_stocks, get_industry_stocks, get_stock_blocks |
| 技术指标 | ✅ | get_MACD, get_KDJ, get_RSI, get_CCI |
| 策略配置 | ✅ | set_benchmark, set_commission, set_slippage, set_universe, set_parameters, set_yesterday_position |
| 生命周期 | ✅ | initialize, before_trading_start, handle_data, after_trading_end |
| 融资融券 | — | 不在回测范围内（实盘交易API） |
| 期货/期权 | — | 不在回测范围内（实盘交易API） |

---

## 📄 许可证

本项目采用 **双许可证** 模式：

### 🆓 开源使用
- **GNU Affero General Public License v3.0 (AGPL-3.0)** - 查看 [LICENSE](LICENSE) | [中文说明](licenses/LICENSE.zh-CN)
- ✅ 免费用于开源项目
- ✅ 个人学习和研究
- ⚠️ 网络使用需开源（AGPL要求）

### 💼 商业使用
- **商业许可证** - 查看 [LICENSE-COMMERCIAL.md](licenses/LICENSE-COMMERCIAL.md) | [中文说明](licenses/LICENSE-COMMERCIAL.zh-CN.md)
- ✅ 用于商业/闭源产品
- ✅ 提供技术支持和定制服务
- 📧 联系: [kayou@duck.com](mailto:kayou@duck.com)

**何时需要商业许可：**
- 将SimTradeLab集成到商业产品/SaaS服务中
- 作为内部工具但不希望开源代码
- 需要技术支持和定制开发

---

## 🏗️ 项目结构

```
SimTradeLab/
├── src/simtradelab/
│   ├── ptrade/          # PTrade API模拟层（日/分钟线100%覆盖回测场景API）
│   ├── backtest/        # 回测引擎（统计、优化、配置）
│   ├── service/         # 核心服务（数据常驻）
│   └── utils/           # 工具模块（路径、性能、兼容检查）
├── strategies/          # 策略目录
├── data/               # 数据目录
└── docs/               # 文档
    ├── ARCHITECTURE.md                       # 架构设计文档
    ├── TOOLS.md                              # 工具脚本说明
    ├── IDE_SETUP.md                          # IDE配置指南
    └── CONTRIBUTING.md                       # 贡献指南
```

---

## 🔧 开发指南

### 添加新策略
1. 在 `strategies/` 创建新目录
2. 添加 `backtest.py` 文件，实现生命周期函数
3. 修改 `run_backtest.py` 的 `strategy_name`
4. 运行回测

### 扩展API
1. 在 `src/simtradelab/ptrade/api.py` 添加新方法
2. 在 `src/simtradelab/ptrade/lifecycle_config.py` 配置阶段限制
3. 更新文档

---

## 🚧 待改进与已知问题

### 主要限制
- ❌ 不支持实盘交易（仅回测）
- ⚠️ 测试覆盖不全面（策略驱动测试中）

### 计划改进
- 🔧 内存优化（支持小内存环境<8GB）
- 🔧 SimTradeData性能优化（数据获取速度慢）

**详细问题追踪：** [GitHub Issues](https://github.com/kay-ou/SimTradeLab/issues)

---

## 🐛 常见问题

**Q: 如何修改初始资金？**
```python
config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=2000000.0  # 修改这里
)
```

**Q: 如何使用分钟回测？**
```python
config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    frequency='1m'  # 设置为分钟回测
)
```
注意：分钟回测需要在 `data/stocks_1m/` 目录下准备分钟数据。

**Q: 回测太慢怎么办？**
- 减少股票数量或缩短回测时间
- 数据常驻已默认启用（二次运行秒级启动）

**Q: 如何查看更多日志？**
日志文件位于 `strategies/{strategy_name}/stats/*.log`

**Q: 数据从哪里获取？**
使用 [SimTradeData](https://github.com/kay-ou/SimTradeData) 项目获取A股历史数据

**Q: 数据加载异常或回测结果不正常？**
可能是缓存问题，尝试清理并重建：
```bash
cd data
rm -rf .keys_cache/
```

---

## 🤝 贡献指南

我们非常欢迎社区贡献！

**参与方式：**
- 🐛 [报告问题](https://github.com/kay-ou/SimTradeLab/issues)
- 💻 实现缺失的API功能
- 🔧 修复Bug和性能优化
- 📚 完善文档和示例
- 💡 分享策略和使用反馈

**贡献者许可协议（CLA）：**
- 您拥有提交代码的完整版权
- 您同意按照 AGPL-3.0 许可证发布
- 您同意项目维护者有权用于商业许可授权

**详细贡献指南：** [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## ⚖️ 免责声明

SimTradeLab 是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动设计理念，但并未包含 PTrade 的源代码、商标或任何受保护内容。该项目不隶属于 PTrade，也未获得其官方授权。

使用本框架构建或测试策略的用户应自行确保符合所在地区的法律法规、交易平台的使用条款及数据源的合规性。项目开发者不对任何由使用本项目所引发的直接或间接损失承担责任。

---

## 🙏 致谢

- 感谢PTrade提供的API设计灵感
- 感谢所有贡献者和用户反馈
- 感谢在实际策略开发中帮助发现和修复Bug的用户

**特别说明：** SimTradeLab是社区驱动的开源项目，我们在实际策略开发中不断完善功能。由于时间和资源有限，测试覆盖还不够全面，欢迎社区参与，共同发现和解决问题。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[🐛 报告问题](https://github.com/kay-ou/SimTradeLab/issues) | [💡 功能请求](https://github.com/kay-ou/SimTradeLab/issues) | [📚 完整文档](docs/)

---

## 💖 赞助支持

如果这个项目对您有帮助，欢迎赞助支持开发！

<img src="docs/sponsor/WechatPay.png?raw=true" alt="微信赞助" width="200">
<img src="docs/sponsor/AliPay.png?raw=true" alt="支付宝赞助" width="200">

**您的支持是我们持续改进的动力！**

</div>
