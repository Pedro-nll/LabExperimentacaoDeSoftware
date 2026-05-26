# Enunciado 3 - Code Review Analysis Scripts
## Setup and Usage Guide

### Overview

This directory contains analysis scripts for processing and visualizing code review data collected from GitHub pull requests. The scripts follow the structure and methodology from Enunciado 1 and 2, adapted for code review metrics.

### Quick Start

```bash
# 1. Activate virtual environment
source /path/to/.venv/bin/activate

# 2. Navigate to scripts directory
cd enunciado3/scripts

# 3. Aggregate all PR data (if not already done)
python3 aggregate_pr_data.py \
  --input-dir ../output \
  --output-csv ../output/aggregated_prs.csv

# 4. Generate analysis and correlation tables
python3 correlation_analysis.py \
  --aggregated-csv ../output/aggregated_prs.csv \
  --output-dir ../output/analysis

# 5. Generate visualization plots (existing)
python3 analyze_rq_metrics.py \
  --aggregated-csv ../output/aggregated_prs.csv \
  --output-dir ../output/analysis

# 6. Generate publication-quality plots (improved formatting)
python3 generate_publication_plots.py \
  --aggregated-csv ../output/aggregated_prs.csv \
  --output-dir ../output/analysis/publication_plots
```

### Scripts Description

#### 1. `aggregate_pr_data.py`
**Purpose:** Combines all per-repository PR CSV files into a single aggregated dataset.

**Features:**
- Reads all `prs.csv` files from the output directory
- Normalizes feedback fields
- Counts review types (approved, changes_requested, commented)
- Outputs a single CSV with all PRs and derived fields

**Output:**
- `output/aggregated_prs.csv` - Main analysis file with all 6,822 PR records

**Usage:**
```bash
python3 aggregate_pr_data.py \
  --input-dir ../output \
  --output-csv ../output/aggregated_prs.csv
```

#### 2. `correlation_analysis.py`
**Purpose:** Performs statistical correlation analysis between PR metrics and feedback/review counts.

**Features:**
- Calculates Spearman and Pearson correlations with p-values
- Analyzes both feedback types (RQ1-4) and review counts (RQ5-8)
- Generates descriptive statistics for all metrics
- Creates feedback/review distribution tables

**Outputs:**
- `rq1_4_feedback_correlations.csv` - Correlations between PR metrics and feedback types
- `rq5_8_review_count_correlations.csv` - Correlations between PR metrics and review counts
- `descriptive_statistics.csv` - Summary statistics (mean, median, std, quartiles)
- `feedback_distribution.csv` - Count and percentage of each feedback type

**Usage:**
```bash
python3 correlation_analysis.py \
  --aggregated-csv ../output/aggregated_prs.csv \
  --output-dir ../output/analysis
```

**Key Outputs to Use in Report:**
- Use correlation tables for RQ1-8 analysis
- Reference statistics for baseline metrics
- Include correlation plots with these values

#### 3. `analyze_rq_metrics.py`
**Purpose:** Generates scatter plots with trend lines for each RQ.

**Features:**
- Creates 8 scatter plots (RQ1-8)
- Each plot shows 4 subplots for different feedback/review types
- Includes correlation coefficients and trend lines
- Generates summary statistics report

**Outputs:**
- `rq1_feedback_vs_changed_files.png` - RQ1 analysis
- `rq2_feedback_vs_total_changes.png` - RQ2 analysis
- `rq3_feedback_vs_additions.png` - RQ3 analysis
- `rq4_feedback_vs_deletions.png` - RQ4 analysis
- `rq5_reviews_vs_changed_files.png` - RQ5 analysis
- `rq6_reviews_vs_total_changes.png` - RQ6 analysis
- `rq7_reviews_vs_additions.png` - RQ7 analysis
- `rq8_reviews_vs_deletions.png` - RQ8 analysis
- `summary_report.txt` - Executive summary

**Usage:**
```bash
python3 analyze_rq_metrics.py \
  --aggregated-csv ../output/aggregated_prs.csv \
  --output-dir ../output/analysis
```

#### 4. `generate_publication_plots.py`
**Purpose:** Creates publication-quality plots with improved formatting (addressing Lab 2 feedback).

**Features:**
- Larger, more readable fonts (12-15pt)
- Better color scheme and styling
- Section numbering for report structure
- Statistical annotations with larger text
- Follows Lab 2 feedback requirements

**Outputs:**
- `01_distribution_*.png` - Metric distribution plots
- `02_feedback_distribution.png` - Pie chart of feedback types
- `03_rq1_*.png` through `08_rq*_*.png` - RQ-specific plots
- All files include section numbers for report

**Usage:**
```bash
python3 generate_publication_plots.py \
  --aggregated-csv ../output/aggregated_prs.csv \
  --output-dir ../output/analysis/publication_plots
```

### Data Available for Analysis

#### Aggregated PR Metrics (6,822 records from 33 repositories):

