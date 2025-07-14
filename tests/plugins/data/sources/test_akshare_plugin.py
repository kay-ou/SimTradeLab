# -*- coding: utf-8 -*-
"""
AkShare数据源插件测试 - v5.0 架构对齐版

此测试套件旨在验证重写后的 AkShareDataSource 是否：
1.  正确实现了 BaseDataSourcePlugin 的接口。
2.  能正确处理参数、调用模拟的akshare API。
import datetime
import datetime
3.  能正确处理API返回的数据和异常。
4.  配置模型健壮且符合预期。
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from simtradelab.plugins.base import PluginMetadata
from simtradelab.plugins.data.base_data_source import DataFrequency, MarketType
from simtradelab.plugins.data.sources.akshare_plugin import (
    AkShareDataPluginConfig,
    AkShareDataSource,
)


@pytest.fixture
def sample_akshare_hist_df() -> pd.DataFrame:
    """创建一个模拟的akshare.stock_zh_a_hist返回的DataFrame。"""
    data = {
        "日期": pd.to_datetime(["2023-01-03", "2023-01-04"]),
        "开盘": [10.0, 10.5],
        "收盘": [10.4, 10.8],
        "最高": [10.6, 11.0],
        "最低": [9.9, 10.4],
        "成交量": [10000, 12000],
        "成交额": [102000.0, 130000.0],
        "振幅": [0.7, 0.6],
        "涨跌幅": [0.04, 0.038],
        "涨跌额": [0.4, 0.4],
        "换手率": [0.01, 0.012],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_akshare_spot_df() -> pd.DataFrame:
    """创建一个模拟的akshare.stock_zh_a_spot_em返回的DataFrame。"""
    data = {
        "代码": ["000001", "000002"],
        "名称": ["平安银行", "万科A"],
        "最新价": [15.0, 20.0],
    }
    return pd.DataFrame(data)


class TestAkShareDataPluginConfig:
    """测试AkShare数据插件配置模型"""

    def test_config_creation_with_defaults(self):
        """测试配置创建和默认值"""
        config = AkShareDataPluginConfig(start_date="2023-01-01")
        assert config.start_date == "2023-01-01"
        assert config.api_timeout == 30
        assert config.cache_enabled is True
        assert datetime.strptime(config.end_date, "%Y-%m-%d")

    def test_config_validation_date_range(self):
        """测试日期范围验证"""
        with pytest.raises(ValueError, match="end_date 必须在 start_date 之后"):
            AkShareDataPluginConfig(start_date="2023-12-31", end_date="2023-01-01")


class TestAkShareDataSource:
    """测试重写后的AkShare数据源插件"""

    @pytest.fixture
    def config(self) -> AkShareDataPluginConfig:
        """创建测试配置"""
        return AkShareDataPluginConfig(start_date="2023-01-01", end_date="2023-12-31")

    @pytest.fixture
    def plugin(self, config: AkShareDataPluginConfig) -> AkShareDataSource:
        """创建AkShare数据源插件实例"""
        metadata = PluginMetadata(
            name="akshare_data_source",
            version="2.0.0",
            description="AkShare数据源插件",
            author="SimTradeLab Team",
        )
        return AkShareDataSource(metadata, config)

    def test_plugin_initialization(self, plugin: AkShareDataSource):
        """测试插件初始化和元数据方法"""
        plugin._on_initialize()
        assert plugin.get_supported_markets() == {MarketType.STOCK_CN}
        assert plugin.get_supported_frequencies() == {
            DataFrequency.DAILY,
            DataFrequency.WEEKLY,
            DataFrequency.MONTHLY,
        }
        assert plugin.get_data_delay() == 0
        assert plugin.is_available() is True  # 暂时返回True

    @patch("akshare.stock_zh_a_hist")
    def test_get_history_data_success(
        self,
        mock_ak_hist: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_hist_df: pd.DataFrame,
    ):
        """测试成功获取历史数据"""
        mock_ak_hist.return_value = sample_akshare_hist_df

        df = plugin.get_history_data(security="000001")

        # 验证akshare接口被正确调用
        mock_ak_hist.assert_called_once()
        call_args = mock_ak_hist.call_args[1]
        assert call_args["symbol"] == "000001"
        assert call_args["period"] == "daily"
        assert call_args["adjust"] == "qfq"

        # 验证返回的DataFrame格式正确
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert df.index.name == "date"
        expected_columns = ["open", "close", "high", "low", "volume", "amount"]
        for col in expected_columns:
            assert col in df.columns

    @patch("akshare.stock_zh_a_hist")
    def test_get_history_data_api_error(
        self, mock_ak_hist: MagicMock, plugin: AkShareDataSource
    ):
        """测试当akshare API返回异常时的情况"""
        mock_ak_hist.side_effect = Exception("Network Error")

        df = plugin.get_history_data(security="000001")

        # 验证返回的是一个空的DataFrame
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("akshare.stock_zh_a_spot_em")
    def test_get_current_price_success(
        self,
        mock_ak_spot: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_spot_df: pd.DataFrame,
    ):
        """测试成功获取当前价格"""
        mock_ak_spot.return_value = sample_akshare_spot_df

        prices = plugin.get_current_price(security_list=["000001"])

        mock_ak_spot.assert_called_once()
        assert isinstance(prices, dict)
        assert "000001" in prices
        assert prices["000001"] == 15.0

    def test_unimplemented_methods(self, plugin: AkShareDataSource):
        """测试尚未实现的方法会抛出NotImplementedError"""
        with pytest.raises(NotImplementedError):
            plugin.get_snapshot(security_list=["000001"])
        with pytest.raises(NotImplementedError):
            plugin.get_trading_day(date="2023-01-01")
        with pytest.raises(NotImplementedError):
            plugin.get_fundamentals([], "", [], "")
