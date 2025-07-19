# -*- coding: utf-8 -*-
"""
撮合引擎插件实现

提供多种撮合引擎插件，模拟不同的交易撮合逻辑：
- 深度撮合引擎：考虑订单深度的撮合
"""

import heapq
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from simtradelab.backtest.plugins.base import (
    BaseMatchingEngine,
    Fill,
    MarketData,
    Order,
    PluginMetadata,
)
from simtradelab.backtest.plugins.config import DepthMatchingEngineConfig


class DepthMatchingEngine(BaseMatchingEngine):
    """
    深度撮合引擎

    实现一个基于真实订单簿（LOB）的撮合引擎，能够处理部分成交和订单队列。
    """

    METADATA = PluginMetadata(
        name="depth_matching_engine",
        version="1.4.0",
        description="考虑订单深度的撮合引擎，支持高级订单类型",
        author="SimTradeLab",
        category="matching_engine",
        tags=[
            "backtest",
            "matching",
            "depth",
            "market_impact",
            "stop_order",
            "ioc",
            "fok",
            "trailing_stop",
        ],
    )
    config_model = DepthMatchingEngineConfig

    class _OrderBook:
        """内部订单簿类"""

        def __init__(self):
            self.bids = []  # 买单，大顶堆 (-price, timestamp, order)
            self.asks = []  # 卖单，小顶堆 (price, timestamp, order)
            self.stop_orders: List[Order] = []  # 待激活的止损单

        def add_order(self, order: Order, market_price: Optional[Decimal] = None):
            """添加订单到订单簿"""
            timestamp = order.timestamp or datetime.now()

            if order.order_type in ["stop", "stop_limit", "trailing_stop"]:
                self.stop_orders.append(order)
                return

            price = order.price if order.price is not None else market_price
            if price is None:
                return

            if order.side == "buy":
                heapq.heappush(self.bids, (-price, timestamp, order))
            else:  # sell
                heapq.heappush(self.asks, (price, timestamp, order))

        def get_best_bid(self):
            return self.bids[0] if self.bids else None

        def get_best_ask(self):
            return self.asks[0] if self.asks else None

    def __init__(
        self,
        metadata: PluginMetadata,
        config: Optional[DepthMatchingEngineConfig] = None,
    ):
        super().__init__(metadata, config)
        self._order_books: Dict[str, "DepthMatchingEngine._OrderBook"] = {}
        self._market_data_cache: Dict[str, Decimal] = {}

    def _on_initialize(self):
        """初始化撮合引擎状态"""
        self._order_books.clear()
        self._market_data_cache.clear()
        self.logger.info(f"{self.METADATA.name} initialized.")

    def _on_start(self):
        """启动撮合引擎"""
        self.logger.info(f"{self.METADATA.name} started.")

    def _on_stop(self):
        """停止撮合引擎，清理资源"""
        self._order_books.clear()
        self._market_data_cache.clear()
        self.logger.info(f"{self.METADATA.name} stopped and cleaned up.")

    def _get_order_book(self, symbol: str) -> "DepthMatchingEngine._OrderBook":
        """获取或创建指定标的的订单簿"""
        if symbol not in self._order_books:
            self._order_books[symbol] = self._OrderBook()
        return self._order_books[symbol]

    def _check_stop_orders(self, order_book: "_OrderBook", market_data: MarketData):
        """检查并激活止损单和跟踪止损单"""
        triggered_stop_orders = []
        remaining_stop_orders = []
        for stop_order in order_book.stop_orders:
            triggered = False
            if stop_order.order_type == "trailing_stop":
                if stop_order.trailing_reference_price is None:
                    if stop_order.side == "buy":
                        stop_order.trailing_reference_price = market_data.low_price
                    else:
                        stop_order.trailing_reference_price = market_data.high_price

                if stop_order.side == "buy":
                    stop_order.trailing_reference_price = min(
                        stop_order.trailing_reference_price, market_data.low_price
                    )
                    if stop_order.trail_amount:
                        stop_order.trigger_price = (
                            stop_order.trailing_reference_price
                            + stop_order.trail_amount
                        )
                    elif stop_order.trail_percent:
                        stop_order.trigger_price = (
                            stop_order.trailing_reference_price
                            * (Decimal("1") + stop_order.trail_percent)
                        )
                else:
                    stop_order.trailing_reference_price = max(
                        stop_order.trailing_reference_price, market_data.high_price
                    )
                    if stop_order.trail_amount:
                        stop_order.trigger_price = (
                            stop_order.trailing_reference_price
                            - stop_order.trail_amount
                        )
                    elif stop_order.trail_percent:
                        stop_order.trigger_price = (
                            stop_order.trailing_reference_price
                            * (Decimal("1") - stop_order.trail_percent)
                        )

            if stop_order.trigger_price is not None:
                if (
                    stop_order.side == "buy"
                    and market_data.close_price >= stop_order.trigger_price
                ) or (
                    stop_order.side == "sell"
                    and market_data.close_price <= stop_order.trigger_price
                ):
                    triggered_stop_orders.append(stop_order)
                    triggered = True

            if not triggered:
                remaining_stop_orders.append(stop_order)

        order_book.stop_orders = remaining_stop_orders

        for order in triggered_stop_orders:
            order.status = "active"
            if order.order_type in ["stop", "trailing_stop"]:
                order.order_type = "market"
            elif order.order_type == "stop_limit":
                order.order_type = "limit"
            order_book.add_order(order, market_data.close_price)

    def add_order(self, order: Order) -> None:
        order_book = self._get_order_book(order.symbol)
        market_price = self._market_data_cache.get(order.symbol, order.price)
        order.status = "active"
        order_book.add_order(order, market_price)

    def trigger_matching(
        self, symbol: str, market_data: MarketData
    ) -> Tuple[List[Fill], List[Order]]:
        self._market_data_cache[symbol] = market_data.close_price
        order_book = self._get_order_book(symbol)
        self._check_stop_orders(order_book, market_data)

        fills: List[Fill] = []
        filled_orders: List[Order] = []

        while order_book.bids and order_book.asks:
            best_bid_price = -order_book.bids[0][0]
            best_ask_price = order_book.asks[0][0]

            # 如果最优买价小于最优卖价，则无法撮合，退出循环
            if best_bid_price < best_ask_price:
                break

            # 只有在价格可匹配时才弹出订单
            bid_price, bid_ts, bid_order = heapq.heappop(order_book.bids)
            ask_price, ask_ts, ask_order = heapq.heappop(order_book.asks)

            fill_price = best_ask_price  # 通常使用卖方价格作为成交价
            fill_qty = min(bid_order.quantity, ask_order.quantity)

            if fill_qty <= 0:  # 避免0数量成交
                # 将未成交的订单放回，因为它们可能与其他订单匹配
                heapq.heappush(order_book.bids, (bid_price, bid_ts, bid_order))
                heapq.heappush(order_book.asks, (ask_price, ask_ts, ask_order))
                break  # 如果数量为0，通常意味着订单有问题，终止撮合

            # FOK 订单检查
            if bid_order.time_in_force == "fok" and fill_qty < bid_order.quantity:
                bid_order.status = "cancelled"
                filled_orders.append(bid_order)
                heapq.heappush(
                    order_book.asks, (ask_price, ask_ts, ask_order)
                )  # 将对手单放回
                continue

            if ask_order.time_in_force == "fok" and fill_qty < ask_order.quantity:
                ask_order.status = "cancelled"
                filled_orders.append(ask_order)
                heapq.heappush(
                    order_book.bids, (bid_price, bid_ts, bid_order)
                )  # 将对手单放回
                continue

            # 创建成交记录
            buy_fill = Fill(
                order_id=bid_order.order_id,
                symbol=symbol,
                side="buy",
                quantity=fill_qty,
                price=fill_price,
                timestamp=datetime.now(),
            )
            sell_fill = Fill(
                order_id=ask_order.order_id,
                symbol=symbol,
                side="sell",
                quantity=fill_qty,
                price=fill_price,
                timestamp=datetime.now(),
            )

            # 计算佣金和滑点
            if self._commission_model:
                buy_fill.commission = self._commission_model.calculate_commission(
                    buy_fill
                )
                sell_fill.commission = self._commission_model.calculate_commission(
                    sell_fill
                )

            if self._slippage_model:
                buy_fill.slippage = self._slippage_model.calculate_slippage(
                    bid_order, market_data, fill_price
                )
                sell_fill.slippage = self._slippage_model.calculate_slippage(
                    ask_order, market_data, fill_price
                )

            fills.append(buy_fill)
            fills.append(sell_fill)

            # 更新订单状态
            bid_order.filled_quantity += fill_qty
            ask_order.filled_quantity += fill_qty
            bid_order.quantity -= fill_qty
            ask_order.quantity -= fill_qty

            # 处理剩余订单
            if bid_order.quantity > 0:
                if bid_order.time_in_force == "ioc":
                    bid_order.status = "cancelled"  # IOC 未完全成交的部分被取消
                    filled_orders.append(bid_order)
                else:
                    # 将部分成交的买单重新放回订单簿
                    heapq.heappush(order_book.bids, (bid_price, bid_ts, bid_order))
            else:
                bid_order.status = "filled"
                filled_orders.append(bid_order)

            if ask_order.quantity > 0:
                if ask_order.time_in_force == "ioc":
                    ask_order.status = "cancelled"  # IOC 未完全成交的部分被取消
                    filled_orders.append(ask_order)
                else:
                    # 将部分成交的卖单重新放回订单簿
                    heapq.heappush(order_book.asks, (ask_price, ask_ts, ask_order))
            else:
                ask_order.status = "filled"
                filled_orders.append(ask_order)

        return fills, filled_orders
