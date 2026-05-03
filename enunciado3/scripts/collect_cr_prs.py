#!/usr/bin/env python3
"""Collect pull request level metrics for the selected repositories."""

from __future__ import annotations

import argparse
import csv
import concurrent.futures
import threading
from collections import OrderedDict
import math
from pathlib import Path
import random
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
    "population_total_prs",
    "sample_target_prs",
    "sampling_confidence",
    "sampling_margin_error",
]

RUN_LOG_COLUMNS = ["owner", "repo", "status", "message"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect code review PR metrics")
    parser.add_argument("--repos-csv", required=True, help="CSV with selected repositories")
    parser.add_argument("--output", required=True, help="Output directory for per-repo PR CSVs")
    parser.add_argument(
        "--repo-limit",
        type=int,
        default=0,
        help="How many repositories to process from checkpoint (0 = all remaining)",
    )
    parser.add_argument("--pr-limit", type=int, default=50, help="Maximum PRs to collect per repository")
    parser.add_argument(
        "--confidence",
        type=int,
        default=95,
        choices=[90, 95, 99],
        help="Confidence level for statistical sample size (used when --pr-limit <= 0)",
    )
    parser.add_argument(
        "--margin-error",
        type=float,
        default=0.05,
        help="Margin of error for statistical sample size (used when --pr-limit <= 0)",
    )
    parser.add_argument(
        "--population-proportion",
        type=float,
        default=0.5,
        help="Expected proportion p in sample size formula (default worst-case 0.5)",
    )
    parser.add_argument(
        "--min-sample",
        type=int,
        default=30,
        help="Minimum sample size per repository when using statistical mode",
    )
    parser.add_argument(
        "--max-sample",
        type=int,
        default=500,
        help="Maximum sample size per repository when using statistical mode",
    )
    parser.add_argument(
        "--interaction-mode",
        choices=["summary", "full"],
        default="summary",
        help="summary uses PR payload counts only; full also fetches comment threads",
    )
    parser.add_argument("--max-retries", type=int, default=5, help="API retries")
    parser.add_argument("--checkpoint", default="", help="Checkpoint JSON file")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of repo-level workers to run in parallel (default 1)",
    )
    return parser.parse_args()


def z_for_confidence(confidence: int) -> float:
    if confidence == 90:
        return 1.645
    if confidence == 99:
        return 2.576
    return 1.96


def compute_sample_size(
    population_size: int,
    confidence: int,
    margin_error: float,
    proportion: float,
    min_sample: int,
    max_sample: int,
) -> int:
    if population_size <= 0:
        return max(1, min_sample)

    safe_margin = margin_error if margin_error > 0 else 0.05
    p = min(0.999, max(0.001, proportion))
    z = z_for_confidence(confidence)

    n0 = (z * z * p * (1.0 - p)) / (safe_margin * safe_margin)
    n = n0 / (1.0 + ((n0 - 1.0) / float(population_size)))
    n_int = int(math.ceil(n))
    n_int = max(min_sample, n_int)
    n_int = min(max_sample, n_int)
    return min(population_size, max(1, n_int))


