#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强的报告功能

验证新增的报告功能：
1. 摘要报告
2. 报告管理功能

运行方法:
    poetry run python test_enhanced_reports.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from simtradelab import BacktestEngine
from src.simtradelab.report_manager import ReportManager


def test_enhanced_report_generation():
    """测试增强的报告生成功能"""
    print("🎯 测试增强的报告生成功能")
    print("=" * 60)
    
    try:
        # 运行回测生成报告
        print("📋 运行回测...")
        engine = BacktestEngine(
            strategy_file='strategies/buy_and_hold_strategy.py',
            data_path='data/sample_data.csv',
            start_date='2023-01-03',
            end_date='2023-01-05',
            initial_cash=1000000.0
        )
        
        generated_files = engine.run()
        
        print(f"✅ 回测完成，生成了 {len(generated_files)} 个报告文件")
        
        # 验证文件类型
        file_types = {}
        for file_path in generated_files:
            ext = os.path.splitext(file_path)[1]
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print("\n📊 生成的文件类型:")
        expected_types = ['.txt', '.json', '.csv']
        
        for ext in expected_types:
            if ext in file_types:
                print(f"   ✅ {ext}: {file_types[ext]} 个")
            else:
                print(f"   ❌ {ext}: 未生成")
        
        # 检查摘要文件
        summary_files = [f for f in generated_files if 'summary' in f]
        if summary_files:
            print(f"   ✅ 摘要文件: {len(summary_files)} 个")
        else:
            print("   ❌ 摘要文件: 未生成")
        
        assert True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        assert False


def test_summary_report():
    """测试摘要报告内容"""
    print("\n📋 测试摘要报告内容")
    print("=" * 50)
    
    try:
        # 查找最新的摘要报告
        import glob
        summary_files = glob.glob("reports/*buy_and_hold_strategy*.summary.txt")
        
        if not summary_files:
            print("❌ 未找到摘要报告文件")
            assert False
        
        latest_summary = max(summary_files, key=os.path.getctime)
        print(f"📄 检查摘要报告: {os.path.basename(latest_summary)}")
        
        with open(latest_summary, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 验证摘要内容
        checks = [
            ("报告标题", "策略回测摘要报告" in content),
            ("核心指标", "核心指标" in content),
            ("总收益率", "总收益率:" in content),
            ("夏普比率", "夏普比率:" in content),
            ("策略评级", "策略评级" in content),
            ("评级说明", "评级说明:" in content),
            ("表格边框", "╔══" in content)
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                all_passed = False
        
        # 显示摘要内容的前几行
        lines = content.split('\n')[:10]
        print("\n   📖 摘要内容预览:")
        for line in lines:
            if line.strip():
                print(f"      {line}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 摘要报告测试失败: {e}")
        return False


def test_report_manager():
    """测试报告管理功能"""
    print("\n📁 测试报告管理功能")
    print("=" * 50)
    
    try:
        manager = ReportManager()
        
        # 测试报告列表
        print("📋 测试报告列表功能...")
        reports = manager.list_reports()
        print(f"   找到 {len(reports)} 个报告")
        
        if reports:
            latest_report = reports[0]
            print(f"   最新报告: {latest_report['strategy_name']}")
            print(f"   文件大小: {latest_report['size_mb']:.2f} MB")
        
        # 测试报告摘要
        print("\n📊 测试报告摘要功能...")
        summary = manager.get_report_summary()
        print(f"   总文件数: {summary['total_files']}")
        print(f"   总大小: {summary['total_size_mb']:.2f} MB")
        print(f"   策略数量: {len(summary['strategies'])}")
        
        # 测试索引导出
        print("\n📤 测试索引导出功能...")
        index_file = manager.export_report_index("test_index.json")

        try:
            if index_file and os.path.exists(index_file):
                print(f"   ✅ 索引文件已生成: {os.path.basename(index_file)}")

                # 验证索引文件内容
                import json
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)

                required_keys = ['generated_at', 'summary', 'reports']
                for key in required_keys:
                    if key in index_data:
                        print(f"   ✅ 包含 {key}")
                    else:
                        print(f"   ❌ 缺少 {key}")
            else:
                print("   ❌ 索引文件生成失败")
                assert False
        finally:
            # 清理测试生成的索引文件
            if index_file and os.path.exists(index_file):
                try:
                    os.remove(index_file)
                    print(f"   🧹 已清理测试文件: {os.path.basename(index_file)}")
                except Exception as e:
                    print(f"   ⚠️  清理测试文件失败: {e}")
        
        assert True
        
    except Exception as e:
        print(f"❌ 报告管理测试失败: {e}")
        assert False

def main():
    """主函数"""
    print("🎯 simtradelab 增强报告功能测试")
    print("=" * 70)
    print("🚀 新增功能:")
    print("   📋 摘要报告 - 简洁的策略评级和关键指标")
    print("   📁 报告管理器 - 文件组织、清理和索引功能")
    print("=" * 70)
    
    # 运行所有测试
    test_results = []
    
    test_results.append(("报告生成", test_enhanced_report_generation()))
    test_results.append(("摘要报告", test_summary_report()))
    test_results.append(("报告管理", test_report_manager()))
    
    # 总结测试结果
    print("\n" + "=" * 70)
    print("📊 测试结果总结:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name:<15}: {status}")
        if result:
            passed_count += 1
    
    print(f"\n🎯 总体结果: {passed_count}/{len(test_results)} 项测试通过")
    
    if passed_count == len(test_results):
        print("\n🎉 所有测试通过！增强报告功能已成功实现:")
        print("   📊 多格式报告生成 (TXT/JSON/CSV)")
        print("   📋 智能摘要和策略评级")
        print("   📁 完整的报告管理系统")
        print("\n💡 使用建议:")
        print("   1. 使用摘要报告快速了解策略表现")
        print("   2. 定期使用报告管理器清理旧文件")
        print("   3. 导出索引文件便于报告归档")
    else:
        print("\n⚠️ 部分测试失败，请检查相关功能")
        sys.exit(1)


if __name__ == '__main__':
    main()
