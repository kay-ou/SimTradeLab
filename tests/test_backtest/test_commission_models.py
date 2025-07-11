# -*- coding: utf-8 -*-
"""
手续费模型插件测试
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock

from simtradelab.backtest.plugins.commission_models import (
    ChinaAStockCommissionModel,
    FixedCommissionModel,
    TieredCommissionModel,
    ComprehensiveCommissionModel,
    PerShareCommissionModel,
)
from simtradelab.backtest.plugins.base import Fill, PluginMetadata


class TestChinaAStockCommissionModel:
    """测试中国A股手续费模型"""
    
    def test_initialization(self):
        """测试初始化"""
        metadata = PluginMetadata(
            name="ChinaAStockCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = ChinaAStockCommissionModel(metadata)
        assert model.metadata == metadata
        assert model._stamp_tax_rate == Decimal("0.001")
        assert model._commission_rate == Decimal("0.0003")
        assert model._min_commission == Decimal("5.0")
    
    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        metadata = PluginMetadata(
            name="ChinaAStockCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        config = {
            "stamp_tax_rate": 0.002,
            "commission_rate": 0.0005,
            "min_commission": 10.0,
            "transfer_fee_rate": 0.00003,
            "exchange_fee_rate": 0.0001,
            "regulatory_fee_rate": 0.00003
        }
        
        model = ChinaAStockCommissionModel(metadata, config)
        assert model._stamp_tax_rate == Decimal("0.002")
        assert model._commission_rate == Decimal("0.0005")
        assert model._min_commission == Decimal("10.0")
        assert model._transfer_fee_rate == Decimal("0.00003")
        assert model._exchange_fee_rate == Decimal("0.0001")
        assert model._regulatory_fee_rate == Decimal("0.00003")
    
    def test_calculate_commission_buy(self):
        """测试计算买入手续费"""
        metadata = PluginMetadata(
            name="ChinaAStockCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = ChinaAStockCommissionModel(metadata)
        
        buy_fill = Fill(
            order_id="buy_order",
            symbol="600000.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        commission = model.calculate_commission(buy_fill)
        
        # 买入不收印花税
        assert commission > 0
        
        # 检查手续费明细
        breakdown = model.calculate_commission_breakdown(buy_fill)
        assert breakdown["stamp_tax"] == Decimal("0")  # 买入无印花税
        assert breakdown["commission"] >= model._min_commission  # 有最低佣金
        assert breakdown["transfer_fee"] > 0  # 沪市有过户费
        assert breakdown["exchange_fee"] > 0  # 有经手费
        assert breakdown["regulatory_fee"] > 0  # 有监管费
    
    def test_calculate_commission_sell(self):
        """测试计算卖出手续费"""
        metadata = PluginMetadata(
            name="ChinaAStockCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = ChinaAStockCommissionModel(metadata)
        
        sell_fill = Fill(
            order_id="sell_order",
            symbol="600000.SH",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        commission = model.calculate_commission(sell_fill)
        
        # 卖出收印花税
        assert commission > 0
        
        # 检查手续费明细
        breakdown = model.calculate_commission_breakdown(sell_fill)
        assert breakdown["stamp_tax"] > 0  # 卖出有印花税
        assert breakdown["commission"] >= model._min_commission  # 有最低佣金
        assert breakdown["transfer_fee"] > 0  # 沪市有过户费
        assert breakdown["exchange_fee"] > 0  # 有经手费
        assert breakdown["regulatory_fee"] > 0  # 有监管费
    
    def test_sh_vs_sz_market(self):
        """测试沪市vs深市差异"""
        metadata = PluginMetadata(
            name="ChinaAStockCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = ChinaAStockCommissionModel(metadata)
        
        # 沪市股票
        sh_fill = Fill(
            order_id="sh_order",
            symbol="600000.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        # 深市股票
        sz_fill = Fill(
            order_id="sz_order",
            symbol="000001.SZ",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        sh_breakdown = model.calculate_commission_breakdown(sh_fill)
        sz_breakdown = model.calculate_commission_breakdown(sz_fill)
        
        # 沪市有过户费，深市没有
        assert sh_breakdown["transfer_fee"] > 0
        assert sz_breakdown["transfer_fee"] == 0
        
        # 其他费用应该相同
        assert sh_breakdown["commission"] == sz_breakdown["commission"]
        assert sh_breakdown["exchange_fee"] == sz_breakdown["exchange_fee"]
        assert sh_breakdown["regulatory_fee"] == sz_breakdown["regulatory_fee"]
    
    def test_is_sh_market(self):
        """测试沪市判断"""
        metadata = PluginMetadata(
            name="ChinaAStockCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = ChinaAStockCommissionModel(metadata)
        
        assert model._is_sh_market("600000.SH") is True
        assert model._is_sh_market("600000.SSE") is True
        assert model._is_sh_market("000001.SZ") is False
        assert model._is_sh_market("000001.SZSE") is False
        assert model._is_sh_market("NASDAQ:AAPL") is False


class TestFixedCommissionModel:
    """测试固定手续费模型"""
    
    def test_initialization(self):
        """测试初始化"""
        metadata = PluginMetadata(
            name="FixedCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = FixedCommissionModel(metadata)
        assert model.metadata == metadata
        assert model._buy_commission_rate == Decimal("0.0003")
        assert model._sell_commission_rate == Decimal("0.0003")
        assert model._min_commission == Decimal("1.0")
    
    def test_calculate_commission_buy(self):
        """测试计算买入手续费"""
        metadata = PluginMetadata(
            name="FixedCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = FixedCommissionModel(metadata)
        
        buy_fill = Fill(
            order_id="buy_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        commission = model.calculate_commission(buy_fill)
        
        # 计算期望手续费：10.0 * 100 * 0.0003 = 0.3
        expected_commission = buy_fill.price * buy_fill.quantity * model._buy_commission_rate
        expected_commission = max(expected_commission, model._min_commission)
        
        assert commission == expected_commission
    
    def test_calculate_commission_sell(self):
        """测试计算卖出手续费"""
        metadata = PluginMetadata(
            name="FixedCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = FixedCommissionModel(metadata)
        
        sell_fill = Fill(
            order_id="sell_order",
            symbol="TEST.SH",
            side="sell",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        commission = model.calculate_commission(sell_fill)
        
        # 计算期望手续费：10.0 * 100 * 0.0003 = 0.3
        expected_commission = sell_fill.price * sell_fill.quantity * model._sell_commission_rate
        expected_commission = max(expected_commission, model._min_commission)
        
        assert commission == expected_commission
    
    def test_different_buy_sell_rates(self):
        """测试不同的买卖费率"""
        metadata = PluginMetadata(
            name="FixedCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        config = {
            "buy_commission_rate": 0.0002,
            "sell_commission_rate": 0.0004,
            "min_commission": 0.1  # 降低最小手续费
        }
        
        model = FixedCommissionModel(metadata, config)
        
        buy_fill = Fill(
            order_id="buy_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("1000"),  # 增加交易量
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        sell_fill = Fill(
            order_id="sell_order",
            symbol="TEST.SH",
            side="sell",
            quantity=Decimal("1000"),  # 增加交易量
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        buy_commission = model.calculate_commission(buy_fill)
        sell_commission = model.calculate_commission(sell_fill)
        
        # 卖出手续费应该是买入的两倍
        assert sell_commission == buy_commission * 2
    
    def test_min_max_commission_limits(self):
        """测试最小最大手续费限制"""
        metadata = PluginMetadata(
            name="FixedCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        config = {
            "buy_commission_rate": 0.0001,
            "min_commission": 5.0,
            "max_commission": 100.0
        }
        
        model = FixedCommissionModel(metadata, config)
        
        # 小金额订单，应该使用最小手续费
        small_fill = Fill(
            order_id="small_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("1"),
            price=Decimal("1.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        small_commission = model.calculate_commission(small_fill)
        assert small_commission == Decimal("5.0")
        
        # 大金额订单，应该使用最大手续费
        large_fill = Fill(
            order_id="large_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100000"),
            price=Decimal("100.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        large_commission = model.calculate_commission(large_fill)
        assert large_commission == Decimal("100.0")


class TestTieredCommissionModel:
    """测试阶梯手续费模型"""
    
    def test_initialization(self):
        """测试初始化"""
        metadata = PluginMetadata(
            name="TieredCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = TieredCommissionModel(metadata)
        assert model.metadata == metadata
        assert len(model._tiers) == 3  # 默认3个阶梯
        assert model._min_commission == Decimal("1.0")
        assert model._cumulative_mode is False
    
    def test_initialization_with_custom_tiers(self):
        """测试自定义阶梯初始化"""
        metadata = PluginMetadata(
            name="TieredCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        config = {
            "tiers": [
                {"min_value": 0, "max_value": 50000, "rate": 0.0005},
                {"min_value": 50000, "max_value": 200000, "rate": 0.0003},
                {"min_value": 200000, "max_value": float("inf"), "rate": 0.0001}
            ],
            "min_commission": 2.0,
            "cumulative_mode": True
        }
        
        model = TieredCommissionModel(metadata, config)
        assert len(model._tiers) == 3
        assert model._min_commission == Decimal("2.0")
        assert model._cumulative_mode is True
        
        # 检查阶梯配置
        assert model._tiers[0]["rate"] == Decimal("0.0005")
        assert model._tiers[1]["rate"] == Decimal("0.0003")
        assert model._tiers[2]["rate"] == Decimal("0.0001")
    
    def test_get_applicable_rate(self):
        """测试获取适用费率"""
        metadata = PluginMetadata(
            name="TieredCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = TieredCommissionModel(metadata)
        
        # 测试不同金额的费率
        # 默认阶梯: 0-100k (0.0003), 100k-1M (0.0002), 1M+ (0.0001)
        
        # 小金额
        small_rate = model._get_applicable_rate("TEST.SH", Decimal("50000"))
        assert small_rate == Decimal("0.0003")
        
        # 中等金额
        medium_rate = model._get_applicable_rate("TEST.SH", Decimal("500000"))
        assert medium_rate == Decimal("0.0002")
        
        # 大金额
        large_rate = model._get_applicable_rate("TEST.SH", Decimal("2000000"))
        assert large_rate == Decimal("0.0001")
    
    def test_calculate_commission_tiered(self):
        """测试阶梯手续费计算"""
        metadata = PluginMetadata(
            name="TieredCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = TieredCommissionModel(metadata)
        
        # 小金额订单
        small_fill = Fill(
            order_id="small_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        small_commission = model.calculate_commission(small_fill)
        
        # 应该使用第一阶梯的费率
        trade_value = small_fill.price * small_fill.quantity
        expected_commission = trade_value * Decimal("0.0003")  # 第一阶梯
        expected_commission = max(expected_commission, model._min_commission)
        
        assert small_commission == expected_commission
        
        # 大金额订单
        large_fill = Fill(
            order_id="large_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("200.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        large_commission = model.calculate_commission(large_fill)
        
        # 应该使用第三阶梯的费率（2,000,000 > 1,000,000）
        trade_value = large_fill.price * large_fill.quantity
        expected_commission = trade_value * Decimal("0.0001")  # 第三阶梯
        expected_commission = max(expected_commission, model._min_commission)
        
        assert large_commission == expected_commission
    
    def test_cumulative_mode(self):
        """测试累积模式"""
        metadata = PluginMetadata(
            name="TieredCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        config = {"cumulative_mode": True}
        model = TieredCommissionModel(metadata, config)
        
        # 第一笔订单
        first_fill = Fill(
            order_id="first_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("800.0"),  # 80,000
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        first_commission = model.calculate_commission(first_fill)
        
        # 第二笔订单
        second_fill = Fill(
            order_id="second_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("800.0"),  # 80,000
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        second_commission = model.calculate_commission(second_fill)
        
        # 累积模式下，第二笔订单应该考虑累积交易量
        # 第一笔: 80,000 (第一阶梯 0.0003)
        # 第二笔: 80,000 + 80,000 = 160,000 (第二阶梯 0.0002)
        
        # 第二笔的手续费应该更低（使用第二阶梯费率）
        assert second_commission < first_commission


class TestPerShareCommissionModel:
    """测试按股计费模型"""
    
    def test_initialization(self):
        """测试初始化"""
        metadata = PluginMetadata(
            name="PerShareCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = PerShareCommissionModel(metadata)
        assert model.metadata == metadata
        assert model._per_share_fee == Decimal("0.005")
        assert model._min_commission == Decimal("1.0")
        assert model._max_commission == Decimal("100.0")
    
    def test_calculate_commission_per_share(self):
        """测试按股计费"""
        metadata = PluginMetadata(
            name="PerShareCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = PerShareCommissionModel(metadata)
        
        fill = Fill(
            order_id="test_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("1000"),
            price=Decimal("50.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        commission = model.calculate_commission(fill)
        
        # 计算期望手续费：1000 * 0.005 = 5.0
        expected_commission = fill.quantity * model._per_share_fee
        expected_commission = max(expected_commission, model._min_commission)
        expected_commission = min(expected_commission, model._max_commission)
        
        assert commission == expected_commission
    
    def test_min_max_commission_limits(self):
        """测试最小最大手续费限制"""
        metadata = PluginMetadata(
            name="PerShareCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        config = {
            "per_share_fee": 0.01,
            "min_commission": 2.0,
            "max_commission": 50.0
        }
        
        model = PerShareCommissionModel(metadata, config)
        
        # 小订单，应该使用最小手续费
        small_fill = Fill(
            order_id="small_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("10"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        small_commission = model.calculate_commission(small_fill)
        assert small_commission == Decimal("2.0")  # 最小手续费
        
        # 大订单，应该使用最大手续费
        large_fill = Fill(
            order_id="large_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("10000"),
            price=Decimal("10.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        large_commission = model.calculate_commission(large_fill)
        assert large_commission == Decimal("50.0")  # 最大手续费
    
    def test_price_independence(self):
        """测试价格无关性"""
        metadata = PluginMetadata(
            name="PerShareCommissionModel",
            version="1.0.0",
            description="Test",
            author="Test",
            category="commission_model",
            tags=["test"]
        )
        
        model = PerShareCommissionModel(metadata)
        
        # 同样股数，不同价格
        low_price_fill = Fill(
            order_id="low_price_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("1.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        high_price_fill = Fill(
            order_id="high_price_order",
            symbol="TEST.SH",
            side="buy",
            quantity=Decimal("100"),
            price=Decimal("1000.0"),
            timestamp=datetime.now(),
            commission=Decimal("0"),
            slippage=Decimal("0")
        )
        
        low_commission = model.calculate_commission(low_price_fill)
        high_commission = model.calculate_commission(high_price_fill)
        
        # 手续费应该相同（只依赖股数）
        assert low_commission == high_commission