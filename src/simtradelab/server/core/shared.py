from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from simtradelab.server.core.task_manager import TaskManager

task_manager = TaskManager()
executor = ThreadPoolExecutor(max_workers=1)
