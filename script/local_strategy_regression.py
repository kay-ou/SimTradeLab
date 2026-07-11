#!/usr/bin/env python3
"""Run a user-configured private strategy suite as a local regression gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPOSITORY_ROOT / ".simtradelab-strategy-regression.json"
SCHEMA_VERSION = 1
SUBPROCESS_STARTUP_ALLOWANCE_SECONDS = 30.0

NUMERIC_TOLERANCES = {
    "final_value": 0.01,
    "total_return": 1e-9,
    "annual_return": 1e-9,
    "max_drawdown": 1e-9,
    "sharpe_ratio": 1e-9,
    "benchmark_return": 1e-9,
    "alpha": 1e-9,
    "beta": 1e-9,
}


class StrategyRegressionError(RuntimeError):
    """Raised when the local regression run cannot be completed safely."""


@dataclass(frozen=True)
class LocalStrategySuite:
    """Validated project-local paths and strategy definitions."""

    config_path: Path
    data_path: Path
    strategies_path: Path
    baseline_path: Path
    history_path: Path
    checksum_cache_path: Path
    strategies: dict


def _resolve_config_path(config_path: Path, value, default_name: str) -> Path:
    path = Path(value) if value else config_path.with_name(default_name)
    if not path.is_absolute():
        path = config_path.parent / path
    return path.expanduser().resolve()


def _validate_performance(strategy: str, performance) -> None:
    if not isinstance(performance, dict):
        raise StrategyRegressionError("%s performance config is invalid" % strategy)
    for field in ("execution_seconds_ceiling", "wall_seconds_ceiling"):
        value = performance.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise StrategyRegressionError(
                "%s performance %s is invalid" % (strategy, field)
            )


def _load_suite_config(path: Path) -> LocalStrategySuite:
    config_path = path.expanduser().resolve()
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StrategyRegressionError(
            "local strategy regression config is missing: %s; create it or pass --config PATH"
            % config_path
        ) from exc
    except json.JSONDecodeError as exc:
        raise StrategyRegressionError(
            "local strategy regression config is not valid JSON: %s" % config_path
        ) from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise StrategyRegressionError(
            "unsupported local strategy regression config schema: %r"
            % (payload.get("schema_version") if isinstance(payload, dict) else None)
        )
    strategies = payload.get("strategies")
    if not isinstance(strategies, dict) or not strategies:
        raise StrategyRegressionError("local strategy regression config needs strategies")

    normalized = {}
    for strategy, entry in strategies.items():
        if not isinstance(strategy, str) or not strategy or not isinstance(entry, dict):
            raise StrategyRegressionError("strategy entries must use non-empty names and objects")
        config = entry.get("config")
        if not isinstance(config, dict):
            raise StrategyRegressionError("%s backtest config is invalid" % strategy)
        for field in ("strategy_name", "start_date", "end_date"):
            if not config.get(field):
                raise StrategyRegressionError("%s config %s is missing" % (strategy, field))
        config = dict(config)
        config.setdefault("frequency", "1d")
        config.setdefault("market", "CN")
        config.setdefault("strategy_file", "backtest.py")
        performance = entry.get("performance")
        _validate_performance(strategy, performance)
        normalized[strategy] = {
            "config": config,
            "performance": dict(performance),
        }

    stem = config_path.stem
    configured_data_path = payload.get("data_path") or os.environ.get(
        "SIMTRADELAB_DATA_PATH"
    )
    data_path = _resolve_config_path(
        config_path, configured_data_path, "data"
    ) if configured_data_path else REPOSITORY_ROOT / "data"
    strategies_path = _resolve_config_path(
        config_path, payload.get("strategies_path"), "strategies"
    ) if payload.get("strategies_path") else REPOSITORY_ROOT / "strategies"
    return LocalStrategySuite(
        config_path=config_path,
        data_path=data_path,
        strategies_path=strategies_path,
        baseline_path=_resolve_config_path(
            config_path, payload.get("baseline_path"), stem + "-baseline.json"
        ),
        history_path=_resolve_config_path(
            config_path, payload.get("history_path"), stem + "-history.jsonl"
        ),
        checksum_cache_path=_resolve_config_path(
            config_path, payload.get("checksum_cache_path"), stem + "-checksums.json"
        ),
        strategies=normalized,
    )


def _canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def configuration_fingerprint(config, strategy_path: Path) -> str:
    """Fingerprint behavior-affecting config together with strategy source."""
    payload = {
        "config": config,
        "strategy_sha256": hashlib.sha256(strategy_path.read_bytes()).hexdigest(),
    }
    return _fingerprint(payload)


def _required_dataset_kinds(config, strategy_path: Path):
    from simtradelab.ptrade.strategy_data_analyzer import (
        analyze_strategy_data_requirements,
    )

    dependencies = analyze_strategy_data_requirements(str(strategy_path))
    kinds = set()
    if dependencies.needs_price_data:
        kinds.add("price")
    if dependencies.needs_valuation:
        kinds.add("valuation")
    if dependencies.needs_fundamentals:
        kinds.add("fundamentals")
    if dependencies.needs_exrights:
        kinds.add("exrights")
    if config.get("frequency") == "1m":
        kinds.add("price_1m")
    return kinds


def _market_data_path(data_path: Path, market: str) -> Path:
    from simtradelab.ptrade.market_profile import get_market_profile

    profile = get_market_profile(market)
    if data_path.name == profile.data_dir_name:
        return data_path
    candidate = data_path / profile.data_dir_name
    return candidate if candidate.exists() else data_path


def _relevant_data_files(config, data_path: Path, strategy_path: Path):
    """Select only datasets loaded by these fixed market/frequency dependencies."""
    market_path = _market_data_path(data_path, config["market"])
    kinds = _required_dataset_kinds(config, strategy_path)
    files = []

    manifest = market_path / "manifest.json"
    if manifest.is_file():
        files.append(manifest)

    metadata_path = market_path / "metadata"
    for name in (
        "benchmark.parquet",
        "index_constituents.parquet",
        "stock_metadata.parquet",
        "stock_status.parquet",
        "trade_days.parquet",
    ):
        path = metadata_path / name
        if path.is_file():
            files.append(path)

    directory_by_kind = {
        "price": "stocks",
        "price_1m": "stocks_1m",
        "valuation": "valuation",
        "fundamentals": "fundamentals",
        "exrights": "exrights",
    }
    for kind in sorted(kinds):
        directory = market_path / directory_by_kind[kind]
        if directory.is_dir():
            files.extend(sorted(directory.glob("*.parquet")))

    if "exrights" in kinds:
        for name in ("ptrade_adj_pre.parquet", "ptrade_adj_post.parquet"):
            path = market_path / name
            if path.is_file():
                files.append(path)

    unique = {path.relative_to(market_path).as_posix(): path for path in files}
    return market_path, [(relative, unique[relative]) for relative in sorted(unique)]


def _load_checksum_cache(path: Path, data_root: Path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if (
        payload.get("schema_version") != 1
        or payload.get("data_root") != str(data_root.resolve())
        or not isinstance(payload.get("entries"), dict)
    ):
        return {}
    return payload["entries"]


def _write_checksum_cache(path: Path, entries, data_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-%d" % os.getpid())
    temporary.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "data_root": str(data_root.resolve()),
                "entries": entries,
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _content_inventory(config, data_path: Path, strategy_path: Path, cache_path: Path):
    market_path, selected_files = _relevant_data_files(config, data_path, strategy_path)
    cache = _load_checksum_cache(cache_path, market_path)
    inventory = []
    for relative_path, path in selected_files:
        stat = path.stat()
        cache_key = "%s/%s" % (config["market"].upper(), relative_path)
        cached = cache.get(cache_key, {})
        if cached.get("size") == stat.st_size and cached.get("mtime_ns") == stat.st_mtime_ns:
            checksum = cached.get("sha256")
        else:
            checksum = None
        if not isinstance(checksum, str) or len(checksum) != 64:
            checksum = _sha256_file(path)
            cache[cache_key] = {
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": checksum,
            }
        inventory.append(
            {"path": relative_path, "size": stat.st_size, "sha256": checksum}
        )
    _write_checksum_cache(cache_path, cache, market_path)
    return inventory


def data_range_fingerprint(
    config,
    data_path: Path,
    strategy_path: Path,
    cache_path: Path,
) -> str:
    """Fingerprint fixed range and portable SHA-256 identities of required data."""
    required_kinds = sorted(_required_dataset_kinds(config, strategy_path))
    return _fingerprint(
        {
            "start_date": config["start_date"],
            "end_date": config["end_date"],
            "frequency": config["frequency"],
            "market": config["market"],
            "required_dataset_kinds": required_kinds,
            "data_files": _content_inventory(
                config, data_path, strategy_path, cache_path
            ),
        }
    )


def source_fingerprint() -> str:
    """Record the local package source identity without making it a baseline gate."""
    digest = hashlib.sha256()
    source_root = REPOSITORY_ROOT / "src" / "simtradelab"
    for path in sorted(source_root.rglob("*.py")):
        digest.update(path.relative_to(REPOSITORY_ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validate_fingerprints(result, baseline):
    """Reject comparisons made with a different strategy config or data range."""
    failures = []
    if result.get("configuration_fingerprint") != baseline.get(
        "configuration_fingerprint"
    ):
        failures.append("configuration fingerprint mismatch; review and update the baseline")
    if result.get("data_range_fingerprint") != baseline.get(
        "data_range_fingerprint"
    ):
        failures.append("data-range fingerprint mismatch; review and update the baseline")
    return failures


def compare_correctness(result, baseline):
    """Return human-readable exact and tolerance comparison failures."""
    failures = []
    actual_exact = result.get("exact", {})
    for metric, expected in baseline.get("exact", {}).items():
        actual = actual_exact.get(metric)
        if actual != expected:
            failures.append(
                "%s changed: expected %r, got %r" % (metric, expected, actual)
            )

    actual_metrics = result.get("metrics", {})
    for metric, expectation in baseline.get("numeric", {}).items():
        expected = float(expectation["expected"])
        tolerance = float(expectation["abs_tolerance"])
        actual = actual_metrics.get(metric)
        if actual is None:
            failures.append("%s is missing from the structured result" % metric)
            continue
        delta = abs(float(actual) - expected)
        if not math.isfinite(delta) or delta > tolerance:
            failures.append(
                "%s changed by %.12g: expected %.12g ± %.12g, got %.12g"
                % (metric, delta, expected, tolerance, float(actual))
            )
    return failures


def compare_performance(result, baseline):
    """Return failures for deliberately wide wall/execution time ceilings."""
    failures = []
    for metric in ("wall_seconds", "execution_seconds"):
        ceiling_key = metric + "_ceiling"
        ceiling = baseline.get(ceiling_key)
        actual = result.get(metric)
        if ceiling is None or actual is None:
            continue
        if float(actual) > float(ceiling):
            failures.append(
                "%s exceeded ceiling: %.2fs > %.2fs"
                % (metric, float(actual), float(ceiling))
            )
    return failures


def append_history(path: Path, record) -> None:
    """Append one deterministic JSON object without rewriting prior history."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical_json(record) + "\n")


