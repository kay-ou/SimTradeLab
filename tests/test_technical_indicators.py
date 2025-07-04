# -*- coding: utf-8 -*-
"""
技术指标功能测试
"""
import sys
import os
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ptradeSim.engine import BacktestEngine
from ptradeSim.market_data import get_MACD, get_KDJ, get_RSI, get_CCI, get_technical_indicators


def test_technical_indicators():
    """测试技术指标计算功能"""
    print("=" * 50)
    print("测试技术指标功能")
    print("=" * 50)
    
    # 创建回测引擎
    engine = BacktestEngine(
        strategy_file='strategies/test_strategy.py',
        data_path='data/sample_data.csv',
        start_date='2023-01-01',
        end_date='2023-01-31',
        initial_cash=1000000.0
    )
    
    # 设置当前时间
    engine.context.current_dt = pd.to_datetime('2023-01-15')
    
    # 获取测试股票
    test_security = list(engine.data.keys())[0]
    print(f"测试股票: {test_security}")
    
    # 测试MACD指标
    print("\n1. 测试MACD指标")
    try:
        macd_data = get_MACD(engine, test_security)
        print(f"MACD数据形状: {macd_data.shape}")
        if not macd_data.empty:
            print("MACD指标列:", list(macd_data.columns))
            print("最新MACD值:")
            for col in macd_data.columns:
                if not pd.isna(macd_data[col].iloc[-1]):
                    print(f"  {col}: {macd_data[col].iloc[-1]:.4f}")
        print("✅ MACD指标测试通过")
    except Exception as e:
        print(f"❌ MACD指标测试失败: {e}")
    
    # 测试KDJ指标
    print("\n2. 测试KDJ指标")
    try:
        kdj_data = get_KDJ(engine, test_security)
        print(f"KDJ数据形状: {kdj_data.shape}")
        if not kdj_data.empty:
            print("KDJ指标列:", list(kdj_data.columns))
            print("最新KDJ值:")
            for col in kdj_data.columns:
                if not pd.isna(kdj_data[col].iloc[-1]):
                    print(f"  {col}: {kdj_data[col].iloc[-1]:.4f}")
        print("✅ KDJ指标测试通过")
    except Exception as e:
        print(f"❌ KDJ指标测试失败: {e}")
    
    # 测试RSI指标
    print("\n3. 测试RSI指标")
    try:
        rsi_data = get_RSI(engine, test_security)
        print(f"RSI数据形状: {rsi_data.shape}")
        if not rsi_data.empty:
            print("RSI指标列:", list(rsi_data.columns))
            print("最新RSI值:")
            for col in rsi_data.columns:
                if not pd.isna(rsi_data[col].iloc[-1]):
                    print(f"  {col}: {rsi_data[col].iloc[-1]:.4f}")
        print("✅ RSI指标测试通过")
    except Exception as e:
        print(f"❌ RSI指标测试失败: {e}")
    
    # 测试CCI指标
    print("\n4. 测试CCI指标")
    try:
        cci_data = get_CCI(engine, test_security)
        print(f"CCI数据形状: {cci_data.shape}")
        if not cci_data.empty:
            print("CCI指标列:", list(cci_data.columns))
            print("最新CCI值:")
            for col in cci_data.columns:
                if not pd.isna(cci_data[col].iloc[-1]):
                    print(f"  {col}: {cci_data[col].iloc[-1]:.4f}")
        print("✅ CCI指标测试通过")
    except Exception as e:
        print(f"❌ CCI指标测试失败: {e}")
    
    # 测试综合技术指标函数
    print("\n5. 测试综合技术指标函数")
    try:
        all_indicators = get_technical_indicators(
            engine, test_security, 
            ['MACD', 'KDJ', 'RSI', 'CCI'], 
            period=14
        )
        print(f"综合指标数据形状: {all_indicators.shape}")
        if not all_indicators.empty:
            print("所有指标列:", list(all_indicators.columns))
        print("✅ 综合技术指标测试通过")
    except Exception as e:
        print(f"❌ 综合技术指标测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("技术指标功能测试完成")
    print("=" * 50)


if __name__ == "__main__":
    test_technical_indicators()
