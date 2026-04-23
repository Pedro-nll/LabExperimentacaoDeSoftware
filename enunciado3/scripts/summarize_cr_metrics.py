#!/usr/bin/env python3
"""Summarize the collected code review metrics."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path
from typing import Dict, List


NUMERIC_COLUMNS = [
    "body_chars",
    "changed_files",
    "additions",
    "deletions",
    "total_changes",
    "issue_comments",
    "review_comments",
    "total_comments",
    "human_review_count",
    "participant_count",
    "analysis_hours",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize PR metrics from collected CSVs")
    parser.add_argument("--input-dir", required=True, help="Directory containing per-repo prs.csv files")
    parser.add_argument("--output-csv", required=True, help="Output CSV for metric summary")
    parser.add_argument(
        "--feedback-output-csv",
        default="",
        help="Optional output CSV for final feedback distribution",
    )
    return parser.parse_args()


def safe_float(value: str) -> float | None:
    try:
        parsed = float(value)
        if not math.isfinite(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def collect_pr_files(input_dir: Path) -> List[Path]:
    return sorted(input_dir.glob("*/prs.csv"))


def summarize_values(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"count": 0.0, "mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    if len(values) == 1:
        value = values[0]
        return {"count": 1.0, "mean": value, "median": value, "std": 0.0, "min": value, "max": value}
    return {
        "count": float(len(values)),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "std": statistics.stdev(values),
        "min": min(values),
        "max": max(values),
    }


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_csv = Path(args.output_csv).resolve()
    feedback_output = Path(args.feedback_output_csv).resolve() if args.feedback_output_csv else None

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    values_by_metric: Dict[str, List[float]] = {metric: [] for metric in NUMERIC_COLUMNS}
    feedback_counts: Dict[str, int] = {}
    total_rows = 0

    pr_files = collect_pr_files(input_dir)
    for csv_file in pr_files:
        with csv_file.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                for metric in NUMERIC_COLUMNS:
                    metric_value = safe_float(row.get(metric, ""))
                    if metric_value is not None:
                        values_by_metric[metric].append(metric_value)
                feedback = (row.get("final_feedback", "") or "").strip() or "unknown"
                feedback_counts[feedback] = feedback_counts.get(feedback, 0) + 1

    summary_rows: List[Dict[str, str]] = []
    for metric in NUMERIC_COLUMNS:
        stats = summarize_values(values_by_metric[metric])
        summary_rows.append(
            {
                "metric": metric,
                "count": str(int(stats["count"])),
                "mean": f"{stats['mean']:.6f}",
                "median": f"{stats['median']:.6f}",
                "std": f"{stats['std']:.6f}",
                "min": f"{stats['min']:.6f}",
                "max": f"{stats['max']:.6f}",
            }
        )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "count", "mean", "median", "std", "min", "max"])
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    if feedback_output is not None:
        feedback_output.parent.mkdir(parents=True, exist_ok=True)
        with feedback_output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["final_feedback", "count"])
            writer.writeheader()
            for feedback, count in sorted(feedback_counts.items()):
                writer.writerow({"final_feedback": feedback, "count": str(count)})

    print(f"Processed {total_rows} PR rows from {len(pr_files)} repositories")
    print(f"Wrote metric summary to {output_csv}")
    if feedback_output is not None:
        print(f"Wrote feedback summary to {feedback_output}")
    return 0 if total_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())