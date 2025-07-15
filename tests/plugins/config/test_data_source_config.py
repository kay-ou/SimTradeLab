# -*- coding: utf-8 -*-
"""
数据源插件配置模型测试

测试统一的Pydantic配置验证
"""

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from simtradelab.plugins.data.config import (
    DATA_SOURCE_PLUGIN_CONFIG_MAPPING,
    CSVDataPluginConfig,
    ExternalDataSourceConfig,
    MockDataPluginConfig,
    TDXDataSourceConfig,
    get_config_model_for_data_plugin,
)


class TestCSVDataPluginConfig:
    """CSV数据插件配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = CSVDataPluginConfig()

        assert config.cache_timeout == 300
        assert config.supported_markets == {"stock_cn"}
        assert config.supported_frequencies == {"1d"}
        assert config.data_delay == 0
        assert config.data_dir is None
        assert config.auto_create_missing is True
        assert config.default_history_days == 365
        assert config.base_volatility == Decimal("0.02")

    def test_valid_config(self):
        """测试有效配置"""
        data = {
            "data_dir": "/tmp/test_data",
            "auto_create_missing": False,
            "default_history_days": 500,
            "base_volatility": "0.03",
            "cleanup_old_data_days": 60,
            "cache_timeout": 600,
        }

        config = CSVDataPluginConfig(**data)

        assert config.data_dir == Path("/tmp/test_data")
        assert config.auto_create_missing is False
        assert config.default_history_days == 500
        assert config.base_volatility == Decimal("0.03")
        assert config.cleanup_old_data_days == 60
        assert config.cache_timeout == 600

    def test_invalid_history_days(self):
        """测试无效历史天数"""
        with pytest.raises(ValidationError):
            CSVDataPluginConfig(default_history_days=20)  # 小于最小值30

        with pytest.raises(ValidationError):
            CSVDataPluginConfig(default_history_days=4000)  # 大于最大值3650

    def test_invalid_base_volatility(self):
        """测试无效基础波动率"""
        with pytest.raises(ValidationError):
            CSVDataPluginConfig(base_volatility="-0.01")

        with pytest.raises(ValidationError):
            CSVDataPluginConfig(base_volatility="1.5")

    def test_invalid_cache_timeout(self):
        """测试无效缓存超时时间"""
        with pytest.raises(ValidationError):
            CSVDataPluginConfig(cache_timeout=-10)

        with pytest.raises(ValidationError):
            CSVDataPluginConfig(cache_timeout=4000)

    def test_data_dir_validation(self):
        """测试数据目录验证"""
        # 测试字符串路径转换
        config = CSVDataPluginConfig(data_dir="/tmp/test")
        assert isinstance(config.data_dir, Path)
        assert config.data_dir == Path("/tmp/test")

        # 测试Path对象
        config = CSVDataPluginConfig(data_dir=Path("/tmp/test2"))
        assert isinstance(config.data_dir, Path)
        assert config.data_dir == Path("/tmp/test2")


class TestMockDataPluginConfig:
    """Mock数据插件配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = MockDataPluginConfig()

        assert config.enabled is True
        assert config.seed == 42
        assert config.volatility == Decimal("0.02")
        assert config.trend == Decimal("0.0001")
        assert config.daily_volatility_factor == Decimal("0.5")
        assert "STOCK_A" in config.base_prices
        assert config.volume_range["min"] == 1000
        assert config.volume_range["max"] == 10000

    def test_valid_config(self):
        """测试有效配置"""
        data = {
            "enabled": False,
            "seed": 123,
            "base_prices": {"TEST_STOCK": 20.0, "000001.SZ": 25.0},
            "volatility": "0.03",
            "trend": "0.0005",
            "volume_range": {"min": 2000, "max": 20000},
        }

        config = MockDataPluginConfig(**data)

        assert config.enabled is False
        assert config.seed == 123
        assert config.base_prices["TEST_STOCK"] == 20.0
        assert config.volatility == Decimal("0.03")
        assert config.trend == Decimal("0.0005")
        assert config.volume_range["min"] == 2000

    def test_invalid_seed(self):
        """测试无效随机种子"""
        with pytest.raises(ValidationError):
            MockDataPluginConfig(seed=-1)

        with pytest.raises(ValidationError):
            MockDataPluginConfig(seed=2147483648)  # 大于最大值

    def test_invalid_base_prices(self):
        """测试无效基础价格"""
        with pytest.raises(ValidationError):
            MockDataPluginConfig(base_prices={"STOCK_A": -10.0, "STOCK_B": 20.0})  # 负价格

        with pytest.raises(ValidationError):
            MockDataPluginConfig(base_prices={"STOCK_A": 0.0, "STOCK_B": 20.0})  # 零价格

    def test_invalid_volatility(self):
        """测试无效波动率"""
        with pytest.raises(ValidationError):
            MockDataPluginConfig(volatility="-0.01")

        with pytest.raises(ValidationError):
            MockDataPluginConfig(volatility="1.5")

    def test_invalid_trend(self):
        """测试无效趋势系数"""
        with pytest.raises(ValidationError):
            MockDataPluginConfig(trend="-0.02")  # 小于最小值

        with pytest.raises(ValidationError):
            MockDataPluginConfig(trend="0.02")  # 大于最大值

    def test_invalid_volume_range(self):
        """测试无效成交量范围"""
        with pytest.raises(ValidationError):
            MockDataPluginConfig(volume_range={"min": 5000, "max": 3000})  # min > max

        with pytest.raises(ValidationError):
            MockDataPluginConfig(volume_range={"min": 0, "max": 3000})  # min = 0

        with pytest.raises(ValidationError):
            MockDataPluginConfig(volume_range={"min": -100, "max": 3000})  # min < 0


