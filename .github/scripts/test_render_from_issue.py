"""Local sanity test for the issue-form parser.

Run from repo root:  python .github/scripts/test_render_from_issue.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from render_from_issue import build_command, get_value, parse_sections  # noqa: E402

SAMPLE_FULL = """### City

Paris

### Country

France

### Theme

tropical

### Zoom level

City (~18 km)

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
"""

SAMPLE_COORDS_OVERRIDE = """### City

Lower Keys

### Country

USA

### Theme

ocean

### Zoom level

Wide (~90 km)

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
"""


def test_full_form():
    sections = parse_sections(SAMPLE_FULL)
    assert get_value(sections, "City") == "Paris"
    assert get_value(sections, "Override latitude (optional)") is None

    cmd = build_command(sections)
    assert "Paris" in cmd and "France" in cmd
    assert "tropical" in cmd
    assert "18000" in cmd
    assert "standard" in cmd
    assert "--airports" in cmd
    assert "--buildings" in cmd
    assert "--natl-parks" not in cmd
    assert "--stadiums" not in cmd
    assert "--show-date" in cmd
    assert "--no-text" not in cmd
    assert "-lat" not in cmd
    print("test_full_form: ok")


def test_coords_override():
    sections = parse_sections(SAMPLE_COORDS_OVERRIDE)
    cmd = build_command(sections)
    assert "ocean" in cmd
    assert "90000" in cmd
    assert "low" in cmd
    assert "-lat" in cmd and "24.65" in cmd
    assert "-long" in cmd and "-81.55" in cmd
    assert "--airports" not in cmd
    print("test_coords_override: ok")


def test_missing_required():
    sections = parse_sections("### City\n\n_No response_\n\n### Country\n\nFrance")
    try:
        build_command(sections)
    except ValueError as e:
        assert "City" in str(e) or "Country" in str(e)
        print("test_missing_required: ok")
        return
    raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_full_form()
    test_coords_override()
    test_missing_required()
    print("\nAll tests passed.")
