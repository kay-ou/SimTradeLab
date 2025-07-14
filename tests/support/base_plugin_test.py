# -*- coding: utf-8 -*-
"""
SimTradeLab 统一插件测试框架 - 测试基类

本文件定义了 `BasePluginTest` 类，所有插件的单元测试都应继承自此类。
它使用 pytest fixture 自动为测试用例注入核心服务的模拟（Mock）对象，
从而将插件与核心框架的其他部分隔离开来，简化插件的单元测试。
"""

from unittest.mock import MagicMock

import pytest

from simtradelab.core.config.config_manager import PluginConfigManager
from simtradelab.core.event_bus import EventBus
from simtradelab.core.plugin_manager import PluginManager


class BasePluginTest:
    """
    插件测试的基类，提供预置的核心服务模拟。
    """

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        """
        一个自动执行的 pytest fixture，用于在每个测试方法运行前设置模拟对象。

        它会模拟以下核心服务：
        - EventBus: 事件总线
        - PluginConfigManager: 统一配置管理器
        - PluginManager: 插件管理器

        并将这些模拟对象存储在 `self.mocks` 字典中，方便测试用例访问。
        """
        # 使用 mocker.patch.object 来模拟类实例的行为
        self.mock_event_bus = MagicMock(spec=EventBus)
        self.mock_config_manager = MagicMock(spec=PluginConfigManager)
        self.mock_plugin_manager = MagicMock(spec=PluginManager)

        # 将模拟对象集中存储，方便在测试用例中通过 self.mocks['service_name'] 的方式使用
        self.mocks = {
            "event_bus": self.mock_event_bus,
            "config_manager": self.mock_config_manager,
            "plugin_manager": self.mock_plugin_manager,
        }
