#!/usr/bin/env python3
"""Run the Lab 05 controlled experiment comparing GitHub REST and GraphQL."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from lab05_common import (
    HttpResult,
    append_csv_row,
    deterministic_api_order,
    github_token,
    graphql_raw,
    load_checkpoint,
    read_csv_rows,
    rest_json,
    save_checkpoint,
    token_label,
    utc_now_iso,
)

MEASUREMENT_COLUMNS = [
    "measurement_id",
    "pair_id",
    "timestamp",
    "api_type",
    "scenario_id",
    "scenario_name",
    "repository",
    "owner",
    "repo",
    "run_number",
    "order_index",
    "http_status",
    "success",
    "elapsed_ms",
    "response_bytes",
    "request_count",
    "attempts",
    "token_label",
    "error",
]

SCENARIOS = {
    "C1": "repository_metadata",
    "C2": "recent_pull_requests",
    "C3": "recent_issues",
    "C4": "combined_repository_prs_issues",
}

GQL_C1 = """
query RepoMetadata($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    nameWithOwner
    url
    description
    stargazerCount
    forkCount
    primaryLanguage { name }
    createdAt
    updatedAt
    pushedAt
    defaultBranchRef { name }
    issues { totalCount }
    pullRequests { totalCount }
  }
}
"""

GQL_C2 = """
query RecentPullRequests($owner: String!, $repo: String!, $limit: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: $limit, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        state
        createdAt
        updatedAt
        author { login }
        comments { totalCount }
        changedFiles
        additions
        deletions
      }
    }
  }
}
"""

GQL_C3 = """
query RecentIssues($owner: String!, $repo: String!, $limit: Int!) {
  repository(owner: $owner, name: $repo) {
    issues(first: $limit, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        state
        createdAt
        updatedAt
        author { login }
        comments { totalCount }
      }
    }
  }
}
"""

GQL_C4 = """
query CombinedRepoData($owner: String!, $repo: String!, $limit: Int!) {
  repository(owner: $owner, name: $repo) {
    nameWithOwner
    url
    description
    stargazerCount
    forkCount
    primaryLanguage { name }
    createdAt
    updatedAt
    pushedAt
    defaultBranchRef { name }
    issues { totalCount }
    pullRequests { totalCount }
    recentPullRequests: pullRequests(first: $limit, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        state
        createdAt
        updatedAt
        author { login }
        comments { totalCount }
        changedFiles
        additions
        deletions
      }
    }
    recentIssues: issues(first: $limit, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        state
        createdAt
        updatedAt
        author { login }
        comments { totalCount }
      }
    }
  }
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run REST vs GraphQL measurements")
    parser.add_argument("--repos-csv", default="enunciado5/data/top_python_repos.csv", help="Repository CSV")
    parser.add_argument("--output", default="enunciado5/output/measurements.csv", help="Output measurements CSV")
    parser.add_argument("--checkpoint", default="", help="Checkpoint JSON path")
    parser.add_argument("--runs", type=int, default=30, help="Repetitions per repository/scenario/treatment")
    parser.add_argument("--repo-limit", type=int, default=0, help="Limit repositories for smoke tests; 0 means all")
    parser.add_argument("--scenarios", default="C1,C2,C3,C4", help="Comma-separated scenario ids")
    parser.add_argument("--item-limit", type=int, default=10, help="PR/issue count for list scenarios")
    parser.add_argument("--max-retries", type=int, default=5, help="API retry count")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional sleep between measurements")
    return parser.parse_args()


def aggregate_results(results: List[HttpResult]) -> HttpResult:
    status = 200 if all(result.status == 200 and not result.error for result in results) else next(
        (result.status for result in results if result.status != 200 or result.error),
        0,
    )
    error = "; ".join(result.error for result in results if result.error)
    return HttpResult(
        status=status,
        elapsed_ms=sum(result.elapsed_ms for result in results),
        response_bytes=sum(result.response_bytes for result in results),
        body_text="",
        error=error,
        attempts=sum(result.attempts for result in results),
    )


def run_rest(owner: str, repo: str, scenario_id: str, item_limit: int, token: str | None, max_retries: int) -> Tuple[HttpResult, int]:
    if scenario_id == "C1":
        result, _ = rest_json(f"/repos/{owner}/{repo}", None, token=token, max_retries=max_retries)
        return result, 1
    if scenario_id == "C2":
        result, _ = rest_json(
            f"/repos/{owner}/{repo}/pulls",
            {"state": "all", "sort": "updated", "direction": "desc", "per_page": item_limit},
            token=token,
            max_retries=max_retries,
        )
        return result, 1
    if scenario_id == "C3":
        result, _ = rest_json(
            "/search/issues",
            {"q": f"repo:{owner}/{repo} type:issue", "sort": "updated", "order": "desc", "per_page": item_limit},
            token=token,
            max_retries=max_retries,
        )
        return result, 1
    if scenario_id == "C4":
        results = [
            rest_json(f"/repos/{owner}/{repo}", None, token=token, max_retries=max_retries)[0],
            rest_json(
                f"/repos/{owner}/{repo}/pulls",
                {"state": "all", "sort": "updated", "direction": "desc", "per_page": item_limit},
                token=token,
                max_retries=max_retries,
            )[0],
            rest_json(
                "/search/issues",
                {"q": f"repo:{owner}/{repo} type:issue", "sort": "updated", "order": "desc", "per_page": item_limit},
                token=token,
                max_retries=max_retries,
            )[0],
        ]
        return aggregate_results(results), len(results)
    raise ValueError(f"Unknown scenario: {scenario_id}")


