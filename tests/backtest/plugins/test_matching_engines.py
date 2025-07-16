# -*- coding: utf-8 -*-
"""
撮合引擎单元测试

全面测试 DepthMatchingEngine 的所有核心功能和边界情况。
"""

from datetime import datetime
from decimal import Decimal
from typing import List

import pytest

from simtradelab.backtest.plugins.base import Fill, MarketData, Order, PluginMetadata
from simtradelab.backtest.plugins.config import DepthMatchingEngineConfig
from simtradelab.backtest.plugins.matching_engines import DepthMatchingEngine

# region Fixtures


@pytest.fixture
def metadata() -> PluginMetadata:
    """提供一个标准的插件元数据实例。"""
    return PluginMetadata(
        name="TestEngine",
        version="1.0",
        description="A test matching engine.",
        author="Test",
        category="test_category",
        tags=["test"],
    )


@pytest.fixture
def engine_config() -> DepthMatchingEngineConfig:
    """提供一个深度撮合引擎的默认配置。"""
    return DepthMatchingEngineConfig()


@pytest.fixture
def matching_engine(
    metadata: PluginMetadata, engine_config: DepthMatchingEngineConfig
) -> DepthMatchingEngine:
    """提供一个全新的 DepthMatchingEngine 实例，并执行初始化。"""
    engine = DepthMatchingEngine(metadata=metadata, config=engine_config)
    engine._on_initialize()
    return engine


@pytest.fixture
def sample_market_data() -> MarketData:
    """提供一个样本市场数据。"""
    return MarketData(
        symbol="TEST",
        timestamp=datetime.now(),
        open_price=Decimal("100"),
        high_price=Decimal("105"),
        low_price=Decimal("95"),
        close_price=Decimal("102"),
        volume=Decimal("10000"),
    )


# endregion

# region Test Cases


def test_engine_initialization(matching_engine: DepthMatchingEngine):
    """
    测试: 验证撮合引擎是否能被成功初始化。
    预期: 引擎实例不应为 None，且内部订单簿为空。
    """
    assert matching_engine is not None
    assert not matching_engine._order_books


def test_add_single_buy_order(matching_engine: DepthMatchingEngine):
    """
    测试: 向引擎中添加一个买单。
    预期: 订单被正确添加到对应标的的订单簿的买单队列中。
    """
    order = Order(
        order_id="buy1",
        symbol="TEST",
        side="buy",
        quantity=Decimal("10"),
        price=Decimal("100"),
        order_type="limit",
    )
    matching_engine.add_order(order)

    order_book = matching_engine._get_order_book("TEST")
    assert len(order_book.bids) == 1
    assert len(order_book.asks) == 0

    best_bid = order_book.get_best_bid()
    assert best_bid is not None
    assert best_bid[2] == order  # best_bid is a tuple (-price, timestamp, order)
    assert order.price is not None
    assert best_bid[0] == -order.price


def test_add_single_sell_order(matching_engine: DepthMatchingEngine):
    """
    测试: 向引擎中添加一个卖单。
    预期: 订单被正确添加到对应标的的订单簿的卖单队列中。
    """
    order = Order(
        order_id="sell1",
        symbol="TEST",
        side="sell",
        quantity=Decimal("10"),
        price=Decimal("101"),
        order_type="limit",
    )
    matching_engine.add_order(order)

    order_book = matching_engine._get_order_book("TEST")
    assert len(order_book.bids) == 0
    assert len(order_book.asks) == 1

    best_ask = order_book.get_best_ask()
    assert best_ask is not None
    assert best_ask[2] == order  # best_ask is a tuple (price, timestamp, order)
    assert best_ask[0] == order.price


def test_add_multiple_orders_different_symbols(matching_engine: DepthMatchingEngine):
    """
    测试: 添加多个不同标的的订单。
    预期: 引擎为每个标的创建独立的订单簿。
    """
    order1 = Order(
        order_id="order1",
        symbol="STOCK_A",
        side="buy",
        quantity=Decimal("10"),
        price=Decimal("50"),
    )
    order2 = Order(
        order_id="order2",
        symbol="STOCK_B",
        side="sell",
        quantity=Decimal("20"),
        price=Decimal("75"),
    )

    matching_engine.add_order(order1)
    matching_engine.add_order(order2)

    assert "STOCK_A" in matching_engine._order_books
    assert "STOCK_B" in matching_engine._order_books

    book_a = matching_engine._get_order_book("STOCK_A")
    book_b = matching_engine._get_order_book("STOCK_B")

    assert len(book_a.bids) == 1
    assert len(book_a.asks) == 0
    assert len(book_b.bids) == 0
    assert len(book_b.asks) == 1


