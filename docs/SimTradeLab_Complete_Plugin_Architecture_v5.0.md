# SimTradeLab 完整插件化架构设计文档 v5.0

## 1. 架构总览

### 1.1 设计原则

基于PTrade API深入分析和实际生产需求，本架构遵循以下核心原则：

1.  **性能优先**: 核心交易功能不使用插件，确保最佳性能。
2.  **完全兼容**: 100% 遵循PTrade官方API文档规范。
3.  **合理插件化**: 每个插件都有充分的技术和业务理由。
4.  **生产就绪**: 支持企业级部署和多平台扩展。
5.  **开发友好**: 提供完整的开发工具链和调试支持。
6.  **动态可控**: 支持插件热插拔和运行时配置更新。
7.  **安全隔离**: 多级沙箱机制保障系统安全性。
8.  **健壮可靠**: 内置事件契约、配置验证与标准化测试框架。

### 1.2 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    平台适配层                                │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   PTrade适配器   │    │  掘金适配器      │                 │
│  │   adapter.py    │    │  adapter.py     │                 │
│  └─────────────────┘    └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    核心框架层                                │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   核心引擎       │    │   插件管理器     │                 │
│  │   engine.py     │    │   plugin_mgr.py │                 │
│  └─────────────────┘    └─────────────────┘                 │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ 生命周期管理器   │    │   安全沙箱       │                 │
│  │ lifecycle_mgr.py│    │   sandbox.py    │                 │
│  └─────────────────┘    └─────────────────┘                 │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   事件总线       │    │   配置验证器     │                 │
│  │   event_bus.py  │    │ validator.py    │                 │
│  └─────────────────┘    └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    插件扩展层                                │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │   数据     │ │   策略     │ │   分析     │ │   集成     │   │
│  │   插件     │ │   插件     │ │   插件     │ │   插件     │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐   │
│  │ 监控告警   │ │ 配置中心   │ │ 分布式     │ │ 可视化     │   │
│  │   插件     │ │   插件     │ │ 缓存插件   │ │   插件     │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 v4.0新增特性

**🔥 插件生命周期管理**
- 热插拔支持：无需重启系统即可加载/卸载插件
- 版本升级：支持插件在线升级和回滚
- 状态迁移：插件重载时保持运行状态

**🔒 多级安全隔离**
- 线程级隔离：轻量级隔离适用于可信插件
- 进程级隔离：中等安全级别，独立进程运行
- 容器级隔离：最高安全级别，Docker容器隔离

**📊 动态配置中心**
- 实时配置更新：运行时修改插件配置
- 配置历史追踪：完整的配置变更记录
- 配置回滚：支持配置快速回滚到历史版本

**🚀 智能数据分层**
- 冷热数据分离：热数据内存缓存，冷数据归档存储
- 分布式缓存：多节点缓存集群支持动态扩展
- 智能迁移：基于访问模式自动数据迁移

### 1.4 v5.0 新增特性

**v5.0 架构在 v4.0 的基础上，聚焦于提升系统的健壮性、开发效率和可维护性。**

**📜 标准化事件总线契约**
- **目的**: 统一插件间通信标准，避免混乱。
- **实现**: 定义了标准的事件结构和核心事件的 `payload` 格式，形成稳定的“内部API”。

**⚙️ 可插拔的回测组件**
- **目的**: 提升回测的灵活性和保真度。
- **实现**: 将撮合引擎、滑点、手续费等核心模拟逻辑抽象为可插拔的插件，允许用户按需组合。

**✅ 健壮的配置验证机制**
- **目的**: 从源头保证配置的正确性，提前暴露问题。
- **实现**: 集成 `Pydantic` 进行配置模型的定义和验证，在加载时对配置的结构、类型和值进行严格校验。

**🧪 统一的插件测试框架**
- **目的**: 简化和规范插件的测试流程。
- **实现**: 提供 `BasePluginTest` 测试基类，预先模拟核心服务，并提供完整的集成测试示例。

**🚀 开发者快速入门**
- **目的**: 降低新开发者的上手门槛。
- **实现**: 提供 `cookiecutter` 模板用于一键生成插件项目骨架，并附有详细的入门指南。

**🔗 插件依赖管理**
- **目的**: 确保插件生态系统的稳定性和兼容性。
- **实现**: 提供插件清单（Manifest）系统，支持版本依赖、能力声明和冲突检测。

**🎯 企业级多租户支持**
- **目的**: 支持企业环境下的多租户部署和资源隔离。
- **实现**: 插件实例隔离、资源配额管理和完整的审计日志系统。

## 2. PTrade实盘/回测模式区分设计

### 2.1 模式感知适配器

