#!/usr/bin/env python3
"""Collect pull request metrics using GitHub GraphQL API (optimized)."""

from __future__ import annotations

import argparse
import csv
import concurrent.futures
import threading
import math
from datetime import datetime, timezone
from pathlib import Path
import random
import time
from typing import Any, Dict, List, Optional

from github_cr import (
    format_iso8601,
    github_token,
    graphql_fetch_pr_detail,
    graphql_fetch_prs_batch,
    graphql_rate_limit_status,
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
    parser = argparse.ArgumentParser(description="Collect code review PR metrics via GraphQL (optimized)")
    parser.add_argument("--repos-csv", required=True, help="CSV with selected repositories")
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for per-repo PR CSVs (reuse the same canonical output tree)",
    )
    parser.add_argument(
        "--repo-limit",
        type=int,
        default=0,
        help="How many repositories to process (0 = all remaining)",
    )
    parser.add_argument("--pr-limit", type=int, default=10, help="Maximum PRs to collect per repository (default 10 for 8-hour collection)")
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
    parser.add_argument("--max-retries", type=int, default=5, help="API retries")
    parser.add_argument("--checkpoint", default="", help="Checkpoint JSON file")
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of repo-level workers to run in parallel (default 4 for 8-hour target; use --workers=1 to minimize rate-limit pressure)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of PRs to fetch per GraphQL query (default 100, max 100)",
    )
    parser.add_argument(
        "--preflight-min-remaining",
        type=int,
        default=20,
        help="Minimum GraphQL remaining quota required to start (default 20)",
    )
    parser.add_argument(
        "--preflight-wait-until-reset",
        action="store_true",
        help="Wait for the rate-limit reset instead of exiting when quota is below the threshold",
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


def sample_pr_indexes(population_size: int, target_count: int, owner: str, repo: str) -> List[int]:
    """Generate deterministic sample of PR indexes using seeded RNG."""
    if target_count <= 0 or population_size <= 0:
        return []
    
    sample_size = min(target_count, population_size)
    rng = random.Random(f"{owner}/{repo}:{population_size}:{sample_size}")
    return sorted(rng.sample(range(population_size), k=sample_size))


def log_repo_event(worker_label: str, message: str) -> None:
    prefix = f"[{worker_label}] " if worker_label else ""
    print(f"{prefix}{message}")


def preflight_rate_limit(token: Optional[str], min_remaining: int, wait_until_reset: bool, max_retries: int) -> bool:
    status = graphql_rate_limit_status(token=token, max_retries=1)
    remaining = safe_int(status.get("remaining"), default=-1)
    limit = safe_int(status.get("limit"), default=-1)
    reset_at = str(status.get("resetAt", "") or "")
    cost = safe_int(status.get("cost"), default=-1)
    print(
        "[preflight] GraphQL rate limit "
        f"remaining={remaining} limit={limit} cost={cost} resetAt={reset_at or 'unknown'}"
    )

    if remaining >= min_remaining:
        print(f"[preflight] quota is sufficient (threshold={min_remaining})")
        return True

    message = (
        f"[preflight] quota below threshold: remaining={remaining} < {min_remaining}; "
        f"this run would likely stall or fail"
    )
    if not wait_until_reset:
        print(message)
        return False

    if not reset_at:
        print(message)
        print("[preflight] missing resetAt; cannot wait safely")
        return False

    try:
        reset_dt = parse_iso8601(reset_at)
    except ValueError:
        print(message)
        print(f"[preflight] invalid resetAt value: {reset_at}")
        return False

    wait_seconds = max(1, int((reset_dt - datetime.now(timezone.utc)).total_seconds()) + 1)
    print(f"[preflight] waiting {wait_seconds}s for rate limit reset at {reset_at}")
    time.sleep(wait_seconds)
    return True


def repo_slug(owner: str, repo: str) -> str:
    return f"{owner}__{repo}"


def append_csv_row(path: Path, row: Dict[str, Any], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def append_run_log_row(path: Path, row: Dict[str, Any]) -> None:
    append_csv_row(path, row, RUN_LOG_COLUMNS)


def extract_pr_row(
    pr_data: Dict[str, Any],
    owner: str,
    repo: str,
    population_total_prs: int,
    sample_target_prs: int,
    confidence: int,
    margin_error: float,
) -> Dict[str, str]:
    """Convert GraphQL PR data to CSV row format."""
    number = safe_int(pr_data.get("number"), default=0)
    
    created_at = str(pr_data.get("createdAt", "") or "")
    updated_at = str(pr_data.get("updatedAt", "") or "")
    merged_at = str(pr_data.get("mergedAt", "") or "")
    
    # Calculate last activity from reviews
    last_activity_candidates = [updated_at]
    reviews = (pr_data.get("reviews") or {}).get("nodes", []) or []
    for review in reviews:
        submitted = review.get("submittedAt")
        if submitted:
            last_activity_candidates.append(submitted)
    last_activity = max_datetime(last_activity_candidates)
    
    created_dt = parse_iso8601(created_at) if created_at else None
    analysis_hours = 0.0
    if created_dt and last_activity:
        delta = last_activity - created_dt
        analysis_hours = delta.total_seconds() / 3600.0
    
    # Review data
    review_states = [str(review.get("state", "") or "") for review in reviews]
    human_reviewers = [
        str((review.get("author") or {}).get("login", ""))
        for review in reviews
        if is_human_login(str((review.get("author") or {}).get("login", "")))
    ]
    human_review_count = len(human_reviewers)
    
    # Participants
    participants = {str((pr_data.get("author") or {}).get("login", "")): None}
    for reviewer in human_reviewers:
        if reviewer:
            participants[reviewer] = None
    
    # Feedback
    final_state = "NO_REVIEW"
    if human_review_count > 0:
        latest_review = max(
            (r for r in reviews if is_human_login(str(r.get("author", {}).get("login", "")))),
            key=lambda x: x.get("submittedAt", ""),
            default=None,
        )
        if latest_review:
            final_state = str(latest_review.get("state", "NO_REVIEW") or "NO_REVIEW")
    
    body_text = str(pr_data.get("bodyText", "") or "")
    
    return {
        "owner": owner,
        "repo": repo,
        "full_name": f"{owner}/{repo}",
        "pr_number": str(number),
        "html_url": f"https://github.com/{owner}/{repo}/pull/{number}",
        "title": str(pr_data.get("title", "") or ""),
        "state": str(pr_data.get("state", "") or ""),
        "created_at": created_at,
        "updated_at": updated_at,
        "last_activity_at": format_iso8601(last_activity) if last_activity else "",
        "analysis_hours": f"{analysis_hours:.6f}",
        "body_chars": str(len(body_text)),
        "changed_files": str(safe_int(pr_data.get("changedFiles"), default=0)),
        "additions": str(safe_int(pr_data.get("additions"), default=0)),
        "deletions": str(safe_int(pr_data.get("deletions"), default=0)),
        "total_changes": str(
            safe_int(pr_data.get("additions"), default=0) + safe_int(pr_data.get("deletions"), default=0)
        ),
        "issue_comments": str(pr_data.get("comments", {}).get("totalCount", 0)),
        "review_comments": "0",  # GraphQL doesn't easily expose this separately
        "total_comments": str(pr_data.get("comments", {}).get("totalCount", 0)),
        "human_review_count": str(human_review_count),
        "participant_count": str(len(participants)),
        "final_review_state": final_state,
        "final_feedback": normalize_feedback(final_state),
        "review_states": "|".join(review_states),
        "review_participants": "|".join(human_reviewers),
        "has_human_review": "yes" if human_review_count > 0 else "no",
        "author_login": str(pr_data.get("author", {}).get("login", "") or ""),
        "merged_at": merged_at,
        "population_total_prs": str(max(0, population_total_prs)),
        "sample_target_prs": str(max(0, sample_target_prs)),
        "sampling_confidence": str(confidence),
        "sampling_margin_error": f"{margin_error:.6f}",
    }


def collect_sampled_pr_numbers(
    owner: str,
    repo: str,
    population_total_prs: int,
    sample_target_prs: int,
    token: Optional[str],
    max_retries: int,
    batch_size: int,
    worker_label: str = "",
) -> List[int]:
    sample_indexes = sample_pr_indexes(population_total_prs, sample_target_prs, owner, repo)
    if not sample_indexes:
        return []

    wanted_indexes = set(sample_indexes)
    selected_numbers: List[int] = []
    after_cursor = None
    global_index = 0
    highest_index = sample_indexes[-1]
    total_pages = max(1, int(math.ceil(population_total_prs / float(max(1, batch_size)))))
    pages_seen = 0

    log_repo_event(worker_label, f"Sampling {len(sample_indexes)} PRs from population={population_total_prs} using lightweight page scans")
    while global_index <= highest_index:
        pages_seen += 1
        batch = graphql_fetch_prs_batch(
            owner,
            repo,
            first=min(max(1, batch_size), 100),
            after=after_cursor,
            token=token,
            max_retries=max_retries,
        )
        nodes = batch.get("nodes") or []
        if not nodes:
            log_repo_event(worker_label, f"Page scan stopped early at page {pages_seen}/{total_pages}; no nodes returned")
            break
        log_repo_event(worker_label, f"Scanned page {pages_seen}/{total_pages} with {len(nodes)} PR headers")

        for node in nodes:
            if global_index in wanted_indexes:
                number = safe_int(node.get("number"), default=0)
                if number > 0:
                    selected_numbers.append(number)
            global_index += 1
            if global_index > highest_index:
                break

        page_info = batch.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after_cursor = page_info.get("endCursor")

        if pages_seen % 10 == 0:
            log_repo_event(worker_label, f"Page scan progress: sampled={len(selected_numbers)}/{len(sample_indexes)} global_index={global_index}/{population_total_prs}")

    return selected_numbers[:sample_target_prs]


def main() -> int:
    args = parse_args()
    token = github_token()
    start_time = time.time()

    if not preflight_rate_limit(
        token=token,
        min_remaining=max(0, args.preflight_min_remaining),
        wait_until_reset=args.preflight_wait_until_reset,
        max_retries=args.max_retries,
    ):
        return 2

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
    
    # Sort repos by population size (ascending) to complete small ones first for faster feedback
    selected_repos = sorted(selected_repos, key=lambda r: safe_int(r.get("total_prs", 0), default=0))

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

        if (owner, repo) in {(r.get("owner"), r.get("repo")) for r in run_log if r.get("status") == "ok"} and repo_csv and repo_csv.exists():
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
                sample_target_prs = min(args.pr_limit, max(1, population_total_prs)) if population_total_prs > 0 else args.pr_limit
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
                log_repo_event(worker_label, f"Population unknown for {slug}; falling back to first page only")
            
            rows: List[Dict[str, str]] = []
            selected_numbers = []
            if population_total_prs > 0:
                selected_numbers = collect_sampled_pr_numbers(
                    owner=owner,
                    repo=repo,
                    population_total_prs=population_total_prs,
                    sample_target_prs=sample_target_prs,
                    token=token,
                    max_retries=args.max_retries,
                    batch_size=args.batch_size,
                    worker_label=worker_label,
                )
            elif args.pr_limit > 0:
                selected_numbers = [1]

            if not selected_numbers:
                log_repo_event(worker_label, f"No sampled PR numbers resolved for {slug}")
            else:
                log_repo_event(worker_label, f"Fetching full detail for {len(selected_numbers)} sampled PRs")

            for index, pr_number in enumerate(selected_numbers, 1):
                try:
                    detail = graphql_fetch_pr_detail(
                        owner,
                        repo,
                        pr_number,
                        token=token,
                        max_retries=args.max_retries,
                    )
                    if not detail:
                        log_repo_event(worker_label, f"Skipping PR #{pr_number}: empty detail payload")
                        continue
                    row = extract_pr_row(detail, owner, repo, population_total_prs, sample_target_prs, args.confidence, args.margin_error)
                    rows.append(row)
                    if repo_csv:
                        append_csv_row(repo_csv, row, PR_COLUMNS)
                    if index % 10 == 0 or index == len(selected_numbers):
                        log_repo_event(worker_label, f"Saved {index}/{len(selected_numbers)} sampled PRs to prs.csv")
                except Exception as detail_exc:  # noqa: BLE001
                    log_repo_event(worker_label, f"PR #{pr_number} detail failed: {detail_exc}")
                    continue

            result = {
                "owner": owner,
                "repo": repo,
                "status": "ok",
                "message": f"rows={len(rows)} sample_target={sample_target_prs} population={population_total_prs}",
            }
            
            if repo_done_marker:
                repo_done_marker.parent.mkdir(parents=True, exist_ok=True)
                repo_done_marker.write_text("done\n", encoding="utf-8")
                
        except Exception as exc:  # noqa: BLE001
            result = {"owner": owner, "repo": repo, "status": "error", "message": str(exc)}

        with lock:
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
                except Exception as exc:  # pragma: no cover
                    print(f"Worker error: {exc}")

    failures = [row for row in run_log if row.get("status") != "ok"]
    elapsed_sec = time.time() - start_time
    elapsed_min = elapsed_sec / 60
    elapsed_hr = elapsed_min / 60
    
    print()
    print("=" * 60)
    print(f"COLLECTION SUMMARY")
    print(f"  Total time: {elapsed_sec:.0f}s = {elapsed_min:.1f}m = {elapsed_hr:.2f}h")
    print(f"  Processed: {len(run_log)} repositories")
    print(f"  Succeeded: {len(run_log) - len(failures)}")
    print(f"  Failed: {len(failures)}")
    if len(run_log) > 0:
        avg_time = elapsed_sec / len(run_log)
        print(f"  Avg time/repo: {avg_time:.1f}s")
    print("=" * 60)
    
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
