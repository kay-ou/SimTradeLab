# -*- coding: utf-8 -*-
"""
市场数据接口功能测试脚本
测试新实现的市场数据接口功能
"""

import pandas as pd
import numpy as np
from functools import partial
from ptradesim import (
    BacktestEngine,
    get_price,
    get_current_data,
    get_market_snapshot,
    get_technical_indicators,
    get_history
)

def test_market_data_apis():
    """测试所有新的市场数据接口"""
    print("📈 开始测试市场数据接口功能")
    print("=" * 60)
    
    # 创建回测引擎实例
    engine = BacktestEngine(
        strategy_file='strategies/test_strategy.py',
        data_path='data/sample_data.csv',
        start_date='2023-01-13',
        end_date='2023-01-13',
        initial_cash=1000000.0
    )
    
    # 测试股票列表
    test_stocks = ['STOCK_A', 'STOCK_B']
    
    print("📊 测试股票:", test_stocks)
    print()
    
    # 绑定引擎实例到API函数
    _get_price = partial(get_price, engine)
    _get_current_data = partial(get_current_data, engine)
    _get_market_snapshot = partial(get_market_snapshot, engine)
    _get_technical_indicators = partial(get_technical_indicators, engine)
    _get_history = partial(get_history, engine)
    
    # 1. 测试增强的get_price接口
    print("1️⃣ 测试增强的get_price接口")
    print("-" * 40)
    
    # 测试基础价格字段
    basic_price = _get_price(test_stocks, fields=['open', 'high', 'low', 'close', 'volume'])
    print("基础价格数据:")
    print(basic_price)
    print()
    
    # 测试扩展价格字段
    extended_price = _get_price(test_stocks, fields=['close', 'change', 'pct_change', 'amplitude', 'turnover_rate'])
    print("扩展价格数据:")
    print(extended_price)
    print()
    
    # 2. 测试实时报价数据接口
    print("2️⃣ 测试实时报价数据接口")
    print("-" * 40)
    
    # 测试get_current_data
    current_data = _get_current_data(test_stocks)
    print("实时数据 (STOCK_A):")
    for key, value in list(current_data['STOCK_A'].items())[:10]:  # 只显示前10个字段
        print(f"  {key}: {value:.4f}" if isinstance(value, (int, float)) else f"  {key}: {value}")
    print("  ...")
    print()
    
    # 测试get_market_snapshot
    snapshot = _get_market_snapshot(test_stocks, fields=['close', 'change', 'pct_change', 'bid1', 'ask1'])
    print("市场快照:")
    print(snapshot)
    print()
    
    # 3. 测试技术指标计算接口
    print("3️⃣ 测试技术指标计算接口")
    print("-" * 40)
    
    # 测试移动平均线
    ma_data = _get_technical_indicators(test_stocks, 'MA', period=5)
    print("移动平均线 (MA5):")
    print(ma_data.tail(3))  # 显示最后3行
    print()
    
    # 测试MACD指标
    macd_data = _get_technical_indicators(test_stocks, 'MACD')
    print("MACD指标:")
    print(macd_data.tail(3))  # 显示最后3行
    print()
    
    # 测试RSI指标
    rsi_data = _get_technical_indicators(test_stocks, 'RSI', period=14)
    print("RSI指标:")
    print(rsi_data.tail(3))  # 显示最后3行
    print()
    
    # 4. 测试增强的历史数据接口
    print("4️⃣ 测试增强的历史数据接口")
    print("-" * 40)
    
    # 测试字典格式返回
    history_dict = _get_history(5, field=['close', 'volume'], security_list=test_stocks, is_dict=True)
    print("历史数据 (字典格式):")
    for stock in test_stocks:
        print(f"  {stock} - close: {history_dict[stock]['close'][-3:]}")  # 最后3个值
    print()
    
    # 测试DataFrame格式返回
    history_df = _get_history(5, field=['close', 'volume'], security_list=test_stocks, is_dict=False)
    print("历史数据 (DataFrame格式):")
    print(history_df.tail(3))
    print()
    
    # 5. 测试数据一致性
    print("5️⃣ 测试数据一致性")
    print("-" * 40)
    
    # 测试同一股票多次调用的一致性
    price1 = _get_price(['STOCK_A'], fields=['turnover_rate'])
    price2 = _get_price(['STOCK_A'], fields=['turnover_rate'])
    
    is_consistent = abs(price1.iloc[0, 0] - price2.iloc[0, 0]) < 1e-10
    print(f"价格数据一致性测试: {'✅ 通过' if is_consistent else '❌ 失败'}")
    print(f"第一次调用: {price1.iloc[0, 0]:.6f}")
    print(f"第二次调用: {price2.iloc[0, 0]:.6f}")
    print()
    
    # 6. 测试错误处理
    print("6️⃣ 测试错误处理")
    print("-" * 40)
    
    try:
        # 测试不存在的股票
        error_data = _get_current_data(['NON_EXISTENT_STOCK'])
        print(f"不存在股票处理: ✅ 正常返回空数据 (返回 {len(error_data)} 条记录)")
    except Exception as e:
        print(f"不存在股票处理: ❌ 抛出异常 - {e}")
    
    try:
        # 测试不支持的字段
        error_price = _get_price(test_stocks, fields=['non_existent_field'])
        print("不支持字段处理: ✅ 正常处理")
    except Exception as e:
        print(f"不支持字段处理: ❌ 抛出异常 - {e}")
    
    print()
    
    # 7. 性能测试
    print("7️⃣ 性能测试")
    print("-" * 40)
    
    import time
    
    # 测试大量数据处理
    start_time = time.time()
    large_history = _get_history(50, field=['close'], security_list=test_stocks, is_dict=True)
    end_time = time.time()
    
    print(f"获取50条历史数据耗时: {(end_time - start_time)*1000:.2f}ms")
    
    # 测试技术指标计算性能
    start_time = time.time()
    multiple_indicators = _get_technical_indicators(test_stocks, ['MA', 'RSI', 'MACD'])
    end_time = time.time()
    
    print(f"计算多个技术指标耗时: {(end_time - start_time)*1000:.2f}ms")
    print()
    
    print("🎉 市场数据接口功能测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_market_data_apis()
