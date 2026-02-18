# Desktop App Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建 SimTradeLab 桌面应用：FastAPI 服务层（打包进 PyPI `[server]` extra）+ Electron + React UI，实现策略编辑、回测运行、实时日志、结果可视化。

**Architecture:** Electron 主进程 spawn FastAPI 子进程；HTTP REST 管理策略和任务；WebSocket 流式推送日志。FastAPI 通过 `ServerBacktestRunner`（继承 `BacktestRunner`）注入 `QueueHandler` 捕获日志，`asyncio.Queue` + `loop.call_soon_threadsafe` 跨线程推送到 WebSocket 客户端。MVP 阶段一次只允许一个回测运行（避免全局 logging 冲突）。

**Tech Stack:** Python: FastAPI 0.115+, uvicorn, pydantic v2（已有）；UI: Electron 33+, React 18, TypeScript, Vite（electron-vite），Ant Design 5, Monaco Editor, ECharts；打包: PyInstaller, electron-builder

---

## Phase 1: FastAPI Server

---

### Task 1: 添加 server 依赖 + 测试工具

**Files:**
- Modify: `pyproject.toml`

**Step 1: 添加依赖**

在 `pyproject.toml` 中增加以下内容：

```toml
[tool.poetry.dependencies]
# 在已有依赖后追加：
fastapi   = {version = "^0.115.0", optional = true}
uvicorn   = {version = "^0.34.0",  optional = true, extras = ["standard"]}

[tool.poetry.extras]
# 更新 extras（保留现有，新增 server）：
indicators = ["ta-lib"]
optimizer  = ["optuna"]
server     = ["fastapi", "uvicorn"]
all        = ["ta-lib", "optuna", "fastapi", "uvicorn"]

[tool.poetry.scripts]
simtradelab = "simtradelab.cli.serve:main"

[tool.poetry.group.dev.dependencies]
# 在已有 dev 依赖后追加：
pytest          = "^8.0.0"
pytest-asyncio  = "^0.24.0"
httpx           = "^0.27.0"
```

**Step 2: 安装依赖**

```bash
poetry add --optional fastapi uvicorn[standard]
poetry add --group dev pytest pytest-asyncio httpx
```

**Step 3: 验证安装**

```bash
poetry run python -c "import fastapi; print(fastapi.__version__)"
```

Expected: `0.115.x`

**Step 4: Commit**

```bash
git add pyproject.toml poetry.lock
git commit -m "chore: add server extras and test dependencies"
```

---

### Task 2: 创建 schemas.py（Pydantic 请求/响应模型）

**Files:**
- Create: `src/simtradelab/server/__init__.py`
- Create: `src/simtradelab/server/schemas.py`

**Step 1: 创建 `__init__.py`（空文件）**

```python
# src/simtradelab/server/__init__.py
```

**Step 2: 创建 schemas.py**

```python
# src/simtradelab/server/schemas.py
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
```

**Step 3: 验证 schema 可导入**

```bash
poetry run python -c "from simtradelab.server.schemas import RunBacktestRequest; print('OK')"
```

Expected: `OK`

**Step 4: Commit**

```bash
git add src/simtradelab/server/
git commit -m "feat(server): add Pydantic schemas"
```

---

### Task 3: 创建 task_manager.py

**Files:**
- Create: `src/simtradelab/server/core/__init__.py`
- Create: `src/simtradelab/server/core/task_manager.py`
- Create: `tests/server/test_task_manager.py`

**Step 1: 写失败的测试**

```python
# tests/server/test_task_manager.py
import asyncio
import pytest
from simtradelab.server.core.task_manager import TaskManager
from simtradelab.server.schemas import RunBacktestRequest


@pytest.fixture
def manager():
    return TaskManager()


@pytest.fixture
def sample_request():
    return RunBacktestRequest(
        strategy_name="simple",
        start_date="2024-01-01",
        end_date="2024-12-31",
    )


def test_create_task_returns_id(manager, sample_request):
    task_id = manager.create_task(sample_request)
    assert isinstance(task_id, str)
    assert len(task_id) == 8


def test_new_task_status_is_pending(manager, sample_request):
    task_id = manager.create_task(sample_request)
    task = manager.get_task(task_id)
    assert task.status == "pending"
    assert task.progress == 0.0
    assert task.result is None
    assert task.error is None


def test_get_nonexistent_task_raises(manager):
    with pytest.raises(KeyError):
        manager.get_task("nonexistent")


def test_mark_running(manager, sample_request):
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    task = manager.get_task(task_id)
    assert task.status == "running"
    assert task.started_at is not None


def test_mark_finished(manager, sample_request):
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    manager.mark_finished(task_id, result={"total_return": 0.1})
    task = manager.get_task(task_id)
    assert task.status == "finished"
    assert task.result == {"total_return": 0.1}
    assert task.finished_at is not None


def test_mark_failed(manager, sample_request):
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    manager.mark_failed(task_id, error="策略加载失败")
    task = manager.get_task(task_id)
    assert task.status == "failed"
    assert task.error == "策略加载失败"


def test_has_running_task(manager, sample_request):
    assert not manager.has_running_task()
    task_id = manager.create_task(sample_request)
    manager.mark_running(task_id)
    assert manager.has_running_task()
```

**Step 2: 运行测试确认失败**

```bash
poetry run pytest tests/server/test_task_manager.py -v
```

Expected: `ModuleNotFoundError` 或 `ImportError`

**Step 3: 创建 core/__init__.py 和 task_manager.py**

```python
# src/simtradelab/server/core/__init__.py
```

```python
# src/simtradelab/server/core/task_manager.py
from __future__ import annotations

import asyncio
import secrets
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional

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
    # 日志缓冲（新 WS 连接时回放历史日志）
    log_buffer: list[dict] = field(default_factory=list)
    # asyncio Queue，供 WS handler 消费
    log_queue: Optional[asyncio.Queue] = field(default=None, compare=False)
    # ThreadPoolExecutor Future，用于 cancel
    future: Optional[Future] = field(default=None, compare=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskManager:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskState] = {}

    def create_task(self, request: RunBacktestRequest) -> str:
        task_id = secrets.token_hex(4)  # 8 chars
        loop = self._get_or_create_loop()
        self._tasks[task_id] = TaskState(
            task_id=task_id,
            task_type="backtest",
            status="pending",
            request=request,
            log_queue=asyncio.Queue() if loop else None,
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

    def _get_or_create_loop(self):
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            return None
```

