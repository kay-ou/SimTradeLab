from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig
from simtradelab.server.core.log_streamer import ThreadSafeQueueHandler
from simtradelab.server.core.task_manager import TaskManager

_DONE_SENTINEL = {"level": "SYSTEM", "msg": "__DONE__", "ts": 0.0}
_FAIL_SENTINEL = {"level": "SYSTEM", "msg": "__FAIL__", "ts": 0.0}


class ServerBacktestRunner(BacktestRunner):
    """BacktestRunner 的服务端子类，注入 QueueHandler 捕获日志。"""

    def __init__(
        self,
        log_queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
        log_buffer: list,
    ) -> None:
        super().__init__()
        self._log_queue = log_queue
        self._loop = loop
        self._log_buffer = log_buffer

    def _setup_logging(self, config: BacktestConfig) -> None:
        # 父类调用 basicConfig(force=True) 清空 root logger handlers
        super()._setup_logging(config)
        # 父类完成后，追加我们的 QueueHandler
        handler = ThreadSafeQueueHandler(self._log_queue, self._loop)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logging.getLogger().addHandler(handler)


def run_backtest_in_thread(task_id: str, manager: TaskManager) -> dict | None:
    """在 ThreadPoolExecutor 子线程中执行回测。"""
    task = manager.get_task(task_id)
    req = task.request
    loop = asyncio.get_event_loop()
    log_queue = task.log_queue
    assert log_queue is not None

    def _send(msg: dict) -> None:
        task.log_buffer.append(msg)
        loop.call_soon_threadsafe(log_queue.put_nowait, msg)

    manager.mark_running(task_id)

    try:
        config = BacktestConfig(
            strategy_name=req.strategy_name,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
            frequency=req.frequency,
            enable_charts=req.enable_charts,
            sandbox=req.sandbox,
            enable_logging=True,
        )

        runner = ServerBacktestRunner(log_queue, loop, task.log_buffer)
        report = runner.run(config=config)

        if not report:
            manager.mark_failed(task_id, "回测返回空结果，请检查策略或日期范围")
            _send({**_FAIL_SENTINEL, "ts": time.time()})
            return None

        manager.mark_finished(task_id, report)
        _send({**_DONE_SENTINEL, "ts": time.time()})
        return report

    except Exception as exc:
        err = str(exc)
        manager.mark_failed(task_id, err)
        _send({"level": "ERROR", "msg": err, "ts": time.time()})
        _send({**_FAIL_SENTINEL, "ts": time.time()})
        return None
