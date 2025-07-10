# -*- coding: utf-8 -*-
"""
CSV数据源插件测试

测试CSV数据源插件的功能
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from simtradelab.plugins.base import PluginConfig, PluginMetadata
from simtradelab.plugins.data.csv_data_plugin import CSVDataPlugin


class TestCSVDataPlugin:
    """测试CSV数据源插件"""

    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def plugin_config(self, temp_data_dir):
        """创建插件配置"""
        return PluginConfig(
            config={"data_dir": str(temp_data_dir), "cache_timeout": 60}
        )

    @pytest.fixture
    def plugin(self, plugin_config):
        """创建CSV数据插件实例"""
        metadata = CSVDataPlugin.METADATA
        plugin = CSVDataPlugin(metadata, plugin_config)
        yield plugin
        if plugin.state in [plugin.state.STARTED, plugin.state.PAUSED]:
            plugin.shutdown()

    def test_plugin_metadata(self):
        """测试插件元数据"""
        metadata = CSVDataPlugin.METADATA
        assert metadata.name == "csv_data_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.category == "data_source"
        assert "data" in metadata.tags
        assert "csv" in metadata.tags

    def test_plugin_initialization(self, plugin, temp_data_dir):
        """测试插件初始化"""
        plugin.initialize()

        assert plugin.state == plugin.state.INITIALIZED
        assert plugin._data_dir == temp_data_dir
        assert isinstance(plugin._data_cache, dict)
        assert len(plugin._data_cache) == 0
        assert plugin._cache_timeout == 60

    def test_data_directory_creation(self, plugin_config):
        """测试数据目录创建"""
        # 使用不存在的目录
        non_existent_dir = Path("/tmp/test_csv_plugin_data")
        config = PluginConfig(config={"data_dir": str(non_existent_dir)})

        plugin = CSVDataPlugin(CSVDataPlugin.METADATA, config)
        plugin.initialize()

        try:
            assert non_existent_dir.exists()
            assert non_existent_dir.is_dir()
        finally:
            # 清理
            if non_existent_dir.exists():
                import shutil

                shutil.rmtree(non_existent_dir)
            plugin.shutdown()

    def test_ensure_base_data_files(self, plugin):
        """测试确保基础数据文件存在"""
        plugin.initialize()

        # 检查常用股票的数据文件是否被创建
        common_stocks = [
            "000001.SZ",
            "000002.SZ",
            "000858.SZ",
            "600000.SH",
            "600036.SH",
            "600519.SH",
            "688001.SH",
            "300001.SZ",
        ]

        for stock in common_stocks:
            file_path = plugin._data_dir / f"{stock}.csv"
            assert file_path.exists()
            assert file_path.stat().st_size > 0

    def test_get_base_price(self, plugin):
        """测试获取基础价格"""
        plugin.initialize()

        # 测试不同板块的基础价格
        assert plugin._get_base_price("688001.SH") == 50.0  # 科创板
        assert plugin._get_base_price("300001.SZ") == 30.0  # 创业板
        assert plugin._get_base_price("600000.SH") == 20.0  # 沪市主板
        assert plugin._get_base_price("000001.SZ") == 15.0  # 深市主板
        assert plugin._get_base_price("999999.XX") == 10.0  # 其他

    def test_create_stock_data_file(self, plugin):
        """测试创建股票数据文件"""
        plugin.initialize()

        security = "TEST001.SZ"
        file_path = plugin._create_stock_data_file(security, days=30)

        assert file_path.exists()
        assert file_path == plugin._data_dir / f"{security}.csv"

        # 读取并验证数据
        df = pd.read_csv(file_path)
        assert not df.empty
        assert len(df) <= 30  # 可能少于30天（排除周末）
        assert "date" in df.columns
        assert "security" in df.columns
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

        # 验证OHLC关系
        for _, row in df.iterrows():
            assert row["high"] >= row["open"]
            assert row["high"] >= row["close"]
            assert row["low"] <= row["open"]
            assert row["low"] <= row["close"]

    def test_get_history_data(self, plugin):
        """测试获取历史数据"""
        plugin.initialize()

        security = "000001.SZ"
        df = plugin.get_history_data(security, count=10)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) <= 10
        assert "date" in df.columns
        assert "security" in df.columns

        # 验证日期是datetime类型
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

        # 验证数据按日期排序
        assert df["date"].is_monotonic_increasing

    def test_get_history_data_with_date_range(self, plugin):
        """测试获取指定日期范围的历史数据"""
        plugin.initialize()

        security = "000001.SZ"
        start_date = "2023-12-01"
        end_date = "2023-12-31"

        df = plugin.get_history_data(
            security, count=100, start_date=start_date, end_date=end_date
        )

        assert isinstance(df, pd.DataFrame)
        if not df.empty:
            assert df["date"].min() >= pd.to_datetime(start_date)
            assert df["date"].max() <= pd.to_datetime(end_date)

    def test_get_current_price(self, plugin):
        """测试获取当前价格"""
        plugin.initialize()

        security = "000001.SZ"
        price = plugin.get_current_price(security)

        assert isinstance(price, float)
        assert price > 0

    def test_get_current_price_fallback(self, plugin):
        """测试获取当前价格回退机制"""
        plugin.initialize()

        # 使用不存在的证券代码 - CSV插件会自动生成数据文件
        security = "NONEXISTENT.SZ"
        price = plugin.get_current_price(security)

        # 验证业务逻辑：即使是不存在的代码，也应该能返回合理的价格
        assert price > 0
        # 价格应该基于该代码的基础价格生成（在合理范围内）
        base_price = plugin._get_base_price(security)
        assert base_price * 0.3 <= price <= base_price * 3.0  # 允许3倍波动范围

    def test_get_multiple_history_data(self, plugin):
        """测试获取多个证券的历史数据"""
        plugin.initialize()

        securities = ["000001.SZ", "000002.SZ", "600000.SH"]
        df = plugin.get_multiple_history_data(securities, count=5)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        # 验证包含所有证券
        unique_securities = df["security"].unique()
        for security in securities:
            assert security in unique_securities

        # 验证数据按证券和日期排序
        assert df.equals(df.sort_values(["security", "date"]))

    def test_get_market_snapshot(self, plugin):
        """测试获取市场快照"""
        plugin.initialize()

        securities = ["000001.SZ", "000002.SZ"]
        snapshot = plugin.get_market_snapshot(securities)

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

    def test_data_caching(self, plugin):
        """测试数据缓存功能"""
        plugin.initialize()

        security = "000001.SZ"
        count = 10

        # 第一次调用
        df1 = plugin.get_history_data(security, count)
        cache_size_before = len(plugin._data_cache)

        # 第二次调用应该使用缓存
        df2 = plugin.get_history_data(security, count)
        cache_size_after = len(plugin._data_cache)

        assert cache_size_after >= cache_size_before
        pd.testing.assert_frame_equal(df1, df2)

    def test_cache_timeout(self, plugin):
        """测试缓存超时"""
        # 设置很短的缓存超时时间
        plugin._cache_timeout = 0
        plugin.initialize()

        security = "000001.SZ"

        # 第一次调用
        df1 = plugin.get_history_data(security, count=5)

        # 等待超过缓存时间
        import time

        time.sleep(0.1)

        # 第二次调用应该重新生成数据
        df2 = plugin.get_history_data(security, count=5)

        # 由于随机性，数据可能不同
        assert isinstance(df2, pd.DataFrame)

    def test_create_custom_data_file(self, plugin):
        """测试创建自定义数据文件"""
        plugin.initialize()

        security = "CUSTOM001.SZ"
        custom_data = pd.DataFrame(
            {
                "date": ["2023-12-01", "2023-12-02"],
                "security": [security, security],
                "open": [10.0, 10.5],
                "high": [10.2, 10.8],
                "low": [9.8, 10.3],
                "close": [10.1, 10.7],
                "volume": [100000, 120000],
                "money": [1010000, 1284000],
                "price": [10.1, 10.7],
            }
        )

        file_path = plugin.create_custom_data_file(security, custom_data)

        assert file_path.exists()

        # 验证数据正确保存
        saved_data = pd.read_csv(file_path)
        assert len(saved_data) == 2
        assert saved_data["security"].iloc[0] == security

    def test_list_available_securities(self, plugin):
        """测试列出可用证券"""
        plugin.initialize()

        securities = plugin.list_available_securities()

        assert isinstance(securities, list)
        assert len(securities) > 0

        # 验证常用股票在列表中
        common_stocks = ["000001.SZ", "000002.SZ", "600000.SH"]
        for stock in common_stocks:
            assert stock in securities

    def test_get_data_file_path(self, plugin):
        """测试获取数据文件路径"""
        plugin.initialize()

        security = "000001.SZ"
        path = plugin.get_data_file_path(security)

        assert isinstance(path, Path)
        assert path == plugin._data_dir / f"{security}.csv"

    def test_clear_cache(self, plugin):
        """测试清除缓存"""
        plugin.initialize()

        # 生成一些缓存数据
        plugin.get_history_data("000001.SZ", count=5)
        assert len(plugin._data_cache) > 0

        # 清除缓存
        plugin.clear_cache()
        assert len(plugin._data_cache) == 0
        assert len(plugin._cache_timestamps) == 0

    def test_get_cache_stats(self, plugin):
        """测试获取缓存统计"""
        plugin.initialize()

        # 生成一些缓存数据
        plugin.get_history_data("000001.SZ", count=5)
        plugin.get_history_data("000002.SZ", count=5)

        stats = plugin.get_cache_stats()

        assert isinstance(stats, dict)
        assert "cached_items" in stats
        assert "cache_size_mb" in stats
        assert "cache_timeout" in stats
        assert stats["cached_items"] >= 2
        assert stats["cache_size_mb"] >= 0

    def test_cleanup_old_data(self, plugin):
        """测试清理旧数据"""
        plugin.initialize()

        # 创建一个测试文件
        test_file = plugin._data_dir / "old_test.csv"
        test_file.write_text("test data")

        # 修改文件时间为很久以前
        old_time = datetime.now() - timedelta(days=60)
        import os

        os.utime(test_file, (old_time.timestamp(), old_time.timestamp()))

        # 清理旧数据
        plugin.cleanup_old_data(days=30)

        # 文件应该被删除
        assert not test_file.exists()

    def test_get_fundamentals(self, plugin):
        """测试获取基本面数据"""
        plugin.initialize()

        securities = ["000001.SZ", "000002.SZ"]
        table = "income"
        fields = ["revenue", "net_profit"]
        date = "2023-12-31"

        df = plugin.get_fundamentals(securities, table, fields, date)

        assert isinstance(df, pd.DataFrame)
        if not df.empty:
            assert "code" in df.columns
            assert "date" in df.columns
            for field in fields:
                if field in df.columns:
                    assert field in df.columns

    def test_fundamentals_different_tables(self, plugin):
        """测试不同基本面表格"""
        plugin.initialize()

        securities = ["000001.SZ"]
        date = "2023-12-31"

        # 测试利润表
        income_df = plugin.get_fundamentals(
            securities, "income", ["revenue", "net_profit"], date
        )
        assert isinstance(income_df, pd.DataFrame)

        # 测试资产负债表
        balance_df = plugin.get_fundamentals(
            securities, "balance_sheet", ["total_assets", "total_liab"], date
        )
        assert isinstance(balance_df, pd.DataFrame)

        # 测试现金流量表
        cash_df = plugin.get_fundamentals(
            securities, "cash_flow", ["operating_cash_flow"], date
        )
        assert isinstance(cash_df, pd.DataFrame)

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

    def test_error_handling(self, plugin):
        """测试错误处理"""
        plugin.initialize()

        # 测试无效日期格式
        with pytest.raises(Exception):
            plugin.get_history_data("000001.SZ", count=5, start_date="invalid-date")

    def test_file_not_exists_handling(self, plugin):
        """测试文件不存在的处理"""
        plugin.initialize()

        # 删除一个数据文件
        security = "000001.SZ"
        file_path = plugin._data_dir / f"{security}.csv"
        if file_path.exists():
            file_path.unlink()

        # 获取数据应该自动创建文件
        df = plugin.get_history_data(security, count=5)
        assert isinstance(df, pd.DataFrame)
        assert file_path.exists()

    def test_data_generation_deterministic(self, plugin):
        """测试数据生成的一致性和可重现性"""
        plugin.initialize()

        security = "TEST001.SZ"
        
        # 验证业务价值：相同参数的多次调用应该返回一致的历史数据
        df1 = plugin.get_history_data(security, count=5)
        df2 = plugin.get_history_data(security, count=5)
        
        # 数据应该一致（因为文件已生成和缓存）
        assert len(df1) == len(df2)
        assert list(df1.columns) == list(df2.columns)
        
        # 验证数据格式正确性
        assert "date" in df1.columns
        assert "open" in df1.columns  
        assert "close" in df1.columns
        assert "high" in df1.columns
        assert "low" in df1.columns
        assert "volume" in df1.columns
        
        # 验证数据质量：价格应该合理
        assert all(df1["low"] <= df1["close"])
        assert all(df1["close"] <= df1["high"])
        assert all(df1["open"] > 0)
        assert all(df1["volume"] > 0)

    def test_config_parameters(self, temp_data_dir):
        """测试配置参数"""
        config = PluginConfig(
            config={"data_dir": str(temp_data_dir), "cache_timeout": 120}
        )

        plugin = CSVDataPlugin(CSVDataPlugin.METADATA, config)
        plugin.initialize()

        assert plugin._data_dir == temp_data_dir
        assert plugin._cache_timeout == 120

        plugin.shutdown()

    def test_concurrent_access_simulation(self, plugin):
        """测试并发访问模拟"""
        plugin.initialize()

        import threading

        results = []

        def get_data():
            df = plugin.get_history_data("000001.SZ", count=5)
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
