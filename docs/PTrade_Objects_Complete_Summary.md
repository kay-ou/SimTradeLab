# PTrade API 对象属性完整总结

## 对象属性详细分析

经过重新检查原始文档，我发现之前的对象属性总结确实不够完整。以下是从文档中提取的完整对象定义：

## 1. g - 全局对象

**功能**: 全局变量容器，用于存储用户的各类可被不同函数调用的全局数据

**使用场景**: 回测/交易

**属性**: 用户自定义属性，常见用法：
```python
g.security = "600570.SS"  # 股票池
g.count = 1               # 计数器
g.flag = 0               # 标志位
```

## 2. Context - 上下文对象

**功能**: 业务上下文对象，包含策略运行的完整环境信息

**使用场景**: 回测/交易

**主要属性**:
- `capital_base` - 起始资金
- `previous_date` - 前一个交易日  
- `sim_params` - SimulationParameters对象
  - `capital_base` - 起始资金
  - `data_frequency` - 数据频率
- `portfolio` - 账户信息（Portfolio对象）
- `initialized` - 是否执行初始化
- `slippage` - 滑点（VolumeShareSlippage对象）
  - `volume_limit` - 成交限量
  - `price_impact` - 价格影响力
- `commission` - 佣金费用（Commission对象）
  - `tax` - 印花税费率
  - `cost` - 佣金费率
  - `min_trade_cost` - 最小佣金
- `blotter` - Blotter对象（记录）
  - `current_dt` - 当前单位时间的开始时间（datetime.datetime对象，北京时间）
- `recorded_vars` - 收益曲线值

## 3. SecurityUnitData对象

**功能**: 一个单位时间内的股票数据，是一个字典，根据sid获取BarData对象数据

**使用场景**: 回测/交易

**基本属性**:
- `dt` - 时间
- `open` - 时间段开始时价格
- `close` - 时间段结束时价格  
- `price` - 结束时价格
- `low` - 最低价
- `high` - 最高价
- `volume` - 成交的股票数量
- `money` - 成交的金额

## 4. Portfolio对象

**功能**: 账户当前的资金、标的信息，即所有标的操作仓位的信息汇总

**使用场景**: 回测/交易

### 股票账户属性 (8个):
- `cash` - 当前可用资金（不包含冻结资金）
- `positions` - 当前持有的标的（包含不可卖出的标的），dict类型，key是标的代码，value是Position对象
- `portfolio_value` - 当前持有的标的和现金的总价值
- `positions_value` - 持仓价值
- `capital_used` - 已使用的现金
- `returns` - 当前的收益比例，相对于初始资金
- `pnl` - 当前账户总资产-初始账户总资产
- `start_date` - 开始时间

### 期货账户属性 (8个):
- `cash` - 当前可用资金（不包含冻结资金）
- `positions` - 当前持有的标的（包含不可卖出的标的），dict类型，key是标的代码，value是Position对象
- `portfolio_value` - 当前持有的标的和现金的总价值
- `positions_value` - 持仓价值
- `capital_used` - 已使用的现金
- `returns` - 当前的收益比例，相对于初始资金
- `pnl` - 当前账户总资产-初始账户总资产
- `start_date` - 开始时间

### 期权账户属性 (9个):
- `cash` - 当前可用资金（不包含冻结资金）
- `positions` - 当前持有的标的（包含不可卖出的标的），dict类型，key是标的代码，value是Position对象
- `portfolio_value` - 当前持有的标的和现金的总价值
- `positions_value` - 持仓价值
- `returns` - 当前的收益比例，相对于初始资金
- `pnl` - 当前账户总资产-初始账户总资产
- `margin` - 保证金
- `risk_degree` - 风险度
- `start_date` - 开始时间

## 5. Position对象

**功能**: 持有的某个标的的信息

**使用场景**: 回测/交易

**注意**: 期货业务持仓分为多头仓(long)、空头仓(short)；期权业务持仓分为权利仓(long)、义务仓(short)、备兑仓(covered)

