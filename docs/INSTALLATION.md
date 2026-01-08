# 安装指南

本文档提供 SimTradeLab 的详细安装说明，包括系统依赖、多种安装方式和常见问题解决方案。

---

## 目录

- [快速安装（推荐）](#快速安装推荐)
- [源码安装（开发者）](#源码安装开发者)
- [系统依赖安装](#系统依赖安装)
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

# 安装指定版本
pip install simtradelab==2.0.0

# 包含优化器（可选）
pip install simtradelab[optimizer]
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

# 仅安装生产依赖
poetry install --no-dev

# 包含可选依赖（优化器）
poetry install -E optimizer
```

### 4. 激活虚拟环境

```bash
poetry shell
```

### 5. 验证安装

```bash
poetry run python -c "import simtradelab; print(simtradelab.__version__)"
```

---

## 系统依赖安装

SimTradeLab 依赖以下系统库：

### macOS

```bash
# 使用 Homebrew 安装
brew install hdf5 ta-lib

# 设置环境变量
export HDF5_DIR=$(brew --prefix hdf5)

# 添加到 ~/.zshrc 或 ~/.bash_profile 使其永久生效
echo 'export HDF5_DIR=$(brew --prefix hdf5)' >> ~/.zshrc
```

### Ubuntu/Debian

```bash
# 安装 HDF5
sudo apt-get update
sudo apt-get install libhdf5-dev

# 编译安装 TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 更新动态库缓存
sudo ldconfig
```

### CentOS/RHEL

```bash
# 安装 HDF5
sudo yum install hdf5-devel

# 编译安装 TA-Lib（同 Ubuntu）
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 更新动态库缓存
sudo ldconfig
```

### Windows

```bash
# 使用 Conda（推荐）
conda install -c conda-forge hdf5 ta-lib

# 或下载预编译包
# HDF5: https://www.hdfgroup.org/downloads/hdf5/
# TA-Lib: https://github.com/mrjbq7/ta-lib#windows
```

---

## 工作目录配置

### 1. 创建工作目录

```bash
# 创建工作目录
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
│   ├── ptrade_data.h5           # 股票价格、除权数据
│   └── ptrade_fundamentals.h5   # 基本面数据
├── strategies/
│   ├── my_strategy/
│   │   ├── backtest.py          # 策略代码
│   │   └── stats/               # 回测结果
│   └── another_strategy/
│       └── backtest.py
└── research/
    └── analysis.ipynb           # Jupyter notebooks
```

### 3. 下载示例策略（可选）

```bash
# 从 GitHub 获取示例文件
wget https://raw.githubusercontent.com/kay-ou/SimTradeLab/main/strategies/5mv/backtest.py -P strategies/5mv/
```

---

## 数据准备

### 方式 A: 使用 SimTradeData 项目

**推荐方式**，提供完整的A股历史数据。

```bash
# 访问 SimTradeData 项目获取数据
# https://github.com/kay-ou/SimTradeData

# 下载数据文件并放到 data/ 目录
cp path/to/ptrade_data.h5 ~/simtrade_workspace/data/
cp path/to/ptrade_fundamentals.h5 ~/simtrade_workspace/data/
```

⚠️ **注意：** SimTradeData 项目目前存在性能问题，数据获取速度较慢，后续会持续优化。

### 方式 B: 使用自己的数据

如果您有自己的数据源，需要转换为 HDF5 格式：

**数据格式要求：**
- 使用 HDF5 格式（pandas HDFStore）
- 日线数据（不支持分钟线）
- 必需字段：`open`, `high`, `low`, `close`, `volume`, `money`
- 索引：`pd.DatetimeIndex`

**数据结构示例：**

```python
import pandas as pd

# 股票价格数据结构
# /stock_data/{股票代码}
stock_df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...],
    'money': [...]
}, index=pd.DatetimeIndex([...]))

