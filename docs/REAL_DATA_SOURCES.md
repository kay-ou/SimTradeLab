# 📊 ptradeSim 真实数据源接入指南

## 概述

ptradeSim 现在支持多种真实数据源，让您可以使用真实的股票数据进行回测和策略开发。支持的数据源包括：

- **CSV文件**：离线数据，向后兼容
- **Tushare**：专业的中国股市数据源
- **AkShare**：免费开源的金融数据接口

## 🚀 快速开始

### 1. 安装依赖

```bash
# 基础依赖（已包含）
pip install pandas PyYAML

# Tushare数据源（可选）
pip install tushare

# AkShare数据源（可选）
pip install akshare
```

### 2. 基本使用

#### 使用CSV数据源（向后兼容）

```python
from ptradesim import BacktestEngine

# 传统方式，完全向后兼容
engine = BacktestEngine(
    strategy_file='strategies/my_strategy.py',
    data_path='data/sample_data.csv',
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=1000000
)

engine.run()
```

#### 使用Tushare数据源

```python
from ptradesim import BacktestEngine

# 设置环境变量
import os
os.environ['TUSHARE_TOKEN'] = 'your_token_here'

# 使用Tushare数据源
engine = BacktestEngine(
    strategy_file='strategies/my_strategy.py',
    data_source='tushare',
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=1000000,
    securities=['000001.SZ', '000002.SZ', '600000.SH']
)

engine.run()
```

#### 使用AkShare数据源

```python
from ptradesim import BacktestEngine

# 使用AkShare数据源（无需token）
engine = BacktestEngine(
    strategy_file='strategies/my_strategy.py',
    data_source='akshare',
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=1000000,
    securities=['000001', '000002', '600000']  # 6位代码
)

engine.run()
```

## ⚙️ 配置管理

### 配置文件

创建 `ptrade_config.yaml` 文件：

```yaml
data_sources:
  default: tushare
  
  csv:
    data_path: "./data/sample_data.csv"
  
  tushare:
    token: "your_token_here"
    cache_dir: "./cache/tushare"
    cache_enabled: true
  
  akshare:
    cache_dir: "./cache/akshare"
    cache_enabled: true

cache:
  enabled: true
  ttl: 3600
```

### 使用配置文件

```python
from ptradesim import BacktestEngine, load_config

# 加载配置
config = load_config('ptrade_config.yaml')

# 使用配置创建引擎
engine = BacktestEngine(
    strategy_file='strategies/my_strategy.py',
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=1000000,
    securities=['000001.SZ', '000002.SZ']
)
```

## 🔧 高级用法

### 自定义数据源

```python
from ptradesim import BacktestEngine
from ptradesim.data_sources import TushareDataSource

# 创建自定义数据源
data_source = TushareDataSource(
    token='your_token',
    cache_enabled=True,
    cache_dir='./my_cache'
)

# 使用自定义数据源
engine = BacktestEngine(
    strategy_file='strategies/my_strategy.py',
    data_source=data_source,
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=1000000,
    securities=['000001.SZ']
)
```

### 数据源管理器

```python
from ptradesim.data_sources import DataSourceManager, TushareDataSource, CSVDataSource

# 创建主数据源和备用数据源
primary = TushareDataSource(token='your_token')
fallback = CSVDataSource(data_path='data/backup.csv')

# 创建数据源管理器
manager = DataSourceManager(primary, [fallback])

# 使用管理器
engine = BacktestEngine(
    strategy_file='strategies/my_strategy.py',
    data_source=manager,
    start_date='2023-01-01',
    end_date='2023-12-31',
    initial_cash=1000000
)
```

## 📋 数据源对比

| 数据源 | 优点 | 缺点 | 适用场景 |
|--------|------|------|----------|
| CSV文件 | 离线、快速、稳定 | 数据需要手动更新 | 历史回测、开发测试 |
| Tushare | 数据全面、质量高 | 需要注册、有调用限制 | 专业量化、实盘策略 |
| AkShare | 免费、开源 | 数据源不稳定 | 学习研究、快速验证 |

## 🔑 Tushare 配置

### 1. 注册账号

访问 [Tushare官网](https://tushare.pro) 注册账号并获取token。

### 2. 设置Token

方法一：环境变量（推荐）
```bash
export TUSHARE_TOKEN=your_token_here
```

方法二：配置文件
```yaml
data_sources:
  tushare:
    token: "your_token_here"
```

### 3. 股票代码格式

Tushare使用带交易所后缀的格式：
- 深交所：`000001.SZ`
- 上交所：`600000.SH`

## 📊 AkShare 使用

### 特点

- 免费开源
- 无需注册
- 支持多种数据源

### 股票代码格式

AkShare通常使用6位数字代码：
- `000001`（平安银行）
- `600000`（浦发银行）

## 🚨 注意事项

### 1. API限制

- **Tushare**：有调用频率限制，建议启用缓存
- **AkShare**：部分接口有反爬限制，请合理使用

### 2. 数据质量

- 真实数据可能包含停牌、除权等情况
- 建议在策略中添加数据验证逻辑

### 3. 网络依赖

- 在线数据源需要网络连接
- 建议配置重试机制和缓存

### 4. 缓存管理

```python
# 清空缓存
engine.data_source_manager.clear_cache()

# 检查数据源状态
status = engine.data_source_manager.get_source_status()
print(status)
```

## 🔍 故障排除

### 常见问题

1. **Tushare token错误**
   ```
   解决：检查token是否正确设置
   ```

2. **网络连接失败**
   ```
   解决：检查网络连接，或使用CSV备用数据源
   ```

3. **股票代码格式错误**
   ```
   解决：确认使用正确的代码格式（Tushare需要后缀）
   ```

4. **数据获取失败**
   ```
   解决：检查日期范围，确保在交易日内
   ```

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 运行引擎查看详细日志
engine.run()
```

## 📈 性能优化

### 1. 启用缓存

```yaml
cache:
  enabled: true
  ttl: 3600  # 1小时缓存
```

### 2. 批量获取

```python
# 一次获取多只股票
securities = ['000001.SZ', '000002.SZ', '600000.SH']
```

### 3. 合理的日期范围

```python
# 避免过长的时间范围
start_date = '2023-01-01'
end_date = '2023-03-31'  # 3个月
```

## 🎯 最佳实践

1. **开发阶段**：使用CSV数据源快速测试
2. **验证阶段**：使用AkShare免费验证策略
3. **生产阶段**：使用Tushare获取高质量数据
4. **备份方案**：配置多个数据源作为备用
5. **缓存策略**：合理设置缓存时间和大小

## 📚 示例代码

完整的示例代码请参考：
- `strategies/real_data_strategy.py` - 真实数据源策略示例
- `test_real_data_sources.py` - 数据源测试脚本
- `ptrade_config.yaml` - 配置文件示例
