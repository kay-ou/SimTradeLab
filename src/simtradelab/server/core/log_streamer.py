from __future__ import annotations

import asyncio
import logging
import time


class ThreadSafeQueueHandler(logging.Handler):
    """将日志记录通过 call_soon_threadsafe 安全推入 asyncio.Queue。

    BacktestRunner 在子线程运行，WebSocket handler 在主事件循环。
    此 Handler 桥接两者，确保线程安全。
    """

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, log_buffer: list | None = None) -> None:
        super().__init__()
        self._queue = queue
        self._loop = loop
        self._log_buffer = log_buffer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = {
                "level": record.levelname,
                "msg": self.format(record),
                "ts": time.time(),
            }
            if self._log_buffer is not None:
                self._log_buffer.append(msg)
            self._loop.call_soon_threadsafe(self._queue.put_nowait, msg)
        except Exception:
            self.handleError(record)
