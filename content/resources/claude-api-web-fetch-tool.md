---
title: "Claude API: Web fetch tool"
link: https://simonwillison.net/2025/Sep/10/claude-web-fetch-tool/
category: [constraints]
resource_kind: article
source: ["simonwillison"]
added: 2026-08-02
date: 2026-08-02
tags: ["tools", "search"]
---

Analyzes Anthropic's web_fetch tool design, which deterministically blocks the model from constructing arbitrary URLs and restricts fetches to user-provided or prior-search results, with optional domain allow-lists. A concrete case study in building exfiltration resistance into a tool's harness rather than relying on the model.
