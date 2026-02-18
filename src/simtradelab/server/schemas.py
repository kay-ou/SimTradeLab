from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class RunBacktestRequest(BaseModel):
    strategy_name: str
    start_date: str
    end_date: str
    initial_capital: float = Field(default=100000.0, gt=0)
    frequency: str = Field(default="1d", pattern="^(1d|1m)$")
    enable_charts: bool = True
    sandbox: bool = True


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["pending", "running", "finished", "failed"]
    task_type: Literal["backtest", "optimize"] = "backtest"
    progress: float = 0.0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


class BacktestMetrics(BaseModel):
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    alpha: float
    beta: float
    information_ratio: float
    excess_return: float
    benchmark_return: float
    benchmark_name: str
    win_rate: float
    profit_loss_ratio: float
    win_count: int
    lose_count: int
    trading_days: int
    initial_value: float
    final_value: float


class BacktestSeries(BaseModel):
    dates: list[str]
    portfolio_values: list[float]
    daily_pnl: list[float]
    daily_buy_amount: list[float]
    daily_sell_amount: list[float]
    daily_positions_value: list[float]


class BacktestResult(BaseModel):
    metrics: BacktestMetrics
    series: BacktestSeries
    chart_png_path: Optional[str] = None


class LogMessage(BaseModel):
    level: str
    msg: str
    ts: float


class StrategySource(BaseModel):
    name: str
    source: str


class CreateStrategyRequest(BaseModel):
    name: str
