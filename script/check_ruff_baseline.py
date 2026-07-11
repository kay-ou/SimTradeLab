#!/usr/bin/env python3
"""Reject Ruff findings that are not present in the checked-in baseline."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = REPOSITORY_ROOT / ".ruff-baseline.json"
RUFF_COMMAND = [
    "poetry",
    "run",
    "ruff",
    "check",
    "src",
    "tests",
    "--output-format",
    "json",
]


class RuffBaselineError(RuntimeError):
    """Raised when Ruff output or the baseline cannot be interpreted."""


def _identity_key(finding):
    return (
        finding["path"],
        finding["row"],
        finding["column"],
        finding["code"],
    )


def _normalize_path(filename, repository):
    path = Path(filename)
    if not path.is_absolute():
        path = repository / path
    path = path.resolve()
    repository = repository.resolve()
    try:
        return path.relative_to(repository).as_posix()
    except ValueError:
        return path.as_posix()


def normalize_findings(entries, repository):
    """Convert Ruff JSON entries to sorted location identities."""
    normalized = []
    for entry in entries:
        location = entry["location"]
        normalized.append(
            {
                "path": _normalize_path(entry["filename"], repository),
                "row": int(location["row"]),
                "column": int(location["column"]),
                "code": entry["code"],
            }
        )
    return _sort_identities(normalized)


def _sort_identities(findings):
    unique = {_identity_key(finding): finding for finding in findings}
    return [unique[key] for key in sorted(unique)]


def collect_ruff_findings(repository):
    """Run Ruff and return normalized findings for the repository."""
    result = subprocess.run(
        RUFF_COMMAND,
        cwd=repository,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        raise RuffBaselineError(
            "Ruff failed with exit code %s: %s"
            % (result.returncode, result.stderr.strip())
        )
    try:
        entries = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuffBaselineError("Ruff did not return valid JSON") from exc
    if not isinstance(entries, list):
        raise RuffBaselineError("Ruff JSON output must be a list")
    if result.returncode == 1 and not entries:
        raise RuffBaselineError("Ruff exited with findings but returned no JSON entries")
    return normalize_findings(entries, repository)


def load_baseline(path):
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuffBaselineError(
            "Ruff baseline is missing; run with --update to create it"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuffBaselineError("Ruff baseline is not valid JSON") from exc
    if not isinstance(entries, list):
        raise RuffBaselineError("Ruff baseline must be a JSON list")
    required = {"path", "row", "column", "code"}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != required:
            raise RuffBaselineError(
                "Each Ruff baseline entry must contain path, row, column, and code"
            )
    return _sort_identities(entries)


def write_baseline(path, findings):
    path.write_text(
        json.dumps(_sort_identities(findings), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def find_new_findings(current, baseline):
    baseline_keys = {_identity_key(finding) for finding in baseline}
    return _sort_identities(
        finding for finding in current if _identity_key(finding) not in baseline_keys
    )


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Reject Ruff findings that are absent from the checked-in baseline."
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help="baseline JSON path (default: .ruff-baseline.json)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the baseline with the current sorted Ruff findings",
    )
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        current = _sort_identities(collect_ruff_findings(REPOSITORY_ROOT))
        if args.update:
            write_baseline(args.baseline, current)
            print("Updated Ruff baseline with %d findings." % len(current))
            return 0

        baseline = load_baseline(args.baseline)
        new_findings = find_new_findings(current, baseline)
        if new_findings:
            print("New Ruff findings are not allowed:", file=sys.stderr)
            for finding in new_findings:
                print(
                    "{path}:{row}:{column}: {code}".format(**finding),
                    file=sys.stderr,
                )
            return 1

        removed_count = len(baseline) - len(current)
        message = "Ruff baseline check passed (%d current findings" % len(current)
        if removed_count > 0:
            message += ", %d removed" % removed_count
        print(message + ").")
        return 0
    except RuffBaselineError as exc:
        print("Ruff baseline check failed: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
