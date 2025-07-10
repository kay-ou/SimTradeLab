# -*- coding: utf-8 -*-
"""
PTrade上下文管理器测试

测试PTradeContext的功能和属性管理
"""

import pytest

from simtradelab.adapters.ptrade.context import PTradeContext
from simtradelab.adapters.ptrade.models import Blotter, Portfolio, Position


class TestPTradeContext:
    """测试PTrade上下文"""

    @pytest.fixture
    def portfolio(self):
        """创建测试组合"""
        return Portfolio(cash=1000000.0)

    @pytest.fixture
    def blotter(self):
        """创建测试订单记录器"""
        return Blotter()

    @pytest.fixture
    def context(self, portfolio, blotter):
        """创建测试上下文"""
        return PTradeContext(portfolio=portfolio, blotter=blotter)

    def test_context_initialization(self, context, portfolio, blotter):
        """测试上下文初始化"""
        assert context.portfolio is portfolio
        assert context.blotter is blotter
        assert context.current_dt is None
        assert context.universe == []
        assert context.benchmark is None

    def test_context_initialization_with_optional_params(self):
        """测试带可选参数的上下文初始化"""
        portfolio = Portfolio(cash=500000.0)
        blotter = Blotter()
        universe = ["000001.XSHE", "000002.XSHE"]
        benchmark = "000300.SH"

        context = PTradeContext(
            portfolio=portfolio, blotter=blotter, universe=universe, benchmark=benchmark
        )

        assert context.portfolio is portfolio
        assert context.blotter is blotter
        assert context.universe == universe
        assert context.benchmark == benchmark

    def test_set_universe(self, context):
        """测试设置股票池"""
        universe = ["000001.XSHE", "000002.XSHE", "600000.XSHG"]
        context.universe = universe
        assert context.universe == universe

    def test_set_benchmark(self, context):
        """测试设置基准"""
        benchmark = "000300.SH"
        context.benchmark = benchmark
        assert context.benchmark == benchmark

    def test_set_current_time(self, context):
        """测试设置当前时间"""
        import datetime

        current_time = datetime.datetime(2023, 12, 29, 9, 30, 0)
        context.current_time = current_time
        assert context.current_time == current_time

    def test_dynamic_attributes(self, context):
        """测试动态属性设置"""
        # 测试可以动态添加属性
        context.custom_attr = "custom_value"
        assert context.custom_attr == "custom_value"

        # 测试策略参数
        context.strategy_params = {"param1": 10, "param2": "test"}
        assert context.strategy_params == {"param1": 10, "param2": "test"}

    def test_portfolio_access(self, context):
        """测试组合访问"""
        # 测试可以通过上下文访问组合
        assert context.portfolio.total_value > 0
        assert context.portfolio.cash == 1000000.0

    def test_blotter_access(self, context):
        """测试订单记录器访问"""
        # 测试可以通过上下文访问订单记录器
        assert context.blotter is not None
        assert len(context.blotter.orders) == 0

    def test_context_string_representation(self, context):
        """测试上下文字符串表示"""
        str_repr = str(context)
        assert "PTradeContext" in str_repr
        assert "portfolio" in str_repr.lower()

    def test_context_attribute_error(self, context):
        """测试访问不存在属性"""
        with pytest.raises(AttributeError):
            _ = context.nonexistent_attribute

    def test_context_with_positions(self, context):
        """测试上下文可以正确管理持仓信息 - 这是量化交易的核心功能"""
        # 业务场景：用户买入股票后，持仓应该正确更新
        position = Position(
            sid="000001.XSHE",
            enable_amount=1000,
            amount=1000,
            last_sale_price=12.5,
            cost_basis=10.0,
        )
        context.portfolio.positions["000001.XSHE"] = position

        # 验证业务逻辑：用户应该能查询到持仓信息
        assert "000001.XSHE" in context.portfolio.positions
        position_data = context.portfolio.positions["000001.XSHE"]
        assert position_data.amount == 1000
        assert position_data.cost_basis == 10.0

        # 验证业务价值：持仓盈亏计算应该正确
        # 成本：1000股 × 10.0元 = 10000元
        # 现值：1000股 × 12.5元 = 12500元
        # 预期盈利：2500元
        assert position_data.market_value == 12500.0
        assert position_data.pnl == 2500.0  # 验证盈亏计算

    def test_context_copy_behavior(self, context):
        """测试上下文复制行为"""
        # 修改上下文属性
        context.test_attr = "original"

        # 创建浅拷贝引用
        context_ref = context
        context_ref.test_attr = "modified"

        # 原上下文应该也被修改（因为是引用）
        assert context.test_attr == "modified"

    def test_context_universe_operations(self, context):
        """测试股票池操作"""
        # 初始为空
        assert len(context.universe) == 0

        # 添加股票
        context.universe = ["000001.XSHE"]
        assert len(context.universe) == 1

        # 扩展股票池
        context.universe.extend(["000002.XSHE", "600000.XSHG"])
        assert len(context.universe) == 3
        assert "000001.XSHE" in context.universe
        assert "000002.XSHE" in context.universe
        assert "600000.XSHG" in context.universe

    def test_context_benchmark_validation(self, context):
        """测试基准设置验证"""
        # 设置有效基准
        valid_benchmarks = ["000300.SH", "000905.SH", "399006.SZ"]

        for benchmark in valid_benchmarks:
            context.benchmark = benchmark
            assert context.benchmark == benchmark

    def test_context_serialization_data(self, context):
        """测试上下文序列化数据"""
        # 设置一些数据
        context.universe = ["000001.XSHE", "000002.XSHE"]
        context.benchmark = "000300.SH"
        context.custom_param = {"key": "value"}

        # 检查关键属性存在
        assert hasattr(context, "portfolio")
        assert hasattr(context, "blotter")
        assert hasattr(context, "universe")
        assert hasattr(context, "benchmark")
        assert hasattr(context, "custom_param")

    def test_context_method_delegation(self, context):
        """测试上下文应该正确委托给Portfolio和Blotter的核心业务方法"""
        # 验证Portfolio核心功能可访问性 - 这对量化交易至关重要
        assert hasattr(context.portfolio, "update_portfolio_value")
        assert hasattr(context.portfolio, "positions")
        assert hasattr(context.portfolio, "cash")

        # 验证Blotter核心功能可访问性 - 订单管理是交易的基础
        assert hasattr(context.blotter, "create_order")
        assert hasattr(context.blotter, "orders")

        # 验证业务逻辑：下单功能应该正常工作
        initial_cash = context.portfolio.cash
        order_id = context.blotter.create_order("000001.XSHE", 100, 10.0)
        assert order_id in context.blotter.orders

        # 验证订单信息正确性
        order = context.blotter.orders[order_id]
        assert order.symbol == "000001.XSHE"
        assert order.amount == 100
        assert order.limit == 10.0

        # 验证投资组合价值更新功能
        context.portfolio.update_portfolio_value()
        assert (
            context.portfolio.portfolio_value
            == context.portfolio.cash + context.portfolio.positions_value
        )

    def test_context_state_consistency(self, context):
        """测试上下文状态一致性"""
        # 修改组合现金
        original_cash = context.portfolio.cash
        context.portfolio.cash = 500000.0

        # 验证修改生效
        assert context.portfolio.cash == 500000.0
        assert context.portfolio.cash != original_cash

        # 恢复原值
        context.portfolio.cash = original_cash
        assert context.portfolio.cash == original_cash

    def test_context_thread_safety_simulation(self, context):
        """测试上下文线程安全性模拟"""
        import threading
        import time

        results = []

        def modify_context(value):
            context.thread_test_attr = value
            time.sleep(0.01)  # 模拟并发
            results.append(context.thread_test_attr)

        # 创建并启动多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=modify_context, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果（最后的值应该是某个线程设置的值）
        assert hasattr(context, "thread_test_attr")
        assert len(results) == 5

    def test_context_memory_usage(self, context):
        """测试上下文内存使用"""
        # 添加大量属性以测试内存处理
        for i in range(100):
            setattr(context, f"attr_{i}", f"value_{i}")

        # 验证属性存在
        assert context.attr_0 == "value_0"
        assert context.attr_99 == "value_99"

        # 删除属性
        for i in range(100):
            delattr(context, f"attr_{i}")

        # 验证属性已删除
        assert not hasattr(context, "attr_0")
        assert not hasattr(context, "attr_99")

    def test_context_with_none_values(self):
        """测试上下文能正确处理None值输入 - 确保系统的鲁棒性"""
        portfolio = Portfolio(cash=1000000.0)
        blotter = Blotter()

        # 业务场景：用户可能传入None值，系统应该优雅处理
        context = PTradeContext(
            portfolio=portfolio, blotter=blotter, universe=None, benchmark=None
        )

        # 验证系统鲁棒性：系统应该能正确处理None值
        assert context.universe is None  # 接受None作为"未设置"的状态
        assert context.benchmark is None  # 无基准是可接受的

        # 验证基础功能仍然正常工作
        assert context.portfolio.cash == 1000000.0
        assert len(context.blotter.orders) == 0

    def test_context_equality(self, portfolio, blotter):
        """测试上下文相等性"""
        context1 = PTradeContext(portfolio=portfolio, blotter=blotter)
        context2 = PTradeContext(portfolio=portfolio, blotter=blotter)

        # 不同实例不应该相等（即使内容相同）
        assert context1 is not context2

        # 但它们的属性应该引用相同的对象
        assert context1.portfolio is context2.portfolio
        assert context1.blotter is context2.blotter
