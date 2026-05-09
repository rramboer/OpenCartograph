"""Tests for .github/scripts/upload_render.py."""
from __future__ import annotations

from unittest.mock import patch

import pytest

import upload_render


@pytest.fixture(autouse=True)
def _gh_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")


def test_safe_filename_strips_unicode_accents():
    assert upload_render.safe_filename("são_paulo_tropical.png") == "sao_paulo_tropical.png"
    assert upload_render.safe_filename("zürich_emerald.png") == "zurich_emerald.png"
    assert upload_render.safe_filename("tōkyō_noir.png") == "tokyo_noir.png"


def test_safe_filename_keeps_ascii_unchanged():
    assert upload_render.safe_filename("paris_terracotta.png") == "paris_terracotta.png"


def test_safe_filename_handles_all_non_ascii():
    """A pure non-ASCII input must not crash and must not produce an empty path."""
    assert upload_render.safe_filename("漢字漢字") == "render.png"


def test_safe_filename_collapses_unsafe_chars():
    """Apostrophes, commas, spaces become underscores; ASCII letters/digits/.-_ survive."""
    result = upload_render.safe_filename("st. john's, nl_noir.png")
    assert "'" not in result and "," not in result and " " not in result
    assert result.endswith(".png")
    assert "noir" in result


def test_ensure_renders_branch_skips_when_present():
    with patch.object(upload_render, "request_api", return_value={"name": "renders"}) as m:
        upload_render.ensure_renders_branch()
    assert m.call_count == 1


def test_ensure_renders_branch_uses_hardcoded_empty_tree_sha():
    """Avoids the undocumented POST /git/trees with an empty array."""
    responses = [
        None,                              # GET branches/renders → 404
        {"sha": "init_commit_sha"},        # POST /git/commits
        {"ref": "refs/heads/renders"},     # POST /git/refs
    ]
    calls = []

    def fake_api(method, path, body=None, **kwargs):
        calls.append((method, path, body))
        return responses[len(calls) - 1]

    with patch.object(upload_render, "request_api", side_effect=fake_api):
        upload_render.ensure_renders_branch()

    assert len(calls) == 3, f"expected 3 API calls, got {len(calls)}: {calls}"
    methods = [c[0] for c in calls]
    paths = [c[1] for c in calls]
    assert methods == ["GET", "POST", "POST"]
    assert "/repos/owner/repo/git/trees" not in paths

    _, commit_path, commit_body = calls[1]
    assert commit_path == "/repos/owner/repo/git/commits"
    assert commit_body["tree"] == upload_render.EMPTY_TREE_SHA
    assert commit_body["parents"] == []

    _, ref_path, ref_body = calls[2]
    assert ref_path == "/repos/owner/repo/git/refs"
    assert ref_body["ref"] == "refs/heads/renders"
    assert ref_body["sha"] == "init_commit_sha"
