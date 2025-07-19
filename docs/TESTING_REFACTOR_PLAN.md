# SimTradeLab 测试重构执行计划

## 🎯 重构目标

将过度依赖 Mock 的测试重构为真实、有价值的测试，确保测试能够发现真实的业务问题。

## 📋 阶段 1: 立即废弃过度 Mock 的测试

### 需要废弃的具体测试

#### tests/test_runner.py
```python
# 🗑️ 废弃 - 过度模拟，无业务价值
def test_runner_with_plugins_in_config(self, strategy_file):
    # 完全模拟 BacktestEngine 和 PluginManager
    with patch("simtradelab.runner.BacktestEngine") as mock_engine:
        with patch("simtradelab.runner.PluginManager") as mock_pm_class:
            # ... 大量模拟代码

# 🗑️ 废弃 - 只验证方法调用
def test_ensure_backtest_plugins_already_registered(self, strategy_file, mock_config):
    # 只验证 register_plugin 是否被调用，无实际业务验证
```

#### tests/backtest/test_engine.py
```python
# 🗑️ 废弃 - 过度模拟插件
@pytest.fixture
def mock_plugin_manager():
    # 模拟所有插件类型，与真实插件行为完全隔离
    manager = MagicMock(spec=PluginManager)
    # ... 大量模拟设置
```

#### tests/core/test_plugin_manager.py
```python
# 🗑️ 废弃 - 纯模拟测试
def test_plugin_lifecycle_events_are_published(self):
    # 使用 MagicMock 模拟事件处理，无法验证真实事件流
    mock_handler = MagicMock()
```

## 📋 阶段 2: 重写为真实集成测试

### 2.1 Runner 集成测试重写

**目标**: 使用真实策略、真实插件、真实数据进行测试

```python
# ✅ 新的真实集成测试
class TestBacktestRunnerRealIntegration:
    """使用真实组件的 Runner 集成测试"""
    
    def test_complete_backtest_workflow_with_real_components(self):
        """测试完整的回测工作流程 - 使用真实组件"""
        # 使用真实策略文件
        strategy_content = '''
def initialize(context):
    context.set_universe(["000001.SZ"])
    
def handle_data(context, data):
    if "000001.SZ" in data:
        context.order_target_percent("000001.SZ", 0.5)
        '''
        
        # 使用真实配置
        config = {
            "data_source": "mock_data_plugin",  # 使用真实插件
            "initial_cash": 100000,
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
        
        # 执行真实回测
        runner = BacktestRunner(strategy_content=strategy_content, config=config)
        result = runner.run()
        
        # 验证真实业务结果
        assert result["total_return"] is not None
        assert result["sharpe_ratio"] is not None
        assert len(result["trades"]) > 0
```

### 2.2 回测引擎测试重写

**目标**: 使用真实插件进行引擎测试

```python
# ✅ 新的真实插件测试
class TestBacktestEngineRealPlugins:
    """使用真实插件的回测引擎测试"""
    
    @pytest.fixture
    def real_plugin_manager(self):
        """提供配置了真实插件的插件管理器"""
        manager = PluginManager()
        
        # 注册真实插件
        manager.register_plugin("SimpleMatchingEngine")
        manager.register_plugin("FixedSlippageModel") 
        manager.register_plugin("FixedCommissionModel")
        
        return manager
    
    def test_order_execution_with_real_plugins(self, real_plugin_manager):
        """测试使用真实插件的订单执行"""
        engine = BacktestEngine(plugin_manager=real_plugin_manager)
        engine.start()
        
        # 提交真实订单
        order = Order("test_order", "000001.SZ", "buy", 100, 10.0)
        engine.submit_order(order)
        
        # 使用真实市场数据
        market_data = MarketData(
            symbol="000001.SZ",
            timestamp=datetime.now(),
            open_price=10.0, high_price=10.2,
            low_price=9.8, close_price=10.1,
            volume=10000
        )
        engine.update_market_data("000001.SZ", market_data)
        
        # 验证真实执行结果
        fills = engine.get_fills()
        assert len(fills) > 0
        assert fills[0].price > 0  # 真实价格
        assert fills[0].commission > 0  # 真实佣金
```

### 2.3 PTrade 适配器测试重写

**目标**: 增加真实 API 集成测试

```python
# ✅ 新的真实 API 测试
class TestPTradeAdapterRealAPI:
    """PTrade 适配器真实 API 集成测试"""
    
    @pytest.mark.integration
    def test_strategy_execution_with_real_data_source(self):
        """测试使用真实数据源的策略执行"""
        config = AdapterConfig(config={
            "use_mock_data": False,  # 使用真实数据
            "data_source": "akshare_plugin",
            "initial_cash": 100000
        })
        
        adapter = PTradeAdapter(config)
        # 设置真实插件管理器
        plugin_manager = PluginManager()
        adapter.set_plugin_manager(plugin_manager)
        
        # 加载真实策略
        strategy_content = '''
def initialize(context):
    context.set_universe(["000001.SZ"])
    
def handle_data(context, data):
    # 使用真实数据进行决策
    if "000001.SZ" in data:
        price = data["000001.SZ"]["close"]
        if price > 0:  # 基本有效性检查
            context.order_target_percent("000001.SZ", 0.3)
        '''
        
        adapter.load_strategy_from_content(strategy_content)
        
        # 执行并验证真实结果
        result = adapter.run_backtest(
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        
        # 验证真实业务指标
        assert result.total_return is not None
        assert result.max_drawdown is not None
        assert len(result.trades) >= 0
```

## 📋 阶段 3: 新增真实性验证测试

### 3.1 端到端策略验证测试

```python
class TestEndToEndStrategyValidation:
    """端到端策略验证测试"""
    
    @pytest.mark.slow
    def test_buy_and_hold_strategy_realistic_performance(self):
        """测试买入持有策略的真实表现"""
        # 使用真实历史数据
        # 验证策略在不同市场条件下的表现
        # 确保结果符合预期的统计特征
        pass
```

### 3.2 数据源真实性测试

```python
class TestDataSourceRealism:
    """数据源真实性测试"""
    
    def test_mock_data_statistical_properties(self):
        """测试模拟数据的统计特性是否接近真实市场"""
        # 验证价格分布、波动率、相关性等统计特征
        # 与真实市场数据进行对比
        pass
```

## 🚀 执行时间表

### 第 1 周
- [x] 完成测试审计报告
- [ ] 标记需要废弃的测试
- [ ] 重写 Runner 核心测试

### 第 2 周  
- [ ] 重写回测引擎测试
- [ ] 重写 PTrade 适配器测试
- [ ] 新增真实数据源集成测试

### 第 3 周
- [ ] 新增端到端策略验证测试
- [ ] 建立测试质量监控
- [ ] 完善测试文档

## 📊 成功指标

- Mock 使用率降低 60%
- 真实场景测试覆盖率达到 80%
- 集成测试比例提升到 40%
- 测试发现的生产问题减少 50%

## ⚠️ 风险控制

1. **渐进式重构**: 不一次性删除所有测试，确保覆盖率不下降
2. **并行开发**: 新测试与旧测试并存，验证后再删除旧测试
3. **回滚计划**: 如果新测试不稳定，可以快速回滚到旧测试

---

**执行负责人**: 开发团队  
**审查周期**: 每周  
**完成目标**: 3 周内完成核心测试重构