```python
# src/simtradelab/adapters/ptrade/adapter.py
class PTradeAdapter:
    """PTrade模式感知适配器"""
    
    def __init__(self, core_engine, mode='backtest', backtest_config=None):
        self.core = core_engine
        self.mode = mode  # 'backtest' | 'live'
        self.api_router = self._init_api_router(backtest_config)
    
    def _init_api_router(self, backtest_config=None):
        """初始化API路由器"""
        if self.mode == 'backtest':
            # v5.0: 注入可插拔的回测引擎
            return BacktestAPIRouter(self.core, backtest_config)
        else:
            return TradingAPIRouter(self.core)
    
    # ... (其他方法保持不变)
```

### 2.2 v5.0: 可插拔的高保真回测引擎

为了实现更灵活和精确的回测，v5.0 将回测引擎的核心组件插件化。

```python
# src/simtradelab/backtest/engine.py
class BacktestEngine:
    """可插拔的回测引擎"""
    def __init__(self, config):
        # v5.0: 增加组件间的依赖关系和兼容性验证
        self._validate_component_compatibility()
        self.matcher = self._load_plugin(config.get('matcher', 'default_matcher'))
        self.slippage_model = self._load_plugin(config.get('slippage', 'default_slippage'))
        self.commission_model = self._load_plugin(config.get('commission', 'default_commission'))
        self.latency_model = self._load_plugin(config.get('latency', 'default_latency'))

    def _validate_component_compatibility(self):
        """验证回测组件间的兼容性"""
        # 检查组件版本兼容性
        # 验证组件间的依赖关系
        # 确保配置参数的一致性
        pass

    def _load_plugin(self, plugin_name):
        # 从插件管理器加载对应回测组件插件
        return plugin_manager.load_plugin(plugin_name)

    def run(self, data_feed):
        for bar in data_feed:
            # 1. 获取策略订单
            orders = self.strategy.handle_bar(bar)
            
            # 2. 应用延迟模型
            delayed_orders = self.latency_model.apply(orders)
            
            # 3. 撮合成交
            fills = self.matcher.match(delayed_orders, bar)
            
            # 4. 计算滑点
            slipped_fills = self.slippage_model.apply(fills, bar)
            
            # 5. 计算手续费
            final_fills = self.commission_model.apply(slipped_fills)
            
            # 6. 更新投资组合
            self.portfolio.update(final_fills)

# 示例：滑点模型插件
# src/simtradelab/plugins/backtest/slippage.py
class BaseSlippageModel(BasePlugin):
    def apply(self, fills, bar):
        raise NotImplementedError

class VolumeShareSlippage(BaseSlippageModel):
    def __init__(self, config):
        self.volume_ratio = config.get('volume_ratio', 0.025)
        self.price_impact = config.get('price_impact', 0.1)

    def apply(self, fills, bar):
        # 根据成交量在bar中的占比，模拟价格冲击
        for fill in fills:
            trade_ratio = fill.amount / bar.volume
            price_adjustment = (trade_ratio / self.volume_ratio) ** 2 * self.price_impact
            fill.price *= (1 + price_adjustment) # 对买单不利，对卖单有利
        return fills
```

**优点**:
- **高度灵活**: 用户可以像搭乐高一样组合不同的回测组件。
- **易于扩展**: 添加新的滑点或手续费模型只需实现一个新的插件。
- **研究友好**: 便于研究不同市场微观结构对策略性能的影响。

## 3. 插件生命周期管理和热插拔
(内容与v4.0保持一致)

## 4. 插件隔离和安全（沙箱）
(内容与v4.0保持一致)

## 5. 动态配置中心和监控系统

### 5.1 - 5.4
(内容与v4.0保持一致)

### 5.5 v5.0: 统一配置管理器 (Unified Configuration Manager)

为解决配置系统的架构问题，v5.0 引入了统一配置管理器，实现了编译时配置验证和类型安全的配置创建机制。

#### 5.5.1 配置装饰器系统

```python
# src/simtradelab/core/config/decorators.py
from simtradelab.core.config.decorators import plugin_config, optional_config, config_required

# 强制配置装饰器
@plugin_config(AkShareDataPluginConfig)
class AkShareDataPlugin(BasePlugin):
    """AkShare数据源插件，配置模型在编译时绑定"""
    pass

# 可选配置装饰器
@optional_config(SimpleConfig)
class SimplePlugin(BasePlugin):
    """可选配置插件，可以使用默认配置或自定义配置"""
    pass

# 强制配置装饰器（运行时验证）
@config_required(ComplexConfig)
class ComplexPlugin(BasePlugin):
    """强制配置插件，必须提供有效配置才能初始化"""
    pass
```

#### 5.5.2 统一配置管理器

