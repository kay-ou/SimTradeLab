# 更新日志

本项目的所有重要变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html) 规范。

## [2.4.2] - 2026-02-23

### 🐛 Bug 修复

- **pyarrow 依赖缺失** - 补入 `pyarrow>=10.0.0` 为必须依赖，修复 `pip install simtradelab` 后 Parquet 读写报 `ImportError` 的问题

### 📦 升级指南

```bash
pip install --upgrade simtradelab==2.4.2
```

**兼容性：** ✅ API 接口无 breaking change。

---

## [2.4.1] - 2026-02-23

### 🐛 Bug 修复

- **Windows 相对路径修复** - `DataServer` 的 `data_path` 参数现使用 `Path.resolve()` 转换为绝对路径，修复 Windows 下相对路径失效问题
- **Windows 路径自动发现** - `get_project_root()` 新增检查 `cwd.parent`，支持从子目录（如 `notebooks/`）运行时自动发现上级的 `data/` 和 `strategies/` 目录
- **路径常量懒加载** - `paths.py` 模块级常量改用 `__getattr__` 延迟计算，避免 import 时 CWD 错误导致路径固化；`Config.data_path` 属性每次动态调用 `get_project_root()`，不再缓存旧路径

### 📦 升级指南

```bash
pip install --upgrade simtradelab==2.4.1
```

**兼容性：** ✅ API 接口无 breaking change。

---

## [2.4.0] - 2026-02-21

### ✨ 新增功能

- **整手约束** - 买卖数量自动对齐至手数：A股100股，科创板200股最小申报量；调整后数量为0时自动拒单，与 PTrade 行为对齐
- **涨跌停检查** - 买入时检测涨停，卖出时检测跌停，命中则拒单
- **停牌检测** - volume=0 时视为停牌，拒绝所有买卖订单

### 🐛 Bug 修复

- **前复权公式修正** - 统一使用 `adj_a * price + adj_b` 公式（原 `(price - adj_b) / adj_a` 为错误公式），消除除法精度损失
- **舍入精度修正** - `_round2` 新增 TypeA（float64 低于真实 .XX5 时向上取整）和 Anti-TypeA（float64 高于 .XX5 一个 ULP、偶数第二位时向下取整）边界处理，精确匹配 PTrade 行为
- **资金不足前置检查** - 调整买入数量前先验证剩余资金，避免无效下单循环

### 🔧 改进

- **图表工具模块** - 提取 `utils/plot.py`，统一处理图表水印和保存，简化 `backtest/stats.py`
- **文档更新** - 补全 Parquet 存储相关文档，移除 HDF5 系统依赖说明，性能基准从 20-30x 更新为 100-160x

### 📦 升级指南

从 v2.3.0 升级：

```bash
pip install --upgrade simtradelab==2.4.0
```

**⚠️ 行为变更（可能影响回测结果）：**
- 整手约束现已生效：买入数量将自动向下取整（A股至100股，科创板至200股），与 PTrade 一致
- 前复权价格计算公式修正，复权价格数值会有细微差异

**兼容性：** ✅ API 接口无 breaking change。

---

## [2.3.0] - 2026-02-12

### ✨ 新增功能

- **沙箱模式** - 新增 `BacktestConfig(sandbox=True/False)` 配置。`sandbox=True`（默认）限制策略代码的 `import`（禁止 os/sys/io/subprocess 等）和 `builtins`（禁止 exec/eval/compile），与 PTrade 平台行为一致；`sandbox=False` 解除所有限制，适合本地开发调试
- **run_daily 实际执行** - `run_daily()` 不再是空操作，日频模式在每日收盘前执行，分钟模式在注册时间对应的分钟 bar 执行

### 🐛 Bug 修复

