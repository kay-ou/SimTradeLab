from __future__ import annotations

import asyncio
import runpy
import time

from simtradelab.server.core.task_manager import TaskManager
from simtradelab.server.core.runner_thread import _QueueWriter

_DONE_SENTINEL = {"level": "SYSTEM", "msg": "__DONE__", "ts": 0.0}
_FAIL_SENTINEL = {"level": "SYSTEM", "msg": "__FAIL__", "ts": 0.0}


def run_optimizer_in_thread(
    task_id: str,
    manager: TaskManager,
    loop: asyncio.AbstractEventLoop,
) -> None:
    import sys

    task = manager.get_task(task_id)
    log_queue = task.log_queue
    assert log_queue is not None
    script_path = task.script_path
    assert script_path is not None

    def _send(msg: dict) -> None:
        task.log_buffer.append(msg)
        loop.call_soon_threadsafe(log_queue.put_nowait, msg)

    manager.mark_running(task_id)
    _orig_stdout = sys.stdout
    sys.stdout = _QueueWriter(log_queue, loop, task.log_buffer)  # type: ignore[assignment]

    try:
        runpy.run_path(script_path, run_name="__main__")
        manager.mark_finished(task_id, {})
        _send({**_DONE_SENTINEL, "ts": time.time()})
    except SystemExit:
        manager.mark_finished(task_id, {})
        _send({**_DONE_SENTINEL, "ts": time.time()})
    except Exception as exc:
        err = str(exc)
        manager.mark_failed(task_id, err)
        _send({"level": "ERROR", "msg": err, "ts": time.time()})
        _send({**_FAIL_SENTINEL, "ts": time.time()})
    finally:
        sys.stdout = _orig_stdout