# 基本面数据结构
# /valuation/{股票代码}
valuation_df = pd.DataFrame({
    'pe_ttm': [...],
    'pb': [...],
    'ps_ttm': [...],
    ...
}, index=pd.DatetimeIndex([...]))
```

### 数据文件说明

**ptrade_data.h5** 包含：
- `/stock_data/{股票代码}` - 股票日线价格
- `/exrights/{股票代码}` - 除权除息信息
- `/stock_metadata` - 股票元数据（名称、上市日期、退市日期等）
- `/benchmark` - 基准指数数据（默认沪深300）
- `/trade_days` - 交易日历
- `/metadata` - 元数据（指数成分股、股票状态历史等）

**ptrade_fundamentals.h5** 包含：
- `/valuation/{股票代码}` - 估值数据（PE、PB、PS等）
- `/fundamentals/{股票代码}` - 财务数据（利润、成长、资产负债等）

---

## 常见问题

### Q1: 安装 tables 失败

**错误信息：**
```
error: command 'gcc' failed with exit status 1
```

**解决方案：**
```bash
# macOS
brew install hdf5
export HDF5_DIR=$(brew --prefix hdf5)
pip install tables

# Ubuntu/Debian
sudo apt-get install libhdf5-dev
pip install tables
```

### Q2: 安装 TA-Lib 失败

**错误信息：**
```
talib/_ta_lib.c:…: fatal error: ta-lib/ta_defs.h: No such file or directory
```

**解决方案：**
```bash
# macOS
brew install ta-lib

# Linux - 需要先编译安装 TA-Lib C库（见上方"系统依赖安装"）
```

### Q3: 导入 simtradelab 失败

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

### Q4: HDF5 版本不兼容

**错误信息：**
```
ValueError: The file 'ptrade_data.h5' was created with HDF5 version...
```

**解决方案：**
```bash
# 升级 HDF5 和相关库
pip install --upgrade tables h5py

# 如果仍有问题，可能需要重新生成数据文件
```

### Q5: 权限问题（Linux/macOS）

**错误信息：**
```
PermissionError: [Errno 13] Permission denied
```

**解决方案：**
```bash
# 确保数据目录有读写权限
chmod -R 755 ~/simtrade_workspace/data/

# 或使用 chown 修改所有者
sudo chown -R $USER:$USER ~/simtrade_workspace/
```

### Q6: Windows 路径问题

**错误信息：**
```
FileNotFoundError: [Errno 2] No such file or directory
```

**解决方案：**
```python
# 使用 pathlib.Path 或原始字符串
from pathlib import Path
data_path = Path.home() / 'simtrade_workspace' / 'data'

# 或使用原始字符串
data_path = r'C:\Users\YourName\simtrade_workspace\data'
```

### Q7: 数据加载异常或缓存问题

**症状：**
- 数据加载失败
- 回测结果异常
- 索引错误或数据不一致
- 复权计算错误

**解决方案：**
```bash
# 删除缓存文件并重建
cd ~/simtrade_workspace/data

# 1. 删除数据索引缓存
rm -rf .keys_cache/

# 2. 删除复权因子缓存
rm -f ptrade_adj_pre.h5

# 3. 删除分红缓存
rm -f ptrade_dividend_cache.h5

# 4. 重新运行回测（缓存会自动重建）
poetry run python -m simtradelab.backtest.run_backtest
```

**缓存文件说明：**
- `.keys_cache/` - HDF5索引缓存（加速数据访问）
- `ptrade_adj_pre.h5` - 前复权因子缓存（预计算）
- `ptrade_dividend_cache.h5` - 分红事件缓存（预计算）

**何时需要清理缓存：**
- 更新数据文件后
- 升级 SimTradeLab 版本后
- 出现数据不一致错误时
- 复权计算结果异常时

---

## 升级

### 从 PyPI 升级

```bash
# 升级到最新版本
pip install --upgrade simtradelab

# 升级到指定版本
pip install --upgrade simtradelab==2.0.0
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

- 📚 阅读 [快速开始](../README.md#快速开始)
- 💻 查看 [示例策略](../strategies/)
- 📖 浏览 [API文档](PTrade_API_Implementation_Status.md)
- 🔧 配置 [IDE开发环境](IDE_SETUP.md)
