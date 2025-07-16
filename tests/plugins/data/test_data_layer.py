# -*- coding: utf-8 -*-
"""
数据层测试

测试数据源抽象层的完整功能
"""

import pandas as pd
import pytest

from simtradelab.plugins.base import PluginMetadata
from simtradelab.plugins.data import (
    CSVDataPlugin,
    DataFrequency,
    DataSourceConfig,
    DataSourceManager,
    MarketType,
)
from simtradelab.plugins.data.config import CSVDataPluginConfig
from tests.support.base_plugin_test import BasePluginTest


class TestBaseDataSourcePlugin:
    """测试BaseDataSourcePlugin抽象基类"""

    def test_enum_definitions(self):
        """测试枚举定义"""
        # 测试DataFrequency
        assert DataFrequency.DAILY.value == "1d"
        assert DataFrequency.WEEKLY.value == "1w"
        assert DataFrequency.MONTHLY.value == "1M"
        assert DataFrequency.MINUTE_1.value == "1m"

        # 测试MarketType
        assert MarketType.STOCK_CN.value == "stock_cn"
        assert MarketType.STOCK_US.value == "stock_us"
        assert MarketType.STOCK_HK.value == "stock_hk"


class TestDataSourceManager(BasePluginTest):
    """测试DataSourceManager"""

    @pytest.fixture
    def manager_with_csv(self):
        """创建包含CSV数据源的管理器"""
        manager = DataSourceManager()

        # 创建CSV插件
        metadata = PluginMetadata(
            name="test_csv_plugin", version="1.0.0", description="Test CSV Data Plugin"
        )
        config = CSVDataPluginConfig()
        csv_plugin = CSVDataPlugin(metadata, config)

        # 注册数据源
        data_source_config = DataSourceConfig(enabled=True)
        manager.register_data_source("csv", csv_plugin, data_source_config)
        manager.initialize()

        yield manager

        # 清理
        manager.shutdown()

    def test_data_source_registration(self, manager_with_csv):
        """测试数据源注册"""
        available_sources = manager_with_csv.get_available_data_sources()
        assert "csv" in available_sources

        status = manager_with_csv.get_data_source_status()
        assert "csv" in status
        assert status["csv"]["enabled"]

    def test_unified_data_access(self, manager_with_csv):
        """测试统一数据访问接口"""
        # 测试历史数据
        history_data = manager_with_csv.get_history_data("000001.SZ", count=3)
        assert isinstance(history_data, pd.DataFrame)
        assert not history_data.empty

        # 测试当前价格
        prices = manager_with_csv.get_current_price(["000001.SZ"])
        assert isinstance(prices, dict)
        assert "000001.SZ" in prices

        # 测试快照数据
        snapshot = manager_with_csv.get_snapshot(["000001.SZ"])
        assert isinstance(snapshot, dict)
        assert "000001.SZ" in snapshot

        # 测试交易日
        trading_day = manager_with_csv.get_trading_day("2023-12-01")
        assert isinstance(trading_day, str)

        # 测试交易日列表
        trading_days = manager_with_csv.get_all_trading_days()
        assert isinstance(trading_days, list)
        assert len(trading_days) > 0

    def test_data_source_management(self, manager_with_csv):
        """测试数据源管理功能"""
        # 测试禁用数据源
        manager_with_csv.disable_data_source("csv")
        available_sources = manager_with_csv.get_available_data_sources()
        assert "csv" not in available_sources

        # 测试启用数据源
        manager_with_csv.enable_data_source("csv")
        available_sources = manager_with_csv.get_available_data_sources()
        assert "csv" in available_sources

        # 测试缓存清理
        manager_with_csv.clear_cache()  # 应该不会抛出异常

    def test_failover_mechanism(self):
        """测试故障切换机制"""
        manager = DataSourceManager()

        # 没有注册任何数据源时，应该抛出异常
        with pytest.raises(Exception):
            manager.get_history_data("000001.SZ")

        manager.shutdown()

    def test_data_source_manager_with_mocked_dependencies(self):
        """测试DataSourceManager与模拟依赖项的交互"""
        # 使用BasePluginTest提供的模拟对象
        manager = DataSourceManager()

        # 验证模拟对象可用
        assert self.mock_event_bus is not None
        assert self.mock_config_manager is not None
        assert self.mock_plugin_manager is not None

        # 可以在这里添加更多使用模拟对象的测试
        manager.shutdown()


class TestDataLayerIntegration(BasePluginTest):
    """测试数据层集成"""

    def test_data_format_consistency(self):
        """测试数据格式一致性"""
        metadata = PluginMetadata(
            name="test_csv_plugin", version="1.0.0", description="Test CSV Data Plugin"
        )
        config = CSVDataPluginConfig()
        csv_plugin = CSVDataPlugin(metadata, config)

        # 通过插件直接获取
        direct_data = csv_plugin.get_history_data("000001.SZ", count=3)

        # 通过管理器获取
        manager = DataSourceManager()
        data_source_config = DataSourceConfig(enabled=True)
        manager.register_data_source("csv", csv_plugin, data_source_config)
        manager.initialize()

        manager_data = manager.get_history_data("000001.SZ", count=3)

        # 验证数据格式一致性
        assert direct_data.columns.tolist() == manager_data.columns.tolist()
        assert len(direct_data) == len(manager_data)

        manager.shutdown()

    def test_data_plugin_hot_swap(self):
        """测试数据插件热插拔"""
        manager = DataSourceManager()

        # 注册第一个插件
        metadata1 = PluginMetadata(
            name="csv1", version="1.0.0", description="CSV Plugin 1"
        )
        plugin1 = CSVDataPlugin(metadata1, CSVDataPluginConfig())
        config1 = DataSourceConfig(enabled=True)
        manager.register_data_source("csv1", plugin1, config1)
        manager.initialize()

        # 验证插件1可用
        assert "csv1" in manager.get_available_data_sources()

        # 注册第二个插件（更高优先级）
        metadata2 = PluginMetadata(
            name="csv2", version="1.0.0", description="CSV Plugin 2"
        )
        plugin2 = CSVDataPlugin(metadata2, CSVDataPluginConfig())
        config2 = DataSourceConfig(enabled=True)  # 简化：不再使用优先级
        manager.register_data_source("csv2", plugin2, config2)

        # 验证两个插件都可用
        available_sources = manager.get_available_data_sources()
        assert "csv1" in available_sources
        assert "csv2" in available_sources

        # 注销第一个插件
        manager.unregister_data_source("csv1")
        available_sources = manager.get_available_data_sources()
        assert "csv1" not in available_sources
        assert "csv2" in available_sources

        manager.shutdown()

    def test_integration_with_mock_dependencies(self):
        """测试与模拟依赖项的集成"""
        # 使用BasePluginTest提供的模拟对象
        assert self.mock_event_bus is not None
        assert self.mock_config_manager is not None
        assert self.mock_plugin_manager is not None

        # 验证模拟对象的类型
        assert str(type(self.mock_event_bus)) == "<class 'unittest.mock.MagicMock'>"
        assert (
            str(type(self.mock_config_manager)) == "<class 'unittest.mock.MagicMock'>"
        )
        assert (
            str(type(self.mock_plugin_manager)) == "<class 'unittest.mock.MagicMock'>"
        )

        # 验证spec属性存在
        assert hasattr(self.mock_event_bus, "_spec_class")
        assert hasattr(self.mock_config_manager, "_spec_class")
        assert hasattr(self.mock_plugin_manager, "_spec_class")
