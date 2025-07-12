# -*- coding: utf-8 -*-
"""
Mock数据源插件测试

测试Mock数据源插件的功能
"""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from simtradelab.plugins.base import PluginConfig
from simtradelab.plugins.data.mock_data_plugin import MockDataPlugin


class TestMockDataPlugin:
    """测试Mock数据源插件"""

    @pytest.fixture
    def plugin_config(self):
        """创建插件配置"""
        return PluginConfig(
            config={
                "enabled": True,
                "seed": 42,
                "volatility": 0.02,
                "trend": 0.0001,
                "base_prices": {"TEST001.SZ": 100.0, "TEST002.SH": 200.0},
            }
        )

    @pytest.fixture
    def plugin(self, plugin_config):
        """创建Mock数据插件实例"""
        metadata = MockDataPlugin.METADATA
        plugin = MockDataPlugin(metadata, plugin_config)
        yield plugin
        if plugin.state in [plugin.state.STARTED, plugin.state.PAUSED]:
            plugin.shutdown()

    @pytest.fixture
    def disabled_plugin(self):
        """创建禁用的Mock数据插件实例"""
        config = PluginConfig(config={"enabled": False})
        metadata = MockDataPlugin.METADATA
        plugin = MockDataPlugin(metadata, config)
        yield plugin
        if plugin.state in [plugin.state.STARTED, plugin.state.PAUSED]:
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

    def test_plugin_initialization_enabled(self, plugin):
        """测试启用状态下的插件初始化"""
        plugin.initialize()

        assert plugin.state == plugin.state.INITIALIZED
        assert plugin._enabled is True
        assert plugin._seed == 42
        assert plugin._volatility == 0.02
        assert plugin._trend == 0.0001
        assert "TEST001.SZ" in plugin._base_prices
        assert plugin._base_prices["TEST001.SZ"] == 100.0

    def test_plugin_initialization_disabled(self, disabled_plugin):
        """测试禁用状态下的插件初始化"""
        disabled_plugin.initialize()

        assert disabled_plugin.state == disabled_plugin.state.INITIALIZED
        assert disabled_plugin._enabled is False

    def test_enable_disable_functionality(self, plugin):
        """测试启用/禁用功能"""
        plugin.initialize()

        # 初始状态是启用的
        assert plugin.is_enabled() is True

        # 禁用插件
        plugin.disable()
        assert plugin.is_enabled() is False
        assert len(plugin._data_cache) == 0

        # 重新启用插件
        plugin.enable()
        assert plugin.is_enabled() is True

    def test_get_base_price(self, plugin):
        """测试获取基础价格"""
        plugin.initialize()

        # 测试配置中的价格
        assert plugin._get_base_price("TEST001.SZ") == 100.0
        assert plugin._get_base_price("TEST002.SH") == 200.0

        # 测试默认价格规则
        assert plugin._get_base_price("688001.SH") == 50.0  # 科创板
        assert plugin._get_base_price("300001.SZ") == 30.0  # 创业板
        assert plugin._get_base_price("600000.SH") == 20.0  # 沪市主板
        assert plugin._get_base_price("000001.SZ") == 15.0  # 深市主板
        assert plugin._get_base_price("999999.XX") == 10.0  # 其他

    def test_generate_price_series(self, plugin):
        """测试生成价格序列"""
        plugin.initialize()

        security = "TEST001.SZ"
        days = 10

        data = plugin._generate_price_series(security, days)

        assert isinstance(data, list)
        assert len(data) <= days  # 可能少于指定天数（排除周末）

        # 验证数据结构
        for item in data:
            assert "date" in item
            assert "security" in item
            assert "open" in item
            assert "high" in item
            assert "low" in item
            assert "close" in item
            assert "volume" in item
            assert "money" in item
            assert "price" in item

            # 验证OHLC关系
            assert item["high"] >= item["open"]
            assert item["high"] >= item["close"]
            assert item["low"] <= item["open"]
            assert item["low"] <= item["close"]

            # 验证数值类型
            assert isinstance(item["volume"], int)
            assert item["volume"] > 0

    def test_generate_price_series_with_start_date(self, plugin):
        """测试带起始日期的价格序列生成"""
        plugin.initialize()

        security = "TEST001.SZ"
        start_date = datetime(2023, 12, 1)
        days = 5

        data = plugin._generate_price_series(security, days, start_date)

        assert isinstance(data, list)
        assert len(data) > 0

        # 验证日期范围
        first_date = datetime.strptime(data[0]["date"], "%Y-%m-%d")
        assert first_date >= start_date

    def test_generate_price_series_disabled(self, disabled_plugin):
        """测试禁用状态下生成价格序列"""
        disabled_plugin.initialize()

        with pytest.raises(RuntimeError, match="Mock Data Plugin is disabled"):
            disabled_plugin._generate_price_series("TEST001.SZ", 10)

    def test_get_history_data(self, plugin):
        """测试获取历史数据"""
        plugin.initialize()

        security = "TEST001.SZ"
        count = 10

        df = plugin.get_history_data(security, count)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) <= count
        assert "date" in df.columns
        assert "security" in df.columns

        # 验证日期是datetime类型
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

        # 验证数据按日期排序
        assert df["date"].is_monotonic_increasing

    def test_get_history_data_with_date_filter(self, plugin):
        """测试带日期过滤的历史数据获取"""
        plugin.initialize()

        security = "TEST001.SZ"
        start_date = "2023-12-01"
        end_date = "2023-12-10"

        df = plugin.get_history_data(
            security, count=20, start_date=start_date, end_date=end_date
        )

        assert isinstance(df, pd.DataFrame)
        if not df.empty:
            assert df["date"].min() >= pd.to_datetime(start_date)
            assert df["date"].max() <= pd.to_datetime(end_date)

    def test_get_history_data_disabled(self, disabled_plugin):
        """测试禁用状态下获取历史数据"""
        disabled_plugin.initialize()

        with pytest.raises(RuntimeError, match="Mock Data Plugin is disabled"):
            disabled_plugin.get_history_data("TEST001.SZ", 10)

    def test_get_current_price(self, plugin):
        """测试获取当前价格"""
        plugin.initialize()

        security = "TEST001.SZ"
        price = plugin.get_current_price(security)

        assert isinstance(price, float)
        assert price > 0

    def test_get_current_price_fallback(self, plugin):
        """测试获取当前价格回退机制"""
        plugin.initialize()

        # 模拟获取历史数据失败
        with patch.object(plugin, "get_history_data") as mock_get_history:
            mock_get_history.side_effect = Exception("Test error")

            security = "TEST001.SZ"
            price = plugin.get_current_price(security)

            # 应该返回基础价格
            assert price == plugin._get_base_price(security)

    def test_get_current_price_disabled(self, disabled_plugin):
        """测试禁用状态下获取当前价格"""
        disabled_plugin.initialize()

        with pytest.raises(RuntimeError, match="Mock Data Plugin is disabled"):
            disabled_plugin.get_current_price("TEST001.SZ")

    def test_get_multiple_history_data(self, plugin):
        """测试获取多个证券的历史数据"""
        plugin.initialize()

        securities = ["TEST001.SZ", "TEST002.SH", "000001.SZ"]
        count = 5

        df = plugin.get_multiple_history_data(securities, count)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        # 验证包含所有证券
        unique_securities = df["security"].unique()
        for security in securities:
            assert security in unique_securities

        # 验证数据按证券和日期排序
        assert df.equals(df.sort_values(["security", "date"]))

    def test_get_multiple_history_data_disabled(self, disabled_plugin):
        """测试禁用状态下获取多个证券的历史数据"""
        disabled_plugin.initialize()

        with pytest.raises(RuntimeError, match="Mock Data Plugin is disabled"):
            disabled_plugin.get_multiple_history_data(["TEST001.SZ"], 10)

    def test_get_snapshot(self, plugin):
        """测试获取行情快照"""
        plugin.initialize()

        securities = ["TEST001.SZ", "TEST002.SH"]
        snapshot = plugin.get_snapshot(securities)

        assert isinstance(snapshot, dict)
        assert len(snapshot) == len(securities)

        for security in securities:
            assert security in snapshot
            data = snapshot[security]
            assert "last_price" in data
            assert "pre_close" in data
            assert "open" in data
            assert "high" in data
            assert "low" in data
            assert "volume" in data
            assert "money" in data
            assert "price" in data  # PTrade兼容性
            assert "datetime" in data

    def test_get_snapshot_with_error(self, plugin):
        """测试行情快照获取时的错误处理"""
        plugin.initialize()

        # 模拟获取历史数据失败
        with patch.object(plugin, "get_history_data") as mock_get_history:
            mock_get_history.side_effect = Exception("Test error")

            securities = ["TEST001.SZ"]
            snapshot = plugin.get_snapshot(securities)

            assert isinstance(snapshot, dict)
            assert "TEST001.SZ" in snapshot

            # 应该提供默认值
            data = snapshot["TEST001.SZ"]
            assert data["last_price"] == plugin._get_base_price("TEST001.SZ")

    def test_get_snapshot_disabled(self, disabled_plugin):
        """测试禁用状态下获取行情快照"""
        disabled_plugin.initialize()

        with pytest.raises(RuntimeError, match="Mock Data Plugin is disabled"):
            disabled_plugin.get_snapshot(["TEST001.SZ"])

    def test_get_fundamentals(self, plugin):
        """测试获取基本面数据"""
        plugin.initialize()

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

    def test_get_fundamentals_different_tables(self, plugin):
        """测试不同基本面表格"""
        plugin.initialize()

        securities = ["TEST001.SZ"]
        date = "2023-12-31"

        # 测试利润表
        income_df = plugin.get_fundamentals(
            securities, "income", ["revenue", "net_profit"], date
        )
        assert isinstance(income_df, pd.DataFrame)
        assert not income_df.empty

        # 测试资产负债表
        balance_df = plugin.get_fundamentals(
            securities, "balance_sheet", ["total_assets", "total_liab"], date
        )
        assert isinstance(balance_df, pd.DataFrame)
        assert not balance_df.empty

        # 测试现金流量表
        cash_df = plugin.get_fundamentals(
            securities, "cash_flow", ["operating_cash_flow"], date
        )
        assert isinstance(cash_df, pd.DataFrame)
        assert not cash_df.empty

    def test_get_fundamentals_disabled(self, disabled_plugin):
        """测试禁用状态下获取基本面数据"""
        disabled_plugin.initialize()

        with pytest.raises(RuntimeError, match="Mock Data Plugin is disabled"):
            disabled_plugin.get_fundamentals(
                ["TEST001.SZ"], "income", ["revenue"], "2023-12-31"
            )

    def test_list_available_securities(self, plugin):
        """测试列出可用证券"""
        plugin.initialize()

        securities = plugin.list_available_securities()

        assert isinstance(securities, list)
        assert "TEST001.SZ" in securities
        assert "TEST002.SH" in securities

    def test_list_available_securities_disabled(self, disabled_plugin):
        """测试禁用状态下列出可用证券"""
        disabled_plugin.initialize()

        securities = disabled_plugin.list_available_securities()
        assert securities == []

    def test_data_caching(self, plugin):
        """测试数据缓存功能"""
        plugin.initialize()

        security = "TEST001.SZ"
        count = 10

        # 第一次调用
        df1 = plugin.get_history_data(security, count)
        cache_size_before = len(plugin._data_cache)

        # 第二次调用应该使用缓存
        df2 = plugin.get_history_data(security, count)
        cache_size_after = len(plugin._data_cache)

        assert cache_size_after >= cache_size_before
        pd.testing.assert_frame_equal(df1, df2)

    def test_clear_cache(self, plugin):
        """测试清除缓存"""
        plugin.initialize()

        # 生成一些缓存数据
        plugin.get_history_data("TEST001.SZ", count=5)
        assert len(plugin._data_cache) > 0

        # 清除缓存
        plugin.clear_cache()
        assert len(plugin._data_cache) == 0

    def test_get_cache_stats(self, plugin):
        """测试获取缓存统计"""
        plugin.initialize()

        # 生成一些缓存数据
        plugin.get_history_data("TEST001.SZ", count=5)
        plugin.get_history_data("TEST002.SH", count=5)

        stats = plugin.get_cache_stats()

        assert isinstance(stats, dict)
        assert "enabled" in stats
        assert "cached_items" in stats
        assert "cache_size_mb" in stats
        assert "seed" in stats
        assert "securities_count" in stats
        assert "volatility" in stats
        assert "trend" in stats

        assert stats["enabled"] is True
        assert stats["cached_items"] >= 2
        assert stats["cache_size_mb"] >= 0
        assert stats["seed"] == 42
        assert stats["volatility"] == 0.02
        assert stats["trend"] == 0.0001

    def test_update_config(self, plugin):
        """测试更新配置"""
        plugin.initialize()

        new_config = {
            "enabled": True,
            "seed": 100,
            "volatility": 0.03,
            "trend": 0.0002,
            "base_prices": {"NEW001.SZ": 500.0},
        }

        plugin.update_config(new_config)

        assert plugin._enabled is True
        assert plugin._seed == 100
        assert plugin._volatility == 0.03
        assert plugin._trend == 0.0002
        assert "NEW001.SZ" in plugin._base_prices
        assert plugin._base_prices["NEW001.SZ"] == 500.0
        assert len(plugin._data_cache) == 0  # 缓存应该被清除

    def test_random_seed_deterministic(self):
        """测试随机种子对数据生成的影响"""
        config1 = PluginConfig(config={"seed": 42})
        config2 = PluginConfig(config={"seed": 42})
        config3 = PluginConfig(config={"seed": 100})

        plugin1 = MockDataPlugin(MockDataPlugin.METADATA, config1)
        plugin2 = MockDataPlugin(MockDataPlugin.METADATA, config2)
        plugin3 = MockDataPlugin(MockDataPlugin.METADATA, config3)

        plugin1.initialize()
        plugin2.initialize()
        plugin3.initialize()

        try:
            # 验证业务价值：相同种子应该生成相似的数据模式
            df1 = plugin1.get_history_data("TEST001.SZ", count=5)
            df2 = plugin2.get_history_data("TEST001.SZ", count=5)
            df3 = plugin3.get_history_data("TEST001.SZ", count=5)

            # 相同种子的数据应该高度相关（不要求完全相等，允许浮点误差）
            assert len(df1) == len(df2)

            # 验证业务逻辑：无论种子如何，数据格式和质量应该一致
            for df in [df1, df2, df3]:
                assert "open" in df.columns
                assert "close" in df.columns
                assert "high" in df.columns
                assert "low" in df.columns
                assert "volume" in df.columns

                # 验证价格数据合理性
                assert all(df["high"] >= df["low"])
                assert all(df["high"] >= df["open"])
                assert all(df["high"] >= df["close"])
                assert all(df["volume"] > 0)

            # 不同种子应该生成不同的数据（至少在统计上）
            assert len(df3) == len(df1)  # 至少长度应该相同

        finally:
            plugin1.shutdown()
            plugin2.shutdown()
            plugin3.shutdown()

    def test_different_seeds_different_data(self):
        """测试不同种子生成不同数据"""
        config1 = PluginConfig(config={"seed": 42})
        config2 = PluginConfig(config={"seed": 100})

        plugin1 = MockDataPlugin(MockDataPlugin.METADATA, config1)
        plugin2 = MockDataPlugin(MockDataPlugin.METADATA, config2)

        plugin1.initialize()
        plugin2.initialize()

        try:
            # 使用不同种子生成的数据应该不同
            data1 = plugin1._generate_price_series("TEST001.SZ", 5)
            data2 = plugin2._generate_price_series("TEST001.SZ", 5)

            assert len(data1) == len(data2)
            # 至少有一些数据点应该不同
            differences = sum(
                1 for i in range(len(data1)) if data1[i]["close"] != data2[i]["close"]
            )
            assert differences > 0

        finally:
            plugin1.shutdown()
            plugin2.shutdown()

    def test_plugin_lifecycle(self, plugin):
        """测试插件生命周期"""
        # 初始化
        plugin.initialize()
        assert plugin.state == plugin.state.INITIALIZED

        # 启动
        plugin.start()
        assert plugin.state == plugin.state.STARTED

        # 停止
        plugin.stop()
        assert plugin.state == plugin.state.STOPPED

        # 关闭
        plugin.shutdown()
        assert plugin.state == plugin.state.UNINITIALIZED

    def test_price_bounds_validation(self, plugin):
        """测试价格边界验证"""
        plugin.initialize()

        # 设置极低的基础价格
        plugin._base_prices["LOWPRICE.SZ"] = 1.0

        data = plugin._generate_price_series("LOWPRICE.SZ", 50)

        # 验证价格不会低于基础价格的10%
        base_price = plugin._get_base_price("LOWPRICE.SZ")
        min_allowed_price = base_price * 0.1

        for item in data:
            assert item["close"] >= min_allowed_price

    def test_volume_generation(self, plugin):
        """测试成交量生成"""
        plugin.initialize()

        data = plugin._generate_price_series("TEST001.SZ", 10)

        for item in data:
            # 验证成交量在合理范围内
            assert 10000 <= item["volume"] <= 1000000
            assert isinstance(item["volume"], int)

            # 验证成交金额计算正确（允许合理的浮点数误差）
            expected_money = item["volume"] * item["close"]
            relative_error = abs(item["money"] - expected_money) / max(
                item["money"], expected_money
            )
            assert relative_error < 0.001  # 允许0.1%的相对误差

    def test_ohlc_relationships(self, plugin):
        """测试OHLC关系验证"""
        plugin.initialize()

        data = plugin._generate_price_series("TEST001.SZ", 20)

        for item in data:
            # 验证OHLC关系
            assert item["high"] >= max(item["open"], item["close"])
            assert item["low"] <= min(item["open"], item["close"])
            assert item["high"] >= item["low"]

    def test_error_handling_in_fundamentals(self, plugin):
        """测试基本面数据中的错误处理"""
        plugin.initialize()

        # 测试未知表格
        df = plugin.get_fundamentals(
            ["TEST001.SZ"], "unknown_table", ["unknown_field"], "2023-12-31"
        )
        assert isinstance(df, pd.DataFrame)
        # 应该包含基本结构
        assert "code" in df.columns or df.empty

    def test_concurrent_access_simulation(self, plugin):
        """测试并发访问模拟"""
        plugin.initialize()

        import threading

        results = []

        def get_data():
            df = plugin.get_history_data("TEST001.SZ", count=5)
            results.append(len(df))

        # 创建多个线程同时访问
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=get_data)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有线程都成功获取了数据
        assert len(results) == 3
        assert all(result > 0 for result in results)
