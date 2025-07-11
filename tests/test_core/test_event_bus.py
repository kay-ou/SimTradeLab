# -*- coding: utf-8 -*-
"""
EventBus事件总线测试

专注测试事件总线在量化交易系统中的核心业务价值：
1. 系统组件间的可靠事件通信
2. 交易事件的实时传播和处理
3. 插件系统的事件驱动架构
4. 高并发交易场景下的稳定性
"""

import asyncio
import threading
import time

import pytest

from simtradelab.core.event_bus import EventBus, default_event_bus, emit, subscribe


class TestQuantitativeTradingEventCommunication:
    """测试量化交易系统中的事件通信核心能力"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus(max_workers=2, max_history=100)
        yield bus
        bus.shutdown()

    def test_trading_system_component_communication(self, event_bus):
        """测试交易系统组件间的事件通信 - 核心业务价值"""
        # 模拟量化交易系统中的组件通信场景

        # 存储接收到的事件，模拟各组件的反应
        portfolio_updates = []
        risk_alerts = []
        strategy_signals = []

        def portfolio_manager(event):
            """投资组合管理器：响应交易事件"""
            if event.type == "order_filled":
                portfolio_updates.append(
                    {
                        "security": event.data["security"],
                        "quantity": event.data["quantity"],
                        "price": event.data["price"],
                        "timestamp": event.timestamp,
                    }
                )

        def risk_manager(event):
            """风险管理器：监控所有交易事件"""
            if event.type == "order_filled":
                order_value = event.data["quantity"] * event.data["price"]
                if order_value > 50000:  # 大额交易风险提醒
                    risk_alerts.append(
                        {
                            "type": "large_order",
                            "value": order_value,
                            "security": event.data["security"],
                        }
                    )

        def strategy_engine(event):
            """策略引擎：基于市场数据生成信号"""
            if event.type == "market_data":
                price = event.data["price"]
                if price > 100:  # 简单的价格突破策略
                    strategy_signals.append(
                        {
                            "signal": "BUY",
                            "security": event.data["security"],
                            "price": price,
                            "confidence": 0.8,
                        }
                    )

        # 订阅事件 - 模拟系统组件注册
        event_bus.subscribe("order_filled", portfolio_manager)
        event_bus.subscribe("order_filled", risk_manager)
        event_bus.subscribe("market_data", strategy_engine)

        # 模拟交易事件
        event_bus.publish(
            "order_filled",
            data={"security": "000001.XSHE", "quantity": 1000, "price": 15.5},
        )

        # 模拟大额交易事件
        event_bus.publish(
            "order_filled",
            data={"security": "000002.XSHE", "quantity": 5000, "price": 12.0},
        )

        # 模拟市场数据事件
        event_bus.publish(
            "market_data",
            data={"security": "000001.XSHE", "price": 105.5, "volume": 10000},
        )

        # 验证业务价值：系统组件间的事件通信工作正常
        assert len(portfolio_updates) == 2, "投资组合管理器应该接收到2个交易事件"
        assert len(risk_alerts) == 1, "风险管理器应该产生1个大额交易警报"
        assert len(strategy_signals) == 1, "策略引擎应该生成1个交易信号"

        # 验证事件数据完整性
        assert portfolio_updates[0]["security"] == "000001.XSHE"
        assert portfolio_updates[1]["quantity"] == 5000
        assert risk_alerts[0]["value"] == 60000  # 5000 * 12.0
        assert strategy_signals[0]["signal"] == "BUY"

    def test_plugin_system_event_driven_architecture(self, event_bus):
        """测试插件系统的事件驱动架构 - 系统扩展性验证"""
        # 模拟插件系统中的事件驱动通信
        plugin_responses = []

        def data_plugin_handler(event):
            """数据插件：响应数据请求事件"""
            if event.type == "data_request":
                # 模拟数据获取
                plugin_responses.append(
                    {
                        "plugin": "csv_data_plugin",
                        "data_type": event.data["data_type"],
                        "status": "success",
                        "result": f"data_for_{event.data['security']}",
                    }
                )

        def indicator_plugin_handler(event):
            """技术指标插件：响应指标计算事件"""
            if event.type == "indicator_request":
                plugin_responses.append(
                    {
                        "plugin": "technical_indicators_plugin",
                        "indicator": event.data["indicator"],
                        "status": "calculated",
                        "result": f"macd_values_for_{event.data['security']}",
                    }
                )

        def risk_plugin_handler(event):
            """风险插件：响应风险评估事件"""
            if event.type == "risk_assessment":
                plugin_responses.append(
                    {
                        "plugin": "risk_control_plugin",
                        "assessment": "passed",
                        "risk_level": "low",
                        "portfolio_var": event.data.get("var", 0.05),
                    }
                )

        # 模拟插件注册事件处理器
        event_bus.subscribe("data_request", data_plugin_handler)
        event_bus.subscribe("indicator_request", indicator_plugin_handler)
        event_bus.subscribe("risk_assessment", risk_plugin_handler)

        # 模拟系统请求插件服务
        event_bus.publish(
            "data_request",
            data={
                "security": "000001.XSHE",
                "data_type": "daily",
                "start_date": "2024-01-01",
            },
        )

        event_bus.publish(
            "indicator_request",
            data={
                "security": "000001.XSHE",
                "indicator": "MACD",
                "parameters": {"fast": 12, "slow": 26},
            },
        )

        event_bus.publish(
            "risk_assessment", data={"portfolio_value": 1000000, "var": 0.08}
        )

        # 验证业务价值：插件系统通过事件总线实现松耦合通信
        assert len(plugin_responses) == 3, "应该收到3个插件响应"

        # 验证各插件都响应了相应的事件
        plugin_names = [resp["plugin"] for resp in plugin_responses]
        assert "csv_data_plugin" in plugin_names
        assert "technical_indicators_plugin" in plugin_names
        assert "risk_control_plugin" in plugin_names

        # 验证插件响应的完整性
        data_response = next(
            r for r in plugin_responses if r["plugin"] == "csv_data_plugin"
        )
        assert data_response["status"] == "success"
        assert "000001.XSHE" in data_response["result"]

    def test_high_frequency_trading_event_performance(self, event_bus):
        """测试高频交易场景下的事件性能 - 系统性能验证"""
        # 模拟高频交易场景
        processed_ticks = []
        trade_signals = []

        def tick_processor(event):
            """高频tick数据处理器"""
            tick_data = event.data
            processed_ticks.append(
                {
                    "security": tick_data["security"],
                    "price": tick_data["price"],
                    "timestamp": event.timestamp,
                }
            )

            # 简单的高频交易逻辑
            if tick_data["price_change"] > 0.005:  # 价格变化超过0.5%
                trade_signals.append(
                    {
                        "action": "BUY",
                        "security": tick_data["security"],
                        "trigger_price": tick_data["price"],
                    }
                )

        # 订阅tick事件
        event_bus.subscribe("market_tick", tick_processor)

        # 模拟大量高频tick数据
        import time

        start_time = time.time()

        for i in range(100):  # 模拟100个tick
            event_bus.publish(
                "market_tick",
                data={
                    "security": "000001.XSHE",
                    "price": 100 + i * 0.01,
                    "price_change": 0.01,  # 所有tick都有足够的变化
                    "volume": 1000 + i,
                },
            )

        processing_time = time.time() - start_time

        # 验证业务价值：事件系统能处理高频数据
        assert len(processed_ticks) == 100, "应该处理了所有100个tick"
        assert len(trade_signals) == 100, "应该生成了100个交易信号"  # 所有tick都有变化
        assert processing_time < 1.0, f"处理100个tick应该在1秒内完成，实际用时{processing_time:.3f}秒"

        # 验证信号质量
        for signal in trade_signals:
            assert signal["action"] == "BUY"
            assert signal["security"] == "000001.XSHE"
            assert signal["trigger_price"] >= 100  # 第一个价格是100.0

    def test_system_error_handling_and_recovery(self, event_bus):
        """测试系统错误处理和恢复 - 系统可靠性验证"""
        # 模拟交易系统中的错误处理
        error_logs = []
        successful_operations = []

        def robust_data_handler(event):
            """健壮的数据处理器：能处理错误并继续运行"""
            try:
                data = event.data
                if data.get("corrupt", False):
                    raise ValueError("Corrupted data detected")

                successful_operations.append(
                    {
                        "operation": "data_processing",
                        "security": data["security"],
                        "status": "success",
                    }
                )
            except Exception as e:
                error_logs.append(
                    {
                        "error_type": type(e).__name__,
                        "message": str(e),
                        "recovery_action": "skip_corrupted_data",
                    }
                )

        def failing_handler(event):
            """故意失败的处理器：测试错误隔离"""
            raise RuntimeError("Critical handler failure")

        def backup_handler(event):
            """备用处理器：在主处理器失败时提供服务"""
            successful_operations.append(
                {
                    "operation": "backup_processing",
                    "security": event.data["security"],
                    "status": "recovered",
                }
            )

        # 注册处理器
        event_bus.subscribe("data_update", robust_data_handler)
        event_bus.subscribe("data_update", failing_handler)  # 会失败
        event_bus.subscribe("data_update", backup_handler)  # 备用

        # 发送正常数据
        event_bus.publish(
            "data_update",
            data={"security": "000001.XSHE", "price": 15.5, "corrupt": False},
        )

        # 发送损坏的数据
        event_bus.publish(
            "data_update",
            data={"security": "000002.XSHE", "price": 12.0, "corrupt": True},
        )

        # 验证业务价值：系统能优雅处理错误并继续运行
        assert len(successful_operations) == 3, "应该有3个成功操作(1个正常+2个备用)"
        assert len(error_logs) == 1, "应该有1个错误日志(损坏数据)"

        # 验证错误不影响整体系统运行
        normal_ops = [op for op in successful_operations if op["status"] == "success"]
        backup_ops = [op for op in successful_operations if op["status"] == "recovered"]

        assert len(normal_ops) == 1, "应该有1个正常操作"
        assert len(backup_ops) == 2, "应该有2个备用操作"

        # 验证错误被正确记录
        assert error_logs[0]["error_type"] == "ValueError"
        assert "Corrupted data" in error_logs[0]["message"]

    def test_concurrent_trading_system_stability(self, event_bus):
        """测试并发交易系统的稳定性 - 多线程环境验证"""
        # 模拟多个并发的交易组件
        order_executions = []
        processing_times = []
        lock = threading.Lock()

        def order_execution_engine(event):
            """订单执行引擎：处理下单请求"""
            start_time = time.time()
            # 模拟一些处理时间
            time.sleep(0.001)  # 1ms的处理时间

            with lock:
                order_data = event.data
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                order_executions.append(
                    {
                        "order_id": order_data["order_id"],
                        "security": order_data["security"],
                        "quantity": order_data["quantity"],
                        "status": "executed",
                        "processing_thread": threading.current_thread().ident,
                        "publisher_thread": order_data.get("publisher_thread"),
                        "processing_time": processing_time,
                    }
                )

        # 注册订单处理器
        event_bus.subscribe("place_order", order_execution_engine)

        # 记录开始时间
        test_start_time = time.time()

        # 模拟多个线程同时发送订单
        def submit_orders(thread_id, order_count):
            publisher_thread_id = threading.current_thread().ident
            for i in range(order_count):
                event_bus.publish(
                    "place_order",
                    data={
                        "order_id": f"ORD_{thread_id}_{i}",
                        "security": f"00000{thread_id}.XSHE",
                        "quantity": 100 * (i + 1),
                        "price": 15.0 + thread_id,
                        "publisher_thread": publisher_thread_id,
                    },
                )

        # 启动多个并发线程
        threads = []
        for thread_id in range(1, 6):  # 5个线程
            thread = threading.Thread(target=submit_orders, args=(thread_id, 10))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        total_test_time = time.time() - test_start_time

        # 验证业务价值：并发环境下系统稳定运行
        assert len(order_executions) == 50, "应该执行了50个订单(5个线程 * 10个订单)"

        # 验证没有重复或丢失的订单
        order_ids = [execution["order_id"] for execution in order_executions]
        assert len(set(order_ids)) == 50, "所有订单ID应该唯一"

        # 验证数据完整性 - 这是并发测试的关键
        for execution in order_executions:
            assert execution["status"] == "executed", "所有订单都应该成功执行"
            assert execution["quantity"] > 0, "订单数量应该大于0"
            assert execution["processing_time"] > 0, "处理时间应该大于0"

        # 验证每个线程的订单都被正确处理
        for thread_id in range(1, 6):
            thread_orders = [
                ex for ex in order_executions if f"ORD_{thread_id}_" in ex["order_id"]
            ]
            assert len(thread_orders) == 10, f"线程{thread_id}应该处理了10个订单"

            # 验证每个线程的订单数据完整性
            for order in thread_orders:
                expected_security = f"00000{thread_id}.XSHE"
                assert order["security"] == expected_security, "订单证券代码应该正确"

        # 验证EventBus的线程安全性 - 通过检查处理顺序和数据一致性
        # 如果有竞争条件，订单可能丢失或重复，但我们已经验证了50个唯一订单
        assert len(order_executions) == len(order_ids), "处理的订单数应该等于唯一订单数"

        # 验证EventBus统计信息的正确性（这也测试了内部状态的线程安全性）
        stats = event_bus.get_stats()
        assert stats["events_published"] == 50, "应该发布了50个事件"
        assert stats["events_processed"] == 50, "应该处理了50个事件"

        # 验证性能特征：即使在并发环境下，系统也应该高效
        avg_processing_time = sum(processing_times) / len(processing_times)
        assert (
            avg_processing_time < 0.1
        ), f"平均处理时间不应超过100ms，实际：{avg_processing_time:.3f}秒"

        # 验证总体执行时间合理（所有50个事件能够在合理时间内处理完成）
        assert total_test_time < 2.0, f"总测试时间不应超过2秒，实际：{total_test_time:.3f}s"


class TestEventSystemAsyncCapabilities:
    """测试事件系统的异步处理能力"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus(max_workers=2, max_history=100)
        yield bus
        bus.shutdown()

    @pytest.mark.asyncio
    async def test_real_time_data_processing_async(self, event_bus):
        """测试实时数据的异步处理能力 - 量化系统的核心需求"""
        # 模拟实时市场数据异步处理
        processed_data = []
        calculated_indicators = []

        async def async_data_processor(event):
            """异步数据处理器：模拟复杂的数据清洗和验证"""
            await asyncio.sleep(0.01)  # 模拟数据处理延迟
            market_data = event.data
            processed_data.append(
                {
                    "security": market_data["security"],
                    "cleaned_price": round(market_data["price"], 2),
                    "normalized_volume": market_data["volume"] / 1000,
                    "processing_time": "async",
                }
            )
            return f"processed_{market_data['security']}"

        async def async_indicator_calculator(event):
            """异步技术指标计算器：模拟复杂的技术分析"""
            await asyncio.sleep(0.005)  # 模拟计算延迟
            market_data = event.data
            # 模拟MACD计算
            macd_value = market_data["price"] * 0.1  # 简化计算
            calculated_indicators.append(
                {
                    "security": market_data["security"],
                    "macd": macd_value,
                    "rsi": 50 + (market_data["price"] % 100),
                    "calculation_type": "async",
                }
            )
            return f"indicators_{market_data['security']}"

        def sync_logger(event):
            """同步日志记录器：快速记录事件"""
            return f"logged_{event.data['security']}"

        # 注册异步和同步处理器
        event_bus.subscribe("market_data", async_data_processor)
        event_bus.subscribe("market_data", async_indicator_calculator)
        event_bus.subscribe("market_data", sync_logger)

        # 异步发布市场数据事件
        results = await event_bus.publish_async(
            "market_data",
            data={
                "security": "000001.XSHE",
                "price": 105.75,
                "volume": 15000,
                "timestamp": time.time(),
            },
        )

        # 验证业务价值：异步处理器和同步处理器都正常工作
        assert len(results) == 3, "应该有3个处理器的结果"
        assert "processed_000001.XSHE" in results
        assert "indicators_000001.XSHE" in results
        assert "logged_000001.XSHE" in results

        # 验证异步数据处理
        assert len(processed_data) == 1
        assert processed_data[0]["security"] == "000001.XSHE"
        assert processed_data[0]["cleaned_price"] == 105.75

        # 验证异步指标计算
        assert len(calculated_indicators) == 1
        assert abs(calculated_indicators[0]["macd"] - 10.575) < 0.001  # 允许浮点数精度误差
        assert (
            abs(calculated_indicators[0]["rsi"] - (50 + (105.75 % 100))) < 0.001
        )  # 修正RSI计算

    @pytest.mark.asyncio
    async def test_async_error_isolation(self, event_bus):
        """测试异步处理中的错误隔离 - 系统稳定性保障"""
        successful_results = []

        async def failing_async_processor(event):
            """失败的异步处理器"""
            raise RuntimeError("Async processing failed")

        async def working_async_processor(event):
            """正常的异步处理器"""
            await asyncio.sleep(0.01)
            result = f"async_success_{event.data['security']}"
            successful_results.append(result)
            return result

        def working_sync_processor(event):
            """正常的同步处理器"""
            result = f"sync_success_{event.data['security']}"
            successful_results.append(result)
            return result

        # 注册处理器（包括会失败的）
        event_bus.subscribe("order_event", failing_async_processor)
        event_bus.subscribe("order_event", working_async_processor)
        event_bus.subscribe("order_event", working_sync_processor)

        # 异步发布事件
        results = await event_bus.publish_async(
            "order_event",
            data={"security": "000001.XSHE", "order_id": "ORD_001", "quantity": 1000},
        )

        # 验证业务价值：错误处理器不影响其他处理器
        assert len(results) == 3, "应该有3个处理器的结果"
        assert None in results, "失败的处理器应该返回None"
        assert "async_success_000001.XSHE" in results
        assert "sync_success_000001.XSHE" in results

        # 验证成功的处理器都执行了
        assert len(successful_results) == 2
        assert "async_success_000001.XSHE" in successful_results
        assert "sync_success_000001.XSHE" in successful_results


