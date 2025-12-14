# 🚀 SimTradeLab 发布指南

## 📋 发布流程概述

使用 `scripts/release.py` 自动化发布流程：

```bash
# 完整发布流程（推荐）
python scripts/release.py --version 1.2.3 --skip-tests

# 仅构建测试
python scripts/release.py --build

# 预览模式（不执行实际操作）
python scripts/release.py --version 1.2.3 --dry-run
```

## 🎯 标准发布流程

### 1️⃣ 使用脚本自动发布

```bash
# 步骤1: 运行发布脚本
python scripts/release.py --version 1.2.3 --skip-tests

# 脚本自动执行：
# - 更新 pyproject.toml 版本号
# - 更新 README.md 版本号（badge、当前版本、安装示例）
# - 提交版本更新（commit message: "chore: bump version to 1.2.3"）
# - 创建 git tag v1.2.3

# 步骤2: 推送到远程
git push origin main
git push origin v1.2.3

# 步骤3: 在 GitHub 创建 Release
# 访问：https://github.com/kay-ou/SimTradeLab/releases/new
# - 选择标签: v1.2.3
# - 填写 Release 标题: SimTradeLab v1.2.3
# - 填写 Release 说明（参考下方模板）
# - 点击 "Publish release"

# 步骤4: GitHub Actions 自动构建并发布到 PyPI
# 监控构建进度：https://github.com/kay-ou/SimTradeLab/actions
```

### 2️⃣ Release 说明模板

```markdown
## 🎉 新功能
- [列出新增功能]

## 🔧 改进优化
- [列出改进项]

## 🐛 Bug修复
- [列出修复的问题]

## 📝 文档更新
- [列出文档更新]

## 📦 安装

### 基础安装
\`\`\`bash
pip install simtradelab==1.2.3
\`\`\`

### 包含优化器
\`\`\`bash
pip install simtradelab[optimizer]==1.2.3
\`\`\`

### 验证安装
\`\`\`bash
python -c "import simtradelab; print(simtradelab.__version__)"
\`\`\`
```

## 🛠️ release.py 使用说明

### 基本用法

```bash
# 更新版本号并创建标签
python scripts/release.py --version 1.2.3

# 更新版本号并创建标签（跳过测试）
python scripts/release.py --version 1.2.3 --skip-tests

# 更新版本号、创建标签、构建包
python scripts/release.py --version 1.2.3 --build

# 完整流程（更新、标签、构建、推送）
python scripts/release.py --version 1.2.3 --push
```

### 高级用法

```bash
# 仅创建标签（不更新版本号）
python scripts/release.py --tag-only

# 仅构建包
python scripts/release.py --build

# 预览模式（查看将执行的操作）
python scripts/release.py --version 1.2.3 --dry-run

# 查看帮助
python scripts/release.py --help
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--version X.Y.Z` | 指定新版本号（格式：x.y.z） |
| `--skip-tests` | 跳过测试步骤 |
| `--build` | 构建包（wheel + sdist） |
| `--push` | 推送到远程仓库 |
| `--tag-only` | 仅创建标签 |
| `--dry-run` | 预览模式 |

## 📦 GitHub Actions 自动发布

创建 GitHub Release 后，Workflow 自动执行：

1. ✅ **测试** - Python 3.9/3.10/3.11/3.12
2. ✅ **构建** - 安装系统依赖（HDF5, TA-Lib）→ 构建 wheel 和 tar.gz
3. ✅ **发布** - 使用 Trusted Publishing 发布到 PyPI
4. ✅ **验证** - 从 PyPI 安装并测试
5. ✅ **更新 Release Notes** - 自动生成并更新（使用 `scripts/generate_release_notes.py`）

监控进度：https://github.com/kay-ou/SimTradeLab/actions/workflows/publish.yml

### 自动生成 Release Notes

