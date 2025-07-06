# SimTradeLab Web 用户界面

<div align="center">

**🌐 直观的策略回测Web平台**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.1.3-purple.svg)](https://getbootstrap.com/)

*降低使用门槛，让更多用户体验量化交易的魅力*

</div>

## 🎯 功能特性

### 📊 回测结果可视化
- **收益曲线图表** - 直观展示策略表现
- **仓位变动分析** - 跟踪持仓变化
- **胜率指标统计** - 全面的绩效指标
- **风险指标展示** - 最大回撤、夏普比率等

### 📝 在线策略编辑器
- **语法高亮** - Python代码智能着色
- **实时保存** - 自动保存编辑内容
- **代码提示** - 智能代码补全
- **模板支持** - 预置策略模板

### 📁 数据源管理
- **多数据源支持** - CSV、AkShare、Tushare
- **文件上传** - 拖拽式文件上传
- **数据预览** - 查看数据格式和内容
- **源状态监控** - 实时数据源状态

### 🧪 批量参数测试
- **参数优化** - 多参数组合测试
- **并行执行** - 高效的批量测试
- **结果对比** - 可视化参数效果
- **最优选择** - 自动推荐最佳参数

### 🔧 后台API服务
- **RESTful API** - 标准化接口设计
- **异步处理** - 非阻塞任务执行
- **实时监控** - 任务进度实时更新
- **状态管理** - 完整的任务生命周期

## 🚀 快速开始

### 📦 安装依赖

```bash
# 使用poetry安装Web界面依赖
poetry install --with web
```

### ⚡ 启动Web界面

**方法一：使用启动脚本（推荐）**
```bash
# 在项目根目录下运行
python start_web.py
```

**方法二：直接启动**
```bash
# 启动后端服务
cd web/backend
python app.py

# 访问 http://localhost:8000
```

### 🌐 访问界面

启动成功后，浏览器会自动打开 `http://localhost:8000`

**重要链接：**
- 🏠 **主界面**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs
- 🔧 **交互式API**: http://localhost:8000/redoc

## 📋 界面功能详解

### 1. 仪表盘 📊
- **统计概览** - 策略数量、数据文件、运行任务等
- **最近任务** - 查看最新的回测和优化任务
- **系统状态** - 监控API和数据源状态
- **快速操作** - 一键刷新和快速导航

### 2. 策略管理 📝
- **策略列表** - 浏览所有已保存的策略
- **在线编辑** - 支持语法高亮的代码编辑器
- **即时保存** - 实时保存策略代码
- **模板创建** - 基于模板快速创建新策略

**预置策略模板：**
- 📈 双均线交叉策略
- 📉 RSI超买超卖策略
- 🔄 动量轮动策略
- 📊 技术指标组合策略

### 3. 数据管理 📁
- **数据源配置** - 管理CSV、AkShare、Tushare等数据源
- **文件上传** - 拖拽式CSV文件上传
- **数据预览** - 查看数据格式和字段信息
- **源状态监控** - 实时显示数据源可用性

### 4. 回测执行 ▶️
- **策略选择** - 从策略库中选择策略
- **参数配置** - 设置回测时间、资金、手续费等
- **数据源选择** - 选择CSV文件或在线数据
- **实时监控** - 查看回测进度和状态

### 5. 批量测试 🧪
- **参数范围** - 定义多个参数的取值范围
- **组合生成** - 自动生成所有参数组合
- **并行执行** - 高效的批量测试执行
- **结果分析** - 可视化展示优化结果

### 6. 结果分析 📊
- **任务列表** - 查看所有已完成的任务
- **可视化图表** - 收益曲线、风险指标等
- **性能指标** - 详细的回测性能统计
- **参数对比** - 批量测试结果对比

### 7. 报告中心 📄
- **报告文件** - 下载各种格式的回测报告
- **文件管理** - 按策略分类管理报告
- **格式支持** - TXT、JSON、CSV片等

## 🔧 API接口文档

### 策略管理 API
```
GET    /api/strategies          # 获取策略列表
GET    /api/strategies/{name}   # 获取特定策略
POST   /api/strategies          # 保存策略
DELETE /api/strategies/{name}   # 删除策略
```

### 数据管理 API
```
GET    /api/data/sources        # 获取数据源列表
GET    /api/data/files          # 获取数据文件列表
POST   /api/data/upload         # 上传数据文件
```

### 回测执行 API
```
POST   /api/backtest            # 启动回测
POST   /api/batch-test          # 启动批量测试
GET    /api/jobs                # 获取任务列表
GET    /api/jobs/{job_id}       # 获取任务状态
```

### 报告管理 API
```
GET    /api/reports             # 获取报告列表
GET    /api/reports/{strategy}/{file}  # 下载报告文件
```

## 💡 使用技巧

### 策略开发最佳实践
1. **从模板开始** - 使用预置模板快速上手
2. **增量开发** - 逐步完善策略逻辑
3. **充分测试** - 使用批量测试验证参数
4. **查看日志** - 通过日志了解策略执行过程

### 批量测试技巧
1. **合理设置参数范围** - 避免过大的参数空间
2. **使用有意义的参数值** - 基于实际经验设置参数
3. **关注多个指标** - 不只看收益率，还要看风险指标
4. **验证结果** - 用不同时间段验证最优参数

### 性能优化建议
1. **限制历史数据量** - 避免加载过多历史数据
2. **合理设置测试周期** - 平衡测试效果和计算时间
3. **清理旧任务** - 定期清理完成的任务节省内存
4. **监控系统资源** - 避免同时运行过多任务

## 🎨 界面定制

### 主题定制
Web界面使用Bootstrap 5框架，支持主题定制：

```css
/* 修改主色调 */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
}

/* 自定义侧边栏样式 */
.sidebar {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
}
```

### 组件扩展
可以轻松添加新的图表和可视化组件：

```javascript
// 添加新的图表类型
function createCustomChart(data, containerId) {
    const ctx = document.getElementById(containerId).getContext('2d');
    new Chart(ctx, {
        type: 'customType',
        data: data,
        options: customOptions
    });
}
```

## 🔒 安全考虑

### 数据安全
- **本地运行** - 所有数据在本地处理，不上传到外部服务器
- **文件隔离** - 上传文件存储在独立目录
- **权限控制** - 限制文件访问权限

### 代码安全
- **代码沙箱** - 策略代码在受限环境中执行
- **输入验证** - 所有用户输入都经过验证
- **错误处理** - 完善的异常处理机制

## 🛠️ 故障排除

### 常见问题

**Q: Web界面无法启动**
A: 检查是否安装了FastAPI和uvicorn依赖

```bash
pip install fastapi uvicorn
```

**Q: 策略执行失败**
A: 检查策略代码语法和数据文件格式

**Q: 批量测试卡住**
A: 检查参数范围设置，避免过大的组合数量

**Q: 图表不显示**
A: 检查浏览器是否支持Canvas和JavaScript

### 调试模式
启用调试模式获取更详细的错误信息：

```bash
# 设置调试模式
export DEBUG=1
python start_web.py
```

### 日志查看
查看详细的运行日志：

```bash
# 查看后端日志
tail -f logs/web_backend.log

# 查看策略执行日志
tail -f logs/strategy_execution.log
```

## 🤝 贡献指南

欢迎为Web界面贡献代码和建议！

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/kay-ou/SimTradeLab.git
cd SimTradeLab

# 安装开发依赖
poetry install --with dev,web

# 启动开发服务器
python start_web.py
```

### 贡献方式
1. **功能建议** - 在GitHub Issues中提出新功能建议
2. **Bug报告** - 报告发现的问题和错误
3. **代码贡献** - 提交Pull Request改进代码
4. **文档完善** - 帮助完善文档和教程

## 📚 相关资源

- 🏠 **项目主页**: [GitHub Repository](https://github.com/kay-ou/SimTradeLab)
- 📖 **完整文档**: [API参考文档](../docs/SIMTRADELAB_API_COMPLETE_REFERENCE.md)
- 🎓 **策略教程**: [策略开发指南](../docs/STRATEGY_GUIDE.md)
- 🔧 **技术文档**: [技术指标说明](../docs/TECHNICAL_INDICATORS.md)

---

<div align="center">

**🎉 享受可视化的量化交易体验！**

如有问题或建议，欢迎在 [GitHub Issues](https://github.com/kay-ou/SimTradeLab/issues) 中反馈

</div>