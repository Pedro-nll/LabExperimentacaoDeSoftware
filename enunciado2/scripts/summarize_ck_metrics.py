#!/usr/bin/env python3
"""Summarize CK class-level metrics for pilot output."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path
from typing import Iterable

METRIC_ALIASES = {
    "cbo": ["cbo"],
    "dit": ["dit"],
    "lcom": ["lcom"],
    "lcom_star": ["lcom*", "lcom_star", "lcomhs", "lcom_hs"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize CK outputs")
    parser.add_argument("--input-dir", required=True, help="Root dir containing per-repo CK output")
    parser.add_argument("--output-csv", required=True, help="Summary output CSV")
    return parser.parse_args()


def safe_float(value: str) -> float | None:
    try:
        parsed = float(value)
        if not math.isfinite(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def locate_column(headers: Iterable[str], aliases: list[str]) -> str | None:
    lowered = {h.lower().strip(): h for h in headers}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


def aggregate(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return (0.0, 0.0, 0.0)
    if len(values) == 1:
        v = values[0]
        return (v, v, 0.0)
    return (
        statistics.mean(values),
        statistics.median(values),
        statistics.stdev(values),
    )


def summarize_class_csv(class_csv: Path) -> dict[str, float] | None:
    with class_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return None

        metric_columns = {
            metric_name: locate_column(reader.fieldnames, aliases)
            for metric_name, aliases in METRIC_ALIASES.items()
        }

        values = {key: [] for key in METRIC_ALIASES}
        class_count = 0

        for row in reader:
            class_count += 1
            for metric_name, column in metric_columns.items():
                if not column:
                    continue
                metric_value = safe_float(row.get(column, ""))
                if metric_value is not None:
                    values[metric_name].append(metric_value)

    result: dict[str, float] = {"class_count": float(class_count)}
    for metric_name in METRIC_ALIASES:
        mean_v, median_v, std_v = aggregate(values[metric_name])
        result[f"{metric_name}_mean"] = mean_v
        result[f"{metric_name}_median"] = median_v
        result[f"{metric_name}_std"] = std_v

    return result


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_csv = Path(args.output_csv).resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir not found: {input_dir}")

    summary_rows: list[dict[str, str]] = []
    for repo_dir in sorted([p for p in input_dir.iterdir() if p.is_dir()]):
        class_csv = repo_dir / "class.csv"
        if not class_csv.exists():
            continue

        stats = summarize_class_csv(class_csv)
        if not stats:
            continue

        owner_repo = repo_dir.name.replace("__", "/", 1)
        owner, repo = owner_repo.split("/", 1) if "/" in owner_repo else ("", owner_repo)

        row = {
            "owner": owner,
            "repo": repo,
            "class_count": str(int(stats["class_count"])),
            "cbo_mean": f"{stats['cbo_mean']:.6f}",
            "cbo_median": f"{stats['cbo_median']:.6f}",
            "cbo_std": f"{stats['cbo_std']:.6f}",
            "dit_mean": f"{stats['dit_mean']:.6f}",
            "dit_median": f"{stats['dit_median']:.6f}",
            "dit_std": f"{stats['dit_std']:.6f}",
            "lcom_mean": f"{stats['lcom_mean']:.6f}",
            "lcom_median": f"{stats['lcom_median']:.6f}",
            "lcom_std": f"{stats['lcom_std']:.6f}",
            "lcom_star_mean": f"{stats['lcom_star_mean']:.6f}",
            "lcom_star_median": f"{stats['lcom_star_median']:.6f}",
            "lcom_star_std": f"{stats['lcom_star_std']:.6f}",
        }
        summary_rows.append(row)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "owner",
        "repo",
        "class_count",
        "cbo_mean",
        "cbo_median",
        "cbo_std",
        "dit_mean",
        "dit_median",
        "dit_std",
        "lcom_mean",
        "lcom_median",
        "lcom_std",
        "lcom_star_mean",
        "lcom_star_median",
        "lcom_star_std",
    ]

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    print(f"Wrote {len(summary_rows)} rows to {output_csv}")
    return 0 if summary_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
