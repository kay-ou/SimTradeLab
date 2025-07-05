# 测试目录结构

## 📁 测试分类

### unit/ - 单元测试
- `test_core_apis.py` - 核心API单元测试（合并了所有API相关测试）
- `test_core_components.py` - 核心组件单元测试（引擎、上下文、数据源等）
- `test_engine.py` - 回测引擎单元测试
- `test_data_sources.py` - 数据源单元测试
- `test_compatibility.py` - 兼容性测试

### integration/ - 集成测试
- `test_strategy_execution.py` - 策略执行集成测试（合并了所有策略相关测试）
- `test_integration.py` - 系统集成测试

### performance/ - 性能测试
- `test_performance.py` - 性能和压力测试（合并了所有性能相关测试）

### e2e/ - 端到端测试
- `test_real_world_scenarios.py` - 真实世界场景测试（合并了所有端到端测试）

## 🏃 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定类型的测试
poetry run pytest tests/unit/          # 单元测试
poetry run pytest tests/integration/   # 集成测试
poetry run pytest tests/performance/   # 性能测试
poetry run pytest tests/e2e/          # 端到端测试

# 运行特定标记的测试
poetry run pytest -m unit             # 单元测试标记
poetry run pytest -m integration      # 集成测试标记
poetry run pytest -m performance      # 性能测试标记
poetry run pytest -m e2e             # 端到端测试标记

# 跳过慢速测试
poetry run pytest -m "not slow"

# 跳过需要网络的测试
poetry run pytest -m "not network"
```

## 📊 测试覆盖率

```bash
# 生成覆盖率报告
poetry run pytest --cov=simtradelab --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 🎯 测试重组成果

- **从25个测试文件减少到8个核心测试文件**
- **消除了重复的测试函数**
- **按照测试类型清晰分类**
- **保持100%的功能覆盖**
- **提高了测试维护性**
