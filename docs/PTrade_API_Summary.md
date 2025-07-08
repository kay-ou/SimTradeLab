# PTrade API 完整接口总结

## 策略生命周期函数 (7个)

### 核心生命周期函数
- **initialize(context)** - 策略初始化（必选）*[回测/交易]*
- **handle_data(context, data)** - 主策略逻辑（必选）*[回测/交易]*
- **before_trading_start(context, data)** - 盘前处理（可选）*[回测/交易]*
- **after_trading_end(context, data)** - 盘后处理（可选）*[回测/交易]*
- **tick_data(context, data)** - tick级别处理（可选）*[仅交易]*

### 事件回调函数
- **on_order_response(context, order)** - 委托回报（可选）*[仅交易]*
- **on_trade_response(context, trade)** - 成交回报（可选）*[仅交易]*

## 设置函数 (12个)

### 基础设置
- **set_universe(securities)** - 设置股票池 *[回测/交易]*
- **set_benchmark(benchmark)** - 设置基准 *[回测/交易]*
- **set_commission(commission)** - 设置佣金费率 *[仅回测]*
- **set_fixed_slippage(slippage)** - 设置固定滑点 *[仅回测]*
- **set_slippage(slippage)** - 设置滑点 *[仅回测]*
- **set_volume_ratio(ratio)** - 设置成交比例 *[仅回测]*
- **set_limit_mode(mode)** - 设置回测成交数量限制模式 *[仅回测]*
- **set_yesterday_position(positions)** - 设置底仓 *[仅回测]*
- **set_parameters(params)** - 设置策略配置参数 *[回测/交易]*

### 定时函数
- **run_daily(func, time)** - 按日周期处理 *[回测/交易]*
- **run_interval(func, interval)** - 按设定周期处理 *[仅交易]*

### 期货设置
- **set_future_commission(commission)** - 设置期货手续费 *[仅回测]*
- **set_margin_rate(security, rate)** - 设置期货保证金比例 *[回测/交易]*

## 获取信息函数 (50+个)

### 基础信息 (3个)
- **get_trading_day(date, offset=0)** - 获取交易日期 *[研究/回测/交易]*
- **get_all_trades_days()** - 获取全部交易日期 *[研究/回测/交易]*
- **get_trade_days(start_date, end_date)** - 获取指定范围交易日期 *[研究/回测/交易]*

### 市场信息 (3个)
- **get_market_list()** - 获取市场列表 *[研究/回测/交易]*
- **get_market_detail(market)** - 获取市场详细信息 *[研究/回测/交易]*
- **get_cb_list()** - 获取可转债市场代码表 *[仅交易]*

### 行情信息 (10个)
- **get_history(count, frequency, field, security_list, fq, include, fill, is_dict, start_date, end_date)** - 获取历史行情 *[回测/交易]*
- **get_price(security, start_date, end_date, frequency, fields, count)** - 获取历史数据 *[研究/回测/交易]*
- **get_individual_entrust(security_list)** - 获取逐笔委托行情 *[仅交易]*
- **get_individual_transaction(security_list)** - 获取逐笔成交行情 *[仅交易]*
- **get_tick_direction(security_list)** - 获取分时成交行情 *[仅交易]*
- **get_sort_msg(market, category, sort_type)** - 获取板块、行业的涨幅排名 *[仅交易]*
- **get_etf_info(etf_code)** - 获取ETF信息 *[仅交易]*
- **get_etf_stock_info(etf_code)** - 获取ETF成分券信息 *[仅交易]*
- **get_gear_price(security_list)** - 获取指定代码的档位行情价格 *[仅交易]*
- **get_snapshot(security_list)** - 获取行情快照 *[仅交易]*
- **get_cb_info(cb_code)** - 获取可转债基础信息 *[研究/交易]*

