#!/usr/bin/env python3
"""Parse the awesome-harness-engineering README into structured resource files.

Each resource becomes one Markdown file under content/resources/ with YAML
front matter.  The category is derived from the README section heading; `kind`
and `source` are inferred heuristically from the URL and title.

Usage: scripts/migrate_readme.py <readme_path> <output_dir>
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


# Map README section headings -> slug, display name, category key.
# Order matches the README's Contents block.
SECTIONS: list[tuple[str, str, str]] = [
    ("Courses & Learning Resources", "courses", "Courses & Learning Resources"),
    ("Foundations", "foundations", "Foundations"),
    ("Context, Memory & Working State", "context", "Context, Memory & Working State"),
    ("Constraints, Guardrails & Safe Autonomy", "constraints", "Constraints, Guardrails & Safe Autonomy"),
    ("Specs, Agent Files & Workflow Design", "specs", "Specs, Agent Files & Workflow Design"),
    ("Evals & Observability", "evals", "Evals & Observability"),
    ("Benchmarks", "benchmarks", "Benchmarks"),
    ("Runtimes, Harnesses & Reference Implementations", "runtimes", "Runtimes, Harnesses & Reference Implementations"),
]

ENTRY_RE = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<url>https?[^)]+)\) - (?P<desc>.+)$")
# Lines that are not entries we should import (comments, blank, prose).
SKIP_LINE_PREFIXES = ("<!--", "These benchmarks", "##", "-", ">", "#")


def slugify(value: str) -> str:
    """Return a filesystem-safe slug from an arbitrary string."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    value = value.strip("-")
    return value or "resource"


def infer_kind(url: str, title: str, category: str) -> str:
    """Best-effort kind classification: article | tool | benchmark | course | spec."""
    host = urlparse(url).netloc.lower()
    path = urlparse(url).path.lower()
    if category == "benchmarks":
        return "benchmark"
    if category == "courses":
        return "course"
    if category == "specs":
        # spec-kit / agents.md / agent.md / 12-factor style resources
        if any(k in title.lower() for k in ("spec", "agents.md", "agent.md", "factor")):
            return "spec"
        return "article"
    if "github.com" in host:
        # GitHub repos are usually tools or reference implementations
        return "tool"
    if category == "runtimes":
        return "tool"
    # Articles dominate the remaining categories
    return "article"


def infer_source(url: str, title: str) -> str:
    """Best-effort source/author classification from the URL host."""
    host = urlparse(url).netloc.lower()
    mapping = {
        "anthropic.com": "anthropic",
        "openai.com": "openai",
        "blog.langchain.com": "langchain",
        "martinfowler.com": "thoughtworks",
        "www.humanlayer.dev": "humanlayer",
        "humanlayer.dev": "humanlayer",
        "openhands.dev": "openhands",
        "manus.im": "manus",
        "inngest.com": "inngest",
        "ghuntley.com": "ghuntley",
        "sawinyh.com": "sawinyh",
        "www.preprints.org": "preprints",
        "preprints.org": "preprints",
        "code.claude.com": "anthropic",
        "claude.com": "anthropic",
        "inspect.aisi.org.uk": "uk-aisi",
        "opentelemetry.io": "opentelemetry",
        "www.tbench.ai": "terminal-bench",
        "tbench.ai": "terminal-bench",
        "skills.sh": "skills.sh",
        "www.12factoragentops.com": "12factoragentops",
        "12factoragentops.com": "12factoragentops",
    }
    for h, src in mapping.items():
        if host == h or host.endswith("." + h):
            return src
    # GitHub repos: try owner/repo -> owner
    if "github.com" in host:
        parts = urlparse(url).path.strip("/").split("/")
        if len(parts) >= 1 and parts[0]:
            return parts[0].lower()
    # Fall back to the bare registrable domain
    parts = host.split(".")[-2:] if "." in host else [host]
    return ".".join(parts)


def parse_readme(readme_path: Path) -> list[dict]:
    text = readme_path.read_text(encoding="utf-8")
    entries: list[dict] = []
    current_category_slug = None
    current_category_name = None
    current_intro: list[str] = []
    section_intros: dict[str, list[str]] = {}

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        # Section heading?
        if line.startswith("## "):
            heading = line[3:].strip()
            match = next((s for s in SECTIONS if s[0] == heading), None)
            if match:
                current_category_name, current_category_slug, _ = match
                current_intro = []
                section_intros[current_category_slug] = current_intro
            else:
                current_category_slug = None
                current_category_name = None
            continue
        # Skip non-content lines when not in a section
        if current_category_slug is None:
            continue
        # Skip comments and prose between entries
        if line.startswith("<!--"):
            continue
        # Lines that start with words (prose, like the Benchmarks intro)
        if not line.startswith("- "):
            current_intro.append(line)
            continue
        m = ENTRY_RE.match(line)
        if not m:
            continue
        title = m.group("title").strip()
        url = m.group("url").strip()
        desc = m.group("desc").strip()
        entries.append(
            {
                "title": title,
                "url": url,
                "description": desc,
                "category": current_category_slug,
                "category_name": current_category_name,
                "kind": infer_kind(url, title, current_category_slug),
                "source": infer_source(url, title),
            }
        )
    return entries, section_intros


def ensure_unique_slug(base: str, used: set[str]) -> str:
    slug = base
    i = 2
    while slug in used:
        slug = f"{base}-{i}"
        i += 1
    used.add(slug)
    return slug


def write_resource(entry: dict, out_dir: Path, used_slugs: set[str]) -> Path:
    base = slugify(entry["title"])
    slug = ensure_unique_slug(base, used_slugs)
    # Front matter
    fm = [
        "---",
        f'title: {yaml_quote(entry["title"])}',
        f'link: {entry["url"]}',
        f'category: [{entry["category"]}]',
        f'resource_kind: {entry["kind"]}',
        f'source: [{yaml_quote(entry["source"])}]',
        f'added: {date.today().isoformat()}',
        "---",
        "",
        entry["description"],
        "",
    ]
    out_path = out_dir / f"{slug}.md"
    out_path.write_text("\n".join(fm), encoding="utf-8")
    return out_path


def yaml_quote(value: str) -> str:
    """Quote a string for YAML if it contains characters that need quoting."""
    if value == "" or any(c in value for c in [":", "#", "@", "`", "'", '"', "{", "}", "[", "]", ",", "&", "*", "?", "|", "<", ">", "=", "!"]):
        return '"' + value.replace('"', '\\"') + '"'
    return value


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: migrate_readme.py <readme_path> <output_dir>", file=sys.stderr)
        return 2
    readme_path = Path(argv[1])
    out_dir = Path(argv[2])
    if not readme_path.is_file():
        print(f"not a file: {readme_path}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    entries, intros = parse_readme(readme_path)
    used: set[str] = set()
    for entry in entries:
        write_resource(entry, out_dir, used)
    # Sidecar: section intros
    intro_path = out_dir / "_section_intros.json"
    import json
    intro_path.write_text(json.dumps(intros, indent=2), encoding="utf-8")
    print(f"wrote {len(entries)} resources to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))