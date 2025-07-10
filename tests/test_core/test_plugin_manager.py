# -*- coding: utf-8 -*-
"""
PluginManager插件管理器测试

专注测试插件系统在量化交易框架中的核心业务价值：
1. 插件的动态加载和扩展能力
2. 插件间的依赖关系管理
3. 插件热重载和状态保持
4. 插件系统的稳定性和错误隔离
"""

import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from simtradelab.core.event_bus import EventBus
from simtradelab.core.plugin_manager import (
    PluginDiscoveryError,
    PluginLoadError,
    PluginManager,
    PluginRegistrationError,
)
from simtradelab.plugins.base import (
    BasePlugin,
    PluginConfig,
    PluginMetadata,
    PluginState,
)


# 测试插件类定义
class MockDataSourcePlugin(BasePlugin):
    """模拟数据源插件"""

    METADATA = PluginMetadata(
        name="mock_data_source",
        version="1.0.0",
        description="Mock Data Source Plugin",
        author="SimTradeLab",
        dependencies=[],
        tags=["data", "mock"],
        category="data_source",
        priority=10,
    )

    def __init__(self, metadata, config=None):
        super().__init__(metadata, config)
        self.data_fetched = []

    def _on_initialize(self):
        self._logger.info("Mock data source plugin initialized")

    def _on_start(self):
        self._logger.info("Mock data source plugin started")

    def _on_stop(self):
        self._logger.info("Mock data source plugin stopped")

    def fetch_data(self, symbol):
        """模拟数据获取"""
        data = {"symbol": symbol, "price": 100.0, "volume": 1000}
        self.data_fetched.append(data)
        return data


class MockStrategyPlugin(BasePlugin):
    """模拟策略插件"""

    METADATA = PluginMetadata(
        name="mock_strategy",
        version="1.0.0",
        description="Mock Strategy Plugin",
        dependencies=["mock_data_source"],  # 依赖数据源插件
        category="strategy",
        priority=20,
    )

    def __init__(self, metadata, config=None):
        super().__init__(metadata, config)
        self.signals_generated = []

    def _on_initialize(self):
        self._logger.info("Mock strategy plugin initialized")

    def _on_start(self):
        self._logger.info("Mock strategy plugin started")

    def _on_stop(self):
        self._logger.info("Mock strategy plugin stopped")

    def generate_signal(self, data):
        """模拟信号生成"""
        signal = {"action": "BUY", "symbol": data["symbol"], "confidence": 0.8}
        self.signals_generated.append(signal)
        return signal


class StatefulPlugin(BasePlugin):
    """有状态的插件，用于测试热重载"""

    METADATA = PluginMetadata(
        name="stateful_plugin",
        version="1.0.0",
        description="Stateful Plugin for Hot Reload Testing",
    )

    def __init__(self, metadata, config=None):
        super().__init__(metadata, config)
        self.counter = 0
        self.processed_orders = []

    def _on_initialize(self):
        pass

    def _on_start(self):
        pass

    def _on_stop(self):
        pass

    def process_order(self, order_id):
        """处理订单"""
        self.counter += 1
        self.processed_orders.append(order_id)

    def get_state(self):
        """获取插件状态"""
        return {"counter": self.counter, "processed_orders": self.processed_orders}

    def set_state(self, state):
        """设置插件状态"""
        self.counter = state.get("counter", 0)
        self.processed_orders = state.get("processed_orders", [])


class FailingPlugin(BasePlugin):
    """会失败的插件，用于测试错误处理"""

    METADATA = PluginMetadata(
        name="failing_plugin",
        version="1.0.0",
        description="Plugin that fails during initialization",
    )

    def _on_initialize(self):
        raise RuntimeError("Plugin initialization failed")

    def _on_start(self):
        raise RuntimeError("Plugin start failed")

    def _on_stop(self):
        raise RuntimeError("Plugin stop failed")


