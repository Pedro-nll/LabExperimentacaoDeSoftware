#!/usr/bin/env python3
"""Generate figures for Lab 05 analysis and dashboard."""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt


SCENARIO_LABELS = {
    "C1": "C1\nMetadados",
    "C2": "C2\nPRs",
    "C3": "C3\nIssues",
    "C4": "C4\nCombinada",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Lab 05 figures")
    parser.add_argument("--paired", default="enunciado5/output/analysis/paired_measurements.csv", help="Paired measurements CSV")
    parser.add_argument("--output-dir", default="enunciado5/output/analysis/figures", help="Figure output directory")
    return parser.parse_args()


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]


def as_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def median(values: List[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def grouped_values(rows: List[Dict[str, str]], column: str) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        grouped[row["scenario_id"]].append(as_float(row[column]))
    return grouped


def save_grouped_bar(rows: List[Dict[str, str]], output_dir: Path) -> None:
    scenarios = sorted({row["scenario_id"] for row in rows})
    rest_time = grouped_values(rows, "rest_elapsed_ms")
    gql_time = grouped_values(rows, "graphql_elapsed_ms")
    rest_bytes = grouped_values(rows, "rest_response_bytes")
    gql_bytes = grouped_values(rows, "graphql_response_bytes")

    x = list(range(len(scenarios)))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 5))
    rest_medians = [median(rest_time[s]) for s in scenarios]
    gql_medians = [median(gql_time[s]) for s in scenarios]
    ax.bar([i - width / 2 for i in x], rest_medians, width, label="REST", color="#4C78A8")
    ax.bar([i + width / 2 for i in x], gql_medians, width, label="GraphQL", color="#2A9D8F")
    ax.set_title("Tempo mediano de resposta por cenario")
    ax.set_ylabel("Milissegundos")
    ax.set_xticks(x, [SCENARIO_LABELS.get(s, s) for s in scenarios])
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "rq1_tempo_mediano_por_cenario.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    rest_medians = [median(rest_bytes[s]) for s in scenarios]
    gql_medians = [median(gql_bytes[s]) for s in scenarios]
    ax.bar([i - width / 2 for i in x], rest_medians, width, label="REST", color="#4C78A8")
    ax.bar([i + width / 2 for i in x], gql_medians, width, label="GraphQL", color="#2A9D8F")
    ax.set_title("Tamanho bruto mediano da resposta por cenario")
    ax.set_ylabel("Bytes em escala log")
    ax.set_yscale("log")
    ax.set_xticks(x, [SCENARIO_LABELS.get(s, s) for s in scenarios])
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "rq2_tamanho_mediano_por_cenario.png", dpi=160)
    plt.close(fig)


def save_delta_boxplots(rows: List[Dict[str, str]], output_dir: Path) -> None:
    scenarios = sorted({row["scenario_id"] for row in rows})
    labels = [SCENARIO_LABELS.get(s, s) for s in scenarios]
    time_delta = grouped_values(rows, "delta_elapsed_pct")
    size_delta = grouped_values(rows, "delta_response_pct")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot([time_delta[s] for s in scenarios], tick_labels=labels, showfliers=False)
    ax.axhline(0, color="#222222", linewidth=1)
    ax.set_title("Diferenca percentual de tempo: GraphQL vs REST")
    ax.set_ylabel("% em relacao ao REST")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "rq1_delta_percentual_tempo.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot([size_delta[s] for s in scenarios], tick_labels=labels, showfliers=False)
    ax.axhline(0, color="#222222", linewidth=1)
    ax.set_title("Diferenca percentual de tamanho: GraphQL vs REST")
    ax.set_ylabel("% em relacao ao REST")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "rq2_delta_percentual_tamanho.png", dpi=160)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    rows = read_rows(Path(args.paired))
    if not rows:
        print(f"[figures] no paired rows found at {args.paired}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_grouped_bar(rows, output_dir)
    save_delta_boxplots(rows, output_dir)
    print(f"[figures] wrote figures to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