- **日期类型验证修正** - `BacktestConfig` 的 `start_date`/`end_date` 验证器简化为 `pd.Timestamp(v)`，不再限制只接受 `str` 和 `pd.Timestamp`，修复传入 `datetime.date` 等类型时的报错
- **估值数据查询日期修正** - `get_fundamentals` 对 valuation 表改用 `side='right'` 查找，返回查询日当天数据而非前一交易日
- **order_target_value 生命周期校验** - 补加 `@validate_lifecycle` 装饰器（此前缺失）
- **佣金零费率路径修正** - 移除 `calculate_commission` 中 `commission_ratio == 0` 的提前返回，统一走标准计算流程（确保 min_commission 仍生效）

### 🔧 改进

- **统计收集器重构** - `StatsCollector` 的内部存储从 `dict[str, list]` 重构为 `BacktestStats` 数据类，属性访问替代字典键查找
- **生命周期装饰器零开销优化** - `validate_lifecycle` 对全阶段 API（get_history/get_price 等）直接返回原函数，无任何包装开销；受限 API 仅做 `frozenset` 成员检查，移除 `RLock`、`Pydantic` 验证对象
- **日期索引 int64 化** - `get_stock_date_index` 用 `int64` 纳秒戳作为 dict key 和 numpy 数组做二分查找，避免 `pd.Timestamp` 构造开销
- **LRU 缓存替代手动淘汰** - `stock_status_cache`、`fundamentals_cache` 改用 `cachetools.LRUCache`，移除手动 `.clear()` 逻辑
- **前复权精度修正** - 新增 `_round2()` 函数，使用 Python `round()` 语义替代 `np.round()`，修正银行家舍入导致的与 PTrade 精度不一致
- **复权计算简化** - 移除从原始除权事件手动计算的 fallback 路径，统一使用平台预计算因子，代码量减少 ~60 行
- **交易 API 去重** - 提取 `_get_price_and_check_limit`、`_adjust_buy_amount`、`_submit_order` 三个内部方法，`order`/`order_target`/`order_value` 共用，消除大量重复代码
- **生命周期控制器精简** - 移除 `APICallRecord`、`LifecycleValidationResult`、调用历史记录、全局控制器等未使用功能，代码从 ~350 行缩减至 ~50 行
- **图表渲染优化** - 每日盈亏和交易金额改用 `fill_between` 替代 `bar`（无需 bar_width 参数）；`tight_layout()` 替代 `bbox_inches='tight'` 避免双重渲染
- **分钟 bar 生成优化** - 使用类级别预计算的时间偏移模板，避免每日重复调用 `pd.date_range`
- **Portfolio 收盘价日缓存** - 同一交易日内多次计算 `portfolio_value` 时复用收盘价查找结果
- **get_price/get_history 空结果日志** - 返回空时输出 warning 级别日志，便于排查数据问题
- **ta-lib 改为可选依赖** - `pip install simtradelab` 不再强制安装 ta-lib；需要技术指标时使用 `pip install simtradelab[indicators]`
- **清理死代码** - 移除 `importlib_metadata` fallback、`API_MODE_RESTRICTIONS`、`ptrade/__init__.py` 中未使用的导出等
- **Python 3.13 支持** - classifiers 新增 Python 3.13

### 🏗️ 基础设施

- **CI 工作流** - 添加同步 dev 分支的 GitHub Actions 工作流配置

### 📦 升级指南

从 v2.2.1 升级：

```bash
pip install --upgrade simtradelab==2.3.0
```

**兼容性：** ✅ 向后兼容，无 breaking change。

---

## [2.2.1] - 2026-02-09

### 🐛 Bug 修复

- **买入成本含佣金** - `cost_basis` 现在包含佣金，与 PTrade 实际行为对齐
- **除权事件处理修复** - 使用 `date` 列匹配替代索引查找，除权时同步调整 `cost_basis`
- **空数据快速报错** - `StockData` 数据为空时抛出明确 `ValueError`
- **日期类型修正** - 回测循环中确保 `current_date` 为 `pd.Timestamp`，避免 `datetime.date` 无法 `replace` 时间分量

### 🔧 改进

- **路径处理重构** - 使用 `Path` 对象替代字符串拼接，跨平台兼容
- **项目根目录查找优化** - 新增 CWD 优先检测，支持 `manifest.json` 判定
- **图表 x 轴自适应** - 根据回测时长自动选择年/季/月刻度间隔
- **控制台编码修正** - 使用 `reconfigure` 确保 UTF-8 编码和实时输出

