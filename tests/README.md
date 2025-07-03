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

## 📈 测试覆盖

### 核心功能
- **引擎核心：** 数据加载、策略执行、投资组合管理
- **API注入：** 函数绑定、命名空间管理、log系统
- **交易系统：** 订单处理、资金管理、持仓跟踪

### 数据接口
- **基础数据：** 价格数据、历史数据、股票信息
- **财务数据：** 基本面指标、财务报表、财务比率
- **市场数据：** 实时报价、技术指标、多频率数据

### 质量保证
- **数据一致性：** 相同输入产生相同输出
- **错误处理：** 优雅处理异常和无效输入
- **性能验证：** 数据获取<1ms，指标计算<100ms

## 🔧 故障排除

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError` | 确保在项目根目录运行测试 |
| `FileNotFoundError` | 检查 `data/sample_data.csv` 是否存在 |
| API函数调用失败 | 检查策略文件语法 |
| 投资组合状态异常 | 检查引擎配置参数 |

## 📋 维护建议

1. **每次代码变更后**运行完整测试套件
2. **新增功能时**添加相应测试用例
3. **发布前**确保所有测试通过
4. **定期更新**测试数据保持时效性

---

**测试结果：4/4 测试通过 (100%)**
