#!/usr/bin/env python3
"""Select eligible repositories for the code review study."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional

from github_cr import (
    build_url,
    github_get_json,
    github_token,
    is_human_login,
    load_checkpoint,
    read_csv_rows,
    save_checkpoint,
    write_csv_rows,
)

DEFAULT_COLUMNS = [
    "owner",
    "repo",
    "full_name",
    "html_url",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "language",
    "created_at",
    "pushed_at",
    "default_branch",
    "total_prs",
    "review_probe_pr",
    "review_probe_state",
    "review_probe_human_reviewer",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect eligible GitHub repositories")
    parser.add_argument("--output", required=True, help="Output CSV with selected repositories")
    parser.add_argument("--target", type=int, default=200, help="How many top repositories to inspect")
    parser.add_argument("--per-page", type=int, default=100, help="GitHub search page size")
    parser.add_argument("--min-prs", type=int, default=100, help="Minimum total PRs for a repo to qualify")
    parser.add_argument(
        "--review-scan-limit",
        type=int,
        default=10,
        help="How many recent PRs to inspect for a human review",
    )
    parser.add_argument("--checkpoint", default="", help="Checkpoint JSON file")
    parser.add_argument("--max-retries", type=int, default=5, help="API retries")
    return parser.parse_args()


def repo_key(owner: str, repo: str) -> str:
    return f"{owner}/{repo}"


def search_repositories(page: int, per_page: int, token: Optional[str], max_retries: int) -> List[Dict[str, Any]]:
    url = build_url(
        "/search/repositories",
        {
            "q": "stars:>0",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page,
        },
    )
    payload = github_get_json(url, token=token, max_retries=max_retries)
    items = payload.get("items", [])
    return items if isinstance(items, list) else []


def count_pull_requests(owner: str, repo: str, token: Optional[str], max_retries: int) -> int:
    url = build_url(
        "/search/issues",
        {
            "q": f"repo:{owner}/{repo} type:pr",
            "per_page": 1,
        },
    )
    payload = github_get_json(url, token=token, max_retries=max_retries)
    return int(payload.get("total_count", 0) or 0)


def list_recent_pulls(owner: str, repo: str, token: Optional[str], max_retries: int, per_page: int) -> List[Dict[str, Any]]:
    url = build_url(
        f"/repos/{owner}/{repo}/pulls",
        {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": per_page,
            "page": 1,
        },
    )
    payload = github_get_json(url, token=token, max_retries=max_retries)
    items = payload if isinstance(payload, list) else []
    return items


def list_reviews(owner: str, repo: str, number: int, token: Optional[str], max_retries: int) -> List[Dict[str, Any]]:
    url = build_url(f"/repos/{owner}/{repo}/pulls/{number}/reviews", {"per_page": 100, "page": 1})
    payload = github_get_json(url, token=token, max_retries=max_retries)
    return payload if isinstance(payload, list) else []


def find_human_review_probe(
    owner: str,
    repo: str,
    token: Optional[str],
    max_retries: int,
    review_scan_limit: int,
) -> tuple[Optional[int], str, str]:
    pulls = list_recent_pulls(owner, repo, token, max_retries=max_retries, per_page=review_scan_limit)
    for pull in pulls:
        number = int(pull.get("number", 0) or 0)
        if number <= 0:
            continue
        reviews = list_reviews(owner, repo, number, token, max_retries=max_retries)
        for review in reviews:
            user = review.get("user") or {}
            login = str(user.get("login", ""))
            if is_human_login(login):
                state = str(review.get("state", ""))
                return number, state, login
    return None, "", ""


def repo_to_row(repo_item: Dict[str, Any], total_prs: int, review_probe_pr: Optional[int], review_probe_state: str, review_probe_human_reviewer: str) -> Dict[str, str]:
    owner = ((repo_item.get("owner") or {}).get("login")) or ""
    name = repo_item.get("name", "") or ""
    return {
        "owner": owner,
        "repo": name,
        "full_name": repo_item.get("full_name", "") or "",
        "html_url": repo_item.get("html_url", "") or "",
        "stargazers_count": str(int(repo_item.get("stargazers_count", 0) or 0)),
        "forks_count": str(int(repo_item.get("forks_count", 0) or 0)),
        "open_issues_count": str(int(repo_item.get("open_issues_count", 0) or 0)),
        "language": repo_item.get("language", "") or "",
        "created_at": repo_item.get("created_at", "") or "",
        "pushed_at": repo_item.get("pushed_at", "") or "",
        "default_branch": repo_item.get("default_branch", "") or "",
        "total_prs": str(total_prs),
        "review_probe_pr": str(review_probe_pr or ""),
        "review_probe_state": review_probe_state,
        "review_probe_human_reviewer": review_probe_human_reviewer,
    }


def main() -> int:
    args = parse_args()
    token = github_token()
    output_path = Path(args.output).resolve()
    checkpoint_path = Path(args.checkpoint).resolve() if args.checkpoint else output_path.with_suffix(".checkpoint.json")

    checkpoint = load_checkpoint(checkpoint_path, {"page": 1})
    page = int(checkpoint.get("page", 1) or 1)

    selected_rows = read_csv_rows(output_path)
    selected = {repo_key(row.get("owner", ""), row.get("repo", "")): row for row in selected_rows}

    max_pages = max(1, (args.target + args.per_page - 1) // args.per_page)

    while page <= max_pages:
        items = search_repositories(page=page, per_page=args.per_page, token=token, max_retries=args.max_retries)
        if not items:
            break

        for item in items:
            owner = ((item.get("owner") or {}).get("login")) or ""
            repo = item.get("name", "") or ""
            if not owner or not repo:
                continue

            key = repo_key(owner, repo)
            if key in selected:
                continue

            total_prs = count_pull_requests(owner, repo, token=token, max_retries=args.max_retries)
            if total_prs < args.min_prs:
                continue

            review_probe_pr, review_probe_state, review_probe_human_reviewer = find_human_review_probe(
                owner=owner,
                repo=repo,
                token=token,
                max_retries=args.max_retries,
                review_scan_limit=args.review_scan_limit,
            )
            if review_probe_pr is None:
                continue

            selected[key] = repo_to_row(
                item,
                total_prs=total_prs,
                review_probe_pr=review_probe_pr,
                review_probe_state=review_probe_state,
                review_probe_human_reviewer=review_probe_human_reviewer,
            )
            write_csv_rows(output_path, selected.values(), DEFAULT_COLUMNS)
            print(f"Selected {key} (total_prs={total_prs})")

        page += 1
        save_checkpoint(checkpoint_path, {"page": page})
        print(f"Checkpoint saved at page {page}")

    print(f"Wrote {len(selected)} selected repositories to {output_path}")
    return 0 if selected else 1


if __name__ == "__main__":
    raise SystemExit(main())