# -*- coding: utf-8 -*-
"""
回测交易服务

处理回测模式下的所有交易相关业务逻辑，包括订单执行、风险控制、
持仓管理等，从API路由器中分离出来
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from . import BaseService

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class BacktestService(BaseService):
    """回测服务 - 处理回测模式下的交易业务逻辑"""

    def __init__(self, context: "PTradeContext", **kwargs):
        super().__init__(**kwargs)
        self.context = context
        self._slippage_rate = 0.0
        self._commission_rate = 0.0
        self._volume_ratio = 1.0
        self._limit_mode = "limit"

    def initialize(self) -> None:
        """初始化回测服务"""
        self._logger.info("Initializing BacktestService")

    def shutdown(self) -> None:
        """关闭回测服务"""
        self._logger.info("Shutting down BacktestService")

    # ================================
    # 配置管理
    # ================================

    def set_commission(self, commission: float) -> None:
        """设置佣金费率"""
        self._commission_rate = commission
        self._logger.info(f"Commission rate set to {commission}")
        self.publish_event(
            "backtest.commission.updated",
            {"commission_rate": commission},
            "backtest_service",
        )

    def set_slippage(self, slippage: float) -> None:
        """设置滑点"""
        self._slippage_rate = slippage
        self._logger.info(f"Slippage rate set to {slippage}")
        self.publish_event(
            "backtest.slippage.updated", {"slippage_rate": slippage}, "backtest_service"
        )

    def set_volume_ratio(self, ratio: float) -> None:
        """设置成交比例"""
        if not 0 < ratio <= 1:
            raise ValueError("Volume ratio must be between 0 and 1")
        self._volume_ratio = ratio
        self._logger.info(f"Volume ratio set to {ratio}")

    def set_limit_mode(self, mode: str) -> None:
        """设置限价模式"""
        valid_modes = ["limit", "market", "strict"]
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid limit mode: {mode}. Must be one of {valid_modes}"
            )
        self._limit_mode = mode
        self._logger.info(f"Limit mode set to {mode}")

    # ================================
    # 订单管理
    # ================================

    def execute_order_value(
        self, security: str, value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值执行订单"""
        # 获取当前价格
        current_price = limit_price or self._get_current_price(security)

        # 计算股数
        amount = int(value / current_price)
        if amount <= 0:
            return None

        return self.execute_order(security, amount, limit_price)

    def execute_order_target(
        self, security: str, target_amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """执行目标数量订单"""
        # 获取当前持仓
        current_amount = 0
        if security in self.context.portfolio.positions:
            current_amount = self.context.portfolio.positions[security].amount

        # 计算需要交易的数量
        trade_amount = target_amount - current_amount
        if trade_amount == 0:
            return None

        return self.execute_order(security, trade_amount, limit_price)

    def execute_order_target_value(
        self, security: str, target_value: float, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """执行目标价值订单"""
        # 获取当前价格
        current_price = limit_price or self._get_current_price(security)

        # 计算目标股数
        target_amount = int(target_value / current_price)

        return self.execute_order_target(security, target_amount, limit_price)

    def execute_market_order(self, security: str, amount: int) -> Optional[str]:
        """执行市价订单"""
        # 在回测模式下，市价单使用当前价格
        current_price = self._get_current_price(security)
        return self.execute_order(security, amount, current_price)

    def execute_order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> Optional[str]:
        """执行订单 - 核心交易业务逻辑"""
        if not self.context.blotter:
            self._logger.error("No blotter available for order execution")
            return None

        # 1. 风险检查
        if not self._validate_order_risk(security, amount, limit_price):
            return None

        # 2. 创建订单
        order_id = self._create_order(security, amount, limit_price)
        if not order_id:
            return None

        # 3. 执行订单
        self._process_order_execution(order_id)

        # 4. 发布事件
        self.publish_event(
            "backtest.order.executed",
            {
                "order_id": order_id,
                "security": security,
                "amount": amount,
                "limit_price": limit_price,
            },
            "backtest_service",
        )

        return order_id

    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        if not self.context.blotter:
            return False

        if order_id not in self.context.blotter.orders:
            self._logger.warning(f"Order {order_id} not found")
            return False

        order = self.context.blotter.orders[order_id]
        if order.status != "submitted":
            self._logger.warning(
                f"Cannot cancel order {order_id} with status {order.status}"
            )
            return False

        order.status = "cancelled"
        self._logger.info(f"Order cancelled: {order_id}")

        self.publish_event(
            "backtest.order.cancelled", {"order_id": order_id}, "backtest_service"
        )

        return True

    def cancel_order_ex(self, order_id: str) -> bool:
        """扩展撤单功能"""
        # 在回测模式下，扩展撤单与cancel_order功能相同
        return self.cancel_order(order_id)

    # ================================
    # 持仓管理
    # ================================

    def get_position(self, security: str) -> Optional["Position"]:
        """获取持仓"""
        return self.context.portfolio.positions.get(security)

    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多个持仓"""
        positions = {}
        for security in security_list:
            position = self.get_position(security)
            if position:
                positions[security] = {
                    "amount": position.amount,
                    "cost_basis": position.cost_basis,
                    "last_sale_price": position.last_sale_price,
                    "market_value": position.market_value,
                }
            else:
                positions[security] = {
                    "amount": 0,
                    "cost_basis": 0.0,
                    "last_sale_price": 0.0,
                    "market_value": 0.0,
                }
        return positions

    def set_yesterday_position(self, positions: Dict[str, Any]) -> None:
        """设置昨日持仓"""
        for security, position_data in positions.items():
            if isinstance(position_data, dict):
                amount = position_data.get("amount", 0)
                cost_basis = position_data.get("cost_basis", 0.0)
            else:
                amount = int(position_data)
                cost_basis = 0.0

            if amount > 0:
                from ..models import Position

                position = Position(
                    sid=security,
                    amount=amount,
                    enable_amount=amount,
                    cost_basis=cost_basis,
                    last_sale_price=cost_basis,
                )
                self.context.portfolio.positions[security] = position

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()

        self._logger.info(f"Yesterday positions set: {len(positions)} securities")

    # ================================
    # 私有方法 - 内部业务逻辑
    # ================================

    def _validate_order_risk(
        self, security: str, amount: int, limit_price: Optional[float]
    ) -> bool:
        """验证订单风险"""
        # 资金检查（买入订单）
        if amount > 0:
            price = limit_price or self._get_current_price(security)
            execution_price = price * (1 + self._slippage_rate)
            commission = abs(amount * execution_price * self._commission_rate)
            required_cash = amount * execution_price + commission

            if self.context.portfolio.cash < required_cash:
                self._logger.warning(
                    f"Order rejected: insufficient cash for {security}. "
                    f"Required: {required_cash:.2f}, Available: {self.context.portfolio.cash:.2f}"
                )
                return False

        # 持仓检查（卖出订单）
        else:
            current_position = self.context.portfolio.positions.get(security)
            if not current_position or current_position.amount < abs(amount):
                self._logger.warning(
                    f"Order rejected: insufficient position for {security}. "
                    f"Current: {current_position.amount if current_position else 0}, "
                    f"Requested: {abs(amount)}"
                )
                return False

        return True

    def _create_order(
        self, security: str, amount: int, limit_price: Optional[float]
    ) -> Optional[str]:
        """创建订单"""
        import uuid

        from ..models import Order

        order_id = str(uuid.uuid4())
        order = Order(
            id=order_id,
            symbol=security,
            amount=amount,
            limit=limit_price,
            dt=self.context.current_dt,
        )

        self.context.blotter.orders[order_id] = order
        self._logger.info(f"Order created: {order_id}")
        return order_id

    def _process_order_execution(self, order_id: str) -> None:
        """处理订单执行"""
        order = self.context.blotter.orders[order_id]
        security = order.symbol
        amount = order.amount
        price = order.limit or self._get_current_price(security)

        # 计算实际成交价格（包含滑点）
        execution_price = price * (
            1 + self._slippage_rate if amount > 0 else 1 - self._slippage_rate
        )

        # 计算手续费
        commission = abs(amount * execution_price * self._commission_rate)

        # 更新持仓
        self._update_position(security, amount, execution_price, price)

        # 更新现金
        if amount > 0:  # 买入订单：减少现金
            self.context.portfolio.cash -= amount * execution_price + commission
        else:  # 卖出订单：增加现金，但扣除手续费
            self.context.portfolio.cash += abs(amount) * execution_price - commission

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()

        # 更新订单状态
        order.status = "filled"
        order.filled = amount

        self._logger.info(
            f"Order executed: {order_id}, {security}, {amount} @ {execution_price:.2f}, commission: {commission:.2f}"
        )

    def _update_position(
        self, security: str, amount: int, execution_price: float, market_price: float
    ) -> None:
        """更新持仓"""
        from ..models import Position

        if security in self.context.portfolio.positions:
            position = self.context.portfolio.positions[security]
            if amount > 0:  # 买入：更新成本基础
                total_cost = (
                    position.amount * position.cost_basis + amount * execution_price
                )
                total_amount = position.amount + amount
                position.cost_basis = (
                    total_cost / total_amount if total_amount > 0 else 0
                )
                position.amount = total_amount
            else:  # 卖出：减少持仓
                position.amount += amount  # amount是负数
            position.last_sale_price = market_price
        else:
            # 创建新持仓
            if amount > 0:
                self.context.portfolio.positions[security] = Position(
                    sid=security,
                    amount=amount,
                    enable_amount=amount,
                    cost_basis=execution_price,
                    last_sale_price=market_price,
                )

    def _get_current_price(self, security: str) -> float:
        """获取当前价格"""
        # 这里应该通过DataService获取价格，暂时返回默认值
        return 10.0

    # ================================
    # 查询接口
    # ================================

    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取订单列表"""
        if not self.context.blotter:
            return []

        orders = list(self.context.blotter.orders.values())
        if security:
            orders = [order for order in orders if order.symbol == security]

        return sorted(orders, key=lambda o: o.dt, reverse=True)

    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取未完成订单"""
        orders = self.get_orders(security)
        return [order for order in orders if order.status == "submitted"]

    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取成交记录"""
        orders = self.get_orders(security)
        trades = []

        for order in orders:
            if order.status == "filled":
                trades.append(
                    {
                        "order_id": order.id,
                        "security": order.symbol,
                        "amount": order.filled,
                        "price": order.limit or 0.0,
                        "filled_amount": order.filled,
                        "commission": abs(
                            order.filled * (order.limit or 0.0) * self._commission_rate
                        ),
                        "datetime": order.dt,
                        "side": "buy" if order.amount > 0 else "sell",
                    }
                )

        return sorted(trades, key=lambda t: t["datetime"], reverse=True)

    # ================================
    # 数据更新处理
    # ================================

    def handle_data_update(self, data: Dict[str, Any]) -> None:
        """处理数据更新"""
        # 更新当前价格数据
        for security, price_data in data.items():
            if security in self.context.portfolio.positions:
                position = self.context.portfolio.positions[security]
                position.last_sale_price = price_data.get(
                    "price", position.last_sale_price
                )

        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()
