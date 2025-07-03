# -*- coding: utf-8 -*-
"""
ptradeSim 完整测试套件运行器
包含所有核心功能和新增功能的测试
"""

import subprocess
import sys
from pathlib import Path

def run_test(test_name, test_command):
    """运行单个测试并返回结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ {test_name} - 成功")
            # 显示测试输出的关键信息
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if any(keyword in line for keyword in ['✅', '❌', '🎉', '测试', '通过', '失败']):
                    print(line)
            return True
        else:
            print(f"❌ {test_name} - 失败")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} - 超时")
        return False
    except Exception as e:
        print(f"💥 {test_name} - 异常: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 ptradeSim 完整测试套件运行器")
    print("=" * 60)
    
    # 检查前置条件
    required_files = [
        "data/sample_data.csv",
        "strategies/buy_and_hold.py",
        "strategies/test_strategy.py",
        "tests/test_api_injection.py",
        "tests/test_strategy_execution.py",
        "tests/test_financial_apis.py",
        "tests/test_market_data_apis.py"
    ]
    
    print("📋 检查前置条件...")
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"❌ 缺少文件: {file_path}")
        else:
            print(f"✅ 文件存在: {file_path}")
    
    if missing_files:
        print(f"\n❌ 缺少必要文件，无法运行测试:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return 1
    
    # 定义所有测试
    tests = [
        ("API注入测试", "poetry run python tests/test_api_injection.py"),
        ("策略执行测试", "poetry run python tests/test_strategy_execution.py"),
        ("财务接口测试", "poetry run python tests/test_financial_apis.py"),
        ("市场数据接口测试", "poetry run python tests/test_market_data_apis.py"),
    ]
    
    # 运行所有测试
    results = []
    for test_name, test_command in tests:
        success = run_test(test_name, test_command)
        results.append((test_name, success))
    
    # 显示测试总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"成功: {passed_tests}")
    print(f"失败: {failed_tests}")
    
    # 显示详细结果
    print("\n详细结果:")
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    if failed_tests == 0:
        print("\n🎉 所有测试通过！")
        print("\n📈 功能验证完成:")
        print("  ✅ 核心引擎功能正常")
        print("  ✅ API注入机制正常")
        print("  ✅ 策略执行流程正常")
        print("  ✅ 财务数据接口正常")
        print("  ✅ 市场数据接口正常")
        print("  ✅ 技术指标计算正常")
        print("  ✅ 实时数据模拟正常")
        return 0
    else:
        print(f"\n💥 有 {failed_tests} 个测试失败，请检查上述错误信息")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
