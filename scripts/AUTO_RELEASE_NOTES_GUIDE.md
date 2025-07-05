# 🤖 自动生成Release Notes指南

## 📋 概述

SimTradeLab现在支持自动生成Release Notes，基于Git提交历史、CHANGELOG.md和GitHub API自动创建格式化的发布说明。

## 🔧 实现方式

### 1. **多种触发方式**

#### 自动触发
- **创建Git标签时**: 推送标签到仓库时自动生成
- **发布流程中**: 在publish.yml工作流中自动集成
- **本地发布脚本**: release.py脚本中自动调用

#### 手动触发
- **GitHub Actions**: 在Actions页面手动运行release-notes工作流
- **本地命令**: 直接运行生成脚本

### 2. **智能内容分析**

#### 提交信息分类
根据Conventional Commits规范自动分类：
- `feat:` → 新增功能
- `fix:` → 问题修复  
- `docs:` → 文档更新
- `perf:`, `refactor:` → 改进优化
- `BREAKING CHANGE` → 破坏性变更

#### CHANGELOG.md集成
- 优先使用CHANGELOG.md中的内容
- 自动解析版本章节
- 按类型分组显示

#### Git历史分析
- 自动统计提交数量
- 识别贡献者列表
- 计算文件变更数量

## 🚀 使用方法

### 1. **本地生成**

```bash
# 基本用法
python scripts/generate_release_notes.py v1.0.0

# 保存到文件
python scripts/generate_release_notes.py v1.0.0 --output release_notes.md

# 打印到控制台
python scripts/generate_release_notes.py v1.0.0 --print
```

### 2. **集成到发布流程**

```bash
# 使用发布脚本（自动调用）
poetry run python scripts/release.py

# 跳过测试的快速发布
poetry run python scripts/release.py --skip-tests
```

### 3. **GitHub Actions自动化**

#### 推送标签触发
```bash
git tag v1.0.0
git push origin v1.0.0
# 自动生成Release Notes并创建GitHub Release
```

#### 手动触发
1. 进入GitHub仓库的Actions页面
2. 选择"Generate Release Notes"工作流
3. 点击"Run workflow"
4. 输入标签名称（如v1.0.0）
5. 选择是否创建GitHub Release

## 📝 模板自定义

### 1. **修改模板文件**

编辑 `.github/release-template.md` 来自定义格式：

```markdown
# 🎉 SimTradeLab {{tag_name}} 发布

## ✨ 新增功能
{{new_features}}

## 🔧 改进优化  
{{improvements}}

## 🐛 问题修复
{{bug_fixes}}

## 📦 安装方法
```bash
pip install simtradelab=={{version}}
```
```

### 2. **可用变量**

| 变量 | 说明 | 示例 |
|------|------|------|
| `{{tag_name}}` | Git标签名 | v1.0.0 |
| `{{version}}` | 版本号 | 1.0.0 |
| `{{release_date}}` | 发布日期 | 2025-07-05 |
| `{{previous_tag}}` | 上一个标签 | v0.9.0 |
| `{{commit_count}}` | 提交数量 | 25 |
| `{{contributor_count}}` | 贡献者数量 | 3 |
| `{{files_changed}}` | 变更文件数 | 15 |
| `{{new_features}}` | 新增功能列表 | - 添加新API |
| `{{improvements}}` | 改进列表 | - 优化性能 |
| `{{bug_fixes}}` | 修复列表 | - 修复bug |
| `{{documentation}}` | 文档更新 | - 更新README |
| `{{breaking_changes}}` | 破坏性变更 | - 移除旧API |
| `{{contributors}}` | 贡献者列表 | @user1, @user2 |

## 📋 最佳实践

### 1. **提交信息规范**

使用Conventional Commits格式：
```bash
feat: 添加新的数据源支持
fix: 修复CLI参数解析问题
docs: 更新API文档
perf: 优化数据处理性能
BREAKING CHANGE: 移除废弃的API
```

### 2. **CHANGELOG.md维护**

保持CHANGELOG.md格式一致：
```markdown
## [1.0.0] - 2025-07-05

### 新增功能
- 添加AkShare数据源支持
- 新增CLI命令行工具

### 问题修复
- 修复数据加载问题
- 解决内存泄漏
```

### 3. **版本标签规范**

使用语义化版本标签：
```bash
v1.0.0    # 正式版本
v1.0.0-rc.1  # 候选版本
v1.0.0-beta.1  # 测试版本
v1.0.0-alpha.1  # 预览版本
```

## 🔧 配置选项

### 1. **脚本参数**

```bash
python scripts/generate_release_notes.py --help

usage: generate_release_notes.py [-h] [--output OUTPUT] [--print] tag

positional arguments:
  tag                   Git标签名称

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        输出文件路径
  --print, -p           打印到控制台
```

### 2. **GitHub Actions配置**

在 `.github/workflows/release-notes.yml` 中可以配置：
- 触发条件
- Python版本
- 输出格式
- 通知设置

## 🎯 高级功能

### 1. **自动Release创建**

- 推送标签时自动创建GitHub Release
- 自动设置预发布标记（alpha/beta/rc）
- 自动上传构建产物

### 2. **PR关联**

- 自动在相关PR中添加发布通知
- 链接到具体的Release页面
- 追踪功能实现进度

### 3. **多格式输出**

- Markdown格式（GitHub Release）
- 纯文本格式（邮件通知）
- JSON格式（API集成）

## 🐛 故障排除

### 常见问题

#### 1. **生成失败**
```bash
# 检查Git历史
git log --oneline

# 检查标签
git tag -l

# 手动运行脚本
python scripts/generate_release_notes.py v1.0.0 --print
```

#### 2. **内容为空**
- 检查CHANGELOG.md格式
- 确认提交信息格式
- 验证标签是否存在

#### 3. **GitHub Actions失败**
- 检查权限设置
- 验证工作流语法
- 查看详细日志

### 调试模式

```bash
# 详细输出
python scripts/generate_release_notes.py v1.0.0 --print --verbose

# 检查模板
cat .github/release-template.md

# 验证Git信息
git describe --tags --abbrev=0
```

## 🎉 总结

自动生成Release Notes功能提供了：

- ✅ **自动化**: 减少手动工作
- ✅ **一致性**: 统一的格式和风格  
- ✅ **智能化**: 基于提交历史智能分类
- ✅ **集成性**: 与现有工作流无缝集成
- ✅ **可定制**: 灵活的模板和配置

现在您可以专注于开发，让工具自动处理发布说明的生成！🚀