**Step 4: 创建 tests/__init__.py 和 tests/server/__init__.py**

```bash
mkdir -p tests/server
touch tests/__init__.py tests/server/__init__.py
```

**Step 5: 运行测试确认通过**

```bash
poetry run pytest tests/server/test_task_manager.py -v
```

Expected: 所有测试 PASS

**Step 6: Commit**

```bash
git add src/simtradelab/server/core/ tests/
git commit -m "feat(server): add TaskManager with state lifecycle"
```

---

### Task 4: 创建 log_streamer.py

**Files:**
- Create: `src/simtradelab/server/core/log_streamer.py`
- Create: `tests/server/test_log_streamer.py`

**Step 1: 写失败的测试**

```python
# tests/server/test_log_streamer.py
import asyncio
import logging
import pytest
from simtradelab.server.core.log_streamer import ThreadSafeQueueHandler


@pytest.mark.asyncio
async def test_handler_puts_message_in_queue():
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    handler = ThreadSafeQueueHandler(queue, loop)

    logger = logging.getLogger("test_streamer")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    logger.info("hello from thread")

    await asyncio.sleep(0.05)
    assert not queue.empty()
    msg = await queue.get()
    assert msg["level"] == "INFO"
    assert msg["msg"] == "hello from thread"
    assert "ts" in msg
```

**Step 2: 运行测试确认失败**

```bash
poetry run pytest tests/server/test_log_streamer.py -v
```

Expected: `ImportError`

**Step 3: 实现 log_streamer.py**

```python
# src/simtradelab/server/core/log_streamer.py
from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class ThreadSafeQueueHandler(logging.Handler):
    """将日志记录通过 call_soon_threadsafe 安全推入 asyncio.Queue。

    BacktestRunner 在子线程运行，WebSocket handler 在主事件循环。
    此 Handler 桥接两者，确保线程安全。
    """

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()
        self._queue = queue
        self._loop = loop

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = {
                "level": record.levelname,
                "msg": self.format(record),
                "ts": time.time(),
            }
            self._loop.call_soon_threadsafe(self._queue.put_nowait, msg)
        except Exception:
            self.handleError(record)
```

**Step 4: 在 pytest.ini 或 pyproject.toml 配置 asyncio mode**

在 `pyproject.toml` 末尾追加：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**Step 5: 运行测试确认通过**

```bash
poetry run pytest tests/server/test_log_streamer.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add src/simtradelab/server/core/log_streamer.py tests/server/test_log_streamer.py pyproject.toml
git commit -m "feat(server): add thread-safe log queue handler"
```

---

### Task 5: 创建 runner_thread.py（在线程中运行回测）

**Files:**
- Create: `src/simtradelab/server/core/runner_thread.py`

**注意：** 此模块继承 `BacktestRunner`，无需写单元测试（集成测试在 Task 11 覆盖）。

**Step 1: 创建 runner_thread.py**

```python
# src/simtradelab/server/core/runner_thread.py
from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from simtradelab.backtest.runner import BacktestRunner
from simtradelab.backtest.config import BacktestConfig
from simtradelab.server.core.log_streamer import ThreadSafeQueueHandler
from simtradelab.server.core.task_manager import TaskManager

if TYPE_CHECKING:
    pass

_DONE_SENTINEL = {"level": "SYSTEM", "msg": "__DONE__", "ts": 0.0}
_FAIL_SENTINEL = {"level": "SYSTEM", "msg": "__FAIL__", "ts": 0.0}


class ServerBacktestRunner(BacktestRunner):
    """BacktestRunner 的服务端子类，注入 QueueHandler 捕获日志。"""

    def __init__(
        self,
        log_queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
        log_buffer: list[dict],
    ) -> None:
        super().__init__()
        self._log_queue = log_queue
        self._loop = loop
        self._log_buffer = log_buffer
        self._queue_handler: ThreadSafeQueueHandler | None = None

    def _setup_logging(self, config: BacktestConfig) -> None:
        # 调用父类设置（会 basicConfig(force=True) 清空 root logger handlers）
        super()._setup_logging(config)
        # 父类设置完毕后，追加我们的 QueueHandler 到 root logger
        handler = ThreadSafeQueueHandler(self._log_queue, self._loop)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logging.getLogger().addHandler(handler)
        self._queue_handler = handler


def _buffering_queue_wrapper(
    source_queue: asyncio.Queue,
    log_buffer: list[dict],
    loop: asyncio.AbstractEventLoop,
) -> asyncio.Queue:
    """创建一个代理 Queue，写入时同时追加到 log_buffer。"""
    proxy = asyncio.Queue()

    async def _pump():
        while True:
            msg = await source_queue.get()
            log_buffer.append(msg)
            await proxy.put(msg)
            if msg.get("msg") in ("__DONE__", "__FAIL__"):
                break

    asyncio.run_coroutine_threadsafe(_pump(), loop)
    return proxy


def run_backtest_in_thread(task_id: str, manager: TaskManager) -> dict | None:
    """在 ThreadPoolExecutor 子线程中执行回测。

    此函数由 executor.submit() 调用，运行在非 asyncio 线程。
    """
    task = manager.get_task(task_id)
    req = task.request
    loop = asyncio.get_event_loop()

    # 确保 log_queue 存在（task 创建时已初始化）
    log_queue = task.log_queue
    assert log_queue is not None

    def _send(msg: dict) -> None:
        task.log_buffer.append(msg)
        loop.call_soon_threadsafe(log_queue.put_nowait, msg)

    manager.mark_running(task_id)

    try:
        config = BacktestConfig(
            strategy_name=req.strategy_name,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
            frequency=req.frequency,
            enable_charts=req.enable_charts,
            sandbox=req.sandbox,
            enable_logging=True,
        )

        runner = ServerBacktestRunner(log_queue, loop, task.log_buffer)
        report = runner.run(config=config)

        if not report:
            manager.mark_failed(task_id, "回测返回空结果，请检查策略或日期范围")
            _send({**_FAIL_SENTINEL, "ts": time.time()})
            return None

        manager.mark_finished(task_id, report)
        _send({**_DONE_SENTINEL, "ts": time.time()})
        return report

    except Exception as exc:
        err = str(exc)
        manager.mark_failed(task_id, err)
        _send({"level": "ERROR", "msg": err, "ts": time.time()})
        _send({**_FAIL_SENTINEL, "ts": time.time()})
        return None
```

