# 📊 SimTradeLab 数据格式规范

## 概述

SimTradeLab 支持标准的 CSV 格式数据输入，采用**长格式**（Long Format）数据结构，便于处理多股票、多时间频率的数据。

## 🔧 标准数据格式

### 必需列

| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `date` | string | 交易日期，格式：YYYY-MM-DD | 2023-01-01 |
| `open` | float | 开盘价 | 100.50 |
| `high` | float | 最高价 | 102.30 |
| `low` | float | 最低价 | 99.80 |
| `close` | float | 收盘价 | 101.20 |
| `volume` | int | 成交量 | 1500000 |
| `security` | string | 股票代码/标识符 | STOCK_A |

### 分钟级数据格式

对于分钟级数据，`date` 列应包含完整的日期时间信息：

| 列名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `datetime` | string | 日期时间，格式：YYYY-MM-DD HH:MM:SS | 2023-01-01 09:30:00 |
| `open` | float | 开盘价 | 100.50 |
| `high` | float | 最高价 | 102.30 |
| `low` | float | 最低价 | 99.80 |
| `close` | float | 收盘价 | 101.20 |
| `volume` | int | 成交量 | 15000 |
| `security` | string | 股票代码/标识符 | STOCK_A |

## 📝 示例数据

### 日线数据示例

```csv
date,open,high,low,close,volume,security
2023-01-01,100.00,102.50,99.50,101.20,1500000,STOCK_A
2023-01-02,101.20,103.80,100.90,102.50,1600000,STOCK_A
2023-01-03,102.50,104.20,101.80,103.10,1400000,STOCK_A
2023-01-01,50.00,51.25,49.75,50.60,800000,STOCK_B
2023-01-02,50.60,51.90,50.45,51.25,850000,STOCK_B
2023-01-03,51.25,52.10,50.90,51.55,750000,STOCK_B
```

### 分钟级数据示例

```csv
datetime,open,high,low,close,volume,security
2023-01-01 09:30:00,100.00,100.50,99.80,100.20,15000,STOCK_A
2023-01-01 09:31:00,100.20,100.80,100.10,100.60,12000,STOCK_A
2023-01-01 09:32:00,100.60,101.20,100.40,100.90,18000,STOCK_A
2023-01-01 09:30:00,50.00,50.25,49.90,50.10,8000,STOCK_B
2023-01-01 09:31:00,50.10,50.40,50.05,50.30,6000,STOCK_B
2023-01-01 09:32:00,50.30,50.60,50.20,50.45,9000,STOCK_B
```

## 🔄 数据格式转换

### 从宽格式转换为长格式

如果您的数据是宽格式（每个股票的OHLCV作为单独列），可以使用以下Python代码转换：

```python
import pandas as pd

def convert_wide_to_long(wide_df):
    """将宽格式数据转换为长格式"""
    long_data = []
    
    # 提取股票列表
    stocks = set()
    for col in wide_df.columns:
        if '_' in col and col != 'datetime' and col != 'date':
            stock = col.split('_')[0]
            stocks.add(stock)
    
    # 转换每只股票的数据
    for stock in stocks:
        stock_data = wide_df[['date']].copy() if 'date' in wide_df.columns else wide_df[['datetime']].copy()
        stock_data['open'] = wide_df[f'{stock}_open']
        stock_data['high'] = wide_df[f'{stock}_high']
        stock_data['low'] = wide_df[f'{stock}_low']
        stock_data['close'] = wide_df[f'{stock}_close']
        stock_data['volume'] = wide_df[f'{stock}_volume']
        stock_data['security'] = stock
        
        long_data.append(stock_data)
    
    return pd.concat(long_data, ignore_index=True)

# 使用示例
wide_df = pd.read_csv('wide_format_data.csv')
long_df = convert_wide_to_long(wide_df)
long_df.to_csv('long_format_data.csv', index=False)
```

## ⚠️ 注意事项

### 数据质量要求

1. **无缺失值**：所有必需列不能有空值
2. **数据类型**：确保价格为数值类型，成交量为整数类型
3. **日期格式**：严格按照 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS 格式
4. **逻辑一致性**：high ≥ max(open, close)，low ≤ min(open, close)
5. **正数约束**：价格和成交量必须为正数

### 多股票数据

- 同一个CSV文件可以包含多只股票的数据
- 通过 `security` 列区分不同股票
- 建议按日期和股票代码排序

### 时间频率支持

SimTradeLab 支持以下时间频率：
- **日线**：1d
- **分钟线**：1m, 5m, 15m, 30m
- **小时线**：1h
- **周线**：1w
- **月线**：1M

## 🛠️ 数据验证

在使用数据前，建议进行以下验证：

```python
def validate_data_format(df):
    """验证数据格式是否正确"""
    required_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'security']
    
    # 检查必需列
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必需列: {missing_cols}")
    
    # 检查数据类型
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"列 {col} 必须为数值类型")
    
    # 检查逻辑一致性
    invalid_rows = df[(df['high'] < df['open']) | (df['high'] < df['close']) | 
                      (df['low'] > df['open']) | (df['low'] > df['close'])]
    if not invalid_rows.empty:
        raise ValueError(f"发现 {len(invalid_rows)} 行数据逻辑不一致")
    
    print("✅ 数据格式验证通过")

# 使用示例
df = pd.read_csv('your_data.csv')
validate_data_format(df)
```

## 📚 相关文档

- [API参考文档](API_REFERENCE.md)
- [策略开发指南](STRATEGY_GUIDE.md)
- [多频率交易文档](MULTI_FREQUENCY_TRADING.md)