# endregion


def test_simple_match_full_fill(
    matching_engine: DepthMatchingEngine, sample_market_data: MarketData
):
    """
    测试: 简单撮合场景，买单和卖单完全成交。
    预期: 双方订单都被填充，生成两条成交记录，订单簿清空。
    """
    buy_order = Order(
        order_id="buy1",
        symbol="TEST",
        side="buy",
        quantity=Decimal("10"),
        price=Decimal("102"),
        order_type="limit",
    )
    sell_order = Order(
        order_id="sell1",
        symbol="TEST",
        side="sell",
        quantity=Decimal("10"),
        price=Decimal("101"),
        order_type="limit",
    )

    matching_engine.add_order(buy_order)
    matching_engine.add_order(sell_order)

    fills, filled_orders = matching_engine.trigger_matching("TEST", sample_market_data)

    assert len(fills) == 2
    assert len(filled_orders) == 2

    # 验证成交记录
    buy_fill = next(f for f in fills if f.side == "buy")
    sell_fill = next(f for f in fills if f.side == "sell")

    assert buy_fill.quantity == Decimal("10")
    assert sell_fill.quantity == Decimal("10")
    assert buy_fill.price == Decimal("101")  # 成交价应为卖方报价
    assert sell_fill.price == Decimal("101")

    # 验证订单状态
    assert buy_order.status == "filled"
    assert sell_order.status == "filled"
    assert buy_order.filled_quantity == Decimal("10")
    assert sell_order.filled_quantity == Decimal("10")

    # 验证订单簿
    order_book = matching_engine._get_order_book("TEST")
    assert len(order_book.bids) == 0
    assert len(order_book.asks) == 0


def test_partial_fill_match(
    matching_engine: DepthMatchingEngine, sample_market_data: MarketData
):
    """
    测试: 部分成交场景。买单数量大于卖单。
    预期: 卖单完全成交，买单部分成交，订单簿中留下剩余的买单。
    """
    buy_order = Order(
        order_id="buy1",
        symbol="TEST",
        side="buy",
        quantity=Decimal("20"),
        price=Decimal("102"),
        order_type="limit",
    )
    sell_order = Order(
        order_id="sell1",
        symbol="TEST",
        side="sell",
        quantity=Decimal("10"),
        price=Decimal("101"),
        order_type="limit",
    )

    matching_engine.add_order(buy_order)
    matching_engine.add_order(sell_order)

    fills, filled_orders = matching_engine.trigger_matching("TEST", sample_market_data)

    assert len(fills) == 2
    assert len(filled_orders) == 1  # 只有卖单被完全填充

    # 验证成交记录
    buy_fill = next(f for f in fills if f.side == "buy")
    sell_fill = next(f for f in fills if f.side == "sell")

    assert buy_fill.quantity == Decimal("10")
    assert sell_fill.quantity == Decimal("10")
    assert buy_fill.price == Decimal("101")

    # 验证订单状态
    assert buy_order.status == "active"  # 仍有剩余，状态应为 active
    assert sell_order.status == "filled"
    assert buy_order.quantity == Decimal("10")  # 剩余数量
    assert buy_order.filled_quantity == Decimal("10")
    assert sell_order.filled_quantity == Decimal("10")

    # 验证订单簿
    order_book = matching_engine._get_order_book("TEST")
    assert len(order_book.bids) == 1
    assert len(order_book.asks) == 0

    remaining_bid = order_book.bids[0][2]
    assert remaining_bid.order_id == "buy1"
    assert remaining_bid.quantity == Decimal("10")


