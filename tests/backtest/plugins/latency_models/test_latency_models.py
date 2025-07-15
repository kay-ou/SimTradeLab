# -*- coding: utf-8 -*-
"""
测试延迟模型基类和具体实现
"""

from datetime import datetime, timedelta
from decimal import Decimal


from simtradelab.backtest.plugins.base import MarketData, Order
from simtradelab.backtest.plugins.latency_models.default_latency_model import (
    DefaultLatencyModel,
    DefaultLatencyModelConfig,
)
from simtradelab.backtest.plugins.latency_models.fixed_latency_model import (
    FixedLatencyModel,
    FixedLatencyModelConfig,
)
from simtradelab.backtest.plugins.latency_models.network_latency_model import (
    NetworkLatencyModel,
    NetworkLatencyModelConfig,
)
from simtradelab.plugins.base import PluginMetadata


class TestDefaultLatencyModel:
    """测试默认延迟模型"""

    def setup_method(self):
        """设置测试环境"""
        self.metadata = PluginMetadata(
            name="DefaultLatencyModel",
            version="1.0.0",
            description="Default latency model for testing",
            author="TestAuthor",
        )
        self.config = DefaultLatencyModelConfig(
            base_latency_ms=50,
            market_order_latency_ms=30,
            limit_order_latency_ms=100,
            volume_impact_factor=0.1,
            max_latency_ms=1000,
        )
        self.model = DefaultLatencyModel(self.metadata, self.config)

    def create_test_order(self, order_type="market", quantity=100):
        """创建测试订单"""
        return Order(
            order_id="test_order_001",
            symbol="000001",
            side="buy",
            quantity=Decimal(str(quantity)),
            order_type=order_type,
            timestamp=datetime.now(),
        )

    def create_test_market_data(self, volume=10000):
        """创建测试市场数据"""
        return MarketData(
            symbol="000001",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.5"),
            low_price=Decimal("9.5"),
            close_price=Decimal("10.2"),
            volume=Decimal(str(volume)),
        )

    def test_plugin_type(self):
        """测试插件类型"""
        assert self.model.get_plugin_type() == "latency_model"

    def test_market_order_latency(self):
        """测试市价单延迟计算"""
        order = self.create_test_order(order_type="market", quantity=100)
        market_data = self.create_test_market_data(volume=10000)

        latency = self.model.calculate_latency(order, market_data)

        # 基础延迟 + 市价单延迟 + 成交量影响
        expected_base = 0.050  # 50ms
        expected_type = 0.030  # 30ms
        expected_volume = (100 / 10000) * 0.1  # 0.001
        expected_total = expected_base + expected_type + expected_volume

        assert abs(latency - expected_total) < 0.001

    def test_limit_order_latency(self):
        """测试限价单延迟计算"""
        order = self.create_test_order(order_type="limit", quantity=100)
        market_data = self.create_test_market_data(volume=10000)

        latency = self.model.calculate_latency(order, market_data)

        # 基础延迟 + 限价单延迟 + 成交量影响
        expected_base = 0.050  # 50ms
        expected_type = 0.100  # 100ms
        expected_volume = (100 / 10000) * 0.1  # 0.001
        expected_total = expected_base + expected_type + expected_volume

        assert abs(latency - expected_total) < 0.001

    def test_max_latency_limit(self):
        """测试最大延迟限制"""
        order = self.create_test_order(order_type="limit", quantity=100000)
        market_data = self.create_test_market_data(volume=1000)

        latency = self.model.calculate_latency(order, market_data)

        # 应该被限制在最大延迟内
        assert latency <= 1.0  # 1000ms

    def test_execution_time_calculation(self):
        """测试执行时间计算"""
        order = self.create_test_order(order_type="market", quantity=100)
        market_data = self.create_test_market_data(volume=10000)

        execution_time = self.model.get_execution_time(order, market_data)

        # 执行时间应该是订单时间 + 延迟
        latency = self.model.calculate_latency(order, market_data)
        expected_time = order.timestamp + timedelta(seconds=latency)

        assert abs((execution_time - expected_time).total_seconds()) < 0.001

    def test_volume_impact(self):
        """测试成交量对延迟的影响"""
        order = self.create_test_order(order_type="market", quantity=1000)

        # 小成交量市场
        small_volume_data = self.create_test_market_data(volume=5000)
        small_latency = self.model.calculate_latency(order, small_volume_data)

        # 大成交量市场
        large_volume_data = self.create_test_market_data(volume=50000)
        large_latency = self.model.calculate_latency(order, large_volume_data)

        # 小成交量市场的延迟应该更高
        assert small_latency > large_latency


