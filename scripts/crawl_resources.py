#!/usr/bin/env python3
"""Crawl every resource URL and extract enrichment metadata.

For each content/resources/*.md file, fetches the URL and extracts:
  - title, meta description, author, publish date, language
  - og:image, og:title, og:description
  - canonical URL (resolves redirects)
  - content type (article, github, pdf, video, podcast, etc.)
  - word count + reading time (for articles)
  - heading outline (h1-h3)
  - GitHub stars, forks, topics, last push (for GitHub URLs)
  - last-modified header
  - HTTP status + crawl timestamp

Writes sidecar JSON files to data/enriched/<slug>.json.

Usage: scripts/crawl_resources.py [--dry-run] [--limit N] [--only <slug>]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path


try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: pip install beautifulsoup4 lxml", file=sys.stderr)
    sys.exit(1)


RESOURCES_DIR = Path("content/resources")
OUTPUT_DIR = Path("data/enriched")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
TIMEOUT = 15
DELAY = 1.0  # seconds between fetches (rate limiting)


# ---------------------------------------------------------------------------
# Front matter parsing
# ---------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


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


# ---------------------------------------------------------------------------
# HTTP fetch
# ---------------------------------------------------------------------------

UA = "harness-engineer-crawler/1.0 (+https://github.com/johndstudios/harness-engineer)"


def fetch(url: str) -> dict:
    """Fetch a URL and return {status, headers, body, final_url}."""
    headers = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"}
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        body = resp.read(500_000)  # cap at 500KB
        return {
            "status": resp.status,
            "headers": dict(resp.headers),
            "body": body,
            "final_url": resp.url,
        }
    except urllib.error.HTTPError as e:
        return {"status": e.code, "headers": dict(e.headers), "body": b"", "final_url": url, "error": str(e)}
    except Exception as e:
        return {"status": 0, "headers": {}, "body": b"", "final_url": url, "error": str(e)[:200]}


def fetch_github_api(url: str) -> dict:
    """Fetch from GitHub API with token auth."""
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Enrichment extractors
# ---------------------------------------------------------------------------

def is_github_repo(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if "github.com" not in parsed.netloc:
        return False
    parts = parsed.path.strip("/").split("/")
    # /owner/repo or /owner/repo/...
    return len(parts) >= 2 and parts[0] and parts[1]


def github_repo_path(url: str) -> tuple[str, str] | None:
    parsed = urllib.parse.urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] and parts[1]:
        return parts[0], parts[1]
    return None


def enrich_github(url: str) -> dict:
    """Use GitHub API to enrich a GitHub repo URL."""
    repo_path = github_repo_path(url)
    if not repo_path:
        return {}
    owner, repo = repo_path
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    data = fetch_github_api(api_url)
    if not data:
        return {}
    return {
        "github_stars": data.get("stargazers_count", 0),
        "github_forks": data.get("forks_count", 0),
        "github_open_issues": data.get("open_issues_count", 0),
        "github_topics": data.get("topics", []),
        "github_language": data.get("language"),
        "github_description": data.get("description", ""),
        "github_created": data.get("created_at", "")[:10] if data.get("created_at") else "",
        "github_updated": data.get("updated_at", "")[:10] if data.get("updated_at") else "",
        "github_pushed": data.get("pushed_at", "")[:10] if data.get("pushed_at") else "",
        "github_license": (data.get("license") or {}).get("spdx_id", "") if data.get("license") else "",
        "github_homepage": data.get("homepage", ""),
    }


def extract_meta(soup: BeautifulSoup, name: str) -> str:
    """Extract a <meta name=...> or <meta property=...> value."""
    tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
    return tag.get("content", "").strip() if tag else ""


def extract_jsonld(soup: BeautifulSoup) -> dict:
    """Extract JSON-LD structured data."""
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0] if data else {}
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return {}


def enrich_html(fetch_result: dict) -> dict:
    """Parse HTML and extract metadata."""
    enrichment: dict = {}
    body = fetch_result["body"]
    if not body:
        return enrichment

    try:
        soup = BeautifulSoup(body, "lxml")
    except Exception:
        soup = BeautifulSoup(body, "html.parser")

    # Title
    if soup.title:
        enrichment["fetched_title"] = soup.title.string.strip() if soup.title.string else ""

    # Meta tags
    enrichment["meta_description"] = extract_meta(soup, "description")
    enrichment["og_title"] = extract_meta(soup, "og:title")
    enrichment["og_description"] = extract_meta(soup, "og:description")
    og_image = extract_meta(soup, "og:image")
    if og_image and not og_image.startswith(("http://", "https://")):
        og_image = urllib.parse.urljoin(fetch_result["final_url"], og_image)
    enrichment["og_image"] = og_image
    enrichment["og_type"] = extract_meta(soup, "og:type")
    enrichment["twitter_card"] = extract_meta(soup, "twitter:card")
    twitter_image = extract_meta(soup, "twitter:image")
    if twitter_image and not twitter_image.startswith(("http://", "https://")):
        twitter_image = urllib.parse.urljoin(fetch_result["final_url"], twitter_image)
    enrichment["twitter_image"] = twitter_image

    # Author
    author = extract_meta(soup, "author") or extract_meta(soup, "article:author")
    if not author:
        jsonld = extract_jsonld(soup)
        author = jsonld.get("author", {}).get("name", "") if isinstance(jsonld.get("author"), dict) else ""
    if author:
        enrichment["author"] = author

    # Publish date
    pub_date = extract_meta(soup, "article:published_time") or extract_meta(soup, "datePublished")
    if not pub_date:
        jsonld = extract_jsonld(soup)
        pub_date = jsonld.get("datePublished", "")
    if pub_date:
        enrichment["publish_date"] = pub_date[:10] if len(pub_date) >= 10 else pub_date

    # Language
    if soup.html and soup.html.get("lang"):
        enrichment["language"] = soup.html.get("lang")

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        enrichment["canonical_url"] = canonical.get("href")

    # Word count + reading time (for articles)
    # Strip scripts, styles, and nav before counting words
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    words = text.split()
    enrichment["word_count"] = len(words)
    enrichment["reading_time_min"] = max(1, round(len(words) / 200))

    # Heading outline (h1-h3)
    outline: list[dict] = []
    for heading in soup.find_all(["h1", "h2", "h3"]):
        level = int(heading.name[1])
        text = heading.get_text(strip=True)
        if text and len(text) < 200:
            outline.append({"level": level, "text": text})
    if outline:
        enrichment["outline"] = outline[:30]  # cap at 30 headings

    return enrichment


def classify_content_type(url: str, fetch_result: dict) -> str:
    """Classify the resource by content type."""
    content_type = fetch_result["headers"].get("Content-Type", "").lower()
    if "application/pdf" in content_type:
        return "pdf"
    if is_github_repo(url):
        return "github"
    parsed = urllib.parse.urlparse(url)
    if "youtube.com" in parsed.netloc or "youtu.be" in parsed.netloc:
        return "video"
    if "latent.space" in parsed.netloc or "practicalai.fm" in parsed.netloc:
        return "podcast"
    if "arxiv.org" in parsed.netloc:
        return "paper"
    if "html" in content_type or "text/html" in content_type:
        return "article"
    return "web"


# ---------------------------------------------------------------------------
# Main crawl loop
# ---------------------------------------------------------------------------

def crawl_one(slug: str, link: str) -> dict:
    """Crawl a single resource and return enrichment data."""
    enrichment: dict = {
        "slug": slug,
        "url": link,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
    }

    fetch_result = fetch(link)
    enrichment["http_status"] = fetch_result["status"]
    enrichment["final_url"] = fetch_result["final_url"]
    enrichment["content_type"] = classify_content_type(link, fetch_result)
    enrichment["last_modified"] = fetch_result["headers"].get("Last-Modified", "")

    if fetch_result["status"] != 200:
        enrichment["status"] = "fetch_error"
        enrichment["error"] = fetch_result.get("error", f"HTTP {fetch_result['status']}")
        return enrichment

    # GitHub repos: use API for structured data
    if is_github_repo(link):
        enrichment.update(enrich_github(link))

    # Parse HTML for web pages
    if "html" in fetch_result["headers"].get("Content-Type", "").lower() or fetch_result["status"] == 200:
        enrichment.update(enrich_html(fetch_result))

    return enrichment


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Crawl resource URLs for enrichment.")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, just print")
    parser.add_argument("--limit", type=int, default=0, help="Max resources to crawl (0 = all)")
    parser.add_argument("--only", type=str, default="", help="Only crawl this slug")
    parser.add_argument("--delay", type=float, default=DELAY, help="Delay between fetches (seconds)")
    args = parser.parse_args()

    if not RESOURCES_DIR.is_dir():
        print(f"error: {RESOURCES_DIR} not found", file=sys.stderr)
        return 2

    if not args.dry_run:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    resources: list[tuple[str, str]] = []
    for path in sorted(RESOURCES_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        fm = parse_front_matter(path.read_text(encoding="utf-8"))
        link = fm.get("link", "")
        if not link:
            continue
        slug = path.stem
        if args.only and slug != args.only:
            continue
        resources.append((slug, link))

    if args.limit > 0:
        resources = resources[: args.limit]

    print(f"crawling {len(resources)} resources (delay={args.delay}s)...")
    success = 0
    errors = 0
    for i, (slug, link) in enumerate(resources, 1):
        print(f"[{i}/{len(resources)}] {slug} — {link[:70]}", end="")
        enrichment = crawl_one(slug, link)
        if enrichment.get("status") == "ok":
            success += 1
            print(" OK")
        else:
            errors += 1
            print(f" {enrichment.get('status', 'error')}")

        if not args.dry_run:
            out_path = OUTPUT_DIR / f"{slug}.json"
            out_path.write_text(json.dumps(enrichment, indent=2), encoding="utf-8")

        if i < len(resources):
            time.sleep(args.delay)

    print(f"\n{success} ok, {errors} errors, {len(resources)} total")
    if not args.dry_run:
        print(f"wrote to {OUTPUT_DIR}/")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))