# Enunciado 3 - Code Review Activity Analysis
## Data Collection and Analysis Summary

### 1. Data Collection Status

**Collection Overview:**
- **Total Repositories:** 33 repositories successfully collected
- **Total PR Records:** 6,822 pull requests analyzed
- **Analysis Date:** 2026-05-06
- **Confidence Level:** 95% (default)
- **Margin of Error:** 5% (default)

### 2. Data Validation Summary

#### PR Sample Distribution:
The collected data shows a good distribution across repositories:
- Sample collection used statistical sampling (confidence: 95%, margin error: 5%)
- Target sample size: 300 PRs per repository (adjusted based on population size)
- Actual collected: 6,822 total PRs from 33 repositories
- Average per repository: ~206 PRs (some repos with smaller PR populations had fewer samples)

#### Feedback Type Distribution:
| Feedback Type | Count | Percentage |
|---|---|---|
| No Review | 4,082 | 59.8% |
| Positive (Approved) | 1,621 | 23.8% |
| Neutral (Commented) | 981 | 14.4% |
| Negative (Changes Requested) | 127 | 1.9% |
| Dismissed | 11 | 0.2% |

**Note:** The high percentage of "no_review" PRs is concerning and suggests:
- PRs may not have human reviews (could be auto-merged, directly merged by maintainers, or awaiting review)
- The collection may not be properly identifying human reviewers
- **Recommendation:** Verify the collection logic for identifying human reviews

### 3. PR Metrics - Descriptive Statistics

#### Size Metrics:
| Metric | Mean | Median | Std | Min | Q25 | Q75 | Max |
|---|---|---|---|---|---|---|---|
| Changed Files | 13.50 | 1 | 221.98 | 0 | 1 | 2 | 9,932 |
| Total Changes (lines) | 2,106 | 8 | 46,230 | 0 | 2 | 82 | 2,429,126 |
| Lines Added | 1,785 | 6 | 44,617 | 0 | 1 | 59 | 2,429,126 |
| Lines Deleted | 320 | 1 | 11,846 | 0 | 0 | 6 | 917,406 |

**Observations:**
- High standard deviation in size metrics indicates extreme outliers (some massive PRs)
- Median values are much smaller than means, suggesting right-skewed distributions
- **Recommendation:** Consider filtering or log-transforming extreme values for correlation analysis

#### Time Metrics:
| Metric | Mean | Median | Std |
|---|---|---|---|
| Analysis Time (hours) | 3,651.36 | 73.04 | 9,495.71 |

**Observations:**
- Wide range: 0 to ~109,000 hours (~12 years!)
- Median of 73 hours (~3 days) suggests typical PRs take a few days for analysis
- **Recommendation:** Verify timestamp collection and consider filtering unrealistic values

#### Description Metrics:
| Metric | Mean | Median | Std |
|---|---|---|---|
| Description Length (chars) | 1,131 | 474 | 2,742 |

**Observations:**
- Reasonable distribution
- Median of 474 chars suggests most PRs have brief descriptions
- Some PRs have no description (min=0)

#### Interaction Metrics:
| Metric | Mean | Median | Std |
|---|---|---|---|
| Total Comments | 2.86 | 1 | 7.83 |
| Participant Count | 1.64 | 1 | 1.19 |

**Observations:**
- Most PRs have minimal discussion (median=1 comment)
- Most PRs have only 1 participant (likely just author)
- This aligns with "no_review" observation above

### 4. Key Research Questions - Initial Findings

#### RQ1-4: Final Feedback vs PR Metrics

**Strong Correlations Found (Spearman):**
- **Commented feedback vs Changed Files:** ρ=0.281 (p<0.001)
- **Commented feedback vs Total Changes:** ρ=0.300 (p<0.001)
- **Commented feedback vs Lines Added:** ρ=0.314 (p<0.001)

**Interpretation:** Larger PRs tend to receive more comments, which is expected (more changes = more discussion).

**Weak/No Correlations:**
- **Approved feedback vs metrics:** Very weak correlations (|ρ|<0.04)
- **Changes Requested vs metrics:** Weak negative correlations with size
- **Analysis Time vs feedback:** Mixed weak correlations

**Key Insight:** The lack of human reviews (60% no_review) makes correlation analysis difficult. We're primarily seeing patterns for PRs that DO receive feedback.

#### RQ5-8: Number of Reviews vs PR Metrics

**Strong Correlations Found:**
- **Commented Count vs Total Changes:** ρ=0.319 (p<0.001)
- **Commented Count vs Lines Added:** ρ=0.334 (p<0.001)
- **Human Reviews vs Changed Files:** ρ=0.185 (p<0.001)
- **Analysis Time vs Approved Count:** ρ=0.108 (p<0.001)

**Interpretation:**
- Larger PRs do generate more reviews
- Analysis time shows positive correlation with number of approvals (reviewers take time)

