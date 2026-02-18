# SimTradeLab 桌面应用设计文档

日期：2026-02-18
状态：已批准，待实施

---

## 一、目标与约束

**目标**：基于 SimTradeLab 回测引擎构建一个桌面应用，提供策略编辑、回测运行、日志监控、结果可视化的完整工作流。

**约束**：
- 本地开发简单（`poetry run python` + `npm run dev`）
- 普通用户开箱即用（下载安装包，双击运行，无需安装 Python）
- 架构为 SaaS 预留：FastAPI server 将来可直接部署到云端，UI 只改 API 地址

---

## 二、整体架构

```
用户 → Electron UI（React + TypeScript）
              ↓ HTTP REST / WebSocket
         FastAPI Server（Python，子进程）
              ↓ 直接 import
         SimTradeLab 回测引擎
```

**进程模型**：
- Electron 主进程启动时 `spawn` FastAPI 可执行文件
- FastAPI 监听 `127.0.0.1:随机端口`（避免端口冲突）
- Electron 退出时 kill FastAPI 子进程

**打包模型**：
- PyInstaller 将 FastAPI server + simtradelab 引擎打包为单个可执行文件
- electron-builder 将上述可执行文件 + Electron UI 打包为系统安装包

---

## 三、目录结构

```
SimTradeLab/                              ← monorepo
├── src/simtradelab/
│   ├── backtest/                         ← 现有（不改动）
│   ├── ptrade/                           ← 现有（不改动）
│   ├── server/                           ← 新增：FastAPI 服务层
│   │   ├── __init__.py
│   │   ├── main.py                       ← FastAPI app 入口
│   │   ├── routers/
│   │   │   ├── strategies.py
│   │   │   └── backtest.py
│   │   ├── core/
│   │   │   ├── task_manager.py           ← 任务生命周期管理
│   │   │   ├── log_streamer.py           ← logging → asyncio Queue → WebSocket
│   │   │   └── runner_thread.py          ← 在 ThreadPoolExecutor 中运行 BacktestRunner
│   │   └── schemas.py                    ← Pydantic 请求/响应模型
│   └── cli/
│       └── serve.py                      ← `simtradelab serve` CLI 入口
│
├── ui/                                   ← Electron + React 子项目
│   ├── electron/
│   │   ├── main.ts                       ← 主进程：spawn server，管理生命周期
│   │   └── preload.ts                    ← contextBridge 安全桥
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── StrategyPanel/            ← 左侧：策略列表 + 新建/删除
│   │   │   ├── EditorPanel/              ← Monaco 代码编辑器 + 保存
│   │   │   ├── RunPanel/                 ← BacktestConfig 表单 + 运行/取消
│   │   │   ├── LogConsole/               ← WebSocket 实时日志
│   │   │   └── ResultPanel/              ← ECharts 图表 + PNG 导出入口
│   │   └── services/
│   │       ├── api.ts                    ← axios 封装（baseURL 动态注入端口）
│   │       └── backtest.ws.ts            ← WebSocket 日志订阅封装
│   ├── package.json
│   └── electron-builder.yml
│
├── pyproject.toml                        ← 新增 [server] extra + CLI script
└── strategies/                           ← 现有（不改动）
```

---

## 四、依赖变更（pyproject.toml）

```toml
[tool.poetry.dependencies]
# 新增 server extra
fastapi   = {version = "^0.115.0", optional = true}
uvicorn   = {version = "^0.34.0",  optional = true}

[tool.poetry.extras]
server = ["fastapi", "uvicorn"]
all    = ["ta-lib", "optuna", "fastapi", "uvicorn"]

[tool.poetry.scripts]
simtradelab = "simtradelab.cli.serve:main"
```

安装方式：
- 普通用户：通过 Electron 安装包，无需手动安装
- 开发者：`pip install simtradelab[server]` + `simtradelab serve`

---

## 五、API 端点

### 策略管理

| 方法   | 路径                    | 说明               |
|--------|-------------------------|--------------------|
| GET    | /strategies             | 列出所有策略名称   |
| GET    | /strategies/{name}      | 读取策略源码       |
| PUT    | /strategies/{name}      | 保存策略源码       |
| POST   | /strategies/{name}      | 从模板创建新策略   |
| DELETE | /strategies/{name}      | 删除策略           |

### 回测

| 方法      | 路径                          | 说明                         |
|-----------|-------------------------------|------------------------------|
| POST      | /backtest/run                 | 启动回测，返回 task_id       |
| GET       | /backtest/{task_id}/status    | 查询任务状态与进度           |
| GET       | /backtest/{task_id}/result    | 获取指标 + 时间序列数据      |
| WebSocket | /backtest/{task_id}/logs      | 实时日志流                   |
| POST      | /backtest/{task_id}/cancel    | 取消运行中的任务             |

### 请求/响应结构

**POST /backtest/run 请求体**：
```json
{
  "strategy_name": "simple",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000.0,
  "frequency": "1d",
  "enable_charts": true,
  "sandbox": true
}
```

**GET /backtest/{task_id}/status 响应**：
```json
{
  "task_id": "a3f8c2d1",
  "status": "running",
  "progress": 0.42,
  "started_at": "2026-02-18T10:23:00",
  "finished_at": null,
  "error": null
}
```

