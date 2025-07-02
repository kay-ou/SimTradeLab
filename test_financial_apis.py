# -*- coding: utf-8 -*-
"""
财务接口功能测试脚本
测试新实现的财务数据接口功能
"""

from ptradeSim.engine import BacktestEngine
import pandas as pd

def test_financial_apis():
    """测试所有新的财务接口"""
    print("🧪 开始测试财务接口功能")
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
    test_stocks = ['STOCK_A', 'STOCK_B', 'STOCK_C']
    
    print("📊 测试股票:", test_stocks)
    print()
    
    # 导入API函数
    from ptradeSim import api as ptrade_api
    from functools import partial
    
    # 绑定引擎实例到API函数
    get_fundamentals = partial(ptrade_api.get_fundamentals, engine)
    get_income_statement = partial(ptrade_api.get_income_statement, engine)
    get_balance_sheet = partial(ptrade_api.get_balance_sheet, engine)
    get_cash_flow = partial(ptrade_api.get_cash_flow, engine)
    get_financial_ratios = partial(ptrade_api.get_financial_ratios, engine)
    
    # 1. 测试扩展的get_fundamentals接口
    print("1️⃣ 测试扩展的get_fundamentals接口")
    print("-" * 40)
    
    # 测试估值指标
    valuation_data = get_fundamentals(test_stocks, 'valuation', 
                                    fields=['market_cap', 'pe_ratio', 'pb_ratio'])
    print("估值指标:")
    print(valuation_data)
    print()
    
    # 测试盈利能力指标
    income_data = get_fundamentals(test_stocks, 'income', 
                                 fields=['revenue', 'net_income', 'roe', 'roa'])
    print("盈利能力指标:")
    print(income_data)
    print()
    
    # 2. 测试损益表接口
    print("2️⃣ 测试损益表接口")
    print("-" * 40)
    
    income_statement = get_income_statement(test_stocks, 
                                          fields=['revenue', 'gross_profit', 'net_income', 'eps_basic'])
    print("损益表数据:")
    print(income_statement)
    print()
    
    # 3. 测试资产负债表接口
    print("3️⃣ 测试资产负债表接口")
    print("-" * 40)
    
    balance_sheet = get_balance_sheet(test_stocks, 
                                    fields=['total_assets', 'total_liabilities', 'total_equity', 'cash_and_equivalents'])
    print("资产负债表数据:")
    print(balance_sheet)
    print()
    
    # 4. 测试现金流量表接口
    print("4️⃣ 测试现金流量表接口")
    print("-" * 40)
    
    cash_flow = get_cash_flow(test_stocks, 
                            fields=['operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'free_cash_flow'])
    print("现金流量表数据:")
    print(cash_flow)
    print()
    
    # 5. 测试财务比率接口
    print("5️⃣ 测试财务比率接口")
    print("-" * 40)
    
    financial_ratios = get_financial_ratios(test_stocks, 
                                          fields=['current_ratio', 'debt_to_equity', 'roe', 'roa', 'gross_margin'])
    print("财务比率数据:")
    print(financial_ratios)
    print()
    
    # 6. 测试数据一致性
    print("6️⃣ 测试数据一致性")
    print("-" * 40)
    
    # 同一股票多次调用应该返回相同数据
    data1 = get_fundamentals(['STOCK_A'], 'valuation', fields=['pe_ratio'])
    data2 = get_fundamentals(['STOCK_A'], 'valuation', fields=['pe_ratio'])
    
    is_consistent = data1.equals(data2)
    print(f"数据一致性测试: {'✅ 通过' if is_consistent else '❌ 失败'}")
    print(f"第一次调用: {data1.iloc[0, 0]:.6f}")
    print(f"第二次调用: {data2.iloc[0, 0]:.6f}")
    print()
    
    # 7. 测试错误处理
    print("7️⃣ 测试错误处理")
    print("-" * 40)
    
    try:
        # 测试不存在的字段
        error_data = get_fundamentals(test_stocks, 'valuation', fields=['non_existent_field'])
        print("错误字段处理: ✅ 正常返回None值")
        print(error_data)
    except Exception as e:
        print(f"错误字段处理: ❌ 抛出异常 - {e}")
    
    print()
    print("🎉 财务接口功能测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_financial_apis()
