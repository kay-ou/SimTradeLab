from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException

from simtradelab.utils.paths import get_strategies_path
from simtradelab.server.schemas import StrategySource, CreateStrategyRequest

router = APIRouter(prefix="/strategies", tags=["strategies"])

_STRATEGY_TEMPLATE = '''\
def initialize(context):
    """初始化策略"""
    set_benchmark('000300.SS')
    # 在此定义策略参数


def before_trading_start(context, data):
    pass


def handle_data(context, data):
    """每日交易逻辑"""
    pass


def after_trading_end(context, data):
    pass
'''


def _strategy_file(name: str) -> Path:
    return get_strategies_path() / name / "backtest.py"


@router.get("", response_model=list[str])
def list_strategies():
    base = get_strategies_path()
    if not base.exists():
        return []
    return sorted(
        d.name for d in base.iterdir()
        if d.is_dir() and (d / "backtest.py").exists()
    )


@router.get("/{name}", response_model=StrategySource)
def get_strategy(name: str):
    path = _strategy_file(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="策略 '{}' 不存在".format(name))
    return StrategySource(name=name, source=path.read_text(encoding="utf-8"))


@router.put("/{name}")
def save_strategy(name: str, body: StrategySource):
    path = _strategy_file(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="策略 '{}' 不存在".format(name))
    path.write_text(body.source, encoding="utf-8")
    return {"ok": True}


@router.post("/{name}", status_code=201)
def create_strategy(name: str, _body: CreateStrategyRequest):
    path = _strategy_file(name)
    if path.exists():
        raise HTTPException(status_code=409, detail="策略 '{}' 已存在".format(name))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_STRATEGY_TEMPLATE, encoding="utf-8")
    return {"ok": True, "name": name}


@router.delete("/{name}")
def delete_strategy(name: str):
    folder = get_strategies_path() / name
    if not folder.exists():
        raise HTTPException(status_code=404, detail="策略 '{}' 不存在".format(name))
    shutil.rmtree(folder)
    return {"ok": True}
