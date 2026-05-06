#!/usr/bin/env python3
"""Generate publication-quality plots with improved formatting.

Addresses feedback from Lab 2:
- Larger, more readable fonts
- Better figure titles with section numbering
- Improved color schemes
- Larger font sizes for legends and labels
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


plt.rcParams['figure.dpi'] = 100
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 16


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate publication-quality plots")
    parser.add_argument("--aggregated-csv", required=True, help="Aggregated PR data CSV")
    parser.add_argument("--output-dir", required=True, help="Output directory for PNG files")
    return parser.parse_args()


def load_data(csv_path: Path) -> pd.DataFrame:
    """Load and preprocess PR data."""
    df = pd.read_csv(csv_path)
    numeric_cols = [
        "changed_files", "total_changes", "additions", "deletions",
        "analysis_hours", "body_chars", "total_comments", "participant_count",
        "human_review_count", "approved_count", "changes_requested_count", "commented_count"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.replace([np.inf, -np.inf], np.nan)
    return df


def calculate_correlation(x: pd.Series, y: pd.Series) -> tuple:
    """Calculate correlations and p-values."""
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        return np.nan, np.nan, np.nan, np.nan, 0
    
    try:
        pearson_r, pearson_p = stats.pearsonr(x_clean, y_clean)
    except:
        pearson_r, pearson_p = np.nan, np.nan
    
    try:
        spearman_rho, spearman_p = stats.spearmanr(x_clean, y_clean)
    except:
        spearman_rho, spearman_p = np.nan, np.nan
    
    return pearson_r, pearson_p, spearman_rho, spearman_p, len(x_clean)


def create_publication_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
) -> None:
    """Create a publication-quality scatter plot."""
    # Remove NaN
    mask = df[x_col].notna() & df[y_col].notna()
    x = df[mask][x_col]
    y = df[mask][y_col]
    
    if len(x) < 2:
        return
    
    # Create figure with better spacing
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Scatter plot
    ax.scatter(x, y, alpha=0.5, s=30, color="#2E86AB", edgecolors="navy", linewidth=0.5)
    
    # Add trend line
    try:
        slope, intercept = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, "r--", linewidth=2.5, label="Trend line", alpha=0.8)
    except:
        pass
    
    # Calculate correlations
    pearson_r, pearson_p, spearman_rho, spearman_p, n = calculate_correlation(df[x_col], df[y_col])
    
    # Add correlation text box
    if not np.isnan(pearson_r) and not np.isnan(spearman_rho):
        correlation_text = (
            f"Pearson r = {pearson_r:.4f} (p={'<0.001' if pearson_p < 0.001 else f'{pearson_p:.4f}'})\n"
            f"Spearman ρ = {spearman_rho:.4f} (p={'<0.001' if spearman_p < 0.001 else f'{spearman_p:.4f}'})\n"
            f"n = {n}"
        )
        ax.text(
            0.05, 0.95, correlation_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7, pad=0.8),
            family="monospace"
        )
    
    # Labels and title
    ax.set_xlabel(x_label, fontsize=13, fontweight="bold")
    ax.set_ylabel(y_label, fontsize=13, fontweight="bold")
    ax.set_title(title, fontsize=15, fontweight="bold", pad=20)
    
    ax.grid(True, alpha=0.3, linestyle="--")
    if "Trend line" in str(ax.get_lines()):
        ax.legend(fontsize=12, loc="lower right")
    
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✓ Saved: {output_path.name}")


def generate_distribution_plots(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate distribution plots for key metrics."""
    print("\n## Section 1: Data Overview - Metric Distributions")
    
    metrics = [
        ("changed_files", "Number of Changed Files", "Frequency", "PR Size Distribution: Changed Files"),
        ("total_changes", "Total Changes (lines)", "Frequency", "PR Size Distribution: Total Changes"),
        ("analysis_hours", "Analysis Time (hours, log scale)", "Frequency", "Temporal Metric: Analysis Time"),
        ("body_chars", "Description Length (characters)", "Frequency", "Description Metric: Length"),
    ]
    
    for col, x_label, y_label, title in metrics:
        if col not in df.columns:
            continue
        
        data = df[col].dropna()
        if len(data) == 0:
            continue
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Use log scale for skewed data
        if col in ["total_changes", "analysis_hours"]:
            data_plot = data[data > 0]
            ax.hist(np.log10(data_plot + 1), bins=50, color="#2E86AB", edgecolor="navy", alpha=0.7)
            ax.set_xlabel(f"{x_label} (log10 scale)", fontsize=13, fontweight="bold")
        else:
            ax.hist(data, bins=50, color="#2E86AB", edgecolor="navy", alpha=0.7)
            ax.set_xlabel(x_label, fontsize=13, fontweight="bold")
        
        ax.set_ylabel(y_label, fontsize=13, fontweight="bold")
        ax.set_title(f"Section 1: {title}", fontsize=15, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, axis="y")
        
        # Add statistics box
        stats_text = (
            f"Mean: {data.mean():.2f}\n"
            f"Median: {data.median():.2f}\n"
            f"Std: {data.std():.2f}\n"
            f"n: {len(data)}"
        )
        ax.text(
            0.98, 0.97, stats_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8, pad=0.8),
            family="monospace"
        )
        
        fig.tight_layout()
        output_path = output_dir / f"01_distribution_{col}.png"
        fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"✓ Saved: {output_path.name}")


