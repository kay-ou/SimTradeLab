#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动生成Release Notes脚本

基于Git提交历史、CHANGELOG.md和GitHub API自动生成Release Notes
"""

import os
import re
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def run_command(cmd: str, cwd: Optional[str] = None) -> str:
    """执行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, check=True,
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {cmd}")
        print(f"错误: {e.stderr}")
        return ""


def get_version_from_pyproject() -> str:
    """从pyproject.toml获取版本号"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return "unknown"
    
    content = pyproject_path.read_text()
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    return version_match.group(1) if version_match else "unknown"


def get_git_info(tag: str) -> Dict[str, str]:
    """获取Git相关信息"""
    info = {}
    
    # 获取上一个标签
    previous_tag = run_command(f"git describe --tags --abbrev=0 {tag}^")
    info['previous_tag'] = previous_tag if previous_tag else "HEAD"
    
    # 获取提交数量
    commit_count = run_command(f"git rev-list --count {info['previous_tag']}..{tag}")
    info['commit_count'] = commit_count if commit_count else "0"
    
    # 获取文件变更数量
    files_changed = run_command(f"git diff --name-only {info['previous_tag']}..{tag} | wc -l")
    info['files_changed'] = files_changed if files_changed else "0"
    
    # 获取贡献者
    contributors = run_command(f"git log {info['previous_tag']}..{tag} --format='%an' | sort | uniq")
    info['contributors'] = contributors.split('\n') if contributors else []
    info['contributor_count'] = str(len(info['contributors']))
    
    return info


def parse_commits(tag: str, previous_tag: str) -> Dict[str, List[str]]:
    """解析提交信息并分类"""
    commits = run_command(f"git log {previous_tag}..{tag} --format='%s'")
    if not commits:
        return {
            'new_features': [],
            'improvements': [],
            'bug_fixes': [],
            'documentation': [],
            'breaking_changes': []
        }
    
    commit_lines = commits.split('\n')
    categorized = {
        'new_features': [],
        'improvements': [],
        'bug_fixes': [],
        'documentation': [],
        'breaking_changes': []
    }
    
    for commit in commit_lines:
        commit = commit.strip()
        if not commit:
            continue
            
        # 根据conventional commits规范分类
        if commit.startswith('feat'):
            categorized['new_features'].append(commit)
        elif commit.startswith('fix'):
            categorized['bug_fixes'].append(commit)
        elif commit.startswith('docs'):
            categorized['documentation'].append(commit)
        elif commit.startswith('perf') or commit.startswith('refactor'):
            categorized['improvements'].append(commit)
        elif 'BREAKING CHANGE' in commit or commit.startswith('feat!') or commit.startswith('fix!'):
            categorized['breaking_changes'].append(commit)
        else:
            # 根据关键词分类
            commit_lower = commit.lower()
            if any(keyword in commit_lower for keyword in ['add', 'new', 'feature', '新增', '添加']):
                categorized['new_features'].append(commit)
            elif any(keyword in commit_lower for keyword in ['fix', 'bug', 'issue', '修复', '解决']):
                categorized['bug_fixes'].append(commit)
            elif any(keyword in commit_lower for keyword in ['improve', 'enhance', 'optimize', '优化', '改进']):
                categorized['improvements'].append(commit)
            elif any(keyword in commit_lower for keyword in ['doc', 'readme', '文档']):
                categorized['documentation'].append(commit)
            else:
                categorized['improvements'].append(commit)
    
    return categorized


def parse_changelog(version: str) -> Dict[str, str]:
    """从CHANGELOG.md解析版本信息"""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        return {}
    
    content = changelog_path.read_text(encoding='utf-8')
    
    # 查找对应版本的内容
    version_pattern = rf"## \[{re.escape(version)}\].*?\n(.*?)(?=## \[|\Z)"
    match = re.search(version_pattern, content, re.DOTALL)
    
    if not match:
        return {}
    
    version_content = match.group(1).strip()
    
    # 解析不同类型的变更
    sections = {
        'new_features': [],
        'improvements': [],
        'bug_fixes': [],
        'documentation': [],
        'breaking_changes': []
    }
    
    # 根据markdown标题分类
    current_section = None
    for line in version_content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('### '):
            section_title = line[4:].lower()
            if '新增' in section_title or 'feature' in section_title:
                current_section = 'new_features'
            elif '修复' in section_title or 'fix' in section_title or 'bug' in section_title:
                current_section = 'bug_fixes'
            elif '改进' in section_title or 'improve' in section_title or 'enhance' in section_title:
                current_section = 'improvements'
            elif '文档' in section_title or 'doc' in section_title:
                current_section = 'documentation'
            elif '破坏' in section_title or 'breaking' in section_title:
                current_section = 'breaking_changes'
            else:
                current_section = 'improvements'
        elif line.startswith('- ') and current_section:
            sections[current_section].append(line[2:])
    
    return sections


def format_section(items: List[str], prefix: str = "- ") -> str:
    """格式化章节内容"""
    if not items:
        return "无"
    
    formatted_items = []
    for item in items:
        # 清理提交信息格式
        item = re.sub(r'^(feat|fix|docs|style|refactor|perf|test|chore)(\(.+?\))?\s*:\s*', '', item)
        item = item.strip()
        if item:
            formatted_items.append(f"{prefix}{item}")
    
    return '\n'.join(formatted_items)


def generate_release_notes(tag: str, output_file: Optional[str] = None) -> str:
    """生成Release Notes"""
    print(f"🎯 生成 {tag} 的Release Notes...")
    
    # 获取版本信息
    version = tag.lstrip('v')
    
    # 获取Git信息
    git_info = get_git_info(tag)
    
    # 解析提交信息
    commits_info = parse_commits(tag, git_info['previous_tag'])
    
    # 尝试从CHANGELOG解析信息
    changelog_info = parse_changelog(version)
    
    # 合并信息（优先使用CHANGELOG中的信息）
    for key in commits_info:
        if key in changelog_info and changelog_info[key]:
            commits_info[key] = changelog_info[key]
    
    # 读取模板
    template_path = Path(".github/release-template.md")
    if template_path.exists():
        template = template_path.read_text(encoding='utf-8')
    else:
        template = create_default_template()
    
    # 替换模板变量
    release_notes = template.replace('{{tag_name}}', tag)
    release_notes = release_notes.replace('{{version}}', version)
    release_notes = release_notes.replace('{{release_date}}', datetime.now().strftime('%Y-%m-%d'))
    release_notes = release_notes.replace('{{previous_tag}}', git_info['previous_tag'])
    release_notes = release_notes.replace('{{commit_count}}', git_info['commit_count'])
    release_notes = release_notes.replace('{{contributor_count}}', git_info['contributor_count'])
    release_notes = release_notes.replace('{{files_changed}}', git_info['files_changed'])
    
    # 格式化各个章节
    release_notes = release_notes.replace('{{new_features}}', format_section(commits_info['new_features']))
    release_notes = release_notes.replace('{{improvements}}', format_section(commits_info['improvements']))
    release_notes = release_notes.replace('{{bug_fixes}}', format_section(commits_info['bug_fixes']))
    release_notes = release_notes.replace('{{documentation}}', format_section(commits_info['documentation']))
    release_notes = release_notes.replace('{{breaking_changes}}', format_section(commits_info['breaking_changes']))
    
    # 格式化贡献者列表
    contributors_text = '\n'.join([f"- @{contributor}" for contributor in git_info['contributors']])
    release_notes = release_notes.replace('{{contributors}}', contributors_text)
    
    # 确定发布类型
    if commits_info['breaking_changes']:
        release_type = "重大更新 (Major)"
    elif commits_info['new_features']:
        release_type = "功能更新 (Minor)"
    else:
        release_type = "补丁更新 (Patch)"
    
    release_notes = release_notes.replace('{{release_type}}', release_type)
    
    # 保存到文件
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(release_notes, encoding='utf-8')
        print(f"✅ Release Notes已保存到: {output_path}")
    
    return release_notes


def create_default_template() -> str:
    """创建默认模板"""
    return """# 🎉 SimTradeLab {{tag_name}} 发布

## ✨ 新增功能
{{new_features}}

## 🔧 改进优化
{{improvements}}

## 🐛 问题修复
{{bug_fixes}}

## 📚 文档更新
{{documentation}}

## ⚠️ 破坏性变更
{{breaking_changes}}

## 📦 安装方法
```bash
pip install simtradelab=={{version}}
```

**完整变更日志**: https://github.com/kay-ou/SimTradeLab/compare/{{previous_tag}}...{{tag_name}}
"""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成Release Notes')
    parser.add_argument('tag', help='Git标签名称')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--print', '-p', action='store_true', help='打印到控制台')
    
    args = parser.parse_args()
    
    try:
        release_notes = generate_release_notes(args.tag, args.output)
        
        if args.print:
            print("\n" + "="*60)
            print("📋 生成的Release Notes:")
            print("="*60)
            print(release_notes)
        
    except Exception as e:
        print(f"❌ 生成Release Notes失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
