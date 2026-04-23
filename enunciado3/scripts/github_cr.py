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
                reset_value = exc.headers.get("X-RateLimit-Reset")
                remaining = exc.headers.get("X-RateLimit-Remaining")
                if remaining == "0" and reset_value:
                    reset_time = int(reset_value)
                    sleep_for = max(1, reset_time - int(time.time()) + 1)
                else:
                    sleep_for = backoff
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
