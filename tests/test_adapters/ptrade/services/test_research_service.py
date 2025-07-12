# -*- coding: utf-8 -*-
"""
研究服务测试
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.simtradelab.adapters.ptrade.services import ResearchService
from src.simtradelab.adapters.ptrade.context import PTradeContext
from src.simtradelab.core.event_bus import EventBus


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
            event_bus=self.event_bus
        )
    
    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service.context == self.context
        assert self.service.event_bus == self.event_bus
        assert self.service._plugin_manager == self.plugin_manager
    
    def test_get_data_plugin_found(self):
        """测试找到数据插件"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        mock_data_plugin.get_history_data = Mock()
        mock_data_plugin.get_current_price = Mock()
        mock_data_plugin.get_snapshot = Mock()
        mock_data_plugin.get_multiple_history_data = Mock()
        
        # 模拟其他插件
        mock_other_plugin = Mock()
        
        self.plugin_manager.get_all_plugins.return_value = {
            "data_plugin": mock_data_plugin,
            "other_plugin": mock_other_plugin
        }
        
        result = self.service._get_data_plugin()
        assert result == mock_data_plugin
    
    def test_get_data_plugin_not_found(self):
        """测试未找到数据插件"""
        self.plugin_manager.get_all_plugins.return_value = {}
        
        result = self.service._get_data_plugin()
        assert result is None
    
    def test_get_data_plugin_no_plugin_manager(self):
        """测试无插件管理器时获取数据插件"""
        service = ResearchService(context=self.context, plugin_manager=None)
        result = service._get_data_plugin()
        assert result is None
    
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
        """测试通过插件获取历史数据"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        expected_data = pd.DataFrame({"close": [10, 11, 12]})
        mock_data_plugin.get_multiple_history_data.return_value = expected_data
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_history_data(
                count=30,
                frequency="1d",
                security_list=["000001.XSHE"]
            )
        
        assert result.equals(expected_data)
        mock_data_plugin.get_multiple_history_data.assert_called_once()
    
    def test_get_history_data_no_plugin(self):
        """测试无插件时获取历史数据"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_history_data(is_dict=False)
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    def test_get_history_data_dict_format(self):
        """测试获取字典格式的历史数据"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_history_data(is_dict=True)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_get_price_data_single_security(self):
        """测试获取单个证券价格"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        mock_data_plugin.get_history_data.return_value = pd.DataFrame({
            "close": [10.0, 11.0, 12.0]
        })
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_price_data(security="000001.XSHE", count=1)
        
        assert result == 12.0  # 最新收盘价
    
    def test_get_price_data_multiple_securities(self):
        """测试获取多个证券价格"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        
        def mock_get_history_data(security, count):
            if security == "000001.XSHE":
                return pd.DataFrame({"close": [10.0]})
            elif security == "000002.XSHE":
                return pd.DataFrame({"close": [20.0]})
            else:
                return pd.DataFrame()
        
        mock_data_plugin.get_history_data.side_effect = mock_get_history_data
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_price_data(
                security=["000001.XSHE", "000002.XSHE"],
                count=1
            )
        
        assert result == {"000001.XSHE": 10.0, "000002.XSHE": 20.0}
    
    def test_get_price_data_no_plugin(self):
        """测试无插件时获取价格数据"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_price_data(security="000001.XSHE")
        
        assert result == 10.0  # 默认价格
    
    def test_get_snapshot_data_with_plugin(self):
        """测试通过插件获取快照数据"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        mock_snapshot = {
            "000001.XSHE": {"price": 10.0, "volume": 1000},
            "000002.XSHE": {"price": 20.0, "volume": 2000}
        }
        mock_data_plugin.get_snapshot.return_value = mock_snapshot
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_snapshot_data(["000001.XSHE", "000002.XSHE"])
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "security" in result.columns
    
    def test_get_snapshot_data_no_plugin(self):
        """测试无插件时获取快照数据"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_snapshot_data(["000001.XSHE"])
        
        assert isinstance(result, pd.DataFrame)
        assert result.empty
    
    def test_get_current_data_with_plugin(self):
        """测试通过插件获取当前数据"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        mock_snapshot = {
            "000001.XSHE": {
                "price": 10.0,
                "open": 9.5,
                "high": 10.5,
                "low": 9.0,
                "volume": 1000,
                "money": 10000.0
            }
        }
        mock_data_plugin.get_snapshot.return_value = mock_snapshot
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_current_data(["000001.XSHE"])
        
        assert "000001.XSHE" in result
        assert result["000001.XSHE"]["price"] == 10.0
        assert result["000001.XSHE"]["close"] == 10.0
    
    def test_get_current_data_use_universe(self):
        """测试使用universe获取当前数据"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_current_data()  # 不指定security_list
        
        assert isinstance(result, dict)
    
    def test_calculate_macd_with_plugin(self):
        """测试通过插件计算MACD"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        expected_macd = pd.DataFrame({
            "MACD": [0.1, 0.2, 0.3],
            "SIGNAL": [0.05, 0.15, 0.25],
            "HISTOGRAM": [0.05, 0.05, 0.05]
        })
        mock_indicators_plugin.calculate_macd.return_value = expected_macd
        
        with patch.object(self.service, '_get_indicators_plugin', return_value=mock_indicators_plugin):
            close_data = np.array([10, 11, 12])
            result = self.service.calculate_macd(close_data)
        
        assert result.equals(expected_macd)
    
    def test_calculate_macd_no_plugin(self):
        """测试无插件时计算MACD"""
        with patch.object(self.service, '_get_indicators_plugin', return_value=None):
            close_data = np.array([10, 11, 12])
            result = self.service.calculate_macd(close_data)
        
        assert isinstance(result, pd.DataFrame)
        assert "MACD" in result.columns
        assert len(result) == len(close_data)
    
    def test_calculate_kdj_with_plugin(self):
        """测试通过插件计算KDJ"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        expected_kdj = pd.DataFrame({
            "K": [20, 30, 40],
            "D": [25, 35, 45],
            "J": [10, 20, 30]
        })
        mock_indicators_plugin.calculate_kdj.return_value = expected_kdj
        
        with patch.object(self.service, '_get_indicators_plugin', return_value=mock_indicators_plugin):
            high_data = np.array([12, 13, 14])
            low_data = np.array([8, 9, 10])
            close_data = np.array([10, 11, 12])
            result = self.service.calculate_kdj(high_data, low_data, close_data)
        
        assert result.equals(expected_kdj)
    
    def test_calculate_rsi_with_plugin(self):
        """测试通过插件计算RSI"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        expected_rsi = pd.DataFrame({"RSI": [30, 40, 50]})
        mock_indicators_plugin.calculate_rsi.return_value = expected_rsi
        
        with patch.object(self.service, '_get_indicators_plugin', return_value=mock_indicators_plugin):
            close_data = np.array([10, 11, 12])
            result = self.service.calculate_rsi(close_data)
        
        assert result.equals(expected_rsi)
    
    def test_calculate_cci_with_plugin(self):
        """测试通过插件计算CCI"""
        # 模拟技术指标插件
        mock_indicators_plugin = Mock()
        expected_cci = pd.DataFrame({"CCI": [-100, 0, 100]})
        mock_indicators_plugin.calculate_cci.return_value = expected_cci
        
        with patch.object(self.service, '_get_indicators_plugin', return_value=mock_indicators_plugin):
            high_data = np.array([12, 13, 14])
            low_data = np.array([8, 9, 10])
            close_data = np.array([10, 11, 12])
            result = self.service.calculate_cci(high_data, low_data, close_data)
        
        assert result.equals(expected_cci)
    
    def test_get_stock_info(self):
        """测试获取股票基础信息"""
        securities = ["000001.XSHE", "600000.XSHG", "invalid_code"]
        
        result = self.service.get_stock_info(securities)
        
        assert len(result) == 3
        assert result["000001.XSHE"]["market"] == "SZSE"
        assert result["600000.XSHG"]["market"] == "SSE"
        assert result["invalid_code"]["market"] == "UNKNOWN"
    
    def test_get_trading_day_with_plugin(self):
        """测试通过插件获取交易日期"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        mock_data_plugin.get_trading_day.return_value = "2023-12-29"
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_trading_day("2023-12-28", 1)
        
        assert result == "2023-12-29"
        mock_data_plugin.get_trading_day.assert_called_once_with("2023-12-28", 1)
    
    def test_get_trading_day_no_plugin(self):
        """测试无插件时获取交易日期"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_trading_day("2023-12-28", 1)
        
        assert result == "2023-12-28"  # 返回原日期
    
    def test_get_all_trading_days_with_plugin(self):
        """测试通过插件获取全部交易日期"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        expected_days = ["2023-01-03", "2023-01-04", "2023-01-05"]
        mock_data_plugin.get_all_trading_days.return_value = expected_days
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_all_trading_days()
        
        assert result == expected_days
    
    def test_get_all_trading_days_no_plugin(self):
        """测试无插件时获取全部交易日期"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_all_trading_days()
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_check_limit_status_with_plugin(self):
        """测试通过插件检查涨跌停状态"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        mock_limit_data = {
            "000001.XSHE": {
                "limit_up": False,
                "limit_down": False,
                "limit_up_price": 16.5,
                "limit_down_price": 13.5,
                "current_price": 15.0
            }
        }
        mock_data_plugin.check_limit_status.return_value = mock_limit_data
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.check_limit_status("000001.XSHE")
        
        assert "000001.XSHE" in result
        assert result["000001.XSHE"]["current_price"] == 15.0
    
    def test_check_limit_status_no_plugin(self):
        """测试无插件时检查涨跌停状态"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.check_limit_status("000001.XSHE")
        
        assert "000001.XSHE" in result
        assert result["000001.XSHE"]["limit_up"] is False
        assert result["000001.XSHE"]["limit_down"] is False
    
    def test_get_fundamentals_with_plugin(self):
        """测试通过插件获取财务数据"""
        # 模拟数据插件
        mock_data_plugin = Mock()
        expected_data = pd.DataFrame({
            "code": ["000001.XSHE"],
            "date": ["2023-12-31"],
            "revenue": [1000000.0]
        })
        mock_data_plugin.get_fundamentals.return_value = expected_data
        
        with patch.object(self.service, '_get_data_plugin', return_value=mock_data_plugin):
            result = self.service.get_fundamentals(
                ["000001.XSHE"], "income", ["revenue"], "2023-12-31"
            )
        
        assert result.equals(expected_data)
    
    def test_get_fundamentals_no_stocks(self):
        """测试无股票时获取财务数据"""
        # 模拟无插件的情况
        self.plugin_manager.get_all_plugins.return_value = {}
        
        result = self.service.get_fundamentals([], "income", ["revenue"], "2023-12-31")
        
        assert isinstance(result, pd.DataFrame)
        assert "code" in result.columns
        assert "date" in result.columns
        assert "revenue" in result.columns
        assert len(result) == 0
    
    def test_get_fundamentals_no_fields(self):
        """测试无字段时获取财务数据"""
        # 模拟无插件的情况
        self.plugin_manager.get_all_plugins.return_value = {}
        
        result = self.service.get_fundamentals(["000001.XSHE"], "income", [], "2023-12-31")
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["code"] == "000001.XSHE"
    
    def test_get_fundamentals_mock_data(self):
        """测试获取模拟财务数据"""
        with patch.object(self.service, '_get_data_plugin', return_value=None):
            result = self.service.get_fundamentals(
                ["000001.XSHE"], "income", ["revenue", "pe_ratio"], "2023-12-31"
            )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["code"] == "000001.XSHE"
        assert result.iloc[0]["revenue"] == 0.0
        assert result.iloc[0]["pe_ratio"] == 0.0