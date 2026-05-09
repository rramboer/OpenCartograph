#!/usr/bin/env python3
"""Parse a GitHub Issue Form body and run opencartograph with the requested args.

Reads ISSUE_BODY from env. Writes path=<output-png> to $GITHUB_OUTPUT.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ZOOM_TO_DISTANCE = {
    "Neighborhood (~4 km)": 4000,
    "Downtown (~8 km)": 8000,
    "City (~18 km)": 18000,
    "Metro (~30 km)": 30000,
    "Region (~60 km)": 60000,
    "Wide (~90 km)": 90000,
}

QUALITY_LABEL_TO_FLAG = {
    "Low (fast preview)": "low",
    "Standard": "standard",
    "High": "high",
}

LAYER_FLAGS = {
    "Airports": "--airports",
    "National parks": "--natl-parks",
    "Stadiums": "--stadiums",
    "Buildings": "--buildings",
}

TEXT_FLAGS = {
    "Show date": "--show-date",
    "Show OpenStreetMap attribution": "--show-attribution",
    "No text overlay": "--no-text",
}


def parse_sections(body: str) -> dict[str, str]:
    """Split a GitHub Issue Form body into {header: content} sections."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = re.match(r"^###\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def get_value(sections: dict[str, str], label: str) -> str | None:
    val = sections.get(label, "").strip()
    if not val or val == "_No response_":
        return None
    return val


def checked_options(sections: dict[str, str], label: str) -> list[str]:
    raw = sections.get(label, "")
    out: list[str] = []
    for line in raw.splitlines():
        match = re.match(r"^\s*[-*]\s*\[[xX]\]\s*(.+?)\s*$", line)
        if match:
            out.append(match.group(1).strip())
    return out


def _has_match(needle: str, options: list[str]) -> bool:
    needle_low = needle.lower()
    return any(needle_low in opt.lower() for opt in options)


def build_command(sections: dict[str, str]) -> list[str]:
    city = get_value(sections, "City")
    country = get_value(sections, "Country")
    if not city or not country:
        raise ValueError("Both City and Country are required")

    theme = get_value(sections, "Theme") or "terracotta"
    zoom_label = get_value(sections, "Zoom level") or "City (~18 km)"
    quality_label = get_value(sections, "Quality") or "Standard"

    distance = ZOOM_TO_DISTANCE.get(zoom_label, 18000)
    quality = QUALITY_LABEL_TO_FLAG.get(quality_label, "standard")

    cmd = [
        sys.executable, "-m", "opencartograph",
        "-c", city,
        "-C", country,
        "-t", theme,
        "-d", str(distance),
        "-q", quality,
    ]

    lat = get_value(sections, "Override latitude (optional)")
    lon = get_value(sections, "Override longitude (optional)")
    if lat and lon:
        cmd += ["-lat", lat, "-long", lon]

    layers_checked = checked_options(sections, "Extra layers")
    for label, flag in LAYER_FLAGS.items():
        if _has_match(label, layers_checked):
            cmd.append(flag)

    text_checked = checked_options(sections, "Text overlay")
    for label, flag in TEXT_FLAGS.items():
        if _has_match(label, text_checked):
            cmd.append(flag)

    return cmd


def main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    if not body:
        print("ERROR: ISSUE_BODY env var is empty", file=sys.stderr)
        return 1

    sections = parse_sections(body)
    cmd = build_command(sections)

    print("Running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)

    pngs = sorted(Path("output").glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not pngs:
        print("ERROR: no PNG produced", file=sys.stderr)
        return 1

    out_file = pngs[0]
    print(f"Rendered: {out_file}", flush=True)

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"path={out_file}\n")
            f.write(f"filename={out_file.name}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