### 股票信息 (12个)
- **get_stock_name(security_list)** - 获取股票名称 *[研究/回测/交易]*
- **get_stock_info(security_list)** - 获取股票基础信息 *[研究/回测/交易]*
- **get_stock_status(security_list)** - 获取股票状态信息 *[研究/回测/交易]*
- **get_stock_exrights(security_list)** - 获取股票除权除息信息 *[研究/回测/交易]*
- **get_stock_blocks(security_list)** - 获取股票所属板块信息 *[研究/回测/交易]*
- **get_index_stocks(index_code)** - 获取指数成份股 *[研究/回测/交易]*
- **get_etf_stock_list(etf_code)** - 获取ETF成分券列表 *[仅交易]*
- **get_industry_stocks(industry_code)** - 获取行业成份股 *[研究/回测/交易]*
- **get_fundamentals(stocks, table, fields, date)** - 获取财务数据信息 *[研究/回测/交易]*
- **get_Ashares(date)** - 获取指定日期A股代码列表 *[研究/回测/交易]*
- **get_etf_list()** - 获取ETF代码 *[仅交易]*
- **get_ipo_stocks()** - 获取当日IPO申购标的 *[仅交易]*

### 其他信息 (8个)
- **get_trades_file()** - 获取对账数据文件 *[仅回测]*
- **convert_position_from_csv(file_path)** - 获取设置底仓的参数列表 *[仅回测]*
- **get_user_name()** - 获取登录终端的资金账号 *[回测/交易]*
- **get_deliver(start_date, end_date)** - 获取历史交割单信息 *[仅交易]*
- **get_fundjour(start_date, end_date)** - 获取历史资金流水信息 *[仅交易]*
- **get_research_path()** - 获取研究路径 *[回测/交易]*
- **get_trade_name()** - 获取交易名称 *[仅交易]*

## 交易相关函数 (30+个)

### 股票交易函数 (11个)
- **order(security, amount, limit_price=None)** - 按数量买卖 *[回测/交易]*
- **order_target(security, target_amount)** - 指定目标数量买卖 *[回测/交易]*
- **order_value(security, value)** - 指定目标价值买卖 *[回测/交易]*
- **order_target_value(security, target_value)** - 指定持仓市值买卖 *[回测/交易]*
- **order_market(security, amount)** - 按市价进行委托 *[仅交易]*
- **ipo_stocks_order(amount_per_stock=10000)** - 新股一键申购 *[仅交易]*
- **after_trading_order(security, amount, limit_price)** - 盘后固定价委托 *[仅交易]*
- **after_trading_cancel_order(order_id)** - 盘后固定价委托撤单 *[仅交易]*
- **etf_basket_order(etf_code, amount, side)** - ETF成分券篮子下单 *[仅交易]*
- **etf_purchase_redemption(etf_code, amount, side)** - ETF基金申赎接口 *[仅交易]*
- **get_positions(security_list)** - 获取多支股票持仓信息 *[回测/交易]*

### 公共交易函数 (11个)
- **order_tick(security, amount, limit_price, tick_type)** - tick行情触发买卖 *[仅交易]*
- **cancel_order(order_id)** - 撤单 *[回测/交易]*
- **cancel_order_ex(order_id)** - 撤单扩展 *[仅交易]*
- **debt_to_stock_order(cb_code, amount)** - 债转股委托 *[仅交易]*
- **get_open_orders(security=None)** - 获取未完成订单 *[回测/交易]*
- **get_order(order_id)** - 获取指定订单 *[回测/交易]*
- **get_orders(security=None)** - 获取全部订单 *[回测/交易]*
- **get_all_orders()** - 获取账户当日全部订单 *[仅交易]*
- **get_trades(security=None)** - 获取当日成交订单 *[回测/交易]*
- **get_position(security)** - 获取持仓信息 *[回测/交易]*

## 融资融券专用函数 (19个)

### 融资融券交易类函数 (7个)
- **margin_trade(security, amount, limit_price=None)** - 担保品买卖 *[两融回测/两融交易]*
- **margincash_open(security, amount, limit_price=None)** - 融资买入 *[仅两融交易]*
- **margincash_close(security, amount, limit_price=None)** - 卖券还款 *[仅两融交易]*
- **margincash_direct_refund(amount)** - 直接还款 *[仅两融交易]*
- **marginsec_open(security, amount, limit_price=None)** - 融券卖出 *[仅两融交易]*
- **marginsec_close(security, amount, limit_price=None)** - 买券还券 *[仅两融交易]*
- **marginsec_direct_refund(security, amount)** - 直接还券 *[仅两融交易]*

