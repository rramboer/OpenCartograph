"""Minimal GitHub REST API client used by the issue-form workflow scripts.

stdlib-only so workflow scripts don't need extra dependencies installed.
"""
from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

API_BASE = "https://api.github.com"


def _token() -> str:
    return os.environ["GITHUB_TOKEN"]


def _repo() -> str:
    return os.environ["GITHUB_REPOSITORY"]


def request_api(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    *,
    expect_404: bool = False,
) -> Any:
    """Call the GitHub API. Returns parsed JSON, or None for a 404 when expected."""
    data = json.dumps(body).encode() if body is not None else None
    req = request.Request(
        f"{API_BASE}{path}",
        method=method,
        data=data,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "opencartograph-issue-form",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except error.HTTPError as e:
        if expect_404 and e.code == 404:
            return None
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} → {e.code}: {body_text}") from e


def repo_path(suffix: str) -> str:
    return f"/repos/{_repo()}{suffix}"