class TestExternalDataSourceConfig:
    """外部数据源配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ExternalDataSourceConfig()

        assert config.connection_string is None
        assert config.api_key is None
        assert config.api_base_url is None
        assert config.timeout == 30
        assert config.retry_count == 3
        assert config.rate_limit is None
        assert config.enable_cache is True

    def test_valid_config(self):
        """测试有效配置"""
        data = {
            "connection_string": "postgresql://user:pass@localhost/db",
            "api_key": "test_api_key",
            "api_base_url": "https://api.example.com",
            "timeout": 60,
            "retry_count": 5,
            "rate_limit": 100,
            "enable_cache": False,
        }

        config = ExternalDataSourceConfig(**data)

        assert config.connection_string == "postgresql://user:pass@localhost/db"
        assert config.api_key == "test_api_key"
        assert config.api_base_url == "https://api.example.com"
        assert config.timeout == 60
        assert config.retry_count == 5
        assert config.rate_limit == 100
        assert config.enable_cache is False

    def test_invalid_timeout(self):
        """测试无效超时时间"""
        with pytest.raises(ValidationError):
            ExternalDataSourceConfig(timeout=0)

        with pytest.raises(ValidationError):
            ExternalDataSourceConfig(timeout=400)

    def test_invalid_retry_count(self):
        """测试无效重试次数"""
        with pytest.raises(ValidationError):
            ExternalDataSourceConfig(retry_count=-1)

        with pytest.raises(ValidationError):
            ExternalDataSourceConfig(retry_count=15)

    def test_invalid_rate_limit(self):
        """测试无效速率限制"""
        with pytest.raises(ValidationError):
            ExternalDataSourceConfig(rate_limit=0)

        with pytest.raises(ValidationError):
            ExternalDataSourceConfig(rate_limit=2000)


class TestTDXDataSourceConfig:
    """通达信数据源配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = TDXDataSourceConfig()

        assert config.server_ip == "119.147.212.81"
        assert config.server_port == 7709
        assert config.connect_timeout == 10
        assert config.read_timeout == 30
        assert config.max_retry == 3
        assert config.enable_heartbeat is True
        assert config.heartbeat_interval == 60

    def test_valid_config(self):
        """测试有效配置"""
        data = {
            "server_ip": "192.168.1.100",
            "server_port": 8888,
            "connect_timeout": 20,
            "read_timeout": 60,
            "max_retry": 5,
            "enable_heartbeat": False,
            "heartbeat_interval": 120,
        }

        config = TDXDataSourceConfig(**data)

        assert config.server_ip == "192.168.1.100"
        assert config.server_port == 8888
        assert config.connect_timeout == 20
        assert config.read_timeout == 60
        assert config.max_retry == 5
        assert config.enable_heartbeat is False
        assert config.heartbeat_interval == 120

    def test_invalid_server_port(self):
        """测试无效服务器端口"""
        with pytest.raises(ValidationError):
            TDXDataSourceConfig(server_port=0)

        with pytest.raises(ValidationError):
            TDXDataSourceConfig(server_port=70000)

    def test_invalid_timeouts(self):
        """测试无效超时时间"""
        with pytest.raises(ValidationError):
            TDXDataSourceConfig(connect_timeout=0)

        with pytest.raises(ValidationError):
            TDXDataSourceConfig(connect_timeout=100)

        with pytest.raises(ValidationError):
            TDXDataSourceConfig(read_timeout=0)

        with pytest.raises(ValidationError):
            TDXDataSourceConfig(read_timeout=400)

    def test_invalid_retry_count(self):
        """测试无效重试次数"""
        with pytest.raises(ValidationError):
            TDXDataSourceConfig(max_retry=-1)

        with pytest.raises(ValidationError):
            TDXDataSourceConfig(max_retry=15)

    def test_invalid_heartbeat_interval(self):
        """测试无效心跳间隔"""
        with pytest.raises(ValidationError):
            TDXDataSourceConfig(heartbeat_interval=5)

        with pytest.raises(ValidationError):
            TDXDataSourceConfig(heartbeat_interval=400)


