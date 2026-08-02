#!/usr/bin/env python3
"""Generate Hugo content stubs for category pages from the resource files.

Emits:
  content/categories/_index.md          — categories listing page
  content/categories/<slug>/_index.md   — one stub per category

Each per-category stub uses the `resources-by-category` shortcode to render
the filtered list of resources at build time.

Usage: scripts/generate_categories.py <resources_dir> <content_dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


CATEGORY_ORDER = [
    ("courses", "Courses & Learning"),
    ("foundations", "Foundations"),
    ("context", "Context, Memory & Working State"),
    ("constraints", "Constraints, Guardrails & Safe Autonomy"),
    ("specs", "Specs, Agent Files & Workflow Design"),
    ("evals", "Evals & Observability"),
    ("benchmarks", "Benchmarks"),
    ("runtimes", "Runtimes, Harnesses & Reference Implementations"),
]

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def parse_front_matter(text: str) -> dict:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}
    fm_text = m.group(1)
    fm: dict = {}
    for line in fm_text.splitlines():
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


def count_by_category(resources_dir: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in resources_dir.glob("*.md"):
        if path.name.startswith("_"):
            continue
        fm = parse_front_matter(path.read_text(encoding="utf-8"))
        cat = fm.get("category", "")
        if cat:
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: generate_categories.py <resources_dir> <content_dir>", file=sys.stderr)
        return 2
    resources_dir = Path(argv[1])
    content_dir = Path(argv[2])
    if not resources_dir.is_dir():
        print(f"not a dir: {resources_dir}", file=sys.stderr)
        return 2

    counts = count_by_category(resources_dir)
    cats_dir = content_dir / "categories"
    cats_dir.mkdir(parents=True, exist_ok=True)

    # Per-category stubs
    for slug, label in CATEGORY_ORDER:
        cat_dir = cats_dir / slug
        cat_dir.mkdir(parents=True, exist_ok=True)
        n = counts.get(slug, 0)
        content = (
            "---\n"
            f'title: "{label}"\n'
            f'description: "{n} resources in {label}"\n'
            "---\n"
            "\n"
            f"{{{{< resources-by-category category=\"{slug}\" >}}}}\n"
        )
        (cat_dir / "_index.md").write_text(content, encoding="utf-8")

    # Categories index
    lines = ["---", 'title: "Categories"', 'description: "Browse resources by category."', "---", ""]
    for slug, label in CATEGORY_ORDER:
        n = counts.get(slug, 0)
        lines.append(f"- [{label}](/categories/{slug}/) — {n} resources")
    lines.append("")
    (cats_dir / "_index.md").write_text("\n".join(lines), encoding="utf-8")

    # Clean up any stale category dirs not in CATEGORY_ORDER
    for d in cats_dir.iterdir():
        if d.is_dir() and d.name not in [s for s, _ in CATEGORY_ORDER]:
            import shutil
            shutil.rmtree(d)

    print(f"wrote {len(CATEGORY_ORDER)} category stubs to {cats_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))