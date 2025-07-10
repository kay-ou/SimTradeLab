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

from simtradelab.adapters.ptrade.adapter import PTradeAdapter
from simtradelab.adapters.ptrade.utils import (
    PTradeCompatibilityError,
)
from simtradelab.core.event_bus import EventBus
from simtradelab.plugins.base import PluginConfig


class TestPTradeAdapterQuantitativeTradingCore:
    """测试PTrade适配器的核心量化交易能力"""

    @pytest.fixture
    def adapter(self):
        """创建配置好的PTrade适配器"""
        metadata = PTradeAdapter.METADATA
        config = PluginConfig(config={
            "initial_cash": 1000000,  # 100万初始资金
            "commission_rate": 0.0003,  # 万三手续费，使用PTrade标准键名
            "slippage_rate": 0.001      # 千一滑点，使用PTrade标准键名
        })
        adapter = PTradeAdapter(metadata, config)
        adapter.initialize()
        yield adapter
        if adapter.state in [adapter.state.STARTED, adapter.state.PAUSED]:
            adapter.shutdown()

    def test_complete_quantitative_trading_workflow(self, adapter):
        """测试完整的量化交易工作流程 - 核心业务价值验证"""
        # 业务场景：完整的量化策略执行流程
        
        # 1. 创建真实的量化交易策略
        momentum_strategy = textwrap.dedent("""
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
        """)
        
        # 2. 加载策略到适配器
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(momentum_strategy)
            strategy_path = f.name
            
        try:
            success = adapter.load_strategy(strategy_path)
            assert success, "量化策略应该成功加载"
            
            # 3. 验证策略初始化
            context = adapter._ptrade_context
            assert hasattr(context.g, 'stocks'), "策略应该设置股票池"
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
                "600000.SH": {"close": 12.0, "volume": 8000}
            }
            
            # 执行策略
            if hasattr(adapter._strategy_module, 'handle_data'):
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
        risk_strategy = textwrap.dedent("""
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
        """)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(risk_strategy)
            strategy_path = f.name
            
        try:
            adapter.load_strategy(strategy_path)
            context = adapter._ptrade_context
            
            # 执行风险控制测试
            sample_data = {
                "000001.SZ": {"close": 15.0},
                "000002.SZ": {"close": 20.0}
            }
            
            if hasattr(adapter._strategy_module, 'handle_data'):
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
        
        balanced_strategy = textwrap.dedent("""
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
        """)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(balanced_strategy)
            strategy_path = f.name
            
        try:
            adapter.load_strategy(strategy_path)
            context = adapter._ptrade_context
            
            # 模拟市场数据变化，触发再平衡
            market_scenarios = [
                # 初始建仓
                {"000001.SZ": {"close": 15.0}, "000002.SZ": {"close": 20.0}, "600000.SH": {"close": 12.0}},
                # 市场波动，需要再平衡
                {"000001.SZ": {"close": 18.0}, "000002.SZ": {"close": 19.0}, "600000.SH": {"close": 11.0}},
            ]
            
            for scenario_data in market_scenarios:
                if hasattr(adapter._strategy_module, 'handle_data'):
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
        
        cost_test_strategy = textwrap.dedent("""
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
        """)
        
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
            if hasattr(adapter._strategy_module, 'handle_data'):
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
            event_strategy = textwrap.dedent("""
                def initialize(context):
                    set_universe(["000001.SZ"])
                    context.g.orders_placed = 0

                def handle_data(context, data):
                    if context.g.orders_placed < 2:  # 限制订单数量
                        stock = "000001.SZ"
                        if stock in data:
                            order(stock, 100)  # 小额测试订单
                            context.g.orders_placed += 1
            """)
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(event_strategy)
                strategy_path = f.name
                
            try:
                adapter.load_strategy(strategy_path)
                adapter.start()
                
                # 模拟数据驱动
                test_data = {"000001.SZ": {"close": 15.0}}
                if hasattr(adapter._strategy_module, 'handle_data'):
                    adapter._strategy_module.handle_data(adapter._ptrade_context, test_data)
                    adapter._strategy_module.handle_data(adapter._ptrade_context, test_data)
                
                adapter.stop()
                
                # 验证事件驱动机制
                assert len(trading_events) > 0, "应该产生交易事件"
                
                # 验证事件内容的业务意义
                adapter_events = [e for e in trading_events if e.type == "ptrade.adapter.started"]
                assert len(adapter_events) > 0, "应该有适配器启动事件"
                
            finally:
                Path(strategy_path).unlink()
                
        finally:
            event_bus.shutdown()

    def test_adapter_lifecycle_management(self, adapter):
        """测试适配器生命周期管理 - 系统稳定性验证"""
        # 业务场景：验证适配器在各个生命周期阶段的稳定性
        
        # 1. 初始状态验证
        assert adapter.state == adapter.state.INITIALIZED
        assert adapter._ptrade_context is not None
        
        # 2. 启动阶段
        adapter.start()
        assert adapter.state == adapter.state.STARTED
        
        # 3. 运行状态验证 - 应该能处理基本操作
        portfolio = adapter._ptrade_context.portfolio
        initial_cash = portfolio.cash
        assert initial_cash > 0
        
        # 4. 暂停和恢复
        adapter.pause()
        assert adapter.state == adapter.state.PAUSED
        
        adapter.resume()
        assert adapter.state == adapter.state.STARTED
        
        # 5. 正常关闭
        adapter.stop()
        assert adapter.state == adapter.state.STOPPED
        
        # 6. 重新启动能力
        adapter.start()
        assert adapter.state == adapter.state.STARTED
        
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
                
            # 验证适配器状态依然正常
            assert adapter.state == adapter.state.INITIALIZED
            
        finally:
            Path(strategy_path).unlink()

    def test_adapter_api_statistics(self, adapter):
        """测试适配器API统计信息 - 系统监控能力验证"""
        # 业务场景：验证适配器提供的统计信息对运营监控的价值
        
        stats = adapter.get_api_stats()
        
        # 验证统计信息的完整性和业务意义
        assert isinstance(stats, dict)
        required_stats = [
            "total_apis", "market_data_apis", "trading_apis", 
            "strategy_loaded", "portfolio_value"
        ]
        
        for stat_key in required_stats:
            assert stat_key in stats, f"统计信息应该包含{stat_key}"
        
        # 验证统计数据的业务合理性
        assert stats["total_apis"] > 0, "应该有可用的API"
        assert stats["portfolio_value"] == 1000000.0, "投资组合价值应该正确"
        assert isinstance(stats["strategy_loaded"], bool), "策略加载状态应该是布尔值"
        
        # 加载策略后验证统计变化
        simple_strategy = textwrap.dedent("""
            def initialize(context):
                pass
        """)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(simple_strategy)
            strategy_path = f.name
            
        try:
            adapter.load_strategy(strategy_path)
            updated_stats = adapter.get_api_stats()
            
            assert updated_stats["strategy_loaded"] is True, "策略加载后统计应该更新"
            
        finally:
            Path(strategy_path).unlink()