```python
# src/simtradelab/core/config/config_manager.py
class PluginConfigManager:
    """统一配置管理器，消除插件管理器的配置职责混乱"""
    
    def create_validated_config(
        self, 
        plugin_class: Type,
        config_data: Optional[Any] = None
    ) -> BaseModel:
        """
        创建经过验证的配置对象
        
        这是E9修复的核心方法，替换插件管理器中的复杂配置代码
        实现：
        - 编译时确定配置模型（避免运行时类型检查）
        - 使用Pydantic内置机制处理额外字段
        - 类型安全的配置创建
        """
        config_model_class = self._get_config_model(plugin_class)
        
        if config_data is None:
            return config_model_class()
            
        if isinstance(config_data, config_model_class):
            return config_data
            
        # 使用Pydantic的model_validate，自动处理额外字段
        return self._create_config_from_data(config_model_class, config_data, plugin_name)

# 插件管理器中的简化调用
class PluginManager:
    def load_plugin(self, plugin_name: str, config: Optional[Any] = None) -> BasePlugin:
        # E9修复：替换35行复杂配置代码为3行清晰调用
        plugin_config = self._config_manager.create_validated_config(
            registry.plugin_class, 
            config or registry.config
        )
        
        # 创建插件实例
        instance = registry.plugin_class(registry.metadata, plugin_config)
        # ... 其他逻辑
```

#### 5.5.3 配置验证机制

```python
# src/simtradelab/plugins/config/base_config.py
class BasePluginConfig(BaseModel):
    """统一配置基类，支持环境变量和多环境配置"""
    
    model_config = ConfigDict(
        extra='forbid',  # 不允许未定义字段
        validate_assignment=True,  # 运行时验证
        str_strip_whitespace=True,  # 自动去除空白
    )
    
    enabled: bool = Field(default=True, description="是否启用插件")
    environment: Literal['development', 'testing', 'production'] = 'development'
    
    @field_validator('*', mode='before')
    @classmethod
    def resolve_environment_variables(cls, v):
        """支持环境变量注入，如 ${ENV_VAR}"""
        if isinstance(v, str) and v.startswith('${') and v.endswith('}'):
            env_var = v[2:-1]
            return os.getenv(env_var, v)
        return v

class AkShareDataPluginConfig(BasePluginConfig):
    """AkShare数据源插件配置模型"""
    name: str = Field("akshare_data_source", description="插件名称")
    symbols: List[str] = Field(..., min_length=1, description="股票代码列表")
    start_date: str = Field(..., description="开始日期")
    end_date: str = Field(..., description="结束日期")
    api_timeout: int = Field(default=30, ge=1, le=300, description="API超时时间")
    cache_enabled: bool = Field(default=True, description="是否启用缓存")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
```

#### 5.5.4 E9重构成果

**架构改进**：
- ✅ **职责分离**：配置管理从插件管理器中独立出来
- ✅ **编译时验证**：使用装饰器在类定义时绑定配置模型
- ✅ **类型安全**：完全类型安全的配置创建机制
- ✅ **零侵入**：现有插件API完全不变

**代码质量提升**：
- ✅ 删除35行复杂配置验证代码 → 3行清晰调用
- ✅ 消除运行时类型检查和手动字段过滤
- ✅ 利用Pydantic内置机制处理配置验证
- ✅ 创建200行高质量配置管理组件

**性能优化**：
- ✅ 减少运行时反射和异常处理开销
- ✅ 编译时确定配置模型，避免动态导入
- ✅ 使用Pydantic的高性能验证机制

### 5.6 v5.0: 配置验证 (Configuration Validation) - 已弃用

> **注意**: 本节内容已被5.5节的统一配置管理器替代。E9重构移除了分散的配置验证逻辑，统一到配置管理器中处理。

## 6. 数据系统优化
(内容与v4.0保持一致)

## 7. 多策略协同和动态权重调整
(内容与v4.0保持一致)

---
## **以下为 v5.0 新增核心章节**
---

## 8. 事件总线架构 (Event Bus Architecture)

事件总线是插件化架构的神经系统，v5.0 对其进行了标准化，以确保插件间通信的可靠与可追溯。

### 8.1 标准事件结构

所有通过 `EventBus` 传递的事件都必须遵循以下结构：

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid

class CloudEvent(BaseModel):
    """
    标准云事件模型 (遵循 CNCF CloudEvents 规范)
    v5.0 增强版本，支持事件优先级、版本控制和关联追踪
    """
    specversion: str = "1.0"
    type: str = Field(..., description="事件类型, e.g., 'com.simtradelab.plugin.loaded'")
    source: str = Field(..., description="事件来源, e.g., 'PluginLifecycleManager'")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="唯一事件ID")
    time: datetime = Field(default_factory=datetime.utcnow)
    datacontenttype: str = "application/json"
    data: Dict[str, Any] = Field(..., description="事件的具体负载")
    
    # v5.0 新增字段
    priority: int = Field(default=5, ge=1, le=10, description="事件优先级，1最高，10最低")
    version: str = Field(default="1.0", description="事件结构版本")
    correlation_id: Optional[str] = Field(None, description="关联ID，用于追踪事件链")
    tags: Dict[str, str] = Field(default_factory=dict, description="事件标签，用于分类和过滤")

