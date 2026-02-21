#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimTradeLab 发布脚本

根据 docs/RELEASE.md 的流程自动化版本发布：
1. 更新版本号（可选）
2. 提交版本更新
3. 创建 Git 标签
4. 构建包（可选）
5. 推送到远程（可选）
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


def update_version_in_files(version):
    """更新所有文件中的版本号"""
    print(f"更新版本号至: {version}")

    # 1. 更新 pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("找不到 pyproject.toml 文件")

    content = pyproject_path.read_text(encoding="utf-8")

    # 替换版本号（只在 [tool.poetry] 部分）
    new_content = re.sub(
        r'(\[tool\.poetry\].*?^name\s*=\s*"[^"]+"\s*^version\s*=\s*")[^"]+(")',
        rf'\g<1>{version}\g<2>',
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    pyproject_path.write_text(new_content, encoding="utf-8")
    print("  ✓ pyproject.toml")

    # 2. 更新 README.md
    readme_path = Path("README.md")
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")

        # Badge 版本号
        content = re.sub(
            r'(!\[Version\]\(https://img\.shields\.io/badge/Version-)[^-]+(-orange\.svg\)\]\(#\))',
            rf'\g<1>{version}\g<2>',
            content
        )

        # 当前版本
        content = re.sub(
            r'(\*\*当前版本：\*\*\s+v)[0-9]+\.[0-9]+\.[0-9]+',
            rf'\g<1>{version}',
            content
        )

        # pip install 示例
        content = re.sub(
            r'(pip install simtradelab==)[0-9]+\.[0-9]+\.[0-9]+',
            rf'\g<1>{version}',
            content
        )

        readme_path.write_text(content, encoding="utf-8")
        print("  ✓ README.md")

    print("版本号更新完成")


def commit_version_update(version):
    """提交版本更新"""
    print("提交版本更新...")
    run_command("git add scripts/release.py pyproject.toml README.md")

    commit_msg = f"chore: bump version to {version}"
    run_command(f'git commit -m "{commit_msg}"')
    print("版本更新已提交")


def check_git_status():
    """检查Git状态"""
    print("检查Git状态...")

    # 检查是否有未提交的更改
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("警告：发现未提交的更改")
        print(result.stdout)

    # 检查当前分支
    result = run_command("git branch --show-current")
    current_branch = result.stdout.strip()
    print(f"当前分支: {current_branch}")

    if current_branch != "main":
        print("警告：当前不在 main 分支")


def run_tests():
    """运行测试"""
    print("运行测试...")
    try:
        run_command("poetry run pytest tests/ -v")
        print("所有测试通过")
    except subprocess.CalledProcessError:
        print("测试失败")
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
        print("删除旧标签...")
        run_command(f"git tag -d v{version}")
        run_command(f"git push origin :refs/tags/v{version}", check=False)

    # 创建标签
    tag_message = "Release v{}"
    run_command(f'git tag -a v{version} -m \"{tag_message}\"')

    print(f"标签 v{version} 创建成功")


def push_to_remote(version, push_tag_only=False):
    """推送到远程仓库"""
    if not push_tag_only:
        print("推送代码到远程...")
        run_command("git push origin main")

    print("推送标签到远程...")
    run_command(f"git push origin v{version}")
    print("推送完成")


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="SimTradeLab 发布脚本（根据 docs/RELEASE.md）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python scripts/release.py --version 1.2.3              # 更新版本号、提交、打标签
  python scripts/release.py --version 1.2.3 --push       # 更新版本号、提交、打标签并推送
  python scripts/release.py --version 1.2.3 --build      # 更新版本号、提交、打标签、构建
  python scripts/release.py --build                       # 仅构建（使用当前版本号）
  python scripts/release.py --tag-only                    # 仅创建标签（使用当前版本号）

发布流程（根据 docs/RELEASE.md）：
  1. 运行脚本更新版本并创建标签
  2. 检查本地构建是否成功
  3. 推送到远程：git push origin main && git push origin v1.2.3
  4. 在 GitHub 网页手动创建 Release（填写 release notes）
  5. GitHub Actions 自动构建并发布到 PyPI
        """,
    )

    parser.add_argument(
        "--version",
        help="新版本号（格式：x.y.z），会自动更新文件并提交"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="跳过测试步骤"
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="构建包"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="推送到远程仓库（包括代码和标签）"
    )
    parser.add_argument(
        "--tag-only",
        action="store_true",
        help="仅创建并推送标签（不更新版本号）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，不执行实际操作"
    )

    return parser.parse_args()


def main():
    """主发布流程"""
    args = parse_arguments()

    print("SimTradeLab 发布流程")
    print("=" * 60)

    if args.dry_run:
        print("预览模式 - 不会执行实际操作")
    print()

    try:
        current_version = get_version_from_pyproject()

        # 模式1: 仅创建标签
        if args.tag_only:
            print("模式：仅创建标签")
            print(f"当前版本: {current_version}")
            print()

            if not args.dry_run:
                check_git_status()
                create_git_tag(current_version)
                if args.push:
                    push_to_remote(current_version, push_tag_only=True)
                else:
                    print()
                    print("下一步：推送标签")
                    print(f"  git push origin v{current_version}")
            else:
                print(f"[预览] 创建标签 v{current_version}")

            return

        # 模式2: 更新版本号并发布
        if args.version:
            # 验证版本号格式
            if not re.match(r'^\d+\.\d+\.\d+$', args.version):
                print("错误：版本号格式无效，应为 x.y.z 格式（如 1.2.3）")
                sys.exit(1)

            print("模式：更新版本并发布")
            print(f"当前版本: {current_version}")
            print(f"目标版本: {args.version}")
            print()

            if not args.dry_run:
                # 1. 更新版本号
                update_version_in_files(args.version)

                # 2. 提交版本更新
                commit_version_update(args.version)
                print()

                # 3. 检查状态
                check_git_status()

                # 4. 运行测试（可选）
                if not args.skip_tests:
                    run_tests()
                else:
                    print("跳过测试")

                # 5. 构建包（可选）
                if args.build:
                    build_package()

                # 6. 创建标签
                create_git_tag(args.version)

                # 7. 推送（可选）
                if args.push:
                    push_to_remote(args.version)

                version = args.version
            else:
                print("[预览] 更新版本号")
                print("[预览] 提交更改")
                print("[预览] 创建标签")
                if args.build:
                    print("[预览] 构建包")
                if args.push:
                    print("[预览] 推送到远程")
                version = args.version

        # 模式3: 仅构建
        elif args.build:
            print("模式：仅构建")
            print(f"当前版本: {current_version}")
            print()

            if not args.dry_run:
                build_package()
            else:
                print("[预览] 构建包")

            version = current_version

        else:
            print("错误：请指定操作模式")
            print()
            print("示例:")
            print("  --version 1.2.3        更新版本号并创建标签")
            print("  --tag-only             仅创建标签")
            print("  --build                仅构建包")
            print()
            print("运行 --help 查看详细说明")
            sys.exit(1)

        # 显示完成信息
        print()
        print("=" * 60)
        if args.dry_run:
            print("预览完成！")
        else:
            print("完成！")
        print()
        print(f"版本: v{version}")

        if args.build and not args.dry_run:
            print("构建文件: dist/")
            for file in Path("dist").glob("*"):
                print(f"  - {file.name}")

        if not args.push:
            print()
            print("下一步操作（根据 docs/RELEASE.md）：")
            print()
            print("1. 推送到远程仓库：")
            print("   git push origin main")
            print(f"   git push origin v{version}")
            print()
            print("2. 在 GitHub 创建 Release：")
            print("   https://github.com/kay-ou/SimTradeLab/releases/new")
            print(f"   - 选择标签: v{version}")
            print("   - 填写 Release 标题和说明")
            print()
            print("3. GitHub Actions 会自动构建并发布到 PyPI")
            print()
            print("4. 验证发布：")
            print("   https://pypi.org/project/simtradelab/")

    except Exception as e:
        print()
        print(f"发布失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
