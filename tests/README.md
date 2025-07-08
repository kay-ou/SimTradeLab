# 测试目录结构

## 📁 测试分类

### unit/ - 单元测试

### integration/ - 集成测试

### performance/ - 性能测试

### e2e/ - 端到端测试


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
