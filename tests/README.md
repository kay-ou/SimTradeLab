# ptradeSim 测试套件

这个文件夹包含了ptradeSim项目的完整测试套件，用于验证系统的各个组件是否正常工作。

## 🧪 测试文件

| 文件名 | 功能描述 | 测试重点 |
|--------|----------|----------|
| `test_api_injection.py` | API和日志注入测试 | 验证策略中API函数和log对象的正确注入 |
| `test_strategy_execution.py` | 策略执行流程测试 | 测试策略生命周期和完整回测流程 |

## 🚀 快速开始

### 一键运行所有测试（推荐）
```bash
# 使用测试运行器（自动检查前置条件和运行所有测试）
poetry run python run_tests.py
```

### 单独运行测试
```bash
# 进入项目根目录
cd /path/to/ptradeSim

# 运行API注入测试
poetry run python tests/test_api_injection.py

# 运行策略执行测试
poetry run python tests/test_strategy_execution.py
```

### 前置条件
确保以下文件存在：
- ✅ `data/sample_data.csv` - 测试数据文件
- ✅ `strategies/buy_and_hold.py` - 测试策略文件

## 📋 详细测试内容

### 🔌 API注入测试 (`test_api_injection.py`)

**测试目标**：验证ptradeSim引擎是否正确地将API函数和日志对象注入到策略中

**测试项目**：
- ✅ log对象注入验证
- ✅ 18个核心API函数的注入检查
- ✅ partial函数绑定验证
- ✅ 策略初始化过程测试
- ✅ API函数实际调用测试

**关键验证点**：
```python
# 验证的API函数包括：
get_Ashares, get_stock_status, get_stock_info, get_stock_name,
get_fundamentals, get_history, get_price, order, order_target,
order_value, set_universe, is_trade, get_research_path,
set_commission, set_limit_mode, get_initial_cash, get_num_of_positions
```

### 📈 策略执行测试 (`test_strategy_execution.py`)

**测试目标**：验证策略的完整执行流程和回测引擎的正确性

**测试项目**：
- ✅ 策略生命周期函数存在性检查
- ✅ 单日策略执行流程测试
- ✅ 投资组合状态更新验证
- ✅ 多日完整回测流程测试
- ✅ 交易逻辑正确性验证

**生命周期函数**：
```python
initialize()          # 策略初始化
before_trading_start() # 盘前处理
handle_data()         # 核心交易逻辑
after_trading_end()   # 盘后处理
```

## 📊 测试输出示例

### 成功输出
```
=== 测试完整的API和log注入机制 ===
1. 检查log对象注入:
   - 策略是否有log: True ✓
   - log对象类型: <class 'ptradeSim.api.Logger'>

2. 检查关键API函数注入:
   - get_Ashares: ✓ (partial绑定: ✓)
   - order: ✓ (partial绑定: ✓)
   ...

5. 测试API函数调用:
   ✓ get_Ashares(): ['STOCK_A', 'STOCK_B']
   ✓ get_stock_status(): 2 个结果
```

### 错误排查
如果测试失败，检查：
1. 📁 数据文件路径是否正确
2. 🔧 策略文件语法是否正确
3. 🐍 Python环境和依赖是否完整
4. 📝 日志输出中的具体错误信息

## 🛠️ 开发指南

### 添加新测试
1. 在相应的测试文件中添加新的测试函数
2. 遵循现有的测试模式和命名规范
3. 确保测试具有清晰的输出和错误处理

### 测试最佳实践
- 🎯 每个测试应该有明确的目标
- 📝 提供详细的测试输出信息
- 🔍 包含适当的错误处理和异常捕获
- ✅ 验证预期结果和实际结果

## 🔧 故障排除

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| `ModuleNotFoundError` | Python路径问题 | 确保在项目根目录运行测试 |
| `FileNotFoundError` | 数据文件缺失 | 检查 `data/sample_data.csv` 是否存在 |
| API函数调用失败 | 策略语法错误 | 检查策略文件中的API调用方式 |
| 投资组合状态异常 | 引擎初始化问题 | 检查引擎配置参数 |
