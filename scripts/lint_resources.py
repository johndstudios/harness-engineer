#!/usr/bin/env python3
"""Validate front matter of resource files in content/resources/.

Checks every *.md file (except _index.md) for:
- required fields present (title, link, category, resource_kind, source, added)
- category is one of the allowed values
- resource_kind is one of the allowed values
- link is a non-empty http(s) URL
- added is a valid YYYY-MM-DD date
- no duplicate titles or links across resources
- tags are drawn from the controlled vocabulary in data/tags.yml (if present)

Exits non-zero on any violation.

Usage: scripts/lint_resources.py [resources_dir]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


ALLOWED_CATEGORIES = {
    "courses", "foundations", "context", "constraints",
    "specs", "evals", "benchmarks", "runtimes",
}
ALLOWED_KINDS = {"article", "tool", "benchmark", "course", "spec", "podcast", "video", "paper"}
REQUIRED_FIELDS = ("title", "link", "category", "resource_kind", "source", "added")

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TAG_VALUE_RE = re.compile(r'"([^"]+)"')


def parse_front_matter(text: str) -> dict:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    fm: dict = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1].split(",")[0].strip().strip('"')
        elif value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        fm[key] = value
    return fm


def parse_tags(text: str) -> list[str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return []
    for line in m.group(1).splitlines():
        if line.strip().startswith("tags:"):
            return TAG_VALUE_RE.findall(line)
    return []


def load_tag_vocabulary(resources_dir: Path) -> set[str] | None:
    # data/tags.yml lives at the repo root (parent of content/).
    tags_file = resources_dir.parent.parent / "data" / "tags.yml"
    if not tags_file.is_file():
        return None
    tags = set()
    for line in tags_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        slug = line.split(":", 1)[0].strip()
        if slug:
            tags.add(slug)
    return tags


def main(argv: list[str]) -> int:
    resources_dir = Path(argv[1] if len(argv) > 1 else "content/resources")
    if not resources_dir.is_dir():
        print(f"error: not a directory: {resources_dir}", file=sys.stderr)
        return 2

    errors: list[str] = []
    seen_titles: dict[str, str] = {}
    seen_links: dict[str, str] = {}
    vocab = load_tag_vocabulary(resources_dir)

    for path in sorted(resources_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        rel = str(path)
        text = path.read_text(encoding="utf-8")
        fm = parse_front_matter(text)
        if not fm:
            errors.append(f"{rel}: missing front matter")
            continue
        for field in REQUIRED_FIELDS:
            if field not in fm or not fm[field]:
                errors.append(f"{rel}: missing required field '{field}'")
        if fm.get("category") and fm["category"] not in ALLOWED_CATEGORIES:
            errors.append(f"{rel}: invalid category '{fm['category']}'")
        if fm.get("resource_kind") and fm["resource_kind"] not in ALLOWED_KINDS:
            errors.append(f"{rel}: invalid resource_kind '{fm['resource_kind']}'")
        link = fm.get("link", "")
        if link and not link.startswith(("http://", "https://")):
            errors.append(f"{rel}: link must be an http(s) URL, got '{link}'")
        added = fm.get("added", "")
        if added and not DATE_RE.match(added):
            errors.append(f"{rel}: added must be YYYY-MM-DD, got '{added}'")
        if vocab is not None:
            for tag in parse_tags(text):
                if tag not in vocab:
                    errors.append(f"{rel}: tag '{tag}' not in controlled vocabulary (data/tags.yml)")
        title = fm.get("title", "")
        if title:
            if title.lower() in seen_titles:
                errors.append(f"{rel}: duplicate title '{title}' (also in {seen_titles[title.lower()]})")
            else:
                seen_titles[title.lower()] = rel
        if link:
            if link in seen_links:
                errors.append(f"{rel}: duplicate link '{link}' (also in {seen_links[link]})")
            else:
                seen_links[link] = rel

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        print(f"\n{len(errors)} error(s) in {len(list(resources_dir.glob('*.md')))} files", file=sys.stderr)
        return 1
    print(f"ok: {len(list(resources_dir.glob('*.md')))} resource files validated")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))