**Step 2: 验证导入**

```bash
poetry run python -c "from simtradelab.server.core.runner_thread import run_backtest_in_thread; print('OK')"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add src/simtradelab/server/core/runner_thread.py
git commit -m "feat(server): add ServerBacktestRunner with log capture"
```

---

### Task 6: 创建 strategies 路由

**Files:**
- Create: `src/simtradelab/server/routers/__init__.py`
- Create: `src/simtradelab/server/routers/strategies.py`
- Create: `tests/server/test_strategies_router.py`

**Step 1: 写失败的测试**

```python
# tests/server/test_strategies_router.py
import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def strategies_dir(tmp_path):
    # 创建测试策略目录
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "backtest.py").write_text("def initialize(context): pass\n")
    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "backtest.py").write_text("def initialize(context): pass\n")
    return tmp_path


@pytest.fixture
def app(strategies_dir, monkeypatch):
    import simtradelab.server.routers.strategies as mod
    monkeypatch.setattr(mod, "STRATEGIES_PATH", strategies_dir)
    from simtradelab.server.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_list_strategies(app, strategies_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/strategies")
    assert resp.status_code == 200
    names = resp.json()
    assert "alpha" in names
    assert "beta" in names


@pytest.mark.asyncio
async def test_get_strategy_source(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/strategies/alpha")
    assert resp.status_code == 200
    assert "initialize" in resp.json()["source"]


@pytest.mark.asyncio
async def test_get_nonexistent_strategy_returns_404(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/strategies/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_save_strategy_source(app):
    new_source = "def initialize(context): context.x = 1\n"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.put("/strategies/alpha", json={"name": "alpha", "source": new_source})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_strategy(app, strategies_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/strategies/new_strat", json={"name": "new_strat"})
    assert resp.status_code == 201
    assert (strategies_dir / "new_strat" / "backtest.py").exists()


@pytest.mark.asyncio
async def test_delete_strategy(app, strategies_dir):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.delete("/strategies/beta")
    assert resp.status_code == 200
    assert not (strategies_dir / "beta").exists()
```

**Step 2: 创建 routers/__init__.py**

```python
# src/simtradelab/server/routers/__init__.py
```

**Step 3: 创建 strategies.py**

```python
# src/simtradelab/server/routers/strategies.py
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from simtradelab.utils.paths import STRATEGIES_PATH
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
    return Path(str(STRATEGIES_PATH)) / name / "backtest.py"


@router.get("", response_model=list[str])
def list_strategies():
    base = Path(str(STRATEGIES_PATH))
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
        raise HTTPException(status_code=404, detail=f"策略 '{name}' 不存在")
    return StrategySource(name=name, source=path.read_text(encoding="utf-8"))


@router.put("/{name}")
def save_strategy(name: str, body: StrategySource):
    path = _strategy_file(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"策略 '{name}' 不存在")
    path.write_text(body.source, encoding="utf-8")
    return {"ok": True}


@router.post("/{name}", status_code=201)
def create_strategy(name: str, _body: CreateStrategyRequest):
    path = _strategy_file(name)
    if path.exists():
        raise HTTPException(status_code=409, detail=f"策略 '{name}' 已存在")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_STRATEGY_TEMPLATE, encoding="utf-8")
    return {"ok": True, "name": name}


@router.delete("/{name}")
def delete_strategy(name: str):
    folder = Path(str(STRATEGIES_PATH)) / name
    if not folder.exists():
        raise HTTPException(status_code=404, detail=f"策略 '{name}' 不存在")
    shutil.rmtree(folder)
    return {"ok": True}
```

**Step 4: 创建占位 main.py（供测试导入）**

```python
# src/simtradelab/server/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simtradelab.server.routers import strategies


def create_app() -> FastAPI:
    app = FastAPI(title="SimTradeLab Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(strategies.router)
    return app


app = create_app()
```

**Step 5: 运行测试**

```bash
poetry run pytest tests/server/test_strategies_router.py -v
```

Expected: 所有测试 PASS

**Step 6: Commit**

```bash
git add src/simtradelab/server/ tests/server/test_strategies_router.py
git commit -m "feat(server): add strategies CRUD router"
```

---

### Task 7: 创建 backtest HTTP 路由

**Files:**
- Create: `src/simtradelab/server/routers/backtest.py`
- Create: `tests/server/test_backtest_router.py`

**Step 1: 写失败的测试**

```python
# tests/server/test_backtest_router.py
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def app():
    from simtradelab.server.main import create_app
    return create_app()


@pytest.mark.asyncio
async def test_run_backtest_returns_task_id(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert isinstance(data["task_id"], str)


@pytest.mark.asyncio
async def test_get_status_pending(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        run_resp = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
        task_id = run_resp.json()["task_id"]
        status_resp = await client.get(f"/backtest/{task_id}/status")

    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["task_id"] == task_id
    assert data["status"] in ("pending", "running")


@pytest.mark.asyncio
async def test_get_status_nonexistent_returns_404(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/backtest/nonexistent/status")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cannot_run_two_concurrent_backtests(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 第一个请求
        r1 = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
        task_id = r1.json()["task_id"]

        # 模拟第一个任务进入 running 状态
        from simtradelab.server.routers.backtest import task_manager
        task_manager.mark_running(task_id)

        # 第二个请求应该被拒绝
        r2 = await client.post("/backtest/run", json={
            "strategy_name": "simple",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        })
    assert r2.status_code == 409
```

**Step 2: 创建 backtest.py 路由**

