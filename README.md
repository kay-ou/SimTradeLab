# 📈 SimTradeLab 深测Lab

<div align="center">

**开源策略回测框架**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#测试)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)](#版本历程)

*灵感来自PTrade的事件驱动模型，提供轻量、清晰、可插拔的策略验证环境*

</div>

## 🎯 项目简介

SimTradeLab（深测Lab） 是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动架构。它具备完全自主的实现与出色的扩展能力，为策略开发者提供一个轻量级、结构清晰、模块可插拔的策略验证环境。框架无需依赖 PTrade 即可独立运行，但与其语法保持高度兼容。所有在 SimTradeLab 中编写的策略可无缝迁移至 PTrade 平台，反之亦然，两者之间的 API 可直接互通使用。详情参考：https://github.com/kay-ou/ptradeAPI 项目。

### ✨ 核心特性

- 🔧 **事件驱动引擎**: 完整的回测引擎实现
- 📊 **多格式报告**: TXT、JSON、CSV、HTML、摘要、图表等6种格式
- 🌐 **真实数据源**: 支持AkShare、Tushare等主流数据源
- ⚡ **智能CLI**: 集成的 `simtradelab` 命令行工具
- ✅ **PTrade兼容**: 保持与PTrade语法习惯的兼容性
- 📈 **可视化报告**: HTML交互式报告和matplotlib图表

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

## ⚡ 命令行工具

### 基本用法
```bash
# 查看帮助
simtradelab --help

# CSV数据源
simtradelab --strategy strategies/test_strategy.py --data data/sample_data.csv

# 真实数据源
simtradelab --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ,000002.SZ
```

### 主要参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `--strategy` | 策略文件路径 | `strategies/test_strategy.py` |
| `--data` | CSV数据文件 | `data/sample_data.csv` |
| `--data-source` | 真实数据源 | `akshare`, `tushare` |
| `--securities` | 股票代码 | `000001.SZ,000002.SZ` |
| `--start-date` | 开始日期 | `2023-01-01` |
| `--end-date` | 结束日期 | `2023-12-31` |
| `--cash` | 初始资金 | `1000000` |

## 🌐 数据源配置

### AkShare（免费）
```bash
# 无需配置，直接使用
simtradelab --strategy strategies/real_data_strategy.py --data-source akshare --securities 000001.SZ
```

### Tushare（需要token）
```yaml
# simtrade_config.yaml
data_sources:
  tushare:
    enabled: true
    token: "your_tushare_token_here"
```

## 📊 报告系统

每次运行后自动生成多种格式的报告：

- 📝 **详细文本报告** (`.txt`) - 完整策略分析
- 📊 **结构化数据** (`.json`) - 程序化分析
- 📈 **数据表格** (`.csv`) - Excel分析
- 🌐 **交互式网页** (`.html`) - 现代化展示
- 📋 **智能摘要** (`.summary.txt`) - 快速概览
- 📊 **可视化图表** (`.png`) - 直观展示

报告自动按策略分类存储在 `reports/{strategy_name}/` 目录下。

## 🎓 策略开发

### 基本策略结构
```python
def initialize(context):
    """策略初始化"""
    log.info("策略初始化")
    g.stock = '000001.SZ'

def handle_data(context, data):
    """每日数据处理"""
    current_price = data.current(g.stock, 'close')
    
    # 买入逻辑
    if context.portfolio.positions[g.stock].amount == 0:
        order_target_percent(g.stock, 0.8)
        log.info(f"买入 {g.stock}")

def after_trading_end(context, data):
    """交易结束后处理"""
    total_value = context.portfolio.total_value
    log.info(f"总资产: ¥{total_value:,.2f}")
```

### 可用API
- **交易接口**: `order`, `order_target`, `order_target_percent`
- **数据接口**: `data.current()`, `get_history()`
- **查询接口**: `context.portfolio`, `context.current_dt`
- **工具函数**: `log.info()`, `set_commission()`

## 🧪 测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/unit/

# 生成覆盖率报告
poetry run pytest --cov=simtradelab --cov-report=html
```

## 📦 作为包使用

### 安装
```bash
pip install simtradelab
```

### 使用
```python
from simtradelab import BacktestEngine
from simtradelab.data_sources import AkshareDataSource

# 创建引擎
engine = BacktestEngine(
    strategy_file='my_strategy.py',
    data_source=AkshareDataSource(),
    securities=['000001.SZ'],
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=1000000.0
)

# 运行回测
files = engine.run()
```

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ⚖️ 法律免责声明

SimTradeLab 是一个由社区独立开发的开源策略回测框架，灵感来源于 PTrade 的事件驱动设计理念，但并未包含 PTrade 的源代码、商标或任何受保护内容。该项目不隶属于 PTrade，也未获得其官方授权。SimTradeLab 的所有实现均为自主构建，仅用于教学研究、策略验证和非商业性用途。

使用本框架构建或测试策略的用户应自行确保符合所在地区的法律法规、交易平台的使用条款及数据源的合规性。项目开发者不对任何由使用本项目所引发的直接或间接损失承担责任。

## 🙏 致谢

- 感谢 PTrade 提供的设计灵感
- 感谢 AkShare 和 Tushare 提供的数据源支持
- 感谢所有贡献者和用户的支持

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[📖 文档](docs/) | [🐛 报告问题](https://github.com/kay-ou/SimTradeLab/issues) | [💡 功能请求](https://github.com/kay-ou/SimTradeLab/issues)

</div>

---

<div align="center">

## 💖 赞助支持

如果这个项目对您有帮助，欢迎赞助支持开发！

<img src="https://github.com/kay-ou/SimTradeLab/blob/main/sponsor/WechatPay.png?raw=true" alt="微信赞助" width="200">
<img src="https://github.com/kay-ou/SimTradeLab/blob/main/sponsor/AliPay.png?raw=true" alt="支付宝赞助" width="200">

**您的支持是我们持续改进的动力！**

</div>
