恒生投研平台

* [首页](/start)
* [研究](/home)
* [策略](/strategys)
* [交易](/trades)
* [数据](/data)
* [帮助](/help/api)

- [API文档](#API文档 "API文档")
- [使用说明](#使用说明 "使用说明")
- [新建策略](#新建策略 "新建策略")
- [新建回测](#新建回测 "新建回测")
- [新建交易](#新建交易 "新建交易")
- [策略运行周期](#策略运行周期 "策略运行周期")
- [策略运行时间](#策略运行时间 "策略运行时间")
- [交易策略委托下单时间](#交易策略委托下单时间 "交易策略委托下单时间")
- [回测支持业务类型](#回测支持业务类型 "回测支持业务类型")
- [交易支持业务类型](#交易支持业务类型 "交易支持业务类型")
- [开始写策略](#开始写策略 "开始写策略")
- [简单但是完整的策略](#简单但是完整的策略 "简单但是完整的策略")
- [添加一些交易](#添加一些交易 "添加一些交易")
- [实用的策略](#实用的策略 "实用的策略")
- [模拟盘和实盘注意事项](#模拟盘和实盘注意事项 "模拟盘和实盘注意事项")
- [策略引擎简介](#策略引擎简介 "策略引擎简介")
- [业务流程框架](#业务流程框架 "业务流程框架")
- [initialize(必选)](#initialize "initialize")
- [before\_trading\_start(可选)](#before_trading_start "before_trading_start")
- [handle\_data(必选)](#handle_data "handle_data")
- [after\_trading\_end(可选)](#after_trading_end "after_trading_end(可选)")
- [tick\_data(可选)](#tick_data "tick_data(可选)")
- [on\_order\_response - 委托主推(可选)](#on_order_response "on_order_response - 委托主推(可选)")
- [on\_trade\_response - 交易主推(可选)](#on_trade_response "on_trade_response - 交易主推(可选)")
- [策略API介绍](#策略API介绍 "策略API介绍")
- [设置函数](#设置函数 "设置函数")
- [set\_universe - 设置股票池](#set_universe "set_universe - 设置股票池")
- [set\_benchmark - 设置基准](#set_benchmark "set_benchmark - 设置基准")
- [set\_commission - 设置佣金费率](#set_commission "set_commission - 设置佣金费率")
- [set\_fixed\_slippage - 设置固定滑点](#set_fixed_slippage "set_fixed_slippage - 设置固定滑点")
- [set\_slippage - 设置滑点](#set_slippage "set_slippage - 设置滑点")
- [set\_volume\_ratio – 设置成交比例](#set_volume_ratio "set_volume_ratio – 设置成交比例")
- [set\_limit\_mode – 设置回测成交数量限制模式](#set_limit_mode "set_limit_mode – 设置成交数量限制模式")
- [set\_yesterday\_position – 设置底仓(股票)](#set_yesterday_position "set_yesterday_position – 设置底仓(股票)")
- [set\_parameters - 设置策略配置参数](#set_parameters "set_parameters - 设置策略配置参数")
- [定时周期性函数](#定时周期性函数 "定时周期性函数")
- [run\_daily - 按日周期处理](#run_daily "run_daily - 按日周期处理")
- [run\_interval - 按设定周期处理](#run_interval "run_interval - 按设定周期处理")
- [获取信息函数](#获取信息函数 "获取信息函数")
- [获取基础信息](#获取基础信息 "获取基础信息")
- [get\_trading\_day – 获取交易日期](#get_trading_day "get_trading_day – 获取交易日期")
- [get\_all\_trades\_days – 获取全部交易日期](#get_all_trades_days "get_all_trades_days – 获取全部交易日期")
- [get\_trade\_days – 获取指定范围交易日期](#get_trade_days "get_trade_days – 获取指定范围交易日期")
- [获取市场信息](#获取市场信息 "获取市场信息")
- [get\_market\_list - 获取市场列表](#get_market_list "get_market_list - 获取市场列表")
- [get\_market\_detail - 获取市场详细信息](#get_market_detail "get_market_detail - 获取市场详细信息")
- [get\_cb\_list - 获取可转债市场代码表](#get_cb_list "get_cb_list - 获取可转债市场代码表")
- [获取行情信息](#获取行情信息 "获取行情信息")
- [get\_history - 获取历史行情](#get_history "get_history - 获取历史行情")
- [get\_price - 获取历史数据](#get_price "get_price - 获取历史数据")
- [get\_individual\_entrust– 获取逐笔委托行情](#get_individual_entrust "get_individual_entrust– 获取逐笔委托行情")
- [get\_individual\_transaction– 获取逐笔成交行情](#get_individual_transaction "get_individual_transaction– 获取逐笔成交行情")
- [get\_tick\_direction– 获取分时成交行情](#get_tick_direction "get_tick_direction– 获取分时成交行情")
- [get\_sort\_msg– 获取板块、行业的涨幅排名](#get_sort_msg "get_sort_msg– 获取板块、行业的涨幅排名")
- [get\_etf\_info - 获取ETF信息](#get_etf_info "get_etf_info - 获取ETF信息")
- [get\_etf\_stock\_info - 获取ETF成分券信息](#get_etf_stock_info "get_etf_stock_info - 获取ETF成分券信息")
- [get\_gear\_price – 获取指定代码的档位行情价格](#get_gear_price "get_gear_price – 获取指定代码的档位行情价格")
- [get\_snapshot - 取行情快照](#get_snapshot "get_snapshot - 取行情快照")
- [get\_cb\_info - 获取可转债基础信息](#get_cb_info "get_cb_info - 获取可转债基础信息")
- [获取股票信息](#获取股票信息 "获取股票信息")
- [get\_stock\_name - 获取股票名称](#get_stock_name "get_stock_name - 获取股票名称")
- [get\_stock\_info - 获取股票基础信息](#get_stock_info "get_stock_info - 获取股票基础信息")
- [get\_stock\_status – 获取股票状态信息](#get_stock_status "get_stock_status – 获取股票状态信息")
- [get\_stock\_exrights - 获取股票除权除息信息](#get_stock_exrights "get_stock_exrights - 获取股票除权除息信息")
- [get\_stock\_blocks - 获取股票所属板块信息](#get_stock_blocks "get_stock_blocks - 获取股票所属板块信息")
- [get\_index\_stocks - 获取指数成份股](#get_index_stocks "get_index_stocks - 获取指数成份股")
- [get\_etf\_stock\_list - 获取ETF成分券列表](#get_etf_stock_list "get_etf_stock_list - 获取ETF成分券列表")
- [get\_industry\_stocks - 获取行业成份股](#get_industry_stocks "get_industry_stocks - 获取行业成份股")
- [get\_fundamentals - 获取财务数据信息](#get_fundamentals "get_fundamentals - 获取财务数据信息")
- [get\_Ashares – 获取指定日期A股代码列表](#get_Ashares "get_Ashares – 获取指定日期A股代码列表")
- [get\_etf\_list - 获取ETF代码](#get_etf_list "get_etf_list - 获取ETF代码")
- [get\_ipo\_stocks - 获取当日IPO申购标的](#get_ipo_stocks "get_ipo_stocks - 获取当日IPO申购标的")
- [获取其他信息](#获取其他信息 "获取其他信息")
- [get\_trades\_file – 获取对账数据文件](#get_trades_file "get_trades_file – 获取对账数据文件")
- [convert\_position\_from\_csv – 获取设置底仓的参数列表(股票)](#convert_position_from_csv "convert_position_from_csv – 获取设置底仓的参数列表(股票)")
- [get\_user\_name – 获取登录终端的资金账号](#get_user_name "get_user_name – 获取登录终端的资金账号")
- [get\_deliver – 获取历史交割单信息](#get_deliver "get_deliver – 获取登录终端的资金账号")
- [get\_fundjour – 获取历史资金流水信息](#get_fundjour "get_fundjour – 获取登录终端的资金账号")
- [get\_research\_path – 获取研究路径](#get_research_path "get_research_path – 获取研究路径")
- [get\_trade\_name – 获取交易名称](#get_trade_name "get_trade_name – 获取交易名称")
- [交易相关函数](#交易相关函数 "交易相关函数")
- [股票交易函数](#股票交易函数 "股票交易函数")
- [order - 按数量买卖](#order "order - 按数量买卖(股票)")
- [order\_target - 指定目标数量买卖](#order_target "order_target - 指定目标数量买卖(股票)")
- [order\_value - 指定目标价值买卖](#order_value "order_value - 指定目标价值买卖(股票)")
- [order\_target\_value - 指定持仓市值买卖](#order_target_value "order_target_value - 指定持仓市值买卖(股票)")
- [order\_market - 按市价进行委托](#order_market "order_market - 按市价进行委托(股票)")
- [ipo\_stocks\_order - 新股一键申购(股票)](#ipo_stocks_order "ipo_stocks_order - 新股一键申购(股票)")
- [after\_trading\_order - 盘后固定价委托(股票)](#after_trading_order "after_trading_order - 盘后固定价委托(股票)")
- [after\_trading\_cancel\_order - 盘后固定价委托撤单(股票)](#after_trading_cancel_order "after_trading_cancel_order - 盘后固定价委托撤单(股票)")
- [etf\_basket\_order - ETF成分券篮子下单](#etf_basket_order "etf_basket_order - ETF成分券篮子下单")
- [etf\_purchase\_redemption - ETF基金申赎接口](#etf_purchase_redemption "etf_purchase_redemption - ETF基金申赎接口")
- [get\_positions - 获取多支股票持仓信息](#get_positions "get_positions - 获取多支股票持仓信息")
- [公共交易函数](#公共交易函数 "公共交易函数")
- [order\_tick - tick行情触发买卖](#order_tick "order_tick - tick行情触发买卖")
- [cancel\_order - 撤单](#cancel_order "cancel_order - 撤单")
- [cancel\_order\_ex - 撤单](#cancel_order_ex "cancel_order_ex - 撤单")
- [debt\_to\_stock\_order - 债转股委托](#debt_to_stock_order "debt_to_stock_order - 债转股委托")
- [get\_open\_orders - 获取未完成订单](#get_open_orders "get_open_orders - 获取未完成订单")
- [get\_order - 获取指定订单](#get_order "get_order - 获取指定订单")
- [get\_orders - 获取全部订单](#get_orders "get_orders - 获取全部订单")
- [get\_all\_orders - 获取账户当日全部订单](#get_all_orders "get_all_orders - 获取账户当日全部订单")
- [get\_trades - 获取当日成交订单](#get_trades "get_trades - 获取当日成交订单")
- [get\_position - 获取持仓信息](#get_position "get_position - 获取持仓信息")
- [融资融券专用函数](#融资融券专用函数 "融资融券专用函数")
- [融资融券交易类函数](#融资融券交易类函数 "融资融券交易类函数")
- [margin\_trade - 担保品买卖](#margin_trade "margin_trade - 担保品买卖")
- [margincash\_open - 融资买入](#margincash_open "margincash_open - 融资买入")
- [margincash\_close - 卖券还款](#margincash_close "margincash_close - 卖券还款")
- [margincash\_direct\_refund - 直接还款](#margincash_direct_refund "margincash_direct_refund - 直接还款")
- [marginsec\_open - 融券卖出](#marginsec_open "marginsec_open - 融券卖出")
- [marginsec\_close - 买券还券](#marginsec_close "marginsec_close - 买券还券")
- [marginsec\_direct\_refund - 直接还券](#marginsec_direct_refund "marginsec_direct_refund - 直接还券")
- [融资融券查询类函数](#融资融券查询类函数 "融资融券查询类函数")
- [get\_margincash\_stocks - 获取融资标的](#get_margincash_stocks "get_margincash_stocks - 获取融资标的列表")
- [get\_marginsec\_stocks - 获取融券标的](#get_marginsec_stocks "get_marginsec_stocks - 获取融券标的列表")
- [get\_margin\_contract - 合约查询](#get_margin_contract "get_margin_contract - 合约查询")
- [get\_margin\_contractreal - 实时合约查询](#get_margin_contractreal "get_margin_contractreal - 实时合约查询")
- [get\_margin\_assert - 信用资产查询](#get_margin_assert "get_margin_assert - 信用资产查询")
- [get\_assure\_security\_list - 担保券查询](#get_assure_security_list "get_assure_security_list - 担保券查询")
- [get\_margincash\_open\_amount - 融资标的最大可买数量查询](#get_margincash_open_amount "get_margincash_open_amount - 融资标的最大可买数量查询")
- [get\_margincash\_close\_amount - 卖券还款标的最大可卖数量查询](#get_margincash_close_amount "get_margincash_close_amount - 卖券还款标的最大可卖数量查询")
- [get\_marginsec\_open\_amount - 融券标的最大可卖数量查询](#get_marginsec_open_amount "get_marginsec_open_amount - 融券标的最大可卖数量查询")
- [get\_marginsec\_close\_amount - 买券还券标的最大可买数量查询](#get_marginsec_close_amount "get_marginsec_close_amount - 买券还券标的最大可买数量查询")
- [get\_margin\_entrans\_amount - 现券还券数量查询](#get_margin_entrans_amount "get_margin_entrans_amount - 现券还券数量查询")
- [get\_enslo\_security\_info - 融券头寸信息查询](#get_enslo_security_info "get_enslo_security_info - 融券头寸信息查询")
- [期货专用函数](#期货专用函数 "期货专用函数")
- [期货交易类函数](#期货交易类函数 "期货交易类函数")
- [buy\_open - 开多](#buy_open "buy_open - 多开(期货、期权使用)")
- [sell\_close - 多平](#sell_close "sell_close - 多平(期货、期权使用)")
- [sell\_open - 空开](#sell_open "sell_open - 空开(期货、期权使用)")
- [buy\_close - 空平](#buy_close "buy_close - 空平(期货、期权使用)")
- [期货查询类函数](#期货查询类函数 "期货查询类函数")
- [get\_margin\_rate – 获取用户设置的保证金比例](#get_margin_rate "get_margin_rate – 获取用户设置的保证金比例")
- [get\_instruments – 获取合约信息](#get_instruments "get_instruments – 获取合约信息")
- [期货设置类函数](#期货设置类函数 "期货设置类函数")
- [set\_future\_commission – 设置期货手续费](#set_future_commission "set_future_commission – 设置期货手续费")
- [set\_margin\_rate – 设置期货保证金比例](#set_margin_rate "set_margin_rate – 设置期货保证金比例")
- [期权专用函数](#期权专用函数 "期权专用函数")
- [期权查询类函数](#期权查询类函数 "期权查询类函数")
- [get\_opt\_objects – 获取期权标的列表](#get_opt_objects "get_opt_objects – 获取期权标的列表")
- [get\_opt\_last\_dates – 获取期权标的到期日列表](#get_opt_last_dates "get_opt_last_dates – 获取期权标的到期日列表")
- [get\_opt\_contracts – 获取期权标的对应合约列表](#get_opt_contracts "get_opt_contracts – 获取期权标的对应合约列表")
- [get\_contract\_info – 获取期权合约信息](#get_contract_info "get_contract_info – 获取期权合约信息")
- [get\_covered\_lock\_amount – 获取期权标的可备兑锁定数量](#get_covered_lock_amount "get_covered_lock_amount – 获取期权标的允许备兑锁定数量")
- [get\_covered\_unlock\_amount – 获取期权标的允许备兑解锁数量](#get_covered_unlock_amount "get_covered_unlock_amount – 获取期权标的允许备兑解锁数量")
- [期权交易类函数](#期权交易类函数 "期权交易类函数")
- [buy\_open - 权利仓开仓](#option_buy_open "buy_open - 权利仓开仓(期货、期权使用)")
- [sell\_close - 权利仓平仓](#option_sell_close "sell_close - 权利仓平仓(期货、期权使用)")
- [sell\_open - 义务仓开仓](#option_sell_open "sell_open - 义务仓开仓(期货、期权使用)")
- [buy\_close - 义务仓平仓](#option_buy_close "buy_close - 义务仓平仓(期货、期权使用)")
- [open\_prepared - 备兑开仓](#open_prepared "open_prepared - 备兑开仓(期权专用)")
- [close\_prepared - 备兑平仓](#close_prepared "close_prepared - 备兑平仓(期权专用)")
- [option\_exercise - 行权](#option_exercise "option_exercise - 行权(期权专用)")
- [期权其他函数](#期权其他函数 "期权其他函数")
- [option\_covered\_lock - 期权标的备兑锁定](#option_covered_lock "option_covered_lock - 期权标的备兑锁定(期货、期权使用)")
- [option\_covered\_unlock - 期权标的备兑解锁](#option_covered_unlock "option_covered_unlock - 期权标的备兑解锁(期货、期权使用)")
- [计算函数](#计算函数 "计算函数")
- [技术指标计算函数](#技术指标计算函数 "技术指标计算函数")
- [get\_MACD – 异同移动平均线](#get_MACD "get_MACD – 异同移动平均线")
- [get\_KDJ – 随机指标](#get_KDJ "get_KDJ – 随机指标")
- [get\_RSI – 相对强弱指标](#get_RSI "get_RSI – 相对强弱指标")
- [get\_CCI – 顺势指标](#get_CCI "get_CCI – 顺势指标")
- [其他函数](#其他函数 "其他函数")
- [log - 日志记录](#log "log - 日志记录")
- [is\_trade - 业务代码场景判断](#is_trade "is_trade - 业务代码场景判断")
- [check\_limit - 代码涨跌停状态判断](#check_limit "check_limit - 代码涨跌停状态判断")
- [send\_email - 发送邮箱信息](#send_email "send_email - 发送邮箱信息")
- [send\_qywx - 发送企业微信信息](#send_qywx "send_qywx - 发送企业微信信息")
- [permission\_test - 权限校验](#permission_test "permission_test - 权限校验")
- [create\_dir - 创建文件路径](#create_dir "create_dir - 创建文件路径")
- [对象](#对象 "对象")
- [g - 全局对象](#g "g - 全局对象")
- [Context - 上下文对象](#Context "Context - 上下文对象")
- [SecurityUnitData对象](#SecurityUnitData "SecurityUnitData对象")
- [Portfolio对象](#Portfolio "Portfolio对象")
- [Position对象](#Position "Position对象")
- [Order对象](#Order "Order对象")
- [策略示例](#策略示例 "策略示例")
- [集合竞价追涨停策略](#集合竞价追涨停策略 "集合竞价追涨停策略")
- [tick级别均线策略](#tick级别均线策略 "tick级别均线策略")
- [双均线策略](#双均线策略 "双均线策略")
- [融资融券双均线策略](#融资融券双均线策略 "融资融券双均线策略")
- [MACD策略](#macd策略 "MACD策略")
- [常见问题](#常见问题 "常见问题")
- [支持的三方库](#支持的三方库 "支持的三方库")
- [接口版本变动](#接口版本变动 "接口版本变动")

# API文档

# 使用说明

## 新建策略

开始回测和交易前需要先新建策略，点击下图中左上角标识进行策略添加。可以选择不同的业务类型（比如股票），然后给策略设定一个名称，添加成功后可以在默认策略模板基础上进行策略编写。

![](/static/images/help/creat_strategy.png)

## 新建回测

策略添加完成后就可以开始进行回测操作了。回测之前需要对开始时间、结束时间、回测资金、回测基准、回测频率几个要素进行设定，设定完毕后点击保存。然后再点击回测按键，系统就会开始运行回测，回测的评价指标、收益曲线、日志都会在界面中展现。

![](/static/images/help/backtest_factor.png)

## 新建交易

交易界面点击新增按键进行新增交易操作，策略方案中的对象为所有策略列表中的策略，给本次交易设定名称并点击确定后系统就开始运行交易了。

![](/static/images/help/creat_trade.png)

交易开始运行后，可以实时看到总资产和可用资金情况，同时可以在交易列表查询交易状态。

![](/static/images/help/account_info.png)

交易开始运行后，可以点击交易详情，查看策略评价指标、交易明细、持仓明细、交易日志。

![](/static/images/help/trade_info.png)

## 策略运行周期

回测支持日线级别、分钟级别运行，详见[handle\_data](#handle_data)方法。

交易支持日线级别、分钟级别、tick级别运行，日线级别和分钟级别详见[handle\_data](#handle_data)方法，tick级别运行详见[run\_interval](#run_interval)和[tick\_data](#tick_data)方法。

频率：日线级别

当选择日线频率时，回测和交易都是每天运行一次，运行时间为每天盘后。

频率：分钟级别

当选择分钟频率时，回测和交易都是每分钟运行一次，运行时间为每根分钟K线结束。

频率：tick级别

当选择tick频率时，交易最小频率可以达到3秒运行一次。

## 策略运行时间

盘前运行:

9:30分钟之前为盘前运行时间，交易环境支持运行在[run\_daily](#run_daily)中指定交易时间(如time='09:15')运行的函数；回测环境和交易环境支持运行[before\_trading\_start](#before_trading_start)函数

盘中运行:

9:31(回测)/9:30(交易)\~15:00分钟为盘中运行时间，分钟级别回测环境和交易环境支持运行在[run\_daily](#run_daily)中指定交易时间(如time='14:30')运行的函数；回测环境和交易环境支持运行[handle\_data](#handle_data)函数；交易环境支持运行[run\_interval](#run_interval)函数

盘后运行:

15:30分钟为盘后运行时间，回测环境和交易环境支持运行[after\_trading\_end](#after_trading_end)函数(该函数为定时运行)；15:00之后交易环境支持运行在[run\_daily](#run_daily)中指定交易时间(如time='15:10')运行的函数，

## 交易策略委托下单时间

使用order系列接口进行股票委托下单，将直接报单到柜台。

## 回测支持业务类型

目前所支持的业务类型:

1.普通股票买卖(单位：股)。

2.可转债买卖(单位：张，T+0)。

3.融资融券担保品买卖(单位：股)。

4.期货投机类型交易(单位：手，T+0)。

5.LOF基金买卖(单位：股)。

6.ETF基金买卖(单位：股)。

## 交易支持业务类型

目前所支持的业务类型:

1.普通股票买卖(单位：股)。

2.可转债买卖(具体单位请咨询券商，T+0)。

3.融资融券交易(单位：股)。

4.ETF申赎、套利(单位：份)。

5.国债逆回购(单位：份)。

6.期货投机类型交易(单位：手，T+0)。

7.LOF基金买卖(单位：股)。

8.ETF基金买卖(单位：股)。

9.期权交易(单位：手)。

# 开始写策略

## 简单但是完整的策略

先来看一个简单但是完整的策略:

```python
def initialize(context):
    set_universe('600570.SS')

def handle_data(context, data):
    pass
```

一个完整策略只需要两步:

1. set\_universe: 设置我们要操作的股票池，上面的例子中，只操作一支股票: '600570.SS'，恒生电子。所有的操作只能对股票池的标的进行。
2. 实现一个函数: handle\_data。

这是一个完整的策略，但是我们没有任何交易，下面我们来添加一些交易

## 添加一些交易

```python
def initialize(context):
    g.security = '600570.SS'
    # 是否创建订单标识
    g.flag = False
    set_universe(g.security)

def handle_data(context, data):
    if not g.flag:
        order(g.security, 1000)
        g.flag = True
```

这个策略里，当我们没有创建订单时就买入1000股'600570.SS'，具体的下单API请看[order](#order)函数。这里我们有了交易，但是只是无意义的交易，没有依据当前的数据做出合理的分析。

## 实用的策略

下面我们来看一个真正实用的策略

在这个策略里，我们会根据历史价格做出判断:

* 如果上一时间点价格高出五天平均价1%，则全仓买入
* 如果上一时间点价格低于五天平均价，则空仓卖出

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    
def handle_data(context, data):
    security = g.security
    sid = g.security
    
    # 取得过去五天的历史价格
    df = get_history(5, '1d', 'close', security, fq=None, include=False)
    
    # 取得过去五天的平均价格
    average_price = round(df['close'][-5:].mean(), 3)

    # 取得上一时间点价格
    current_price = data[sid]['close']
    
    # 取得当前的现金
    cash = context.portfolio.cash
    
    # 如果上一时间点价格高出五天平均价1%, 则全仓买入
    if current_price > 1.01*average_price:
        # 用所有 cash 买入股票
        order_value(g.security, cash)
        log.info('buy %s' % g.security)
    # 如果上一时间点价格低于五天平均价, 则空仓卖出
    elif current_price < average_price and get_position(security).amount > 0:
        # 卖出所有股票,使这只股票的最终持有量为0
        order_target(g.security, 0)
        log.info('sell %s' % g.security)
```

## 模拟盘和实盘注意事项

### 关于持久化

#### 为什么要做持久化处理

服务器异常、策略优化等诸多场景，都会使得正在进行的模拟盘和实盘策略存在中断后再重启的需求，但是一旦交易中止后，策略中存储在内存中的全局变量就清空了，因此通过持久化处理为量化交易保驾护航必不可少。

#### 量化框架持久化处理

使用pickle模块保存股票池、账户信息、订单信息、全局变量g定义的变量等内容。

注意事项：

1. 框架会在[before\_trading\_start（隔日开始）](#before_trading_start)、[handle\_data](#handle_data)、[after\_trading\_end](#after_trading_end)事件后触发持久化信息更新及保存操作；
2. 券商升级/环境重启后恢复交易时，框架会先执行策略[initialize](#initialize)函数再执行持久化信息恢复操作。如果持久化信息保存有策略定义的全局对象g中的变量，将会以持久化信息中的变量覆盖掉[initialize](#initialize)函数中初始化的该变量。
3. 全局变量g中不能被序列化的变量将不会被保存。您可在[initialize](#initialize)中初始化该变量时名字以'\_\_'开头；
4. 涉及到IO(打开的文件，实例化的类对象等)的对象是不能被序列化的；
5. 全局变量g中以'\_\_'开头的变量为私有变量，持久化时将不会被保存；

#### 示例

```python
class Test(object):
    count = 5

    def print_info(self):
        self.count += 1
        log.info("a" * self.count)


def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)
    # 初始化无法被序列化类对象，并赋值为私有变量，落地持久化信息时跳过保存该变量
    g.__test_class = Test()

def handle_data(context, data):
    # 调用私有变量中定义的方法
    g.__test_class.print_info()
```

#### 策略中持久化处理方法

使用pickle模块保存 g 对象(全局变量)。

#### 示例

```python
import pickle
from collections import defaultdict
NOTEBOOK_PATH = '/home/fly/notebook/'
'''
持仓N日后卖出，仓龄变量每日pickle进行保存，重启策略后可以保证逻辑连贯
'''
def initialize(context):
    #尝试启动pickle文件
    try:
        with open(NOTEBOOK_PATH+'hold_days.pkl','rb') as f:
            g.hold_days = pickle.load(f)
    #定义空的全局字典变量
    except:
        g.hold_days = defaultdict(list)
    g.security = '600570.SS'
    set_universe(g.security)

# 仓龄增加一天
def before_trading_start(context, data):
    if g.hold_days:
        g.hold_days[g.security] += 1
        
# 每天将存储仓龄的字典对象进行pickle保存
def handle_data(context, data):
    if g.security not in list(context.portfolio.positions.keys()) and g.security not in g.hold_days:
        order(g.security, 100)
        g.hold_days[g.security] = 1
    if g.hold_days:
        if g.hold_days[g.security] > 5:
            order(g.security, -100)
            del g.hold_days[g.security]
    with open(NOTEBOOK_PATH+'hold_days.pkl','wb') as f:
        pickle.dump(g.hold_days,f,-1)
```

# 策略引擎简介

## 业务流程框架

ptrade量化引擎以事件触发为基础，通过初始化事件（initialize）、盘前事件（before\_trading\_start）、盘中事件（handle\_data）、盘后事件（after\_trading\_end）来完成每个交易日的策略任务。

initialize和handle\_data是一个允许运行策略的最基础结构，也就是必选项，before\_trading\_start和after\_trading\_end是可以按需运行的。

handle\_data仅满足日线和分钟级别的盘中处理，tick级别的盘中处理则需要通过tick\_data或者run\_interval来实现。

ptrade还支持委托主推事件（on\_order\_response）、交易主推事件（on\_trade\_response），可以通过委托和成交的信息来处理策略逻辑，是tick级的一个补充。

除了以上的一些事件以外，ptrade也支持通过定时任务来运行策略逻辑，可以通过run\_daily接口实现。

![](/static/images/help/BizFrame.png)

### initialize（必选）

```python
initialize(context)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数用于初始化一些全局变量，是策略运行的唯二必须定义函数之一。

注意事项：

该函数只会在回测和交易启动的时候运行一次

#### 可调用接口

|                                                           |                                                                |                                                          |
| --------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------- |
| [set\_universe(回测/交易)](#set_universe)                     | [set\_benchmark(回测/交易)](#set_benchmark)                        | [set\_commission(回测)](#set_commission)                   |
| [set\_fixed\_slippage(回测)](#set_fixed_slippage)           | [set\_slippage(回测)](#set_slippage)                             | [set\_volume\_ratio(回测)](#set_volume_ratio)              |
| [set\_limit\_mode(回测)](#set_limit_mode)                   | [set\_yesterday\_position(回测)](#set_yesterday_position)        | [run\_daily(回测/交易)](#run_daily)                          |
| [run\_interval(交易)](#run_interval)                        | [get\_trading\_day(研究/回测/交易)](#get_trading_day)                | [get\_all\_trades\_days(研究/回测/交易)](#get_all_trades_days) |
| [get\_trade\_days(交易)](#get_trade_days)                   | [convert\_position\_from\_csv(回测)](#convert_position_from_csv) | [get\_user\_name(回测/交易)](#get_user_name)                 |
| [is\_trade(回测/交易)](#is_trade)                             | [get\_research\_path(回测/交易)](#get_research_path)               | [permission\_test(交易)](#permission_test)                 |
| [set\_future\_commission(回测(期货))](#set_future_commission) | [set\_margin\_rate(回测(期货))](#set_margin_rate)                  | [get\_margin\_rate(回测(期货))](#get_margin_rate)            |
| [create\_dir(回测/交易)](#create_dir)                         | [set\_parameters(回测/交易)](#set_parameters)                      |                                                          |

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息；

#### 返回

None

#### 示例

```python
def initialize(context):
    #g为全局对象
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    order('600570.SS',100)
```

### before\_trading\_start（可选）

```python
before_trading_start(context, data)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数在每天开始交易前被调用一次，用于添加每天都要初始化的信息，如无盘前初始化需求，该函数可以在策略中不做定义。

注意事项：

1. 在回测中，该函数在每个回测交易日8:30分执行。
2. 在交易中，该函数在开启交易时立即执行，从隔日开始每天9:10分(默认)执行。
3. 当在9:10前开启交易时，受行情未更新原因在该函数内调用实时行情接口会导致数据有误。可通过在该函数内sleep至9:10分或调用实时行情接口改为run\_daily执行等方式进行避免。

#### 可调用接口

|                                                                 |                                                                |                                                            |
| --------------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| [set\_universe(回测/交易)](#set_universe)                           | [get\_Ashares(研究/回测/交易)](#get_Ashares)                         | [set\_yesterday\_position(回测)](#set_yesterday_position)    |
| [get\_stock\_info(研究/回测/交易)](#get_stock_info)                   | [get\_index\_stocks(研究/回测/交易)](#get_index_stocks)              | [get\_fundamentals(研究/回测/交易)](#get_fundamentals)           |
| [get\_trading\_day(回测/交易)](#get_trading_day)                    | [get\_all\_trades\_days(研究/回测/交易)](#get_all_trades_days)       | [get\_trade\_days(研究/回测/交易)](#get_trade_days)              |
| [get\_history(回测/交易)](#get_history)                             | [get\_price(研究/回测/交易)](#get_price)                             | [get\_individual\_entrust(交易)](#get_individual_entrust)    |
| [get\_individual\_transaction(交易)](#get_individual_transaction) | [convert\_position\_from\_csv(回测)](#convert_position_from_csv) | [get\_stock\_name(研究/回测/交易)](#get_stock_name)              |
| [get\_stock\_status(研究/回测/交易)](#get_stock_status)               | [get\_stock\_exrights(研究/回测/交易)](#get_stock_exrights)          | [get\_stock\_blocks(研究/回测/交易)](#get_stock_blocks)          |
| [get\_etf\_list(交易)](#get_etf_list)                             | [get\_industry\_stocks(研究/回测/交易)](#get_industry_stocks)        | [get\_user\_name(回测/交易)](#get_user_name)                   |
| [get\_cb\_list(交易)](#get_cb_list)                               | [get\_deliver(交易)](#get_deliver)                               | [get\_fundjour(交易)](#get_fundjour)                         |
| [get\_research\_path(回测/交易)](#get_research_path)                | [get\_market\_list(研究/回测/交易)](#get_market_list)                | [get\_market\_detail(研究/回测/交易)](#get_market_detail)        |
| [permission\_test(交易)](#permission_test)                        | [get\_trade\_name(交易)](#get_trade_name)                        | [set\_future\_commission(回测(期货))](#set_future_commission)  |
| [set\_margin\_rate(回测(期货))](#set_margin_rate)                   | [get\_margin\_rate(回测(期货))](#get_margin_rate)                  | [get\_instruments(回测/交易(期货))](#get_instruments)            |
| [get\_MACD(回测/交易)](#get_MACD)                                   | [get\_KDJ(回测/交易)](#get_KDJ)                                    | [get\_RSI(回测/交易)](#get_RSI)                                |
| [get\_CCI(回测/交易)](#get_CCI)                                     | [create\_dir(回测/交易)](#create_dir)                              | [get\_opt\_objects(研究/回测/交易(期权))](#get_opt_objects)        |
| [get\_opt\_last\_dates(研究/回测/交易(期权))](#get_opt_last_dates)      | [get\_opt\_contracts(研究/回测/交易(期权))](#get_opt_contracts)        | [get\_contract\_info(研究/回测/交易(期权))](#get_contract_info)    |
| [set\_parameters(回测/交易)](#set_parameters)                       | [get\_cb\_info(研究/交易)](#get_cb_info)                           | [get\_enslo\_security\_info(交易)](#get_enslo_security_info) |
| [get\_ipo\_stocks(交易)](#get_ipo_stocks)                         |                                                                |                                                            |

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息；

data：保留字段暂无数据；

#### 返回

None

#### 示例

```python
def initialize(context):
    #g为全局变量
    g.security = '600570.SS'
    set_universe(g.security)

def before_trading_start(context, data):
    log.info(g.security)

def handle_data(context, data):
    order('600570.SS',100)
```

### handle\_data（必选）

```python
handle_data(context, data)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数在交易时间内按指定的周期频率运行，是用于处理策略交易的主要模块，根据策略保存时的周期参数分为每分钟运行和每天运行，是策略运行的唯二必须定义函数之一。

注意事项：

1. 该函数每个单位周期执行一次
2. 如果是日线级别策略，每天执行一次。股票回测场景下，在15:00执行；股票交易场景下，执行时间为券商实际配置时间。
3. 如果是分钟级别策略，每分钟执行一次，股票回测场景下，执行时间为9:31 -- 15:00，股票交易场景下，执行时间为9:30 -- 14:59。
4. 回测与交易中，handle\_data函数不会在非交易日触发（如回测或交易起始日期为2015年12月21日，则策略在2016年1月1日-3日时，handle\_data不会运行，4日继续运行）。

#### 可调用接口

|                                                                    |                                                                    |                                                                  |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| [get\_trading\_day(回测/交易)](#get_trading_day)                       | [get\_all\_trades\_days(研究/回测/交易)](#get_all_trades_days)           | [get\_trade\_days(研究/回测/交易)](#get_trade_days)                    |
| [get\_history(回测/交易)](#get_history)                                | [get\_price(研究/回测/交易)](#get_price)                                 | [get\_individual\_entrust(交易)](#get_individual_entrust)          |
| [get\_individual\_transaction(交易)](#get_individual_transaction)    | [get\_gear\_price(交易)](#get_gear_price)                            | [get\_stock\_name(研究/回测/交易)](#get_stock_name)                    |
| [get\_stock\_status(研究/回测/交易)](#get_stock_status)                  | [get\_stock\_exrights(研究/回测/交易)](#get_stock_exrights)              | [get\_stock\_blocks(研究/回测/交易)](#get_stock_blocks)                |
| [get\_index\_stocks(研究/回测/交易)](#get_index_stocks)                  | [get\_industry\_stocks(研究/回测/交易)](#get_industry_stocks)            | [get\_fundamentals(研究/回测/交易)](#get_fundamentals)                 |
| [get\_Ashares(研究/回测/交易)](#get_Ashares)                             | [get\_snapshot(交易)](#get_snapshot)                                 | [convert\_position\_from\_csv(回测)](#convert_position_from_csv)   |
| [order(回测/交易)](#order)                                             | [order\_target(回测/交易)](#order_target)                              | [order\_value(回测/交易)](#order_value)                              |
| [order\_target\_value(回测/交易)](#order_target_value)                 | [order\_market(交易)](#order_market)                                 | [ipo\_stocks\_order(交易)](#ipo_stocks_order)                      |
| [after\_trading\_order(交易)](#after_trading_order)                  | [after\_trading\_cancel\_order(交易)](#after_trading_cancel_order)   | [etf\_basket\_order(交易)](#etf_basket_order)                      |
| [etf\_purchase\_redemption(交易)](#etf_purchase_redemption)          | [cancel\_order(回测/交易)](#cancel_order)                              | [get\_stock\_info(研究/回测/交易)](#get_stock_info)                    |
| [get\_order(回测/交易)](#get_order)                                    | [get\_orders(回测/交易)](#get_orders)                                  | [get\_open\_orders(回测/交易)](#get_open_orders)                     |
| [get\_trades(回测/交易)](#get_trades)                                  | [get\_position(回测/交易)](#get_position)                              | [get\_positions(回测/交易)](#get_positions)                          |
| [get\_etf\_info(交易)](#get_etf_info)                                | [get\_etf\_stock\_info(交易)](#get_etf_stock_info)                   | [get\_etf\_stock\_list(交易)](#get_etf_stock_list)                 |
| [get\_etf\_list(交易)](#get_etf_list)                                | [get\_all\_orders(交易)](#get_all_orders)                            | [cancel\_order\_ex(交易)](#cancel_order_ex)                        |
| [debt\_to\_stock\_order(交易)](#debt_to_stock_order)                 | [get\_user\_name(回测/交易)](#get_user_name)                           | [get\_research\_path(回测/交易)](#get_research_path)                 |
| [get\_marginsec\_stocks(交易)](#get_marginsec_stocks)                | [get\_margincash\_stocks(交易)](#get_margincash_stocks)              | [debt\_to\_stock\_order(交易)](#debt_to_stock_order)               |
| [get\_margin\_contractreal(交易)](#get_margin_contractreal)          | [get\_margin\_contract(交易)](#get_margin_contract)                  | [marginsec\_direct\_refund(交易)](#marginsec_direct_refund)        |
| [get\_margin\_entrans\_amount(交易)](#get_margin_entrans_amount)     | [get\_margin\_contract(交易)](#get_margin_contract)                  | [margincash\_direct\_refund(交易)](#margincash_direct_refund)      |
| [marginsec\_open(交易)](#marginsec_open)                             | [marginsec\_close(交易)](#marginsec_close)                           | [margincash\_open(交易)](#margincash_open)                         |
| [margincash\_close(交易)](#margincash_close)                         | [margin\_trade(交易)](#margin_trade)                                 | [get\_marginsec\_close\_amount(交易)](#get_marginsec_close_amount) |
| [get\_marginsec\_open\_amount(交易)](#get_marginsec_open_amount)     | [get\_margincash\_close\_amount(交易)](#get_margincash_close_amount) | [get\_margincash\_open\_amount(交易)](#get_margincash_open_amount) |
| [get\_cb\_list(交易)](#get_cb_list)                                  | [get\_tick\_direction(交易)](#get_tick_direction)                    | [get\_sort\_msg(交易)](#get_sort_msg)                              |
| [get\_trade\_name(交易)](#get_trade_name)                            | [get\_margin\_rate(回测(期货))](#get_margin_rate)                      | [get\_instruments(回测/交易(期货)](#get_instruments)                   |
| [buy\_open(回测/交易(期货)](#buy_open)                                   | [sell\_close(回测/交易(期货)](#sell_close)                               | [sell\_close(回测/交易(期货)](#sell_close)                             |
| [buy\_close(回测/交易(期货)](#buy_close)                                 | [get\_MACD(回测/交易)](#get_MACD)                                      | [get\_KDJ(回测/交易)](#get_KDJ)                                      |
| [get\_RSI(回测/交易)](#get_RSI)                                        | [get\_CCI(回测/交易)](#get_CCI)                                        | [create\_dir(回测/交易)](#create_dir)                                |
| [get\_opt\_objects(研究/回测/交易(期权))](#get_opt_objects)                | [get\_opt\_last\_dates(研究/回测/交易(期权))](#get_opt_last_dates)         | [get\_opt\_contracts(研究/回测/交易(期权))](#get_opt_contracts)          |
| [get\_contract\_info(研究/回测/交易(期权))](#get_contract_info)            | [set\_parameters(回测/交易)](#set_parameters)                          | [get\_covered\_lock\_amount(交易(期权))](#get_covered_lock_amount)   |
| [get\_covered\_unlock\_amount(交易(期权))](#get_covered_unlock_amount) | [buy\_open(交易(期权))](#option_buy_open)                              | [sell\_close(交易(期权))](#option_sell_close)                        |
| [sell\_open(交易(期权))](#option_sell_open)                            | [buy\_close(交易(期权))](#option_buy_close)                            | [open\_prepared(交易(期权))](#open_prepared)                         |
| [close\_prepared(交易(期权))](#close_prepared)                         | [option\_exercise(交易(期权))](#option_exercise)                       | [option\_covered\_lock(交易(期权))](#option_covered_lock)            |
| [option\_covered\_unlock(交易(期权))](#option_covered_unlock)          | [get\_cb\_info(研究/交易)](#get_cb_info)                               | [get\_enslo\_security\_info(交易)](#get_enslo_security_info)       |
| [get\_ipo\_stocks(交易)](#get_ipo_stocks)                            | [check\_limit(回测/研究/交易)](#check_limit)                             |                                                                  |

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息；

data：一个字典(dict)，key是标的代码，value是当时的SecurityUnitData对象，存放当前周期（日线策略，则是当天；分钟策略，则是这一分钟）的数据；

注意：为了加速，data中的数据只包含股票池中所订阅标的的信息，可使用data\[security]的方式来获取当前周期对应的标的信息；

#### 返回

None

#### 示例

```python
def initialize(context):
    #g为全局变量
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    order('600570.SS',100)
```

### after\_trading\_end（可选）

```python
after_trading_end(context, data)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数会在每天交易结束之后调用，用于处理每天收盘后的操作，如无盘后处理需求，该函数可以在策略中不做定义。

注意事项：

1. 该函数只会执行一次
2. 该函数执行时间为由券商配置决定，一般为15:30。

#### 可调用接口

|                                                            |                                                            |                                                                 |
| ---------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------- |
| [get\_trades\_file(回测)](#get_trades_file)                  | [get\_stock\_info(研究/回测/交易)](#get_stock_info)              | [get\_open\_orders(回测/交易)](#get_open_orders)                    |
| [get\_all\_trades\_days(研究/回测/交易)](#get_all_trades_days)   | [get\_trade\_days(研究/回测/交易)](#get_trade_days)              | [get\_history(回测/交易)](#get_history)                             |
| [get\_price(研究/回测/交易)](#get_price)                         | [get\_individual\_entrust(交易)](#get_individual_entrust)    | [get\_individual\_transaction(交易)](#get_individual_transaction) |
| [get\_Ashares(研究/回测/交易)](#get_Ashares)                     | [get\_stock\_name(研究/回测/交易)](#get_stock_name)              | [get\_stock\_status(研究/回测/交易)](#get_stock_status)               |
| [get\_stock\_exrights(研究/回测/交易)](#get_stock_exrights)      | [get\_stock\_blocks(研究/回测/交易)](#get_stock_blocks)          | [get\_index\_stocks(研究/回测/交易)](#get_index_stocks)               |
| [get\_industry\_stocks(研究/回测/交易)](#get_industry_stocks)    | [get\_fundamentals(研究/回测/交易)](#get_fundamentals)           | [get\_user\_name(回测/交易)](#get_user_name)                        |
| [get\_cb\_list(交易)](#get_cb_list)                          | [get\_deliver(交易)](#get_deliver)                           | [get\_fundjour(交易)](#get_fundjour)                              |
| [get\_research\_path(回测/交易)](#get_research_path)           | [get\_trade\_name(交易)](#get_trade_name)                    | [get\_market\_list(研究/回测/交易)](#get_market_list)                 |
| [get\_market\_detail(研究/回测/交易)](#get_market_detail)        | [permission\_test(交易)](#permission_test)                   | [get\_tick\_direction(交易)](#get_tick_direction)                 |
| [get\_sort\_msg(交易)](#get_sort_msg)                        | [get\_margin\_rate(回测(期货))](#get_margin_rate)              | [get\_margin\_rate(回测(期货))](#get_margin_rate)                   |
| [get\_instruments(回测/交易(期货))](#get_instruments)            | [get\_MACD(回测/交易)](#get_MACD)                              | [get\_KDJ(回测/交易)](#get_KDJ)                                     |
| [get\_RSI(回测/交易)](#get_RSI)                                | [get\_CCI(回测/交易)](#get_CCI)                                | [create\_dir(回测/交易)](#create_dir)                               |
| [get\_opt\_objects(研究/回测/交易(期权))](#get_opt_objects)        | [get\_opt\_last\_dates(研究/回测/交易(期权))](#get_opt_last_dates) | [get\_opt\_contracts(研究/回测/交易(期权))](#get_opt_contracts)         |
| [get\_contract\_info(研究/回测/交易(期权))](#get_contract_info)    | [set\_parameters(回测/交易)](#set_parameters)                  | [get\_cb\_info(研究/交易)](#get_cb_info)                            |
| [get\_enslo\_security\_info(交易)](#get_enslo_security_info) |                                                            |                                                                 |

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息；

data：保留字段暂无数据；

#### 返回

None

#### 示例

```python
def initialize(context):
    #g为全局变量
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    order('600570.SS',100)

def after_trading_end(context, data):
    log.info(g.security)
```

### tick\_data（可选）

```python
tick_data(context, data)
```

#### 使用场景

该函数仅交易模块可用

#### 接口说明

该函数可以用于处理tick级别策略的交易逻辑，每隔3秒执行一次，如无tick处理需求，该函数可以在策略中不做定义。

注意事项：

1. 该函数执行时间为9:30 -- 14:59。
2. 该函数中的data和[handle\_data](#handle_data)函数中的data是不一样的，请勿混肴。
3. 参数data中包含的逐笔委托，逐笔成交数据需开通level2行情才能获取到数据，否则对应数据返回None。
4. 参数data中的tick数据取自[get\_snapshot()](#get_snapshot)并转换为DataFrame格式，如要更快速的获取快照强烈建议直接使用[get\_snapshot()](#get_snapshot)获取。
5. 当调用[set\_parameters()](#set_parameters)并设置tick\_data\_no\_l2="1"时，参数data中将不包含逐笔委托、逐笔成交字段，当券商有l2行情时配置该参数可提升data取速；
6. 当策略执行时间超过3s时，将会丢弃中间堵塞的tick\_data。
7. 在收盘后，将会清空队列中未执行的tick\_data。
8. 参数data中包含的逐笔委托，逐笔成交数据正常返回DataFrame格式，异常时返回None。

#### 可调用接口

|                                                                    |                                                                    |                                                                |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | -------------------------------------------------------------- |
| [get\_trading\_day(研究/回测/交易)](#get_trading_day)                    | [get\_all\_trades\_days(研究/回测/交易)](#get_all_trades_days)           | [get\_trade\_days(研究/回测/交易)](#get_trade_days)                  |
| [get\_cb\_list(交易)](#get_cb_list)                                  | [get\_history(回测/交易)](#get_history)                                | [get\_price(研究/回测/交易)](#get_price)                             |
| [get\_individual\_entrust(交易)](#get_individual_entrust)            | [get\_individual\_transaction(交易)](#get_individual_transaction)    | [get\_tick\_direction(交易)](#get_tick_direction)                |
| [get\_sort\_msg(交易)](#get_sort_msg)                                | [get\_etf\_info(交易)](#get_etf_info)                                | [get\_etf\_stock\_info(交易)](#get_etf_stock_info)               |
| [get\_gear\_price(交易)](#get_gear_price)                            | [get\_snapshot(交易)](#get_snapshot)                                 | [get\_stock\_name(研究/回测/交易)](#get_stock_name)                  |
| [get\_stock\_info(研究/回测/交易)](#get_stock_info)                      | [get\_stock\_status(研究/回测/交易)](#get_stock_status)                  | [get\_stock\_exrights(研究/回测/交易)](#get_stock_exrights)          |
| [get\_stock\_blocks(研究/回测/交易)](#get_stock_blocks)                  | [get\_index\_stocks(研究/回测/交易)](#get_index_stocks)                  | [get\_etf\_stock\_list(交易)](#get_etf_stock_list)               |
| [get\_industry\_stocks(研究/回测/交易)](#get_industry_stocks)            | [get\_fundamentals(研究/回测/交易)](#get_fundamentals)                   | [get\_Ashares(研究/回测/交易)](#get_Ashares)                         |
| [get\_etf\_list(交易)](#get_etf_list)                                | [get\_user\_name(回测/交易)](#get_user_name)                           | [get\_research\_path(研究/回测/交易)](#get_research_path)            |
| [get\_trade\_name(交易)](#get_trade_name)                            | [set\_universe(回测/交易)](#set_universe)                              | [order(回测/交易)](#order)                                         |
| [order\_target(回测/交易)](#order_target)                              | [order\_value(回测/交易)](#order_value)                                | [order\_target\_value(回测/交易)](#order_target_value)             |
| [order\_market(交易)](#order_market)                                 | [ipo\_stocks\_order(交易)](#ipo_stocks_order)                        | [after\_trading\_order(交易)](#after_trading_order)              |
| [after\_trading\_cancel\_order(交易)](#after_trading_cancel_order)   | [etf\_basket\_order(交易)](#etf_basket_order)                        | [etf\_purchase\_redemption(交易)](#etf_purchase_redemption)      |
| [get\_positions(回测/交易)](#get_positions)                            | [order\_tick(交易)](#order_tick)                                     | [cancel\_order(回测/交易)](#cancel_order)                          |
| [cancel\_order\_ex(交易)](#cancel_order_ex)                          | [debt\_to\_stock\_order(交易)](#debt_to_stock_order)                 | [get\_open\_orders(回测/交易)](#get_open_orders)                   |
| [get\_order(回测/交易)](#get_order)                                    | [get\_orders(回测/交易)](#get_orders)                                  | [get\_all\_orders(交易)](#get_all_orders)                        |
| [get\_trades(回测/交易)](#get_trades)                                  | [get\_position(回测/交易)](#get_position)                              | [margin\_trade(交易)](#margin_trade)                             |
| [margincash\_open(交易)](#margincash_open)                           | [margincash\_close(交易)](#margincash_close)                         | [margincash\_direct\_refund(交易)](#margincash_direct_refund)    |
| [marginsec\_open(交易)](#marginsec_open)                             | [marginsec\_close(交易)](#marginsec_close)                           | [marginsec\_direct\_refund(交易)](#marginsec_direct_refund)      |
| [get\_margincash\_stocks(交易)](#get_margincash_stocks)              | [get\_marginsec\_stocks(交易)](#get_marginsec_stocks)                | [get\_margin\_contract(交易)](#get_margin_contract)              |
| [get\_margin\_contractreal(交易)](#get_margin_contractreal)          | [get\_margin\_assert(交易)](#get_margin_assert)                      | [get\_assure\_security\_list(交易)](#get_assure_security_list)   |
| [get\_margincash\_open\_amount(交易)](#get_margincash_open_amount)   | [get\_margincash\_close\_amount(交易)](#get_margincash_close_amount) | [get\_marginsec\_open\_amount(交易)](#get_marginsec_open_amount) |
| [get\_marginsec\_close\_amount(交易)](#get_marginsec_close_amount)   | [get\_margin\_entrans\_amount(交易)](#get_margin_entrans_amount)     | [buy\_open(回测/交易(期货))](#buy_open)                              |
| [sell\_close(回测/交易(期货))](#sell_close)                              | [sell\_open(回测/交易(期货))](#sell_open)                                | [buy\_close(回测/交易(期货))](#buy_close)                            |
| [get\_instruments(回测/交易(期货))](#get_instruments)                    | [log(回测/交易)](#log)                                                 | [is\_trade(回测/交易)](#is_trade)                                  |
| [check\_limit(交易)](#check_limit)                                   | [send\_email(交易)](#send_email)                                     | [send\_qywx(交易)](#send_qywx)                                   |
| [get\_MACD(回测/交易)](#get_MACD)                                      | [get\_KDJ(回测/交易)](#get_KDJ)                                        | [get\_RSI(回测/交易)](#get_RSI)                                    |
| [get\_CCI(回测/交易)](#get_CCI)                                        | [create\_dir(回测/交易)](#create_dir)                                  | [get\_opt\_contracts(研究/回测/交易(期权))](#get_opt_contracts)        |
| [get\_contract\_info(研究/回测/交易(期权))](#get_contract_info)            | [set\_parameters(回测/交易)](#set_parameters)                          | [get\_covered\_lock\_amount(交易(期权))](#get_covered_lock_amount) |
| [get\_covered\_unlock\_amount(交易(期权))](#get_covered_unlock_amount) | [buy\_open(交易(期权))](#option_buy_open)                              | [sell\_close(交易(期权))](#option_sell_close)                      |
| [sell\_open(交易(期权))](#option_sell_open)                            | [buy\_close(交易(期权))](#option_buy_close)                            | [open\_prepared(交易(期权))](#open_prepared)                       |
| [close\_prepared(交易(期权))](#close_prepared)                         | [option\_exercise(交易(期权))](#option_exercise)                       | [option\_covered\_lock(交易(期权))](#option_covered_lock)          |
| [option\_covered\_unlock(交易(期权))](#option_covered_unlock)          | [get\_cb\_info(研究/交易)](#get_cb_info)                               | [get\_enslo\_security\_info(交易)](#get_enslo_security_info)     |
| [get\_ipo\_stocks(交易)](#get_ipo_stocks)                            |                                                                    |                                                                |

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息；

data: 一个字典（dict），key为对应的标的代码（如：'600570.SS'），value为一个字典（dict），包含order（逐笔委托）、tick（当前tick数据）、transcation（逐笔成交）三项

结构如下：

```
{'股票代码':
    {
        'order(最近一条逐笔委托)':DataFrame/None,
        'tick(当前tick数据)':DataFrame,
        'transcation(最近一条逐笔成交)':DataFrame/None,
    }
}
```

每项具体介绍：

```
order - 逐笔委托对应DataFrame包含字段：
    business_time：时间戳毫秒级
    hq_px：价格
    business_amount：委托量
    order_no：委托编号
    business_direction：委托方向
        0 – 卖；
        1 – 买；
        2 – 借入；
        3 – 出借；
    trans_kind：委托类别
        1-- 市价委托；
        2 -- 限价委托；
        3 -- 本方最优；
tick - tick数据对应DataFrame包含字段：
    amount：持仓量
    avg_px：均价
    bid_grp：买档位，dict类型，内容如：{1:[42.71,200,0],2:[42.74,200,0],3:[42.75,700,...，以档位为Key，以list为Value，每个Value包含：委托价格、委托数量和委托笔数；
    business_amount：成交数量；
    business_amount_in：内盘成交量；
    business_amount_out：外盘成交量
    business_balance：成交金额；
    business_count：成交笔数；
    circulation_amount：流通股本；
    close_px：今日收盘
    current_amount：最近成交量(现手)；
    down_px：跌停价格；
    end_trade_date：最后交易日
    entrust_diff：委差；
    entrust_rate：委比；
    high_px：最高价；
    hsTimeStamp：时间戳，格式为YYYYMMDDHHMISS，如20170711141612，表示2017年7月11日14时16分12秒的tick数据信息；
    issue_date：上市日期
    last_px：最新成交价；
    low_px：最低价；
    offer_grp：卖档位，dict类型，内容如：{1:[42.71,200,0],2:[42.74,200,0],3:[42.75,700,...，以档位为Key，以list为Value，每个Value包含：委托价格、委托数量和委托笔数；
    open_px：今开盘价；
    pb_rate：市净率；
    pe_rate：动态市盈率；
    preclose_px：昨收价；
    prev_settlement：昨结算
    px_change_rate: 涨跌幅
    settlement：结算价
    start_trade_date：首个交易日
    tick_size：最小报价单位
    total_bid_turnover: 委买金额
    total_bidqty: 委买量
    total_offer_turnover: 委卖金额
    total_offerqty: 委卖量
    trade_mins：交易时间，距离开盘已过交易时间，如100则表示每日240分钟交易时间中的第100分钟；
    trade_status：交易状态；
        START -- 市场启动(初始化之后，集合竞价前)
        PRETR -- 盘前
        OCALL -- 开始集合竞价
        TRADE -- 交易(连续撮合)
        HALT -- 暂停交易
        SUSP -- 停盘
        BREAK -- 休市
        POSTR -- 盘后
        ENDTR -- 交易结束
        STOPT -- 长期停盘，停盘n天，n>=1
        DELISTED -- 退市
        POSMT -- 盘后交易
        PCALL -- 盘后集合竞价
        INIT -- 盘后固定价格启动前
        ENDPT -- 盘后固定价格闭市阶段
        POSSP -- 盘后固定价格停牌
    turnover_ratio：换手率
    up_px：涨停价格；
    vol_ratio：量比；
    wavg_px：加权平均价；
transcation - 逐笔成交对应DataFrame包含字段：
    business_time：时间戳毫秒级；
    hq_px：价格；
    business_amount：成交量；
    trade_index：成交编号；
    business_direction：成交方向；
        0 – 卖；
        1 – 买；
    buy_no: 叫买方编号；
    sell_no: 叫卖方编号；
    trans_flag: 成交标记；
        0 – 普通成交；
        1 – 撤单成交；
    trans_identify_am: 盘后逐笔成交序号标识；
        0 – 盘中；
        1 – 盘后；
    channel_num: 成交通道信息；
```

返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def tick_data(context,data):
    # 获取买一价
    security = g.security
    current_price = eval(data[security]['tick']['bid_grp'][0])[1][0]
    log.info(current_price)
    # 获取买二价
    # current_price = eval(data[security]['tick']['bid_grp'][0])[2][0]
    # 获取买三量
    # current_amount = eval(data[security]['tick']['bid_grp'][0])[3][1]
    # 获取tick最高价
    # current_high_price = data[security]['tick']['high_px'][0]
    # 最近一笔逐笔成交的成交量
    # transaction = data[security]["transcation"]
    # business_amount = list(transaction["business_amount"])
    # if len(business_amount) > 0:
    #     log.info("最近一笔逐笔成交的成交量：%s" % business_amount[0])
    # 最近一笔逐笔委托的委托类别
    # order = data[security]["order"]
    # trans_kind = list(order["trans_kind"])
    # if len(trans_kind) > 0:
    #     log.info("最近一笔逐笔委托的委托类别：%s" % trans_kind[0])
    if current_price > 38.19:
        # 按买一档价格下单
        order_tick(security, 100, 1)

def handle_data(context, data):
    pass
```

### on\_order\_response - 委托主推(可选)

```python
on_order_response(context, order_list)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该函数会在委托主推回调时响应，比引擎、get\_order()和get\_orders()函数更新Order状态的速度更快，适合对速度要求比较高的策略。

注意事项：

1. 目前可接收股票、可转债、ETF、LOF、期货代码的主推数据。
2. 当接到策略外交易产生的主推时(需券商配置默认不推送)，由于没有对应的Order对象，主推信息中order\_id字段赋值为""。
3. 当在主推里调用委托接口时，需要进行判断处理避免无限迭代循环问题。
4. 当券商配置接收策略外交易产生的主推且策略调用[set\_parameters()](#set_parameters)并设置receive\_other\_response="1"时，策略中将接收非本交易产生的主推。
5. 当策略调用[set\_parameters()](#set_parameters)并设置receive\_cancel\_response="1"，策略接收到撤单成交主推时，主推信息中的order\_id为买入或卖出委托Order对象的order\_id，entrust\_no为撤单委托的委托编号。
6. 撤单委托主推信息中成交数量均处理为正数。

#### 可调用委托接口

|                                                           |                                                                  |                                                             |
| --------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------- |
| [order(回测/交易)](#order)                                    | [order\_target(回测/交易)](#order_target)                            | [order\_value(回测/交易)](#order_value)                         |
| [order\_target\_value(回测/交易)](#order_target_value)        | [order\_market(交易)](#order_market)                               | [ipo\_stocks\_order(交易)](#ipo_stocks_order)                 |
| [after\_trading\_order(交易)](#after_trading_order)         | [after\_trading\_cancel\_order(交易)](#after_trading_cancel_order) | [etf\_basket\_order(交易)](#etf_basket_order)                 |
| [etf\_purchase\_redemption(交易)](#etf_purchase_redemption) | [cancel\_order(回测/交易)](#cancel_order)                            | [margin\_trade(交易)](#margin_trade)                          |
| [margincash\_open(交易)](#margincash_open)                  | [margincash\_close(交易)](#margincash_close)                       | [margincash\_direct\_refund(交易)](#margincash_direct_refund) |
| [margincash\_open(交易)](#marginsec_open)                   | [marginsec\_close(交易)](#marginsec_close)                         | [marginsec\_direct\_refund(交易)](#marginsec_direct_refund)   |
| [get\_user\_name(回测/交易)](#get_user_name)                  | [get\_cb\_list(交易)](#get_cb_list)                                | [get\_instruments(回测/交易(期货))](#get_instruments)             |
| [get\_opt\_contracts(研究/回测/交易(期权))](#get_opt_contracts)   | [get\_contract\_info(研究/回测/交易(期权))](#get_contract_info)          | [set\_parameters(回测/交易)](#set_parameters)                   |
| [get\_cb\_info(研究/交易)](#get_cb_info)                      | [get\_enslo\_security\_info(交易)](#get_enslo_security_info)       |                                                             |

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息；

order\_list：一个列表，当前委托单发生变化时，发生变化的委托单列表。委托单以字典形式展现，内容包括：'entrust\_no'(委托编号), 'error\_info'(错误信息), 'order\_time'(委托时间), 'stock\_code'(股票代码), 'amount'(委托数量), 'price'(委托价格), 'business\_amount'(成交数量), 'status'(委托状态), 'entrust\_type'(委托类别), 'entrust\_prop'(委托属性), 'order\_id'([Order对象](#Order)编号)；

字段备注:

* status -- 委托状态，详见[Order对象](#Order)；
* entrust\_type -- 委托类别(str)
* * 0 -- 委托
  * 2 -- 撤单
  * 4 -- 确认
  * 6 -- 信用融资
  * 7 -- 信用融券
  * 9 -- 信用交易
  entrust\_prop -- 委托属性(str)
  * 0 -- 买卖
  * 1 -- 配股
  * 3 -- 申购
  * 7 -- 转股
  * 9 -- 股息
  * N -- ETF申赎
  * Q -- 对手方最优价格
  * R -- 最优五档即时成交剩余转限价
  * S -- 本方最优价格
  * T -- 即时成交剩余撤销
  * U -- 最优五档即时成交剩余撤销
  * b -- 定价委托
  * c -- 确认委托
  * d -- 限价委托

#### 返回

None

#### 接收到的主推格式如下:

```python
本交易产生的主推：[{'business_amount': 0.0, 'order_id': 'e71d1684c8a74b4ca00b3326c9eb8614', 'order_time': '2022-05-10 15:52:10.780', 'entrust_prop': '0', 'status': '2', 'price': 36.95, 'entrust_no': '700006', 'error_info': '', 'amount': 200, 'stock_code': '600570.SS', 'entrust_type': '0'}]
非本交易产生的主推：[{'business_amount': 0.0, 'order_id': '', 'order_time': '2022-05-10 15:54:30.204', 'entrust_prop': '0', 'status': '2', 'price': 36.95, 'entrust_no': '700008', 'error_info': '', 'amount': 200, 'stock_code': '600570.SS', 'entrust_type': '0'}]
```

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS','002416.SZ']
    set_universe(g.security)
    g.flag = 0

def on_order_response(context, order_list):
    log.info(order_list)
    if(g.flag==0):
        order('600570.SS', 100)
        g.flag = 1
    else:
        log.info("end")

def handle_data(context, data):
    order('600570.SS', 100)
```

### on\_trade\_response - 交易主推(可选)

```python
on_trade_response (context, trade_list)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该函数会在成交主推回调时响应，比引擎和get\_trades()函数更新Order状态的速度更快，适合对速度要求比较高的策略。

注意事项：

1. 目前可接收股票、可转债、ETF、LOF、期货代码的主推数据。
2. 当接到策略外交易产生的主推时(需券商配置默认不推送)，由于没有对应的Order对象，主推信息中order\_id字段赋值为""。
3. 当在主推里调用委托接口时，需要进行判断处理避免无限迭代循环问题。
4. 当券商配置接收策略外交易产生的主推且策略调用[set\_parameters()](#set_parameters)并设置receive\_other\_response="1"时，策略中将接收非本交易产生的主推。
5. 当策略调用[set\_parameters()](#set_parameters)并设置receive\_cancel\_response="1"，策略接收到撤单成交主推时，主推信息中的order\_id为买入或卖出委托Order对象的order\_id，entrust\_no为撤单委托的委托编号。
6. 撤单成交主推信息中成交数量均处理为正数。
7. 部分券商柜台成交主推信息中status字段为""，策略中需予以保护。

#### 可调用委托接口

|                                                           |                                                                  |                                                             |
| --------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------- |
| [order(回测/交易)](#order)                                    | [order\_target(回测/交易)](#order_target)                            | [order\_value(回测/交易)](#order_value)                         |
| [order\_target\_value(回测/交易)](#order_target_value)        | [order\_market(交易)](#order_market)                               | [ipo\_stocks\_order(交易)](#ipo_stocks_order)                 |
| [after\_trading\_order(交易)](#after_trading_order)         | [after\_trading\_cancel\_order(交易)](#after_trading_cancel_order) | [etf\_basket\_order(交易)](#etf_basket_order)                 |
| [etf\_purchase\_redemption(交易)](#etf_purchase_redemption) | [cancel\_order(回测/交易)](#cancel_order)                            | [margin\_trade(交易)](#margin_trade)                          |
| [margincash\_open(交易)](#margincash_open)                  | [margincash\_close(交易)](#margincash_close)                       | [margincash\_direct\_refund(交易)](#margincash_direct_refund) |
| [margincash\_open(交易)](#marginsec_open)                   | [marginsec\_close(交易)](#marginsec_close)                         | [marginsec\_direct\_refund(交易)](#marginsec_direct_refund)   |
| [get\_user\_name(回测/交易)](#get_user_name)                  | [get\_cb\_list(交易)](#get_cb_list)                                | [get\_instruments(回测/交易(期货))](#get_instruments)             |
| [get\_opt\_contracts(研究/回测/交易(期权))](#get_opt_contracts)   | [get\_contract\_info(研究/回测/交易(期权))](#get_contract_info)          | [set\_parameters(回测/交易)](#set_parameters)                   |
| [get\_cb\_info(研究/交易)](#get_cb_info)                      | [get\_enslo\_security\_info(交易)](#get_enslo_security_info)       |                                                             |

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息；

trade\_list：一个列表，当前成交单发生变化时，发生变化的成交单列表。成交单以字典形式展现，内容包括：'entrust\_no'(委托编号), 'business\_time'(成交时间), 'stock\_code'(股票代码), 'entrust\_bs'(成交方向), 'business\_amount'(成交数量), 'business\_price'(成交价格), 'business\_balance'(成交额), 'business\_id'(成交编号), 'status'(委托状态), 'order\_id'([Order对象](#Order)编号)；

字段备注:

* entrust\_bs -- 成交方向(str)，1-买，2-卖；
* status -- 委托状态，详见[Order对象](#Order)；

#### 返回

None

#### 接收到的主推格式如下:

```python
本交易产生的主推：[{'status': '8', 'business_id': '76', 'business_amount': 200, 'order_id': 'e71d1684c8a74b4ca00b3326c9eb8614', 'entrust_no': '700006', 'business_balance': 7390.000000000001, 'business_price': 36.95, 'stock_code': '600570.SS', 'entrust_bs': '1', 'business_time': '2022-05-10 15:51:47'}]
非本交易产生的主推：[{'status': '8', 'business_id': 'b155235000000003', 'business_amount': 200, 'order_id': '', 'entrust_no': '700007', 'business_balance': 3000.0, 'business_price': 15.0, 'stock_code': '000001.SZ', 'entrust_bs': '1', 'business_time': '2022-05-10 15:52:35'}]
```

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS','002416.SZ']
    set_universe(g.security)
    g.flag = 0

def on_trade_response(context, trade_list):
    log.info(trade_list)
    if(g.flag==0):
        order('600570.SS', 100)
        g.flag = 1
    else:
        log.info("end")

def handle_data(context, data):
    order('600570.SS', 100)
```

# 策略API介绍

## 设置函数

### set\_universe-设置股票池

```python
set_universe(security_list)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数用于设置或者更新此策略要操作的股票池。

注意事项：

股票策略中，该函数只用于设定get\_history函数的默认security\_list入参, 除此之外并无其他用处，因此为非必须设定的函数。

#### 参数

security\_list: 股票列表，支持单支或者多支股票(list\[str]/str)

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS','600571.SS']
    # 将g.security中的股票设置为股票池
    set_universe(g.security)

def handle_data(context, data):
    # 获取初始化设定的股票池行情数据
    his = get_history(5, '1d', 'close', security_list=None)
```

### set\_benchmark-设置基准

```python
set_benchmark(sids)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数用于设置策略的比较基准，前端展现的策略评价指标都基于此处设置的基准标的。

注意事项：

此函数只能在initialize使用。

#### 参数

security：股票/指数/ETF代码(str)

#### 默认设置

如果不做基准设置，默认选定沪深300指数(000300.SS)的每日价格作为判断策略好坏和一系列风险值计算的基准。如果要指定其他股票/指数/ETF的价格作为基准，就需要使用set\_benchmark。

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '000001.SZ'
    set_universe(g.security)
    #将上证50（000016.SS）设置为参考基准
    set_benchmark('000016.SS')

def handle_data(context, data):
    order('000001.SZ',100)
```

### set\_commission-设置佣金费率

```python
set_commission(commission_ratio=0.0003, min_commission=5.0, type="STOCK")
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该函数用于设置佣金费率。

注意事项：

关于回测手续费计算：手续费=佣金费+经手费

佣金费=佣金费率\*交易总金额(若佣金费计算后小于设置的最低佣金，则佣金费取最小佣金)

经手费=经手费率(万分之0.487)\*交易总金额

#### 参数

commission\_ratio：佣金费率，默认股票每笔交易的佣金费率是万分之三，ETF基金、LOF基金每笔交易的佣金费率是万分之八。(float)

min\_commission：最低交易佣金，默认每笔交易最低扣5元佣金。(float)

type：交易类型，不传参默认为STOCK(目前只支持STOCK, ETF, LOF)。(string)

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    #将佣金费率设置为万分之三，将最低手续费设置为3元
    set_commission(commission_ratio =0.0003, min_commission=3.0)

def handle_data(context, data):
    pass
```

### set\_fixed\_slippage-设置固定滑点

```python
set_fixed_slippage(fixedslippage=0.0)
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该函数用于设置固定滑点，滑点在真实交易场景是不可避免的，因此回测中设置合理的滑点有利于让回测逼近真实场景。

注意事项：

无

#### 参数

fixedslippage：固定滑点，委托价格与最后的成交价格的价差设置，这个价差是一个固定的值(比如0.02元，撮合成交时委托价格±0.01元)。最终的成交价格=委托价格±float(fixedslippage)/2。

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)
    # 将滑点设置为固定的0.2元，即原本买入交易的成交价为10元，则设置之后成交价将变成10.1元
    set_fixed_slippage(fixedslippage=0.2)

def handle_data(context, data):
    pass
```

### set\_slippage-设置滑点

```python
set_slippage(slippage=0.001)
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该函数用于设置滑点比例，滑点在真实交易场景是不可避免的，因此回测中设置合理的滑点有利于让回测逼近真实场景。

注意事项：

无

#### 参数

slippage：滑点比例，委托价格与最后的成交价格的价差设置，这个价差是当时价格的一个百分比(比如设置0.002时，撮合成交时委托价格±当前周期价格\*0.001)。最终成交价格=委托价格±委托价格\*float(slippage)/2。

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)
    # 将滑点设置为0.002
    set_slippage(slippage=0.002)

def handle_data(context, data):
    pass
```

### set\_volume\_ratio-设置成交比例

```python
set_volume_ratio(volume_ratio=0.25)
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该函数用于设置回测中单笔委托的成交比例，使得盘口流动性方面的设置尽量逼近真实交易场景。

注意事项：

假如委托下单数量大于成交比例计算后的数量，系统会按成交比例计算后的数量撮合，差额部分委托数量不会继续挂单。

#### 参数

volume\_ratio：设置成交比例，默认0.25，即指本周期最大成交数量为本周期市场可成交总量的四分之一(float)

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    #将最大成交数量设置为本周期可成交总量的二分之一
    set_volume_ratio(volume_ratio = 0.5)

def handle_data(context, data):
    pass
```

### set\_limit\_mode-设置成交数量限制模式

```python
set_limit_mode(limit_mode='LIMIT')
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该函数用于设置回测的成交数量限制模式。对于月度调仓等低频策略，对流动性冲击不是很敏感，不做成交量限制可以让回测更加便捷。

注意事项：

不做限制之后实际撮合成交量是可以大于该时间段的实际成交总量。

#### 参数

limit\_mode：设置成交数量限制模式，即指回测撮合交易时对成交数量是否做限制进行控制(str)

默认为限制，入参'LIMIT'，不做限制则入参'UNLIMITED'

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    #回测中不限制成交数量
    set_limit_mode('UNLIMITED')

def handle_data(context, data):
    pass
```

### set\_yesterday\_position – 设置底仓

```python
set_yesterday_position(poslist)
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该函数用于设置回测的初始底仓。

注意事项：

该函数会使策略初始化运行就创建出持仓对象，里面包含了设置的持仓信息。

#### 参数

poslist：list类型数据，该list中是字典类型的元素，参数不能为空(list\[dict\[str:str],...])；

数据格式及参数字段如下：

```
[{
    'sid':标的代码,
    'amount':持仓数量,
    'enable_amount':可用数量,
    'cost_basis':每股的持仓成本价格,
}]
```

参数也可通过csv文件的形式传入，参考接口[convert\_position\_from\_csv](#convert_position_from_csv)

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    # 设置底仓
    pos={}
    pos['sid'] = "600570.SS"
    pos['amount'] = "1000"
    pos['enable_amount'] = "600"
    pos['cost_basis'] = "55"
    set_yesterday_position([pos])

def handle_data(context, data):
    #卖出100股
    order(g.security,-100)
```

### set\_parameters - 设置策略配置参数

```python
set_parameters(**kwargs)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数用于设置策略中的配置参数。

注意事项：

该函数入参格式必须为a=b样式。

#### 支持的参数

holiday\_not\_do\_before：交易中节假日是否执行before\_trading\_start。缺省，执行；1，不执行。

tick\_data\_no\_l2：tick\_data中data是否包含order和transcation。缺省，包含；1，不包含。

receive\_other\_response：策略中是否接收非本交易产生的主推。缺省，不接收；1，接收。

receive\_cancel\_response：策略中是否接收撤单委托产生的主推。缺省，不接收；1，接收。

#### 返回

None

#### 示例

```python
def initialize(context):
    # 初始化策略
    g.security = "600570.SS"
    set_universe(g.security)
    # 设置非交易日不执行before_trading_start
    # 设置tick_data中data不包含order和transaction
    # 设置接收非本交易产生的主推
    # 设置接收撤单委托产生的主推
    set_parameters(holiday_not_do_before="1", tick_data_no_l2="1", receive_other_response="1",
                   receive_cancel_response="1")

def before_trading_start(context, data):
    log.info("do before_trading_start")
    g.count = 0

def on_order_response(context, order_list):
    log.info("委托主推：%s" % order_list)

def on_trade_response(context, trade_list):
    log.info("成交主推：%s" % trade_list)

def tick_data(context, data):
    if g.count == 0:
        log.info(data[g.security])
        g.count += 1

def handle_data(context, data):
    pass
```

## 定时周期性函数

### run\_daily-按日周期处理

```python
run_daily(context, func, time='9:31')
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该函数用于以日为单位周期性运行指定函数，可对运行触发时间进行指定。

注意事项：

1、该函数只能在初始化阶段initialize函数中调用。

2、该函数可以多次设定，以实现多个定时任务。

3、股票策略回测中，当回测周期为分钟时，time的取值指定在09:31\~11:30与13:00\~15:00之间，当回测周期为日时，无论设定值是多少都只会在15:00执行；交易中不受此时间限制。

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息(Context)；

func：自定义函数名称，此函数必须以context作为参数(Callable\[\[Context], None])；

time：指定周期运行具体触发运行时间点，交易场景可设置范围：00:00\~23:59，必传字段。

#### 返回

None

#### 示例

```python
# 定义一个财务数据获取函数，每天执行一次 
def initialize(context):
    run_daily(context, get_finance, time='9:31')
    g.security = '600570.SS'
    set_universe(g.security)

def get_finance(context):
    re = get_fundamentals(g.security,'balance_statement','total_assets')
    log.info(re)

def handle_data(context, data):
    pass
```

### run\_interval - 按设定周期处理

```python
run_interval(context, func, seconds=10)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该函数用于以设定时间间隔（单位为秒）周期性运行指定函数，可对运行触发时间间隔进行指定。

注意事项：

1、该函数只能在初始化阶段initialize函数中调用。

2、该函数可以多次设定，会以多个线程并行运行，但要小心不同线程之间的逻辑关联处理

3、seconds设置最小时间间隔为3秒，小于3秒默认设定为3秒。

#### 参数

context: [Context对象](#Context)，存放有当前的账户及持仓信息(Context)；

func：自定义函数名称，此函数必须以context作为参数(Callable\[\[Context], None])；

seconds：设定时间间隔（单位为秒），取值为正整数(int)。

#### 返回

None

#### 示例

```python
# 定义一个周期处理函数，每10秒执行一次 
def initialize(context):
    run_interval(context, interval_handle, seconds = 10)
    g.security = '600570.SS'
    set_universe(g.security)

def interval_handle(context):
    snapshot = get_snapshot(g.security)
    log.info(snapshot)

def handle_data(context, data):
    pass
```

## 获取信息函数

### 获取基础信息

### get\_trading\_day - 获取交易日期

```python
get_trading_day(day)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该函数用于获取当前时间数天前或数天后的交易日期。

注意事项：

1、默认情况下，回测中当前时间为策略中调用该接口的回测日日期(context.blotter.current\_dt)。

2、默认情况下，研究中当前时间为调用当天日期。

3、默认情况下，交易中当前时间为调用当天日期。

#### 参数

day：表示天数，正的为数天后，负的为数天前，day取0表示获取当前交易日，如果当前日期为非交易日则返回上一交易日的日期。day默认取值为0，不建议获取交易所还未公布的交易日期(int)；

#### 返回

date：datetime.date日期对象

#### 示例

```python
def initialize(context):
    g.security = ['600670.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    # 获取后一天的交易日期
    previous_trading_date = get_trading_day(1)
    log.info(previous_trading_date)
    # 获取前一天的交易日期
    next_trading_date = get_trading_day(-1)
    log.info(next_trading_date)
```

### get\_all\_trades\_days - 获取全部交易日期

```python
get_all_trades_days(date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该函数用于获取某个日期之前的所有交易日日期。

注意事项：

1、默认情况下，回测中date为策略中调用该接口的回测日日期(context.blotter.current\_dt)。

2、默认情况下，研究中date为调用当天日期。

3、默认情况下，交易中date为调用当天日期。

#### 参数

date：如'2016-02-13'或'20160213'

#### 返回

一个包含所有交易日的numpy.ndarray

#### 示例

```python
def initialize(context):
    # 获取当前回测日期之前的所有交易日
    all_trades_days = get_all_trades_days()
    log.info(all_trades_days)
    all_trades_days_date = get_all_trades_days('20150312')
    log.info(all_trades_days_date)
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    pass
```

### get\_trade\_days - 获取指定范围交易日期

```python
get_trade_days(start_date=None, end_date=None, count=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该函数用于获取指定范围交易日期。

注意事项：

1、默认情况下，回测中end\_date为策略中调用该接口的回测日日期(context.blotter.current\_dt)。

2、默认情况下，研究中end\_date为调用当天日期。

3、默认情况下，交易中end\_date为调用当天日期。

#### 参数

start\_date：开始日期，与count二选一，不可同时使用。如'2016-02-13'或'20160213',开始日期最早不超过1990年(str)；

end\_date：结束日期，如'2016-02-13'或'20160213'。如果输入的结束日期大于今年则至多返回截止到今年的数据(str)；

count：数量，与start\_date二选一，不可同时使用，必须大于0。表示获取end\_date往前的count个交易日，包含end\_date当天。count建议不大于3000，即返回数据的开始日期不早于1990年(int)；

#### 返回

一个包含指定范围交易日的numpy.ndarray

#### 示例

```python
def initialize(context):
    # 获取指定范围内交易日
    trade_days = get_trade_days('2016-01-01', '2016-02-01')
    log.info(trade_days)
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    # 获取回测日期往前10天的所有交易日，包含历史回测日期
    trading_days = get_trade_days(count=10)
    log.info(trading_days)
```

### 获取市场信息

<!--
                      <h3 id="get_market_value">get_market_value- 获取当前市值</h3>
                      <pre class="prettyprint"><code class="language-python">get_market_value(security,fields=None)</code></pre>
                      <p>获取一支或者多只股票的市值数据。</p>
                      <h4>参数</h4>
                      <p>security: 一支股票代码或者一个股票代码的list。</p>
                      <p>fields: 需获取的数据字段字符串，list类型，支持字段包括：prod_name-股票名称/market_value-总市值/circulation_amount-流通股本/circulation_value-流通市值/dyn_pb_rate-市净率/pe_rate-市盈率/ipo_price-IPO价格/issue_date-上市日期/eps-每股收益/bps-每股净资产/iopv-基金净值</p>
                      <h4>返回</h4>
                      <p>返回数据类型：pandas.DataFrame类型。</p>
                      <p>返回包含fields设定的字段，或者目前所支持的11个字段。</p>
                  <h4>示例</h4>
                      <pre class="prettyprint"><code class="language-python"># 获取一支股票600570.SS(恒生电子)最新的市场数据
      get_market_value('600570.SS')
      
      # 获取一支股票600570.SS(恒生电子)最新的市场数据中prod_name和market_value两个字段的数据 
      get_market_value('600570.SS', ['prod_name','market_value'])
      
      # 获取多只股票，如获取600570.SS(恒生电子)，600571.SS(信雅达)的最新市场数据
      get_market_value(['600570.SS','600571.SS'])
      
      # 获取多只股票某些字段的市场数据，如获取600570.SS(恒生电子)，600571.SS(信雅达)
      #'prod_name','market_value'两个字段的市场数据
      get_market_value(['600570.SS','600571.SS'],['prod_name','market_value'])</code></pre>
                      -->

### get\_market\_list-获取市场列表

```python
get_market_list()
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该函数用于返回当前市场列表目录。

注意事项：

回测和交易中仅限before\_trading\_start和after\_trading\_end中使用

#### 参数

无

#### 返回

返回pandas.DataFrame对象，返回字段包括:

finance\_mic – 市场编码(str:str)

finance\_name – 市场名称(str:str)

#### 示例

```python
get_market_list()
```

如返回：

|    | finance\_mic | finance\_name |
| -- | ------------ | ------------- |
| 0  | A            | 美国证券交易所       |
| 1  | CBJC         | 北京邮票          |
| 2  | CBOT         | 芝加哥商品期货       |
| 3  | CCFX         | 中国金融期货交易所     |
| 4  | CCGG         | 中国国际文交所       |
| 5  | CCJC         | 卡巴拉长江交易所      |
| …  | …            | …             |
| 66 | XFUND        | 基金            |
| 67 | XHKG-SS      | 沪港通           |
| 68 | XHKG-SZ      | 深港通           |
| 69 | XSGE         | 上海期货交易所       |
| 70 | XSHO         | 上海个股期权        |
| 71 | XZCE         | 郑州商品交易所       |
| 72 | YCME         | 渝川玉石          |

### get\_market\_detail-获取市场详细信息

```python
get_market_detail(finance_mic)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该函数用于返回市场编码对应的详细信息。

注意事项：

回测和交易中仅限before\_trading\_start和after\_trading\_end中使用

#### 参数

finance\_mic: 市场代码，相关市场编码参考get\_market\_list返回信息(str)。

#### 返回

返回市场详细信息，类型为pandas.DataFrame对象，返回字段包括：

产品代码: prod\_code(str:str)

产品名称: prod\_name(str:str)

类型代码: hq\_type\_code(str:str)

时间规则: trade\_time\_rule(str:numpy.int64)

返回如下:

```python
      hq_type_code prod_code prod_name  trade_time_rule
0              MRI    000001      上证指数                0
1              MRI    000002      Ａ股指数                0
2              MRI    000003      Ｂ股指数                0
3              MRI    000004      工业指数                0
4              MRI    000005      商业指数                0
5              MRI    000006      地产指数                0
6              MRI    000007      公用指数                0
7              MRI    000008      综合指数                0
```

#### 示例

```python
# 获取上海证券交易所相关信息 'XSHG'/'SS'
get_market_detail('XSHG')
```

### get\_cb\_list-获取可转债市场代码表

```python
get_cb_list()
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

返回当前可转债市场的所有代码列表(包含停牌代码)。

注意事项：

为减小对行情服务压力，该函数在交易模块中同一分钟内多次调用返回当前分钟首次查询的缓存数据。

#### 参数

无

#### 返回

返回当前可转债市场的所有代码列表(包含停牌代码)(list)。失败则返回空列表\[]。

### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)
    run_daily(context, get_trade_cb_list, "9:25")


def before_trading_start(context, data):
    # 每日清空，避免取到昨日市场代码表
    g.trade_cb_list = []


def handle_data(context, data):
    pass


# 获取当天可交易的可转债代码列表
def get_trade_cb_list(context):
    cb_list = get_cb_list()
    cb_snapshot = get_snapshot(cb_list)
    # 代码有行情快照并且交易状态不在暂停交易、停盘、长期停盘、退市状态的判定为可交易代码
    g.trade_cb_list = [cb_code for cb_code in cb_list if
                       cb_snapshot.get(cb_code, {}).get("trade_status") not in
                       [None, "HALT", "SUSP", "STOPT", "DELISTED"]]
    log.info("当天可交易的可转债代码列表为：%s" % g.trade_cb_list)
```

### 获取行情信息

#### get\_history - 获取历史行情

```python
get_history(count, frequency='1d', field='close', security_list=None, fq=None, include=False, fill='nan', is_dict=False)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取最近N条历史行情K线数据。支持多股票、多行情字段获取。

注意事项：

该接口只能获取2005年后的数据。

针对停牌场景，我们没有跳过停牌的日期，无论对单只股票还是多只股票进行调用，时间轴均为二级市场交易日日历，停牌时使用停牌前的数据填充，成交量为0，日K线可使用成交量为0的逻辑进行停牌日过滤。

#### 参数

count： K线数量，大于0，返回指定数量的K线行情；必填参数；入参类型：int；

frequency：K线周期，现有支持1分钟线(1m)、5分钟线(5m)、15分钟线(15m)、30分钟线(30m)、60分钟线(60m)、120分钟线(120m)、日线(1d)、周线(1w/weekly)、月线(mo/monthly)、季度线(1q/quarter)和年线(1y/yearly)频率的数据；选填参数，默认为'1d'；入参类型：str；

field：指明数据结果集中所支持输出的行情字段；选填参数，默认为\['open','high','low','close','volume','money','price']；入参类型：list\[str,str]或str；输出字段包括：

* open -- 开盘价，字段返回类型：numpy.float64；
* high -- 最高价，字段返回类型：numpy.float64；
* low --最低价，字段返回类型：numpy.float64；
* close -- 收盘价，字段返回类型：numpy.float64；
* volume -- 交易量，字段返回类型：numpy.float64；
* money -- 交易金额，字段返回类型：numpy.float64；
* price -- 最新价，字段返回类型：numpy.float64；
* preclose -- 昨收盘价，字段返回类型：numpy.float64(仅日线返回)；
* high\_limit -- 涨停价，字段返回类型：numpy.float64(仅日线返回)；
* low\_limit -- 跌停价，字段返回类型：numpy.float64(仅日线返回)；
* unlimited -- 判断查询日是否是无涨跌停限制(1:该日无涨跌停限制;0:该日不是无涨跌停限制)，字段返回类型：numpy.float64(仅日线返回)；

security\_list：要获取数据的股票列表；选填参数，None表示在上下文中的universe中选中的所有股票；入参类型：list\[str,str]或str；

fq：数据复权选项，支持包括，pre-前复权，post-后复权，dypre-动态前复权，None-不复权；选填参数，默认为None；入参类型：str；

include：是否包含当前周期，True –包含，False-不包含；选填参数，默认为False；入参类型：bool；

fill：行情获取不到某一时刻的分钟数据时，是否用上一分钟的数据进行填充该时刻数据，'pre'–用上一分钟数据填充，'nan'–NaN进行填充(仅交易有效)；选填参数，默认为'nan'；入参类型：str；

is\_dict：返回是否是字典(dict)格式{str: array()}，True –是，False-不是；选填参数，默认为False；返回为字典格式取数速度相对较快；入参类型：bool；

#### 返回

##### 第一种返回数据：

当获取单支股票（单只股票必须为字符串类型security\_list='600570.SS'，不能用security\_list=\['600570.SS']）的时候，无论行情字段field入参单个或多个，返回的都是pandas.DataFrame对象，行索引是datetime.datetime对象，列索引是行情字段,为str类型。比如：

如果当前时间是2017-04-18，get\_history(5, '1d', 'open', '600570.SS', fq=None, include=False)将返回：

|            | open  |
| ---------- | ----- |
| 2017-04-11 | 40.30 |
| 2017-04-12 | 40.08 |
| 2017-04-13 | 40.03 |
| 2017-04-14 | 40.04 |
| 2017-04-17 | 39.90 |

##### 第二种返回数据：

当获取多支股票（多只股票必须为list类型，特殊情况：当list只有一个股票时仍然当做多股票处理，比如security\_list=\['600570.SS']）的时候，如果行情字段field入参为单个，返回的是pandas.DataFrame对象，行索引是datetime.datetime对象，列索引是股票代码的编号,为str类型。比如：

如果当前时间是2017-04-18，get\_history(5, '1d', 'open', \['600570.SS','600571.SS'], fq=None, include=False)将返回：

|            | 600570.SS | 600571.SS |
| ---------- | --------- | --------- |
| 2017-04-11 | 40.30     | 17.81     |
| 2017-04-12 | 40.08     | 17.56     |
| 2017-04-13 | 40.03     | 17.42     |
| 2017-04-14 | 40.04     | 17.40     |
| 2017-04-17 | 39.90     | 17.49     |

##### 第三种返回数据：

当获取多支股票（多只股票必须为list类型，特殊情况：当list只有一个股票时仍然当做多股票处理，比如security\_list=\['600570.SS']）的时候，如果行情字段field入参为多个，则返回pandas.Panel对象，items索引是行情字段（如'open'、'close'等），里面是很多pandas.DataFrame对象，每个pandas.DataFrame的行索引是datetime.datetime对象， 列索引是股票代码,为str类型，比如:

如果当前时间是2015-01-07，get\_history(2, frequency='1d', field=\['open','close'], security\_list=\['600570.SS', '600571.SS'], fq=None, include=False)\['open']将返回:

|            | 600570.SS | 600571.SS |
| ---------- | --------- | --------- |
| 2015-01-05 | 54.77     | 26.93     |
| 2015-01-06 | 51.00     | 25.83     |

假如要对panel索引中的对象进行转换，比如将items索引由行情字段转换成股票代码，可以通过panel\_info = panel\_info.swapaxes("minor\_axis", "items")的方法转换。

比如:

panel\_info = get\_history(2, frequency='1d', field=\['open','close'], security\_list=\['600570.SS', '600571.SS'], fq=None, include=False)

按默认索引：df = panel\_info\['open']

对默认索引做转换：panel\_info = panel\_info.swapaxes("minor\_axis", "items")

转换之后的索引：df = panel\_info\['600570.SS']

关于numpy和pandas，请看下面的第三方库介绍。

### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def before_trading_start(context, data):
    # 获取农业版块过去10天的每日收盘价
    industry_info = get_history(10, frequency="1d", field="close", security_list="A01000.XBHS")
    log.info(industry_info)

def handle_data(context, data):
    # 股票池中全部股票过去5天的每日收盘价
    his = get_history(5, '1d', 'close', security_list=g.security)
    log.info('股票池中全部股票过去5天的每日收盘价')
    log.info(his)

    # 获取600570(恒生电子)过去5天的每天收盘价,
    # 一个pd.Series对象, index是datatime
    log.info('获取600570(恒生电子)过去5天的每天收盘价')
    log.info(his['600570.SS'])

    # 获取600570(恒生电子)昨天(数组最后一项)的收盘价
    log.info('获取600570(恒生电子)昨天的收盘价')
    log.info(his['600570.SS'][-1])

    # 获取股票池中全部股票昨天的收盘价
    log.info('获取股票池中全部股票昨天的收盘价')
    log.info(his.iloc[-1])

    # 获取600570(恒生电子)昨天(数组最后一项)的收盘价
    log.info('获取600570(恒生电子)昨天的收盘价')
    log.info(his.iloc[-1]['600570.SS'])

    # 取得每一列的平均值
    log.info('取得每一列的平均值')
    log.info(his.mean())

    # 获取股票池中全部股票的过去10分钟的成交量
    his1 = get_history(10, '1m', 'volume')
    log.info('获取股票池中全部股票的过去10分钟的成交量')
    log.info(his1)

    # 获取恒生电子的过去5天的每天的收盘价
    his2 = get_history(5, '1d', 'close', security_list='600570.SS')
    log.info('获取恒生电子的过去5天的每天的收盘价')
    log.info(his2)

    # 获取恒生电子的过去5天的每天的后复权收盘价
    his3 = get_history(5, '1d', 'close', security_list='600570.SS', fq='post')
    log.info('获取恒生电子的过去5天的每天的后复权收盘价')
    log.info(his3)

    # 获取恒生电子的过去5周的每周的收盘价
    his4 = get_history(5, '1w', 'close', security_list='600570.SS')
    log.info('获取恒生电子的过去5天的每天的收盘价')
    log.info(his4)

    # 获取多只股票的开盘价和收盘价数据
    panel_info = get_history(2, frequency='1d', field=['open','close'], security_list=g.security)
    open_df = panel_info['open']
    log.info('获所有股票的取开盘价数据')
    log.info(open_df)
    df = open_df['600570.SS']
    log.info('仅获取恒生电子的开盘价数据')
    log.info(df)
    
    # panel索引中的对象进行转换
    panel_info2 = panel_info.swapaxes("minor_axis", "items")
    df = panel_info2['600570.SS']
    log.info('仅获取恒生电子的开盘价和收盘价数据')
    log.info(df)
    open_df = df['open']
    log.info('获取恒生电子的开盘价数据')
    log.info(open_df)
```

### get\_price - 获取历史数据

```python
get_price(security, start_date=None, end_date=None, frequency='1d', fields=None, fq=None, count=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口用于获取指定日期的前N条的历史行情K线数据或者指定时间段内的历史行情K线数据。支持多股票、多行情字段获取。

注意事项：

1、start\_date与count必须且只能选择输入一个，不能同时输入或者同时都不输入。

2、针对停牌场景，我们没有跳过停牌的日期，无论对单只股票还是多只股票进行调用，时间轴均为二级市场交易日日历，停牌时使用停牌前的数据填充，成交量为0，日K线可使用成交量为0的逻辑进行停牌日过滤。

3、数据返回内容不包括当天数据。

4、count只针对'daily', 'weekly', 'monthly', 'quarter', 'yearly', '1d', '1m', '5m', '15m', '30m', '60m', '120m', '1w', 'mo', '1q', '1y'频率有效，并且输入日期的类型需与频率对应。

5、'weekly', '1w', 'monthly', 'mo', 'quarter', '1q', 'yearly', '1y'频率不支持start\_date和end\_date组合的入参，只支持end\_date和count组合的入参形式。

6、返回的周线数据是由日线数据进行合成。

7、该接口只能获取2005年后的数据。

#### 参数

security：一支股票代码或者一个股票代码的list(list\[str]/str)

start\_date：开始时间，默认为空。传入格式仅支持：YYYYmmdd、YYYY-mm-dd、YYYY-mm-dd HH:MM、YYYYmmddHHMM，如'20150601'、'2015-06-01'、'2015-06-01 10:00'、'201506011000'(str)；

end\_date：结束时间，默认为空，传入格式仅支持：YYYYmmdd、YYYY-mm-dd、YYYY-mm-dd HH:MM、YYYYmmddHHMM，如'20150601'、'2015-06-01'、'2015-06-01 14:00'、'201506011400'(str)；

frequency： 单位时间长度，现有支持1分钟线(1m)、5分钟线(5m)、15分钟线(15m)、30分钟线(30m)、60分钟线(60m)、120分钟线(120m)、日线(1d)、周线(1w/weekly)、月线(mo/monthly)、季度线(1q/quarter)和年线(1y/yearly)频率数据(str)；

fields：指明数据结果集中所支持输出字段(list\[str]/str)，输出字段包括 ：

* open -- 开盘价(str:numpy.float64)；
* high -- 最高价(str:numpy.float64)；
* low --最低价(str:numpy.float64)；
* close -- 收盘价(str:numpy.float64)；
* volume -- 交易量(str:numpy.float64)；
* money -- 交易金额(str:numpy.float64)；
* price -- 最新价(str:numpy.float64)；
* preclose -- 昨收盘价(str:numpy.float64)(仅日线返回)；
* high\_limit -- 涨停价(str:numpy.float64)(仅日线返回)；
* low\_limit -- 跌停价(str:numpy.float64)(仅日线返回)；
* unlimited -- 判断查询日是否无涨跌停限制(1：该日无涨跌停限制；0：该日有涨跌停限制)(str:numpy.float64)(仅日线返回)；

fq：数据复权选项，支持包括，pre-前复权，post-后复权，None-不复权(str)；

count：大于0，不能与start\_date同时输入，获取end\_date前count根的数据，不支持除天（'daily'/'1d'）、分钟（'1m'）、5分钟线('5m')、15分钟线('15m')、30分钟线('30m')、60分钟线('60m')、120分钟线('120m')、周（'weekly'/'1w'）、（'monthly'/'mo'）、（'quarter'/'1q'）和（'yearly'/'1y'）以外的其它频率(int)；

#### 返回

get\_price对于多股票和多字段不同场景下获取返回数据的规则与[get\_history](#get_history)一致，如下：

##### 第一种返回数据：

当获取单支股票（单只股票必须为字符串类型security='600570.SS'，不能用security=\['600570.SS']）和单个或多个字段的时候，返回的是pandas.DataFrame对象，行索引是datetime.datetime对象，列索引是行情字段，为str类型。

例如，输入为get\_price(security='600570.SS',start\_date='20170201',end\_date='20170213',frequency='1d')时，将返回：

```python

                 open	close	 high	 low	 volume	        price	   money     preclose    high_limit    low_limit    unlimited
2017-02-03	44.47	43.90	44.50	43.58	4418325.0	43.90	193895820.0	44.26	   48.69	39.83   	0
2017-02-06	43.91	44.10	44.30	43.66	4428487.0	44.10	194979290.0	43.90	   48.29	39.51   	0
2017-02-07	44.05	43.52	44.07	43.34	5649251.0	43.52	246776480.0	44.10	   48.51	39.69   	0
2017-02-08	43.59	44.59	44.78	43.53	12570233.0	44.59	557883600.0	43.52	   47.87	39.17   	0
2017-02-09	44.74	44.74	45.28	44.39	9240223.0	44.74	413875390.0	44.59	   49.05	40.13   	0
2017-02-10	44.80	44.62	44.98	44.41	8097465.0	44.62	361757300.0	44.74	   49.21	40.27   	0
2017-02-13	44.32	44.89	45.98	44.02	14931596.0	44.89	672360490.0	44.62	   49.08	40.16   	0
```

##### 第二种返回数据：

当获取多支股票（多只股票必须为list类型，特殊情况：当list只有一个股票时仍然当做多股票处理，比如security=\['600570.SS']）和单个字段的时候，返回的是pandas.DataFrame对象，行索引是datetime.datetime对象，列索引是股票代码的编号，为str类型。

例如，输入为get\_price(\['600570.SS'], start\_date='20170201', end\_date='20170213', frequency='1d', fields='open')时，将返回：

```python

              600570.SS
2017-02-03      44.47
2017-02-06      43.91
2017-02-07      44.05
2017-02-08      43.59
2017-02-09      44.74
2017-02-10      44.80
2017-02-13      44.32
```

##### 第三种返回数据：

如果是获取多支股票（多只股票必须为list类型，特殊情况：当list只有一个股票时仍然当做多股票处理，比如security=\['600570.SS']）和多个字段，则返回pandas.Panel对象，items索引是行情字段，为str类型（如'open'、'close'等），里面是很多pandas.DataFrame对象，每个pandas.DataFrame的行索引是datetime.datetime对象， 列索引是股票代码，为str类型。

例如，输入为get\_price(\['600570.SS','600571.SS'], start\_date='20170201', end\_date='20170213', frequency='1d', fields=\['open','close'])\['open']时，将返回：

```python

             600570.SS   600571.SS
2017-02-03    44.47        19.36
2017-02-06    43.91        19.00
2017-02-07    44.05        19.27
2017-02-08    43.59        19.10
2017-02-09    44.74        19.47
2017-02-10    44.80        19.57
2017-02-13    44.32        19.22
```

假如要对panel索引中的对象进行转换，比如将items索引由行情字段转换成股票代码，可以通过panel\_info = panel\_info.swapaxes("minor\_axis", "items")的方法转换。

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获得600570.SS(恒生电子)的2015年01月的天数据，只获取open字段
    price_open = get_price('600570.SS', start_date='20150101', end_date='20150131', frequency='1d')['open']
    log.info(price_open)
    # 获取指定结束日期前count天到结束日期的所有开盘数据
    # price_open = get_price('600570.SS', end_date='20150131', frequency='daily', count=10)['open']
    # log.info(price_open)
    # 获取股票指定结束时间前count分钟到指定结束时间的所有数据
    # stock_info = get_price('600570.SS', end_date='2015-01-31 10:00', frequency='1m', count=10)
    # log.info(stock_info)
    # 获取指定结束日期前count周到结束日期所在周的所有开盘数据
    # week_open = get_price('600570.SS', end_date='20150131', frequency='1w', count=10)['open']
    # log.info(week_open)

    # 获取多只股票
    # 获取沪深300的2015年1月的天数据，返回一个[pandas.Panel]
    security_list = get_index_stocks('000300.XBHS', '20150101')
    price = get_price(security_list, start_date='20150101', end_date='20150131')
    log.info(price)
    # 获取某股票开盘价，行索引是[datetime.datetime]对象，列索引是行情字段
    price_open = price['open'][security_list[0]]
    log.info(price_open)

    # 获取农业版块指定结束日期前count天到结束日期的数据
    industry_info = get_price("A01000.XBHS", end_date="20210315", frequency="daily", count=10)
    log.info(industry_info)
```

### get\_individual\_entrust– 获取逐笔委托行情

```python
get_individual_entrust(stocks=None, data_count=50, start_pos=0, search_direction=1)
```

#### 使用场景

该函数在交易模块可用

#### 接口说明

该接口用于获取当日逐笔委托行情数据。

注意事项：

1、沪深市场都有逐笔委托数据；

2、逐笔委托，逐笔成交数据需开通level2行情才能获取到数据，否则无数据返回；

#### 参数

stocks: 默认为当前股票池中代码列表(list\[str])；

data\_count: 数据条数，默认为50，最大为200(int)；

start\_pos: 起始位置，默认为0(int)；

search\_direction: 搜索方向（1向前，2向后），默认为1(int)；

#### 返回

正常返回Pandas.panel对象，异常时返回None。

Items axis: 股票代码列表(str)；

Major\_axis axis: 数据索引为自然数列(DataFrame)；

Minor\_axis axis: 包含以下信息：

* business\_time: 时间戳毫秒级(str:numpy.int64)；
* hq\_px: 价格(str:numpy.int64)；
* business\_amount: 委托数量(str:numpy.int64)；
* order\_no: 委托编号(str:numpy.int64)；
* business\_direction: 委托方向，0:卖，1:买，2:借入，3:出借(str:numpy.int64)；
* trans\_kind: 委托类别，深圳市场(1:市价委托，2:限价委托，3:本方最优)，上海市场(4:增加订单 5:删除订单)(str:numpy.int64)；

#### 示例

```python
def initialize(context):
    g.security = "000001.SZ"
    set_universe(g.security)

def handle_data(context, data):
    # 获取当前股票池逐笔委托数据
    entrust = get_individual_entrust()
    log.info(entrust)

    # 获取指定股票列表逐笔委托数据
    entrust = get_individual_entrust(["000002.SZ", "000032.SZ"])
    log.info(entrust)

    # 获取委托量
    if entrust is not None:
        business_amount = entrust["000002.SZ"]["business_amount"]
        log.info("逐笔数据的委托量为：%s" % business_amount)
```

### get\_individual\_transaction – 获取逐笔成交行情

```python
get_individual_transaction(stocks=None, data_count=50, start_pos=0, search_direction=1)
```

#### 使用场景

该函数在交易模块可用

#### 接口说明

该接口用于获取当日逐笔成交行情数据。

注意事项：

1、沪深市场都有逐笔成交数据；

2、逐笔委托，逐笔成交数据需开通level2行情才能获取到数据，否则无数据返回；

#### 参数

stocks: 默认为当前股票池中代码列表(list\[str])；

data\_count: 数据条数，默认为50，最大为200(int)；

start\_pos: 起始位置，默认为0(int)；

search\_direction: 搜索方向（1向前，2向后），默认为1(int)；

#### 返回

正常返回Pandas.panel对象，异常时返回None。

Items axis: 股票代码列表(str)；

Major\_axis axis: 数据索引为自然数列(DataFrame)；

Minor\_axis axis: 包含以下信息：

* business\_time: 时间戳毫秒级(str:numpy.int64)；
* hq\_px: 价格(str:numpy.float64)；
* business\_amount: 成交数量(str:numpy.int64)；
* trade\_index: 成交编号(str:numpy.int64)；
* business\_direction: 成交方向，0:卖，1:买，2:借入，3:出借(str:numpy.int64)；
* buy\_no: 叫买方编号(str:numpy.int64)；
* sell\_no: 叫卖方编号(str:numpy.int64)；
* trans\_flag: 成交标记（0：普通成交，1：撤单成交）(str:numpy.int64)；
* trans\_identify\_am: 盘后逐笔成交序号标识(0表示盘中，1表示盘后)(str:numpy.int64)；
* channel\_num: 成交通道信息(str:numpy.int64)；

#### 示例

```python
def initialize(context):
    g.security = "000001.SZ"
    set_universe(g.security)

def handle_data(context, data):
    # 获取当前股票池逐笔成交数据
    transaction = get_individual_transaction()
    log.info(transaction)

    # 获取指定股票列表逐笔成交数据
    transaction = get_individual_transaction(["000002.SZ", "000032.SZ"])
    log.info(transaction)

    # 获取成交量
    if transaction is not None:
        business_amount = transaction["000002.SZ"]["business_amount"]
        log.info("逐笔数据的成交量为：%s" % business_amount)
```

### get\_tick\_direction– 获取分时成交行情

```python
get_tick_direction(symbols=None, query_date=0, start_pos=0, search_direction=1, data_count=50)
```

#### 使用场景

该函数在交易模块可用

#### 接口说明

该接口用于获取当日分时成交行情数据。

注意事项：

1、沪深市场都有分时成交数据；

2、分时成交数据需开通level2行情才有数据推送，否则无数据返回；

#### 参数

symbols: 默认为当前股票池中代码列表(list\[str])；

query\_date: 查询日期，默认为0，返回当日日期数据(目前行情只支持查询当日的数据，格式为YYYYMMDD)(int)；

start\_pos: 起始位置，默认为0(int)；

search\_direction: 搜索方向（1向前，2向后），默认为1(int)；

data\_count: 数据条数，默认为50，最大为200(int)；

#### 返回

返回一个OrderedDict对象，包含每只代码的分时成交行情数据。(OrderedDict(\[(),()...]))

返回结果字段介绍：

* time\_stamp: 时间戳毫秒级(str:numpy.int64)；
* hq\_px: 价格(str:numpy.float64)；
* hq\_px64: 价格(str:numpy.int64)(行情暂不支持，返回均为0)；
* business\_amount: 成交数量(str:numpy.int64)；
* business\_balance: 成交金额(str:numpy.int64)；
* business\_count: 成交笔数(str:numpy.int64)；
* business\_direction: 成交方向（0：卖，1：买，2：平盘)(str:numpy.int64)；
* amount: 持仓量(str:numpy.int64)(行情暂不支持，返回均为0)；
* start\_index: 分笔关联的逐笔开始序号(str:numpy.int64)(行情暂不支持，返回均为0)；
* end\_index: 分笔关联的逐笔结束序号(str:numpy.int64)(行情暂不支持，返回均为0)；

#### 示例

```python
def initialize(context):
    g.security = '000001.SZ'
    set_universe(g.security)

def handle_data(context, data):
    #获取000001.SZ的分时成交数据
    direction_data = get_tick_direction(g.security)
    log.info(direction_data)
    #获取指定股票列表分时成交数据
    direction_data = get_tick_direction(['000002.SZ','000032.SZ'])
    log.info(direction_data)
    #获取成交量
    business_amount = direction_data['000002.SZ']['business_amount']
    log.info('分时成交的成交量为：%s' % business_amount)
```

### get\_sort\_msg – 获取板块、行业的涨幅排名

```python
get_sort_msg(sort_type_grp=None, sort_field_name=None, sort_type=1, data_count=100)
```

#### 使用场景

该函数在交易模块可用

#### 接口说明

该接口用于获取板块、行业的涨幅排名。

#### 参数

sort\_type\_grp: 板块或行业的代码(list\[str]/str)；(暂时只支持XBHS.DY地域、XBHS.GN概念、XBHS.ZJHHY证监会行业、XBHS.ZS指数、XBHS.HY行业等)

sort\_field\_name: 需要排序的字段(str)；该字段支持输入的参数如下：

* preclose\_px: 昨日收盘价；
* open\_px: 今日开盘价；
* last\_px: 最新价；
* high\_px: 最高价；
* low\_px: 最低价；
* wavg\_px: 加权平均价；
* business\_amount: 总成交量；
* business\_balance: 总成交额；
* px\_change: 涨跌额；
* amplitude: 振幅；
* px\_change\_rate: 涨跌幅；
* circulation\_amount: 流通股本；
* total\_shares: 总股本；
* market\_value: 市值；
* circulation\_value: 流通市值；
* vol\_ratio: 量比；
* rise\_count: 上涨家数；
* fall\_count: 下跌家数；

sort\_type: 排序方式，默认降序(0:升序，1:降序)(int)；

data\_count: 数据条数，默认为100，最大为10000(int)；

#### 返回

正常返回一个List列表，里面包含板块、行业代码的涨幅排名信息(list\[dict{str:str,...},...])，

返回每个代码的信息包含以下字段内容：

* prod\_code: 行业代码(str:str)；
* prod\_name: 行业名称(str:str)；
* hq\_type\_code: 行业板块代码(str:str)；
* time\_stamp: 时间戳毫秒级(str:int)；
* trade\_mins: 交易分钟数(str:int)；
* trade\_status: 交易状态(str:str)；
* preclose\_px: 昨日收盘价(str:float)；
* open\_px: 今日开盘价(str:float)；
* last\_px: 最新价(str:float)；
* high\_px: 最高价(str:float)；
* low\_px: 最低价(str:float)；
* wavg\_px: 加权平均价(str:float)；
* business\_amount: 总成交量(str:int)；
* business\_balance: 总成交额(str:int)；
* px\_change: 涨跌额(str:float)；
* amplitude: 振幅(str:int)；
* px\_change\_rate: 涨跌幅(str:float)；
* circulation\_amount: 流通股本(str:int)；
* total\_shares: 总股本(str:int)；
* market\_value: 市值(str:int)；
* circulation\_value: 流通市值(str:int)；
* vol\_ratio: 量比(str:float)；
* shares\_per\_hand: 每手股数(str:int)；
* rise\_count: 上涨家数(str:int)；
* fall\_count: 下跌家数(str:int)；
* member\_count: 成员个数(str:int)；
* rise\_first\_grp: 领涨股票(其包含以下五个字段)(str:list\[dict{str:int,str:str,str:str,str:float,str:float},...])；
* * prod\_code: 股票代码(str:str)；
  * prod\_name: 证券名称(str:str)；
  * hq\_type\_code: 类型代码(str:str)；
  * last\_px: 最新价(str:float)；
  * px\_change\_rate: 涨跌幅(str:float)；
  fall\_first\_grp: 领跌股票(其包含以下五个字段)(str:list\[dict{str:int,str:str,str:str,str:float,str:float},...])；
  * prod\_code: 股票代码(str:str)；
  * prod\_name: 证券名称(str:str)；
  * hq\_type\_code: 类型代码(str:str)；
  * last\_px: 最新价(str:float)；
  * px\_change\_rate: 涨跌幅(str:float)；

#### 示例

```python
def initialize(context):
    g.security = '000001.SZ'
    set_universe(g.security)

def handle_data(context, data):
    #获取XBHS.DY板块的涨幅排名信息
    sort_data = get_sort_msg(sort_type_grp='XBHS.DY', sort_field_name='preclose_px', sort_type=1, data_count=100)
    log.info(sort_data)
    #获取sort_data排序第一条代码的数据
    sort_data_first = sort_data[0]
    log.info(sort_data_first)
```

### get\_etf\_info - 获取ETF信息

```python
get_etf_info(etf_code)
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于获取单支或者多支ETF的信息。

注意事项：

无

#### 参数

etf\_code : 单支ETF代码或者一个ETF代码的list，必传参数(list\[str]/str)

#### 返回

正常返回一个dict类型字段，包含每只ETF信息，key为ETF代码，values为包含etf信息的dict。异常返回空dict，如{}(dict\[str:dict\[...]])

返回结果字段介绍：

* etf\_redemption\_code -- 申赎代码(str:str)；
* publish -- 是否需要发布IOPV(str:int)；
* report\_unit -- 最小申购、赎回单位(str:int)；
* cash\_balance -- 现金差额(str:float)；
* max\_cash\_ratio -- 现金替代比例上限(str:float)；
* pre\_cash\_component -- T-1日申购基准单位现金余额(str:float)；
* nav\_percu -- T-1日申购基准单位净值(str:float)；
* nav\_pre -- T-1日基金单位净值(str:float)；
* allot\_max -- 申购上限(str:float)；
* redeem\_max -- 赎回上限(str:float)；

字段备注:

* publish -- 是否需要发布IOPV，1是需要发布，0是不需要发布；

返回如下:

```python
{'510020.SS': {'nav_percu': 206601.39, 'redeem_max': 0.0, 'nav_pre': 0.207, 'report_unit': 1000000, 'max_cash_ratio': 0.4,
                'cash_balance': -813.75, 'etf_redemption_code': '510021', 'pre_cash_component': 598.39, 'allot_max': 0.0, 'publish': 1}}
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #ETF信息
    etf_info = get_etf_info('510020.SS')
    log.info(etf_info)
    etfs_info = get_etf_info(['510020.SS','510050.SS'])
    log.info(etfs_info)
```

### get\_etf\_stock\_info - 获取ETF成分券信息

```python
get_etf_stock_info(etf_code,security)
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于获取ETF成分券信息。

注意事项：

无

#### 参数

etf\_code : 单支ETF代码，必传参数(str)

security : 单只股票代码或者一个由多只股票代码组成的列表，必传参数(list\[str]/str)

#### 返回

正常返回一个dict类型字段，包含每只etf代码中成分股的信息。异常返回空dict，如{}(dict\[str:dict\[...]])

返回结果字段介绍：

* code\_num -- 成分券数量(str:float)；
* cash\_replace\_flag -- 现金替代标志(str:str)；
* * '0' -- 禁止替代；
  * '1' -- 允许替代；
  * '2' -- 必须替代；
  * '3' -- 非沪市退补现金替代；
  * '4' -- 非沪市必须现金替代；
  * '5' -- 非沪深退补现金替代；
  * '6' -- 非沪深必须现金替代；
  replace\_ratio -- 保证金率（溢价比率），允许现金替代标的此字段有效(str:float)；
* replace\_balance -- 替代金额,必须现金替代标的此字段有效(str:float)；
* is\_open -- 停牌标志，0-停牌，1-非停牌(str:int)；

返回如下:

```python
{'600000.SS': {'cash_replace_flag': '1', 'replace_ratio': 0.1, 'is_open': 1, 'code_num': 4700.0, 'replace_balance': 0.0}}
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #ETF成分券信息
    stock_info = get_etf_stock_info('510050.SS','600000.SS')
    log.info(stock_info)
    stocks_info = get_etf_stock_info('510050.SS',['600000.SS','600036.SS'])
    log.info(stocks_info)
```

### get\_gear\_price – 获取指定代码的档位行情价格

```python
get_gear_price(sids)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于获取指定代码的档位行情价格。

注意事项：

获取实时行情快照失败时返回档位内容为空dict({"bid\_grp": {}, "offer\_grp": {}})

若无L2行情时，委托笔数字段返回0。

#### 参数

sids：股票代码(list\[str]/str)；

#### 返回

包含以下信息(dict\[str:dict\[int:list\[float,int,int],...],...])：

* bid\_grp:委买档位(str:dict\[int:list\[float,int,int],...])；
* offer\_grp:委卖档位(str:dict\[int:list\[float,int,int],...])；

```python
单只代码返回：
{'bid_grp': {1: [价格, 委托量,委托笔数], 2: [价格, 委托量,委托笔数], 3: [价格, 委托量,委托笔数], 4: [价格, 委托量,委托笔数], 5: [价格, 委托量,委托笔数]},
 'offer_grp': {1: [价格, 委托量,委托笔数], 2: [价格, 委托量,委托笔数], 3: [价格, 委托量,委托笔数], 4: [价格, 委托量,委托笔数], 5: [价格, 委托量,委托笔数]}}
多只代码返回：
{代码：{'bid_grp': {1: [价格, 委托量,委托笔数], 2: [价格, 委托量,委托笔数], 3: [价格, 委托量,委托笔数], 4: [价格, 委托量,委托笔数], 5: [价格, 委托量,委托笔数]},
 'offer_grp': {1: [价格, 委托量,委托笔数], 2: [价格, 委托量,委托笔数], 3: [价格, 委托量,委托笔数], 4: [价格, 委托量,委托笔数], 5: [价格, 委托量,委托笔数]}}
}
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #获取600570.SS当前档位行情
    gear_price = get_gear_price('600570.SS')
    log.info(gear_price)
    #获取600571.SS当前档位行情
    gear_price = get_gear_price('600571.SS')
    log.info(gear_price)
```

### get\_snapshot - 取行情快照

```python
get_snapshot(security)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于获取实时行情快照。

注意事项：

无

#### 参数

security： 单只股票代码或者多只股票代码组成的列表，必填字段(list\[str]/str)；

#### 返回

正常返回一个dict类型数据，包含每只股票代码的行情快照信息，其中key为股票代码，value为对应的快照信息。异常返回空dict，如{}(dict\[str:dict\[...]])

快照包含以下信息：

* amount:持仓量(str:int)；
* avg\_px:均价
* bid\_grp:委买档位(第一档包含委托队列（仅L2支持）)(str:dict\[int:list\[float,int,int,{int:int,...}],int:list\[float,int,int]...])；
* business\_amount:总成交量(str:int)；
* business\_amount\_in:内盘成交量(str:int)；
* business\_amount\_out:外盘成交量(str:int)；
* business\_balance:总成交额(str:float)；
* business\_count:成交笔数(str:int)
* circulation\_amount:流通股本(str:int)；
* close\_px:今收价(str:float)
* current\_amount:最近成交量(现手)(str:int)；
* down\_px:跌停价格(str:float)；
* end\_trade\_date:最后交易日(str:str)
* entrust\_diff:委差(str:float)；
* entrust\_rate:委比(str:float)；
* high\_px:最高价(str:float)；
* hsTimeStamp:时间戳(str:float)；
* issue\_date:上市日期(str:int)；
* last\_px:最新成交价(str:float)；
* low\_px:最低价(str:float)；
* offer\_grp:委卖档位(第一档包含委托队列（仅L2支持）)(str:dict\[int:list\[float,int,int,{int:int,...}],int:list\[float,int,int]...])；
* open\_px:今开盘价(str:float)；
* pb\_rate:市净率(str:float)；
* pe\_rate:动态市盈率(str:float)；
* preclose\_px:昨收价(str:float)；
* prev\_settlement:昨结算(str:float)；
* px\_change\_rate:涨跌幅(str:float)；
* settlement:结算价(str:float)
* start\_trade\_date:首个交易日(str:float)
* tick\_size:最小报价单位(str:float)
* total\_bid\_turnover:委买金额(str:int)；
* total\_bidqty:委买量(str:int)；
* total\_offer\_turnover:委卖金额(str:int)
* total\_offerqty:委卖量(str:int)；
* trade\_mins:交易分钟数(str:int)
* trade\_status:交易状态(str:str)；
* turnover\_ratio:换手率(str:int)；
* up\_px:涨停价格(str:float)；
* vol\_ratio:量比(str:float)；
* wavg\_px:加权平均价(str:float)；

字段备注:

* bid\_grp -- 委买档位，{'bid\_grp': {1: \[价格, 委托量,委托笔数,委托对列{}], 2: \[价格, 委托量,委托笔数], 3: \[价格, 委托量,委托笔数], 4: \[价格, 委托量,委托笔数], 5: \[价格, 委托量,委托笔数]}} ；
* offer\_grp -- 委卖档位，{'offer\_grp': {1: \[价格, 委托量,委托笔数,委托对列{}], 2: \[价格, 委托量,委托笔数], 3: \[价格, 委托量,委托笔数], 4: \[价格, 委托量,委托笔数], 5: \[价格, 委托量,委托笔数]}} ；
* total\_bid\_turnover/total\_offer\_turnover,委买金额/委卖金额主推数据(tick数据中)不支持(值为0)，仅在线请求中支持；
* trade\_status -- 交易状态；
  * START -- 市场启动(初始化之后，集合竞价前)
  * PRETR -- 盘前
  * OCALL -- 开始集合竞价
  * TRADE -- 交易(连续撮合)
  * HALT -- 暂停交易
  * SUSP -- 停盘
  * BREAK -- 休市
  * POSTR -- 盘后
  * ENDTR -- 交易结束
  * STOPT -- 长期停盘，停盘n天，n>=1
  * DELISTED -- 退市
  * POSMT -- 盘后交易
  * PCALL -- 盘后集合竞价
  * INIT -- 盘后固定价格启动前
  * ENDPT -- 盘后固定价格闭市阶段
  * POSSP -- 盘后固定价格停牌

返回如下:

```python
{'600570.SS': {'offer_grp': {1: [44.47, 3300, 0, {}], 2: [44.48, 2800, 0], 3: [44.49, 3900, 0], 4: [44.5, 17300, 0], 5: [44.51, 1600, 0]}, 'open_px': 44.91, 'pe_rate': 4294573.83, 'pb_rate': 11.42, 'entrust_diff': -100.0, 'entrust_rate': -0.2092, 'total_bidqty': 18900, 'preclose_px': 45.2, 'total_offer_turnover': 0, 'issue_date': 0, 'business_amount_out': 2600706, 'px_change_rate': -1.62, 'turnover_ratio': 0.0042, 'total_bid_turnover': 0, 'vol_ratio': 1.12, 'hsTimeStamp': 20220622102358580, 'amount': 0, 'prev_settlement': 0.0, 'circulation_amount': 1461560480, 'low_px': 44.31, 'down_px': 40.68, 'bid_grp': {1: [44.45, 600, 0, {}], 2: [44.44, 600, 0], 3: [44.43, 8300, 0], 4: [44.42, 9200, 0], 5: [44.41, 200, 0]}, 'business_balance': 274847503.0, 'business_amount': 6161800, 'business_amount_in': 3561094, 'last_px': 44.47, 'total_offerqty': 28900, 'up_px': 49.72, 'wavg_px': 44.6, 'high_px': 45.05, 'trade_status': 'TRADE'}}
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 行情快照
    snapshot = get_snapshot(g.security)
    log.info(snapshot)
```

### get\_cb\_info – 获取可转债基础信息

```python
get_cb_info()
```

#### 使用场景

该函数仅在研究、交易模块可用

#### 接口说明

获取可转债基础信息。

注意事项：

获取失败时返回空DataFrame

#### 参数

无

#### 返回

正常返回一个DataFrame类型数据，包含每只可转债的信息

包含以下信息：

* bond\_code:可转债代码(str)；
* bond\_name:可转债名称(str)；
* stock\_code:股票代码(str)；
* stock\_name:股票名称(str)；
* list\_date:上市日期(str)；
* premium\_rate:溢价率(float)；
* convert\_date:转股起始日(str)；
* maturity\_date:到期日(str)；
* convert\_rate:转股比例(float)；
* convert\_price:转股价格(float)；
* convert\_value:转股价值(float)；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    df = get_cb_info()
    log.info(df)
```

## 获取股票信息

### get\_stock\_name - 获取股票名称

```python
get_stock_name(stocks)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口可获取股票、可转债、ETF等名称。

注意事项：

无

#### 参数

stocks：股票代码(list\[str]/str)；

#### 返回

股票名称字典，dict类型，key为股票代码，value为股票名称，当没有查询到相关数据或者输入有误时value为None(dict\[str:str])；

```python
{'600570.SS': '恒生电子'}
```

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '600571.SS']
    set_universe(g.security)

def handle_data(context, data):
    #获取600570.SS股票名称
    stock_name = get_stock_name(g.security[0])
    log.info(stock_name)
    #获取股票池所有的股票名称
    stock_names = get_stock_name(g.security)
    log.info(stock_names)
```

### get\_stock\_info - 获取股票基础信息

```python
get_stock_info(stocks, field=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口可获取股票、可转债、ETF等基础信息。

注意事项：

field不做入参时默认只返回stock\_name字段

#### 参数

stocks：股票代码(list\[str]/str)；

field：指明数据结果集中所支持输出字段(list\[str]/str)，输出字段包括 ：

* stock\_name -- 股票代码对应公司名(str:str)；
* listed\_date -- 股票上市日期(str:str)；
* de\_listed\_date -- 股票退市日期，若未退市，返回2900-01-01(str:str)；

#### 返回

嵌套dict类型，包含内容为field中指定内容，若field=None，返回股票基础信息仅包含对应公司名(dict\[str:dict\[str:str,...],...])

```python
{'600570.SS': {'stock_name': '恒生电子', 'listed_date': '2003-12-16', 'de_listed_date': '2900-01-01'}}
```

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '600571.SS']
    set_universe(g.security)

def handle_data(context, data):
    #获取单支股票的基础信息
    stock_info = get_stock_info(g.security[0])
    log.info(stock_info)
    #获取多支股票的基础信息
    stock_infos = get_stock_info(g.security, ['stock_name','listed_date','de_listed_date'])
    log.info(stock_infos)
```

### get\_stock\_status – 获取股票状态信息

```python
get_stock_status(stocks, query_type='ST', query_date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口用于获取指定日期股票的ST、停牌、退市属性。

注意事项：

退市整理期股票不包含在退市状态内，可通过get\_stock\_name函数判断股票名称是否包含【退】确认退市整理期代码

#### 参数

stocks: 例如 \['000001.SZ','000003.SZ']。该字段必须输入，否则返回None(list\[str]/str)；

query\_type: 支持以下三种类型属性的查询，默认为'ST'(str)；

具体支持输入的字段包括 ：

* 'ST' – 查询是否属于ST股票
* 'HALT' – 查询是否停牌
* 'DELISTING' – 查询是否退市

query\_date: 格式为YYYYmmdd，默认为None,表示当前日期（回测为回测当前周期，研究与交易则取系统当前时间）(str)；

#### 返回

返回dict类型，每支股票对应的值为True或False，当没有查询到相关数据或者输入有误时返回None(dict\[str:bool,...])；

```python
{'600570': None}
```

#### 示例

```python
def initialize(context):
    g.security = ['600397.SS', '600701.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    stocks_list = g.security
    filter_stocks = []
    # 判断股票是否为ST、停牌或者退市的股票
    st_status = get_stock_status(stocks_list, 'ST')
    # 将不是ST的股票筛选出来
    for i in stocks_list:
        if st_status[i] is not True:
            filter_stocks.append(i)
    # 获取股票停牌信息
    # halt_status = get_stock_status(stocks_list, 'HALT')
    # 获取指定日期的对应属性
    # halt_status = get_stock_status(stocks_list, 'HALT', '20180312')
    # 获取股票退市信息
    # delist_status = get_stock_status(stocks_list, 'DELISTING')
    log.info('筛选不是ST的股票列表: %s' % filter_stocks)
```

### get\_stock\_exrights - 获取股票除权除息信息

```python
get_stock_exrights(stock_code, date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口用于获取股票除权除息信息。

注意事项：

无

#### 参数

stock\_code; str类型, 股票代码(str)；

date: 查询该日期的除权除息信息，默认获取该股票历史上所有除权除息信息，e.g. '20180228'/20180228/datetime.date(2018,2,28)(str/int/datetime.date)

#### 返回

输入日期若没有除权除息信息则返回None,有相关数据则返回pandas.DataFrame类型数据

例如输入get\_stock\_exrights('600570.SS')，返回

```python

         allotted_ps   rationed_ps   rationed_px   bonus_ps   exer_forward_a   exer_forward_b   exer_backward_a   exer_backward_b
date
20040604  0.0          0.0           0.0           0.43       0.046077         -1.433            1.000000         0.430
20050601  0.5          0.0           0.0           0.20       0.046077         -1.413            1.500000         0.630
20050809  0.4          0.0           0.0           0.00       0.069115         -1.404            2.100000         0.630
20060601  0.4          0.0           0.0           0.11       0.096762         -1.404            2.940000         0.861
20070423  0.3          0.0           0.0           0.10       0.135466         -1.394            3.822000         1.155
20080528  0.6          0.0           0.0           0.07       0.176106         -1.380            6.115200         1.422
20090423  0.5          0.0           0.0           0.10       0.281770         -1.368            9.172799         2.034
20100510  0.4          0.0           0.0           0.05       0.422654         -1.340            12.841919        2.492
20110517  0.0          0.0           0.0           0.05       0.591716         -1.318            12.841919        3.134
20120618  0.0          0.0           0.0           0.08       0.591716         -1.289            12.841919        4.162
20130514  0.0          0.0           0.0           0.10       0.591716         -1.242            12.841919        5.446
20140523  0.0          0.0           0.0           0.16       0.591716         -1.182            12.841919        7.501
20150529  0.0          0.0           0.0           0.18       0.591716         -1.088            12.841919        9.812
20160530  0.0          0.0           0.0           0.26       0.591716         -0.981            12.841919        13.151
20170510  0.0          0.0           0.0           0.10       0.591716         -0.827            12.841919        14.435
20180524  0.0          0.0           0.0           0.29       0.591716         -0.768            12.841919        18.159
20190515  0.3          0.0           0.0           0.32       0.591716         -0.597            16.694494        22.269
20200605  0.3          0.0           0.0           0.53       0.769231         -0.407            21.702843        31.117
```

返回结果字段介绍：

* date -- 日期(索引列，类型为int64)；
* allotted\_ps -- 每股送股(str:numpy.float64)；
* rationed\_ps -- 每股配股(str:numpy.float64)；
* rationed\_px -- 配股价(str:numpy.float64)；
* bonus\_ps -- 每股分红(str:numpy.float64)；
* exer\_forward\_a -- 前复权除权因子A；用于计算前复权价格(前复权价格=A\*价格+B)(str:numpy.float64)
* exer\_forward\_b -- 前复权除权因子B；用于计算前复权价格(前复权价格=A\*价格+B)(str:numpy.float64)
* exer\_backward\_a -- 后复权除权因子A；用于计算后复权价格(后复权价格=A\*价格+B)(str:numpy.float64)
* exer\_backward\_b -- 后复权除权因子B；用于计算后复权价格(后复权价格=A\*价格+B)(str:numpy.float64)

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    stock_exrights = get_stock_exrights(g.security)
    log.info('the stock exrights info of security %s:\n%s' % (g.security, stock_exrights))
```

<!--
                      <h3 id="get_change_to_forward">get_change_to_forward-获取前复权数据</h3>
                      <pre class="prettyprint"><code class="language-python">get_change_to_forward(security,data)</code></pre>
                      <p>获取指定股票的前复权数据。</p>
                      <h4>参数</h4>
                      <p>security：一支股票代码；</p>
                      <p>data：对应查询股票复权之前的价格，支持价格包括以下字段：</p>
                      <ul>
                        <li>open -- 开盘价；</li>
                        <li>high -- 最高价；</li>
                        <li>low --最低价；</li>
                        <li>close -- 收盘价；</li>
                        <li>money -- 交易金额；</li>
                        <li>price -- 平均价；</li>
                      </ul>
                      <p>获取方式：在handle_data中获取对应data信息，取对应股票的对应字段，例如收盘价：data[security][ 'close']作为该接口的输入参数；</p>
                      <p style="color: red">注意：</p>
                      <p style="color: red">该函数仅在回测与交易模块使用。</p>
                      <h4>返回</h4>
                      <p>返回查询股票对应字段的前复权数据。</p>
                      <h4>示例</h4>
                      <pre class="prettyprint"><code class="language-python">def initialize(context):
          g.security = '600570.SS'
          set_universe(g.security)
      
      def handle_data(context, data):
          real_price = get_change_to_forward('600570.SS',data['600570.SS']['close'])
          log.info(real_price)</code></pre>
                      <h3 id="get_change_to_backward">get_change_to_backward-获取后复权数据</h3>
                      <pre class="prettyprint"><code class="language-python">get_change_to_backward(security,data)</code></pre>
                      <p>获取指定股票的后复权数据。</p>
                      <h4>参数</h4>
                      <p>security：一支股票代码；</p>
                      <p>data：对应查询股票复权之前的价格，支持价格包括以下字段：</p>
                      <ul>
                          <li>open -- 开盘价；</li>
                          <li>high -- 最高价；</li>
                          <li>low --最低价；</li>
                          <li>close -- 收盘价；</li>
                          <li>money -- 交易金额；</li>
                          <li>price -- 平均价；</li>
                      </ul>
                      <p>获取方式：在handle_data中获取对应data信息，取对应股票的对应字段，例如收盘价：data[security][ 'close']作为该接口的输入参数；</p>
                      <p style="color: red">注意：</p>
                      <p style="color: red">该函数仅在回测与交易模块使用。</p>
                      <h4>返回</h4>
                      <p>返回查询股票对应字段的后复权数据。</p>
                      <h4>示例</h4>
                      <pre class="prettyprint"><code class="language-python">def initialize(context):
          g.security = '600570.SS'
          set_universe(g.security)
      
      def handle_data(context, data):
          real_price = get_change_to_backward ('600570.SS',data['600570.SS']['close'])
          log.info(real_price)</code></pre>
                      -->

### get\_stock\_blocks - 获取股票所属板块信息

```python
get_stock_blocks(stock_code)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口用于获取股票所属板块。

注意事项：

该函数获取的是当下的数据，因此回测不能取到真正匹配回测日期的数据，注意未来函数

已退市股票无法成功获取数据，接口会返回None

#### 参数

stock\_code: 股票代码(str)；

#### 返回

获取成功返回dict类型，包含所属行业、板块等详细信息(dict\[str:list\[list\[str,str],...],...])，获取失败返回None。返回数据如：

```python
{
'HGT': [['HGTHGT.XBHK', '沪股通']],
'HY': [['710200.XBHS', '计算机应用']],
'DY': [['DY1172.XBHS', '浙江板块']], 
'ZJHHY': [['I65000.XBHS', '软件和信息技术服务业']],
'GN': [['003596.XBHS', '融资融券'], ['003631.XBHS', '转融券标的'], ['003637.XBHS', '互联网金融'], ['003665.XBHS', '电商概念'], ['003707.XBHS', '沪股通'], ['003718.XBHS', '证金持股'], ['003800.XBHS', '人工智能'], ['003830.XBHS', '区块链'], ['031027.XBHS', 'MSCI概念'], ['B10003.XBHS', '蚂蚁金服概念']]
}
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    blocks = get_stock_blocks(g.security)
    log.info('security %s in these blocks:\n%s' % (g.security, blocks))
```

### get\_index\_stocks- 获取指数成分股

```python
get_index_stocks(index_code,date)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口用于获取一个指数在平台可交易的成分股列表，[指数列表](/data/index)

注意事项：

1、在回测中，date不入参默认取当前回测周期所属历史日期

2、在研究中，date不入参默认取的是当前日期

3、在交易中，date不入参默认取的是当前日期

#### 参数

index\_code：指数代码，尾缀必须是.SS 如沪深300：000300.SS(str)

date：日期，输入形式必须为'YYYYMMDD'，如'20170620'，不输入默认为当前日期(str)；

#### 返回

返回股票代码的list(list\[str,...])。

```python
['000001.SZ', '000002.SZ', '000063.SZ', '000069.SZ', '000100.SZ', '000157.SZ', '000425.SZ', '000538.SZ', '000568.SZ', '000625.SZ', '000651.SZ', '000725.SZ', '000728.SZ', '000768.SZ', '000776.SZ',
 '000783.SZ', '000786.SZ', ..., '603338.SS', '603939.SS', '603233.SS', '600426.SS', '688126.SS', '600079.SS', '600521.SS', '600143.SS', '000800.SZ'] 
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def before_trading_start(context, data):
    # 获取当前所有沪深300的股票
    g.stocks = get_index_stocks('000300.XBHS')
    log.info(g.stocks)
    # 获取2016年6月20日所有沪深300的股票, 设为股票池
    g.stocks = get_index_stocks('000300.XBHS','20160620')
    set_universe(g.stocks)
    log.info(g.stocks)

def handle_data(context, data):
    pass
```

### get\_etf\_stock\_list - 获取ETF成分券列表

```python
get_etf_stock_list(etf_code)
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于获取目标ETF的成分券列表

注意事项：

无

#### 参数

etf\_code : 单支ETF代码，必传参数(str)

#### 返回

正常返回一个list类型字段，包含每只etf代码所对应的成分股。异常返回空list，如\[]\(list\[str,...])

```python
['600000.SS', '600010.SS', '600016.SS'] 
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def before_trading_start(context, data):
    #ETF成分券列表
    stock_list = get_etf_stock_list('510020.SS')
    log.info(stock_list)

def handle_data(context, data):
    pass
```

### get\_industry\_stocks- 获取行业成份股

```python
get_industry_stocks(industry_code)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口用于获取一个行业的所有股票，[行业列表](/data/industry_concept)

注意事项：

该函数获取的是当下的数据，因此回测不能取到真正匹配回测日期的数据，注意未来函数

#### 参数

industry\_code: 行业编码，尾缀必须是.XBHS 如农业股：A01000.XBHS(str)

#### 返回

返回股票代码的list(list\[str,...])

```python
['300970.SZ', '300087.SZ', '300972.SZ', '002772.SZ', '000998.SZ', '002041.SZ', '600598.SS', '600371.SS', '600506.SS', '300511.SZ', '600359.SS', '600354.SS', '601118.SS', '600540.SS', '300189.SZ',
 '600313.SS', '600108.SS'] 
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def before_trading_start(context, data):
    # 获取农业的股票, 设为股票池
    stocks = get_industry_stocks('A01000.XBHS')
    set_universe(stocks)
    log.info(stocks)

def handle_data(context, data):
    pass
```

### get\_fundamentals-获取财务数据

```python
get_fundamentals(security, table, fields=None, date=None, start_year=None, end_year=None, report_types=None, merge_type=None)
```

#### 使用场景

该函数可在研究、回测、交易模块使用

#### 接口说明

该接口用于获取财务三大报表数据、日频估值数据、各项财务能力指标数据。

注意事项：

1、该接口为http在线获取，会存在因网络拥堵等原因导致应答失败的情况，如果返回数据结果为空请多次尝试，策略中请增加保护机制。

2、该接口有流量限制，每秒不得调用超过100次，单次最大调用量是500条数据，每一条数据的定义为：一个股票对应一个表的一个字段，相当于最大不超过5万条。因此如果涉及多股多字段的查询要考虑限流情况，依据实际调用场景加入sleep做时间间隔，方法可参考示例。

#### 参数

为保持各表接口统一，输入字段略有不同，具体可参见 [财务数据的API接口说明](/data/finance)

security：一支股票代码或者多只股票代码组成的list(list\[str])

table：财务数据表名，输入具体表名可查询对应表中信息(str)

| 表名                    | 包含内容   |
| --------------------- | ------ |
| valuation             | 估值数据   |
| balance\_statement    | 资产负债表  |
| income\_statement     | 利润表    |
| cashflow\_statement   | 现金流量表  |
| growth\_ability       | 成长能力指标 |
| profit\_ability       | 盈利能力指标 |
| eps                   | 每股指标   |
| operating\_ability    | 营运能力指标 |
| debt\_paying\_ability | 偿债能力指标 |

fields：指明数据结果集中所需输出业务字段，支持多个业务字段输出（list类型），如fields=\['settlement\_provi', 'client\_provi']\(list\[str])；输出具体字段请参考 [财务数据的API接口说明](/data/finance)

date：查询日期，按日期查询模式，返回查询日期之前对应的财务数据，输入形式如'20170620'，回测中支持datetime.date时间格式输入，不能与start\_year与end\_year同时作用。回测中，支持按日期查询模式，不传入date默认取回测时的日期(str)；

start\_year：查询开始年份，按年份查询模式，返回输入年份范围内对应的财务数据，如'2015'，start\_year与end\_year必须同时输入，且不能与date同时作用(str)

end\_year：查询截止年份，按年份查询模式，返回输入年份范围内对应的财务数据，如'2015'，start\_year与end\_year必须同时输入，且不能与date同时作用(str)

report\_types：财报类型；如果为年份查询模式（start\_year/end\_year），不输入report\_types返回当年可查询到的全部类型财报；如果为日期查询模式（date），不输入report\_types返回距离指定日期最近一份财报(str)。

* report\_types='1':表示获取一季度财报
* report\_types='2':表示获取半年报
* report\_types='3':表示获取截止到三季度财报
* report\_types='4':表示获取年度财报

~~（已废弃）date\_type：数据参考时间设置，该参数只适用于按日期查询模式(date参数模式)(int) ：~~

* ~~（已废弃）date\_type不传或传入date\_type = None，返回发布日期（publ\_date）在查询日期（date）之前指定财报类型数据（report\_types），若未指定财报类型（report\_types）则默认为离查询日期（date）最近季度的数据，数据未公布用NAN填充~~
* ~~（已废弃）date\_type传入1，返回会计周期（end\_date）在查询日期（date）之前指定财报类型数据（report\_types），若未指定财报类型（report\_types）则默认为查询日期（date）最近季度会计周期的数据，数据未公布用NAN填充~~

merge\_type：数据更新设置；相关财务数据信息会不断进行修正更新，为了避免未来数据影响，可以通过参数获取原始发布或最新发布数据信息；只有部分表包含此字段(int) ：

* merge\_type不传或传入merge\_type = None，获取首次发布的数据，即使实际数据发生变化，也只返回原样数据信息；回测场景为避免未来数据建议使用此模式
* merge\_type=传入1，获取已发布财报数据的更新数据，更新数据范围包括但不限于相关日期数据，研究场景或交易场景建议使用此模式，但需要指定报告期，否则会获取到历史最近一期有过更新情况的财报数据(不一定是最近一个财报期)

注意：

* date字段与start\_year/end\_year不能同时输入，否则按日期查询模式（date参数模式）
* 当date和start\_year/end\_year相关数据都不传入时，默认为按日期查询模式（date参数模式），研究和回测中date取值有所不同：在研究中，date取的是当前日期
* fields不入参的情况下，date必须参数名入参，否则会报错。正确调用示例：get\_fundamentals('600570.XSHG', 'balance\_statement', date='2018-06-01')

#### 返回

返回值形式根据输入参数类型不同而有所区分：

1.按日期查询模式（date参数模式）返回数据类型为pandas.DataFrame类型，索引为股票代码，如get\_fundamentals('600000.SS','balance\_statement',date='20161201')将返回：

|           | secu\_abbr | end\_date  | publ\_date | total\_assets | ……     | total\_liability |
| --------- | ---------- | ---------- | ---------- | ------------- | ------ | ---------------- |
| 600000.SS | 浦发银行       | 2016-09-30 | 2016-10-29 | 5.56e+12      | ...... | 5.20e+12         |

2.按年份查询模式（start\_year/end\_year参数模式）返回数据类型为pandas.Panel类型，索引为股票代码，其中包含的DataFrame索引为返回股票对应会计日期（end\_date），如get\_fundamentals(\['600000.SS', '600570.SS', '000002.SZ'], 'balance\_statement', start\_year='2016', end\_year='2016')将返回：

![](/static/images/help/get_fundamentals_1.png)

### 示例

```python
import time
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def before_trading_start(context, data):
     # 假设取4000股*10年一季报数据为4万条，之后再取中报又是4万条，因为规则要求每秒不得调用超过100次（单次最大调用量是500条数据），调用过程就需要sleep1秒，防止流控触发。
     funda_data = get_fundamentals(g.security, 'balance_statement', fields = 'total_assets', start_year='2011', end_year='2020', report_types = '1')
     time.sleep(1)
     funda_data = get_fundamentals(g.security, 'balance_statement', fields = 'total_assets', start_year='2010', end_year='2020', report_types = '2')
def handle_data(context, data):
     # 获取股票池
     stocks = get_index_stocks('000906.XBHS')
     # 指定股票池
     stocks = ['600000.SS','600570.SS']

     # 获取数据的两种模式
     # 1. 按日期查询模式（默认以发布日期为参考时间）：返回输入日期之前对应的财务数据
     # 在回测中获取单一股票中对应回测日期资产负债表中资产总计（total_assets）数据
     #（回测中date默认获取回测日期，无需传入date，除非在回测中获取指定某个日期的数据，日期格式如”20160628”）
     get_fundamentals('600000.SS', 'balance_statement', 'total_assets')

     # 获取股票池中对应上市公司在2016年6月28日之前发布的最近季度（即2016年一季度）
     # 的资产负债表中资产总计（total_assets）数据，如果到查询日期为止一季度数据还,未发布则所有数据用Nan填充
     get_fundamentals(stocks, 'balance_statement', 'total_assets','20160628')

     # 获取股票池中对应上市公司在2016年6月28日最近会计周期（即20160331）的资产负
     # 债表中资产总计（total_assets）数据，如果未查到相关数据则用Nan填充
     get_fundamentals(stocks, 'balance_statement', 'total_assets','20160628', date_type=1)

     # 获取股票池中对应上市公司发布日期在2016年6月28日之前，年度（即2015年年报）
     # 资产负债表中资产总计（total_assets）数据，如果到查询日期为止还未发布则所有数据用Nan填充
     get_fundamentals(stocks, 'balance_statement', 'total_assets', '20160628', report_types='4')

     # 获取股票池中对应上市公司2016年6月28日最近季度资产负债表中对应fields字段数据
     fields =['sold_buyback_secu_proceeds','specific_account_payable']
     get_fundamentals(stocks, 'balance_statement', fields,'20160628',)

     # 获取股票池中对应上市公司2016年6月28日最近季度资产负债表中对应fields字段最新数据，
     # 如果最近更新日期（发布日期）在2016年6月28日之后则无法获取对应数据
     fields =['sold_buyback_secu_proceeds','specific_account_payable']
     get_fundamentals(stocks, 'balance_statement', fields,'20160628',merge_type=1)

     # 2. 按年份查询模式：返回输入年份范围内对应季度的财务数据
     # 获取公司浦发银行(600000.SS)从2013年至2015年第一季度资产负债表中资产总计（total_assets）数据
     get_fundamentals('600000.SS','balance_statement','total_assets',start_year='2013',end_year='2015', report_types='1')

     # 获取股票池中对应上市公司从2013年至2015年年度资产负债表中对应fields字段数据
     fields =['sold_buyback_secu_proceeds','specific_account_payable']
     get_fundamentals(stocks,'balance_statement',fields,start_year='2013',end_year='2015', report_types='4')
```

### get\_Ashares – 获取指定日期A股代码列表

```python
get_Ashares(date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

该接口用于获取指定日期沪深市场的所有A股代码列表

注意事项：

1、在回测中，date不入参默认取回测日期，默认值会随着回测日期变化而变化，等于context.current\_dt

2、在研究中，date不入参默认取当天日期

3、在交易中，date不入参默认取当天日期

#### 参数

date：格式为YYYYmmdd

#### 返回

股票代码列表，list类型(list\[str,...])

```python
['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ', '000011.SZ', '000012.SZ', '000014.SZ', '000016.SZ', '000017.SZ', '000018.SZ', '000019.SZ',
 '000020.SZ', '000021.SZ', '000023.SZ', '000024.SZ', '000025.SZ', '000026.SZ', '000027.SZ',..., '603128.SS', '603167.SS', '603333.SS', '603366.SS', '603399.SS', '603766.SS', '603993.SS'] 
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #沪深A股代码
    ashares = get_Ashares()
    log.info('%s A股数量为%s' % (context.blotter.current_dt,len(ashares)))
    ashares = get_Ashares('20130512')
    log.info('20130512 A股数量为%s'%len(ashares))
```

### get\_etf\_list - 获取ETF代码

```python
get_etf_list()
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于获取柜台返回的ETF代码列表

注意事项：

无

#### 返回

正常返回一个list类型对象，包含所有ETF代码。异常返回空list，如\[]\(list\[str,...])。

```python
['510010.SS', '510020.SS', '510030.SS', '510050.SS', '510060.SS', '510180.SS', '510300.SS', '510310.SS', '510330.SS', '511800.SS', '511810.SS', '511820.SS', '511830.SS', '511880.SS', '511990.SS', '512010.SS',
 '512510.SS', '159001.SZ', '159003.SZ', '159005.SZ', '159901.SZ', '159903.SZ', '159905.SZ', '159906.SZ', '159909.SZ', '159910.SZ', '159919.SZ', '159923.SZ', '159923.SZ', '159924.SZ', '159925.SZ', '159927.SZ',
 '159928.SZ', '159929.SZ']
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #ETF代码列表
    etf_code_list = get_etf_list()
    log.info('ETF列表为%s' % etf_code_list)
```

### get\_ipo\_stocks - 获取当日IPO申购标的

```python
get_ipo_stocks()
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于获取当日IPO申购标的信息

注意事项：

无

#### 返回

正常返回一个dict类型对象，key为各个分类市场，value为市场对应的申购代码列表。异常返回空dict，如{}({str:\[],str:\[],...})。分类市场明细如下：

* 上证普通代码；
* 上证科创板代码；
* 深证普通代码；
* 深证创业板代码；
* 可转债代码；

```python
{'深证普通代码': ['002952.SZ', '072318.SZ'], '深证创业板代码': ['300765.SZ'], '上证普通代码': ['732116.SS', '732136.SS', '732367.SS', '732378.SS', '732380.SS', '732616.SS', '780086.SS', '780211.SS', '780860.SS', '718001.SS', '783012.SS', '783127.SS'], '可转债代码': ['718001.SS', '783012.SS', '783127.SS', '072318.SZ'], '上证科创板代码': ['787006.SS']}
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 当日可转债IPO申购标的
    ipo_stocks = get_ipo_stocks().get('可转债代码')
    log.info('可转债IPO申购标的列表为%s' % ipo_stocks)
```

## 获取其他信息

### get\_trades\_file – 获取对账数据文件

```python
get_trades_file(save_path='')
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该接口用于获取对账数据文件

注意事项：

文件目录的命名需要遵守如下规则：

1、长度不能超过256个字符；

2、名称中不能出下如下字符：:?,@#$&();\\"\\'<>\`\~!%^\*；

#### 参数

save\_path：导出对账数据存储的路径， 默认在notebook的根目录下(str)；

#### 返回

成功返回导出文件的路径,失败返回None(str)；

```python
导出数据格式的说明:
交易数据文件的组织格式为csv文件，表头信息为：
订单编号，成交编号，委托编号，标的代码，交易类型，成交数量，成交价，成交金额，交易费用，交易时间，对应的表头字段为：
[order_id,trading_id,entrust_id,security_code,order_type,volume,price,total_money,trading_fee, trade_time]
```

注意：

order\_id列中可能出现如下几种取值：

1、M000000，通过外部系统委托的成交数据；

2、类似a6fbc145958843cc86639b23fbcfdc4c的字符串，通过平台委托的成交数据；

3、H000000，引入对账数据接口前的版本产生的交易数据；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 委托
    order_obj = order(g.security, 100)
    log.info('订单编号为：%s'% order_obj)

def after_trading_end(context, data):
    # 获取对账数据，存放到默认目录
    data_path = get_trades_file()
    log.info(data_path)

    # 获取对账数据，存放到notebook下的指定目录
    user_data_path = get_trades_file('user_data/data')
    log.info(user_data_path)
```

### convert\_position\_from\_csv – 获取设置底仓的参数列表(股票)

```python
convert_position_from_csv(path)
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

该接口用于从csv文件中获取设置底仓的参数列表

注意事项：

文件目录的命名需要遵守如下规则：

1、长度不能超过256个字符；

2、名称中不能出下如下字符：:?,@#$&();\\"\\'<>\`\~!%^\*；

#### 参数

path: csv文件对应路径及文件名(需要在研究中上传该文件)(str)；

csv文件内容格式要求如下:

```
sid,enable_amount,amount,cost_basis
600570.SS,10000,10000,45
```

* sid: 标的代码(str)；
* amount: 持仓数量(str)；
* enable\_amount: 可用数量(str)；
* cost\_basis: 每股的持仓成本价格(str)：

#### 返回

用于设置底仓的参数列表，该list中是字典类型的元素；

返回一个list，该list中是一个字典类型的元素(list\[dict\[str:str],...])，如：

```
[{
    'sid':标的代码,
    'amount':持仓数量,
    'enable_amount':可用数量,
    'cost_basis':每股的持仓成本价格,
}]
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    # 设置底仓
    poslist= convert_position_from_csv("Poslist.csv")
    set_yesterday_position(poslist)

def handle_data(context, data):
    # 卖出100股
    order(g.security, -100)
```

### get\_user\_name – 获取登录终端的资金账号

```python
get_user_name()
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取登录终端的账号

注意事项：

无

#### 返回

返回登录终端的资金账号(str)或者None。如果查询成功登录终端的资金账号(str)，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)
    g.user_name = get_user_name()

def before_trading_start(context, data):
    g.flag = False

def handle_data(context, data):
    # 账号为123456789且当日未委托过，买入100股
    if g.user_name == "123456789" and not g.flag:
        # 买入100股
        order(g.security, 100)
        g.flag = True
```

### get\_deliver – 获取历史交割单信息

```python
get_deliver(start_date, end_date)
```

#### 使用场景

该函数仅在交易模块使用；仅支持before\_trading\_start和after\_trading\_end阶段调用

#### 接口说明

该接口用来获取账户历史交割单信息。

注意事项：

1、开始日期start\_date和结束日期end\_date为必传字段

2、仅支持查询上一个交易日（包含）之前的交割单信息

3、因不同柜台返回的字段存在差异，因此接口返回的为柜台原数据，使用时请根据实际柜台信息做字段解析

4、该接口仅支持查询普通股票账户（非两融）

#### 参数

start\_date: 开始日期，输入形式仅支持"YYYYmmdd"，如'20170620'；

end\_date: 结束日期，输入形式仅支持"YYYYmmdd"，如'20170620'；

#### 返回

返回一个list类型对象(list\[dict,...])，包含一个或N个dict，每个dict为一条交割单信息，其中包含柜台返回的字段信息，失败则返回\[]。

```python
[{'entrust_way': '7', 'exchange_fare': 0.04, 'post_balance': 3539128.83, 'stock_account': '0010110920', 'exchange_farex': 0.0, 'fare0': 0.5, 'report_milltime': 110400187, 'business_balance': 2987.0, 'exchange_fare5': 0.0, 'fare_remark': '内部:.5( | ,费用类别:9999)', 'client_id': '10110920', 'uncome_flag': '0', 'exchange_fare0': 0.03, 'exchange_fare2': 0.0, 'fare1': 0.0, 'init_date': 20210811, 'stock_code': '162605', 'occur_amount': 1000.0, 'report_time': 110400, 'entrust_bs': '1', 'seat_no': '123456', 'business_id': '0110351000000242', 'business_amount': 1000.0, 'business_time': 110351, 'fund_account': '10110920', 'begin_issueno': ' ', 'post_amount': 1000.0, 'correct_amount': 0.0, 'money_type': '0', 'client_name': '客户10110920', 'business_type': '0', 'business_flag': 4002, 'clear_balance': -2987.5, 'exchange_fare1': 0.0, 'date_back': 20210811, 'branch_no': 1011, 'serial_no': 153, 'occur_balance': -2987.5, 'stock_name': '景顺鼎益', 'curr_time': 173028, 'exchange_fare4': 0.0, 'brokerage': 0.0, 'business_name': '证券买入', 'order_id': 'F04Z', 'business_times': 1, 'entrust_date': 20210811, 'remark': '证券买入;uft节点:31;', 'exchange_fare6': 0.0, 'standard_fare0': 0.5, 'exchange_fare3': 0.01, 'farex': 0.0, 'clear_fare0': 0.46, 'entrust_no': 38, 'profit': 0.0, 'exchange_type': '2', 'fare2': 0.0, 'business_no': 181, 'stock_type': 'L', 'fare3': 0.0, 'business_status': '0', 'business_price': 2.987, 'position_str': '020210811010110000000153', 'stock_name_long': '景顺鼎益LOF', 'report_no': 38, 'correct_balance': 0.0, 'exchange_rate': 0.0}] 
```

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def before_trading_start(context, data):
    h = get_deliver('20210101', '20211117')
    log.info(h)

def handle_data(context, data):
    pass
```

### get\_fundjour – 获取历史资金流水信息

```python
get_fundjour(start_date, end_date)
```

#### 使用场景

该函数仅在交易模块使用；仅支持before\_trading\_start和after\_trading\_end阶段调用

#### 接口说明

该接口用来获取账户历史资金流水信息。

注意事项：

1、开始日期start\_date和结束日期end\_date为必传字段

2、仅支持查询上一个交易日（包含）之前的资金流水信息

3、因不同柜台返回的字段存在差异，因此接口返回的为柜台原数据，使用时请根据实际柜台信息做字段解析

4、该接口仅支持查询普通股票账户（非两融）

#### 参数

start\_date: 开始日期，输入形式仅支持"YYYYmmdd"，如'20170620'；

end\_date: 结束日期，输入形式仅支持"YYYYmmdd"，如'20170620'；

#### 返回

返回一个list类型对象(list\[dict,...])，包含一个或N个dict，每个dict为一条资金流水，其中包含柜台返回的字段信息，失败则返回\[]。

```python
[{'post_balance': 3260341.36, 'init_date': 20210104, 'asset_prop': '0', 'serial_no': 1, 'business_flag': 4002, 'occur_balance': -10598.21, 'exchange_type': '0', 'stock_name': ' ', 'business_date': 20210104, 'business_price': 0.0, 'bank_no': '0', 'occur_amount': 0.0, 'remark': '证券买入,恒生电子,100股,价格105.93', 'stock_account': ' ', 'money_type': '0', 'fund_account': '10110920', 'position_str': '20210104010110000000001', 'bank_name': '内部银行', 'business_name': '证券买入', 'stock_code': ' ', 'curr_date': 20210104, 'entrust_bs': ' ', 'business_time': 171730}] 
```

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def before_trading_start(context, data):
    h = get_fundjour('20210101', '20211117')
    log.info(h)

def handle_data(context, data):
    pass
```

### get\_research\_path – 获取研究路径

```python
get_research_path()
```

#### 使用场景

该函数可在回测、交易模块使用

#### 接口说明

该接口用于获取研究根目录路径，该路径为'/home/fly/notebook/'。

注意事项：

无

#### 参数

无

#### 返回

返回一个字符串类型对象(str)

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)
    path = get_research_path()

def handle_data(context, data):
    pass
```

### get\_trade\_name – 获取交易名称

```python
get_trade_name()
```

#### 使用场景

该函数仅在交易模块使用

#### 接口说明

该接口用于获取当前交易的名称。

注意事项：

无

#### 参数

无

#### 返回

返回一个字符串类型对象(str)

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def handle_data(context, data):
    name = get_trade_name()
```

# 交易相关函数

注意：代码精度位为3位小数的类型(后台已保护为3位)，如ETF、国债；代码精度为2位小数类型，需要在传参时限制价格参数的精度，如股票。

## 股票交易函数

### order-按数量买卖

```python
order(security, amount, limit_price=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于买卖指定数量为amount的股票，同时支持国债逆回购

注意事项：

1、支持交易场景的逆回购交易。委托方向为卖出(amount必须为负数)，逆回购最小申购金额为1000元(10张)，因此本接口amount入参应大于等于10(10张)，否则会导致委托失败。

2、回测场景，amount有最小下单数量校验，股票、ETF、LOF：100股，可转债：10张；交易场景接口不做amount校验，直接报柜台。

3、交易场景如果limit\_price字段不入参，系统会默认用行情快照数据最新价报单，假如行情快照获取失败会导致委托失败，系统会在日志中增加提醒。

4、由于下述原因，回测中实际买入或者卖出的股票数量有时候可能与委托设置的不一样，针对上述内容调整，系统会在日志中增加警告信息：

1. 根据委托买入数量与价格经计算后的资金数量，大于当前可用资金；
2. 委托卖出数量大于当前可用持仓数量；
3. 每次交易股票时取整100股，交易可转债时取整10张，但是卖出所有股票时不受此限制；
4. 股票停牌、股票未上市或者退市、股票不存在；
5. 回测中每天结束时会取消所有未完成交易；

#### 参数

security: 股票代码(str)；

amount: 交易数量，正数表示买入，负数表示卖出(int)；

limit\_price：买卖限价(float)；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)。

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    #以系统最新价委托
    order('600570.SS', 100)
    # 逆回购1000元
    order('131810.SZ', -10)
    #以39块价格下一个限价单
    order('600570.SS', 100, limit_price=39)
```

### order\_target - 指定目标数量买卖

```python
order_target(security, amount, limit_price=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于买卖股票，直到股票最终数量达到指定的amount

注意事项：

1、该函数不支持逆回购交易。

2、该函数在委托股票时取整100股，委托可转债时取整10张。

3、交易场景如果limit\_price字段不入参，系统会默认用行情快照数据最新价报单，假如行情快照获取失败会导致委托失败，系统会在日志中增加提醒。

4、因可能造成重复下单，因此建议在交易中谨慎使用该接口。具体原因如下：

* 柜台返回持仓数据体现当日变化(由柜台配置决定)：交易场景中持仓信息同步有时滞，一般在6秒左右，假如在这6秒之内连续下单两笔或更多order\_target委托，由于持仓数量不会瞬时更新，会造成重复下单。
* 柜台返回持仓数据体现当日变化(由柜台配置决定)：第一笔委托未完全成交，如果不对第一笔做撤单再次order\_target相同的委托目标数量，引擎不会计算包括在途的总委托数量，也会造成重复下单。
* 柜台返回持仓数据不体现当日变化(由柜台配置决定)：这种情况下持仓数量只会一天同步一次，必然会造成重复下单。

针对以上几种情况，假如要在交易场景使用该接口，首先要确定券商柜台的配置，是否实时更新持仓情况，其次需要增加订单和持仓同步的管理，来配合order\_target使用。

#### 参数

security: 股票代码(str)；

amount: 期望的最终数量(int)；

limit\_price：买卖限价(float)；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)。

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    #买卖恒生电子股票数量到100股
    order_target('600570.SS', 100)
    #卖出恒生电子所有股票
    if data['600570.SS']['close'] > 39:
        order_target('600570.SS', 0)
```

### order\_value - 指定目标价值买卖

```python
order_value(security, value, limit_price=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于买卖指定价值为value的股票

注意事项：

1、该函数不支持逆回购交易。

2、该函数在委托股票时取整100股，委托可转债时取整10张。

3、交易场景如果limit\_price字段不入参，系统会默认用行情快照数据最新价报单，假如行情快照获取失败会导致委托失败，系统会在日志中增加提醒。

#### 参数

security：股票代码(str)；

value：股票价值(float)

limit\_price：买卖限价(float)

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)。

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    #买入价值为10000元的恒生电子股票
    order_value('600570.SS', 10000)

    if data['600570.SS']['close'] > 39:
        #卖出价值为10000元的恒生电子股票
        order_value('600570.SS', -10000)
```

### order\_target\_value - 指定持仓市值买卖

```python
order_target_value(security, value, limit_price=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于调整股票持仓市值到value价值

注意事项：

1、该函数不支持逆回购交易。

2、该函数在委托股票时取整100股，委托可转债时取整10张。

3、交易场景如果limit\_price字段不入参，系统会默认用行情快照数据最新价报单，假如行情快照获取失败会导致委托失败，系统会在日志中增加提醒。

4、因可能造成重复下单，因此建议在交易中谨慎使用该接口。具体原因如下：

* 柜台返回持仓数据体现当日变化(由柜台配置决定)：交易场景中持仓信息同步有时滞，一般在6秒左右，假如在这6秒之内连续下单两笔或更多order\_target\_value委托，由于持仓市值不会瞬时更新，会造成重复下单。
* 柜台返回持仓数据体现当日变化(由柜台配置决定)：第一笔委托未完全成交，如果不对第一笔做撤单再次order\_target\_value相同的委托目标金额，引擎不会计算包括在途的总委托数量，也会造成重复下单。
* 柜台返回持仓数据不体现当日变化(由柜台配置决定)：这种情况下持仓金额只会一天同步一次，必然会造成重复下单。

针对以上几种情况，假如要在交易场景使用该接口，首先要确定券商柜台的配置，是否实时更新持仓情况，其次需要增加订单和持仓同步的管理，来配合order\_target\_value使用。

#### 参数

security: 股票代码(str)；

value: 期望的股票最终价值(float)；

limit\_price：买卖限价(float)；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)。

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    #买卖股票到指定价值
    order_target_value('600570.SS', 10000)

    #卖出当前所有恒生电子的股票
    if data['600570.SS']['close'] > 39:
        order_target_value('600570.SS', 0)
```

### order\_market - 按市价进行委托

```python
order_market(security, amount, market_type, limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于使用多种市价类型进行委托

注意事项：

1. 支持逆回购交易。委托方向为卖出(amount必须为负数)，逆回购最小申购金额为1000元(10张)，因此本接口amount入参应大于等于10(10张)，否则会导致委托失败。
2. 不支持可转债交易.
3. 该函数中market\_type是必传字段，如不传入参数会出现报错。
4. 该函数委托上证股票时limit\_price是必传字段，如不传入参数会出现报错。

#### 参数

security：股票代码(str)；

amount：交易数量(int)，正数表示买入，负数表示卖出；

market\_type：市价委托类型(int)，上证股票支持参数0、1、2、4，深证股票支持参数0、2、3、4、5，必传参数；

limit\_price：保护限价(float)，委托上证股票时必传参数；

* 0：对手方最优价格；
* 1：最优五档即时成交剩余转限价；
* 2：本方最优价格；
* 3：即时成交剩余撤销；
* 4：最优五档即时成交剩余撤销；
* 5：全额成交或撤单；

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def before_trading_start(context, data):
    g.flag = False

def handle_data(context, data):
    if not g.flag:
        # 以35保护限价按对手方最优价格买入100股
        order_market(g.security, 100, 0, 35)
        # 以35保护限价按最优五档即时成交剩余转限价买入100股
        order_market(g.security, 100, 1, 35)
        # 以35保护限价按本方最优价格买入100股
        order_market(g.security, 100, 2, 35)
        # 以35保护限价按最优五档即时成交剩余撤销买入100股
        order_market(g.security, 100, 4, 35)

        # 按对手方最优价格买入100股
        order_market("000001.SZ", 100, 0)
        # 按本方最优价格买入100股
        order_market("000001.SZ", 100, 2)
        # 按即时成交剩余撤销买入100股
        order_market("000001.SZ", 100, 3)
        # 按最优五档即时成交剩余撤销买入100股
        order_market("000001.SZ", 100, 4)
        # 按全额成交或撤单买入100股
        order_market("000001.SZ", 100, 5)
        g.flag = True
```

### ipo\_stocks\_order - 新股一键申购

```python
ipo_stocks_order(market_type=None, black_stocks=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于一键申购当日全部新股

注意事项：

申购黑名单的股票代码必须为申购代码，代码可以是6位数（不带尾缀），也可以带尾缀入参,比如：black\_stocks='787001'或black\_stocks='787001.SS'。

#### 参数

market\_type：申购代码所属市场，不传时默认申购全部新股(int)；

black\_stocks：黑名单股票，可以是单个股票或者股票列表，传入的黑名单股票将不做申购，不传时默认申购全部新股(str/list)；

* 0：上证普通代码；
* 1：上证科创板代码；
* 2：深证普通代码；
* 3：深证创业板代码；
* 4：可转债代码；

#### 返回

返回dict类型，包含委托代码、委托编号、委托状态(委托失败为0，委托成功为1)、委托数量等信息(dict\[str:dict\[str:str,str:int,str:float],...])

#### 示例

```python
import time
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)
    g.flag = False

def before_trading_start(context, data):
    g.flag = False

def handle_data(context, data):
    if not g.flag:
        # 上证普通代码
        log.info("申购上证普通代码：")
        ipo_stocks_order(market_type=0)
        time.sleep(5)
        # 上证科创板代码
        log.info("申购上证科创板代码：")
        ipo_stocks_order(market_type=1)
        time.sleep(5)
        # 深证普通代码
        log.info("申购深证普通代码：")
        ipo_stocks_order(market_type=2)
        time.sleep(5)
        # 深证创业板代码
        log.info("申购深证创业板代码：")
        ipo_stocks_order(market_type=3)
        time.sleep(5)
        # 可转债代码
        log.info("申购可转债代码：")
        ipo_stocks_order(market_type=4)
        time.sleep(5)
        g.flag = True
```

### after\_trading\_order - 盘后固定价委托(股票)

```python
after_trading_order(security, amount, entrust_price)
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于盘后固定价委托申报

注意事项：

1、entrust\_price为必传字段

2、盘后固定价委托时间为9:30\~11:30,13:00\~15:30

#### 参数

security: 股票代码(str)；

amount: 交易数量，正数表示买入，负数表示卖出(int)；

entrust\_price：买卖限价(float)；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)。

#### 示例

```python
def initialize(context):
    g.security = "300001.SZ"
    set_universe(g.security)
    # 15:00-15:30期间使用run_daily进行盘后固定价委托
    run_daily(context, order_test, time="15:15")
    g.flag = False

def order_test(context):
    snapshot = get_snapshot(g.security)
    if snapshot is not None:
        last_px = snapshot[g.security].get("last_px", 0)
        if last_px > 0:
            after_trading_order(g.security, 200, float(last_px))

def handle_data(context, data):
    if not g.flag:
        snapshot = get_snapshot(g.security)
        if snapshot is not None:
            last_px = snapshot[g.security].get("last_px", 0)
            if last_px > 0:
                after_trading_order(g.security, 200, float(last_px))
                g.flag = True
```

### after\_trading\_cancel\_order - 盘后固定价委托撤单(股票)

```python
after_trading_cancel_order(order_param)
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于盘后固定价委托取消订单，根据Order对象或order\_id取消订单。

注意事项：

无

#### 参数

order\_param: [Order对象](#Order)或者order\_id(Order/str)

#### 返回

None

#### 示例

```python
import time

def initialize(context):
    g.security = "300001.SZ"
    set_universe(g.security)
    # 15:00-15:30期间使用run_daily进行盘后固定价委托、盘后固定价委托撤单
    run_daily(context, order_test, time="15:15")
    g.flag = False

def order_test(context):
    snapshot = get_snapshot(g.security)
    if snapshot is not None:
        last_px = snapshot[g.security].get("last_px", 0)
        if last_px > 0:
            order_id = after_trading_order(g.security, 200, float(last_px))
            time.sleep(5)
            after_trading_cancel_order(order_id)


def handle_data(context, data):
    if not g.flag:
        snapshot = get_snapshot(g.security)
        if snapshot is not None:
            last_px = snapshot[g.security].get("last_px", 0)
            if last_px > 0:
                order_id = after_trading_order(g.security, 200, float(last_px))
                time.sleep(5)
                after_trading_cancel_order(order_id)
                g.flag = True
```

### etf\_basket\_order - ETF成分券篮子下单

```python
etf_basket_order(etf_code ,amount, price_style=None, position=True, info=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于ETF成分券篮子下单。

注意事项：

无

#### 参数

etf\_code : 单支ETF代码，必传参数(str)

amount : 下单篮子份数, 正数表示买入, 负数表示卖出，必传参数(int)

price\_style : 设定委托价位，可传入’B1’、’B2’、’B3’、’B4’、’B5’、’S1’、’S2’、’S3’、’S4’、’S5’、’new’，分别为买一\~买五、卖一\~卖五、最新价，默认为最新价(str)

position : 取值True和False，仅在篮子买入时使用。申购是否使用持仓替代，True为使用，该情况下篮子股票买入时使用已有的持仓部分；False为不使用。默认使用持仓替代(bool)

info : dict类型，成份股信息。key为成分股代码，values为dict类型，包含的成分股信息字段作为key(Mapping\[str, Mapping\[str, Union\[int, float]]]):

* cash\_replace\_flag -- 设定现金替代标志，1为替代，0为不替代，仅允许替代状态的标的传入有效，否则无效，如不传入info或不传入该字段信息系统默认为成分股不做现金替代
* position\_replace\_flag -- 设定持仓替代标志，1为替代，0为不替代，如不传入info或不传入该字段信息按position参数的设定进行计算
* limit\_price -- 设定委托价格，如不传入info或不传入该字段信息按price\_style参数的设定进行计算

#### 返回

创建订单成功，正常返回一个dict类型字段， key为股票代码，values为Order对象的id，失败则返回空dict，如{}(dict\[str:str]))

#### 示例

```python
def initialize(context):
    g.security = get_Ashares()
    set_universe(g.security)

def handle_data(context, data):
    #ETF成分券篮子下单
    etf_basket_order('510050.SS' ,1, price_style='S3',position=True)
    stock_info = {'600000.SS':{'cash_replace_flag':1,'position_replace_flag':1,'limit_price':12}}
    etf_basket_order('510050.SS' ,1, price_style='S2',position=False, info=stock_info)
```

### etf\_purchase\_redemption - ETF基金申赎接口

```python
etf_purchase_redemption(etf_code,amount,limit_price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用、仅在股票交易模块可用

#### 接口说明

该接口用于单只ETF基金申赎。

注意事项：

无

#### 参数

etf\_code : 单支ETF代码，必传参数(str)

amount : 基金申赎数量, 正数表示申购, 负数表示赎回(int)

#### 返回

创建订单成功，返回Order对象的id，失败则返回None(str)

#### 示例

```python
def initialize(context):
    g.security = '510050.SS'
    set_universe(g.security)

def handle_data(context, data):
    #ETF申购
    etf_purchase_redemption('510050.SS',900000)
    #ETF赎回
    etf_purchase_redemption('510050.SS',-900000,limit_price = 2.9995)
```

### get\_positions - 获取多支股票持仓信息

```python
get_positions(security)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取多支股票的持仓信息详情。

注意事项：

无

#### 参数

security：股票代码，可以为一个列表，不传时默认为获取所有持仓(list\[str]/str)；

#### 返回

返回一个数据字典，键为股票代码，值为[Position对象](#Position)(dict\[str:Position])，如下：

注意：四位尾缀或者两位尾缀代码皆可作为键取到返回的数据字典值，如'600570.XSHG'或者'600570.SS'。

```python
{'600570.XSHG': <Position {'business_type': 'stock', 'short_amount': 0, 'contract_multiplier': 1, 'short_pnl': 0, 'delivery_date': None, 'today_short_amount': 0, 'last_sale_price': 118.7, 'sid': '600570.SS',
'enable_amount': 100, 'margin_rate': 1, 'amount': 200, 'long_amount': 0, 'short_cost_basis': 0, 'today_long_amount': 0, 'cost_basis': 117.9, 'long_pnl': 0, 'long_cost_basis': 0}>}
```

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS','600000.SS']
    set_universe(g.security)

def handle_data(context, data):
    log.info(get_positions('600570.SS'))
    log.info(get_positions(g.security))
    log.info(get_positions())
```

## 公共交易函数

### order\_tick - tick行情触发买卖

```python
order_tick(sid, amount, priceGear='1', limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于在tick\_data模块中进行买卖股票下单，可设定价格档位进行委托。

注意事项：

该函数只能在tick\_data模块中使用

#### 参数

sid：股票代码(str)；

amount：交易数量，正数表示买入，负数表示卖出(int)

priceGear：盘口档位，level1:1\~5买档/-1\~-5卖档，level2:1\~10买档/-1\~-10卖档(str)

limit\_price：买卖限价，当输入参数中也包含priceGear时，下单价格以limit\_price为主(float)；

#### 返回

返回一个委托流水编号(str)

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def tick_data(context,data):
    security = g.security
    current_price = eval(data[security]['tick']['bid_grp'][0])[1][0]
    if current_price > 56 and current_price < 57:
        # 以买一档下单
        order_tick(g.security, -100, "1")
        # 以卖二档下单
        order_tick(g.security, 100, "-2")
        # 以指定价格下单
        order_tick(g.security, 100, limit_price=56.5)

def handle_data(context, data):
    pass
```

### cancel\_order - 撤单

```python
cancel_order(order_param)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于取消订单，根据[Order对象](#Order)或order\_id取消订单。

注意事项：

无

#### 参数

order\_param: [Order对象](#Order)或者order\_id(Order/str)

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    _id = order(g.security, 100)

    cancel_order(_id)
    log.info(get_order(_id))
```

### cancel\_order\_ex - 撤单

```python
cancel_order_ex(order_param)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于取消订单，根据[get\_all\_orders](#get_all_orders)返回列表中的单个字典取消订单。

注意事项：

该函数仅可撤[get\_all\_orders](#get_all_orders)函数返回的可撤状态订单。

账户多个交易运行时调用该函数会撤销其他交易产生的订单，可能对其他正在运行的交易策略产生影响。

#### 参数

order\_param: [get\_all\_orders](#get_all_orders)函数返回列表的单个字典(dict)

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    g.count = 0

def handle_data(context, data):
    if g.count == 0:
        log.info("当日全部订单为：%s" % get_all_orders())
        # 遍历账户当日全部订单，对已报、部成状态订单进行撤单操作
        for _order in get_all_orders():
            if _order['status'] in ['2', '7']:
                cancel_order_ex(_order)
    if g.count == 1:
        # 查看撤单是否成功
        log.info("当日全部订单为：%s" % get_all_orders())
    g.count += 1
```

### debt\_to\_stock\_order - 债转股委托

```python
debt_to_stock_order(security, amount)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于可转债转股操作。

注意事项：

无

#### 参数

security: 可转债代码(str)

amount: 委托数量(int)

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)。

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def before_trading_start(context, data):
    g.count = 0

def handle_data(context, data):
    if g.count == 0:
        # 对持仓内的国贸转债进行转股操作
        debt_to_stock_order("110033.SS", -1000)
        g.count += 1
    # 查看委托状态
    log.info(get_orders())
    g.count += 1
```

### get\_open\_orders - 获取未完成订单

```python
get_open_orders(security=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取当天所有未完成的订单，或按条件获取指定未完成的订单。

注意事项：

无

#### 参数

security：标的代码，如'600570.SS'，不传时默认为获取所有未成交订单(str)；

#### 返回

返回一个list，该list中包含多个[Order对象](#Order)(list\[Order,...])。

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    for _sec in g.security:
        _id = order(_sec, 100, limit_price = 30)
    # 当运行周期为分钟则可获取本周期及之前所有未完成的订单
    dict_list = get_open_orders()
    log.info(dict_list)

# 当运行周期为天，可在after_trading_end中调用此函数获取当天未完成的订单
def after_trading_end(context, data):
    dict_list = get_open_orders()
    log.info(dict_list)
```

### get\_order - 获取指定订单

```python
get_order(order_id)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取指定编号订单。

注意事项：

无

获取指定编号订单。

#### 参数

order\_id：订单编号(str)

#### 返回

返回一个list，该list中只包含一个[Order对象](#Order)(list\[Order])。

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    order_id = order(g.security, 100)
    current_order = get_order(order_id)
    log.info(current_order)
```

### get\_orders - 获取全部订单

```python
get_orders(security=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取策略内所有订单，或按条件获取指定订单。

注意事项：

无

#### 参数

security：标的代码，如'600570.SS'，不传时默认为获取所有订单(str)；

#### 返回

返回一个list，该list中包含多个[Order对象](#Order)(list\[Order,...])。

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    _id = order(g.security, 100)

    order_obj = get_orders()
    log.info(order_obj)
```

### get\_all\_orders - 获取账户当日全部订单

```python
get_all_orders(security=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于获取账户当日所有订单(包含非本交易的订单记录)，或按条件获取指定代码的订单。

注意事项：

1、该函数返回账户当日在柜台的全部委托记录，不能查询策略中待报、未报状态的委托。

2、该函数返回的可撤委托仅可通过[cancel\_order\_ex](#cancel_order_ex)函数进行撤单，且非本交易的委托进行撤单仅可通过本函数查询委托状态更新。

#### 参数

security：标的代码，如'600570.SS'，不传时默认为获取所有订单(str)；

#### 返回

返回一个list，该list中包含多条订单记录(list\[dict, ...])：

\[{'symbol': 股票代码(str), 'entrust\_no': 委托编号(str), 'amount': 委托数量(int), 'entrust\_bs': 委托方向(int), 'price': 委托价格(float), 'status': 委托状态(str), 'filled\_amount': 成交数量(int)}, ...]

字段备注:

* entrust\_bs -- 成交方向，1-买，2-卖；
* status -- 委托状态，详见[Order对象](#Order)中status字段；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取账户当日委托600570代码的全部订单
    log.info('当日委托600570代码的全部订单：%s' % get_all_orders(g.security))
    # 获取账户当日全部订单
    log.info('当日全部订单：%s' % get_all_orders())
```

### get\_trades - 获取当日成交订单

```python
get_trades()
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取策略内当日已成交订单详情。

注意事项：

1、为减小对柜台压力，该函数在股票交易模块中同一分钟内多次调用返回当前分钟首次查询的缓存数据；

2、该接口会返回当日截止到当前时间段内的成交数据；

3、一个订单编号会对应一笔或多笔成交记录；

4、股票、期货、期权返回字段不同；

#### 参数

无

#### 返回

返回数据：

一个订单编号一笔成交：{'订单编号': \[ \[] ]} ( dict{ str: list\[ list\[] ] } )

一个订单编号多笔成交：{'订单编号': \[ \[], \[] ]} ( dict{ str: list\[ list\[], list\[] ] } )

股票返回字段：{'订单编号': \[ \[成交编号, 委托编号, 标的代码, 买卖类型, 成交数量, 成交价格, 成交金额, 成交时间] ] }

期货返回字段：{'订单编号': \[ \[成交编号, 委托编号, 标的代码, 买卖类型, 开平仓类型, 成交数量, 成交价格, 成交金额, 成交时间] ] }

期权返回字段：{'订单编号': \[ \[成交编号, 委托编号, 标的代码, 买卖类型, 开平仓类型, 成交数量, 成交价格, 成交金额, 成交时间, 备兑标志] ] }

* 成交编号： str类型
* 委托编号： str类型
* 标的代码： str类型
* 买卖类型： str类型
* 开平仓类型： 仅支持期货、期权，str类型
* 成交数量： float类型
* 成交价格： float类型
* 成交金额： float类型
* 成交时间： str类型
* 备兑标志： 仅支持期权，str类型

示例如下(股票)：

注意：股票标的代码尾缀为四位，上证为XSHG，深圳为XSHE，如需对应到代码请做代码尾缀兼容

```python
{'ba6a80d9746347a99c050b29069807c7': [['5001', 700001, '600570.XSHG', '买', 100000.0, 86.60, 8660000.0, '2021-08-15 09:32:00']]}
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #获取当日成交数据
    trades_info = get_trades()
    log.info(trades_info)
```

### get\_position - 获取持仓信息

```python
get_position(security)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

该接口用于获取某个标的持仓信息详情。

注意事项：

无

#### 参数

security：标的代码，如'600570.SS'，不传时默认为获取所有持仓(str)；

#### 返回

返回一个[Position对象](#Position)(Position)。

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    position = get_position(g.security)
    log.info(position)
```

# 融资融券专用函数

## 融资融券交易类函数

### margin\_trade - 担保品买卖

```python
margin_trade(security, amount, limit_price=None, market_type=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融回测、两融交易模块可用。

#### 接口说明

该接口用于担保品买卖。

注意事项：

1. 限价和市价委托类型都不传时默认取当前最新价进行限价委托，限价和市价委托类型都传入时以limit\_price为委托限价进行市价委托。
2. 当market\_type传入且委托上证股票时，limit\_price为保护限价字段，必传字段。

#### 参数

security：股票代码(str)；

amount：交易数量(int)，正数表示买入，负数表示卖出；

limit\_price：买卖限价/保护限价(float)；

market\_type：市价委托类型(int)，上证股票支持参数0、1、2、4，深证股票支持参数0、2、3、4、5；

* 0：对手方最优价格；
* 1：最优五档即时成交剩余转限价；
* 2：本方最优价格；
* 3：即时成交剩余撤销；
* 4：最优五档即时成交剩余撤销；
* 5：全额成交或撤单；

#### 返回

Order对象中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def before_trading_start(context, data):
    g.flag = False

def handle_data(context, data):
    if not g.flag:
        # 以系统最新价委托
        margin_trade(g.security, 100)
        # 以46块价格下一个限价单
        margin_trade(g.security, 100, limit_price=46)

        # 以46保护限价按最优五档即时成交剩余转限价买入100股
        margin_trade(g.security, 100, limit_price=46, market_type=1)
        # 按全额成交或撤单买入100股
        margin_trade("000001.SZ", 100, market_type=5)
        g.flag = True
```

### margincash\_open - 融资买入

```python
margincash_open(security, amount, limit_price=None, market_type=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于融资买入。

注意事项：

1. 限价和市价委托类型都不传时默认取当前最新价进行限价委托，限价和市价委托类型都传入时以limit\_price为委托限价进行市价委托。
2. 当market\_type传入且委托上证股票时，limit\_price为保护限价字段，必传字段。

#### 参数

security：股票代码(str)；

amount：交易数量，输入正数(int)；

limit\_price：买卖限价(float)；

market\_type：市价委托类型(int)，上证股票支持参数0、1、2、4，深证股票支持参数0、2、3、4、5；

* 0：对手方最优价格；
* 1：最优五档即时成交剩余转限价；
* 2：本方最优价格；
* 3：即时成交剩余撤销；
* 4：最优五档即时成交剩余撤销；
* 5：全额成交或撤单；

#### 返回

Order对象中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe(g.security)

def before_trading_start(context, data):
    g.flag = False

def handle_data(context, data):
    if not g.flag:
        # 以系统最新价委托
        margincash_open(g.security, 100)
        # 以46块价格下一个限价单
        margincash_open(g.security, 100, limit_price=46)

        # 以46保护限价按最优五档即时成交剩余转限价买入100股
        margincash_open(g.security, 100, limit_price=46, market_type=1)
        # 按全额成交或撤单买入100股
        margincash_open("000001.SZ", 100, market_type=5)
        g.flag = True
```

### margincash\_close - 卖券还款

```python
margincash_close(security, amount, limit_price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于卖券还款。

注意事项：

无

#### 参数

security：股票代码(str)；

amount：交易数量，输入正数(int)；

limit\_price：买卖限价(float)；

#### 返回

Order对象中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    # 卖100股还款
    margincash_close(security, 100)
```

### margincash\_direct\_refund - 直接还款

```python
margincash_direct_refund(value)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于直接还款。

注意事项：

无

#### 参数

value：还款金额(float)；

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取负债总额
    fin_compact_balance = get_margin_assert().get('fin_compact_balance')
    # 还款
    margincash_direct_refund(fin_compact_balance)
```

### marginsec\_open - 融券卖出

```python
marginsec_open(security, amount, limit_price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于融券卖出。

注意事项：

无

#### 参数

security：股票代码(str)；

amount：交易数量，输入正数(int)；

limit\_price：买卖限价(float)；

#### 返回

Order对象中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)

#### 示例

```python
def initialize(context):
    g.security = '600030.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    # 融券卖出100股
    marginsec_open(security, 100)
```

### marginsec\_close - 买券还券

```python
marginsec_close(security, amount, limit_price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于买券还券。

注意事项：

无

#### 参数

security：股票代码(str)；

amount：交易数量，输入正数(int)；

limit\_price：买卖限价(float)；

#### 返回

Order对象中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None(str)

#### 示例

```python
def initialize(context):
    g.security = '600030.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    #买100股还券
    marginsec_close(security, 100)
```

### marginsec\_direct\_refund - 直接还券

```python
marginsec_direct_refund(security, amount)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于直接还券。

注意事项：

无

#### 参数

security：股票代码(str)；

amount：交易数量，输入正数(int)；

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600030.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    #买100股
    marginsec_direct_refund(security, 100)
```

## 融资融券查询类函数

### get\_margincash\_stocks - 获取融资标的列表

```python
get_margincash_stocks()
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于获取融资标的。

注意事项：

无

#### 参数

无

#### 返回

返回上交所、深交所最近一次披露的的可融资标的列表的list(list\[str,...])

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取最新的融资标的列表
    margincash_stocks = get_margincash_stocks()
    log.info(margincash_stocks)
```

### get\_marginsec\_stocks - 获取融券标的列表

```python
get_marginsec_stocks()
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于获取融券标的。

注意事项：

无

#### 参数

无

#### 返回

返回上交所、深交所最近一次披露的的可融券标的列表的list(list\[str,...])

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取最新的融券标的列表
    marginsec_stocks = get_marginsec_stocks()
    log.info(marginsec_stocks)
```

### get\_margin\_contract - 合约查询

```python
get_margin_contract()
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于合约查询。

注意事项：

无

#### 参数

无

#### 返回

正常返回一个DataFrame类型字段，columns为每个合约所包含的信息(相应字段无数据时返回None)，异常返回None

合约包含以下信息：

* open\_date:开户日期(str:int)；
* compact\_id:合约编号(str:str)；
* stock\_code:证券代码(str:str)；
* entrust\_no:委托编号(str:str)；
* entrust\_price:委托价格(str:float)；
* entrust\_amount:委托数量(str:float)；
* business\_amount:成交数量(str:float)；
* business\_balance:成交金额(str:float)；
* compact\_type:合约类别(str:str)；
* compact\_status:合约状态(str:str)；
* repaid\_interest:已还利息(str:float)；
* repaid\_amount:已还数量(str:float)；
* repaid\_balance:已还金额(str:float)；
* used\_bail\_balance:已用保证金(str:float)；
* ret\_end\_date:归还截止日(str:int)；
* date\_clear:清算日期(str:int)；
* fin\_income:融资合约盈亏(str:float)；
* slo\_income:融券合约盈亏(str:float)；
* total\_debit:负债总额(str:float)；
* compact\_interest:合约利息金额(str:float)；
* real\_compact\_interest:日间实时利息金额(str:float)；
* real\_compact\_balance:日间实时合约金额(str:float)；
* real\_compact\_amount:日间实时合约数量(str:float)；

字段备注:

* compact\_type -- 合约类别，0-融资，1-融券，2-其他负债；；
* compact\_status -- 合约状态；
  * 0 -- 开仓未归还；
  * 1 -- 部分归还；
  * 2 -- 合约已过期；
  * 3 -- 客户自行归还；
  * 4 -- 手工了结；
  * 5 -- 未形成负债；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取最新合约
    df = get_margin_contract()
    log.info(df)
```

### get\_margin\_contractreal - 实时合约流水查询

```python
get_margin_contractreal()
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于实时合约流水查询。

注意事项：

无

#### 参数

无

#### 返回

正常返回一个DataFrame类型字段，columns为每个合约所包含的信息(相应字段无数据时返回None)，异常返回None

实时合约流水包含以下信息：

* init\_date:交易日期(str:int)；
* compact\_id:合约编号(str:str)；
* client\_id:客户编号(str:str)；
* money\_type:币种类别(str:str)；
* market\_type:证券市场(str:str)；
* entrust\_no:委托编号(str:str)；
* compact\_type:合约类别(str:str)；
* stock\_code:证券代码(str:str)；
* business\_flag:业务标志(str:int)；
* occur\_balance:发生金额(str:float)；
* post\_balance:后资金额(str:float)；
* occur\_amount:发生数量(str:float)；
* post\_amount:后证券额(str:float)；
* occur\_fare:发生费用(str:float)；
* post\_fare:后余费用(str:float)；
* occur\_interest:发生利息(str:float)；
* post\_interest:后余利息(str:float)；
* remark:备注(str:str)；

字段备注:

* compact\_type -- 合约类别，0-融资，1-融券，2-其他负债；；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取实时流水
    df = get_margin_contractreal()
    log.info(df)
```

### get\_margin\_assert - 信用资产查询

```python
get_margin_assert()
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于信用资产查询。

注意事项：

无

#### 参数

无

#### 返回

正常返回一个dict类型字段，包含所有信用资产信息。异常返回空dict，如{}(dict\[str:float,...])

信用资产包含以下信息(相应字段无数据时返回None)：

* assure\_asset:担保资产(str:float)；
* total\_debit:负债总额(str:float)；
* enable\_bail\_balance:可用保证金(str:float)；
* assure\_enbuy\_balance:买担保品可用资金(str:float)；
* fin\_enrepaid\_balance:现金还款可用资金(str:float)；
* fin\_max\_quota:融资额度上限(str:float)；
* fin\_enable\_quota:融资可用额度(str:float)；
* fin\_used\_quota:融资已用额度(str:float)；
* fin\_compact\_balance:融资合约金额(str:float)；
* fin\_compact\_fare:融资合约费用(str:float)；
* fin\_compact\_interest:融资合约利息(str:float)；
* slo\_enable\_quota:融券可用额度(str:float)；
* slo\_compact\_fare:融券合约费用(str:float)；
* slo\_compact\_interest:融券合约利息(str:float)；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取信用账户资产信息
    margin_asset = get_margin_assert()
    log.info(margin_asset)
```

### get\_assure\_security\_list - 担保券查询

```python
get_assure_security_list()
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于担保券查询。

注意事项：

无

#### 参数

无

#### 返回

返回上交所、深交所最近一次披露的担保券列表的list(list\[str,...])

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取最新的担保券列表
    assure_security = get_assure_security_list()
    log.info(assure_security)
```

### get\_margincash\_open\_amount - 融资标的最大可买数量查询

```python
get_margincash_open_amount(security, price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于融资标的最大可买数量查询。

注意事项：

无

#### 参数

security：股票代码(str)；

price：限定价格(float)；

#### 返回

正常返回一个dict类型对象，key为股票代码，values为最大数量。异常返回空dict，如{}(dict\[str:int])

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    # 查询恒生电子最大可融资买入数量
    margincash_open_dict = get_margincash_open_amount(security)
    if margincash_open_dict is not None:
        log.info(margincash_open_dict.get(security))
```

### get\_margincash\_close\_amount - 卖券还款标的最大可卖数量查询

```python
get_margincash_close_amount(security, price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于卖券还款标的最大可卖数量查询。

注意事项：

无

#### 参数

security：股票代码(str)；

price：限定价格(float)；

#### 返回

正常返回一个dict类型对象，key为股票代码，values为最大数量。异常返回空dict，如{}(dict\[str:int])

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    # 查询恒生电子最大可卖券还款数量
    margincash_close_dict = get_margincash_close_amount(security)
    if margincash_close_dict is not None:
        log.info(margincash_close_dict.get(security))
```

### get\_marginsec\_open\_amount - 融券标的最大可卖数量查询

```python
get_marginsec_open_amount(security, price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于融券标的最大可卖数量查询。

注意事项：

无

#### 参数

security：股票代码(str)；

price：限定价格(float)；

#### 返回

正常返回一个dict类型对象，key为股票代码，values为最大数量。异常返回空dict，如{}(dict\[str:int])

#### 示例

```python
def initialize(context):
    g.security = '600030.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    # 查询中信证券最大可融券卖出数量
    marginsec_open_dict = get_marginsec_open_amount(security)
    if marginsec_open_dict is not None:
        log.info(marginsec_open_dict.get(security))
```

### get\_marginsec\_close\_amount - 买券还券标的最大可买数量查询

```python
get_marginsec_close_amount(security, price=None)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于买券还券标的最大可买数量查询。

注意事项：

无

#### 参数

security：股票代码(str)；

price：限定价格(float)；

#### 返回

正常返回一个dict类型对象，key为股票代码，values为最大数量。异常返回空dict，如{}(dict\[str:int])

#### 示例

```python
def initialize(context):
    g.security = '600030.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    # 查询中信证券最大可买券还券数量
    marginsec_close_dict = get_marginsec_close_amount(security)
    if marginsec_close_dict is not None:
        log.info(marginsec_close_dict.get(security))
```

### get\_margin\_entrans\_amount - 现券还券数量查询

```python
get_margin_entrans_amount(security)
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于现券还券数量查询。

注意事项：

无

#### 参数

security：股票代码(str)；

#### 返回

正常返回一个dict类型对象，key为股票代码，values为最大数量。异常返回空dict，如{}(dict\[str:int])

#### 示例

```python
def initialize(context):
    g.security = '600030.SS'
    set_universe(g.security)

def handle_data(context, data):
    security = g.security
    # 查询中信证券最大可现券还券数量
    margin_entrans_dict = get_margin_entrans_amount(security)
    if margin_entrans_dict is not None:
        log.info(margin_entrans_dict.get(security))
```

### get\_enslo\_security\_info - 融券头寸信息查询

```python
get_enslo_security_info()
```

#### 使用场景

该函数仅支持Ptrade客户端可用，仅在两融交易模块可用。

#### 接口说明

该接口用于获取融券头寸信息。

注意事项：

无

#### 参数

无

#### 返回

正常返回一个dict类型对象，key为股票代码，values为dict，包含返回的相关字段信息，如(dict\[{}, {}])。异常返回None。

包含以下信息(相应字段无数据时返回None)：

* market\_type: 市场，包括SH、SZ(str)；
* slo\_ratio: 融券保证金比例(float)；
* enable\_amount: 可用数量(int)；
* real\_buy\_amount: 回报买入数量(int)；
* real\_sell\_amount: 回报卖出数量(int)；
* slo\_status: 融券状态，包括"0":正常，"1":暂停，"2":作废(str)；
* cashgroup\_prop: 头寸性质，包括"0":核心，"1":普通，"2":专项(str)；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 获取最新的融券头寸信息
    h = get_enslo_security_info()
    log.info(h)
```

# 期货专用函数

## 期货交易类函数

### buy\_open - 多开

```python
buy_open(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

买入开仓

注意：

不同期货品种每一跳的价格变动都不一样，limit\_price入参的时候要参考对应品种的价格变动规则，如limit\_price不做入参则会以交易的行情快照最新价或者回测的分钟最新价进行报单；

根据交易所规则，每天结束时会取消所有未完成交易；

#### 参数

contract：期货合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = ['IF2312.CCFX']
    set_universe(g.security)

def handle_data(context, data):
    #买入开仓
    buy_open('IF2312.CCFX', 1)
```

### sell\_close - 多平

```python
sell_close(contract, amount, limit_price=None, close_today=False)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

卖出平仓

注意：

不同期货品种每一跳的价格变动都不一样，limit\_price入参的时候要参考对应品种的价格变动规则，如limit\_price不做入参则会以交易的行情快照最新价或者回测的分钟最新价进行报单；

根据交易所规则，每天结束时会取消所有未完成交易；

#### 参数

contract：期货合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

close\_today：平仓方式。close\_today=False为优先平昨仓，不足部分再平今仓；close\_today=True为仅平今仓，委托数量若大于今仓系统会调整为今仓数量。close\_today=True仅对上海期货交易所生效，其他交易所无需入参close\_today字段，若设置为True系统会警告，并强行转换为close\_today=False。

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = ['IF2312.CCFX']
    set_universe(g.security)

def handle_data(context, data):
    #卖出平仓
    sell_close('IF2312.CCFX', 1)
```

### sell\_open - 空开

```python
sell_open(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

卖出开仓

注意：

不同期货品种每一跳的价格变动都不一样，limit\_price入参的时候要参考对应品种的价格变动规则，如limit\_price不做入参则会以交易的行情快照最新价或者回测的分钟最新价进行报单；

根据交易所规则，每天结束时会取消所有未完成交易；

#### 参数

contract：期货合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = ['IF2312.CCFX']
    set_universe(g.security)

def handle_data(context, data):
    #卖出开仓
    sell_open('IF2312.CCFX', 1)
```

### buy\_close - 空平

```python
buy_close(contract, amount, limit_price=None, close_today=False)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

买入平仓

注意：

不同期货品种每一跳的价格变动都不一样，limit\_price入参的时候要参考对应品种的价格变动规则，如limit\_price不做入参则会以交易的行情快照最新价或者回测的分钟最新价进行报单；

根据交易所规则，每天结束时会取消所有未完成交易；

#### 参数

contract：期货合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

close\_today：平仓方式。close\_today=False为优先平昨仓，不足部分再平今仓；close\_today=True为仅平今仓，委托数量若大于今仓系统会调整为今仓数量。close\_today=True仅对上海期货交易所生效，其他交易所无需入参close\_today字段，若设置为True系统会警告，并强行转换为close\_today=False。

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = ['IF2312.CCFX']
    set_universe(g.security)

def handle_data(context, data):
    #买入平仓
    buy_close('IF2312.CCFX', 1)
```

## 期货查询类函数

### get\_margin\_rate- 获取用户设置的保证金比例

```python
get_margin_rate(transaction_code)
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

获取用户设置的保证金比例

#### 参数

transaction\_code：期货合约的交易代码，str类型，如沪铜2112（"CU2112"）的交易代码为"CU"；

#### 返回

用户设置的保证金比例，float浮点型数据，默认返回交易所设定的保证金比例；

#### 示例

```python
def initialize(context):
    g.security = "IF2312.CCFX"
    set_universe(g.security)
    # 设置沪深300指数的保证金比例为8%
    set_margin_rate("IF", 0.08)

def before_trading_start(context, data):
    # 获取沪深300指数的保证金比例
    margin_rate = get_margin_rate("IF")
    log.info(margin_rate)
    # 获取5年期国债的保证金比例
    margin_rate = get_margin_rate("TF")
    log.info(margin_rate)

def handle_data(context, data):
    pass
```

### get\_instruments- 获取合约信息

```python
get_instruments(contract)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

获取合约的上市的具体信息

#### 参数

contract：字符串，期货的合约代码，str类型；

#### 返回

FutureParams对象，主要返回的字段为:

* contract\_code -- 合约代码，str类型；
* contract\_name -- 合约名称，str类型；
* exchange -- 交易所：大商所、郑商所、上期所、中金所，str类型；
* trade\_unit -- 交易单位，int类型；
* contract\_multiplier -- 合约乘数，float类型；
* delivery\_date -- 交割日期，str类型；
* listing\_date -- 上市日期，str类型；
* trade\_code -- 交易代码，str类型；
* margin\_rate -- 保证金比例，float类型；

注意：

期货实盘模块中，由于行情源的限制，涨跌幅目前暂无法提供

#### 示例

```python
def initialize(context):
    g.security = ["IF2312.CCFX"]
    set_universe(g.security)

def before_trading_start(context, data):
    # 获取股票池代码合约信息
    for security in g.security:
        info = get_instruments(security)
    log.info(info)

def handle_data(context, data):
    pass
```

## 期货设置类函数

### set\_future\_commission - 设置期货手续费

```python
set_future_commission(transaction_code, commission)
```

#### 使用场景

该函数仅在回测模块可用

#### 接口说明

设置期货手续费，手续费是按照交易代码进行设置的

#### 参数

transaction\_code：期货合约的交易代码，str类型，如沪铜2112（"CU2112"）的交易代码为"CU"；

commission：手续费，浮点型，设置说明：

* 当交易时的手续费是按手数收取时，则这里应当设置为每手收取的金额，例如：将期货的手续费设置为2元/手，此处应填写2；
* 当交易时的手续费是按总成交额收取时，则这里应当设置为总成交额的比例，例如：将期货的手续费费率设置为0.4/万，此处应填写0.00004；

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = "IF2312.CCFX"
    set_universe(g.security)
    # 设置沪深300指数的手续费，0.4/万
    set_future_commission("IF", 0.00004)
    # 设置沪深300指数的手续费，2元/手
    set_future_commission("IF", 2)

def handle_data(context, data):
    # 买入指数2312
    buy_open(g.security, 2)
```

### set\_margin\_rate - 设置期货保证金比例

```python
set_margin_rate(transaction_code, margin_rate)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

设置期货收取的保证金比例，保证金比例是按照交易代码进行设置的

#### 参数

transaction\_code：期货合约的交易代码，str类型，如沪铜2112（"CU2112"）的交易代码为"CU"；

margin\_rate：保证金比例，浮点型，将对应期货的保证金比例设置为5%则输入0.05；

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = "IF2312.CCFX"
    set_universe(g.security)
    # 设置沪深300指数收取的保证金比例设置为5%
    set_margin_rate("IF", 0.05)

def handle_data(context, data):
    # 买入指数2312
    buy_open(g.security, 10)
```

# 期权专用函数

## 期权查询类函数

### get\_opt\_objects - 获取期权标的列表

```python
get_opt_objects(date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

用于获取某日期的ETF期权标的，默认返回当前交易日的期权标的

注意：

无

#### 参数

date：查询日期，str类型，仅支持YYYYmmdd或者YYYY-mm-dd格式；

#### 返回

期权标的列表，list类型，调用异常返回\[]。

#### 示例

```python
def initialize(context):
    pass

def handle_data(context, data):
    # 获取2022年07月03日的所有ETF期权标的列表
    get_opt_objects(date='20220703')
```

```python
生成的列表：['510050.SS', '510300.SS', '159919.SZ']
```

### get\_opt\_last\_dates - 获取期权标的到期日列表

```python
get_opt_last_dates(security, date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

用于获取某日期的ETF期权标的到期日，默认返回当前交易日的到期日

注意：

无

#### 参数

security：查询标的，str类型，如'510050.SS'；

date：查询日期，str类型，仅支持YYYYmmdd或者YYYY-mm-dd格式；

#### 返回

期权标的到期日列表，list类型，调用异常返回\[]。

#### 示例

```python
def initialize(context):
    pass

def handle_data(context, data):
    # 获取2022年07月03日的所有50ETF期权标的到期日列表
    get_opt_last_dates('510050.SS', date='20220703')
```

```python
生成的列表：['2022-07-27', '2022-09-28', '2022-12-28']
```

### get\_opt\_contracts - 获取期权标的对应合约列表

```python
get_opt_contracts(security, date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

用于获取某期权标的某交易日处于挂牌期间的合约列表

注意：

无

#### 参数

security：查询标的，str类型，如'510050.SS'；

date：查询日期，str类型，仅支持YYYYmmdd或者YYYY-mm-dd格式；

#### 返回

期权标的合约列表，list类型，调用异常返回\[]。

#### 示例

```python
def initialize(context):
    pass

def handle_data(context, data):
    # 获取2022年07月03日50ETF期权标的对应的挂牌期合约列表
    get_opt_contracts('510050.SS', date='20220703')
```

```python
生成的列表：['10003975.XSHO', '10003976.XSHO', '10003977.XSHO', '10003978.XSHO', '10003979.XSHO', '10003980.XSHO', '10003981.XSHO', ... , '10004332.XSHO', '10004337.XSHO', '10004338.XSHO', '10004339.XSHO', '10004340.XSHO']
```

### get\_contract\_info - 获取期权合约信息

```python
get_contract_info(contract)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

用于获取期权合约信息

注意：

无

#### 参数

contract：合约编号，str类型，如上证期权'10003975.XSHO'、深圳期权'90000961.XSZO'；

#### 返回

字典类型，主要返回的字段为:

* contract\_code -- 合约代码，str类型；
* contract\_name -- 合约名称，str类型；
* exchange -- 交易所：上交所、深交所，str类型；
* warrant\_way -- 期权类型，10-欧式，20-美式，30-百慕大式，str类型；
* contract\_multiplier -- 合约乘数，float类型；
* expiration\_date -- 到期日，str类型；
* listing\_date -- 上市日期，str类型；
* option\_type -- 期权属性，'C'-看涨期权，'P'-看跌期权，str类型；
* trade\_code -- 交易代码，str类型；
* littlest\_changeunit -- 最小价格变动单位，float类型；
* exercise\_price -- 行权价格，float类型；

#### 示例

```python
def initialize(context):
    pass

def handle_data(context, data):
    # 获取'10003975.XSHO'合约的详细信息
    get_contract_info('10003975.XSHO')
```

```python
生成的字典：{'exercise_price': 2.85, 'contract_name': '50ETF购9月2850', 'contract_code': '10003975.ZSHO', 'exchange': '上交所', 'warrant_way': '10', 'trade_code': '510050C2209M02850', 'listing_date': '2022-01-27', 'expiration_date': '2022-09-28', 'contract_multiplier': 10000.0, 'littlest_changeunit': 0.0001, 'option_type': 'C'}
```

### get\_covered\_lock\_amount - 获取期权标的允许备兑锁定数量

```python
get_covered_lock_amount(code)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

获取期权标的允许备兑锁定数量

注意：

从现货账号中获取标的数量

仅支持上交所ETF期权标的

#### 参数

code：期权标的代码，str类型，如50ETF：'510050.SS'；

#### 返回

允许备兑锁定数量: int类型:

#### 示例

```python
def initialize(context):
    pass

def handle_data(context, data):
    # 获取'510050.SS'允许备兑锁定数量
    get_covered_lock_amount('510050.SS')
```

### get\_covered\_unlock\_amount - 获取期权标的允许备兑解锁数量

```python
get_covered_unlock_amount(code)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

获取期权标的允许备兑解锁数量

注意：

从现货账号中获取标的数量

仅支持上交所ETF期权标的

#### 参数

code：期权标的代码，str类型，如50ETF：'510050.SS'；

#### 返回

允许备兑解锁数量: int类型:

#### 示例

```python
def initialize(context):
    pass

def handle_data(context, data):
    # 获取'510050.SS'允许备兑解锁数量
    get_covered_unlock_amount('510050.SS')
```

## 期权交易类函数

### buy\_open - 权利仓开仓

```python
buy_open(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

权利仓开仓

注意：

无

#### 参数

contract：期权合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 权利仓开仓
    buy_open(g.security, 1)

    # 权利仓开仓(限定价格0.0501)
    buy_open(g.security, 1, limit_price=0.0501)
```

### sell\_close - 权利仓平仓

```python
sell_close(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

权利仓平仓

注意：

无

#### 参数

contract：期权合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 权利仓平仓
    sell_close(g.security, 1)
    # 权利仓平仓(限定价格为0.0499)
    sell_close (g.security, 1, limit_price=0.0499)
```

### sell\_open - 义务仓开仓

```python
sell_open(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

义务仓开仓

注意：

无

#### 参数

contract：期权合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 义务仓开仓
    sell_open(g.security, 1)

    # 义务仓开仓(限定价格为0.0501)
    sell_open (g.security, 1, limit_price=0.0501)
```

### buy\_close - 义务仓平仓

```python
buy_close(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

义务仓平仓

注意：

无

#### 参数

contract：期权合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 义务仓平仓
    buy_close(g.security, 1)
    # 义务仓平仓(限定价格为0.0499)
    buy_close (g.security, 1, limit_price=0.0499)
```

### open\_prepared - 备兑开仓

```python
open_prepared(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

备兑开仓

注意：

仅支持上交所ETF期权标的；

仅支持认购类型期权；

#### 参数

contract：期权合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 备兑开仓
    open_prepared(g.security, 1)
    # 备兑开仓(限定价格为0.0501)
    open_prepared(g.security, 1, limit_price=0.0501)
```

### close\_prepared - 备兑平仓

```python
close_prepared(contract, amount, limit_price=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

备兑平仓

注意：

仅支持上交所ETF期权标的；

仅支持认购类型期权；

#### 参数

contract：期权合约代码；

amount：交易数量，正数；

limit\_price：买卖限价；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 备兑平仓
    close_prepared(g.security, 1)
    # 备兑平仓(限定价格为0.0499)
    close_prepared(g.security, 1, limit_price=0.0499)
```

### option\_exercise - 行权

```python
option_exercise(contract, amount)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

合约在行权日支持行权

注意：

按合约行权价行权

#### 参数

contract：期货合约代码；

amount：交易数量，正数；

#### 返回

[Order对象](#Order)中的id或者None。如果创建订单成功，则返回Order对象的id，失败则返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 行权
    option_exercise(g.security, 1)
```

## 期权其他函数

### option\_covered\_lock - 期权标的备兑锁定

```python
option_covered_lock(code, amount)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

期权标的备兑锁定，锁定现货账户标的；

注意：

仅支持上交所ETF期权标的；

#### 参数

code：期权标的代码；

amount：交易数量，正数；

#### 返回

返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 510050.SS备兑锁定
    option_covered_lock('510050.SS', 1000)
```

### option\_covered\_unlock - 期权标的备兑解锁

```python
option_covered_unlock(code, amount)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

期权标的备兑解锁，解锁现货账户标的；

注意：

仅支持上交所ETF期权标的；

#### 参数

code：期权标的代码；

amount：交易数量，正数；

#### 返回

返回None。

#### 示例

```python
def initialize(context):
    g.security = '10004335.XSHO'
    set_universe(g.security)

def handle_data(context, data):
    # 510050.SS备兑解锁
    option_covered_unlock('510050.SS', 1000)
```

# 计算函数

## 技术指标计算函数

### get\_MACD - 异同移动平均线

```python
get_MACD(close, short=12, long=26, m=9)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

获取异同移动平均线MACD指标的计算结果

#### 参数

close：价格的时间序列数据, numpy.ndarray类型；

short: 短周期, int类型；

long: 长周期, int类型；

m: 移动平均线的周期, int类型；

#### 返回

MACD指标dif值的时间序列, numpy.ndarray类型

MACD指标dea值的时间序列, numpy.ndarray类型

MACD指标macd值的时间序列, numpy.ndarray类型

#### 示例

```python
def initialize(context):
    g.security = "600570.XSHG"
    set_universe(g.security)

def handle_data(context, data):
    h = get_history(100, '1d', ['close','high','low'], security_list=g.security)
    close_data = h['close'].values
    macdDIF_data, macdDEA_data, macd_data = get_MACD(close_data, 12, 26, 9)
    dif = macdDIF_data[-1]
    dea = macdDEA_data[-1]
    macd = macd_data[-1]
```

### get\_KDJ - 随机指标

```python
get_KDJ(high, low, close, n=9, m1=3, m2=3)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

获取随机指标KDJ指标的计算结果

#### 参数

high：最高价的时间序列数据, numpy.ndarray类型；

low：最低价的时间序列数据, numpy.ndarray类型；

close：收盘价的时间序列数据, numpy.ndarray类型；

n: 周期, int类型；

m1: 参数m1, int类型；

m2: 参数m2, int类型；

#### 返回

KDJ指标k值的时间序列, numpy.ndarray类型

KDJ指标d值的时间序列, numpy.ndarray类型

KDJ指标j值的时间序列, numpy.ndarray类型

#### 示例

```python
def initialize(context):
    g.security = "600570.XSHG"
    set_universe(g.security)

def handle_data(context, data):
    h = get_history(100, '1d', ['close','high','low'], security_list=g.security)
    high_data = h['high'].values
    low_data = h['low'].values
    close_data = h['close'].values
    k_data, d_data, j_data = get_KDJ(high_data, low_data, close_data, 9, 3, 3)
    k = k_data[-1]
    d = d_data[-1]
    j = j_data[-1]
```

### get\_RSI - 相对强弱指标

```python
get_RSI(close, n=6)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

获取相对强弱指标RSI指标的计算结果

#### 参数

close：价格的时间序列数据, numpy.ndarray类型；

n: 周期, int类型；

#### 返回

RSI指标rsi值的时间序列, numpy.ndarray类型

#### 示例

```python
def initialize(context):
    g.security = "600570.XSHG"
    set_universe(g.security)

def handle_data(context, data):
    h = get_history(100, '1d', ['close','high','low'], security_list=g.security)
    close_data = h['close'].values
    rsi_data = get_RSI(close_data, 6)
    rsi = rsi_data[-1]
```

### get\_CCI - 顺势指标

```python
get_CCI(close, n=14)
```

#### 使用场景

该函数仅在回测、交易模块可用

#### 接口说明

获取顺势指标CCI指标的计算结果

#### 参数

high：最高价的时间序列数据, numpy.ndarray类型；

low：最低价的时间序列数据, numpy.ndarray类型；

close：收盘价的时间序列数据, numpy.ndarray类型；

n: 周期, int类型；

#### 返回

CCI指标cci值的时间序列, numpy.ndarray类型

#### 示例

```python
def initialize(context):
    g.security = "600570.XSHG"
    set_universe(g.security)

def handle_data(context, data):
    h = get_history(100, '1d', ['close','high','low'], security_list=g.security)
    high_data = h['high'].values
    low_data = h['low'].values
    close_data = h['close'].values
    cci_data = get_CCI(high_data, low_data, close_data, 14)
    cci = cci_data[-1]
```

## 其他函数

### log-日志记录

```python
log(content)
```

#### 使用场景

该函数仅在回测、交易模块可用。

#### 接口说明

该接口用于打印日志。

支持如下场景的日志记录：

```python
log.debug("debug")
log.info("info")
log.warning("warning")
log.error("error")
log.critical("critical")
```

与python的logging模块用法一致

注意事项：

无

#### 参数

参数可以是字符串、对象等。

#### 返回

None

#### 示例

```python
# 打印出一个格式化后的字符串
g.security='600570.SS'
log.info("Selling %s, amount=%s" % (g.security, 10000)) 
```

### is\_trade-业务代码场景判断

```python
is_trade()
```

#### 使用场景

该函数仅在回测、交易模块可用。

#### 接口说明

该接口用于提供业务代码执行场景判断依据，明确标识当前业务代码运行场景为回测还是交易。因部分函数仅限回测或交易场景使用，该函数可以协助区分对应场景，以便限制函数可以在一套策略代码同时兼容回测与交易场景。

注意事项：

无

#### 参数

无

#### 返回

布尔类型，当前代码在交易中运行返回True，当前代码在回测中运行返回False(bool)。

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    _id = order(g.security, 100)
    
    if is_trade():
        log.info("当前运行场景：交易")
    else:
        log.info("当前运行场景：回测")
```

### check\_limit - 代码涨跌停状态判断

```python
check_limit(security, query_date=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用。

#### 接口说明

该接口用于标识股票的涨跌停情况。

注意事项：

1、入参的security非str非list类型，返回空字典

2、入参的query\_date仅支持YYYYmmdd格式的传参，当query\_date入参为None或传入当日日期时，返回的结果是以实时最新价判断涨跌停状态;当query\_date入参为历史交易日期，则均以交易日收盘价判断涨跌停状态。

#### 参数

security：单只股票代码或者多只股票代码组成的列表，必填字段(list\[str]/str)；

query\_date：查询日期，查询指定日期股票代码的涨跌停状态，回测不传默认是回测当日时间，交易和研究不传默认是执行当日时间，非必填字段(str)；

#### 返回

正常返回一个dict类型数据，包含每只股票代码的涨停状态。多只股票代码查询时其中部分股票代码查询异常则该代码返回既不涨停也不跌停状态0。(dict\[str:int])

涨跌停状态说明：

* 2：触板涨停（已经是涨停价格，但还有卖盘）(仅支持交易研究查询当日)；
* 1：涨停；
* 0：既不涨停也不跌停；
* -1：跌停；
* -2：触板跌停（已经是跌停价格，但还有买盘）(仅支持交易研究查询当日)；

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    # 代码涨跌停状态
    stock_flag = check_limit(g.security)[g.security]
    log.info(stock_flag)
```

### send\_email - 发送邮箱信息

```python
send_email(send_email_info, get_email_info, smtp_code, info='', path='', subject='')
```

#### 使用场景

该函数仅在交易模块可用。

#### 接口说明

该接口用于通过QQ邮箱发送邮件内容。

注意事项：

1、该接口需要服务端连通外网，是否开通由所在券商决定

2、是否允许发送附件（即path参数），由所在券商的配置管理决定

3、邮件中接受到的附件为文件名而非附件路径

#### 参数

send\_email\_info：发送方的邮箱地址，必填字段，如:50xxx00\@qq.com(str)；

get\_email\_info：接收方的邮箱地址，必填字段，如:\[50xxx00\@qq.com, 1xxx10\@126.com]\(list\[str]/str)；

smtp\_code：邮箱的smtp授权码，注意，不是邮箱密码，必填字段(str)；

info：发送内容，选填字段，默认空字符串(str)；

path：附件路径，选填字段，如:'/home/fly/notebook/stock.csv'，默认空字符串(str)；

subject：邮件主题，默认空字符串(str)；

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #发送文字信息
    send_email('53xxxxxx7@qq.com', ['53xxxxx7@qq.com', 'Kxxxxn@126.com'], 'phfxxxxxxxxxxcd', info='今天的股票池信息')
```

### send\_qywx - 发送企业微信信息

```python
send_qywx(corp_id, secret, agent_id, info='', path='', toparty='', touser= '', totag= '')
```

#### 使用场景

该函数仅在交易模块可用。

#### 接口说明

该接口用于通过企业微信发送内容，使用方法请查看[ 企业微信功能使用手册](/data/send_qywx)。

注意事项：

1、该接口需要服务端连通外网，是否开通由所在券商决定

2、是否允许发送文件（即path参数），由所在券商的配置管理决定

3、企业微信不能同时发送文字和文件，当同时入参info和path的时候，默认发送文件

4、企业微信接受到的文件为文件名而非文件路径

#### 参数

corp\_id：企业ID，必填字段(str)；

secret：企业微信应用的密码，必填字段(str)；

agent\_id：企业微信应用的ID，必填字段(str)；

info：发送内容，选填字段，默认空字符串(str)；

path：发送文件，选填字段，如:'/home/fly/notebook/stock.csv'，默认空字符串(str)；

toparty：发送对象为部门，选填字段，默认空字符串(str)，多个对象之间用 '|' 符号分割；

touser：发送内容为个人，选填字段，默认空字符串(str)，多个对象之间用 '|' 符号分割；

totag：发送内容为分组，选填字段，默认空字符串(str)，多个对象之间用 '|' 符号分割；

注意：toparty、touser、totag如果都不传入，接口默认发送至应用中设定的第一个toparty

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    #发送文字信息
    send_qywx('wwxxxxxxxxxxxxf9', 'hixxxxxxxxxxxxxxxxxxxBX8', '10xxxx3', info='已触发委托买入', toparty='1|2')
```

### permission\_test-权限校验

```python
permission_test(account=None, end_date=None)
```

#### 使用场景

该函数仅在交易模块可用

#### 接口说明

该接口用于账号和有效期的权限校验，用户可以在接口中入参指定账号和指定有效期截止日，策略运行时会校验运行策略的账户与指定账户是否相符，以及运行当日日期是否超过指定的有效期截止日，任一条件校验失败，接口都会返回False，两者同时校验成功则返回True。校验失败会在策略日志中提示原因。

注意事项：

如果需要使用授权模式下载功能，不要在接口中入参，策略编码时候直接调用permission\_test()，授权工具会把需要授权的账号和有效期信息放到策略文件中。

该函数仅在initialize、before\_trading\_start、after\_trading\_end模块中支持调用

#### 参数

account：授权账号，选填字段，如果不填就代表不需要验证账号(str)；

end\_date：授权有效期截止日，选题字段，如果不填就代表不需要验证有效期(str)，日期格式必须为'YYYYmmdd'的8位日期格式，如'20200101'；

#### 返回

布尔类型，校验成功返回True，校验失败返回False(bool)。

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
def handle_data(context, data):
    pass
def after_trading_end(context, data):
    # 需要用授权模式下载功能的情况下不用入参
    flag = permission_test()
    if not flag:
        raise RuntimeError('授权不通过，终止程序，抛出异常')
    # 不需要用授权模式下载功能的情况下通过入参来进行授权校验
    flag = permission_test(account='10110922',end_date='20220101')
    if not flag:
        raise RuntimeError('授权不通过，终止程序，抛出异常')
```

### create\_dir-创建文件目录路径

```python
create_dir(user_path=None)
```

#### 使用场景

该函数在研究、回测、交易模块可用

#### 接口说明

由于ptrade引擎禁用了os模块，因此用户无法在策略中通过编写代码实现子目录创建。用户可以通过此接口来创建文件的子目录路径。

注意事项：

文件根目录路径为'/home/fly/notebook'。

#### 参数

user\_path：子目录路径，选填字段，(str)。

比如user\_path='download'，会在研究中生成/home/fly/notebook/download的目录；

比如user\_path='download/2022'，会在研究中生成/home/fly/notebook/download/2022的目录；

#### 返回

None

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)
    create_dir(user_path=g.security)
def handle_data(context, data):
    pass
```

## 对象

### g-全局对象

#### 使用场景

该对象仅支持回测、交易模块。

#### 对象说明

全局对象g，用于存储用户的各类可被不同函数（包括自定义函数）调用的全局数据,如：

```python
g.security = None #股票池
```

注意事项：

无

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    g.count = 1
    g.flag = 0
    set_universe(g.security)

def handle_data(context, data):
    log.info(g.security)
    log.info(g.count)
    log.info(g.flag)
```

### Context-上下文对象

#### 使用场景

该对象仅支持回测、交易模块。

#### 对象说明

类型为业务上下文对象

注意事项：

无

#### 内容：

```python
capital_base -- 起始资金
previous_date –- 前一个交易日
sim_params -- SimulationParameters对象
    capital_base -- 起始资金
    data_frequency -- 数据频率
portfolio -- 账户信息，可参考Portfolio对象
initialized -- 是否执行初始化
slippage -- 滑点，VolumeShareSlippage对象
    volume_limit -- 成交限量
    price_impact -- 价格影响力
commission -- 佣金费用，Commission对象
    tax—印花税费率
    cost—佣金费率
    min_trade_cost—最小佣金
blotter -- Blotter对象（记录）
    current_dt -- 当前单位时间的开始时间，datetime.datetime对象（北京时间）
recorded_vars -- 收益曲线值
```

#### 示例

```python
def initialize(context):
    g.security = ['600570.SS', '000001.SZ']
    set_universe(g.security)

def handle_data(context, data):
    #获得当前回测相关时间
    pre_date = context.previous_date
    log.info(pre_date)
    year = context.blotter.current_dt.year
    log.info(year)
    month = context.blotter.current_dt.month
    log.info(month)
    day = context.blotter.current_dt.day
    log.info(day)
    hour = context.blotter.current_dt.hour
    log.info(hour)
    minute = context.blotter.current_dt.minute
    log.info(minute)
    second = context.blotter.current_dt.second
    log.info(second)
    #得到"年-月-日"格式
    date = context.blotter.current_dt.strftime("%Y-%m-%d")
    log.info(date)
    #得到周几
    weekday = context.blotter.current_dt.isoweekday()
    log.info(weekday)
```

### SecurityUnitData

#### 使用场景

该对象仅支持回测、交易模块。

#### 对象说明

一个单位时间内的股票的数据，是一个字典，根据sid获取BarData对象数据

注意事项：

无

#### 基本属性

以下属性也能通过get\_history/get\_price获取到

```python
dt 时间
open 时间段开始时价格
close 时间段结束时价格
price结束时价格
low 最低价
high 最高价
volume 成交的股票数量
money 成交的金额
```

### Portfolio

#### 使用场景

该对象仅支持回测、交易模块。

#### 对象说明

对象数据包含账户当前的资金，标的信息，即所有标的操作仓位的信息汇总

注意事项：

无

#### 内容

```python
股票账户返回
     cash 当前可用资金（不包含冻结资金）
     positions 当前持有的标的(包含不可卖出的标的)，dict类型，key是标的代码，value是Position对象
     portfolio_value 当前持有的标的和现金的总价值
     positions_value 持仓价值
     capital_used 已使用的现金
     returns 当前的收益比例, 相对于初始资金
     pnl 当前账户总资产-初始账户总资产
     start_date 开始时间
期货账户返回：
     cash 当前可用资金（不包含冻结资金）
     positions 当前持有的标的(包含不可卖出的标的)，dict类型，key是标的代码，value是Position对象
     portfolio_value 当前持有的标的和现金的总价值
     positions_value 持仓价值
     capital_used 已使用的现金
     returns 当前的收益比例, 相对于初始资金
     pnl 当前账户总资产-初始账户总资产
     start_date 开始时间
期权账户返回：
     cash 当前可用资金（不包含冻结资金）
     positions 当前持有的标的(包含不可卖出的标的)，dict类型，key是标的代码，value是Position对象
     portfolio_value 当前持有的标的和现金的总价值
     positions_value 持仓价值
     returns 当前的收益比例, 相对于初始资金
     pnl 当前账户总资产-初始账户总资产
     margin 保证金
     risk_degree 风险度
     start_date 开始时间
```

#### 示例

```python
def initialize(context):
    g.security = "600570.SS"
    set_universe([g.security])

def handle_data(context, data):
    log.info(context.portfolio.portfolio_value)
```

### Position

#### 使用场景

该对象仅支持回测、交易模块。

#### 对象说明

持有的某个标的的信息。

注意事项：

期货业务持仓把单个合约的持仓分为了多头仓(long)、空头仓(short)。

期权业务持仓把单个合约的持仓分为了权利仓(long)、义务仓(short)、备兑仓(covered)，备兑仓虽然也是空开的业务类型，但为了区分备兑业务类型，所以没有和义务仓合并。

#### 内容

```python
股票账户返回
     sid 标的代码
     enable_amount 可用数量
     amount 总持仓数量
     last_sale_price 最新价格
     cost_basis 持仓成本价格
     today_amount 今日开仓数量(且仅回测有效)
     business_type 持仓类型
期货账户返回：
     sid 标的代码
     short_enable_amount 空头仓可用数量
     long_enable_amount 多头仓可用数量
     today_short_amount 空头仓今仓数量
     today_long_amount 多头仓今仓数量
     long_cost_basis 多头仓持仓成本
     short_cost_basis 空头仓持仓成本
     long_amount 多头仓总持仓量
     short_amount 空头仓总持仓量
     long_pnl 多头仓浮动盈亏
     short_pnl 空头仓浮动盈亏
     amount 总持仓数量
     enable_amount 可用数量
     last_sale_price 最新价格
     business_type 持仓类型
     delivery_date 交割日，期货使用
     margin_rate 保证金比例
     contract_multiplier 合约乘数
期权账户返回：
     sid 标的代码
     short_enable_amount 义务仓可用数量
     long_enable_amount 权利仓可用数量
     covered_enable_amount 备兑仓可用数量
     short_cost_basis 义务仓持仓成本
     long_cost_basis 权利仓持仓成本
     covered_cost_basis 备兑仓持仓成本
     short_amount 义务仓总持仓量
     long_amount 权利仓总持仓量
     covered_amount 备兑仓总持仓量
     short_pnl 义务仓浮动盈亏
     long_pnl 权利仓浮动盈亏
     covered_pnl 备兑仓浮动盈亏
     last_sale_price 最新价格
     margin 保证金
     exercise_date 行权日，期权使用
     business_type 持仓类型
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    order(g.security,1000)
    position = get_position(g.security)
    log.info(position)
```

### Order

#### 使用场景

该对象仅支持回测、交易模块。

#### 对象说明

买卖订单信息

注意事项：

无

#### 内容

```python
id -- 订单号
dt -- 订单产生时间，datetime.datetime类型
limit -- 指定价格
symbol -- 标的代码(备注：标的代码尾缀为四位，上证为XSHG，深圳为XSHE，如需对应到代码请做代码尾缀兼容)
amount -- 下单数量，买入是正数，卖出是负数
created -- 订单生成时间，datetime.datetime类型
filled -- 成交数量，买入时为正数，卖出时为负数
entrust_no -- 委托编号
priceGear -- 盘口档位
status -- 订单状态(str)，该字段取值范围：
    '0' -- "未报"
    '1' -- "待报"
    '2' -- "已报"
    '3' -- "已报待撤"
    '4' -- "部成待撤"
    '5' -- "部撤"
    '6' -- "已撤"
    '7' -- "部成"
    '8' -- "已成"
    '9' -- "废单"
    '+' -- "已受理"
    '-' -- "已确认"
    'V' -- "已确认"
```

#### 示例

```python
def initialize(context):
    g.security = '600570.SS'
    set_universe(g.security)

def handle_data(context, data):
    order(g.security, 100)
    order_obj = get_orders()
    log.info(order_obj)
```

# 策略示例

## 集合竞价追涨停策略

```python
def initialize(context):
    # 初始化此策略
    # 设置我们要操作的股票池, 这里我们只操作一支股票
    g.security = '600570.SS'
    set_universe(g.security)
    #每天9:23分运行集合竞价处理函数
    run_daily(context, aggregate_auction_func, time='9:23')  

def aggregate_auction_func(context):
    stock = g.security
    #最新价
    snapshot = get_snapshot(stock)
    price = snapshot[stock]['last_px']
    #涨停价
    up_limit = snapshot[stock]['up_px']
    #如果最新价不小于涨停价，买入
    if float(price) >= float(up_limit):
        order(g.security, 100, limit_price=up_limit)
    
def handle_data(context, data):
    pass
```

## tick级别均线策略

```python
def initialize(context):
    # 初始化此策略
    # 设置我们要操作的股票池, 这里我们只操作一支股票
    g.security = '600570.SS'
    set_universe(g.security)
    #每3秒运行一次主函数
    run_interval(context, func, seconds=3)
      
#盘前准备历史数据
def before_trading_start(context, data):
    history = get_history(10, '1d', 'close', g.security, fq='pre', include=False)
    g.close_array = history['close'].values
    
#当五日均线高于十日均线时买入，当五日均线低于十日均线时卖出
def func(context):
    
    stock = g.security
    
    #获取最新价
    snapshot = get_snapshot(stock)
    price = snapshot[stock]['last_px']
    
    # 得到五日均线价格
    days = 5
    ma5 = get_MA_day(stock, days, g.close_array[-4:], price)   
    # 得到十日均线价格
    days = 10
    ma10 = get_MA_day(stock, days, g.close_array[-9:], price)

    # 得到当前资金余额
    cash = context.portfolio.cash
    
    # 如果当前有余额，并且五日均线大于十日均线
    if ma5 > ma10:
        # 用所有 cash 买入股票
        order_value(stock, cash)
        # 记录这次买入
        log.info("Buying %s" % (stock))
        
    # 如果五日均线小于十日均线，并且目前有头寸
    elif ma5 < ma10 and get_position(stock).amount > 0:
        # 全部卖出
        order_target(stock, 0)
        # 记录这次卖出
        log.info("Selling %s" % (stock))    

#计算实时均线函数
def get_MA_day(stock,days,close_array,current_price):
    close_sum = close_array[-(days-1):].sum()
    MA = (current_price + close_sum)/days
    return MA

def handle_data(context, data):
    pass
```

## 双均线策略

```python
def initialize(context):
    # 初始化此策略
    # 设置我们要操作的股票池, 这里我们只操作一支股票
    g.security = '600570.SS'
    set_universe(g.security)
    
#当五日均线高于十日均线时买入，当五日均线低于十日均线时卖出
def handle_data(context, data):
    security = g.security

    #得到十日历史价格
    df = get_history(10, '1d', 'close', security, fq=None, include=False)
    
    # 得到五日均线价格
    ma5 = round(df['close'][-5:].mean(), 3)
    
    # 得到十日均线价格
    ma10 = round(df['close'][-10:].mean(), 3)

    # 取得昨天收盘价
    price = data[security]['close']

    # 得到当前资金余额
    cash = context.portfolio.cash
    
    # 如果当前有余额，并且五日均线大于十日均线
    if ma5 > ma10:
        # 用所有 cash 买入股票
        order_value(security, cash)
        # 记录这次买入
        log.info("Buying %s" % (security))
        
    # 如果五日均线小于十日均线，并且目前有头寸
    elif ma5 < ma10 and get_position(security).amount > 0:
        # 全部卖出
        order_target(security, 0)
        # 记录这次卖出
        log.info("Selling %s" % (security))
```

## 融资融券双均线策略

```python
def initialize(context):
    # 初始化策略
    # 设置我们要操作的股票池, 这里我们只操作一支股票
    g.security = "600570.SS"
    set_universe(g.security)

def before_trading_start(context, data):
    # 买入标识
    g.order_buy_flag = False
    # 卖出标识
    g.order_sell_flag = False

#当五日均线高于十日均线时买入，当五日均线低于十日均线时卖出
def handle_data(context, data):
    # 得到十日历史价格
    df = get_history(10, "1d", "close", g.security, fq=None, include=False)
    # 得到五日均线价格
    ma5 = round(df["close"][-5:].mean(), 3)
    # 得到十日均线价格
    ma10 = round(df["close"][-10:].mean(), 3)
    # 取得昨天收盘价
    price = data[g.security]["close"]
    # 如果五日均线大于十日均线
    if ma5 > ma10:
        if not g.order_buy_flag:
            # 获取最大可融资数量
            amount = get_margincash_open_amount(g.security).get(g.security)
            # 进行融资买入操作
            margincash_open(g.security, amount)
            # 记录这次操作
            log.info("Buying %s Amount %s" % (g.security, amount))
            # 当日已融资买入
            g.order_buy_flag = True

    # 如果五日均线小于十日均线，并且目前有头寸
    elif ma5 < ma10 and get_position(g.security).amount > 0:
        if not g.order_sell_flag:
            # 获取标的卖券还款最大可卖数量
            amount = get_margincash_close_amount(g.security).get(g.security)
            # 进行卖券还款操作
            margincash_close(g.security, -amount)
            # 记录这次操作
            log.info("Selling %s Amount %s" % (g.security, amount))
            # 当日已卖券还款
            g.order_sell_flag = True
```

## macd策略

指数平滑均线函数，以price计算，可以选择收盘、开盘价等价格，N为时间周期，m用于计算平滑系数a=m/(N+1)，EXPMA1为前一日值

```python
def f_expma(N,m,EXPMA1,price):
    a = m/(N+1)
    EXPMA2 = a * price + (1 - a)*EXPMA1
    return EXPMA2 #2为后一天值

#定义macd函数，输入平滑系数参数、前一日值，输出当日值
def macd(N1,N2,N3,m,EXPMA12_1,EXPMA26_1,DEA1,price):
    EXPMA12_2 = f_expma(N1,m,EXPMA12_1,price)
    EXPMA26_2 = f_expma(N2,m,EXPMA26_1,price)
    DIF2 = EXPMA12_2 - EXPMA26_2
    a = m/(N3+1)
    DEA2 = a * DIF2 + (1 - a)*DEA1
    BAR2=2*(DIF2-DEA2)
    return EXPMA12_2,EXPMA26_2,DIF2,DEA2,BAR2

def initialize(context):
    global init_price
    init_price = None
    # 获取沪深300股票
    g.security = get_index_stocks('000300.SS')
    #g.security = ['600570.SS']
    # 设置我们要操作的股票池, 这里我们只操作一支股票
    set_universe(g.security)

def handle_data(context, data):
    # 获取历史数据，这里只获取了2天的数据，如果希望最终MACD指标结果更准确最好是获取
    # 从股票上市至今的所有历史数据，即增加获取的天数
    close_price = get_history(2, '1d', field='close', security_list=g.security)
    #如果是停牌不进行计算
    for security in g.security:
        if data[security].is_open >0:
            global init_price,EXPMA12_1,EXPMA26_1,EXPMA12_2,EXPMA26_2,DIF1,DIF2,DEA1,DEA2
            if init_price is None:
                init_price = close_price[security].mean()#nan和N-1个数，mean为N-1个数的均值
                EXPMA12_1 = init_price
                EXPMA26_1 = init_price
                DIF1 = init_price
                DEA1 = init_price
            # m用于计算平滑系数a=m/(N+1)
            m = 2.0
            #设定指数平滑基期数
            N1 = 12
            N2 = 26
            N3 = 9
            EXPMA12_2,EXPMA26_2,DIF2,DEA2,BAR2 = macd(N1,N2,N3,m,EXPMA12_1,EXPMA26_1,DEA1,close_price[security][-1])
            # 取得当前价格
            current_price = data[security].price
            # 取得当前的现金
            cash = context.portfolio.cash
            # DIF、DEA均为正，DIF向上突破DEA，买入信号参考
            if DIF2 > 0 and DEA2 > 0 and DIF1 < DEA1 and DIF2 > DEA2:
                # 计算可以买多少只股票
                number_of_shares = int(cash/current_price)
                # 购买量大于0时，下单
                if number_of_shares > 0:
                    # 以市单价买入股票，日回测时即是开盘价
                    order(security, +number_of_shares)
                    # 记录这次买入
                    log.info("Buying %s" % (security))
            # DIF、DEA均为负，DIF向下突破DEA，卖出信号参考
            elif DIF2 < 0 and DEA2 < 0 and DIF1 > DEA1 and DIF2 < DEA2 and get_position(security).amount > 0:
                # 卖出所有股票,使这只股票的最终持有量为0
                order_target(security, 0)
                # 记录这次卖出
                log.info("Selling %s" % (security))
            # 将今日的值赋给全局变量作为下一次前一日的值
            DEA1 = DEA2
            DIF1 = DIF2
            EXPMA12_1 = EXPMA12_2
            EXPMA26_1 = EXPMA26_2
```

# 常见问题

使用本平台受阻，可参考[常见问题说明](/data/QA_data)

# 支持的三方库

| 序号  | 三方库名称                  | 版本号         |
| --- | ---------------------- | ----------- |
| 1   | APScheduler            | 3.3.1       |
| 2   | arch                   | 3.2         |
| 3   | bcolz                  | 1.2.1       |
| 4   | beautifulsoup4         | 4.6.0       |
| 5   | bleach                 | 1.5.0       |
| 6   | boto                   | 2.43.0      |
| 7   | Bottleneck             | 1.0.0       |
| 8   | bz2file                | 0.98        |
| 9   | cachetools             | 3.1.0       |
| 10  | click                  | 4.0         |
| 11  | contextlib2            | 0.4.0       |
| 12  | crypto                 | 1.4.1       |
| 13  | cvxopt                 | 1.1.8       |
| 14  | cx-Oracle              | 8.0.1       |
| 15  | cycler                 | 0.10.0      |
| 16  | cyordereddict          | 0.2.2       |
| 17  | Cython                 | 0.22.1      |
| 18  | decorator              | 4.0.10      |
| 19  | entrypoints            | 0.2.2       |
| 20  | fastcache              | 1.0.2       |
| 21  | gensim                 | 0.13.3      |
| 22  | h5py                   | 2.6.0       |
| 23  | hmmlearn               | 0.2.0       |
| 24  | html5lib               | 0.9999999   |
| 25  | ipykernel              | 4.5.0       |
| 26  | ipython                | 5.1.0       |
| 27  | ipython-genutils       | 0.1.0       |
| 28  | ipywidgets             | 5.2.2       |
| 29  | jieba                  | 0.38        |
| 30  | Jinja2                 | 2.8         |
| 31  | jsonpickle             | 1.0         |
| 32  | jsonschema             | 2.5.1       |
| 33  | jupyter                | 1.0.0       |
| 34  | jupyter-client         | 4.4.0       |
| 35  | jupyter-console        | 5.0.0       |
| 36  | jupyter-core           | 4.2.0       |
| 37  | jupyter-kernel-gateway | 1.1.1       |
| 38  | Keras                  | 2.2.4       |
| 39  | Keras-Applications     | 1.0.8       |
| 40  | Keras-Preprocessing    | 1.1.0       |
| 41  | line-profiler          | 2.1.2       |
| 42  | Logbook                | 1.4.3       |
| 43  | lxml                   | 4.5.0       |
| 44  | Markdown               | 2.2.0       |
| 45  | MarkupSafe             | 0.23        |
| 46  | matplotlib             | 1.5.3       |
| 47  | mistune                | 0.7.3       |
| 48  | Naked                  | 0.1.31      |
| 49  | nbconvert              | 4.2.0       |
| 50  | nbformat               | 4.1.0       |
| 51  | networkx               | 1.9.1       |
| 52  | nose                   | 1.3.6       |
| 53  | notebook               | 4.2.3       |
| 54  | numexpr                | 2.6.1       |
| 55  | numpy                  | 1.11.2      |
| 56  | pandas                 | 0.23.4      |
| 57  | patsy                  | 0.4.0       |
| 58  | pexpect                | 4.2.1       |
| 59  | pickleshare            | 0.7.4       |
| 60  | pip                    | 9.0.1       |
| 61  | pkgconfig              | 1.0.0       |
| 62  | prompt-toolkit         | 1.0.8       |
| 63  | protobuf               | 3.3.0       |
| 64  | ptvsd                  | 2.2.0       |
| 65  | ptyprocess             | 0.5.1       |
| 66  | PyBrain                | 0.3         |
| 67  | pycrypto               | 2.6.1       |
| 68  | Pygments               | 2.1.3       |
| 69  | PyMySQL                | 0.9.3       |
| 70  | pyparsing              | 2.1.10      |
| 71  | python-dateutil        | 2.7.5       |
| 72  | pytz                   | 2015.4      |
| 73  | PyWavelets             | 0.4.0       |
| 74  | PyYAML                 | 3.13        |
| 75  | pyzmq                  | 16.1.0.dev0 |
| 76  | qtconsole              | 4.2.1       |
| 77  | requests               | 2.7.0       |
| 78  | retrying               | 1.3.3       |
| 79  | scikit-learn           | 0.18        |
| 80  | scipy                  | 0.18.0      |
| 81  | seaborn                | 0.7.1       |
| 82  | setuptools             | 28.7.1      |
| 83  | setuptools-scm         | 3.1.0       |
| 84  | shellescape            | 3.4.1       |
| 85  | simplegeneric          | 0.8.1       |
| 86  | simplejson             | 3.17.0      |
| 87  | six                    | 1.10.0      |
| 88  | sklearn                | 0.0         |
| 89  | smart-open             | 1.3.5       |
| 90  | SQLAlchemy             | 1.0.8       |
| 91  | statsmodels            | 0.10.2      |
| 92  | TA-Lib                 | 0.4.10      |
| 93  | tables                 | 3.3.0       |
| 94  | tabulate               | 0.7.5       |
| 95  | tensorflow             | 1.3.0rc1    |
| 96  | tensorflow-tensorboard | 0.1.2       |
| 97  | terminado              | 0.6         |
| 98  | Theano                 | 0.8.2       |
| 99  | toolz                  | 0.7.4       |
| 100 | tornado                | 4.4.2       |
| 101 | traitlets              | 4.3.1       |
| 102 | tushare                | 1.2.48      |
| 103 | tzlocal                | 1.3         |
| 104 | wcwidth                | 0.1.7       |
| 105 | Werkzeug               | 0.12.2      |
| 106 | wheel                  | 0.29.0      |
| 107 | widgetsnbextension     | 1.2.6       |
| 108 | xcsc-tushare           | 1.0.0       |
| 109 | xgboost                | 0.6a2       |
| 110 | xlrd                   | 1.1.0       |
| 111 | xlwt                   | 1.3.0       |
| 112 | zipline                | 0.8.3       |
| 113 | walrus                 | 0.9.3       |

# 接口版本变动

当前版本：PBOXQT1.0V202202.01.041

| 变动版本                    | 变动内容                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PBOXQT1.0V202101.03.000 | 1. [on\_order\_response()](#on_order_response)主推信息中新增entrust\_type、entrust\_prop字段；
2. 修复信用交易接口兼容问题；
3. [get\_price()](#get_price)、[get\_history()](#get_history)支持周频(1w)行情获取；
4. 由于行情源不再更新维护，[get\_fundamentals()](#get_fundamentals)接口去除share\_change表；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| PBOXQT1.0V202101.04.000 | 1) 修复[get\_all\_orders()](#get_all_orders)获取特定委托状态报错问题，status字段返回数据类型从int改为str；
2) [on\_order\_response()](#on_order_response)、[on\_trade\_response()](#on_trade_response)支持获取非本策略交易的主推信息(需券商配置默认不推送)，且on\_order\_response推送非本策略交易的主推信息时不包含order\_id字段；
3) 相关功能优化；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| PBOXQT1.0V202101.05.000 | 1. 信用账户支持[ipo\_stocks\_order()](#ipo_stocks_order)接口调用；
2. 由于行情源返回信息不包含，[get\_fundamentals()](#get_fundamentals)获取growth\_ability、profit\_ability、eps、operating\_ability、debt\_paying\_ability表不再返回company\_type字段；
3. 由于上交所债券业务规则变更，调用[debt\_to\_stock\_order()](#debt_to_stock_order)接口对上海市场可转债进行转股操作时需传入可转债代码，不再传入转股代码；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| PBOXQT1.0V202101.06.000 | 1) 新增[get\_user\_name()](#get_user_name)API接口，用于获取登录终端的资金账号；
2) 研究中[get\_price()](#get_price)新增支持获取周线数据；
3) [get\_snapshot()](#get_snapshot)新增支持获取XBHS行业版块市场数据；
4) [send\_qywx()](#send_qywx)新增toparty(发送对象为部门)、touser(发送内容为个人)、totag(发送内容为分组)入参；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| PBOXQT1.0V202101.07.000 | 1. [get\_snapshot()](#get_snapshot)新增wavg\_px(加权平均价)、px\_change\_rate(涨跌幅)出参；
2. 可转债回测业务新增支持T+0；
3. 新增支持融资融券回测业务，[融资融券专用函数](#融资融券专用函数)中暂只支持[margin\_trade()](#margin_trade)接口；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| PBOXQT1.0V202101.08.000 | 1) [initialize](#initialize)对部分API接口调用进行限制，仅[initialize](#initialize)可调用接口说明中的API可在initialize函数内使用；
2) [before\_trading\_start](#before_trading_start)和[after\_trading\_end](#after_trading_end)对两融委托API接口调用进行限制；
3) 修复仅单笔成交订单时调用get\_trades()返回格式有误问题；
4) 修复交易场景中获取当日K线14:58、14:59分价格为0问题；
5) [send\_email()](#send_email)发送邮件信息新增path(附件路径)、subject(邮件主题)入参；
6) 新增[get\_cb\_list()](#get_cb_list)获取可转债列表；
7) 新增[get\_deliver()](#get_deliver)获取历史交割单信息；
8) 新增[get\_fundjour()](#get_fundjour)获取历史资金流水信息；
9) 新增[get\_research\_path()](#get_research_path)获取研究路径；
10) [get\_market\_detail()](#get_market_detail)新增支持在回测、交易场景中调用；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| PBOXQT1.0V202101.09.000 | 1. [get\_market\_detail()](#get_market_detail)限制仅[before\_trading\_start](#before_trading_start)和[after\_trading\_end](#after_trading_end)中使用；
2. [get\_snapshot()](#get_snapshot)新增返回hsTimeStamp(快照时间戳)字段；对接L2行情买卖一档新增返回委托队列；
3. [ipo\_stocks\_order()](#ipo_stocks_order)新增black\_stocks(新股/债黑名单)入参；
4. [on\_order\_response()](#on_order_response)新增返回error\_info(错误信息)字段；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| PBOXQT1.0V202201.00.000 | 1) [get\_individual\_transaction()](#get_individual_transaction)新增返回buy\_no(叫买方编号)、sell\_no(叫卖方编号)、trans\_flag(成交标记)、trans\_identify\_am(盘后逐笔成交序号标识)、channel\_num(成交通道信息)字段；
2) [get\_margin\_contract()](#get_margin_contract)新增返回compact\_interest(合约利息金额)、real\_compact\_interest(日间实时利息金额)、real\_compact\_balance(日间实时合约金额)、real\_compact\_amount(日间实时合约数量)字段；
3) [get\_price()](#get_price)、[get\_history()](#get_history)新增支持：1月(mo)、1季度(1q)、1年(1y)频率行情获取；
4) [set\_commission()](#set_commission)中type字段新增支持传入"LOF"类型；
5) [get\_individual\_entrust()](#get_individual_entrust)和[get\_individual\_transaction()](#get_individual_transaction)返回内容中hq\_px字段值缩小1000倍，返回为真实价格；
6) 新增支持期货日盘回测功能、期货日盘交易功能(对接UFT柜台)，期货API接口详见量化帮助文档[期货专用函数](#期货专用函数)模块；
7) 新增[get\_tick\_direction()](#get_tick_direction)获取分时成交行情；
8) 新增[get\_sort\_msg()](#get_sort_msg)获取版块、行业的涨幅排名；
9) 新增[permission\_test()](#permission_test)权限校验；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| PBOXQT1.0V202201.01.000 | 1. 修复委托状态类型不一致问题，[get\_orders()](#get_orders)、[get\_all\_orders()](#get_all_orders)以及[Order](#Order)对象中的委托状态字段数据类型从int统一为str；
2. 新增[get\_trade\_name()](#get_trade_name)获取交易名称；
3. [tick\_data](#tick_data)中可调用接口完善；
4. 研究中[get\_stock\_name()](#get_stock_name)、[get\_stock\_info()](#get_stock_info)新增支持获取可转债、ETF、LOF品种；
5. [get\_history()](#get_history)新增fill(填充类型)入参；
6. [get\_price()](#get_price)、[get\_history()](#get_history)新增支持：5分钟(5m)、15分钟(15m)、30分钟(30m)、60分钟(60m)、120分钟(120m)频率行情获取；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| PBOXQT1.0V202202.00.000 | 1) [log](#log)新增支持DEBUG级别日志记录；
2) [get\_price()](#get_price)、[get\_history()](#get_history)新增返回preclose(昨收盘价)、high\_limit(涨停价)、low\_limit(跌停价)、unlimited(是否无涨跌停限制)字段；
3) [get\_snapshot()](#get_snapshot)新增返回total\_bidqty(委买量)、total\_offerqty(委卖量)、total\_bid\_turnover(委买金额)、total\_offer\_turnover(委卖金额)字段；
4) [on\_trade\_response()](#on_trade_response)新增返回order\_id(Order订单编号)字段；
5) 当接到策略外交易产生的主推时(需券商配置默认不推送)，由于没有对应的Order对象，[on\_order\_response()](#on_order_response)、[on\_trade\_response()](#on_trade_response)中order\_id字段赋值为""；
6) [tick\_data](#tick_data)中可调用接口完善；
7) 弃用set\_close\_position\_type()(设置期货平仓方式)、get\_close\_position\_type()(获取期货平仓方式)API接口；
8) 期货[Position对象](#Position)中删除close\_position\_type(平仓方式)字段；
9) [sell\_close()](#sell_close)、[buy\_close()](#buy_close)新增close\_today(平仓方式)入参；
10) 新增[get\_MACD()](#get_MACD)异同移动平均线；
11) 新增[get\_KDJ()](#get_KDJ)随机指标；
12) 新增[get\_RSI()](#get_RSI)相对强弱指标；
13) 新增[get\_CCI()](#get_CCI)顺势指标；
14) 新增[create\_dir()](#create_dir)创建文件目录路径；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| PBOXQT1.0V202202.01.000 | 1. 委托流程调整，交易模式中非交易时间段内产生的委托直接发送柜台进行处理；
2. 优化[tick\_data](#tick_data)触发逻辑：当策略执行时间超过3s时，将会丢弃中间堵塞的tick\_data；在收盘后，将会清空队列中未执行的tick\_data；
3. [tick\_data](#tick_data)中参数data里的快照数据修改为从[get\_snapshot()](#get_snapshot)中获取，详见注意事项；
4. 修复[get\_individual\_entrust()](#get_individual_entrust)和[get\_individual\_transaction()](#get_individual_transaction)中stocks入参代码数量大于50只时返回数据缺失问题；
5. [run\_interval()](#run_interval)和[run\_daily()](#run_daily)中新增支持[get\_sort\_msg()](#get_sort_msg)调用；
6. [get\_snapshot()](#get_snapshot)新增返回business\_amount\_in(内盘成交量)、business\_amount\_out(外盘成交量)字段；
7. 交易场景中[buy\_open()](#option_buy_open)、[sell\_close()](#option_sell_close)、[sell\_open()](#option_sell_open)、[buy\_close()](#option_buy_close)新增支持期权业务；
8. [on\_trade\_response()](#on_trade_response)新增接收撤单的成交主推，详见接口说明注意事项；
9. [Portfolio](#Portfolio)账户对象新增支持期权业务，字段详见帮助说明；
10. [Position](#Position)持仓对象新增支持期权业务，字段详见帮助说明；
11. 新增[get\_contract\_info()](#get_contract_info)获取期权合约信息；
12. 新增[get\_opt\_objects()](#get_opt_objects)获取期权标的列表；
13. 新增[get\_opt\_last\_dates()](#get_opt_last_dates)获取期权标的到期日列表；
14. 新增[get\_opt\_contracts()](#get_opt_contracts)获取期权标的对应合约列表；
15. 新增[get\_covered\_lock\_amount()](#get_covered_lock_amount)获取期权标的允许备兑锁定数量；
16. 新增[get\_covered\_unlock\_amount()](#get_covered_unlock_amount)获取期权标的允许备兑解锁数量；
17. 新增[option\_covered\_lock()](#option_covered_lock)期权标的备兑锁定；
18. 新增[option\_covered\_unlock()](#option_covered_unlock)期权标的备兑解锁；
19. 新增[open\_prepared()](#open_prepared)备兑开仓；
20. 新增[close\_prepared()](#close_prepared)备兑平仓；
21. 新增[option\_exercise()](#option_exercise)行权；
22. 新增[set\_parameters()](#set_parameters)设置策略配置参数，支持的参数详见接口说明； |
| PBOXQT1.0V202202.01.004 | 1) [order\_market()](#order_market)和[margin\_trade()](#margin_trade)做市价委托上证股票时，limit\_price(保护限价)为必传字段。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| PBOXQT1.0V202202.01.016 | 1. 由于Keras库2.3.1版本与TensorFlow库不兼容，Keras降为2.2.4版本。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| PBOXQT1.0V202202.01.021 | 1) [margincash\_open()](#margincash_open)做市价委托上证股票时，limit\_price(保护限价)为必传字段。
2) [get\_history()](#get_history)新增支持is\_dict(返回是否是字典格式数据)入参；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| PBOXQT1.0V202202.01.025 | 1. 新增[get\_cb\_info()](#get_cb_info)获取可转债基础信息；
2. 新增[get\_enslo\_security\_info()](#get_enslo_security_info)融券头寸信息查询；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| PBOXQT1.0V202202.01.026 | 1) 新增[get\_ipo\_stocks()](#get_ipo_stocks)获取当日IPO申购标的；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| PBOXQT1.0V202202.01.029 | 1. [get\_fundamentals()](#get_fundamentals)获取balance\_statement资产负债表新增返回total\_assets(资产总计)、 total\_liability(负债合计)、 total\_liability\_and\_equity(负债和股东权益总计)字段；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| PBOXQT1.0V202202.01.031 | 1) [get\_fundamentals()](#get_fundamentals)废弃date\_type入参，详见参数说明；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| PBOXQT1.0V202202.01.037 | 1. [get\_etf\_info()](#get_etf_info)获取ETF信息将pre\_cash\_componet字段修正为pre\_cash\_component；
2. 新增[get\_individual\_transaction()](#get_individual_transaction)获取逐笔成交行情，弃用get\_individual\_transcation()；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| PBOXQT1.0V202202.01.038 | 1) 新增支持walrus(0.9.3)库；
2) [check\_limit()](#check_limit)新增支持在回测、研究场景中使用；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| PBOXQT1.0V202202.01.041 | 1. [get\_margin\_contract()](#get_margin_contract)entrust\_no委托编号字段返回类型改为str类型；
2. [get\_margin\_contractreal()](#get_margin_contractreal)entrust\_no委托编号字段返回类型改为str类型；                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

[]()[](#)
