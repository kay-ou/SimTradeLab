# 📋 数据格式迁移指南

## 概述

如果您之前使用的是宽格式（Wide Format）数据，本指南将帮助您快速迁移到ptradeSim v2.0+要求的长格式（Long Format）数据。

## 🔄 格式对比

### 旧格式（宽格式）❌
```csv
datetime,STOCK_A_open,STOCK_A_high,STOCK_A_low,STOCK_A_close,STOCK_A_volume,STOCK_B_open,STOCK_B_high,STOCK_B_low,STOCK_B_close,STOCK_B_volume
2023-01-01,100.00,102.50,99.50,101.20,1500000,50.00,51.25,49.75,50.60,800000
2023-01-02,101.20,103.80,100.90,102.50,1600000,50.60,51.90,50.45,51.25,850000
```

### 新格式（长格式）✅
```csv
date,open,high,low,close,volume,security
2023-01-01,100.00,102.50,99.50,101.20,1500000,STOCK_A
2023-01-02,101.20,103.80,100.90,102.50,1600000,STOCK_A
2023-01-01,50.00,51.25,49.75,50.60,800000,STOCK_B
2023-01-02,50.60,51.90,50.45,51.25,850000,STOCK_B
```

## 🛠️ 自动转换工具

### Python转换脚本

创建 `convert_data_format.py` 文件：

```python
import pandas as pd
import re
from pathlib import Path

def convert_wide_to_long(input_file, output_file=None):
    """
    将宽格式数据转换为长格式
    
    Args:
        input_file: 输入的宽格式CSV文件路径
        output_file: 输出的长格式CSV文件路径（可选）
    """
    # 读取宽格式数据
    df = pd.read_csv(input_file)
    
    # 自动检测日期列
    date_col = None
    for col in ['date', 'datetime', 'Date', 'DateTime']:
        if col in df.columns:
            date_col = col
            break
    
    if date_col is None:
        raise ValueError("未找到日期列，请确保数据包含 'date' 或 'datetime' 列")
    
    # 提取股票代码
    stock_pattern = r'^([A-Z_]+[A-Z0-9_]*)_(open|high|low|close|volume)$'
    stocks = set()
    
    for col in df.columns:
        if col != date_col:
            match = re.match(stock_pattern, col, re.IGNORECASE)
            if match:
                stocks.add(match.group(1))
    
    if not stocks:
        raise ValueError("未找到符合格式的股票数据列")
    
    print(f"检测到 {len(stocks)} 只股票: {', '.join(sorted(stocks))}")
    
    # 转换为长格式
    long_data = []
    
    for stock in stocks:
        # 构建列名
        open_col = f"{stock}_open"
        high_col = f"{stock}_high"
        low_col = f"{stock}_low"
        close_col = f"{stock}_close"
        volume_col = f"{stock}_volume"
        
        # 检查所有必需列是否存在
        required_cols = [open_col, high_col, low_col, close_col, volume_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"警告: 股票 {stock} 缺少列: {missing_cols}，跳过")
            continue
        
        # 提取该股票的数据
        stock_data = pd.DataFrame({
            'date': df[date_col],
            'open': df[open_col],
            'high': df[high_col],
            'low': df[low_col],
            'close': df[close_col],
            'volume': df[volume_col],
            'security': stock
        })
        
        # 过滤掉包含NaN的行
        stock_data = stock_data.dropna()
        
        if not stock_data.empty:
            long_data.append(stock_data)
            print(f"✅ 成功转换股票 {stock}: {len(stock_data)} 条记录")
        else:
            print(f"⚠️  股票 {stock} 没有有效数据")
    
    if not long_data:
        raise ValueError("没有成功转换任何股票数据")
    
    # 合并所有股票数据
    result_df = pd.concat(long_data, ignore_index=True)
    
    # 按日期和股票代码排序
    result_df = result_df.sort_values(['date', 'security']).reset_index(drop=True)
    
    # 确定输出文件名
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_long_format{input_path.suffix}"
    
    # 保存结果
    result_df.to_csv(output_file, index=False)
    
    print(f"\n🎉 转换完成!")
    print(f"📁 输入文件: {input_file}")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 总记录数: {len(result_df)}")
    print(f"📈 股票数量: {result_df['security'].nunique()}")
    print(f"📅 日期范围: {result_df['date'].min()} 到 {result_df['date'].max()}")
    
    return result_df

# 使用示例
if __name__ == "__main__":
    # 转换单个文件
    convert_wide_to_long("data/old_format_data.csv", "data/new_format_data.csv")
    
    # 批量转换
    import glob
    
    for file in glob.glob("data/*_wide.csv"):
        try:
            convert_wide_to_long(file)
            print(f"✅ 成功转换: {file}")
        except Exception as e:
            print(f"❌ 转换失败: {file} - {e}")
```

### 使用方法

1. **单文件转换**：
```bash
python convert_data_format.py
```

2. **自定义转换**：
```python
from convert_data_format import convert_wide_to_long

# 转换指定文件
convert_wide_to_long("my_old_data.csv", "my_new_data.csv")
```

## ✅ 验证转换结果

转换完成后，使用以下代码验证数据格式：

```python
import pandas as pd

def validate_long_format(file_path):
    """验证长格式数据是否正确"""
    df = pd.read_csv(file_path)
    
    # 检查必需列
    required_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'security']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"❌ 缺少必需列: {missing_cols}")
        return False
    
    # 检查数据类型
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"❌ 列 {col} 不是数值类型")
            return False
    
    # 检查逻辑一致性
    invalid_rows = df[
        (df['high'] < df['open']) | 
        (df['high'] < df['close']) | 
        (df['low'] > df['open']) | 
        (df['low'] > df['close'])
    ]
    
    if not invalid_rows.empty:
        print(f"❌ 发现 {len(invalid_rows)} 行数据逻辑不一致")
        return False
    
    print("✅ 数据格式验证通过!")
    print(f"📊 总记录数: {len(df)}")
    print(f"📈 股票数量: {df['security'].nunique()}")
    print(f"📅 日期范围: {df['date'].min()} 到 {df['date'].max()}")
    
    return True

# 验证转换后的数据
validate_long_format("data/new_format_data.csv")
```

## 🚨 常见问题

### Q1: 转换后数据量变大了？
**A**: 这是正常的。长格式会为每只股票的每个日期创建单独的行，所以总行数会增加。

### Q2: 某些股票数据丢失了？
**A**: 检查原始数据中是否有缺失值或列名不规范。转换工具会自动跳过不完整的数据。

### Q3: 日期格式不对？
**A**: 确保原始数据的日期列格式为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS。

### Q4: 如何处理分钟级数据？
**A**: 分钟级数据转换方法相同，只需确保日期列包含时间信息。

## 📚 相关文档

- [数据格式规范](DATA_FORMAT.md)
- [API参考文档](API_REFERENCE.md)
- [策略开发指南](STRATEGY_GUIDE.md)
