#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ptradeSim 命令行接口模块

提供 ptradesim 命令行工具的入口点
"""

import sys
import os

# 添加项目根目录到路径，确保可以导入 ptradeSim.py
# 从 src/ptradesim/cli.py 到项目根目录需要向上两级
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, current_dir)


def main():
    """命令行工具主入口点"""
    try:
        # 导入并执行主命令行脚本
        import subprocess
        ptrade_sim_path = os.path.join(current_dir, 'ptradeSim.py')
        
        if os.path.exists(ptrade_sim_path):
            # 执行 ptradeSim.py 并传递所有参数
            cmd = [sys.executable, ptrade_sim_path] + sys.argv[1:]
            result = subprocess.run(cmd, cwd=current_dir)
            sys.exit(result.returncode)
        else:
            print("❌ 错误: 找不到 ptradeSim.py 文件")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
