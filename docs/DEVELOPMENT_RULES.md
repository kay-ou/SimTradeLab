### **SimTradeLab 开发核心规则 v1.1**

#### **1. 核心原则 (Core Principles)**

*   **架构先行，文档驱动 (Architecture First, Document-Driven)**
    *   在进行任何重要修改前，必须仔细阅读并深刻理解以下核心文档，以确保开发工作与项目蓝图保持一致：
        *   [`docs/PTrade_API_Summary.md`](docs/PTrade_API_Summary.md)
    *   所有开发活动必须严格遵守已定义的架构，保持代码的模块化、可扩展性和可维护性。

*   **杜绝技术债务 (Zero Tolerance for Technical Debt)**
    *   禁止为了短期便利而引入临时的、不完善的解决方案。必须深入分析问题根源，寻求长期、稳健的实现方式。

*   **彻底革新，不向后兼容 (Embrace Greenfield Development)**
    *   本项目为全新开发，不考虑向后兼容。发现过时或冗余的代码应立即予以删除，以确保测试能够尽早暴露新架构下的问题。兼容性设计会掩盖潜在缺陷，必须避免。

#### **2. 发布工作流 (Release Workflow)**

*   **版本发布步骤**
    1.  更新 `CHANGELOG.md`（手动）
    2.  运行发布脚本：`poetry run python scripts/release.py --version x.y.z --skip-tests`
    3.  Push dev 分支并创建 PR：`git push origin dev`
    4.  在 GitHub 上选择 **Rebase and merge**
    5.  **⚠️ 合并后必须同步本地 dev**（Rebase 会重写 commit hash，导致本地与远端分叉）：
        ```bash
        git fetch origin && git reset --hard origin/dev
        ```
    6.  CI 自动创建 tag、GitHub Release 并发布 PyPI

#### **3. 开发工作流 (Development Workflow)**

*   **代码复用优于重复实现 (Prioritize Reuse Over Reinvention)**
    *   在创建新功能或代码前，必须检查项目中是否已存在类似实现。若有，需向团队解释为何无法复用，并评估是否可以整合或删除冗余部分。

*   **重大变更需评审 (Review Required for Major Changes)**
    *   若计划对核心模块或项目结构进行大量修改，严禁擅自改动。必须先提交一份清晰的修改提案，详述改动理由、预期收益及潜在影响范围，获得批准后方可实施。

*   **统一的执行环境 (Consistent Execution Environment)**
    *   所有 Python 脚本的执行必须通过 Poetry 进行，以保证依赖环境的一致性。
    *   **正确方式**: `poetry run python your_script.py`
    *   **禁止方式**: `python your_script.py`

#### **3. 代码质量 (Code Quality)**

*   **遵循最佳实践 (Adhere to Best Practices)**
    *   严格遵循 Python 社区及 SimTradeLab 项目内部定义的编码规范与最佳实践。

*   **清晰的注释策略 (Clear Commenting Policy)**
    *   代码注释必须使用 **中文**，清晰地解释关键逻辑、设计决策和复杂算法。
    *   严禁在任何代码注释中提及架构文档的版本号（如 `v5.0`, `v5` 等），以避免信息过时带来的混淆。

*   **专业的代码风格 (Professional Code Style)**
    *   严禁在程序代码中使用任何 emoji 字符。仅允许在 Markdown 文档中（如 `README.md`）克制地使用，以增强可读性。

#### **4. 测试与数据 (Testing & Data)**

*   **测试服务于代码，而非相反 (Tests Serve Code, Not Vice Versa)**
    *   严禁为了让测试通过而修改核心业务逻辑，除非能证明核心代码本身存在缺陷。测试应真实反映代码的正确性。

*   **测试必须与时俱进 (Tests Must Evolve with Code)**
    *   当核心文件发生重大变更时，必须彻底重写或重构相应的测试用例，确保测试的有效性和覆盖率。

*   **严格的数据源管理 (Strict Data Source Management)**
    *   除 `Mock Data Plugin` 和单元测试场景外，项目任何地方都 **绝对不允许** 使用模拟数据（Mock Data）。所有功能都应基于真实或可复现的数据源进行开发和测试。