### 📦 升级指南

从 v2.2.0 升级：

```bash
pip install --upgrade simtradelab==2.2.1
```

**兼容性：** ✅ 向后兼容，无 breaking change。

---

## [2.2.0] - 2026-02-07

### ✨ 新增功能

- **分钟线回测** - 支持 `frequency='1m'` 分钟级回测，需配合 `data/stocks_1m/` 分钟数据
- **API 增强** - 增强股票筛选和策略参数配置能力
- **Ptrade API 类型声明脚本** - `scripts/setup_typeshed.sh`，让 Pylance 识别策略中的 Ptrade API 全局函数

### 🔧 改进

- **回测图表中文化** - 图表标签从英文改为中文（策略净值、每日盈亏、买卖金额、持仓市值）
- **图表柱宽自适应** - 根据回测周期自动调整柱状图宽度
- **统计数据收集优化** - 改进 StatsCollector 数据采集流程
- **复权计算向量化** - `_apply_adj_factors` 替代逐行计算，提升性能
- **类型注解现代化** - 全面使用 `list[str]`、`dict[str, Any]`、`X | None` 等现代语法
- **发布工作流精简** - 移除冗余步骤，简化 CI 配置

### 📦 升级指南

从 v2.1.0 升级：

```bash
pip install --upgrade simtradelab==2.2.0
```

**兼容性：** ✅ 向后兼容，无 breaking change。分钟回测为新增功能，需额外准备分钟数据。

---

## [2.1.0] - 2026-01-30

### 🔧 改进

- **持仓更新逻辑优化** - 优化持仓更新和卖出验证流程
- **API 异常处理** - 优化异常处理和复权计算性能
- **订单字段规范化** - 订单处理中统一使用 `symbol` 替换 `stock` 字段

### ⚠️ 破坏性变更

- **数据保存格式变更** - 从 HDF5（.h5）改为 Parquet 格式，旧缓存需重建

---

## [2.0.0] - 2026-01-08

### ⚠️ 重大变更（Breaking Changes）

本版本包含重大变更，升级前请仔细阅读。

#### 📄 许可证变更

**从 MIT 更改为 AGPL-3.0 + 商业双许可模式**

- **开源使用**：AGPL-3.0 许可证
  - ✅ 免费用于开源项目
  - ✅ 个人学习和研究
  - ⚠️ 网络使用需开源（AGPL要求）

- **商业使用**：需购买商业许可
  - 用于商业/闭源产品
  - 作为内部工具但不希望开源代码
  - 需要技术支持和定制开发
  - 📧 联系: kayou@duck.com

**影响范围**：
- 现有开源项目：✅ 可继续使用（符合AGPL要求）
- 商业闭源项目：⚠️ 需购买商业许可或迁移到v1.x
- 个人学习研究：✅ 无影响

详见：[LICENSE](LICENSE) 和 [LICENSE-COMMERCIAL.md](LICENSE-COMMERCIAL.md)

#### 🔧 API Breaking Changes

**4个交易/查询API参数重命名（与PTrade官方规范对齐）**

| API | 旧参数名 | 新参数名 | 影响 |
|-----|---------|---------|------|
| `order_target` | `stock` | `security` | ⚠️ 关键字参数调用会报错 |
| `order_value` | `stock` | `security` | ⚠️ 关键字参数调用会报错 |
| `order_target_value` | `stock` | `security` | ⚠️ 关键字参数调用会报错 |
| `get_fundamentals` | `stocks` | `security` | ⚠️ 关键字参数调用会报错 |

**迁移示例：**

```python
# ❌ v1.x 写法（关键字参数）
order_target(stock='600519.SS', amount=1000)
order_value(stock='600519.SS', value=10000)
get_fundamentals(stocks=['600519.SS'], ...)

# ✅ v2.0 写法（推荐）
order_target(security='600519.SS', amount=1000)
order_value(security='600519.SS', value=10000)
get_fundamentals(security=['600519.SS'], ...)

# ✅ 位置参数不受影响（无需修改）
order_target('600519.SS', 1000)
order_value('600519.SS', 10000)
```

