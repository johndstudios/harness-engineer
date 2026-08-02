---
title: Auto mode for Claude Code
link: https://simonwillison.net/2026/Mar/24/auto-mode-for-claude-code/
category: [constraints]
resource_kind: article
source: ["simonwillison"]
added: 2026-08-02
date: 2026-08-02
tags: ["security"]
---

Examines Claude Code's auto-mode, where a separate Sonnet 4.6 classifier gates each action against an extensive JSON allow/soft-deny/block policy. Includes the full default policy and argues why deterministic sandboxing outside the agent layer is more trustworthy than non-deterministic AI permission classifiers.
