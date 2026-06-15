"""Tests for .github/scripts/prune_renders.py.

Focuses on the destructive code paths: any regression here can permanently
delete user data on the renders branch.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

import prune_renders


@pytest.fixture(autouse=True)
def _gh_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")


def test_issue_closed_at_open_issue_returns_none():
    with patch.object(prune_renders, "request_api", return_value={"state": "open"}):
        assert prune_renders.issue_closed_at(42) is None


def test_issue_closed_at_closed_returns_utc_datetime():
    issue = {"state": "closed", "closed_at": "2026-01-15T10:30:00Z"}
    with patch.object(prune_renders, "request_api", return_value=issue):
        result = prune_renders.issue_closed_at(42)
    assert result == datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


def test_issue_closed_at_404_returns_none_not_far_past(capsys):
    """CRITICAL: 404 must NOT trigger deletion. Auth blips return 404 too."""
    with patch.object(prune_renders, "request_api", return_value=None):
        result = prune_renders.issue_closed_at(42)
    assert result is None, "404 must keep renders, not mark them ancient"
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "#42" in err


def test_issue_closed_at_closed_without_closed_at_returns_none():
    """Defensive: closed state but no closed_at field shouldn't crash."""
    with patch.object(prune_renders, "request_api", return_value={"state": "closed"}):
        assert prune_renders.issue_closed_at(42) is None


def test_collect_paths_does_not_suppress_subdir_404():
    """A 404 on a subdirectory of a known-existing dir must raise, not be silently
    dropped (which would leave the dir half-pruned)."""
    def fake_api(method, path, body=None, **kwargs):
        if kwargs.get("expect_404", False):
            return None
        raise RuntimeError(f"GET {path} → 404 simulated")

    with patch.object(prune_renders, "request_api", side_effect=fake_api):
        with pytest.raises(RuntimeError, match="404 simulated"):
            prune_renders.collect_paths_under("issue-1")


def test_collect_paths_recurses_correctly():
    responses = {
        "/repos/owner/repo/contents/issue-1?ref=renders": [
            {"type": "file", "name": "a.png", "path": "issue-1/a.png"},
            {"type": "dir", "name": "sub", "path": "issue-1/sub"},
        ],
        "/repos/owner/repo/contents/issue-1/sub?ref=renders": [
            {"type": "file", "name": "b.png", "path": "issue-1/sub/b.png"},
        ],
    }

    def fake_api(method, path, body=None, **kwargs):
        return responses[path]

    with patch.object(prune_renders, "request_api", side_effect=fake_api):
        paths = prune_renders.collect_paths_under("issue-1")
    assert sorted(paths) == ["issue-1/a.png", "issue-1/sub/b.png"]


def test_commit_deletions_payload_shape():
    """Lock the Git Data API payload shape — this is the most consequential code."""
    responses = [
        {"object": {"sha": "head_sha"}},                # GET /git/refs/heads/renders
        {"tree": {"sha": "base_tree_sha"}},             # GET /git/commits/head_sha
        {"sha": "new_tree_sha"},                        # POST /git/trees
        {"sha": "new_commit_sha"},                      # POST /git/commits
        {"object": {"sha": "new_commit_sha"}},          # PATCH ref
    ]
    calls = []

    def fake_api(method, path, body=None, **kwargs):
        calls.append((method, path, body))
        return responses[len(calls) - 1]

    with patch.object(prune_renders, "request_api", side_effect=fake_api):
        prune_renders.commit_deletions(["issue-1/a.png", "issue-1/b.png"])

    assert len(calls) == 5

    assert calls[0][:2] == ("GET", "/repos/owner/repo/git/refs/heads/renders")
    assert calls[1][:2] == ("GET", "/repos/owner/repo/git/commits/head_sha")

    method, path, body = calls[2]
    assert (method, path) == ("POST", "/repos/owner/repo/git/trees")
    assert body["base_tree"] == "base_tree_sha", \
        "MUST send base_tree — without it, the new tree is empty and the next commit wipes the branch"
    assert len(body["tree"]) == 2
    for entry in body["tree"]:
        assert entry["sha"] is None, "null sha is what signals 'delete this path'"
        assert entry["type"] == "blob"
        assert entry["path"] in {"issue-1/a.png", "issue-1/b.png"}

    method, path, body = calls[3]
    assert (method, path) == ("POST", "/repos/owner/repo/git/commits")
    assert body["tree"] == "new_tree_sha"
    assert body["parents"] == ["head_sha"], "must chain off current HEAD, not orphan"

    method, path, body = calls[4]
    assert (method, path) == ("PATCH", "/repos/owner/repo/git/refs/heads/renders")
    assert body["sha"] == "new_commit_sha"
    assert body["force"] is False, "force-push would let stale logic clobber concurrent commits"

    assert len(calls) == len(responses), \
        "extra API calls would IndexError mid-test; expand `responses` if a new call was added"


def test_commit_deletions_aborts_above_safety_limit():
    """Refuse to delete more than MAX_PRUNE_FILES in one run, no API calls made."""
    too_many = [f"issue-{i}/file.png" for i in range(prune_renders.MAX_PRUNE_FILES + 1)]
    with patch.object(prune_renders, "request_api") as m:
        with pytest.raises(RuntimeError, match="Refusing to delete"):
            prune_renders.commit_deletions(too_many)
    assert m.call_count == 0