class TestFixedLatencyModel:
    """测试固定延迟模型"""

    def setup_method(self):
        """设置测试环境"""
        self.metadata = PluginMetadata(
            name="FixedLatencyModel",
            version="1.0.0",
            description="Fixed latency model for testing",
            author="TestAuthor",
        )
        self.config = FixedLatencyModelConfig(latency_ms=100)
        self.model = FixedLatencyModel(self.metadata, self.config)

    def create_test_order(self):
        """创建测试订单"""
        return Order(
            order_id="test_order_001",
            symbol="000001",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            timestamp=datetime.now(),
        )

    def create_test_market_data(self):
        """创建测试市场数据"""
        return MarketData(
            symbol="000001",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.5"),
            low_price=Decimal("9.5"),
            close_price=Decimal("10.2"),
            volume=Decimal("10000"),
        )

    def test_plugin_type(self):
        """测试插件类型"""
        assert self.model.get_plugin_type() == "latency_model"

    def test_fixed_latency(self):
        """测试固定延迟"""
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        latency = self.model.calculate_latency(order, market_data)

        # 应该始终返回配置的固定延迟
        assert latency == 0.1  # 100ms

    def test_execution_time_calculation(self):
        """测试执行时间计算"""
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        execution_time = self.model.get_execution_time(order, market_data)

        # 执行时间应该是订单时间 + 固定延迟
        expected_time = order.timestamp + timedelta(seconds=0.1)

        assert abs((execution_time - expected_time).total_seconds()) < 0.001

    def test_consistency(self):
        """测试延迟的一致性"""
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        # 多次计算应该返回相同的结果
        latency1 = self.model.calculate_latency(order, market_data)
        latency2 = self.model.calculate_latency(order, market_data)

        assert latency1 == latency2

    def test_default_config(self):
        """测试默认配置"""
        model = FixedLatencyModel(self.metadata)
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        latency = model.calculate_latency(order, market_data)

        # 默认配置应该是100ms
        assert latency == 0.1


class TestNetworkLatencyModel:
    """测试网络延迟模型"""

    def setup_method(self):
        """设置测试环境"""
        self.metadata = PluginMetadata(
            name="NetworkLatencyModel",
            version="1.0.0",
            description="Network latency model for testing",
            author="TestAuthor",
        )
        self.config = NetworkLatencyModelConfig(
            base_network_latency_ms=20,
            exchange_processing_ms=50,
            variance_factor=0.3,
            peak_hours_multiplier=1.5,
            peak_start_hour=9,
            peak_end_hour=15,
        )
        self.model = NetworkLatencyModel(self.metadata, self.config)

    def create_test_order(self, hour=10):
        """创建测试订单"""
        timestamp = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        return Order(
            order_id="test_order_001",
            symbol="000001",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            timestamp=timestamp,
        )

    def create_test_market_data(self):
        """创建测试市场数据"""
        return MarketData(
            symbol="000001",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.5"),
            low_price=Decimal("9.5"),
            close_price=Decimal("10.2"),
            volume=Decimal("10000"),
        )

    def test_plugin_type(self):
        """测试插件类型"""
        assert self.model.get_plugin_type() == "latency_model"

    def test_peak_hours_multiplier(self):
        """测试高峰时段延迟倍数"""
        market_data = self.create_test_market_data()

        # 高峰时段订单（10点）
        peak_order = self.create_test_order(hour=10)

        # 非高峰时段订单（16点）
        off_peak_order = self.create_test_order(hour=16)

        # 多次测试以获得平均值（由于有随机性）
        peak_latencies = []
        off_peak_latencies = []

        for _ in range(100):
            peak_latencies.append(self.model.calculate_latency(peak_order, market_data))
            off_peak_latencies.append(
                self.model.calculate_latency(off_peak_order, market_data)
            )

        avg_peak = sum(peak_latencies) / len(peak_latencies)
        avg_off_peak = sum(off_peak_latencies) / len(off_peak_latencies)

        # 高峰时段的平均延迟应该更高
        assert avg_peak > avg_off_peak

    def test_latency_variance(self):
        """测试延迟的变异性"""
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        # 多次计算延迟
        latencies = []
        for _ in range(100):
            latencies.append(self.model.calculate_latency(order, market_data))

        # 应该有变异性
        min_latency = min(latencies)
        max_latency = max(latencies)

        assert max_latency > min_latency

    def test_minimum_latency(self):
        """测试最小延迟限制"""
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        # 多次测试确保延迟不会为负或过小
        for _ in range(100):
            latency = self.model.calculate_latency(order, market_data)
            assert latency >= 0.001  # 最小1毫秒

    def test_execution_time_calculation(self):
        """测试执行时间计算"""
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        execution_time = self.model.get_execution_time(order, market_data)

        # 执行时间应该在订单时间之后
        assert execution_time > order.timestamp

    def test_default_config(self):
        """测试默认配置"""
        model = NetworkLatencyModel(self.metadata)
        order = self.create_test_order()
        market_data = self.create_test_market_data()

        latency = model.calculate_latency(order, market_data)

        # 应该能正常计算延迟
        assert latency > 0


class TestLatencyModelIntegration:
    """测试延迟模型集成"""

    def test_all_models_implement_interface(self):
        """测试所有模型都实现了正确的接口"""
        metadata = PluginMetadata(
            name="TestModel",
            version="1.0.0",
            description="Test model",
            author="TestAuthor",
        )

        models = [
            DefaultLatencyModel(metadata),
            FixedLatencyModel(metadata),
            NetworkLatencyModel(metadata),
        ]

        order = Order(
            order_id="test_order_001",
            symbol="000001",
            side="buy",
            quantity=Decimal("100"),
            order_type="market",
            timestamp=datetime.now(),
        )

        market_data = MarketData(
            symbol="000001",
            timestamp=datetime.now(),
            open_price=Decimal("10.0"),
            high_price=Decimal("10.5"),
            low_price=Decimal("9.5"),
            close_price=Decimal("10.2"),
            volume=Decimal("10000"),
        )

        for model in models:
            # 测试接口方法
            assert model.get_plugin_type() == "latency_model"

            # 测试延迟计算
            latency = model.calculate_latency(order, market_data)
            assert isinstance(latency, float)
            assert latency >= 0

            # 测试执行时间计算
            execution_time = model.get_execution_time(order, market_data)
            assert isinstance(execution_time, datetime)
            assert execution_time >= order.timestamp
