# -*- coding: utf-8 -*-
"""
CloudEvent使用示例

演示如何在SimTradeLab v5.0中使用CNCF CloudEvents标准事件模型：
1. 创建CloudEvent事件
2. 使用EventBus发布和订阅CloudEvent
3. 事件契约使用
4. 向后兼容性
"""

import asyncio

from simtradelab.core.event_bus import EventBus
from simtradelab.core.events.cloud_event import CloudEvent
from simtradelab.core.events.contracts import (
    create_order_created_event,
    create_plugin_loaded_event,
    create_system_start_event,
)


def basic_cloud_event_usage():
    """基本CloudEvent使用示例"""
    print("=== 基本CloudEvent使用示例 ===")

    # 1. 创建最简单的CloudEvent
    event = CloudEvent(type="com.simtradelab.strategy.signal", source="MACDStrategy")
    print(f"创建事件: {event.type} from {event.source}")
    print(f"事件ID: {event.id}")
    print(f"时间戳: {event.time}")

    # 2. 创建包含数据的CloudEvent
    trading_signal = CloudEvent(
        type="com.simtradelab.strategy.signal",
        source="MACDStrategy",
        data={
            "symbol": "000001.XSHE",
            "action": "BUY",
            "quantity": 1000,
            "price": 15.68,
            "confidence": 0.85,
        },
        priority=2,  # 高优先级
        tags={"strategy": "MACD", "signal_type": "golden_cross"},
    )

    print("\n交易信号事件:")
    print(f"  类型: {trading_signal.type}")
    print(f"  数据: {trading_signal.data}")
    print(f"  优先级: {trading_signal.priority}")
    print(f"  标签: {trading_signal.tags}")


def event_bus_integration():
    """EventBus集成示例"""
    print("\n=== EventBus集成示例 ===")

    event_bus = EventBus()

    # 1. 定义CloudEvent处理器
    def cloud_event_handler(event: CloudEvent):
        print(f"CloudEvent处理器收到: {event.type}")
        print(f"  数据: {event.data}")
        return f"processed_{event.id}"

    # 2. 定义传统Event处理器（向后兼容）
    def legacy_handler(event):
        print(f"传统处理器收到: {event.type}")
        print(f"  数据: {event.data}")
        return f"legacy_processed_{event.event_id}"

    # 3. 订阅事件（EventBus自动检测处理器类型）
    event_bus.subscribe("test.event", cloud_event_handler)
    event_bus.subscribe("test.event", legacy_handler)

    # 4. 发布CloudEvent
    cloud_event = CloudEvent(
        type="test.event", source="TestSource", data={"message": "Hello CloudEvent!"}
    )

    results = event_bus.publish_cloud_event(cloud_event)
    print(f"处理结果: {results}")

    # 5. 使用传统publish方法（自动转换为CloudEvent）
    legacy_results = event_bus.publish(
        "test.event", data={"message": "Hello from legacy!"}, source="LegacySource"
    )
    print(f"传统发布结果: {legacy_results}")

    event_bus.shutdown()


def event_contracts_usage():
    """事件契约使用示例"""
    print("\n=== 事件契约使用示例 ===")

    # 1. 使用预定义的系统事件
    system_start = create_system_start_event(version="5.0")
    print(f"系统启动事件: {system_start.type}")
    print(f"  版本: {system_start.data['version']}")
    print(f"  优先级: {system_start.priority}")

    # 2. 使用预定义的插件事件
    plugin_loaded = create_plugin_loaded_event(
        "TechnicalIndicators", "1.2.0", load_time_ms=156.7
    )
    print(f"\n插件加载事件: {plugin_loaded.type}")
    print(f"  插件名: {plugin_loaded.data['plugin_name']}")
    print(f"  版本: {plugin_loaded.data['version']}")
    print(f"  加载时间: {plugin_loaded.data['load_time_ms']}ms")

    # 3. 使用预定义的交易事件
    order_event = create_order_created_event(
        order_id="ORD20240101001",
        symbol="000001.XSHE",
        amount=1000.0,
        price=15.68,
        strategy="MACDStrategy",
    )
    print(f"\n订单创建事件: {order_event.type}")
    print(f"  订单ID: {order_event.data['order_id']}")
    print(f"  股票代码: {order_event.data['symbol']}")
    print(f"  数量: {order_event.data['amount']}")