```

### 8.2 核心事件契约 (Core Event Contracts)

系统定义了一系列核心事件，插件开发者可以订阅这些事件，或在特定条件下发布这些事件。

| 事件类型 (`type`) | 优先级 | 来源 (`source`) | `data` 负载 (Payload) 示例 | 描述 |
| :--- | :---: | :--- | :--- | :--- |
| `com.simtradelab.system.start` | 2 | `CoreEngine` | `{'startup_time': '2024-01-01T00:00:00Z'}` | 系统核心引擎启动 |
| `com.simtradelab.plugin.loaded` | 5 | `PluginLifecycleManager` | `{'plugin_name': 'risk_plugin_v2', 'version': '2.1.0'}` | 插件被成功加载 |
| `com.simtradelab.plugin.unloaded`| 5 | `PluginLifecycleManager` | `{'plugin_name': 'risk_plugin_v2', 'reason': 'user_request'}` | 插件被卸载 |
| `com.simtradelab.config.changed` | 4 | `DynamicConfigCenter` | `{'plugin': 'ma_strategy', 'key': 'short_window', 'old_value': 10, 'new_value': 15}` | 插件配置发生变更 |
| `com.simtradelab.trade.order.created` | 3 | `StrategyPlugin` | `{'order_id': 'ord_123', 'symbol': '600519', 'amount': 100, 'price': 1500.0}` | 策略创建了一个新订单 |
| `com.simtradelab.trade.order.filled` | 2 | `BacktestEngine` / `LiveAdapter` | `{'order_id': 'ord_123', 'fill_price': 1500.0, 'fill_time': '2024-01-01T09:30:00Z'}` | 订单被成交 |
| `com.simtradelab.risk.alert` | 1 | `RiskControlPlugin` | `{'rule': 'max_drawdown', 'current_value': 0.15, 'threshold': 0.10, 'severity': 'critical'}` | 触发了风控警报 |
| `com.simtradelab.data.error` | 2 | `DataSourcePlugin` | `{'source': 'akshare', 'symbol': '000001', 'error': 'connection_timeout'}` | 数据源异常 |

### 8.3 使用示例

```python
# 一个插件发布事件
def some_strategy_logic(context, data):
    if condition_met:
        order_event = CloudEvent(
            type="com.simtradelab.trade.order.created",
            source="MyAwesomeStrategy",
            id=str(uuid.uuid4()),
            data={'symbol': 'AAPL', 'amount': 100, 'order_type': 'market'}
        )
        context.event_bus.emit(order_event)

# 另一个插件监听事件
class OrderAuditorPlugin(BasePlugin):
    def __init__(self, config):
        super().__init__(config)
        self.event_bus.subscribe(
            "com.simtradelab.trade.order.created", 
            self.on_order_created
        )

    def on_order_created(self, event: CloudEvent):
        logger.info(f"Audit: New order created by {event.source}: {event.data}")

```

## 9. 插件测试框架 (Plugin Testing Framework)

为保证插件质量并简化开发，v5.0 提供了一个统一的测试框架。

### 9.1 核心理念

- **隔离测试**: 插件的单元测试应在不依赖其他真实插件的情况下进行。
- **依赖注入**: 核心服务 (`EventBus`, `DynamicConfigCenter` 等) 应被模拟 (Mock) 并注入到被测插件中。
- **集成测试**: 提供工具来测试插件之间的真实交互。

### 9.2 `BasePluginTest` 基类

我们提供一个 `pytest` 基类，它预设了所有必要的模拟。

```python
# tests/framework/base_test.py
import pytest
from unittest.mock import MagicMock

class BasePluginTest:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        # 模拟核心服务
        self.mock_event_bus = MagicMock(spec=EventBus)
        self.mock_config_center = MagicMock(spec=DynamicConfigCenter)
        self.mock_plugin_manager = MagicMock(spec=PluginLifecycleManager)
        
        # 将模拟对象注入，方便测试用例使用
        self.mocks = {
            'event_bus': self.mock_event_bus,
            'config_center': self.mock_config_center,
            'plugin_manager': self.mock_plugin_manager
        }

# tests/plugins/test_my_plugin.py
from .framework.base_test import BasePluginTest
from my_awesome_plugin import MyAwesomePlugin

