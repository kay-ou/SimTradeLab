# 📈 SimTradeLab

English | [中文](README.zh-CN.md)

**Lightweight Quantitative Backtesting Framework — Local PTrade API Simulation**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![License: Commercial](https://img.shields.io/badge/License-Commercial--Available-red)](licenses/LICENSE-COMMERCIAL.md)
[![Version](https://img.shields.io/badge/Version-2.7.0-orange.svg)](#)
[![PyPI](https://img.shields.io/pypi/v/simtradelab.svg)](https://pypi.org/project/simtradelab/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/simtradelab.svg)](https://pypi.org/project/simtradelab/)

*Full PTrade API simulation — strategies transfer seamlessly between SimTradeLab and PTrade*

---

## 🎯 Overview

SimTradeLab is a community-driven, open-source strategy backtesting framework inspired by PTrade's event-driven architecture. It provides a lightweight, modular, and extensible environment for strategy validation — no PTrade dependency required. Strategies written in SimTradeLab can be deployed to PTrade with zero code changes, and vice versa. See also: [ptradeAPI](https://github.com/kay-ou/ptradeAPI).

**Key features:**
- ✅ **46 backtest/research APIs** — 100% coverage of stock backtesting scenarios (daily & minute bars)
- ⚡ **100–160x faster** than PTrade platform
- 🚀 **In-memory data persistence** — singleton pattern, sub-second startup after first load
- 💾 **Multi-level caching** — LRU caches for MA/VWAP/adjustment factors/history, >95% hit rate
- 🧠 **Smart data loading** — AST analysis of strategy code, loads only required data
- 🔧 **Lifecycle control** — 7 lifecycle phases, strict simulation of PTrade's API restrictions
- 📊 **Full stats reporting** — returns, risk metrics (Sharpe/Sortino/Calmar), trade details, FIFO dividend tax, CSV export
- 🔌 **T+0 / T+1 modes** — configurable trading restrictions for A-shares, ETFs, and US stocks

**Current version:** v2.7.0 | **Status:** Core features complete, continuously refined in live strategy development

---

## 🚀 Quick Start

### 📦 Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install latest version
pip install simtradelab

# With technical indicators (requires system-level ta-lib, optional)
pip install simtradelab[indicators]

# With optimizer (optional)
pip install simtradelab[optimizer]

# All optional dependencies
pip install simtradelab[all]
```

**System dependencies (only for technical indicator APIs):**
- macOS: `brew install ta-lib`
- Linux: build from source — see [ta-lib docs](https://github.com/ta-lib/ta-lib-python)
- Windows: download pre-built from [ta-lib releases](https://github.com/ta-lib/ta-lib-python)

### 📁 Prepare Data

Place data files in the `data/` directory:
```
data/
├── stocks/              # Daily stock data (parquet)
├── stocks_1m/           # Minute stock data (for minute backtesting)
├── valuation/           # Valuation data
├── fundamentals/        # Financial data
├── exrights/            # Ex-rights data
└── metadata/            # Metadata
```

**Data source:** Use [SimTradeData](https://github.com/kay-ou/SimTradeData) to download China A-share historical data.

### ✍️ Write a Strategy

Create `strategies/my_strategy/backtest.py`:

```python
def initialize(context):
    set_benchmark('000300.SS')
    context.stocks = ['600519.SS', '000858.SZ']

def handle_data(context, data):
    for stock in context.stocks:
        hist = get_history(20, '1d', 'close', [stock], is_dict=True)
        if stock not in hist:
            continue

        prices = hist[stock]
        ma5 = sum(prices[-5:]) / 5
        ma20 = sum(prices[-20:]) / 20

        if ma5 > ma20 and stock not in context.portfolio.positions:
            order_value(stock, context.portfolio.portfolio_value * 0.3)
        elif ma5 < ma20 and stock in context.portfolio.positions:
            order_target(stock, 0)
```

**Note:** Backtest mode strictly simulates PTrade restrictions:
- ❌ No f-strings (use `.format()` or `%`)
- ❌ No `io` / `sys` imports
- ✅ Automatic Python 3.5 compatibility check on startup

### ▶️ Run Backtest

```python
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig

config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=1000000.0,
    frequency='1d',             # '1d' daily (default), '1m' minute
    benchmark_code='000300.SS', # benchmark index (default: CSI 300)
    enable_charts=True,         # generate .png charts (default: True)
    enable_export=False,        # generate .csv stats (default: False)
    sandbox=True,               # PTrade compat mode (default: True)
    t_plus_1=True,              # T+1 restriction (default: True); set False for ETFs/US stocks
)

runner = BacktestRunner()
report = runner.run(config=config)
```

### 📊 Output

After backtesting, results are generated under the strategy directory:
```
strategies/my_strategy/stats/
├── backtest_*.log                     # Detailed log
├── backtest_*.png                     # 4-panel chart
├── daily_stats_*.csv                  # Daily portfolio stats (enable_export=True)
└── positions_history_*.csv            # Daily position snapshots (enable_export=True)
```

**Batch backtesting:**
```python
from simtradelab.backtest.batch import BatchBacktestRunner, BatchConfig

runner = BatchBacktestRunner()
results = runner.run(BatchConfig(
    strategy_name='my_strategy',
    date_ranges=[('2023-01-01', '2023-06-30'), ('2023-07-01', '2023-12-31')],
))
runner.summary(results)  # Print comparison table of Sharpe/Sortino/Calmar across periods
```

---

## 📚 API Reference

46 backtest/research APIs implemented — 100% stock backtesting coverage.

| Category | Status | APIs |
|----------|--------|------|
| Trading | ✅ | order, order_target, order_value, order_target_value, cancel_order, get_positions, get_trades |
| Data | ✅ | get_price, get_history, get_fundamentals, get_stock_info |
| Sector | ✅ | get_index_stocks, get_industry_stocks, get_stock_blocks |
| Indicators | ✅ | get_MACD, get_KDJ, get_RSI, get_CCI |
| Config | ✅ | set_benchmark, set_commission, set_slippage, set_universe, set_parameters, set_yesterday_position |
| Lifecycle | ✅ | initialize, before_trading_start, handle_data, after_trading_end |
| Margin trading | — | Not in backtest scope (live trading only) |
| Futures/Options | — | Not in backtest scope (live trading only) |

---

## 🏗️ Project Structure

```
SimTradeLab/
├── src/simtradelab/
│   ├── ptrade/          # PTrade API simulation layer
│   ├── backtest/        # Backtest engine (stats, optimizer, config)
│   ├── service/         # Core services (data persistence)
│   └── utils/           # Utilities (paths, perf, compat checks)
├── strategies/          # Strategy directory
├── data/                # Data directory
└── docs/                # Documentation
```

---

## 📄 License

This project uses a **dual license** model:

### 🆓 Open Source
- **GNU Affero General Public License v3.0 (AGPL-3.0)** — see [LICENSE](LICENSE)
- ✅ Free for open-source projects
- ✅ Personal learning and research
- ⚠️ Network use requires source disclosure (AGPL requirement)

### 💼 Commercial
- **Commercial License** — see [LICENSE-COMMERCIAL.md](licenses/LICENSE-COMMERCIAL.md)
- ✅ Use in commercial / closed-source products
- ✅ Technical support and customization
- 📧 Contact: [kayou@duck.com](mailto:kayou@duck.com)

---

## 🤝 Contributing

We welcome community contributions!

- 🐛 [Report issues](https://github.com/kay-ou/SimTradeLab/issues)
- 💻 Implement missing API features
- 🔧 Fix bugs and optimize performance
- 📚 Improve documentation and examples

**Contributor License Agreement (CLA):**
- You hold full copyright of your submitted code
- You agree to release under AGPL-3.0
- You agree the maintainer may use contributions under the commercial license

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

---

## ⚖️ Disclaimer

SimTradeLab is a community-developed, open-source backtesting framework inspired by PTrade's event-driven design. It does not contain PTrade's source code, trademarks, or any protected content. This project is not affiliated with or endorsed by PTrade.

Users are responsible for ensuring compliance with local regulations, trading platform terms, and data source agreements. The developers assume no liability for any losses arising from the use of this project.

---

## 💖 Sponsor

If this project helps you, consider sponsoring!

<div align="center">

**⭐ Star this project if you find it useful!**

[🐛 Report Issue](https://github.com/kay-ou/SimTradeLab/issues) | [💡 Feature Request](https://github.com/kay-ou/SimTradeLab/issues) | [📚 Documentation](docs/)

</div>
