import json

import script.check_ruff_baseline as checker


def finding(path, row, column, code):
    return {
        "filename": str(path),
        "location": {"row": row, "column": column},
        "code": code,
    }


def test_normalize_findings_uses_repository_relative_location_identity(tmp_path):
    repository = tmp_path / "repository"
    source = repository / "src" / "package" / "module.py"

    normalized = checker.normalize_findings(
        [finding(source, 12, 7, "F401")], repository
    )

    assert normalized == [
        {
            "path": "src/package/module.py",
            "row": 12,
            "column": 7,
            "code": "F401",
        }
    ]


def test_check_fails_for_new_identity_and_allows_removed_identity():
    retained = {"path": "src/a.py", "row": 1, "column": 1, "code": "F401"}
    removed = {"path": "src/b.py", "row": 2, "column": 3, "code": "I001"}
    added = {"path": "tests/test_a.py", "row": 4, "column": 5, "code": "B006"}

    assert checker.find_new_findings([retained, added], [retained, removed]) == [added]
    assert checker.find_new_findings([retained], [retained, removed]) == []


def test_update_writes_sorted_deterministic_json(monkeypatch, tmp_path):
    baseline_path = tmp_path / ".ruff-baseline.json"
    findings = [
        {"path": "tests/z.py", "row": 9, "column": 2, "code": "F401"},
        {"path": "src/a.py", "row": 10, "column": 1, "code": "I001"},
        {"path": "src/a.py", "row": 2, "column": 8, "code": "B006"},
    ]
    monkeypatch.setattr(checker, "collect_ruff_findings", lambda repository: findings)

    assert checker.main(["--baseline", str(baseline_path), "--update"]) == 0
    first_write = baseline_path.read_text(encoding="utf-8")
    assert checker.main(["--baseline", str(baseline_path), "--update"]) == 0

    assert baseline_path.read_text(encoding="utf-8") == first_write
    assert json.loads(first_write) == [
        {"path": "src/a.py", "row": 2, "column": 8, "code": "B006"},
        {"path": "src/a.py", "row": 10, "column": 1, "code": "I001"},
        {"path": "tests/z.py", "row": 9, "column": 2, "code": "F401"},
    ]


def test_main_returns_failure_only_for_new_findings(monkeypatch, tmp_path):
    baseline_path = tmp_path / ".ruff-baseline.json"
    baseline = [
        {"path": "src/a.py", "row": 1, "column": 1, "code": "F401"},
        {"path": "src/removed.py", "row": 2, "column": 1, "code": "I001"},
    ]
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    monkeypatch.setattr(
        checker,
        "collect_ruff_findings",
        lambda repository: [baseline[0]],
    )
    assert checker.main(["--baseline", str(baseline_path)]) == 0

    monkeypatch.setattr(
        checker,
        "collect_ruff_findings",
        lambda repository: [
            baseline[0],
            {"path": "tests/new.py", "row": 3, "column": 4, "code": "B006"},
        ],
    )
    assert checker.main(["--baseline", str(baseline_path)]) == 1


def test_collect_ruff_findings_accepts_exit_one_with_json(monkeypatch, tmp_path):
    completed = type(
        "Completed",
        (),
        {
            "returncode": 1,
            "stdout": json.dumps([finding("src/a.py", 1, 2, "F401")]),
            "stderr": "",
        },
    )()
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return completed

    monkeypatch.setattr(checker.subprocess, "run", fake_run)

    assert checker.collect_ruff_findings(tmp_path) == [
        {"path": "src/a.py", "row": 1, "column": 2, "code": "F401"}
    ]
    assert calls == [
        (
            [
                "poetry",
                "run",
                "ruff",
                "check",
                "src",
                "tests",
                "--output-format",
                "json",
            ],
            {
                "cwd": tmp_path,
                "check": False,
                "capture_output": True,
                "text": True,
            },
        )
    ]
