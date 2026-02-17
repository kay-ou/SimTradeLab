# SimTradeLab 使用指南 - PyPI安装版

## 安装

```bash
pip install simtradelab

# 可选：技术指标（需要系统级 ta-lib）
pip install simtradelab[indicators]

# 可选：参数优化器
pip install simtradelab[optimizer]
```

## 创建工作目录

安装后需要创建工作目录来存放数据、策略和 notebooks：

```bash
mkdir -p ~/simtrade_workspace
cd ~/simtrade_workspace

mkdir -p data          # 数据文件
mkdir -p strategies    # 策略文件
mkdir -p notebooks     # Jupyter notebooks
```

最终目录结构：
```
~/simtrade_workspace/
├── data/
│   ├── stocks/              # 股票日线（.parquet）
│   ├── stocks_1m/           # 分钟数据（.parquet）
│   ├── valuation/           # 估值数据
│   ├── fundamentals/        # 财务数据
│   ├── exrights/            # 除权数据
│   ├── metadata/            # 元数据
│   └── manifest.json        # 数据清单
├── strategies/
│   ├── my_strategy/
│   │   └── backtest.py
│   └── another_strategy/
│       └── backtest.py
└── notebooks/
    └── research.ipynb
```

## 准备数据

### 方式1: 使用 SimTradeData 项目

访问 [SimTradeData](https://github.com/kay-ou/SimTradeData) 下载数据，放到 `data/` 目录。

### 方式2: 使用自己的数据

确保数据为 Parquet 格式，按上述目录结构组织。每只股票一个 `.parquet` 文件，包含 `open`、`high`、`low`、`close`、`volume`、`money` 字段。

## 编写策略

创建策略文件 `strategies/my_strategy/backtest.py`：

```python
def initialize(context):
    """策略初始化"""
    set_benchmark('000300.SS')
    context.stocks = ['600519.SS', '000858.SZ']

def handle_data(context, data):
    """每日交易逻辑"""
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

def after_trading_end(context, data):
    """盘后处理"""
    log.info("总资产: %.2f" % context.portfolio.portfolio_value)
```

> **注意：** 策略代码中无需 import，所有 PTrade API（`set_benchmark`、`get_history`、`order_value` 等）由框架自动注入。Backtest 模式不支持 f-string 和 `import io/sys`。

## 运行回测

创建运行脚本 `run_backtest.py`：

```python
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig

config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=1000000.0,
    data_path='data',          # 数据目录路径
    strategies_path='strategies' # 策略目录路径
)

runner = BacktestRunner()
runner.run(config=config)
```

运行：
```bash
python run_backtest.py
```

## Research模式（Jupyter Notebook）

### 启动 Jupyter

```bash
cd ~/simtrade_workspace/notebooks
jupyter notebook
```

### 在 Notebook 中使用

```python
# Cell 1: 导入和初始化
from simtradelab.research.api import init_api, get_price, get_history

api = init_api(data_path='../data')
```

```python
# Cell 2: 获取历史价格
df = get_price(
    '600519.SS',
    start_date='2024-01-01',
    end_date='2024-12-31',
    fields=['open', 'high', 'low', 'close', 'volume']
)
df.head()
```

```python
# Cell 3: 获取指数成分股
stocks = api.get_index_stocks('000300.SS', date='2024-01-01')
```

## 常见问题

### Q: ModuleNotFoundError: No module named 'simtradelab'

确保虚拟环境已激活：
```bash
which python  # 应指向虚拟环境
pip install --upgrade simtradelab
```

### Q: 找不到数据文件

确保：
1. 数据文件路径正确
2. `data/` 目录下有 `stocks/`、`metadata/` 等子目录
3. BacktestConfig 中正确指定了 `data_path`

```python
from pathlib import Path
data_path = Path.home() / 'simtrade_workspace' / 'data'
print(f"数据路径: {data_path}")
print(f"存在: {data_path.exists()}")
print(f"子目录: {list(data_path.iterdir())}")
```

### Q: 如何查看回测报告？

回测报告自动保存在策略目录的 `stats/` 子目录：
```bash
ls ~/simtrade_workspace/strategies/my_strategy/stats/
# backtest_*.log  - 详细日志
# backtest_*.png  - 可视化图表
```

## 更多资源

- **完整文档**: https://github.com/kay-ou/SimTradeLab
- **API参考**: [docs/PTrade_API_Implementation_Status.md](PTrade_API_Implementation_Status.md)
- **数据获取**: https://github.com/kay-ou/SimTradeData
- **问题反馈**: https://github.com/kay-ou/SimTradeLab/issues
