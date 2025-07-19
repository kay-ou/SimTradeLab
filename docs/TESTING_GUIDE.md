# SimTradeLab 测试运行指南

## 📋 测试分类

SimTradeLab 使用 pytest marker 来组织不同类型的测试：

### 测试类型标记

- `@pytest.mark.unit` - 单元测试（快速，隔离）
- `@pytest.mark.integration` - 集成测试（使用真实组件）
- `@pytest.mark.slow` - 慢速测试（性能测试等）
- `@pytest.mark.data` - 需要数据文件的测试
- `@pytest.mark.network` - 需要网络访问的测试

## 🚀 常用测试命令

### 运行所有测试
```bash
poetry run pytest
```

### 按类型运行测试

#### 只运行单元测试（快速）
```bash
poetry run pytest -m unit
```

#### 只运行集成测试
```bash
poetry run pytest -m integration
```

#### 运行慢速测试
```bash
poetry run pytest -m slow
```

#### 排除慢速测试
```bash
poetry run pytest -m "not slow"
```

#### 运行单元测试和集成测试，但排除慢速测试
```bash
poetry run pytest -m "(unit or integration) and not slow"
```

### 按模块运行测试

#### 运行 Runner 相关测试
```bash
poetry run pytest tests/test_runner*.py -v
```

#### 运行回测引擎测试
```bash
poetry run pytest tests/backtest/ -v
```

#### 运行集成测试
```bash
# 运行 Runner 的集成测试
poetry run pytest tests/test_runner.py::TestBacktestRunnerIntegration -v

# 运行回测引擎的集成测试
poetry run pytest tests/backtest/test_engine.py::TestBacktestEngineIntegration -v

# 运行所有集成测试
poetry run pytest -m integration -v

# 运行特定的集成测试类
poetry run pytest -k "Integration" -v
```

### 测试覆盖率

#### 生成覆盖率报告
```bash
poetry run pytest --cov=simtradelab --cov-report=html
```

#### 查看覆盖率报告
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 📊 测试质量标准

### ✅ 好的测试特征

1. **使用真实组件**: 优先使用真实的业务对象而非 Mock
2. **验证业务价值**: 测试实际的业务逻辑而非方法调用
3. **适当的标记**: 使用正确的 pytest marker
4. **清晰的命名**: 测试名称清楚描述测试内容
5. **独立性**: 测试之间不相互依赖

### ❌ 需要避免的测试模式

1. **过度 Mock**: 模拟核心业务对象
2. **方法调用验证**: 只验证方法是否被调用
3. **脆弱的测试**: 对实现细节过度敏感
4. **重复的测试**: 多个测试验证相同的功能
5. **缺乏断言**: 测试没有明确的验证

## 🔧 测试开发工作流

### 1. 编写新测试

```bash
# 创建测试文件
touch tests/test_new_feature.py

# 添加适当的标记
@pytest.mark.unit
def test_new_feature():
    # 测试代码
    pass
```

### 2. 运行新测试

```bash
# 运行特定测试文件
poetry run pytest tests/test_new_feature.py -v

# 运行特定测试函数
poetry run pytest tests/test_new_feature.py::test_new_feature -v
```

### 3. 调试测试

```bash
# 显示详细输出
poetry run pytest tests/test_new_feature.py -v -s

# 在第一个失败时停止
poetry run pytest tests/test_new_feature.py -x

# 显示局部变量
poetry run pytest tests/test_new_feature.py -l
```

## 📈 持续集成

### GitHub Actions 中的测试

```yaml
# .github/workflows/test.yml 示例
- name: Run unit tests
  run: poetry run pytest -m unit

- name: Run integration tests  
  run: poetry run pytest -m integration

- name: Run all tests with coverage
  run: poetry run pytest --cov=simtradelab
```

### 本地预提交检查

```bash
# 运行快速测试
poetry run pytest -m "unit and not slow"

# 运行完整测试套件
poetry run pytest
```

## 🎯 测试最佳实践

### 1. 测试命名

```python
# ✅ 好的命名
def test_order_execution_with_real_plugins():
    """测试使用真实插件的订单执行"""

# ❌ 不好的命名  
def test_order():
    """测试订单"""
```

### 2. 测试结构

```python
# ✅ 清晰的测试结构
def test_commission_calculation():
    # Arrange - 准备测试数据
    engine = BacktestEngine(plugin_manager=real_plugin_manager)
    order = Order("test", "000001.SZ", "buy", 100, 10.0)
    
    # Act - 执行被测试的操作
    engine.submit_order(order)
    result = engine.get_fills()
    
    # Assert - 验证结果
    assert len(result) > 0
    assert result[0].commission > 0
```

### 3. Fixture 使用

```python
# ✅ 复用的测试数据
@pytest.fixture
def real_plugin_manager():
    """提供配置了真实插件的插件管理器"""
    manager = PluginManager(register_core_plugins=True)
    # 配置插件...
    return manager

def test_with_real_plugins(real_plugin_manager):
    # 使用 fixture
    engine = BacktestEngine(plugin_manager=real_plugin_manager)
```

## 📚 相关文档

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-cov 插件](https://pytest-cov.readthedocs.io/)
- [SimTradeLab 测试审计报告](./TESTING_AUDIT_REPORT.md)
- [SimTradeLab 测试重构计划](./TESTING_REFACTOR_PLAN.md)

---

**维护者**: SimTradeLab 开发团队  
**更新日期**: 2025-07-17
