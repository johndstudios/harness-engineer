#!/usr/bin/env python3
"""Extract contributor counts from git history and write a data file.

For each resource file under content/resources/, counts how many times each
author added or modified that file, then aggregates per-author totals across
all resources. Writes two outputs:

  data/contributors.json   — leaderboard: [{ name, count, resources: [slug] }]
  data/resource_authors.json — per-resource authorship: { slug: [author, ...] }

These power the contributors page and the "added by" line on resource pages.

The script shells out to `git log` and must be run from the repo root. In CI,
it runs after checkout (which has full history by default).

Usage: scripts/generate_contributors.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


RESOURCES_DIR = Path("content/resources")
DATA_DIR = Path("data")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def file_authors(path: str) -> list[str]:
    # %an = author name, one line per commit touching the file.
    out = git("log", "--follow", "--format=%an", "--", path)
    return [line for line in out.splitlines() if line]


def main() -> int:
    if not RESOURCES_DIR.is_dir():
        print(f"error: {RESOURCES_DIR} not found", file=sys.stderr)
        return 2
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Per-resource authorship
    resource_authors: dict[str, list[str]] = {}
    per_author: dict[str, list[str]] = defaultdict(list)

    for path in sorted(RESOURCES_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        slug = path.stem
        rel = str(path)
        authors = file_authors(rel)
        if not authors:
            continue
        # Preserve order but dedupe (first occurrence wins).
        seen = []
        for a in authors:
            if a not in seen:
                seen.append(a)
        resource_authors[slug] = seen
        for a in seen:
            per_author[a].append(slug)

    # Leaderboard sorted by count desc, then name.
    leaderboard = [
        {"name": name, "count": len(slugs), "resources": sorted(slugs)}
        for name, slugs in per_author.items()
    ]
    leaderboard.sort(key=lambda x: (-x["count"], x["name"]))

    (DATA_DIR / "contributors.json").write_text(
        json.dumps(leaderboard, indent=2), encoding="utf-8"
    )
    (DATA_DIR / "resource_authors.json").write_text(
        json.dumps(resource_authors, indent=2), encoding="utf-8"
    )
    print(f"wrote {len(leaderboard)} contributors, {len(resource_authors)} resources authored")
    return 0


if __name__ == "__main__":
    sys.exit(main())