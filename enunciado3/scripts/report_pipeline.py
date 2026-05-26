#!/usr/bin/env python3
"""Master pipeline for generating the Lab 3 report artifacts.

On run, prompts the user to choose:
  1 - Show collected counts vs target from the lab PDF
  2 - Run full analysis pipeline (aggregation, correlation, plotting)

The script locates data in `../output/` relative to this scripts directory
and runs the existing scripts created earlier.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
OUTPUT_DIR = ROOT / "output"
ANALYSIS_DIR = OUTPUT_DIR / "analysis"

TARGET_REPOS = 200  # from the lab PDF


def count_repos_and_prs(output_dir: Path) -> tuple[int,int]:
    """Count how many repo folders contain `prs.csv` and total PR rows."""
    repo_count = 0
    pr_total = 0
    if not output_dir.exists():
        return 0, 0

    for sub in sorted(output_dir.iterdir()):
        if not sub.is_dir():
            continue
        prs_file = sub / "prs.csv"
        if prs_file.exists():
            repo_count += 1
            # Count lines minus header
            with prs_file.open("r", encoding="utf-8") as f:
                # read first line as header and then count rest
                try:
                    reader = csv.reader(f)
                    header = next(reader)
                except StopIteration:
                    continue
                for _ in reader:
                    pr_total += 1
    return repo_count, pr_total


def run_command(cmd: list[str]) -> int:
    """Run command and stream output to terminal. Return exit code."""
    try:
        process = subprocess.run(cmd, check=False)
        return process.returncode
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 1


def option_counts() -> int:
    repos, prs = count_repos_and_prs(OUTPUT_DIR)
    print(f"Collected repositories: {repos}")
    print(f"Collected PR rows: {prs}")
    print(f"Target repositories (from lab PDF): {TARGET_REPOS}")
    percent = (repos / TARGET_REPOS * 100) if TARGET_REPOS else 0
    print(f"Progress: {percent:.1f}% of target repos")
    return 0


def option_run_pipeline() -> int:
    """Run the whole pipeline: aggregate -> correlation -> analysis -> publication plots."""
    # 1) Aggregate
    print("Running aggregation...")
    ret = run_command([sys.executable, str(SCRIPTS_DIR / "aggregate_pr_data.py"), "--input-dir", str(OUTPUT_DIR), "--output-csv", str(OUTPUT_DIR / "aggregated_prs.csv")])
    if ret != 0:
        print("Aggregation failed")
        return ret

    # 2) Correlation analysis
    print("Running correlation analysis...")
    ret = run_command([sys.executable, str(SCRIPTS_DIR / "correlation_analysis.py"), "--aggregated-csv", str(OUTPUT_DIR / "aggregated_prs.csv"), "--output-dir", str(ANALYSIS_DIR)])
    if ret != 0:
        print("Correlation analysis failed")
        return ret

    # 3) RQ plotting and summary
    print("Running RQ plotting and summary...")
    ret = run_command([sys.executable, str(SCRIPTS_DIR / "analyze_rq_metrics.py"), "--aggregated-csv", str(OUTPUT_DIR / "aggregated_prs.csv"), "--output-dir", str(ANALYSIS_DIR)])
    if ret != 0:
        print("RQ plotting failed")
        return ret

    # 4) Publication plots (optional)
    print("Generating publication-quality plots...")
    pub_dir = ANALYSIS_DIR / "publication_plots"
    pub_dir.mkdir(parents=True, exist_ok=True)
    ret = run_command([sys.executable, str(SCRIPTS_DIR / "generate_publication_plots.py"), "--aggregated-csv", str(OUTPUT_DIR / "aggregated_prs.csv"), "--output-dir", str(pub_dir)])
    if ret != 0:
        print("Publication plot generation failed")
        return ret

    print("Pipeline finished successfully. Outputs are in:")
    print(f"  {ANALYSIS_DIR}")
    print(f"  {pub_dir}")
    return 0


def main() -> int:
    print("Choose an option:\n  1 - Show collected counts vs target\n  2 - Run full pipeline (may take several minutes)")
    try:
        choice = input("Enter 1 or 2: ").strip()
    except EOFError:
        print("No input provided. Exiting.")
        return 1

    if choice == "1":
        return option_counts()
    if choice == "2":
        return option_run_pipeline()

    print("Invalid choice")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
