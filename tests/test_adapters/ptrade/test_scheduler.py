# -*- coding: utf-8 -*-
"""
PTrade调度器测试

专注测试调度器的核心业务价值：
1. 量化策略的定时执行能力
2. 实时数据回调处理能力
3. 系统稳定性和错误恢复
4. 并发安全性
"""

import threading
import time
from datetime import datetime, timedelta

import pytest

from simtradelab.adapters.ptrade.scheduling.scheduler import (
    PTradeScheduler,
    ScheduleJob,
)
from simtradelab.core.event_bus import EventBus


class TestScheduleJob:
    """测试调度任务类"""

    def test_daily_strategy_scheduling(self):
        """测试每日策略调度 - 量化交易的核心需求"""
        strategy_executed = False
        strategy_results = []

        def morning_strategy():
            """模拟晨间策略：计算昨日收益率并调整仓位"""
            nonlocal strategy_executed
            strategy_executed = True
            # 模拟策略逻辑：计算收益并调整仓位
            portfolio_return = 0.025  # 2.5%收益
            strategy_results.append({
                "return": portfolio_return,
                "action": "rebalance",
                "timestamp": datetime.now()
            })
            return portfolio_return

        job = ScheduleJob(
            job_id="morning_strategy", 
            func=morning_strategy, 
            job_type="daily", 
            run_time="09:30"
        )

        # 验证业务价值：策略任务配置正确
        assert job.job_id == "morning_strategy"
        assert job.job_type == "daily"
        assert job.run_time == "09:30"
        assert job.enabled is True
        
        # 验证核心能力：策略可以执行并产生交易决策
        result = job.run()
        assert strategy_executed is True
        assert result == 0.025
        assert len(strategy_results) == 1
        assert strategy_results[0]["action"] == "rebalance"

    def test_market_open_timing_accuracy(self):
        """测试市场开盘时间调度准确性 - 确保策略在正确时机执行"""
        def market_open_strategy():
            """开盘策略：分析隔夜消息面并调整持仓"""
            return {"news_sentiment": "positive", "position_adjustment": "+5%"}

        job = ScheduleJob(
            job_id="market_open_strategy", 
            func=market_open_strategy, 
            job_type="daily", 
            run_time="09:30"
        )

        # 验证业务价值：开盘策略在正确时间执行
        assert job.next_run is not None
        assert job.next_run.hour == 9
        assert job.next_run.minute == 30
        
        # 验证策略执行能力
        result = job.run()
        assert result["news_sentiment"] == "positive"
        assert "+5%" in result["position_adjustment"]

    def test_high_frequency_monitoring(self):
        """测试高频监控任务 - 风险管理的核心需求"""
        risk_alerts = []
        
        def risk_monitor():
            """风险监控：每分钟检查组合风险指标"""
            # 模拟风险计算
            portfolio_var = 0.15  # 15% VaR
            max_drawdown = 0.08   # 8% 最大回撤
            
            if portfolio_var > 0.20 or max_drawdown > 0.10:
                risk_alerts.append({
                    "var": portfolio_var,
                    "drawdown": max_drawdown,
                    "alert_level": "high",
                    "timestamp": datetime.now()
                })
                return "RISK_ALERT"
            return "NORMAL"

        # 测试1分钟间隔的风险监控
        job = ScheduleJob(
            job_id="risk_monitor", 
            func=risk_monitor, 
            job_type="interval", 
            interval=60
        )

        now = datetime.now()
        assert job.next_run is not None
        time_diff = (job.next_run - now).total_seconds()
        assert 59 <= time_diff <= 61  # 允许1秒误差
        
        # 验证风险监控功能
        result = job.run()
        assert result == "NORMAL"  # 当前风险水平正常
        assert len(risk_alerts) == 0  # 无风险告警

    def test_strategy_rebalancing_intervals(self):
        """测试策略重平衡间隔 - 投资组合管理的关键功能"""
        rebalance_actions = []
        
        def portfolio_rebalance():
            """投资组合重平衡：每5分钟检查并调整权重"""
            # 模拟重平衡逻辑
            current_weights = {"stock_a": 0.6, "stock_b": 0.4}
            target_weights = {"stock_a": 0.5, "stock_b": 0.5}
            
            rebalance_needed = abs(current_weights["stock_a"] - target_weights["stock_a"]) > 0.05
            
            if rebalance_needed:
                rebalance_actions.append({
                    "from_weights": current_weights,
                    "to_weights": target_weights,
                    "timestamp": datetime.now()
                })
                return "REBALANCED"
            return "NO_ACTION"

        # 测试5分钟重平衡间隔
        job = ScheduleJob(
            job_id="portfolio_rebalance",
            func=portfolio_rebalance,
            job_type="interval",
            interval="5m",
        )

        now = datetime.now()
        assert job.next_run is not None
        time_diff = (job.next_run - now).total_seconds()
        assert 299 <= time_diff <= 301  # 5分钟 = 300秒
        
        # 验证重平衡功能
        result = job.run()
        assert result == "REBALANCED"  # 权重偏差超过阈值，触发重平衡
        assert len(rebalance_actions) == 1

    def test_trading_strategy_execution_flow(self):
        """测试交易策略执行流程 - 对量化交易系统的核心验证"""
        strategy_decisions = []
        
        def momentum_strategy():
            """动量策略：基于动量因子做出交易决策"""
            # 模拟动量计算
            momentum_score = 0.75  # 正动量
            confidence = 0.85
            
            decision = {
                "signal": "BUY" if momentum_score > 0.5 else "SELL",
                "strength": momentum_score,
                "confidence": confidence,
                "timestamp": datetime.now()
            }
            
            strategy_decisions.append(decision)
            return decision

        # 创建交易策略任务
        job = ScheduleJob(
            job_id="momentum_strategy", 
            func=momentum_strategy, 
            job_type="daily",
            run_time="14:30"  # 下午收盘前执行
        )

        # 模拟过去时间来触发执行
        job.next_run = datetime.now() - timedelta(hours=1)
        assert job.should_run() is True

        # 执行策略并验证结果
        result = job.run()
        
        # 验证业务价值：策略产生了有意义的交易信号
        assert result["signal"] == "BUY"
        assert result["strength"] == 0.75
        assert result["confidence"] == 0.85
        assert len(strategy_decisions) == 1
        
        # 验证任务执行时间更新
        assert job.last_run is not None
        
        # 禁用后不应该执行
        job.enabled = False
        job.next_run = datetime.now() - timedelta(hours=1)
        assert job.should_run() is False

    def test_strategy_with_parameters(self):
        """测试带参数的策略执行 - 验证参数化策略的灵活性"""
        executed_strategies = []
        
        def mean_reversion_strategy(lookback_days, threshold_std=2.0):
            """均值回归策略：使用可配置参数"""
            # 模拟均值回归计算
            z_score = -2.5  # 价格偏离均值-2.5个标准差
            
            if abs(z_score) > threshold_std:
                signal = "BUY" if z_score < -threshold_std else "SELL"
                position_size = min(abs(z_score) / threshold_std * 0.1, 0.2)  # 最多20%仓位
            else:
                signal = "HOLD"
                position_size = 0
                
            strategy_result = {
                "lookback_days": lookback_days,
                "threshold_std": threshold_std,
                "z_score": z_score,
                "signal": signal,
                "position_size": position_size
            }
            
            executed_strategies.append(strategy_result)
            return strategy_result

        job = ScheduleJob(
            job_id="mean_reversion_strategy",
            func=mean_reversion_strategy,
            job_type="daily",
            args=(20,),  # 20天回期
            kwargs={"threshold_std": 2.0},  # 2.0倍标准差阈值
        )

        result = job.run()
        
        # 验证业务价值：策略正确使用参数并产生交易信号
        assert result["lookback_days"] == 20
        assert result["threshold_std"] == 2.0
        assert result["signal"] == "BUY"  # z_score=-2.5 < -2.0，触发买入
        assert result["position_size"] == 0.125  # 2.5/2.0 * 0.1 = 0.125
        assert len(executed_strategies) == 1


