# -*- coding: utf-8 -*-
"""
Mock数据源插件测试 - 彻底重写版

此文件旨在提供一个结构清晰、覆盖全面、可维护性高的测试套件。
主要改进点：
- 使用 parametrize 减少冗余测试代码。
- 增强数据质量和统计特性的验证。
- 强化边界条件和错误处理测试。
- 引入更真实的集成测试场景。
"""

import random
import threading
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from simtradelab.plugins.base import PluginMetadata, PluginState
from simtradelab.plugins.data.base_data_source import DataFrequency, MarketType
from simtradelab.plugins.data.config import MockDataPluginConfig
from simtradelab.plugins.data.sources.mock_data_plugin import MockDataPlugin


@pytest.fixture(scope="module")
def default_plugin_metadata():
    """提供一个默认的插件元数据 fixture。"""
    return PluginMetadata(
        name="test_mock_plugin",
        version="0.1.0",
        description="A test version of the mock data plugin.",
        author="Test Author",
    )


class TestMockDataPluginConfig:
    """测试 MockDataPluginConfig 配置模型的验证逻辑。"""

    def test_default_config_creation(self):
        """测试默认配置是否能成功创建并包含正确的默认值。"""
        config = MockDataPluginConfig()
        assert config.enabled is True
        assert config.seed == 42
        assert config.volatility == Decimal("0.02")
        assert config.trend == Decimal("0.0001")
        assert config.daily_volatility_factor == Decimal("0.5")
        assert config.base_prices == {
            "STOCK_A": 10.0,
            "000001.SZ": 15.0,
            "000002.SZ": 12.0,
            "600000.SH": 8.0,
            "600036.SH": 35.0,
        }
        assert config.volume_range == {"min": 1000, "max": 10000}

    def test_custom_config_creation(self):
        """测试使用自定义值创建配置。"""
        custom_data = {
            "enabled": False,
            "seed": 123,
            "volatility": Decimal("0.05"),
            "trend": Decimal("-0.001"),
            "base_prices": {"CUSTOM.SYM": 200.0},
            "volume_range": {"min": 500, "max": 5000},
        }
        config = MockDataPluginConfig(**custom_data)
        assert config.enabled is False
        assert config.seed == 123
        assert config.volatility == Decimal("0.05")
        assert config.trend == Decimal("-0.001")
        assert config.base_prices == {"CUSTOM.SYM": 200.0}
        assert config.volume_range == {"min": 500, "max": 5000}

    @pytest.mark.parametrize(
        "param, value, expected_error",
        [
            ("seed", -1, "Input should be greater than or equal to 0"),
            ("seed", 2**32, "Input should be less than or equal to 2147483647"),
            (
                "volatility",
                Decimal("-0.1"),
                "Input should be greater than or equal to 0",
            ),
            ("volatility", Decimal("1.1"), "Input should be less than or equal to 1"),
            (
                "trend",
                Decimal("-0.02"),
                "Input should be greater than or equal to -0.01",
            ),
            ("trend", Decimal("0.02"), "Input should be less than or equal to 0.01"),
            ("base_prices", {"STOCK_A": 0.0}, "基础价格必须大于0"),
            ("base_prices", {"STOCK_A": -10.0}, "基础价格必须大于0"),
            ("volume_range", {"min": 1000, "max": 500}, "最小成交量必须小于最大成交量"),
            ("volume_range", {"min": 0, "max": 1000}, "最小成交量必须大于0"),
        ],
    )
    def test_config_validation_errors(self, param, value, expected_error):
        """测试配置模型的各种验证错误。"""
        with pytest.raises(ValidationError) as excinfo:
            MockDataPluginConfig(**{param: value})
        assert expected_error in str(excinfo.value)


