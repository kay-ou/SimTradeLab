from __future__ import annotations

import asyncio
import logging
import sys
import time

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig
from simtradelab.server.core.log_streamer import ThreadSafeQueueHandler
from simtradelab.server.core.task_manager import TaskManager

_DONE_SENTINEL = {"level": "SYSTEM", "msg": "__DONE__", "ts": 0.0}
_FAIL_SENTINEL = {"level": "SYSTEM", "msg": "__FAIL__", "ts": 0.0}


class _QueueWriter:
    """将 sys.stdout 写入转发到 asyncio.Queue，同时写入 log_buffer 供 replay。"""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, log_buffer: list) -> None:
        self._queue = queue
        self._loop = loop
        self._log_buffer = log_buffer
        self._buf = ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.rstrip()
            if line:
                msg = {"level": "INFO", "msg": line, "ts": time.time()}
                self._log_buffer.append(msg)
                self._loop.call_soon_threadsafe(self._queue.put_nowait, msg)
        return len(text)

    def flush(self) -> None:
        if self._buf.strip():
            msg = {"level": "INFO", "msg": self._buf.strip(), "ts": time.time()}
            self._log_buffer.append(msg)
            self._loop.call_soon_threadsafe(self._queue.put_nowait, msg)
            self._buf = ""

    @property
    def encoding(self) -> str:
        return "utf-8"


class ServerBacktestRunner(BacktestRunner):
    """BacktestRunner 的服务端子类，注入 QueueHandler 捕获日志和 print 输出。"""

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
        # 完全覆盖父类实现：不加 StreamHandler(stdout)，避免与 _QueueWriter 重复
        # logging 消息只走 ThreadSafeQueueHandler；print 消息走 _QueueWriter(stdout)
        import os
        os.makedirs(config.log_dir, exist_ok=True)
        handlers: list[logging.Handler] = []
        if config.enable_logging:
            self._log_filename = config.get_log_filename()
            handlers.append(logging.FileHandler(self._log_filename, mode='w', encoding='utf-8'))
        if config.enable_charts:
            self._chart_filename = config.get_chart_filename()
        queue_handler = ThreadSafeQueueHandler(self._log_queue, self._loop, self._log_buffer)
        queue_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        handlers.append(queue_handler)
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(message)s',
            handlers=handlers,
            force=True,
        )


def run_backtest_in_thread(task_id: str, manager: TaskManager, loop: asyncio.AbstractEventLoop) -> dict | None:
    """在 ThreadPoolExecutor 子线程中执行回测。"""
    task = manager.get_task(task_id)
    req = task.request
    log_queue = task.log_queue
    assert log_queue is not None

    def _send(msg: dict) -> None:
        task.log_buffer.append(msg)
        loop.call_soon_threadsafe(log_queue.put_nowait, msg)

    manager.mark_running(task_id)
    _orig_stdout = sys.stdout
    sys.stdout = _QueueWriter(log_queue, loop, task.log_buffer)  # type: ignore[assignment]

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

    finally:
        sys.stdout = _orig_stdout
