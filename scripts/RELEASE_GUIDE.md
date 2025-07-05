# simtradelab 发布指南

本指南详细说明如何发布 simtradelab 的新版本到 GitHub 和 PyPI。

## 📋 发布前准备

### 1. 确保代码质量

```bash
# 运行所有测试
poetry run pytest tests/ -v

# 检查代码格式（可选）
poetry run black simtradelab/
poetry run flake8 simtradelab/
```

### 2. 更新版本信息

1. **更新 `pyproject.toml` 中的版本号**
2. **更新 `CHANGELOG.md`** - 添加新版本的更新内容
3. **更新 `README.md`** - 确保文档反映最新功能

### 3. 提交所有更改

```bash
git add .
git commit -m "chore: prepare for v1.0.0 release"
git push origin main
```

## 🚀 自动化发布流程

### 使用发布脚本（推荐）

发布脚本支持多种模式，可以根据需要选择：

```bash
# 完整发布流程（默认，包含测试）
poetry run python scripts/release.py

# 跳过测试的快速发布
poetry run python scripts/release.py --skip-tests

# 预览模式（检查流程但不执行）
poetry run python scripts/release.py --dry-run

# 跳过测试的预览模式
poetry run python scripts/release.py --skip-tests --dry-run

# 查看帮助信息
poetry run python scripts/release.py --help
```

#### 📋 参数说明

| 参数 | 说明 | 使用场景 |
|------|------|----------|
| `--skip-tests` | 跳过测试步骤 | 快速发布，节省时间 |
| `--dry-run` | 预览模式 | 检查发布流程，不执行实际操作 |
| `--help` | 显示帮助 | 查看使用方法和参数说明 |

#### 🔄 发布流程对比

**完整流程（默认）**：
1. 获取版本信息 ✅
2. 检查Git状态 ✅
3. 运行测试 ✅
4. 构建包 ✅
5. 创建Git标签 ✅
6. 生成发布说明 ✅

**跳过测试流程**：
1. 获取版本信息 ✅
2. 检查Git状态 ✅
3. 运行测试 ⏭️ (跳过)
4. 构建包 ✅
5. 创建Git标签 ✅
6. 生成发布说明 ✅

**预览模式**：
1. 获取版本信息 ✅
2. 检查Git状态 🔍 (预览)
3. 运行测试 🔍 (预览)
4. 构建包 🔍 (预览)
5. 创建Git标签 🔍 (预览)
6. 生成发布说明 🔍 (预览)

#### 🎯 使用场景

**1. 快速发布**
```bash
# 当您确信代码质量没问题，想要快速发布时
poetry run python scripts/release.py --skip-tests
```

**2. 预览检查**
```bash
# 检查发布流程是否正确，但不实际执行
poetry run python scripts/release.py --dry-run
```

**3. 调试发布流程**
```bash
# 调试发布流程，跳过测试以节省时间
poetry run python scripts/release.py --skip-tests --dry-run
```

**4. 完整发布**
```bash
# 正式发布时，运行完整流程（推荐）
poetry run python scripts/release.py
```

## 📦 手动发布流程

如果需要手动控制发布过程：

### 1. 构建包

```bash
# 清理之前的构建
rm -rf dist/ build/ *.egg-info/

# 构建包
poetry build

# 验证构建结果
ls -la dist/
```

### 2. 测试包

```bash
# 运行包测试脚本
python scripts/test-package.py
```

### 3. 创建Git标签

```bash
# 创建标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送标签
git push origin v1.0.0
```

## 🌐 GitHub Release

### 1. 创建Release

1. 访问 [GitHub Releases页面](https://github.com/kay-ou/SimTradeLab/releases/new)
2. 选择刚创建的标签 `v1.0.0`
3. 填写Release标题: `simtradelab v1.0.0 - 真实数据源集成与引擎优化`

### 2. 发布说明

使用 `scripts/github-release-template.md` 作为发布说明模板，或者使用自动生成的 `release-notes-v1.0.0.md`。

### 3. 上传文件

上传 `dist/` 目录中的所有文件：
- `simtradelab-1.0.0-py3-none-any.whl`
- `simtradelab-1.0.0.tar.gz`

### 4. 发布

点击 "Publish release" 完成GitHub Release。

## 📦 PyPI 发布（可选）

### 1. 配置PyPI凭据

```bash
# 配置PyPI token（首次）
poetry config pypi-token.pypi your-pypi-token

# 或使用用户名密码
poetry config http-basic.pypi your-username your-password
```

### 2. 发布到PyPI

```bash
# 发布到PyPI
poetry publish

# 或者先发布到TestPyPI测试
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
```

### 3. 验证发布

```bash
# 从PyPI安装并测试
pip install simtradelab==1.0.0

# 测试基本功能
python -c "import simtradelab; print('安装成功')"
```

## 🔍 发布后验证

### 1. GitHub Release验证

- ✅ Release页面显示正确
- ✅ 下载链接工作正常
- ✅ 发布说明完整

### 2. 包安装验证

```bash
# 创建新的虚拟环境测试
python -m venv test_env
source test_env/bin/activate  # Linux/macOS
# 或 test_env\Scripts\activate  # Windows

# 安装并测试
pip install simtradelab==1.0.0
python -c "from simtradelab import BacktestEngine; print('导入成功')"
```

### 3. 命令行工具验证

```bash
# 测试命令行工具
simtradelab --help
```

## 📋 发布检查清单

发布前请确认：

- [ ] 所有测试通过
- [ ] 版本号已更新
- [ ] CHANGELOG.md已更新
- [ ] README.md已更新
- [ ] 代码已提交并推送
- [ ] 包构建成功
- [ ] 包测试通过
- [ ] Git标签已创建
- [ ] GitHub Release已发布
- [ ] PyPI发布（如需要）
- [ ] 发布后验证完成

## 🐛 常见问题

### 测试失败

如果测试失败，可以：

1. **修复测试问题后重新运行**（推荐）
2. **跳过测试继续发布**（确认代码质量的情况下）：

```bash
# 跳过测试继续发布
poetry run python scripts/release.py --skip-tests
```

### 发布脚本问题

**查看帮助信息**：
```bash
poetry run python scripts/release.py --help
```

**预览发布流程**：
```bash
# 检查发布流程但不执行实际操作
poetry run python scripts/release.py --dry-run
```

**调试模式**：
```bash
# 跳过测试的预览模式，快速检查流程
poetry run python scripts/release.py --skip-tests --dry-run
```

### 构建失败

```bash
# 清理并重新构建
rm -rf dist/ build/ *.egg-info/
poetry install
poetry build
```

### 标签已存在

```bash
# 删除本地标签
git tag -d v1.0.0

# 删除远程标签
git push origin :refs/tags/v1.0.0

# 重新创建标签
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### PyPI发布失败

```bash
# 检查包名是否冲突
pip search simtradelab

# 使用不同的包名
# 在pyproject.toml中修改name字段
```

## 📞 获取帮助

如果遇到问题：

1. 检查 [Poetry文档](https://python-poetry.org/docs/)
2. 查看 [PyPI发布指南](https://packaging.python.org/tutorials/packaging-projects/)
3. 参考 [GitHub Releases文档](https://docs.github.com/en/repositories/releasing-projects-on-github)

---

**祝发布顺利！** 🎉