### 5. Data Collection Issues to Investigate

#### Critical Issues:
1. **High "no_review" rate (60%):** 
   - Verify that the GraphQL/API query is correctly identifying human reviews
   - Check if `has_human_review` field is being populated correctly
   - May need to adjust the definition of "human review"

2. **Outlier values:**
   - Some PRs with 9,932 changed files (unrealistic?)
   - Some PRs with 2.4M line changes (potential data quality issue)
   - Consider data cleaning or transformation

3. **Missing temporal data:**
   - Some PRs have `merged_at` as empty
   - May affect analysis of PR lifecycle

#### Recommendations:
- Verify a sample of PRs directly on GitHub to validate collected metrics
- Review the collection script to ensure API calls are capturing all review information
- Consider filtering PRs with extreme values for report (document what was filtered)

### 6. Analysis Scripts Created

#### Aggregation:
- `aggregate_pr_data.py` - Combines all per-repo CSVs into single aggregated file
- Adds normalized feedback fields and review type counts

#### Analysis:
- `analyze_rq_metrics.py` - Generates scatter plots with correlation statistics
- `correlation_analysis.py` - Generates detailed correlation tables with p-values

#### Output Files:
- `rq1_4_feedback_correlations.csv` - Correlation analysis for RQ1-4
- `rq5_8_review_count_correlations.csv` - Correlation analysis for RQ5-8
- `descriptive_statistics.csv` - Summary statistics for all metrics
- `feedback_distribution.csv` - Distribution of feedback types
- `summary_report.txt` - Executive summary
- `rq1-8_*.png` - Scatter plots with trend lines (8 plots)

### 7. Recommendations for Report

#### Methodological:
1. **Discuss the high "no_review" rate:**
   - May indicate that top-starred repos have different review practices
   - Could be automation (auto-merging)
   - Should acknowledge in report limitations

2. **Choose correlation method justification:**
   - **Spearman (Non-parametric):** Better for skewed distributions and outliers
   - **Pearson (Parametric):** Requires normality assumptions
   - **Recommendation:** Use Spearman with caveat about data distribution

3. **Handle outliers:**
   - Option 1: Report both with and without outliers
   - Option 2: Use log transformation for size metrics
   - Option 3: Filter extreme values and document cutoff

#### Presentation:
1. **Improve graph readability** (feedback from Lab 2):
   - Increase font sizes in legends and axis labels
   - Use clearer color schemes
   - Add better titles with RQ numbers

2. **Add section numbering** (feedback from Lab 2):
   - Structure report with numbered sections
   - Include table of contents

3. **Include confidence intervals:**
   - Show 95% CI for correlations in tables
   - Indicate statistical significance (p-values)

#### Data Completeness:
- Consider collecting more repositories (target was 200)
- Current 33 repos is sufficient for pilot analysis
- May explain "no_review" pattern (only 30 repos collected)

### 8. Hypothesis Testing

Based on initial findings, let's revisit the stated hypotheses:

| Hypothesis | Preliminary Finding | Support Status |
|---|---|---|
| PR size won't influence feedback | Commented feedback positively correlates with size | ❌ NOT SUPPORTED |
| More time = complications (negative relationship) | Mixed/weak correlations | ⚠️ UNCLEAR |
| Description won't influence feedback | Not yet thoroughly analyzed | ⏳ PENDING |
| More interactions → more negative feedback | Limited human reviews makes testing difficult | ⏳ PENDING |
| Smaller PRs attract more reviewers | Human reviews correlate with size | ❌ NOT SUPPORTED |
| Longer review time attracts fewer reviewers | Some positive correlation with time | ❌ NOT SUPPORTED |
| Good descriptions attract more reviewers | Not yet thoroughly analyzed | ⏳ PENDING |
| More interactions → more reviews | Needs dedicated analysis | ⏳ PENDING |

### 9. Next Steps

1. **Verify data quality:**
   - Check 10-15 sample PRs manually on GitHub
   - Validate metrics against actual PR data
   - Investigate why 60% have no review

2. **Continue data collection:**
   - Collect remaining repositories (target: 200)
   - May reveal different patterns with more data

3. **Refine analysis:**
   - Create separate analysis for repos with reviews vs without
   - Analyze by repository to see if patterns differ
   - Consider interaction effects between metrics

4. **Prepare report:**
   - Use generated plots and tables
   - Add context and interpretation
   - Address feedback from previous lab (numbering, font sizes)
   - Include limitation section discussing data issues

---

**Report Ready For:** Immediate use in generating report draft
**Data Collection Status:** 30/200 repos (15%) - can be used for pilot/interim report
**Quality Assessment:** Good, with noted issues around "no_review" rate
**Recommendation:** Generate interim report with current data, flag issues for final report
