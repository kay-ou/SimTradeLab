from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from simtradelab.server.core.task_manager import TaskManager
from simtradelab.server.core.runner_thread import run_backtest_in_thread
from simtradelab.server.schemas import RunBacktestRequest, TaskStatus

router = APIRouter(prefix="/backtest", tags=["backtest"])
task_manager = TaskManager()
_executor = ThreadPoolExecutor(max_workers=1)


@router.post("/run")
async def run_backtest(req: RunBacktestRequest):
    if task_manager.has_running_task():
        raise HTTPException(status_code=409, detail="已有回测正在运行，请等待完成")
    loop = asyncio.get_running_loop()
    task_id = task_manager.create_task(req)
    task = task_manager.get_task(task_id)
    task.loop = loop
    future = _executor.submit(run_backtest_in_thread, task_id, task_manager, loop)
    task.future = future
    return {"task_id": task_id}


@router.get("/{task_id}/status", response_model=TaskStatus)
def get_status(task_id: str):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskStatus(
        task_id=task.task_id,
        status=task.status,
        task_type=task.task_type,
        progress=task.progress,
        started_at=task.started_at,
        finished_at=task.finished_at,
        error=task.error,
    )


@router.get("/{task_id}/result")
def get_result(task_id: str):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "finished":
        raise HTTPException(status_code=425, detail="任务尚未完成，当前状态: {}".format(task.status))
    report = task.result
    assert report is not None
    stats = report.get("_stats")
    if stats:
        series_data = {
            "dates": [str(d.date()) if hasattr(d, "date") else str(d) for d in stats.trade_dates],
            "portfolio_values": [float(v) for v in stats.portfolio_values],
            "daily_pnl": [float(v) for v in stats.daily_pnl],
            "daily_buy_amount": [float(v) for v in stats.daily_buy_amount],
            "daily_sell_amount": [float(v) for v in stats.daily_sell_amount],
            "daily_positions_value": [float(v) for v in stats.daily_positions_value],
            "benchmark_nav": [float(v) for v in report.get("_benchmark_nav", [])],
        }
    else:
        series_data = {k: [] for k in ["dates", "portfolio_values", "daily_pnl",
                                        "daily_buy_amount", "daily_sell_amount", "daily_positions_value"]}
    metrics = {
        k: v for k, v in report.items()
        if not k.startswith("_") and isinstance(v, (str, float, int, bool))
    }
    return {
        "metrics": metrics,
        "series": series_data,
        "chart_png_path": report.get("_chart_path"),
    }


@router.post("/{task_id}/cancel")
def cancel_task(task_id: str):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status in ("finished", "failed"):
        return {"ok": True, "skipped": True}
    if task.future:
        task.future.cancel()
    task_manager.mark_failed(task_id, "用户取消")
    return {"ok": True}


@router.websocket("/{task_id}/logs")
async def stream_logs(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        await websocket.send_json({"level": "ERROR", "msg": "任务不存在", "ts": 0})
        await websocket.close()
        return
    for msg in task.log_buffer:
        await websocket.send_json(msg)
    if task.status in ("finished", "failed"):
        await websocket.close()
        return
    log_queue = task.log_queue
    assert log_queue is not None
    try:
        while True:
            msg = await asyncio.wait_for(log_queue.get(), timeout=30.0)
            await websocket.send_json(msg)
            if msg.get("msg") in ("__DONE__", "__FAIL__"):
                break
    except asyncio.TimeoutError:
        pass
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