```python
# src/simtradelab/server/routers/backtest.py
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from simtradelab.server.core.task_manager import TaskManager
from simtradelab.server.core.runner_thread import run_backtest_in_thread
from simtradelab.server.schemas import RunBacktestRequest, TaskStatus, BacktestResult

router = APIRouter(prefix="/backtest", tags=["backtest"])
task_manager = TaskManager()
_executor = ThreadPoolExecutor(max_workers=1)


@router.post("/run")
def run_backtest(req: RunBacktestRequest):
    if task_manager.has_running_task():
        raise HTTPException(status_code=409, detail="已有回测正在运行，请等待完成")

    task_id = task_manager.create_task(req)

    future = _executor.submit(run_backtest_in_thread, task_id, task_manager)
    task_manager.get_task(task_id).future = future

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
        raise HTTPException(status_code=425, detail=f"任务尚未完成，当前状态: {task.status}")

    report = task.result
    assert report is not None

    from simtradelab.backtest.backtest_stats import BacktestStats
    stats: BacktestStats = report.get("_stats")

    series_data = {}
    if stats:
        import pandas as pd
        series_data = {
            "dates": [str(d.date()) if hasattr(d, 'date') else str(d) for d in stats.trade_dates],
            "portfolio_values": [float(v) for v in stats.portfolio_values],
            "daily_pnl": [float(v) for v in stats.daily_pnl],
            "daily_buy_amount": [float(v) for v in stats.daily_buy_amount],
            "daily_sell_amount": [float(v) for v in stats.daily_sell_amount],
            "daily_positions_value": [float(v) for v in stats.daily_positions_value],
        }
    else:
        series_data = {k: [] for k in
                       ["dates", "portfolio_values", "daily_pnl",
                        "daily_buy_amount", "daily_sell_amount", "daily_positions_value"]}

    # 过滤掉不可序列化的内部字段
    metrics = {k: v for k, v in report.items()
               if not k.startswith("_") and not hasattr(v, '__iter__') or isinstance(v, (str, float, int, bool))}

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

    if task.status != "running":
        raise HTTPException(status_code=400, detail="任务未在运行中")

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

    # 回放历史日志（断线重连或回测已完成时有用）
    for msg in task.log_buffer:
        await websocket.send_json(msg)

    # 如果任务已结束，直接关闭
    if task.status in ("finished", "failed"):
        await websocket.close()
        return

    # 实时推送
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
```

**Step 3: 更新 main.py，注册 backtest 路由**

```python
# src/simtradelab/server/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from simtradelab.server.routers import strategies, backtest


def create_app() -> FastAPI:
    app = FastAPI(title="SimTradeLab Server")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(strategies.router)
    app.include_router(backtest.router)
    return app


app = create_app()
```

**Step 4: 运行测试**

```bash
poetry run pytest tests/server/test_backtest_router.py -v
```

Expected: 所有测试 PASS

**Step 5: 运行全部 server 测试**

```bash
poetry run pytest tests/server/ -v
```

Expected: 全部 PASS

**Step 6: Commit**

```bash
git add src/simtradelab/server/ tests/server/test_backtest_router.py
git commit -m "feat(server): add backtest HTTP + WebSocket router"
```

---

### Task 8: 创建 CLI 入口（`simtradelab serve`）

**Files:**
- Create: `src/simtradelab/cli/__init__.py`（若不存在）
- Create: `src/simtradelab/cli/serve.py`

**Step 1: 检查 cli/__init__.py 是否存在**

```bash
ls src/simtradelab/cli/
```

若不存在 `__init__.py`，创建空文件。

**Step 2: 创建 serve.py**

```python
# src/simtradelab/cli/serve.py
from __future__ import annotations

import argparse
import importlib


def main() -> None:
    parser = argparse.ArgumentParser(description="SimTradeLab API Server")
    parser.add_argument("command", nargs="?", default="serve",
                        choices=["serve"], help="子命令")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true",
                        help="开发模式自动重载（不用于生产）")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        raise SystemExit(
            "缺少 server 依赖，请运行: pip install simtradelab[server]"
        )

    print("SimTradeLab Server starting on {}:{}".format(args.host, args.port))
    uvicorn.run(
        "simtradelab.server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
```

**Step 3: 测试 CLI 启动（快速验证，Ctrl+C 退出）**

```bash
poetry run simtradelab serve --port 8765 &
sleep 2
curl -s http://127.0.0.1:8765/strategies
kill %1
```

Expected: 返回策略名称列表 JSON

**Step 4: Commit**

```bash
git add src/simtradelab/cli/
git commit -m "feat(cli): add simtradelab serve command"
```

---

### Task 9: 修复 result 端点的 series 数据（runner 需要保存 stats）

**Files:**
- Modify: `src/simtradelab/server/core/runner_thread.py`
- Modify: `src/simtradelab/backtest/runner.py`

**分析：** `get_result` 端点需要 `BacktestStats`（时间序列），但 `BacktestRunner.run()` 目前只返回 report dict。需要在 `ServerBacktestRunner` 中保存 stats 引用。

**Step 1: 修改 runner.py，让 _generate_reports 也把 stats 存入 report**

在 `runner.py` 的 `_generate_reports` 方法中，在 `return report` 之前追加：

```python
# 供 API 层读取时间序列数据
report["_stats"] = stats
if config.enable_charts:
    report["_chart_path"] = self._chart_filename
```

找到 `_generate_reports` 中 `return report` 这一行（约第 402 行），在其前插入以上两行。

**Step 2: 验证 result 端点能正确返回 series**

此步骤在 Task 11 集成测试中验证。

**Step 3: Commit**

```bash
git add src/simtradelab/backtest/runner.py src/simtradelab/server/core/runner_thread.py
git commit -m "feat(server): expose BacktestStats in report for API series data"
```

---

## Phase 2: Electron + React UI

---

### Task 10: 搭建 Electron + React 项目

**Files:**
- Create: `ui/` 目录（electron-vite 脚手架）

**Step 1: 搭建项目（在 SimTradeLab 根目录执行）**

```bash
npm create @quick-start/electron ui -- --template react-ts
cd ui
npm install
```

**Step 2: 安装 UI 依赖**

```bash
cd ui
npm install antd @ant-design/icons
npm install @monaco-editor/react
npm install echarts echarts-for-react
npm install axios
npm install @types/node --save-dev
```

**Step 3: 确认开发模式可以启动**

```bash
cd ui
npm run dev
```

Expected: Electron 窗口打开，显示默认 React 页面

**Step 4: Commit**

```bash
git add ui/
git commit -m "chore(ui): scaffold electron-vite react-ts project"
```

---

### Task 11: Electron 主进程——服务器生命周期管理

**Files:**
- Modify: `ui/electron/main.ts`
- Create: `ui/electron/server.ts`

**Step 1: 创建 server.ts（管理 FastAPI 子进程）**

