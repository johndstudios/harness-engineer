---
title: "About"
description: "About Harness Engineer"
---

Harness Engineer is a curated directory of resources for **harness engineering** — the practice of shaping the environment around AI agents so they can work reliably.

It builds on the [Awesome Harness Engineering](https://github.com/walkinglabs/awesome-harness-engineering) list, originally curated by the [Walking Labs](https://github.com/walkinglabs) community and released under CC0. This site keeps the same content as structured, searchable data and adds:

- Per-resource pages with tags, source, and category.
- Client-side full-text search.
- Category and kind filters.
- A "recently added" feed and RSS.
- A contribution pipeline where new entries open as pull requests for review.

## Content model

Each resource is one Markdown file in [`content/resources/`](https://github.com/johndstudios/harness-engineer/tree/main/content/resources) with structured front matter:

```yaml
---
title: Effective harnesses for long-running agents
link: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
category: [foundations]
resource_kind: [article]
source: [anthropic]
added: 2026-08-02
date: 2026-08-02
tags: [context-engineering, long-running, handoff]
---
Anthropic's core article on initializer agents, feature lists, `init.sh`,
self-verification, and handoff artifacts across many context windows.
```

The `README.md` at the repo root is generated from the same data so the project still reads as a classic awesome list for people who want the raw Markdown view.

## License

Content on this site is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The upstream awesome list was released under CC0, which is compatible with this license.

## Source code

Site code and content live at [johndstudios/harness-engineer](https://github.com/johndstudios/harness-engineer). Issues and pull requests are welcome.