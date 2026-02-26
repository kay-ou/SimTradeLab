from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from simtradelab.utils.paths import get_strategies_path
from simtradelab.server.core.shared import task_manager, executor
from simtradelab.server.core.optimizer_thread import run_optimizer_in_thread

router = APIRouter(prefix="/optimizer", tags=["optimizer"])

_SCRIPT_TEMPLATE = '''\
from simtradelab.backtest.optimizer_framework import (
    ParameterSpace,
    optimize_strategy,
)


class MyParameterSpace(ParameterSpace):
    """参数空间定义

    使用类属性定义候选值，框架自动推导。
    支持 list / tuple / numpy.ndarray。
    """

    # 示例参数（按实际策略修改）
    # ma_short = [5, 10, 15, 20]
    # ma_long = [20, 30, 40, 50, 60]


if __name__ == "__main__":
    # custom_mapping 仅在变量名与参数名不一致时使用
    # 例如 context.max_position 对应参数名 max_position 时：
    # custom_mapping = {{"max_position": "context.max_position"}}

    optimize_strategy(
        parameter_space=MyParameterSpace,
        optimization_period=("2025-01-01", "2025-08-31"),
        holdout_period=("2025-09-01", "2025-12-31"),
        regularization_weight=0.5,
        stability_weight=0.5,
        walk_forward_config={{
            "train_months": 3,
            "test_months": 1,
            "step_months": 1,
        }},
    )
'''


class SaveScriptBody(BaseModel):
    source: str


def _script_file(strategy_name: str):
    return get_strategies_path() / strategy_name / "optimization" / "optimize_params.py"


@router.get("/{strategy_name}/script")
def get_script(strategy_name: str):
    path = _script_file(strategy_name)
    if not path.exists():
        return {"source": _SCRIPT_TEMPLATE, "exists": False}
    return {"source": path.read_text(encoding="utf-8"), "exists": True}


@router.put("/{strategy_name}/script")
def save_script(strategy_name: str, body: SaveScriptBody):
    path = _script_file(strategy_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.source, encoding="utf-8")
    return {"ok": True}


@router.post("/{strategy_name}/run")
async def run_optimizer(strategy_name: str):
    if task_manager.has_running_task():
        raise HTTPException(status_code=409, detail="已有任务正在运行，请等待完成")
    path = _script_file(strategy_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="优化脚本不存在，请先保存")
    loop = asyncio.get_running_loop()
    task_id = task_manager.create_optimizer_task(str(path))
    task = task_manager.get_task(task_id)
    task.loop = loop
    future = executor.submit(run_optimizer_in_thread, task_id, task_manager, loop)
    task.future = future
    return {"task_id": task_id}
