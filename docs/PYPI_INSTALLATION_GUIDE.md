# SimTradeLab 使用指南 - PyPI安装版

## 📦 安装

```bash
pip install simtradelab
```

## 🏗️ 创建工作目录

安装后需要创建工作目录来存放数据、策略和notebooks：

```bash
# 创建工作目录
mkdir -p ~/simtrade_workspace
cd ~/simtrade_workspace

# 创建子目录
mkdir -p data          # 数据文件
mkdir -p strategies    # 策略文件
mkdir -p notebooks     # Jupyter notebooks
```

最终目录结构：
```
~/simtrade_workspace/
├── data/
│   ├── ptrade_data.h5
│   └── ptrade_fundamentals.h5
├── strategies/
│   ├── my_strategy/
│   │   └── backtest.py
│   └── another_strategy/
│       └── backtest.py
└── notebooks/
    ├── research.ipynb
    └── analysis.ipynb
```

## 📊 准备数据

### 方式1: 使用SimTradeData项目

访问 [SimTradeData](https://github.com/kay-ou/SimTradeData) 下载数据，放到 `data/` 目录。

### 方式2: 使用自己的数据

确保数据文件是HDF5格式，包含以下内容：
- `ptrade_data.h5` - 价格和除权数据
- `ptrade_fundamentals.h5` - 基本面数据

## 📝 编写策略

创建策略文件 `strategies/my_strategy/backtest.py`：

```python
from simtradelab.ptrade.api import *

def initialize(context):
    """策略初始化"""
    set_benchmark('000300.SS')
    context.stocks = ['600519.SS', '000858.SZ']

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
    log.info("总资产: %.2f" % context.portfolio.portfolio_value)
```

## 🚀 运行回测

创建运行脚本 `run_backtest.py`：

```python
from simtradelab.backtest.runner import BacktestRunner
from pathlib import Path

# 配置路径
workspace = Path.home() / 'simtrade_workspace'
data_path = workspace / 'data'
strategies_path = workspace / 'strategies'

# 创建回测引擎
runner = BacktestRunner(
    data_path=str(data_path),
    strategies_path=str(strategies_path)
)

# 运行回测
runner.run(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=1000000.0
)

print("回测完成！")
print("报告位置:", strategies_path / 'my_strategy' / 'stats')
```

运行：
```bash
python run_backtest.py
```

## 📊 Research模式（Jupyter Notebook）

### 启动Jupyter

```bash
cd ~/simtrade_workspace/notebooks
jupyter notebook
```

### 在Notebook中使用

```python
# Cell 1: 导入和初始化
from simtradelab.research.api import init_api, get_price, get_history
from pathlib import Path
import pandas as pd

# 指定数据路径
data_path = Path.home() / 'simtrade_workspace' / 'data'
api = init_api(data_path=str(data_path))

print("✅ API初始化成功")
```

```python
# Cell 2: 获取历史价格
df = get_price(
    '600519.SS',
    start_date='2024-01-01',
    end_date='2024-12-31',
    fields=['open', 'high', 'low', 'close', 'volume']
)

print(f"数据形状: {df.shape}")
df.head()
```

```python
# Cell 3: 获取历史数据
hist = get_history(20, '600519.SS', 'close')
print(f"最近20日收盘价:")
print(hist)
```

```python
# Cell 4: 获取基本面数据
fundamentals = api.get_fundamentals(
    ['600519.SS'],
    'valuation',
    ['pe_ratio', 'pb_ratio'],
    '2024-01-01'
)
print(fundamentals)
```

## ⚙️ 高级配置

### 自定义数据路径

如果不想使用默认路径，可以在代码中指定：

```python
# 回测
from simtradelab.backtest.runner import BacktestRunner

runner = BacktestRunner(
    data_path='/path/to/your/data',
    strategies_path='/path/to/your/strategies'
)

# Research
from simtradelab.research.api import init_api

api = init_api(data_path='/path/to/your/data')
```

### 环境变量配置

也可以设置环境变量：

```bash
export SIMTRADE_DATA_PATH=~/simtrade_workspace/data
export SIMTRADE_STRATEGIES_PATH=~/simtrade_workspace/strategies
```

## 🐛 常见问题

### Q: ModuleNotFoundError: No module named 'tables'

安装系统依赖：

**macOS:**
```bash
brew install hdf5
export HDF5_DIR=$(brew --prefix hdf5)
pip install tables
```

**Linux:**
```bash
sudo apt-get install libhdf5-dev
pip install tables
```

### Q: 找不到数据文件

确保：
1. 数据文件路径正确
2. 文件名为 `ptrade_data.h5` 和 `ptrade_fundamentals.h5`
3. 在代码中正确指定了 `data_path`

```python
# 检查路径
from pathlib import Path
data_path = Path.home() / 'simtrade_workspace' / 'data'
print(f"数据路径: {data_path}")
print(f"文件存在: {data_path.exists()}")
print(f"包含文件: {list(data_path.glob('*.h5'))}")
```

### Q: 如何查看回测报告？

回测报告自动保存在策略目录的 `stats/` 子目录：

```bash
ls ~/simtrade_workspace/strategies/my_strategy/stats/

# 输出：
# backtest_240101_241231_*.log  - 详细日志
# backtest_240101_241231_*.png  - 可视化图表
```

### Q: 从哪里获取示例策略？

从GitHub下载：

```bash
cd ~/simtrade_workspace/strategies
git clone https://github.com/kay-ou/SimTradeLab.git temp
mv temp/strategies/* .
rm -rf temp
```

或访问 https://github.com/kay-ou/SimTradeLab/tree/main/strategies

## 📚 更多资源

- **完整文档**: https://github.com/kay-ou/SimTradeLab
- **API参考**: `docs/PTrade_API_Implementation_Status.md`
- **数据获取**: https://github.com/kay-ou/SimTradeData
- **问题反馈**: https://github.com/kay-ou/SimTradeLab/issues

## 🎯 快速开始示例

完整的端到端示例：

```bash
# 1. 安装
pip install simtradelab

# 2. 创建工作目录
mkdir -p ~/simtrade_workspace/{data,strategies/simple,notebooks}
cd ~/simtrade_workspace

# 3. 下载示例策略
cat > strategies/simple/backtest.py << 'EOF'
from simtradelab.ptrade.api import *

def initialize(context):
    set_benchmark('000300.SS')
    context.stocks = ['600519.SS']

def handle_data(context, data):
    for stock in context.stocks:
        if stock not in context.portfolio.positions:
            order_value(stock, 100000)
EOF

# 4. 创建运行脚本
cat > run.py << 'EOF'
from simtradelab.backtest.runner import BacktestRunner
from pathlib import Path

workspace = Path.home() / 'simtrade_workspace'
runner = BacktestRunner(
    data_path=str(workspace / 'data'),
    strategies_path=str(workspace / 'strategies')
)

runner.run(
    strategy_name='simple',
    start_date='2024-01-01',
    end_date='2024-12-31',
    initial_capital=1000000.0
)
EOF

# 5. 运行（需要先准备数据文件）
python run.py
```