class TestDataSourceConfigMapping:
    """数据源配置映射测试"""

    def test_get_config_model_for_data_plugin(self):
        """测试根据数据插件名获取配置模型"""
        # 测试已知插件
        assert get_config_model_for_data_plugin("CSVDataPlugin") == CSVDataPluginConfig
        assert (
            get_config_model_for_data_plugin("csv_data_plugin") == CSVDataPluginConfig
        )
        assert (
            get_config_model_for_data_plugin("MockDataPlugin") == MockDataPluginConfig
        )
        assert (
            get_config_model_for_data_plugin("mock_data_plugin") == MockDataPluginConfig
        )
        assert (
            get_config_model_for_data_plugin("ExternalDataSource")
            == ExternalDataSourceConfig
        )
        assert get_config_model_for_data_plugin("TDXDataSource") == TDXDataSourceConfig

        # 测试未知插件
        from simtradelab.plugins.data.config import DataSourceConfig

        assert get_config_model_for_data_plugin("UnknownDataPlugin") == DataSourceConfig

    def test_config_mapping_completeness(self):
        """测试配置映射完整性"""
        expected_plugins = {
            "CSVDataPlugin",
            "csv_data_plugin",
            "MockDataPlugin",
            "mock_data_plugin",
            "ExternalDataSource",
            "TDXDataSource",
        }

        actual_plugins = set(DATA_SOURCE_PLUGIN_CONFIG_MAPPING.keys())
        assert expected_plugins.issubset(actual_plugins)


class TestDataSourceConfigFromDict:
    """数据源配置从字典测试"""

    def test_csv_load_from_dict(self):
        """测试CSV插件从字典加载配置"""
        config_data = {
            "default": {
                "data_dir": "/tmp/csv_data",
                "auto_create_missing": False,
                "default_history_days": 600,
                "cache_timeout": 450,
            }
        }

        config = CSVDataPluginConfig.load_from_dict(config_data)

        assert config.data_dir == Path("/tmp/csv_data")
        assert config.auto_create_missing is False
        assert config.default_history_days == 600
        assert config.cache_timeout == 450

    def test_mock_load_from_dict(self):
        """测试Mock插件从字典加载配置"""
        config_data = {
            "default": {
                "enabled": True,
                "seed": 999,
                "base_prices": {"CUSTOM_STOCK": 30.0},
                "volatility": "0.025",
            }
        }

        config = MockDataPluginConfig.load_from_dict(config_data)

        assert config.enabled is True
        assert config.seed == 999
        assert config.base_prices["CUSTOM_STOCK"] == 30.0
        assert config.volatility == Decimal("0.025")

    def test_load_with_invalid_data(self):
        """测试加载无效数据"""
        config_data = {"default": {"cache_timeout": -100, "seed": -1}}  # 无效值  # 无效值

        with pytest.raises(ValidationError):
            MockDataPluginConfig.load_from_dict(config_data)

    def test_load_with_missing_optional_fields(self):
        """测试加载缺少可选字段的配置"""
        config_data = {"default": {"enabled": False}}

        config = MockDataPluginConfig.load_from_dict(config_data)

        # 应该使用默认值
        assert config.enabled is False
        assert config.seed == 42  # 默认值
        assert config.volatility == Decimal("0.02")  # 默认值
