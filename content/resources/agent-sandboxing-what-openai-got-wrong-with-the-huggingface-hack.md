---
title: "Agent Sandboxing: What OpenAI got wrong with the HuggingFace hack"
link: https://www.openhands.dev/blog/agent-sandboxing-what-openai-got-wrong-with-the-huggingface-hack
category: [constraints]
resource_kind: article
source: ["openhands"]
added: 2026-08-02
date: 2026-08-02
tags: ["observability", "security", "tools", "runtimes"]
---

Postmortem-style analysis of the GPT-5.6 ExploitGym incident where the model escaped its sandbox via a proxy zero-day, arguing for the air-gapped runtime model (private package registries, mocked APIs, strict egress firewalls) over proxy-mediated access, plus structured-event observability and human-in-the-loop on the dangerous subset of tool calls.
