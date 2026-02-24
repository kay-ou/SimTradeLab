from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig
from simtradelab.server.core.log_streamer import ThreadSafeQueueHandler
from simtradelab.server.core.task_manager import TaskManager
from simtradelab.utils.paths import get_strategies_path

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
        import os
        os.makedirs(config.log_dir, exist_ok=True)

        # 用统一时间戳生成同一 stem，保证 .log 和 .json 文件名完全一致
        ts = datetime.now().strftime("%y%m%d_%H%M%S")
        stem = "backtest_{}_{}_{}" .format(
            config.start_date.strftime("%y%m%d"),  # type: ignore[union-attr]
            config.end_date.strftime("%y%m%d"),    # type: ignore[union-attr]
            ts,
        )
        self._log_filename = str(Path(config.log_dir) / (stem + ".log"))
        self._json_filename = str(Path(config.log_dir) / (stem + ".json"))

        handlers: list[logging.Handler] = [
            logging.FileHandler(self._log_filename, mode="w", encoding="utf-8"),
        ]
        queue_handler = ThreadSafeQueueHandler(self._log_queue, self._loop, self._log_buffer)
        queue_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        handlers.append(queue_handler)
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(message)s",
            handlers=handlers,
            force=True,
        )


def run_backtest_in_thread(task_id: str, manager: TaskManager, loop: asyncio.AbstractEventLoop) -> dict | None:
    """在 ThreadPoolExecutor 子线程中执行回测。"""
    task = manager.get_task(task_id)
    req = task.request
    assert req is not None
    log_queue = task.log_queue
    assert log_queue is not None

    def _send(msg: dict) -> None:
        task.log_buffer.append(msg)
        loop.call_soon_threadsafe(log_queue.put_nowait, msg)

    manager.mark_running(task_id)
    run_start = time.time()
    _orig_stdout = sys.stdout
    sys.stdout = _QueueWriter(log_queue, loop, task.log_buffer)  # type: ignore[assignment]

    try:
        config = BacktestConfig(
            strategy_name=req.strategy_name,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
            frequency=req.frequency,
            enable_charts=False,   # UI 已生成更漂亮的图表，无需 matplotlib 再生成一遍
            sandbox=req.sandbox,
            enable_logging=True,
        )

        runner = ServerBacktestRunner(log_queue, loop, task.log_buffer)
        runner._cancel_event = task.cancel_event
        report = runner.run(config=config)

        if not report:
            manager.mark_failed(task_id, "回测返回空结果，请检查策略或日期范围")
            _send({**_FAIL_SENTINEL, "ts": time.time()})
            return None

        duration = time.time() - run_start
        _save_history_json(runner, req, task_id, report, run_start, duration)

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


def _save_history_json(runner: ServerBacktestRunner, req: object, task_id: str, report: dict, run_start: float, duration: float) -> None:
    if not hasattr(runner, "_json_filename"):
        return
    stats = report.get("_stats")
    if stats:
        series = {
            "dates": [str(d.date()) if hasattr(d, "date") else str(d) for d in stats.trade_dates],
            "portfolio_values": [float(v) for v in stats.portfolio_values],
            "daily_pnl": [float(v) for v in stats.daily_pnl],
            "daily_buy_amount": [float(v) for v in stats.daily_buy_amount],
            "daily_sell_amount": [float(v) for v in stats.daily_sell_amount],
            "daily_positions_value": [float(v) for v in stats.daily_positions_value],
            "benchmark_nav": [float(v) for v in report.get("_benchmark_nav", [])],
        }
    else:
        series = {}
    metrics = {
        k: v for k, v in report.items()
        if not k.startswith("_") and isinstance(v, (str, float, int, bool))
    }
    strategy_file = get_strategies_path() / req.strategy_name / "backtest.py"  # type: ignore[attr-defined]
    source = strategy_file.read_text(encoding="utf-8") if strategy_file.exists() else ""
    data = {
        "task_id": task_id,
        "strategy": req.strategy_name,       # type: ignore[attr-defined]
        "start_date": req.start_date,          # type: ignore[attr-defined]
        "end_date": req.end_date,              # type: ignore[attr-defined]
        "initial_capital": req.initial_capital,# type: ignore[attr-defined]
        "frequency": req.frequency,            # type: ignore[attr-defined]
        "run_at": run_start,
        "duration": duration,
        "metrics": metrics,
        "benchmark_name": metrics.get("benchmark_name", ""),
        "series": series,
        "log_path": getattr(runner, "_log_filename", None),
        "source": source,
    }
    Path(runner._json_filename).write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )
