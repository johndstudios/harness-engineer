---
title: "How we built Claude Code auto mode: a safer way to skip permissions"
link: https://www.anthropic.com/engineering/claude-code-auto-mode
category: [constraints]
resource_kind: article
source: ["anthropic"]
added: 2026-08-02
date: 2026-08-02
tags: ["security", "tools"]
---

Detailed design of a model-based transcript classifier that substitutes for human approval on Claude Code tool calls, including a two-stage fast-filter + reasoning pipeline, reasoning-blind construction to resist prompt injection, deny-and-continue behavior, and honest false-negative reporting. A concrete reference for automated permission gating inside an agent harness.