class TestMyAwesomePlugin(BasePluginTest):
    def test_initialization(self):
        # 使用模拟的配置中心
        self.mock_config_center.get_config.return_value = {'param': 'value'}
        
        plugin = MyAwesomePlugin(self.mocks)
        
        # 断言插件正确地订阅了事件
        self.mock_event_bus.subscribe.assert_called_with("some_event", plugin.on_some_event)

    def test_event_handling(self):
        plugin = MyAwesomePlugin(self.mocks)
        
        # 模拟事件发生
        test_event = CloudEvent(...)
        plugin.on_some_event(test_event)
        
        # 断言插件发布了正确的响应事件
        self.mock_event_bus.emit.assert_called_once()
        emitted_event = self.mock_event_bus.emit.call_args[0][0]
        assert emitted_event.type == "response_event"
```

### 9.3 集成测试示例

集成测试则会加载真实的插件，但可能只模拟外部依赖（如交易所API）。

```python
# tests/integration/test_strategy_with_risk_plugin.py
def test_strategy_stops_on_risk_alert():
    # 1. 初始化真实的事件总线和配置中心
    event_bus = EventBus()
    config_center = DynamicConfigCenter()
    
    # 2. 加载策略插件和风控插件
    strategy_config = {'threshold': 0.5}
    risk_config = {'max_orders': 10}
    strategy = StrategyPlugin(config_center.get_config('strategy', strategy_config), event_bus)
    risk_plugin = RiskPlugin(config_center.get_config('risk', risk_config), event_bus)
    
    # 3. 模拟市场数据并驱动策略
    for i in range(15):
        strategy.handle_data(...) # 假设这会发出订单事件
        
    # 4. 断言：风控插件应该发出了警报，并且策略应该停止了交易
    # (可以通过检查日志、数据库或策略内部状态来验证)
```

## 10. 开发者快速入门 (Developer Quickstart)

为了让新开发者能快速贡献代码，我们提供了一套标准化的工具。

### 10.1 使用 `cookiecutter` 创建插件

我们提供了一个 `cookiecutter` 模板来一键生成新插件的完整目录结构。

**安装 `cookiecutter`**:
```bash
pip install cookiecutter
```

**使用模板创建新插件**:
```bash
cookiecutter gh:simtradelab/cookiecutter-simtradelab-plugin
```

之后，你会被要求输入插件名称、类型等信息，然后 `cookiecutter` 会自动生成包括以下内容的标准目录：

```
my_new_plugin/
├── src/
│   └── simtradelab/
│       └── plugins/
│           └── my_new_plugin/
│               ├── __init__.py
│               ├── plugin.py      # 插件主逻辑
│               └── config.py      # Pydantic 配置模型
├── tests/
│   ├── __init__.py
│   └── test_plugin.py             # 插件测试用例
├── pyproject.toml                 # 项目依赖
└── README.md                      # 插件说明文档
```

### 10.2 "Hello, World!" 插件开发流程

1.  **创建项目**: 使用上面的 `cookiecutter` 命令创建一个新的数据源插件 `my_data_source`。
2.  **定义配置 (`config.py`)**:
    ```python
    class MyDataSourceConfig(BasePluginConfig):
        api_key: str = Field(..., description="API Key")
    ```
3.  **实现逻辑 (`plugin.py`)**:
    ```python
    class MyDataSource(BaseDataSourcePlugin):
        def __init__(self, config: MyDataSourceConfig, event_bus):
            super().__init__(config, event_bus)
            self.api_key = config.api_key
        
        def get_data(self, symbol):
            print(f"Hello, World! Getting data for {symbol} with key {self.api_key}")
            # ... 实际的数据获取逻辑
            return some_data
    ```
4.  **编写测试 (`test_plugin.py`)**:
    ```python
    class TestMyDataSource(BasePluginTest):
        def test_get_data(self):
            config = MyDataSourceConfig(api_key="test_key")
            plugin = MyDataSource(config, self.mock_event_bus)
            data = plugin.get_data("AAPL")
            # assert data is not None
    ```
5.  **本地运行**:
    - 在 `simtradelab_config.yaml` 中注册你的新插件。
    - 运行 `main.py`，观察 "Hello, World!" 日志输出。

6.  **提交代码**: 确保所有测试 (`poetry run pytest`) 和代码质量检查 (`poetry run flake8`) 通过后，提交你的代码。

---
## **以下为 v5.0 新增企业级功能章节**
---

## 11. 插件依赖管理系统 (Plugin Dependency Management)

v5.0 引入了完整的插件依赖管理系统，确保插件生态系统的稳定性和可维护性。

### 11.1 插件清单 (Plugin Manifest)

每个插件都必须提供一个 `plugin_manifest.yaml` 文件，声明其元信息、依赖关系和能力。

```python
# src/simtradelab/plugins/base.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class PluginManifest(BaseModel):
    """插件清单模型"""
    name: str = Field(..., description="插件名称")
    version: str = Field(..., description="插件版本（遵循语义化版本）")
    description: str = Field(..., description="插件描述")
    author: str = Field(..., description="插件作者")
    license: str = Field(default="MIT", description="许可证")
    
    # 依赖管理
    dependencies: Dict[str, str] = Field(
        default_factory=dict, 
        description="依赖的其他插件，格式: {'plugin_name': '>=1.0.0,<2.0.0'}"
    )
    conflicts: List[str] = Field(
        default_factory=list, 
        description="与此插件冲突的插件列表"
    )
    
    # 能力声明
    provides: List[str] = Field(
        default_factory=list, 
        description="插件提供的能力列表，如 ['data_source', 'market_data']"
    )
    requires: List[str] = Field(
        default_factory=list, 
        description="插件需要的能力列表，如 ['event_bus', 'config_center']"
    )
    
    # 运行时要求
    python_version: str = Field(default=">=3.8", description="支持的Python版本")
    platform: List[str] = Field(
        default_factory=lambda: ["linux", "windows", "darwin"], 
        description="支持的操作系统平台"
    )
    
    # 安全和资源
    security_level: int = Field(default=3, ge=1, le=5, description="安全级别，1-5")
    max_memory_mb: Optional[int] = Field(None, description="最大内存使用（MB）")
    max_cpu_percent: Optional[float] = Field(None, description="最大CPU使用率")

