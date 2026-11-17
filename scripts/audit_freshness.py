#!/usr/bin/env python3
"""Audit resources for staleness and produce a freshness report.

Reads content/resources/*.md front matter and the crawler's history in
data/enriched/*.json, then sorts resources into action buckets:

  dead        Hard failure (404/410, DNS, TLS, connection) for DEAD_AFTER or
              more consecutive weekly crawls. Safe to archive automatically
              (--apply-archive); the link is replaced by a Wayback snapshot on
              the site.
  unreachable Soft failure (403/429/5xx, timeouts) for several crawls. Often
              bot-blocking rather than a dead page, so it is reported only.
  repo        GitHub repo archived upstream, or no push for INACTIVE_DAYS.
  moved       The URL now redirects somewhere materially different.
  review      Not reviewed (or added) within the category's review window.
  stale       Already marked lifecycle: stale and waiting for a decision.

Nothing here deletes a resource. Expiry is a front-matter state change:
`lifecycle: stale | superseded | archived` (see CONTRIBUTING.md).

Usage:
  scripts/audit_freshness.py [--report out.md] [--json out.json]
                             [--apply-archive] [--today YYYY-MM-DD]

Exit status is 0 unless the inputs are missing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from datetime import date, datetime
from pathlib import Path


RESOURCES_DIR = Path("content/resources")
ENRICHED_DIR = Path("data/enriched")

# Weekly crawls of consecutive hard failure before a resource is archived.
DEAD_AFTER = 4
# Weekly crawls of consecutive soft failure before it is reported.
UNREACHABLE_AFTER = 4
# A GitHub repo with no push for this long is reported as inactive.
INACTIVE_DAYS = 365
# Days between human reviews, by category. Fast-moving areas get less time.
REVIEW_WINDOW_DAYS = {
    "runtimes": 180,
    "benchmarks": 180,
    "evals": 270,
}
DEFAULT_REVIEW_WINDOW_DAYS = 365

HARD_HTTP = {404, 410, 451}
HARD_ERROR_MARKERS = (
    "name resolution", "nodename nor servname", "name or service not known",
    "getaddrinfo", "certificate", "ssl", "connection refused",
)
EXPIRED = {"superseded", "archived"}

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)
MARKER = "<!-- freshness-report -->"


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


def parse_day(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except ValueError:
        return None


def normalize_url(url: str) -> str:
    p = urllib.parse.urlparse(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/") or "/"
    return f"{host}{path}"


def is_hard_failure(info: dict) -> bool:
    status = int(info.get("http_status") or 0)
    if status in HARD_HTTP:
        return True
    if status == 0:
        err = (info.get("error") or "").lower()
        return any(m in err for m in HARD_ERROR_MARKERS)
    return False


def failure_label(info: dict) -> str:
    status = int(info.get("http_status") or 0)
    if status:
        return f"HTTP {status}"
    err = info.get("error") or "fetch error"
    m = re.search(r"\] (.*?)(?: \(_ssl|>|$)", err)
    return (m.group(1) if m else err)[:80]


def audit(today: date) -> dict:
    buckets: dict[str, list[dict]] = {k: [] for k in
                                      ("dead", "unreachable", "repo", "moved", "review", "stale")}
    counts = {"total": 0, "active": 0, "stale": 0, "superseded": 0, "archived": 0}

    for path in sorted(RESOURCES_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        slug = path.stem
        fm = parse_front_matter(path.read_text(encoding="utf-8"))
        lifecycle = fm.get("lifecycle", "active") or "active"
        counts["total"] += 1
        counts[lifecycle] = counts.get(lifecycle, 0) + 1
        if lifecycle in EXPIRED:
            continue

        info: dict = {}
        enriched_path = ENRICHED_DIR / f"{slug}.json"
        if enriched_path.is_file():
            info = json.loads(enriched_path.read_text(encoding="utf-8"))

        base = {"slug": slug, "title": fm.get("title", slug), "link": fm.get("link", ""),
                "category": fm.get("category", "")}

        # Link health, using the crawler's run-over-run history.
        fails = int(info.get("consecutive_failures") or 0)
        if info.get("status") not in (None, "ok"):
            # Crawls from before history tracking count as a single failure.
            fails = max(fails, 1)
            entry = {**base, "failures": fails, "reason": failure_label(info),
                     "since": (info.get("first_failed_at") or info.get("crawled_at") or "")[:10]}
            if is_hard_failure(info) and fails >= DEAD_AFTER:
                buckets["dead"].append(entry)
            elif fails >= UNREACHABLE_AFTER or is_hard_failure(info):
                buckets["unreachable"].append(entry)

        # GitHub repo health.
        if info.get("github_archived"):
            buckets["repo"].append({**base, "reason": "repository archived upstream"})
        else:
            pushed = parse_day(info.get("github_pushed"))
            if pushed and (today - pushed).days > INACTIVE_DAYS:
                buckets["repo"].append({**base, "reason": f"no push since {pushed.isoformat()}"})

        # Moved content: redirect to a different page.
        final_url = info.get("final_url") or ""
        if info.get("status") == "ok" and final_url and base["link"] and \
                normalize_url(final_url) != normalize_url(base["link"]):
            buckets["moved"].append({**base, "reason": f"redirects to {final_url}"})

        # Review cadence.
        reviewed = parse_day(fm.get("reviewed")) or parse_day(fm.get("added"))
        window = REVIEW_WINDOW_DAYS.get(base["category"], DEFAULT_REVIEW_WINDOW_DAYS)
        if reviewed and (today - reviewed).days > window:
            buckets["review"].append({**base, "reason": f"last reviewed {reviewed.isoformat()} "
                                                         f"({window}-day window)"})

        if lifecycle == "stale":
            buckets["stale"].append({**base, "reason": fm.get("lifecycle_note", "")})

    return {"date": today.isoformat(), "counts": counts, "buckets": buckets}


SECTIONS = [
    ("dead", "Dead links — auto-archive candidates",
     f"Hard failures for {DEAD_AFTER}+ consecutive weekly crawls. The bot opens a PR "
     "marking these `lifecycle: archived`; the site then links to a Wayback snapshot. "
     "If a page moved, fix `link` in that PR instead."),
    ("unreachable", "Unreachable — check by hand",
     "Soft failures (403/429/5xx/timeouts) are often bot-blocking, not dead pages. "
     "Open the link in a browser; archive only if it is really gone."),
    ("repo", "Repository health",
     "Archived or long-inactive GitHub repos. Consider `lifecycle: stale`, or "
     "`superseded` with `superseded_by:` if a successor is listed."),
    ("moved", "Moved content",
     "The URL redirects somewhere materially different. Update `link` if the new "
     "location is the canonical one."),
    ("review", "Review due",
     "Past the category's review window. Re-read it: if it still holds up, set "
     "`reviewed: <today>`; if newer work replaces it, mark it `superseded`; if it "
     "is simply dated, mark it `stale`."),
    ("stale", "Marked stale — awaiting a decision",
     "Refresh (`reviewed: <today>`, drop `lifecycle`), supersede, or archive."),
]


def render_markdown(result: dict, repo_url: str = "") -> str:
    c = result["counts"]
    out = [MARKER, "", f"# Freshness report — {result['date']}", "",
           f"{c['total']} resources: {c.get('active', 0)} active, {c.get('stale', 0)} stale, "
           f"{c.get('superseded', 0)} superseded, {c.get('archived', 0)} archived.", ""]
    any_items = False
    for key, heading, help_text in SECTIONS:
        items = result["buckets"][key]
        if not items:
            continue
        any_items = True
        out += [f"## {heading} ({len(items)})", "", help_text, ""]
        for it in items:
            where = f"[`{it['slug']}`]({repo_url}/blob/main/content/resources/{it['slug']}.md)" \
                if repo_url else f"`{it['slug']}`"
            detail = it.get("reason", "")
            if key in ("dead", "unreachable"):
                detail = f"{it['reason']}, {it['failures']} crawl(s) in a row since {it['since']}"
            out.append(f"- [ ] {where} — [{it['title']}]({it['link']}) · {detail}".rstrip(" ·"))
        out.append("")
    if not any_items:
        out += ["Nothing needs attention this week. ✅", ""]
    out += ["---", "",
            "_Generated weekly by `scripts/audit_freshness.py` after the crawl. "
            "This issue is rewritten each run; tick boxes are for your own tracking._", ""]
    return "\n".join(out)


def apply_archive(items: list[dict], today: date) -> list[str]:
    """Mark dead resources `lifecycle: archived` in their front matter."""
    changed = []
    for it in items:
        path = RESOURCES_DIR / f"{it['slug']}.md"
        text = path.read_text(encoding="utf-8")
        m = FRONT_MATTER_RE.match(text)
        if not m:
            continue
        lines = [ln for ln in m.group(1).splitlines()
                 if not ln.startswith(("lifecycle:", "lifecycle_note:"))]
        note = (f"Link unreachable ({it['reason']}) since {it['since']}; "
                f"archived automatically on {today.isoformat()}.").replace('"', "'")
        lines += ["lifecycle: archived", f'lifecycle_note: "{note}"']
        path.write_text("---\n" + "\n".join(lines) + "\n---\n" + m.group(2), encoding="utf-8")
        changed.append(it["slug"])
    return changed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--report", help="write the Markdown report here")
    ap.add_argument("--json", help="write the raw result as JSON here")
    ap.add_argument("--apply-archive", action="store_true",
                    help="mark dead resources lifecycle: archived in place")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    ap.add_argument("--repo-url", default="", help="link slugs to files in this GitHub repo")
    args = ap.parse_args(argv[1:])

    if not RESOURCES_DIR.is_dir():
        print(f"error: {RESOURCES_DIR} not found (run from the repo root)", file=sys.stderr)
        return 2
    today = parse_day(args.today) if args.today else date.today()
    if today is None:
        print(f"error: --today must be YYYY-MM-DD, got {args.today!r}", file=sys.stderr)
        return 2

    result = audit(today)
    report = render_markdown(result, args.repo_url.rstrip("/"))
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not args.report and not args.json:
        print(report)

    summary = ", ".join(f"{k}={len(v)}" for k, v in result["buckets"].items())
    print(f"audit {result['date']}: {summary}", file=sys.stderr)

    if args.apply_archive:
        changed = apply_archive(result["buckets"]["dead"], today)
        print(f"archived {len(changed)}: {' '.join(changed)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