def correlation_and_tags():
    """关联和标签使用示例"""
    print("\n=== 关联和标签使用示例 ===")

    # 1. 创建父事件
    parent_event = CloudEvent(
        type="com.simtradelab.strategy.analysis_start",
        source="StrategyEngine",
        correlation_id="analysis_session_001",
        data={"symbols": ["000001.XSHE", "000002.XSHE"]},
        tags={"session": "morning", "type": "backtest"},
    )

    print(f"父事件: {parent_event.type}")
    print(f"关联ID: {parent_event.correlation_id}")

    # 2. 创建关联的子事件
    child_event = parent_event.create_correlated_event(
        "com.simtradelab.strategy.signal_generated",
        data={"symbol": "000001.XSHE", "signal": "BUY", "confidence": 0.92},
    )

    print(f"\n子事件: {child_event.type}")
    print(f"关联ID: {child_event.correlation_id}")  # 继承父事件的关联ID
    print(f"数据: {child_event.data}")

    # 3. 标签管理
    child_event.add_tag("signal_strength", "strong")
    child_event.add_tag("market_condition", "bullish")

    print(f"标签: {child_event.tags}")
    print(f"是否有signal_strength标签: {child_event.has_tag('signal_strength')}")
    print(
        f"signal_strength值是否为strong: {child_event.has_tag('signal_strength', 'strong')}"
    )


async def async_event_processing():
    """异步事件处理示例"""
    print("\n=== 异步事件处理示例 ===")

    event_bus = EventBus()

    # 异步处理器
    async def async_processor(event: CloudEvent):
        print(f"异步处理开始: {event.type}")
        await asyncio.sleep(0.1)  # 模拟异步操作
        print(f"异步处理完成: {event.type}")
        return f"async_result_{event.id[:8]}"

    # 同步处理器
    def sync_processor(event: CloudEvent):
        print(f"同步处理: {event.type}")
        return f"sync_result_{event.id[:8]}"

    # 订阅
    event_bus.subscribe("async.test", async_processor)
    event_bus.subscribe("async.test", sync_processor)

    # 异步发布
    event = CloudEvent(
        type="async.test", source="AsyncDemo", data={"test": "async processing"}
    )

    results = await event_bus.publish_cloud_event_async(event)
    print(f"异步处理结果: {results}")

    event_bus.shutdown()


def legacy_compatibility():
    """向后兼容性示例"""
    print("\n=== 向后兼容性示例 ===")

    # 1. 创建CloudEvent
    cloud_event = CloudEvent(
        type="test.compatibility",
        source="TestSource",
        data={"message": "CloudEvent data"},
        priority=3,
        correlation_id="test_correlation",
        tags={"env": "test"},
    )

    # 2. 转换为旧格式
    legacy_dict = cloud_event.to_legacy_event()
    print("转换为旧格式:")
    print(f"  类型: {legacy_dict['type']}")
    print(f"  数据: {legacy_dict['data']}")
    print(f"  事件ID: {legacy_dict['event_id']}")
    print(f"  时间戳: {legacy_dict['timestamp']}")
    print(f"  元数据: {legacy_dict['metadata']}")

    # 3. 从旧格式重建CloudEvent
    rebuilt_event = CloudEvent.from_legacy_event(legacy_dict)
    print("\n重建的CloudEvent:")
    print(f"  类型: {rebuilt_event.type}")
    print(f"  数据: {rebuilt_event.data}")
    print(f"  优先级: {rebuilt_event.priority}")
    print(f"  关联ID: {rebuilt_event.correlation_id}")


def main():
    """主示例函数"""
    print("SimTradeLab v5.0 CloudEvent使用示例")
    print("=" * 50)

    # 运行各种示例
    basic_cloud_event_usage()
    event_bus_integration()
    event_contracts_usage()
    correlation_and_tags()
    legacy_compatibility()

    # 运行异步示例
    print("\n运行异步示例...")
    asyncio.run(async_event_processing())

    print("\n" + "=" * 50)
    print("CloudEvent示例演示完成!")


if __name__ == "__main__":
    main()