def _strategy_path(suite: LocalStrategySuite, strategy: str) -> Path:
    config = suite.strategies[strategy]["config"]
    return suite.strategies_path / config["strategy_name"] / config["strategy_file"]


def _current_identity(suite: LocalStrategySuite, strategy: str):
    config = suite.strategies[strategy]["config"]
    strategy_path = _strategy_path(suite, strategy)
    if not strategy_path.is_file():
        raise StrategyRegressionError("strategy file is missing: %s" % strategy_path)
    return {
        "configuration_fingerprint": configuration_fingerprint(config, strategy_path),
        "data_range_fingerprint": data_range_fingerprint(
            config, suite.data_path, strategy_path, suite.checksum_cache_path
        ),
    }


def _measured_runner_class():
    from simtradelab.backtest.runner import BacktestRunner

    class MeasuredBacktestRunner(BacktestRunner):
        def _execute_backtest(self, engine, date_range):
            start = time.perf_counter()
            try:
                return super()._execute_backtest(engine, date_range)
            finally:
                self.execution_seconds = time.perf_counter() - start

    return MeasuredBacktestRunner


def _structured_result(
    suite: LocalStrategySuite, strategy: str, report, runner, wall_seconds: float
):
    stats = report.get("_stats")
    if stats is None:
        raise StrategyRegressionError("runner report does not contain structured stats")

    metrics = {}
    for metric in NUMERIC_TOLERANCES:
        if metric not in report:
            raise StrategyRegressionError("runner report is missing metric: %s" % metric)
        metrics[metric] = float(report[metric])

    exact = {
        "trading_days": int(report["trading_days"]),
        "trade_count": len(stats.trades),
        "portfolio_fingerprint": _fingerprint(
            [format(float(value), ".2f") for value in stats.portfolio_values]
        ),
        "positions_count_fingerprint": _fingerprint(
            [int(value) for value in stats.positions_count]
        ),
        "trade_fingerprint": _fingerprint([list(trade) for trade in stats.trades]),
    }
    identity = _current_identity(suite, strategy)
    return {
        "strategy": strategy,
        **identity,
        "source_fingerprint": source_fingerprint(),
        "metrics": metrics,
        "exact": exact,
        "wall_seconds": round(float(wall_seconds), 6),
        "execution_seconds": round(float(runner.execution_seconds), 6),
    }