**兼容性说明：**
- ✅ 使用位置参数的代码：无需修改
- ⚠️ 使用关键字参数的代码：必须修改参数名
- ✅ `get_fundamentals` 现在支持单个股票和股票列表

**自动检测工具：**
```bash
# 扫描策略代码中使用旧参数名的位置
grep -n "stock=" strategies/*/backtest.py
grep -n "stocks=" strategies/*/backtest.py
```

### ✨ 新增功能

#### 📚 文档重构

**README 精简优化**
- 从 911 行压缩到 340 行（压缩 62.7%）
- 移除冗余的技术细节和重复内容
- 保留核心使用指南和快速开始流程
- 许可证说明提前到更显眼位置

**新增独立文档**
- `docs/INSTALLATION.md` - 详细安装指南
  - 多平台系统依赖安装（macOS/Linux/Windows）
  - 源码安装和PyPI安装方式
  - 工作目录配置和数据准备
  - 常见问题排查（Q&A 6条）

- `docs/ARCHITECTURE.md` - 架构设计文档
  - 核心模块职责说明
  - 性能优化详解（数据常驻、多级缓存、向量化计算）
  - 策略执行引擎设计
  - 生命周期管理机制
  - 持仓管理与分红税算法

- `docs/TOOLS.md` - 工具脚本说明
  - 参数优化框架（Optuna集成）
  - 性能监控工具（@timer装饰器）
  - 策略代码静态分析
  - Python 3.5兼容性检查

- `docs/IDE_SETUP.md` - IDE配置指南
  - VS Code 和 PyCharm 配置
  - 类型提示和代码片段
  - 开发环境优化

#### 📝 源码文件头

**统一的 SPDX 许可标识**

所有30个Python源文件添加标准化文件头：
```python
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (c) 2025 Kay
#
# This file is part of SimTradeLab, dual-licensed under AGPL-3.0 and a
# commercial license. See LICENSE-COMMERCIAL.md or contact kayou@duck.com
```

**影响文件：**
- `src/simtradelab/` 下所有 `.py` 文件（30个）
- 提升法律合规性和机器可读性
- 符合 SPDX 规范 2.3

### 🔧 改进

#### 🎯 API 设计优化

**统一参数命名**
- 交易API统一使用 `security` 参数（与PTrade官方一致）
- `get_fundamentals` 支持 `str | list[str]` 类型（更灵活）

#### 📖 贡献者协议

**完善 CLA 条款**
- 明确贡献者版权归属
- 说明开源许可和商业许可权利
- 提供清晰的贡献指南

详见：`docs/CONTRIBUTING.md`

### 📦 升级指南

#### 从 v1.x 升级到 v2.0.0

**重要提示：** 仔细评估许可证变更对您的项目的影响

```bash
# 1. 备份现有策略
cp -r strategies strategies_backup

# 2. 升级到新版本
pip install --upgrade simtradelab==2.0.0

# 3. 检查策略代码中的关键字参数
grep -rn "stock=" strategies/
grep -rn "stocks=" strategies/

# 4. 修改代码（如果使用了关键字参数）
# 将 stock= 改为 security=
# 将 stocks= 改为 security=

# 5. 运行回测验证
poetry run python -m simtradelab.backtest.run_backtest
```

#### 许可证选择决策树

```
是否用于网络服务（SaaS/Web应用）？
├─ 是 → 是否愿意开源所有代码？
│  ├─ 是 → ✅ 使用 AGPL-3.0（免费）
│  └─ 否 → ⚠️ 需购买商业许可
└─ 否 → 是否用于商业产品？
   ├─ 是 → 是否愿意开源产品代码？
   │  ├─ 是 → ✅ 使用 AGPL-3.0（免费）
   │  └─ 否 → ⚠️ 需购买商业许可
   └─ 否 → ✅ 使用 AGPL-3.0（个人学习/开源项目免费）
```

