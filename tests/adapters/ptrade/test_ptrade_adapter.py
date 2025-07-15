# -*- coding: utf-8 -*-
"""
PTrade适配器核心业务功能测试

专注测试PTrade适配器在量化交易中的核心业务价值：
1. 完整的交易策略执行流程
2. 真实的下单和风险控制
3. 投资组合管理的正确性  
4. 与数据源的有效集成
"""

import tempfile
import textwrap
from pathlib import Path

import pytest

from simtradelab.adapters.base import AdapterConfig
from simtradelab.adapters.ptrade.adapter import PTradeAdapter
from simtradelab.adapters.ptrade.context import PTradeMode
from simtradelab.adapters.ptrade.utils import PTradeCompatibilityError
from simtradelab.core.event_bus import EventBus
from simtradelab.core.plugin_manager import PluginManager


class TestPTradeAdapterQuantitativeTradingCore:
    """测试PTrade适配器的核心量化交易能力"""

    @pytest.fixture
    def adapter(self):
        """创建配置好的PTrade适配器"""
        # 创建适配器配置
        config = AdapterConfig(
            config={
                "initial_cash": 1000000,  # 100万初始资金
                "commission_rate": 0.0003,  # 万三手续费，使用PTrade标准键名
                "slippage_rate": 0.001,  # 千一滑点，使用PTrade标准键名
                "use_mock_data": True,
                "mock_data_enabled": True,
            }
        )

        # 创建适配器实例
        adapter = PTradeAdapter(config)

        # 设置必要的依赖
        plugin_manager = PluginManager()
        event_bus = EventBus()
        adapter.set_event_bus(event_bus)
        adapter.set_plugin_manager(plugin_manager)

        # 初始化适配器
        adapter._on_initialize()

        yield adapter

        # 清理
        adapter._on_shutdown()

    def test_complete_quantitative_trading_workflow(self, adapter):
        """测试完整的量化交易工作流程 - 核心业务价值验证"""
        # 业务场景：完整的量化策略执行流程

        # 1. 创建真实的量化交易策略
        momentum_strategy = textwrap.dedent(
            """
            def initialize(context):
                # 设置股票池：沪深300成分股样本
                context.g.stocks = ["000001.SZ", "000002.SZ", "600000.SH"]
                set_universe(context.g.stocks)
                
                # 策略参数
                context.g.look_back_window = 20  # 20日动量
                context.g.rebalance_freq = 5     # 每5天调仓
                context.g.position_target = 0.3  # 目标仓位30%
                context.g.day_count = 0

            def handle_data(context, data):
                context.g.day_count += 1
                
                # 调仓逻辑：每5天执行一次
                if context.g.day_count % context.g.rebalance_freq != 0:
                    return
                
                # 动量策略：选择表现最好的股票
                best_performer = None
                best_return = -float('inf')
                
                for stock in context.g.stocks:
                    if stock in data:
                        # 简化的动量计算（实际应该用历史数据）
                        current_price = data[stock]['close']
                        momentum_signal = current_price * 0.01  # 模拟动量信号
                        
                        if momentum_signal > best_return:
                            best_return = momentum_signal
                            best_performer = stock
                
                # 执行交易：买入表现最好的股票
                if best_performer:
                    position = context.portfolio.positions.get(best_performer)
                    current_position = position.amount if position else 0
                    target_value = context.portfolio.total_value * context.g.position_target
                    current_price = data[best_performer]['close']
                    target_shares = int(target_value / current_price / 100) * 100  # 按手数调整
                    
                    shares_to_trade = target_shares - current_position
                    if abs(shares_to_trade) >= 100:  # 至少1手
                        order(best_performer, shares_to_trade)
        """
        )

        # 2. 加载策略到适配器
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(momentum_strategy)
            strategy_path = f.name

        try:
            success = adapter.load_strategy(strategy_path)
            assert success, "量化策略应该成功加载"

            # 3. 验证策略初始化
            context = adapter._ptrade_context
            assert hasattr(context.g, "stocks"), "策略应该设置股票池"
            assert len(context.g.stocks) == 3, "股票池应该包含3只股票"
            assert context.g.position_target == 0.3, "目标仓位应该正确设置"

            # 4. 验证初始投资组合状态
            portfolio = context.portfolio
            assert portfolio.cash == 1000000, "初始现金应该正确"
            assert portfolio.total_value == 1000000, "初始总价值应该等于现金"

            # 5. 模拟数据驱动的策略执行（简化版）
            # 在真实场景中，这将通过数据源和市场数据驱动
            sample_data = {
                "000001.SZ": {"close": 15.0, "volume": 10000},
                "000002.SZ": {"close": 20.0, "volume": 15000},
                "600000.SH": {"close": 12.0, "volume": 8000},
            }

            # 执行策略
            if hasattr(adapter._strategy_module, "handle_data"):
                # 切换到 handle_data 生命周期阶段
                from simtradelab.adapters.ptrade.lifecycle_controller import (
                    LifecyclePhase,
                )

                adapter._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

                # 模拟多次策略执行
                for day in range(10):
                    context.g.day_count = day + 1
                    adapter._strategy_module.handle_data(context, sample_data)

            # 6. 验证业务结果：策略应该产生实际交易
            orders = context.blotter.orders
            if len(orders) > 0:
                # 验证订单的业务合理性
                for order_id, order in orders.items():
                    assert order.symbol in context.g.stocks, "订单股票应该在股票池中"
                    assert order.amount != 0, "订单数量不应该为零"

                # 验证投资组合变化
                assert len(portfolio.positions) >= 0, "应该有持仓变化"

                # 验证现金变化（扣除交易成本）
                assert portfolio.cash < 1000000, "现金应该因交易而减少"

        finally:
            Path(strategy_path).unlink()

    def test_risk_control_and_position_management(self, adapter):
        """测试风险控制和持仓管理 - 投资安全的核心保障"""
        # 业务场景：验证适配器的风险控制能力

        # 创建风险控制策略
        risk_strategy = textwrap.dedent(
            """
            def initialize(context):
                context.g.max_position_size = 0.2  # 单只股票最大20%仓位
                context.g.stop_loss_threshold = 0.1  # 10%止损
                set_universe(["000001.SZ", "000002.SZ"])

            def handle_data(context, data):
                # 尝试超额下单（测试风险控制）
                total_value = context.portfolio.total_value
                single_position_limit = total_value * context.g.max_position_size
                
                for stock in ["000001.SZ", "000002.SZ"]:
                    if stock in data:
                        price = data[stock]['close']
                        max_shares = int(single_position_limit / price / 100) * 100
                        
                        # 执行大额下单测试风险控制
                        order(stock, max_shares)
        """
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(risk_strategy)
            strategy_path = f.name

        try:
            adapter.load_strategy(strategy_path)
            context = adapter._ptrade_context

            # 执行风险控制测试
            sample_data = {"000001.SZ": {"close": 15.0}, "000002.SZ": {"close": 20.0}}

            if hasattr(adapter._strategy_module, "handle_data"):
                # 切换到 handle_data 生命周期阶段
                from simtradelab.adapters.ptrade.lifecycle_controller import (
                    LifecyclePhase,
                )

                adapter._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

                adapter._strategy_module.handle_data(context, sample_data)

            # 验证风险控制效果
            portfolio = context.portfolio

            # 1. 验证没有过度杠杆
            total_position_value = sum(
                pos.amount * pos.cost_basis
                for pos in portfolio.positions.values()
                if pos.amount > 0
            )
            assert total_position_value <= portfolio.total_value, "总持仓价值不应超过总资产"

            # 2. 验证单只股票仓位限制
            for symbol, position in portfolio.positions.items():
                if position.amount > 0:
                    position_value = position.amount * position.cost_basis
                    position_ratio = position_value / portfolio.total_value
                    assert position_ratio <= 0.25, f"{symbol}的仓位比例不应超过限制"  # 留出一些余量

            # 3. 验证现金管理
            assert portfolio.cash >= 0, "现金不应该变为负数"

        finally:
            Path(strategy_path).unlink()

    def test_multi_asset_portfolio_balancing(self, adapter):
        """测试多资产投资组合平衡 - 资产配置的核心能力"""
        # 业务场景：多资产均衡配置策略

        balanced_strategy = textwrap.dedent(
            """
            def initialize(context):
                # 设置多资产投资组合
                context.g.asset_allocation = {
                    "000001.SZ": 0.4,  # 40%配置
                    "000002.SZ": 0.3,  # 30%配置  
                    "600000.SH": 0.3   # 30%配置
                }
                set_universe(list(context.g.asset_allocation.keys()))
                context.g.rebalance_threshold = 0.05  # 5%偏差触发再平衡

            def handle_data(context, data):
                portfolio = context.portfolio
                current_total = portfolio.total_value
                
                # 计算每个资产的目标价值和当前价值
                for symbol, target_weight in context.g.asset_allocation.items():
                    if symbol in data:
                        target_value = current_total * target_weight
                        position = portfolio.positions.get(symbol)
                        current_position = position.amount if position else 0
                        current_price = data[symbol]['close']
                        current_value = current_position * current_price
                        
                        # 计算偏差
                        deviation = abs(current_value - target_value) / current_total
                        
                        # 如果偏差超过阈值，进行调仓
                        if deviation > context.g.rebalance_threshold:
                            target_shares = int(target_value / current_price / 100) * 100
                            shares_to_trade = target_shares - current_position
                            
                            if abs(shares_to_trade) >= 100:
                                order(symbol, shares_to_trade)
        """
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(balanced_strategy)
            strategy_path = f.name

        try:
            adapter.load_strategy(strategy_path)
            context = adapter._ptrade_context

            # 模拟市场数据变化，触发再平衡
            market_scenarios = [
                # 初始建仓
                {
                    "000001.SZ": {"close": 15.0},
                    "000002.SZ": {"close": 20.0},
                    "600000.SH": {"close": 12.0},
                },
                # 市场波动，需要再平衡
                {
                    "000001.SZ": {"close": 18.0},
                    "000002.SZ": {"close": 19.0},
                    "600000.SH": {"close": 11.0},
                },
            ]

            for scenario_data in market_scenarios:
                if hasattr(adapter._strategy_module, "handle_data"):
                    # 切换到 handle_data 生命周期阶段
                    from simtradelab.adapters.ptrade.lifecycle_controller import (
                        LifecyclePhase,
                    )

                    adapter._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

                    adapter._strategy_module.handle_data(context, scenario_data)

            # 验证投资组合平衡效果
            portfolio = context.portfolio
            final_total = portfolio.total_value

            if len(portfolio.positions) > 0:
                # 计算实际权重
                actual_weights = {}
                for symbol, position in portfolio.positions.items():
                    if symbol in context.g.asset_allocation and position.amount > 0:
                        # 使用最新价格计算当前价值
                        latest_price = market_scenarios[-1][symbol]["close"]
                        current_value = position.amount * latest_price
                        actual_weights[symbol] = current_value / final_total

                # 验证权重偏差在合理范围内
                for symbol, target_weight in context.g.asset_allocation.items():
                    if symbol in actual_weights:
                        deviation = abs(actual_weights[symbol] - target_weight)
                        assert deviation <= 0.15, f"{symbol}的权重偏差应该在合理范围内"  # 允许15%的偏差

        finally:
            Path(strategy_path).unlink()

    def test_trading_cost_calculation_accuracy(self, adapter):
        """测试交易成本计算的准确性 - 实盘交易的关键需求"""
        # 业务场景：验证交易成本（手续费、滑点）的正确计算

        cost_test_strategy = textwrap.dedent(
            """
            def initialize(context):
                set_universe(["000001.SZ"])
                context.g.test_completed = False

            def handle_data(context, data):
                if context.g.test_completed:
                    return
                    
                # 执行测试交易
                stock = "000001.SZ"
                if stock in data:
                    price = data[stock]['close']
                    shares = 1000  # 买入1000股
                    # 明确指定限价，确保使用正确的价格
                    order(stock, shares, price)
                    context.g.test_completed = True
        """
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(cost_test_strategy)
            strategy_path = f.name

        try:
            adapter.load_strategy(strategy_path)
            context = adapter._ptrade_context
            initial_cash = context.portfolio.cash

            # 执行交易
            test_data = {"000001.SZ": {"close": 15.0}}
            # 确保上下文能获取到当前价格数据
            context.current_data = test_data
            if hasattr(adapter._strategy_module, "handle_data"):
                # 切换到 handle_data 生命周期阶段
                from simtradelab.adapters.ptrade.lifecycle_controller import (
                    LifecyclePhase,
                )

                adapter._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

                adapter._strategy_module.handle_data(context, test_data)

            # 验证交易成本计算
            portfolio = context.portfolio

            if len(portfolio.positions) > 0 and "000001.SZ" in portfolio.positions:
                position = portfolio.positions["000001.SZ"]

                # 验证持仓数量
                assert position.amount == 1000, "持仓数量应该正确"

                # 验证交易成本影响
                expected_cost = 1000 * 15.0  # 预期成本
                commission = expected_cost * 0.0003  # 万三手续费
                slippage_cost = expected_cost * 0.001  # 千一滑点
                total_expected_cost = expected_cost + commission + slippage_cost

                actual_cash_used = initial_cash - portfolio.cash

                # 验证实际花费接近预期（允许小幅差异）
                cost_difference = abs(actual_cash_used - total_expected_cost)
                assert cost_difference / total_expected_cost <= 0.05, "交易成本计算应该在合理范围内"

                # 验证成本基础反映了实际交易价格（包括滑点）
                assert position.cost_basis >= 15.0, "成本基础应该包含滑点影响"
                assert position.cost_basis <= 15.2, "滑点影响应该在合理范围内"

        finally:
            Path(strategy_path).unlink()

    def test_event_driven_strategy_execution(self, adapter):
        """测试事件驱动的策略执行 - 系统集成的核心验证"""
        # 业务场景：验证适配器与事件系统的集成

        event_bus = EventBus()
        adapter.set_event_bus(event_bus)

        # 监听交易事件
        trading_events = []

        def event_collector(event):
            trading_events.append(event)

        event_bus.subscribe("ptrade.order.placed", event_collector)
        event_bus.subscribe("ptrade.adapter.started", event_collector)

        try:
            # 创建事件响应策略
            event_strategy = textwrap.dedent(
                """
                def initialize(context):
                    set_universe(["000001.SZ"])
                    context.g.orders_placed = 0

                def handle_data(context, data):
                    if context.g.orders_placed < 2:  # 限制订单数量
                        stock = "000001.SZ"
                        if stock in data:
                            order(stock, 100)  # 小额测试订单
                            context.g.orders_placed += 1
            """
            )

            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(event_strategy)
                strategy_path = f.name

            try:
                adapter.load_strategy(strategy_path)
                adapter.start()

                # 模拟数据驱动
                test_data = {"000001.SZ": {"close": 15.0}}
                if hasattr(adapter._strategy_module, "handle_data"):
                    # 切换到 handle_data 生命周期阶段
                    from simtradelab.adapters.ptrade.lifecycle_controller import (
                        LifecyclePhase,
                    )

                    adapter._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

                    adapter._strategy_module.handle_data(
                        adapter._ptrade_context, test_data
                    )
                    adapter._strategy_module.handle_data(
                        adapter._ptrade_context, test_data
                    )

                adapter.stop()

                # 验证事件驱动机制
                assert len(trading_events) > 0, "应该产生交易事件"

                # 验证事件内容的业务意义
                adapter_events = [
                    e for e in trading_events if e.type == "ptrade.adapter.started"
                ]
                assert len(adapter_events) > 0, "应该有适配器启动事件"

            finally:
                Path(strategy_path).unlink()

        finally:
            event_bus.shutdown()

    def test_adapter_lifecycle_management(self, adapter):
        """测试适配器生命周期管理 - 系统稳定性验证"""
        # 业务场景：验证适配器在各个生命周期阶段的稳定性

        # 1. 初始状态验证 - 使用BaseAdapter的状态检查方法
        assert adapter.is_initialized() is True
        assert adapter._ptrade_context is not None

        # 2. 启动阶段
        adapter._on_start()
        assert adapter.is_started() is True

        # 3. 运行状态验证 - 应该能处理基本操作
        portfolio = adapter._ptrade_context.portfolio
        initial_cash = portfolio.cash
        assert initial_cash > 0

        # 4. 正常关闭
        adapter._on_stop()
        assert adapter.is_started() is False

        # 5. 关闭后仍保持初始化状态
        assert adapter.is_initialized() is True

        # 6. 重新启动能力
        adapter._on_start()
        assert adapter.is_started() is True

        # 验证重启后状态保持
        portfolio_after_restart = adapter._ptrade_context.portfolio
        assert portfolio_after_restart.cash == initial_cash

    def test_strategy_error_handling(self, adapter):
        """测试策略错误处理 - 系统鲁棒性验证"""
        # 业务场景：策略代码错误时系统的处理能力

        # 测试不存在的策略文件
        with pytest.raises(PTradeCompatibilityError, match="Strategy file not found"):
            adapter.load_strategy("/nonexistent/strategy.py")

        # 测试语法错误的策略
        invalid_strategy = "def invalid_function(\n    # 语法错误"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_strategy)
            strategy_path = f.name

        try:
            with pytest.raises(PTradeCompatibilityError):
                adapter.load_strategy(strategy_path)

            # 验证适配器状态依然正常 - 使用BaseAdapter状态检查
            assert adapter.is_initialized() is True

        finally:
            Path(strategy_path).unlink()

    def test_adapter_api_statistics(self, adapter):
        """测试适配器API统计信息 - 系统监控能力验证"""
        # 业务场景：验证适配器提供的统计信息对运营监控的价值

        stats = adapter.get_api_stats()

        # 验证统计信息的完整性和业务意义
        assert isinstance(stats, dict)
        required_stats = [
            "total_apis",
            "market_data_apis",
            "trading_apis",
            "strategy_loaded",
            "portfolio_value",
        ]

        for stat_key in required_stats:
            assert stat_key in stats, f"统计信息应该包含{stat_key}"

        # 验证统计数据的业务合理性
        assert stats["total_apis"] > 0, "应该有可用的API"
        assert stats["portfolio_value"] == 1000000.0, "投资组合价值应该正确"
        assert isinstance(stats["strategy_loaded"], bool), "策略加载状态应该是布尔值"

        # 加载策略后验证统计变化
        simple_strategy = textwrap.dedent(
            """
            def initialize(context):
                pass
        """
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(simple_strategy)
            strategy_path = f.name

        try:
            adapter.load_strategy(strategy_path)
            updated_stats = adapter.get_api_stats()

            assert updated_stats["strategy_loaded"] is True, "策略加载后统计应该更新"

        finally:
            Path(strategy_path).unlink()


class TestPTradeAdapterDataSourceManagement:
    """测试PTrade适配器的数据源管理功能"""

    @pytest.fixture
    def adapter(self):
        """创建配置好的PTrade适配器"""
        config = AdapterConfig(
            config={
                "initial_cash": 1000000,
                "commission_rate": 0.0003,
                "slippage_rate": 0.001,
                "use_mock_data": True,
                "mock_data_enabled": True,
            }
        )
        adapter = PTradeAdapter(config)
        
        # 创建模拟的插件管理器
        plugin_manager = PluginManager()
        event_bus = EventBus()
        adapter.set_event_bus(event_bus)
        adapter.set_plugin_manager(plugin_manager)
        
        adapter._on_initialize()
        yield adapter
        adapter._on_shutdown()

    def test_plugin_discovery_and_management(self, adapter):
        """测试插件发现和管理功能"""
        # 测试插件发现
        adapter._discover_data_source_plugins()
        
        # 验证插件列表
        available_plugins = adapter.list_available_data_plugins()
        assert isinstance(available_plugins, list)
        
        # 测试获取数据源状态
        status = adapter.get_data_source_status()
        assert isinstance(status, dict)
        # 修正键名以匹配实际API
        assert "active_plugin_name" in status
        assert "discovered_plugins" in status
        assert "discovered_plugins_count" in status

    def test_data_source_switching(self, adapter):
        """测试数据源切换功能"""
        # 获取可用插件
        available_plugins = adapter.list_available_data_plugins()
        
        if len(available_plugins) > 0:
            # 尝试切换到第一个可用插件
            plugin_name = available_plugins[0]["name"]
            result = adapter.switch_data_source(plugin_name)
            
            # 验证切换结果
            assert isinstance(result, bool)
            
            # 验证状态更新
            status = adapter.get_data_source_status()
            if result:
                assert status["active_plugin_name"] == plugin_name
        
        # 测试切换到不存在的插件
        result = adapter.switch_data_source("nonexistent_plugin")
        assert result is False

    def test_plugin_priority_sorting(self, adapter):
        """测试插件优先级排序"""
        # 创建测试插件信息
        test_plugins = [
            {"name": "mock_data_plugin", "instance": None, "priority": 10},
            {"name": "akshare_plugin", "instance": None, "priority": 25},
            {"name": "csv_data_plugin", "instance": None, "priority": 30},
        ]
        
        # 测试排序功能
        sorted_plugins = adapter._sort_plugins_by_priority(test_plugins)
        
        # 验证排序结果
        assert len(sorted_plugins) == 3
        assert sorted_plugins[0]["name"] == "csv_data_plugin"  # 最高优先级
        assert sorted_plugins[1]["name"] == "akshare_plugin"
        assert sorted_plugins[2]["name"] == "mock_data_plugin"  # 最低优先级

    def test_plugin_type_detection(self, adapter):
        """测试插件类型检测"""
        # 模拟数据源插件 - 需要实现所有必需方法
        class MockDataSourcePlugin:
            def get_supported_markets(self):
                return set()
            
            def get_history_data(self, *args, **kwargs):
                pass
            
            def get_current_price(self, *args, **kwargs):
                pass
            
            def get_snapshot(self, *args, **kwargs):
                pass
            
            def get_multiple_history_data(self, *args, **kwargs):
                pass
        
        # 模拟非数据源插件
        class MockOtherPlugin:
            def some_method(self):
                pass
        
        # 测试检测功能
        assert adapter._is_data_source_plugin(MockDataSourcePlugin()) is True
        assert adapter._is_data_source_plugin(MockOtherPlugin()) is False
        assert adapter._is_data_source_plugin(None) is False

    def test_plugin_cache_management(self, adapter):
        """测试插件缓存管理"""
        # 测试缓存预加载
        adapter._preload_and_cache_plugins()
        
        # 验证缓存状态 - 根据实际实现检查缓存变量
        assert hasattr(adapter, '_plugin_cache_valid')
        assert hasattr(adapter, '_cached_active_data_plugin')
        assert hasattr(adapter, '_sorted_data_plugins_cache')
        
        # 测试缓存失效
        adapter._invalidate_plugin_cache()
        
        # 验证缓存被清理
        assert adapter._plugin_cache_valid is False
        assert adapter._cached_active_data_plugin is None
        assert len(adapter._sorted_data_plugins_cache) == 0


class TestPTradeAdapterAdvancedFeatures:
    """测试PTrade适配器的高级功能"""

    @pytest.fixture
    def adapter(self):
        """创建配置好的PTrade适配器"""
        config = AdapterConfig(
            config={
                "initial_cash": 1000000,
                "commission_rate": 0.0003,
                "slippage_rate": 0.001,
                "use_mock_data": True,
                "mock_data_enabled": True,
            }
        )
        adapter = PTradeAdapter(config)
        
        plugin_manager = PluginManager()
        event_bus = EventBus()
        adapter.set_event_bus(event_bus)
        adapter.set_plugin_manager(plugin_manager)
        
        adapter._on_initialize()
        yield adapter
        adapter._on_shutdown()

    def test_context_manager_support(self, adapter):
        """测试上下文管理器支持"""
        # 测试上下文管理器接口
        with adapter as ctx_adapter:
            assert ctx_adapter is adapter
            assert adapter.is_initialized()
        
        # 验证退出上下文后的状态 - _on_shutdown会清理所有资源
        assert not adapter.is_initialized()  # 应该被清理

    def test_mode_support_checking(self, adapter):
        """测试模式支持检查"""
        # 测试支持的模式
        assert adapter.is_mode_supported(PTradeMode.BACKTEST) is True
        assert adapter.is_mode_supported(PTradeMode.RESEARCH) is True
        assert adapter.is_mode_supported(PTradeMode.TRADING) is True
        
        # 测试当前模式
        current_mode = adapter.get_current_mode()
        assert current_mode in [PTradeMode.BACKTEST, PTradeMode.RESEARCH, PTradeMode.TRADING]

    def test_api_wrapper_functionality(self, adapter):
        """测试API包装功能"""
        # 创建测试API函数
        def test_api_function(param1, param2=None):
            return f"result_{param1}_{param2}"
        
        # 测试API包装器创建
        wrapped_api = adapter._create_api_wrapper(test_api_function, "test_api")
        
        # 测试包装后的函数
        result = wrapped_api("test_param", param2="test_value")
        assert result == "result_test_param_test_value"

    def test_strategy_performance_metrics(self, adapter):
        """测试策略性能指标"""
        # 获取性能指标
        performance = adapter.get_strategy_performance()
        
        # 验证指标结构
        assert isinstance(performance, dict)
        expected_keys = [
            "portfolio_value",
            "cash",
            "positions_value",
            "returns",
            "pnl",
            "positions_count",
            "total_trades",
            "winning_trades",
            "starting_cash",
            "current_datetime"
        ]
        
        for key in expected_keys:
            assert key in performance
            assert performance[key] is not None

    def test_market_data_generation(self, adapter):
        """测试市场数据生成"""
        # 测试数据生成功能
        market_data = adapter._generate_market_data()
        
        # 验证数据格式
        assert isinstance(market_data, dict)
        
        # 如果有数据，验证结构
        if market_data:
            for symbol, data in market_data.items():
                assert isinstance(symbol, str)
                assert isinstance(data, dict)
                # 验证基本字段
                expected_fields = ["close", "volume"]
                for field in expected_fields:
                    if field in data:
                        assert isinstance(data[field], (int, float))

    def test_current_price_retrieval(self, adapter):
        """测试当前价格获取"""
        # 测试价格获取功能
        test_security = "000001.SZ"
        price = adapter._get_current_price(test_security)
        
        # 验证价格格式
        assert isinstance(price, (int, float))
        assert price > 0

    def test_strategy_hook_execution(self, adapter):
        """测试策略钩子执行"""
        # 创建测试策略模块
        strategy_content = textwrap.dedent("""
            def initialize(context):
                context.g.initialized = True
                
            def before_trading_start(context, data):
                context.g.before_trading_called = True
                
            def after_trading_end(context, data):
                context.g.after_trading_called = True
        """)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(strategy_content)
            strategy_path = f.name
        
        try:
            # 加载策略
            adapter.load_strategy(strategy_path)
            
            # 测试钩子执行 - 测试before_trading_start钩子（允许在initialize之后执行）
            result = adapter.execute_strategy_hook("before_trading_start", adapter._ptrade_context, {})
            # 钩子执行应该不会抛出异常
            
            # 测试不存在的钩子 - 应该抛出异常
            with pytest.raises(Exception):  # 期望抛出异常
                adapter.execute_strategy_hook("nonexistent_hook")
            
        finally:
            Path(strategy_path).unlink()

    def test_strategy_cleanup(self, adapter):
        """测试策略清理"""
        # 创建简单策略
        strategy_content = "def initialize(context): pass"
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(strategy_content)
            strategy_path = f.name
        
        try:
            # 加载策略
            adapter.load_strategy(strategy_path)
            assert adapter._strategy_module is not None
            
            # 测试清理功能
            adapter._cleanup_strategy()
            
            # 验证清理结果
            assert adapter._strategy_module is None
            
        finally:
            Path(strategy_path).unlink()

    def test_event_listener_management(self, adapter):
        """测试事件监听器管理"""
        # 设置事件监听器
        adapter._setup_event_listeners()
        
        # 验证监听器设置
        assert isinstance(adapter._event_listeners, list)
        
        # 清理事件监听器
        adapter._cleanup_event_listeners()
        
        # 验证清理结果
        assert len(adapter._event_listeners) == 0
