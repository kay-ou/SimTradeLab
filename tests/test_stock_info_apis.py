#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试股票基础信息补充API的实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import (
    get_stock_exrights, get_index_stocks, get_industry_stocks, get_ipo_stocks
)


def test_get_stock_exrights():
    """测试获取除权除息信息"""
    print("\n=== 测试获取除权除息信息 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试单只股票
    result1 = get_stock_exrights(engine, '600519.SH')
    print(f"单只股票除权除息信息: {result1}")
    assert '600519.SH' in result1, "应该包含查询的股票"
    assert 'dividend_date' in result1['600519.SH'], "应该包含分红日期"
    assert 'cash_dividend' in result1['600519.SH'], "应该包含现金分红"
    
    # 测试多只股票
    stocks = ['600519.SH', '000001.SZ', '000002.SZ']
    result2 = get_stock_exrights(engine, stocks)
    print(f"多只股票除权除息信息: {len(result2)}只股票")
    
    for stock in stocks:
        assert stock in result2, f"应该包含股票 {stock}"
        assert 'ex_dividend_date' in result2[stock], "应该包含除息日"
        assert 'record_date' in result2[stock], "应该包含股权登记日"
    
    print("✅ 除权除息信息测试完成")


def test_get_index_stocks():
    """测试获取指数成份股"""
    print("\n=== 测试获取指数成份股 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试不同指数
    test_indices = ['000001.SH', '000300.SH', '399001.SZ', '399006.SZ']
    
    for index_code in test_indices:
        stocks = get_index_stocks(engine, index_code)
        print(f"指数 {index_code} 成份股: {len(stocks)}只")
        assert isinstance(stocks, list), "应该返回列表"
        assert len(stocks) > 0, f"指数 {index_code} 应该有成份股"
        
        # 验证股票代码格式
        for stock in stocks:
            assert '.' in stock, f"股票代码 {stock} 格式应该正确"
    
    # 测试不存在的指数
    unknown_stocks = get_index_stocks(engine, 'UNKNOWN.XX')
    assert len(unknown_stocks) == 0, "不存在的指数应该返回空列表"
    
    print("✅ 指数成份股测试完成")


def test_get_industry_stocks():
    """测试获取行业成份股"""
    print("\n=== 测试获取行业成份股 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试不同行业
    test_industries = ['银行', '白酒', '科技', '医药', '地产']
    
    for industry in test_industries:
        stocks = get_industry_stocks(engine, industry)
        print(f"行业 {industry} 成份股: {len(stocks)}只")
        assert isinstance(stocks, list), "应该返回列表"
        assert len(stocks) > 0, f"行业 {industry} 应该有成份股"
        
        # 验证股票代码格式
        for stock in stocks:
            assert '.' in stock, f"股票代码 {stock} 格式应该正确"
    
    # 测试不存在的行业
    unknown_stocks = get_industry_stocks(engine, '未知行业')
    assert len(unknown_stocks) == 0, "不存在的行业应该返回空列表"
    
    print("✅ 行业成份股测试完成")


def test_get_ipo_stocks():
    """测试获取IPO申购标的"""
    print("\n=== 测试获取IPO申购标的 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取IPO申购标的
    ipo_stocks = get_ipo_stocks(engine)
    print(f"IPO申购标的: {len(ipo_stocks)}只")
    
    assert isinstance(ipo_stocks, list), "应该返回列表"
    
    for ipo in ipo_stocks:
        assert isinstance(ipo, dict), "每个IPO标的应该是字典"
        
        # 验证必要字段
        required_fields = ['stock_code', 'stock_name', 'issue_price', 'issue_date', 
                          'max_purchase_amount', 'min_purchase_amount', 'market']
        for field in required_fields:
            assert field in ipo, f"IPO标的应该包含字段 {field}"
        
        # 验证数据类型
        assert isinstance(ipo['issue_price'], (int, float)), "发行价应该是数字"
        assert isinstance(ipo['max_purchase_amount'], int), "最大申购数量应该是整数"
        assert isinstance(ipo['min_purchase_amount'], int), "最小申购数量应该是整数"
        assert ipo['market'] in ['SH', 'SZ'], "市场应该是SH或SZ"
        
        print(f"  - {ipo['stock_code']} {ipo['stock_name']} 发行价: {ipo['issue_price']}")
    
    # 测试指定日期
    ipo_stocks_date = get_ipo_stocks(engine, '2023-06-20')
    assert isinstance(ipo_stocks_date, list), "指定日期应该返回列表"
    
    print("✅ IPO申购标的测试完成")


def test_integration():
    """集成测试：验证API之间的协调工作"""
    print("\n=== 集成测试 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 获取指数成份股
    hs300_stocks = get_index_stocks(engine, '000300.SH')
    print(f"沪深300成份股: {len(hs300_stocks)}只")
    
    # 获取这些股票的除权除息信息
    if hs300_stocks:
        sample_stocks = hs300_stocks[:3]  # 取前3只
        exrights_info = get_stock_exrights(engine, sample_stocks)
        print(f"获取 {len(sample_stocks)} 只股票的除权除息信息")
        
        assert len(exrights_info) == len(sample_stocks), "除权除息信息数量应该匹配"
    
    # 获取银行行业股票
    bank_stocks = get_industry_stocks(engine, '银行')
    print(f"银行行业股票: {len(bank_stocks)}只")
    
    # 获取IPO信息
    ipo_info = get_ipo_stocks(engine)
    print(f"当前IPO申购标的: {len(ipo_info)}只")
    
    print("✅ 集成测试完成")


def main():
    """运行所有测试"""
    print("开始测试股票基础信息补充API...")
    
    try:
        test_get_stock_exrights()
        test_get_index_stocks()
        test_get_industry_stocks()
        test_get_ipo_stocks()
        test_integration()
        
        print("\n🎉 所有股票基础信息API测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
