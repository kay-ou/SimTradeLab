# tests/support/base_plugin_test.py

import pytest
from unittest.mock import MagicMock

# 导入需要模拟的核心服务类
from src.simtradelab.core.event_bus import EventBus
from src.simtradelab.plugins.config.dynamic_config_center import DynamicConfigCenter
from src.simtradelab.plugins.lifecycle.plugin_lifecycle_manager import PluginLifecycleManager

class BasePluginTest:
    """
    统一的插件测试基类 (v5.0 架构规范)

    该基类为所有插件的单元测试提供了一个标准化的、隔离的环境。
    它会自动模拟并注入核心的系统服务，使得插件测试可以专注于其自身逻辑，
    而无需关心外部依赖的真实实现。

    核心功能:
    - **自动模拟**: 使用 pytest.fixture 自动模拟 EventBus, DynamicConfigCenter 等核心服务。
    - **依赖注入**: 将模拟的服务实例通过 `self.mocks` 字典提供给测试用例。
    - **隔离环境**: 确保每个测试都在一个干净、可预测的环境中运行。
    """

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mocker):
        """
        为每个测试用例设置模拟的核心服务。

        `autouse=True` 确保此 fixture 在每个测试方法运行前自动执行。
        `mocker` 是 `pytest-mock` 提供的 fixture，用于创建模拟对象。
        """
        # 模拟核心服务，使用 spec=... 来确保模拟对象拥有与真实对象相同的接口
        self.mock_event_bus = mocker.MagicMock(spec=EventBus)
        self.mock_config_center = mocker.MagicMock(spec=DynamicConfigCenter)
        self.mock_plugin_manager = mocker.MagicMock(spec=PluginLifecycleManager)

        # 将所有模拟对象聚合到一个字典中，方便在测试用例中统一访问
        # 这种方式使得测试代码更清晰，易于维护
        self.mocks = {
            'event_bus': self.mock_event_bus,
            'config_center': self.mock_config_center,
            'plugin_manager': self.mock_plugin_manager,
        }
