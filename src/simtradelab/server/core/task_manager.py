from __future__ import annotations

import asyncio
import secrets
import threading
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional

from simtradelab.server.schemas import RunBacktestRequest


@dataclass
class TaskState:
    task_id: str
    task_type: Literal["backtest", "optimize"]
    status: Literal["pending", "running", "finished", "failed"]
    request: RunBacktestRequest
    progress: float = 0.0
    result: Optional[dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    log_buffer: list[dict] = field(default_factory=list)
    log_queue: Optional[asyncio.Queue] = field(default=None, compare=False)
    future: Optional[Future] = field(default=None, compare=False)
    loop: Optional[asyncio.AbstractEventLoop] = field(default=None, compare=False)
    cancel_event: threading.Event = field(default_factory=threading.Event)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskState] = {}

    def create_task(self, request: RunBacktestRequest) -> str:
        task_id = secrets.token_hex(4)
        self._tasks[task_id] = TaskState(
            task_id=task_id,
            task_type="backtest",
            status="pending",
            request=request,
            log_queue=asyncio.Queue(),
        )
        return task_id

    def get_task(self, task_id: str) -> TaskState:
        if task_id not in self._tasks:
            raise KeyError(task_id)
        return self._tasks[task_id]

    def mark_running(self, task_id: str) -> None:
        task = self.get_task(task_id)
        task.status = "running"
        task.started_at = _now_iso()
        task.progress = 0.0

    def mark_finished(self, task_id: str, result: dict) -> None:
        task = self.get_task(task_id)
        task.status = "finished"
        task.result = result
        task.progress = 1.0
        task.finished_at = _now_iso()

    def mark_failed(self, task_id: str, error: str) -> None:
        task = self.get_task(task_id)
        task.status = "failed"
        task.error = error
        task.finished_at = _now_iso()

    def has_running_task(self) -> bool:
        return any(t.status == "running" for t in self._tasks.values())
