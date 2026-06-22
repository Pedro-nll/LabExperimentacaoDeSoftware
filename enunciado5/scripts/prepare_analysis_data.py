#!/usr/bin/env python3
"""Prepare paired datasets and summaries for Lab 05 analysis/dashboard."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from lab05_common import read_csv_rows, write_csv_rows

PAIRED_COLUMNS = [
    "pair_id",
    "repository",
    "owner",
    "repo",
    "scenario_id",
    "scenario_name",
    "run_number",
    "rest_elapsed_ms",
    "graphql_elapsed_ms",
    "delta_elapsed_ms",
    "delta_elapsed_pct",
    "rest_response_bytes",
    "graphql_response_bytes",
    "delta_response_bytes",
    "delta_response_pct",
    "rest_request_count",
    "graphql_request_count",
]

SUMMARY_COLUMNS = [
    "scenario_id",
    "scenario_name",
    "metric",
    "n_pairs",
    "rest_mean",
    "graphql_mean",
    "rest_median",
    "graphql_median",
    "median_delta",
    "median_delta_pct",
]

FAILURE_COLUMNS = ["api_type", "scenario_id", "http_status", "error", "count"]
TEST_COLUMNS = [
    "scenario_id",
    "scenario_name",
    "metric",
    "n_pairs",
    "wilcoxon_statistic",
    "p_value",
    "rest_median",
    "graphql_median",
    "median_delta",
    "median_delta_pct",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Lab 05 analysis datasets")
    parser.add_argument("--measurements", default="enunciado5/output/measurements.csv", help="Input measurements CSV")
    parser.add_argument("--output-dir", default="enunciado5/output/analysis", help="Output analysis directory")
    return parser.parse_args()


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def median(values: Iterable[float]) -> float:
    values_list = list(values)
    return statistics.median(values_list) if values_list else 0.0


def mean(values: Iterable[float]) -> float:
    values_list = list(values)
    return statistics.mean(values_list) if values_list else 0.0


def pct_delta(rest_value: float, graphql_value: float) -> float:
    if rest_value == 0:
        return 0.0
    return (graphql_value - rest_value) / rest_value * 100.0


def build_paired_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Dict[str, str]]] = defaultdict(dict)
    for row in rows:
        grouped[row.get("pair_id", "")][row.get("api_type", "")] = row

    paired_rows: List[Dict[str, Any]] = []
    for pair_id, by_api in sorted(grouped.items()):
        rest = by_api.get("REST")
        graphql = by_api.get("GraphQL")
        if not rest or not graphql:
            continue
        if rest.get("success") != "1" or graphql.get("success") != "1":
            continue

        rest_time = as_float(rest.get("elapsed_ms"))
        graphql_time = as_float(graphql.get("elapsed_ms"))
        rest_bytes = as_float(rest.get("response_bytes"))
        graphql_bytes = as_float(graphql.get("response_bytes"))

        paired_rows.append(
            {
                "pair_id": pair_id,
                "repository": rest.get("repository", ""),
                "owner": rest.get("owner", ""),
                "repo": rest.get("repo", ""),
                "scenario_id": rest.get("scenario_id", ""),
                "scenario_name": rest.get("scenario_name", ""),
                "run_number": rest.get("run_number", ""),
                "rest_elapsed_ms": f"{rest_time:.3f}",
                "graphql_elapsed_ms": f"{graphql_time:.3f}",
                "delta_elapsed_ms": f"{graphql_time - rest_time:.3f}",
                "delta_elapsed_pct": f"{pct_delta(rest_time, graphql_time):.3f}",
                "rest_response_bytes": int(rest_bytes),
                "graphql_response_bytes": int(graphql_bytes),
                "delta_response_bytes": int(graphql_bytes - rest_bytes),
                "delta_response_pct": f"{pct_delta(rest_bytes, graphql_bytes):.3f}",
                "rest_request_count": as_int(rest.get("request_count")),
                "graphql_request_count": as_int(graphql.get("request_count")),
            }
        )
    return paired_rows


def build_summary_rows(paired_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_scenario: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in paired_rows:
        by_scenario[row["scenario_id"]].append(row)

    summary_rows: List[Dict[str, Any]] = []
    metric_specs = [
        ("elapsed_ms", "rest_elapsed_ms", "graphql_elapsed_ms", "delta_elapsed_ms", "delta_elapsed_pct"),
        ("response_bytes", "rest_response_bytes", "graphql_response_bytes", "delta_response_bytes", "delta_response_pct"),
    ]
    for scenario_id, rows in sorted(by_scenario.items()):
        scenario_name = rows[0].get("scenario_name", "")
        for metric, rest_col, graphql_col, delta_col, delta_pct_col in metric_specs:
            rest_values = [as_float(row[rest_col]) for row in rows]
            graphql_values = [as_float(row[graphql_col]) for row in rows]
            delta_values = [as_float(row[delta_col]) for row in rows]
            delta_pct_values = [as_float(row[delta_pct_col]) for row in rows]
            summary_rows.append(
                {
                    "scenario_id": scenario_id,
                    "scenario_name": scenario_name,
                    "metric": metric,
                    "n_pairs": len(rows),
                    "rest_mean": f"{mean(rest_values):.3f}",
                    "graphql_mean": f"{mean(graphql_values):.3f}",
                    "rest_median": f"{median(rest_values):.3f}",
                    "graphql_median": f"{median(graphql_values):.3f}",
                    "median_delta": f"{median(delta_values):.3f}",
                    "median_delta_pct": f"{median(delta_pct_values):.3f}",
                }
            )
    return summary_rows


def build_failure_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    counts: Dict[tuple[str, str, str, str], int] = defaultdict(int)
    for row in rows:
        if row.get("success") == "1":
            continue
        key = (
            row.get("api_type", ""),
            row.get("scenario_id", ""),
            row.get("http_status", ""),
            row.get("error", ""),
        )
        counts[key] += 1
    return [
        {
            "api_type": api_type,
            "scenario_id": scenario_id,
            "http_status": http_status,
            "error": error,
            "count": count,
        }
        for (api_type, scenario_id, http_status, error), count in sorted(counts.items())
    ]


def build_test_rows(paired_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        print("[analysis] scipy not available; skipping Wilcoxon tests")
        return []

    by_scenario: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in paired_rows:
        by_scenario[row["scenario_id"]].append(row)

    test_rows: List[Dict[str, Any]] = []
    metric_specs = [
        ("elapsed_ms", "rest_elapsed_ms", "graphql_elapsed_ms", "delta_elapsed_ms", "delta_elapsed_pct"),
        ("response_bytes", "rest_response_bytes", "graphql_response_bytes", "delta_response_bytes", "delta_response_pct"),
    ]
    for scenario_id, rows in sorted(by_scenario.items()):
        scenario_name = rows[0].get("scenario_name", "")
        for metric, rest_col, graphql_col, delta_col, delta_pct_col in metric_specs:
            rest_values = [as_float(row[rest_col]) for row in rows]
            graphql_values = [as_float(row[graphql_col]) for row in rows]
            delta_values = [as_float(row[delta_col]) for row in rows]
            delta_pct_values = [as_float(row[delta_pct_col]) for row in rows]
            try:
                result = wilcoxon(graphql_values, rest_values, zero_method="wilcox", alternative="two-sided")
                statistic = float(result.statistic)
                p_value = float(result.pvalue)
            except ValueError:
                statistic = 0.0
                p_value = 1.0
            test_rows.append(
                {
                    "scenario_id": scenario_id,
                    "scenario_name": scenario_name,
                    "metric": metric,
                    "n_pairs": len(rows),
                    "wilcoxon_statistic": f"{statistic:.6f}",
                    "p_value": f"{p_value:.8f}",
                    "rest_median": f"{median(rest_values):.3f}",
                    "graphql_median": f"{median(graphql_values):.3f}",
                    "median_delta": f"{median(delta_values):.3f}",
                    "median_delta_pct": f"{median(delta_pct_values):.3f}",
                }
            )
    return test_rows


def main() -> int:
    args = parse_args()
    rows = read_csv_rows(Path(args.measurements))
    if not rows:
        print(f"[analysis] no measurements found at {args.measurements}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paired_rows = build_paired_rows(rows)
    summary_rows = build_summary_rows(paired_rows)
    failure_rows = build_failure_rows(rows)
    test_rows = build_test_rows(paired_rows)

    write_csv_rows(output_dir / "paired_measurements.csv", paired_rows, PAIRED_COLUMNS)
    write_csv_rows(output_dir / "scenario_summary.csv", summary_rows, SUMMARY_COLUMNS)
    write_csv_rows(output_dir / "failure_summary.csv", failure_rows, FAILURE_COLUMNS)
    if test_rows:
        write_csv_rows(output_dir / "wilcoxon_summary.csv", test_rows, TEST_COLUMNS)

    total = len(rows)
    successful = sum(1 for row in rows if row.get("success") == "1")
    print(f"[analysis] measurements={total} successful={successful} valid_pairs={len(paired_rows)}")
    print(f"[analysis] wrote {output_dir / 'paired_measurements.csv'}")
    print(f"[analysis] wrote {output_dir / 'scenario_summary.csv'}")
    print(f"[analysis] wrote {output_dir / 'failure_summary.csv'}")
    if test_rows:
        print(f"[analysis] wrote {output_dir / 'wilcoxon_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
