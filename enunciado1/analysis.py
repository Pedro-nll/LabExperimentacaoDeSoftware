"""
Analysis Script for GitHub Repository Metrics
Calculates RQ metrics and generates graphs for Google Docs report.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

def main():
    # Read the CSV data
    csv_file = "repos_data.csv"
    if not pd.io.common.file_exists(csv_file):
        csv_file = "repos_data_backup.csv"
        if not pd.io.common.file_exists(csv_file):
            print("No CSV file found. Please run main.py first to fetch data.")
            return

    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)

    # Filter out repositories as per the original logic
    non_programming_languages = ["Unknown", "Markdown"]
    keep_condition = (
        ~df["language"].isin(non_programming_languages) &
        ~((df["merged_prs"] == 0) & (df["total_issues"] == 0))
    )
    df_filtered = df[keep_condition]

    print(f"Analyzing {len(df_filtered)} filtered repositories...")

    # Calculate metrics
    metrics = {}

    # RQ1: Median age in years
    metrics['RQ1_median_age'] = df_filtered['age_years'].median()

    # RQ2: Median, avg, std for merged PRs
    metrics['RQ2_median_prs'] = df_filtered['merged_prs'].median()
    metrics['RQ2_avg_prs'] = df_filtered['merged_prs'].mean()
    metrics['RQ2_std_prs'] = df_filtered['merged_prs'].std()

    # RQ3: Median releases
    metrics['RQ3_median_releases'] = df_filtered['releases'].median()

    # RQ4: Median days since update
    metrics['RQ4_median_days'] = df_filtered['days_since_update'].median()

    # RQ5: Count per language
    language_counts = Counter(df_filtered['language'])
    metrics['RQ5_language_counts'] = dict(language_counts)

    # RQ6: Median closed issue ratio
    # Filter out None values for ratio calculation
    ratios = df_filtered['closed_issue_ratio'].dropna()
    metrics['RQ6_median_ratio'] = ratios.median()

    # RQ7: Language popularity vs median PRs and releases
    # Calculate medians per language for top languages
    top_languages = sorted(metrics['RQ5_language_counts'].items(), key=lambda x: x[1], reverse=True)[:20]  # Top 20 languages
    rq7_data = []

    for lang, count in top_languages:
        lang_repos = df[df['language'] == lang]
        if len(lang_repos) > 0:
            median_prs = lang_repos['merged_prs'].median()
            median_releases = lang_repos['releases'].median()
            rq7_data.append({
                'language': lang,
                'repo_count': count,
                'median_prs': median_prs,
                'median_releases': median_releases
            })

    metrics['RQ7_language_analysis'] = rq7_data

    # Save metrics to txt file
    with open('metrics_summary.txt', 'w') as f:
        f.write("GitHub Repository Metrics Summary\n")
        f.write("=" * 40 + "\n\n")

        f.write("RQ1 - Repository Age (years):\n")
        f.write(f"  Median: {metrics['RQ1_median_age']:.2f}\n\n")

        f.write("RQ2 - Merged Pull Requests:\n")
        f.write(f"  Median: {metrics['RQ2_median_prs']:.2f}\n")
        f.write(f"  Average: {metrics['RQ2_avg_prs']:.2f}\n")
        f.write(f"  Std Dev: {metrics['RQ2_std_prs']:.2f}\n\n")

        f.write("RQ3 - Total Releases:\n")
        f.write(f"  Median: {metrics['RQ3_median_releases']:.2f}\n\n")

        f.write("RQ4 - Days Since Last Push:\n")
        f.write(f"  Median: {metrics['RQ4_median_days']:.2f}\n\n")

        f.write("RQ5 - Repository Count by Language:\n")
        for lang, count in sorted(metrics['RQ5_language_counts'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {lang}: {count}\n")
        f.write("\n")

        f.write("RQ6 - Closed Issue Ratio:\n")
        f.write(f"  Median: {metrics['RQ6_median_ratio']:.4f}\n\n")

        f.write("RQ7 - Language Popularity vs Median PRs and Releases:\n")
        f.write("Language\t\tRepos\tMedian PRs\tMedian Releases\n")
        f.write("-" * 55 + "\n")
        for item in metrics['RQ7_language_analysis']:
            f.write(f"{item['language'][:15]:<15}\t{item['repo_count']:<5}\t{item['median_prs']:<10.1f}\t{item['median_releases']:<14.1f}\n")
        f.write("\n")

    print("Metrics saved to metrics_summary.txt")

    # Create graphs
    create_graphs(df_filtered, metrics)

def create_graphs(df, metrics):
    """Create graphs for Google Docs report"""

    # Set up the plotting style
    plt.style.use('default')
    plt.rcParams['figure.figsize'] = (10, 6)

    # RQ1: Age distribution
    plt.figure()
    plt.hist(df['age_years'], bins=30, edgecolor='black', alpha=0.7)
    plt.axvline(metrics['RQ1_median_age'], color='red', linestyle='--', label=f'Median: {metrics["RQ1_median_age"]:.1f}')
    plt.xlabel('Repository Age (years)')
    plt.ylabel('Number of Repositories')
    plt.title('RQ1: Distribution of Repository Ages')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('rq1_age_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    # RQ2: Merged PRs distribution
    plt.figure()
    plt.hist(df['merged_prs'], bins=30, edgecolor='black', alpha=0.7)
    plt.axvline(metrics['RQ2_median_prs'], color='red', linestyle='--', label=f'Median: {metrics["RQ2_median_prs"]:.1f}')
    plt.xlabel('Number of Merged Pull Requests')
    plt.ylabel('Number of Repositories')
    plt.title('RQ2: Distribution of Merged Pull Requests')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('rq2_prs_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    # RQ3: Releases distribution
    plt.figure()
    plt.hist(df['releases'], bins=30, edgecolor='black', alpha=0.7)
    plt.axvline(metrics['RQ3_median_releases'], color='red', linestyle='--', label=f'Median: {metrics["RQ3_median_releases"]:.1f}')
    plt.xlabel('Number of Releases')
    plt.ylabel('Number of Repositories')
    plt.title('RQ3: Distribution of Releases')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('rq3_releases_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    # RQ4: Days since update distribution
    plt.figure()
    plt.hist(df['days_since_update'], bins=30, edgecolor='black', alpha=0.7)
    plt.axvline(metrics['RQ4_median_days'], color='red', linestyle='--', label=f'Median: {metrics["RQ4_median_days"]:.1f}')
    plt.xlabel('Days Since Last Push')
    plt.ylabel('Number of Repositories')
    plt.title('RQ4: Distribution of Days Since Last Push')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('rq4_days_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    # RQ5: Language counts (top 15)
    top_languages = sorted(metrics['RQ5_language_counts'].items(), key=lambda x: x[1], reverse=True)[:15]
    langs, counts = zip(*top_languages)

    plt.figure(figsize=(12, 8))
    bars = plt.bar(range(len(langs)), counts, edgecolor='black', alpha=0.7)
    plt.xticks(range(len(langs)), langs, rotation=45, ha='right')
    plt.xlabel('Programming Language')
    plt.ylabel('Number of Repositories')
    plt.title('RQ5: Repository Count by Programming Language (Top 15)')

    # Add value labels on bars
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                str(count), ha='center', va='bottom')

    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('rq5_language_counts.png', dpi=300, bbox_inches='tight')
    plt.close()

    # RQ6: Closed issue ratio distribution
    ratios = df['closed_issue_ratio'].dropna()
    plt.figure()
    plt.hist(ratios, bins=30, edgecolor='black', alpha=0.7)
    plt.axvline(metrics['RQ6_median_ratio'], color='red', linestyle='--', label=f'Median: {metrics["RQ6_median_ratio"]:.3f}')
    plt.xlabel('Closed Issue Ratio')
    plt.ylabel('Number of Repositories')
    plt.title('RQ6: Distribution of Closed Issue Ratios')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('rq6_ratio_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    # RQ7: Language popularity vs median PRs and releases
    rq7_df = pd.DataFrame(metrics['RQ7_language_analysis'])

    # Scatter plot: Repo count vs Median PRs
    plt.figure(figsize=(12, 8))
    plt.scatter(rq7_df['repo_count'], rq7_df['median_prs'], s=100, alpha=0.7, edgecolors='black')

    # Add language labels
    for i, row in rq7_df.iterrows():
        plt.annotate(row['language'], (row['repo_count'], row['median_prs']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

    plt.xlabel('Number of Repositories (Language Popularity)')
    plt.ylabel('Median Merged Pull Requests')
    plt.title('RQ7: Language Popularity vs Median Pull Requests')
    plt.grid(True, alpha=0.3)

    # Add trend line
    if len(rq7_df) > 1:
        z = np.polyfit(rq7_df['repo_count'], rq7_df['median_prs'], 1)
        p = np.poly1d(z)
        plt.plot(rq7_df['repo_count'], p(rq7_df['repo_count']), "r--", alpha=0.8, label='Trend line')

    plt.legend()
    plt.tight_layout()
    plt.savefig('rq7_popularity_vs_prs.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Scatter plot: Repo count vs Median Releases
    plt.figure(figsize=(12, 8))
    plt.scatter(rq7_df['repo_count'], rq7_df['median_releases'], s=100, alpha=0.7, edgecolors='black')

    # Add language labels
    for i, row in rq7_df.iterrows():
        plt.annotate(row['language'], (row['repo_count'], row['median_releases']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

    plt.xlabel('Number of Repositories (Language Popularity)')
    plt.ylabel('Median Releases')
    plt.title('RQ7: Language Popularity vs Median Releases')
    plt.grid(True, alpha=0.3)

    # Add trend line
    if len(rq7_df) > 1:
        z = np.polyfit(rq7_df['repo_count'], rq7_df['median_releases'], 1)
        p = np.poly1d(z)
        plt.plot(rq7_df['repo_count'], p(rq7_df['repo_count']), "r--", alpha=0.8, label='Trend line')

    plt.legend()
    plt.tight_layout()
    plt.savefig('rq7_popularity_vs_releases.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Graphs saved as PNG files:")
    print("- rq1_age_distribution.png")
    print("- rq2_prs_distribution.png")
    print("- rq3_releases_distribution.png")
    print("- rq4_days_distribution.png")
    print("- rq5_language_counts.png")
    print("- rq6_ratio_distribution.png")
    print("- rq7_popularity_vs_prs.png")
    print("- rq7_popularity_vs_releases.png")

if __name__ == "__main__":
    main()