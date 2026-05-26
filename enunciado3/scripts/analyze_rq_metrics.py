#!/usr/bin/env python3
"""Generate scatter plots and statistical analysis for Code Review RQs.

RQs analyzed:
- RQ1-4: final_feedback vs PR metrics (size, analysis_time, description, interactions)
- RQ5-8: human_review_count vs PR metrics (size, analysis_time, description, interactions)
"""

from __future__ import annotations

import argparse
import math
import statistics
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


# Configuration
METRIC_CONFIGS = {
    "size_metrics": {
        "changed_files": "Changed Files",
        "total_changes": "Total Changes (lines)",
        "additions": "Lines Added",
        "deletions": "Lines Deleted",
    },
    "time_metrics": {
        "analysis_hours": "Analysis Time (hours)",
    },
    "description_metrics": {
        "body_chars": "Description Length (chars)",
    },
    "interaction_metrics": {
        "total_comments": "Total Comments",
        "participant_count": "Participant Count",
    },
}

FEEDBACK_TYPES = ["no_review", "commented", "approved", "changes_requested", "positive"]
REVIEW_METRICS = ["approved_count", "changes_requested_count", "commented_count", "human_review_count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate RQ scatter plots and statistics for code review analysis"
    )
    parser.add_argument("--aggregated-csv", required=True, help="Aggregated PR data CSV")
    parser.add_argument("--output-dir", required=True, help="Directory for PNG and text outputs")
    parser.add_argument(
        "--analysis-date",
        default="",
        help="Date used for reference (YYYY-MM-DD). Defaults to today UTC.",
    )
    return parser.parse_args()


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and preprocess PR data."""
    df = pd.read_csv(csv_path)
    
    # Convert numeric columns
    numeric_cols = [
        "changed_files", "total_changes", "additions", "deletions",
        "analysis_hours", "body_chars", "total_comments", "participant_count",
        "human_review_count", "approved_count", "changes_requested_count", "commented_count"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Filter out rows with missing critical values
    df = df.replace([np.inf, -np.inf], np.nan)
    
    return df


def calculate_correlation(x: pd.Series, y: pd.Series) -> Tuple[float, float]:
    """Calculate Pearson and Spearman correlations."""
    # Remove NaN values
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return np.nan, np.nan
    
    pearson = x_clean.corr(y_clean, method="pearson")
    spearman = x_clean.corr(y_clean, method="spearman")
    
    return pearson, spearman


def create_scatter_plot(
    ax: plt.Axes,
    x: pd.Series,
    y: pd.Series,
    x_label: str,
    y_label: str,
    title: str,
) -> None:
    """Create a scatter plot with optional trend line and correlation info."""
    # Remove NaN values
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) == 0:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", transform=ax.transAxes)
        return
    
    # Create scatter plot
    ax.scatter(x_clean, y_clean, alpha=0.6, s=30, color="steelblue", edgecolors="navy", linewidth=0.5)
    
    # Add trend line if sufficient data
    if len(x_clean) >= 2:
        try:
            slope, intercept = np.polyfit(x_clean, y_clean, 1)
            x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, "r--", linewidth=2, label="Trend line", alpha=0.8)
            ax.legend(fontsize=9)
        except Exception:
            pass
    
    # Calculate and display correlation
    pearson, spearman = calculate_correlation(x, y)
    if not np.isnan(pearson) and not np.isnan(spearman):
        correlation_text = f"Pearson: {pearson:.3f}\nSpearman: {spearman:.3f}\nn={len(x_clean)}"
        ax.text(
            0.05, 0.95, correlation_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )
    
    ax.set_xlabel(x_label, fontsize=10)
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)


def analyze_rq_feedback_vs_metric(
    df: pd.DataFrame,
    metric_col: str,
    metric_label: str,
    output_dir: Path,
    rq_number: int,
) -> dict:
    """Analyze feedback vs a metric (for RQs 1-4)."""
    results = {
        "rq": f"RQ{rq_number}",
        "metric": metric_col,
        "metric_label": metric_label,
        "correlations": {},
    }
    
    # Calculate summary statistics for the metric
    metric_data = df[metric_col].dropna()
    if len(metric_data) > 0:
        results["metric_stats"] = {
            "count": len(metric_data),
            "mean": metric_data.mean(),
            "median": metric_data.median(),
            "std": metric_data.std(),
            "min": metric_data.min(),
            "max": metric_data.max(),
        }
    
    # Create plots for each feedback type
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"RQ{rq_number}: Final Feedback vs {metric_label}", fontsize=13, fontweight="bold")
    axes = axes.flatten()
    
    feedback_types = ["no_review", "commented", "approved", "changes_requested"]
    
    for idx, feedback_type in enumerate(feedback_types):
        # Create binary feedback (has this type or not)
        feedback_col = f"has_{feedback_type}"
        df[feedback_col] = df["final_feedback_normalized"].fillna("no_review").str.contains(
            feedback_type, case=False, regex=False
        ).astype(int)
        
        x = df[metric_col]
        y = df[feedback_col]
        
        pearson, spearman = calculate_correlation(x, y)
        results["correlations"][feedback_type] = {
            "pearson": pearson,
            "spearman": spearman,
        }
        
        title = f"{feedback_type.capitalize()} Feedback"
        create_scatter_plot(
            axes[idx],
            x, y,
            metric_label,
            f"Has {feedback_type.title()} (0/1)",
            title,
        )
    
    plt.tight_layout()
    output_path = output_dir / f"rq{rq_number}_feedback_vs_{metric_col}.png"
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")
    
    return results


def analyze_rq_reviews_vs_metric(
    df: pd.DataFrame,
    metric_col: str,
    metric_label: str,
    output_dir: Path,
    rq_number: int,
) -> dict:
    """Analyze review count vs a metric (for RQs 5-8)."""
    results = {
        "rq": f"RQ{rq_number}",
        "metric": metric_col,
        "metric_label": metric_label,
        "correlations": {},
    }
    
    # Calculate summary statistics for the metric
    metric_data = df[metric_col].dropna()
    if len(metric_data) > 0:
        results["metric_stats"] = {
            "count": len(metric_data),
            "mean": metric_data.mean(),
            "median": metric_data.median(),
            "std": metric_data.std(),
            "min": metric_data.min(),
            "max": metric_data.max(),
        }
    
    # Create plots for each review type
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"RQ{rq_number}: Review Count vs {metric_label}", fontsize=13, fontweight="bold")
    axes = axes.flatten()
    
    review_types = [
        ("human_review_count", "Human Reviews"),
        ("approved_count", "Approved Reviews"),
        ("changes_requested_count", "Changes Requested"),
        ("commented_count", "Comments"),
    ]
    
    for idx, (review_col, label) in enumerate(review_types):
        if review_col not in df.columns:
            continue
        
        x = df[metric_col]
        y = df[review_col]
        
        pearson, spearman = calculate_correlation(x, y)
        results["correlations"][review_col] = {
            "pearson": pearson,
            "spearman": spearman,
        }
        
        create_scatter_plot(
            axes[idx],
            x, y,
            metric_label,
            label,
            label,
        )
    
    plt.tight_layout()
    output_path = output_dir / f"rq{rq_number}_reviews_vs_{metric_col}.png"
    plt.savefig(output_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")
    
    return results


def generate_summary_report(
    df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Generate a summary statistics report."""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("CODE REVIEW METRICS SUMMARY REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"\nTotal PR records analyzed: {len(df)}")
    report_lines.append(f"\nFinal Feedback Distribution:")
    
    feedback_counts = df["final_feedback_normalized"].value_counts()
    for feedback, count in feedback_counts.items():
        pct = 100 * count / len(df)
        report_lines.append(f"  {feedback}: {count} ({pct:.1f}%)")
    
    report_lines.append(f"\n\nPR Size Metrics Summary:")
    for metric, label in METRIC_CONFIGS["size_metrics"].items():
        if metric in df.columns:
            data = df[metric].dropna()
            if len(data) > 0:
                report_lines.append(f"\n  {label}:")
                report_lines.append(f"    Mean: {data.mean():.2f}")
                report_lines.append(f"    Median: {data.median():.2f}")
                report_lines.append(f"    Std: {data.std():.2f}")
                report_lines.append(f"    Min: {data.min():.2f}, Max: {data.max():.2f}")
    
    report_lines.append(f"\n\nAnalysis Time (Hours):")
    if "analysis_hours" in df.columns:
        data = df["analysis_hours"].dropna()
        if len(data) > 0:
            report_lines.append(f"  Mean: {data.mean():.2f}")
            report_lines.append(f"  Median: {data.median():.2f}")
            report_lines.append(f"  Std: {data.std():.2f}")
    
    report_lines.append(f"\n\nDescription Length (Characters):")
    if "body_chars" in df.columns:
        data = df["body_chars"].dropna()
        if len(data) > 0:
            report_lines.append(f"  Mean: {data.mean():.2f}")
            report_lines.append(f"  Median: {data.median():.2f}")
            report_lines.append(f"  Std: {data.std():.2f}")
    
    report_lines.append(f"\n\nInteraction Metrics:")
    for metric, label in METRIC_CONFIGS["interaction_metrics"].items():
        if metric in df.columns:
            data = df[metric].dropna()
            if len(data) > 0:
                report_lines.append(f"\n  {label}:")
                report_lines.append(f"    Mean: {data.mean():.2f}")
                report_lines.append(f"    Median: {data.median():.2f}")
                report_lines.append(f"    Std: {data.std():.2f}")
    
    report_lines.append("\n" + "=" * 80)
    
    report_text = "\n".join(report_lines)
    output_path = output_dir / "summary_report.txt"
    output_path.write_text(report_text, encoding="utf-8")
    print(f"\nSaved summary report: {output_path}")


def main() -> int:
    args = parse_args()
    aggregated_csv = Path(args.aggregated_csv).resolve()
    output_dir = Path(args.output_dir).resolve()
    
    if not aggregated_csv.exists():
        print(f"Error: Aggregated CSV not found: {aggregated_csv}")
        return 1
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading data from {aggregated_csv}...")
    df = load_data(aggregated_csv)
    print(f"Loaded {len(df)} PR records")
    
    # Generate summary report
    generate_summary_report(df, output_dir)
    
    # RQ1-4: Final Feedback vs PR Metrics
    print("\n" + "=" * 60)
    print("Generating RQ1-4 plots (Feedback vs PR Metrics)...")
    print("=" * 60)
    
    rq_counter = 1
    for metric_col, metric_label in METRIC_CONFIGS["size_metrics"].items():
        if metric_col in df.columns:
            analyze_rq_feedback_vs_metric(df, metric_col, metric_label, output_dir, rq_counter)
            rq_counter += 1
    
    # RQ5-8: Review Count vs PR Metrics
    print("\n" + "=" * 60)
    print("Generating RQ5-8 plots (Review Count vs PR Metrics)...")
    print("=" * 60)
    
    rq_counter = 5
    for metric_col, metric_label in METRIC_CONFIGS["size_metrics"].items():
        if metric_col in df.columns:
            analyze_rq_reviews_vs_metric(df, metric_col, metric_label, output_dir, rq_counter)
            rq_counter += 1
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"Output directory: {output_dir}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