class TestEventFilteringInTradingScenarios:
    """测试交易场景中的事件过滤功能"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus()
        yield bus
        bus.shutdown()

    def test_trading_event_filtering_by_risk_level(self, event_bus):
        """测试基于风险级别的交易事件过滤 - 风险控制的核心需求"""
        high_risk_trades = []
        all_trades = []

        def high_risk_handler(event):
            """只处理高风险交易的处理器"""
            trade_data = event.data
            high_risk_trades.append(
                {
                    "order_id": trade_data["order_id"],
                    "value": trade_data["value"],
                    "risk_level": "high",
                }
            )

        def all_trades_handler(event):
            """处理所有交易的处理器"""
            all_trades.append(event.data["order_id"])

        def high_risk_filter(event):
            """高风险过滤器：只允许大额交易通过"""
            return event.data.get("value", 0) > 100000  # 10万以上为高风险

        # 订阅时应用过滤器
        event_bus.subscribe(
            "trade_order", high_risk_handler, filter_func=high_risk_filter
        )
        event_bus.subscribe("trade_order", all_trades_handler)  # 无过滤器

        # 发布低风险交易
        event_bus.publish(
            "trade_order",
            data={"order_id": "ORD_001", "security": "000001.XSHE", "value": 50000},
        )

        # 发布高风险交易
        event_bus.publish(
            "trade_order",
            data={"order_id": "ORD_002", "security": "000002.XSHE", "value": 150000},
        )

        # 发布另一个高风险交易
        event_bus.publish(
            "trade_order",
            data={"order_id": "ORD_003", "security": "000003.XSHE", "value": 200000},
        )

        # 验证业务价值：过滤器正确识别高风险交易
        assert len(all_trades) == 3, "全部交易处理器应该处理3个交易"
        assert len(high_risk_trades) == 2, "高风险处理器应该只处理2个高风险交易"

        # 验证过滤的准确性
        high_risk_order_ids = [trade["order_id"] for trade in high_risk_trades]
        assert "ORD_002" in high_risk_order_ids
        assert "ORD_003" in high_risk_order_ids
        assert "ORD_001" not in high_risk_order_ids  # 低风险交易被过滤

    def test_market_condition_based_event_filtering(self, event_bus):
        """测试基于市场条件的事件过滤 - 策略适应性需求"""
        volatile_market_signals = []
        normal_market_signals = []

        def volatile_market_strategy(event):
            """波动市场策略：仅在高波动时执行"""
            market_data = event.data
            volatile_market_signals.append(
                {
                    "security": market_data["security"],
                    "strategy": "volatility_breakout",
                    "volatility": market_data["volatility"],
                }
            )

        def normal_market_strategy(event):
            """正常市场策略：在非高波动时执行"""
            market_data = event.data
            normal_market_signals.append(
                {
                    "security": market_data["security"],
                    "strategy": "trend_following",
                    "volatility": market_data["volatility"],
                }
            )

        def high_volatility_filter(event):
            """高波动过滤器"""
            return event.data.get("volatility", 0) > 0.05  # 5%以上波动率

        def low_volatility_filter(event):
            """低波动过滤器"""
            return event.data.get("volatility", 0) <= 0.05

        # 根据市场条件订阅不同策略
        event_bus.subscribe(
            "market_update",
            volatile_market_strategy,
            filter_func=high_volatility_filter,
        )
        event_bus.subscribe(
            "market_update", normal_market_strategy, filter_func=low_volatility_filter
        )

        # 模拟不同波动率的市场数据
        market_conditions = [
            {"security": "000001.XSHE", "price": 100, "volatility": 0.02},  # 低波动
            {"security": "000002.XSHE", "price": 200, "volatility": 0.08},  # 高波动
            {"security": "000003.XSHE", "price": 150, "volatility": 0.03},  # 低波动
            {"security": "000004.XSHE", "price": 300, "volatility": 0.12},  # 高波动
        ]

        for condition in market_conditions:
            event_bus.publish("market_update", data=condition)

        # 验证业务价值：策略根据市场条件自动适应
        assert len(volatile_market_signals) == 2, "应该有2个高波动市场信号"
        assert len(normal_market_signals) == 2, "应该有2个正常市场信号"

        # 验证过滤的正确性
        volatile_securities = [signal["security"] for signal in volatile_market_signals]
        normal_securities = [signal["security"] for signal in normal_market_signals]

        assert "000002.XSHE" in volatile_securities  # 8%波动率
        assert "000004.XSHE" in volatile_securities  # 12%波动率
        assert "000001.XSHE" in normal_securities  # 2%波动率
        assert "000003.XSHE" in normal_securities  # 3%波动率


class TestGlobalEventBusIntegration:
    """测试全局事件总线集成"""

    def test_system_wide_event_coordination(self):
        """测试系统级事件协调 - 全局事件总线的核心价值"""
        # 模拟系统级事件协调场景
        system_responses = []

        @subscribe("system_alert")
        def emergency_handler(event):
            """紧急情况处理器"""
            alert_data = event.data
            system_responses.append(
                {
                    "handler": "emergency",
                    "alert_type": alert_data["type"],
                    "action": "system_shutdown"
                    if alert_data["severity"] == "critical"
                    else "monitor",
                }
            )
            return f"emergency_response_{alert_data['type']}"

        @subscribe("system_alert")
        def logging_handler(event):
            """日志记录处理器"""
            system_responses.append(
                {
                    "handler": "logger",
                    "logged_event": event.type,
                    "timestamp": event.timestamp,
                }
            )
            return "logged"

        # 使用全局发布函数模拟系统警报
        results = emit(
            "system_alert",
            data={
                "type": "market_circuit_breaker",
                "severity": "high",
                "market": "XSHE",
                "trigger_time": time.time(),
            },
        )

        # 发布关键级别警报
        critical_results = emit(
            "system_alert",
            data={
                "type": "data_feed_failure",
                "severity": "critical",
                "affected_systems": ["trading", "risk", "portfolio"],
            },
        )

        # 验证业务价值：全局事件总线协调系统响应
        assert len(results) == 2, "第一个警报应该有2个处理器响应"
        assert len(critical_results) == 2, "关键警报应该有2个处理器响应"
        assert len(system_responses) == 4, "总共应该有4个系统响应"

        # 验证紧急处理器的响应
        emergency_responses = [
            r for r in system_responses if r["handler"] == "emergency"
        ]
        assert len(emergency_responses) == 2

        # 验证关键警报触发系统关闭
        critical_response = next(
            r for r in emergency_responses if r["alert_type"] == "data_feed_failure"
        )
        assert critical_response["action"] == "system_shutdown"

        # 验证高级警报只监控
        high_response = next(
            r
            for r in emergency_responses
            if r["alert_type"] == "market_circuit_breaker"
        )
        assert high_response["action"] == "monitor"

        # 清理全局订阅
        default_event_bus.unsubscribe_all("system_alert")


class TestEventBusSystemManagement:
    """测试事件总线的系统管理能力"""

    @pytest.fixture
    def event_bus(self):
        """事件总线fixture"""
        bus = EventBus(max_history=10)
        yield bus
        bus.shutdown()

    def test_trading_system_health_monitoring(self, event_bus):
        """测试交易系统健康监控 - 系统管理的核心需求"""
        # 模拟交易系统健康监控
        system_health = {"data_feed": [], "order_execution": [], "risk_management": []}

        def data_feed_monitor(event):
            system_health["data_feed"].append(
                {
                    "status": "active",
                    "latency": event.data.get("latency", 0),
                    "timestamp": event.timestamp,
                }
            )

        def order_execution_monitor(event):
            system_health["order_execution"].append(
                {
                    "orders_processed": event.data.get("orders", 0),
                    "avg_execution_time": event.data.get("execution_time", 0),
                    "timestamp": event.timestamp,
                }
            )

        def risk_management_monitor(event):
            system_health["risk_management"].append(
                {
                    "risk_checks": event.data.get("risk_checks", 0),
                    "violations": event.data.get("violations", 0),
                    "timestamp": event.timestamp,
                }
            )

        # 订阅系统健康事件
        event_bus.subscribe("system_health", data_feed_monitor)
        event_bus.subscribe("system_health", order_execution_monitor)
        event_bus.subscribe("system_health", risk_management_monitor)

        # 模拟定期健康检查
        health_reports = [
            {"component": "data_feed", "latency": 50, "status": "healthy"},
            {"component": "order_execution", "orders": 150, "execution_time": 120},
            {"component": "risk_management", "risk_checks": 200, "violations": 2},
        ]

        for report in health_reports:
            event_bus.publish("system_health", data=report)

        # 验证业务价值：系统健康监控正常运行
        assert len(system_health["data_feed"]) == 3
        assert len(system_health["order_execution"]) == 3
        assert len(system_health["risk_management"]) == 3

        # 验证监控数据质量
        assert system_health["data_feed"][0]["latency"] == 50
        assert system_health["order_execution"][1]["orders_processed"] == 150
        assert system_health["risk_management"][2]["violations"] == 2

        # 验证事件历史记录
        history = event_bus.get_event_history()
        assert len(history) == 3
        assert all(event.type == "system_health" for event in history)

        # 验证统计信息
        stats = event_bus.get_stats()
        assert stats["events_published"] == 3
        assert stats["events_processed"] == 9  # 3个事件 * 3个处理器
        assert stats["active_subscriptions"] == 3

    def test_event_bus_lifecycle_management(self, event_bus):
        """测试事件总线生命周期管理 - 系统稳定性保障"""
        # 模拟完整的事件总线生命周期
        lifecycle_events = []

        def lifecycle_tracker(event):
            lifecycle_events.append(
                {
                    "event_type": event.type,
                    "data": event.data,
                    "timestamp": event.timestamp,
                }
            )

        # 初始化阶段：订阅关键事件
        critical_events = [
            "trading_start",
            "market_open",
            "strategy_init",
            "trading_end",
        ]
        for event_type in critical_events:
            event_bus.subscribe(event_type, lifecycle_tracker)

        # 系统启动阶段
        event_bus.publish(
            "trading_start", data={"session_id": "SESS_001", "start_time": time.time()}
        )
        event_bus.publish("market_open", data={"market": "XSHE", "status": "open"})
        event_bus.publish(
            "strategy_init", data={"strategies": ["momentum", "mean_reversion"]}
        )

        # 运行阶段统计
        initial_stats = event_bus.get_stats()
        assert initial_stats["events_published"] == 3
        assert initial_stats["active_subscriptions"] == 4  # 4个事件类型

        # 系统关闭阶段
        event_bus.publish(
            "trading_end", data={"session_id": "SESS_001", "end_time": time.time()}
        )

        # 验证完整生命周期
        assert len(lifecycle_events) == 4
        event_types = [event["event_type"] for event in lifecycle_events]
        assert "trading_start" in event_types
        assert "market_open" in event_types
        assert "strategy_init" in event_types
        assert "trading_end" in event_types

        # 清理资源测试
        subscriptions_before_clear = event_bus.get_stats()["active_subscriptions"]
        cleared_count = event_bus.clear_all_subscriptions()

        assert cleared_count == subscriptions_before_clear
        assert event_bus.get_stats()["active_subscriptions"] == 0

        # 验证清理后事件历史仍可访问
        history = event_bus.get_event_history()
        assert len(history) == 4  # 历史记录保留

        # 清理历史
        event_bus.clear_history()
        assert len(event_bus.get_event_history()) == 0
