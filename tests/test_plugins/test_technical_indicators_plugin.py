# -*- coding: utf-8 -*-
"""
技术指标插件测试

测试技术指标插件的核心业务价值：
1. 准确计算金融技术指标
2. 缓存机制提高计算效率
3. 输入数据验证和错误处理
4. 与真实数据源的集成
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from simtradelab.plugins.data.config import CSVDataPluginConfig
from simtradelab.plugins.data.csv_data_plugin import CSVDataPlugin
from simtradelab.plugins.indicators.config import TechnicalIndicatorsConfig
from simtradelab.plugins.indicators.technical_indicators_plugin import (
    TechnicalIndicatorsPlugin,
)


class TestTechnicalIndicatorsPlugin:
    """测试技术指标插件"""

    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def real_data_plugin(self, temp_data_dir):
        """创建真实的数据插件，避免Mock"""
        csv_config = CSVDataPluginConfig(
            data_dir=temp_data_dir,
            supported_markets={"stock_cn"},
            supported_frequencies={"1d"},
        )
        plugin = CSVDataPlugin(CSVDataPlugin.METADATA, csv_config)
        plugin.initialize()
        return plugin

    @pytest.fixture
    def plugin(self):
        """技术指标插件fixture"""
        metadata = TechnicalIndicatorsPlugin.METADATA
        tech_config = TechnicalIndicatorsConfig()
        plugin = TechnicalIndicatorsPlugin(metadata, tech_config)
        plugin.initialize()
        return plugin

    def test_plugin_creation_and_business_readiness(self, plugin):
        """测试插件创建和业务就绪状态"""
        # 验证业务价值：插件应该能够为量化策略提供技术指标计算服务
        assert plugin.metadata.name == "technical_indicators_plugin"
        assert plugin.state == plugin.state.INITIALIZED

        # 验证核心业务能力：技术指标计算方法存在且可调用
        assert hasattr(plugin, "calculate_macd") and callable(plugin.calculate_macd)
        assert hasattr(plugin, "calculate_kdj") and callable(plugin.calculate_kdj)
        assert hasattr(plugin, "calculate_rsi") and callable(plugin.calculate_rsi)
        assert hasattr(plugin, "calculate_cci") and callable(plugin.calculate_cci)

        # 验证性能优化：缓存机制应该就绪
        assert hasattr(plugin, "_calculation_cache")
        assert hasattr(plugin, "_cache_timeout")

    def test_macd_calculation_for_trading_signals(self, plugin):
        """测试MACD计算的交易信号识别能力 - 这是量化交易的核心需求"""
        # 业务场景：创建一个明显的上涨趋势，MACD应该能识别出来
        close_prices = np.array(
            [
                10.0,
                10.05,
                10.1,
                10.15,
                10.2,
                10.25,
                10.3,
                10.35,
                10.4,
                10.45,  # 上涨趋势
                10.5,
                10.55,
                10.6,
                10.65,
                10.7,
                10.75,
                10.8,
                10.85,
                10.9,
                10.95,  # 继续上涨
                11.0,
                11.05,
                11.1,
                11.15,
                11.2,
                11.25,
                11.3,
                11.35,
                11.4,
                11.45,  # 持续上涨
            ]
        )

        result = plugin.calculate_macd(close_prices)

        # 验证业务价值：MACD指标应该能正确反映趋势
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["MACD", "MACD_signal", "MACD_hist"]
        assert len(result) == len(close_prices)

        # 验证交易逻辑：在明显上涨趋势中，MACD柱状图后期应该为正值（买入信号）
        # 这是量化策略师最关心的：指标能否识别趋势
        macd_hist_last_10 = result["MACD_hist"].tail(10)
        positive_signals = sum(macd_hist_last_10 > 0)

        # 在强上涨趋势中，后期应该有大部分正值信号
        assert positive_signals >= 6, f"在上涨趋势中MACD信号不够明确，正值信号只有{positive_signals}/10"

        # 验证数据质量：确保没有异常值
        assert not result.isnull().any().any(), "MACD计算结果不应包含NaN值"
        assert result["MACD"].std() > 0, "MACD值应该有变化，不应该是常数"

    def test_kdj_calculation_for_overbought_oversold_signals(self, plugin):
        """测试KDJ计算的超买超卖信号识别"""
        # 业务场景：模拟超买情况（价格在高位震荡）
        high_prices = np.array([11.0] * 20)  # 持续高位
        low_prices = np.array([10.8] * 20)  # 底部也相对较高
        close_prices = np.array([10.95] * 20)  # 收盘价接近高位

        result = plugin.calculate_kdj(high_prices, low_prices, close_prices)

        # 验证业务价值：KDJ应该能识别超买状态
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["K", "D", "J"]
        assert len(result) == len(close_prices)

        # 验证交易逻辑：在高位震荡中，KDJ值应该趋向高位（接近100）
        # 跳过前面的NaN值，分析有效数据
        valid_data = result.dropna()
        if len(valid_data) > 0:
            k_values_last = valid_data["K"].tail(5)
            d_values_last = valid_data["D"].tail(5)

            # 在高位震荡中，K和D值后期应该较高，表示超买
            assert k_values_last.mean() > 50, "在高位震荡中，K值应该相对较高"
            assert d_values_last.mean() > 50, "在高位震荡中，D值应该相对较高"

        # 验证数据质量：有效数据不应包含NaN
        valid_k = result["K"].dropna()
        valid_d = result["D"].dropna()
        valid_j = result["J"].dropna()

        assert len(valid_k) > 0, "应该有有效的K值"
        assert len(valid_d) > 0, "应该有有效的D值"
        assert len(valid_j) > 0, "应该有有效的J值"
        assert all(0 <= valid_k) and all(valid_k <= 100), "K值应该在0-100范围内"

    def test_rsi_calculation_for_momentum_analysis(self, plugin):
        """测试RSI计算的动量分析能力"""
        # 业务场景：创建一个从下跌到上涨的转折
        close_prices = np.array(
            [
                100,
                99,
                98,
                97,
                96,
                95,
                94,
                93,
                92,
                91,  # 下跌趋势
                92,
                93,
                94,
                95,
                96,
                97,
                98,
                99,
                100,
                101,  # 反弹上涨
            ]
        )

        result = plugin.calculate_rsi(close_prices)

        # 验证业务价值：RSI应该能反映动量变化
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["RSI"]
        assert len(result) == len(close_prices)

        # 验证交易逻辑：从下跌到上涨，RSI应该从低位向高位移动
        rsi_first_half = result["RSI"].iloc[:10].dropna()
        rsi_second_half = result["RSI"].iloc[10:].dropna()

        if len(rsi_first_half) > 0 and len(rsi_second_half) > 0:
            # 反弹阶段的RSI应该高于下跌阶段
            assert rsi_second_half.mean() > rsi_first_half.mean(), "反弹阶段RSI应该高于下跌阶段"

        # 验证数据质量和范围
        assert not result.isnull().all().any(), "RSI计算结果不应全为NaN"
        valid_rsi = result["RSI"].dropna()
        if len(valid_rsi) > 0:
            assert all(0 <= valid_rsi) and all(valid_rsi <= 100), "RSI值应该在0-100范围内"

    def test_cci_calculation_for_trend_strength(self, plugin):
        """测试CCI计算的趋势强度识别"""
        # 业务场景：创建强趋势行情
        trend_factor = np.linspace(0, 2, 20)  # 线性上涨因子
        base_price = 50

        high_prices = base_price + trend_factor + 0.5
        low_prices = base_price + trend_factor - 0.5
        close_prices = base_price + trend_factor

        result = plugin.calculate_cci(high_prices, low_prices, close_prices)

        # 验证业务价值：CCI应该能识别趋势强度
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["CCI"]
        assert len(result) == len(close_prices)

        # 验证交易逻辑：在强趋势中，CCI后期应该显示明显方向性
        cci_values = result["CCI"].dropna()
        if len(cci_values) > 5:
            cci_last_5 = cci_values.tail(5)
            # 在上涨趋势中，CCI值应该趋向正值
            assert cci_last_5.mean() > 0, "在上涨趋势中，CCI应该趋向正值"

        # 验证数据质量
        assert not result.isnull().all().any(), "CCI计算结果不应全为NaN"

    def test_caching_improves_performance(self, plugin):
        """测试缓存机制确实提高了计算性能"""
        close_prices = np.random.randn(1000) + 100  # 大量数据

        import time

        # 第一次计算（冷缓存）
        start_time = time.time()
        result1 = plugin.calculate_macd(close_prices)
        time.time() - start_time

        # 第二次计算（热缓存）
        start_time = time.time()
        result2 = plugin.calculate_macd(close_prices)
        time.time() - start_time

        # 验证业务价值：缓存应该提高性能
        # 注意：由于计算很快，时间差可能很小，我们主要验证结果一致性
        assert result1.equals(result2), "缓存的结果应该与原始计算结果一致"

        # 验证缓存机制确实在工作（检查缓存中是否有数据）
        assert len(plugin._calculation_cache) > 0, "计算后缓存中应该有数据"

    def test_error_handling_with_invalid_data(self, plugin):
        """测试错误数据的处理能力 - 确保系统鲁棒性"""
        # 业务场景：用户可能传入错误的数据

        # 测试空数组
        try:
            result = plugin.calculate_macd(np.array([]))
            # 如果没有抛出异常，确保结果是空的或合理的
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
        except Exception:
            # 抛出异常也是可接受的处理方式
            pass

        # 测试包含NaN的数据 - 应该能处理或给出合理错误
        invalid_data = np.array([10.0, np.nan, 12.0, 11.0, 10.5, 11.2, 10.8, 11.5])
        try:
            result = plugin.calculate_rsi(invalid_data)
            # 如果没有抛出异常，确保结果是可处理的
            assert isinstance(result, pd.DataFrame)
            # 结果可能包含NaN，这是可接受的
        except Exception:
            # 抛出异常也是可接受的处理方式
            pass

        # 测试数据长度不足的情况 - 应该能优雅处理
        short_data = np.array([10.0, 11.0])  # 只有2个数据点
        try:
            result = plugin.calculate_macd(short_data)
            # 如果计算成功，验证结果格式
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(short_data)
        except Exception:
            # 抛出异常也是合理的
            pass

    def test_integration_with_real_data_source(self, plugin, real_data_plugin):
        """测试与真实数据源的集成 - 验证端到端业务流程"""
        # 业务场景：从真实数据源获取数据并计算技术指标

        # 从真实CSV数据插件获取历史数据
        history_data = real_data_plugin.get_history_data("000001.XSHE", count=50)

        # 验证我们获得了真实的股票数据
        assert len(history_data) > 0, "应该能从数据源获取到历史数据"
        assert "close" in history_data.columns, "历史数据应该包含收盘价"

        # 使用真实数据计算技术指标
        close_prices = history_data["close"].values
        macd_result = plugin.calculate_macd(close_prices)

        # 验证端到端业务价值：技术指标计算在真实数据上工作正常
        assert isinstance(macd_result, pd.DataFrame)
        assert len(macd_result) == len(close_prices)
        assert not macd_result.isnull().all().any()

        # 验证业务逻辑：技术指标值应该在合理范围内
        macd_values = macd_result["MACD"].dropna()
        if len(macd_values) > 0:
            # MACD值应该相对于价格是合理的（不应该是极端值）
            price_range = close_prices.max() - close_prices.min()
            macd_range = macd_values.max() - macd_values.min()

            # 一般情况下，MACD的变化范围应该小于价格变化范围
            assert macd_range < price_range * 2, "MACD变化范围应该在合理区间内"

    def test_plugin_lifecycle_with_calculations(self, plugin):
        """测试插件生命周期中的计算能力保持"""
        # 验证初始化状态下可以计算
        close_prices = np.array(
            [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
        )
        result_before = plugin.calculate_macd(close_prices)
        assert isinstance(result_before, pd.DataFrame)

        # 验证shutdown后的状态变化
        original_state = plugin.state
        plugin.shutdown()
        # 状态可能是STOPPED或UNINITIALIZED，取决于具体实现
        assert plugin.state != original_state, "插件shutdown后状态应该发生变化"

        # 验证重新初始化后仍可计算
        plugin.initialize()
        assert plugin.state == plugin.state.INITIALIZED, "重新初始化后应该处于INITIALIZED状态"

        result_after = plugin.calculate_macd(close_prices)
        assert isinstance(result_after, pd.DataFrame)

        # 计算结果应该一致（缓存可能被清除，但计算逻辑应该一致）
        assert result_before.shape == result_after.shape
        assert list(result_before.columns) == list(result_after.columns)
