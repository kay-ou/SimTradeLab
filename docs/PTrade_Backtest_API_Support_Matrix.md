# PTrade 本地回测 API 支持矩阵（2026-07-10）

## 判定口径

- 范围为当前官方页面可见、可检索的 `65` 个回测相关 API；`log` 是策略注入对象，不是 `PtradeAPI` 成员函数。
- `full`：至少有一个从公开 API 到可观察结果的行为测试。
- `partial`：入口可调用，但目前只有接口、生命周期、参数或返回形态覆盖，尚无完整行为证据。
- `pending`：真实 PTrade 兼容行为或所需外部数据基线尚不能可靠验证。
- `unsupported`：本地回测明确不支持，调用会抛出 `NotImplementedError`。
- 机器可检查的分类和测试证据位于 `tests/ptrade_api_contracts.py`。

## 总览

| 分类 | 数量 |
| --- | ---: |
| `full` | 26 |
| `partial` | 26 |
| `pending` | 2 |
| `unsupported` | 10 |
| 特殊项 `log` | 1 |
| 合计 | 65 |

## Full：具有行为测试证据

| 类别 | API |
| --- | --- |
| 设置、持仓与调度 | `set_universe`、`set_slippage`、`set_fixed_slippage`、`set_volume_ratio`、`set_limit_mode`、`set_yesterday_position`、`run_daily` |
| 行情与证券数据 | `get_history`、`get_market_list`、`get_stock_exrights`、`get_fundamentals` |
| 交易日与状态 | `get_trading_day`、`get_trade_days`、`get_trading_day_by_date`、`check_limit` |
| 交易、订单与持仓 | `order`、`order_target`、`order_value`、`order_target_value`、`get_order`、`get_orders`、`get_trades`、`get_position`、`get_positions` |
| 其它 | `convert_position_from_csv`、`create_dir` |

## Partial：可调用但行为证据不完整

以下接口不能仅凭“函数存在”或“配置值写入成功”宣称完整支持：

| 类别 | API |
| --- | --- |
| 设置与调度 | `set_benchmark`、`set_commission` |
| 行情与证券数据 | `get_price`、`get_market_detail`、`get_stock_info`、`get_stock_name`、`get_stock_status`、`get_stock_blocks`、`get_index_stocks`、`get_industry_stocks`、`get_Ashares` |
| 状态与上下文 | `get_all_trades_days`、`filter_stock_by_status`、`get_current_kline_count`、`get_frequency`、`get_business_type`、`is_trade` |
| 交易与订单 | `cancel_order`、`get_open_orders` |
| 文件与账户 | `get_user_name`、`get_research_path`、`get_trades_file` |
| 技术指标 | `get_MACD`、`get_KDJ`、`get_RSI`、`get_CCI` |

参数级说明：`set_commission` 的 `commission_ratio` 和 `min_commission` 已传递到实际手续费、现金与持仓成本；`type` 仅被保存，尚无证券类型识别和分类型费率表，因此整体仍为 partial。

行情接口说明：`get_price` 的基础返回形态和复权数值已有测试，但当前交易日是否纳入结果、周/月/季/年频率的日期范围查询仍缺少权威 PTrade 基线，因此保持 partial。

订单模型说明：本地回测采用同步即时成交，公开下单 API 不会产生可由策略观察或撤销的未成交订单。因此 `cancel_order` 和 `get_open_orders` 仅验证了接口、生命周期和底层订单对象兼容，不能宣称完整复现异步挂单行为。

## Pending：兼容性待验证

- `get_reits_list`：需要可验证的券商/PTrade 数据基线。
- `get_trend_data`：券商可用性和集中竞价数据语义需要真实平台基线。

## Unsupported：明确不支持

以下接口保留入口并明确抛出 `NotImplementedError`：

- `margin_trade`（两融）
- `buy_open`、`sell_close`、`sell_open`、`buy_close`（期货）
- `set_future_commission`、`set_margin_rate`、`get_margin_rate`（期货配置）
- `get_instruments`、`get_dominant_contract`（期货查询）

补充说明：`get_individual_transaction` 和 `get_margin_assert` 不在上述当前可见 `65` 个回测 API 统计口径内，本地回测同样不支持。

## 特殊项

- `log`：由策略执行器注入策略命名空间，不是 `PtradeAPI` 成员函数。

## 代码依据

- 回测 API 实现：`src/simtradelab/ptrade/api.py`
- 生命周期限制：`src/simtradelab/ptrade/lifecycle_config.py`
- 支持契约清单：`tests/ptrade_api_contracts.py`
- 契约守卫：`tests/unit/test_ptrade_support_contracts.py`
