# 🚀 SimTradeLab PyPI发布快速指南

## ✅ 已有配置（无需重复）

之前已成功发布过3个版本（1.0.0, 1.1.0, 1.1.1），当前配置：

- ✅ PyPI项目已存在：https://pypi.org/project/simtradelab/
- ✅ Trusted Publishing已配置
- ✅ GitHub环境 `pypi` 已创建
- ✅ 发布workflow已就绪（已修复系统依赖）

## 📦 发布新版本（v1.2.0）

### 1️⃣ 准备发布

```bash
# 确认当前在main分支
git checkout main
git pull origin main

# 版本号已统一为1.2.0（pyproject.toml两处 + __init__.py）
grep "version" pyproject.toml
grep "__version__" src/simtradelab/__init__.py

# 如果需要修改版本号：
# vim pyproject.toml  # 修改 [project] version 和 [tool.poetry] version
# vim src/simtradelab/__init__.py  # 修改 __version__
```

### 2️⃣ 提交代码

```bash
# 提交所有修改（包括依赖修复）
git add .
git commit -m "chore: bump version to 1.2.0 and fix dependencies"
git push origin main
```

### 3️⃣ 创建Tag

```bash
# 创建并推送tag
git tag v1.2.0
git push origin v1.2.0
```

### 4️⃣ 创建GitHub Release

访问：https://github.com/kay-ou/SimTradeLab/releases/new

填写：
- **Choose a tag**: v1.2.0
- **Release title**: SimTradeLab v1.2.0
- **Description**:
  ```markdown
  ## 🎉 新功能
  - 添加缺失依赖（cachetools, joblib, matplotlib）
  - 优化器支持（可选安装 `pip install simtradelab[optimizer]`）

  ## 🐛 Bug修复
  - 修复GitHub Actions CI构建失败（HDF5/TA-Lib依赖）
  - 修复版本号不一致问题
  - 修复模块导入错误

  ## 📝 文档更新
  - 更新README，明确API实现状态（52个核心API，34%完成度）
  - 添加详细的功能对比和待改进说明
  - 添加PyPI发布指南

  ## 📦 安装
  ```bash
  pip install simtradelab==1.2.0

  # 包含优化器
  pip install simtradelab[optimizer]==1.2.0
  ```
  ```

点击 **"Publish release"** 按钮

### 5️⃣ 自动发布流程

发布后自动执行（约10-15分钟）：

1. ✅ **测试** - Python 3.10/3.11/3.12
2. ✅ **构建** - 安装系统依赖（HDF5, TA-Lib）→ 构建wheel和tar.gz
3. ✅ **发布** - 使用Trusted Publishing发布到PyPI
4. ✅ **验证** - 从PyPI安装并测试
5. ✅ **更新** - 自动生成Release Notes

### 6️⃣ 监控和验证

**查看构建进度：**
https://github.com/kay-ou/SimTradeLab/actions

**等待10-15分钟后验证：**
```bash
# 测试安装
pip install --upgrade simtradelab==1.2.0

# 验证版本
python -c "import simtradelab; print(simtradelab.__version__)"
# 应输出: 1.2.0

# 测试导入
python -c "
from simtradelab.backtest.runner import BacktestRunner
from simtradelab.ptrade.context import Context
print('✅ 导入成功')
"
```

**查看PyPI页面：**
https://pypi.org/project/simtradelab/

## 🔍 与之前版本的改进

相比v1.1.1，本次发布的关键改进：

1. **修复构建问题**
   - ✅ 添加系统依赖安装（HDF5, TA-Lib从源码编译）
   - ✅ 仅在Linux上运行CI（避免macOS/Windows编译问题）
   - ✅ 添加缺失的Python依赖

2. **完善依赖管理**
   - ✅ cachetools ^5.3.0（LRU缓存）
   - ✅ joblib ^1.3.0（并行处理）
   - ✅ matplotlib ^3.7.0（图表绘制）
   - ✅ optuna ^3.0.0（可选，参数优化）

3. **修复导入错误**
   - ✅ 添加 `__version__` 到包根目录
   - ✅ 修正所有CI中的导入路径

## ⚠️ 常见问题

### Q: 发布失败怎么办？

**查看构建日志：**
https://github.com/kay-ou/SimTradeLab/actions/workflows/publish.yml

**常见错误：**

1. **测试失败**
   ```bash
   # 本地运行测试
   poetry install
   poetry run pytest tests/ -v
   ```

2. **构建失败（系统依赖）**
   - 已修复：从源码编译ta-lib
   - 如仍有问题，手动触发workflow选择"Skip tests"

3. **PyPI发布失败**
   - 检查Trusted Publishing配置
   - 确认pypi环境存在
   - 查看workflow权限（id-token: write）

### Q: 如何回滚？

PyPI不支持删除已发布版本，只能发布新版本：

```bash
# 如果1.2.0有问题，发布1.2.1修复
vim pyproject.toml  # version = "1.2.1"
git tag v1.2.1
git push origin v1.2.1
# 创建新Release
```

### Q: 如何测试发布流程？

使用TestPyPI（需要单独配置）：

```bash
# 修改publish.yml中的PyPI URL
# repository-url: https://test.pypi.org/legacy/

# 测试安装
pip install --index-url https://test.pypi.org/simple/ simtradelab
```

## 📊 版本历史

| 版本 | 发布日期 | 主要变更 |
|------|---------|---------|
| 1.2.0 | 待发布 | 修复依赖、CI、导入错误 |
| 1.1.1 | 2025-07-07 | 修复依赖错误 |
| 1.1.0 | 2025-07-07 | 功能更新 |
| 1.0.0 | 2025-07-05 | 首次正式发布 |

## 🎯 下次发布准备

发布后需要：

- [ ] 验证PyPI安装正常
- [ ] 更新文档（如有API变更）
- [ ] 通知用户更新（如有重大变更）
- [ ] 规划下一版本功能
- [ ] 开始1.3.0开发分支

---

**详细文档：** `docs/PYPI_PUBLISHING_GUIDE.md`
