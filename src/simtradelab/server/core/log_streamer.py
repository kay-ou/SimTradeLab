from __future__ import annotations

import asyncio
import logging
import time

backtest_date: str | None = None


class ThreadSafeQueueHandler(logging.Handler):
    def __init__(
        self,
        queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
        log_buffer: list | None = None,
    ) -> None:
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
                "date": backtest_date,
            }
            if self._log_buffer is not None:
                self._log_buffer.append(msg)
            self._loop.call_soon_threadsafe(self._queue.put_nowait, msg)
        except Exception:
            self.handleError(record)
