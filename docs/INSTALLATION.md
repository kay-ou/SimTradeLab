# 安装指南

本文档提供 SimTradeLab 的详细安装说明，包括多种安装方式、数据准备和常见问题解决方案。

---

## 目录

- [快速安装（推荐）](#快速安装推荐)
- [源码安装（开发者）](#源码安装开发者)
- [系统依赖（可选）](#系统依赖可选)
- [工作目录配置](#工作目录配置)
- [数据准备](#数据准备)
- [常见问题](#常见问题)

---

## 快速安装（推荐）

适合普通用户，直接从 PyPI 安装。

### 1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 2. 安装 SimTradeLab

```bash
# 安装最新版本
pip install simtradelab

# 包含技术指标（需要系统级 ta-lib，可选）
pip install simtradelab[indicators]

# 包含优化器（可选）
pip install simtradelab[optimizer]

# 安装全部可选依赖
pip install simtradelab[all]
```

### 3. 验证安装

```python
python -c "import simtradelab; print(simtradelab.__version__)"
```

---

## 源码安装（开发者）

适合需要修改源码或参与开发的用户。

### 1. 克隆仓库

```bash
git clone https://github.com/kay-ou/SimTradeLab.git
cd SimTradeLab
```

### 2. 安装 Poetry

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Windows PowerShell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# 或使用 pip
pip install poetry
```

### 3. 安装依赖

```bash
# 安装所有依赖（包括开发依赖）
poetry install

# 包含可选依赖（技术指标）
poetry install -E indicators

# 包含可选依赖（优化器）
poetry install -E optimizer

# 包含全部可选依赖
poetry install -E all
```

### 4. 验证安装

```bash
poetry run python -c "import simtradelab; print(simtradelab.__version__)"
```

---

## 系统依赖（可选）

SimTradeLab 核心功能**无需任何系统级依赖**。仅在使用技术指标 API（`get_MACD`、`get_KDJ` 等）时需要安装 TA-Lib C 库。

### macOS

```bash
brew install ta-lib
pip install simtradelab[indicators]
```

### Ubuntu/Debian

```bash
# 编译安装 TA-Lib C库
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig

# 安装 Python 绑定
pip install simtradelab[indicators]
```

### CentOS/RHEL

```bash
sudo yum install gcc make
# 编译安装 TA-Lib（同 Ubuntu）
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig

pip install simtradelab[indicators]
```

### Windows

```bash
# 使用 Conda（推荐）
conda install -c conda-forge ta-lib

# 或从 https://github.com/ta-lib/ta-lib-python 下载预编译包
```

---

## 工作目录配置

### 1. 创建工作目录

```bash
mkdir -p ~/simtrade_workspace
cd ~/simtrade_workspace

# 创建必要的子目录
mkdir -p data          # 存放数据文件
mkdir -p strategies    # 存放策略文件
mkdir -p research      # 存放Jupyter notebooks
```

### 2. 目录结构

```
~/simtrade_workspace/
├── data/
│   ├── stocks/              # 股票日线数据（每只股票一个 .parquet 文件）
│   ├── stocks_1m/           # 股票分钟数据（分钟回测需要）
│   ├── valuation/           # 估值数据
│   ├── fundamentals/        # 财务数据
│   ├── exrights/            # 除权除息数据
│   ├── metadata/            # 元数据（指数成分、交易日历等）
│   └── manifest.json        # 数据清单文件
├── strategies/
│   ├── my_strategy/
│   │   ├── backtest.py      # 策略代码
│   │   └── stats/           # 回测结果
│   └── another_strategy/
│       └── backtest.py
└── research/
    └── analysis.ipynb       # Jupyter notebooks
```

---

## 数据准备

### 方式 A: 使用 SimTradeData 项目

**推荐方式**，提供完整的A股历史数据。

```bash
# 访问 SimTradeData 项目获取数据
# https://github.com/kay-ou/SimTradeData

# 下载数据文件并放到 data/ 目录
cp -r path/to/simtradedata/* ~/simtrade_workspace/data/
```

### 方式 B: 使用自己的数据

如果您有自己的数据源，需要转换为 Parquet 格式。

**数据格式要求：**
- 使用 Parquet 格式（每只股票一个文件）
- 日线数据或分钟线数据
- 必需字段：`open`, `high`, `low`, `close`, `volume`, `money`
- 索引：`pd.DatetimeIndex`

**数据结构示例：**

```python
import pandas as pd

# 股票价格数据
# 保存到 data/stocks/{股票代码}.parquet
stock_df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...],
    'money': [...]
}, index=pd.DatetimeIndex([...]))

stock_df.to_parquet('data/stocks/600519.SS.parquet')
```

### 数据目录说明

| 目录 | 内容 | 说明 |
|------|------|------|
| `stocks/` | 股票日线价格 | 每只股票一个 `.parquet` 文件 |
| `stocks_1m/` | 股票分钟价格 | 分钟回测需要 |
| `exrights/` | 除权除息信息 | 复权计算使用 |
| `valuation/` | 估值数据（PE、PB、PS等） | `get_fundamentals` 查询 |
| `fundamentals/` | 财务数据（利润、成长等） | `get_fundamentals` 查询 |
| `metadata/` | 元数据 | 指数成分股、交易日历、股票元信息等 |

---

## 常见问题

### Q1: 安装 TA-Lib 失败

**错误信息：**
```
talib/_ta_lib.c:…: fatal error: ta-lib/ta_defs.h: No such file or directory
```

**解决方案：**
```bash
# macOS
brew install ta-lib

# Linux - 需要先编译安装 TA-Lib C库（见上方"系统依赖"）
```

> 注意：如果不使用技术指标 API，无需安装 TA-Lib。

### Q2: 导入 simtradelab 失败

**错误信息：**
```
ModuleNotFoundError: No module named 'simtradelab'
```

**解决方案：**
```bash
# 检查虚拟环境是否激活
which python  # 应该指向虚拟环境

# 重新安装
pip install --upgrade simtradelab
```

### Q3: 权限问题（Linux/macOS）

**错误信息：**
```
PermissionError: [Errno 13] Permission denied
```

**解决方案：**
```bash
# 确保数据目录有读写权限
chmod -R 755 ~/simtrade_workspace/data/
```

### Q4: Windows 路径问题

**错误信息：**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**解决方案：**
```python
from pathlib import Path
data_path = Path.home() / 'simtrade_workspace' / 'data'
```

### Q5: 数据加载异常或缓存问题

**症状：**
- 数据加载失败
- 回测结果异常
- 复权计算错误

**解决方案：**
```bash
cd ~/simtrade_workspace/data

# 删除复权因子缓存
rm -f ptrade_adj_pre.parquet
rm -f ptrade_adj_post.parquet

# 重新运行回测（缓存会自动重建）
```

**缓存文件说明：**
- `ptrade_adj_pre.parquet` - 前复权因子缓存（预计算）
- `ptrade_adj_post.parquet` - 后复权因子缓存（预计算）

**何时需要清理缓存：**
- 更新数据文件后
- 升级 SimTradeLab 版本后
- 复权计算结果异常时

---

## 升级

### 从 PyPI 升级

```bash
pip install --upgrade simtradelab
```

### 从源码升级

```bash
cd SimTradeLab
git pull
poetry install
```

---

## 卸载

### PyPI 安装的卸载

```bash
pip uninstall simtradelab
```

### 源码安装的卸载

```bash
cd SimTradeLab
poetry env remove python
rm -rf .venv
```

---

## 下一步

- 阅读 [快速开始](../README.md#快速开始)
- 查看 [示例策略](../strategies/)
- 浏览 [API文档](PTrade_API_Implementation_Status.md)
- 配置 [IDE开发环境](IDE_SETUP.md)