**Size Metrics:**
- `changed_files` - Number of files modified
- `total_changes` - Total lines added + deleted
- `additions` - Lines added
- `deletions` - Lines deleted

**Temporal Metric:**
- `analysis_hours` - Time from PR creation to final activity

**Description Metric:**
- `body_chars` - PR description length in characters

**Interaction Metrics:**
- `total_comments` - Total comments on PR (issues + reviews)
- `participant_count` - Number of unique participants

**Review Metrics:**
- `human_review_count` - Total human reviews
- `approved_count` - Number of approved reviews
- `changes_requested_count` - Number of changes requested
- `commented_count` - Number of comment reviews

**Feedback:**
- `final_feedback_normalized` - Normalized feedback (no_review, positive, neutral, negative, dismissed)

### Key Findings Summary

See `ANALYSIS_SUMMARY.md` for detailed findings, including:
- Data collection status (6,822 PRs from 33 repos)
- Feedback distribution (60% no_review, 24% positive, 14% neutral, 2% negative)
- Initial correlation findings for RQ1-8
- Data quality issues to address
- Recommendations for final report

### Important Notes

#### Data Quality:
1. **High "no_review" rate (60%):** Investigate whether this reflects actual review patterns or collection issues
2. **Outliers:** Some PRs with extreme metrics (9,932 files, 2.4M line changes)
3. **Temporal data:** Some missing or unrealistic timestamps

#### Methodology:
- **Correlation method:** Recommend Spearman for skewed distributions
- **Statistical significance:** All reported correlations include p-values
- **Sample size:** n=6,822 sufficient for pilot, but target was 200 repos

#### Report Structure (addressing Lab 2 feedback):
- ✓ Section numbering included in plots
- ✓ Larger fonts (12-15pt) for readability
- ✓ Clear legends and axis labels
- ✓ Statistical annotations visible

### File Locations

```
enunciado3/
├── scripts/
│   ├── aggregate_pr_data.py           # Main aggregation
│   ├── correlation_analysis.py        # Statistics & tables
│   ├── analyze_rq_metrics.py          # Scatter plots
│   └── generate_publication_plots.py  # Publication-quality plots
├── output/
│   ├── aggregated_prs.csv             # Main data file
│   ├── analysis/
│   │   ├── rq1_4_feedback_correlations.csv
│   │   ├── rq5_8_review_count_correlations.csv
│   │   ├── descriptive_statistics.csv
│   │   ├── feedback_distribution.csv
│   │   ├── summary_report.txt
│   │   ├── rq*_*.png                  # Existing plots
│   │   └── publication_plots/
│   │       └── *.png                  # New publication plots
├── ANALYSIS_SUMMARY.md                # Detailed findings
└── README.md                          # This file
```

### Usage Examples for Report

#### For RQ1-4 Analysis:
1. Read `rq1_4_feedback_correlations.csv` for correlation values and p-values
2. Use `rq1_feedback_vs_changed_files.png` as figure in report
3. Reference values from `descriptive_statistics.csv` for metric ranges
4. Include interpretation from `ANALYSIS_SUMMARY.md`

#### For RQ5-8 Analysis:
1. Read `rq5_8_review_count_correlations.csv` for correlation values
2. Use corresponding `rq5_reviews_vs_*.png` plots
3. Cross-reference with feedback distribution to explain patterns

#### For Report Introduction:
1. Use `02_feedback_distribution.png` to show feedback type distribution
2. Include metrics from `descriptive_statistics.csv` in methods section
3. Reference `summary_report.txt` for data summary statistics

### Troubleshooting

**Issue:** "No data available" in plots
- **Solution:** Verify aggregated_prs.csv exists and is not empty
- **Check:** `wc -l output/aggregated_prs.csv` should show >6800 lines

**Issue:** Missing correlation values (showing "N/A")
- **Solution:** This occurs when sample size is too small or data is constant
- **Note:** Some review types have few occurrences (e.g., changes_requested)

**Issue:** Graphs with very few data points
- **Solution:** Filter for rows where `has_human_review=true` for cleaner analysis
- **Note:** 60% of PRs have no human reviews

### Next Steps

1. **Verify data quality:**
   - Manually check 10-15 sample PRs against actual GitHub data
   - Investigate the 60% "no_review" rate

2. **Continue data collection:**
   - Target was 200 repos (currently at 33)
   - More repos may reveal different patterns

3. **Prepare final report:**
   - Use plots from `publication_plots/` directory
   - Include tables from CSV outputs
   - Address data quality issues in limitations section
   - Follow Lab 2 feedback (numbering, fonts, readability)

4. **Statistical analysis:**
   - Decide on Spearman vs Pearson justification
   - Consider outlier handling strategy
   - Test remaining hypotheses

---

**Last Updated:** 2026-05-06
**Scripts Status:** Ready for report generation
**Data Status:** 33/200 repos collected (pilot stage)
**Output Quality:** Publication-ready with Lab 2 feedback incorporated