# 示例插件清单
# plugins/akshare_data_source/plugin_manifest.yaml
manifest_example = """
name: akshare_data_source
version: 2.1.0
description: AkShare数据源插件，提供A股市场数据
author: SimTradeLab Team
license: MIT

dependencies:
  redis_cache_plugin: ">=1.0.0,<2.0.0"
  
conflicts:
  - tushare_data_source

provides:
  - data_source
  - market_data
  - fundamental_data

requires:
  - event_bus
  - config_center
  - cache_service

python_version: ">=3.8"
platform: ["linux", "windows", "darwin"]
security_level: 3
max_memory_mb: 512
max_cpu_percent: 50.0
"""
```

### 11.2 依赖解析引擎

```python
# src/simtradelab/plugins/dependency/resolver.py
from packaging import version, specifiers
from typing import Dict, List, Set
import networkx as nx

class DependencyResolver:
    """插件依赖解析引擎"""
    
    def __init__(self, plugin_registry):
        self.registry = plugin_registry
        self.dependency_graph = nx.DiGraph()
    
    def resolve_dependencies(self, target_plugins: List[str]) -> List[str]:
        """
        解析插件依赖，返回正确的加载顺序
        
        Args:
            target_plugins: 目标插件列表
            
        Returns:
            按依赖顺序排列的插件列表
            
        Raises:
            DependencyConflictError: 存在依赖冲突
            CircularDependencyError: 存在循环依赖
            MissingDependencyError: 缺少必需的依赖
        """
        # 1. 收集所有需要的插件及其依赖
        all_plugins = self._collect_all_dependencies(target_plugins)
        
        # 2. 检查版本兼容性
        self._validate_version_compatibility(all_plugins)
        
        # 3. 检查冲突
        self._check_conflicts(all_plugins)
        
        # 4. 构建依赖图
        self._build_dependency_graph(all_plugins)
        
        # 5. 检查循环依赖
        if not nx.is_directed_acyclic_graph(self.dependency_graph):
            cycles = list(nx.simple_cycles(self.dependency_graph))
            raise CircularDependencyError(f"Circular dependencies detected: {cycles}")
        
        # 6. 拓扑排序得到加载顺序
        return list(nx.topological_sort(self.dependency_graph))
    
    def _collect_all_dependencies(self, plugins: List[str], collected: Set[str] = None) -> Set[str]:
        """递归收集所有依赖的插件"""
        if collected is None:
            collected = set()
        
        for plugin_name in plugins:
            if plugin_name in collected:
                continue
                
            collected.add(plugin_name)
            manifest = self.registry.get_manifest(plugin_name)
            if manifest and manifest.dependencies:
                deps = list(manifest.dependencies.keys())
                self._collect_all_dependencies(deps, collected)
        
        return collected
    
    def _validate_version_compatibility(self, plugins: Set[str]):
        """验证版本兼容性"""
        for plugin_name in plugins:
            manifest = self.registry.get_manifest(plugin_name)
            if not manifest:
                raise MissingDependencyError(f"Plugin manifest not found: {plugin_name}")
            
            for dep_name, version_spec in manifest.dependencies.items():
                if dep_name not in plugins:
                    raise MissingDependencyError(f"Missing dependency: {dep_name}")
                
                dep_manifest = self.registry.get_manifest(dep_name)
                dep_version = version.parse(dep_manifest.version)
                spec = specifiers.SpecifierSet(version_spec)
                
                if dep_version not in spec:
                    raise DependencyConflictError(
                        f"Version conflict: {plugin_name} requires {dep_name} {version_spec}, "
                        f"but found {dep_manifest.version}"
                    )