class TestMockDataPluginInitialization:
    """测试 MockDataPlugin 的初始化过程。"""

    def test_initialization_with_default_config(self, default_plugin_metadata):
        """测试使用默认配置初始化插件。"""
        plugin = MockDataPlugin(default_plugin_metadata)
        assert plugin.is_enabled() is True
        assert plugin._seed == 42
        assert plugin.state == PluginState.UNINITIALIZED

    def test_initialization_with_custom_config(self, default_plugin_metadata):
        """测试使用自定义配置初始化插件。"""
        config = MockDataPluginConfig(enabled=False, seed=100)
        plugin = MockDataPlugin(default_plugin_metadata, config)
        assert plugin.is_enabled() is False
        assert plugin._seed == 100
        assert plugin.state == PluginState.UNINITIALIZED

    def test_supported_features(self, default_plugin_metadata):
        """测试插件声明的支持功能是否正确。"""
        plugin = MockDataPlugin(default_plugin_metadata)
        assert plugin.get_supported_markets() == {MarketType.STOCK_CN}
        assert plugin.get_supported_frequencies() == {
            DataFrequency.DAILY,
            DataFrequency.MINUTE_1,
        }
        assert plugin.get_data_delay() == 0


class TestMockDataPluginLifecycle:
    """测试插件的生命周期管理。"""

    @pytest.fixture
    def plugin(self, default_plugin_metadata):
        """提供一个插件实例用于生命周期测试。"""
        return MockDataPlugin(default_plugin_metadata)

    def test_full_lifecycle(self, plugin):
        """测试插件从创建到销毁的完整生命周期状态转换。"""
        assert plugin.state == PluginState.UNINITIALIZED
        plugin.initialize()
        assert plugin.state == PluginState.INITIALIZED
        plugin.start()
        assert plugin.state == PluginState.STARTED
        plugin.stop()
        assert plugin.state == PluginState.STOPPED
        plugin.shutdown()
        assert plugin.state == PluginState.UNINITIALIZED
        assert not plugin._data_cache  # 缓存应被清空

    def test_enable_disable_methods(self, plugin):
        """测试启用和禁用插件的功能。"""
        assert plugin.is_enabled() is True
        plugin.disable()
        assert plugin.is_enabled() is False
        assert plugin.is_available() is False
        plugin.enable()
        assert plugin.is_enabled() is True
        assert plugin.is_available() is True


class TestMockDataPluginDataGeneration:
    """测试数据生成的核心逻辑。"""

    @pytest.fixture
    def plugin(self, default_plugin_metadata):
        """提供一个已初始化的、配置好的插件实例。"""
        config = MockDataPluginConfig(
            seed=42,
            base_prices={"TEST.S": 100.0, "ANOTHER.S": 50.0},
            volatility=Decimal("0.02"),
            trend=Decimal("0.0001"),
        )
        plugin = MockDataPlugin(default_plugin_metadata, config)
        plugin.initialize()
        return plugin

    def test_get_history_data_structure_and_quality(self, plugin):
        """测试 get_history_data 返回的数据结构和基本质量。"""
        df = plugin.get_history_data("TEST.S", count=10)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) <= 10

        expected_columns = {"open", "high", "low", "close", "volume", "amount"}
        assert expected_columns.issubset(df.columns)

        # 数据质量验证
        assert (df["high"] >= df["low"]).all()
        assert (df["high"] >= df["open"]).all()
        assert (df["high"] >= df["close"]).all()
        assert (df["low"] <= df["open"]).all()
        assert (df["low"] <= df["close"]).all()
        assert (
            (df[["open", "high", "low", "close", "volume", "amount"]] > 0).all().all()
        )

    @pytest.mark.parametrize("frequency", [DataFrequency.DAILY, DataFrequency.MINUTE_1])
    def test_get_history_data_frequencies(self, plugin, frequency):
        """测试不同频率下的历史数据生成。"""
        df = plugin.get_history_data("TEST.S", count=5, frequency=frequency)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 5
        assert set(df.columns).issuperset({"open", "high", "low", "close"})

    def test_get_multiple_history_data(self, plugin):
        """测试获取多个证券的历史数据。"""
        securities = ["TEST.S", "ANOTHER.S"]

        # 测试字典返回格式
        data_dict = plugin.get_multiple_history_data(securities, count=5, as_dict=True)
        assert isinstance(data_dict, dict)
        assert set(data_dict.keys()) == set(securities)
        assert isinstance(data_dict["TEST.S"], pd.DataFrame)

        # 测试DataFrame返回格式
        data_df = plugin.get_multiple_history_data(securities, count=5, as_dict=False)
        assert isinstance(data_df, pd.DataFrame)
        assert "security" in data_df.columns
        assert set(data_df["security"].unique()) == set(securities)

    def test_get_current_price_and_snapshot(self, plugin):
        """测试获取当前价格和市场快照。"""
        securities = ["TEST.S", "ANOTHER.S"]

        # 当前价格
        prices = plugin.get_current_price(securities)
        assert isinstance(prices, dict)
        assert set(prices.keys()) == set(securities)
        assert all(isinstance(p, float) and p > 0 for p in prices.values())

        # 市场快照
        snapshot = plugin.get_snapshot(securities)
        assert isinstance(snapshot, dict)
        assert set(snapshot.keys()) == set(securities)
        assert "last_price" in snapshot["TEST.S"]
        assert snapshot["TEST.S"]["bid1"] < snapshot["TEST.S"]["ask1"]

    def test_data_generation_statistical_properties(self, plugin):
        """测试生成数据的统计特性是否与配置大致相符。"""
        df = plugin.get_history_data("TEST.S", count=252)  # 约一年的日线数据
        returns = df["close"].pct_change().dropna()

        # 检查波动率是否在合理范围内（由于随机性，设定一个较宽的容忍度）
        # 理论日波动率是 0.02
        assert 0.01 < returns.std() < 0.03

        # 检查趋势是否为正
        # 理论日趋势是 0.0001
        assert returns.mean() > 0


