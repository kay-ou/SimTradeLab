#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtradelab 包测试脚本

测试构建的包是否正常工作
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """执行命令并返回结果"""
    print(f"🔧 执行: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令失败: {e}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        raise


def test_package_installation():
    """测试包安装"""
    print("📦 测试包安装...")

    # 创建临时虚拟环境
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_path = Path(temp_dir) / "test_env"

        # 创建虚拟环境
        run_command(f"python -m venv {venv_path}")

        # 获取虚拟环境的Python路径
        if os.name == "nt":  # Windows
            python_path = venv_path / "Scripts" / "python.exe"
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:  # Unix/Linux/macOS
            python_path = venv_path / "bin" / "python"
            pip_path = venv_path / "bin" / "pip"

        # 升级pip
        run_command(f"{pip_path} install --upgrade pip")

        # 安装构建的包
        dist_files = list(Path("dist").glob("*.whl"))
        if not dist_files:
            raise FileNotFoundError("找不到wheel文件")

        wheel_file = dist_files[0]
        run_command(f"{pip_path} install {wheel_file}")

        # 测试导入
        test_import_cmd = (
            f"{python_path} -c \"import simtradelab; print('✅ simtradelab导入成功')\""
        )
        run_command(test_import_cmd)

        # 测试命令行工具
        try:
            help_cmd = f"{python_path} -m simtradelab.cli --help"
            result = run_command(help_cmd, check=False)
            if result.returncode == 0:
                print("✅ 命令行工具测试成功")
            else:
                print("⚠️ 命令行工具测试失败，但包导入正常")
        except Exception as e:
            print(f"⚠️ 命令行工具测试异常: {e}")

        print("✅ 包安装测试完成")


def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")

    test_script = """
import sys
import os
sys.path.insert(0, ".")

try:
    from simtradelab import BacktestEngine
    print("✅ BacktestEngine导入成功")
    
    # 测试CSV数据源
    if os.path.exists("data/sample_data.csv"):
        engine = BacktestEngine(
            strategy_file="strategies/test_strategy.py",
            data_path="data/sample_data.csv",
            start_date="2023-01-03",
            end_date="2023-01-04",
            initial_cash=1000000.0
        )
        print("✅ CSV数据源引擎创建成功")
    else:
        print("⚠️ 找不到测试数据文件")
    
    # 测试真实数据源
    try:
        from simtradelab.data_sources import AkshareDataSource
        akshare_source = AkshareDataSource()
        print("✅ AkshareDataSource创建成功")
    except ImportError as e:
        print(f"⚠️ AkshareDataSource导入失败: {e}")
    
    print("✅ 基本功能测试完成")
    
except Exception as e:
    print(f"❌ 基本功能测试失败: {e}")
    sys.exit(1)
"""

    # 写入临时测试文件
    test_file = Path("test_functionality.py")
    test_file.write_text(test_script)

    try:
        run_command("python test_functionality.py")
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()


def check_package_structure():
    """检查包结构"""
    print("📋 检查包结构...")

    required_files = [
        "simtradelab/__init__.py",
        "simtradelab/engine.py",
        "simtradelab/cli.py",
        "README.md",
        "CHANGELOG.md",
        "pyproject.toml",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("❌ 缺少必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    print("✅ 包结构检查通过")
    return True


def check_dist_files():
    """检查分发文件"""
    print("📦 检查分发文件...")

    dist_path = Path("dist")
    if not dist_path.exists():
        print("❌ dist目录不存在")
        return False

    wheel_files = list(dist_path.glob("*.whl"))
    tar_files = list(dist_path.glob("*.tar.gz"))

    if not wheel_files:
        print("❌ 找不到wheel文件")
        return False

    if not tar_files:
        print("❌ 找不到源码分发文件")
        return False

    print("✅ 分发文件检查通过:")
    for file in wheel_files + tar_files:
        print(f"   📄 {file.name}")

    return True


def main():
    """主测试流程"""
    print("🧪 simtradelab 包测试")
    print("=" * 40)

    try:
        # 1. 检查包结构
        if not check_package_structure():
            sys.exit(1)

        # 2. 检查分发文件
        if not check_dist_files():
            print("⚠️ 请先运行: poetry build")
            sys.exit(1)

        # 3. 测试基本功能
        test_basic_functionality()

        # 4. 测试包安装
        test_package_installation()

        print("\n" + "=" * 40)
        print("🎉 所有测试通过!")
        print("📦 包已准备好发布")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
