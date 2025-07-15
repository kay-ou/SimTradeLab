# 测试目录结构

## 📁 测试分类

SimTradeLab 采用**按功能模块组织**的测试结构，与项目的插件化架构保持一致。

### test_core/ - 核心功能测试
- 事件总线 (EventBus)
- 插件管理器 (PluginManager)
- CloudEvent 标准事件
- 配置验证系统

### test_plugins/ - 插件测试
- 基础插件 (BasePlugin)
- 数据插件 (DataPlugin)
- 策略插件 (StrategyPlugin)
- 配置验证插件

### test_adapters/ - 适配器测试
- PTrade 适配器
- 路由器测试
- 模型验证测试

## 🏃 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定模块的测试
poetry run pytest tests/test_core/          # 核心功能测试
poetry run pytest tests/test_plugins/       # 插件测试
poetry run pytest tests/test_adapters/      # 适配器测试

# 运行特定标记的测试
poetry run pytest -m unit                   # 单元测试标记
poetry run pytest -m integration            # 集成测试标记
poetry run pytest -m performance            # 性能测试标记

# 跳过慢速测试
poetry run pytest -m "not slow"

# 跳过需要网络的测试
poetry run pytest -m "not network"

# 运行特定插件的测试
poetry run pytest tests/test_plugins/test_base.py
```

## 📊 测试覆盖率

```bash
# 生成覆盖率报告
poetry run pytest --cov=simtradelab --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

## 🎯 测试标记系统

项目使用 pytest 标记来区分测试类型：

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.performance`: 性能测试
- `@pytest.mark.slow`: 慢速测试
- `@pytest.mark.network`: 需要网络的测试
- `@pytest.mark.asyncio`: 异步测试

## 🔧 编写测试

### 使用共享 fixture

```python
import pytest

def test_my_plugin(sample_plugin_metadata, sample_plugin_config, mock_event_bus):
    # 使用 conftest.py 中定义的 fixture
    plugin = MyPlugin(sample_plugin_metadata, sample_plugin_config)
    plugin.initialize()
    assert plugin.state == PluginState.INITIALIZED
```

### 测试插件生命周期

```python
@pytest.mark.unit
def test_plugin_lifecycle(mock_plugin):
    # 测试完整生命周期
    mock_plugin.initialize()
    mock_plugin.start()
    mock_plugin.stop()
    mock_plugin.cleanup()

    # 验证调用历史
    expected_calls = ["initialize", "start", "stop", "cleanup"]
    assert mock_plugin.call_history == expected_calls
```

## 📋 测试最佳实践

1. **功能模块隔离**: 每个功能模块的测试独立，符合插件化架构
2. **标记分类**: 使用 pytest 标记区分测试类型，而非目录结构
3. **简单直接**: 直接编写测试，避免过度抽象
4. **共享配置**: 使用 conftest.py 中的 fixture 避免重复代码
5. **性能监控**: 重要功能包含性能基准测试
