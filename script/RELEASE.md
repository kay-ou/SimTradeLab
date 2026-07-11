# SimTradeLab 发布指南

## 发布模型（当前仓库真实流程）

当前发布由两部分组成：

1. 本地执行 `script/release.py`：
- 更新 `pyproject.toml` 版本号
- 更新 `README.md` / `README.zh-CN.md` / `README.de.md` 中版本相关文本
- 提交版本 bump commit（`chore: bump version to X.Y.Z`）

2. 推送 `main` 后，GitHub Actions（`.github/workflows/publish.yml`）自动：
- 检查 `pyproject.toml` 版本是否已有 tag
- 自动创建并推送 tag（`vX.Y.Z`）
- 创建 GitHub Release（从 `CHANGELOG.md` 提取对应版本说明）
- 构建并发布到 PyPI（Trusted Publishing）
- 安装回归验证

## 发布前检查

```bash
# 1) 工作区必须干净（除了你准备发布的改动）
git status --short

# 2) 测试必须通过
poetry run pytest -q

# 3) 严重 Ruff 问题和 Ruff 基线检查必须通过
poetry run ruff check src tests --select E9,F63,F7,F82
poetry run python script/check_ruff_baseline.py

# 4) CHANGELOG 需包含目标版本段落（例如 2.10.2）
rg -n "^## \\[2\\.10\\.2\\]" CHANGELOG.md
```

## Ruff 基线维护

`.ruff-baseline.json` 记录当前历史 Ruff 问题的文件路径、行、列和规则编号。
CI 允许删除已有问题，但不允许增加或替换为新的问题身份。

仅在有意清理历史问题后刷新基线：

```bash
poetry run python script/check_ruff_baseline.py --update
poetry run python script/check_ruff_baseline.py
```

刷新时必须审查变更，确认基线条目数量没有增长；不得用刷新基线绕过新问题。

## 本地策略回归

修改 PTrade API、行情数据、订单执行、组合核算或缓存逻辑后，在本地运行：

```bash
poetry run python script/local_strategy_regression.py \
  --config .simtradelab-strategy-regression.json --all
```

策略清单、回测参数和人工审查的性能上限保存在本机配置中，不进入版本控制。默认
配置路径为仓库根目录的 `.simtradelab-strategy-regression.json`。示例结构如下；
策略键和配置值应替换为本机私有内容：

```json
{
  "schema_version": 1,
  "data_path": "data",
  "strategies_path": "strategies",
  "strategies": {
    "strategy_a": {
      "config": {
        "strategy_name": "strategy_a",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "frequency": "1d",
        "enable_charts": false,
        "enable_logging": false
      },
      "performance": {
        "execution_seconds_ceiling": 300,
        "wall_seconds_ceiling": 360
      }
    }
  }
}
```

相对路径以配置文件所在目录为基准。配置未指定数据或策略目录时，工具使用项目
默认目录；`SIMTRADELAB_DATA_PATH` 仍可覆盖默认数据目录。每个策略在独立子进程
运行，精确检查交易/净值指纹，并以显式容差检查报告指标。配置指纹包含策略源码；
数据指纹包含回测区间和实际依赖数据文件的相对路径、大小及完整 SHA-256，不包含
机器相关路径或修改时间。

`--all` 运行配置中的完整私有套件；`--strategy NAME` 只运行配置中对应的单个条目。

性能门槛只来自本机配置，不会根据最近一次慢运行自动放宽。子进程在墙钟上限之外
最多获得 30 秒启动余量；超时会清理整个 worker 进程树并返回非零状态。

默认基线、历史记录和数据校验缓存与配置文件同目录，文件名分别追加
`-baseline.json`、`-history.jsonl` 和 `-checksums.json`。默认配置及这些派生文件均
由 `.gitignore` 排除。可用 `--baseline PATH` 或 `--history PATH` 覆盖，覆盖路径也
必须保持为本机私有文件。临时不记录历史可加 `--no-history`。

只有在确认策略、固定配置或数据版本发生预期变化后，才能更新基线：

```bash
poetry run python script/local_strategy_regression.py \
  --config .simtradelab-strategy-regression.json --all --update-baseline
poetry run python script/local_strategy_regression.py \
  --config .simtradelab-strategy-regression.json --all
```

必须审查本机基线中的收益、交易数、指纹和性能上限；不得为绕过回归而静默接受
新结果。此检查只在本地发布/API 变更流程运行，不加入 GitHub Actions。配置文件
缺失时命令会明确报错，不会使用仓库内置策略或结果作为后备。

## 标准发布步骤

以发布 `2.10.2` 为例：

```bash
# 1) 执行版本准备（默认会先跑测试）
python script/release.py --version 2.10.2

# 2) 推送主分支
git push origin main
```

推送后无需手动打 tag，也无需手动上传 PyPI。CI 会自动完成。

## 进度与结果查看

- Actions 运行页：`https://github.com/kay-ou/SimTradeLab/actions`
- 发布流水线：`Auto Release`（`publish.yml`）
- PyPI 包页：`https://pypi.org/project/simtradelab/`
- GitHub Releases：`https://github.com/kay-ou/SimTradeLab/releases`

## 常用命令

```bash
# 跳过本地测试（仅在你已确认 CI 测试覆盖时使用）
python script/release.py --version 2.10.2 --skip-tests

# 查看当前版本
python - << 'PY'
import re, pathlib
txt = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
print(re.search(r'version\\s*=\\s*"([^"]+)"', txt).group(1))
PY

# 验证 tag 是否已存在
git tag --list "v2.10.2"
```

## 失败回滚策略

PyPI 不支持覆盖同版本重新发布。若发布失败或有问题：

1. 修复问题
2. 增加补丁版本（例如 `2.10.3`）
3. 重新执行发布流程

## 版本号建议（SemVer）

- PATCH（`x.y.Z`）：bugfix、文档修正、兼容性补丁
- MINOR（`x.Y.z`）：向后兼容的新功能
- MAJOR（`X.y.z`）：破坏性变更

当前已有 tag 到 `v2.10.1`，本次若为兼容修复，建议 `2.10.2`。