def generate_feedback_distribution(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate feedback type distribution plot."""
    print("\n## Section 2: Research Question Context - Feedback Distribution")
    
    # Normalize feedback
    df["feedback_norm"] = df["final_feedback_normalized"].fillna("no_review")
    feedback_counts = df["feedback_norm"].value_counts()
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#6A994E"]
    wedges, texts, autotexts = ax.pie(
        feedback_counts.values,
        labels=feedback_counts.index,
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
        textprops={"fontsize": 12, "weight": "bold"}
    )
    
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(12)
        autotext.set_weight("bold")
    
    ax.set_title(
        "Section 2: Final Feedback Distribution Across All PRs\n(RQ1-4 Context)",
        fontsize=15,
        fontweight="bold",
        pad=20
    )
    
    fig.tight_layout()
    output_path = output_dir / "02_feedback_distribution.png"
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✓ Saved: {output_path.name}")


def generate_rq_plots(df: pd.DataFrame, output_dir: Path) -> None:
    """Generate RQ scatter plots."""
    print("\n## Section 3-6: Research Questions - Correlation Analysis")
    
    metrics = [
        ("changed_files", "Number of Changed Files"),
        ("total_changes", "Total Line Changes"),
        ("analysis_hours", "Analysis Time (hours)"),
        ("body_chars", "Description Length (chars)"),
    ]
    
    review_types = [
        ("approved_count", "Number of Approved Reviews"),
        ("changes_requested_count", "Number of Changes Requested"),
        ("commented_count", "Number of Commented Reviews"),
        ("human_review_count", "Number of Human Reviews"),
    ]
    
    # RQ1-4: Feedback vs Metrics
    rq_num = 3
    for metric_col, metric_label in metrics[:1]:  # Just changed_files as example
        create_publication_plot(
            df,
            metric_col, "has_approved",
            metric_label, "Has Approved Review (0/1)",
            f"Section {rq_num}: RQ1 - PR Size vs Approved Feedback",
            output_dir / f"03_rq1_size_vs_feedback.png"
        )
        rq_num += 1
    
    # RQ5-8: Review Count vs Metrics  
    rq_num = 5
    for review_col, review_label in review_types[:2]:
        create_publication_plot(
            df,
            "changed_files", review_col,
            "Number of Changed Files", review_label,
            f"Section {rq_num}: RQ{rq_num-4+4} - PR Size vs Review Count",
            output_dir / f"0{rq_num}_rq{rq_num-4+4}_size_vs_reviews.png"
        )
        rq_num += 1


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
    
    print("Generating publication-quality plots...\n")
    print("=" * 60)
    
    generate_distribution_plots(df, output_dir)
    generate_feedback_distribution(df, output_dir)
    generate_rq_plots(df, output_dir)
    
    print("\n" + "=" * 60)
    print(f"\nAll plots generated and saved to: {output_dir}")
    print("Files follow Lab report structure with section numbering.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
