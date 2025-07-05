#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据源测试脚本

演示如何使用不同的数据源进行回测
"""

import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from ptradeSim import (
    BacktestEngine, DataSourceFactory, DataSourceConfig, 
    TUSHARE_AVAILABLE, AKSHARE_AVAILABLE, log
)


def test_csv_data_source():
    """测试CSV数据源（向后兼容）"""
    print("\n" + "="*60)
    print("测试 CSV 数据源")
    print("="*60)
    
    try:
        # 使用传统方式创建引擎（向后兼容）
        engine = BacktestEngine(
            strategy_file='strategies/real_data_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-01',
            end_date='2023-01-10',
            initial_cash=1000000.0,
            frequency='1d'
        )
        
        print("✓ CSV数据源引擎创建成功")
        
        # 运行回测
        engine.run()
        print("✓ CSV数据源回测完成")
        
    except Exception as e:
        print(f"✗ CSV数据源测试失败: {e}")


def test_tushare_data_source():
    """测试Tushare数据源"""
    print("\n" + "="*60)
    print("测试 Tushare 数据源")
    print("="*60)
    
    if not TUSHARE_AVAILABLE:
        print("✗ Tushare未安装，跳过测试")
        print("  安装命令: pip install tushare")
        return
    
    # 检查token
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        print("✗ 未设置TUSHARE_TOKEN环境变量，跳过测试")
        print("  请先设置环境变量: export TUSHARE_TOKEN=your_token")
        return
    
    try:
        # 使用Tushare数据源
        engine = BacktestEngine(
            strategy_file='strategies/real_data_strategy.py',
            data_source='tushare',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0,
            frequency='1d',
            securities=['000001.SZ', '000002.SZ']  # 指定股票列表
        )
        
        print("✓ Tushare数据源引擎创建成功")
        
        # 运行回测
        engine.run()
        print("✓ Tushare数据源回测完成")
        
    except Exception as e:
        print(f"✗ Tushare数据源测试失败: {e}")


def test_akshare_data_source():
    """测试AkShare数据源"""
    print("\n" + "="*60)
    print("测试 AkShare 数据源")
    print("="*60)
    
    if not AKSHARE_AVAILABLE:
        print("✗ AkShare未安装，跳过测试")
        print("  安装命令: pip install akshare")
        return
    
    try:
        # 使用AkShare数据源
        engine = BacktestEngine(
            strategy_file='strategies/real_data_strategy.py',
            data_source='akshare',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0,
            frequency='1d',
            securities=['000001', '000002']  # AkShare使用6位代码
        )
        
        print("✓ AkShare数据源引擎创建成功")
        
        # 运行回测
        engine.run()
        print("✓ AkShare数据源回测完成")
        
    except Exception as e:
        print(f"✗ AkShare数据源测试失败: {e}")


def test_data_source_factory():
    """测试数据源工厂"""
    print("\n" + "="*60)
    print("测试数据源工厂")
    print("="*60)
    
    try:
        # 列出可用的数据源
        available_sources = DataSourceFactory.list_available()
        print(f"✓ 可用数据源: {available_sources}")
        
        # 测试CSV数据源创建
        csv_source = DataSourceFactory.create('csv', data_path='data/sample_data.csv')
        print(f"✓ CSV数据源创建成功: {type(csv_source).__name__}")
        
        # 测试获取股票列表
        stock_list = csv_source.get_stock_list()
        print(f"✓ 获取股票列表: {stock_list[:5]}...")  # 只显示前5个
        
        if TUSHARE_AVAILABLE and os.getenv('TUSHARE_TOKEN'):
            # 测试Tushare数据源创建
            tushare_source = DataSourceFactory.create('tushare', token=os.getenv('TUSHARE_TOKEN'))
            print(f"✓ Tushare数据源创建成功: {type(tushare_source).__name__}")
        
        if AKSHARE_AVAILABLE:
            # 测试AkShare数据源创建
            akshare_source = DataSourceFactory.create('akshare')
            print(f"✓ AkShare数据源创建成功: {type(akshare_source).__name__}")
        
    except Exception as e:
        print(f"✗ 数据源工厂测试失败: {e}")


def test_config_system():
    """测试配置系统"""
    print("\n" + "="*60)
    print("测试配置系统")
    print("="*60)
    
    try:
        # 创建配置对象
        config = DataSourceConfig()
        print("✓ 配置对象创建成功")
        
        # 测试默认配置
        default_source = config.get_default_source()
        print(f"✓ 默认数据源: {default_source}")
        
        # 测试配置验证
        is_valid = config.validate()
        print(f"✓ 配置验证: {'通过' if is_valid else '失败'}")
        
        # 测试Tushare token获取
        tushare_token = config.get_tushare_token()
        if tushare_token:
            print(f"✓ Tushare token: {tushare_token[:10]}...")
        else:
            print("! Tushare token未配置")
        
    except Exception as e:
        print(f"✗ 配置系统测试失败: {e}")


def main():
    """主函数"""
    print("ptradeSim 真实数据源功能测试")
    print("="*60)
    
    # 显示环境信息
    print(f"Tushare可用: {'是' if TUSHARE_AVAILABLE else '否'}")
    print(f"AkShare可用: {'是' if AKSHARE_AVAILABLE else '否'}")
    print(f"TUSHARE_TOKEN: {'已设置' if os.getenv('TUSHARE_TOKEN') else '未设置'}")
    
    # 运行测试
    test_config_system()
    test_data_source_factory()
    test_csv_data_source()
    
    # 只有在相应依赖可用时才测试
    if TUSHARE_AVAILABLE and os.getenv('TUSHARE_TOKEN'):
        test_tushare_data_source()
    else:
        print("\n跳过Tushare测试（依赖或token未配置）")
    
    if AKSHARE_AVAILABLE:
        test_akshare_data_source()
    else:
        print("\n跳过AkShare测试（依赖未安装）")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    
    # 提供使用建议
    print("\n使用建议:")
    print("1. 对于离线回测，继续使用CSV数据源")
    print("2. 对于实时数据，推荐使用Tushare（需要注册token）")
    print("3. 对于免费数据，可以使用AkShare（无需token）")
    print("4. 可以通过配置文件管理数据源设置")


if __name__ == '__main__':
    main()
