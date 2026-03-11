# 📈 SimTradeLab

English | [中文](README.zh-CN.md)

**Lightweight Quantitative Backtesting Framework — Local PTrade API Simulation**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![License: Commercial](https://img.shields.io/badge/License-Commercial--Available-red)](licenses/LICENSE-COMMERCIAL.md)
[![Version](https://img.shields.io/badge/Version-2.7.0-orange.svg)](#)
[![PyPI](https://img.shields.io/pypi/v/simtradelab.svg)](https://pypi.org/project/simtradelab/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/simtradelab.svg)](https://pypi.org/project/simtradelab/)

> Full PTrade API simulation — strategies transfer seamlessly between SimTradeLab and PTrade. See also: [ptradeAPI](https://github.com/kay-ou/ptradeAPI)

---

## 🎯 Why SimTradeLab?

| | SimTradeLab | PTrade |
|---|---|---|
| Speed | **100–160x faster** | Baseline |
| Startup | Sub-second (data persists in memory) | Minutes |
| API Coverage | 46 backtest/research APIs | Full platform |
| Strategy Porting | Zero code changes | Zero code changes |
| Environment | Local, free, open-source | Cloud, licensed |

**Core capabilities:**

- ✅ **46 APIs** — 100% coverage of stock backtesting scenarios (daily & minute bars)
- ⚡ **100–160x faster** than PTrade platform
- 🚀 **In-memory data persistence** — singleton pattern, sub-second startup after first load
- 💾 **Multi-level caching** — LRU caches for MA/VWAP/adjustment factors/history, >95% hit rate
- 🧠 **Smart data loading** — AST analysis of strategy code, loads only required data
- 🔧 **Lifecycle control** — 7 lifecycle phases, strict simulation of PTrade's API restrictions
- 📊 **Full stats reporting** — returns, risk metrics (Sharpe/Sortino/Calmar), trade details, FIFO dividend tax, CSV export
- 🔌 **T+0 / T+1 modes** — configurable trading restrictions for A-shares, ETFs, and US stocks

---

## 🚀 Need More? Try SimTradeDesk

> **[SimTradeDesk](https://github.com/kay-ou/SimTradeDesk)** is a professional desktop application built on SimTradeLab — no coding required.

| Feature | SimTradeLab (this repo) | SimTradeDesk |
|---|---|---|
| Target users | Developers & quant engineers | All traders |
| Interface | Python API | Desktop GUI |
| Strategy editing | Code editor | Built-in editor with syntax highlighting |
| Visualization | PNG charts | Interactive real-time charts |
| Data management | Manual setup | One-click download & update |
| Parameter tuning | Write code | Visual optimizer |

**[👉 Get SimTradeDesk →](https://github.com/kay-ou/SimTradeDesk)**

---

## 📦 Quick Start

```bash
pip install simtradelab

# Optional: technical indicators (requires system ta-lib)
pip install simtradelab[indicators]

# Optional: parameter optimizer
pip install simtradelab[optimizer]
```

**Data:** Use [SimTradeData](https://github.com/kay-ou/SimTradeData) to download China A-share historical data.

**Run a backtest:**

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

## 📚 API Overview

46 backtest/research APIs — 100% stock backtesting coverage.

| Category | APIs |
|----------|------|
| Trading | order, order_target, order_value, order_target_value, cancel_order, get_positions, get_trades |
| Data | get_price, get_history, get_fundamentals, get_stock_info |
| Sector | get_index_stocks, get_industry_stocks, get_stock_blocks |
| Indicators | get_MACD, get_KDJ, get_RSI, get_CCI |
| Config | set_benchmark, set_commission, set_slippage, set_universe, set_parameters |
| Lifecycle | initialize, before_trading_start, handle_data, after_trading_end |

---

## 📄 License

**Dual license** model:

- **AGPL-3.0** — Free for open-source projects and personal research. See [LICENSE](LICENSE)
- **Commercial License** — For closed-source / commercial use. See [LICENSE-COMMERCIAL.md](licenses/LICENSE-COMMERCIAL.md) or contact [kayou@duck.com](mailto:kayou@duck.com)

---

## 🤝 Contributing

- 🐛 [Report issues](https://github.com/kay-ou/SimTradeLab/issues)
- 💻 Implement missing API features
- 📚 Improve documentation

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for CLA details.

---

## ⚖️ Disclaimer

SimTradeLab is a community-developed, open-source backtesting framework inspired by PTrade's event-driven design. It does not contain PTrade's source code, trademarks, or any protected content. This project is not affiliated with or endorsed by PTrade. Users are responsible for compliance with local regulations and platform terms.

---

<div align="center">

**⭐ Star this project if you find it useful!**

[🐛 Report Issue](https://github.com/kay-ou/SimTradeLab/issues) | [💡 Feature Request](https://github.com/kay-ou/SimTradeLab/issues) | [🖥️ SimTradeDesk](https://github.com/kay-ou/SimTradeDesk)

---

## 💖 Sponsor

If this project helps you, consider sponsoring!

<img src="docs/sponsor/WechatPay.png?raw=true" alt="WeChat Pay" width="200">
<img src="docs/sponsor/AliPay.png?raw=true" alt="Alipay" width="200">

</div>
