# -*- coding: utf-8 -*-
"""
代码完成度检查工具

功能:
- 扫描指定目录下的Python源代码
- 统计 TODO/FIXME 提示
- 识别未实现或占位函数:
  - 仅包含 `pass` 的函数（排除 @abstractmethod 修饰的抽象方法）
  - 包含 `raise NotImplementedError` 的函数
  - 仅包含 `...` (Ellipsis) 的函数
- 输出人类可读摘要和 JSON 报告文件

用法示例:
    poetry run python -m simtradelab.codecheck --path src/simtradelab --output-dir reports --format both

注意:
- 该工具不会修改任何源码，仅做静态分析
- 为避免误报, 抽象方法(@abstractmethod)不会被计为未实现
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple


TODO_PATTERN = re.compile(r"\b(TODO|FIXME)\b", re.IGNORECASE)


@dataclass
class IncompleteFunction:
    file: str
    name: str
    lineno: int
    reason: str  # 'pass', 'not_implemented', 'ellipsis'


@dataclass
class CompletenessReport:
    scanned_path: str
    python_files: int
    total_lines: int
    todo_count: int
    incomplete_functions_count: int
    incomplete_functions: List[IncompleteFunction]

    def to_json(self) -> str:
        data = asdict(self)
        # 将 dataclass 列表转换为普通 dict 列表
        data["incomplete_functions"] = [asdict(item) for item in self.incomplete_functions]
        return json.dumps(data, ensure_ascii=False, indent=2)

    def to_text(self) -> str:
        lines = []
        lines.append("代码完成度检查报告")
        lines.append("=" * 30)
        lines.append(f"扫描路径: {self.scanned_path}")
        lines.append(f"Python 文件数: {self.python_files}")
        lines.append(f"总代码行数: {self.total_lines}")
        lines.append(f"TODO/FIXME 数量: {self.todo_count}")
        lines.append(f"未实现函数数量: {self.incomplete_functions_count}")
        lines.append("")
        if self.incomplete_functions:
            lines.append("未实现/占位函数明细:")
            for item in self.incomplete_functions:
                lines.append(f"  - {item.file}:{item.lineno}  {item.name}()  [{item.reason}]")
        else:
            lines.append("未发现未实现/占位函数 ✅")
        return "\n".join(lines)


def _decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[str]:
    names: List[str] = []
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            names.append(d.id)
        elif isinstance(d, ast.Attribute):
            # e.g. abc.abstractmethod
            names.append(d.attr)
    return names


def _function_body_is_pass_only(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    # 函数体只有一个 pass
    return len(node.body) == 1 and isinstance(node.body[0], ast.Pass)


def _function_body_is_ellipsis_only(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    # 函数体只有一个 Ellipsis（...）
    return len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Ellipsis)


def _function_has_not_implemented(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    # 函数体内是否显式抛出 NotImplementedError
    for n in ast.walk(node):
        if isinstance(n, ast.Raise) and isinstance(n.exc, (ast.Name, ast.Call)):
            # raise NotImplementedError
            if isinstance(n.exc, ast.Name) and n.exc.id == "NotImplementedError":
                return True
            if isinstance(n.exc, ast.Call) and isinstance(n.exc.func, ast.Name) and n.exc.func.id == "NotImplementedError":
                return True
    return False


def analyze_file(path: Path) -> Tuple[int, List[IncompleteFunction]]:
    """分析单个 Python 文件, 返回 (todo_count, incomplete_functions)"""
    todo_count = 0
    incomplete: List[IncompleteFunction] = []

    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        # 非UTF-8或无法读取的文件忽略
        return 0, []

    # 统计 TODO/FIXME
    for i, line in enumerate(source.splitlines(), start=1):
        if TODO_PATTERN.search(line):
            todo_count += 1

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # 跳过语法错误文件（不应发生）
        return todo_count, []

    # 收集抽象方法（避免误报）
    abstract_methods: set[Tuple[str, int]] = set()

    class _ClassVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            # 遍历类中的函数，识别@abstractmethod
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    decos = _decorator_names(item)
                    if any(name.lower() == "abstractmethod" for name in decos):
                        abstract_methods.add((item.name, item.lineno))
            # 继续递归
            self.generic_visit(node)

    _ClassVisitor().visit(tree)

    # 遍历函数定义
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 忽略抽象方法
            if (node.name, node.lineno) in abstract_methods:
                continue
            # 忽略私有或魔术方法
            if node.name.startswith("__") and node.name.endswith("__"):
                continue

            # 判断未实现/占位情况
            if _function_body_is_pass_only(node):
                incomplete.append(
                    IncompleteFunction(str(path), node.name, node.lineno, "pass")
                )
            elif _function_body_is_ellipsis_only(node):
                incomplete.append(
                    IncompleteFunction(str(path), node.name, node.lineno, "ellipsis")
                )
            elif _function_has_not_implemented(node):
                incomplete.append(
                    IncompleteFunction(str(path), node.name, node.lineno, "not_implemented")
                )

    return todo_count, incomplete


def build_report(scan_path: Path) -> CompletenessReport:
    python_files = list(scan_path.rglob("*.py"))

    total_lines = 0
    total_todos = 0
    all_incomplete: List[IncompleteFunction] = []

    for file in python_files:
        try:
            total_lines += sum(1 for _ in file.open("r", encoding="utf-8"))
        except Exception:
            # 非utf-8 文件忽略到总行数统计
            pass
        todos, incomplete = analyze_file(file)
        total_todos += todos
        all_incomplete.extend(incomplete)

    report = CompletenessReport(
        scanned_path=str(scan_path),
        python_files=len(python_files),
        total_lines=total_lines,
        todo_count=total_todos,
        incomplete_functions_count=len(all_incomplete),
        incomplete_functions=all_incomplete,
    )
    return report


def save_report(report: CompletenessReport, output_dir: Path, fmt: str = "both") -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: List[Path] = []

    if fmt in ("json", "both"):
        json_path = output_dir / "code_completeness_report.json"
        json_path.write_text(report.to_json(), encoding="utf-8")
        outputs.append(json_path)

    if fmt in ("txt", "both"):
        txt_path = output_dir / "code_completeness_report.txt"
        txt_path.write_text(report.to_text(), encoding="utf-8")
        outputs.append(txt_path)

    return outputs


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="SimTradeLab 代码完成度检查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  poetry run python -m simtradelab.codecheck\n"
            "  poetry run python -m simtradelab.codecheck --path src/simtradelab --output-dir reports --format both\n"
        ),
    )
    parser.add_argument(
        "--path", default="src/simtradelab", help="扫描路径（默认: src/simtradelab）"
    )
    parser.add_argument(
        "--output-dir", default="reports", help="报告输出目录（默认: reports）"
    )
    parser.add_argument(
        "--format", choices=["json", "txt", "both"], default="both", help="报告格式（默认: both）"
    )

    args = parser.parse_args(args=argv)

    scan_path = Path(args.path)
    if not scan_path.exists():
        print(f"❌ 指定扫描路径不存在: {scan_path}")
        return 1

    report = build_report(scan_path)

    # 输出摘要到控制台
    print(report.to_text())

    # 保存报告文件
    output_paths = save_report(report, Path(args.output_dir), args.format)
    for p in output_paths:
        print(f"💾 已保存报告: {p}")

    # 始终返回0，避免在CI中将提醒视为失败
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
