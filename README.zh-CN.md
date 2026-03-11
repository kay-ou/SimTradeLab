# 📈 SimTradeLab

[English](README.md) | 中文

**轻量级量化回测框架 - PTrade API本地实现**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![License: Commercial](https://img.shields.io/badge/License-Commercial--Available-red)](licenses/LICENSE-COMMERCIAL.md)
[![Version](https://img.shields.io/badge/Version-2.7.0-orange.svg)](#)
[![PyPI](https://img.shields.io/pypi/v/simtradelab.svg)](https://pypi.org/project/simtradelab/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/simtradelab.svg)](https://pypi.org/project/simtradelab/)

> 完整模拟PTrade平台API，策略可无缝迁移。详情参考：[ptradeAPI](https://github.com/kay-ou/ptradeAPI)

---

## 🎯 为什么选择 SimTradeLab？

| | SimTradeLab | PTrade |
|---|---|---|
| 速度 | **快100–160倍** | 基准 |
| 启动 | 亚秒级（数据常驻内存） | 分钟级 |
| API覆盖 | 46个回测/研究API | 全平台 |
| 策略迁移 | 零代码修改 | 零代码修改 |
| 运行环境 | 本地、免费、开源 | 云端、授权 |

**核心能力：**

- ✅ **46个API** — 股票日/分钟线回测场景100%覆盖
- ⚡ **100-160倍性能提升** — 本地回测比PTrade平台快100-160倍
- 🚀 **数据常驻内存** — 单例模式，首次加载后常驻，二次运行秒级启动
- 💾 **多级智能缓存** — LRU缓存（MA/VWAP/复权/历史数据），命中率>95%
- 🧠 **智能数据加载** — AST静态分析策略代码，按需加载数据，节省内存
- 🔧 **生命周期控制** — 7个生命周期阶段，严格模拟PTrade的API调用限制
- 📊 **完整统计报告** — 收益、风险（夏普/索提诺/卡玛）、交易明细、FIFO分红税、CSV导出
- 🔌 **T+0 / T+1 模式** — 可配置A股、ETF、美股交易限制

---

## 🚀 想要更强大的体验？试试 SimTradeDesk

> **[SimTradeDesk](https://github.com/kay-ou/SimTradeDesk)** 是基于 SimTradeLab 打造的专业桌面应用 — 无需编程。

| 功能 | SimTradeLab（本仓库） | SimTradeDesk |
|---|---|---|
| 目标用户 | 开发者 & 量化工程师 | 所有交易者 |
| 操作界面 | Python API | 桌面 GUI |
| 策略编辑 | 代码编辑器 | 内置语法高亮编辑器 |
| 可视化 | PNG 图表 | 交互式实时图表 |
| 数据管理 | 手动配置 | 一键下载与更新 |
| 参数调优 | 编写代码 | 可视化优化器 |

**[👉 获取 SimTradeDesk →](https://github.com/kay-ou/SimTradeDesk)**

---

## 📦 快速开始

```bash
pip install simtradelab

# 可选：技术指标（需要系统级 ta-lib）
pip install simtradelab[indicators]

# 可选：参数优化器
pip install simtradelab[optimizer]
```

**数据获取：** 使用 [SimTradeData](https://github.com/kay-ou/SimTradeData) 获取A股历史数据。

**运行回测：**

```python
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig

config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
)
runner = BacktestRunner()
report = runner.run(config=config)
```

---

## 📚 API 概览

46个回测/研究API — 股票回测场景100%覆盖。

| 类别 | API |
|------|-----|
| 交易 | order, order_target, order_value, order_target_value, cancel_order, get_positions, get_trades |
| 数据 | get_price, get_history, get_fundamentals, get_stock_info |
| 板块 | get_index_stocks, get_industry_stocks, get_stock_blocks |
| 指标 | get_MACD, get_KDJ, get_RSI, get_CCI |
| 配置 | set_benchmark, set_commission, set_slippage, set_universe, set_parameters |
| 生命周期 | initialize, before_trading_start, handle_data, after_trading_end |

---

## 📄 许可证

**双许可证** 模式：

- **AGPL-3.0** — 免费用于开源项目和个人研究。查看 [LICENSE](LICENSE) | [中文说明](licenses/LICENSE.zh-CN)
- **商业许可证** — 用于闭源/商业产品。查看 [LICENSE-COMMERCIAL.md](licenses/LICENSE-COMMERCIAL.md) | [中文说明](licenses/LICENSE-COMMERCIAL.zh-CN.md) 或联系 [kayou@duck.com](mailto:kayou@duck.com)

---

## 🤝 贡献

- 🐛 [报告问题](https://github.com/kay-ou/SimTradeLab/issues)
- 💻 实现缺失的API功能
- 📚 完善文档

详见 [CONTRIBUTING.md](docs/CONTRIBUTING.md)。

---

## ⚖️ 免责声明

SimTradeLab 是社区独立开发的开源回测框架，灵感来源于 PTrade 的事件驱动设计。不包含 PTrade 的源代码、商标或受保护内容，不隶属于 PTrade。用户需自行确保合规。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个星标！**

[🐛 报告问题](https://github.com/kay-ou/SimTradeLab/issues) | [💡 功能请求](https://github.com/kay-ou/SimTradeLab/issues) | [🖥️ SimTradeDesk](https://github.com/kay-ou/SimTradeDesk)

---

## 💖 赞助支持

如果这个项目对您有帮助，欢迎赞助支持开发！

<img src="docs/sponsor/WechatPay.png?raw=true" alt="微信赞助" width="200">
<img src="docs/sponsor/AliPay.png?raw=true" alt="支付宝赞助" width="200">

**您的支持是我们持续改进的动力！**

</div>
