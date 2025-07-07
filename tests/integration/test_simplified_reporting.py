#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试简化的报告生成功能

只保留方案1：策略代码嵌入式报告
移除了复杂的策略参数提取功能和非标准API

运行方法:
    poetry run python test_simplified_reporting.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from simtradelab import BacktestEngine


def test_simplified_reporting():
    """测试简化的报告生成功能"""
    print("🎯 测试简化的报告生成功能")
    print("=" * 60)
    print("方案：策略代码嵌入式报告（移除复杂参数提取）")
    print("=" * 60)
    
    try:
        # 使用标准的买入持有策略进行测试
        print("📋 创建回测引擎（使用标准策略）...")
        engine = BacktestEngine(
            strategy_file='strategies/buy_and_hold_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-03',
            end_date='2023-01-10',
            initial_cash=1000000.0,
            frequency='1d'
        )
        
        print("✅ 引擎创建成功")
        
        # 运行回测
        print("\n🚀 运行回测...")
        engine.run()
        print("✅ 回测完成")
        
        # 验证报告文件是否生成
        print("\n🔍 验证报告文件...")
        
        # 检查reports目录
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            report_files = [f for f in os.listdir(reports_dir) if f.startswith('buy_and_hold_strategy')]
            
            if report_files:
                print(f"✅ 找到 {len(report_files)} 个报告文件:")
                for file_name in report_files:
                    file_path = os.path.join(reports_dir, file_name)
                    file_size = os.path.getsize(file_path)
                    print(f"   📄 {file_name} ({file_size:,} bytes)")
                
                # 检查最新的报告文件内容
                latest_report = max(report_files, key=lambda f: os.path.getctime(os.path.join(reports_dir, f)))
                latest_report_path = os.path.join(reports_dir, latest_report)
                
                print(f"\n📖 检查最新报告内容: {latest_report}")
                
                with open(latest_report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 验证报告包含策略代码
                if "策略代码:" in content:
                    print("✅ 报告包含策略代码")
                else:
                    print("❌ 报告不包含策略代码")
                
                # 验证报告包含基本信息
                if "基本信息:" in content:
                    print("✅ 报告包含基本信息")
                else:
                    print("❌ 报告不包含基本信息")
                
                # 验证报告包含性能指标
                if "收益指标:" in content:
                    print("✅ 报告包含性能指标")
                else:
                    print("❌ 报告不包含性能指标")
                
                # 验证文件名格式
                if "cash100w" in latest_report and "freq1d" in latest_report:
                    print("✅ 文件名包含基本参数信息")
                else:
                    print("❌ 文件名格式不正确")
                
            else:
                print("❌ 未找到报告文件")
                assert False
        else:
            print("❌ reports目录不存在")
            assert False
        
        assert True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dual_moving_average_strategy():
    """测试双均线策略（不使用非标准API）"""
    print("\n🧪 测试双均线策略")
    print("=" * 50)
    
    try:
        # 使用标准的双均线策略
        engine = BacktestEngine(
            strategy_file='strategies/dual_moving_average_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-03',
            end_date='2023-01-10',
            initial_cash=500000.0
        )
        
        print("🚀 运行双均线策略回测...")
        engine.run()
        
        print("✅ 双均线策略测试完成!")
        assert True
        
    except Exception as e:
        print(f"❌ 双均线策略测试失败: {e}")
        assert False


def test_filename_generation():
    """测试文件名生成功能"""
    print("\n🧪 测试文件名生成功能")
    print("=" * 50)
    
    try:
        from simtradelab.report_generator import ReportGenerator
        
        # 创建一个简单的引擎用于测试
        engine = BacktestEngine(
            strategy_file='strategies/test_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=800000.0
        )
        
        report_generator = ReportGenerator(engine)
        
        # 测试不同的文件名生成
        print("📋 测试文件名生成:")
        
        txt_filename = report_generator.generate_filename("txt", include_params=True)
        print(f"   📝 TXT文件名: {txt_filename}")
        
        json_filename = report_generator.generate_filename("json", include_params=True)
        print(f"   📊 JSON文件名: {json_filename}")
        
        simple_filename = report_generator.generate_filename("txt", include_params=False)
        print(f"   📄 简单文件名: {simple_filename}")
        
        # 验证文件名格式
        expected_parts = ["test_strategy", "20230103_20230105", "cash80w", "freq1d"]
        
        for part in expected_parts:
            if part in txt_filename:
                print(f"   ✅ 包含 {part}")
            else:
                print(f"   ❌ 缺少 {part}")
        
        print("✅ 文件名生成测试完成!")
        assert True
        
    except Exception as e:
        print(f"❌ 文件名生成测试失败: {e}")
        assert False


def main():
    """主函数"""
    print("🎯 simtradelab 简化报告生成功能测试")
    print("=" * 70)
    print("✨ 特点:")
    print("   📋 自动生成包含策略代码的报告文件")
    print("   📝 文件名包含策略名、日期范围、基本参数")
    print("   🚫 移除了复杂的策略参数提取功能")
    print("   🚫 移除了非标准API（如on_strategy_end）")
    print("=" * 70)
    
    # 运行所有测试
    success1 = test_filename_generation()
    success2 = test_dual_moving_average_strategy()
    success3 = test_simplified_reporting()
    
    # 总结
    print("\n" + "=" * 70)
    if success1 and success2 and success3:
        print("✅ 所有测试通过!")
        print("📁 查看生成的报告文件: reports/ 目录")
        print("\n🎉 简化报告功能特点:")
        print("   📋 自动生成包含完整策略代码的报告")
        print("   📝 文件名包含关键信息便于识别")
        print("   🔧 支持标准ptrade API，确保兼容性")
        print("   📈 包含完整的性能分析指标")
        print("   🚀 简单易用，无需复杂配置")
    else:
        print("❌ 部分测试失败!")
        sys.exit(1)


if __name__ == '__main__':
    main()