def sample_pull_summaries(
    owner: str,
    repo: str,
    population_size: int,
    target_count: int,
    token: Optional[str],
    max_retries: int,
    worker_label: str = "",
) -> List[Dict[str, Any]]:
    if target_count <= 0 or population_size <= 0:
        return []

    sample_size = min(target_count, population_size)
    rng = random.Random(f"{owner}/{repo}:{population_size}:{sample_size}")
    selected_indexes = sorted(rng.sample(range(population_size), k=sample_size))

    page_to_offsets: Dict[int, List[int]] = {}
    for index in selected_indexes:
        page = (index // 100) + 1
        offset = index % 100
        page_to_offsets.setdefault(page, []).append(offset)

    selected: List[Dict[str, Any]] = []
    seen_numbers = set()

    prefix = f"[{worker_label}] " if worker_label else ""
    print(
        f"{prefix}Sampling {sample_size} PRs from population={population_size} ({len(page_to_offsets)} pages to fetch)",
    )

    for page in sorted(page_to_offsets.keys()):
        print(f"{prefix}Fetching sampled page {page}")
        pulls = list_repo_pulls(owner, repo, token=token, max_retries=max_retries, page=page)
        if not pulls:
            continue
        for offset in page_to_offsets[page]:
            if offset >= len(pulls):
                continue
            pull = pulls[offset]
            number = safe_int(pull.get("number"), default=0)
            if number <= 0 or number in seen_numbers:
                continue
            seen_numbers.add(number)
            selected.append(pull)

    if len(selected) < sample_size:
        max_pages = max(1, int(math.ceil(population_size / 100.0)))
        print(f"{prefix}Sample backfill required ({len(selected)}/{sample_size}), scanning up to {max_pages} pages")
        for page in range(1, max_pages + 1):
            if len(selected) >= sample_size:
                break
            if page == 1 or page % 10 == 0:
                print(f"{prefix}Backfill page {page} ({len(selected)}/{sample_size})")
            pulls = list_repo_pulls(owner, repo, token=token, max_retries=max_retries, page=page)
            if not pulls:
                break
            for pull in pulls:
                number = safe_int(pull.get("number"), default=0)
                if number <= 0 or number in seen_numbers:
                    continue
                seen_numbers.add(number)
                selected.append(pull)
                if len(selected) >= sample_size:
                    break

    print(f"{prefix}Sample ready: {len(selected[:sample_size])} PRs")
    return selected[:sample_size]


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


def participant_proxy(author_login: str, reviewers: List[str]) -> List[str]:
    logins = OrderedDict()
    if author_login:
        logins[author_login] = None
    for login in reviewers:
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


def collect_pr_rows(
    owner: str,
    repo: str,
    token: Optional[str],
    max_retries: int,
    pull_summaries: List[Dict[str, Any]],
    population_total_prs: int,
    sample_target_prs: int,
    confidence: int,
    margin_error: float,
    interaction_mode: str,
    worker_label: str = "",
    repo_csv_path: Optional[Path] = None,
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for pull in pull_summaries:
        number = safe_int(pull.get("number"), default=0)
        if number <= 0:
            continue

        details = pull_details(owner, repo, number, token=token, max_retries=max_retries)
        reviews = list_pull_reviews(owner, repo, number, token=token, max_retries=max_retries)

        created_at = str(details.get("created_at", "") or pull.get("created_at", ""))
        updated_at = str(details.get("updated_at", "") or pull.get("updated_at", ""))
        last_activity = max_datetime(
            [
                updated_at,
                *(review.get("submitted_at") for review in reviews),
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
        author_login = str((details.get("user") or {}).get("login", "") or "")
        if interaction_mode == "full":
            issue_comments = list_issue_comments(owner, repo, number, token=token, max_retries=max_retries)
            review_comments = list_review_comments(owner, repo, number, token=token, max_retries=max_retries)
            participants = participant_logins(
                author_login=author_login,
                issue_comments=issue_comments,
                reviews=reviews,
                review_comments=review_comments,
            )
            issue_comment_count = len(issue_comments)
            review_comment_count = len(review_comments)
        else:
            issue_comment_count = safe_int(pull.get("comments"), default=safe_int(details.get("comments"), default=0))
            review_comment_count = safe_int(
                pull.get("review_comments"), default=safe_int(details.get("review_comments"), default=0)
            )
            participants = participant_proxy(author_login=author_login, reviewers=human_reviewers)
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
                "issue_comments": str(issue_comment_count),
                "review_comments": str(review_comment_count),
                "total_comments": str(issue_comment_count + review_comment_count),
                "human_review_count": str(len(human_review_list)),
                "participant_count": str(len(participants)),
                "final_review_state": final_state,
                "final_feedback": normalize_feedback(final_state),
                "review_states": "|".join(review_states),
                "review_participants": "|".join(human_reviewers),
                "has_human_review": "yes" if human_review_list else "no",
                "author_login": author_login,
                "merged_at": str(details.get("merged_at", "") or ""),
                "population_total_prs": str(max(0, population_total_prs)),
                "sample_target_prs": str(max(0, sample_target_prs)),
                "sampling_confidence": str(confidence),
                "sampling_margin_error": f"{margin_error:.6f}",
            }
        )

        if repo_csv_path is not None:
            append_csv_row(repo_csv_path, rows[-1], PR_COLUMNS)
            prefix = f"[{worker_label}] " if worker_label else ""
            print(f"{prefix}Saved {len(rows)}/{len(pull_summaries)} PRs to {repo_csv_path.name}")

    return rows


def append_run_log_row(path: Path, row: Dict[str, Any]) -> None:
    append_csv_row(path, row, RUN_LOG_COLUMNS)


def append_csv_row(path: Path, row: Dict[str, Any], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    args = parse_args()
    token = github_token()
    repos_csv = Path(args.repos_csv).resolve()
    output_root = Path(args.output).resolve()
    checkpoint_path = Path(args.checkpoint).resolve() if args.checkpoint else output_root / "pipeline_run_log.checkpoint.json"

    repos = read_csv_rows(repos_csv)
    if not repos:
        raise RuntimeError(f"No repositories found in {repos_csv}")

    checkpoint = load_checkpoint(checkpoint_path, {"completed_repos": []})
    completed_repos = {
        str(item)
        for item in (checkpoint.get("completed_repos") or [])
        if str(item).strip()
    }

    run_log_path = output_root / "pipeline_run_log.csv"
    run_log: List[Dict[str, str]] = read_csv_rows(run_log_path)
    completed_repos.update(
        {
            f"{row.get('owner', '').strip()}/{row.get('repo', '').strip()}"
            for row in run_log
            if row.get("status") == "ok" and row.get("owner") and row.get("repo")
        }
    )
    completed = {
        (row.get("owner", ""), row.get("repo", ""))
        for row in run_log
        if row.get("status") == "ok"
    }

    pending_repos = []
    for row in repos:
        owner = row.get("owner", "").strip()
        repo = row.get("repo", "").strip()
        if not owner or not repo:
            continue
        slug = f"{owner}/{repo}"
        if slug in completed_repos:
            continue
        pending_repos.append(row)

    if not pending_repos:
        print(f"No pending repositories remain (completed={len(completed_repos)})")
        return 0

    selected_repos = pending_repos if args.repo_limit <= 0 else pending_repos[: max(1, args.repo_limit)]

    lock = threading.Lock()

    def save_completion_checkpoint_locked() -> None:
        save_checkpoint(checkpoint_path, {"completed_repos": sorted(completed_repos)})

    def process_single(repo_row: Dict[str, str]) -> Dict[str, str]:
        thread_id = threading.get_ident()
        worker_label = f"worker-{thread_id}"
        owner = repo_row.get("owner", "").strip()
        repo = repo_row.get("repo", "").strip()
        slug = repo_slug(owner, repo) if owner and repo else ""
        repo_output_dir = output_root / slug if slug else None
        repo_csv = repo_output_dir / "prs.csv" if slug else None
        repo_done_marker = repo_output_dir / "done.json" if repo_output_dir else None

        if not owner or not repo:
            result = {"owner": owner, "repo": repo, "status": "skip", "message": "empty owner/repo"}
            with lock:
                append_run_log_row(run_log_path, result)
            return result

        if (owner, repo) in completed and repo_csv and repo_csv.exists():
            result = {"owner": owner, "repo": repo, "status": "ok", "message": "already completed"}
            with lock:
                append_run_log_row(run_log_path, result)
            return result

        if repo_csv and repo_csv.exists():
            repo_csv.unlink()
        if repo_done_marker and repo_done_marker.exists():
            repo_done_marker.unlink()

        try:
            print(f"[{worker_label}] Collecting {slug}")
            population_total_prs = safe_int(repo_row.get("total_prs"), default=0)
            if args.pr_limit > 0:
                sample_target_prs = args.pr_limit
                if population_total_prs > 0:
                    sample_target_prs = min(sample_target_prs, population_total_prs)
            else:
                sample_target_prs = compute_sample_size(
                    population_size=population_total_prs,
                    confidence=args.confidence,
                    margin_error=args.margin_error,
                    proportion=args.population_proportion,
                    min_sample=max(1, args.min_sample),
                    max_sample=max(1, args.max_sample),
                )

            if population_total_prs <= 0:
                pull_summaries = list_repo_pulls(owner, repo, token=token, max_retries=args.max_retries, page=1)
                sample_target_prs = min(len(pull_summaries), max(1, sample_target_prs))
                pull_summaries = pull_summaries[:sample_target_prs]
            else:
                pull_summaries = sample_pull_summaries(
                    owner=owner,
                    repo=repo,
                    population_size=population_total_prs,
                    target_count=sample_target_prs,
                    token=token,
                    max_retries=args.max_retries,
                    worker_label=worker_label,
                )

            rows = collect_pr_rows(
                owner,
                repo,
                token=token,
                max_retries=args.max_retries,
                pull_summaries=pull_summaries,
                population_total_prs=population_total_prs,
                sample_target_prs=sample_target_prs,
                confidence=args.confidence,
                margin_error=args.margin_error,
                interaction_mode=args.interaction_mode,
                worker_label=worker_label,
                repo_csv_path=repo_csv,
            )
            if rows and repo_csv and not repo_csv.exists():
                write_csv_rows(repo_csv, rows, PR_COLUMNS)
            if repo_done_marker:
                repo_done_marker.parent.mkdir(parents=True, exist_ok=True)
                repo_done_marker.write_text("done\n", encoding="utf-8")
            result = {
                "owner": owner,
                "repo": repo,
                "status": "ok",
                "message": f"rows={len(rows)} sample_target={sample_target_prs} population={population_total_prs}",
            }
        except Exception as exc:  # noqa: BLE001
            result = {"owner": owner, "repo": repo, "status": "error", "message": str(exc)}

        with lock:
            run_log.append(result)
            append_run_log_row(run_log_path, result)
            if result.get("status") == "ok":
                completed_repos.add(slug)
                save_completion_checkpoint_locked()

        return result

    if args.workers <= 1:
        for row in selected_repos:
            _ = process_single(row)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as exe:
            futures = {exe.submit(process_single, row): row for row in selected_repos}
            for fut in concurrent.futures.as_completed(futures):
                try:
                    _ = fut.result()
                except Exception as exc:  # pragma: no cover - defensive
                    print(f"Worker error: {exc}")

    failures = [row for row in run_log if row.get("status") != "ok"]
    print(f"Processed {len(run_log)} repositories | failed={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())