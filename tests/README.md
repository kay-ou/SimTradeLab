# ptradeSim 测试文档

## 📋 测试概述

ptradeSim项目包含完整的测试套件，验证系统各组件功能。所有测试均已通过验证。

## 🧪 测试文件

| 文件 | 功能 | 状态 |
|------|------|------|
| `test_api_injection.py` | API和日志注入测试 | ✅ 通过 |
| `test_strategy_execution.py` | 策略执行流程测试 | ✅ 通过 |
| `test_financial_apis.py` | 财务数据接口测试 | ✅ 通过 |
| `test_market_data_apis.py` | 市场数据接口测试 | ✅ 通过 |
| `test_minute_trading.py` | 分钟级交易综合测试 | ✅ 通过 |

## 🚀 运行测试

### 一键运行所有测试
```bash
poetry run python run_tests.py
```

### 单独运行测试
```bash
# API注入测试
poetry run python tests/test_api_injection.py

# 策略执行测试
poetry run python tests/test_strategy_execution.py

# 财务接口测试
poetry run python tests/test_financial_apis.py

# 市场数据测试
poetry run python tests/test_market_data_apis.py

# 分钟级交易综合测试
poetry run python tests/test_minute_trading.py
```

## 📊 测试内容

### 1. API注入测试
**验证功能：**
- ✅ log对象正确注入
- ✅ 17个核心API函数注入并绑定引擎
- ✅ partial函数绑定机制
- ✅ API函数调用功能

### 2. 策略执行测试
**验证功能：**
- ✅ 策略生命周期函数（initialize, before_trading_start, handle_data, after_trading_end）
- ✅ 交易订单生成和处理
- ✅ 投资组合状态管理
- ✅ 完整回测流程

### 3. 财务接口测试
**验证功能：**
- ✅ get_fundamentals接口（30+财务指标）
- ✅ 财务报表接口（损益表、资产负债表、现金流量表）
- ✅ 财务比率计算接口
- ✅ 数据一致性和错误处理

### 4. 市场数据测试
**验证功能：**
- ✅ get_price接口（15+价格字段）
- ✅ 实时报价数据（五档买卖盘、市场快照）
- ✅ 技术指标计算（MA, MACD, RSI, BOLL, KDJ）
- ✅ 多频率历史数据获取

### 5. 分钟级交易综合测试
**验证功能：**
- ✅ 日线和分钟级交易周期支持（1d, 1m）
- ✅ 分钟级数据自动生成（从日线数据）
- ✅ 分钟级数据文件加载和处理
- ✅ 不同频率下的策略执行
- ✅ 分钟级投资组合状态管理
- ✅ 分钟级均线交易策略
- ✅ 分钟级交易信号生成和执行
- ✅ 日内交易逻辑和风险控制
- ✅ 分钟级持仓管理和盈亏计算
- ✅ 日线与分钟级策略效果对比

## 📈 测试覆盖

### 核心功能
- **引擎核心：** 数据加载、策略执行、投资组合管理
- **API注入：** 函数绑定、命名空间管理、log系统
- **交易系统：** 订单处理、资金管理、持仓跟踪

### 数据接口
- **基础数据：** 价格数据、历史数据、股票信息
- **财务数据：** 基本面指标、财务报表、财务比率
- **市场数据：** 实时报价、技术指标、多频率数据
- **分钟级数据：** 1m频率数据、日内交易支持

## 📋 维护建议

1. **每次代码变更后**运行完整测试套件
2. **新增功能时**添加相应测试用例
3. **发布前**确保所有测试通过
4. **定期更新**测试数据保持时效性

## 🚀 新功能特性

### 分钟级交易支持
ptradeSim现在支持多种交易频率，包括：

**支持的频率：**
- `1d` - 日线交易（默认）
- `1m` - 1分钟线交易

**使用方法：**
```python
# 创建分钟级回测引擎
engine = BacktestEngine(
    strategy_file='strategies/minute_strategy.py',
    data_path='data/sample_data.csv',
    start_date='2022-11-01',
    end_date='2022-11-03',
    initial_cash=1000000.0,
    frequency='1m'  # 1分钟频率
)
```

**自动数据生成：**
- 当使用分钟级频率但数据是日线时，系统会自动生成分钟级数据
- 支持从日线数据模拟生成OHLCV分钟级数据
- 保证数据的一致性和可重现性

**策略适配：**
- 分钟级策略支持盘前、盘中、盘后不同阶段的处理
- 支持分钟级技术指标计算和交易信号生成
- 提供详细的分钟级交易日志和状态跟踪

---

**测试结果：5/5 测试通过 (100%)**
