#!/usr/bin/env python3
"""Add heuristic tags to resource files based on their description.

Looks at the title + description and appends a `tags:` line with up to 4
lowercase tags drawn from a controlled vocabulary. Idempotent: overwrites any
existing tags with the heuristic set (safe because Phase 3 establishes tags).

Usage: scripts/tag_resources.py <resources_dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

# Keyword -> tag mapping. Order matters: more specific tags win.
TAG_RULES = [
    ("context engineering", "context-engineering"),
    ("context window", "context-engineering"),
    ("working memory", "context-engineering"),
    ("kv-cache", "context-engineering"),
    ("claude.md", "agent-files"),
    ("agents.md", "agent-files"),
    ("agent.md", "agent-files"),
    ("init.sh", "agent-files"),
    ("repo-local instructions", "agent-files"),
    ("instruction files", "agent-files"),
    ("spec-driven", "specs"),
    ("spec kit", "specs"),
    ("spec-driven-development", "specs"),
    ("12 factor", "specs"),
    ("12-factor", "specs"),
    ("eval", "evals"),
    ("grading", "evals"),
    ("trace grading", "evals"),
    ("trajectory", "evals"),
    ("verifier", "evals"),
    ("verification", "evals"),
    ("observability", "observability"),
    ("telemetry", "observability"),
    ("opentelemetry", "observability"),
    ("tracing", "observability"),
    ("monitoring", "observability"),
    ("session replay", "observability"),
    ("prompt injection", "security"),
    ("sandboxing", "security"),
    ("sandbox", "security"),
    ("safe autonomy", "security"),
    ("guardrail", "security"),
    ("policy", "security"),
    ("capabilities", "security"),
    ("long-running", "long-running"),
    ("long-running agent", "long-running"),
    ("resumab", "long-running"),
    ("pause-resume", "long-running"),
    ("retry", "long-running"),
    ("orchestration", "orchestration"),
    ("multi-agent", "multi-agent"),
    ("multi-agent system", "multi-agent"),
    ("coordination", "multi-agent"),
    ("delegation", "orchestration"),
    ("tool", "tools"),
    ("tool calling", "tools"),
    ("tool use", "tools"),
    ("mcp", "mcp"),
    ("model context protocol", "mcp"),
    ("benchmark", "benchmarks"),
    ("leaderboard", "benchmarks"),
    ("coding agent", "coding-agents"),
    ("coding", "coding-agents"),
    ("software engineering", "coding-agents"),
    ("computer use", "computer-use"),
    ("browser", "web-agents"),
    ("web agent", "web-agents"),
    ("web navigation", "web-agents"),
    ("planning", "planning"),
    ("retrieval", "retrieval"),
    ("search", "search"),
    ("reference implementation", "reference-implementation"),
    ("runtime", "runtimes"),
    ("framework", "frameworks"),
    ("handoff", "handoff"),
    ("condensat", "compression"),
    ("backpressure", "compression"),
    ("brownfield", "brownfield"),
    ("greenfield", "greenfield"),
    ("quality", "quality"),
    ("checkpoints", "checkpoints"),
]

MAX_TAGS = 4


def classify(title: str, desc: str) -> list[str]:
    text = (title + " " + desc).lower()
    tags: list[str] = []
    seen = set()
    for keyword, tag in TAG_RULES:
        if keyword in text and tag not in seen:
            tags.append(tag)
            seen.add(tag)
            if len(tags) >= MAX_TAGS:
                break
    return tags


def update_file(path: Path, tags: list[str]) -> bool:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return False
    fm_text = m.group(1)
    body = m.group(2)
    lines = fm_text.splitlines()
    # Remove existing tags line
    lines = [l for l in lines if not l.strip().startswith("tags:")]
    if tags:
        tag_value = "[" + ", ".join(f'"{t}"' for t in tags) + "]"
        lines.append(f"tags: {tag_value}")
    if not body.startswith("\n\n"):
        body = "\n\n" + body.lstrip("\n")
    new_text = "---\n" + "\n".join(lines) + "\n---" + body
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
        text = path.read_text(encoding="utf-8")
        m = FRONT_MATTER_RE.match(text)
        if not m:
            continue
        fm_text = m.group(1)
        body = m.group(2)
        title = ""
        desc = body.strip().splitlines()[0] if body.strip() else ""
        for line in fm_text.splitlines():
            if line.strip().startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
        tags = classify(title, desc)
        if update_file(path, tags):
            changed += 1
    print(f"tagged {changed}/{total} resources")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))