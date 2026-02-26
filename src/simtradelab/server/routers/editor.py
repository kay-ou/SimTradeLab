from __future__ import annotations

import inspect
import re
from pathlib import Path
from fastapi import APIRouter
from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.lifecycle_config import API_LIFECYCLE_RESTRICTIONS
from simtradelab.utils.paths import get_project_root

router = APIRouter(prefix="/editor", tags=["editor"])

_DOC_SIG_RE = re.compile(r"\*\*(\w+)\(([^)]*)\)\*\*\s*-\s*([^*\[{`\n]+)")


def _load_doc_signatures() -> dict[str, tuple[str, str]]:
    doc_path = Path(get_project_root()) / "docs" / "PTrade_API_Summary.md"
    if not doc_path.exists():
        return {}
    sigs: dict[str, tuple[str, str]] = {}
    for m in _DOC_SIG_RE.finditer(doc_path.read_text(encoding="utf-8")):
        name, params, desc = m.group(1), m.group(2).strip(), m.group(3).strip()
        if name not in sigs:
            sigs[name] = (params, desc)
    return sigs


def _fmt_ann(ann) -> str:
    if ann is inspect.Parameter.empty:
        return ""
    s = ann if isinstance(ann, str) else getattr(ann, "__name__", str(ann))
    for prefix in ("typing.", "pandas.core.frame.", "numpy.", "simtradelab.ptrade."):
        s = s.replace(prefix, "")
    return s


def _insert_from_sig(name: str, params: list[inspect.Parameter]) -> str:
    """生成 insertText：所有参数，context 保持字面量，None 默认值作为可编辑占位符。"""
    parts: list[str] = []
    i = 1
    for p in params:
        if p.name == "context":
            parts.append("context")
            continue
        if p.default is inspect.Parameter.empty:
            parts.append(f"${{{i}:{p.name}}}")
        elif p.default is None:
            parts.append(f"${{{i}:None}}")
        else:
            parts.append(f"${{{i}:{repr(p.default)}}}")
        i += 1
    return f"{name}({', '.join(parts)})"


def _insert_from_doc(name: str, params_str: str) -> str:
    """从文档参数字符串生成 insertText（所有参数，None 作为占位符）。"""
    if not params_str:
        return f"{name}()"
    parts: list[str] = []
    i = 1
    for p in params_str.split(","):
        p = p.strip()
        param_name = p.split("=")[0].strip()
        if param_name in ("self",):
            continue
        if param_name == "context":
            parts.append("context")
            continue
        has_default = "=" in p
        default_val = p.split("=", 1)[1].strip() if has_default else None
        if not has_default:
            parts.append(f"${{{i}:{param_name}}}")
        elif default_val:
            parts.append(f"${{{i}:{default_val}}}")
        else:
            parts.append(f"${{{i}:None}}")
        i += 1
    return f"{name}({', '.join(parts)})"


def _build_items() -> list[dict]:
    doc_sigs = _load_doc_signatures()
    items = []

    for name, restrictions in API_LIFECYCLE_RESTRICTIONS.items():
        method = getattr(PtradeAPI, name, None)
        sig = None
        if method is not None:
            try:
                sig = inspect.signature(method)
            except (ValueError, TypeError):
                pass

        if sig is not None:
            params = [p for p in sig.parameters.values() if p.name != "self"]
            param_strs = [
                p.name if p.default is inspect.Parameter.empty
                else f"{p.name}={repr(p.default)}"
                for p in params
            ]
            ret = sig.return_annotation
            ret_str = f" -> {_fmt_ann(ret)}" if ret is not inspect.Parameter.empty else ""
            detail = f"({', '.join(param_strs)}){ret_str}"
            insert_text = _insert_from_sig(name, params)
            raw_doc = getattr(method, "__doc__", "") or ""
            doc = raw_doc.strip().split("\n")[0].strip()

        elif name in doc_sigs:
            params_str, doc = doc_sigs[name]
            detail = f"({params_str})"
            insert_text = _insert_from_doc(name, params_str)

        else:
            detail = "()"
            insert_text = f"{name}(${{1}})"
            doc = ""

        items.append({
            "label": name,
            "kind": "Function",
            "detail": detail,
            "insertText": insert_text,
            "doc": doc,
            "scopes": restrictions,
        })

    return items


@router.get("/completions")
def get_completions() -> list[dict]:
    # 不缓存，保证代码修改后立即生效
    return _build_items()
