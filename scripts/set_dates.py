#!/usr/bin/env python3
"""Add a `date:` field to each resource file equal to its `added:` value.

Hugo uses the `date` front-matter field for page ordering and RSS pubDates.
We use `added` for display (to avoid confusion with Hugo reserved words in
templates), but mirror it into `date` so RSS and recently-added sort work.

Idempotent: re-running updates `date` to match `added` if missing or stale.

Usage: scripts/set_dates.py <resources_dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
ADDED_RE = re.compile(r"^added:\s*(.+)$", re.M)
DATE_RE = re.compile(r"^date:\s*.+$", re.M)


def update_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return False
    fm_text = m.group(1)
    body = m.group(2)
    added_match = ADDED_RE.search(fm_text)
    if not added_match:
        return False
    added_value = added_match.group(1).strip()
    lines = fm_text.splitlines()
    # Replace existing date line or insert after `added:`.
    new_lines = []
    inserted = False
    for line in lines:
        if DATE_RE.match(line):
            new_lines.append(f"date: {added_value}")
            inserted = True
        elif line.strip().startswith("added:"):
            new_lines.append(line)
            if not inserted:
                new_lines.append(f"date: {added_value}")
                inserted = True
        else:
            new_lines.append(line)
    if not inserted:
        new_lines.append(f"date: {added_value}")
    if not body.startswith("\n\n"):
        body = "\n\n" + body.lstrip("\n")
    new_text = "---\n" + "\n".join(new_lines) + "\n---" + body
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main(argv: list[str]) -> int:
    resources_dir = Path(argv[1] if len(argv) > 1 else "content/resources")
    if not resources_dir.is_dir():
        print(f"error: not a directory: {resources_dir}", file=sys.stderr)
        return 2
    changed = 0
    total = 0
    for path in sorted(resources_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        total += 1
        if update_file(path):
            changed += 1
    print(f"set dates on {changed}/{total} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))