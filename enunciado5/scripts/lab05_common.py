#!/usr/bin/env python3
"""Shared helpers for Lab 05 REST vs GraphQL experiment."""

from __future__ import annotations

import csv
import json
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_VERSION = "2022-11-28"
GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"


@dataclass
class HttpResult:
    status: int
    elapsed_ms: float
    response_bytes: int
    body_text: str
    error: str = ""
    attempts: int = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def github_token(kind: str) -> Optional[str]:
    if kind == "rest":
        token = os.getenv("GITHUB_REST_TOKEN", "").strip()
    elif kind == "graphql":
        token = os.getenv("GITHUB_GRAPHQL_TOKEN", "").strip()
    else:
        token = ""
    return token or os.getenv("GITHUB_TOKEN", "").strip() or None


def token_label(kind: str) -> str:
    specific = "GITHUB_REST_TOKEN" if kind == "rest" else "GITHUB_GRAPHQL_TOKEN"
    if os.getenv(specific, "").strip():
        return specific
    if os.getenv("GITHUB_TOKEN", "").strip():
        return "GITHUB_TOKEN"
    return "none"


def build_headers(token: Optional[str], *, graphql: bool = False) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "lab05-rest-graphql-experiment",
    }
    if graphql:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def build_url(path: str, query: Optional[Dict[str, Any]] = None) -> str:
    query_string = f"?{urlencode(query)}" if query else ""
    return f"{GITHUB_API}{path}{query_string}"


def load_checkpoint(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return dict(default)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    result = dict(default)
    if isinstance(data, dict):
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
        return [dict(row) for row in csv.DictReader(f)]


def write_csv_rows(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_csv_row(path: Path, row: Dict[str, Any], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _sleep_from_rate_limit(headers: Any) -> Optional[int]:
    if headers is None:
        return None
    remaining = str(headers.get("X-RateLimit-Remaining", "")).strip()
    reset = str(headers.get("X-RateLimit-Reset", "")).strip()
    if remaining != "0" or not reset:
        return None
    try:
        reset_epoch = int(reset)
    except ValueError:
        return None
    return max(1, reset_epoch - int(time.time()) + 1)


def request_raw(
    url: str,
    *,
    method: str = "GET",
    data: Optional[bytes] = None,
    token: Optional[str],
    graphql: bool = False,
    timeout: int = 60,
    max_retries: int = 5,
) -> HttpResult:
    headers = build_headers(token, graphql=graphql)
    backoff = 2.0
    last_error = ""

    for attempt in range(1, max_retries + 1):
        request = Request(url, data=data, headers=headers, method=method)
        start = time.perf_counter()
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                text = raw.decode("utf-8", errors="replace")
                return HttpResult(
                    status=int(response.status),
                    elapsed_ms=elapsed_ms,
                    response_bytes=len(raw),
                    body_text=text,
                    attempts=attempt,
                )
        except HTTPError as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            raw = exc.read() if hasattr(exc, "read") else b""
            last_error = f"HTTP {exc.code}"
            if exc.code in (403, 408, 409, 425, 429, 500, 502, 503, 504) and attempt < max_retries:
                sleep_for = _sleep_from_rate_limit(exc.headers)
                if sleep_for is None:
                    sleep_for = backoff
                    backoff *= 2
                print(f"[retry] {last_error} for {url}; sleeping {sleep_for}s before attempt {attempt + 1}/{max_retries}")
                time.sleep(sleep_for)
                continue
            return HttpResult(
                status=int(exc.code),
                elapsed_ms=elapsed_ms,
                response_bytes=len(raw),
                body_text=raw.decode("utf-8", errors="replace"),
                error=last_error,
                attempts=attempt,
            )
        except (TimeoutError, URLError) as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            last_error = type(exc).__name__
            if attempt < max_retries:
                print(f"[retry] {last_error} for {url}; sleeping {backoff}s before attempt {attempt + 1}/{max_retries}")
                time.sleep(backoff)
                backoff *= 2
                continue
            return HttpResult(
                status=0,
                elapsed_ms=elapsed_ms,
                response_bytes=0,
                body_text="",
                error=last_error,
                attempts=attempt,
            )

    return HttpResult(status=0, elapsed_ms=0.0, response_bytes=0, body_text="", error=last_error, attempts=max_retries)


def rest_json(path: str, query: Optional[Dict[str, Any]], *, token: Optional[str], max_retries: int) -> Tuple[HttpResult, Any]:
    result = request_raw(build_url(path, query), token=token, max_retries=max_retries)
    try:
        payload = json.loads(result.body_text) if result.body_text else None
    except json.JSONDecodeError:
        payload = None
        if not result.error:
            result.error = "invalid_json"
    return result, payload


def graphql_raw(query: str, variables: Dict[str, Any], *, token: Optional[str], max_retries: int) -> Tuple[HttpResult, Any]:
    body = json.dumps({"query": query, "variables": variables}, separators=(",", ":")).encode("utf-8")
    result = request_raw(
        GITHUB_GRAPHQL,
        method="POST",
        data=body,
        token=token,
        graphql=True,
        max_retries=max_retries,
    )
    try:
        payload = json.loads(result.body_text) if result.body_text else None
    except json.JSONDecodeError:
        payload = None
        if not result.error:
            result.error = "invalid_json"
    if isinstance(payload, dict) and payload.get("errors") and not result.error:
        message = str(payload["errors"][0].get("message", "graphql_error"))
        result.error = f"GraphQL error: {message}"
    return result, payload


def deterministic_api_order(repository: str, scenario_id: str, run_number: int) -> List[str]:
    order = ["REST", "GraphQL"]
    rng = random.Random(f"{repository}:{scenario_id}:{run_number}")
    rng.shuffle(order)
    return order


def safe_get(mapping: Dict[str, Any], key: str, default: Any = "") -> Any:
    value = mapping.get(key, default)
    return default if value is None else value
