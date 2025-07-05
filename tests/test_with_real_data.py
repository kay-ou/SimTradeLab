#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据源测试脚本

如果您有Tushare token或想测试AkShare，可以运行此脚本
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from ptradeSim import BacktestEngine, log


def test_tushare_with_token():
    """测试Tushare数据源（需要真实token）"""
    print("\n" + "="*60)
    print("测试 Tushare 真实数据源")
    print("="*60)
    
    token = input("请输入您的Tushare token（回车跳过）: ").strip()
    if not token:
        print("跳过Tushare测试")
        return
    
    # 设置环境变量
    os.environ['TUSHARE_TOKEN'] = token
    
    try:
        print("正在创建Tushare数据源引擎...")
        engine = BacktestEngine(
            strategy_file='strategies/real_data_strategy.py',
            data_source='tushare',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0,
            securities=['000001.SZ', '000002.SZ']  # 平安银行、万科A
        )
        
        print("✓ Tushare引擎创建成功")
        print("正在运行回测...")
        engine.run()
        print("✓ Tushare回测完成")
        
    except Exception as e:
        print(f"✗ Tushare测试失败: {e}")
        print("可能的原因：")
        print("1. Token无效或已过期")
        print("2. 网络连接问题")
        print("3. API调用次数限制")


def test_akshare_installation():
    """测试AkShare安装和基本功能"""
    print("\n" + "="*60)
    print("测试 AkShare 数据源")
    print("="*60)
    
    try:
        import akshare as ak
        print("✓ AkShare已安装")
        
        # 测试获取股票列表
        print("正在测试AkShare连接...")
        stock_list = ak.stock_zh_a_spot_em()
        print(f"✓ 成功获取股票列表，共 {len(stock_list)} 只股票")
        
        # 测试ptradeSim的AkShare数据源
        print("正在创建AkShare数据源引擎...")
        engine = BacktestEngine(
            strategy_file='strategies/real_data_strategy.py',
            data_source='akshare',
            start_date='2023-01-01',
            end_date='2023-01-31',
            initial_cash=1000000.0,
            securities=['000001', '000002']  # AkShare使用6位代码
        )
        
        print("✓ AkShare引擎创建成功")
        print("正在运行回测...")
        engine.run()
        print("✓ AkShare回测完成")
        
    except ImportError:
        print("✗ AkShare未安装")
        install = input("是否现在安装AkShare？(y/n): ").strip().lower()
        if install == 'y':
            print("正在安装AkShare...")
            os.system("pip install akshare")
            print("安装完成，请重新运行此脚本")
        else:
            print("跳过AkShare测试")
    except Exception as e:
        print(f"✗ AkShare测试失败: {e}")
        print("可能的原因：")
        print("1. 网络连接问题")
        print("2. AkShare服务暂时不可用")
        print("3. 反爬虫限制")


def test_data_source_comparison():
    """对比不同数据源的性能"""
    print("\n" + "="*60)
    print("数据源性能对比")
    print("="*60)
    
    import time
    
    # 测试CSV数据源性能
    print("测试CSV数据源性能...")
    start_time = time.time()
    try:
        engine = BacktestEngine(
            strategy_file='strategies/real_data_strategy.py',
            data_source='csv',
            start_date='2023-01-01',
            end_date='2023-01-10',
            initial_cash=1000000.0,
            securities=['STOCK_A', 'STOCK_B']
        )
        engine.run()
        csv_time = time.time() - start_time
        print(f"✓ CSV数据源耗时: {csv_time:.2f}秒")
    except Exception as e:
        print(f"✗ CSV数据源测试失败: {e}")
        csv_time = None
    
    # 如果有Tushare token，测试Tushare性能
    if os.getenv('TUSHARE_TOKEN'):
        print("测试Tushare数据源性能...")
        start_time = time.time()
        try:
            engine = BacktestEngine(
                strategy_file='strategies/real_data_strategy.py',
                data_source='tushare',
                start_date='2023-01-01',
                end_date='2023-01-10',
                initial_cash=1000000.0,
                securities=['000001.SZ', '000002.SZ']
            )
            engine.run()
            tushare_time = time.time() - start_time
            print(f"✓ Tushare数据源耗时: {tushare_time:.2f}秒")
        except Exception as e:
            print(f"✗ Tushare数据源测试失败: {e}")
            tushare_time = None
    else:
        tushare_time = None
    
    # 性能总结
    print("\n性能总结:")
    if csv_time:
        print(f"CSV数据源: {csv_time:.2f}秒 (离线数据，最快)")
    if tushare_time:
        print(f"Tushare数据源: {tushare_time:.2f}秒 (在线数据)")
        if csv_time:
            ratio = tushare_time / csv_time
            print(f"Tushare相对CSV慢 {ratio:.1f}倍")


def create_sample_config():
    """创建示例配置文件"""
    print("\n" + "="*60)
    print("创建示例配置文件")
    print("="*60)
    
    from ptradeSim.config import create_sample_config
    
    config_path = 'ptrade_config_sample.yaml'
    create_sample_config(config_path)
    print(f"✓ 示例配置文件已创建: {config_path}")
    
    # 显示配置文件内容
    print("\n配置文件内容:")
    print("-" * 40)
    with open(config_path, 'r', encoding='utf-8') as f:
        print(f.read())
    print("-" * 40)


def main():
    """主函数"""
    print("ptradeSim 真实数据源测试工具")
    print("="*60)
    
    print("此工具用于测试真实数据源的连接和功能")
    print("请确保您有稳定的网络连接")
    
    while True:
        print("\n请选择测试项目:")
        print("1. 测试Tushare数据源（需要token）")
        print("2. 测试AkShare数据源")
        print("3. 数据源性能对比")
        print("4. 创建示例配置文件")
        print("5. 退出")
        
        choice = input("\n请输入选择 (1-5): ").strip()
        
        if choice == '1':
            test_tushare_with_token()
        elif choice == '2':
            test_akshare_installation()
        elif choice == '3':
            test_data_source_comparison()
        elif choice == '4':
            create_sample_config()
        elif choice == '5':
            break
        else:
            print("无效选择，请重新输入")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    
    print("\n📝 使用提示:")
    print("1. Tushare需要注册账号获取token: https://tushare.pro")
    print("2. AkShare是免费开源项目，无需注册")
    print("3. 建议在策略开发时使用CSV数据源，部署时使用真实数据源")
    print("4. 可以配置多个数据源作为备用，提高系统稳定性")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断执行")
    except Exception as e:
        print(f"\n执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
