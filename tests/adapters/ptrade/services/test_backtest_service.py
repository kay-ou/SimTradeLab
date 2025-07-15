# -*- coding: utf-8 -*-
"""
回测服务测试
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Blotter, Portfolio
from simtradelab.adapters.ptrade.services import BacktestService
from simtradelab.core.event_bus import EventBus


class TestBacktestService:
    """回测服务测试类"""

    def setup_method(self):
        """设置测试环境"""
        # 模拟事件总线
        self.event_bus = Mock(spec=EventBus)

        # 模拟组合对象
        self.portfolio = Mock(spec=Portfolio)
        self.portfolio.cash = 100000.0
        self.portfolio.positions = {}

        # 模拟交易记录对象
        self.blotter = Mock(spec=Blotter)
        self.blotter.orders = {}

        # 模拟上下文
        self.context = Mock(spec=PTradeContext)
        self.context.portfolio = self.portfolio
        self.context.blotter = self.blotter
        self.context.current_dt = datetime.now()

        # 创建服务实例
        self.service = BacktestService(context=self.context, event_bus=self.event_bus)

    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service.context == self.context
        assert self.service.event_bus == self.event_bus
        assert self.service._slippage_rate == 0.0
        assert self.service._commission_rate == 0.0
        assert self.service._volume_ratio == 1.0
        assert self.service._limit_mode == "limit"

    def test_set_commission(self):
        """测试设置佣金费率"""
        commission_rate = 0.001
        self.service.set_commission(commission_rate)

        assert self.service._commission_rate == commission_rate
        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "backtest.commission.updated",
            data={"commission_rate": commission_rate},
            source="backtest_service",
        )

    def test_set_slippage(self):
        """测试设置滑点"""
        slippage_rate = 0.002
        self.service.set_slippage(slippage_rate)

        assert self.service._slippage_rate == slippage_rate
        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "backtest.slippage.updated",
            data={"slippage_rate": slippage_rate},
            source="backtest_service",
        )

    def test_set_volume_ratio(self):
        """测试设置成交比例"""
        # 测试有效比例
        ratio = 0.5
        self.service.set_volume_ratio(ratio)
        assert self.service._volume_ratio == ratio

        # 测试无效比例
        with pytest.raises(ValueError, match="Volume ratio must be between 0 and 1"):
            self.service.set_volume_ratio(1.5)

        with pytest.raises(ValueError, match="Volume ratio must be between 0 and 1"):
            self.service.set_volume_ratio(0)

    def test_set_limit_mode(self):
        """测试设置限价模式"""
        # 测试有效模式
        mode = "market"
        self.service.set_limit_mode(mode)
        assert self.service._limit_mode == mode

        # 测试无效模式
        with pytest.raises(ValueError, match="Invalid limit mode"):
            self.service.set_limit_mode("invalid_mode")

    def test_execute_order_success(self):
        """测试成功执行订单"""
        # 设置模拟条件
        security = "000001.XSHE"
        amount = 100
        limit_price = 10.0

        # 模拟创建订单成功
        mock_order_id = "order_123"
        with patch.object(self.service, "_create_order", return_value=mock_order_id):
            with patch.object(self.service, "_validate_order_risk", return_value=True):
                with patch.object(self.service, "_process_order_execution"):
                    result = self.service.execute_order(security, amount, limit_price)

        assert result == mock_order_id
        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "backtest.order.executed",
            data={
                "order_id": mock_order_id,
                "security": security,
                "amount": amount,
                "limit_price": limit_price,
            },
            source="backtest_service",
        )

    def test_execute_order_no_blotter(self):
        """测试无交易记录器时执行订单"""
        self.context.blotter = None
        result = self.service.execute_order("000001.XSHE", 100, 10.0)
        assert result is None

    def test_execute_order_risk_validation_failed(self):
        """测试风险验证失败时执行订单"""
        with patch.object(self.service, "_validate_order_risk", return_value=False):
            result = self.service.execute_order("000001.XSHE", 100, 10.0)
        assert result is None

    def test_execute_order_value(self):
        """测试按价值执行订单"""
        security = "000001.XSHE"
        value = 1000.0
        limit_price = 10.0

        with patch.object(
            self.service, "execute_order", return_value="order_123"
        ) as mock_execute:
            result = self.service.execute_order_value(security, value, limit_price)

        # 验证计算出的股数
        expected_amount = int(value / limit_price)  # 100
        mock_execute.assert_called_once_with(security, expected_amount, limit_price)
        assert result == "order_123"

    def test_execute_order_target(self):
        """测试目标数量执行订单"""
        security = "000001.XSHE"
        target_amount = 200

        # 模拟当前持仓
        mock_position = Mock()
        mock_position.amount = 50
        self.portfolio.positions[security] = mock_position

        with patch.object(
            self.service, "execute_order", return_value="order_123"
        ) as mock_execute:
            result = self.service.execute_order_target(security, target_amount, 10.0)

        # 验证计算出的交易数量
        expected_trade_amount = target_amount - 50  # 150
        mock_execute.assert_called_once_with(security, expected_trade_amount, 10.0)
        assert result == "order_123"

    def test_execute_order_target_no_trade_needed(self):
        """测试目标数量等于当前持仓时无需交易"""
        security = "000001.XSHE"
        target_amount = 50

        # 模拟当前持仓
        mock_position = Mock()
        mock_position.amount = 50
        self.portfolio.positions[security] = mock_position

        result = self.service.execute_order_target(security, target_amount, 10.0)
        assert result is None

    def test_cancel_order_success(self):
        """测试成功取消订单"""
        order_id = "order_123"

        # 模拟订单存在且状态为submitted
        mock_order = Mock()
        mock_order.status = "submitted"
        self.blotter.orders[order_id] = mock_order

        result = self.service.cancel_order(order_id)

        assert result is True
        assert mock_order.status == "cancelled"
        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "backtest.order.cancelled",
            data={"order_id": order_id},
            source="backtest_service",
        )

    def test_cancel_order_not_found(self):
        """测试取消不存在的订单"""
        result = self.service.cancel_order("nonexistent_order")
        assert result is False

    def test_cancel_order_wrong_status(self):
        """测试取消状态错误的订单"""
        order_id = "order_123"

        # 模拟订单存在但状态为filled
        mock_order = Mock()
        mock_order.status = "filled"
        self.blotter.orders[order_id] = mock_order

        result = self.service.cancel_order(order_id)
        assert result is False

    def test_get_position(self):
        """测试获取持仓"""
        security = "000001.XSHE"
        mock_position = Mock()
        self.portfolio.positions[security] = mock_position

        result = self.service.get_position(security)
        assert result == mock_position

    def test_get_position_not_found(self):
        """测试获取不存在的持仓"""
        result = self.service.get_position("nonexistent")
        assert result is None

    def test_get_positions(self):
        """测试获取多个持仓"""
        securities = ["000001.XSHE", "000002.XSHE"]

        # 模拟一个持仓存在，一个不存在
        mock_position = Mock()
        mock_position.sid = "000001.XSHE"
        mock_position.amount = 100
        mock_position.enable_amount = 100
        mock_position.cost_basis = 10.0
        mock_position.last_sale_price = 11.0
        mock_position.market_value = 1100.0
        mock_position.pnl = 100.0
        mock_position.returns = 0.1
        mock_position.today_amount = 0
        mock_position.business_type = "stock"

        self.portfolio.positions["000001.XSHE"] = mock_position

        result = self.service.get_positions(securities)

        # 验证返回结果
        assert len(result) == 2
        assert result["000001.XSHE"]["amount"] == 100
        assert result["000002.XSHE"]["amount"] == 0

    def test_get_orders(self):
        """测试获取订单列表"""
        # 模拟多个订单
        order1 = Mock()
        order1.symbol = "000001.XSHE"
        order1.dt = datetime(2023, 1, 1)

        order2 = Mock()
        order2.symbol = "000002.XSHE"
        order2.dt = datetime(2023, 1, 2)

        self.blotter.orders = {"order1": order1, "order2": order2}

        # 测试获取所有订单
        result = self.service.get_orders()
        assert len(result) == 2

        # 测试按证券过滤
        result = self.service.get_orders("000001.XSHE")
        assert len(result) == 1
        assert result[0] == order1

    def test_get_open_orders(self):
        """测试获取未完成订单"""
        # 模拟不同状态的订单
        order1 = Mock()
        order1.status = "submitted"
        order1.symbol = "000001.XSHE"
        order1.dt = datetime(2023, 1, 1)

        order2 = Mock()
        order2.status = "filled"
        order2.symbol = "000001.XSHE"
        order2.dt = datetime(2023, 1, 2)

        self.blotter.orders = {"order1": order1, "order2": order2}

        result = self.service.get_open_orders()
        assert len(result) == 1
        assert result[0] == order1

    def test_get_trades(self):
        """测试获取成交记录"""
        # 模拟订单
        order1 = Mock()
        order1.status = "filled"
        order1.filled = 100
        order1.id = "order1"
        order1.symbol = "000001.XSHE"
        order1.limit = 10.0
        order1.dt = datetime(2023, 1, 1)
        order1.amount = 100

        order2 = Mock()
        order2.status = "submitted"
        order2.filled = 0
        order2.dt = datetime(2023, 1, 2)

        self.blotter.orders = {"order1": order1, "order2": order2}

        result = self.service.get_trades()
        assert len(result) == 1

        trade = result[0]
        assert trade["order_id"] == "order1"
        assert trade["security"] == "000001.XSHE"
        assert trade["amount"] == 100
        assert trade["side"] == "buy"

    def test_set_yesterday_position(self):
        """测试设置昨日持仓"""
        positions = {
            "000001.XSHE": {"amount": 100, "cost_basis": 10.0},
            "000002.XSHE": {"amount": 200, "cost_basis": 15.0},
        }

        with patch("simtradelab.adapters.ptrade.models.Position") as MockPosition:
            self.service.set_yesterday_position(positions)

        # 验证Position被正确创建
        assert MockPosition.call_count == 2
        # 验证投资组合更新
        self.portfolio.update_portfolio_value.assert_called_once()

    def test_handle_data_update(self):
        """测试处理数据更新"""
        # 模拟持仓
        mock_position = Mock()
        mock_position.last_sale_price = 10.0
        self.portfolio.positions["000001.XSHE"] = mock_position

        # 模拟数据更新
        data = {
            "000001.XSHE": {"price": 11.0},
            "000002.XSHE": {"price": 12.0},  # 这个没有持仓，应该被忽略
        }

        self.service.handle_data_update(data)

        # 验证价格更新
        assert mock_position.last_sale_price == 11.0
        # 验证投资组合价值更新
        self.portfolio.update_portfolio_value.assert_called_once()

    def test_validate_order_risk_buy_insufficient_cash(self):
        """测试买入订单资金不足的风险验证"""
        self.portfolio.cash = 100.0  # 资金不足

        result = self.service._validate_order_risk("000001.XSHE", 100, 10.0)
        assert result is False

    def test_validate_order_risk_sell_insufficient_position(self):
        """测试卖出订单持仓不足的风险验证"""
        # 没有持仓的情况
        result = self.service._validate_order_risk("000001.XSHE", -100, 10.0)
        assert result is False

        # 持仓不足的情况
        mock_position = Mock()
        mock_position.amount = 50
        self.portfolio.positions["000001.XSHE"] = mock_position

        result = self.service._validate_order_risk("000001.XSHE", -100, 10.0)
        assert result is False

    def test_validate_order_risk_success(self):
        """测试成功的风险验证"""
        # 买入订单 - 资金充足
        self.portfolio.cash = 10000.0
        result = self.service._validate_order_risk("000001.XSHE", 100, 10.0)
        assert result is True

        # 卖出订单 - 持仓充足
        mock_position = Mock()
        mock_position.amount = 200
        self.portfolio.positions["000001.XSHE"] = mock_position

        result = self.service._validate_order_risk("000001.XSHE", -100, 10.0)
        assert result is True
