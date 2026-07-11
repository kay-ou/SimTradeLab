"""Guards for the documented PTrade API support classifications."""

from __future__ import annotations

import ast
import inspect
import re
import subprocess
import sys
from pathlib import Path

import pytest

from simtradelab.ptrade.api import PtradeAPI
from simtradelab.ptrade.lifecycle_config import API_ALLOWED_PHASES_LOOKUP
from simtradelab.ptrade.lifecycle_controller import LifecyclePhase
from simtradelab.ptrade.broker_profile import BROKER_PROFILES
from tests.ptrade_api_contracts import (
    PTRADE_API_CONTRACTS,
    SUPPORTED_PTRADE_APIS,
    UNSUPPORTED_PTRADE_APIS,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/PTrade_Backtest_API_Support_Matrix.md"
CANONICAL_API_LIST = ROOT / "docs/PTrade_Backtest_Available_APIs.md"
INJECTED_GLOBAL_APIS = {"log"}
SURFACE_ONLY_APIS = {
    "get_stock_info",
    "get_stock_status",
    "get_stock_blocks",
    "get_index_stocks",
    "get_industry_stocks",
    "get_Ashares",
    "get_all_trades_days",
    "is_trade",
    "cancel_order",
    "get_open_orders",
}
UNSUPPORTED_CALL_ARGS = {
    "margin_trade": ("600000.SH", 100),
    "buy_open": ("IF88", 1),
    "sell_close": ("IF88", 1),
    "sell_open": ("IF88", 1),
    "buy_close": ("IF88", 1),
    "set_future_commission": ("IF", 0.0001),
    "set_margin_rate": ("IF", 0.1),
    "get_margin_rate": ("IF",),
    "get_instruments": ("IF",),
    "get_dominant_contract": ("IF",),
}


def _matrix_classifications() -> dict[str, set[str]]:
    text = MATRIX.read_text(encoding="utf-8")
    sections = {}
    for support, heading in (
        ("full", "## Full："),
        ("partial", "## Partial："),
        ("pending", "## Pending："),
        ("unsupported", "## Unsupported："),
    ):
        section = text.split(heading, 1)[1].split("\n## ", 1)[0]
        contract_lines = [
            line for line in section.splitlines() if line.startswith("|") or line.startswith("- `")
        ]
        sections[support] = set(
            re.findall(r"`([A-Za-z][A-Za-z0-9_]*)`", "\n".join(contract_lines))
        )
    return sections


def _canonical_backtest_apis() -> list[str]:
    text = CANONICAL_API_LIST.read_text(encoding="utf-8").split("## 待确认接口", 1)[0]
    api_lines = [line for line in text.splitlines() if line.startswith("- `")]
    return re.findall(r"`([A-Za-z][A-Za-z0-9_]*)`", "\n".join(api_lines))


def _overview_counts() -> dict[str, int]:
    text = MATRIX.read_text(encoding="utf-8")
    return {
        label.replace("`", "").strip(): int(count)
        for label, count in re.findall(r"^\| ([^|]+?) \| (\d+) \|$", text, re.MULTILINE)
    }


def _test_node_references_api(node_id: str, api_name: str) -> bool:
    parts = node_id.split("::")
    module = ast.parse((ROOT / parts[0]).read_text(encoding="utf-8"))
    body = module.body
    if len(parts) == 3:
        class_node = next(
            node for node in body if isinstance(node, ast.ClassDef) and node.name == parts[1]
        )
        body = class_node.body
    function_name = parts[-1]
    function_node = next(
        node
        for node in body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    )
    return any(
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Attribute)
            and node.func.attr == api_name)
            or (isinstance(node.func, ast.Name)
            and node.func.id == api_name)
        )
        for node in ast.walk(function_node)
    )


def _collect_behavior_nodes(node_ids: list[str]) -> set[str]:
    paths = sorted({node_id.split("::", 1)[0] for node_id in node_ids})
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *paths],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return {line.strip() for line in result.stdout.splitlines() if "::" in line}


def test_surface_only_evidence_is_not_classified_as_full_support():
    incorrectly_full = sorted(
        api_name
        for api_name in SURFACE_ONLY_APIS
        if PTRADE_API_CONTRACTS[api_name]["support"] == "full"
    )
    assert incorrectly_full == []


def test_ptrade_support_inventory_matches_documented_matrix():
    documented = _matrix_classifications()
    inventoried = {
        support: {
            api_name
            for api_name, contract in PTRADE_API_CONTRACTS.items()
            if contract["support"] == support
        }
        for support in documented
    }
    assert documented == inventoried
    assert set(PTRADE_API_CONTRACTS) == set(SUPPORTED_PTRADE_APIS) | set(
        UNSUPPORTED_PTRADE_APIS
    )


