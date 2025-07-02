# ptradeSim

ptradeSim 是一个轻量级 Python 开源项目，旨在模拟 PTrade 的策略框架与事件驱动机制。它帮助用户在本地环境中编写、加载并运行量化交易策略，支持常用接口如 get_history()、order()、context.portfolio.cash 等，并提供完整的策略生命周期流程与交易账户仿真，适用于策略研究、教学演示与快速原型验证。

---

## 核心功能

- **轻量级框架**: 核心代码简洁，易于理解和扩展。
- **事件驱动**: 基于事件循环机制，模拟真实交易环境。
- **策略仿真**: 支持完整的策略生命周期管理，从初始化到盘后处理。
- **交易模拟**: 内置账户与持仓管理，自动处理订单、成交和资金变化。
- **常用 API**: 提供 `get_history()`, `order()` 等常用函数，与主流平台保持一致。
- **本地运行**: 无需连接外部服务，方便快速进行策略的开发与验证。

---

## 安装指南

**通过 pip 安装 (推荐)**
```bash
pip install ptradeSim
```

**从源码安装**
```bash
git clone https://github.com/your-username/ptradeSim.git
cd ptradeSim
pip install .
```

---

## 快速入门

以下是一个简单的双均线策略示例 (`my_strategy.py`)：

```python
# my_strategy.py

def initialize(context):
    """策略初始化"""
    context.securities = ['000001.XSHE']
    context.short_ma = 5
    context.long_ma = 20

def handle_data(context, data):
    """每个交易日的策略逻辑"""
    hist = data.get_history(context.securities, ['close'], context.long_ma, '1d')
    
    if hist is None or len(hist) < context.long_ma:
        return

    ma_short = hist['close'][-context.short_ma:].mean()
    ma_long = hist['close'].mean()

    # 金叉：买入
    if ma_short > ma_long and context.portfolio.positions[context.securities].amount == 0:
        context.order(context.securities, 100)
        print(f"INFO: Buying 100 shares of {context.securities}")

    # 死叉：卖出
    elif ma_short < ma_long and context.portfolio.positions[context.securities].amount > 0:
        context.order_target(context.securities, 0)
        print(f"INFO: Selling all shares of {context.securities}")

```

**运行回测:**

```bash
# 假设 ptradeSim 提供一个命令行工具来运行回测
ptradeSim run --strategy my_strategy.py --start 2023-01-01 --end 2023-12-31 --cash 100000
```

---

## API 参考

- `context.order(security, amount)`: 按指定股数下单。
- `context.order_target(security, amount)`: 将指定证券的持仓调整至目标股数。
- `data.get_history(security, fields, count, frequency)`: 获取历史行情数据。
- `context.portfolio.cash`: 获取当前账户的可用现金。
- `context.portfolio.positions`: 获取当前持仓信息。

---

## 贡献指南

我们欢迎任何形式的贡献！如果您想为 ptradeSim 做出贡献，请遵循以下步骤：

1.  Fork 本项目。
2.  创建您的特性分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  推送到分支 (`git push origin feature/AmazingFeature`)。
5.  提交一个 Pull Request。

---

## 许可证

本项目采用 [MIT](LICENSE) 许可证。
