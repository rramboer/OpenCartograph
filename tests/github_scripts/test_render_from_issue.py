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

### Display name for city

_No response_

### Display name for country

_No response_

### Override latitude

_No response_

### Override longitude

_No response_

### Custom width in inches

_No response_

### Custom height in inches

_No response_

### Map rotation in degrees

_No response_

### Compass badge

Auto (shown when rotated)

### Road width scale

_No response_

### Google Fonts family

_No response_

### Extra layers

- [x] Airports
- [ ] National parks
- [ ] Stadiums
- [x] Buildings (heavy for dense cities)

### Text overlay

- [x] Show date
- [ ] Show OpenStreetMap attribution
- [ ] No text overlay (map only)
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

### Display name for city

_No response_

### Display name for country

_No response_

### Override latitude

24.65

### Override longitude

-81.55

### Custom width in inches

_No response_

### Custom height in inches

_No response_

### Map rotation in degrees

_No response_

### Compass badge

Auto (shown when rotated)

### Road width scale

_No response_

### Google Fonts family

_No response_

### Extra layers

- [ ] Airports
- [ ] National parks
- [ ] Stadiums
- [ ] Buildings (heavy for dense cities)

### Text overlay

- [ ] Show date
- [ ] Show OpenStreetMap attribution
- [ ] No text overlay (map only)
"""


def _arg_after(cmd: list[str], flag: str) -> str:
    return cmd[cmd.index(flag) + 1]


def _replace_section(body: str, header: str, new_content: str) -> str:
    return body.replace(f"### {header}\n\n_No response_", f"### {header}\n\n{new_content}")


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
    assert r.get_value(sections, "Override latitude") is None
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
    body = _replace_section(SAMPLE_FULL, "Custom width in inches", "14")
    body = _replace_section(body, "Custom height in inches", "11")
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "-W") == "14"
    assert _arg_after(cmd, "-H") == "11"


def test_dimensions_omitted_when_blank():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)
    assert "-W" not in cmd
    assert "-H" not in cmd


def test_display_name_overrides():
    body = _replace_section(SAMPLE_FULL, "Display name for city", "東京")
    body = _replace_section(body, "Display name for country", "日本")
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "-dc") == "東京"
    assert _arg_after(cmd, "-dC") == "日本"
    assert _arg_after(cmd, "-c") == "Paris"
    assert _arg_after(cmd, "-C") == "France"


def test_display_names_omitted_when_blank():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)
    assert "-dc" not in cmd
    assert "-dC" not in cmd


def test_rotation_passes_through():
    body = _replace_section(SAMPLE_FULL, "Map rotation in degrees", "45")
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "-O") == "45"


def test_rotation_omitted_when_blank():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)
    assert "-O" not in cmd


def test_compass_default_is_auto():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)
    assert "--show-north" not in cmd
    assert "--hide-north" not in cmd


def test_compass_always_show():
    body = SAMPLE_FULL.replace(
        "### Compass badge\n\nAuto (shown when rotated)",
        "### Compass badge\n\nAlways show",
    )
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert "--show-north" in cmd
    assert "--hide-north" not in cmd


def test_compass_always_hide():
    body = SAMPLE_FULL.replace(
        "### Compass badge\n\nAuto (shown when rotated)",
        "### Compass badge\n\nAlways hide",
    )
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert "--hide-north" in cmd
    assert "--show-north" not in cmd


def test_line_scale_passes_through():
    body = _replace_section(SAMPLE_FULL, "Road width scale", "1.5")
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "--line-scale") == "1.5"


def test_line_scale_omitted_when_blank():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)
    assert "--line-scale" not in cmd


def test_font_family_passes_through():
    body = _replace_section(SAMPLE_FULL, "Google Fonts family", "Noto Sans JP")
    sections = r.parse_sections(body)
    cmd = r.build_command(sections)
    assert _arg_after(cmd, "--font-family") == "Noto Sans JP"


def test_font_family_omitted_when_blank():
    sections = r.parse_sections(SAMPLE_FULL)
    cmd = r.build_command(sections)
    assert "--font-family" not in cmd