def _run_worker(
    suite: LocalStrategySuite, strategy: str, result_path: Path
) -> int:
    from simtradelab.backtest.config import BacktestConfig

    config_values = dict(suite.strategies[strategy]["config"])
    config_values["data_path"] = str(suite.data_path)
    config_values["strategies_path"] = str(suite.strategies_path)
    config = BacktestConfig(**config_values)
    runner = _measured_runner_class()()
    start = time.perf_counter()
    report = runner.run(config=config)
    wall_seconds = time.perf_counter() - start
    if not report:
        raise StrategyRegressionError("backtest returned an empty report")
    result = _structured_result(suite, strategy, report, runner, wall_seconds)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def subprocess_timeout_seconds(baseline_entry) -> float:
    """Allow only a small process-start margin beyond the reviewed wall limit."""
    return (
        float(baseline_entry["performance"]["wall_seconds_ceiling"])
        + SUBPROCESS_STARTUP_ALLOWANCE_SECONDS
    )


def _terminate_worker_process(
    process,
    posix: bool | None = None,
    windows: bool | None = None,
    grace_seconds: float = 5.0,
) -> None:
    """Terminate the whole worker tree where the platform provides that primitive."""
    if process.poll() is not None:
        return
    if posix is None:
        posix = os.name == "posix"
    if windows is None:
        windows = os.name == "nt"

    try:
        if posix:
            os.killpg(process.pid, signal.SIGTERM)
        elif windows:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=grace_seconds,
            )
        else:
            process.terminate()
        process.wait(timeout=grace_seconds)
        return
    except (ProcessLookupError, subprocess.TimeoutExpired):
        pass

    try:
        if posix:
            os.killpg(process.pid, signal.SIGKILL)
        elif windows:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=grace_seconds,
            )
        else:
            process.kill()
    except ProcessLookupError:
        return
    process.wait()