```typescript
// ui/electron/server.ts
import { spawn, ChildProcess } from 'child_process'
import * as net from 'net'
import * as path from 'path'
import { app } from 'electron'

let serverProcess: ChildProcess | null = null

export async function findFreePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const port = (server.address() as net.AddressInfo).port
      server.close(() => resolve(port))
    })
    server.on('error', reject)
  })
}

export async function startServer(port: number): Promise<void> {
  const isDev = !app.isPackaged

  const serverBin = isDev
    ? process.platform === 'win32' ? 'simtradelab.cmd' : 'simtradelab'
    : path.join(process.resourcesPath, 'server',
        process.platform === 'win32' ? 'simtradelab-server.exe' : 'simtradelab-server')

  serverProcess = spawn(serverBin, ['serve', '--port', String(port)], {
    env: { ...process.env },
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  serverProcess.stdout?.on('data', (d) => console.log('[server]', d.toString()))
  serverProcess.stderr?.on('data', (d) => console.error('[server]', d.toString()))

  // 等待服务器就绪（轮询 /strategies 端点）
  await waitForServer(port, 15000)
}

async function waitForServer(port: number, timeoutMs: number): Promise<void> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    try {
      const { default: http } = await import('http')
      await new Promise<void>((resolve, reject) => {
        const req = http.get(`http://127.0.0.1:${port}/strategies`, (res) => {
          if (res.statusCode === 200) resolve()
          else reject(new Error(`status ${res.statusCode}`))
        })
        req.on('error', reject)
        req.setTimeout(1000, () => reject(new Error('timeout')))
      })
      return
    } catch {
      await new Promise((r) => setTimeout(r, 500))
    }
  }
  throw new Error('FastAPI server failed to start within timeout')
}

export function stopServer(): void {
  if (serverProcess) {
    serverProcess.kill()
    serverProcess = null
  }
}
```

**Step 2: 修改 main.ts，集成 server 生命周期**

在 `main.ts` 的 `app.whenReady()` 回调中，在创建窗口之前启动服务器，并通过 IPC 把端口传给渲染进程：

```typescript
// ui/electron/main.ts（关键修改部分）
import { app, BrowserWindow, ipcMain } from 'electron'
import { startServer, stopServer, findFreePort } from './server'

let serverPort: number

app.whenReady().then(async () => {
  serverPort = await findFreePort()
  await startServer(serverPort)
  createWindow()
})

// 渲染进程请求端口
ipcMain.handle('get-server-port', () => serverPort)

app.on('before-quit', () => stopServer())
```

**Step 3: 修改 preload.ts，暴露 getServerPort**

```typescript
// ui/electron/preload.ts
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  getServerPort: () => ipcRenderer.invoke('get-server-port'),
})
```

**Step 4: 验证（开发模式）**

```bash
cd ui && npm run dev
```

Expected: Electron 启动，FastAPI 服务器在随机端口启动，控制台显示 `[server] SimTradeLab Server starting on 127.0.0.1:XXXX`

**Step 5: Commit**

```bash
cd ..
git add ui/electron/
git commit -m "feat(ui): electron main process spawns FastAPI server"
```

---

### Task 12: API 服务层（axios + WebSocket 封装）

**Files:**
- Create: `ui/src/services/api.ts`
- Create: `ui/src/services/backtest.ws.ts`

**Step 1: 创建 api.ts**

```typescript
// ui/src/services/api.ts
import axios from 'axios'

declare global {
  interface Window {
    electronAPI?: {
      getServerPort: () => Promise<number>
    }
  }
}

async function getBaseURL(): Promise<string> {
  if (window.electronAPI) {
    const port = await window.electronAPI.getServerPort()
    return `http://127.0.0.1:${port}`
  }
  return import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
}

let _client: ReturnType<typeof axios.create> | null = null

export async function getClient() {
  if (!_client) {
    const baseURL = await getBaseURL()
    _client = axios.create({ baseURL })
  }
  return _client
}

export type Strategy = { name: string; source: string }
export type TaskStatusResp = {
  task_id: string
  status: 'pending' | 'running' | 'finished' | 'failed'
  progress: number
  started_at?: string
  finished_at?: string
  error?: string
}

export const strategiesAPI = {
  list: async (): Promise<string[]> => (await (await getClient()).get('/strategies')).data,
  get: async (name: string): Promise<Strategy> => (await (await getClient()).get(`/strategies/${name}`)).data,
  save: async (name: string, source: string) =>
    (await (await getClient()).put(`/strategies/${name}`, { name, source })).data,
  create: async (name: string) =>
    (await (await getClient()).post(`/strategies/${name}`, { name })).data,
  delete: async (name: string) =>
    (await (await getClient()).delete(`/strategies/${name}`)).data,
}

export const backtestAPI = {
  run: async (params: {
    strategy_name: string
    start_date: string
    end_date: string
    initial_capital: number
    frequency: string
    enable_charts: boolean
    sandbox: boolean
  }): Promise<{ task_id: string }> =>
    (await (await getClient()).post('/backtest/run', params)).data,

  status: async (taskId: string): Promise<TaskStatusResp> =>
    (await (await getClient()).get(`/backtest/${taskId}/status`)).data,

  result: async (taskId: string) =>
    (await (await getClient()).get(`/backtest/${taskId}/result`)).data,

  cancel: async (taskId: string) =>
    (await (await getClient()).post(`/backtest/${taskId}/cancel`)).data,
}
```

**Step 2: 创建 backtest.ws.ts**

```typescript
// ui/src/services/backtest.ws.ts
export type LogMessage = {
  level: string
  msg: string
  ts: number
}

export function createLogStream(
  baseURL: string,
  taskId: string,
  onMessage: (msg: LogMessage) => void,
  onDone: () => void,
): () => void {
  const wsURL = baseURL.replace(/^http/, 'ws') + `/backtest/${taskId}/logs`
  const ws = new WebSocket(wsURL)

  ws.onmessage = (event) => {
    const msg: LogMessage = JSON.parse(event.data)
    if (msg.msg === '__DONE__' || msg.msg === '__FAIL__') {
      onDone()
      ws.close()
    } else {
      onMessage(msg)
    }
  }

  ws.onerror = () => onDone()

  return () => ws.close()
}
```

**Step 3: Commit**

```bash
git add ui/src/services/
git commit -m "feat(ui): add axios API client and WebSocket log stream"
```

---

### Task 13: StrategyPanel 组件（策略列表）

**Files:**
- Create: `ui/src/components/StrategyPanel/index.tsx`

```tsx
// ui/src/components/StrategyPanel/index.tsx
import { useEffect, useState } from 'react'
import { Button, List, Input, Popconfirm, message, Spin } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { strategiesAPI } from '../../services/api'

interface Props {
  selected: string | null
  onSelect: (name: string) => void
  onRefresh?: () => void
}