def test_inventory_covers_independent_canonical_backtest_api_list():
    canonical = _canonical_backtest_apis()
    assert len(canonical) == len(set(canonical)), "canonical API list contains duplicate bullets"
    assert set(canonical) == set(PTRADE_API_CONTRACTS) | INJECTED_GLOBAL_APIS


def test_markdown_overview_counts_match_classified_sections():
    documented = _matrix_classifications()
    counts = _overview_counts()
    assert counts["full"] == len(documented["full"])
    assert counts["partial"] == len(documented["partial"])
    assert counts["pending"] == len(documented["pending"])
    assert counts["unsupported"] == len(documented["unsupported"])
    assert counts["合计"] == sum(map(len, documented.values())) + counts["特殊项 log"]


def test_full_support_references_collected_behavior_tests():
    errors = []
    behavior_nodes = [
        node_id
        for contract in PTRADE_API_CONTRACTS.values()
        if contract["support"] == "full"
        for node_id in contract["behavior_tests"]
    ]
    collected = _collect_behavior_nodes(behavior_nodes)

    for api_name, contract in PTRADE_API_CONTRACTS.items():
        support = contract["support"]
        if support not in {"full", "partial", "pending", "unsupported"}:
            errors.append(f"{api_name}: invalid support level {support!r}")
            continue

        assert hasattr(PtradeAPI, api_name), api_name
        applicability = contract.get("applicability")
        if not isinstance(applicability, dict) or set(applicability) != {
            "lifecycle",
            "market",
            "frequency",
            "profile",
        }:
            errors.append(f"{api_name}: incomplete applicability metadata")
        elif not all(
            (isinstance(value, str) and value not in {"", "documented"})
            or (isinstance(value, list) and value and all(isinstance(item, str) and item for item in value))
            for value in applicability.values()
        ):
            errors.append(f"{api_name}: empty applicability metadata")
        else:
            frequency = applicability["frequency"]
            has_frequency_parameter = "frequency" in inspect.signature(
                getattr(PtradeAPI, api_name)
            ).parameters
            valid_frequencies = {
                "1m", "5m", "15m", "30m", "60m", "120m",
                "1d", "1w", "mo", "1q", "1y", "not_applicable",
            }
            if not isinstance(frequency, list) or not set(frequency) <= valid_frequencies:
                errors.append(f"{api_name}: invalid frequency applicability {frequency!r}")
            elif has_frequency_parameter != (frequency != ["not_applicable"]):
                errors.append(f"{api_name}: frequency applicability disagrees with signature")
            profiles = applicability["profile"]
            if not isinstance(profiles, list) or not profiles or not set(profiles) <= set(BROKER_PROFILES):
                errors.append(f"{api_name}: invalid broker profile applicability {profiles!r}")
        observable_contract = contract.get("observable_contract")
        if (
            not observable_contract
            or not str(observable_contract).startswith(f"{api_name}:")
            or "public return value or documented portfolio" in str(observable_contract)
        ):
            errors.append(f"{api_name}: missing observable contract")
        behavior_tests = contract["behavior_tests"]
        if support == "full":
            if not behavior_tests:
                errors.append(f"{api_name}: full support has no behavioral test")
            for node_id in behavior_tests:
                if not any(
                    collected_node == node_id
                    or collected_node.startswith(f"{node_id}[")
                    for collected_node in collected
                ):
                    errors.append(f"{api_name}: uncollected pytest node {node_id}")
                elif not _test_node_references_api(node_id, api_name):
                    errors.append(f"{api_name}: behavioral node does not call claimed API {node_id}")
            if "_unsupported_api(" in inspect.getsource(getattr(PtradeAPI, api_name)):
                errors.append(f"{api_name}: full support delegates to _unsupported_api")
        elif behavior_tests:
            errors.append(f"{api_name}: {support} support must not claim behavioral evidence")

    assert errors == []


@pytest.mark.parametrize("api_name", UNSUPPORTED_PTRADE_APIS)
def test_unsupported_apis_raise_not_implemented(ptrade_api, api_name):
    method = getattr(ptrade_api, api_name)
    ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.INITIALIZE)
    if "initialize" not in API_ALLOWED_PHASES_LOOKUP[api_name]:
        ptrade_api.context._lifecycle_controller.set_phase(LifecyclePhase.HANDLE_DATA)

    with pytest.raises(NotImplementedError, match=api_name):
        method(*UNSUPPORTED_CALL_ARGS[api_name])