**GET /backtest/{task_id}/result 响应**：
```json
{
  "metrics": {
    "total_return": 0.183,
    "annual_return": 0.201,
    "sharpe_ratio": 1.42,
    "max_drawdown": -0.087
  },
  "series": {
    "dates": ["2024-01-02", "..."],
    "portfolio_values": [100000, "..."],
    "daily_pnl": [0, "..."],
    "daily_buy_amount": [0, "..."],
    "daily_sell_amount": [0, "..."],
    "daily_positions_value": [0, "..."]
  },
  "chart_png_path": "strategies/simple/stats/backtest_xxx.png"
}
```

**WS /backtest/{task_id}/logs 消息格式**：
```json
{ "level": "INFO",   "msg": "[买入信号] 600519.SS ...", "ts": 1739000000.123 }
{ "level": "SYSTEM", "msg": "__DONE__",                 "ts": 1739000000.999 }
```

---

## 六、任务管理设计

```python
@dataclass
class TaskState:
    task_id: str
    task_type: Literal["backtest", "optimize"]   # 预留 optimize
    status: Literal["pending", "running", "finished", "failed"]
    config: BacktestConfig
    progress: float           # 0.0 ~ 1.0
    result: dict | None
    error: str | None
    log_queue: asyncio.Queue  # 线程安全日志桥
    future: Future | None     # ThreadPoolExecutor 的 Future，用于 cancel
```

**生命周期**：
1. `POST /backtest/run` → 生成 `task_id`，写入 `tasks` dict，提交到 `ThreadPoolExecutor`
2. 子线程运行 `BacktestRunner.run()`，通过 `QueueHandler` 把日志写入 `log_queue`
3. WebSocket handler 用 `asyncio` 从 `log_queue` 读取并推送给客户端
4. 回测完成 → `status = "finished"`，`result` 写入，推送 `__DONE__` 信号
5. `POST /cancel` → `future.cancel()` + 设置中断标志

**跨线程通信**：
- `BacktestRunner` 在子线程，WebSocket 在 asyncio 主循环
- 通过 `loop.call_soon_threadsafe(queue.put_nowait, msg)` 安全跨线程

---

## 七、日志流桥接

```
BacktestRunner（子线程）
  └── logging.getLogger('backtest')
       └── QueueHandler（自定义）
            └── loop.call_soon_threadsafe → asyncio.Queue
                                                  ↓
                                     asyncio 消费者协程
                                       └── WebSocket.send_json()
                                            → 所有订阅该 task_id 的客户端
```

多个 WebSocket 客户端订阅同一 `task_id` 时，通过 `set[WebSocket]` 广播。

---

## 八、前端组件结构

```
App
└── BacktestPage（主页面，三栏布局）
    ├── StrategyPanel（左栏，~240px）
    │   ├── 策略列表（Ant Design Tree / List）
    │   ├── 新建按钮
    │   └── 右键菜单（重命名、删除）
    │
    ├── WorkspacePanel（中栏，flex-grow）
    │   ├── EditorPanel
    │   │   └── Monaco Editor（Python 语法高亮）
    │   ├── RunPanel
    │   │   ├── 日期选择器（start_date / end_date）
    │   │   ├── 初始资金输入
    │   │   ├── 频率选择（1d / 1m）
    │   │   └── 运行 / 取消 按钮
    │   └── LogConsole（底部，可折叠）
    │       └── 实时日志（WebSocket，自动滚动到底部）
    │
    └── ResultPanel（右栏，~400px，回测完成后展开）
        ├── 指标卡片（总收益、夏普、最大回撤等）
        ├── ECharts 净值曲线（策略 vs 基准）
        ├── ECharts 每日盈亏柱状图
        └── 导出 PNG 按钮
```

**技术选型**：
- UI 框架：React 18 + TypeScript + Ant Design 5
- 代码编辑器：Monaco Editor（`@monaco-editor/react`）
- 图表：Apache ECharts（`echarts-for-react`）
- HTTP 客户端：axios
- 构建：Vite + electron-vite
- 打包：electron-builder + PyInstaller

---

## 九、优化器预留接口

优化器（`simtradelab[optimizer]`）将来融入时，只需：

1. `TaskState.task_type` 已包含 `"optimize"` 选项
2. 新增路由 `POST /optimize/run`、`GET /optimize/{task_id}/result`
3. UI 新增 `OptimizePanel` tab，编辑 `optimize_params.py`，展示参数热力图 + WF 净值曲线
4. 任务管理、日志流、WebSocket 机制**零改动**

---

## 十、开发阶段计划（概览）

| 阶段 | 内容 |
|------|------|
| Phase 1 | FastAPI server：策略增删改查 + 回测任务管理 + 日志流 |
| Phase 2 | Electron 主进程：spawn server + 端口管理 |
| Phase 3 | React UI：策略列表 + Monaco 编辑器 + 运行面板 + 日志控制台 |
| Phase 4 | 结果展示：ECharts 图表 + 指标卡片 |
| Phase 5 | 打包：PyInstaller + electron-builder |