class TestMockDataPluginConsistencyAndConcurrency:
    """测试数据生成的一致性和并发安全性。"""

    def test_same_seed_produces_consistent_data(self, default_plugin_metadata):
        """测试相同的种子和配置应生成完全相同的数据。"""
        config1 = MockDataPluginConfig(seed=42, base_prices={"TEST.S": 100.0})
        plugin1 = MockDataPlugin(default_plugin_metadata, config1)

        config2 = MockDataPluginConfig(seed=42, base_prices={"TEST.S": 100.0})
        plugin2 = MockDataPlugin(default_plugin_metadata, config2)

        end_date = "2023-01-10"

        # 第一次调用
        np.random.seed(42)
        random.seed(42)
        df1 = plugin1.get_history_data("TEST.S", count=10, end_date=end_date)

        # 第二次调用前重置种子
        np.random.seed(42)
        random.seed(42)
        df2 = plugin2.get_history_data("TEST.S", count=10, end_date=end_date)

        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_produce_different_data(self, default_plugin_metadata):
        """测试不同的种子应生成不同的数据。"""
        config1 = MockDataPluginConfig(seed=42)
        plugin1 = MockDataPlugin(default_plugin_metadata, config1)

        config2 = MockDataPluginConfig(seed=123)
        plugin2 = MockDataPlugin(default_plugin_metadata, config2)

        df1 = plugin1.get_history_data("TEST.S", count=10)
        df2 = plugin2.get_history_data("TEST.S", count=10)

        assert not df1.equals(df2)

    def test_concurrent_data_access_is_safe(self, default_plugin_metadata):
        """测试多线程并发访问数据生成方法是否线程安全。"""
        plugin = MockDataPlugin(default_plugin_metadata, MockDataPluginConfig(seed=42))
        errors = []

        def worker():
            try:
                df = plugin.get_history_data("TEST.S", count=10)
                assert len(df) <= 10
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrency test failed with errors: {errors}"


class TestMockDataPluginErrorHandling:
    """测试插件的错误处理和边界情况。"""

    @pytest.fixture
    def plugin(self, default_plugin_metadata):
        """提供一个用于错误处理测试的插件实例。"""
        plugin = MockDataPlugin(default_plugin_metadata)
        plugin.initialize()
        return plugin

    def test_disabled_plugin_returns_empty(self, plugin):
        """测试被禁用的插件调用数据接口时返回空结果。"""
        plugin.disable()
        assert plugin.get_history_data("TEST.S").empty
        assert plugin.get_multiple_history_data(["TEST.S"]).empty
        assert not plugin.get_current_price(["TEST.S"])
        assert not plugin.get_snapshot(["TEST.S"])

    @pytest.mark.parametrize("count", [0, -1])
    def test_invalid_count_for_history_data(self, plugin, count):
        """测试 get_history_data 的 count 参数为无效值（0或负数）时的行为。"""
        df = plugin.get_history_data("TEST.S", count=count)
        assert df.empty

    def test_empty_security_list_handling(self, plugin):
        """测试向数据接口传入空证券列表时的行为。"""
        assert plugin.get_multiple_history_data([]).empty
        assert not plugin.get_current_price([])
        assert not plugin.get_snapshot([])
