# -*- coding: utf-8 -*-
"""
全局测试配置
提供基本的测试环境设置和共享fixture
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from simtradelab.core.event_bus import EventBus
from simtradelab.core.events.cloud_event import CloudEvent
from simtradelab.core.plugin_manager import PluginManager
from simtradelab.plugins.base import BasePlugin, PluginMetadata


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_event_bus():
    """模拟事件总线"""
    return MagicMock(spec=EventBus)


@pytest.fixture
def mock_plugin_manager():
    """模拟插件管理器"""
    return MagicMock(spec=PluginManager)


@pytest.fixture
def sample_plugin_metadata():
    """示例插件元数据"""
    return PluginMetadata(
        name="test_plugin",
        version="1.0.0",
        description="Test plugin for unit testing",
        author="SimTradeLab",
        license="MIT",
        dependencies=[],
        permissions=[],
    )


@pytest.fixture
def sample_plugin_config():
    """示例插件配置"""
    return {
        "name": "test_plugin",
        "enabled": True,
        "parameters": {"threshold": 0.5, "max_iterations": 100},
    }


@pytest.fixture
def temp_plugin_dir():
    """临时插件目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_cloud_event():
    """示例CloudEvent"""
    return CloudEvent(
        type="com.simtradelab.test.event",
        source="test_source",
        data={"message": "test event"},
    )


class MockPlugin(BasePlugin):
    """测试用模拟插件"""

    def __init__(self, metadata, config=None, fail_on=None):
        super().__init__(metadata, config)
        self.fail_on = fail_on or []
        self.call_history = []

    def _on_initialize(self):
        self.call_history.append("initialize")
        if "initialize" in self.fail_on:
            raise RuntimeError("Initialize failed")

    def _on_start(self):
        self.call_history.append("start")
        if "start" in self.fail_on:
            raise RuntimeError("Start failed")

    def _on_stop(self):
        self.call_history.append("stop")
        if "stop" in self.fail_on:
            raise RuntimeError("Stop failed")

    def _on_pause(self):
        self.call_history.append("pause")
        if "pause" in self.fail_on:
            raise RuntimeError("Pause failed")

    def _on_resume(self):
        self.call_history.append("resume")
        if "resume" in self.fail_on:
            raise RuntimeError("Resume failed")

    def _on_cleanup(self):
        self.call_history.append("cleanup")
        if "cleanup" in self.fail_on:
            raise RuntimeError("Cleanup failed")


@pytest.fixture
def mock_plugin(sample_plugin_metadata, sample_plugin_config):
    """创建模拟插件实例"""
    return MockPlugin(sample_plugin_metadata, sample_plugin_config)


# 测试标记配置
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "performance: 性能测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "network: 需要网络的测试")
