# -*- coding: utf-8 -*-
"""
PTrade调度器

负责处理定时任务和回调事件的调度管理
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

from ....core.event_bus import EventBus


class ScheduleJob:
    """调度任务"""

    def __init__(
        self,
        job_id: str,
        func: Callable,
        job_type: str,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        interval: Optional[Union[int, str]] = None,
        run_time: Optional[str] = None,
        enabled: bool = True,
    ):
        self.job_id = job_id
        self.func = func
        self.job_type = job_type  # 'daily', 'interval', 'tick', 'callback'
        self.args = args
        self.kwargs = kwargs or {}
        self.interval = interval
        self.run_time = run_time
        self.enabled = enabled
        self.last_run = None
        self.next_run = None
        self._calculate_next_run()

    def _calculate_next_run(self):
        """计算下次运行时间"""
        now = datetime.now()

        if self.job_type == "daily":
            if self.run_time:
                # 解析时间格式 "HH:MM"
                hour, minute = map(int, self.run_time.split(":"))
                next_run = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                # 如果今天的时间已过，设置为明天
                if next_run <= now:
                    next_run += timedelta(days=1)

                self.next_run = next_run
            else:
                # 默认每天9:30运行
                next_run = now.replace(hour=9, minute=30, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                self.next_run = next_run

        elif self.job_type == "interval":
            if isinstance(self.interval, int):
                # 间隔秒数
                self.next_run = now + timedelta(seconds=self.interval)
            else:
                # 解析字符串格式，如 "5m", "1h", "30s"
                if self.interval is not None:
                    interval_seconds = self._parse_interval_string(self.interval)
                    self.next_run = now + timedelta(seconds=interval_seconds)
                else:
                    # 默认60秒间隔
                    self.next_run = now + timedelta(seconds=60)

        elif self.job_type in ["tick", "callback"]:
            # tick和callback任务不需要预定时间
            self.next_run = None

    def _parse_interval_string(self, interval_str: str) -> int:
        """解析间隔字符串，返回秒数"""
        if not interval_str:
            return 60  # 默认1分钟

        interval_str = interval_str.lower().strip()

        if interval_str.endswith("s"):
            return int(interval_str[:-1])
        elif interval_str.endswith("m"):
            return int(interval_str[:-1]) * 60
        elif interval_str.endswith("h"):
            return int(interval_str[:-1]) * 3600
        else:
            # 假设是秒数
            return int(interval_str)

    def should_run(self) -> bool:
        """检查是否应该运行"""
        if not self.enabled or self.job_type in ["tick", "callback"]:
            return False

        if self.next_run is None:
            return False

        return datetime.now() >= self.next_run

    def run(self):
        """执行任务"""
        try:
            self.last_run = datetime.now()
            result = self.func(*self.args, **self.kwargs)

            # 更新下次运行时间
            if self.job_type == "interval":
                self._calculate_next_run()
            elif self.job_type == "daily" and self.next_run is not None:
                self.next_run += timedelta(days=1)

            return result
        except Exception as e:
            logging.error(f"Error running job {self.job_id}: {e}")
            raise


class PTradeScheduler:
    """PTrade调度器"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._logger = logging.getLogger(self.__class__.__name__)
        self._jobs: Dict[str, ScheduleJob] = {}
        self._running = False
        self._scheduler_thread = None
        self._tick_callbacks: List[Callable] = []
        self._order_response_callbacks: List[Callable] = []
        self._trade_response_callbacks: List[Callable] = []

    def start(self):
        """启动调度器"""
        if self._running:
            return

        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self._scheduler_thread.start()
        self._logger.info("PTrade scheduler started")

    def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        self._logger.info("PTrade scheduler stopped")

    def _scheduler_loop(self):
        """调度循环"""
        while self._running:
            try:
                # 检查并运行到期的任务
                for job in list(self._jobs.values()):
                    if job.should_run():
                        try:
                            job.run()
                            self._logger.debug(f"Executed job: {job.job_id}")
                        except Exception as e:
                            self._logger.error(f"Error executing job {job.job_id}: {e}")

                # 短暂休眠，避免CPU占用过高
                time.sleep(1)

            except Exception as e:
                self._logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)

    def add_daily_job(
        self,
        job_id: str,
        func: Callable,
        time_str: str = "09:30",
        args: tuple = (),
        kwargs: Optional[dict] = None,
    ) -> str:
        """添加每日定时任务"""
        job = ScheduleJob(
            job_id=job_id,
            func=func,
            job_type="daily",
            args=args,
            kwargs=kwargs or {},
            run_time=time_str,
        )

        self._jobs[job_id] = job
        self._logger.info(f"Added daily job: {job_id} at {time_str}")
        return job_id

    def add_interval_job(
        self,
        job_id: str,
        func: Callable,
        interval: Union[int, str],
        args: tuple = (),
        kwargs: Optional[dict] = None,
    ) -> str:
        """添加间隔执行任务"""
        job = ScheduleJob(
            job_id=job_id,
            func=func,
            job_type="interval",
            args=args,
            kwargs=kwargs or {},
            interval=interval,
        )

        self._jobs[job_id] = job
        self._logger.info(f"Added interval job: {job_id} every {interval}")
        return job_id

    def add_tick_callback(self, callback: Callable):
        """添加tick数据回调"""
        if callback not in self._tick_callbacks:
            self._tick_callbacks.append(callback)
            self._logger.info(f"Added tick callback: {callback.__name__}")

    def add_order_response_callback(self, callback: Callable):
        """添加委托回报回调"""
        if callback not in self._order_response_callbacks:
            self._order_response_callbacks.append(callback)
            self._logger.info(f"Added order response callback: {callback.__name__}")

    def add_trade_response_callback(self, callback: Callable):
        """添加成交回报回调"""
        if callback not in self._trade_response_callbacks:
            self._trade_response_callbacks.append(callback)
            self._logger.info(f"Added trade response callback: {callback.__name__}")

    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._logger.info(f"Removed job: {job_id}")
            return True
        return False

    def remove_tick_callback(self, callback: Callable) -> bool:
        """移除tick回调"""
        if callback in self._tick_callbacks:
            self._tick_callbacks.remove(callback)
            self._logger.info(f"Removed tick callback: {callback.__name__}")
            return True
        return False

    def remove_order_response_callback(self, callback: Callable) -> bool:
        """移除委托回报回调"""
        if callback in self._order_response_callbacks:
            self._order_response_callbacks.remove(callback)
            self._logger.info(f"Removed order response callback: {callback.__name__}")
            return True
        return False

    def remove_trade_response_callback(self, callback: Callable) -> bool:
        """移除成交回报回调"""
        if callback in self._trade_response_callbacks:
            self._trade_response_callbacks.remove(callback)
            self._logger.info(f"Removed trade response callback: {callback.__name__}")
            return True
        return False

    def trigger_tick_data(self, tick_data: Dict[str, Any]):
        """触发tick数据回调"""
        for callback in self._tick_callbacks:
            try:
                callback(tick_data)
            except Exception as e:
                self._logger.error(f"Error in tick callback {callback.__name__}: {e}")

    def trigger_order_response(self, order_response: Dict[str, Any]):
        """触发委托回报回调"""
        for callback in self._order_response_callbacks:
            try:
                callback(order_response)
            except Exception as e:
                self._logger.error(
                    f"Error in order response callback {callback.__name__}: {e}"
                )

    def trigger_trade_response(self, trade_response: Dict[str, Any]):
        """触发成交回报回调"""
        for callback in self._trade_response_callbacks:
            try:
                callback(trade_response)
            except Exception as e:
                self._logger.error(
                    f"Error in trade response callback {callback.__name__}: {e}"
                )

    def get_jobs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        return {
            job_id: {
                "type": job.job_type,
                "enabled": job.enabled,
                "last_run": job.last_run,
                "next_run": job.next_run,
                "interval": job.interval,
                "run_time": job.run_time,
            }
            for job_id, job in self._jobs.items()
        }