def test_commit_deletions_at_safety_limit_proceeds():
    """Exactly MAX_PRUNE_FILES is allowed and goes through the full API sequence."""
    paths = [f"issue-{i}/file.png" for i in range(prune_renders.MAX_PRUNE_FILES)]
    responses = [
        {"object": {"sha": "head_sha"}},
        {"tree": {"sha": "base_tree_sha"}},
        {"sha": "new_tree_sha"},
        {"sha": "new_commit_sha"},
        {"object": {"sha": "new_commit_sha"}},
    ]
    with patch.object(prune_renders, "request_api", side_effect=responses) as m:
        prune_renders.commit_deletions(paths)
    assert m.call_count == 5, "all 5 API calls must occur — no early return at the limit"


def test_commit_deletions_falls_back_to_contents_api_on_git_data_404():
    calls = []

    def fake_api(method, path, body=None, **kwargs):
        calls.append((method, path, body, kwargs))
        if (method, path) == ("GET", "/repos/owner/repo/git/refs/heads/renders"):
            return {"object": {"sha": "head_sha"}}
        if (method, path) == ("GET", "/repos/owner/repo/git/commits/head_sha"):
            return {"tree": {"sha": "base_tree_sha"}}
        if (method, path) == ("POST", "/repos/owner/repo/git/trees"):
            raise RuntimeError(
                'POST /repos/owner/repo/git/trees → 404: {"message":"Not Found"}'
            )
        if (method, path) == ("GET", "/repos/owner/repo/contents/issue-1/a.png?ref=renders"):
            return {"sha": "sha-a"}
        if (method, path) == ("GET", "/repos/owner/repo/contents/issue-1/b.png?ref=renders"):
            return {"sha": "sha-b"}
        if (method, path) == ("DELETE", "/repos/owner/repo/contents/issue-1/a.png"):
            return {}
        if (method, path) == ("DELETE", "/repos/owner/repo/contents/issue-1/b.png"):
            return {}
        raise AssertionError(f"unexpected API call: {(method, path, body, kwargs)}")

    with patch.object(prune_renders, "request_api", side_effect=fake_api):
        prune_renders.commit_deletions(["issue-1/a.png", "issue-1/b.png"])

    assert calls[3] == (
        "GET",
        "/repos/owner/repo/contents/issue-1/a.png?ref=renders",
        None,
        {"expect_404": True},
    )
    assert calls[4] == (
        "DELETE",
        "/repos/owner/repo/contents/issue-1/a.png",
        {
            "message": "Prune stale render file issue-1/a.png",
            "branch": "renders",
            "sha": "sha-a",
        },
        {},
    )
    assert calls[5] == (
        "GET",
        "/repos/owner/repo/contents/issue-1/b.png?ref=renders",
        None,
        {"expect_404": True},
    )
    assert calls[6] == (
        "DELETE",
        "/repos/owner/repo/contents/issue-1/b.png",
        {
            "message": "Prune stale render file issue-1/b.png",
            "branch": "renders",
            "sha": "sha-b",
        },
        {},
    )


def test_list_issue_dirs_ignores_non_issue_entries():
    contents = [
        {"type": "dir", "name": "issue-1", "path": "issue-1"},
        {"type": "dir", "name": "issue-42", "path": "issue-42"},
        {"type": "dir", "name": "scratch", "path": "scratch"},
        {"type": "file", "name": "README.md", "path": "README.md"},
    ]
    with patch.object(prune_renders, "request_api", return_value=contents):
        result = prune_renders.list_issue_dirs()
    assert result == [(1, "issue-1"), (42, "issue-42")]


def test_list_issue_dirs_empty_when_branch_absent():
    with patch.object(prune_renders, "request_api", return_value=None):
        assert prune_renders.list_issue_dirs() == []


def test_main_dry_run_makes_no_mutations(monkeypatch, capsys):
    """Verify dry-run mode never issues PATCH/POST — protects against a regression
    that ignores the DRY_RUN flag."""
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("MAX_AGE_DAYS", "30")

    closed_long_ago = {"state": "closed", "closed_at": "2020-01-01T00:00:00Z"}
    routes = {
        "/repos/owner/repo/branches/renders": {"name": "renders"},
        "/repos/owner/repo/contents?ref=renders": [
            {"type": "dir", "name": "issue-1", "path": "issue-1"},
        ],
        "/repos/owner/repo/issues/1": closed_long_ago,
        "/repos/owner/repo/contents/issue-1?ref=renders": [
            {"type": "file", "name": "x.png", "path": "issue-1/x.png"},
        ],
    }
    call_log = []

    def fake_api(method, path, body=None, **kwargs):
        call_log.append((method, path))
        assert path in routes, f"unexpected API call to {path} — test fixture incomplete?"
        return routes[path]

    with patch.object(prune_renders, "request_api", side_effect=fake_api):
        rc = prune_renders.main()

    assert rc == 0
    for method, path in call_log:
        assert method == "GET", f"DRY RUN made a {method} {path}"
    assert "DRY RUN" in capsys.readouterr().out


def test_main_no_branch_exits_clean(monkeypatch, capsys):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("MAX_AGE_DAYS", "30")
    with patch.object(prune_renders, "request_api", return_value=None):
        assert prune_renders.main() == 0
    assert "does not exist" in capsys.readouterr().out
