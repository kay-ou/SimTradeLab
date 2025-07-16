# -*- coding: utf-8 -*-
"""
PTrade回测服务测试

专注测试回测系统的核心业务价值：
1. 完整的量化策略回测流程
2. 准确的交易成本和滑点计算
3. 风险控制和仓位管理
4. 回测结果的准确性和一致性
"""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Blotter, Portfolio
from simtradelab.adapters.ptrade.services.backtest_service import BacktestService
from simtradelab.core.event_bus import EventBus
from simtradelab.plugins.data.config import CSVDataPluginConfig
from simtradelab.plugins.data.sources.csv_data_plugin import CSVDataPlugin


class TestBacktestService:
    """测试回测服务的核心业务能力"""

    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录和测试数据"""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)

            dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
            n_days = len(dates)
            stable_days = int(n_days * 0.8)
            momentum_days = n_days - stable_days

            stable_prices = np.full(stable_days, 10.0) + np.random.normal(
                0, 0.05, stable_days
            )
            momentum_base = np.linspace(10.0, 12.0, momentum_days - 5)
            momentum_spike = np.linspace(12.0, 16.0, 5)
            momentum_prices = np.concatenate([momentum_base, momentum_spike])
            close_prices = np.concatenate([stable_prices, momentum_prices])

            stock1_data = pd.DataFrame(
                {
                    "security": ["000001.XSHE"] * len(dates),
                    "date": dates,
                    "open": close_prices + np.random.normal(0, 0.05, len(dates)),
                    "high": close_prices
                    + np.abs(np.random.normal(0.1, 0.05, len(dates))),
                    "low": close_prices
                    - np.abs(np.random.normal(0.1, 0.05, len(dates))),
                    "close": close_prices,
                    "volume": np.random.randint(1000000, 5000000, len(dates)),
                    "amount": np.random.randint(10000000, 50000000, len(dates)),
                }
            )
            stock1_data["low"] = stock1_data["low"].clip(lower=0.01)
            stock1_data["high"] = np.maximum(stock1_data["high"], stock1_data["close"])
            stock1_data["low"] = np.minimum(stock1_data["low"], stock1_data["close"])
            stock1_data["open"] = stock1_data["open"].clip(lower=0.01)
            stock1_file = data_dir / "000001.XSHE.csv"
            stock1_data.to_csv(stock1_file, index=False)

            close_2 = (
                20.0
                + np.sin(np.arange(len(dates)) * 0.1) * 2
                + np.random.normal(0, 0.2, len(dates))
            )
            stock2_data = pd.DataFrame(
                {
                    "security": ["000002.XSHE"] * len(dates),
                    "date": dates,
                    "open": close_2 + np.random.normal(0, 0.1, len(dates)),
                    "high": close_2 + np.abs(np.random.normal(0.2, 0.1, len(dates))),
                    "low": close_2 - np.abs(np.random.normal(0.2, 0.1, len(dates))),
                    "close": close_2,
                    "volume": np.random.randint(500000, 3000000, len(dates)),
                    "amount": np.random.randint(10000000, 60000000, len(dates)),
                }
            )
            stock2_data["low"] = stock2_data["low"].clip(lower=0.01)
            stock2_data["high"] = np.maximum(stock2_data["high"], stock2_data["close"])
            stock2_data["low"] = np.minimum(stock2_data["low"], stock2_data["close"])
            stock2_data["open"] = stock2_data["open"].clip(lower=0.01)
            stock2_data["close"] = stock2_data["close"].clip(lower=0.01)
            stock2_file = data_dir / "000002.XSHE.csv"
            stock2_data.to_csv(stock2_file, index=False)

            yield data_dir

    @pytest.fixture
    def real_data_plugin(self, temp_data_dir):
        config = CSVDataPluginConfig(data_dir=temp_data_dir)
        plugin = CSVDataPlugin(CSVDataPlugin.METADATA, config)
        plugin.initialize()
        return plugin

    @pytest.fixture
    def context(self):
        portfolio = Portfolio(cash=1000000)
        blotter = Blotter()
        context = PTradeContext(portfolio=portfolio, blotter=blotter)
        context.universe = ["000001.XSHE", "000002.XSHE"]
        context.benchmark = "000300.SH"
        return context

    @pytest.fixture
    def service(self, context, real_data_plugin):
        event_bus = EventBus()
        service = BacktestService(
            context=context, event_bus=event_bus, plugin_manager=None
        )
        service.set_commission(0.0003)
        service.set_slippage(0.001)
        service._get_data_plugin = lambda: real_data_plugin
        return service

    def test_order_execution_with_realistic_costs(self, service):
        initial_cash = service.context.portfolio.cash
        security = "000001.XSHE"
        quantity = 1000
        price = 15.0
        theoretical_value = quantity * price

        order_id = service.execute_order(security, quantity, price)
        assert order_id is not None

        order = service.get_order(order_id)
        assert order.status == "filled"

        actual_cash_used = initial_cash - service.context.portfolio.cash
        expected_slippage = theoretical_value * service._slippage_rate
        value_with_slippage = theoretical_value + expected_slippage
        expected_commission = value_with_slippage * service._commission_rate
        expected_total_cost = value_with_slippage + expected_commission

        cost_error = abs(actual_cash_used - expected_total_cost) / expected_total_cost
        assert cost_error < 0.01

        position = service.get_position(security)
        assert position.amount == quantity
        assert position.cost_basis > price

    def test_risk_management_in_backtest(self, service):
        initial_cash = service.context.portfolio.cash
        huge_order_value = initial_cash + 500000
        order_id = service.execute_order_value("000001.XSHE", huge_order_value, 15.0)
        assert order_id is None
        assert service.context.portfolio.cash == initial_cash

        valid_order_id = service.execute_order_value("000001.XSHE", 100000, 15.0)
        assert valid_order_id is not None

        position = service.get_position("000001.XSHE")
        assert position.amount > 0

        oversell_amount = position.amount + 1000
        sell_order_id = service.execute_order("000001.XSHE", -oversell_amount, 15.0)
        assert sell_order_id is None
