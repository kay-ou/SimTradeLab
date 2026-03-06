# 工具脚本说明

SimTradeLab 提供了一系列实用工具脚本，用于数据处理、参数优化、性能监控等任务。

---

## 目录

- [批量回测](#批量回测)
- [CSV导出](#csv导出)
- [参数优化框架](#参数优化框架)
- [性能监控工具](#性能监控工具)
- [策略分析工具](#策略分析工具)

---

## 批量回测

对同一策略跑多个日期区间，数据只加载一次，适合做分段归因分析。

```python
from simtradelab.backtest.batch import BatchBacktestRunner, BatchConfig

runner = BatchBacktestRunner()
results = runner.run(BatchConfig(
    strategy_name='my_strategy',
    date_ranges=[
        ('2022-01-01', '2022-12-31'),
        ('2023-01-01', '2023-12-31'),
        ('2024-01-01', '2024-12-31'),
    ],
    initial_capital=1000000.0,
    benchmark_code='000300.SS',
    enable_export=False,  # 每轮是否导出CSV
))

# 打印各区间核心指标对比表
df = runner.summary(results)
```

**输出示例：**
```
======================================================================
批量回测汇总
======================================================================
          区间   总收益率   年化收益  夏普比率 索提诺比率  卡玛比率   最大回撤    胜率
2022-01-01~... +12.34%  +13.21%    0.823     1.102    0.654  -18.45% 53.2%
2023-01-01~... +28.76%  +29.54%    1.245     1.876    1.123   -9.32% 57.8%
2024-01-01~... +15.43%  +16.02%    0.967     1.334    0.891  -12.67% 54.9%
======================================================================
```

---

## CSV导出

回测结束后自动导出两个 CSV 文件（Excel 兼容的 utf-8-sig 编码）。

**通过配置项开启：**
```python
config = BacktestConfig(
    strategy_name='my_strategy',
    start_date='2024-01-01',
    end_date='2024-12-31',
    enable_export=True,  # 回测结束自动导出
)
```

**或手动调用：**
```python
from simtradelab.backtest.export import export_to_csv

paths = export_to_csv(report, 'strategies/my_strategy/stats')
# paths = {
#   'daily_stats': 'strategies/.../daily_stats_20240101_20241231.csv',
#   'positions':   'strategies/.../positions_history_20240101_20241231.csv',
# }
```

**输出文件说明：**

`daily_stats_{start}_{end}.csv` — 每日汇总：
| date | portfolio_value | daily_pnl | buy_amount | sell_amount | positions_value |

`positions_history_{start}_{end}.csv` — 每日持仓快照：
| date | stock_code | name | amount | market_value | cost_basis |

---

## 参数优化框架

SimTradeLab 提供基于 Optuna 的智能参数优化框架，支持贝叶斯优化和自动剪枝。

### 功能特性

- ✅ **贝叶斯采样** - TPE算法智能搜索参数空间
- ✅ **自动剪枝** - Hyperband剪枝器提前终止无效trial
- ✅ **断点续传** - 支持中断后继续优化
- ✅ **早停机制** - 可配置的early stopping
- ✅ **数据共享** - 复用BacktestRunner实例减少内存占用
- ✅ **进度追踪** - 实时显示优化进度和最优结果

### 快速开始

#### 1. 安装依赖

```bash
# PyPI安装
pip install simtradelab[optimizer]

# Poetry安装
poetry install -E optimizer
```

#### 2. 编写优化脚本

创建 `strategies/my_strategy/optimization/optimize_params.py`：

```python
from simtradelab.backtest.optimizer_framework import StrategyOptimizer

# 创建优化器
optimizer = StrategyOptimizer(
    strategy_path='strategies/my_strategy',
    data_path='data',
    start_date='2020-01-01',
    end_date='2024-12-31'
)

# 定义参数空间
def objective(trial):
    # 定义要优化的参数
    max_position = trial.suggest_int('max_position', 5, 30)
    rotation_period = trial.suggest_int('rotation_period', 10, 60)
    stop_loss = trial.suggest_float('stop_loss', 0.05, 0.20)

    # 运行回测并返回目标值（年化收益率）
    return optimizer.evaluate(trial, max_position, rotation_period, stop_loss)

# 运行优化（200次trial）
best_params = optimizer.optimize(objective, n_trials=200)

print(f"最优参数: {best_params}")
```

#### 3. 运行优化

```bash
poetry run python strategies/my_strategy/optimization/optimize_params.py
```

### 参数类型

Optuna 支持多种参数类型：

```python
def objective(trial):
    # 整数参数
    max_position = trial.suggest_int('max_position', 5, 30)

    # 浮点数参数
    stop_loss = trial.suggest_float('stop_loss', 0.05, 0.20)

    # 分类参数
    ma_type = trial.suggest_categorical('ma_type', ['SMA', 'EMA', 'WMA'])

    # 对数尺度参数（适合学习率等）
    learning_rate = trial.suggest_float('lr', 1e-5, 1e-1, log=True)

    # 离散参数（指定步长）
    window = trial.suggest_int('window', 10, 100, step=5)
```

### 高级配置

#### 自定义优化目标

```python
def objective(trial):
    # ... 参数定义 ...

    # 运行回测
    stats = optimizer.run_backtest_with_params(
        max_position=max_position,
        rotation_period=rotation_period
    )

    # 自定义目标函数（使用卡玛比率：年化收益/最大回撤）
    annual_return = stats['annual_return']
    max_drawdown = stats['max_drawdown']
    sharpe_ratio = stats['sharpe_ratio']
    sortino_ratio = stats['sortino_ratio']
    calmar_ratio = stats['calmar_ratio']

    # 示例：最大化索提诺比率（更关注下行风险控制）
    return sortino_ratio
```

#### 早停机制

```python
# 配置早停：连续20次trial无改进则停止
best_params = optimizer.optimize(
    objective,
    n_trials=200,
    early_stopping_rounds=20
)
```

#### 断点续传

```python
# 使用SQLite存储优化历史
import optuna

study = optuna.create_study(
    study_name='my_strategy_optimization',
    storage='sqlite:///optimization.db',
    load_if_exists=True,  # 断点续传
    direction='maximize'
)

study.optimize(objective, n_trials=200)
```

#### 并行优化

```python
# 使用多进程并行优化
study.optimize(objective, n_trials=200, n_jobs=4)
```

### 可视化结果

```python
import optuna

# 加载优化历史
study = optuna.load_study(
    study_name='my_strategy_optimization',
    storage='sqlite:///optimization.db'
)

# 可视化优化历史
optuna.visualization.plot_optimization_history(study).show()

# 参数重要性分析
optuna.visualization.plot_param_importances(study).show()

# 参数关系图
optuna.visualization.plot_parallel_coordinate(study).show()

# 切片图
optuna.visualization.plot_slice(study).show()
```

### 实战案例：5mv策略优化

完整示例见 `strategies/5mv/optimization/optimize_params.py`：

```python
from simtradelab.backtest.optimizer_framework import StrategyOptimizer

optimizer = StrategyOptimizer(
    strategy_path='strategies/5mv',
    data_path='data',
    start_date='2020-01-01',
    end_date='2024-12-31'
)

def objective(trial):
    # 定义参数空间
    max_position = trial.suggest_int('max_position', 5, 30)
    rotation_period = trial.suggest_int('rotation_period', 10, 60)
    min_market_cap = trial.suggest_float('min_market_cap', 50, 200)  # 亿
    filter_st = trial.suggest_categorical('filter_st', [True, False])

    # 运行回测
    return optimizer.evaluate(
        trial,
        max_position=max_position,
        rotation_period=rotation_period,
        min_market_cap=min_market_cap,
        filter_st=filter_st
    )

# 运行优化
best_params = optimizer.optimize(objective, n_trials=200)

print(f"""
最优参数：
- 最大持仓数: {best_params['max_position']}
- 轮动周期: {best_params['rotation_period']}天
- 最小市值: {best_params['min_market_cap']}亿
- 过滤ST: {best_params['filter_st']}
""")
```

---

## 性能监控工具

### @timer 装饰器

精准测量函数执行时间，定位性能瓶颈。

#### 基础用法

```python
from simtradelab.utils.perf import timer

@timer()
def slow_function():
    # 函数实现...
    pass

# 调用时自动打印执行时间
slow_function()
# 输出: [PERF] slow_function: 0.1234s (123.4ms)
```

#### 高级用法

**自定义名称：**
```python
@timer(name='数据加载')
def load_data():
    pass

# 输出: 数据加载: 2.35秒
```

**条件记录：**
```python
@timer(threshold=0.1)  # 只记录超过100ms的调用
def maybe_slow_function():
    pass
```

**实际示例：**
```python
from simtradelab.utils.perf import timer

@timer(threshold=0.5, name='加载股票数据')
def load_stock_data(count):
    # 函数实现...
    pass

# 只有当函数执行超过0.5秒时才会输出
load_stock_data(5000)
# 输出: 加载股票数据: 1.23秒
```

---

## 策略分析工具

### 策略代码静态分析

自动分析策略代码，识别使用的API和需要的数据。

#### 用法

```python
from simtradelab.ptrade.strategy_data_analyzer import StrategyDataAnalyzer

# 分析策略文件
analyzer = StrategyDataAnalyzer('strategies/my_strategy/backtest.py')
required_data = analyzer.analyze()

print(f"需要的数据集: {required_data}")
# 输出: {'price', 'exrights', 'valuation'}

print(f"使用的API: {analyzer.api_calls}")
# 输出: ['get_history', 'get_fundamentals', 'order_value']
```

#### 应用场景

**按需加载数据：**
```python
# 只加载策略实际使用的数据
from simtradelab.service.data_server import DataServer

required_data = StrategyDataAnalyzer('backtest.py').analyze()
data_server = DataServer(required_data=required_data)
```

**兼容性检查：**
```python
# 检查是否使用了PTrade不支持的语法
from simtradelab.utils.py35_compat_checker import check_strategy_compatibility

issues = check_strategy_compatibility('strategies/my_strategy/backtest.py')

if issues:
    print("发现兼容性问题:")
    for issue in issues:
        print(f"  - {issue}")
```

### Python 3.5 兼容性检查

自动检查策略代码是否使用了PTrade不支持的语法。

#### 检查项目

- ❌ f-string（f"..."）
- ❌ 变量类型注解（x: int = 1）
- ❌ 海象运算符（:=）
- ❌ 禁用模块导入（io、sys等）
- ❌ async/await语法

#### 用法

```python
from simtradelab.utils.py35_compat_checker import Py35CompatChecker

# 检查策略文件
checker = Py35CompatChecker('strategies/my_strategy/backtest.py')
issues = checker.check()

if issues:
    print("发现兼容性问题:")
    for issue in issues:
        print(f"  行{issue.line}: {issue.message}")
        print(f"     {issue.code}")
```

#### 自动修复

```python
from simtradelab.utils.fstring_fixer import FStringFixer

# 自动修复f-string
fixer = FStringFixer('strategies/my_strategy/backtest.py')
fixer.fix_and_save()
```

---

## Ptrade API 类型声明

### setup_typeshed.sh

在 pyright/Pylance 的 typeshed 中注入 Ptrade API 类型声明，使 VS Code 能识别策略代码中的全局函数（如 `order`、`get_history`、`context` 等）。

#### 用法

```bash
bash scripts/setup_typeshed.sh
```

#### 说明

- 脚本幂等，重复运行会自动跳过
- pyright 更新后需重新运行
- 仅修改 `.venv` 内的 typeshed，不影响项目代码

---

## 工具脚本列表

| 脚本 | 功能 | 路径 |
|------|------|------|
| 批量回测 | 多日期区间批量回测，数据只加载一次 | `backtest/batch.py` |
| CSV导出 | 每日统计和持仓快照导出为CSV | `backtest/export.py` |
| 参数优化框架 | 基于Optuna的参数优化 | `backtest/optimizer_framework.py` |
| 性能监控 | 函数执行时间/内存监控 | `utils/perf.py` |
| 策略分析 | 静态分析策略代码 | `ptrade/strategy_data_analyzer.py` |
| 兼容性检查 | Python 3.5兼容性检查 | `utils/py35_compat_checker.py` |
| f-string修复 | 自动修复f-string语法 | `utils/fstring_fixer.py` |
| 类型声明注入 | 让Pylance识别Ptrade API全局函数 | `scripts/setup_typeshed.sh` |

---

## 下一步

- 📖 阅读 [架构设计文档](ARCHITECTURE.md)
- 🔧 配置 [IDE开发环境](IDE_SETUP.md)
- 🤝 贡献代码 [贡献指南](CONTRIBUTING.md)
