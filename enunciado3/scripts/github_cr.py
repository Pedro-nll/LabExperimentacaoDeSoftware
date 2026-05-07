#!/usr/bin/env python3
"""Shared helpers for the GitHub code review pipeline."""

from __future__ import annotations

import csv
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_VERSION = "2022-11-28"
GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"


def github_token() -> Optional[str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    return token or None


def build_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "lab03-code-review-pipeline",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def graphql_rate_limit_status(token: Optional[str] = None, max_retries: int = 5) -> Dict[str, Any]:
        """Return the current GraphQL rate-limit status."""
        query = """
        query RateLimitStatus {
            rateLimit {
                limit
                cost
                remaining
                resetAt
            }
        }
        """
        result = github_graphql_query(query, token=token, max_retries=max_retries)
        try:
                return result.get("data", {}).get("rateLimit", {}) or {}
        except (KeyError, TypeError):
                return {}


def _rate_limit_sleep_seconds(headers: Any) -> Optional[int]:
    if headers is None:
        return None
    try:
        remaining = str(headers.get("X-RateLimit-Remaining", "")).strip()
        reset_value = str(headers.get("X-RateLimit-Reset", "")).strip()
    except Exception:
        return None
    if remaining != "0" or not reset_value:
        return None
    try:
        reset_time = int(reset_value)
    except ValueError:
        return None
    return max(1, reset_time - int(time.time()) + 1)


def _log_rate_limit_wait(source: str, sleep_for: int, attempt: int, max_retries: int, detail: str) -> None:
    reset_in = f"{sleep_for}s"
    print(f"[{source}] rate limit hit ({detail}); sleeping {reset_in} before retry {attempt + 1}/{max_retries}")


def github_get_json(url: str, token: Optional[str] = None, max_retries: int = 5) -> Dict[str, Any]:
    headers = build_headers(token)
    backoff = 2.0
    for attempt in range(1, max_retries + 1):
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload)
        except HTTPError as exc:
            if exc.code in (403, 408, 409, 425, 429, 500, 502, 503, 504) and attempt < max_retries:
                sleep_for = _rate_limit_sleep_seconds(exc.headers)
                if sleep_for is not None:
                    _log_rate_limit_wait("rest", sleep_for, attempt, max_retries, f"HTTP {exc.code}")
                else:
                    sleep_for = backoff
                    print(f"[rest] transient HTTP {exc.code}; sleeping {sleep_for}s before retry {attempt + 1}/{max_retries}")
                    backoff *= 2
                time.sleep(sleep_for)
                continue
            raise
        except URLError:
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise

    raise RuntimeError(f"Max retries reached for {url}")


def build_url(path: str, query: Optional[Dict[str, Any]] = None) -> str:
    query_string = f"?{urlencode(query)}" if query else ""
    return f"{GITHUB_API}{path}{query_string}"


def parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def format_iso8601(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
        if not math.isfinite(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def is_human_login(login: str) -> bool:
    return bool(login) and "[bot]" not in login.lower()


def load_checkpoint(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return dict(default)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    result = dict(default)
    result.update(data)
    return result


def save_checkpoint(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def write_csv_rows(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def max_datetime(values: Iterable[Optional[str]]) -> Optional[datetime]:
    parsed: List[datetime] = []
    for value in values:
        if not value:
            continue
        try:
            parsed.append(parse_iso8601(value))
        except ValueError:
            continue
    return max(parsed) if parsed else None


def normalize_feedback(state: str) -> str:
    normalized = (state or "").strip().upper()
    if normalized == "APPROVED":
        return "positive"
    if normalized == "CHANGES_REQUESTED":
        return "negative"
    if normalized == "COMMENTED":
        return "neutral"
    if normalized == "DISMISSED":
        return "dismissed"
    if normalized == "NO_REVIEW":
        return "no_review"
    return normalized.lower() or "unknown"


def github_graphql_query(query: str, variables: Optional[Dict[str, Any]] = None, token: Optional[str] = None, max_retries: int = 5) -> Dict[str, Any]:
    """Execute a GraphQL query against GitHub API."""
    headers = build_headers(token)
    headers["Content-Type"] = "application/json"
    backoff = 2.0
    payload_dict = {"query": query}
    if variables:
        payload_dict["variables"] = variables
    payload = json.dumps(payload_dict).encode("utf-8")
    
    for attempt in range(1, max_retries + 1):
        request = Request(GITHUB_GRAPHQL, data=payload, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=60) as response:
                response_data = response.read().decode("utf-8")
            result = json.loads(response_data)
            # Check for GraphQL errors even on 200 status
            if "errors" in result:
                errors = result.get("errors", [])
                error_msg = str(errors[0].get("message", "")) if errors else ""
                rate_limit_block = "API rate limit" in error_msg or "rate limit exceeded" in error_msg.lower()
                if rate_limit_block and attempt < max_retries:
                    rate_limit = result.get("data", {}).get("rateLimit", {}) if isinstance(result.get("data"), dict) else {}
                    reset_at = str(rate_limit.get("resetAt", "") or "")
                    sleep_for = None
                    if reset_at:
                        try:
                            reset_dt = parse_iso8601(reset_at)
                            sleep_for = max(1, int((reset_dt - datetime.now(timezone.utc)).total_seconds()) + 1)
                        except ValueError:
                            sleep_for = None
                    if sleep_for is None:
                        sleep_for = backoff
                        backoff *= 2
                    remaining = rate_limit.get("remaining", "?") if isinstance(rate_limit, dict) else "?"
                    print(f"[graphql] rate limit hit (remaining={remaining}, resetAt={reset_at or 'unknown'}); sleeping {sleep_for}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(sleep_for)
                    continue
                raise RuntimeError(f"GraphQL error: {error_msg}")
            rate_limit = result.get("data", {}).get("rateLimit") if isinstance(result.get("data"), dict) else None
            if isinstance(rate_limit, dict):
                remaining = rate_limit.get("remaining", "?")
                reset_at = rate_limit.get("resetAt", "")
                cost = rate_limit.get("cost", "?")
                if attempt == 1 or str(remaining) in {"0", "1", "2", "3", "4", "5"}:
                    print(f"[graphql] rateLimit remaining={remaining} cost={cost} resetAt={reset_at}")
            return result
        except HTTPError as exc:
            if exc.code in (403, 408, 409, 425, 429, 500, 502, 503, 504) and attempt < max_retries:
                sleep_for = _rate_limit_sleep_seconds(exc.headers)
                if sleep_for is not None:
                    remaining = exc.headers.get("X-RateLimit-Remaining", "?")
                    reset_at = exc.headers.get("X-RateLimit-Reset", "?")
                    print(f"[graphql] HTTP {exc.code} rate limited (remaining={remaining}, reset={reset_at}); sleeping {sleep_for}s before retry {attempt + 1}/{max_retries}")
                else:
                    sleep_for = backoff
                    print(f"[graphql] transient HTTP {exc.code}; sleeping {sleep_for}s before retry {attempt + 1}/{max_retries}")
                    backoff *= 2
                time.sleep(sleep_for)
                continue
            raise
        except URLError:
            if attempt < max_retries:
                print(f"[graphql] network error; sleeping {backoff}s before retry {attempt + 1}/{max_retries}")
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    
    raise RuntimeError("Max retries reached for GraphQL query")


def graphql_fetch_prs_batch(
        owner: str,
        repo: str,
        first: int = 20,
        after: Optional[str] = None,
        token: Optional[str] = None,
        max_retries: int = 5,
) -> Dict[str, Any]:
        """Fetch a batch of lightweight PR nodes using GraphQL.

        This query is intentionally narrow so the collector can scan repository pages
        cheaply, then fetch full PR details only for sampled PRs.
        """
        query = """
        query GetRepositoryPRs($owner: String!, $repo: String!, $after: String, $first: Int!) {
            rateLimit {
                cost
                remaining
                resetAt
            }
            repository(owner: $owner, name: $repo) {
                pullRequests(first: $first, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        number
                        title
                        state
                        createdAt
                        updatedAt
                        author {
                            login
                        }
                    }
                }
            }
        }
        """

        variables = {
                "owner": owner,
                "repo": repo,
                "first": first,
                "after": after,
        }

        result = github_graphql_query(query, variables, token=token, max_retries=max_retries)

        try:
                prs = result.get("data", {}).get("repository", {}).get("pullRequests", {})
                return prs
        except (KeyError, TypeError):
                return {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}


def graphql_fetch_pr_detail(
        owner: str,
        repo: str,
        number: int,
        token: Optional[str] = None,
        max_retries: int = 5,
) -> Dict[str, Any]:
        """Fetch a single PR with full detail for the final row extraction."""
        query = """
        query GetRepositoryPRDetail($owner: String!, $repo: String!, $number: Int!) {
            rateLimit {
                cost
                remaining
                resetAt
            }
            repository(owner: $owner, name: $repo) {
                pullRequest(number: $number) {
                    number
                    title
                    state
                    createdAt
                    updatedAt
                    bodyText
                    changedFiles
                    additions
                    deletions
                    comments {
                        totalCount
                    }
                    reviews(first: 100) {
                        nodes {
                            state
                            submittedAt
                            author {
                                login
                            }
                        }
                    }
                    author {
                        login
                    }
                    mergedAt
                }
            }
        }
        """

        variables = {
                "owner": owner,
                "repo": repo,
                "number": number,
        }
        result = github_graphql_query(query, variables, token=token, max_retries=max_retries)
        try:
                return result.get("data", {}).get("repository", {}).get("pullRequest") or {}
        except (KeyError, TypeError):
                return {}
