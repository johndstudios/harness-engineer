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
- For benchmarks only: `task_type`, `environment`, `open_source`, `leaderboard` — these power the [comparison table](/benchmarks/).

Then open a pull request. CI will run link-check and front-matter lint and post a preview deploy URL to the PR comment so reviewers can see how the entry renders before merging.

### Which path should I use?

- **Form** — easiest, no Git or Hugo knowledge needed. Good for adding one resource at a time.
- **Manual PR** — better when you're adding multiple resources at once, editing existing entries, or changing the site itself.

### 2. Submission form (low barrier)

Coming in phase 2: a form on this page that opens a PR for you. No Git knowledge needed.

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