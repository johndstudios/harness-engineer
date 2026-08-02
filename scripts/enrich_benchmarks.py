#!/usr/bin/env python3
"""Enrich benchmark resource files with comparison-table front matter fields.

Adds optional fields to every content/resources/*.md where category=[benchmarks]:
  - task_type:     coding | web | computer-use | tool-use | reasoning | planning | multi-agent | search | conversation | security | economics | multimodal | generic
  - environment:   terminal | browser | desktop | os | ide | api | sandbox | mixed | web
  - open_source:   true | false
  - leaderboard:   <URL or ''>

Run once during Phase 3 setup. Idempotent: re-running overwrites these four
fields with fresh heuristic values (safe because they are optional/derived).

Usage: scripts/enrich_benchmarks.py <resources_dir>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
NEW_FIELDS = ("task_type", "environment", "open_source", "leaderboard")


def parse(text: str) -> tuple[dict, list[str], str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, [], text
    fm_lines = m.group(1).splitlines()
    body = m.group(2)
    return {}, fm_lines, body


def fm_get(fm_lines: list[str], key: str) -> str | None:
    for line in fm_lines:
        if line.strip().startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return None


def fm_has(fm_lines: list[str], key: str) -> bool:
    return any(l.strip().startswith(key + ":") for l in fm_lines)


def classify(title: str, url: str, desc: str) -> dict:
    # Use title + description for classification, NOT the URL — URLs like
    # swebench.com contain "web" and would trigger false positives.
    text = (title + " " + desc).lower()
    url_l = url.lower()

    # task_type
    if any(k in text for k in ("software engineering", "swe-bench", "swe-agent", "leetcode", "codegen", "coding agent", "coding benchmark", "continuous software evolution", "evoclaw")):
        task_type = "coding"
    elif any(k in text for k in ("computer use", "computer agent", "osworld", "desktop", "virtual agent", "computer-use")):
        task_type = "computer-use"
    elif any(k in text for k in ("web", "browser", "webarena", "workarena", "browsergym", "assistantbench", "browsecomp", "clawbench")):
        task_type = "web"
    elif any(k in text for k in ("mcp", "tool-use", "tool use", "tool calling")):
        task_type = "tool-use"
    elif any(k in text for k in ("multi-agent", "magic", "collaboration", "coordination")):
        task_type = "multi-agent"
    elif any(k in text for k in ("security", "vulnerability", "sec-bench")):
        task_type = "security"
    elif any(k in text for k in ("economic", "occupation", "income", "clawwork")):
        task_type = "economics"
    elif any(k in text for k in ("planning", "travelplanner", "planning within multiple constraints")):
        task_type = "planning"
    elif any(k in text for k in ("search", "locating hard-to-find")):
        task_type = "search"
    elif any(k in text for k in ("role-playing", "conversation", "character")):
        task_type = "conversation"
    elif any(k in text for k in ("multimodal", "visual", "image", "screenshot", "vlm", "embodied")):
        task_type = "multimodal"
    else:
        task_type = "generic"

    # environment
    if any(k in text for k in ("terminal", "shell", "filesystem", "verification-heavy", "terminal-bench", "harbor")):
        environment = "terminal"
    elif any(k in text for k in ("browser", "web", "web-facing", "online")):
        environment = "browser"
    elif any(k in text for k in ("desktop", "computer", "ubuntu", "windows", "macos", "osworld")):
        environment = "desktop"
    elif any(k in text for k in ("os", "operating system")):
        environment = "os"
    elif any(k in text for k in ("api", "server", "mcp server")):
        environment = "api"
    elif any(k in text for k in ("sandbox", "containerized", "isolated")):
        environment = "sandbox"
    elif any(k in text for k in ("ide", "editor")):
        environment = "ide"
    elif any(k in text for k in ("web environment", "self-hostable web", "web environment")):
        environment = "browser"
    elif task_type == "coding":
        environment = "terminal"
    elif task_type == "web":
        environment = "browser"
    elif task_type == "computer-use":
        environment = "desktop"
    else:
        environment = "mixed"

    # open_source: heuristic — github.com URLs are open source
    open_source = "true" if "github.com" in url_l else "false"

    # leaderboard: if the URL itself looks like a leaderboard page, use it;
    # otherwise leave blank.
    leaderboard = ""
    if any(k in text for k in ("leaderboard", "elo", "arena", "rank")):
        leaderboard = url

    return {
        "task_type": task_type,
        "environment": environment,
        "open_source": open_source,
        "leaderboard": leaderboard,
    }


def update_file(path: Path, classification: dict) -> bool:
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return False
    fm_text = m.group(1)
    body = m.group(2)
    fm_lines = fm_text.splitlines()

    # Remove existing NEW_FIELDS lines (idempotent)
    kept = [l for l in fm_lines if not any(l.strip().startswith(f + ":") for f in NEW_FIELDS)]

    # Append the classification fields before the closing (i.e. at the end of FM)
    # Insert before any existing `tags:` if present, else at end.
    insert_at = len(kept)
    for i, line in enumerate(kept):
        if line.strip().startswith("tags:"):
            insert_at = i
            break
    new_lines = []
    if classification["leaderboard"]:
        new_lines.append(f'leaderboard: "{classification["leaderboard"]}"')
    else:
        new_lines.append('leaderboard: ""')
    new_lines.append(f'task_type: {classification["task_type"]}')
    new_lines.append(f'environment: {classification["environment"]}')
    new_lines.append(f'open_source: {classification["open_source"]}')

    kept = kept[:insert_at] + new_lines + kept[insert_at:]

    # Ensure body starts with a blank line so front matter closes cleanly.
    if not body.startswith("\n\n"):
        body = "\n\n" + body.lstrip("\n")
    new_text = "---\n" + "\n".join(kept) + "\n---" + body
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
        text = path.read_text(encoding="utf-8")
        m = FRONT_MATTER_RE.match(text)
        if not m:
            continue
        fm_text = m.group(1)
        if "category: [benchmarks]" not in fm_text:
            continue
        total += 1
        title = ""
        link = ""
        desc = m.group(2).strip().splitlines()[0] if m.group(2).strip() else ""
        for line in fm_text.splitlines():
            if line.strip().startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
            elif line.strip().startswith("link:"):
                link = line.split(":", 1)[1].strip()
        classification = classify(title, link, desc)
        if update_file(path, classification):
            changed += 1

    print(f"enriched {changed}/{total} benchmark files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))