class DependencyConflictError(Exception):
    pass

class CircularDependencyError(Exception):
    pass

class MissingDependencyError(Exception):
    pass
```

## 12. 企业级多租户支持 (Enterprise Multi-Tenancy)

### 12.1 租户隔离架构

```python
# src/simtradelab/core/tenant.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import uuid

class TenantConfig(BaseModel):
    """租户配置"""
    tenant_id: str = Field(..., description="租户唯一标识")
    tenant_name: str = Field(..., description="租户名称")
    
    # 资源配额
    max_plugins: int = Field(default=50, description="最大插件数量")
    max_memory_mb: int = Field(default=4096, description="最大内存使用（MB）")
    max_cpu_cores: float = Field(default=2.0, description="最大CPU核心数")
    max_storage_gb: int = Field(default=100, description="最大存储空间（GB）")
    
    # 插件权限
    allowed_plugin_types: List[str] = Field(
        default_factory=lambda: ["data_source", "strategy", "risk", "visualization"],
        description="允许使用的插件类型"
    )
    forbidden_plugins: List[str] = Field(
        default_factory=list,
        description="禁止使用的特定插件"
    )
    
    # 网络和安全
    network_isolation: bool = Field(default=True, description="是否启用网络隔离")
    data_encryption: bool = Field(default=True, description="是否启用数据加密")
    audit_enabled: bool = Field(default=True, description="是否启用审计日志")

class TenantManager:
    """租户管理器"""
    
    def __init__(self):
        self.tenants: Dict[str, TenantConfig] = {}
        self.tenant_plugins: Dict[str, List[str]] = {}
        self.plugin_instances: Dict[str, Dict[str, Any]] = {}
    
    def create_tenant(self, config: TenantConfig) -> str:
        """创建新租户"""
        tenant_id = config.tenant_id or str(uuid.uuid4())
        self.tenants[tenant_id] = config
        self.tenant_plugins[tenant_id] = []
        self.plugin_instances[tenant_id] = {}
        
        # 创建租户专用的资源容器
        self._create_tenant_sandbox(tenant_id, config)
        
        return tenant_id
    
    def load_plugin_for_tenant(self, tenant_id: str, plugin_name: str, plugin_config: Dict) -> bool:
        """为特定租户加载插件"""
        tenant_config = self.tenants.get(tenant_id)
        if not tenant_config:
            raise ValueError(f"Tenant not found: {tenant_id}")
        
        # 检查插件配额
        if len(self.tenant_plugins[tenant_id]) >= tenant_config.max_plugins:
            raise QuotaExceededError(f"Plugin quota exceeded for tenant {tenant_id}")
        
        # 检查插件权限
        plugin_manifest = self._get_plugin_manifest(plugin_name)
        if plugin_manifest.type not in tenant_config.allowed_plugin_types:
            raise PermissionDeniedError(f"Plugin type not allowed: {plugin_manifest.type}")
        
        if plugin_name in tenant_config.forbidden_plugins:
            raise PermissionDeniedError(f"Plugin explicitly forbidden: {plugin_name}")
        
        # 在租户沙箱中实例化插件
        plugin_instance = self._create_plugin_instance(tenant_id, plugin_name, plugin_config)
        self.plugin_instances[tenant_id][plugin_name] = plugin_instance
        self.tenant_plugins[tenant_id].append(plugin_name)
        
        return True
```

### 12.2 资源配额管理

```python
# src/simtradelab/core/quota.py
import psutil
import threading
from datetime import datetime, timedelta

class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.tenant_usage: Dict[str, Dict[str, float]] = {}
        self.monitoring_thread = None
        self.running = False
    
    def start_monitoring(self):
        """开始监控资源使用"""
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop)
        self.monitoring_thread.start()
    
    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            for tenant_id in self.tenant_usage:
                usage = self._calculate_tenant_usage(tenant_id)
                self.tenant_usage[tenant_id] = usage
                
                # 检查是否超出配额
                self._check_quota_violations(tenant_id, usage)
            
            time.sleep(5)  # 每5秒检查一次
    
    def _calculate_tenant_usage(self, tenant_id: str) -> Dict[str, float]:
        """计算租户资源使用情况"""
        # 这里需要根据实际的插件实例计算资源使用
        # 可能需要与容器运行时（如Docker）集成
        return {
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "storage_gb": 0.0,
            "network_io_mb": 0.0
        }
    
    def _check_quota_violations(self, tenant_id: str, usage: Dict[str, float]):
        """检查配额违规"""
        tenant_config = self.tenant_manager.tenants[tenant_id]
        
        violations = []
        if usage["memory_mb"] > tenant_config.max_memory_mb:
            violations.append(f"Memory usage exceeded: {usage['memory_mb']}MB > {tenant_config.max_memory_mb}MB")
        
        if usage["cpu_percent"] > tenant_config.max_cpu_cores * 100:
            violations.append(f"CPU usage exceeded: {usage['cpu_percent']}% > {tenant_config.max_cpu_cores * 100}%")
        
        if violations:
            self._handle_quota_violation(tenant_id, violations)
    
    def _handle_quota_violation(self, tenant_id: str, violations: List[str]):
        """处理配额违规"""
        # 记录审计日志
        audit_logger.warning(f"Quota violation for tenant {tenant_id}: {violations}")
        
        # 可以选择暂停或限制租户的插件
        # self._throttle_tenant_plugins(tenant_id)
