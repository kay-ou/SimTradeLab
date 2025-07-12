# -*- coding: utf-8 -*-
"""
实盘交易服务

处理实盘交易模式下的所有交易相关业务逻辑，包括订单执行、
风险控制、持仓管理等，从API路由器中分离出来
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from . import BaseService

if TYPE_CHECKING:
    from ..context import PTradeContext
    from ..models import Order, Position


class TradingService(BaseService):
    """交易服务 - 处理实盘交易模式下的业务逻辑"""
    
    def __init__(self, context: "PTradeContext", **kwargs):
        super().__init__(**kwargs)
        self.context = context
        
    def initialize(self) -> None:
        """初始化交易服务"""
        self._logger.info("Initializing TradingService")
    
    def shutdown(self) -> None:
        """关闭交易服务"""
        self._logger.info("Shutting down TradingService")
    
    # ================================
    # 订单管理 - 实盘交易逻辑
    # ================================
    
    def execute_order(
        self, 
        security: str, 
        amount: int, 
        limit_price: Optional[float] = None
    ) -> Optional[str]:
        """执行实盘交易订单"""
        # 1. 风险检查
        if not self._validate_order_risk(security, amount, limit_price):
            return None
        
        # 2. 发布交易请求事件（实盘交易需要与外部系统交互）
        self.publish_event(
            "live_trading.order.request",
            {
                "security": security,
                "amount": amount,
                "limit_price": limit_price,
                "timestamp": self.context.current_dt,
            },
            "trading_service"
        )
        
        # 3. 生成订单ID（实际执行结果由外部系统确认）
        import uuid
        order_id = f"live_{uuid.uuid4().hex[:8]}"
        
        self._logger.info(f"Live order request sent: {order_id}")
        return order_id
    
    def execute_order_value(
        self, 
        security: str, 
        value: float, 
        limit_price: Optional[float] = None
    ) -> Optional[str]:
        """按价值执行实盘交易订单"""
        # 获取当前价格（实盘需要从市场数据获取）
        current_price = limit_price or self._get_market_price(security)
        if current_price <= 0:
            self._logger.warning(f"Cannot get valid price for {security}")
            return None
        
        # 计算股数
        amount = int(value / current_price)
        if amount <= 0:
            self._logger.warning(f"Calculated amount ({amount}) is not valid")
            return None
        
        return self.execute_order(security, amount, limit_price)
    
    def execute_order_target(
        self, 
        security: str, 
        target_amount: int, 
        limit_price: Optional[float] = None
    ) -> Optional[str]:
        """执行目标数量实盘交易订单"""
        # 获取当前持仓
        current_position = self.get_position(security)
        current_amount = current_position.amount if current_position else 0
        
        # 计算需要交易的数量
        trade_amount = target_amount - current_amount
        if trade_amount == 0:
            self._logger.info(f"No trade needed for {security}: already at target amount")
            return None
        
        return self.execute_order(security, trade_amount, limit_price)
    
    def execute_order_target_value(
        self, 
        security: str, 
        target_value: float, 
        limit_price: Optional[float] = None
    ) -> Optional[str]:
        """执行目标价值实盘交易订单"""
        # 获取当前价格
        current_price = limit_price or self._get_market_price(security)
        if current_price <= 0:
            return None
        
        # 计算目标股数
        target_amount = int(target_value / current_price)
        return self.execute_order_target(security, target_amount, limit_price)
    
    def execute_market_order(self, security: str, amount: int) -> Optional[str]:
        """执行市价实盘交易订单"""
        # 实盘交易模式下，市价单不需要指定价格
        return self.execute_order(security, amount, None)
    
    def cancel_order(self, order_id: str) -> bool:
        """取消实盘交易订单"""
        # 发布撤单请求事件
        self.publish_event(
            "live_trading.cancel_order.request",
            {"order_id": order_id},
            "trading_service"
        )
        
        self._logger.info(f"Cancel order request sent: {order_id}")
        return True
    
    def cancel_order_ex(self, order_id: str) -> bool:
        """扩展撤单功能"""
        # 在实盘交易模式下，扩展撤单与cancel_order功能相同
        return self.cancel_order(order_id)
    
    # ================================
    # 特殊订单类型 - 实盘交易专有
    # ================================
    
    def execute_ipo_order(self, amount_per_stock: int = 10000) -> List[str]:
        """执行新股申购"""
        # 发布新股申购请求事件
        self.publish_event(
            "live_trading.ipo_order.request",
            {"amount_per_stock": amount_per_stock},
            "trading_service"
        )
        
        self._logger.info(f"IPO order request sent with amount: {amount_per_stock}")
        return ["ipo_order_placeholder"]
    
    def execute_after_trading_order(
        self, 
        security: str, 
        amount: int, 
        limit_price: float
    ) -> Optional[str]:
        """执行盘后固定价委托"""
        # 发布盘后交易请求事件
        self.publish_event(
            "live_trading.after_trading_order.request",
            {
                "security": security,
                "amount": amount,
                "limit_price": limit_price,
            },
            "trading_service"
        )
        
        import uuid
        order_id = f"after_{uuid.uuid4().hex[:8]}"
        self._logger.info(f"After trading order request sent: {order_id}")
        return order_id
    
    def cancel_after_trading_order(self, order_id: str) -> bool:
        """取消盘后固定价委托"""
        # 发布盘后撤单请求事件
        self.publish_event(
            "live_trading.after_trading_cancel_order.request",
            {"order_id": order_id},
            "trading_service"
        )
        
        self._logger.info(f"After trading cancel order request sent: {order_id}")
        return True
    
    # ================================
    # 持仓和订单查询
    # ================================
    
    def get_position(self, security: str) -> Optional["Position"]:
        """获取实盘持仓信息"""
        return self.context.portfolio.positions.get(security)
    
    def get_positions(self, security_list: List[str]) -> Dict[str, Any]:
        """获取多个实盘持仓信息"""
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
    
    def get_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取实盘订单列表"""
        if not self.context.blotter:
            return []
        
        orders = []
        for order in self.context.blotter.orders.values():
            if security is None or order.symbol == security:
                orders.append(order)
        
        orders.sort(key=lambda o: o.dt, reverse=True)
        return orders
    
    def get_open_orders(self, security: Optional[str] = None) -> List["Order"]:
        """获取实盘未完成订单"""
        if not self.context.blotter:
            return []
        
        open_orders = []
        for order in self.context.blotter.orders.values():
            if order.status in ["new", "submitted", "partially_filled"]:
                if security is None or order.symbol == security:
                    open_orders.append(order)
        return open_orders
    
    def get_order(self, order_id: str) -> Optional["Order"]:
        """获取指定实盘订单"""
        if self.context.blotter:
            return self.context.blotter.get_order(order_id)
        return None
    
    def get_trades(self, security: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取实盘成交记录"""
        if not self.context.blotter:
            return []
        
        trades = []
        for order in self.context.blotter.orders.values():
            if order.status == "filled" and order.filled != 0:
                if security is None or order.symbol == security:
                    trades.append({
                        "order_id": order.id,
                        "security": order.symbol,
                        "amount": order.filled,
                        "price": order.limit or 0.0,
                        "filled_amount": order.filled,
                        "commission": 0.0,  # 实盘佣金由经纪商系统计算
                        "datetime": order.dt,
                        "side": "buy" if order.amount > 0 else "sell",
                    })
        
        trades.sort(key=lambda t: t["datetime"], reverse=True)
        return trades
    
    # ================================
    # 配置和参数管理
    # ================================
    
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """设置实盘交易策略参数"""
        # 存储在上下文中
        if not hasattr(self.context, "_parameters"):
            setattr(self.context, "_parameters", {})
        getattr(self.context, "_parameters").update(params)
        
        self._logger.info(f"Live trading parameters set: {params}")
        self.publish_event(
            "live_trading.parameters.updated",
            {"parameters": params},
            "trading_service"
        )
    
    def handle_data_update(self, data: Dict[str, Any]) -> None:
        """处理实盘数据更新"""
        # 更新当前价格数据
        for security, price_data in data.items():
            if security in self.context.portfolio.positions:
                position = self.context.portfolio.positions[security]
                position.last_sale_price = price_data.get(
                    "price", position.last_sale_price
                )
        
        # 更新投资组合价值
        self.context.portfolio.update_portfolio_value()
        
        # 发布数据更新事件
        self.publish_event(
            "live_trading.data.updated",
            {"data": data},
            "trading_service"
        )
    
    # ================================
    # 私有方法 - 内部业务逻辑
    # ================================
    
    def _validate_order_risk(
        self, 
        security: str, 
        amount: int, 
        limit_price: Optional[float]
    ) -> bool:
        """验证实盘交易订单风险"""
        # 基本参数检查
        if not security or amount == 0:
            self._logger.warning("Invalid order parameters")
            return False
        
        # 对于买入订单，检查资金是否充足（简化版检查）
        if amount > 0:
            price = limit_price or self._get_market_price(security)
            if price <= 0:
                self._logger.warning(f"Cannot get valid price for {security}")
                return False
            
            # 实盘交易中，资金检查通常由券商系统处理
            # 这里只做基本的逻辑检查
            estimated_cost = amount * price
            if self.context.portfolio.cash < estimated_cost:
                self._logger.warning(
                    f"Potential insufficient cash for {security}. "
                    f"Estimated cost: {estimated_cost:.2f}, "
                    f"Available: {self.context.portfolio.cash:.2f}"
                )
                # 实盘模式下不阻止订单，让券商系统最终决定
        
        # 对于卖出订单，检查持仓是否充足
        else:
            current_position = self.context.portfolio.positions.get(security)
            if not current_position or current_position.amount < abs(amount):
                self._logger.warning(
                    f"Potential insufficient position for {security}. "
                    f"Current: {current_position.amount if current_position else 0}, "
                    f"Requested: {abs(amount)}"
                )
                # 实盘模式下不阻止订单，让券商系统最终决定
        
        return True
    
    def _get_market_price(self, security: str) -> float:
        """获取实时市场价格"""
        # 在实盘交易中，需要从实时行情数据获取价格
        # 这里提供默认实现，实际使用时应该连接真实的行情数据源
        
        # 尝试从上下文获取当前价格
        if (
            hasattr(self.context, "current_data") 
            and security in self.context.current_data
        ):
            price_data = self.context.current_data[security]
            price = (
                price_data.get("price") 
                or price_data.get("last_price")
                or price_data.get("close", 0.0)
            )
            if price > 0:
                return float(price)
        
        # 如果无法获取实时价格，返回默认值（实际使用时应该报错）
        self._logger.warning(f"Using default price for {security} - should connect to real market data")
        return 10.0