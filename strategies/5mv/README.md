# 5MV 交易策略

## 策略描述 (Strategy Description)

本策略是 `shadow` 策略框架与 `5mv` 策略核心交易逻辑的结合体。它旨在利用 `shadow` 策略成熟的参数管理、动态资金调整、风险控制（仓位大小、动态止损）及数据处理功能，并在此基础上融入 `5mv` 策略独特的信号生成规则，以期在市场中捕捉交易机会。

## 核心功能 (Core Features)

### 股票筛选条件 (Stock Screening Criteria)

本策略在每日交易开始前，会从A股市场中筛选出符合以下条件的股票：

1.  **非ST、非退市股票**：排除特殊处理和已退市的股票。
2.  **上市时间**: 上市时间大于 `g.min_listed_days` (默认为365天)。
3.  **最低股价**: 收盘价高于 `g.min_price` (默认为2.0元)。
4.  **市值范围**: 总市值在 `g.market_cap_min` (默认为10亿) 到 `g.market_cap_max` (默认为200亿) 之间。
5.  **换手率**: 换手率在 `g.turnover_rate_min` (默认为10%) 到 `g.turnover_rate_max` (默认为30%) 之间。
6.  **5MV 买入信号**:
    *   当前收盘价高于5日VWAP (成交量加权平均价) 的 `g.ma_discount_rate` (默认为0.95) 倍 (此参数在5MV策略中作为关键的“魔法数字”用于买入信号判断)。
    *   前一日收盘价低于5日均线。
    *   当前收盘价高于20日均线。

### 交易规则 (Trading Rules)

本策略结合了 `shadow` 策略的风险控制机制和 `5mv` 的入场/离场信号：

1.  **选股**: 从符合上述条件的股票中，按市值升序选择最多 `g.max_stock_num` (默认为2) 支股票进行交易。
2.  **持仓周期**: 单只股票最大持有 `g.max_hold_days` (默认为12) 天。
3.  **止损**: 股价较成本价下跌 `g.stop_loss_rate` (默认为-7%) 时止损。
4.  **止盈/追踪止损**:
    *   若在最大持仓天数内涨幅未超过 `g.take_profit_rate` (默认为20%)，则持有到期卖出。
    *   若涨幅超过 `g.take_profit_rate` (默认为20%)，则继续持有，直到股价从阶段性高点回撤 `g.drawdown_rate` (默认为-3%) 时卖出。
5.  **5MV 离场规则**:
    *   收盘价低于20日均线时卖出。
    *   收盘价低于5日VWAP的 `g.ma_discount_rate` 倍时卖出。

### 资金管理 (Capital Management)

策略包含动态资金管理机制，以应对市场波动：

-   **回撤增资**: 当策略总资产较历史峰值回撤达到 `g.drawdown_threshold_for_capital_increase` (默认为初始资金的7%/2) 时，从待用资金中按比例 (`g.capital_increase_ratio_on_drawdown`, 默认为初始资金的60%/2) 增加投入资金。
-   **回升减资**: 当策略总资产较历史谷值回升达到 `g.rebound_threshold_for_capital_reduction` (默认为初始资金的8%/2) 时，将部分资金 (基于初始资金的 `g.capital_reduction_ratio_on_rebound`, 默认为初始资金的50%/2) 转为待用资金。

## 状态持久化 (State Persistence)

为了确保策略在意外中断并重启后能够恢复之前的运行状态，所有关键的策略状态数据都被统一封装在 `g.state` 字典中，并持久化到名为 `5mv_strategy_state.pkl` 的单个文件中。该文件包含以下核心状态：

-   `cash`: 可用现金
-   `standby_cash`: 待用资金
-   `stock_info_cache`: 股票上市日期等基本信息的缓存
-   `stock_name_cache`: 股票名称的缓存，用于减少API调用
-   `hold_days`: 记录持仓股票的持有天数
-   `highest_prices`: 记录持仓股票自买入以来的最高价
-   `portfolio_values`: 记录每日的策略组合总价值历史序列
-   `peak_since_last_reduction`: 自上次减资后的资产峰值，用于判断增资
-   `valley_since_last_increase`: 自上次增资后的资产谷值，用于判断减资

**注意**: 这个统一的持久化文件 (`5mv_strategy_state.pkl`) 仅在**回测模式 (Backtesting Mode)** 下运行时才会被清空。在实盘模式 (Live Trading Mode) 下，策略会尝试从该文件中加载所有数据以恢复状态。

## 核心参数 (Core Parameters)

这些参数在策略的 `initialize` 函数中定义，并影响策略行为：

