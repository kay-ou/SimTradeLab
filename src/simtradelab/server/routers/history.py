from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from simtradelab.utils.paths import get_strategies_path

router = APIRouter(prefix="/history", tags=["history"])


def _strategies_base() -> Path:
    return get_strategies_path()


def _validate_under_strategies(path: str) -> Path:
    resolved = Path(path).resolve()
    try:
        resolved.relative_to(_strategies_base())
    except ValueError:
        raise HTTPException(status_code=400, detail="无效路径")
    return resolved


@router.get("")
def list_history():
    base = _strategies_base()
    entries = []
    for json_file in sorted(base.glob("*/stats/backtest_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            log_path = json_file.with_suffix(".log")
            entries.append({
                "task_id": data.get("task_id", json_file.stem),
                "strategy": data.get("strategy", ""),
                "start_date": data.get("start_date", ""),
                "end_date": data.get("end_date", ""),
                "initial_capital": data.get("initial_capital", 0),
                "frequency": data.get("frequency", "1d"),
                "run_at": data.get("run_at", 0),
                "duration": data.get("duration", 0),
                "metrics": data.get("metrics", {}),
                "benchmark_name": data.get("benchmark_name", ""),
                "json_path": str(json_file),
                "log_path": str(log_path) if log_path.exists() else None,
            })
        except Exception:
            continue
    return entries


@router.get("/detail")
def get_detail(json_path: str):
    path = _validate_under_strategies(json_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="记录不存在")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="读取失败")


@router.get("/log", response_class=PlainTextResponse)
def get_log(path: str):
    log_path = _validate_under_strategies(path)
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="日志文件不存在")
    lines = []
    for raw in log_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        if raw.startswith("[") and "]" in raw:
            end = raw.index("]")
            level = raw[1:end].upper()
            msg = raw[end + 2:]
        else:
            level, msg = "INFO", raw
        lines.append(json.dumps({"level": level, "msg": msg, "ts": 0}, ensure_ascii=False))
    return "\n".join(lines)


@router.delete("")
def delete_entry(json_path: str):
    path = _validate_under_strategies(json_path)
    path.unlink(missing_ok=True)
    path.with_suffix(".log").unlink(missing_ok=True)
    return {"ok": True}
