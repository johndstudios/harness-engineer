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
tags: [context, long-running, handoff]
---
Short description focused on why this matters for harness engineering.
```

### Required fields

- `title` — the resource title (string)
- `link` — the canonical URL of the resource (string)
- `category` — one of: `courses`, `foundations`, `context`, `constraints`,
  `specs`, `evals`, `benchmarks`, `runtimes` (single-item list)
- `resource_kind` — one of: `article`, `tool`, `benchmark`, `course`, `spec`
- `source` — short author/origin slug, e.g. `anthropic`, `openai`, `langchain`
  (single-item list)
- `added` — date the resource was added, `YYYY-MM-DD`

### Optional fields

- `tags` — list of lower-case tags describing the resource's topics

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
- Run the build locally to verify the site still builds:
  ```bash
  hugo --gc --minify
  ```

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