#!/usr/bin/env python3
"""Generate detailed correlation tables and statistics for RQ analysis."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate detailed RQ correlation statistics")
    parser.add_argument("--aggregated-csv", required=True, help="Aggregated PR data CSV")
    parser.add_argument("--output-dir", required=True, help="Output directory for CSV tables")
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
    
    # Replace inf with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    
    return df


def calculate_spearman_p_value(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
    """Calculate Spearman correlation and p-value."""
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return np.nan, np.nan, 0
    
    try:
        corr, p_value = stats.spearmanr(x_clean, y_clean)
        return float(corr), float(p_value), len(x_clean)
    except Exception:
        return np.nan, np.nan, len(x_clean)


def calculate_pearson_p_value(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
    """Calculate Pearson correlation and p-value."""
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return np.nan, np.nan, 0
    
    try:
        corr, p_value = stats.pearsonr(x_clean, y_clean)
        return float(corr), float(p_value), len(x_clean)
    except Exception:
        return np.nan, np.nan, len(x_clean)


def analyze_feedback_correlations(
    df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Analyze correlations between PR metrics and feedback types."""
    print("Analyzing Feedback Correlations (RQ1-4)...")
    
    metrics = {
        "changed_files": "Changed Files",
        "total_changes": "Total Changes (lines)",
        "additions": "Lines Added",
        "deletions": "Lines Deleted",
        "analysis_hours": "Analysis Time (hours)",
        "body_chars": "Description Length (chars)",
        "total_comments": "Total Comments",
        "participant_count": "Participant Count",
    }
    
    # Create feedback categories
    df["has_approved"] = df["approved_count"].astype(int) > 0
    df["has_changes_requested"] = df["changes_requested_count"].astype(int) > 0
    df["has_commented"] = df["commented_count"].astype(int) > 0
    df["has_human_review"] = (df["human_review_count"].astype(int) > 0) | df["has_approved"] | df["has_changes_requested"] | df["has_commented"]
    
    feedback_types = {
        "has_approved": "Approved",
        "has_changes_requested": "Changes Requested",
        "has_commented": "Commented",
        "has_human_review": "Has Any Review",
    }
    
    rows = []
    for metric_col, metric_label in metrics.items():
        if metric_col not in df.columns:
            continue
        
        for feedback_col, feedback_label in feedback_types.items():
            x = df[metric_col]
            y = df[feedback_col].astype(float)
            
            spearman_corr, spearman_p, n = calculate_spearman_p_value(x, y)
            pearson_corr, pearson_p, _ = calculate_pearson_p_value(x, y)
            
            rows.append({
                "metric": metric_label,
                "feedback_type": feedback_label,
                "n_samples": n,
                "spearman_rho": f"{spearman_corr:.4f}" if not np.isnan(spearman_corr) else "N/A",
                "spearman_p": f"{spearman_p:.4f}" if not np.isnan(spearman_p) else "N/A",
                "pearson_r": f"{pearson_corr:.4f}" if not np.isnan(pearson_corr) else "N/A",
                "pearson_p": f"{pearson_p:.4f}" if not np.isnan(pearson_p) else "N/A",
            })
    
    output_csv = output_dir / "rq1_4_feedback_correlations.csv"
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "metric", "feedback_type", "n_samples",
            "spearman_rho", "spearman_p", "pearson_r", "pearson_p"
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"  Saved: {output_csv}")


