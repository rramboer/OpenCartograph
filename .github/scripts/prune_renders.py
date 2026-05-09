#!/usr/bin/env python3
"""Prune `issue-N/` directories on the `renders` branch whose issues closed >N days ago.

Reads from env: MAX_AGE_DAYS (default 30), DRY_RUN ("true"/"false").
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timedelta, timezone

from _gh_api import repo_path, request_api

BRANCH = "renders"

# Safety guard: prune is the only destructive workflow. Refuse to delete more
# than this in a single run so a future bug in path-collection or staleness
# logic can't wipe the entire branch in one commit.
MAX_PRUNE_FILES = 200


def is_truthy(s: str | None) -> bool:
    return (s or "").strip().lower() in {"1", "true", "yes", "on"}


def list_issue_dirs() -> list[tuple[int, str]]:
    """Return (issue_num, dir_path) for each issue-N/ dir on the renders branch."""
    contents = request_api(
        "GET", repo_path(f"/contents?ref={BRANCH}"), expect_404=True
    )
    if not contents:
        return []
    out: list[tuple[int, str]] = []
    for entry in contents:
        if entry.get("type") != "dir":
            continue
        match = re.fullmatch(r"issue-(\d+)", entry["name"])
        if match:
            out.append((int(match.group(1)), entry["path"]))
    return out


def issue_closed_at(num: int) -> datetime | None:
    """Return the issue's closed_at as a UTC datetime, or None to keep its renders.

    Returns None for: open issues, missing closed_at, AND 404 responses.

    Treating 404 as "keep" — not "prune" — because GitHub returns 404 for many
    auth-shape problems (token rotated, SSO expired, scope changed) as well as
    truly-deleted issues. A single auth blip during a scheduled prune must not
    silently delete every render on the branch.
    """
    issue = request_api("GET", repo_path(f"/issues/{num}"), expect_404=True)
    if issue is None:
        print(
            f"WARNING: issue #{num} returned 404; skipping. "
            f"If the issue is truly deleted, prune renders/issue-{num}/ manually.",
            file=sys.stderr,
        )
        return None
    if issue.get("state") != "closed":
        return None
    closed_at = issue.get("closed_at")
    if not closed_at:
        return None
    return datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def collect_paths_under(dir_path: str) -> list[str]:
    """Recursively list all blob paths under dir_path on the renders branch.

    Subdirectories of a known-existing dir should not 404; if one does, raise so
    the prune run aborts rather than silently skipping a partial subtree (which
    would leave the dir half-pruned and the caller none the wiser).
    """
    paths: list[str] = []
    stack = [dir_path]
    while stack:
        current = stack.pop()
        entries = request_api("GET", repo_path(f"/contents/{current}?ref={BRANCH}"))
        if not entries:
            continue
        for entry in entries:
            if entry["type"] == "dir":
                stack.append(entry["path"])
            elif entry["type"] == "file":
                paths.append(entry["path"])
    return paths


def commit_deletions(paths_to_delete: list[str]) -> None:
    """Build a new tree omitting the given paths and push a single commit."""
    if len(paths_to_delete) > MAX_PRUNE_FILES:
        raise RuntimeError(
            f"Refusing to delete {len(paths_to_delete)} files in one prune run "
            f"(safety limit: {MAX_PRUNE_FILES}). Investigate before raising the limit."
        )

    branch_ref = request_api("GET", repo_path(f"/git/refs/heads/{BRANCH}"))
    head_sha = branch_ref["object"]["sha"]
    head_commit = request_api("GET", repo_path(f"/git/commits/{head_sha}"))
    base_tree_sha = head_commit["tree"]["sha"]

    # null sha on a base_tree entry deletes the path (GitHub Git Data API)
    tree_entries = [
        {"path": p, "mode": "100644", "type": "blob", "sha": None}
        for p in paths_to_delete
    ]

    new_tree = request_api(
        "POST",
        repo_path("/git/trees"),
        {"base_tree": base_tree_sha, "tree": tree_entries},
    )

    new_commit = request_api(
        "POST",
        repo_path("/git/commits"),
        {
            "message": f"Prune {len(paths_to_delete)} stale render file(s)",
            "tree": new_tree["sha"],
            "parents": [head_sha],
        },
    )

    request_api(
        "PATCH",
        repo_path(f"/git/refs/heads/{BRANCH}"),
        {"sha": new_commit["sha"], "force": False},
    )


def main() -> int:
    max_age = int(os.environ.get("MAX_AGE_DAYS", "30") or "30")
    dry_run = is_truthy(os.environ.get("DRY_RUN", "true"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age)

    print(f"Prune cutoff: issues closed before {cutoff.isoformat()} (>{max_age} days)")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}\n")

    if request_api("GET", repo_path(f"/branches/{BRANCH}"), expect_404=True) is None:
        print(f"Branch '{BRANCH}' does not exist — nothing to prune.")
        return 0

    issue_dirs = list_issue_dirs()
    if not issue_dirs:
        print("No issue-* directories on the renders branch.")
        return 0

    to_delete: list[str] = []
    for num, path in sorted(issue_dirs):
        closed_at = issue_closed_at(num)
        if closed_at is None:
            print(f"  keep    issue-{num}: open or unknown")
            continue
        if closed_at >= cutoff:
            age = datetime.now(timezone.utc) - closed_at
            print(f"  keep    issue-{num}: closed {age.days}d ago")
            continue
        files = collect_paths_under(path)
        age = datetime.now(timezone.utc) - closed_at
        print(f"  prune   issue-{num}: closed {age.days}d ago ({len(files)} files)")
        to_delete.extend(files)

    print()
    if not to_delete:
        print("Nothing to prune.")
        return 0

    if dry_run:
        print(f"DRY RUN: would delete {len(to_delete)} file(s).")
        return 0

    commit_deletions(to_delete)
    print(f"Pruned {len(to_delete)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