#### 版本选择建议

| 使用场景 | 推荐版本 | 许可证 |
|---------|---------|--------|
| 开源项目 | v2.0.0 | AGPL-3.0 |
| 个人学习研究 | v2.0.0 | AGPL-3.0 |
| 商业闭源产品 | v1.2.4 或购买商业许可 | MIT / Commercial |
| 内部工具（不开源） | v1.2.4 或购买商业许可 | MIT / Commercial |

**如果不确定：** 请联系 kayou@duck.com 获取许可证咨询

### ⚠️ 已知问题

无新增已知问题，继承 v1.2.0 的已知问题列表。

### 💡 贡献指南

**贡献者许可协议（CLA）：**
- 您拥有提交代码的完整版权
- 您同意按照 AGPL-3.0 许可证发布
- 您同意项目维护者有权用于商业许可授权

详见：`docs/CONTRIBUTING.md`

### 🔗 相关链接

- [完整 API 文档](docs/PTrade_API_Implementation_Status.md)
- [架构设计文档](docs/ARCHITECTURE.md)
- [安装指南](docs/INSTALLATION.md)
- [贡献指南](docs/CONTRIBUTING.md)
- [商业许可咨询](mailto:kayou@duck.com)

---

## [1.2.0] - 2025-11-30

### 🎉 重要更新

本版本主要修复了依赖缺失和CI/CD问题，完善了项目文档和API实现状态说明。

### ✨ 新增功能

#### 📦 依赖管理
- **添加核心依赖**
  - `cachetools ^5.3.0` - LRU缓存支持，提升性能
  - `joblib ^1.3.0` - 并行处理支持
  - `matplotlib ^3.7.0` - 图表绘制功能
  - `optuna ^3.0.0` - 参数优化器（可选依赖）

#### 📚 文档完善
- **新增PyPI发布指南** - 详细的发布流程和配置说明（`docs/PYPI_PUBLISHING_GUIDE.md`）
- **新增快速发布指南** - 简化的发布操作步骤（`RELEASE.md`）
- **完善README** - 添加详细的功能对比和项目状态说明
  - PTrade有的我们也有：52个核心API详细列表
  - PTrade没有我们有：独特的性能优化和智能功能
  - PTrade有我们还没有：99个待实现API清单

### 🔧 改进

#### 🏗️ 项目结构
- **版本号统一** - 同步`pyproject.toml`和`src/simtradelab/__init__.py`的版本号
- **添加`__version__`** - 在包根目录导出版本号
- **修正API数量** - 从56个修正为52个（移除未实现的API）

#### 📊 API实现状态
- **更新完成度统计**
  - 总体完成度：34%（52/151个API）
  - 回测场景：75%（49/65个API）
  - 研究场景：60%（35/58个API）
  - 交易场景：22%（15/67个API）
- **详细功能对比**
  - 核心交易功能：4个基础API
  - 数据查询功能：完整支持
  - 技术指标计算：100%完成（4个指标）
  - 策略配置：75%完成

#### 🎨 README优化
- **新增项目状态章节** - 清晰展示已完成和正在进行的工作
- **新增功能对比章节** - 详细对比PTrade和SimTradeLab的功能
- **新增待改进章节** - 坦诚说明已知问题和改进计划
  - 命令行/UI优化需求
  - 内存优化方案（8-12GB占用问题）
  - SimTradeData性能问题
  - 测试覆盖不全面的说明
- **更新项目结构** - 反映实际的代码组织
- **精简冗余内容** - 移除重复的示例和API列表

### 🐛 Bug修复

#### 🔨 GitHub Actions CI/CD
- **修复系统依赖安装问题**
  - Linux: 从源码编译安装ta-lib（Ubuntu仓库无libta-lib-dev包）
  - macOS: 添加TA_LIBRARY_PATH和TA_INCLUDE_PATH环境变量
  - Windows: 暂时跳过ta-lib安装（编译复杂）
