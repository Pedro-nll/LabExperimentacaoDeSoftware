"""
Lab01S01 - GitHub GraphQL API Query
Fetches top 100 most-starred repositories and answers RQ01-RQ07.

Usage:
    export GITHUB_TOKEN=your_personal_access_token
    python main.py

Requirements:
    pip install requests pandas tabulate
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone
from tabulate import tabulate

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}

TOTAL_REPOS = 1000
MAX_RETRIES = 5          # max attempts per page before giving up
RETRY_BACKOFF_BASE = 2   # seconds; doubles on each retry (2, 4, 8, 16, 32)


# ─────────────────────────────────────────────
# GraphQL Query
# Fields required per RQ:
#   createdAt            → RQ01 (age)
#   mergedPullRequests   → RQ02 (accepted PRs)
#   releases             → RQ03 (release count)
#   updatedAt            → RQ04 (time since last update)
#   primaryLanguage      → RQ05 (primary language)
#   closedIssues /
#   openIssues           → RQ06 (closed-issue ratio)
# ─────────────────────────────────────────────
QUERY = """
query($cursor: String) {
  search(
    query: "stars:>1 sort:stars-desc"
    type: REPOSITORY
    first: 10
    after: $cursor
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        nameWithOwner
        stargazerCount

        # RQ01 – repository age
        createdAt

        # RQ04 – time since last update
        updatedAt

        # RQ05 – primary language
        primaryLanguage { name }

        # RQ02 – accepted (merged) pull requests
        mergedPullRequests: pullRequests(states: MERGED) { totalCount }

        # RQ03 – total releases
        releases { totalCount }

        # RQ06 – closed vs total issues
        closedIssues: issues(states: CLOSED) { totalCount }
        openIssues:   issues(states: OPEN)   { totalCount }
      }
    }
  }
}
"""


# ─────────────────────────────────────────────
# Single request with retry + exponential backoff
# Handles transient 5xx / 502 errors from GitHub
# ─────────────────────────────────────────────
def run_query(cursor: str | None) -> dict:
    """
    Execute one GraphQL page request.
    Retries up to MAX_RETRIES times on network errors or 5xx responses,
    waiting RETRY_BACKOFF_BASE ** attempt seconds between tries.
    """
    variables = {"cursor": cursor}
    payload = {"query": QUERY, "variables": variables}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                GRAPHQL_URL,
                json=payload,
                headers=HEADERS,
                timeout=30,
            )

            # Retry on server-side errors (502 Bad Gateway, 503, etc.)
            if response.status_code >= 500:
                wait = RETRY_BACKOFF_BASE ** attempt
                print(
                    f"  ⚠  HTTP {response.status_code} on attempt {attempt}/{MAX_RETRIES}. "
                    f"{response.json}"
                    f"Retrying in {wait}s…"
                )
                time.sleep(wait)
                continue

            # Let other HTTP errors (401, 403, …) surface immediately
            response.raise_for_status()

            data = response.json()

            # Surface GraphQL-level errors (distinct from HTTP errors)
            if "errors" in data:
                raise RuntimeError(f"GraphQL errors: {data['errors']}")

            return data["data"]["search"]

        except requests.exceptions.ConnectionError as exc:
            wait = RETRY_BACKOFF_BASE ** attempt
            print(
                f"  ⚠  Connection error on attempt {attempt}/{MAX_RETRIES}: {exc}. "
                f"Retrying in {wait}s…"
            )
            time.sleep(wait)

    raise RuntimeError(
        f"Failed to fetch page after {MAX_RETRIES} attempts. "
        "Check your internet connection or try again later."
    )


# ─────────────────────────────────────────────
# Automatic pagination – collects exactly `total` repositories
# ─────────────────────────────────────────────
def fetch_repositories(total: int = TOTAL_REPOS) -> list[dict]:
    """
    Paginates through the GitHub GraphQL API (25 repos per page)
    until `total` repositories have been collected.
    """
    repos = []
    cursor = None

    while len(repos) < total:
        search = run_query(cursor)
        nodes = search["nodes"]
        repos.extend(nodes)

        collected = min(len(repos), total)
        print(f"  Collected {collected} / {total} …")

        page_info = search["pageInfo"]
        if not page_info["hasNextPage"] or len(repos) >= total:
            break

        cursor = page_info["endCursor"]
        time.sleep(1)  # respect GitHub secondary rate limits

    return repos[:total]


# ─────────────────────────────────────────────
# Data normalisation
# ─────────────────────────────────────────────
def parse_repositories(raw: list[dict]) -> pd.DataFrame:
    """Flatten raw GraphQL nodes into a tidy DataFrame."""
    now = datetime.now(timezone.utc)
    rows = []

    for r in raw:
        created_at = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(r["updatedAt"].replace("Z", "+00:00"))

        closed_issues = r["closedIssues"]["totalCount"]
        open_issues   = r["openIssues"]["totalCount"]
        total_issues  = closed_issues + open_issues

        rows.append({
            "repo":              r["nameWithOwner"],
            "stars":             r["stargazerCount"],
            # RQ01
            "age_days":          (now - created_at).days,
            "age_years":         round((now - created_at).days / 365.25, 2),
            # RQ02
            "merged_prs":        r["mergedPullRequests"]["totalCount"],
            # RQ03
            "releases":          r["releases"]["totalCount"],
            # RQ04
            "days_since_update": (now - updated_at).days,
            # RQ05
            "language":          (r["primaryLanguage"]["name"]
                                  if r["primaryLanguage"] else "Unknown"),
            # RQ06
            "closed_issues":     closed_issues,
            "total_issues":      total_issues,
            "closed_issue_ratio": (
                round(closed_issues / total_issues, 4) if total_issues > 0 else None
            ),
        })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────
def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def summarise(series: pd.Series) -> None:
    print(f"  min    : {series.min():.2f}")
    print(f"  median : {series.median():.2f}")
    print(f"  mean   : {series.mean():.2f}")
    print(f"  max    : {series.max():.2f}")


# ─────────────────────────────────────────────
# Main analysis
# ─────────────────────────────────────────────
def main():
    if not GITHUB_TOKEN:
        raise EnvironmentError(
            "GITHUB_TOKEN is not set. Export it before running:\n"
            "  export GITHUB_TOKEN=ghp_..."
        )

    print("Fetching top 100 most-starred repositories from GitHub…")
    
    # Incrementally fetch, parse, and save repositories
    all_repos = []
    df = pd.DataFrame()
    cursor = None
    out_path = "repos_data_backup.csv"
    
    while len(all_repos) < TOTAL_REPOS:
        search = run_query(cursor)
        nodes = search["nodes"]
        all_repos.extend(nodes)
        
        collected = min(len(all_repos), TOTAL_REPOS)
        print(f"  Collected {collected} / {TOTAL_REPOS} …")
        
        # Parse the current batch and append to DataFrame
        batch_df = parse_repositories(nodes)
        df = pd.concat([df, batch_df], ignore_index=True)
        
        # Update CSV after each page
        df.to_csv(out_path, index=False)
        print(f"  ✓ Updated '{out_path}'")
        
        page_info = search["pageInfo"]
        if not page_info["hasNextPage"] or len(all_repos) >= TOTAL_REPOS:
            break
        
        cursor = page_info["endCursor"]
        time.sleep(1)  # respect GitHub secondary rate limits
    
    # Trim to exact total if we exceeded it
    df = df.iloc[:TOTAL_REPOS]
    df.to_csv(out_path, index=False)
    
    print(f"\n✓ {len(df)} repositories collected and parsed.\n")

    # ── RQ01: Are popular systems mature/old? ──────────────────────────────
    print_section("RQ01 – Repository Age (years)")
    print("  Metric: age calculated from creation date")
    summarise(df["age_years"])

    # ── RQ02: Do popular systems receive a lot of external contribution? ───
    print_section("RQ02 – Merged Pull Requests")
    print("  Metric: total accepted (merged) pull requests")
    summarise(df["merged_prs"])

    # ── RQ03: Do popular systems release frequently? ───────────────────────
    print_section("RQ03 – Total Releases")
    print("  Metric: total number of releases")
    summarise(df["releases"])

    # ── RQ04: Are popular systems updated frequently? ──────────────────────
    print_section("RQ04 – Days Since Last Update")
    print("  Metric: days elapsed since the last push/update")
    summarise(df["days_since_update"])

    # ── RQ05: Are popular systems written in the most popular languages? ───
    print_section("RQ05 – Primary Language Distribution")
    print("  Metric: primary language of each repository\n")
    lang_counts = (
        df["language"]
        .value_counts()
        .rename_axis("language")
        .reset_index(name="repo_count")
    )
    print(tabulate(lang_counts, headers="keys", tablefmt="rounded_outline", showindex=False))

    # ── RQ06: Do popular systems have a high ratio of closed issues? ───────
    print_section("RQ06 – Closed Issue Ratio")
    print("  Metric: closed_issues / total_issues")
    summarise(df["closed_issue_ratio"].dropna())

    # ── RQ07 (Bonus): Breakdown of RQ02, RQ03, RQ04 by language ───────────
    print_section("RQ07 (Bonus) – RQ02 / RQ03 / RQ04 Broken Down by Language")
    print(
        "  Do repos in more popular languages receive more contributions,\n"
        "  release more often, and get updated more frequently?\n"
    )
    lang_group = (
        df.groupby("language")
        .agg(
            repo_count          =("repo",             "count"),
            median_merged_prs   =("merged_prs",       "median"),   # RQ02
            median_releases     =("releases",         "median"),   # RQ03
            median_days_updated =("days_since_update","median"),   # RQ04
        )
        .query("repo_count >= 2")
        .sort_values("repo_count", ascending=False)
        .reset_index()
    )
    print(tabulate(
        lang_group,
        headers=[
            "Language", "# Repos",
            "Median Merged PRs (RQ02)",
            "Median Releases (RQ03)",
            "Median Days Since Update (RQ04)",
        ],
        tablefmt="rounded_outline",
        showindex=False,
        floatfmt=".1f",
    ))


if __name__ == "__main__":
    main()