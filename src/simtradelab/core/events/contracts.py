# -*- coding: utf-8 -*-
"""
核心事件契约定义

定义 SimTradeLab 系统中的标准事件类型和负载格式，
确保插件间通信的一致性和可预测性。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .cloud_event import CloudEvent


class CoreEventContracts:
    """
    核心事件契约常量定义

    定义了系统核心事件的类型、优先级和标准负载格式。
    所有插件开发者都应遵循这些契约来保证事件的标准化。
    """

    # 系统级事件
    SYSTEM_START = "com.simtradelab.system.start"
    SYSTEM_STOP = "com.simtradelab.system.stop"
    SYSTEM_ERROR = "com.simtradelab.system.error"

    # 插件生命周期事件
    PLUGIN_LOADED = "com.simtradelab.plugin.loaded"
    PLUGIN_UNLOADED = "com.simtradelab.plugin.unloaded"
    PLUGIN_STARTED = "com.simtradelab.plugin.started"
    PLUGIN_STOPPED = "com.simtradelab.plugin.stopped"
    PLUGIN_ERROR = "com.simtradelab.plugin.error"
    PLUGIN_RELOADED = "com.simtradelab.plugin.reloaded"

    # 配置管理事件
    CONFIG_CHANGED = "com.simtradelab.config.changed"
    CONFIG_VALIDATED = "com.simtradelab.config.validated"
    CONFIG_ERROR = "com.simtradelab.config.error"

    # 交易相关事件
    ORDER_CREATED = "com.simtradelab.trade.order.created"
    ORDER_FILLED = "com.simtradelab.trade.order.filled"
    ORDER_CANCELLED = "com.simtradelab.trade.order.cancelled"
    ORDER_ERROR = "com.simtradelab.trade.order.error"

    # 风险控制事件
    RISK_ALERT = "com.simtradelab.risk.alert"
    RISK_BREACH = "com.simtradelab.risk.breach"
    RISK_CHECK_PASSED = "com.simtradelab.risk.check.passed"

    # 数据相关事件
    DATA_RECEIVED = "com.simtradelab.data.received"
    DATA_ERROR = "com.simtradelab.data.error"
    DATA_SOURCE_CONNECTED = "com.simtradelab.data.source.connected"
    DATA_SOURCE_DISCONNECTED = "com.simtradelab.data.source.disconnected"

    # 回测相关事件
    BACKTEST_STARTED = "com.simtradelab.backtest.started"
    BACKTEST_COMPLETED = "com.simtradelab.backtest.completed"
    BACKTEST_ERROR = "com.simtradelab.backtest.error"

    # 优先级映射
    EVENT_PRIORITIES = {
        # 系统级事件 - 最高优先级
        SYSTEM_START: 1,
        SYSTEM_STOP: 1,
        SYSTEM_ERROR: 1,
        # 风险控制 - 高优先级
        RISK_ALERT: 2,
        RISK_BREACH: 1,
        RISK_CHECK_PASSED: 4,
        # 交易事件 - 高优先级
        ORDER_FILLED: 2,
        ORDER_CREATED: 3,
        ORDER_CANCELLED: 3,
        ORDER_ERROR: 2,
        # 数据错误 - 中高优先级
        DATA_ERROR: 3,
        DATA_SOURCE_DISCONNECTED: 3,
        # 插件生命周期 - 中等优先级
        PLUGIN_LOADED: 5,
        PLUGIN_UNLOADED: 5,
        PLUGIN_STARTED: 5,
        PLUGIN_STOPPED: 5,
        PLUGIN_ERROR: 3,
        PLUGIN_RELOADED: 5,
        # 配置变更 - 中等优先级
        CONFIG_CHANGED: 4,
        CONFIG_VALIDATED: 6,
        CONFIG_ERROR: 3,
        # 数据接收 - 较低优先级
        DATA_RECEIVED: 6,
        DATA_SOURCE_CONNECTED: 5,
        # 回测事件 - 较低优先级
        BACKTEST_STARTED: 6,
        BACKTEST_COMPLETED: 6,
        BACKTEST_ERROR: 4,
    }


def create_system_start_event(
    startup_time: Optional[datetime] = None,
    version: str = "5.0",
    correlation_id: Optional[str] = None,
) -> CloudEvent:
    """
    创建系统启动事件

    Args:
        startup_time: 启动时间，默认为当前时间
        version: 系统版本
        correlation_id: 关联ID

    Returns:
        系统启动事件
    """
    return CloudEvent(
        type=CoreEventContracts.SYSTEM_START,
        source="CoreEngine",
        data={
            "startup_time": (startup_time or datetime.now()).isoformat(),
            "version": version,
            "components": ["EventBus", "PluginManager", "ConfigCenter"],
        },
        priority=CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.SYSTEM_START],
        correlation_id=correlation_id,
        tags={"category": "system", "lifecycle": "start"},
    )


def create_plugin_loaded_event(
    plugin_name: str,
    version: str,
    load_time_ms: Optional[float] = None,
    correlation_id: Optional[str] = None,
) -> CloudEvent:
    """
    创建插件加载事件

    Args:
        plugin_name: 插件名称
        version: 插件版本
        load_time_ms: 加载耗时（毫秒）
        correlation_id: 关联ID

    Returns:
        插件加载事件
    """
    data: Dict[str, Any] = {"plugin_name": plugin_name, "version": version}
    if load_time_ms is not None:
        data["load_time_ms"] = load_time_ms

    return CloudEvent(
        type=CoreEventContracts.PLUGIN_LOADED,
        source="PluginLifecycleManager",
        data=data,
        priority=CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.PLUGIN_LOADED],
        correlation_id=correlation_id,
        tags={"category": "plugin", "lifecycle": "loaded", "plugin": plugin_name},
    )


def create_plugin_unloaded_event(
    plugin_name: str, reason: str, correlation_id: Optional[str] = None
) -> CloudEvent:
    """
    创建插件卸载事件

    Args:
        plugin_name: 插件名称
        reason: 卸载原因
        correlation_id: 关联ID

    Returns:
        插件卸载事件
    """
    return CloudEvent(
        type=CoreEventContracts.PLUGIN_UNLOADED,
        source="PluginLifecycleManager",
        data={"plugin_name": plugin_name, "reason": reason},
        priority=CoreEventContracts.EVENT_PRIORITIES[
            CoreEventContracts.PLUGIN_UNLOADED
        ],
        correlation_id=correlation_id,
        tags={"category": "plugin", "lifecycle": "unloaded", "plugin": plugin_name},
    )


def create_config_changed_event(
    plugin: str,
    key: str,
    old_value: Any,
    new_value: Any,
    correlation_id: Optional[str] = None,
) -> CloudEvent:
    """
    创建配置变更事件

    Args:
        plugin: 插件名称
        key: 配置键
        old_value: 旧值
        new_value: 新值
        correlation_id: 关联ID

    Returns:
        配置变更事件
    """
    return CloudEvent(
        type=CoreEventContracts.CONFIG_CHANGED,
        source="DynamicConfigCenter",
        data={
            "plugin": plugin,
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "changed_at": datetime.now().isoformat(),
        },
        priority=CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.CONFIG_CHANGED],
        correlation_id=correlation_id,
        tags={"category": "config", "plugin": plugin},
    )


def create_order_created_event(
    order_id: str,
    symbol: str,
    amount: float,
    price: Optional[float] = None,
    order_type: str = "market",
    strategy: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> CloudEvent:
    """
    创建订单创建事件

    Args:
        order_id: 订单ID
        symbol: 标的代码
        amount: 数量
        price: 价格
        order_type: 订单类型
        strategy: 策略名称
        correlation_id: 关联ID

    Returns:
        订单创建事件
    """
    data = {
        "order_id": order_id,
        "symbol": symbol,
        "amount": amount,
        "order_type": order_type,
        "created_at": datetime.now().isoformat(),
    }

    if price is not None:
        data["price"] = price
    if strategy is not None:
        data["strategy"] = strategy

    return CloudEvent(
        type=CoreEventContracts.ORDER_CREATED,
        source="StrategyPlugin",
        data=data,
        priority=CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.ORDER_CREATED],
        correlation_id=correlation_id,
        tags={"category": "trade", "action": "create", "symbol": symbol},
    )


def create_order_filled_event(
    order_id: str,
    fill_price: float,
    fill_amount: float,
    fill_time: Optional[datetime] = None,
    correlation_id: Optional[str] = None,
) -> CloudEvent:
    """
    创建订单成交事件

    Args:
        order_id: 订单ID
        fill_price: 成交价格
        fill_amount: 成交数量
        fill_time: 成交时间
        correlation_id: 关联ID

    Returns:
        订单成交事件
    """
    return CloudEvent(
        type=CoreEventContracts.ORDER_FILLED,
        source="BacktestEngine",  # 或 "LiveAdapter"
        data={
            "order_id": order_id,
            "fill_price": fill_price,
            "fill_amount": fill_amount,
            "fill_time": (fill_time or datetime.now()).isoformat(),
        },
        priority=CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.ORDER_FILLED],
        correlation_id=correlation_id,
        tags={"category": "trade", "action": "filled"},
    )


def create_risk_alert_event(
    rule: str,
    current_value: float,
    threshold: float,
    severity: str = "warning",
    description: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> CloudEvent:
    """
    创建风险告警事件

    Args:
        rule: 风控规则名称
        current_value: 当前值
        threshold: 阈值
        severity: 严重程度 (info, warning, critical)
        description: 描述
        correlation_id: 关联ID

    Returns:
        风险告警事件
    """
    data = {
        "rule": rule,
        "current_value": current_value,
        "threshold": threshold,
        "severity": severity,
        "triggered_at": datetime.now().isoformat(),
    }

    if description:
        data["description"] = description

    return CloudEvent(
        type=CoreEventContracts.RISK_ALERT,
        source="RiskControlPlugin",
        data=data,
        priority=CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.RISK_ALERT],
        correlation_id=correlation_id,
        tags={"category": "risk", "severity": severity, "rule": rule},
    )


def create_data_error_event(
    source: str,
    symbol: Optional[str] = None,
    error: str = "unknown_error",
    error_code: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> CloudEvent:
    """
    创建数据异常事件

    Args:
        source: 数据源名称
        symbol: 标的代码
        error: 错误描述
        error_code: 错误代码
        correlation_id: 关联ID

    Returns:
        数据异常事件
    """
    data = {"source": source, "error": error, "occurred_at": datetime.now().isoformat()}

    if symbol:
        data["symbol"] = symbol
    if error_code:
        data["error_code"] = error_code

    return CloudEvent(
        type=CoreEventContracts.DATA_ERROR,
        source="DataSourcePlugin",
        data=data,
        priority=CoreEventContracts.EVENT_PRIORITIES[CoreEventContracts.DATA_ERROR],
        correlation_id=correlation_id,
        tags={"category": "data", "source": source, "error": "true"},
    )


def get_event_priority(event_type: str) -> int:
    """
    获取事件优先级

    Args:
        event_type: 事件类型

    Returns:
        事件优先级 (1-10)，默认为5
    """
    return CoreEventContracts.EVENT_PRIORITIES.get(event_type, 5)


def is_core_event(event_type: str) -> bool:
    """
    检查是否为核心事件类型

    Args:
        event_type: 事件类型

    Returns:
        是否为核心事件
    """
    return event_type in CoreEventContracts.EVENT_PRIORITIES


def get_core_event_types() -> List[str]:
    """
    获取所有核心事件类型

    Returns:
        核心事件类型列表
    """
    return list(CoreEventContracts.EVENT_PRIORITIES.keys())


def validate_event_data(event_type: str, data: Dict[str, Any]) -> bool:
    """
    验证事件数据格式是否符合契约

    Args:
        event_type: 事件类型
        data: 事件数据

    Returns:
        是否符合契约
    """
    # 基础验证规则，可以扩展为更详细的schema验证
    if not isinstance(data, dict):
        return False

    # 根据事件类型进行特定验证
    if event_type == CoreEventContracts.PLUGIN_LOADED:
        required_fields = ["plugin_name", "version"]
        return all(field in data for field in required_fields)

    elif event_type == CoreEventContracts.ORDER_CREATED:
        required_fields = ["order_id", "symbol", "amount"]
        return all(field in data for field in required_fields)

    elif event_type == CoreEventContracts.CONFIG_CHANGED:
        required_fields = ["plugin", "key", "old_value", "new_value"]
        return all(field in data for field in required_fields)

    elif event_type == CoreEventContracts.RISK_ALERT:
        required_fields = ["rule", "current_value", "threshold", "severity"]
        return all(field in data for field in required_fields)

    # 默认通过验证
    return True
