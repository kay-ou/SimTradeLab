# -*- coding: utf-8 -*-
"""
研究服务测试
"""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.services import ResearchService
from simtradelab.core.event_bus import EventBus
from simtradelab.plugins.data import DataSourceManager


class TestResearchService:
    """研究服务测试类"""

    def setup_method(self):
        """设置测试环境"""
        # 模拟事件总线
        self.event_bus = Mock(spec=EventBus)

        # 模拟上下文
        self.context = Mock(spec=PTradeContext)
        self.context.universe = ["000001.XSHE", "000002.XSHE"]

        # 模拟插件管理器
        self.plugin_manager = Mock()

        # 创建服务实例
        self.service = ResearchService(
            context=self.context,
            plugin_manager=self.plugin_manager,
            event_bus=self.event_bus,
        )

    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service.context == self.context
        assert self.service.event_bus == self.event_bus
        assert self.service._plugin_manager == self.plugin_manager
        # 验证DataSourceManager已初始化
        assert hasattr(self.service, "_data_source_manager")
        assert isinstance(self.service._data_source_manager, DataSourceManager)

    def test_get_indicators_plugin_by_name(self):
        """测试通过名称找到技术指标插件"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        mock_indicators_plugin.metadata = Mock()
        mock_indicators_plugin.metadata.name = "technical_indicators_plugin"

        self.plugin_manager.get_all_plugins.return_value = {
            "indicators_plugin": mock_indicators_plugin
        }

        result = self.service._get_indicators_plugin()
        assert result == mock_indicators_plugin

    def test_get_indicators_plugin_by_methods(self):
        """测试通过方法找到技术指标插件"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        mock_indicators_plugin.calculate_macd = Mock()
        mock_indicators_plugin.calculate_kdj = Mock()
        mock_indicators_plugin.calculate_rsi = Mock()
        mock_indicators_plugin.calculate_cci = Mock()

        # 设置metadata属性
        mock_indicators_plugin.metadata = Mock()
        mock_indicators_plugin.metadata.name = "other_plugin"
        mock_indicators_plugin.metadata.tags = ["indicators", "technical"]

        self.plugin_manager.get_all_plugins.return_value = {
            "indicators_plugin": mock_indicators_plugin
        }

        result = self.service._get_indicators_plugin()
        assert result == mock_indicators_plugin

    def test_get_history_data_with_plugin(self):
        """测试通过DataSourceManager获取历史数据"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        expected_data = pd.DataFrame({"close": [10, 11, 12]})
        mock_data_source_manager.get_history_data.return_value = expected_data

        # 替换服务中的DataSourceManager
        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_history_data(
            count=30,
            frequency="1d",
            security_list=["000001.XSHE"],  # 单个证券，会调用get_history_data
        )

        assert_frame_equal(result, expected_data)
        mock_data_source_manager.get_history_data.assert_called_once()

    def test_get_history_data_no_plugin(self):
        """测试DataSourceManager异常时获取历史数据"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_multiple_history_data.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_history_data(is_dict=False)

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_get_history_data_dict_format(self):
        """测试获取字典格式的历史数据"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_multiple_history_data.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_history_data(is_dict=True)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_get_price_data_single_security(self):
        """测试获取单个证券价格数据"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_current_price.return_value = {"000001.XSHE": 15.5}

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_price_data(security="000001.XSHE")

        assert result == 15.5
        mock_data_source_manager.get_current_price.assert_called_once_with(
            ["000001.XSHE"]
        )

    def test_get_price_data_multiple_securities(self):
        """测试获取多个证券价格数据"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        expected_prices = {"000001.XSHE": 15.5, "000002.XSHE": 12.3}
        mock_data_source_manager.get_current_price.return_value = expected_prices

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_price_data(security=["000001.XSHE", "000002.XSHE"])

        assert result == expected_prices
        mock_data_source_manager.get_current_price.assert_called_once_with(
            ["000001.XSHE", "000002.XSHE"]
        )

    def test_get_price_data_no_plugin(self):
        """测试DataSourceManager异常时获取价格数据"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_current_price.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_price_data(security="000001.XSHE")

        assert result == 10.0  # 默认价格

    def test_get_snapshot_data_with_plugin(self):
        """测试通过DataSourceManager获取快照数据"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        mock_snapshot = {"000001.XSHE": {"last_price": 15.5, "volume": 1000}}
        mock_data_source_manager.get_snapshot.return_value = mock_snapshot

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_snapshot_data(["000001.XSHE"])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["security"] == "000001.XSHE"
        assert result.iloc[0]["last_price"] == 15.5

    def test_get_snapshot_data_no_plugin(self):
        """测试DataSourceManager异常时获取快照数据"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_snapshot.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_snapshot_data(["000001.XSHE"])

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_get_current_data_with_plugin(self):
        """测试通过DataSourceManager获取当前数据"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        mock_snapshot = {
            "000001.XSHE": {
                "last_price": 15.5,
                "open": 15.0,
                "high": 16.0,
                "low": 14.5,
                "volume": 1000,
                "money": 15500,
            }
        }
        mock_data_source_manager.get_snapshot.return_value = mock_snapshot

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_current_data(["000001.XSHE"])

        assert isinstance(result, dict)
        assert "000001.XSHE" in result
        security_data = result["000001.XSHE"]
        assert security_data["price"] == 15.5
        assert security_data["close"] == 15.5
        assert security_data["open"] == 15.0

    def test_get_current_data_use_universe(self):
        """测试使用universe获取当前数据"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        mock_snapshot = {
            "000001.XSHE": {
                "last_price": 15.5,
                "open": 15.0,
                "high": 16.0,
                "low": 14.5,
                "volume": 1000,
                "money": 15500,
            },
            "000002.XSHE": {
                "last_price": 12.3,
                "open": 12.0,
                "high": 12.5,
                "low": 11.8,
                "volume": 800,
                "money": 9840,
            },
        }
        mock_data_source_manager.get_snapshot.return_value = mock_snapshot

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_current_data()  # 不传参数，使用universe

        assert isinstance(result, dict)
        assert len(result) == 2
        assert "000001.XSHE" in result
        assert "000002.XSHE" in result

    def test_get_trading_day_with_plugin(self):
        """测试通过DataSourceManager获取交易日"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_trading_day.return_value = "2023-12-25"

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_trading_day("2023-12-24", offset=1)

        assert result == "2023-12-25"
        mock_data_source_manager.get_trading_day.assert_called_once_with(
            "2023-12-24", 1
        )

    def test_get_trading_day_no_plugin(self):
        """测试DataSourceManager异常时获取交易日"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_trading_day.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_trading_day("2023-12-24")

        assert result == "2023-12-24"  # 返回原日期

    def test_get_all_trading_days_with_plugin(self):
        """测试通过DataSourceManager获取所有交易日"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        expected_days = ["2023-12-25", "2023-12-26", "2023-12-27"]
        mock_data_source_manager.get_all_trading_days.return_value = expected_days

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_all_trading_days()

        assert result == expected_days
        mock_data_source_manager.get_all_trading_days.assert_called_once()

    def test_get_all_trading_days_no_plugin(self):
        """测试DataSourceManager异常时获取所有交易日"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_all_trading_days.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_all_trading_days()

        assert isinstance(result, list)
        assert len(result) == 3  # 模拟数据

    def test_check_limit_status_with_plugin(self):
        """测试通过DataSourceManager检查涨跌停状态"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        mock_limit_data = {
            "000001.XSHE": {
                "limit_up": False,
                "limit_down": False,
                "limit_up_price": 16.5,
                "limit_down_price": 13.5,
                "current_price": 15.0,
            }
        }
        mock_data_source_manager.check_limit_status.return_value = mock_limit_data

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.check_limit_status("000001.XSHE")

        assert isinstance(result, dict)
        assert "000001.XSHE" in result
        assert result["000001.XSHE"]["limit_up"] is False
        assert result["000001.XSHE"]["current_price"] == 15.0

    def test_check_limit_status_no_plugin(self):
        """测试DataSourceManager异常时检查涨跌停状态"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.check_limit_status.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.check_limit_status("000001.XSHE")

        assert isinstance(result, dict)
        assert "000001.XSHE" in result
        assert result["000001.XSHE"]["limit_up"] is False
        assert result["000001.XSHE"]["current_price"] == 15.0

    def test_get_fundamentals_with_plugin(self):
        """测试通过DataSourceManager获取基本面数据"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        expected_data = pd.DataFrame(
            {"code": ["000001.XSHE"], "date": ["2023-12-25"], "revenue": [1000000]}
        )
        mock_data_source_manager.get_fundamentals.return_value = expected_data

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_fundamentals(
            stocks=["000001.XSHE"],
            table="income",
            fields=["revenue"],
            date="2023-12-25",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["code"] == "000001.XSHE"
        assert result.iloc[0]["revenue"] == 1000000

    def test_get_fundamentals_mock_data(self):
        """测试DataSourceManager异常时获取基本面数据"""
        # 模拟DataSourceManager抛出异常
        mock_data_source_manager = Mock()
        mock_data_source_manager.get_fundamentals.side_effect = Exception(
            "Data source error"
        )

        self.service._data_source_manager = mock_data_source_manager

        result = self.service.get_fundamentals(
            stocks=["000001.XSHE"],
            table="income",
            fields=["revenue"],
            date="2023-12-25",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["code"] == "000001.XSHE"
        assert result.iloc[0]["revenue"] == 0.0  # 默认值

    def test_calculate_macd_with_plugin(self):
        """测试通过插件计算MACD"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        expected_macd = pd.DataFrame(
            {
                "MACD": [0.1, 0.2, 0.3],
                "SIGNAL": [0.05, 0.15, 0.25],
                "HISTOGRAM": [0.05, 0.05, 0.05],
            }
        )
        mock_indicators_plugin.calculate_macd.return_value = expected_macd

        with patch.object(
            self.service, "_get_indicators_plugin", return_value=mock_indicators_plugin
        ):
            result = self.service.calculate_macd(np.array([10, 11, 12]))

        assert_frame_equal(result, expected_macd)
        mock_indicators_plugin.calculate_macd.assert_called_once()

    def test_calculate_macd_no_plugin(self):
        """测试无技术指标插件时计算MACD"""
        with patch.object(self.service, "_get_indicators_plugin", return_value=None):
            result = self.service.calculate_macd(np.array([10, 11, 12]))

        assert isinstance(result, pd.DataFrame)
        assert "MACD" in result.columns
        assert "SIGNAL" in result.columns
        assert "HISTOGRAM" in result.columns
        assert len(result) == 3

    def test_calculate_kdj_with_plugin(self):
        """测试通过插件计算KDJ"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        expected_kdj = pd.DataFrame(
            {"K": [50.0, 55.0, 60.0], "D": [50.0, 52.5, 55.8], "J": [50.0, 60.0, 68.4]}
        )
        mock_indicators_plugin.calculate_kdj.return_value = expected_kdj

        with patch.object(
            self.service, "_get_indicators_plugin", return_value=mock_indicators_plugin
        ):
            result = self.service.calculate_kdj(
                np.array([12, 13, 14]), np.array([9, 10, 11]), np.array([10, 11, 12])
            )

        assert_frame_equal(result, expected_kdj)
        mock_indicators_plugin.calculate_kdj.assert_called_once()

    def test_calculate_kdj_no_plugin(self):
        """测试无技术指标插件时计算KDJ"""
        with patch.object(self.service, "_get_indicators_plugin", return_value=None):
            result = self.service.calculate_kdj(
                np.array([12, 13, 14]), np.array([9, 10, 11]), np.array([10, 11, 12])
            )

        assert isinstance(result, pd.DataFrame)
        assert "K" in result.columns
        assert "D" in result.columns
        assert "J" in result.columns
        assert len(result) == 3

    def test_initialize_and_shutdown(self):
        """测试服务初始化和关闭"""
        # 模拟DataSourceManager
        mock_data_source_manager = Mock()
        self.service._data_source_manager = mock_data_source_manager

        # 测试初始化
        self.service.initialize()
        mock_data_source_manager.initialize.assert_called_once()

        # 测试关闭
        self.service.shutdown()
        mock_data_source_manager.shutdown.assert_called_once()