-   `g.isGuoSheng`: 是否为国盛证券环境 (默认: `False`)
-   `g.max_stock_num`: 最大持仓股票数量 (默认: 2)
-   `g.max_hold_days`: 单只股票最大持有天数 (默认: 12)
-   `g.stop_loss_rate`: 止损百分比 (默认: -7, 表示下跌7%)
-   `g.take_profit_rate`: 基础止盈百分比 (默认: 20)
-   `g.drawdown_rate`: 从高点回撤卖出的百分比 (默认: -3, 表示回撤3%)
-   `g.initial_cash_divisor`: 初始资金使用比例的除数 (默认: 2)
-   `g.min_listed_days`: 最小上市天数 (默认: 365)
-   `g.min_price`: 最低股价 (默认: 2.0)
-   `g.ma_discount_rate`: MA折扣率，用于5日VWAP判断 (默认: 0.95)
-   `g.market_cap_min`: 最小市值 (默认: 10亿)
-   `g.market_cap_max`: 最大市值 (默认: 200亿)
-   `g.turnover_rate_min`: 换手率最小值 (默认: 10)
-   `g.turnover_rate_max`: 换手率最大值 (默认: 30)
-   `g.base_initial_cash`: 初始基础现金 (通过 `get_initial_cash` 计算，上限30万)
-   `g.drawdown_threshold_for_capital_increase`: 触发回撤增资的阈值 (默认: 0.07 除以 `g.initial_cash_divisor`)
-   `g.capital_increase_ratio_on_drawdown`: 回撤增资时增加的资金比例 (默认: 0.60 除以 `g.initial_cash_divisor`)
-   `g.rebound_threshold_for_capital_reduction`: 触发谷底回升减资的阈值 (默认: 0.08 除以 `g.initial_cash_divisor`)
-   `g.capital_reduction_ratio_on_rebound`: 谷底回升减资时减少的资金比例 (默认: 0.50 除以 `g.initial_cash_divisor`)
-   `g.commission_ratio`: 交易佣金比例 (默认: 0.00015)
-   `g.min_commission`: 最低交易佣金 (默认: 5.0)
-   `g.stamp_duty_rate`: 印花税率 (默认: 0.0005)
-   `g.transfer_fee_rate`: 过户费率 (默认: 0.00001)

## 使用方式 (Usage)

### 在Ptrade平台运行
本策略设计为在 Ptrade 平台运行。将其加载到 Ptrade 环境中即可根据市场数据进行回测或实盘交易。

### 本地开发

#### 文件结构
```
strategies/5mv/
├── 5mv_strategy.py      # 主策略文件
└── README.md           # 说明文档
```

## 主要优化特性 (Key Optimizations)

### 1. 动态持仓管理
- 根据当前可用资金动态计算最大持仓数量
- 每个持仓最小金额：10,000元
- 动态调整仓位大小以适应资金变化

### 2. 统一股票状态缓存
- 每日更新一次股票状态（ST、停牌、退市）
- 避免重复API调用，提高性能
- 自动过滤异常状态股票

### 3. 批量数据预获取
- 批量获取股票基本信息和名称
- 智能缓存管理，防止内存溢出
- 减少网络请求次数

### 4. 科创板股票支持
- 自动识别科创板股票（688开头）
- 最小200股购买限制
- 资金不足时自动跳过

### 5. 停牌股票处理
- 买入时跳过停牌股票
- 卖出时等待复牌，避免无效订单

### 6. 性能优化
- 简化过度健壮的错误处理
- 优化缓存清理机制
- 减少不必要的计算开销

## 优势 (Advantages)

-   **结合优势**: 融合了 `shadow` 策略的稳健资金管理和 `5mv` 策略的特定交易信号，旨在实现更均衡的风险收益。
-   **动态资金管理**: 自动根据策略表现进行增资或减资，优化资金利用效率和风险控制。
-   **状态持久化**: 确保在回测或实盘中断后能够恢复策略状态，提高运行的连续性和可靠性。
-   **多重止盈止损**: 结合固定止损、追踪止损和基于均线的离场规则，全面控制交易风险。

## 局限性 (Limitations)

-   **参数敏感性**: 策略表现可能对 `initialize` 函数中定义的各项参数（如 `g.max_stock_num`, `g.stop_loss_rate` 等）敏感，需要根据市场环境进行调优。
-   **数据依赖**: 策略的有效性依赖于历史数据的准确性和完整性，特别是VWAP和均线计算。
-   **市场适应性**: 5MV策略主要基于量价关系和均线，可能在某些极端市场条件下（如剧烈震荡、流动性枯竭）表现不佳。
-   **回测与实盘差异**: 回测结果可能与实盘表现存在差异，需注意滑点、交易费用、数据延迟等因素。