export function StrategyPanel({ selected, onSelect, onRefresh }: Props) {
  const [strategies, setStrategies] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      setStrategies(await strategiesAPI.list())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!newName.trim()) return
    try {
      await strategiesAPI.create(newName.trim())
      message.success(`策略 "${newName}" 已创建`)
      setNewName('')
      setCreating(false)
      await load()
      onRefresh?.()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '创建失败')
    }
  }

  const handleDelete = async (name: string) => {
    await strategiesAPI.delete(name)
    message.success(`策略 "${name}" 已删除`)
    await load()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontWeight: 600 }}>策略</span>
        <Button
          size="small"
          icon={<PlusOutlined />}
          onClick={() => setCreating(!creating)}
        />
      </div>

      {creating && (
        <Input.Search
          size="small"
          placeholder="策略名称"
          enterButton="创建"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onSearch={handleCreate}
          style={{ marginBottom: 8 }}
        />
      )}

      <Spin spinning={loading} style={{ flex: 1 }}>
        <List
          size="small"
          dataSource={strategies}
          renderItem={(name) => (
            <List.Item
              style={{
                cursor: 'pointer',
                background: name === selected ? '#e6f4ff' : 'transparent',
                padding: '4px 8px',
                borderRadius: 4,
              }}
              onClick={() => onSelect(name)}
              actions={[
                <Popconfirm
                  key="del"
                  title="确认删除？"
                  onConfirm={() => handleDelete(name)}
                >
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => e.stopPropagation()}
                  />
                </Popconfirm>,
              ]}
            >
              {name}
            </List.Item>
          )}
        />
      </Spin>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add ui/src/components/
git commit -m "feat(ui): add StrategyPanel component"
```

---

### Task 14: EditorPanel（Monaco 编辑器）

**Files:**
- Create: `ui/src/components/EditorPanel/index.tsx`

```tsx
// ui/src/components/EditorPanel/index.tsx
import { useEffect, useState, useRef } from 'react'
import Editor from '@monaco-editor/react'
import { Button, Space, message, Tag } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { strategiesAPI } from '../../services/api'

interface Props {
  strategyName: string | null
}

