#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ptradeSim 测试运行器

这个脚本提供了一个简单的方式来运行所有测试。
"""

import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            print(result.stdout)
        else:
            print(f"❌ {description} - 失败")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ {description} - 异常: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 ptradeSim 测试套件运行器")
    print("=" * 60)
    
    # 检查前置条件
    required_files = [
        "data/sample_data.csv",
        "strategies/buy_and_hold.py",
        "tests/test_api_injection.py",
        "tests/test_strategy_execution.py"
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
    
    # 运行测试
    tests = [
        ("poetry run python tests/test_api_injection.py", "API注入测试"),
        ("poetry run python tests/test_strategy_execution.py", "策略执行测试"),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for cmd, description in tests:
        if run_command(cmd, description):
            success_count += 1
    
    # 显示总结
    print(f"\n{'='*60}")
    print(f"📊 测试总结")
    print(f"{'='*60}")
    print(f"总测试数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查上面的错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
