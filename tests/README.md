# 测试文件说明

这个文件夹包含了ptradeSim项目的测试和调试文件。

## 文件结构

### 测试文件
- `test_api_injection.py` - 测试API和log对象注入机制
- `test_strategy_execution.py` - 测试策略执行流程

### 运行方法

```bash
# 运行API注入测试
poetry run python tests/test_api_injection.py

# 运行策略执行测试
poetry run python tests/test_strategy_execution.py
```

## 测试内容

### API注入测试 (`test_api_injection.py`)
- 检查log对象是否正确注入到策略中
- 验证所有API函数是否正确绑定
- 测试策略初始化过程
- 验证API函数调用是否正常

### 策略执行测试 (`test_strategy_execution.py`)
- 测试策略各个生命周期函数的执行
- 验证交易逻辑是否正常
- 检查投资组合状态更新
- 测试完整的回测流程

## 注意事项

1. 运行测试前确保数据文件存在：`data/sample_data.csv`
2. 确保策略文件存在：`strategies/buy_and_hold.py`
3. 使用poetry环境运行测试以确保依赖正确
4. 测试输出包含详细的执行信息，便于调试