def _run_strategy_subprocess(
    config_path: Path, strategy: str, timeout_seconds: float
):
    with tempfile.TemporaryDirectory(prefix="simtradelab-regression-") as temp_dir:
        temp_path = Path(temp_dir)
        result_path = temp_path / "result.json"
        log_path = temp_path / "worker.log"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--config",
            str(config_path),
            "--worker",
            strategy,
            "--result-file",
            str(result_path),
        ]
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = "0"
        with log_path.open("w", encoding="utf-8") as log_handle:
            process_kwargs = {
                "cwd": REPOSITORY_ROOT,
                "env": environment,
                "stdout": log_handle,
                "stderr": subprocess.STDOUT,
                "text": True,
            }
            if os.name == "posix":
                process_kwargs["start_new_session"] = True
            elif os.name == "nt":
                process_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            process = subprocess.Popen(command, **process_kwargs)
            try:
                returncode = process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired as exc:
                _terminate_worker_process(process)
                timed_out = exc
            else:
                timed_out = None
        if timed_out is not None:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = "\n".join(lines[-30:])
            message = "%s worker timed out after %.2fs" % (strategy, timeout_seconds)
            if tail:
                message += "\n" + tail
            raise StrategyRegressionError(message) from timed_out
        if returncode != 0 or not result_path.is_file():
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = "\n".join(lines[-30:])
            raise StrategyRegressionError(
                "%s worker failed with exit code %d\n%s"
                % (strategy, returncode, tail)
            )
        try:
            return json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise StrategyRegressionError(
                "%s worker returned invalid JSON" % strategy
            ) from exc


