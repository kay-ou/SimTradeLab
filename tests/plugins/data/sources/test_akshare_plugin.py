# -*- coding: utf-8 -*-
"""
AkShare数据源插件测试 - v5.0 架构完整测试版

此测试套件全面验证 AkShareDataSource 的所有功能：
1. 正确实现了 BaseDataSourcePlugin 的所有接口
2. 能正确处理参数、调用模拟的akshare API
3. 能正确处理API返回的数据和异常
4. 配置模型健壮且符合预期
5. 所有新实现的交易日历、快照、基本面数据API
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
        "昨收": [14.5, 19.5],
        "今开": [14.8, 19.8],
        "最高": [15.2, 20.2],
        "最低": [14.3, 19.3],
        "成交量": [1000000, 800000],
        "成交额": [15000000.0, 16000000.0],
        "涨跌额": [0.5, 0.5],
        "涨跌幅": [3.45, 2.56],
        "换手率": [1.5, 1.2],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_trading_days_df() -> pd.DataFrame:
    """创建一个模拟的交易日历DataFrame。"""
    data = {"trade_date": ["2023-01-03", "2023-01-04", "2023-01-05", "2023-01-06"]}
    return pd.DataFrame(data)


@pytest.fixture
def sample_stock_info_df() -> pd.DataFrame:
    """创建一个模拟的股票信息DataFrame。"""
    data = {
        "code": ["000001", "000002"],
        "name": ["平安银行", "万科A"],
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

    def test_config_validation_timeout(self):
        """测试超时参数验证"""
        # 测试最小值
        config = AkShareDataPluginConfig(start_date="2023-01-01", api_timeout=5)
        assert config.api_timeout == 5

        # 测试最大值
        config = AkShareDataPluginConfig(start_date="2023-01-01", api_timeout=120)
        assert config.api_timeout == 120

        # 测试超出范围的值
        with pytest.raises(ValueError):
            AkShareDataPluginConfig(start_date="2023-01-01", api_timeout=3)


class TestAkShareDataSource:
    """测试AkShare数据源插件的完整功能"""

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

    @patch("akshare.stock_zh_a_spot_em")
    def test_plugin_initialization(
        self,
        mock_ak_spot: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_spot_df: pd.DataFrame,
    ):
        """测试插件初始化和元数据方法"""
        mock_ak_spot.return_value = sample_akshare_spot_df
        plugin._on_initialize()
        assert plugin.get_supported_markets() == {MarketType.STOCK_CN}
        assert plugin.get_supported_frequencies() == {
            DataFrequency.DAILY,
            DataFrequency.WEEKLY,
            DataFrequency.MONTHLY,
        }
        assert plugin.get_data_delay() == 0

    # 测试数据源状态检查
    @patch("akshare.stock_zh_a_spot_em")
    def test_is_available_success(
        self,
        mock_ak_spot: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_spot_df: pd.DataFrame,
    ):
        """测试服务可用性检查 - 成功"""
        mock_ak_spot.return_value = sample_akshare_spot_df
        assert plugin.is_available() is True

    @patch("akshare.stock_zh_a_spot_em")
    def test_is_available_failure(
        self, mock_ak_spot: MagicMock, plugin: AkShareDataSource
    ):
        """测试服务可用性检查 - 失败"""
        mock_ak_spot.side_effect = Exception("Network Error")
        assert plugin.is_available() is False

    # 测试历史数据获取
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

    @patch("akshare.stock_zh_a_hist")
    def test_get_history_data_empty_response(
        self, mock_ak_hist: MagicMock, plugin: AkShareDataSource
    ):
        """测试当akshare API返回空数据时的情况"""
        mock_ak_hist.return_value = pd.DataFrame()

        df = plugin.get_history_data(security="000001")

        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @patch("akshare.stock_zh_a_hist")
    def test_get_multiple_history_data(
        self,
        mock_ak_hist: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_hist_df: pd.DataFrame,
    ):
        """测试获取多个证券的历史数据"""
        mock_ak_hist.return_value = sample_akshare_hist_df

        result = plugin.get_multiple_history_data(security_list=["000001", "000002"])

        assert isinstance(result, dict)
        assert "000001" in result
        assert "000002" in result
        assert mock_ak_hist.call_count == 2

    # 测试实时快照功能
    @patch("akshare.stock_zh_a_spot_em")
    def test_get_snapshot_success(
        self,
        mock_ak_spot: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_spot_df: pd.DataFrame,
    ):
        """测试成功获取实时快照"""
        mock_ak_spot.return_value = sample_akshare_spot_df

        snapshot = plugin.get_snapshot(security_list=["000001"])

        mock_ak_spot.assert_called_once()
        assert isinstance(snapshot, dict)
        assert "000001" in snapshot
        assert "last_price" in snapshot["000001"]
        assert snapshot["000001"]["last_price"] == 15.0

    @patch("akshare.stock_zh_a_spot_em")
    def test_get_snapshot_api_error(
        self, mock_ak_spot: MagicMock, plugin: AkShareDataSource
    ):
        """测试获取快照时API错误"""
        mock_ak_spot.side_effect = Exception("Network Error")

        snapshot = plugin.get_snapshot(security_list=["000001"])

        assert isinstance(snapshot, dict)
        assert "000001" in snapshot
        assert snapshot["000001"] == {}

    # 测试当前价格获取
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

    @patch("akshare.stock_zh_a_spot_em")
    def test_get_current_price_api_error(
        self, mock_ak_spot: MagicMock, plugin: AkShareDataSource
    ):
        """测试获取当前价格时API错误"""
        mock_ak_spot.side_effect = Exception("Network Error")

        prices = plugin.get_current_price(security_list=["000001"])

        assert isinstance(prices, dict)
        assert prices == {}

    # 测试交易日历功能
    @patch("akshare.tool_trade_date_hist_sina")
    def test_get_all_trading_days_success(
        self,
        mock_ak_trading_days: MagicMock,
        plugin: AkShareDataSource,
        sample_trading_days_df: pd.DataFrame,
    ):
        """测试成功获取所有交易日"""
        mock_ak_trading_days.return_value = sample_trading_days_df

        trading_days = plugin.get_all_trading_days()

        mock_ak_trading_days.assert_called_once()
        assert isinstance(trading_days, list)
        assert len(trading_days) == 4
        assert "2023-01-03" in trading_days

    @patch("akshare.tool_trade_date_hist_sina")
    def test_get_all_trading_days_api_error(
        self, mock_ak_trading_days: MagicMock, plugin: AkShareDataSource
    ):
        """测试获取交易日时API错误"""
        mock_ak_trading_days.side_effect = Exception("Network Error")

        trading_days = plugin.get_all_trading_days()

        assert isinstance(trading_days, list)
        assert len(trading_days) == 0

    def test_get_trading_day_with_valid_days(self, plugin: AkShareDataSource):
        """测试获取交易日偏移"""
        with patch.object(plugin, "get_all_trading_days") as mock_get_all:
            mock_get_all.return_value = ["2023-01-03", "2023-01-04", "2023-01-05"]

            result = plugin.get_trading_day("2023-01-04", offset=1)
            assert result == "2023-01-05"

            result = plugin.get_trading_day("2023-01-04", offset=-1)
            assert result == "2023-01-03"

    def test_get_trading_day_no_trading_days(self, plugin: AkShareDataSource):
        """测试当无法获取交易日时的降级处理"""
        with patch.object(plugin, "get_all_trading_days") as mock_get_all:
            mock_get_all.return_value = []

            result = plugin.get_trading_day("2023-01-04", offset=1)
            assert result == "2023-01-04"  # 返回原始日期

    def test_get_trading_days_range(self, plugin: AkShareDataSource):
        """测试获取交易日范围"""
        with patch.object(plugin, "get_all_trading_days") as mock_get_all:
            mock_get_all.return_value = [
                "2023-01-03",
                "2023-01-04",
                "2023-01-05",
                "2023-01-06",
            ]

            result = plugin.get_trading_days_range("2023-01-04", "2023-01-05")
            assert result == ["2023-01-04", "2023-01-05"]

    def test_is_trading_day(self, plugin: AkShareDataSource):
        """测试判断是否为交易日"""
        with patch.object(plugin, "get_all_trading_days") as mock_get_all:
            mock_get_all.return_value = ["2023-01-03", "2023-01-04", "2023-01-05"]

            assert plugin.is_trading_day("2023-01-04") is True
            assert plugin.is_trading_day("2023-01-07") is False  # 假设这不是交易日

    def test_is_trading_day_fallback(self, plugin: AkShareDataSource):
        """测试交易日判断的降级处理"""
        with patch.object(plugin, "get_all_trading_days") as mock_get_all:
            mock_get_all.return_value = []

            # 应该降级到工作日判断
            result = plugin.is_trading_day("2023-01-04")  # 周三
            assert isinstance(result, bool)

    # 测试涨跌停状态检查
    @patch("akshare.stock_zh_a_spot_em")
    def test_check_limit_status_success(
        self,
        mock_ak_spot: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_spot_df: pd.DataFrame,
    ):
        """测试成功检查涨跌停状态"""
        mock_ak_spot.return_value = sample_akshare_spot_df

        limit_status = plugin.check_limit_status(security_list=["000001"])

        mock_ak_spot.assert_called_once()
        assert isinstance(limit_status, dict)
        assert "000001" in limit_status
        assert "limit_up" in limit_status["000001"]
        assert "limit_down" in limit_status["000001"]
        assert "current_price" in limit_status["000001"]

    @patch("akshare.stock_zh_a_spot_em")
    def test_check_limit_status_api_error(
        self, mock_ak_spot: MagicMock, plugin: AkShareDataSource
    ):
        """测试检查涨跌停状态时API错误"""
        mock_ak_spot.side_effect = Exception("Network Error")

        limit_status = plugin.check_limit_status(security_list=["000001"])

        assert isinstance(limit_status, dict)
        assert "000001" in limit_status

    # 测试基本面数据获取
    @patch("akshare.stock_financial_analysis_indicator")
    def test_get_fundamentals_income_success(
        self, mock_ak_financial: MagicMock, plugin: AkShareDataSource
    ):
        """测试成功获取基本面数据 - 利润表"""
        mock_data = pd.DataFrame(
            {
                "营业收入": [1000000],
                "净利润": [100000],
                "营业利润": [150000],
            }
        )
        mock_ak_financial.return_value = mock_data

        result = plugin.get_fundamentals(
            security_list=["000001"],
            table="income",
            fields=["revenue", "net_profit"],
            date="2023-12-31",
        )

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "code" in result.columns
        assert "revenue" in result.columns
        assert "net_profit" in result.columns

    @patch("akshare.stock_financial_analysis_indicator")
    def test_get_fundamentals_api_error(
        self, mock_ak_financial: MagicMock, plugin: AkShareDataSource
    ):
        """测试获取基本面数据时API错误"""
        mock_ak_financial.side_effect = Exception("Network Error")

        result = plugin.get_fundamentals(
            security_list=["000001"],
            table="income",
            fields=["revenue"],
            date="2023-12-31",
        )

        assert isinstance(result, pd.DataFrame)
        assert "code" in result.columns
        assert "revenue" in result.columns

    # 测试股票信息获取
    @patch("akshare.stock_info_a_code_name")
    def test_get_security_info_success(
        self,
        mock_ak_info: MagicMock,
        plugin: AkShareDataSource,
        sample_stock_info_df: pd.DataFrame,
    ):
        """测试成功获取股票信息"""
        mock_ak_info.return_value = sample_stock_info_df

        info = plugin.get_security_info(security_list=["000001"])

        mock_ak_info.assert_called_once()
        assert isinstance(info, dict)
        assert "000001" in info
        assert "name" in info["000001"]
        assert "market" in info["000001"]
        assert "type" in info["000001"]

    @patch("akshare.stock_info_a_code_name")
    def test_get_security_info_api_error(
        self, mock_ak_info: MagicMock, plugin: AkShareDataSource
    ):
        """测试获取股票信息时API错误"""
        mock_ak_info.side_effect = Exception("Network Error")

        info = plugin.get_security_info(security_list=["000001"])

        assert isinstance(info, dict)
        assert "000001" in info
        assert info["000001"]["name"] == "股票000001"  # 默认名称

    # 测试生命周期方法
    @patch("akshare.stock_zh_a_spot_em")
    def test_lifecycle_methods(
        self,
        mock_ak_spot: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_spot_df: pd.DataFrame,
    ):
        """测试插件生命周期方法"""
        # 设置mock以避免网络调用
        mock_ak_spot.return_value = sample_akshare_spot_df

        # 这些方法应该能正常调用而不抛出异常
        plugin._on_initialize()
        plugin._on_start()
        plugin._on_stop()

    # 测试字段过滤
    @patch("akshare.stock_zh_a_hist")
    def test_get_history_data_with_fields(
        self,
        mock_ak_hist: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_hist_df: pd.DataFrame,
    ):
        """测试带字段过滤的历史数据获取"""
        mock_ak_hist.return_value = sample_akshare_hist_df

        df = plugin.get_history_data(security="000001", fields=["open", "close"])

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        # 只包含请求的字段
        expected_columns = ["open", "close"]
        for col in expected_columns:
            assert col in df.columns

    # 测试不同频率的数据获取
    @patch("akshare.stock_zh_a_hist")
    def test_get_history_data_different_frequencies(
        self,
        mock_ak_hist: MagicMock,
        plugin: AkShareDataSource,
        sample_akshare_hist_df: pd.DataFrame,
    ):
        """测试不同频率的历史数据获取"""
        mock_ak_hist.return_value = sample_akshare_hist_df

        # 测试周线数据
        df = plugin.get_history_data(security="000001", frequency=DataFrequency.WEEKLY)
        call_args = mock_ak_hist.call_args[1]
        assert call_args["period"] == "weekly"

        # 测试月线数据
        df = plugin.get_history_data(security="000001", frequency=DataFrequency.MONTHLY)
        call_args = mock_ak_hist.call_args[1]
        assert call_args["period"] == "monthly"

    def test_get_history_data_unsupported_frequency(self, plugin: AkShareDataSource):
        """测试不支持的数据频率"""
        with pytest.raises(ValueError, match="不支持的数据频率"):
            plugin.get_history_data(security="000001", frequency=DataFrequency.MINUTE_1)
