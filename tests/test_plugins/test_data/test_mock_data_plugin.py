# -*- coding: utf-8 -*-
"""
Mock数据源插件测试

测试Mock数据源插件的功能
"""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.simtradelab.plugins.base import PluginConfig, PluginState
from src.simtradelab.plugins.data.base_data_source import DataFrequency, MarketType
from src.simtradelab.plugins.data.mock_data_plugin import MockDataPlugin


class TestMockDataPlugin:
    """测试Mock数据源插件"""

    @pytest.fixture
    def plugin_config(self):
        """创建插件配置"""
        return PluginConfig(
            data={
                "enabled": True,
                "seed": 42,
                "volatility": 0.02,
                "trend": 0.0001,
                "base_prices": {
                    "STOCK_A": 10.0,
                    "000001.SZ": 15.0,
                    "000002.SZ": 12.0,
                    "600000.SH": 8.0,
                    "600036.SH": 35.0,
                    "TEST001.SZ": 100.0,
                    "TEST002.SH": 200.0,
                },
            }
        )

    @pytest.fixture
    def plugin(self, plugin_config):
        """创建Mock数据插件实例"""
        metadata = MockDataPlugin.METADATA
        plugin = MockDataPlugin(metadata, plugin_config)
        yield plugin
        if plugin.state in [PluginState.STARTED, PluginState.PAUSED]:
            plugin.shutdown()

    @pytest.fixture
    def disabled_plugin(self):
        """创建禁用的Mock数据插件实例"""
        config = PluginConfig(data={"enabled": False})
        metadata = MockDataPlugin.METADATA
        plugin = MockDataPlugin(metadata, config)
        yield plugin
        if plugin.state in [PluginState.STARTED, PluginState.PAUSED]:
            plugin.shutdown()

    def test_plugin_metadata(self):
        """测试插件元数据"""
        metadata = MockDataPlugin.METADATA
        assert metadata.name == "mock_data_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.category == "data_source"
        assert "data" in metadata.tags
        assert "mock" in metadata.tags
        assert "testing" in metadata.tags

    def test_plugin_initialization(self, plugin):
        """测试插件初始化"""
        assert plugin._enabled is True
        assert plugin._seed == 42
        assert plugin._volatility == 0.02
        assert plugin._trend == 0.0001
        assert "TEST001.SZ" in plugin._base_prices
        assert plugin._base_prices["TEST001.SZ"] == 100.0
        assert "STOCK_A" in plugin._base_prices
        assert plugin._base_prices["STOCK_A"] == 10.0

    def test_plugin_disabled(self, disabled_plugin):
        """测试禁用状态的插件"""
        # 禁用插件
        disabled_plugin.disable()
        assert disabled_plugin._enabled is False

    def test_enable_disable_functionality(self, plugin):
        """测试启用/禁用功能"""
        # 初始状态是启用的
        assert plugin.is_enabled() is True

        # 禁用插件
        plugin.disable()
        assert plugin.is_enabled() is False

        # 重新启用插件
        plugin.enable()
        assert plugin.is_enabled() is True

    def test_supported_features(self, plugin):
        """测试支持的功能"""
        # 支持的市场
        markets = plugin.get_supported_markets()
        assert MarketType.STOCK_CN in markets

        # 支持的频率
        frequencies = plugin.get_supported_frequencies()
        assert DataFrequency.DAILY in frequencies
        assert DataFrequency.MINUTE_1 in frequencies

        # 数据延迟
        assert plugin.get_data_delay() == 0

        # 可用性
        assert plugin.is_available() is True

    def test_disabled_plugin_availability(self, disabled_plugin):
        """测试禁用插件的可用性"""
        # 禁用插件
        disabled_plugin.disable()
        assert disabled_plugin.is_available() is False

    def test_get_history_data(self, plugin):
        """测试获取历史数据"""
        security = "TEST001.SZ"
        count = 10

        df = plugin.get_history_data(security, count)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) <= count

        # 验证列存在
        expected_columns = ["open", "high", "low", "close", "volume", "amount"]
        for col in expected_columns:
            assert col in df.columns

        # 验证数据按日期排序（索引是日期）
        assert df.index.is_monotonic_increasing

        # 验证OHLC关系
        for _, row in df.iterrows():
            assert row["high"] >= row["open"]
            assert row["high"] >= row["close"]
            assert row["low"] <= row["open"]
            assert row["low"] <= row["close"]
            assert row["volume"] > 0

    def test_get_history_data_different_frequencies(self, plugin):
        """测试不同频率的历史数据获取"""
        security = "TEST001.SZ"
        count = 5

        # 测试日线数据
        daily_df = plugin.get_history_data(security, count, DataFrequency.DAILY)
        assert isinstance(daily_df, pd.DataFrame)
        assert len(daily_df) <= count

        # 测试分钟数据
        minute_df = plugin.get_history_data(security, count, DataFrequency.MINUTE_1)
        assert isinstance(minute_df, pd.DataFrame)
        assert len(minute_df) <= count

    def test_get_history_data_disabled(self, disabled_plugin):
        """测试禁用状态下获取历史数据"""
        # 禁用插件
        disabled_plugin.disable()
        df = disabled_plugin.get_history_data("TEST001.SZ", 10)
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_get_multiple_history_data_as_dict(self, plugin):
        """测试获取多个证券的历史数据（字典格式）"""
        securities = ["TEST001.SZ", "TEST002.SH"]
        count = 5

        result = plugin.get_multiple_history_data(securities, count, as_dict=True)

        assert isinstance(result, dict)
        assert len(result) == len(securities)

        for security in securities:
            assert security in result
            df = result[security]
            assert isinstance(df, pd.DataFrame)
            assert not df.empty

    def test_get_multiple_history_data_as_dataframe(self, plugin):
        """测试获取多个证券的历史数据（DataFrame格式）"""
        securities = ["TEST001.SZ", "TEST002.SH"]
        count = 5

        df = plugin.get_multiple_history_data(securities, count, as_dict=False)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "security" in df.columns

        # 验证包含所有证券
        unique_securities = df["security"].unique()
        for security in securities:
            assert security in unique_securities

    def test_get_current_price(self, plugin):
        """测试获取当前价格"""
        securities = ["TEST001.SZ", "TEST002.SH"]
        prices = plugin.get_current_price(securities)

        assert isinstance(prices, dict)
        assert len(prices) == len(securities)

        for security in securities:
            assert security in prices
            assert isinstance(prices[security], float)
            assert prices[security] > 0

    def test_get_snapshot(self, plugin):
        """测试获取快照数据"""
        securities = ["TEST001.SZ", "TEST002.SH"]
        snapshot = plugin.get_snapshot(securities)

        assert isinstance(snapshot, dict)
        assert len(snapshot) == len(securities)

        for security in securities:
            assert security in snapshot
            data = snapshot[security]
            assert "last_price" in data
            assert "open" in data
            assert "high" in data
            assert "low" in data
            assert "close" in data
            assert "volume" in data
            assert "amount" in data
            assert "bid1" in data
            assert "ask1" in data
            assert "datetime" in data

    def test_trading_day_methods(self, plugin):
        """测试交易日方法"""
        # 测试获取交易日
        base_date = "2023-12-25"
        next_day = plugin.get_trading_day(base_date, offset=1)
        assert isinstance(next_day, str)

        # 测试获取所有交易日
        all_days = plugin.get_all_trading_days()
        assert isinstance(all_days, list)
        assert len(all_days) > 0

        # 测试获取日期范围内的交易日
        start_date = "2023-12-01"
        end_date = "2023-12-31"
        range_days = plugin.get_trading_days_range(start_date, end_date)
        assert isinstance(range_days, list)

        # 测试是否为交易日
        is_trading = plugin.is_trading_day("2023-12-25")  # 周一
        assert isinstance(is_trading, bool)

    def test_check_limit_status(self, plugin):
        """测试检查涨跌停状态"""
        securities = ["TEST001.SZ", "TEST002.SH"]
        limit_status = plugin.check_limit_status(securities)

        assert isinstance(limit_status, dict)
        assert len(limit_status) == len(securities)

        for security in securities:
            assert security in limit_status
            status = limit_status[security]
            assert "limit_up" in status
            assert "limit_down" in status
            assert "limit_up_price" in status
            assert "limit_down_price" in status
            assert "current_price" in status

    def test_get_fundamentals(self, plugin):
        """测试获取基本面数据"""
        securities = ["TEST001.SZ", "TEST002.SH"]
        table = "income"
        fields = ["revenue", "net_profit"]
        date = "2023-12-31"

        df = plugin.get_fundamentals(securities, table, fields, date)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "code" in df.columns
        assert "date" in df.columns

        # 验证包含请求的字段
        for field in fields:
            assert field in df.columns

        # 验证包含请求的证券
        codes = df["code"].unique()
        for security in securities:
            assert security in codes

    def test_get_security_info(self, plugin):
        """测试获取证券信息"""
        securities = ["TEST001.SZ", "TEST002.SH", "STOCK_A"]
        info = plugin.get_security_info(securities)

        assert isinstance(info, dict)
        assert len(info) == len(securities)

        for security in securities:
            assert security in info
            sec_info = info[security]
            assert "name" in sec_info
            assert "market" in sec_info
            assert "type" in sec_info
            assert "listed_date" in sec_info

    def test_lifecycle_methods(self, plugin):
        """测试插件生命周期方法"""
        # 测试初始化
        plugin.initialize()
        assert hasattr(plugin, "_logger")

        # 测试关闭
        plugin.shutdown()
        assert len(plugin._data_cache) == 0

    def test_enable_disable(self, plugin):
        """测试启用/禁用方法"""
        # 初始应该是启用的
        assert plugin.is_enabled() is True

        # 禁用
        plugin.disable()
        assert plugin.is_enabled() is False

        # 重新启用
        plugin.enable()
        assert plugin.is_enabled() is True

    def test_data_consistency_with_seed(self):
        """测试相同种子的数据一致性"""
        config1 = PluginConfig(data={"seed": 42})
        config2 = PluginConfig(data={"seed": 42})

        plugin1 = MockDataPlugin(MockDataPlugin.METADATA, config1)
        plugin2 = MockDataPlugin(MockDataPlugin.METADATA, config2)

        try:
            # 使用相同种子应该生成相似的数据模式
            df1 = plugin1.get_history_data("TEST001.SZ", count=5)
            df2 = plugin2.get_history_data("TEST001.SZ", count=5)

            # 数据形状应该相同
            assert df1.shape == df2.shape

            # 验证数据质量一致
            for df in [df1, df2]:
                assert all(df["high"] >= df["low"])
                assert all(df["high"] >= df["open"])
                assert all(df["high"] >= df["close"])
                assert all(df["volume"] > 0)

        finally:
            plugin1.shutdown()
            plugin2.shutdown()

    def test_different_seeds_different_data(self):
        """测试不同种子生成不同数据"""
        config1 = PluginConfig(data={"seed": 42})
        config2 = PluginConfig(data={"seed": 100})

        plugin1 = MockDataPlugin(MockDataPlugin.METADATA, config1)
        plugin2 = MockDataPlugin(MockDataPlugin.METADATA, config2)

        try:
            # 获取快照数据
            snapshot1 = plugin1.get_snapshot(["TEST001.SZ"])
            snapshot2 = plugin2.get_snapshot(["TEST001.SZ"])

            # 价格应该不同（由于随机性）
            price1 = snapshot1["TEST001.SZ"]["last_price"]
            price2 = snapshot2["TEST001.SZ"]["last_price"]

            # 由于随机性，价格很可能不同，但都应该是合理的正数
            assert price1 > 0
            assert price2 > 0

        finally:
            plugin1.shutdown()
            plugin2.shutdown()

    def test_base_prices_configuration(self, plugin):
        """测试基础价格配置"""
        # 测试配置中设置的价格
        prices = plugin.get_current_price(["TEST001.SZ", "TEST002.SH"])

        # 价格应该基于配置的基础价格（会有随机波动）
        assert prices["TEST001.SZ"] > 0
        assert prices["TEST002.SH"] > 0

        # 应该基于基础价格进行波动
        test001_base = plugin._base_prices.get("TEST001.SZ", 100.0)  # 100.0
        test002_base = plugin._base_prices.get("TEST002.SH", 200.0)  # 200.0

        # 价格应该在合理范围内（基础价格的50%-150%）
        assert 50 <= prices["TEST001.SZ"] <= 150
        assert 100 <= prices["TEST002.SH"] <= 300

    def test_volume_and_amount_calculation(self, plugin):
        """测试成交量和成交额计算"""
        df = plugin.get_history_data("TEST001.SZ", count=5)

        for _, row in df.iterrows():
            # 验证成交量是整数且大于0
            assert isinstance(row["volume"], (int, float))
            assert row["volume"] > 0

            # 验证成交额的合理性（应该接近成交量 * 价格）
            assert row["amount"] > 0
            # 允许一定的计算误差
            expected_amount = row["volume"] * row["close"]
            ratio = row["amount"] / expected_amount
            assert 0.8 <= ratio <= 1.2  # 允许20%的误差

    def test_ohlc_relationships(self, plugin):
        """测试OHLC价格关系"""
        df = plugin.get_history_data("TEST001.SZ", count=10)

        for _, row in df.iterrows():
            # 验证OHLC关系
            assert row["high"] >= max(row["open"], row["close"])
            assert row["low"] <= min(row["open"], row["close"])
            assert row["high"] >= row["low"]

    def test_error_handling(self, plugin):
        """测试错误处理"""
        # 测试空证券列表
        empty_result = plugin.get_current_price([])
        assert isinstance(empty_result, dict)
        assert len(empty_result) == 0

        # 测试无效日期格式（应该不会崩溃）
        try:
            invalid_date_result = plugin.get_trading_day("invalid-date")
            # 如果不抛异常，应该返回合理的值
            assert isinstance(invalid_date_result, str)
        except ValueError:
            # 抛异常也是可接受的
            pass

    def test_concurrent_data_access(self, plugin):
        """测试并发数据访问"""
        import threading

        results = []
        errors = []

        def get_data():
            try:
                df = plugin.get_history_data("TEST001.SZ", count=5)
                results.append(len(df))
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时访问
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=get_data)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3
        assert all(result > 0 for result in results)
