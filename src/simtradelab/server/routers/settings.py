from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter

from simtradelab.server.schemas import PathSettings
from simtradelab.utils.paths import get_data_path, get_strategies_path

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=PathSettings)
def get_settings():
    return PathSettings(
        data_path=str(get_data_path()),
        strategies_path=str(get_strategies_path()),
    )


@router.put("", response_model=PathSettings)
def update_settings(body: PathSettings):
    os.environ['SIMTRADELAB_DATA_PATH'] = str(Path(body.data_path).resolve())
    os.environ['SIMTRADELAB_STRATEGIES_PATH'] = str(Path(body.strategies_path).resolve())
    return PathSettings(
        data_path=str(get_data_path()),
        strategies_path=str(get_strategies_path()),
    )