### 融资融券查询类函数 (12个)
- **get_margincash_stocks()** - 获取融资标的列表 *[仅两融交易]*
- **get_marginsec_stocks()** - 获取融券标的列表 *[仅两融交易]*
- **get_margin_contract()** - 合约查询 *[仅两融交易]*
- **get_margin_contractreal()** - 实时合约查询 *[仅两融交易]*
- **get_margin_assert()** - 信用资产查询 *[仅两融交易]*
- **get_assure_security_list()** - 担保券查询 *[仅两融交易]*
- **get_margincash_open_amount(security)** - 融资标的最大可买数量查询 *[仅两融交易]*
- **get_margincash_close_amount(security)** - 卖券还款标的最大可卖数量查询 *[仅两融交易]*
- **get_marginsec_open_amount(security)** - 融券标的最大可卖数量查询 *[仅两融交易]*
- **get_marginsec_close_amount(security)** - 买券还券标的最大可买数量查询 *[仅两融交易]*
- **get_margin_entrans_amount(security)** - 现券还券数量查询 *[仅两融交易]*
- **get_enslo_security_info(security)** - 融券头寸信息查询 *[仅两融交易]*

## 期货专用函数 (7个)

### 期货交易类函数 (4个)
- **buy_open(security, amount, limit_price=None)** - 开多 *[回测/交易]*
- **sell_close(security, amount, limit_price=None)** - 多平 *[回测/交易]*
- **sell_open(security, amount, limit_price=None)** - 空开 *[回测/交易]*
- **buy_close(security, amount, limit_price=None)** - 空平 *[回测/交易]*

### 期货查询类函数 (2个)
- **get_margin_rate(security)** - 获取用户设置的保证金比例 *[仅回测]*
- **get_instruments()** - 获取合约信息 *[回测/交易]*

### 期货设置类函数 (1个)
- **set_future_commission(commission)** - 设置期货手续费 *[仅回测]*

## 期权专用函数 (15个)

### 期权查询类函数 (6个)
- **get_opt_objects()** - 获取期权标的列表 *[研究/回测/交易]*
- **get_opt_last_dates(underlying)** - 获取期权标的到期日列表 *[研究/回测/交易]*
- **get_opt_contracts(underlying, last_date)** - 获取期权标的对应合约列表 *[研究/回测/交易]*
- **get_contract_info(contract)** - 获取期权合约信息 *[研究/回测/交易]*
- **get_covered_lock_amount(underlying)** - 获取期权标的可备兑锁定数量 *[仅交易]*
- **get_covered_unlock_amount(underlying)** - 获取期权标的允许备兑解锁数量 *[仅交易]*

### 期权交易类函数 (7个)
- **buy_open(security, amount, limit_price=None)** - 权利仓开仓 *[仅交易]*
- **sell_close(security, amount, limit_price=None)** - 权利仓平仓 *[仅交易]*
- **sell_open(security, amount, limit_price=None)** - 义务仓开仓 *[仅交易]*
- **buy_close(security, amount, limit_price=None)** - 义务仓平仓 *[仅交易]*
- **open_prepared(security, amount, limit_price=None)** - 备兑开仓 *[仅交易]*
- **close_prepared(security, amount, limit_price=None)** - 备兑平仓 *[仅交易]*
- **option_exercise(security, amount)** - 行权 *[仅交易]*

### 期权其他函数 (2个)
- **option_covered_lock(security, amount)** - 期权标的备兑锁定 *[仅交易]*
- **option_covered_unlock(security, amount)** - 期权标的备兑解锁 *[仅交易]*

## 计算函数 (4个)

### 技术指标计算函数
- **get_MACD(close, short=12, long=26, m=9)** - 异同移动平均线 *[回测/交易]*
- **get_KDJ(high, low, close, n=9, m1=3, m2=3)** - 随机指标 *[回测/交易]*
- **get_RSI(close, n=6)** - 相对强弱指标 *[回测/交易]*
- **get_CCI(high, low, close, n=14)** - 顺势指标 *[回测/交易]*

## 其他函数 (7个)