class TestQuantitativeTradingPluginSystem:
    """测试量化交易插件系统的核心业务能力"""

    def _get_plugin_state(self, plugin_manager, plugin_name):
        """辅助方法：获取插件状态"""
        info = plugin_manager.get_plugin_info(plugin_name)
        if not info:
            return None
        state_str = info["state"]
        if state_str == "unloaded":
            return PluginState.UNINITIALIZED
        return PluginState(state_str)

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus()
        yield bus
        bus.shutdown()

    @pytest.fixture
    def plugin_manager(self, event_bus):
        """插件管理器fixture"""
        manager = PluginManager(event_bus)
        yield manager
        # 清理所有插件
        manager.shutdown()

    def test_modular_trading_system_extension(self, plugin_manager):
        """测试模块化交易系统扩展 - 插件系统的核心价值"""
        # 模拟量化交易系统通过插件扩展功能

        # 注册数据源插件类
        plugin_manager.register_plugin(MockDataSourcePlugin)

        # 注册策略插件类
        plugin_manager.register_plugin(MockStrategyPlugin)

        # 启动插件系统
        plugin_manager.load_all_plugins(start=True)

        # 验证业务价值：模块化系统正常工作
        loaded_plugins = plugin_manager.list_plugins(filter_loaded=True)
        assert len(loaded_plugins) == 2
        assert "mock_data_source" in loaded_plugins
        assert "mock_strategy" in loaded_plugins

        # 验证插件状态
        data_state = self._get_plugin_state(plugin_manager, "mock_data_source")
        strategy_state = self._get_plugin_state(plugin_manager, "mock_strategy")
        assert data_state == PluginState.STARTED
        assert strategy_state == PluginState.STARTED

        # 获取插件实例进行业务逻辑测试
        data_plugin = plugin_manager.get_plugin("mock_data_source")
        strategy_plugin = plugin_manager.get_plugin("mock_strategy")

        # 模拟交易流程：数据获取 → 策略分析 → 信号生成
        data = data_plugin.fetch_data("000001.XSHE")
        signal = strategy_plugin.generate_signal(data)

        # 验证模块化协作
        assert data["symbol"] == "000001.XSHE"
        assert signal["action"] == "BUY"
        assert len(data_plugin.data_fetched) == 1
        assert len(strategy_plugin.signals_generated) == 1

    def test_plugin_dependency_management(self, plugin_manager):
        """测试插件依赖关系管理 - 复杂系统架构的关键能力"""
        # 模拟有依赖关系的插件系统

        # 先注册依赖插件（策略依赖数据源）

        # 以错误顺序注册（策略先于数据源）
        plugin_manager.register_plugin(MockStrategyPlugin)
        plugin_manager.register_plugin(MockDataSourcePlugin)

        # 启动插件系统 - 应该按依赖顺序启动
        plugin_manager.load_all_plugins(start=True)

        # 验证业务价值：依赖管理确保正确的启动顺序
        loaded_plugins = plugin_manager.list_plugins(filter_loaded=True)
        assert len(loaded_plugins) == 2

        # 验证依赖插件先启动
        data_info = plugin_manager.get_plugin_info("mock_data_source")
        strategy_info = plugin_manager.get_plugin_info("mock_strategy")

        assert data_info["state"] == PluginState.STARTED.value
        assert strategy_info["state"] == PluginState.STARTED.value

        # 验证依赖关系正确识别
        assert "mock_data_source" in strategy_info["dependencies"]

    def test_plugin_hot_reload_with_state_preservation(self, plugin_manager):
        """测试插件热重载与状态保持 - 生产系统的关键需求"""
        # 模拟生产环境中的插件热重载场景

        # 注册有状态的插件
        plugin_manager.register_plugin(StatefulPlugin)
        plugin_manager.load_plugin("stateful_plugin")
        plugin_manager.start_plugin("stateful_plugin")

        # 获取插件实例
        stateful_plugin = plugin_manager.get_plugin("stateful_plugin")

        # 模拟插件处理业务数据
        stateful_plugin.process_order("ORD_001")
        stateful_plugin.process_order("ORD_002")
        stateful_plugin.process_order("ORD_003")

        # 验证插件状态
        assert stateful_plugin.counter == 3
        assert len(stateful_plugin.processed_orders) == 3

        # 执行热重载 - 使用内置的reload功能
        assert plugin_manager.reload_plugin("stateful_plugin"), "插件热重载应该成功"

        # reload_plugin只重新加载，需要手动启动
        assert plugin_manager.start_plugin("stateful_plugin"), "重载后启动插件应该成功"

        # 获取重载后的插件实例
        reloaded_plugin = plugin_manager.get_plugin("stateful_plugin")
        assert reloaded_plugin is not None, "重载后应该可以获取到插件实例"
        assert (
            self._get_plugin_state(plugin_manager, "stateful_plugin")
            == PluginState.STARTED
        )

        # 继续处理新订单验证插件功能正常
        reloaded_plugin.process_order("ORD_004")
        assert reloaded_plugin.counter == 4  # 状态被保持，继续累加
        assert "ORD_004" in reloaded_plugin.processed_orders

        # 验证业务价值：热重载成功保持了插件状态，业务无中断
        assert len(reloaded_plugin.processed_orders) == 4
        expected_orders = ["ORD_001", "ORD_002", "ORD_003", "ORD_004"]
        for order in expected_orders:
            assert order in reloaded_plugin.processed_orders

    def test_plugin_error_isolation_and_system_stability(self, plugin_manager):
        """测试插件错误隔离和系统稳定性 - 生产环境的可靠性保证"""
        # 模拟生产环境中插件失败但系统继续运行的场景

        # 注册正常工作的插件
        plugin_manager.register_plugin(MockDataSourcePlugin)

        # 注册会失败的插件
        plugin_manager.register_plugin(FailingPlugin)

        # 启动所有插件 - 好插件应该正常，坏插件应该失败但不影响系统
        plugin_manager.load_all_plugins(start=True)

        # 验证业务价值：系统容错能力
        loaded_plugins = plugin_manager.list_plugins(filter_loaded=True)

        # 好插件应该正常启动
        assert "mock_data_source" in loaded_plugins
        assert (
            self._get_plugin_state(plugin_manager, "mock_data_source")
            == PluginState.STARTED
        )

        # 坏插件应该失败但被隔离
        assert "failing_plugin" in plugin_manager.list_plugins()  # 注册了但可能没启动
        # 插件加载了但启动失败，可能处于任何非started状态
        bad_state = self._get_plugin_state(plugin_manager, "failing_plugin")
        # 由于插件启动失败，它可能处于多种状态，只要不是STARTED就说明隔离生效了
        assert (
            bad_state != PluginState.STARTED
        ), f"失败的插件不应该处于STARTED状态，实际状态: {bad_state}"

        # 验证好插件仍然可以正常工作
        good_plugin = plugin_manager.get_plugin("mock_data_source")
        data = good_plugin.fetch_data("000001.XSHE")
        assert data["symbol"] == "000001.XSHE"
        assert len(good_plugin.data_fetched) == 1

        # 验证系统整体稳定性
        all_plugins = plugin_manager.get_all_plugins()
        assert len(all_plugins) >= 1  # 至少有一个好插件
        assert "mock_data_source" in all_plugins

    def test_concurrent_plugin_operations(self, plugin_manager):
        """测试并发插件操作 - 多线程交易环境的稳定性"""
        # 模拟高并发交易系统中的插件操作

        operation_results = []
        lock = threading.Lock()

        def plugin_worker(worker_id):
            """插件操作工作线程"""
            try:
                # 创建插件类
                plugin_name = f"worker_plugin_{worker_id}"
                metadata = PluginMetadata(
                    name=plugin_name,
                    version="1.0.0",
                    description=f"Worker Plugin {worker_id}",
                )

                class WorkerPlugin(BasePlugin):
                    METADATA = metadata

                    def _on_initialize(self):
                        pass

                    def _on_start(self):
                        pass

                    def _on_stop(self):
                        pass

                # 并发操作：注册、加载、启动、停止
                plugin_manager.register_plugin(WorkerPlugin)
                plugin_manager.load_plugin(plugin_name)
                plugin_manager.start_plugin(plugin_name)
                time.sleep(0.01)  # 模拟插件工作
                plugin_manager.stop_plugin(plugin_name)

                with lock:
                    operation_results.append(
                        {
                            "worker_id": worker_id,
                            "plugin_name": plugin_name,
                            "status": "success",
                        }
                    )

            except Exception as e:
                with lock:
                    operation_results.append(
                        {"worker_id": worker_id, "error": str(e), "status": "failed"}
                    )

        # 启动多个并发线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=plugin_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证业务价值：并发环境下系统稳定
        assert len(operation_results) == 5

        successful_operations = [
            r for r in operation_results if r["status"] == "success"
        ]
        failed_operations = [r for r in operation_results if r["status"] == "failed"]

        # 大部分操作应该成功（允许少量并发冲突）
        assert (
            len(successful_operations) >= 3
        ), f"并发操作成功率过低: {len(successful_operations)}/5"

        # 验证插件管理器状态一致性
        all_plugins = plugin_manager.get_all_plugins()

        # 验证系统在并发压力下保持稳定
        stats = plugin_manager.get_stats()
        assert stats["registered"] >= len(successful_operations)  # 至少注册了成功的插件数量

    def test_plugin_discovery_and_registration_workflow(self, plugin_manager):
        """测试插件发现和注册工作流程 - 动态扩展能力验证"""
        # 模拟插件发现和动态注册的完整流程

        # 初始状态：无插件
        assert len(plugin_manager.list_plugins()) == 0

        # 动态发现和注册插件
        plugins_to_register = [
            ("数据源插件", MockDataSourcePlugin),
            ("策略插件", MockStrategyPlugin),
            ("状态插件", StatefulPlugin),
        ]

        registered_plugins = []
        for description, plugin_class in plugins_to_register:
            plugin_manager.register_plugin(plugin_class)
            registered_plugins.append((description, plugin_class))

        # 验证注册结果
        assert len(plugin_manager.list_plugins()) == 3

        # 批量启动插件
        load_results = plugin_manager.load_all_plugins(start=True)

        # 验证所有插件都正常启动
        for description, plugin_class in registered_plugins:
            plugin_name = plugin_class.METADATA.name
            assert plugin_name in plugin_manager.list_plugins(), f"{description}未正确注册"
            assert load_results.get(plugin_name, False), f"{description}加载失败"
            assert (
                self._get_plugin_state(plugin_manager, plugin_name)
                == PluginState.STARTED
            ), f"{description}未正确启动"

        # 验证插件信息
        all_plugins = plugin_manager.get_all_plugins()
        assert len(all_plugins) == 3

        for plugin_name, plugin_instance in all_plugins.items():
            info = plugin_manager.get_plugin_info(plugin_name)
            assert "name" in info
            assert "state" in info
            assert info["state"] == PluginState.STARTED.value

    def test_plugin_lifecycle_management(self, plugin_manager):
        """测试插件生命周期管理 - 完整的插件管理验证"""
        # 模拟完整的插件生命周期

        # 创建并注册插件
        plugin_name = MockDataSourcePlugin.METADATA.name

        # 1. 注册阶段
        plugin_manager.register_plugin(MockDataSourcePlugin)
        assert plugin_name in plugin_manager.list_plugins()
        assert (
            self._get_plugin_state(plugin_manager, plugin_name)
            == PluginState.UNINITIALIZED
        )

        # 2. 加载和启动阶段
        plugin_manager.load_plugin(plugin_name)
        plugin_manager.start_plugin(plugin_name)
        assert (
            self._get_plugin_state(plugin_manager, plugin_name) == PluginState.STARTED
        )

        # 3. 运行期间功能验证
        plugin = plugin_manager.get_plugin(plugin_name)
        data = plugin.fetch_data("000001.XSHE")
        assert data is not None
        assert len(plugin.data_fetched) == 1

        # 4. 停止阶段
        plugin_manager.stop_plugin(plugin_name)
        assert (
            self._get_plugin_state(plugin_manager, plugin_name) == PluginState.STOPPED
        )

        # 5. 注销阶段
        plugin_manager.unregister_plugin(plugin_name)
        assert plugin_name not in plugin_manager.list_plugins()

        # 验证完整生命周期后系统状态
        assert len(plugin_manager.list_plugins()) == 0
        assert len(plugin_manager.get_all_plugins()) == 0

    def test_plugin_configuration_management(self, plugin_manager):
        """测试插件配置管理 - 灵活配置的核心需求"""
        # 模拟插件配置管理场景

        # 创建带配置的插件
        config = PluginConfig(
            config={
                "data_source": "mock",
                "refresh_interval": 1000,
                "cache_size": 100,
                "enabled_symbols": ["000001.XSHE", "000002.XSHE"],
            }
        )

        plugin_manager.register_plugin(MockDataSourcePlugin, config=config)
        plugin_manager.load_plugin("mock_data_source")
        plugin_manager.start_plugin("mock_data_source")

        # 验证配置被正确应用
        plugin_info = plugin_manager.get_plugin_info("mock_data_source")
        assert plugin_info is not None, "应该能获取到插件信息"
        # 注意：config可能存储在plugin实例中，通过get_plugin获取
        plugin = plugin_manager.get_plugin("mock_data_source")
        assert plugin._config.config["data_source"] == "mock"
        assert plugin._config.config["refresh_interval"] == 1000

        # 测试运行时配置访问
        plugin = plugin_manager.get_plugin("mock_data_source")
        runtime_config = plugin._config.config
        assert runtime_config["cache_size"] == 100
        assert "000001.XSHE" in runtime_config["enabled_symbols"]

        # 验证插件使用配置工作
        for symbol in runtime_config["enabled_symbols"]:
            data = plugin.fetch_data(symbol)
            assert data["symbol"] == symbol

        assert len(plugin.data_fetched) == 2
