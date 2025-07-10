# -*- coding: utf-8 -*-
"""
SimTradeLab Events Package
提供标准化事件模型和契约定义
"""

from .cloud_event import CloudEvent
from .contracts import (
    CoreEventContracts,
    create_config_changed_event,
    create_data_error_event,
    create_order_created_event,
    create_order_filled_event,
    create_plugin_loaded_event,
    create_plugin_unloaded_event,
    create_risk_alert_event,
    create_system_start_event,
)

__all__ = [
    "CloudEvent",
    "CoreEventContracts",
    "create_system_start_event",
    "create_plugin_loaded_event",
    "create_plugin_unloaded_event",
    "create_config_changed_event",
    "create_order_created_event",
    "create_order_filled_event",
    "create_risk_alert_event",
    "create_data_error_event",
]
