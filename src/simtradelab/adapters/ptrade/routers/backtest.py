# -*- coding: utf-8 -*-
"""
PTrade回测模式API路由器
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ....core.event_bus import EventBus
from .base import BaseAPIRouter
from .common_utils_mixin import CommonUtilsMixin
from .data_retrieval_mixin import DataRetrievalMixin
from .stock_info_mixin import StockInfoMixin
from .technical_indicator_mixin import TechnicalIndicatorMixin

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class BacktestAPIRouter(
    BaseAPIRouter,
    StockInfoMixin,
    TechnicalIndicatorMixin,
    DataRetrievalMixin,
    CommonUtilsMixin,
):
    """回测模式API路由器"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        slippage_rate: float = 0.0,
        commission_rate: float = 0.0,
    ):
        super().__init__(context, event_bus)
        self._slippage_rate = slippage_rate
        self._commission_rate = commission_rate
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
            "set_commission",
            "set_slippage",
            "set_parameters",
            "set_fixed_slippage",
            "set_volume_ratio",
            "set_limit_mode",
            "set_yesterday_position",
            # 工具API
            "log",
            "check_limit",
            "handle_data",
        }

    def set_data_plugin(self, data_plugin: Any) -> None:
        """设置数据插件引用"""
        self._data_plugin = data_plugin
        self._logger.info("Data plugin set for backtest mode")

    def is_mode_supported(self, api_name: str) -> bool:
        """检查API是否在回测模式下支持"""
        return api_name in self._supported_apis

    def order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """回测模式下单逻辑"""
        if not self.context.blotter:
            return None

        # 检查资金是否充足（仅对买入订单）
        if amount > 0:  # 买入订单
            price = limit_price or 10.0
            execution_price = price * (1 + self._slippage_rate)
            commission = abs(amount * execution_price * self._commission_rate)
            required_cash = amount * execution_price + commission

            if self.context.portfolio.cash < required_cash:
                self._logger.warning(
                    f"Order rejected: insufficient cash for {security}"
                )
                return None

        order_id = self.context.blotter.create_order(security, amount, limit_price)
        self._simulate_order_execution(order_id)
        return order_id

    def order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值下单"""
        # 获取当前价格
        current_price = limit_price or self._get_current_price(security)

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
        current_price = limit_price or self._get_current_price(security)

        # 计算目标股数
        target_amount = int(target_value / current_price)

        return self.order_target(security, target_amount, limit_price)

    def order_market(self, security: str, amount: int) -> Optional[str]:
        """按市价进行委托"""
        # 在回测模式下，市价单使用当前价格
        current_price = self._get_current_price(security)
        return self.order(security, amount, current_price)

    def cancel_order(self, order_id: str) -> bool:
        """回测模式撤单"""
        if self.context.blotter:
            return self.context.blotter.cancel_order(order_id)
        return False

    def cancel_order_ex(self, order_id: str) -> bool:
        """撤单扩展"""
        # 在回测模式下，扩展撤单与cancel_order功能相同
        return self.cancel_order(order_id)

    def get_all_orders(self) -> List["Order"]:
        """获取账户当日全部订单"""
        # 在回测模式下，返回所有订单
        return self.get_orders()

    def ipo_stocks_order(self, amount_per_stock: int = 10000) -> List[str]:
        """新股一键申购"""
        # 回测模式下不支持新股申购，返回空列表
        self._logger.warning("IPO orders are not supported in backtest mode")
        return []

    def after_trading_order(
        self, security: str, amount: int, limit_price: float
    ) -> Optional[str]:
        """盘后固定价委托"""
        # 回测模式下不支持盘后交易，返回None
        self._logger.warning("After trading orders are not supported in backtest mode")
        return None

    def after_trading_cancel_order(self, order_id: str) -> bool:
        """盘后固定价委托撤单"""
        # 回测模式下不支持盘后交易，返回False
        self._logger.warning(
            "After trading cancel orders are not supported in backtest mode"
        )
        return False

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

    # 回测模式特有的配置方法（需要特殊处理）
    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        self._commission_rate = commission
        self._logger.info(f"Commission rate set to {commission}")

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        self._slippage_rate = slippage
        self._logger.info(f"Slippage rate set to {slippage}")

    def set_fixed_slippage(self, slippage: float) -> None:
        """设置固定滑点"""
        self._slippage_rate = slippage
        self._logger.info(f"Fixed slippage rate set to {slippage}")

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        # 验证参数范围
        if not 0 < ratio <= 1:
            raise ValueError("Volume ratio must be between 0 and 1")

        # 存储在上下文中
        setattr(self.context, "_volume_ratio", ratio)

        # 更新交易设置
        if hasattr(self.context, "sim_params") and self.context.sim_params is not None:
            setattr(self.context.sim_params, "volume_ratio", ratio)

        self._logger.info(f"Volume ratio set to {ratio}")

    def set_limit_mode(self, mode: str) -> None:
        """设置回测成交数量限制模式"""
        # 验证模式
        valid_modes = ["volume", "order", "none"]
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid limit mode: {mode}. Must be one of {valid_modes}"
            )

        # 存储在上下文中
        setattr(self.context, "_limit_mode", mode)

        # 更新交易设置
        if hasattr(self.context, "sim_params") and self.context.sim_params is not None:
            setattr(self.context.sim_params, "limit_mode", mode)

        self._logger.info(f"Limit mode set to {mode}")

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置底仓"""
        # 验证底仓数据格式
        for security, position_data in positions.items():
            if not isinstance(position_data, dict):
                raise ValueError(f"Position data for {security} must be a dictionary")

            required_fields = ["amount", "cost_basis"]
            for field in required_fields:
                if field not in position_data:
                    raise ValueError(f"Missing required field '{field}' for {security}")

        # 存储在上下文中
        setattr(self.context, "_yesterday_position", positions)

        # 初始化底仓到投资组合中
        from ..models import Position

        for security, position_data in positions.items():
            position = Position(
                sid=security,
                amount=position_data["amount"],
                enable_amount=position_data["amount"],
                cost_basis=position_data["cost_basis"],
                last_sale_price=position_data.get(
                    "last_price", position_data["cost_basis"]
                ),
                today_amount=0,  # 底仓不是今日开仓
            )
            self.context.portfolio.positions[security] = position

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()

        self._logger.info(f"Yesterday position set with {len(positions)} positions")

    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置策略配置参数"""
        # 将参数存储在上下文中，支持动态更新
        if not hasattr(self.context, "_parameters"):
            setattr(self.context, "_parameters", {})

        # 更新参数
        getattr(self.context, "_parameters").update(params)

        # 处理一些特殊参数
        if "commission" in params:
            self.set_commission(float(params["commission"]))

        if "slippage" in params:
            self.set_slippage(float(params["slippage"]))

        if "universe" in params:
            self.set_universe(params["universe"])

        if "benchmark" in params:
            self.set_benchmark(params["benchmark"])

        self._logger.info(f"Parameters updated: {params}")

        # 发布参数更新事件
        if self.event_bus:
            self.event_bus.publish(
                "ptrade.parameters.updated",
                data={"parameters": params},
                source="ptrade_backtest_router",
            )

    def handle_data(self, data: Dict[str, Any]) -> None:
        """回测模式数据处理"""
        # 更新当前价格数据
        for security, price_data in data.items():
            if security in self.context.portfolio.positions:
                position = self.context.portfolio.positions[security]
                position.last_sale_price = price_data.get(
                    "price", position.last_sale_price
                )

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()

    def _simulate_order_execution(self, order_id: str) -> None:
        """模拟订单执行"""
        if not self.context.blotter:
            return

        order = self.context.blotter.get_order(order_id)
        if not order:
            return

        security = order.symbol
        amount = order.amount
        price = order.limit or 10.0

        # 计算实际成交价格（包含滑点）
        execution_price = price * (
            1 + self._slippage_rate if amount > 0 else 1 - self._slippage_rate
        )

        # 计算手续费
        commission = abs(amount * execution_price * self._commission_rate)

        # 检查资金是否充足（仅对买入订单）
        portfolio = self.context.portfolio
        if amount > 0:  # 买入订单
            required_cash = amount * execution_price + commission
            if portfolio.cash < required_cash:
                # 资金不足，订单失败
                order.status = "rejected"
                self._logger.warning(f"Order {order_id} rejected: insufficient cash")
                return

        # 更新持仓
        if security in portfolio.positions:
            position = portfolio.positions[security]
            total_cost = (
                position.amount * position.cost_basis + amount * execution_price
            )
            total_amount = position.amount + amount
            if total_amount == 0:
                del portfolio.positions[security]
            else:
                position.amount = total_amount
                position.cost_basis = total_cost / total_amount
                position.last_sale_price = execution_price
        else:
            if amount != 0:
                # 动态导入Position类以避免循环导入
                from ..models import Position

                portfolio.positions[security] = Position(
                    sid=security,
                    enable_amount=amount,
                    amount=amount,
                    cost_basis=execution_price,
                    last_sale_price=execution_price,
                )

        # 更新现金
        portfolio.cash -= amount * execution_price + commission

        # 更新投资组合价值
        portfolio.update_portfolio_value()

        # 更新订单状态
        order.status = "filled"
        order.filled = amount

        self._logger.info(
            f"Order executed: {order_id}, {security}, {amount} @ {execution_price}"
        )

    def _get_current_price(self, security: str) -> float:
        """获取股票当前价格"""
        # 从上下文获取价格数据
        if (
            hasattr(self.context, "current_data")
            and security in self.context.current_data
        ):
            price = self.context.current_data[security].get("price", 10.0)
            return float(price)

        # 使用默认价格
        base_price = 15.0 if security.startswith("000") else 20.0
        return base_price
