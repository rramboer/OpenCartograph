"""Tests for the issue-form parser in .github/scripts/render_from_issue.py."""
from __future__ import annotations

import sys

import pytest

import render_from_issue as r


SAMPLE_FULL = """### City

Paris

### Country

France

### Theme

tropical

### Zoom level

City (10 mi)

### Quality

Standard

### Extra layers

- [x] Airports
- [ ] National parks
- [ ] Stadiums
- [x] Buildings (heavy for dense cities)

### Text overlay

- [x] Show date
- [ ] Show OpenStreetMap attribution
- [ ] No text overlay (map only)

### Override latitude (optional)

_No response_

### Override longitude (optional)

_No response_

### Custom width in inches (optional)

_No response_

### Custom height in inches (optional)

_No response_
"""

SAMPLE_COORDS_OVERRIDE = """### City

Lower Keys

### Country

USA

### Theme

ocean

### Zoom level

Region (50 mi)

### Quality

Low (fast preview)

### Extra layers

- [ ] Airports
- [ ] National parks
- [ ] Stadiums
- [ ] Buildings (heavy for dense cities)

### Text overlay

- [ ] Show date
- [ ] Show OpenStreetMap attribution
- [ ] No text overlay (map only)

### Override latitude (optional)

24.65

### Override longitude (optional)

-81.55

### Custom width in inches (optional)

_No response_

### Custom height in inches (optional)

_No response_
"""


def _arg_after(cmd: list[str], flag: str) -> str:
    return cmd[cmd.index(flag) + 1]


def test_full_form_builds_expected_command():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)

    assert cmd[:3] == [sys.executable, "-m", "opencartograph"]
    assert _arg_after(cmd, "-c") == "Paris"
    assert _arg_after(cmd, "-C") == "France"
    assert _arg_after(cmd, "-t") == "tropical"
    assert _arg_after(cmd, "-d") == "16000"
    assert _arg_after(cmd, "-q") == "standard"
    assert "--airports" in cmd
    assert "--buildings" in cmd
    assert "--natl-parks" not in cmd
    assert "--stadiums" not in cmd
    assert "--show-date" in cmd
    assert "--no-text" not in cmd
    assert "-lat" not in cmd


def test_coords_override():
    sections = r.parse_sections(SAMPLE_COORDS_OVERRIDE)
    cmd = r.build_command(sections)

    assert _arg_after(cmd, "-t") == "ocean"
    assert _arg_after(cmd, "-d") == "80000"
    assert _arg_after(cmd, "-q") == "low"
    assert _arg_after(cmd, "-lat") == "24.65"
    assert _arg_after(cmd, "-long") == "-81.55"
    assert "--airports" not in cmd


def test_missing_required_raises():
    sections = r.parse_sections("### City\n\n_No response_\n\n### Country\n\nFrance")
    with pytest.raises(ValueError):
        r.build_command(sections)


def test_no_response_returns_none():
    sections = r.parse_sections(SAMPLE_FULL)
    assert r.get_value(sections, "Override latitude (optional)") is None
    assert r.get_value(sections, "City") == "Paris"


def test_checked_options_handles_no_selections():
    body = "### Extra layers\n\n- [ ] Airports\n- [ ] National parks\n"
    sections = r.parse_sections(body)
    assert r.checked_options(sections, "Extra layers") == []


def test_ultra_quality_maps_to_ultra_flag():
    body = SAMPLE_FULL.replace("Standard", "Ultra (very large file, slow render)")
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "-q") == "ultra"


def test_largest_zoom_maps_to_240km():
    body = SAMPLE_FULL.replace("City (10 mi)", "Multi-state (150 mi)")
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "-d") == "240000"


def test_custom_dimensions_override():
    body = (
        SAMPLE_FULL
        .replace(
            "### Custom width in inches (optional)\n\n_No response_",
            "### Custom width in inches (optional)\n\n14",
        )
        .replace(
            "### Custom height in inches (optional)\n\n_No response_",
            "### Custom height in inches (optional)\n\n11",
        )
    )
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "-W") == "14"
    assert _arg_after(cmd, "-H") == "11"


def test_dimensions_omitted_when_blank():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)
    assert "-W" not in cmd
    assert "-H" not in cmd
