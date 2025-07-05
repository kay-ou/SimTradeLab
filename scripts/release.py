#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ptradeSim 发布脚本

自动化版本发布流程，包括：
1. 版本检查和验证
2. 构建和测试
3. 创建Git标签
4. 构建分发包
5. 生成发布说明
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime


def run_command(cmd, cwd=None, check=True):
    """执行命令并返回结果"""
    print(f"🔧 执行命令: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=check,
            capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        raise


def get_version_from_pyproject():
    """从 pyproject.toml 获取版本号"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("找不到 pyproject.toml 文件")
    
    content = pyproject_path.read_text()
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not version_match:
        raise ValueError("无法从 pyproject.toml 中提取版本号")
    
    return version_match.group(1)


def check_git_status():
    """检查Git状态"""
    print("📋 检查Git状态...")
    
    # 检查是否有未提交的更改
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("⚠️ 发现未提交的更改:")
        print(result.stdout)
        response = input("是否继续发布? (y/N): ")
        if response.lower() != 'y':
            print("❌ 发布已取消")
            sys.exit(1)
    
    # 检查当前分支
    result = run_command("git branch --show-current")
    current_branch = result.stdout.strip()
    print(f"📍 当前分支: {current_branch}")
    
    if current_branch != "main":
        response = input(f"当前不在main分支 ({current_branch})，是否继续? (y/N): ")
        if response.lower() != 'y':
            print("❌ 发布已取消")
            sys.exit(1)


def run_tests():
    """运行测试"""
    print("🧪 运行测试...")
    try:
        run_command("poetry run pytest tests/ -v")
        print("✅ 所有测试通过")
    except subprocess.CalledProcessError:
        print("❌ 测试失败")
        response = input("是否忽略测试失败继续发布? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)


def build_package():
    """构建包"""
    print("📦 构建包...")
    
    # 清理之前的构建
    run_command("rm -rf dist/ build/ *.egg-info/")
    
    # 构建包
    run_command("poetry build")
    
    # 检查构建结果
    dist_path = Path("dist")
    if not dist_path.exists() or not list(dist_path.glob("*")):
        raise RuntimeError("构建失败，没有生成分发文件")
    
    print("✅ 包构建成功")
    for file in dist_path.glob("*"):
        print(f"   📄 {file.name}")


def create_git_tag(version):
    """创建Git标签"""
    print(f"🏷️ 创建Git标签 v{version}...")
    
    # 检查标签是否已存在
    result = run_command(f"git tag -l v{version}", check=False)
    if result.stdout.strip():
        print(f"⚠️ 标签 v{version} 已存在")
        response = input("是否删除现有标签并重新创建? (y/N): ")
        if response.lower() == 'y':
            run_command(f"git tag -d v{version}")
            run_command(f"git push origin :refs/tags/v{version}", check=False)
        else:
            print("❌ 发布已取消")
            sys.exit(1)
    
    # 创建标签
    tag_message = f"Release v{version}\n\nSee CHANGELOG.md for details."
    run_command(f'git tag -a v{version} -m "{tag_message}"')
    
    print(f"✅ 标签 v{version} 创建成功")


def generate_release_notes(version):
    """生成发布说明"""
    print("📝 生成发布说明...")
    
    # 从CHANGELOG.md提取当前版本的更新内容
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("⚠️ 找不到CHANGELOG.md文件")
        return "请查看项目文档了解更新内容。"
    
    content = changelog_path.read_text()
    
    # 提取当前版本的内容
    version_pattern = rf"## \[{re.escape(version)}\].*?(?=## \[|\Z)"
    match = re.search(version_pattern, content, re.DOTALL)
    
    if match:
        return match.group(0).strip()
    else:
        print(f"⚠️ 在CHANGELOG.md中找不到版本 {version} 的内容")
        return f"Release v{version}\n\n请查看CHANGELOG.md了解详细更新内容。"


def create_release_notes_file(version, notes):
    """创建发布说明文件"""
    release_notes_path = Path(f"release-notes-v{version}.md")
    release_notes_path.write_text(notes)
    print(f"📄 发布说明已保存到: {release_notes_path}")
    return release_notes_path


def main():
    """主发布流程"""
    print("🚀 ptradeSim 发布流程开始")
    print("=" * 50)
    
    try:
        # 1. 获取版本信息
        version = get_version_from_pyproject()
        print(f"📋 准备发布版本: v{version}")
        
        # 2. 检查Git状态
        check_git_status()
        
        # 3. 运行测试
        run_tests()
        
        # 4. 构建包
        build_package()
        
        # 5. 创建Git标签
        create_git_tag(version)
        
        # 6. 生成发布说明
        release_notes = generate_release_notes(version)
        notes_file = create_release_notes_file(version, release_notes)
        
        print("\n" + "=" * 50)
        print("🎉 发布准备完成!")
        print(f"📋 版本: v{version}")
        print(f"📄 发布说明: {notes_file}")
        print(f"📦 分发文件: dist/")
        
        print("\n📋 下一步操作:")
        print("1. 推送标签到远程仓库:")
        print(f"   git push origin v{version}")
        print("\n2. 在GitHub上创建Release:")
        print(f"   - 访问: https://github.com/kay-ou/ptradesim/releases/new")
        print(f"   - 选择标签: v{version}")
        print(f"   - 复制发布说明: {notes_file}")
        print(f"   - 上传分发文件: dist/*")
        print("\n3. 发布到PyPI (可选):")
        print("   poetry publish")
        
    except Exception as e:
        print(f"\n❌ 发布失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
