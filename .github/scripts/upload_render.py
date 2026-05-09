#!/usr/bin/env python3
"""Upload a rendered PNG to the orphan `renders` branch.

Uses the Git Data API to bootstrap the orphan branch on first run, and the
Contents API for subsequent uploads.

Reads from env: ISSUE_NUMBER, RENDER_PATH (plus GITHUB_TOKEN/GITHUB_REPOSITORY).
Writes path=<dest-path-on-renders-branch> to $GITHUB_OUTPUT.
"""
from __future__ import annotations

import base64
import os
import re
import sys
import unicodedata
from pathlib import Path

from _gh_api import repo_path, request_api

BRANCH = "renders"

# Universal git empty-tree hash; identical across all repos. Used instead of
# POST /git/trees with an empty array, whose behavior is undocumented.
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def safe_filename(name: str) -> str:
    """Reduce a filename to ASCII so it works in URL paths.

    OpenCartograph slugifies city names with only lower/replace, so non-ASCII
    cities (São Paulo, Tōkyō, Zürich) produce filenames that crash urllib's
    ASCII-only URL encoder before any HTTP request goes out.
    """
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_only).strip("_.")
    return cleaned or "render.png"


def ensure_renders_branch() -> None:
    if request_api("GET", repo_path(f"/branches/{BRANCH}"), expect_404=True) is not None:
        return

    print(f"Creating orphan branch '{BRANCH}'...", flush=True)
    init_commit = request_api(
        "POST",
        repo_path("/git/commits"),
        {
            "message": "Initialize renders branch",
            "tree": EMPTY_TREE_SHA,
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

    dest = f"issue-{issue_num}/{safe_filename(render_path.name)}"
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
