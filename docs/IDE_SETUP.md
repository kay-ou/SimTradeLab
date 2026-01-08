# IDE 开发配置指南

本文档介绍如何配置 VS Code 和 PyCharm，获得最佳的 SimTradeLab 策略开发体验。

---

## 目录

- [功能概览](#功能概览)
- [类型提示（自动生效）](#类型提示自动生效)
- [代码片段（需手动配置）](#代码片段需手动配置)
- [VS Code 配置](#vs-code-配置)
- [PyCharm 配置](#pycharm-配置)
- [常见问题](#常见问题)

---

## 功能概览

SimTradeLab 提供完整的 IDE 智能提示支持，提升策略开发效率：

| 功能 | 说明 | 配置要求 |
|------|------|---------|
| **类型提示** | 函数签名、参数补全、文档悬停 | ✅ 自动生效（无需配置） |
| **代码片段** | 快速插入API调用模板 | ⚙️ 需手动配置 |
| **跳转到定义** | Ctrl+Click跳转到API实现 | ✅ 自动生效 |
| **参数提示** | 输入函数时自动显示参数 | ✅ 自动生效 |

---

## 类型提示（自动生效）

### 功能说明

项目内置 `typings/builtins.pyi` 存根文件，**VS Code 和 PyCharm 会自动识别**，无需额外配置！

### 支持的功能

✅ **鼠标悬停显示文档**
```python
get_history(...)  # 悬停显示完整函数签名和文档
```

✅ **输入时自动显示参数**
```python
get_history(  # 自动提示：count, frequency='1d', field='close', ...
```

✅ **跳转到定义**
```python
get_history(...)  # Ctrl+Click 跳转到 stub 文件查看完整定义
```

✅ **代码补全**
```python
get_  # 自动补全：get_history, get_price, get_fundamentals, ...
```

### 覆盖范围

类型提示覆盖 **52 个 PTrade API 函数**：

**交易API：**
- `order`, `order_target`, `order_value`, `order_target_value`
- `cancel_order`, `get_order`, `get_orders`, `get_open_orders`
- `get_position`, `get_trades`

**数据查询API：**
- `get_price`, `get_history`, `get_fundamentals`
- `get_stock_name`, `get_stock_info`, `get_stock_status`, `get_stock_exrights`
- `get_stock_blocks`, `get_index_stocks`, `get_industry_stocks`

**技术指标API：**
- `get_MACD`, `get_KDJ`, `get_RSI`, `get_CCI`

**配置API：**
- `set_benchmark`, `set_commission`, `set_slippage`, `set_fixed_slippage`
- `set_universe`, `set_limit_mode`, `set_volume_ratio`, `set_yesterday_position`

**工具API：**
- `log`, `is_trade`, `check_limit`, `get_trade_days`, `get_trading_day`

### 示例效果

**鼠标悬停显示：**
```python
get_history
───────────
def get_history(
    count: int,
    frequency: str = '1d',
    field: str | list[str] = 'close',
    security_list: str | list[str] = None,
    fq: str = None,
    include: bool = False,
    fill: str = 'nan',
    is_dict: bool = False
) -> pd.DataFrame | dict | PanelLike

获取指定股票的历史数据。

参数：
  count: 历史数据数量
  frequency: 数据频率（'1d'日线）
  field: 字段名（'close', 'open', 'high', 'low'等）
  security_list: 股票代码列表
  fq: 复权类型（'pre'前复权, None不复权）
  include: 是否包含当日数据
  fill: 缺失数据填充方式
  is_dict: 是否返回字典格式

返回：
  DataFrame或字典，包含历史数据
```

---

## 代码片段（需手动配置）

### 功能说明

代码片段让你快速插入常用 API 调用模板，提高编码效率。

### 下载片段文件

📎 **下载地址：** [ptrade-api.code-snippets](https://gist.github.com/kay-ou/8fb6dc68279bc40828a2f9fdf527fe90)

### 包含的片段

**数据获取：**
- `get_history` - 获取历史数据
- `get_fundamentals` - 获取基本面数据
- `get_price` - 获取历史价格
- `get_index_stocks` - 获取指数成分股

**交易操作：**
- `order_value` - 按金额下单
- `order_target` - 下单到目标数量

**市场分析：**
- `check_limit` - 检查涨跌停
- `get_stock_status` - 获取股票状态

**策略配置：**
- `set_benchmark` - 设置基准
- `set_slippage` - 设置滑点
- `set_fixed_slippage` - 设置固定滑点
- `set_commission` - 设置佣金

### 使用效果

输入 `get_h` → 自动补全为：
```python
hist = get_history(${1:20}, '1d', '${2:close}', [${3:stock}], is_dict=True)
```

按 `Tab` 在占位符间跳转，快速填写参数。

---

## VS Code 配置

### 1. 安装 Python 扩展

1. 打开 VS Code
2. 按 `Ctrl+Shift+X` 打开扩展面板
3. 搜索 `Python`
4. 安装 Microsoft 官方 Python 扩展

### 2. 配置代码片段

#### 方法A：工作区级别（推荐）

1. 在项目根目录创建 `.vscode` 文件夹（如果不存在）
2. 将下载的 `ptrade-api.code-snippets` 文件放到 `.vscode/` 目录
3. 重启 VS Code

**目录结构：**
```
SimTradeLab/
├── .vscode/
│   └── ptrade-api.code-snippets
├── src/
├── strategies/
└── ...
```

#### 方法B：用户级别

1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入 `Preferences: Configure User Snippets`
3. 选择 `python.json`
4. 将 `ptrade-api.code-snippets` 的内容复制粘贴进去
5. 保存文件

### 3. 配置 Python 解释器

1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入 `Python: Select Interpreter`
3. 选择虚拟环境中的 Python 解释器（例如 `./venv/bin/python`）

### 4. 配置 settings.json（可选）

创建 `.vscode/settings.json` 优化开发体验：

```json
{
  // Python 配置
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",

  // 类型检查
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,

  // 文件排除
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true
  },

  // 搜索排除
  "search.exclude": {
    "**/node_modules": true,
    "**/*.h5": true,
    "**/.venv": true
  }
}
```

### 5. 验证配置

打开策略文件 `strategies/my_strategy/backtest.py`，测试：

1. **类型提示：** 鼠标悬停 `get_history` 应显示函数签名
2. **代码补全：** 输入 `get_` 应自动补全 API 列表
3. **代码片段：** 输入 `get_h` 应显示片段提示

---

## PyCharm 配置

### 1. 配置 Python 解释器

1. 打开 `File` → `Settings`（Windows/Linux）或 `PyCharm` → `Preferences`（macOS）
2. 导航到 `Project: SimTradeLab` → `Python Interpreter`
3. 点击齿轮图标 → `Add`
4. 选择 `Existing environment`
5. 选择虚拟环境中的 Python 解释器
6. 点击 `OK`

### 2. 配置代码片段

#### 方法A：导入片段文件

1. 将 `ptrade-api.code-snippets` 转换为 PyCharm 格式（见下方转换脚本）
2. 打开 `File` → `Settings` → `Editor` → `Live Templates`
3. 点击右上角的齿轮图标 → `Import Settings`
4. 选择转换后的 XML 文件
5. 点击 `OK`

#### 方法B：手动创建片段

1. 打开 `File` → `Settings` → `Editor` → `Live Templates`
2. 点击 `+` → `Template Group`，创建 `PTrade API` 组
3. 选中 `PTrade API` 组，点击 `+` → `Live Template`
4. 填写片段信息：
   - **Abbreviation:** `get_h`（触发词）
   - **Description:** 获取历史数据
   - **Template text:**
     ```python
     hist = get_history($count$, '1d', '$field$', [$stocks$], is_dict=True)
     ```
5. 点击 `Define` → 勾选 `Python`
6. 点击 `OK`

### 3. VS Code 片段转 PyCharm 格式

使用以下 Python 脚本转换：

```python
import json
import xml.etree.ElementTree as ET

# 读取 VS Code 片段
with open('ptrade-api.code-snippets', 'r', encoding='utf-8') as f:
    snippets = json.load(f)

# 创建 PyCharm XML
root = ET.Element('templateSet', group='PTrade API')

for name, data in snippets.items():
    template = ET.SubElement(root, 'template',
                             name=name,
                             value=data['body'][0],
                             description=data.get('description', ''),
                             toReformat='true',
                             toShortenFQNames='true')
    context = ET.SubElement(template, 'context')
    ET.SubElement(context, 'option', name='PYTHON', value='true')

# 保存为 XML
tree = ET.ElementTree(root)
tree.write('ptrade-api.xml', encoding='utf-8', xml_declaration=True)
```

### 4. 配置代码风格（可选）

1. 打开 `File` → `Settings` → `Editor` → `Code Style` → `Python`
2. 调整缩进、行宽等设置
3. 点击 `OK`

### 5. 验证配置

打开策略文件，测试：

1. **类型提示：** `Ctrl+Q` 查看 `get_history` 的文档
2. **代码补全：** `Ctrl+Space` 触发自动补全
3. **代码片段：** 输入 `get_h` + `Tab` 插入片段

---

## 常见问题

### Q1: 类型提示不生效

**问题：** 鼠标悬停没有显示函数签名

**解决方案：**

**VS Code:**
```bash
# 1. 确认 Python 扩展已安装
# 2. 重新加载窗口
Ctrl+Shift+P → "Developer: Reload Window"

# 3. 检查 stub 文件是否存在
ls typings/builtins.pyi
```

**PyCharm:**
```bash
# 1. 清除缓存
File → Invalidate Caches / Restart → Invalidate and Restart

# 2. 确认解释器配置正确
File → Settings → Project → Python Interpreter
```

### Q2: 代码片段不显示

**问题：** 输入触发词没有提示

**解决方案：**

**VS Code:**
1. 检查文件是否放在 `.vscode/` 目录
2. 确认文件名为 `*.code-snippets`
3. 重启 VS Code

**PyCharm:**
1. 检查 Live Templates 是否已启用
2. 确认片段的 Context 设置为 Python
3. 尝试手动触发：`Ctrl+J`

### Q3: 跳转到定义不工作

**问题：** Ctrl+Click 无法跳转

**解决方案：**
```bash
# 确认 stub 文件路径正确
# VS Code: typings/builtins.pyi
# PyCharm: 应该自动识别

# 检查 Python 路径配置
import sys
print(sys.path)  # 应该包含项目根目录
```

### Q4: 性能问题（卡顿）

**问题：** IDE 运行缓慢

**解决方案：**

**VS Code:**
```json
// .vscode/settings.json
{
  // 减少索引范围
  "python.analysis.indexing": false,

  // 排除大文件
  "files.watcherExclude": {
    "**/*.h5": true,
    "**/__pycache__": true
  }
}
```

**PyCharm:**
1. `File` → `Settings` → `Project` → `Directories`
2. 将 `data/` 目录标记为 `Excluded`

---

## 推荐配置

### VS Code 推荐扩展

| 扩展 | 功能 | 安装命令 |
|------|------|---------|
| Python | Python 语言支持 | `code --install-extension ms-python.python` |
| Pylance | 高级类型检查 | `code --install-extension ms-python.vscode-pylance` |
| Jupyter | Jupyter Notebook 支持 | `code --install-extension ms-toolsai.jupyter` |
| GitLens | Git 历史查看 | `code --install-extension eamodio.gitlens` |

### PyCharm 推荐插件

| 插件 | 功能 | 安装方式 |
|------|------|---------|
| IdeaVim | Vim 编辑模式 | `File` → `Settings` → `Plugins` |
| Rainbow Brackets | 彩色括号 | `File` → `Settings` → `Plugins` |
| String Manipulation | 字符串处理 | `File` → `Settings` → `Plugins` |

---

## 下一步

- 📖 阅读 [快速开始](../README.md#快速开始)
- 🔧 查看 [工具脚本说明](TOOLS.md)
- 💻 参考 [开发规范](DEVELOPMENT_RULES.md)
- 🤝 贡献代码 [贡献指南](CONTRIBUTING.md)