export function EditorPanel({ strategyName }: Props) {
  const [source, setSource] = useState<string>('')
  const [saved, setSaved] = useState(true)
  const [loading, setLoading] = useState(false)
  const editorRef = useRef<any>(null)

  useEffect(() => {
    if (!strategyName) return
    setLoading(true)
    strategiesAPI.get(strategyName)
      .then((s) => { setSource(s.source); setSaved(true) })
      .finally(() => setLoading(false))
  }, [strategyName])

  const handleSave = async () => {
    if (!strategyName) return
    await strategiesAPI.save(strategyName, source)
    message.success('已保存')
    setSaved(true)
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      handleSave()
    }
  }

  if (!strategyName) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#999' }}>
        从左侧选择或新建策略
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '4px 8px', borderBottom: '1px solid #f0f0f0' }}>
        <Space>
          <span style={{ fontWeight: 600 }}>{strategyName}</span>
          {!saved && <Tag color="orange">未保存</Tag>}
        </Space>
        <Button
          size="small"
          icon={<SaveOutlined />}
          onClick={handleSave}
          type={saved ? 'default' : 'primary'}
        >
          保存 (Ctrl+S)
        </Button>
      </div>
      <Editor
        height="100%"
        defaultLanguage="python"
        value={source}
        loading={loading}
        theme="vs-light"
        options={{
          fontSize: 14,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
        }}
        onMount={(editor) => {
          editorRef.current = editor
          editor.getDomNode()?.addEventListener('keydown', handleKeyDown)
        }}
        onChange={(val) => { setSource(val ?? ''); setSaved(false) }}
      />
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add ui/src/components/EditorPanel/
git commit -m "feat(ui): add Monaco editor panel with auto-save"
```

---

### Task 15: RunPanel + LogConsole（回测控制 + 实时日志）

**Files:**
- Create: `ui/src/components/RunPanel/index.tsx`
- Create: `ui/src/components/LogConsole/index.tsx`

**Step 1: 创建 RunPanel**

```tsx
// ui/src/components/RunPanel/index.tsx
import { useState } from 'react'
import { Form, DatePicker, InputNumber, Select, Button, Space, Alert } from 'antd'
import { PlayCircleOutlined, StopOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { backtestAPI } from '../../services/api'

interface Props {
  strategyName: string | null
  onTaskStarted: (taskId: string) => void
  onTaskDone: () => void
  runningTaskId: string | null
}

export function RunPanel({ strategyName, onTaskStarted, runningTaskId }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRun = async () => {
    if (!strategyName) return
    const values = await form.validateFields()
    setLoading(true)
    setError(null)
    try {
      const { task_id } = await backtestAPI.run({
        strategy_name: strategyName,
        start_date: values.start_date.format('YYYY-MM-DD'),
        end_date: values.end_date.format('YYYY-MM-DD'),
        initial_capital: values.initial_capital,
        frequency: values.frequency,
        enable_charts: true,
        sandbox: true,
      })
      onTaskStarted(task_id)
    } catch (e: any) {
      setError(e.response?.data?.detail || '启动失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!runningTaskId) return
    await backtestAPI.cancel(runningTaskId)
  }

  return (
    <div style={{ padding: '8px 12px' }}>
      <Form
        form={form}
        layout="inline"
        initialValues={{
          start_date: dayjs('2024-01-01'),
          end_date: dayjs('2024-12-31'),
          initial_capital: 100000,
          frequency: '1d',
        }}
      >
        <Form.Item name="start_date" label="开始" rules={[{ required: true }]}>
          <DatePicker size="small" />
        </Form.Item>
        <Form.Item name="end_date" label="结束" rules={[{ required: true }]}>
          <DatePicker size="small" />
        </Form.Item>
        <Form.Item name="initial_capital" label="本金" rules={[{ required: true }]}>
          <InputNumber size="small" min={1000} step={10000} style={{ width: 120 }} />
        </Form.Item>
        <Form.Item name="frequency" label="频率">
          <Select size="small" style={{ width: 70 }} options={[
            { value: '1d', label: '日线' },
            { value: '1m', label: '分钟' },
          ]} />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              loading={loading}
              disabled={!strategyName || !!runningTaskId}
              onClick={handleRun}
            >
              运行
            </Button>
            {runningTaskId && (
              <Button
                danger
                size="small"
                icon={<StopOutlined />}
                onClick={handleCancel}
              >
                取消
              </Button>
            )}
          </Space>
        </Form.Item>
      </Form>
      {error && <Alert type="error" message={error} style={{ marginTop: 4 }} closable onClose={() => setError(null)} />}
    </div>
  )
}
```

**Step 2: 创建 LogConsole**

```tsx
// ui/src/components/LogConsole/index.tsx
import { useEffect, useRef } from 'react'
import { LogMessage } from '../../services/backtest.ws'

const LEVEL_COLOR: Record<string, string> = {
  INFO: '#1677ff',
  WARNING: '#fa8c16',
  ERROR: '#ff4d4f',
  DEBUG: '#8c8c8c',
  SYSTEM: '#52c41a',
}

interface Props {
  logs: LogMessage[]
}

export function LogConsole({ logs }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  return (
    <div style={{
      height: '100%',
      overflowY: 'auto',
      background: '#1e1e1e',
      padding: '8px 12px',
      fontFamily: 'monospace',
      fontSize: 12,
    }}>
      {logs.map((log, i) => (
        <div key={i} style={{ color: LEVEL_COLOR[log.level] || '#d4d4d4', lineHeight: 1.6 }}>
          <span style={{ color: '#6a9955', marginRight: 8 }}>
            {new Date(log.ts * 1000).toLocaleTimeString()}
          </span>
          {log.msg}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add ui/src/components/RunPanel/ ui/src/components/LogConsole/
git commit -m "feat(ui): add RunPanel and LogConsole components"
```

---

### Task 16: ResultPanel（ECharts 图表 + 指标卡片）

**Files:**
- Create: `ui/src/components/ResultPanel/index.tsx`

```tsx
// ui/src/components/ResultPanel/index.tsx
import ReactECharts from 'echarts-for-react'
import { Card, Statistic, Row, Col, Button, Divider } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'

interface Props {
  result: any | null
}

export function ResultPanel({ result }: Props) {
  if (!result) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#999' }}>
        运行回测后结果将显示在此处
      </div>
    )
  }

  const { metrics, series, chart_png_path } = result

  const navOption = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['策略净值', metrics.benchmark_name] },
    xAxis: { type: 'category', data: series.dates, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value' },
    series: [
      {
        name: '策略净值',
        type: 'line',
        data: series.portfolio_values.map((v: number) => (v / series.portfolio_values[0]).toFixed(4)),
        lineStyle: { width: 2 },
        smooth: false,
      },
    ],
  }

  const pnlOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: series.dates, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value' },
    series: [
      {
        name: '每日盈亏',
        type: 'bar',
        data: series.daily_pnl,
        itemStyle: {
          color: (params: any) => params.value >= 0 ? '#ef5350' : '#26a69a',
        },
      },
    ],
  }

  const fmt = (v: number, pct = false) =>
    pct ? `${(v * 100).toFixed(2)}%` : v.toFixed(3)

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 12 }}>
      <Row gutter={[8, 8]}>
        <Col span={8}><Card size="small"><Statistic title="总收益" value={fmt(metrics.total_return, true)} valueStyle={{ color: metrics.total_return >= 0 ? '#cf1322' : '#3f8600' }} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="年化收益" value={fmt(metrics.annual_return, true)} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="最大回撤" value={fmt(metrics.max_drawdown, true)} valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="夏普比率" value={fmt(metrics.sharpe_ratio)} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title="胜率" value={fmt(metrics.win_rate, true)} /></Card></Col>
        <Col span={8}><Card size="small"><Statistic title={`超额(vs ${metrics.benchmark_name})`} value={fmt(metrics.excess_return, true)} /></Card></Col>
      </Row>

      <Divider style={{ margin: '12px 0' }}>净值曲线</Divider>
      <ReactECharts option={navOption} style={{ height: 240 }} />

      <Divider style={{ margin: '12px 0' }}>每日盈亏</Divider>
      <ReactECharts option={pnlOption} style={{ height: 180 }} />

      {chart_png_path && (
        <>
          <Divider style={{ margin: '12px 0' }} />
          <Button
            icon={<DownloadOutlined />}
            onClick={() => {
              const a = document.createElement('a')
              a.href = `file://${chart_png_path}`
              a.download = 'backtest_chart.png'
              a.click()
            }}
          >
            导出 PNG 图表
          </Button>
        </>
      )}
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add ui/src/components/ResultPanel/
git commit -m "feat(ui): add ResultPanel with ECharts and PNG export"
```

---

### Task 17: App.tsx——组装完整页面

**Files:**
- Modify: `ui/src/App.tsx`

```tsx
// ui/src/App.tsx
import { useState, useEffect, useCallback } from 'react'
import { Layout, Splitter, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { StrategyPanel } from './components/StrategyPanel'
import { EditorPanel } from './components/EditorPanel'
import { RunPanel } from './components/RunPanel'
import { LogConsole } from './components/LogConsole'
import { ResultPanel } from './components/ResultPanel'
import { createLogStream, LogMessage } from './services/backtest.ws'
import { backtestAPI } from './services/api'

const { Header, Content } = Layout

export default function App() {
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null)
  const [runningTaskId, setRunningTaskId] = useState<string | null>(null)
  const [logs, setLogs] = useState<LogMessage[]>([])
  const [result, setResult] = useState<any | null>(null)
  const [baseURL, setBaseURL] = useState('http://127.0.0.1:8000')

  useEffect(() => {
    window.electronAPI?.getServerPort().then((port) => {
      setBaseURL(`http://127.0.0.1:${port}`)
    })
  }, [])

  const handleTaskStarted = useCallback((taskId: string) => {
    setRunningTaskId(taskId)
    setLogs([])
    setResult(null)

    const stopStream = createLogStream(
      baseURL,
      taskId,
      (msg) => setLogs((prev) => [...prev, msg]),
      async () => {
        setRunningTaskId(null)
        try {
          const res = await backtestAPI.result(taskId)
          setResult(res)
        } catch {
          // 任务失败，result 不可用
        }
      },
    )

    return stopStream
  }, [baseURL])

  return (
    <ConfigProvider locale={zhCN}>
      <Layout style={{ height: '100vh' }}>
        <Header style={{ background: '#141414', color: '#fff', padding: '0 16px', height: 40, lineHeight: '40px', fontSize: 14 }}>
          SimTradeLab
        </Header>
        <Content style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <RunPanel
            strategyName={selectedStrategy}
            onTaskStarted={handleTaskStarted}
            onTaskDone={() => setRunningTaskId(null)}
            runningTaskId={runningTaskId}
          />
          <Splitter style={{ flex: 1, overflow: 'hidden' }}>
            {/* 左栏：策略列表 */}
            <Splitter.Panel defaultSize={200} min={160} max={320}>
              <StrategyPanel
                selected={selectedStrategy}
                onSelect={setSelectedStrategy}
              />
            </Splitter.Panel>

            {/* 中栏：编辑器 + 日志 */}
            <Splitter.Panel>
              <Splitter layout="vertical">
                <Splitter.Panel defaultSize="60%">
                  <EditorPanel strategyName={selectedStrategy} />
                </Splitter.Panel>
                <Splitter.Panel>
                  <LogConsole logs={logs} />
                </Splitter.Panel>
              </Splitter>
            </Splitter.Panel>

            {/* 右栏：结果 */}
            <Splitter.Panel defaultSize={360} min={280}>
              <ResultPanel result={result} />
            </Splitter.Panel>
          </Splitter>
        </Content>
      </Layout>
    </ConfigProvider>
  )
}
```

**Step 2: 在开发模式下验证整体流程**

```bash
# 终端 1：启动 FastAPI
poetry run simtradelab serve --port 8000

# 终端 2：启动 Electron
cd ui && npm run dev
```

操作：选择策略 → 编辑 → 运行 → 看日志 → 看结果

**Step 3: Commit**

```bash
git add ui/src/App.tsx
git commit -m "feat(ui): assemble full backtest page layout"
```

---

## Phase 3: 打包

---

### Task 18: PyInstaller 打包 FastAPI Server

**Files:**
- Create: `packaging/server.spec`
- Create: `packaging/build_server.sh`

**Step 1: 安装 PyInstaller（dev 依赖）**

```bash
poetry add --group dev pyinstaller
```

**Step 2: 创建 server.spec**

```python
# packaging/server.spec
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['../src/simtradelab/cli/serve.py'],
    pathex=['../src'],
    binaries=[],
    datas=[
        ('../src/simtradelab/data', 'simtradelab/data'),
        ('../strategies', 'strategies'),
    ],
    hiddenimports=[
        'simtradelab.server.main',
        'simtradelab.server.routers.strategies',
        'simtradelab.server.routers.backtest',
        'simtradelab.server.core.task_manager',
        'simtradelab.server.core.log_streamer',
        'simtradelab.server.core.runner_thread',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'pandas',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='simtradelab-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
)
```

**Step 3: 创建 build_server.sh**

```bash
#!/bin/bash
# packaging/build_server.sh
set -e

cd "$(dirname "$0")/.."
poetry run pyinstaller packaging/server.spec --distpath ui/resources/server --clean
echo "Server binary built to ui/resources/server/simtradelab-server"
```

**Step 4: 测试打包**

```bash
chmod +x packaging/build_server.sh
./packaging/build_server.sh
./ui/resources/server/simtradelab-server serve --port 9000 &
sleep 3
curl http://127.0.0.1:9000/strategies
kill %1
```

Expected: 返回策略列表 JSON

**Step 5: Commit**

```bash
git add packaging/
git commit -m "chore: add PyInstaller spec and build script"
```

---

### Task 19: electron-builder 最终打包

**Files:**
- Create: `ui/electron-builder.yml`
- Modify: `ui/electron/main.ts`（确保 isPackaged 分支指向正确路径）

**Step 1: 创建 electron-builder.yml**

```yaml
# ui/electron-builder.yml
appId: com.simtradelab.app
productName: SimTradeLab
directories:
  output: dist

files:
  - '!node_modules/**/*'
  - out/**/*

extraResources:
  - from: resources/server/
    to: server/
    filter:
      - '**/*'

win:
  target: nsis
  icon: resources/icon.ico

mac:
  target: dmg
  icon: resources/icon.icns

linux:
  target: AppImage
  icon: resources/icon.png

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  installerIcon: resources/icon.ico
  installerHeaderIcon: resources/icon.ico
```

**Step 2: 在 package.json 中添加打包命令**

在 `ui/package.json` 的 `scripts` 中添加：

```json
"build:server": "cd .. && ./packaging/build_server.sh",
"build:ui": "electron-vite build",
"package": "npm run build:server && npm run build:ui && electron-builder"
```

**Step 3: 打包并验证**

```bash
cd ui
npm run package
```

Expected：`ui/dist/` 目录下生成平台对应的安装包

**Step 4: 安装并测试**

- Windows: 双击 `.exe` 安装
- macOS: 打开 `.dmg`
- Linux: 运行 `.AppImage`

验证：应用启动，服务器自动启动，策略列表正常加载

**Step 5: Commit**

```bash
git add ui/electron-builder.yml ui/package.json
git commit -m "chore: add electron-builder packaging config"
```

---

## 实施状态（2026-02-18）

| Task | 状态 | Commit |
|------|------|--------|
| Task 1: 添加 server 依赖 | ✅ | a3a313b |
| Task 2: schemas.py | ✅ | 0605e20 |
| Task 3: task_manager.py | ✅ | 41334c8 |
| Task 4: log_streamer.py | ✅ | 15b50cc |
| Task 5: runner_thread.py | ✅ | 7e5024a |
| Task 6+7: routers + main.py | ✅ | e2cc9f7 |
| Task 8+9: CLI + runner stats | ✅ | ebe3d6a |
| fix: asyncio loop 跨线程 | ✅ | b1164d5 |
| Task 10: Electron + React 脚手架 | ✅ | — |
| Task 11: Electron 主进程 | ✅ | b3977c7 |
| Task 12: API 服务层 | ✅ | b3977c7 |
| Task 13-17: UI 组件 + App | ✅ | 11ff1e1 |
| fix: 恢复 simple 策略文件 | ✅ | fcdfe84 |
| Task 18-19: 打包配置 | ✅ | dd84d5e |

**测试**：18/18 通过
**UI 编译**：3728 模块，无错误
**分支**：`feat/desktop-app`（未合并，保留中）

---

## 完成后验证清单

```bash
# 1. 全部 server 测试通过
poetry run pytest tests/server/ -v

# 2. 开发模式联调
poetry run simtradelab serve --port 8000 &
cd ui && npm run dev

# 3. API 手动验证
curl http://127.0.0.1:8000/strategies
curl -X POST http://127.0.0.1:8000/strategies/test -H "Content-Type: application/json" -d '{"name":"test"}'

# 4. 打包验证
cd ui && npm run package
```
