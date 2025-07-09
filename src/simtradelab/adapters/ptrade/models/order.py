# -*- coding: utf-8 -*-
"""
PTrade订单和订单管理模型
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Order:
    """订单对象 - 完全符合PTrade规范"""

    id: str  # 订单号
    dt: datetime  # 订单产生时间
    symbol: str  # 标的代码（注意：标的代码尾缀为四位，上证为XSHG，深圳为XSHE）
    amount: int  # 下单数量，买入是正数，卖出是负数
    limit: Optional[float] = None  # 指定价格
    status: str = "new"  # 订单状态
    filled: int = 0  # 成交数量

    def __post_init__(self) -> None:
        self.security = self.symbol
        self.limit_price = self.limit
        self.created_at = self.dt


class Blotter:
    """订单记录管理器"""

    def __init__(self) -> None:
        self.orders: Dict[str, Order] = {}
        self.order_id_counter = 0
        self.current_dt = datetime.now()  # 当前单位时间的开始时间

    def create_order(
        self, security: str, amount: int, limit_price: Optional[float] = None
    ) -> str:
        """创建订单"""
        order_id = f"order_{self.order_id_counter}"
        self.order_id_counter += 1

        order = Order(
            id=order_id,
            dt=self.current_dt,
            symbol=security,
            amount=amount,
            limit=limit_price,
        )

        self.orders[order_id] = order
        return order_id

    def get_order(self, order_id: str) -> Optional[Order]:
        """获取订单"""
        return self.orders.get(order_id)

    def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        if order_id in self.orders:
            self.orders[order_id].status = "cancelled"
            return True
        return False