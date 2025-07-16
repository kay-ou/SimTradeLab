# -*- coding: utf-8 -*-
"""
撮合引擎插件实现

提供多种撮合引擎插件，模拟不同的交易撮合逻辑：
- 简单撮合引擎：基本的价格撮合
- 深度撮合引擎：考虑订单深度的撮合
- 限价撮合引擎：严格的限价单撮合
"""

import heapq
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from .base import (
    BaseCommissionModel,
    BaseMatchingEngine,
    BaseSlippageModel,
    Fill,
    MarketData,
    Order,
    PluginMetadata,
)
from .config import (
    DepthMatchingEngineConfig,
    LimitMatchingEngineConfig,
    SimpleMatchingEngineConfig,
)


class SimpleMatchingEngine(BaseMatchingEngine):
    """
    简单撮合引擎 (将被废弃)

    实现基本的价格撮合逻辑，并集成滑点和手续费计算。
    """

    METADATA = PluginMetadata(
        name="SimpleMatchingEngine",
        version="1.1.0",
        description="[DEPRECATED] 基本的价格撮合引擎，集成成本计算",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "simple", "deprecated"],
    )

    config_model = SimpleMatchingEngineConfig

    def add_order(self, order: Order) -> None:
        raise NotImplementedError(
            "SimpleMatchingEngine is deprecated. Use DepthMatchingEngine instead."
        )

    def trigger_matching(
        self, symbol: str, market_data: MarketData
    ) -> Tuple[List[Fill], List[Order]]:
        raise NotImplementedError(
            "SimpleMatchingEngine is deprecated. Use DepthMatchingEngine instead."
        )


class DepthMatchingEngine(BaseMatchingEngine):
    """
    深度撮合引擎

    实现一个基于真实订单簿（LOB）的撮合引擎，能够处理部分成交和订单队列。
    """

    METADATA = PluginMetadata(
        name="DepthMatchingEngine",
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
        slippage_model: Optional[BaseSlippageModel] = None,
        commission_model: Optional[BaseCommissionModel] = None,
    ):
        super().__init__(metadata, config, slippage_model, commission_model)
        self._order_books: Dict[str, "DepthMatchingEngine._OrderBook"] = {}
        self._market_data_cache: Dict[str, Decimal] = {}

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

            if best_bid_price < best_ask_price:
                break

            bid_price, bid_ts, bid_order = heapq.heappop(order_book.bids)
            ask_price, ask_ts, ask_order = heapq.heappop(order_book.asks)

            fill_price = best_ask_price
            fill_qty = min(bid_order.quantity, ask_order.quantity)

            if fill_qty <= 0:
                continue

            # 如果买单是FOK订单且不能完全成交，则取消该订单，并将卖单放回队列
            if bid_order.time_in_force == "fok" and fill_qty < bid_order.quantity:
                bid_order.status = "cancelled"
                filled_orders.append(bid_order)
                heapq.heappush(
                    order_book.asks, (ask_price, ask_ts, ask_order)
                )  # 只把对手单放回去
                continue

            # 如果卖单是FOK订单且不能完全成交，则取消该订单，并将买单放回队列
            if ask_order.time_in_force == "fok" and fill_qty < ask_order.quantity:
                ask_order.status = "cancelled"
                filled_orders.append(ask_order)
                heapq.heappush(
                    order_book.bids, (bid_price, bid_ts, bid_order)
                )  # 只把对手单放回去
                continue

            fills.append(
                Fill(
                    order_id=bid_order.order_id,
                    symbol=symbol,
                    side="buy",
                    quantity=fill_qty,
                    price=fill_price,
                    timestamp=datetime.now(),
                )
            )
            fills.append(
                Fill(
                    order_id=ask_order.order_id,
                    symbol=symbol,
                    side="sell",
                    quantity=fill_qty,
                    price=fill_price,
                    timestamp=datetime.now(),
                )
            )

            bid_order.quantity -= fill_qty
            ask_order.quantity -= fill_qty

            if bid_order.quantity > 0:
                if bid_order.time_in_force == "ioc":
                    bid_order.status = "cancelled"
                    filled_orders.append(bid_order)
                else:
                    heapq.heappush(order_book.bids, (bid_price, bid_ts, bid_order))
            else:
                bid_order.status = "filled"
                filled_orders.append(bid_order)

            if ask_order.quantity > 0:
                if ask_order.time_in_force == "ioc":
                    ask_order.status = "cancelled"
                    filled_orders.append(ask_order)
                else:
                    heapq.heappush(order_book.asks, (ask_price, ask_ts, ask_order))
            else:
                ask_order.status = "filled"
                filled_orders.append(ask_order)

        return fills, filled_orders


class StrictLimitMatchingEngine(BaseMatchingEngine):
    """
    严格限价撮合引擎
    """

    METADATA = PluginMetadata(
        name="StrictLimitMatchingEngine",
        version="1.0.0",
        description="严格的限价单撮合引擎",
        author="SimTradeLab",
        category="matching_engine",
        tags=["backtest", "matching", "limit", "strict"],
    )
    config_model = LimitMatchingEngineConfig

    def add_order(self, order: Order) -> None:
        raise NotImplementedError(
            "StrictLimitMatchingEngine has not been refactored yet."
        )

    def trigger_matching(
        self, symbol: str, market_data: MarketData
    ) -> Tuple[List[Fill], List[Order]]:
        raise NotImplementedError(
            "StrictLimitMatchingEngine has not been refactored yet."
        )
