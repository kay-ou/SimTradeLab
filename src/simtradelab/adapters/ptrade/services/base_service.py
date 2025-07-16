# -*- coding: utf-8 -*-
"""
PTrade 服务基类
"""

import logging
from typing import Any, Optional

from ....core.event_bus import EventBus
from ..context import PTradeContext


class BaseService:
    """服务基类"""

    def __init__(
        self,
        context: "PTradeContext",
        event_bus: Optional[EventBus] = None,
        plugin_manager: Optional[Any] = None,
    ):
        self.context = context
        self.event_bus = event_bus
        self._plugin_manager = plugin_manager
        self._logger = logging.getLogger(self.__class__.__name__)

    def publish_event(
        self, event_type: str, data: Any, source: str = "service"
    ) -> None:
        """发布事件到事件总线"""
        if self.event_bus:
            self.event_bus.publish(event_type, data=data, source=source)
        else:
            self._logger.debug(f"Event bus not available, skipping event: {event_type}")

    def _get_data_plugin(self) -> Optional[Any]:
        """通过插件管理器获取数据源插件"""
        if not self._plugin_manager:
            return None

        all_plugins = self._plugin_manager.get_all_plugins()
        for plugin_name, plugin_instance in all_plugins.items():
            if self._is_data_source_plugin(plugin_instance):
                return plugin_instance
        return None

    def _is_data_source_plugin(self, plugin_instance: Any) -> bool:
        """判断插件是否为数据源插件"""
        required_methods = [
            "get_history_data",
            "get_current_price",
            "get_snapshot",
            "get_multiple_history_data",
        ]
        return all(
            hasattr(plugin_instance, method)
            and callable(getattr(plugin_instance, method))
            for method in required_methods
        )
