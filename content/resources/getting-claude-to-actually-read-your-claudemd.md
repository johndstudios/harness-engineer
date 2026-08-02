---
title: Getting Claude to Actually Read Your CLAUDE.md
link: https://humanlayer.dev/blog/stop-claude-from-ignoring-your-claude-md
category: [context]
resource_kind: article
source: ["humanlayer"]
added: 2026-08-02
date: 2026-08-02
tags: ["agent-files"]
---

Tactical pattern for CLAUDE.md/AGENTS.md files: wrap task-specific instructions in conditional `<important if=...>` blocks so the model applies the right rules at the right time instead of treating a long file as optional. Ships with an `improve-claude-md` skill.