```

### 12.3 审计日志系统

```python
# src/simtradelab/core/audit.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional
import json

class AuditEvent(BaseModel):
    """审计事件"""
    event_id: str = Field(..., description="事件唯一标识")
    tenant_id: str = Field(..., description="租户ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    event_type: str = Field(..., description="事件类型")
    action: str = Field(..., description="操作名称")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    
    details: Dict[str, Any] = Field(default_factory=dict, description="事件详情")
    result: str = Field(..., description="操作结果: success/failure/warning")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    source_ip: Optional[str] = Field(None, description="来源IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")

class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, storage_backend="database"):
        self.storage_backend = storage_backend
        self.enabled = True
    
    def log_plugin_operation(self, tenant_id: str, action: str, plugin_name: str, 
                           result: str = "success", details: Dict = None, 
                           user_id: str = None, error_message: str = None):
        """记录插件操作"""
        if not self.enabled:
            return
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="plugin_operation",
            action=action,
            resource_type="plugin",
            resource_id=plugin_name,
            details=details or {},
            result=result,
            error_message=error_message
        )
        
        self._store_event(event)
    
    def log_config_change(self, tenant_id: str, config_path: str, old_value: Any, 
                         new_value: Any, user_id: str = None):
        """记录配置变更"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="configuration_change",
            action="update_config",
            resource_type="configuration",
            resource_id=config_path,
            details={
                "old_value": old_value,
                "new_value": new_value,
                "config_path": config_path
            },
            result="success"
        )
        
        self._store_event(event)
    
    def _store_event(self, event: AuditEvent):
        """存储审计事件"""
        if self.storage_backend == "database":
            # 存储到数据库
            pass
        elif self.storage_backend == "file":
            # 存储到文件
            with open(f"audit_{event.tenant_id}_{datetime.now().strftime('%Y%m%d')}.log", "a") as f:
                f.write(event.json() + "\n")
```

## 13. 实施路线图 (Implementation Roadmap)

### 13.1 Phase 1: 核心增强 (立即实施，1-2个月)
- ✅ **事件总线标准化**：实现CloudEvent模型和核心事件契约
- ✅ **配置验证机制**：集成Pydantic配置验证
- ✅ **基础测试框架**：创建BasePluginTest和示例测试用例
- 🔄 **文档生成工具**：从配置模型自动生成API文档

### 13.2 Phase 2: 可插拔架构 (3-4个月)
- ⏳ **可插拔回测引擎**：实现回测组件插件化
- ⏳ **插件依赖管理**：实现依赖解析和版本管理
- ⏳ **开发者工具链**：创建cookiecutter模板和CLI工具
- ⏳ **性能监控**：插件级别的性能分析工具

### 13.3 Phase 3: 企业级功能 (6个月)
- ⏳ **多租户支持**：实现租户隔离和资源配额
- ⏳ **审计日志系统**：完整的操作审计和合规支持
- ⏳ **插件市场**：插件分发和版本管理平台
- ⏳ **高级安全**：数字签名验证和安全扫描

### 13.4 与当前代码的整合计划

基于最近完成的PTrade适配器重构，建议的整合步骤：

1. **立即行动**（本周）：
   - 将PTrade路由器的生命周期控制框架进一步优化为可插拔回测组件
   - 为Stock信息API添加Pydantic配置模型
   - 创建第一个基于新测试框架的测试用例

2. **短期目标**（1个月内）：
   - 实现事件总线的CloudEvent标准
   - 为现有插件添加依赖管理清单
   - 集成配置验证到插件加载流程

3. **中期目标**（3个月内）：
   - 完整的可插拔回测引擎
   - 企业级多租户支持原型
   - 开发者工具链Beta版本

这个路线图确保了v5.0架构的渐进式实施，最小化对现有系统的影响，同时逐步建立起完整的企业级插件生态系统。