def run_graphql(owner: str, repo: str, scenario_id: str, item_limit: int, token: str | None, max_retries: int) -> Tuple[HttpResult, int]:
    variables: Dict[str, Any] = {"owner": owner, "repo": repo}
    if scenario_id in {"C2", "C3", "C4"}:
        variables["limit"] = item_limit
    query = {"C1": GQL_C1, "C2": GQL_C2, "C3": GQL_C3, "C4": GQL_C4}[scenario_id]
    result, _ = graphql_raw(query, variables, token=token, max_retries=max_retries)
    return result, 1


def measurement_row(
    *,
    pair_id: str,
    api_type: str,
    scenario_id: str,
    repository: str,
    owner: str,
    repo: str,
    run_number: int,
    order_index: int,
    result: HttpResult,
    request_count: int,
) -> Dict[str, Any]:
    measurement_id = f"{pair_id}:{api_type}"
    return {
        "measurement_id": measurement_id,
        "pair_id": pair_id,
        "timestamp": utc_now_iso(),
        "api_type": api_type,
        "scenario_id": scenario_id,
        "scenario_name": SCENARIOS[scenario_id],
        "repository": repository,
        "owner": owner,
        "repo": repo,
        "run_number": run_number,
        "order_index": order_index,
        "http_status": result.status,
        "success": int(result.status == 200 and not result.error),
        "elapsed_ms": f"{result.elapsed_ms:.3f}",
        "response_bytes": result.response_bytes,
        "request_count": request_count,
        "attempts": result.attempts,
        "token_label": token_label("rest" if api_type == "REST" else "graphql"),
        "error": result.error,
    }


def load_completed(path: Path, checkpoint_path: Path) -> set[str]:
    load_checkpoint(checkpoint_path, {})
    completed: set[str] = set()
    for row in read_csv_rows(path):
        measurement_id = row.get("measurement_id", "")
        if measurement_id:
            completed.add(measurement_id)
    return completed


def main() -> int:
    args = parse_args()
    repos = read_csv_rows(Path(args.repos_csv))
    if args.repo_limit > 0:
        repos = repos[: args.repo_limit]
    scenario_ids = [part.strip().upper() for part in args.scenarios.split(",") if part.strip()]
    scenario_ids = [scenario for scenario in scenario_ids if scenario in SCENARIOS]
    if not repos:
        print(f"[experiment] no repositories found in {args.repos_csv}")
        return 1
    if not scenario_ids:
        print("[experiment] no valid scenarios selected")
        return 1

    output_path = Path(args.output)
    checkpoint_path = Path(args.checkpoint) if args.checkpoint else output_path.with_suffix(".checkpoint.json")
    rest_token = github_token("rest")
    graphql_token = github_token("graphql")
    completed = load_completed(output_path, checkpoint_path)

    total_pairs = len(repos) * len(scenario_ids) * args.runs
    total_measurements = total_pairs * 2
    done = len(completed)
    print(
        "[experiment] starting "
        f"repos={len(repos)} scenarios={len(scenario_ids)} runs={args.runs} "
        f"measurements={total_measurements} already_done={done}"
    )
    print(f"[experiment] REST token={token_label('rest')} GraphQL token={token_label('graphql')}")

    for repo_index, repo_row in enumerate(repos, start=1):
        owner = repo_row.get("owner", "")
        repo = repo_row.get("repo", "")
        repository = repo_row.get("full_name", f"{owner}/{repo}")
        if not owner or not repo:
            continue

        for scenario_id in scenario_ids:
            for run_number in range(1, args.runs + 1):
                pair_id = f"{repository}:{scenario_id}:run{run_number:03d}"
                for order_index, api_type in enumerate(deterministic_api_order(repository, scenario_id, run_number), start=1):
                    measurement_id = f"{pair_id}:{api_type}"
                    if measurement_id in completed:
                        continue

                    if api_type == "REST":
                        result, request_count = run_rest(owner, repo, scenario_id, args.item_limit, rest_token, args.max_retries)
                    else:
                        result, request_count = run_graphql(owner, repo, scenario_id, args.item_limit, graphql_token, args.max_retries)

                    row = measurement_row(
                        pair_id=pair_id,
                        api_type=api_type,
                        scenario_id=scenario_id,
                        repository=repository,
                        owner=owner,
                        repo=repo,
                        run_number=run_number,
                        order_index=order_index,
                        result=result,
                        request_count=request_count,
                    )
                    append_csv_row(output_path, row, MEASUREMENT_COLUMNS)
                    completed.add(measurement_id)
                    save_checkpoint(
                        checkpoint_path,
                        {
                            "completed_count": len(completed),
                            "last_measurement_id": measurement_id,
                            "updated_at": utc_now_iso(),
                            "config": {
                                "repos_csv": args.repos_csv,
                                "runs": args.runs,
                                "scenarios": scenario_ids,
                                "item_limit": args.item_limit,
                            },
                        },
                    )

                    done = len(completed)
                    progress = done / total_measurements * 100.0
                    status = "ok" if row["success"] else f"fail:{row['error'] or row['http_status']}"
                    print(
                        f"[experiment] {done:05d}/{total_measurements} ({progress:5.1f}%) "
                        f"repo={repo_index}/{len(repos)} {repository} {scenario_id} run={run_number} "
                        f"api={api_type} status={status} time={row['elapsed_ms']}ms bytes={row['response_bytes']}"
                    )
                    if args.sleep > 0:
                        time.sleep(args.sleep)

    print(f"[experiment] finished output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