def _load_baseline(path: Path):
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StrategyRegressionError(
            "baseline is missing; run with --update-baseline after reviewing the results"
        ) from exc
    except json.JSONDecodeError as exc:
        raise StrategyRegressionError("baseline is not valid JSON: %s" % path) from exc
    if not isinstance(baseline, dict):
        raise StrategyRegressionError("baseline root must be an object")
    if baseline.get("schema_version") != SCHEMA_VERSION:
        raise StrategyRegressionError("unsupported baseline schema: %r" % baseline.get("schema_version"))
    if not isinstance(baseline.get("strategies"), dict):
        raise StrategyRegressionError("baseline must contain a strategies object")
    for strategy, entry in baseline["strategies"].items():
        if not isinstance(entry, dict):
            raise StrategyRegressionError("%s baseline entry must be an object" % strategy)
        for field in ("configuration_fingerprint", "data_range_fingerprint"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise StrategyRegressionError("%s %s is missing" % (strategy, field))
        correctness = entry.get("correctness")
        if not isinstance(correctness, dict) or not isinstance(
            correctness.get("exact"), dict
        ) or not isinstance(correctness.get("numeric"), dict):
            raise StrategyRegressionError("%s correctness baseline is invalid" % strategy)
        performance = entry.get("performance")
        _validate_performance(strategy, performance)
    return baseline


def _baseline_entry(result, performance):
    return {
        "configuration_fingerprint": result["configuration_fingerprint"],
        "data_range_fingerprint": result["data_range_fingerprint"],
        "source_fingerprint": result["source_fingerprint"],
        "correctness": {
            "exact": result["exact"],
            "numeric": {
                metric: {
                    "expected": result["metrics"][metric],
                    "abs_tolerance": tolerance,
                }
                for metric, tolerance in NUMERIC_TOLERANCES.items()
            },
        },
        "performance": dict(performance),
    }


def _write_baseline(path: Path, baseline) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _history_record(result, status: str, failures):
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "failures": failures,
        **result,
    }


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Run local correctness and wide performance regression checks for "
            "a private strategy suite."
        )
    )
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument("--strategy", help="run one configured strategy")
    targets.add_argument("--all", action="store_true", help="run the configured suite")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="private local suite config (default: .simtradelab-strategy-regression.json)",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="replace expectations for the selected strategies after review",
    )
    parser.add_argument(
        "--history",
        type=Path,
        help="override the append-only JSONL history path from the local config",
    )
    parser.add_argument(
        "--no-history", action="store_true", help="do not append machine-specific history"
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="override the private baseline path derived from the local config",
    )
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--result-file", type=Path, help=argparse.SUPPRESS)
    return parser


