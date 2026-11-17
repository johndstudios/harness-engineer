# Contributing

Thanks for helping improve Harness Engineer.

## What belongs here

Please submit resources that are directly useful for designing, evaluating,
or operating agent harnesses. Good additions usually focus on one or more of:

- Context engineering and working-state management
- Tool design, tool calling, and environment control
- Evals, grading, benchmarking, or observability
- Long-running agents, resumability, retries, or orchestration
- Repo-local instructions such as `AGENTS.md`, specs, or workflow scaffolding
- Reference implementations that make harness design inspectable

Generic AI news, model launch posts, or broad agent-framework marketing pages
usually do not belong unless they contain concrete harness-level guidance.

## Quality bar

When proposing a new entry, prefer resources that are:

- Primary sources or original technical write-ups
- Non-duplicative with an existing entry
- Still available and reachable
- Specific enough that the description can explain why the resource matters

## Entry format

Resources live in `content/resources/` as Markdown files with YAML front
matter. Create one file per resource:

```md
---
title: Effective harnesses for long-running agents
link: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
category: [foundations]
resource_kind: article
source: [anthropic]
added: 2026-08-02
date: 2026-08-02
tags: ["context-engineering"]
---
Short description focused on why this matters for harness engineering.
```

### Required fields

- `title` — the resource title (string)
- `link` — the canonical URL of the resource (string)
- `category` — one of: `courses`, `foundations`, `context`, `constraints`,
  `specs`, `evals`, `benchmarks`, `runtimes` (single-item list)
- `resource_kind` — one of: `article`, `tool`, `benchmark`, `course`, `spec`,
  `podcast`, `video`, `paper`
- `source` — short author/origin slug, e.g. `anthropic`, `openai`, `langchain`
  (single-item list)
- `added` — date the resource was added, `YYYY-MM-DD`
- `date` — same value as `added` (Hugo uses it for ordering and RSS)

### Optional fields

- `tags` — list of tags from the controlled vocabulary in `data/tags.yml`
- `highlight: true` — curated "start here" entry for its category
- `lifecycle`, `superseded_by`, `reviewed`, `lifecycle_note` — see below

## Keeping the directory fresh

Harness engineering moves fast, so entries expire instead of piling up. Nothing is deleted: an entry's `lifecycle` field moves it through these states.

| `lifecycle` | Meaning | Where it shows |
|---|---|---|
| `active` (default, omit the field) | Current and recommended | Listings, README |
| `stale` | Still useful context, but the field has moved on | Listings with a *may be outdated* badge |
| `superseded` | Newer work replaces it; requires `superseded_by: <slug>` | [Archive](https://johndstudios.github.io/harness-engineer/archive/), page links to the replacement |
| `archived` | Dead link or abandoned project | [Archive](https://johndstudios.github.io/harness-engineer/archive/), links go to a Wayback snapshot |

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

## Placement

- Put the entry in the most specific category that fits. The valid categories
  are listed above.
- If a new category is genuinely needed, open an issue first to discuss it.
- Avoid adding the same resource to multiple categories.

## Before opening a PR

- Confirm the link works.
- Confirm the resource is actually about harness-relevant concerns.
- Confirm the description is accurate and not promotional.
- Check for duplicates in `content/resources/`.
- Keep the diff focused.
- Run the linter: `npm run lint`.
- Optionally build the site locally: `hugo --gc --minify`.
- No need to regenerate `README.md`; that happens automatically after merge.

## Pull requests

Small, focused pull requests are easiest to review.

If you are adding several links at once, include a short note explaining the
theme that connects them and why they belong in the chosen category.

CI will run link-checking and front-matter validation on your PR and post a
preview deploy URL as a comment so you and reviewers can see how the entry
renders on the live site before merging.

## License

By contributing you agree your content is licensed under
[CC BY-SA 4.0](./LICENSE).