- **简化CI矩阵** - 仅在Linux上运行自动CI（移除macOS/Windows以提升速度）
- **修复publish workflow逻辑** - 修正`release-build` job的条件判断
  - 之前：`if: ${{ !inputs.skip_tests || success() }}`（逻辑错误）
  - 现在：`if: ${{ always() && (inputs.skip_tests == true || needs.test.result == 'success') }}`
- **修复导入测试** - 使用正确的模块路径
  - 错误：`from simtradelab import BacktestEngine, Context`
  - 正确：`from simtradelab.backtest.runner import BacktestRunner`

#### 📝 文件修复
- **修复`__init__.py`编码问题** - 解决中文注释乱码（UTF-8编码）
- **更新poetry.lock** - 同步依赖锁文件

### 🚀 性能优化

#### ⚡ 缓存系统
- **LRU缓存优化** - 通过cachetools实现高效缓存管理
- **并行处理** - 通过joblib支持多进程并行计算

### 📖 文档

#### 新增文档
- `docs/PYPI_PUBLISHING_GUIDE.md` - 完整的PyPI发布指南
  - Trusted Publishing配置
  - 发布流程详解
  - 常见问题排查
- `RELEASE.md` - 快速发布操作指南
- `docs/PTrade_API_Implementation_Status.md` - API实现状态更新

#### 更新文档
- `README.md` - 大幅更新，增加功能对比和项目状态
- 各workflow文件的注释和说明

### ⚠️ 已知问题

- **测试覆盖不全** - 由于时间限制，主要通过实际策略发现和修复问题
- **内存占用较大** - 全量加载5000+股票需要8-12GB内存
- **SimTradeData性能** - 数据获取项目存在性能问题，需要优化
- **部分API不在范围内** - 以下为实盘交易API，不适用于回测框架
  - 融资融券：19个API（实盘交易）
  - 期货交易：7个API（实盘交易）
  - 期权交易：15个API（实盘交易）
  - 实时交易：高级交易、盘后交易、IPO申购等（实盘交易）

### 💡 贡献指南

欢迎社区参与：
- 报告bug和问题
- 实现缺失的API
- 优化性能和内存
- 完善文档和示例
- 分享策略和使用经验

详见：`docs/CONTRIBUTING.md`

### 📦 升级指南

从1.1.x升级到1.2.0：

```bash
# 升级到新版本
pip install --upgrade simtradelab==1.2.0

# 如需参数优化功能
pip install simtradelab[optimizer]==1.2.0
```

**重要变更：**
- 新增必需依赖：cachetools, joblib, matplotlib
- 版本号统一管理
- API数量从56个修正为52个

**兼容性：**
- ✅ 向后兼容 - 策略代码无需修改
- ✅ 数据格式兼容
- ✅ 配置文件兼容

---

## [1.1.1] - 2025-07-07

### 🐛 Bug修复
- 修复依赖错误

---

## [1.1.0] - 2025-07-07

### ✨ 新增功能
- 功能更新

---

## [1.0.0] - 2025-07-05

### 🎉 SimTradeLab 正式发布

**SimTradeLab** 是一个全新的开源策略回测框架，灵感来自PTrade的事件驱动模型，但拥有独立实现和扩展能力。

### 🎯 项目定位
- **开源框架**: 完全开源，避免商业软件的法律风险
- **独立实现**: 无需依赖PTrade，拥有自主知识产权
- **兼容设计**: 保持与PTrade语法习惯的兼容性
- **轻量清晰**: 提供轻量、清晰、可插拔的策略验证环境

### 🌟 重大功能新增

#### 📊 增强报告系统
- **多格式报告生成**: 支持TXT、JSON、CSV、HTML、摘要和图表等6种格式
- **HTML交互式报告**: 现代化网页界面，包含Chart.js图表和响应式设计
- **智能摘要报告**: 自动策略评级系统（优秀/良好/一般/较差）
- **可视化图表**: matplotlib生成的高质量收益曲线图
- **报告管理系统**: 完整的文件管理、清理和索引功能
- **策略分类存储**: 按策略名称自动组织报告到独立目录

