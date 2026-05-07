# Methodology - Enunciado 3

## 1. Study Goal

This study analyzes how code review feedback relates to pull request (PR) characteristics in popular GitHub repositories. The goal is to understand whether larger, longer-running, more descriptive, or more interactive PRs tend to receive different final review outcomes and different numbers of review interactions.

The analysis is framed as an exploratory empirical study over a repository-level sample of open-source projects, with PRs as the unit of observation.

## 2. Research Questions

The report addresses eight research questions:

1. Feedback final vs. size of PRs
2. Feedback final vs. time of analysis
3. Feedback final vs. description
4. Feedback final vs. interactions
5. Number of reviews vs. size of PRs
6. Number of reviews vs. time of analysis
7. Number of reviews vs. description
8. Number of reviews vs. interactions

For the final report, feedback is treated as the final review outcome of each PR, and review activity is treated as the number of review events associated with that PR.

## 3. Dataset Scope and Unit of Analysis

The intended universe for the study is the 200 most popular GitHub repositories that satisfy the collection criteria defined for the project.

The unit of analysis is the pull request. Repository-level summaries are used only for contextual reporting and for validating the coverage of the collection process.

The analysis currently uses the collected subset available in the workspace output. At the time of report generation, the sample contains 6,768 PRs from 132 repositories. The pipeline is designed to be resumable, so partial collection does not invalidate the methodology or the generated outputs.

## 4. Data Collection Pipeline

The data collection and analysis workflow is organized into four main stages.

### 4.1 Repository discovery

Repository candidates are collected from GitHub and stored in the repository list used by the pipeline. The collection is deduplicated and checkpointed so the process can resume safely after interruptions.

### 4.2 PR extraction

For each repository, the pipeline collects PR metadata and review information through the GitHub API / GraphQL layer. The extraction captures the fields needed for the study, including:

- PR identity and URL
- state and timestamps
- size-related metrics
- description length
- review and comment counts
- participant counts
- final feedback classification

The extraction stage is rate-limit aware and uses retry logic with backoff for transient failures.

### 4.3 Aggregation

The collected per-repository CSV files are merged into a single aggregated dataset. This consolidated file is the input for the statistical analysis and plotting scripts.

### 4.4 Analysis and plotting

The aggregated dataset is used to compute descriptive statistics, correlation tables, and exploratory scatter plots. A separate script generates publication-quality plots with improved typography and layout.

## 5. Operational Decisions

Several design choices were made to make the pipeline stable and reproducible.

- The collection is checkpointed so completed repositories do not need to be reprocessed.
- Failed repositories remain eligible for retry in later executions.
- Temporary clone folders are deleted after each repository to control disk usage.
- Parallelism is used at the repository level to improve throughput while keeping the process stable.
- A progress script reports total, successful, failed, and pending repositories.

These choices make the workflow suitable for long-running study pipelines where interruptions, quota constraints, and transient network failures are expected.

## 6. Variables and Metrics

The study uses PR-level metrics derived from the raw GitHub data.

### 6.1 Size

Size is represented by the following fields:

- `changed_files`
- `additions`
- `deletions`
- `total_changes`

### 6.2 Time of analysis

Time of analysis is computed as the interval between PR creation and the last recorded activity or final update in the PR timeline.

### 6.3 Description

Description is measured as the number of characters in the PR body.

### 6.4 Interactions

Interactions are captured through review and comment-related counters such as:

- `total_comments`
- `issue_comments`
- `review_comments`
- `participant_count`
- `human_review_count`

### 6.5 Feedback outcome

Final feedback is normalized into categorical outcomes so that reviewed PRs can be compared consistently. The pipeline also derives helper indicators such as whether a PR received an approved review or another feedback type.

## 7. Data Cleaning and Preprocessing

Before statistical analysis, the dataset is normalized and cleaned.

- Numeric columns are converted to numeric types.
- Non-finite values such as `NaN` and `inf` are filtered or replaced where necessary.
- Derived binary indicators are created from count-based feedback columns when needed for plotting.
- Missing values are excluded pairwise for each statistical test so that each correlation uses the available valid observations for the selected variables.

This preprocessing keeps the schema stable and prevents invalid statistical operations on empty or constant data.

## 8. Statistical Approach

The analysis is exploratory and correlation-based.

### 8.1 Descriptive statistics

For the main PR metrics, the pipeline computes:

- mean
- median
- standard deviation
- minimum
- maximum

These values provide a baseline summary of the collected sample.

### 8.2 Correlation analysis

The study uses both Pearson and Spearman correlation coefficients.

- Pearson is used as a linear association measure.
- Spearman is used as a rank-based measure that is more robust for skewed distributions and outliers.

Both coefficients are reported with p-values where applicable.

### 8.3 Why both measures are reported

PR metrics are typically skewed, with a small number of very large or very long-running PRs. For that reason, Spearman is often the more informative summary, while Pearson remains useful for comparison with linear trends.

## 9. Plotting Strategy

The pipeline produces two families of plots.

### 9.1 Exploratory RQ scatter plots

These plots show pairwise relationships between PR metrics and feedback / review counts. They are intended to support quick inspection of trends and outliers.

### 9.2 Publication-quality plots

The publication plots use larger fonts, clearer section numbering, and improved spacing so they can be included directly in the report.

The plotting stage also generates a short textual summary report to help interpret the figures.

## 10. Current Output Artifacts

The methodology and analysis are supported by the following artifacts in the workspace:

- `enunciado3/output/aggregated_prs.csv`
- `enunciado3/output/analysis/descriptive_statistics.csv`
- `enunciado3/output/analysis/feedback_distribution.csv`
- `enunciado3/output/analysis/rq1_4_feedback_correlations.csv`
- `enunciado3/output/analysis/rq5_8_review_count_correlations.csv`
- `enunciado3/output/analysis/summary_report.txt`
- `enunciado3/output/analysis/*.png`
- `enunciado3/output/analysis/publication_plots/*.png`

These files are the primary evidence base for the results and discussion sections of the report.

## 11. Reproducibility Commands

From the repository root, the main commands are:

```bash
python enunciado3/scripts/aggregate_pr_data.py --input-dir enunciado3/output --output-csv enunciado3/output/aggregated_prs.csv
python enunciado3/scripts/correlation_analysis.py --input-csv enunciado3/output/aggregated_prs.csv --output-dir enunciado3/output/analysis
python enunciado3/scripts/analyze_rq_metrics.py --aggregated-csv enunciado3/output/aggregated_prs.csv --output-dir enunciado3/output/analysis
python enunciado3/scripts/generate_publication_plots.py --aggregated-csv enunciado3/output/aggregated_prs.csv --output-dir enunciado3/output/analysis/publication_plots
python enunciado3/scripts/report_pipeline.py
```

The report pipeline is the preferred entry point because it orchestrates aggregation, statistical analysis, and plot generation in a single run.

## 12. Interpretation Guidance

The results should be interpreted as exploratory evidence about patterns in the collected sample, not as causal claims.

- Correlation does not imply causation.
- Skewed metrics and outliers can influence the strength of linear relationships.
- The final report should distinguish clearly between the intended study design and the actual collected sample size.

This keeps the methodology transparent and makes the limitations of the study explicit.
