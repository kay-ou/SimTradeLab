# -*- coding: utf-8 -*-
"""
数据层测试

测试数据源抽象层的完整功能
"""

from pathlib import Path

import pandas as pd
import pytest

from src.simtradelab.plugins.base import PluginConfig, PluginMetadata
from src.simtradelab.plugins.data import (
    BaseDataSourcePlugin,
    CSVDataPlugin,
    DataFrequency,
    DataSourceConfig,
    DataSourceManager,
    MarketType,
)


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


class TestCSVDataPlugin:
    """测试CSVDataPlugin实现"""

    @pytest.fixture
    def csv_plugin(self):
        """创建CSV插件实例"""
        metadata = PluginMetadata(
            name="test_csv_plugin", version="1.0.0", description="Test CSV Data Plugin"
        )
        config = PluginConfig()
        return CSVDataPlugin(metadata, config)

    def test_plugin_metadata(self, csv_plugin):
        """测试插件元数据"""
        assert csv_plugin.get_supported_markets() == {MarketType.STOCK_CN}
        assert DataFrequency.DAILY in csv_plugin.get_supported_frequencies()
        assert csv_plugin.get_data_delay() == 0
        assert csv_plugin.is_available() == True

    def test_history_data(self, csv_plugin):
        """测试历史数据获取"""
        # 测试单个证券历史数据
        data = csv_plugin.get_history_data("000001.SZ", count=5)
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        assert len(data) <= 5
        assert "close" in data.columns
        assert "open" in data.columns
        assert "high" in data.columns
        assert "low" in data.columns
        assert "volume" in data.columns

    def test_multiple_history_data(self, csv_plugin):
        """测试多个证券历史数据获取"""
        securities = ["000001.SZ", "000002.SZ"]

        # 测试DataFrame格式
        data = csv_plugin.get_multiple_history_data(
            security_list=securities, count=3, as_dict=False
        )
        assert isinstance(data, pd.DataFrame)
        assert not data.empty

        # 测试字典格式
        data_dict = csv_plugin.get_multiple_history_data(
            security_list=securities, count=3, as_dict=True
        )
        assert isinstance(data_dict, dict)
        assert "000001.SZ" in data_dict
        assert "000002.SZ" in data_dict

    def test_current_price(self, csv_plugin):
        """测试当前价格获取"""
        securities = ["000001.SZ", "000002.SZ"]
        prices = csv_plugin.get_current_price(securities)

        assert isinstance(prices, dict)
        assert "000001.SZ" in prices
        assert "000002.SZ" in prices
        assert isinstance(prices["000001.SZ"], (int, float))
        assert prices["000001.SZ"] > 0

    def test_snapshot(self, csv_plugin):
        """测试快照数据获取"""
        securities = ["000001.SZ"]
        snapshot = csv_plugin.get_snapshot(securities)

        assert isinstance(snapshot, dict)
        assert "000001.SZ" in snapshot

        security_data = snapshot["000001.SZ"]
        expected_fields = ["last_price", "open", "high", "low", "volume"]
        for field in expected_fields:
            assert field in security_data

    def test_trading_calendar(self, csv_plugin):
        """测试交易日历功能"""
        # 测试交易日判断
        assert csv_plugin.is_trading_day("2023-12-01") == True  # 周五
        assert csv_plugin.is_trading_day("2023-12-02") == False  # 周六

        # 测试交易日获取
        trading_day = csv_plugin.get_trading_day("2023-12-01", offset=1)
        assert trading_day == "2023-12-04"  # 下一个交易日是周一

        # 测试交易日范围
        trading_days = csv_plugin.get_trading_days_range("2023-12-01", "2023-12-05")
        assert isinstance(trading_days, list)
        assert len(trading_days) == 3  # 周一、周二、周三

    def test_limit_status(self, csv_plugin):
        """测试涨跌停状态"""
        securities = ["000001.SZ"]
        limit_status = csv_plugin.check_limit_status(securities)

        assert isinstance(limit_status, dict)
        assert "000001.SZ" in limit_status

        status = limit_status["000001.SZ"]
        assert "limit_up" in status
        assert "limit_down" in status
        assert "current_price" in status
        assert isinstance(status["limit_up"], bool)
        assert isinstance(status["limit_down"], bool)

    def test_security_info(self, csv_plugin):
        """测试证券信息获取"""
        securities = ["000001.SZ", "600000.SH"]
        info = csv_plugin.get_security_info(securities)

        assert isinstance(info, dict)
        assert "000001.SZ" in info
        assert "600000.SH" in info

        # 检查深市股票
        sz_info = info["000001.SZ"]
        assert sz_info["market"] == "SZSE"
        assert sz_info["type"] == "stock"

        # 检查沪市股票
        sh_info = info["600000.SH"]
        assert sh_info["market"] == "SSE"
        assert sh_info["type"] == "stock"


class TestDataSourceManager:
    """测试DataSourceManager"""

    @pytest.fixture
    def manager_with_csv(self):
        """创建包含CSV数据源的管理器"""
        manager = DataSourceManager()

        # 创建CSV插件
        metadata = PluginMetadata(
            name="test_csv_plugin", version="1.0.0", description="Test CSV Data Plugin"
        )
        config = PluginConfig()
        csv_plugin = CSVDataPlugin(metadata, config)

        # 注册数据源
        data_source_config = DataSourceConfig(priority=1, enabled=True)
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
        assert status["csv"].is_available == True

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


class TestDataLayerIntegration:
    """测试数据层集成"""

    def test_data_format_consistency(self):
        """测试数据格式一致性"""
        metadata = PluginMetadata(
            name="test_csv_plugin", version="1.0.0", description="Test CSV Data Plugin"
        )
        config = PluginConfig()
        csv_plugin = CSVDataPlugin(metadata, config)

        # 通过插件直接获取
        direct_data = csv_plugin.get_history_data("000001.SZ", count=3)

        # 通过管理器获取
        manager = DataSourceManager()
        data_source_config = DataSourceConfig(priority=1, enabled=True)
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
        plugin1 = CSVDataPlugin(metadata1, PluginConfig())
        config1 = DataSourceConfig(priority=1, enabled=True)
        manager.register_data_source("csv1", plugin1, config1)
        manager.initialize()

        # 验证插件1可用
        assert "csv1" in manager.get_available_data_sources()

        # 注册第二个插件（更高优先级）
        metadata2 = PluginMetadata(
            name="csv2", version="1.0.0", description="CSV Plugin 2"
        )
        plugin2 = CSVDataPlugin(metadata2, PluginConfig())
        config2 = DataSourceConfig(priority=0, enabled=True)  # 更高优先级
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
