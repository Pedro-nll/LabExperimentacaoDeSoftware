#!/usr/bin/env python3
"""Collect pull request level metrics for the selected repositories."""

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional

from github_cr import (
    build_url,
    format_iso8601,
    github_get_json,
    github_token,
    is_human_login,
    load_checkpoint,
    max_datetime,
    normalize_feedback,
    parse_iso8601,
    read_csv_rows,
    save_checkpoint,
    safe_int,
    write_csv_rows,
)

PR_COLUMNS = [
    "owner",
    "repo",
    "full_name",
    "pr_number",
    "html_url",
    "title",
    "state",
    "created_at",
    "updated_at",
    "last_activity_at",
    "analysis_hours",
    "body_chars",
    "changed_files",
    "additions",
    "deletions",
    "total_changes",
    "issue_comments",
    "review_comments",
    "total_comments",
    "human_review_count",
    "participant_count",
    "final_review_state",
    "final_feedback",
    "review_states",
    "review_participants",
    "has_human_review",
    "author_login",
    "merged_at",
]

RUN_LOG_COLUMNS = ["owner", "repo", "status", "message"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect code review PR metrics")
    parser.add_argument("--repos-csv", required=True, help="CSV with selected repositories")
    parser.add_argument("--output", required=True, help="Output directory for per-repo PR CSVs")
    parser.add_argument("--repo-limit", type=int, default=1, help="How many repositories to process")
    parser.add_argument("--pr-limit", type=int, default=50, help="Maximum PRs to collect per repository")
    parser.add_argument("--max-retries", type=int, default=5, help="API retries")
    parser.add_argument("--checkpoint", default="", help="Checkpoint JSON file")
    return parser.parse_args()


def repo_slug(owner: str, repo: str) -> str:
    return f"{owner}__{repo}"


def list_repo_pulls(owner: str, repo: str, token: Optional[str], max_retries: int, page: int) -> List[Dict[str, Any]]:
    url = build_url(
        f"/repos/{owner}/{repo}/pulls",
        {
            "state": "all",
            "sort": "updated",
            "direction": "desc",
            "per_page": 100,
            "page": page,
        },
    )
    payload = github_get_json(url, token=token, max_retries=max_retries)
    return payload if isinstance(payload, list) else []


def list_pull_reviews(owner: str, repo: str, number: int, token: Optional[str], max_retries: int) -> List[Dict[str, Any]]:
    url = build_url(f"/repos/{owner}/{repo}/pulls/{number}/reviews", {"per_page": 100, "page": 1})
    payload = github_get_json(url, token=token, max_retries=max_retries)
    return payload if isinstance(payload, list) else []


def list_issue_comments(owner: str, repo: str, number: int, token: Optional[str], max_retries: int) -> List[Dict[str, Any]]:
    url = build_url(f"/repos/{owner}/{repo}/issues/{number}/comments", {"per_page": 100, "page": 1})
    payload = github_get_json(url, token=token, max_retries=max_retries)
    return payload if isinstance(payload, list) else []


def list_review_comments(owner: str, repo: str, number: int, token: Optional[str], max_retries: int) -> List[Dict[str, Any]]:
    url = build_url(f"/repos/{owner}/{repo}/pulls/{number}/comments", {"per_page": 100, "page": 1})
    payload = github_get_json(url, token=token, max_retries=max_retries)
    return payload if isinstance(payload, list) else []


def pull_details(owner: str, repo: str, number: int, token: Optional[str], max_retries: int) -> Dict[str, Any]:
    url = build_url(f"/repos/{owner}/{repo}/pulls/{number}")
    return github_get_json(url, token=token, max_retries=max_retries)


def participant_logins(
    author_login: str,
    issue_comments: List[Dict[str, Any]],
    reviews: List[Dict[str, Any]],
    review_comments: List[Dict[str, Any]],
) -> List[str]:
    logins = OrderedDict()
    if author_login:
        logins[author_login] = None
    for comment in issue_comments:
        login = ((comment.get("user") or {}).get("login")) or ""
        if login:
            logins[login] = None
    for review in reviews:
        login = ((review.get("user") or {}).get("login")) or ""
        if login:
            logins[login] = None
    for comment in review_comments:
        login = ((comment.get("user") or {}).get("login")) or ""
        if login:
            logins[login] = None
    return list(logins.keys())


def human_reviews(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for review in reviews:
        user = review.get("user") or {}
        login = str(user.get("login", ""))
        if is_human_login(login):
            result.append(review)
    return result


def final_review_state(reviews: List[Dict[str, Any]]) -> str:
    human = human_reviews(reviews)
    if not human:
        return "NO_REVIEW"
    latest = max(human, key=lambda item: item.get("submitted_at") or "")
    return str(latest.get("state", "NO_REVIEW") or "NO_REVIEW")


def collect_pr_rows(owner: str, repo: str, token: Optional[str], max_retries: int, pr_limit: int) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    page = 1
    while len(rows) < pr_limit:
        pulls = list_repo_pulls(owner, repo, token=token, max_retries=max_retries, page=page)
        if not pulls:
            break
        for pull in pulls:
            if len(rows) >= pr_limit:
                break

            number = safe_int(pull.get("number"), default=0)
            if number <= 0:
                continue

            details = pull_details(owner, repo, number, token=token, max_retries=max_retries)
            reviews = list_pull_reviews(owner, repo, number, token=token, max_retries=max_retries)
            issue_comments = list_issue_comments(owner, repo, number, token=token, max_retries=max_retries)
            review_comments = list_review_comments(owner, repo, number, token=token, max_retries=max_retries)

            created_at = str(details.get("created_at", "") or pull.get("created_at", ""))
            updated_at = str(details.get("updated_at", "") or pull.get("updated_at", ""))
            last_activity = max_datetime(
                [
                    updated_at,
                    *(comment.get("created_at") for comment in issue_comments),
                    *(review.get("submitted_at") for review in reviews),
                    *(comment.get("created_at") for comment in review_comments),
                ]
            )
            created_dt = parse_iso8601(created_at) if created_at else None
            analysis_hours = 0.0
            if created_dt and last_activity:
                delta = last_activity - created_dt
                analysis_hours = delta.total_seconds() / 3600.0

            body = str(details.get("body", "") or "")
            review_states = [str(review.get("state", "") or "") for review in reviews]
            human_review_list = human_reviews(reviews)
            human_reviewers = [str((review.get("user") or {}).get("login", "")) for review in human_review_list]
            participants = participant_logins(
                author_login=str((details.get("user") or {}).get("login", "") or ""),
                issue_comments=issue_comments,
                reviews=reviews,
                review_comments=review_comments,
            )
            final_state = final_review_state(reviews)

            rows.append(
                {
                    "owner": owner,
                    "repo": repo,
                    "full_name": f"{owner}/{repo}",
                    "pr_number": str(number),
                    "html_url": str(details.get("html_url", pull.get("html_url", "")) or ""),
                    "title": str(details.get("title", pull.get("title", "")) or ""),
                    "state": str(details.get("state", pull.get("state", "")) or ""),
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "last_activity_at": format_iso8601(last_activity) if last_activity else "",
                    "analysis_hours": f"{analysis_hours:.6f}",
                    "body_chars": str(len(body)),
                    "changed_files": str(safe_int(details.get("changed_files"), default=0)),
                    "additions": str(safe_int(details.get("additions"), default=0)),
                    "deletions": str(safe_int(details.get("deletions"), default=0)),
                    "total_changes": str(
                        safe_int(details.get("additions"), default=0) + safe_int(details.get("deletions"), default=0)
                    ),
                    "issue_comments": str(len(issue_comments)),
                    "review_comments": str(len(review_comments)),
                    "total_comments": str(len(issue_comments) + len(review_comments)),
                    "human_review_count": str(len(human_review_list)),
                    "participant_count": str(len(participants)),
                    "final_review_state": final_state,
                    "final_feedback": normalize_feedback(final_state),
                    "review_states": "|".join(review_states),
                    "review_participants": "|".join(human_reviewers),
                    "has_human_review": "yes" if human_review_list else "no",
                    "author_login": str((details.get("user") or {}).get("login", "") or ""),
                    "merged_at": str(details.get("merged_at", "") or ""),
                }
            )
        page += 1

    return rows


def write_run_log(path: Path, rows: List[Dict[str, str]]) -> None:
    write_csv_rows(path, rows, RUN_LOG_COLUMNS)


def main() -> int:
    args = parse_args()
    token = github_token()
    repos_csv = Path(args.repos_csv).resolve()
    output_root = Path(args.output).resolve()
    checkpoint_path = Path(args.checkpoint).resolve() if args.checkpoint else output_root / "pipeline_run_log.checkpoint.json"

    repos = read_csv_rows(repos_csv)
    if not repos:
        raise RuntimeError(f"No repositories found in {repos_csv}")

    checkpoint = load_checkpoint(checkpoint_path, {"repo_index": 0})
    start_index = int(checkpoint.get("repo_index", 0) or 0)
    selected_repos = repos[: max(1, args.repo_limit)]

    run_log_path = output_root / "pipeline_run_log.csv"
    run_log: List[Dict[str, str]] = read_csv_rows(run_log_path)
    completed = {
        (row.get("owner", ""), row.get("repo", ""))
        for row in run_log
        if row.get("status") == "ok"
    }

    for repo_index, row in enumerate(selected_repos[start_index:], start=start_index):
        owner = row.get("owner", "").strip()
        repo = row.get("repo", "").strip()
        if not owner or not repo:
            continue

        slug = repo_slug(owner, repo)
        repo_output_dir = output_root / slug
        repo_csv = repo_output_dir / "prs.csv"

        if (owner, repo) in completed and repo_csv.exists():
            print(f"Skipping completed {slug}")
            continue

        try:
            print(f"Collecting {slug}")
            rows = collect_pr_rows(owner, repo, token=token, max_retries=args.max_retries, pr_limit=args.pr_limit)
            write_csv_rows(repo_csv, rows, PR_COLUMNS)
            result = {"owner": owner, "repo": repo, "status": "ok", "message": f"rows={len(rows)}"}
        except Exception as exc:  # noqa: BLE001
            result = {"owner": owner, "repo": repo, "status": "error", "message": str(exc)}

        run_log.append(result)
        write_run_log(run_log_path, run_log)
        save_checkpoint(checkpoint_path, {"repo_index": repo_index + 1})

    failures = [row for row in run_log if row.get("status") != "ok"]
    print(f"Processed {len(run_log)} repositories | failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())