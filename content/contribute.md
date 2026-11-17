---
title: "Contribute"
description: "How to add or update resources on Harness Engineer"
---

Contributions are welcome. Please prefer resources that are:

- Specific about how agents are constrained, evaluated, resumed, observed, or orchestrated.
- Original implementations, primary-source articles, or high-signal technical write-ups.
- Useful to practitioners building real harnesses instead of generic AI commentary.

If two links say the same thing, prefer the more primary, practical, and implementation-oriented one.
## Two ways to contribute

### 1. Submission form (easiest)

Visit [the submit form](/submit/), paste a URL, and click **Open pull request**.
We'll fetch the page, extract the title and description, auto-classify the
category/kind/tags, check for spam and commercial content, and open a PR — all
automatically. You'll get a link to track the PR once it's created.

This is the recommended path for most people adding a single resource.

### 2. Pull request (standard)

Resources are Markdown files in `content/resources/`. Add a new file with
front matter:

```yaml
---
title: Effective harnesses for long-running agents
link: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
category: [foundations]       # one of the categories below
resource_kind: [article]      # article | tool | benchmark | course | spec | podcast | video | paper
source: [anthropic]
added: 2026-08-02
date: 2026-08-02              # mirror of added, for RSS/ordering
tags: [context-engineering, long-running]   # from data/tags.yml
---
Short description focused on why this matters for harness engineering.
```

Categories:

- `courses` — Courses & Learning
- `foundations` — Foundations
- `context` — Context, Memory & Working State
- `constraints` — Constraints, Guardrails & Safe Autonomy
- `specs` — Specs, Agent Files & Workflow Design
- `evals` — Evals & Observability
- `benchmarks` — Benchmarks
- `runtimes` — Runtimes, Harnesses & Reference Implementations

`category`, `resource_kind`, and `source` are single-item lists. Tags must
come from the [controlled vocabulary](https://github.com/johndstudios/harness-engineer/blob/main/data/tags.yml) — see the [tags index](/tags-index/) for the full list with descriptions.

### Optional fields

- `highlight: true` — flag the resource as a curated "start here" entry for its category.
- `lifecycle`, `superseded_by`, `reviewed`, `lifecycle_note` — see [Keeping the directory fresh](#keeping-the-directory-fresh).
- For benchmarks only: `task_type`, `environment`, `open_source`, `leaderboard` — these power the [comparison table](/benchmarks/).

Then open a pull request. CI will run link-check and front-matter lint and post a preview deploy URL to the PR comment so reviewers can see how the entry renders before merging.

### Which path should I use?

- **Form** — easiest, no Git or Hugo knowledge needed. Good for adding one resource at a time.
- **Manual PR** — better when you're adding multiple resources at once, editing existing entries, or changing the site itself.

## Keeping the directory fresh

Harness engineering moves fast, so entries expire instead of piling up. Nothing is deleted: an entry's `lifecycle` field moves it through these states.

| `lifecycle` | Meaning | Where it shows |
|---|---|---|
| `active` (default, omit the field) | Current and recommended | Listings, README |
| `stale` | Still useful context, but the field has moved on | Listings with a *may be outdated* badge |
| `superseded` | Newer work replaces it; requires `superseded_by: <slug>` | [Archive](/archive/), page links to the replacement |
| `archived` | Dead link or abandoned project | [Archive](/archive/), links go to a Wayback snapshot |

Two optional fields support this:

- `reviewed: YYYY-MM-DD` — last time someone confirmed the entry still holds up. Resets the review clock.
- `lifecycle_note: "..."` — one line on why the state changed.

**When you add something newer** that covers the same ground as an existing entry, mark the old one in the same PR:

```yaml
lifecycle: superseded
superseded_by: your-new-resource-slug
lifecycle_note: "Covered more completely by the 2027 follow-up."
```

**Automation:** a weekly crawl checks every link and keeps a history of failures. A [freshness report issue](https://github.com/johndstudios/harness-engineer/issues?q=label%3Afreshness) lists dead or unreachable links, archived or inactive GitHub repos, URLs that now redirect, and entries past their review window (6 months for runtimes and benchmarks, 9 for evals, 12 otherwise). Links that fail hard for four weeks in a row get a bot PR marking them `archived`, and a maintainer merges or fixes it. Spotted something the bot can't, like newer work replacing an entry? [Open a freshness issue](https://github.com/johndstudios/harness-engineer/issues/new?template=outdated-resource.yml) or send a PR.

## Before opening a PR

- Confirm the link works.
- Confirm the resource is actually about harness-relevant concerns.
- Confirm the description is accurate and not promotional.
- Check for duplicates in the directory.
- Keep the diff focused.

## Pull requests

Small, focused pull requests are easiest to review.

If you are adding several links at once, include a short note explaining the theme that connects them and why they belong in the chosen category.

## License

By contributing you agree your content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).