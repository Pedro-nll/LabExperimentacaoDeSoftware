#!/usr/bin/env python3
"""Aggregate PR data from all collected repositories into a single CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate PR data from multiple CSV files")
    parser.add_argument("--input-dir", required=True, help="Directory containing per-repo prs.csv files")
    parser.add_argument("--output-csv", required=True, help="Output CSV with aggregated PR data")
    return parser.parse_args()


def collect_pr_files(input_dir: Path) -> List[Path]:
    """Find all prs.csv files in subdirectories."""
    return sorted(input_dir.glob("*/prs.csv"))


def normalize_feedback(feedback: str) -> str:
    """Normalize feedback value (remove empty, handle pipes)."""
    if not feedback or feedback.strip() == "":
        return "no_review"
    feedback = feedback.strip()
    if feedback.upper() == "NO_REVIEW":
        return "no_review"
    return feedback.lower()


def parse_review_states(review_states: str) -> List[str]:
    """Parse pipe-separated review states."""
    if not review_states or review_states.strip() == "":
        return []
    return [s.strip() for s in review_states.split("|") if s.strip()]


def count_positive_reviews(review_states: str) -> int:
    """Count APPROVED reviews in the review_states field."""
    states = parse_review_states(review_states)
    return sum(1 for s in states if s.upper() == "APPROVED")


def count_negative_reviews(review_states: str) -> int:
    """Count CHANGES_REQUESTED reviews in the review_states field."""
    states = parse_review_states(review_states)
    return sum(1 for s in states if s.upper() == "CHANGES_REQUESTED")


def count_comment_reviews(review_states: str) -> int:
    """Count COMMENTED reviews in the review_states field."""
    states = parse_review_states(review_states)
    return sum(1 for s in states if s.upper() == "COMMENTED")


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_csv = Path(args.output_csv).resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    pr_files = collect_pr_files(input_dir)
    print(f"Found {len(pr_files)} PR CSV files")

    aggregated_rows: List[Dict[str, Any]] = []
    total_rows = 0

    for csv_file in pr_files:
        with csv_file.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue

            for row in reader:
                total_rows += 1
                # Enhance the row with normalized and derived fields
                enhanced_row = dict(row)
                
                # Normalize feedback
                enhanced_row["final_feedback_normalized"] = normalize_feedback(
                    row.get("final_feedback", "")
                )
                
                # Count review types
                review_states_str = row.get("review_states", "")
                enhanced_row["approved_count"] = str(count_positive_reviews(review_states_str))
                enhanced_row["changes_requested_count"] = str(count_negative_reviews(review_states_str))
                enhanced_row["commented_count"] = str(count_comment_reviews(review_states_str))
                
                aggregated_rows.append(enhanced_row)

    print(f"Aggregated {total_rows} PR records")

    if aggregated_rows:
        # Get all fieldnames from first row and add our new columns
        fieldnames = list(aggregated_rows[0].keys())
        # Ensure new columns are at the end
        if "final_feedback_normalized" not in fieldnames:
            fieldnames.append("final_feedback_normalized")
        if "approved_count" not in fieldnames:
            fieldnames.append("approved_count")
        if "changes_requested_count" not in fieldnames:
            fieldnames.append("changes_requested_count")
        if "commented_count" not in fieldnames:
            fieldnames.append("commented_count")

        output_csv.parent.mkdir(parents=True, exist_ok=True)
        with output_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in aggregated_rows:
                writer.writerow(row)

        print(f"Wrote {len(aggregated_rows)} rows to {output_csv}")
        return 0

    print("No PR records found to aggregate")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
