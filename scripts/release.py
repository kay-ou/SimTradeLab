#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimTradeLab 发布脚本

流程：
1. 更新 pyproject.toml 和 README.md 的版本号
2. 提交 "chore: bump version to x.y.z"
3. push 到 main 后，GitHub Actions 自动创建 tag、Release 并发布到 PyPI
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
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
        print(result.stdout, end="")
    return result


def get_version_from_pyproject():
    content = Path("pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not m:
        raise ValueError("无法从 pyproject.toml 提取版本号")
    return m.group(1)


def update_version_in_files(version):
    print("更新版本号至: {}".format(version))

    pyproject = Path("pyproject.toml")
    content = pyproject.read_text(encoding="utf-8")
    content = re.sub(
        r'(\[tool\.poetry\].*?^name\s*=\s*"[^"]+"\s*^version\s*=\s*")[^"]+(")',
        r'\g<1>{}\g<2>'.format(version),
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    pyproject.write_text(content, encoding="utf-8")
    print("  ✓ pyproject.toml")

    for readme_name in ["README.md", "README.zh-CN.md"]:
        readme = Path(readme_name)
        if readme.exists():
            content = readme.read_text(encoding="utf-8")
            content = re.sub(
                r'(!\[Version\]\(https://img\.shields\.io/badge/Version-)[^-]+(-orange\.svg\)\]\(#\))',
                r'\g<1>{}\g<2>'.format(version),
                content,
            )
            content = re.sub(
                r'(\*\*当前版本：\*\*\s+v)[0-9]+\.[0-9]+\.[0-9]+',
                r'\g<1>{}'.format(version),
                content,
            )
            content = re.sub(
                r'(\*\*Current version:\*\*\s+v)[0-9]+\.[0-9]+\.[0-9]+',
                r'\g<1>{}'.format(version),
                content,
            )
            content = re.sub(
                r'(pip install simtradelab==)[0-9]+\.[0-9]+\.[0-9]+',
                r'\g<1>{}'.format(version),
                content,
            )
            readme.write_text(content, encoding="utf-8")
            print("  ✓ {}".format(readme_name))


def commit_version_update(version):
    run_command("git add pyproject.toml README.md README.zh-CN.md")
    run_command('git commit -m "chore: bump version to {}"'.format(version))


def run_tests():
    print("运行测试...")
    try:
        run_command("poetry run pytest tests/ -q")
        print("测试通过")
    except subprocess.CalledProcessError:
        print("测试失败，终止发布")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="SimTradeLab 发布脚本")
    parser.add_argument("--version", required=True, help="新版本号（格式：x.y.z）")
    parser.add_argument("--skip-tests", action="store_true", help="跳过测试")
    args = parser.parse_args()

    if not re.match(r'^\d+\.\d+\.\d+$', args.version):
        print("错误：版本号格式无效，应为 x.y.z")
        sys.exit(1)

    current = get_version_from_pyproject()
    print("当前版本: {}  →  目标版本: {}".format(current, args.version))

    if not args.skip_tests:
        run_tests()

    update_version_in_files(args.version)
    commit_version_update(args.version)

    print()
    print("完成。下一步：")
    print("  git push origin main")
    print("  GitHub Actions 将自动创建 tag、Release 并发布到 PyPI")


if __name__ == "__main__":
    main()
