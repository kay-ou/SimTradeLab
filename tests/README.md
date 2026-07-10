# SimTradeLab 测试指南

## 🎯 当前状态

✅ **单元测试与集成测试均由 CI 执行**
📊 **覆盖率由完整 `tests/` 测试集生成**
🛡️ **严格遵循PTrade API文档**
⭐ **仅测试文档公开API**
🎯 **聚焦核心兼容性保护**

---

## 📚 目录

- [快速开始](#快速开始)
- [测试文件结构](#测试文件结构)
- [测试范围](#测试范围)
- [代码覆盖率](#代码覆盖率)
- [测试设计原则](#测试设计原则)
- [关键保护](#关键保护)
- [添加新测试](#添加新测试)
- [持续集成](#持续集成)
- [下一步改进](#下一步改进)

---

## 🚀 快速开始

### 安装依赖

```bash
poetry install
```

### 运行测试

```bash
# 单元测试
poetry run pytest tests/unit -q

# 集成测试
poetry run pytest tests/integration -q

# 完整测试集
poetry run pytest tests -q

# 带覆盖率
poetry run pytest tests --cov=simtradelab --cov-report=term-missing

# HTML覆盖率报告
poetry run pytest tests --cov=simtradelab --cov-report=html
# Linux: xdg-open htmlcov/index.html
# macOS: open htmlcov/index.html
# Windows: start htmlcov/index.html
```

### 运行特定测试

```bash
# 单个文件
poetry run pytest tests/unit/test_api.py -v

# 单个测试类
poetry run pytest tests/unit/test_api.py::TestOrderAPI -v

# 单个测试用例
poetry run pytest tests/unit/test_api.py::TestOrderAPI::test_order_in_handle_data -v
```

### 调试测试

```bash
# 显示print输出
poetry run pytest tests/unit -v -s

# 详细错误信息
poetry run pytest tests/unit -vv

# 只运行失败的测试
poetry run pytest tests/unit --lf

# 第一个失败时停止
poetry run pytest tests/unit -x
```

---

## 📦 测试文件结构

```
tests/
├── conftest.py              # 测试fixtures和配置
├── README.md               # 本文档
├── unit/                    # API、对象、订单、回测与统计单元测试
└── integration/             # 跨组件及真实临时数据测试
    └── test_data_server_incremental_loading.py
```

---

## 测试范围

**基于PTrade API官方文档，仅测试文档公开的API**

### API测试
- `test_api*.py` - 核心API、边界、格式与兼容性

### 对象和订单测试
- `test_object*.py` - Portfolio/Position
- `test_order*.py` - 订单系统与成交处理

### 回测与基础设施测试
- `test_minute_runner_regressions.py` - 分钟回测与数据加载配置
- `test_stats_optimizer_regressions.py` - 收益统计与参数优化
- `test_trade_flow_regressions.py` - 佣金、T+1 与跨日交易流程
- `test_cache.py`、`test_lifecycle.py`、`test_data_context.py` - 缓存与生命周期

### 集成测试
- `integration/test_data_server_incremental_loading.py` - 真实临时 Parquet 数据的增量补载

### 已删除的非文档API测试
❌ `get_adjusted_price` - 内部辅助方法，非公开API
❌ `get_stock_blocks` 冗余测试（保留1个基础测试）
❌ `get_stock_exrights` 冗余测试（非必测API）
❌ `get_industry_stocks` 冗余测试（非必测API）
❌ `get_Ashares` 冗余测试（非必测API）

---

## 代码覆盖率

覆盖率会随测试集持续变化，以 CI 生成的 XML/HTML 报告为准：

```bash
poetry run pytest tests --cov=simtradelab --cov-report=term-missing --cov-report=html
```

---

## 测试设计原则

1. **真实对象** - 使用真实Portfolio/Context/API，零Mock
2. **生命周期严格** - 遵循ptrade生命周期，非法调用必须抛异常
3. **自动隔离** - autouse fixture自动重置缓存，独立测试数据
4. **简化数据** - 3个测试股票，20天数据，不依赖完整HDF5

---

## 关键保护

**交易API**: order, order_target, order_value, cancel_order, get_position
**数据API**: get_price, get_history, get_stock_info, check_limit, get_trade_days
**配置API**: set_benchmark, set_universe, set_commission, set_slippage

---

## 添加新测试

```python
def test_my_api(ptrade_api):
    # 设置生命周期
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)
    ptrade_api.context.current_dt = datetime(2024, 1, 2)

    # 调用测试
    result = ptrade_api.my_api()
    assert result is not None
```

---

## 持续集成

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: poetry install
      - name: Run unit tests
        run: poetry run pytest tests/unit
      - name: Run integration tests
        run: poetry run pytest tests/integration
      - name: Run coverage
        run: poetry run pytest tests --cov=simtradelab
```

---

## 下一步改进

**提升覆盖率**
- backtest/runner.py - 回测流程测试
- backtest/stats.py - 统计指标测试
- strategy_engine.py - 策略执行测试

**集成测试** - tests/integration/
- 扩展完整回测流程覆盖
- 多策略并发
- 大数据集性能

---

## 总结

✅ 单元测试与集成测试分层执行
✅ 完整测试集生成覆盖率报告
✅ 严格遵循PTrade API官方文档
✅ 仅测试文档公开API，保证兼容性

**测试质量要求**：优先验证真实行为与返回结构，避免宽松断言；跨组件行为放入集成测试。

**每次修改代码前后都要运行测试！**

```bash
poetry run pytest tests -v
```
