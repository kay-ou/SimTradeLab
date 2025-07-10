# -*- coding: utf-8 -*-
"""
PTrade调度器测试

测试定时任务和回调管理功能
"""

import threading
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from simtradelab.adapters.ptrade.scheduling.scheduler import (
    PTradeScheduler,
    ScheduleJob,
)
from simtradelab.core.event_bus import EventBus


class TestScheduleJob:
    """测试调度任务类"""

    def test_job_initialization(self):
        """测试任务初始化"""

        def test_func():
            return "test"

        job = ScheduleJob(
            job_id="test_job", func=test_func, job_type="daily", run_time="09:30"
        )

        assert job.job_id == "test_job"
        assert job.func == test_func
        assert job.job_type == "daily"
        assert job.run_time == "09:30"
        assert job.enabled is True
        assert job.next_run is not None

    def test_daily_job_time_calculation(self):
        """测试每日任务时间计算"""

        def test_func():
            return "test"

        job = ScheduleJob(
            job_id="daily_test", func=test_func, job_type="daily", run_time="09:30"
        )

        # 检查下次运行时间是否正确设置
        assert job.next_run is not None
        assert job.next_run.hour == 9
        assert job.next_run.minute == 30

    def test_interval_job_calculation(self):
        """测试间隔任务时间计算"""

        def test_func():
            return "test"

        # 测试秒数间隔
        job = ScheduleJob(
            job_id="interval_test", func=test_func, job_type="interval", interval=60
        )

        now = datetime.now()
        assert job.next_run is not None
        time_diff = (job.next_run - now).total_seconds()
        assert 59 <= time_diff <= 61  # 允许1秒误差

    def test_interval_string_parsing(self):
        """测试间隔字符串解析"""

        def test_func():
            return "test"

        # 测试字符串间隔
        job = ScheduleJob(
            job_id="interval_string_test",
            func=test_func,
            job_type="interval",
            interval="5m",
        )

        now = datetime.now()
        assert job.next_run is not None
        time_diff = (job.next_run - now).total_seconds()
        assert 299 <= time_diff <= 301  # 5分钟 = 300秒

    def test_should_run_logic(self):
        """测试是否应该运行的逻辑"""

        def test_func():
            return "test"

        # 创建一个过去时间的任务
        job = ScheduleJob(
            job_id="past_test",
            func=test_func,
            job_type="daily",
            run_time="00:01",  # 昨天的时间
        )

        # 手动设置为过去时间
        job.next_run = datetime.now() - timedelta(hours=1)
        assert job.should_run() is True

        # 设置为未来时间
        job.next_run = datetime.now() + timedelta(hours=1)
        assert job.should_run() is False

        # 禁用的任务不应该运行
        job.enabled = False
        job.next_run = datetime.now() - timedelta(hours=1)
        assert job.should_run() is False

    def test_job_execution(self):
        """测试任务执行"""
        executed = False

        def test_func():
            nonlocal executed
            executed = True
            return "executed"

        job = ScheduleJob(job_id="execution_test", func=test_func, job_type="daily")

        result = job.run()
        assert executed is True
        assert result == "executed"
        assert job.last_run is not None

    def test_job_execution_with_args(self):
        """测试带参数的任务执行"""
        result_value = None

        def test_func(value, multiplier=1):
            nonlocal result_value
            result_value = value * multiplier
            return result_value

        job = ScheduleJob(
            job_id="args_test",
            func=test_func,
            job_type="daily",
            args=(5,),
            kwargs={"multiplier": 3},
        )

        job.run()
        assert result_value == 15


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

    def test_add_daily_job(self, scheduler):
        """测试添加每日任务"""

        def test_task():
            return "daily_executed"

        job_id = scheduler.add_daily_job(
            job_id="test_daily", func=test_task, time_str="10:00"
        )

        assert job_id == "test_daily"
        assert "test_daily" in scheduler._jobs
        assert scheduler._jobs["test_daily"].job_type == "daily"
        assert scheduler._jobs["test_daily"].run_time == "10:00"

    def test_add_interval_job(self, scheduler):
        """测试添加间隔任务"""

        def test_task():
            return "interval_executed"

        job_id = scheduler.add_interval_job(
            job_id="test_interval", func=test_task, interval=30
        )

        assert job_id == "test_interval"
        assert "test_interval" in scheduler._jobs
        assert scheduler._jobs["test_interval"].job_type == "interval"
        assert scheduler._jobs["test_interval"].interval == 30

    def test_add_tick_callback(self, scheduler):
        """测试添加tick回调"""

        def tick_handler(tick_data):
            pass

        scheduler.add_tick_callback(tick_handler)
        assert len(scheduler._tick_callbacks) == 1
        assert tick_handler in scheduler._tick_callbacks

    def test_add_order_response_callback(self, scheduler):
        """测试添加订单回报回调"""

        def order_handler(order_data):
            pass

        scheduler.add_order_response_callback(order_handler)
        assert len(scheduler._order_response_callbacks) == 1
        assert order_handler in scheduler._order_response_callbacks

    def test_add_trade_response_callback(self, scheduler):
        """测试添加成交回报回调"""

        def trade_handler(trade_data):
            pass

        scheduler.add_trade_response_callback(trade_handler)
        assert len(scheduler._trade_response_callbacks) == 1
        assert trade_handler in scheduler._trade_response_callbacks

    def test_remove_job(self, scheduler):
        """测试移除任务"""

        def test_task():
            return "test"

        # 添加任务
        job_id = scheduler.add_daily_job("removable_job", test_task)
        assert "removable_job" in scheduler._jobs

        # 移除任务
        result = scheduler.remove_job("removable_job")
        assert result is True
        assert "removable_job" not in scheduler._jobs

        # 移除不存在的任务
        result = scheduler.remove_job("nonexistent_job")
        assert result is False

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