GitHub Actions 会自动调用 `scripts/generate_release_notes.py` 基于提交历史生成 Release Notes：
- 自动分类提交（新功能、Bug修复、文档更新等）
- 提取贡献者列表
- 生成统计信息

详细说明：`scripts/AUTO_RELEASE_NOTES_GUIDE.md`

## ✅ 发布后验证

```bash
# 等待 10-15 分钟后验证

# 1. 测试安装
pip install --upgrade simtradelab==1.2.3

# 2. 验证版本
python -c "import simtradelab; print(simtradelab.__version__)"
# 应输出: 1.2.3

# 3. 测试导入
python -c "
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.ptrade.context import Context
print('✅ 导入成功')
"

# 4. 查看 PyPI 页面
# https://pypi.org/project/simtradelab/
```

## ⚠️ 常见问题

### Q: 如何修改已发布的版本号？

**不能修改！**只能发布新版本：

```bash
# 如果发布了错误的版本（如 1.2.3），只能发布修正版本
python scripts/release.py --version 1.2.4
```

### Q: GitHub Actions 发布失败怎么办？

查看构建日志：https://github.com/kay-ou/SimTradeLab/actions/workflows/publish.yml

**常见错误：**

1. **测试失败**
   ```bash
   # 本地运行测试
   poetry install
   poetry run pytest tests/ -v
   ```

2. **构建失败（系统依赖）**
   - 检查 `.github/workflows/publish.yml` 中的依赖安装步骤
   - TA-Lib 从源码编译可能失败

3. **PyPI 发布失败**
   - 检查 Trusted Publishing 配置
   - 确认 pypi 环境存在
   - 查看 workflow 权限（id-token: write）

### Q: 如何在本地测试构建？

```bash
# 使用 release.py 测试构建
python scripts/release.py --build

# 手动构建
poetry build

# 检查构建结果
ls -lh dist/
```

### Q: 如何回滚发布？

**PyPI 不支持删除已发布版本**，只能发布新版本：

```bash
# 发布修复版本
python scripts/release.py --version 1.2.4
git push origin main
git push origin v1.2.4
# 在 GitHub 创建新 Release
```

## 📊 版本号规范

遵循语义化版本（SemVer）：

- **MAJOR.MINOR.PATCH**（如 1.2.3）
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

示例：
- 1.0.0 → 1.0.1（修复 bug）
- 1.0.1 → 1.1.0（新增功能）
- 1.1.0 → 2.0.0（破坏性变更）

## 🔧 配置说明

### PyPI 配置（已完成）

- ✅ PyPI 项目：https://pypi.org/project/simtradelab/
- ✅ Trusted Publishing 已配置
- ✅ GitHub 环境 `pypi` 已创建
- ✅ Workflow 权限已设置

### 本地配置

不需要本地 PyPI token，发布由 GitHub Actions 自动处理。

## 📝 发布检查清单

发布前确认：

- [ ] 代码已合并到 main 分支
- [ ] 所有测试通过
- [ ] 版本号已更新（通过 release.py 自动完成）
- [ ] CHANGELOG 已更新（如有）
- [ ] README 已更新（如有 API 变更）
- [ ] 文档已更新（如有重大变更）

发布后确认：

- [ ] Tag 已推送到远程
- [ ] GitHub Release 已创建
- [ ] GitHub Actions 构建成功
- [ ] PyPI 发布成功
- [ ] 本地可以安装新版本
- [ ] 导入测试通过

## 🎯 快速参考

```bash
# 标准发布流程（3 步）
python scripts/release.py --version X.Y.Z --skip-tests
git push origin main && git push origin vX.Y.Z
# 访问 GitHub 创建 Release

# 测试构建
python scripts/release.py --build

# 预览发布操作
python scripts/release.py --version X.Y.Z --dry-run
```

---

**详细文档：**
- GitHub Actions Workflow: `.github/workflows/publish.yml`
- Release 脚本源码: `scripts/release.py`
- PyPI 项目页面: https://pypi.org/project/simtradelab/
