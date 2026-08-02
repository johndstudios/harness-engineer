---
title: An update on recent Claude Code quality reports
link: https://www.anthropic.com/engineering/april-23-postmortem
category: [evals]
resource_kind: article
source: ["anthropic"]
added: 2026-08-02
date: 2026-08-02
tags: ["evals", "coding-agents", "quality"]
---

Postmortem of three separate changes that caused perceived Claude Code degradation — a reasoning-effort default change, a cache-optimization bug that dropped thinking history every turn, and a verbosity prompt that hurt coding quality — illustrating how harness changes slip past unit/e2e review and the eval/rollout practices needed to catch them.
