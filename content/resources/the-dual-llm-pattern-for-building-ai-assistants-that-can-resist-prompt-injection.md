---
title: The Dual LLM pattern for building AI assistants that can resist prompt injection
link: https://simonwillison.net/2023/Apr/25/dual-llm-pattern/
category: [constraints]
resource_kind: article
source: ["simonwillison"]
added: 2026-08-02
date: 2026-08-02
tags: ["security", "tools"]
---

Proposes splitting an agent into a privileged, tool-calling LLM and a quarantined LLM that handles untrusted content, with a non-LLM controller mediating symbolic variables between them. A concrete, implementable architecture for sandboxing untrusted context that later influenced Google DeepMind's CaMeL paper.
