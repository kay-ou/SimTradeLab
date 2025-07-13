# -*- coding: utf-8 -*-
"""
PTrade API服务层基类和服务类导入

定义服务层的通用接口和功能，用于分离路由器中的业务逻辑
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ....core.event_bus import EventBus


class BaseService(ABC):
    """服务层基类"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def initialize(self) -> None:
        """初始化服务"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """关闭服务"""
        pass

    def publish_event(self, event_name: str, data: Dict[str, Any], source: str) -> None:
        """发布事件"""
        if self.event_bus:
            self.event_bus.publish(event_name, data=data, source=source)


# 导入具体的服务类
from .backtest_service import BacktestService
from .research_service import ResearchService
from .trading_service import TradingService

__all__ = [
    "BaseService",
    "BacktestService",
    "TradingService",
    "ResearchService",
]