def test_price_time_priority(
    matching_engine: DepthMatchingEngine, sample_market_data: MarketData
):
    """
    测试: 价格优先和时间优先原则。
    预期: 价格更优的订单先成交；同价订单中，时间更早的先成交。
    """
    # 价格不同，sell_order_1 价格更优
    sell_order_1 = Order(
        order_id="sell1",
        symbol="TEST",
        side="sell",
        quantity=Decimal("5"),
        price=Decimal("101"),
        order_type="limit",
        timestamp=datetime(2023, 1, 1, 12, 0, 1),
    )
    sell_order_2 = Order(
        order_id="sell2",
        symbol="TEST",
        side="sell",
        quantity=Decimal("5"),
        price=Decimal("102"),
        order_type="limit",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )

    # 价格相同，buy_order_1 时间更早
    buy_order_1 = Order(
        order_id="buy1",
        symbol="TEST",
        side="buy",
        quantity=Decimal("5"),
        price=Decimal("102"),
        order_type="limit",
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
    )
    buy_order_2 = Order(
        order_id="buy2",
        symbol="TEST",
        side="buy",
        quantity=Decimal("5"),
        price=Decimal("102"),
        order_type="limit",
        timestamp=datetime(2023, 1, 1, 12, 0, 1),
    )

    matching_engine.add_order(sell_order_1)
    matching_engine.add_order(sell_order_2)
    matching_engine.add_order(buy_order_1)
    matching_engine.add_order(buy_order_2)

    fills, filled_orders = matching_engine.trigger_matching("TEST", sample_market_data)

    # 预期应该发生两次匹配，总共4个fill记录和4个完全成交的订单
    assert len(fills) == 4, "Expected two matches, resulting in 4 fills"
    assert len(filled_orders) == 4, "Expected all four orders to be filled"

    filled_order_ids = {order.order_id for order in filled_orders}
    assert filled_order_ids == {"buy1", "buy2", "sell1", "sell2"}

    # 验证成交细节，确保价格和时间优先
    # 第一次撮合: buy1 (102, t0) vs sell1 (101, t1). 成交价应为卖价 101.
    # 第二次撮合: buy2 (102, t1) vs sell2 (102, t0). 成交价应为卖价 102.

    buy1_fill = next((f for f in fills if f.order_id == "buy1"), None)
    sell1_fill = next((f for f in fills if f.order_id == "sell1"), None)
    buy2_fill = next((f for f in fills if f.order_id == "buy2"), None)
    sell2_fill = next((f for f in fills if f.order_id == "sell2"), None)

    assert buy1_fill is not None, "Fill for buy1 not found"
    assert sell1_fill is not None, "Fill for sell1 not found"
    assert buy2_fill is not None, "Fill for buy2 not found"
    assert sell2_fill is not None, "Fill for sell2 not found"

    # 检查第一次撮合 (价格优先)
    assert buy1_fill.price == Decimal("101")
    assert sell1_fill.price == Decimal("101")
    assert buy1_fill.quantity == Decimal("5")
    assert sell1_fill.quantity == Decimal("5")

    # 检查第二次撮合 (同价，时间优先)
    assert buy2_fill.price == Decimal("102")
    assert sell2_fill.price == Decimal("102")
    assert buy2_fill.quantity == Decimal("5")
    assert sell2_fill.quantity == Decimal("5")

    # 验证订单簿最终为空
    order_book = matching_engine._get_order_book("TEST")
    assert len(order_book.bids) == 0
    assert len(order_book.asks) == 0


def test_ioc_order_partial_fill_and_cancel(
    matching_engine: DepthMatchingEngine, sample_market_data: MarketData
):
    """
    测试: IOC 订单部分成交并立即取消剩余部分。
    预期: IOC 订单成交可成交部分，剩余数量被取消，订单状态为 'cancelled'。
    """
    ioc_buy_order = Order(
        order_id="ioc_buy",
        symbol="TEST",
        side="buy",
        quantity=Decimal("20"),
        price=Decimal("102"),
        order_type="limit",
        time_in_force="ioc",
    )
    sell_order = Order(
        order_id="sell1",
        symbol="TEST",
        side="sell",
        quantity=Decimal("10"),
        price=Decimal("101"),
        order_type="limit",
    )

    matching_engine.add_order(ioc_buy_order)
    matching_engine.add_order(sell_order)

    fills, filled_orders = matching_engine.trigger_matching("TEST", sample_market_data)

    assert len(fills) == 2
    # ioc_buy_order 和 sell_order 都会进入 filled_orders 列表
    assert len(filled_orders) == 2

    buy_fill = next(f for f in fills if f.side == "buy")
    assert buy_fill.quantity == Decimal("10")

    # 验证 IOC 订单的状态
    assert ioc_buy_order.status == "cancelled"
    assert ioc_buy_order.filled_quantity == Decimal("10")
    assert ioc_buy_order.quantity == Decimal("10")  # 剩余数量

    # 验证对手单的状态
    assert sell_order.status == "filled"
    assert sell_order.filled_quantity == Decimal("10")

    # 验证订单簿
    order_book = matching_engine._get_order_book("TEST")
    assert len(order_book.bids) == 0
    assert len(order_book.asks) == 0