#### 🌐 真实数据源集成
- **AkShare集成**: 支持A股实时行情数据，包含价格、成交量等交易信息
- **Tushare集成**: 专业金融数据接口支持（需要配置token）
- **智能数据源管理**: 主数据源失败时自动切换到备用数据源
- **配置管理**: 通过 `simtrade_config.yaml` 统一管理数据源配置

#### ⚡ 命令行工具
- **专业CLI**: 集成的 `simtradelab.cli` 模块，支持 `simtradelab` 命令
- **丰富参数支持**: 全面的参数配置，包括策略文件、数据源、股票代码、时间范围和初始资金
- **多种输出模式**: 详细、安静和普通输出模式，适应不同使用场景
- **智能验证**: 自动参数验证和用户友好的错误提示

### 🛠️ 引擎优化

#### 🔧 核心引擎改进
- **API注入修复**: 解决了类对象错误注入的问题，确保只注入函数对象
- **手续费函数更新**: 新的函数签名 `set_commission(commission_ratio=0.0003, min_commission=5.0, type="STOCK")`
- **性能分析增强**: 改进性能指标计算，对数据不足情况有更好的错误处理
- **兼容性提升**: 移除非标准API（如`on_strategy_end`），确保与ptrade完全兼容

#### 📊 策略改进
- **真实数据策略**: 新增 `real_data_strategy.py` 演示A股真实数据使用
- **智能回退机制**: 历史数据不足时自动切换到简单交易策略
- **详细交易日志**: 中文日志输出，便于策略调试和分析
- **持仓管理**: 修复持仓数据格式问题，支持字典格式的持仓信息

### 🔧 依赖管理
- **模块化依赖**: 将数据源依赖移至可选组，支持按需安装
- **版本冲突解决**: 修复akshare重复定义问题
- **简化安装**: 支持 `poetry install --with data` 安装数据源依赖

### 📚 文档更新
- **全面README**: 更新SimTradeLab 1.0功能、真实数据源使用和命令行工具文档
- **使用示例**: 添加CSV和真实数据源的完整代码示例
- **参数参考**: 详细的参数表格和使用场景
- **快速开始指南**: 为新用户简化入门流程

### 🧪 测试改进
- **真实数据测试**: 使用实际A股数据进行全面测试（平安银行、万科A、浦发银行）
- **CLI工具测试**: 全面的命令行界面测试，包含各种参数组合
- **错误处理**: 改进错误信息和边缘情况处理
- **报告系统测试**: 多格式报告生成和管理功能的完整测试

### 🔄 架构设计
- **包名**: 使用 `simtradelab` 作为包名，避免商标冲突
- **CLI集成**: 使用 `simtradelab.cli` 模块，支持 `simtradelab` 命令
- **配置文件**: 使用 `simtrade_config.yaml` 配置文件
- **标准API**: 移除非标准API，确保与PTrade语法兼容

### 🐛 问题修复
- 修复真实数据源的持仓数据访问问题
- 解决历史数据格式不一致问题
- 纠正API注入机制，防止类对象注入
- 修复手续费函数签名兼容性
- 清理所有非标准API引用

### 📈 性能改进
- 优化真实数据源的数据加载
- 改进大数据集的内存使用
- 增强错误处理和恢复机制
- 提升报告生成效率

---

## 🎯 项目历史

SimTradeLab 是从 ptradeSim 项目演进而来的全新开源框架。为了避免商标和法律风险，我们重新设计并发布了这个独立的开源项目。

### 主要改进
- **法律安全**: 避免商标冲突，拥有完全自主的知识产权
- **架构优化**: 更清晰的包结构和模块组织
- **功能完善**: 集成了多格式报告、真实数据源等高级功能
- **标准化**: 符合Python生态系统的最佳实践

### 兼容性说明
- ✅ **API兼容**: 保持与PTrade语法习惯的兼容性
- ✅ **策略兼容**: 现有策略文件可直接使用
- ✅ **数据兼容**: 支持相同的数据格式和配置
- ✅ **功能增强**: 在兼容基础上提供更多高级功能
