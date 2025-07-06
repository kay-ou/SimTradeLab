#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试高级行情数据API的实现
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simtradelab import (
    get_individual_entrust, get_individual_transaction, 
    get_gear_price, get_sort_msg, send_email, send_qywx
)
import pandas as pd


def test_get_individual_entrust():
    """测试获取逐笔委托行情"""
    print("\n=== 测试获取逐笔委托行情 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试单只股票
    result1 = get_individual_entrust(engine, '600519.SH')
    print(f"单只股票逐笔委托数据: {len(result1)}只股票")
    
    assert '600519.SH' in result1, "应该包含查询的股票"
    entrust_df = result1['600519.SH']
    assert isinstance(entrust_df, pd.DataFrame), "应该返回DataFrame"
    
    # 验证必要字段
    required_fields = ['business_time', 'hq_px', 'business_amount', 'order_no', 
                      'business_direction', 'trans_kind']
    for field in required_fields:
        assert field in entrust_df.columns, f"应该包含字段 {field}"
    
    print(f"  - 数据条数: {len(entrust_df)}")
    print(f"  - 价格范围: {entrust_df['hq_px'].min():.2f} - {entrust_df['hq_px'].max():.2f}")
    
    # 测试多只股票
    stocks = ['600519.SH', '000001.SZ']
    result2 = get_individual_entrust(engine, stocks)
    assert len(result2) == 2, "应该返回2只股票的数据"
    
    print("✅ 逐笔委托行情测试完成")


def test_get_individual_transaction():
    """测试获取逐笔成交行情"""
    print("\n=== 测试获取逐笔成交行情 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试单只股票
    result1 = get_individual_transaction(engine, '600519.SH')
    print(f"单只股票逐笔成交数据: {len(result1)}只股票")
    
    assert '600519.SH' in result1, "应该包含查询的股票"
    transaction_df = result1['600519.SH']
    assert isinstance(transaction_df, pd.DataFrame), "应该返回DataFrame"
    
    # 验证必要字段
    required_fields = ['business_time', 'hq_px', 'business_amount', 'trade_index',
                      'business_direction', 'buy_no', 'sell_no', 'trans_flag',
                      'trans_identify_am', 'channel_num']
    for field in required_fields:
        assert field in transaction_df.columns, f"应该包含字段 {field}"
    
    print(f"  - 数据条数: {len(transaction_df)}")
    print(f"  - 价格范围: {transaction_df['hq_px'].min():.2f} - {transaction_df['hq_px'].max():.2f}")
    print(f"  - 成交量范围: {transaction_df['business_amount'].min()} - {transaction_df['business_amount'].max()}")
    
    # 测试多只股票
    stocks = ['600519.SH', '000001.SZ']
    result2 = get_individual_transaction(engine, stocks)
    assert len(result2) == 2, "应该返回2只股票的数据"
    
    print("✅ 逐笔成交行情测试完成")


def test_get_gear_price():
    """测试获取档位行情价格"""
    print("\n=== 测试获取档位行情价格 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试获取档位行情
    result = get_gear_price(engine, '600519.SH')
    print(f"档位行情数据: {result['security']}")
    
    # 验证必要字段
    required_fields = ['security', 'timestamp', 'bid_prices', 'bid_volumes',
                      'ask_prices', 'ask_volumes', 'last_price', 
                      'total_bid_volume', 'total_ask_volume']
    for field in required_fields:
        assert field in result, f"应该包含字段 {field}"
    
    # 验证数据格式
    assert len(result['bid_prices']) == 5, "应该有5个买档价格"
    assert len(result['ask_prices']) == 5, "应该有5个卖档价格"
    assert len(result['bid_volumes']) == 5, "应该有5个买档量"
    assert len(result['ask_volumes']) == 5, "应该有5个卖档量"
    
    print(f"  - 最新价: {result['last_price']}")
    print(f"  - 买一价: {result['bid_prices'][0]}, 买一量: {result['bid_volumes'][0]}")
    print(f"  - 卖一价: {result['ask_prices'][0]}, 卖一量: {result['ask_volumes'][0]}")
    
    print("✅ 档位行情价格测试完成")


def test_get_sort_msg():
    """测试获取板块、行业排名"""
    print("\n=== 测试获取板块、行业排名 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试板块排名
    sector_result = get_sort_msg(engine, market_type='sector', sort_field='pct_change')
    print(f"板块排名数据: {len(sector_result)}个板块")
    
    assert isinstance(sector_result, list), "应该返回列表"
    assert len(sector_result) > 0, "应该有板块数据"
    
    # 验证数据格式
    for item in sector_result[:3]:  # 检查前3个
        required_fields = ['name', 'code', 'pct_change', 'volume', 'amount',
                          'up_count', 'down_count', 'flat_count']
        for field in required_fields:
            assert field in item, f"板块数据应该包含字段 {field}"
        
        print(f"  - {item['name']}: 涨跌幅 {item['pct_change']}%, 上涨 {item['up_count']}家")
    
    # 测试行业排名
    industry_result = get_sort_msg(engine, market_type='industry', sort_field='volume')
    print(f"行业排名数据: {len(industry_result)}个行业")
    
    assert isinstance(industry_result, list), "应该返回列表"
    assert len(industry_result) > 0, "应该有行业数据"
    
    # 测试排序功能
    ascending_result = get_sort_msg(engine, market_type='sector', sort_field='pct_change', ascending=True, count=5)
    assert len(ascending_result) == 5, "应该返回指定数量的数据"
    
    print("✅ 板块、行业排名测试完成")


def test_send_email():
    """测试发送邮件功能"""
    print("\n=== 测试发送邮件功能 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试发送邮件
    result = send_email(
        engine,
        to_email="test@example.com",
        subject="测试邮件",
        content="这是一封测试邮件，用于验证邮件发送功能。",
        attachments=["report.pdf", "data.csv"]
    )
    
    assert result == True, "邮件发送应该成功"
    print("✅ 邮件发送功能测试完成")


def test_send_qywx():
    """测试发送企业微信功能"""
    print("\n=== 测试发送企业微信功能 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 测试发送到部门
    result1 = send_qywx(
        engine,
        content="策略运行报告：今日收益率 +2.5%",
        toparty="量化投资部"
    )
    assert result1 == True, "发送到部门应该成功"
    
    # 测试发送到个人
    result2 = send_qywx(
        engine,
        content="个人交易提醒：持仓股票涨停",
        touser="张三"
    )
    assert result2 == True, "发送到个人应该成功"
    
    # 测试发送到标签组
    result3 = send_qywx(
        engine,
        content="市场预警：大盘跌幅超过3%",
        totag="交易员组"
    )
    assert result3 == True, "发送到标签组应该成功"
    
    print("✅ 企业微信发送功能测试完成")


def test_integration():
    """集成测试：验证API之间的协调工作"""
    print("\n=== 集成测试 ===")
    
    # 创建简单的模拟引擎
    class MockEngine:
        def __init__(self):
            pass
    
    engine = MockEngine()
    
    # 获取板块排名
    top_sectors = get_sort_msg(engine, market_type='sector', count=3)
    print(f"获取前3个板块排名")
    
    # 模拟根据板块表现发送通知
    if top_sectors:
        best_sector = top_sectors[0]
        if best_sector['pct_change'] > 5:
            # 发送邮件通知
            send_email(
                engine,
                to_email="manager@company.com",
                subject=f"板块异动提醒：{best_sector['name']}",
                content=f"{best_sector['name']}今日涨幅达到{best_sector['pct_change']}%"
            )
            
            # 发送企业微信通知
            send_qywx(
                engine,
                content=f"板块异动：{best_sector['name']}涨幅{best_sector['pct_change']}%",
                toparty="投资部"
            )
    
    # 获取重点股票的逐笔数据
    key_stocks = ['600519.SH', '000001.SZ']
    entrust_data = get_individual_entrust(engine, key_stocks)
    transaction_data = get_individual_transaction(engine, key_stocks)
    
    print(f"获取 {len(key_stocks)} 只重点股票的逐笔数据")
    print(f"委托数据: {sum(len(df) for df in entrust_data.values())} 条")
    print(f"成交数据: {sum(len(df) for df in transaction_data.values())} 条")
    
    print("✅ 集成测试完成")


def main():
    """运行所有测试"""
    print("开始测试高级行情数据API...")
    
    try:
        test_get_individual_entrust()
        test_get_individual_transaction()
        test_get_gear_price()
        test_get_sort_msg()
        test_send_email()
        test_send_qywx()
        test_integration()
        
        print("\n🎉 所有高级行情数据API测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
