#!/usr/bin/env python3
"""Collect top Java repositories from GitHub Search API.

This script enforces pagination of 10 by default to match Sprint 1 requirements.
It supports checkpointing so interrupted runs can continue from the last page.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://api.github.com/search/repositories"
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
]


@dataclass
class RepoRow:
    owner: str
    repo: str
    full_name: str
    html_url: str
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    language: str
    created_at: str
    pushed_at: str
    default_branch: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "owner": self.owner,
            "repo": self.repo,
            "full_name": self.full_name,
            "html_url": self.html_url,
            "stargazers_count": str(self.stargazers_count),
            "forks_count": str(self.forks_count),
            "open_issues_count": str(self.open_issues_count),
            "language": self.language,
            "created_at": self.created_at,
            "pushed_at": self.pushed_at,
            "default_branch": self.default_branch,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect top Java repos from GitHub")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--target", type=int, default=1000, help="Target number of repos")
    parser.add_argument("--per-page", type=int, default=10, help="GitHub page size")
    parser.add_argument("--checkpoint", default="", help="Optional checkpoint JSON file")
    parser.add_argument("--max-retries", type=int, default=5, help="Retries on API failure")
    parser.add_argument("--sleep", type=float, default=1.0, help="Delay between requests (seconds)")
    return parser.parse_args()


def load_checkpoint(path: Path) -> Dict[str, int]:
    if not path.exists():
        return {"page": 1}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    page = int(data.get("page", 1))
    return {"page": max(1, page)}


def save_checkpoint(path: Path, page: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump({"page": page}, f, indent=2)


def build_request_url(page: int, per_page: int) -> str:
    query = {
        "q": "language:Java",
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
        "page": page,
    }
    return f"{API_URL}?{urlencode(query)}"


def github_get(url: str, token: Optional[str], max_retries: int) -> Dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "lab02s01-collector",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    backoff = 2.0
    for attempt in range(1, max_retries + 1):
        req = Request(url, headers=headers, method="GET")
        try:
            with urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
            return json.loads(body)
        except HTTPError as exc:
            if exc.code in (403, 429, 500, 502, 503, 504) and attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
        except URLError:
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise

    raise RuntimeError("Max retries reached")


def item_to_repo_row(item: Dict) -> RepoRow:
    owner = item.get("owner") or {}
    name = item.get("name", "")
    owner_login = owner.get("login", "")
    return RepoRow(
        owner=owner_login,
        repo=name,
        full_name=item.get("full_name", ""),
        html_url=item.get("html_url", ""),
        stargazers_count=int(item.get("stargazers_count", 0)),
        forks_count=int(item.get("forks_count", 0)),
        open_issues_count=int(item.get("open_issues_count", 0)),
        language=item.get("language") or "",
        created_at=item.get("created_at", ""),
        pushed_at=item.get("pushed_at", ""),
        default_branch=item.get("default_branch", ""),
    )


def read_existing(csv_path: Path) -> Dict[str, RepoRow]:
    repos: Dict[str, RepoRow] = {}
    if not csv_path.exists():
        return repos
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row.get('owner', '')}/{row.get('repo', '')}"
            if not key.strip("/"):
                continue
            repos[key] = RepoRow(
                owner=row.get("owner", ""),
                repo=row.get("repo", ""),
                full_name=row.get("full_name", ""),
                html_url=row.get("html_url", ""),
                stargazers_count=int(row.get("stargazers_count", "0") or 0),
                forks_count=int(row.get("forks_count", "0") or 0),
                open_issues_count=int(row.get("open_issues_count", "0") or 0),
                language=row.get("language", ""),
                created_at=row.get("created_at", ""),
                pushed_at=row.get("pushed_at", ""),
                default_branch=row.get("default_branch", ""),
            )
    return repos


def write_csv(path: Path, repos: Dict[str, RepoRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(repos.values(), key=lambda r: r.stargazers_count, reverse=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DEFAULT_COLUMNS)
        writer.writeheader()
        for repo in ordered:
            writer.writerow(repo.to_dict())


def main() -> int:
    args = parse_args()
    if args.per_page != 10:
        print("Warning: Sprint 1 specifies pagination of 10.", file=sys.stderr)

    output_path = Path(args.output)
    checkpoint_path = Path(args.checkpoint) if args.checkpoint else output_path.with_suffix(".checkpoint.json")
    token = os.getenv("GITHUB_TOKEN", "").strip() or None

    repos = read_existing(output_path)
    checkpoint = load_checkpoint(checkpoint_path)
    page = checkpoint["page"]

    max_pages = max(1, (args.target + args.per_page - 1) // args.per_page)
    while len(repos) < args.target and page <= max_pages:
        url = build_request_url(page=page, per_page=args.per_page)
        payload = github_get(url=url, token=token, max_retries=args.max_retries)
        items: List[Dict] = payload.get("items", [])
        if not items:
            print(f"No results at page {page}. Stopping.")
            break

        for item in items:
            repo = item_to_repo_row(item)
            key = f"{repo.owner}/{repo.repo}"
            repos[key] = repo
            if len(repos) >= args.target:
                break

        write_csv(output_path, repos)
        page += 1
        save_checkpoint(checkpoint_path, page)
        print(f"Collected unique repos: {len(repos)} (next page: {page})")
        time.sleep(args.sleep)

    if len(repos) >= args.target:
        print(f"Done. Collected {len(repos)} repositories.")
        return 0

    print(f"Finished with {len(repos)} repositories (target={args.target}).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