### 股票账户属性:
- `sid` - 标的代码
- `enable_amount` - 可用数量
- `amount` - 总持仓数量
- `last_sale_price` - 最新价格
- `cost_basis` - 持仓成本价格
- `today_amount` - 今日开仓数量（且仅回测有效）
- `business_type` - 持仓类型

### 期货账户属性:
- `sid` - 标的代码
- `short_enable_amount` - 空头仓可用数量
- `long_enable_amount` - 多头仓可用数量
- `today_short_amount` - 空头仓今仓数量
- `today_long_amount` - 多头仓今仓数量
- `long_cost_basis` - 多头仓持仓成本
- `short_cost_basis` - 空头仓持仓成本
- `long_amount` - 多头仓总持仓量
- `short_amount` - 空头仓总持仓量
- `long_pnl` - 多头仓浮动盈亏
- `short_pnl` - 空头仓浮动盈亏
- `amount` - 总持仓数量
- `enable_amount` - 可用数量
- `last_sale_price` - 最新价格
- `business_type` - 持仓类型
- `delivery_date` - 交割日，期货使用
- `margin_rate` - 保证金比例
- `contract_multiplier` - 合约乘数

### 期权账户属性:
- `sid` - 标的代码
- `short_enable_amount` - 义务仓可用数量
- `long_enable_amount` - 权利仓可用数量
- `covered_enable_amount` - 备兑仓可用数量
- `short_cost_basis` - 义务仓持仓成本
- `long_cost_basis` - 权利仓持仓成本
- `covered_cost_basis` - 备兑仓持仓成本
- `short_amount` - 义务仓总持仓量
- `long_amount` - 权利仓总持仓量
- `covered_amount` - 备兑仓总持仓量
- `short_pnl` - 义务仓浮动盈亏
- `long_pnl` - 权利仓浮动盈亏
- `covered_pnl` - 备兑仓浮动盈亏
- `last_sale_price` - 最新价格
- `margin` - 保证金
- `exercise_date` - 行权日，期权使用
- `business_type` - 持仓类型

## 6. Order对象

**功能**: 买卖订单信息

**使用场景**: 回测/交易

**主要属性**:
- `id` - 订单号
- `dt` - 订单产生时间（datetime.datetime类型）
- `limit` - 指定价格
- `symbol` - 标的代码（注意：标的代码尾缀为四位，上证为XSHG，深圳为XSHE）
- `amount` - 下单数量，买入是正数，卖出是负数

## 对象属性数量统计

| 对象 | 基础属性数量 | 扩展属性数量 | 总计 |
|------|-------------|-------------|------|
| g | 用户自定义 | 用户自定义 | 灵活 |
| Context | 7个主要属性 | 15+子属性 | 22+ |
| SecurityUnitData | 7个基本属性 | 0 | 7 |
| Portfolio (股票) | 8个属性 | 0 | 8 |
| Portfolio (期货) | 8个属性 | 0 | 8 |
| Portfolio (期权) | 9个属性 | 0 | 10 |
| Position (股票) | 7个属性 | 0 | 7 |
| Position (期货) | 18个属性 | 0 | 18 |
| Position (期权) | 17个属性 | 0 | 17 |
| Order | 5个属性 | 0 | 5 |

## 说明

您是对的，我之前的总结确实对象属性数量对不上。重新检查后发现：

1. **Context对象**: 不只是5个属性，而是有22+个属性（包括嵌套的子对象属性）
2. **Portfolio对象**: 根据业务类型不同，属性数量也不同：
   - 股票账户：8个属性
   - 期货账户：8个属性  
   - 期权账户：9个属性（多了margin和risk_degree）
3. **Position对象**: 根据业务类型不同，属性数量差异很大：
   - 股票账户：7个属性
   - 期货账户：18个属性  
   - 期权账户：17个属性
4. **SecurityUnitData对象**: 7个基本行情属性
5. **Order对象**: 5个订单基础属性

感谢您的纠正！Portfolio对象确实有8个基础属性（股票账户），而不是我之前说的4个。这个更正后的总结应该更准确地反映了PTrade API中各个对象的完整属性结构。