def analyze_review_count_correlations(
    df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Analyze correlations between PR metrics and review counts."""
    print("Analyzing Review Count Correlations (RQ5-8)...")
    
    metrics = {
        "changed_files": "Changed Files",
        "total_changes": "Total Changes (lines)",
        "additions": "Lines Added",
        "deletions": "Lines Deleted",
        "analysis_hours": "Analysis Time (hours)",
        "body_chars": "Description Length (chars)",
        "total_comments": "Total Comments (Issue)",
        "participant_count": "Participant Count",
    }
    
    review_types = {
        "human_review_count": "Human Reviews",
        "approved_count": "Approved",
        "changes_requested_count": "Changes Requested",
        "commented_count": "Commented",
    }
    
    rows = []
    for metric_col, metric_label in metrics.items():
        if metric_col not in df.columns:
            continue
        
        for review_col, review_label in review_types.items():
            if review_col not in df.columns:
                continue
            
            x = df[metric_col]
            y = df[review_col]
            
            spearman_corr, spearman_p, n = calculate_spearman_p_value(x, y)
            pearson_corr, pearson_p, _ = calculate_pearson_p_value(x, y)
            
            rows.append({
                "metric": metric_label,
                "review_type": review_label,
                "n_samples": n,
                "spearman_rho": f"{spearman_corr:.4f}" if not np.isnan(spearman_corr) else "N/A",
                "spearman_p": f"{spearman_p:.4f}" if not np.isnan(spearman_p) else "N/A",
                "pearson_r": f"{pearson_corr:.4f}" if not np.isnan(pearson_corr) else "N/A",
                "pearson_p": f"{pearson_p:.4f}" if not np.isnan(pearson_p) else "N/A",
            })
    
    output_csv = output_dir / "rq5_8_review_count_correlations.csv"
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "metric", "review_type", "n_samples",
            "spearman_rho", "spearman_p", "pearson_r", "pearson_p"
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"  Saved: {output_csv}")


def generate_descriptive_statistics(
    df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Generate descriptive statistics for all metrics."""
    print("Generating descriptive statistics...")
    
    metrics = {
        "changed_files": "Changed Files",
        "total_changes": "Total Changes (lines)",
        "additions": "Lines Added",
        "deletions": "Lines Deleted",
        "analysis_hours": "Analysis Time (hours)",
        "body_chars": "Description Length (chars)",
        "total_comments": "Total Comments",
        "participant_count": "Participant Count",
        "human_review_count": "Human Reviews",
        "approved_count": "Approved Reviews",
        "changes_requested_count": "Changes Requested",
        "commented_count": "Commented Reviews",
    }
    
    rows = []
    for col, label in metrics.items():
        if col not in df.columns:
            continue
        
        data = df[col].dropna()
        if len(data) == 0:
            continue
        
        rows.append({
            "metric": label,
            "count": len(data),
            "mean": f"{data.mean():.2f}",
            "std": f"{data.std():.2f}",
            "min": f"{data.min():.2f}",
            "q25": f"{data.quantile(0.25):.2f}",
            "median": f"{data.median():.2f}",
            "q75": f"{data.quantile(0.75):.2f}",
            "max": f"{data.max():.2f}",
        })
    
    output_csv = output_dir / "descriptive_statistics.csv"
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "metric", "count", "mean", "std", "min", "q25", "median", "q75", "max"
        ])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"  Saved: {output_csv}")


def generate_feedback_distribution(
    df: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Generate feedback type distribution analysis."""
    print("Generating feedback distribution analysis...")
    
    # Analyze feedback types
    feedback_dist = df["final_feedback_normalized"].value_counts()
    
    # Analyze review states
    df["has_approved"] = df["approved_count"].astype(int) > 0
    df["has_changes_requested"] = df["changes_requested_count"].astype(int) > 0
    df["has_commented"] = df["commented_count"].astype(int) > 0
    df["has_any_review"] = (df["human_review_count"].astype(int) > 0) | df["has_approved"] | df["has_changes_requested"] | df["has_commented"]
    
    rows = []
    
    # Feedback distribution
    total = len(df)
    rows.append(["Feedback Distribution", "", "", ""])
    rows.append(["Type", "Count", "Percentage", ""])
    for feedback, count in feedback_dist.items():
        pct = 100 * count / total
        rows.append([feedback, count, f"{pct:.1f}%", ""])
    
    rows.append(["", "", "", ""])
    rows.append(["Review Type Distribution", "", "", ""])
    rows.append(["Type", "Count", "Percentage", ""])
    
    review_types = {
        "has_any_review": "Has Human Review",
        "has_approved": "Has Approved Review",
        "has_changes_requested": "Has Changes Requested",
        "has_commented": "Has Commented Review",
    }
    
    for col, label in review_types.items():
        count = df[col].sum()
        pct = 100 * count / total
        rows.append([label, int(count), f"{pct:.1f}%", ""])
    
    output_csv = output_dir / "feedback_distribution.csv"
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)
    
    print(f"  Saved: {output_csv}")


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
    print(f"Loaded {len(df)} PR records\n")
    
    analyze_feedback_correlations(df, output_dir)
    analyze_review_count_correlations(df, output_dir)
    generate_descriptive_statistics(df, output_dir)
    generate_feedback_distribution(df, output_dir)
    
    print(f"\nAnalysis complete! Output saved to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