def main(argv=None):
    args = _build_parser().parse_args(argv)
    try:
        suite = _load_suite_config(args.config)
    except StrategyRegressionError as exc:
        print("Strategy regression failed: %s" % exc, file=sys.stderr)
        return 2

    if args.worker:
        if args.strategy or args.all or args.result_file is None:
            print("worker mode requires only --worker and --result-file", file=sys.stderr)
            return 2
        if args.worker not in suite.strategies:
            print("worker strategy is not defined in the local config", file=sys.stderr)
            return 2
        try:
            return _run_worker(suite, args.worker, args.result_file)
        except Exception as exc:
            print("strategy regression worker failed: %s" % exc, file=sys.stderr)
            return 2

    if not args.strategy and not args.all:
        print("choose --strategy NAME or --all", file=sys.stderr)
        return 2
    if args.strategy and args.strategy not in suite.strategies:
        print(
            "%s is not defined in the local strategy regression config" % args.strategy,
            file=sys.stderr,
        )
        return 2
    selected = list(suite.strategies) if args.all else [args.strategy]
    baseline_path = args.baseline or suite.baseline_path
    history_path = args.history or suite.history_path

    try:
        baseline = None
        if not args.update_baseline:
            baseline = _load_baseline(baseline_path)
            preflight_failures = []
            for strategy in selected:
                entry = baseline["strategies"].get(strategy)
                if entry is None:
                    preflight_failures.append("%s is missing from the baseline" % strategy)
                    continue
                preflight_failures.extend(
                    "%s: %s" % (strategy, failure)
                    for failure in validate_fingerprints(
                        _current_identity(suite, strategy), entry
                    )
                )
            if preflight_failures:
                for failure in preflight_failures:
                    print("FAIL %s" % failure, file=sys.stderr)
                return 1

        results = []
        failed = False
        for strategy in selected:
            print("RUN  %s" % strategy, flush=True)
            try:
                timeout_entry = (
                    {"performance": suite.strategies[strategy]["performance"]}
                    if args.update_baseline
                    else baseline["strategies"][strategy]
                )
                result = _run_strategy_subprocess(
                    suite.config_path,
                    strategy,
                    subprocess_timeout_seconds(timeout_entry),
                )
            except StrategyRegressionError as exc:
                failed = True
                print("FAIL %s: %s" % (strategy, exc), file=sys.stderr)
                continue

            failures = []
            if not args.update_baseline:
                entry = baseline["strategies"][strategy]
                failures.extend(validate_fingerprints(result, entry))
                failures.extend(compare_correctness(result, entry["correctness"]))
                failures.extend(compare_performance(result, entry["performance"]))
            status = "failed" if failures else "passed"
            if not args.no_history:
                append_history(history_path, _history_record(result, status, failures))
            results.append(result)

            if failures:
                failed = True
                print("FAIL %s" % strategy, file=sys.stderr)
                for failure in failures:
                    print("  - %s" % failure, file=sys.stderr)
            else:
                print(
                    "PASS %s | return %.6f%% | trades %d | wall %.2fs | execution %.2fs"
                    % (
                        strategy,
                        result["metrics"]["total_return"] * 100,
                        result["exact"]["trade_count"],
                        result["wall_seconds"],
                        result["execution_seconds"],
                    )
                )

        if args.update_baseline:
            if len(results) != len(selected):
                return 1
            if baseline_path.exists():
                baseline = _load_baseline(baseline_path)
            else:
                baseline = {"schema_version": SCHEMA_VERSION, "strategies": {}}
            for result in results:
                strategy = result["strategy"]
                baseline["strategies"][strategy] = _baseline_entry(
                    result, suite.strategies[strategy]["performance"]
                )
            baseline["performance_policy"] = {
                "type": "explicit_reviewed_ceilings",
                "subprocess_startup_allowance_seconds": SUBPROCESS_STARTUP_ALLOWANCE_SECONDS,
            }
            _write_baseline(baseline_path, baseline)
            print("Updated reviewed baseline: %s" % baseline_path)

        return 1 if failed else 0
    except StrategyRegressionError as exc:
        print("Strategy regression failed: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
