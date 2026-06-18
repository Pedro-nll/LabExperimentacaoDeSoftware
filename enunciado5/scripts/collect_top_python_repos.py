#!/usr/bin/env python3
"""Collect the 100 most-starred public Python repositories from GitHub."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

from lab05_common import (
    github_token,
    load_checkpoint,
    read_csv_rows,
    rest_json,
    save_checkpoint,
    safe_get,
    write_csv_rows,
)

REPO_COLUMNS = [
    "rank",
    "owner",
    "repo",
    "full_name",
    "html_url",
    "description",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "language",
    "created_at",
    "updated_at",
    "pushed_at",
    "default_branch",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect top Python GitHub repositories for Lab 05")
    parser.add_argument("--output", default="enunciado5/data/top_python_repos.csv", help="Output CSV")
    parser.add_argument("--checkpoint", default="", help="Checkpoint JSON path")
    parser.add_argument("--target", type=int, default=100, help="Number of repositories to collect")
    parser.add_argument("--per-page", type=int, default=100, help="GitHub search page size")
    parser.add_argument("--max-retries", type=int, default=5, help="API retry count")
    return parser.parse_args()


def repo_row(item: Dict[str, Any], rank: int) -> Dict[str, Any]:
    owner = item.get("owner") or {}
    return {
        "rank": rank,
        "owner": safe_get(owner, "login"),
        "repo": safe_get(item, "name"),
        "full_name": safe_get(item, "full_name"),
        "html_url": safe_get(item, "html_url"),
        "description": safe_get(item, "description"),
        "stargazers_count": safe_get(item, "stargazers_count", 0),
        "forks_count": safe_get(item, "forks_count", 0),
        "open_issues_count": safe_get(item, "open_issues_count", 0),
        "language": safe_get(item, "language"),
        "created_at": safe_get(item, "created_at"),
        "updated_at": safe_get(item, "updated_at"),
        "pushed_at": safe_get(item, "pushed_at"),
        "default_branch": safe_get(item, "default_branch"),
    }


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    checkpoint_path = Path(args.checkpoint) if args.checkpoint else output_path.with_suffix(".checkpoint.json")
    token = github_token("rest")

    existing_rows = read_csv_rows(output_path)
    selected: Dict[str, Dict[str, Any]] = {row.get("full_name", ""): row for row in existing_rows if row.get("full_name")}
    checkpoint = load_checkpoint(checkpoint_path, {"page": 1})
    page = int(checkpoint.get("page", 1) or 1)
    max_pages = max(1, (args.target + args.per_page - 1) // args.per_page)

    print(f"[repos] target={args.target} language=Python output={output_path}")
    while len(selected) < args.target and page <= max_pages:
        result, payload = rest_json(
            "/search/repositories",
            {
                "q": "language:Python stars:>0",
                "sort": "stars",
                "order": "desc",
                "per_page": args.per_page,
                "page": page,
            },
            token=token,
            max_retries=args.max_retries,
        )
        if result.status != 200 or not isinstance(payload, dict):
            print(f"[repos] failed page={page} status={result.status} error={result.error}")
            return 1

        items = payload.get("items", [])
        if not isinstance(items, list) or not items:
            print(f"[repos] no items returned at page={page}")
            break

        for item in items:
            if len(selected) >= args.target:
                break
            full_name = str(item.get("full_name", "") or "")
            if not full_name or full_name in selected:
                continue
            rank = len(selected) + 1
            selected[full_name] = repo_row(item, rank)
            progress = len(selected) / args.target * 100.0
            print(f"[repos] {len(selected):03d}/{args.target} ({progress:5.1f}%) selected {full_name}")

        rows: List[Dict[str, Any]] = sorted(selected.values(), key=lambda row: int(row.get("rank", 0) or 0))
        write_csv_rows(output_path, rows, REPO_COLUMNS)
        page += 1
        save_checkpoint(checkpoint_path, {"page": page, "selected": len(selected)})
        print(f"[repos] checkpoint saved page={page} selected={len(selected)}")

    print(f"[repos] finished selected={len(selected)} output={output_path}")
    return 0 if len(selected) >= args.target else 1


if __name__ == "__main__":
    raise SystemExit(main())
