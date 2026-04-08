#!/usr/bin/env python3
"""Generate scatter plots for the CK study RQs.

The script merges GitHub repository metadata with CK summary metrics and
creates one scatter plot per RQ and quality metric combination.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


QUALITY_METRICS = {
    "cbo_median": "CBO",
    "dit_median": "DIT",
    "lcom_median": "LCOM",
    "lcom_star_median": "LCOM*",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot RQ scatter graphs for CK study")
    parser.add_argument("--repos-csv", required=True, help="CSV with GitHub repository metadata")
    parser.add_argument("--ck-summary-csv", required=True, help="CSV with CK summary metrics")
    parser.add_argument("--output-dir", required=True, help="Directory for PNG and text outputs")
    parser.add_argument(
        "--analysis-date",
        default="",
        help="Date used to compute age_years (YYYY-MM-DD). Defaults to today UTC.",
    )
    return parser.parse_args()


def to_datetime(value: str) -> pd.Timestamp | None:
    if not value:
        return None
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed


def load_merged_frame(repos_csv: Path, ck_summary_csv: Path, analysis_date: str) -> pd.DataFrame:
    repos_df = pd.read_csv(repos_csv)
    ck_df = pd.read_csv(ck_summary_csv)

    merged = repos_df.merge(ck_df, on=["owner", "repo"], how="inner")

    if analysis_date:
        anchor = pd.Timestamp(analysis_date, tz="UTC")
    else:
        anchor = pd.Timestamp.now(tz="UTC")

    created = pd.to_datetime(merged["created_at"], utc=True, errors="coerce")
    merged["age_years"] = (anchor - created).dt.total_seconds() / (365.25 * 24 * 3600)

    pushed = pd.to_datetime(merged["pushed_at"], utc=True, errors="coerce")
    merged["days_since_push"] = (anchor - pushed).dt.total_seconds() / (24 * 3600)

    if "releases" in merged.columns:
        merged["activity_count"] = pd.to_numeric(merged["releases"], errors="coerce")
    elif "releases_count" in merged.columns:
        merged["activity_count"] = pd.to_numeric(merged["releases_count"], errors="coerce")
    else:
        merged["activity_count"] = np.nan

    merged["activity_proxy_days_since_push"] = merged["days_since_push"]

    return merged


def finite_frame(frame: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    subset = frame[[x_col, y_col, "full_name"]].copy() if "full_name" in frame.columns else frame[[x_col, y_col]].copy()
    subset = subset.replace([np.inf, -np.inf], np.nan).dropna(subset=[x_col, y_col])
    return subset


def add_trend_line(ax: plt.Axes, x: pd.Series, y: pd.Series) -> None:
    if len(x) < 2:
        return
    try:
        slope, intercept = np.polyfit(x, y, 1)
    except Exception:
        return
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, "r--", linewidth=1.5, label="Trend line")


def correlation_text(x: pd.Series, y: pd.Series) -> str:
    if len(x) < 2:
        return "n/a"
    pearson = x.corr(y, method="pearson")
    spearman = x.corr(y, method="spearman")
    if pd.isna(pearson) or pd.isna(spearman):
        return "n/a"
    return f"pearson={pearson:.4f}, spearman={spearman:.4f}"


def plot_scatter(frame: pd.DataFrame, x_col: str, y_col: str, x_label: str, y_label: str, title: str, output_path: Path) -> str:
    subset = finite_frame(frame, x_col, y_col)
    if subset.empty:
        return "skipped"

    fig, ax = plt.subplots(figsize=(11, 7))
    ax.scatter(subset[x_col], subset[y_col], alpha=0.35, s=22, edgecolors="none")
    add_trend_line(ax, subset[x_col], subset[y_col])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    if len(subset) > 1:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return correlation_text(subset[x_col], subset[y_col])


def main() -> int:
    args = parse_args()
    repos_csv = Path(args.repos_csv).resolve()
    ck_summary_csv = Path(args.ck_summary_csv).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    merged = load_merged_frame(repos_csv, ck_summary_csv, args.analysis_date)
    if merged.empty:
        raise RuntimeError("Merged dataset is empty. Check the input CSV files.")

    rq_specs = {
        "rq1_popularity": ("stargazers_count", "Stars", "RQ1: Popularity vs Quality"),
        "rq2_maturity": ("age_years", "Age (years)", "RQ2: Maturity vs Quality"),
        "rq3_activity": ("activity_count", "Releases", "RQ3: Activity vs Quality"),
        "rq4_size": ("loc_median", "LOC median", "RQ4: Size vs Quality"),
    }

    report_lines: list[str] = []
    report_lines.append(f"Merged rows: {len(merged)}")
    report_lines.append("")

    for rq_name, (x_col, x_label, rq_title) in rq_specs.items():
        if x_col not in merged.columns:
            report_lines.append(f"{rq_name}: skipped (missing column {x_col})")
            continue

        if rq_name == "rq3_activity" and merged[x_col].isna().all():
            x_col = "activity_proxy_days_since_push"
            x_label = "Days since push (proxy)"
            rq_title = "RQ3: Activity proxy vs Quality"
            report_lines.append("rq3_activity: releases unavailable; using days_since_push proxy")

        report_lines.append(rq_title)
        for metric_col, metric_label in QUALITY_METRICS.items():
            plot_path = output_dir / f"{rq_name}_{metric_col}.png"
            correlation = plot_scatter(
                merged,
                x_col=x_col,
                y_col=metric_col,
                x_label=x_label,
                y_label=metric_label,
                title=f"{rq_title} - {metric_label}",
                output_path=plot_path,
            )
            report_lines.append(f"  {metric_label}: {correlation}")
        report_lines.append("")

    report_path = output_dir / "rq_scatter_summary.txt"
    report_path.write_text("\n".join(report_lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote scatter plots to {output_dir}")
    print(f"Wrote summary to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())