# -*- coding: utf-8 -*-
"""
交易服务测试
"""

from datetime import datetime
from unittest.mock import Mock, patch

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Blotter, Portfolio
from simtradelab.adapters.ptrade.services import TradingService
from simtradelab.core.event_bus import EventBus


class TestTradingService:
    """交易服务测试类"""

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
        self.service = TradingService(context=self.context, event_bus=self.event_bus)

    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service.context == self.context
        assert self.service.event_bus == self.event_bus

    def test_execute_order_success(self):
        """测试成功执行实盘订单"""
        security = "000001.XSHE"
        amount = 100
        limit_price = 10.0

        with patch.object(self.service, "_validate_order_risk", return_value=True):
            with patch("uuid.uuid4") as mock_uuid:
                mock_uuid.return_value.hex = "abcd1234" * 4  # 32个字符
                result = self.service.execute_order(security, amount, limit_price)

        expected_order_id = "live_abcd1234"
        assert result == expected_order_id

        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "live_trading.order.request",
            data={
                "security": security,
                "amount": amount,
                "limit_price": limit_price,
                "timestamp": self.context.current_dt,
            },
            source="trading_service",
        )

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

        with patch.object(self.service, "_get_market_price", return_value=10.0):
            with patch.object(
                self.service, "execute_order", return_value="order_123"
            ) as mock_execute:
                result = self.service.execute_order_value(security, value, limit_price)

        # 验证计算出的股数
        expected_amount = int(value / limit_price)  # 100
        mock_execute.assert_called_once_with(security, expected_amount, limit_price)
        assert result == "order_123"

    def test_execute_order_value_invalid_price(self):
        """测试获取不到有效价格时按价值执行订单"""
        with patch.object(self.service, "_get_market_price", return_value=0.0):
            result = self.service.execute_order_value("000001.XSHE", 1000.0, None)
        assert result is None

    def test_execute_order_target(self):
        """测试目标数量执行订单"""
        security = "000001.XSHE"
        target_amount = 200

        # 模拟当前持仓
        mock_position = Mock()
        mock_position.amount = 50

        with patch.object(self.service, "get_position", return_value=mock_position):
            with patch.object(
                self.service, "execute_order", return_value="order_123"
            ) as mock_execute:
                result = self.service.execute_order_target(
                    security, target_amount, 10.0
                )

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

        with patch.object(self.service, "get_position", return_value=mock_position):
            result = self.service.execute_order_target(security, target_amount, 10.0)
        assert result is None

    def test_execute_market_order(self):
        """测试执行市价订单"""
        security = "000001.XSHE"
        amount = 100

        with patch.object(
            self.service, "execute_order", return_value="order_123"
        ) as mock_execute:
            result = self.service.execute_market_order(security, amount)

        mock_execute.assert_called_once_with(security, amount, None)
        assert result == "order_123"

    def test_cancel_order(self):
        """测试取消订单"""
        order_id = "order_123"

        result = self.service.cancel_order(order_id)
        assert result is True

        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "live_trading.cancel_order.request",
            data={"order_id": order_id},
            source="trading_service",
        )

    def test_cancel_order_ex(self):
        """测试扩展撤单功能"""
        order_id = "order_123"

        with patch.object(
            self.service, "cancel_order", return_value=True
        ) as mock_cancel:
            result = self.service.cancel_order_ex(order_id)

        mock_cancel.assert_called_once_with(order_id)
        assert result is True

    def test_execute_ipo_order(self):
        """测试执行新股申购"""
        amount_per_stock = 10000

        result = self.service.execute_ipo_order(amount_per_stock)

        assert result == ["ipo_order_placeholder"]
        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "live_trading.ipo_order.request",
            data={"amount_per_stock": amount_per_stock},
            source="trading_service",
        )

    def test_execute_after_trading_order(self):
        """测试执行盘后固定价委托"""
        security = "000001.XSHE"
        amount = 100
        limit_price = 10.0

        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value.hex = "abcd1234" * 4
            result = self.service.execute_after_trading_order(
                security, amount, limit_price
            )

        expected_order_id = "after_abcd1234"
        assert result == expected_order_id

        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "live_trading.after_trading_order.request",
            data={
                "security": security,
                "amount": amount,
                "limit_price": limit_price,
            },
            source="trading_service",
        )

    def test_cancel_after_trading_order(self):
        """测试取消盘后固定价委托"""
        order_id = "order_123"

        result = self.service.cancel_after_trading_order(order_id)
        assert result is True

        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "live_trading.after_trading_cancel_order.request",
            data={"order_id": order_id},
            source="trading_service",
        )

    def test_get_position(self):
        """测试获取持仓"""
        security = "000001.XSHE"
        mock_position = Mock()
        self.portfolio.positions[security] = mock_position

        result = self.service.get_position(security)
        assert result == mock_position

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

        order2 = Mock()
        order2.status = "filled"
        order2.symbol = "000001.XSHE"

        order3 = Mock()
        order3.status = "new"
        order3.symbol = "000001.XSHE"

        self.blotter.orders = {"order1": order1, "order2": order2, "order3": order3}

        result = self.service.get_open_orders()
        assert len(result) == 2  # submitted 和 new 状态
        assert order1 in result
        assert order3 in result

    def test_get_order(self):
        """测试获取指定订单"""
        order_id = "order_123"
        mock_order = Mock()

        self.blotter.get_order = Mock(return_value=mock_order)

        result = self.service.get_order(order_id)
        assert result == mock_order
        self.blotter.get_order.assert_called_once_with(order_id)

    def test_get_order_no_blotter(self):
        """测试无交易记录器时获取订单"""
        self.context.blotter = None
        result = self.service.get_order("order_123")
        assert result is None

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

        self.blotter.orders = {"order1": order1, "order2": order2}

        result = self.service.get_trades()
        assert len(result) == 1

        trade = result[0]
        assert trade["order_id"] == "order1"
        assert trade["security"] == "000001.XSHE"
        assert trade["amount"] == 100
        assert trade["side"] == "buy"

    def test_set_parameters(self):
        """测试设置策略参数"""
        params = {"max_position": 1000, "stop_loss": 0.05}

        self.service.set_parameters(params)

        # 验证参数存储
        assert hasattr(self.context, "_parameters")
        assert self.context._parameters == params

        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "live_trading.parameters.updated",
            data={"parameters": params},
            source="trading_service",
        )

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
        # 验证事件发布
        self.event_bus.publish.assert_called_with(
            "live_trading.data.updated", data={"data": data}, source="trading_service"
        )

    def test_validate_order_risk_basic_checks(self):
        """测试基本的订单风险验证"""
        # 测试无效参数
        result = self.service._validate_order_risk("", 0, 10.0)
        assert result is False

        result = self.service._validate_order_risk("000001.XSHE", 0, 10.0)
        assert result is False

    def test_validate_order_risk_buy_order(self):
        """测试买入订单风险验证"""
        self.portfolio.cash = 1000.0

        with patch.object(self.service, "_get_market_price", return_value=10.0):
            # 资金充足的情况
            result = self.service._validate_order_risk("000001.XSHE", 50, 10.0)
            assert result is True

            # 资金不足的情况（但不阻止订单）
            result = self.service._validate_order_risk("000001.XSHE", 200, 10.0)
            assert result is True  # 实盘模式下不阻止，由券商系统处理

    def test_validate_order_risk_sell_order(self):
        """测试卖出订单风险验证"""
        # 没有持仓的情况
        result = self.service._validate_order_risk("000001.XSHE", -100, 10.0)
        assert result is True  # 实盘模式下不阻止，由券商系统处理

        # 持仓不足的情况
        mock_position = Mock()
        mock_position.amount = 50
        self.portfolio.positions["000001.XSHE"] = mock_position

        result = self.service._validate_order_risk("000001.XSHE", -100, 10.0)
        assert result is True  # 实盘模式下不阻止，由券商系统处理

    def test_get_market_price_from_context(self):
        """测试从上下文获取市场价格"""
        # 模拟上下文中有价格数据
        self.context.current_data = {"000001.XSHE": {"price": 15.0}}

        result = self.service._get_market_price("000001.XSHE")
        assert result == 15.0

    def test_get_market_price_fallback(self):
        """测试获取市场价格的默认值"""
        # 模拟无价格数据的情况
        if hasattr(self.context, "current_data"):
            delattr(self.context, "current_data")

        result = self.service._get_market_price("000001.XSHE")
        assert result == 10.0  # 默认价格
