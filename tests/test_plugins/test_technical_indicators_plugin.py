# -*- coding: utf-8 -*-
"""
技术指标插件测试

测试技术指标插件的功能和与PTrade适配器的集成。
"""

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from simtradelab.adapters.ptrade.adapter import PTradeAdapter
from simtradelab.core.plugin_manager import PluginManager
from simtradelab.plugins.base import PluginConfig, PluginMetadata
from simtradelab.plugins.indicators.technical_indicators_plugin import (
    TechnicalIndicatorsPlugin,
)


class TestTechnicalIndicatorsPlugin:
    """测试技术指标插件"""

    @pytest.fixture
    def plugin(self):
        """技术指标插件fixture"""
        metadata = TechnicalIndicatorsPlugin.METADATA
        config = PluginConfig()
        plugin = TechnicalIndicatorsPlugin(metadata, config)
        plugin.initialize()
        return plugin

    def test_plugin_creation(self, plugin):
        """测试插件创建"""
        assert plugin.metadata.name == "technical_indicators_plugin"
        assert plugin.state == plugin.state.INITIALIZED
        assert hasattr(plugin, "_calculation_cache")
        assert hasattr(plugin, "_cache_timeout")

    def test_calculate_macd(self, plugin):
        """测试MACD计算"""
        close_data = np.array(
            [
                10.0,
                10.1,
                10.2,
                9.9,
                10.3,
                10.4,
                10.1,
                10.5,
                10.6,
                10.0,
                10.2,
                10.3,
                10.1,
                10.4,
                10.5,
                10.2,
                10.6,
                10.7,
                10.3,
                10.8,
            ]
        )

        result = plugin.calculate_macd(close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(result) == len(close_data)
        assert not result.isnull().all().any()

    def test_calculate_kdj(self, plugin):
        """测试KDJ计算"""
        high_data = np.array(
            [
                10.2,
                10.3,
                10.4,
                10.1,
                10.5,
                10.6,
                10.3,
                10.7,
                10.8,
                10.2,
                10.4,
                10.5,
                10.3,
                10.6,
                10.7,
                10.4,
                10.8,
                10.9,
                10.5,
                11.0,
            ]
        )
        low_data = np.array(
            [
                9.8,
                9.9,
                10.0,
                9.7,
                10.1,
                10.2,
                9.9,
                10.3,
                10.4,
                9.8,
                10.0,
                10.1,
                9.9,
                10.2,
                10.3,
                10.0,
                10.4,
                10.5,
                10.1,
                10.6,
            ]
        )
        close_data = np.array(
            [
                10.0,
                10.1,
                10.2,
                9.9,
                10.3,
                10.4,
                10.1,
                10.5,
                10.6,
                10.0,
                10.2,
                10.3,
                10.1,
                10.4,
                10.5,
                10.2,
                10.6,
                10.7,
                10.3,
                10.8,
            ]
        )

        result = plugin.calculate_kdj(high_data, low_data, close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["K", "D", "J"]
        assert len(result) == len(close_data)

    def test_calculate_rsi(self, plugin):
        """测试RSI计算"""
        close_data = np.array(
            [
                10.0,
                10.1,
                10.2,
                9.9,
                10.3,
                10.4,
                10.1,
                10.5,
                10.6,
                10.0,
                10.2,
                10.3,
                10.1,
                10.4,
                10.5,
                10.2,
                10.6,
                10.7,
                10.3,
                10.8,
            ]
        )

        result = plugin.calculate_rsi(close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["RSI"]
        assert len(result) == len(close_data)

    def test_calculate_cci(self, plugin):
        """测试CCI计算"""
        high_data = np.array(
            [
                10.2,
                10.3,
                10.4,
                10.1,
                10.5,
                10.6,
                10.3,
                10.7,
                10.8,
                10.2,
                10.4,
                10.5,
                10.3,
                10.6,
                10.7,
                10.4,
                10.8,
                10.9,
                10.5,
                11.0,
            ]
        )
        low_data = np.array(
            [
                9.8,
                9.9,
                10.0,
                9.7,
                10.1,
                10.2,
                9.9,
                10.3,
                10.4,
                9.8,
                10.0,
                10.1,
                9.9,
                10.2,
                10.3,
                10.0,
                10.4,
                10.5,
                10.1,
                10.6,
            ]
        )
        close_data = np.array(
            [
                10.0,
                10.1,
                10.2,
                9.9,
                10.3,
                10.4,
                10.1,
                10.5,
                10.6,
                10.0,
                10.2,
                10.3,
                10.1,
                10.4,
                10.5,
                10.2,
                10.6,
                10.7,
                10.3,
                10.8,
            ]
        )

        result = plugin.calculate_cci(high_data, low_data, close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["CCI"]
        assert len(result) == len(close_data)

    def test_caching_mechanism(self, plugin):
        """测试缓存机制"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 第一次计算
        result1 = plugin.calculate_macd(close_data)

        # 第二次计算（应该使用缓存）
        result2 = plugin.calculate_macd(close_data)

        # 结果应该相同
        pd.testing.assert_frame_equal(result1, result2)

        # 检查缓存状态
        stats = plugin.get_cache_stats()
        assert stats["cached_calculations"] > 0

    def test_cache_clear(self, plugin):
        """测试缓存清理"""
        close_data = np.array([10.0, 10.1, 10.2, 9.9, 10.3])

        # 计算产生缓存
        plugin.calculate_macd(close_data)
        plugin.calculate_rsi(close_data)

        # 检查缓存不为空
        stats = plugin.get_cache_stats()
        assert stats["cached_calculations"] > 0

        # 清理缓存
        plugin.clear_cache()

        # 检查缓存已清空
        stats = plugin.get_cache_stats()
        assert stats["cached_calculations"] == 0

    def test_error_handling(self, plugin):
        """测试错误处理"""
        # 测试空数组
        empty_data = np.array([])

        result = plugin.calculate_macd(empty_data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

        # 测试无效数据
        invalid_data = np.array([np.nan, np.inf, -np.inf])

        result = plugin.calculate_rsi(invalid_data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(invalid_data)

    def test_config_driven_parameters(self):
        """测试插件是否使用配置文件中的参数"""
        custom_config = {"macd": {"short": 10, "long": 20, "m": 5}}
        config = PluginConfig(config=custom_config)
        plugin = TechnicalIndicatorsPlugin(TechnicalIndicatorsPlugin.METADATA, config)
        plugin.initialize()

        assert plugin.macd_params["short"] == 10
        assert plugin.macd_params["long"] == 20
        assert plugin.macd_params["m"] == 5

    def test_state_management(self, plugin):
        """测试get_state和set_state方法"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 1. 计算并填充缓存
        plugin.calculate_macd(close_data)
        assert plugin.get_cache_stats()["cached_calculations"] == 1

        # 2. 获取状态
        state = plugin.get_state()
        assert "_calculation_cache" in state
        assert "_cache_timestamps" in state
        assert len(state["_calculation_cache"]) == 1

        # 3. 创建一个新插件实例
        new_metadata = PluginMetadata(name="new_indicator_plugin", version="1.0")
        new_plugin = TechnicalIndicatorsPlugin(new_metadata, PluginConfig())
        new_plugin.initialize()
        assert new_plugin.get_cache_stats()["cached_calculations"] == 0

        # 4. 恢复状态
        new_plugin.set_state(state)

        # 5. 验证状态是否已恢复
        assert new_plugin.get_cache_stats()["cached_calculations"] == 1

        # 6. 再次计算，应命中缓存（验证缓存内容是否正确恢复）
        result1 = plugin.calculate_macd(close_data)
        result2 = new_plugin.calculate_macd(close_data)
        pd.testing.assert_frame_equal(result1, result2)


class TestPTradeAdapterIntegration:
    """测试PTrade适配器与技术指标插件的集成"""

    @pytest.fixture
    def mock_plugin_manager(self):
        """创建模拟插件管理器"""
        manager = MagicMock()

        # 创建模拟数据插件
        data_plugin = MagicMock()
        data_plugin.get_multiple_history_data.return_value = pd.DataFrame(
            {
                "security": ["000001.SZ"] * 5,
                "date": pd.date_range("2023-01-01", periods=5),
                "open": [10.0, 10.1, 10.2, 9.9, 10.3],
                "high": [10.2, 10.3, 10.4, 10.1, 10.5],
                "low": [9.8, 9.9, 10.0, 9.7, 10.1],
                "close": [10.0, 10.1, 10.2, 9.9, 10.3],
                "volume": [100000] * 5,
                "money": [1000000] * 5,
                "price": [10.0, 10.1, 10.2, 9.9, 10.3],
            }
        )

        # 创建真实的技术指标插件
        indicators_plugin = TechnicalIndicatorsPlugin(
            TechnicalIndicatorsPlugin.METADATA, PluginConfig()
        )
        indicators_plugin.initialize()

        def get_plugin(name):
            if name == "csv_data_plugin":
                return data_plugin
            elif name == "technical_indicators_plugin":
                return indicators_plugin
            return None

        manager.get_plugin.side_effect = get_plugin
        return manager

    @pytest.fixture
    def adapter(self, mock_plugin_manager):
        """创建测试适配器"""
        from simtradelab.core.event_bus import EventBus

        metadata = PTradeAdapter.METADATA
        config = PluginConfig(config={"initial_cash": 1000000})
        adapter = PTradeAdapter(metadata, config)

        # 设置事件总线
        event_bus = EventBus()
        adapter.set_event_bus(event_bus)

        adapter.set_plugin_manager(mock_plugin_manager)
        adapter.initialize()
        return adapter

    def test_plugin_integration(self, adapter):
        """测试插件集成"""
        # 检查插件是否正确加载
        assert adapter._indicators_plugin is not None
        assert adapter._data_plugin is not None

        # 检查是否有技术指标插件的方法
        assert hasattr(adapter, "calculate_macd")
        assert hasattr(adapter, "calculate_kdj")
        assert hasattr(adapter, "calculate_rsi")
        assert hasattr(adapter, "calculate_cci")

    def test_macd_delegation(self, adapter):
        """测试MACD计算委托"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 通过PTrade API调用 - 使用路由器方法
        result = adapter._api_router.get_MACD(close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(result) == len(close_data)

        # 直接通过插件调用，结果应该相同
        plugin_result = adapter._indicators_plugin.calculate_macd(close_data)
        pd.testing.assert_frame_equal(result, plugin_result)

    def test_kdj_delegation(self, adapter):
        """测试KDJ计算委托"""
        high_data = np.array(
            [10.2, 10.3, 10.4, 10.1, 10.5, 10.6, 10.3, 10.7, 10.8, 10.2]
        )
        low_data = np.array([9.8, 9.9, 10.0, 9.7, 10.1, 10.2, 9.9, 10.3, 10.4, 9.8])
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 通过PTrade API调用 - 使用路由器方法
        result = adapter._api_router.get_KDJ(high_data, low_data, close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["K", "D", "J"]
        assert len(result) == len(close_data)

    def test_rsi_delegation(self, adapter):
        """测试RSI计算委托"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 通过PTrade API调用 - 使用路由器方法
        result = adapter._api_router.get_RSI(close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["RSI"]
        assert len(result) == len(close_data)

    def test_cci_delegation(self, adapter):
        """测试CCI计算委托"""
        high_data = np.array(
            [10.2, 10.3, 10.4, 10.1, 10.5, 10.6, 10.3, 10.7, 10.8, 10.2]
        )
        low_data = np.array([9.8, 9.9, 10.0, 9.7, 10.1, 10.2, 9.9, 10.3, 10.4, 9.8])
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 通过PTrade API调用 - 使用路由器方法
        result = adapter._api_router.get_CCI(high_data, low_data, close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["CCI"]
        assert len(result) == len(close_data)

    def test_fallback_mechanism(self, adapter):
        """测试回退机制"""
        # 模拟插件失败
        original_plugin = adapter._indicators_plugin
        adapter._indicators_plugin = None

        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 应该回退到内部实现 - 使用路由器方法
        result = adapter._api_router.get_MACD(close_data)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(result) == len(close_data)

        # 恢复插件
        adapter._indicators_plugin = original_plugin

    def test_plugin_caching_integration(self, adapter):
        """测试插件缓存集成"""
        close_data = np.array(
            [10.0, 10.1, 10.2, 9.9, 10.3, 10.4, 10.1, 10.5, 10.6, 10.0]
        )

        # 第一次计算 - 直接通过插件调用
        result1 = adapter._indicators_plugin.calculate_macd(close_data)

        # 第二次计算（应该使用缓存）
        result2 = adapter._indicators_plugin.calculate_macd(close_data)

        # 结果应该相同
        pd.testing.assert_frame_equal(result1, result2)

        # 检查插件缓存状态
        stats = adapter._indicators_plugin.get_cache_stats()
        assert stats["cached_calculations"] > 0

    def test_plugin_proxy_methods(self, adapter):
        """测试插件代理方法"""
        # 检查是否可以直接调用插件方法
        close_data = np.array([10.0, 10.1, 10.2, 9.9, 10.3])

        # 直接调用插件方法（通过代理）
        if hasattr(adapter, "calculate_macd"):
            result = adapter.calculate_macd(close_data)
            assert isinstance(result, pd.DataFrame)
            assert list(result.columns) == ["MACD", "MACD_signal", "MACD_hist"]

    def test_plugin_stats_integration(self, adapter):
        """测试插件统计信息集成"""
        # 获取适配器API统计信息
        stats = adapter.get_api_stats()

        assert "calculations_apis" in stats
        assert stats["calculations_apis"] > 0

        # 检查技术指标插件的统计信息
        if adapter._indicators_plugin:
            plugin_stats = adapter._indicators_plugin.get_cache_stats()
            assert "cached_calculations" in plugin_stats
            assert "cache_timeout" in plugin_stats
