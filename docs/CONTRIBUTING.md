# 贡献指南

欢迎社区贡献代码、报告问题或提出改进建议。我们致力于打造一个开放、协作的开发环境。

## 如何贡献

1.  **Fork项目** - 在GitHub上fork项目到您自己的仓库。
2.  **创建分支** - 从 `main` 分支创建一个新分支来进行您的修改：
    ```bash
    git checkout -b feature/your-new-feature
    ```
3.  **提交代码** - 进行修改并提交您的代码。请遵循下面的 `git commit` 最佳实践。
    ```bash
    git commit -m 'feat: 添加了某个很棒的功能'
    ```
4.  **推送分支** - 将您的分支推送到您的fork仓库：
    ```bash
    git push origin feature/your-new-feature
    ```
5.  **提交PR** - 在SimTradeLab的GitHub仓库页面上创建一个Pull Request，详细描述您的修改内容。

## Git Commit 最佳实践

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范，这有助于我们自动化生成更新日志和更好地管理项目历史。

### Commit 消息格式

每个 commit 消息都由一个 **header**, 一个 **body** 和一个 **footer** 组成。

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Commit 类型

请使用以下类型之一作为 commit 的前缀：

| 类型     | 用途说明                     | 示例                               |
| :------- | :--------------------------- | :--------------------------------- |
| `feat`   | 新功能                       | `feat: 添加策略回测模块`           |
| `fix`    | Bug 修复                     | `fix: 修复数据源连接失败问题`      |
| `docs`   | 文档更新                     | `docs: 更新API使用说明`            |
| `style`  | 代码格式调整（无逻辑变更）   | `style: 格式化回测结果展示代码`    |
| `refactor` | 重构（非功能变更）           | `refactor: 重构任务调度逻辑`       |
| `test`   | 添加或修改测试               | `test: 增加策略回测单元测试`       |
| `chore`  | 构建工具或依赖更新           | `chore: 升级pandas版本`            |

### 问题反馈

-   **Bug报告**: [GitHub Issues](https://github.com/kay-ou/SimTradeLab/issues)
-   **功能请求**: [GitHub Issues](https://github.com/kay-ou/SimTradeLab/issues)
-   **使用问题**: [GitHub Discussions](https://github.com/kay-ou/SimTradeLab/discussions)

感谢您的贡献！