class TestPTradeScheduler:
    """测试PTrade调度器"""

    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        event_bus = EventBus()
        scheduler = PTradeScheduler(event_bus)
        yield scheduler
        # 清理：停止调度器
        if scheduler._running:
            scheduler.stop()

    def test_scheduler_initialization(self, scheduler):
        """测试调度器初始化"""
        assert scheduler.event_bus is not None
        assert scheduler._running is False
        assert len(scheduler._jobs) == 0
        assert len(scheduler._tick_callbacks) == 0
        assert len(scheduler._order_response_callbacks) == 0
        assert len(scheduler._trade_response_callbacks) == 0

    def test_start_stop_scheduler(self, scheduler):
        """测试启动和停止调度器"""
        # 启动调度器
        scheduler.start()
        assert scheduler._running is True
        assert scheduler._scheduler_thread is not None
        assert scheduler._scheduler_thread.is_alive()

        # 停止调度器
        scheduler.stop()
        assert scheduler._running is False

    def test_automated_trading_system_integration(self, scheduler):
        """测试自动化交易系统集成 - 全流程业务场景"""
        executed_strategies = []
        risk_alerts = []
        
        def intraday_momentum_strategy():
            """日内动量策略：每30秒分析动量并交易"""
            # 模拟动量分析
            momentum_score = 0.82
            volume_surge = True
            price_breakout = True
            
            if momentum_score > 0.8 and volume_surge and price_breakout:
                strategy_action = {
                    "signal": "STRONG_BUY",
                    "position_size": 0.15,  # 15%仓位
                    "stop_loss": 0.03,      # 3%止损
                    "take_profit": 0.08,    # 8%止盈
                    "timestamp": datetime.now()
                }
                executed_strategies.append(strategy_action)
                return strategy_action
            return {"signal": "HOLD"}
        
        def risk_monitoring():
            """风险监控：检查组合风险指标"""
            portfolio_beta = 1.25
            max_drawdown = 0.12
            var_95 = 0.18
            
            if max_drawdown > 0.15 or var_95 > 0.20:
                risk_alert = {
                    "level": "HIGH",
                    "beta": portfolio_beta,
                    "drawdown": max_drawdown,
                    "var": var_95,
                    "action_required": "REDUCE_POSITION"
                }
                risk_alerts.append(risk_alert)
                return risk_alert
            return {"level": "NORMAL"}

        # 添加多个交易策略
        scheduler.add_interval_job(
            job_id="momentum_strategy",
            func=intraday_momentum_strategy,
            interval="30s"
        )
        
        scheduler.add_interval_job(
            job_id="risk_monitor",
            func=risk_monitoring,
            interval="1m"
        )

        # 验证系统集成
        assert "momentum_strategy" in scheduler._jobs
        assert "risk_monitor" in scheduler._jobs
        assert len(scheduler._jobs) == 2
        
        # 执行策略并验证结果
        momentum_job = scheduler._jobs["momentum_strategy"]
        risk_job = scheduler._jobs["risk_monitor"]
        
        momentum_result = momentum_job.run()
        risk_result = risk_job.run()
        
        # 验证业务价值：系统生成了完整的交易信号和风险评估
        assert momentum_result["signal"] == "STRONG_BUY"
        assert momentum_result["position_size"] == 0.15
        assert risk_result["level"] == "NORMAL"
        assert len(executed_strategies) == 1
        assert len(risk_alerts) == 0

    def test_real_time_market_data_processing(self, scheduler):
        """测试实时市场数据处理 - 量化交易的关键能力"""
        received_ticks = []
        trading_signals = []
        
        def tick_processor(tick_data):
            """实时tick数据处理：生成交易信号"""
            received_ticks.append(tick_data)
            
            # 模拟简单的动量策略
            price = tick_data.get("price", 0)
            volume = tick_data.get("volume", 0)
            
            if price > 15.0 and volume > 5000:
                signal = {
                    "symbol": tick_data["symbol"],
                    "action": "BUY",
                    "reason": "price_volume_breakout",
                    "timestamp": datetime.now()
                }
                trading_signals.append(signal)

        # 添加tick回调
        scheduler.add_tick_callback(tick_processor)
        assert len(scheduler._tick_callbacks) == 1
        
        # 模拟市场数据
        tick_data = {
            "symbol": "000001.XSHE", 
            "price": 15.5, 
            "volume": 6000,
            "timestamp": datetime.now()
        }
        
        # 触发数据处理
        scheduler.trigger_tick_data(tick_data)
        
        # 验证业务价值：系统正确处理了tick数据并生成交易信号
        assert len(received_ticks) == 1
        assert received_ticks[0] == tick_data
        assert len(trading_signals) == 1
        assert trading_signals[0]["action"] == "BUY"
        assert trading_signals[0]["symbol"] == "000001.XSHE"

    def test_order_execution_confirmation_flow(self, scheduler):
        """测试订单执行确认流程 - 交易系统的核心功能"""
        order_confirmations = []
        portfolio_updates = []
        
        def order_confirmation_handler(order_data):
            """订单确认处理：更新组合状态"""
            order_confirmations.append(order_data)
            
            # 模拟组合更新逻辑
            if order_data.get("status") == "filled":
                portfolio_update = {
                    "symbol": order_data["symbol"],
                    "new_position": order_data["quantity"],
                    "avg_cost": order_data["fill_price"],
                    "cash_used": order_data["quantity"] * order_data["fill_price"]
                }
                portfolio_updates.append(portfolio_update)
        
        scheduler.add_order_response_callback(order_confirmation_handler)
        assert len(scheduler._order_response_callbacks) == 1
        
        # 模拟订单成交回报
        order_data = {
            "order_id": "ORD_20241201_001", 
            "symbol": "000001.XSHE",
            "status": "filled",
            "quantity": 1000,
            "fill_price": 15.25,
            "timestamp": datetime.now()
        }
        
        scheduler.trigger_order_response(order_data)
        
        # 验证业务价值：订单确认触发组合更新
        assert len(order_confirmations) == 1
        assert order_confirmations[0]["order_id"] == "ORD_20241201_001"
        assert len(portfolio_updates) == 1
        assert portfolio_updates[0]["new_position"] == 1000
        assert portfolio_updates[0]["cash_used"] == 15250.0

    def test_trade_settlement_processing(self, scheduler):
        """测试交易结算处理 - 资金管理的关键环节"""
        trade_settlements = []
        risk_metrics = []
        
        def trade_settlement_handler(trade_data):
            """交易结算处理：计算盈亏和风险指标"""
            trade_settlements.append(trade_data)
            
            # 模拟盈亏计算
            quantity = trade_data.get("quantity", 0)
            price = trade_data.get("price", 0)
            trade_value = quantity * price
            
            # 模拟风险计量
            risk_metric = {
                "trade_id": trade_data.get("trade_id"),
                "trade_value": trade_value,
                "position_concentration": trade_value / 1000000,  # 假设100万组合
                "risk_level": "low" if trade_value < 50000 else "medium"
            }
            risk_metrics.append(risk_metric)
        
        scheduler.add_trade_response_callback(trade_settlement_handler)
        assert len(scheduler._trade_response_callbacks) == 1
        
        # 模拟交易数据
        trade_data = {
            "trade_id": "TRD_20241201_001", 
            "symbol": "000001.XSHE",
            "quantity": 2000,
            "price": 15.30,
            "side": "buy",
            "timestamp": datetime.now()
        }
        
        scheduler.trigger_trade_response(trade_data)
        
        # 验证业务价值：交易结算正确计算风险指标
        assert len(trade_settlements) == 1
        assert trade_settlements[0]["trade_id"] == "TRD_20241201_001"
        assert len(risk_metrics) == 1
        assert risk_metrics[0]["trade_value"] == 30600.0  # 2000 * 15.30
        assert risk_metrics[0]["position_concentration"] == 0.0306  # 30600/1000000
        assert risk_metrics[0]["risk_level"] == "low"

    def test_strategy_lifecycle_management(self, scheduler):
        """测试策略生命周期管理 - 策略的动态管理能力"""
        strategy_execution_log = []
        
        def alpha_strategy():
            """模拟Alpha策略"""
            alpha_score = 0.65
            strategy_execution_log.append({
                "strategy": "alpha",
                "score": alpha_score,
                "timestamp": datetime.now()
            })
            return alpha_score

        def beta_strategy():
            """模拟Beta策略"""
            beta_score = -0.45  # 做空信号
            strategy_execution_log.append({
                "strategy": "beta", 
                "score": beta_score,
                "timestamp": datetime.now()
            })
            return beta_score

        # 添加多个策略
        alpha_job_id = scheduler.add_daily_job("alpha_strategy", alpha_strategy, "09:30")
        beta_job_id = scheduler.add_daily_job("beta_strategy", beta_strategy, "14:00")
        
        assert alpha_job_id == "alpha_strategy"
        assert beta_job_id == "beta_strategy"
        assert len(scheduler._jobs) == 2

        # 测试策略移除
        removed = scheduler.remove_job("beta_strategy")
        assert removed is True
        assert "beta_strategy" not in scheduler._jobs
        assert len(scheduler._jobs) == 1

        # 测试移除不存在的策略
        removed_nonexistent = scheduler.remove_job("gamma_strategy")
        assert removed_nonexistent is False
        
        # 执行剩余策略
        alpha_job = scheduler._jobs["alpha_strategy"]
        result = alpha_job.run()
        
        # 验证业务价值：系统可以动态管理策略组合
        assert result == 0.65
        assert len(strategy_execution_log) == 1
        assert strategy_execution_log[0]["strategy"] == "alpha"

    def test_remove_callbacks(self, scheduler):
        """测试移除回调"""

        def tick_handler(tick_data):
            pass

        def order_handler(order_data):
            pass

        def trade_handler(trade_data):
            pass

        # 添加回调
        scheduler.add_tick_callback(tick_handler)
        scheduler.add_order_response_callback(order_handler)
        scheduler.add_trade_response_callback(trade_handler)

        # 移除回调
        assert scheduler.remove_tick_callback(tick_handler) is True
        assert scheduler.remove_order_response_callback(order_handler) is True
        assert scheduler.remove_trade_response_callback(trade_handler) is True

        # 移除不存在的回调
        assert scheduler.remove_tick_callback(tick_handler) is False

    def test_trigger_callbacks(self, scheduler):
        """测试回调触发"""
        tick_received = None
        order_received = None
        trade_received = None

        def tick_handler(tick_data):
            nonlocal tick_received
            tick_received = tick_data

        def order_handler(order_data):
            nonlocal order_received
            order_received = order_data

        def trade_handler(trade_data):
            nonlocal trade_received
            trade_received = trade_data

        # 添加回调
        scheduler.add_tick_callback(tick_handler)
        scheduler.add_order_response_callback(order_handler)
        scheduler.add_trade_response_callback(trade_handler)

        # 触发回调
        tick_data = {"symbol": "000001.XSHE", "price": 10.5}
        order_data = {"order_id": "test_order", "status": "filled"}
        trade_data = {"trade_id": "test_trade", "quantity": 100}

        scheduler.trigger_tick_data(tick_data)
        scheduler.trigger_order_response(order_data)
        scheduler.trigger_trade_response(trade_data)

        # 验证回调被正确触发
        assert tick_received == tick_data
        assert order_received == order_data
        assert trade_received == trade_data

    def test_get_jobs_status(self, scheduler):
        """测试获取任务状态"""

        def test_task():
            return "test"

        # 添加一些任务
        scheduler.add_daily_job("daily_task", test_task, "09:30")
        scheduler.add_interval_job("interval_task", test_task, 60)

        jobs_status = scheduler.get_jobs()
        assert len(jobs_status) == 2
        assert "daily_task" in jobs_status
        assert "interval_task" in jobs_status

        # 检查任务状态信息
        daily_job = jobs_status["daily_task"]
        assert daily_job["type"] == "daily"
        assert daily_job["enabled"] is True
        assert daily_job["run_time"] == "09:30"

        interval_job = jobs_status["interval_task"]
        assert interval_job["type"] == "interval"
        assert interval_job["interval"] == 60

    def test_scheduler_execution(self, scheduler):
        """测试调度器执行功能"""
        executed_jobs = []

        def quick_task(job_name):
            executed_jobs.append(job_name)

        # 添加一个快速执行的间隔任务
        scheduler.add_interval_job(
            job_id="quick_job",
            func=quick_task,
            interval="1s",  # 1秒间隔
            args=("quick_job",),
        )

        # 启动调度器
        scheduler.start()

        # 等待任务执行
        time.sleep(2.5)  # 等待足够时间让任务执行2次

        # 停止调度器
        scheduler.stop()

        # 验证任务被执行
        assert len(executed_jobs) >= 2  # 至少执行2次
        assert all(job == "quick_job" for job in executed_jobs)

    def test_callback_error_handling(self, scheduler):
        """测试回调错误处理"""

        def error_handler(data):
            raise Exception("Test error")

        # 添加会出错的回调
        scheduler.add_tick_callback(error_handler)

        # 触发回调不应该影响其他功能
        scheduler.trigger_tick_data({"test": "data"})

        # 调度器应该仍然正常工作
        assert len(scheduler._tick_callbacks) == 1

    def test_job_error_handling(self, scheduler):
        """测试任务错误处理"""

        def error_task():
            raise Exception("Task error")

        # 添加会出错的任务
        scheduler.add_daily_job("error_job", error_task)

        # 获取任务并尝试执行
        job = scheduler._jobs["error_job"]

        # 任务执行应该抛出异常
        with pytest.raises(Exception, match="Task error"):
            job.run()

    def test_duplicate_callback_prevention(self, scheduler):
        """测试防止重复添加回调"""

        def test_handler(data):
            pass

        # 添加同一个回调两次
        scheduler.add_tick_callback(test_handler)
        scheduler.add_tick_callback(test_handler)

        # 应该只有一个回调
        assert len(scheduler._tick_callbacks) == 1

    def test_concurrent_operations(self, scheduler):
        """测试并发操作"""

        def test_task():
            time.sleep(0.1)  # 短暂延迟
            return "completed"

        # 启动调度器
        scheduler.start()

        # 并发添加任务
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=scheduler.add_daily_job,
                args=(f"concurrent_job_{i}", test_task, "10:00"),
            )
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有任务都被添加
        assert len(scheduler._jobs) == 5

        scheduler.stop()
