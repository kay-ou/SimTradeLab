# -*- coding: utf-8 -*-
"""
PTrade实盘交易模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ....core.event_bus import EventBus
from ..api_validator import APIValidator
from ..lifecycle_controller import LifecycleController
from .base import BaseAPIRouter

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class LiveTradingAPIRouter(BaseAPIRouter):
    """实盘交易模式API路由器"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        lifecycle_controller: Optional[LifecycleController] = None,
        api_validator: Optional[APIValidator] = None,
    ):
        super().__init__(context, event_bus, lifecycle_controller, api_validator)
        self._data_plugin = None  # 将在设置时从适配器获取
        self._supported_apis = {
            # === 已实际实现的API ===
            # 基础信息 (3个) - 通过父类BaseRouter实现
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            # 行情信息 - 通过父类BaseRouter实现
            "get_history",  # [回测/交易]
            "get_price",  # [研究/回测/交易]
            "get_snapshot",  # [仅交易] - 通过父类BaseRouter实现
            "get_stock_info",  # 通过父类BaseRouter实现
            "get_fundamentals",  # 通过父类BaseRouter实现
            # 股票信息 (9个) - 通过父类BaseRouter实现
            "get_stock_name",
            "get_stock_status",
            "get_stock_exrights",
            "get_stock_blocks",
            "get_index_stocks",
            "get_industry_stocks",
            "get_Ashares",
            "get_etf_list",
            "get_ipo_stocks",
            # 技术指标 (4个) - 通过父类BaseRouter实现
            "get_MACD",
            "get_KDJ",
            "get_RSI",
            "get_CCI",
            # 工具函数 - 通过父类BaseRouter实现
            "log",  # 通过父类BaseRouter实现
            "is_trade",  # 通过父类BaseRouter实现
            "check_limit",  # 通过父类BaseRouter实现
            "set_universe",  # 通过父类BaseRouter实现
            "set_benchmark",  # 通过父类BaseRouter实现
            "set_parameters",  # 在路由器中实现
            # 交易相关函数 (在路由器中直接实现)
            "order",
            "order_target",
            "order_value",
            "order_target_value",
            "order_market",
            "cancel_order",
            "cancel_order_ex",
            "get_all_orders",
            "ipo_stocks_order",
            "after_trading_order",
            "after_trading_cancel_order",
            "get_position",
            "get_positions",
            "get_open_orders",
            "get_order",
            "get_orders",
            "get_trades",
            "handle_data",
            # 定时和回调API (在路由器中实现)
            "run_daily",
            "run_interval",
            "tick_data",
            "on_order_response",
            "on_trade_response",
            # === 以下是计划实现但尚未实现的API（注释版） ===
            # # 策略生命周期函数 - 计划实现
            # "initialize",  # 策略初始化 [回测/交易]
            # "before_trading_start",  # 盘前处理 [回测/交易]
            # "after_trading_end",  # 盘后处理 [回测/交易]
            # # 市场信息 - 计划实现
            # "get_market_list",  # 获取市场列表 [研究/回测/交易]
            # "get_market_detail",  # 获取市场详细信息 [研究/回测/交易]
            # "get_cb_list",  # 获取可转债市场代码表 [仅交易]
            # "get_cb_info",  # 获取可转债基础信息 [研究/交易]
            # # 实时行情信息 - 计划实现 [仅交易]
            # "get_individual_entrust",  # 获取逐笔委托行情
            # "get_individual_transaction",  # 获取逐笔成交行情
            # "get_tick_direction",  # 获取分时成交行情
            # "get_sort_msg",  # 获取板块、行业的涨幅排名
            # "get_etf_info",  # 获取ETF信息
            # "get_etf_stock_info",  # 获取ETF成分券信息
            # "get_gear_price",  # 获取指定代码的档位行情价格
            # # 股票信息 - 计划实现 [仅交易]
            # "get_etf_stock_list",  # 获取ETF成分券列表
            # # 期权信息 - 计划实现
            # "get_opt_objects",  # 获取期权标的列表 [研究/回测/交易]
            # "get_opt_last_dates",  # 获取期权标的到期日列表 [研究/回测/交易]
            # "get_opt_contracts",  # 获取期权标的对应合约列表 [研究/回测/交易]
            # "get_contract_info",  # 获取期权合约信息 [研究/回测/交易]
            # "get_covered_lock_amount",  # 获取期权标的可备兑锁定数量 [仅交易]
            # "get_covered_unlock_amount",  # 获取期权标的允许备兑解锁数量 [仅交易]
            # # 其他信息 - 计划实现
            # "get_user_name",  # 获取登录终端的资金账号 [回测/交易]
            # "get_deliver",  # 获取历史交割单信息 [仅交易]
            # "get_fundjour",  # 获取历史资金流水信息 [仅交易]
            # "get_research_path",  # 获取研究路径 [回测/交易]
            # "get_trade_name",  # 获取交易名称 [仅交易]
            # # 高级交易函数 - 计划实现 [仅交易]
            # "order_tick",  # tick行情触发买卖
            # "debt_to_stock_order",  # 债转股委托
            # "etf_basket_order",  # ETF成分券篮子下单
            # "etf_purchase_redemption",  # ETF基金申赎接口
            # # 融资融券函数 - 计划实现 [仅两融交易]
            # "margin_trade",  # 担保品买卖
            # "margincash_open",  # 融资买入
            # "margincash_close",  # 卖券还款
            # "margincash_direct_refund",  # 直接还款
            # "marginsec_open",  # 融券卖出
            # "marginsec_close",  # 买券还券
            # "marginsec_direct_refund",  # 直接还券
            # "get_margincash_stocks",  # 获取融资标的列表
            # "get_marginsec_stocks",  # 获取融券标的列表
            # "get_margin_contract",  # 合约查询
            # "get_margin_contractreal",  # 实时合约查询
            # "get_margin_assert",  # 信用资产查询
            # "get_assure_security_list",  # 担保券查询
            # "get_margincash_open_amount",  # 融资标的最大可买数量查询
            # "get_margincash_close_amount",  # 卖券还款标的最大可卖数量查询
            # "get_marginsec_open_amount",  # 融券标的最大可卖数量查询
            # "get_marginsec_close_amount",  # 买券还券标的最大可买数量查询
            # "get_margin_entrans_amount",  # 现券还券数量查询
            # "get_enslo_security_info",  # 融券头寸信息查询
            # # 期货专用函数 - 计划实现
            # "buy_open",  # 开多 [回测/交易]
            # "sell_close",  # 多平 [回测/交易]
            # "sell_open",  # 空开 [回测/交易]
            # "buy_close",  # 空平 [回测/交易]
            # "get_instruments",  # 获取合约信息 [回测/交易]
            # "set_margin_rate",  # 设置期货保证金比例 [回测/交易]
            # # 期权专用函数 - 计划实现 [仅交易]
            # "option_exercise",  # 行权
            # "option_covered_lock",  # 期权标的备兑锁定
            # "option_covered_unlock",  # 期权标的备兑解锁
            # "open_prepared",  # 备兑开仓
            # "close_prepared",  # 备兑平仓
            # # 工具函数 - 计划实现 [仅交易]
            # "send_email",  # 发送邮箱信息
            # "send_qywx",  # 发送企业微信信息
            # "permission_test",  # 权限校验
            # "create_dir",  # 创建文件路径
        }

    def set_data_plugin(self, data_plugin: Any) -> None:
        """设置数据插件引用"""
        self._data_plugin = data_plugin
        self._logger.info("Data plugin set for live trading mode")

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在实盘交易模式下支持"""
        return api_name in self._supported_apis

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """实盘交易下单逻辑"""
        if self.event_bus:
            self.event_bus.publish(
                "trading.order.request",
                data={
                    "security": security,
                    "amount": amount,
                    "limit_price": limit_price,
                },
                source="ptrade_adapter",
            )
        return "live_order_placeholder"

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单"""
        # 获取当前价格
        current_price = limit_price or 10.0  # 默认价格

        # 计算股数
        amount = int(value / current_price)
        if amount <= 0:
            return None

        return self.order(security, amount, limit_price)

    def order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定目标数量买卖"""
        # 获取当前持仓
        current_amount = 0
        if security in self.context.portfolio.positions:
            current_amount = self.context.portfolio.positions[security].amount

        # 计算需要交易的数量
        trade_amount = target_amount - current_amount
        if trade_amount == 0:
            return None

        return self.order(security, trade_amount, limit_price)

    def order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """指定持仓市值买卖"""
        # 获取当前价格
        current_price = limit_price or 10.0  # 默认价格

        # 计算目标股数
        target_amount = int(target_value / current_price)

        return self.order_target(security, target_amount, limit_price)

    def order_market(self, security: str, amount: int) -> Optional[str]:
        """按市价进行委托"""
        # 实盘交易模式下，市价单不需要指定价格
        return self.order(security, amount, None)

    def cancel_order(self, order_id: str) -> bool:
        """实盘交易撤单"""
        if self.event_bus:
            self.event_bus.publish(
                "trading.cancel_order.request",
                data={"order_id": order_id},
                source="ptrade_adapter",
            )
        return True

    def cancel_order_ex(self, order_id: str) -> bool:
        """撤单扩展"""
        # 在实盘交易模式下，扩展撤单与cancel_order功能相同
        return self.cancel_order(order_id)

    def get_all_orders(self) -> List["Order"]:
        """获取账户当日全部订单"""
        # 在实盘交易模式下，返回所有订单
        return self.get_orders()

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """新股一键申购"""
        # 实盘交易模式下支持新股申购
        if self.event_bus:
            self.event_bus.publish(
                "trading.ipo_order.request",
                data={"amount_per_stock": amount_per_stock},
                source="ptrade_adapter",
            )
        return ["ipo_order_placeholder"]

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        # 实盘交易模式下支持盘后交易
        if self.event_bus:
            self.event_bus.publish(
                "trading.after_trading_order.request",
                data={
                    "security": security,
                    "amount": amount,
                    "limit_price": limit_price,
                },
                source="ptrade_adapter",
            )
        return "after_trading_order_placeholder"

    def after_trading_cancel_order(self, order_id: str) -> bool:
        """盘后固定价委托撤单"""
        # 实盘交易模式下支持盘后撤单
        if self.event_bus:
            self.event_bus.publish(
                "trading.after_trading_cancel_order.request",
                data={"order_id": order_id},
                source="ptrade_adapter",
            )
        return True

    def get_position(self, security: str) -> Optional["Position"]:
        """获取持仓信息"""
        return self.context.portfolio.positions.get(security)

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多支股票持仓信息"""
        positions = {}
        for security in security_list:
            position = self.get_position(security)
            if position:
                positions[security] = {
                    "sid": position.sid,
                    "amount": position.amount,
                    "enable_amount": position.enable_amount,
                    "cost_basis": position.cost_basis,
                    "last_sale_price": position.last_sale_price,
                    "market_value": position.market_value,
                    "pnl": position.pnl,
                    "returns": position.returns,
                    "today_amount": position.today_amount,
                    "business_type": position.business_type,
                }
            else:
                positions[security] = {
                    "sid": security,
                    "amount": 0,
                    "enable_amount": 0,
                    "cost_basis": 0.0,
                    "last_sale_price": 0.0,
                    "market_value": 0.0,
                    "pnl": 0.0,
                    "returns": 0.0,
                    "today_amount": 0,
                    "business_type": "stock",
                }
        return positions

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取未完成订单"""
        if not self.context.blotter:
            return []

        open_orders = []
        for order in self.context.blotter.orders.values():
            if order.status in ["new", "submitted", "partially_filled"]:
                if security is None or order.symbol == security:
                    open_orders.append(order)
        return open_orders

    def get_order(self, order_id: str) -> Optional["Order"]:
        """获取指定订单"""
        if self.context.blotter:
            return self.context.blotter.get_order(order_id)
        return None

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取全部订单"""
        if not self.context.blotter:
            return []

        orders = []
        for order in self.context.blotter.orders.values():
            if security is None or order.symbol == security:
                orders.append(order)

        orders.sort(key=lambda o: o.dt, reverse=True)
        return orders

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当日成交订单"""
        if not self.context.blotter:
            return []

        trades = []
        for order in self.context.blotter.orders.values():
            if order.status == "filled" and order.filled != 0:
                if security is None or order.symbol == security:
                    trades.append(
                        {
                            "order_id": order.id,
                            "security": order.symbol,
                            "amount": order.filled,
                            "price": order.limit or 0.0,
                            "filled_amount": order.filled,
                            "commission": 0.0,
                            "datetime": order.dt,
                            "side": "buy" if order.amount > 0 else "sell",
                        }
                    )

        trades.sort(key=lambda t: t["datetime"], reverse=True)  # type: ignore
        return trades

    # 以下方法现在由父类BaseRouter提供，无需重复实现：
    # get_history, get_price, get_snapshot - 通过父类BaseRouter实现
    # get_stock_info, get_fundamentals - 通过父类BaseRouter实现
    # get_trading_day, get_all_trades_days, get_trade_days - 通过父类BaseRouter实现
    # set_universe, set_benchmark - 通过父类BaseRouter实现
    # get_MACD, get_KDJ, get_RSI, get_CCI - 通过父类BaseRouter实现
    # log, check_limit, is_trade - 通过父类BaseRouter实现
    # get_stock_name等9个新股票信息API - 通过父类BaseRouter实现

    # 实盘交易模式特有的配置方法（一般不支持，只记录警告）
    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        # 实盘交易模式下不支持设置佣金费率
        self._logger.warning("Setting commission is not supported in live trading mode")

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        # 实盘交易模式下不支持设置滑点
        self._logger.warning("Setting slippage is not supported in live trading mode")

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点"""
        # 实盘交易模式下不支持设置固定滑点
        self._logger.warning(
            "Setting fixed slippage is not supported in live trading mode"
        )

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        # 实盘交易模式下不支持设置成交比例
        self._logger.warning(
            "Setting volume ratio is not supported in live trading mode"
        )

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式"""
        # 实盘交易模式下不支持设置限制模式
        self._logger.warning("Setting limit mode is not supported in live trading mode")

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        # 实盘交易模式下不支持设置底仓
        self._logger.warning(
            "Setting yesterday position is not supported in live trading mode"
        )

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数"""
        # 存储在上下文中
        if not hasattr(self.context, "_parameters"):
            setattr(self.context, "_parameters", {})
        getattr(self.context, "_parameters").update(params)
        self._logger.info(f"Parameters set: {params}")

    def handle_data(self, data: Dict[str, Any]) -> None:
        """实盘交易数据处理"""
        # 更新当前价格数据
        for security, price_data in data.items():
            if security in self.context.portfolio.positions:
                position = self.context.portfolio.positions[security]
                position.last_sale_price = price_data.get(
                    "price", position.last_sale_price
                )

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()

    # ==========================================
    # 定时和回调 API 实现
    # ==========================================

    def run_daily(
        self, func: Any, time_str: str = "09:30", *args: Any, **kwargs: Any
    ) -> str:
        """按日周期处理 - 每日定时执行指定函数"""
        self._logger.warning(
            "run_daily scheduling should be handled by external scheduler in live trading mode"
        )
        # 在实盘模式下，定时任务应该由外部调度系统处理
        job_id = f"daily_{id(func)}_{time_str}"
        if not hasattr(self.context, "_daily_functions"):
            setattr(self.context, "_daily_functions", {})
        getattr(self.context, "_daily_functions")[job_id] = {
            "func": func,
            "time": time_str,
            "args": args,
            "kwargs": kwargs,
        }
        return job_id

    def run_interval(
        self, func: Any, interval: Union[int, str], *args: Any, **kwargs: Any
    ) -> str:
        """按设定周期处理 - 按指定间隔重复执行函数"""
        self._logger.warning(
            "run_interval scheduling should be handled by external scheduler in live trading mode"
        )
        # 在实盘模式下，定时任务应该由外部调度系统处理
        job_id = f"interval_{id(func)}_{interval}"
        if not hasattr(self.context, "_interval_functions"):
            setattr(self.context, "_interval_functions", {})
        getattr(self.context, "_interval_functions")[job_id] = {
            "func": func,
            "interval": interval,
            "args": args,
            "kwargs": kwargs,
        }
        return job_id

    def tick_data(self, func: Any) -> bool:
        """tick级别处理 - 注册tick数据回调函数"""
        # 在实盘模式下支持tick数据处理
        if not hasattr(self.context, "_tick_callbacks"):
            setattr(self.context, "_tick_callbacks", [])
        getattr(self.context, "_tick_callbacks").append(func)
        self._logger.info("Tick data callback registered for live trading")
        return True

    def on_order_response(self, func: Any) -> bool:
        """委托回报 - 注册订单状态变化回调函数"""
        # 在实盘模式下，订单回调非常重要
        if not hasattr(self.context, "_order_response_callbacks"):
            setattr(self.context, "_order_response_callbacks", [])
        getattr(self.context, "_order_response_callbacks").append(func)
        self._logger.info("Order response callback registered for live trading")
        return True

    def on_trade_response(self, func: Any) -> bool:
        """成交回报 - 注册成交确认回调函数"""
        # 在实盘模式下，成交回调非常重要
        if not hasattr(self.context, "_trade_response_callbacks"):
            setattr(self.context, "_trade_response_callbacks", [])
        getattr(self.context, "_trade_response_callbacks").append(func)
        self._logger.info("Trade response callback registered for live trading")
        return True