### 工具函数
- **log** - 日志记录 (支持 debug, info, warning, error, critical 级别) *[回测/交易]*
- **is_trade()** - 业务代码场景判断 *[回测/交易]*
- **check_limit(security, query_date=None)** - 代码涨跌停状态判断 *[研究/回测/交易]*
- **send_email(send_email_info, get_email_info, smtp_code, info, path, subject)** - 发送邮箱信息 *[仅交易]*
- **send_qywx(corp_id, secret, agent_id, info, path, toparty, touser, totag)** - 发送企业微信信息 *[仅交易]*
- **permission_test(account=None, end_date=None)** - 权限校验 *[仅交易]*
- **create_dir(user_path=None)** - 创建文件路径 *[仅交易]*

## 对象定义 (11个核心对象)

### 1. g - 全局对象
**功能**: 全局变量容器，用于存储用户的各类可被不同函数调用的全局数据
**使用场景**: 回测/交易
**属性**: 用户自定义属性，常见用法：
```python
g.security = "600570.SS"  # 股票池
g.count = 1               # 计数器
g.flag = 0               # 标志位
```

### 2. Context - 上下文对象
**功能**: 业务上下文对象，包含策略运行的完整环境信息
**使用场景**: 回测/交易
**主要属性**:
- `capital_base` - 起始资金
- `previous_date` - 前一个交易日  
- `sim_params` - SimulationParameters对象
- `portfolio` - 账户信息（Portfolio对象）
- `initialized` - 是否执行初始化
- `slippage` - 滑点（VolumeShareSlippage对象）
- `commission` - 佣金费用（Commission对象）
- `blotter` - Blotter对象（记录）
- `recorded_vars` - 收益曲线值

### 3. SecurityUnitData对象
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

### 4. Portfolio对象
**功能**: 账户当前的资金、标的信息，即所有标的操作仓位的信息汇总
**使用场景**: 回测/交易

#### 股票账户属性 (8个):
- `cash` - 当前可用资金（不包含冻结资金）
- `positions` - 当前持有的标的（包含不可卖出的标的），dict类型，key是标的代码，value是Position对象
- `portfolio_value` - 当前持有的标的和现金的总价值
- `positions_value` - 持仓价值
- `capital_used` - 已使用的现金
- `returns` - 当前的收益比例，相对于初始资金
- `pnl` - 当前账户总资产-初始账户总资产
- `start_date` - 开始时间

#### 期货账户属性 (8个):
- `cash` - 当前可用资金（不包含冻结资金）
- `positions` - 当前持有的标的（包含不可卖出的标的），dict类型，key是标的代码，value是Position对象
- `portfolio_value` - 当前持有的标的和现金的总价值
- `positions_value` - 持仓价值
- `capital_used` - 已使用的现金
- `returns` - 当前的收益比例，相对于初始资金
- `pnl` - 当前账户总资产-初始账户总资产
- `start_date` - 开始时间

#### 期权账户属性 (9个):
- `cash` - 当前可用资金（不包含冻结资金）
- `positions` - 当前持有的标的（包含不可卖出的标的），dict类型，key是标的代码，value是Position对象
- `portfolio_value` - 当前持有的标的和现金的总价值
- `positions_value` - 持仓价值
- `returns` - 当前的收益比例，相对于初始资金
- `pnl` - 当前账户总资产-初始账户总资产
- `margin` - 保证金
- `risk_degree` - 风险度
- `start_date` - 开始时间

### 5. Position对象
**功能**: 持有的某个标的的信息
**使用场景**: 回测/交易
**注意**: 期货业务持仓分为多头仓(long)、空头仓(short)；期权业务持仓分为权利仓(long)、义务仓(short)、备兑仓(covered)

#### 股票账户属性 (7个):
- `sid` - 标的代码
- `enable_amount` - 可用数量
- `amount` - 总持仓数量
- `last_sale_price` - 最新价格
- `cost_basis` - 持仓成本价格
- `today_amount` - 今日开仓数量（且仅回测有效）
- `business_type` - 持仓类型

#### 期货账户属性 (18个):
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
- `delivery_date` - 交割日
- `margin_rate` - 保证金比例
- `contract_multiplier` - 合约乘数
- `business_type` - 持仓类型

#### 期权账户属性 (17个):
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
- `exercise_date` - 行权日
- `business_type` - 持仓类型

