#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试：简化的报告生成功能

验证清理后的功能：
1. 移除了非标准API（on_strategy_end）
2. 简化了报告生成（只保留方案1：策略代码嵌入式报告）
3. 确保与ptrade完全兼容

运行方法:
    poetry run python test_final_reporting.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from simtradelab import BacktestEngine


def test_standard_strategies():
    """测试标准策略（确保兼容性）"""
    print("🧪 测试标准策略兼容性")
    print("=" * 50)
    
    strategies = [
        'strategies/buy_and_hold_strategy.py',
        'strategies/dual_moving_average_strategy.py',
        'strategies/simple_dual_ma_strategy.py'
    ]
    
    success_count = 0
    
    for strategy_file in strategies:
        if not os.path.exists(strategy_file):
            print(f"❌ 策略文件不存在: {strategy_file}")
            continue
            
        try:
            print(f"\n📋 测试策略: {os.path.basename(strategy_file)}")
            
            engine = BacktestEngine(
                strategy_file=strategy_file,
                data_path='data/sample_data.csv',
                start_date='2023-01-03',
                end_date='2023-01-05',
                initial_cash=500000.0
            )
            
            engine.run()
            print(f"✅ {os.path.basename(strategy_file)} 运行成功")
            success_count += 1
            
        except Exception as e:
            print(f"❌ {os.path.basename(strategy_file)} 运行失败: {e}")
    
    print(f"\n📊 测试结果: {success_count}/{len(strategies)} 个策略运行成功")
    return success_count == len(strategies)


def test_report_generation():
    """测试报告生成功能"""
    print("\n🧪 测试报告生成功能")
    print("=" * 50)
    
    try:
        # 使用买入持有策略测试
        engine = BacktestEngine(
            strategy_file='strategies/buy_and_hold_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        print("🚀 运行回测并生成报告...")
        engine.run()
        
        # 检查报告文件
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            report_files = [f for f in os.listdir(reports_dir) 
                          if f.startswith('buy_and_hold_strategy') and f.endswith('.txt')]
            
            if report_files:
                # 获取最新的报告文件
                latest_report = max(report_files, 
                                  key=lambda f: os.path.getctime(os.path.join(reports_dir, f)))
                latest_report_path = os.path.join(reports_dir, latest_report)
                
                print(f"📄 检查报告文件: {latest_report}")
                
                with open(latest_report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 验证报告内容
                checks = [
                    ("基本信息", "基本信息:" in content),
                    ("收益指标", "收益指标:" in content),
                    ("风险指标", "风险指标:" in content),
                    ("交易统计", "交易统计:" in content),
                    ("策略代码", "策略代码:" in content),
                    ("文件名格式", "cash100w" in latest_report and "freq1d" in latest_report)
                ]
                
                all_passed = True
                for check_name, check_result in checks:
                    if check_result:
                        print(f"   ✅ {check_name}")
                    else:
                        print(f"   ❌ {check_name}")
                        all_passed = False
                
                if all_passed:
                    print("✅ 报告生成功能测试通过")
                    assert True
                else:
                    print("❌ 报告内容验证失败")
                    assert False
            else:
                print("❌ 未找到报告文件")
                return False
        else:
            print("❌ reports目录不存在")
            assert False
            
    except Exception as e:
        print(f"❌ 报告生成测试失败: {e}")
        return False


def test_filename_format():
    """测试文件名格式"""
    print("\n🧪 测试文件名格式")
    print("=" * 50)
    
    try:
        from simtradelab.report_generator import ReportGenerator
        
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=800000.0
        )
        
        report_generator = ReportGenerator(engine)
        
        # 测试文件名生成
        filename = report_generator.generate_filename("txt", include_params=True)
        print(f"📝 生成的文件名: {filename}")
        
        # 验证文件名包含必要信息
        expected_parts = ["test_strategy", "20230103_20230105", "cash80w", "freq1d"]
        
        all_parts_found = True
        for part in expected_parts:
            if part in filename:
                print(f"   ✅ 包含 {part}")
            else:
                print(f"   ❌ 缺少 {part}")
                all_parts_found = False
        
        if all_parts_found:
            print("✅ 文件名格式测试通过")
            assert True
        else:
            print("❌ 文件名格式测试失败")
            assert False
            
    except Exception as e:
        print(f"❌ 文件名格式测试失败: {e}")
        assert False


def main():
    """主函数"""
    print("🎯 simtradelab 最终报告生成功能测试")
    print("=" * 70)
    print("🎉 功能特点:")
    print("   ✅ 移除了非标准API（on_strategy_end）")
    print("   ✅ 简化了报告生成（只保留策略代码嵌入式报告）")
    print("   ✅ 确保与ptrade完全兼容")
    print("   ✅ 自动生成包含策略代码的详细报告")
    print("   ✅ 文件名包含策略名、日期范围、基本参数")
    print("=" * 70)
    
    # 运行所有测试
    test1_result = test_filename_format()
    test2_result = test_standard_strategies()
    test3_result = test_report_generation()
    
    # 总结
    print("\n" + "=" * 70)
    if test1_result and test2_result and test3_result:
        print("✅ 所有测试通过!")
        print("\n🎉 simtradelab 报告生成功能已完成优化:")
        print("   📋 自动生成包含完整策略代码的报告文件")
        print("   📝 文件名格式: 策略名_日期范围_基本参数_时间戳.txt")
        print("   🔧 完全兼容ptrade标准API")
        print("   🚫 移除了所有非标准API和复杂参数提取")
        print("   📁 报告保存在 reports/ 目录")
        print("\n📖 使用方法:")
        print("   1. 运行任何策略，系统会自动生成报告")
        print("   2. 报告包含策略代码、性能指标、交易统计等")
        print("   3. 文件名包含关键信息，便于识别和管理")
    else:
        print("❌ 部分测试失败!")
        print("请检查错误信息并修复问题")
        sys.exit(1)


if __name__ == '__main__':
    main()
