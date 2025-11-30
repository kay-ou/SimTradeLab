#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtradelab 发布脚本

自动化版本发布流程，包括：
1. 版本检查和验证
2. 构建和测试
3. 创建Git标签
4. 构建分发包
5. 生成发布说明
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """执行命令并返回结果"""
    print(f"执行命令: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        raise


def get_version_from_pyproject():
    """从 pyproject.toml 获取版本号"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("找不到 pyproject.toml 文件")

    content = pyproject_path.read_text(encoding="utf-8")
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not version_match:
        raise ValueError("无法从 pyproject.toml 中提取版本号")

    return version_match.group(1)


def check_git_status():
    """检查Git状态"""
    print("检查Git状态...")

    # 检查是否有未提交的更改
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("发现未提交的更改:")
        print(result.stdout)
        response = "y"  # 自动回答 'y'
        if response.lower() != "y":
            print("发布已取消")
            sys.exit(1)

    # 检查当前分支
    result = run_command("git branch --show-current")
    current_branch = result.stdout.strip()
    print(f"当前分支: {current_branch}")

    if current_branch != "main":
        response = "y"  # 自动回答 'y'
        if response.lower() != "y":
            print("发布已取消")
            sys.exit(1)


def run_tests():
    """运行测试"""
    print("运行测试...")
    try:
        run_command("poetry run pytest tests/ -v")
        print("所有测试通过")
    except subprocess.CalledProcessError:
        print("测试失败")
        response = "y"  # 自动回答 'y'
        if response.lower() != "y":
            sys.exit(1)


def build_package():
    """构建包"""
    print("构建包...")

    # 清理之前的构建
    for path in ["dist", "build"]:
        if Path(path).exists():
            shutil.rmtree(path)
    for file_pattern in ["*.egg-info", "*.egg-info/*"]:
        for f in Path(".").glob(file_pattern):
            if f.is_file():
                os.remove(f)
            elif f.is_dir():
                shutil.rmtree(f)

    # 构建包
    run_command("poetry build")

    # 检查构建结果
    dist_path = Path("dist")
    if not dist_path.exists() or not list(dist_path.glob("*")):
        raise RuntimeError("构建失败，没有生成分发文件")

    print("包构建成功")
    for file in dist_path.glob("*"):
        print(f"   {file.name}")


def create_git_tag(version):
    """创建Git标签"""
    print(f"创建Git标签 v{version}...")

    # 检查标签是否已存在
    result = run_command(f"git tag -l v{version}", check=False)
    if result.stdout.strip():
        print(f"标签 v{version} 已存在")
        response = "y"  # 自动回答 'y'
        if response.lower() == "y":
            run_command(f"git tag -d v{version}")
            run_command(f"git push origin :refs/tags/v{version}", check=False)
        else:
            print("发布已取消")
            sys.exit(1)

    # 创建标签
    tag_message = f"Release v{version}\n\nSee CHANGELOG.md for details."
    run_command(f'git tag -a v{version} -m "{tag_message}"')

    print(f"标签 v{version} 创建成功")


def generate_release_notes(version):
    """生成发布说明"""
    print("生成发布说明...")

    # 尝试使用自动生成脚本
    tag = f"v{version}"
    generate_script = Path("scripts/generate_release_notes.py")

    if generate_script.exists():
        try:
            print("使用自动生成脚本...")
            result = run_command(f"python {generate_script} {tag}")
            if result:
                print("自动生成Release Notes成功")
                # 读取生成的内容
                temp_file = Path(f"release-notes-{tag}.md")
                if temp_file.exists():
                    notes = temp_file.read_text(encoding="utf-8")
                    temp_file.unlink()  # 删除临时文件
                    return notes
        except Exception as e:
            print(f"自动生成失败，回退到CHANGELOG模式: {e}")

    # 回退到从CHANGELOG.md提取内容
    print("从CHANGELOG.md提取发布说明...")
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("找不到CHANGELOG.md文件")
        return "请查看项目文档了解更新内容。"

    content = changelog_path.read_text(encoding="utf-8")

    # 提取当前版本的内容
    version_pattern = rf"## \[{re.escape(version)}\].*?(?=## \[|\Z)"
    match = re.search(version_pattern, content, re.DOTALL)

    if match:
        return match.group(0).strip()
    else:
        print(f"在CHANGELOG.md中找不到版本 {version} 的内容")
        return f"Release v{version}\n\n请查看CHANGELOG.md了解详细更新内容。"


def create_release_notes_file(version, notes):
    """创建发布说明文件"""
    release_notes_path = Path(f"release-notes-v{version}.md")
    release_notes_path.write_text(notes)
    print(f"发布说明已保存到: {release_notes_path}")
    return release_notes_path


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="SimTradeLab 发布脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/release.py                    # 完整发布流程
  python scripts/release.py --skip-tests       # 跳过测试
  python scripts/release.py --dry-run          # 预览模式，不执行实际操作
        """,
    )

    parser.add_argument("--skip-tests", action="store_true", help="跳过测试步骤")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，显示将要执行的操作但不实际执行")

    return parser.parse_args()


def main():
    """主发布流程"""
    args = parse_arguments()

    print("SimTradeLab 发布流程开始")
    print("=" * 50)

    if args.dry_run:
        print("预览模式 - 不会执行实际操作")
    if args.skip_tests:
        print("跳过测试步骤")
    print()

    try:
        # 1. 获取版本信息
        version = get_version_from_pyproject()
        print(f"准备发布版本: v{version}")

        # 2. 检查Git状态
        if not args.dry_run:
            check_git_status()
        else:
            print("[预览] 检查Git状态")

        # 3. 运行测试 (可选)
        if not args.skip_tests:
            if not args.dry_run:
                run_tests()
            else:
                print("[预览] 运行测试")
        else:
            print("跳过测试步骤")

        # 4. 构建包
        if not args.dry_run:
            build_package()
        else:
            print("[预览] 构建包")

        # 5. 创建Git标签
        if not args.dry_run:
            create_git_tag(version)
        else:
            print("[预览] 创建Git标签")

        # 6. 生成发布说明
        if not args.dry_run:
            release_notes = generate_release_notes(version)
            notes_file = create_release_notes_file(version, release_notes)
        else:
            print("[预览] 生成发布说明")
            notes_file = f"release-notes-v{version}.md"

        print("\n" + "=" * 50)
        if args.dry_run:
            print("预览完成! (未执行实际操作)")
        else:
            print("发布准备完成!")
        print(f"版本: v{version}")
        if not args.dry_run:
            print(f"发布说明: {notes_file}")
            print("分发文件: dist/")

        print("\n下一步操作:")
        print("1. 推送标签到远程仓库:")
        print(f"   git push origin v{version}")
        print("\n2. 在GitHub上创建Release:")
        print("   - 访问: https://github.com/kay-ou/SimTradeLab/releases/new")
        print(f"   - 选择标签: v{version}")
        print(f"   - 复制发布说明: {notes_file}")
        if not args.dry_run:
            print("   - 上传分发文件: dist/*")
        print("\n3. 发布到PyPI (可选):")
        print("   poetry publish")

    except Exception as e:
        print(f"\n发布失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