### 6. Order对象
**功能**: 买卖订单信息
**使用场景**: 回测/交易
**主要属性**:
- `id` - 订单号
- `dt` - 订单产生时间（datetime.datetime类型）
- `limit` - 指定价格
- `symbol` - 标的代码（注意：标的代码尾缀为四位，上证为XSHG，深圳为XSHE）
- `amount` - 下单数量，买入是正数，卖出是负数

### 7. SimulationParameters对象
**功能**: 模拟参数配置
**主要属性**:
- `capital_base` - 起始资金
- `data_frequency` - 数据频率

### 8. VolumeShareSlippage对象
**功能**: 滑点配置
**主要属性**:
- `volume_limit` - 成交限量
- `price_impact` - 价格影响力

### 9. Commission对象
**功能**: 佣金费用配置
**主要属性**:
- `tax` - 印花税费率
- `cost` - 佣金费率
- `min_trade_cost` - 最小佣金

### 10. Blotter对象
**功能**: 订单记录管理
**主要属性**:
- `current_dt` - 当前单位时间的开始时间（datetime.datetime对象，北京时间）

### 11. FutureParams对象
**功能**: 期货参数配置
**主要属性**:
- `margin_rate` - 保证金比例
- `contract_multiplier` - 合约乘数

## API 总数统计

| 分类 | 数量 | 说明 |
|------|------|------|
| 策略生命周期函数 | 7 | 核心框架函数 |
| 设置函数 | 12 | 策略配置和参数设置 |
| 获取信息函数 | 50+ | 数据获取和查询 |
| 交易相关函数 | 30+ | 交易执行和管理 |
| 融资融券函数 | 19 | 两融业务专用 |
| 期货专用函数 | 7 | 期货交易专用 |
| 期权专用函数 | 15 | 期权交易专用 |
| 计算函数 | 4 | 技术指标计算 |
| 其他函数 | 7 | 工具和辅助函数 |
| **总计** | **150+** | **完整API接口** |

## 调用场景分类

| 场景 | 描述 | 支持的API类型 |
|------|------|---------------|
| **研究** | 数据研究和分析环境 | 基础信息获取、股票信息获取、财务数据、期权查询、工具函数 |
| **回测** | 历史数据回测环境 | 除实时交易外的所有API：生命周期函数、设置函数、获取信息函数、交易相关函数、计算函数 |
| **交易** | 实盘交易环境 | 所有API，包括实时数据获取、委托交易、主推回调等 |
| **两融交易** | 融资融券交易环境 | 基础交易API + 融资融券专用函数 |

## 使用场景详细说明

### 研究模式 (Research)
- **支持场景**: 数据分析、策略研究、历史回测数据获取
- **可用API**: 信息获取类函数、计算函数、工具函数
- **限制**: 无法执行实际交易操作

### 回测模式 (Backtest)
- **支持场景**: 策略历史数据回测、性能评估
- **可用API**: 策略生命周期函数、设置函数、获取信息函数、交易相关函数、计算函数
- **限制**: 无法获取实时数据、无法执行实际交易

### 交易模式 (Trading)
- **支持场景**: 实盘交易、实时数据获取、委托下单
- **可用API**: 所有API函数
- **特有功能**: tick级别处理、实时行情获取、委托主推、成交主推

## 使用频率最高的核心API (Top 20)

1. **initialize(context)** - 策略初始化
2. **handle_data(context, data)** - 主策略逻辑
3. **set_universe(securities)** - 设置股票池
4. **get_history()** - 获取历史行情
5. **get_price()** - 获取历史数据
6. **order()** - 下单交易
7. **order_target()** - 目标数量交易
8. **order_value()** - 目标金额交易
9. **get_position()** - 获取持仓
10. **get_orders()** - 获取订单
11. **cancel_order()** - 撤销订单
12. **log.info()** - 日志记录
13. **get_snapshot()** - 获取行情快照
14. **get_stock_info()** - 获取股票信息
15. **get_fundamentals()** - 获取财务数据
16. **set_commission()** - 设置手续费
17. **set_benchmark()** - 设置基准
18. **before_trading_start()** - 盘前处理
19. **after_trading_end()** - 盘后处理
20. **get_MACD()** - 技术指标MACD

本总结涵盖了PTrade量化交易平台的完整API体系，为插件系统的PTrade兼容层提供了完整的参考规范。