#!/usr/bin/env python3
"""Quick progress report for the CK processing pipeline."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show CK pipeline progress")
    parser.add_argument(
        "--repos-csv",
        default="enunciado2/data/java_top1000.csv",
        help="Input CSV with target repositories",
    )
    parser.add_argument(
        "--run-log",
        default="enunciado2/output/pipeline_run_log.csv",
        help="Pipeline run log CSV",
    )
    parser.add_argument(
        "--output-dir",
        default="enunciado2/output",
        help="Root output dir containing per-repo CK folders",
    )
    parser.add_argument(
        "--top-errors",
        type=int,
        default=8,
        help="How many grouped error messages to show",
    )
    return parser.parse_args()


def load_target_repos(path: Path) -> set[tuple[str, str]]:
    targets: set[tuple[str, str]] = set()
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            owner = (row.get("owner") or "").strip()
            repo = (row.get("repo") or "").strip()
            if owner and repo:
                targets.add((owner, repo))
    return targets


def normalize_error(message: str) -> str:
    if "returned non-zero exit status 1" in message:
        return "ck_failed_exit_status_1"
    if "timed out" in message.lower():
        return "timeout"
    if "rpc failed" in message.lower() or "early eof" in message.lower():
        return "git_network_error"
    if "invalid environment settings" in message.lower():
        return "ck_invalid_environment"
    if "nullpointerexception" in message.lower():
        return "ck_null_pointer"
    if "empty stack" in message.lower() or "emptystackexception" in message.lower():
        return "ck_empty_stack"
    if not message.strip():
        return "unknown"
    return message.strip().splitlines()[0][:120]


def load_run_log(path: Path) -> tuple[dict[tuple[str, str], str], Counter[str], Counter[str], int]:
    latest_status: dict[tuple[str, str], str] = {}
    latest_error_buckets: Counter[str] = Counter()
    historical_error_buckets: Counter[str] = Counter()
    attempts = 0

    latest_error_message: dict[tuple[str, str], str] = {}

    if not path.exists():
        return latest_status, latest_error_buckets, historical_error_buckets, attempts

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            attempts += 1
            owner = (row.get("owner") or "").strip()
            repo = (row.get("repo") or "").strip()
            status = (row.get("status") or "").strip().lower()
            message = row.get("message") or ""
            if not owner or not repo:
                continue

            key = (owner, repo)
            latest_status[key] = status
            if status == "error":
                normalized = normalize_error(message)
                historical_error_buckets[normalized] += 1
                latest_error_message[key] = normalized
            else:
                latest_error_message.pop(key, None)

    for key, status in latest_status.items():
        if status == "error":
            label = latest_error_message.get(key, "unknown")
            latest_error_buckets[label] += 1

    return latest_status, latest_error_buckets, historical_error_buckets, attempts


def count_ck_outputs(output_dir: Path) -> tuple[int, int]:
    repo_dirs = [p for p in output_dir.iterdir() if p.is_dir()] if output_dir.exists() else []
    with_class_csv = 0
    for repo_dir in repo_dirs:
        if (repo_dir / "class.csv").exists():
            with_class_csv += 1
    return len(repo_dirs), with_class_csv


def main() -> int:
    args = parse_args()
    repos_csv = Path(args.repos_csv).resolve()
    run_log = Path(args.run_log).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not repos_csv.exists():
        raise FileNotFoundError(f"repos CSV not found: {repos_csv}")

    targets = load_target_repos(repos_csv)
    latest_status, latest_error_buckets, historical_error_buckets, attempts = load_run_log(run_log)

    ok = sum(1 for repo in targets if latest_status.get(repo) == "ok")
    err = sum(1 for repo in targets if latest_status.get(repo) == "error")
    done = ok + err
    pending = len(targets) - done

    pct_done = (done / len(targets) * 100) if targets else 0.0
    pct_ok = (ok / len(targets) * 100) if targets else 0.0

    repo_dirs, with_class_csv = count_ck_outputs(output_dir)

    print("CK Pipeline Progress")
    print("=" * 28)
    print(f"Target repositories    : {len(targets)}")
    print(f"Log attempts           : {attempts}")
    print(f"Processed total        : {done} ({pct_done:.2f}%)")
    print(f"Successful (ok)        : {ok} ({pct_ok:.2f}%)")
    print(f"Failed (error)         : {err}")
    print(f"Pending                : {pending}")
    print()
    print(f"Output repo folders    : {repo_dirs}")
    print(f"Folders with class.csv : {with_class_csv}")
    print()

    if latest_error_buckets:
        print("Top error groups (latest status only)")
        print("-" * 28)
        for label, count in latest_error_buckets.most_common(args.top_errors):
            print(f"{label:<40} {count}")
        print()

    if historical_error_buckets:
        print("Top error groups (all attempts)")
        print("-" * 28)
        for label, count in historical_error_buckets.most_common(args.top_errors):
            print(f"{label:<40} {count}")
    else:
        print("No errors recorded in run log.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
