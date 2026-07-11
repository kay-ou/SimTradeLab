import json
import os
import signal
import subprocess
from pathlib import Path

import pytest
import script.local_strategy_regression as regression


def write_suite_config(tmp_path, strategies=None):
    config_path = tmp_path / "local-suite.json"
    config_path.write_text(
        json.dumps(
            {
                "schema_version": regression.SCHEMA_VERSION,
                "data_path": "data",
                "strategies_path": "strategies",
                "strategies": strategies
                or {
                    "strategy_a": {
                        "config": {
                            "strategy_name": "strategy_a",
                            "start_date": "2025-01-01",
                            "end_date": "2025-12-31",
                        },
                        "performance": {
                            "execution_seconds_ceiling": 30.0,
                            "wall_seconds_ceiling": 45.0,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_configuration_fingerprint_is_deterministic_and_includes_strategy_source(tmp_path):
    strategy = tmp_path / "backtest.py"
    strategy.write_text("def initialize(context):\n    pass\n", encoding="utf-8")
    config = {
        "strategy_name": "example",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "initial_capital": 100000.0,
    }

    first = regression.configuration_fingerprint(config, strategy)
    reordered = regression.configuration_fingerprint(dict(reversed(list(config.items()))), strategy)
    strategy.write_text("def initialize(context):\n    context.changed = True\n", encoding="utf-8")
    changed = regression.configuration_fingerprint(config, strategy)

    assert first == reordered
    assert changed != first


def test_compare_correctness_checks_exact_values_and_numeric_tolerances():
    baseline = {
        "exact": {
            "trade_count": 4,
            "portfolio_fingerprint": "portfolio-a",
        },
        "numeric": {
            "final_value": {"expected": 123456.78, "abs_tolerance": 0.01},
            "total_return": {"expected": 0.2345678, "abs_tolerance": 1e-8},
        },
    }
    accepted = {
        "exact": {
            "trade_count": 4,
            "portfolio_fingerprint": "portfolio-a",
        },
        "metrics": {"final_value": 123456.785, "total_return": 0.234567805},
    }
    rejected = {
        "exact": {
            "trade_count": 5,
            "portfolio_fingerprint": "portfolio-b",
        },
        "metrics": {"final_value": 123456.80, "total_return": 0.2345679},
    }

    assert regression.compare_correctness(accepted, baseline) == []
    failures = regression.compare_correctness(rejected, baseline)

    assert any("trade_count" in failure for failure in failures)
    assert any("portfolio_fingerprint" in failure for failure in failures)
    assert any("final_value" in failure and "0.02" in failure for failure in failures)
    assert any("total_return" in failure for failure in failures)


def test_compare_performance_uses_wide_wall_and_execution_ceilings():
    baseline = {
        "wall_seconds_ceiling": 300.0,
        "execution_seconds_ceiling": 240.0,
    }

    assert regression.compare_performance(
        {"wall_seconds": 299.0, "execution_seconds": 239.0}, baseline
    ) == []

    failures = regression.compare_performance(
        {"wall_seconds": 301.0, "execution_seconds": 241.0}, baseline
    )
    assert any("wall_seconds" in failure for failure in failures)
    assert any("execution_seconds" in failure for failure in failures)


def test_validate_fingerprints_rejects_configuration_or_data_mismatch():
    baseline = {
        "configuration_fingerprint": "config-a",
        "data_range_fingerprint": "data-a",
    }

    assert regression.validate_fingerprints(
        {
            "configuration_fingerprint": "config-a",
            "data_range_fingerprint": "data-a",
        },
        baseline,
    ) == []

    failures = regression.validate_fingerprints(
        {
            "configuration_fingerprint": "config-b",
            "data_range_fingerprint": "data-b",
        },
        baseline,
    )
    assert any("configuration fingerprint" in failure for failure in failures)
    assert any("data-range fingerprint" in failure for failure in failures)


def test_append_history_writes_one_json_object_per_line_without_replacing_existing(tmp_path):
    history_path = tmp_path / "history.jsonl"
    regression.append_history(history_path, {"strategy": "strategy_a", "status": "passed"})
    regression.append_history(
        history_path, {"strategy": "strategy_b", "status": "failed"}
    )

    lines = history_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert json.loads(lines[0]) == {"status": "passed", "strategy": "strategy_a"}
    assert json.loads(lines[1]) == {
        "status": "failed",
        "strategy": "strategy_b",
    }


def test_load_suite_config_resolves_private_artifact_paths_from_config_location(tmp_path):
    config_path = write_suite_config(tmp_path)

    suite = regression._load_suite_config(config_path)

    assert tuple(suite.strategies) == ("strategy_a",)
    assert suite.data_path == tmp_path / "data"
    assert suite.strategies_path == tmp_path / "strategies"
    assert suite.baseline_path == tmp_path / "local-suite-baseline.json"
    assert suite.history_path == tmp_path / "local-suite-history.jsonl"
    assert suite.checksum_cache_path == tmp_path / "local-suite-checksums.json"


def test_load_suite_config_fails_clearly_when_local_config_is_missing(tmp_path):
    missing = tmp_path / "missing.json"

    with pytest.raises(
        regression.StrategyRegressionError,
        match=r"local strategy regression config is missing.*--config",
    ):
        regression._load_suite_config(missing)


def test_load_suite_config_rejects_entry_without_reviewed_performance_limits(tmp_path):
    config_path = write_suite_config(
        tmp_path,
        strategies={
            "strategy_a": {
                "config": {
                    "strategy_name": "strategy_a",
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                }
            }
        },
    )

    with pytest.raises(
        regression.StrategyRegressionError,
        match="strategy_a performance",
    ):
        regression._load_suite_config(config_path)


def test_data_range_fingerprint_is_content_based_and_ignores_unrelated_data(tmp_path):
    data_path = tmp_path / "data"
    dataset = data_path / "cn"
    (dataset / "stocks").mkdir(parents=True)
    (dataset / "stocks_1m").mkdir()
    (data_path / "us" / "stocks").mkdir(parents=True)
    (dataset / "manifest.json").write_text('{"version": "1"}', encoding="utf-8")
    prices = dataset / "stocks" / "000001.SZ.parquet"
    prices.write_bytes(b"version-one")
    minute_prices = dataset / "stocks_1m" / "000001.SZ.parquet"
    minute_prices.write_bytes(b"minute-one")
    us_prices = data_path / "us" / "stocks" / "AAPL.US.parquet"
    us_prices.write_bytes(b"us-one")
    strategy = tmp_path / "backtest.py"
    strategy.write_text(
        "def handle_data(context, data):\n    get_history(1, '1d', 'close', ['000001.XSHE'])\n",
        encoding="utf-8",
    )
    cache_path = tmp_path / "checksums.json"
    config = {
        "strategy_name": "example",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "frequency": "1d",
        "market": "CN",
    }

    original = regression.data_range_fingerprint(
        config, data_path, strategy, cache_path
    )
    stat = prices.stat()
    os.utime(prices, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1))
    touched = regression.data_range_fingerprint(
        config, data_path, strategy, cache_path
    )
    minute_prices.write_bytes(b"minute-two-is-unrelated")
    us_prices.write_bytes(b"us-two-is-unrelated")
    unrelated = regression.data_range_fingerprint(
        config, data_path, strategy, cache_path
    )
    prices.write_bytes(b"version-two")
    replaced = regression.data_range_fingerprint(
        config, data_path, strategy, cache_path
    )

    assert touched == original
    assert unrelated == original
    assert replaced != original


def test_data_range_fingerprint_is_portable_across_roots_and_mtimes(tmp_path):
    strategy = tmp_path / "backtest.py"
    strategy.write_text(
        "def handle_data(context, data):\n    get_history(1, '1d', 'close', ['000001.XSHE'])\n",
        encoding="utf-8",
    )
    config = {
        "strategy_name": "example",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "frequency": "1d",
        "market": "CN",
    }
    roots = []
    for index in range(2):
        root = tmp_path / ("data-%d" % index)
        dataset = root / "cn"
        (dataset / "stocks").mkdir(parents=True)
        (dataset / "manifest.json").write_text('{"version": "1"}', encoding="utf-8")
        prices = dataset / "stocks" / "000001.SZ.parquet"
        prices.write_bytes(b"same-content")
        stat = prices.stat()
        os.utime(prices, ns=(stat.st_atime_ns, stat.st_mtime_ns + index + 1))
        roots.append(root)

    first = regression.data_range_fingerprint(
        config, roots[0], strategy, tmp_path / "cache-0.json"
    )
    second = regression.data_range_fingerprint(
        config, roots[1], strategy, tmp_path / "cache-1.json"
    )

    assert first == second


def test_data_checksum_cache_avoids_rehashing_unchanged_files(monkeypatch, tmp_path):
    data_path = tmp_path / "data"
    dataset = data_path / "cn"
    (dataset / "stocks").mkdir(parents=True)
    (dataset / "manifest.json").write_text('{"version": "1"}', encoding="utf-8")
    (dataset / "stocks" / "000001.SZ.parquet").write_bytes(b"daily-prices")
    strategy = tmp_path / "backtest.py"
    strategy.write_text(
        "def handle_data(context, data):\n    get_history(1, '1d', 'close', ['000001.XSHE'])\n",
        encoding="utf-8",
    )
    config = {
        "strategy_name": "example",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "frequency": "1d",
        "market": "CN",
    }
    calls = []
    real_hash = regression._sha256_file

    def counting_hash(path):
        calls.append(path.name)
        return real_hash(path)

    monkeypatch.setattr(regression, "_sha256_file", counting_hash)
    cache_path = tmp_path / "checksums.json"

    regression.data_range_fingerprint(config, data_path, strategy, cache_path)
    first_count = len(calls)
    regression.data_range_fingerprint(config, data_path, strategy, cache_path)

    assert first_count == 2
    assert len(calls) == first_count


def test_data_checksum_cache_does_not_cross_contaminate_different_roots(tmp_path):
    strategy = tmp_path / "backtest.py"
    strategy.write_text(
        "def handle_data(context, data):\n    get_history(1, '1d', 'close', ['000001.XSHE'])\n",
        encoding="utf-8",
    )
    config = {
        "strategy_name": "example",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "frequency": "1d",
        "market": "CN",
    }
    roots = []
    fixed_mtime = 1_700_000_000_000_000_000
    for index, content in enumerate((b"content-a", b"content-b")):
        root = tmp_path / ("root-%d" % index)
        dataset = root / "cn"
        (dataset / "stocks").mkdir(parents=True)
        manifest = dataset / "manifest.json"
        manifest.write_text('{"version": "1"}', encoding="utf-8")
        prices = dataset / "stocks" / "000001.SZ.parquet"
        prices.write_bytes(content)
        os.utime(prices, ns=(fixed_mtime, fixed_mtime))
        roots.append(root)

    shared_cache = tmp_path / "shared-checksums.json"
    first = regression.data_range_fingerprint(
        config, roots[0], strategy, shared_cache
    )
    second = regression.data_range_fingerprint(
        config, roots[1], strategy, shared_cache
    )

    assert first != second


def test_required_dataset_kinds_follow_strategy_analyzer_and_daily_config(tmp_path):
    strategy = tmp_path / "backtest.py"
    strategy.write_text(
        "def handle_data(context, data):\n"
        "    get_history(1, '1d', 'close', ['000001.XSHE'])\n"
        "    get_fundamentals(None, 'valuation')\n",
        encoding="utf-8",
    )

    assert regression._required_dataset_kinds(
        {"frequency": "1d"}, strategy
    ) == {"price", "valuation", "fundamentals", "exrights"}


def test_run_strategy_subprocess_reports_nonzero_worker_exit(monkeypatch):
    calls = []

    class FakeProcess:
        pid = 123

        def wait(self, timeout):
            return 7

    def fake_popen(command, **kwargs):
        kwargs["stdout"].write("worker exploded\n")
        calls.append(kwargs)
        return FakeProcess()

    monkeypatch.setattr(regression.subprocess, "Popen", fake_popen)

    with pytest.raises(regression.StrategyRegressionError, match="exit code 7"):
        regression._run_strategy_subprocess(
            Path("local-suite.json"), "strategy_a", timeout_seconds=30.0
        )

    assert calls[0].get("start_new_session", False) is (os.name == "posix")


def test_run_strategy_subprocess_reports_timeout_and_uses_requested_limit(monkeypatch):
    calls = []

    class FakeProcess:
        pid = 456

        def wait(self, timeout):
            calls.append(timeout)
            raise subprocess.TimeoutExpired("worker", timeout)

    monkeypatch.setattr(regression.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    monkeypatch.setattr(
        regression,
        "_terminate_worker_process",
        lambda process: calls.append(("terminated", process.pid)),
    )


    with pytest.raises(regression.StrategyRegressionError, match=r"timed out after 123\.00s"):
        regression._run_strategy_subprocess(
            Path("local-suite.json"), "strategy_a", timeout_seconds=123.0
        )

    assert calls == [123.0, ("terminated", 456)]


def test_terminate_worker_process_group_uses_term_then_kill(monkeypatch):
    signals = []

    class FakeProcess:
        pid = 789

        def poll(self):
            return None

        def wait(self, timeout=None):
            if timeout is not None:
                raise subprocess.TimeoutExpired("worker", timeout)
            return -signal.SIGKILL

    monkeypatch.setattr(
        regression.os, "killpg", lambda process_group, sig: signals.append((process_group, sig))
    )

    regression._terminate_worker_process(FakeProcess(), posix=True, grace_seconds=0.01)

    assert signals == [(789, signal.SIGTERM), (789, signal.SIGKILL)]


def test_terminate_worker_process_has_non_posix_parent_fallback():
    calls = []

    class FakeProcess:
        def poll(self):
            return None

        def terminate(self):
            calls.append("terminate")

        def kill(self):
            calls.append("kill")

        def wait(self, timeout=None):
            if timeout is not None:
                raise subprocess.TimeoutExpired("worker", timeout)
            calls.append("wait")
            return -1

    regression._terminate_worker_process(
        FakeProcess(), posix=False, grace_seconds=0.01
    )

    assert calls == ["terminate", "kill", "wait"]


def test_timeout_is_baseline_wall_ceiling_plus_small_process_allowance():
    entry = {"performance": {"wall_seconds_ceiling": 1200.0}}

    assert regression.subprocess_timeout_seconds(entry) == 1230.0


def test_baseline_update_uses_configured_ceiling_instead_of_latest_runtime():
    result = {
        "strategy": "strategy_a",
        "configuration_fingerprint": "config",
        "data_range_fingerprint": "data",
        "source_fingerprint": "source",
        "exact": {},
        "metrics": {metric: 0.0 for metric in regression.NUMERIC_TOLERANCES},
        "wall_seconds": 200.0,
        "execution_seconds": 190.0,
    }
    configured_performance = {
        "execution_seconds_ceiling": 30.0,
        "wall_seconds_ceiling": 45.0,
    }

    entry = regression._baseline_entry(result, configured_performance)

    assert entry["performance"] == configured_performance


def test_load_baseline_rejects_unknown_schema(tmp_path):
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps({"schema_version": 999, "strategies": {}}), encoding="utf-8"
    )

    with pytest.raises(regression.StrategyRegressionError, match="unsupported baseline schema"):
        regression._load_baseline(path)


@pytest.mark.parametrize("baseline", [[], None, "baseline", 42])
def test_load_baseline_rejects_non_object_root(tmp_path, baseline):
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")

    with pytest.raises(
        regression.StrategyRegressionError,
        match="baseline root must be an object",
    ):
        regression._load_baseline(path)


def test_load_baseline_rejects_strategy_entry_without_performance_ceiling(tmp_path):
    path = tmp_path / "baseline.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": regression.SCHEMA_VERSION,
                "strategies": {
                    "strategy_a": {
                        "configuration_fingerprint": "config",
                        "data_range_fingerprint": "data",
                        "correctness": {"exact": {}, "numeric": {}},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(regression.StrategyRegressionError, match="strategy_a performance"):
        regression._load_baseline(path)


def test_main_rejects_identity_mismatch_without_starting_worker(monkeypatch, tmp_path):
    config_path = write_suite_config(tmp_path)
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "schema_version": regression.SCHEMA_VERSION,
                "strategies": {
                    "strategy_a": {
                        "configuration_fingerprint": "expected-config",
                        "data_range_fingerprint": "expected-data",
                        "correctness": {"exact": {}, "numeric": {}},
                        "performance": {
                            "execution_seconds_ceiling": 150.0,
                            "wall_seconds_ceiling": 210.0,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        regression,
        "_current_identity",
        lambda suite, strategy: {
            "configuration_fingerprint": "changed-config",
            "data_range_fingerprint": "expected-data",
        },
    )

    def unexpected_run(*args, **kwargs):
        raise AssertionError("worker must not start after a preflight mismatch")

    monkeypatch.setattr(regression, "_run_strategy_subprocess", unexpected_run)

    assert regression.main(
        [
            "--strategy",
            "strategy_a",
            "--config",
            str(config_path),
            "--baseline",
            str(baseline_path),
            "--no-history",
        ]
    ) == 1


def test_main_rejects_unknown_strategy_from_local_config(capsys, tmp_path):
    config_path = write_suite_config(tmp_path)

    exit_code = regression.main(
        ["--config", str(config_path), "--strategy", "strategy_b"]
    )

    assert exit_code == 2
    assert "strategy_b is not defined" in capsys.readouterr().err


def test_main_reports_missing_default_or_explicit_local_config(capsys, tmp_path):
    exit_code = regression.main(
        ["--config", str(tmp_path / "missing.json"), "--all"]
    )

    assert exit_code == 2
    assert "local strategy regression config is missing" in capsys.readouterr().err


@pytest.mark.parametrize("baseline", [[], None, "baseline", 42])
def test_main_reports_non_object_baseline_without_traceback(capsys, tmp_path, baseline):
    config_path = write_suite_config(tmp_path)
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

    exit_code = regression.main(
        [
            "--config",
            str(config_path),
            "--baseline",
            str(baseline_path),
            "--all",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "baseline root must be an object" in captured.err
    assert "Traceback" not in captured.err
