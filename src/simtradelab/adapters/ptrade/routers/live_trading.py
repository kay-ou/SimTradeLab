# -*- coding: utf-8 -*-
"""
PTrade实盘交易模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ....core.event_bus import EventBus
from .base import BaseAPIRouter
from .common_utils_mixin import CommonUtilsMixin
from .data_retrieval_mixin import DataRetrievalMixin
from .stock_info_mixin import StockInfoMixin
from .technical_indicator_mixin import TechnicalIndicatorMixin

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class LiveTradingAPIRouter(
    BaseAPIRouter,
    StockInfoMixin,
    TechnicalIndicatorMixin,
    DataRetrievalMixin,
    CommonUtilsMixin,
):
    """实盘交易模式API路由器"""

    def __init__(self, context: "PTradeContext", event_bus: Optional[EventBus] = None):
        super().__init__(context, event_bus)
        self._data_plugin = None  # 将在设置时从适配器获取
        self._supported_apis = {
            # 交易相关API
            "order",
            "order_value",
            "order_target",
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
            # 数据获取API
            "get_history",
            "get_price",
            "get_snapshot",
            "get_stock_info",
            "get_fundamentals",
            # 股票信息API (新增的9个API)
            "get_stock_name",
            "get_stock_status",
            "get_stock_exrights",
            "get_stock_blocks",
            "get_index_stocks",
            "get_industry_stocks",
            "get_Ashares",
            "get_etf_list",
            "get_ipo_stocks",
            # 技术指标API
            "get_MACD",
            "get_KDJ",
            "get_RSI",
            "get_CCI",
            # 交易日期API
            "get_trading_day",
            "get_all_trades_days",
            "get_trade_days",
            # 配置API
            "set_universe",
            "set_benchmark",
            "set_parameters",
            # 工具API
            "log",
            "check_limit",
            "handle_data",
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

    # 以下方法现在由Mixin提供，无需重复实现：
    # get_history, get_price, get_snapshot - 来自DataRetrievalMixin
    # get_stock_info, get_fundamentals - 来自DataRetrievalMixin
    # get_trading_day, get_all_trades_days, get_trade_days - 来自CommonUtilsMixin
    # set_universe, set_benchmark - 来自CommonUtilsMixin
    # get_MACD, get_KDJ, get_RSI, get_CCI - 来自TechnicalIndicatorMixin
    # log, check_limit - 来自CommonUtilsMixin
    # get_stock_name等9个新股票信息API - 来自StockInfoMixin

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
    # 数据获取方法 - 委托给DataRetrievalMixin
    # ==========================================
    def get_history(self, *args, **kwargs):
        return DataRetrievalMixin.get_history(self, *args, **kwargs)

    def get_price(self, *args, **kwargs):
        return DataRetrievalMixin.get_price(self, *args, **kwargs)

    def get_snapshot(self, *args, **kwargs):
        return DataRetrievalMixin.get_snapshot(self, *args, **kwargs)

    def get_stock_info(self, *args, **kwargs):
        return DataRetrievalMixin.get_stock_info(self, *args, **kwargs)

    def get_fundamentals(self, *args, **kwargs):
        return DataRetrievalMixin.get_fundamentals(self, *args, **kwargs)

    # ==========================================
    # 股票信息方法 - 委托给StockInfoMixin
    # ==========================================
    def get_stock_name(self, *args, **kwargs):
        return StockInfoMixin.get_stock_name(self, *args, **kwargs)

    def get_stock_status(self, *args, **kwargs):
        return StockInfoMixin.get_stock_status(self, *args, **kwargs)

    def get_stock_exrights(self, *args, **kwargs):
        return StockInfoMixin.get_stock_exrights(self, *args, **kwargs)

    def get_stock_blocks(self, *args, **kwargs):
        return StockInfoMixin.get_stock_blocks(self, *args, **kwargs)

    def get_index_stocks(self, *args, **kwargs):
        return StockInfoMixin.get_index_stocks(self, *args, **kwargs)

    def get_industry_stocks(self, *args, **kwargs):
        return StockInfoMixin.get_industry_stocks(self, *args, **kwargs)

    def get_Ashares(self, *args, **kwargs):
        return StockInfoMixin.get_Ashares(self, *args, **kwargs)

    def get_etf_list(self, *args, **kwargs):
        return StockInfoMixin.get_etf_list(self, *args, **kwargs)

    def get_ipo_stocks(self, *args, **kwargs):
        return StockInfoMixin.get_ipo_stocks(self, *args, **kwargs)

    # ==========================================
    # 技术指标方法 - 委托给TechnicalIndicatorMixin
    # ==========================================
    def get_MACD(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_MACD(self, *args, **kwargs)

    def get_KDJ(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_KDJ(self, *args, **kwargs)

    def get_RSI(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_RSI(self, *args, **kwargs)

    def get_CCI(self, *args, **kwargs):
        return TechnicalIndicatorMixin.get_CCI(self, *args, **kwargs)

    # ==========================================
    # 通用工具方法 - 委托给CommonUtilsMixin
    # ==========================================
    def get_trading_day(self, *args, **kwargs):
        return CommonUtilsMixin.get_trading_day(self, *args, **kwargs)

    def get_all_trades_days(self, *args, **kwargs):
        return CommonUtilsMixin.get_all_trades_days(self, *args, **kwargs)

    def get_trade_days(self, *args, **kwargs):
        return CommonUtilsMixin.get_trade_days(self, *args, **kwargs)

    def set_universe(self, *args, **kwargs):
        return CommonUtilsMixin.set_universe(self, *args, **kwargs)

    def set_benchmark(self, *args, **kwargs):
        return CommonUtilsMixin.set_benchmark(self, *args, **kwargs)

    def log(self, *args, **kwargs):
        return CommonUtilsMixin.log(self, *args, **kwargs)

    def check_limit(self, *args, **kwargs):
        return CommonUtilsMixin.check_limit(self, *args, **kwargs)

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
