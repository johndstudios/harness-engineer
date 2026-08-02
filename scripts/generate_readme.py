#!/usr/bin/env python3
"""Generate the awesome-list README.md from content/resources/*.md.

The README is the raw-Markdown view of the directory. It groups resources by
category, in the canonical category order, and writes one bullet per resource
using the same format as the upstream awesome-harness-engineering list:

    - [Title](url) - Description.

Usage: scripts/generate_readme.py <resources_dir> <out_readme>
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path


CATEGORY_ORDER = [
    ("courses", "Courses & Learning Resources"),
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
    fm_text, body = m.group(1), m.group(2)
    fm: dict = {}
    for line in fm_text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("[") and value.endswith("]"):
            value = value[1:-1].split(",")[0].strip().strip('"')
        fm[key] = value
    fm["_body"] = body.strip()
    return fm


def load_resources(resources_dir: Path) -> list[dict]:
    resources: list[dict] = []
    for path in sorted(resources_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        fm = parse_front_matter(path.read_text(encoding="utf-8"))
        if not fm.get("title") or not fm.get("link"):
            continue
        fm["_path"] = path
        resources.append(fm)
    return resources


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: generate_readme.py <resources_dir> <out_readme>", file=sys.stderr)
        return 2
    resources_dir = Path(argv[1])
    out_path = Path(argv[2])
    if not resources_dir.is_dir():
        print(f"not a dir: {resources_dir}", file=sys.stderr)
        return 2

    resources = load_resources(resources_dir)
    by_category: dict[str, list[dict]] = {slug: [] for slug, _ in CATEGORY_ORDER}
    for r in resources:
        cat = r.get("category", "")
        if cat in by_category:
            by_category[cat].append(r)
        else:
            by_category.setdefault(cat, []).append(r)

    lines: list[str] = []
    lines.append("# Awesome Harness Engineering [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)")
    lines.append("")
    lines.append("> A curated list of articles, playbooks, benchmarks, specifications, and open-source projects for harness engineering: the practice of shaping the environment around AI agents so they can work reliably.")
    lines.append("")
    lines.append("Harness engineering sits at the intersection of context engineering, evaluation, observability, orchestration, safe autonomy, and software architecture. This list focuses on resources that make agents more dependable in real workflows, especially long-running coding and research tasks.")
    lines.append("")
    lines.append("Generic agent tooling is out of scope unless the page directly covers harness design, context management, evaluation, runtime control, or other reliability-critical harness primitives.")
    lines.append("")
    lines.append("This README is generated from the structured directory at [harness-engineer](https://github.com/johndstudios/harness-engineer). See the live, searchable site at <https://harness-engineer.dev/>.")
    lines.append("")
    lines.append("## Contents")
    lines.append("")
    for slug, label in CATEGORY_ORDER:
        lines.append(f"- [{label}](#{slug.replace(' ', '-').replace('--','-').lower()})")
    lines.append("- [Contributing](#contributing)")
    lines.append("- [License](#license)")
    lines.append("")

    for slug, label in CATEGORY_ORDER:
        lines.append(f"## {label}")
        lines.append("")
        for r in by_category.get(slug, []):
            title = r["title"]
            url = r["link"]
            desc = r["_body"].splitlines()[0] if r["_body"] else ""
            if desc:
                lines.append(f"- [{title}]({url}) - {desc}")
            else:
                lines.append(f"- [{title}]({url})")
        lines.append("")

    lines.append("## Contributing")
    lines.append("")
    lines.append("Contributions are welcome. Please prefer resources that are:")
    lines.append("")
    lines.append("- Specific about how agents are constrained, evaluated, resumed, observed, or orchestrated")
    lines.append("- Original implementations, primary-source articles, or high-signal technical write-ups")
    lines.append("- Useful to practitioners building real harnesses instead of generic AI commentary")
    lines.append("")
    lines.append("If two links say the same thing, prefer the more primary, practical, and implementation-oriented one.")
    lines.append("")
    lines.append("See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines and the preferred entry format. New entries can be added via pull request or, on the live site, via a submission form that opens a PR for you.")
    lines.append("")
    lines.append("## License")
    lines.append("")
    lines.append("[CC BY-SA 4.0](./LICENSE)")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {len(resources)} resources to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))