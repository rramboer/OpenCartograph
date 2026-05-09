#!/usr/bin/env python3
"""Upload a rendered PNG to the orphan `renders` branch via the Contents API.

Reads from env: ISSUE_NUMBER, RENDER_PATH (plus GITHUB_TOKEN/GITHUB_REPOSITORY).
Writes path=<dest-path-on-renders-branch> to $GITHUB_OUTPUT.
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

from _gh_api import repo_path, request_api

BRANCH = "renders"


def ensure_renders_branch() -> None:
    if request_api("GET", repo_path(f"/branches/{BRANCH}"), expect_404=True) is not None:
        return

    print(f"Creating orphan branch '{BRANCH}'...", flush=True)
    empty_tree = request_api("POST", repo_path("/git/trees"), {"tree": []})
    init_commit = request_api(
        "POST",
        repo_path("/git/commits"),
        {
            "message": "Initialize renders branch",
            "tree": empty_tree["sha"],
            "parents": [],
        },
    )
    request_api(
        "POST",
        repo_path("/git/refs"),
        {"ref": f"refs/heads/{BRANCH}", "sha": init_commit["sha"]},
    )


def main() -> int:
    issue_num = os.environ["ISSUE_NUMBER"]
    render_path = Path(os.environ["RENDER_PATH"])
    if not render_path.is_file():
        print(f"ERROR: render not found: {render_path}", file=sys.stderr)
        return 1

    ensure_renders_branch()

    dest = f"issue-{issue_num}/{render_path.name}"
    content_b64 = base64.b64encode(render_path.read_bytes()).decode()

    existing = request_api("GET", repo_path(f"/contents/{dest}?ref={BRANCH}"), expect_404=True)
    payload = {
        "message": f"Render for issue #{issue_num}",
        "branch": BRANCH,
        "content": content_b64,
    }
    if existing:
        payload["sha"] = existing["sha"]

    request_api("PUT", repo_path(f"/contents/{dest}"), payload)
    print(f"Uploaded {dest}", flush=True)

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"path={dest}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
