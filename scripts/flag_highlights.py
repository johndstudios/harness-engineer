#!/usr/bin/env python3
"""Flag curated 'start here' highlights by adding `highlight: true` to selected
resource files. Run once during Phase 3 setup. Idempotent.

Usage: scripts/flag_highlights.py <resources_dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

# Curated "start here" slugs per category. Chosen for being primary-source,
# widely cited, and giving a newcomer the fastest grounding in the category.
HIGHLIGHTS = {
    "foundations": [
        "harness-engineering-leveraging-codex-in-an-agent-first-world",  # OpenAI flagship
        "effective-harnesses-for-long-running-agents",                   # Anthropic core
        "the-anatomy-of-an-agent-harness",                               # LangChain framing
    ],
    "context": [
        "effective-context-engineering-for-ai-agents",                   # Anthropic
        "context-engineering-for-ai-agents-lessons-from-building-manus",  # Manus
        "writing-a-good-claudemd",                                       # CLAUDE.md guide
    ],
    "constraints": [
        "beyond-permission-prompts-making-claude-code-more-secure-and-autonomous",
        "writing-effective-tools-for-agents",
        "mitigating-prompt-injection-attacks-in-software-agents",
    ],
    "specs": [
        "agentsmd",
        "12-factor-agents",
        "understanding-spec-driven-development-kiro-spec-kit-and-tessl",
    ],
    "evals": [
        "demystifying-evals-for-ai-agents",
        "how-to-evaluate-agent-skills-and-why-you-should",
        "inspect-ai",
    ],
    "benchmarks": [
        "swe-bench-verified",
        "osworld",
        "webarena",
    ],
    "runtimes": [
        "swe-agent",
        "agent-frameworks-runtimes-and-harnesses-oh-my",
        "deepagents",
    ],
    # courses only has one resource; flag it.
    "courses": [
        "walkinglabslearn-harness-engineering",
    ],
}


def add_highlight(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return False
    fm_text = m.group(1)
    body = m.group(2)
    if re.search(r"^highlight:", fm_text, re.M):
        return False  # already flagged
    # Insert highlight: true before tags: or at end of front matter
    lines = fm_text.splitlines()
    insert_at = len(lines)
    for i, line in enumerate(lines):
        if line.strip().startswith("tags:"):
            insert_at = i
            break
    if not body.startswith("\n\n"):
        body = "\n\n" + body.lstrip("\n")
    lines.insert(insert_at, "highlight: true")
    new_text = "---\n" + "\n".join(lines) + "\n---" + body
    path.write_text(new_text, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    resources_dir = Path(argv[1] if len(argv) > 1 else "content/resources")
    if not resources_dir.is_dir():
        print(f"error: not a directory: {resources_dir}", file=sys.stderr)
        return 2
    flagged = 0
    total = 0
    for slugs in HIGHLIGHTS.values():
        total += len(slugs)
    for slugs in HIGHLIGHTS.values():
        for slug in slugs:
            path = resources_dir / f"{slug}.md"
            if not path.exists():
                print(f"warning: not found: {path}", file=sys.stderr)
                continue
            if add_highlight(path):
                flagged += 1
    print(f"flagged {flagged} highlights (of {total} planned)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))