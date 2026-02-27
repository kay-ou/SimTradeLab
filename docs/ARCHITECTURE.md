# 架构设计文档

本文档详细介绍 SimTradeLab 的核心架构设计、性能优化策略和技术实现细节。

---

## 目录

- [架构概览](#架构概览)
- [性能优化](#性能优化)
- [策略执行引擎](#策略执行引擎)
- [生命周期管理](#生命周期管理)
- [持仓管理与分红税](#持仓管理与分红税)
- [数据服务](#数据服务)
- [缓存系统](#缓存系统)

---

## 架构概览

SimTradeLab 采用模块化设计，主要分为以下几个核心模块：

```
┌─────────────────────────────────────────────────────────┐
│                    Strategy Code                         │
│              (用户策略: backtest.py)                     │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Strategy Engine    │  策略执行引擎
        │  - 生命周期管理     │  - 加载策略
        │  - API注入          │  - 调度执行
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │    PTrade API       │  API模拟层
        │  - 46个核心API      │  - 交易/查询/配置
        │  - 生命周期验证     │  - 数据访问
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │   Data Context      │  数据上下文
        │  - DataServer       │  - 数据常驻
        │  - LazyDataDict     │  - 延迟加载
        │  - 多级缓存        │  - LRU策略
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │   Parquet Storage   │  数据存储
        │  - 股票价格         │  - 5000+股票
        │  - 基本面数据       │  - 日线/分钟线
        └─────────────────────┘
```

### 核心模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| **回测编排器** | `backtest/runner.py` | 数据加载、环境初始化、报告生成 |
| **策略执行引擎** | `ptrade/strategy_engine.py` | 策略加载、生命周期执行、统计收集 |
| **API模拟层** | `ptrade/api.py` | 46个PTrade API实现 |
| **数据上下文** | `ptrade/data_context.py` | 数据结构封装 |
| **数据服务** | `service/data_server.py` | 单例数据常驻服务 |
| **生命周期控制器** | `ptrade/lifecycle_controller.py` | API调用阶段验证 |
| **订单处理器** | `ptrade/order_processor.py` | 订单创建、执行、验证 |
| **缓存管理器** | `ptrade/cache_manager.py` | 多级LRU缓存 |
| **统计收集器** | `backtest/backtest_stats.py` | 交易数据收集 |
| **统计分析** | `backtest/stats.py` | 收益/风险/基准指标计算（含夏普/索提诺/卡玛） |
| **批量回测** | `backtest/batch.py` | 多日期区间批量回测，数据只加载一次 |
| **CSV导出** | `backtest/export.py` | 每日统计和持仓快照导出为CSV |

---

## 性能优化

### 核心优化技术栈

**本地回测性能比PTrade平台提升100-160倍！**

#### 1. 数据常驻内存（单例模式）

**设计思想：**
- 使用单例模式，数据首次加载后常驻内存
- 后续回测直接使用缓存，无需重新加载
- 进程结束时自动释放资源（`atexit`）

**实现：**
```python
class DataServer:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if DataServer._initialized:
            print("使用已加载的数据（常驻内存）")
            return
        # 首次加载数据...
        DataServer._initialized = True
```

**效果：**
- 首次运行：约15秒（5392只股票）
- 后续运行：秒级启动

#### 2. 多级智能缓存系统

**缓存层级：**

| 缓存类型 | 实现 | 淘汰策略 | 容量 | 命中率 |
|---------|------|---------|------|--------|
| 全局MA/VWAP缓存 | `cachetools.LRUCache` | LRU | 1000项 | >95% |
| 前复权因子缓存 | Parquet持久化 | 永久 | 全量 | 100% |
| 分红事件缓存 | 内存计算 | 每次 | 全量 | 100% |
| 历史数据缓存 | `LazyDataDict` | LRU | 500项 | >90% |
| 基本面数据缓存 | `LazyDataDict` | LRU | 200项 | >85% |
| 日期索引缓存 | 内存字典 | 永久 | 全量 | 100% |

**缓存管理器实现：**
```python
class CacheManager:
    def __init__(self):
        self._namespaces = {
            'ma': LRUCache(maxsize=1000),
            'vwap': LRUCache(maxsize=1000),
            'history': LRUCache(maxsize=500),
            'fundamentals': LRUCache(maxsize=200),
        }

    def get_namespace(self, name):
        return self._namespaces.get(name, {})
```

#### 3. 前复权向量化优化

**优化前（逐日计算）：**
```python
# 每次调用 get_history 都要循环计算
for date_idx in df.index:
    adj_price = original_price * adj_a + adj_b
```

**优化后（向量化批量计算）：**
```python
# 一次性向量化计算所有日期
adj_prices = original_prices * adj_a_array + adj_b_array
```

**实现：**
- 预计算所有股票的复权因子，存储到 `ptrade_adj_pre.parquet`
- 使用 Parquet 格式持久化，高效读写
- 向量化计算，利用 numpy 的 SIMD 加速

**性能提升：**
- 复权计算速度提升 **100倍**
- 首次计算后持久化，后续无需重复计算

#### 4. 并行计算加速

**数据加载并行：**
```python
from joblib import Parallel, delayed

# 并行加载股票数据
results = Parallel(n_jobs=-1)(
    delayed(load_stock_data)(stock)
    for stock in stock_list
)
```

**复权计算并行：**
```python
# 并行计算复权因子
adj_factors = Parallel(n_jobs=-1)(
    delayed(calculate_adj_factor)(stock, exrights)
    for stock, exrights in stock_exrights_pairs
)
```

**效果：**
- 充分利用多核CPU
- 数据加载速度提升 **4-8倍**（取决于CPU核心数）

#### 5. 智能启动优化

**AST策略代码分析：**
```python
import ast

class StrategyDataAnalyzer(ast.NodeVisitor):
    def visit_Call(self, node):
        # 识别 API 调用
        if node.func.id == 'get_price':
            self.required_data.add('price')
        elif node.func.id == 'get_fundamentals':
            self.required_data.add('fundamentals')
        # ...
```

**按需加载数据：**
```python
# 只加载策略实际使用的数据集
required_data = analyze_strategy_code('backtest.py')
data_server = DataServer(required_data={'price', 'exrights'})
```

**效果：**
- 节省 **50-70%** 内存占用（不加载未使用的数据）
- 启动速度提升 **2-3倍**

#### 6. 性能监控

**@timer 装饰器：**
```python
from simtradelab.utils.perf import timer

@timer()
def get_history(count, frequency, field, stocks):
    # 函数实现...
    pass
```

**输出示例：**
```
[PERF] get_history: 0.0234s (23.4ms)
[PERF] get_fundamentals: 0.1056s (105.6ms)
```

**用途：**
- 精准定位性能瓶颈
- 验证优化效果
- 调试慢查询

---

## 策略执行引擎

### 核心功能

`StrategyExecutionEngine` 负责策略的完整生命周期管理：

```python
class StrategyExecutionEngine:
    def __init__(self, strategy_module, context, data_context, log):
        self.strategy_module = strategy_module
        self.context = context
        self.data_context = data_context
        self.log = log

        # 注册生命周期函数
        self.lifecycle_functions = {
            'initialize': getattr(strategy_module, 'initialize', None),
            'before_trading_start': getattr(strategy_module, 'before_trading_start', None),
            'handle_data': getattr(strategy_module, 'handle_data', None),
            'after_trading_end': getattr(strategy_module, 'after_trading_end', None),
        }
```

### 生命周期执行流程

```
┌─────────────────────────────────────────────────────────┐
│  1. initialize(context)                                  │
│     - 仅执行一次（全局初始化）                          │
│     - 配置API调用（set_benchmark/set_commission等）     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │  开始日期循环
                   │
        ┌──────────▼──────────┐
        │  2. before_trading_ │
        │     start(context)  │
        │  - 每日开盘前执行   │
        │  - 选股/调仓准备    │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  3. handle_data(    │
        │     context, data)  │
        │  - 每日收盘时执行   │
        │  - 主交易逻辑       │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │  4. after_trading_  │
        │     end(context)    │
        │  - 每日收盘后执行   │
        │  - 统计/日志        │
        └──────────┬──────────┘
                   │
                   │  继续下一交易日
                   │  或结束回测
                   ▼
```

### 错误处理

**策略函数隔离：**
```python
def _safe_call(self, func_name, *args):
    """安全调用策略函数，异常不中断回测"""
    func = self.lifecycle_functions.get(func_name)
    if func is None:
        return

    try:
        func(*args)
    except Exception as e:
        self.log.error(f"[{func_name}] 执行失败: {e}")
        traceback.print_exc()
        # 继续回测，不抛出异常
```

**优势：**
- 单个函数错误不影响回测继续进行
- 详细的错误日志便于调试
- 防止策略代码中断回测流程

---

## 生命周期管理

### 完整模拟PTrade的7阶段生命周期控制

SimTradeLab实现了与PTrade完全一致的生命周期管理，确保策略在本地和平台上行为一致。

### 生命周期阶段定义

| 阶段 | 执行时机 | 频率 | 允许的API |
|------|---------|------|----------|
| `initialize` | 策略启动 | 1次 | 配置API（set_benchmark/set_commission等） |
| `before_trading_start` | 每日开盘前 | 每日 | 查询API + 盘前专用API |
| `handle_data` | 每日收盘时 | 每日 | 查询API + 交易API |
| `after_trading_end` | 每日收盘后 | 每日 | 查询API + 盘后专用API |
| `tick_data` | Tick数据到达 | 高频 | 查询API + 交易API |
| `on_order_response` | 订单回报 | 事件触发 | 查询API |
| `on_trade_response` | 成交回报 | 事件触发 | 查询API |

### 技术实现机制

#### 1. 阶段转换验证

**状态机实现：**
```python
class LifecycleController:
    ALLOWED_TRANSITIONS = {
        None: ['initialize'],
        'initialize': ['before_trading_start', 'handle_data'],
        'before_trading_start': ['handle_data'],
        'handle_data': ['after_trading_end'],
        'after_trading_end': ['before_trading_start'],
    }

    def transition_to(self, new_phase):
        if new_phase not in self.ALLOWED_TRANSITIONS.get(self.current_phase, []):
            raise PTradeLifecycleError(
                f"Invalid transition: {self.current_phase} → {new_phase}"
            )
        self.current_phase = new_phase
```

**违规转换示例：**
```python
# ❌ 错误：跳过 before_trading_start 直接到 after_trading_end
initialize → after_trading_end  # 抛出异常

# ✅ 正确：按顺序转换
initialize → before_trading_start → handle_data → after_trading_end
```

#### 2. API调用限制（基于PTrade官方文档）

**配置文件：** `ptrade/lifecycle_config.py`

```python
API_LIFECYCLE_CONFIG = {
    'set_benchmark': {
        'allowed_phases': ['initialize'],
        'description': '设置策略基准',
    },
    'order': {
        'allowed_phases': ['handle_data', 'tick_data'],
        'description': '买卖指定数量的股票',
    },
    'get_price': {
        'allowed_phases': ['all'],
        'description': '获取历史行情数据',
    },
    # ... 46个API配置
}
```

**运行时校验：**
```python
@validate_lifecycle
def order(self, security, amount, limit_price=None):
    # 装饰器自动验证当前阶段是否允许调用
    # 如果不允许，抛出 PTradeLifecycleError
    pass
```

**错误示例：**
```python
def initialize(context):
    # ❌ 错误：initialize 阶段不能交易
    order('600519.SS', 100)
    # 抛出：API 'order' cannot be called in phase 'initialize'
    # Allowed phases: ['handle_data', 'tick_data']

    # ✅ 正确：initialize 只能配置
    set_benchmark('000300.SS')
```

#### 3. 调用历史追踪

**记录每次API调用：**
```python
class APICallRecord:
    def __init__(self, api_name, phase, timestamp, success):
        self.api_name = api_name
        self.phase = phase
        self.timestamp = timestamp
        self.success = success
```

**统计接口：**
```python
# 查看API调用统计
stats = lifecycle_controller.get_call_statistics()
# {
#   'order': {'count': 150, 'success_rate': 0.98},
#   'get_history': {'count': 500, 'success_rate': 1.0},
#   ...
# }

# 查看最近10次API调用
recent = lifecycle_controller.get_recent_calls(10)
```

**用途：**
- 调试策略逻辑
- 性能分析（高频调用API）
- 错误排查（失败的API调用）

#### 4. 线程安全

**使用RLock确保并发安全：**
```python
import threading

class LifecycleController:
    def __init__(self):
        self._lock = threading.RLock()
        self.current_phase = None

    def transition_to(self, new_phase):
        with self._lock:
            # 原子性状态转换
            self._validate_transition(new_phase)
            self.current_phase = new_phase
```

### 优势

- ✅ **100%兼容PTrade** - API限制配置源自PTrade官方文档
- ✅ **提前发现错误** - 本地回测时就能发现生命周期违规
- ✅ **线程安全** - 使用RLock确保多线程环境下状态一致性
- ✅ **详细错误提示** - 明确指出当前阶段和允许的阶段列表

---

## 持仓管理与分红税

### FIFO批次管理

**设计思想：**
- 每次买入创建独立持仓批次（`PositionBatch`）
- 记录买入价、时间、数量
- 卖出时按先进先出（FIFO）顺序扣减批次
- 自动跟踪每笔持仓的持有时长

**数据结构：**
```python
class PositionBatch:
    def __init__(self, amount, cost_basis, purchase_date):
        self.amount = amount              # 持仓数量
        self.cost_basis = cost_basis      # 买入价
        self.purchase_date = purchase_date  # 买入日期
        self.dividends = []               # 分红记录
```

**买入流程：**
```python
def buy(security, amount, price):
    batch = PositionBatch(
        amount=amount,
        cost_basis=price,
        purchase_date=context.current_dt
    )
    position.batches.append(batch)
```

**卖出流程（FIFO）：**
```python
def sell(security, amount, price):
    remaining = amount
    while remaining > 0 and position.batches:
        batch = position.batches[0]  # 最早买入的批次

        if batch.amount <= remaining:
            # 完全卖出该批次
            remaining -= batch.amount
            position.batches.pop(0)
        else:
            # 部分卖出该批次
            batch.amount -= remaining
            remaining = 0
```

### 分红税计算

**税率规则：**
| 持有时长 | 税率 |
|---------|------|
| ≤ 1个月 | 20% |
| > 1个月 ≤ 1年 | 10% |
| > 1年 | 0% (免税) |

**分红流程：**
```python
def process_dividend(security, dividend_per_share, ex_date):
    for batch in position.batches:
        # 记录分红到批次
        batch.dividends.append({
            'amount': batch.amount * dividend_per_share,
            'date': ex_date
        })
```

**卖出时计算税：**
```python
def calculate_dividend_tax(batch, sell_date):
    holding_days = (sell_date - batch.purchase_date).days

    # 确定税率
    if holding_days <= 30:
        tax_rate = 0.20
    elif holding_days <= 365:
        tax_rate = 0.10
    else:
        tax_rate = 0.0  # 免税

    # 计算总分红税
    total_dividend = sum(d['amount'] for d in batch.dividends)
    dividend_tax = total_dividend * tax_rate
    return dividend_tax
```

**实际案例：**
```python
# 2024-01-01: 买入 600519.SS 1000股，价格50元
# 2024-06-01: 分红 10元/股（持有5个月）
# 2024-07-01: 卖出 1000股，价格60元（持有6个月）

# 计算：
持有时长 = 6个月 (180天)
税率 = 10%  (> 1个月 ≤ 1年)
分红总额 = 1000股 * 10元/股 = 10000元
分红税 = 10000元 * 10% = 1000元
实际收益 = (60 - 50) * 1000 - 1000 = 9000元
```

**优势：**
- ✅ 完整模拟真实交易的税务成本
- ✅ 精确计算每笔持仓的持有时长
- ✅ 自动处理复杂的分批买卖场景
- ✅ 符合中国A股分红税规则

---

## 数据服务

### DataServer 单例模式

**设计目标：**
- 数据首次加载后常驻内存
- 多次运行策略无需重新加载
- 进程结束时自动释放资源

**实现：**
```python
class DataServer:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, required_data=None):
        if DataServer._initialized:
            print("使用已加载的数据（常驻内存）")
            return

        # 首次加载
        self._load_data(required_data)
        atexit.register(self._cleanup_on_exit)
        DataServer._initialized = True
```

### LazyDataDict 延迟加载

**设计思想：**
- 数据不预加载到内存
- 首次访问时从 Parquet 读取
- 使用LRU缓存管理内存
- 支持全量预加载模式

**实现：**
```python
class LazyDataDict:
    def __init__(self, store, prefix, keys, max_cache_size=None, preload=False):
        self._store = store
        self._prefix = prefix
        self._all_keys = keys
        self._cache = LRUCache(maxsize=max_cache_size) if max_cache_size else {}

        if preload:
            # 全量预加载（价格/估值数据）
            self._preload_all()

    def __getitem__(self, key):
        if key in self._cache:
            return self._cache[key]

        # 从 Parquet 加载
        data = self._store[f'{self._prefix}{key}']
        self._cache[key] = data
        return data
```

**使用场景：**
| 数据类型 | 加载策略 | 原因 |
|---------|---------|------|
| 价格数据 | 全量预加载 | 高频访问，内存占用可控 |
| 估值数据 | 全量预加载 | 高频访问，内存占用可控 |
| 财务数据 | 延迟加载 | 低频访问，数据量大 |
| 除权数据 | 延迟加载 | 低频访问，按需使用 |

---

## 缓存系统

### 缓存管理器

**统一缓存接口：**
```python
from simtradelab.ptrade.cache_manager import cache_manager

# 获取MA缓存命名空间
ma_cache = cache_manager.get_namespace('ma')

# 存储缓存
cache_key = ('600519.SS', 20, '2024-01-01')
ma_cache[cache_key] = 52.3

# 读取缓存
if cache_key in ma_cache:
    ma_value = ma_cache[cache_key]
```

### 缓存键设计

**历史数据缓存键：**
```python
cache_key = (
    tuple(sorted(stocks)),  # 股票列表（排序后）
    count,                  # 历史数据数量
    field,                  # 字段名
    fq,                     # 复权类型
    current_dt,             # 当前日期
    include,                # 是否包含当日
    is_dict                 # 返回格式
)
```

**基本面数据缓存键：**
```python
cache_key = (
    table,       # 表名（valuation/fundamentals）
    query_ts     # 查询日期
)
```

**优势：**
- ✅ 精确匹配查询条件
- ✅ 避免缓存污染
- ✅ 支持多种查询模式

### 缓存失效策略

**LRU 淘汰：**
- 按访问时间排序
- 达到容量上限时淘汰最久未使用项
- 自动管理内存占用

**手动清理：**
```python
# 清空所有缓存
cache_manager.clear_all()

# 清空特定命名空间
cache_manager.clear_namespace('ma')
```

---

## 下一步

- 📖 阅读 [API文档](PTrade_API_Implementation_Status.md)
- 🔧 查看 [工具脚本说明](TOOLS.md)
- 💻 参考 [开发规范](DEVELOPMENT_RULES.md)
- 🤝 贡献代码 [贡献指南](CONTRIBUTING.md)
