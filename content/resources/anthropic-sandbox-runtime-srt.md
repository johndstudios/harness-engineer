---
title: Anthropic Sandbox Runtime (srt)
link: https://github.com/anthropic-experimental/sandbox-runtime
category: [constraints]
resource_kind: tool
source: ["anthropic-experimental"]
added: 2026-08-02
date: 2026-08-02
tags: ["security", "mcp", "runtimes"]
---

Open-sourced lightweight sandboxing runtime from Claude Code that enforces filesystem and network restrictions on arbitrary processes using native OS primitives (Seatbelt on macOS, bubblewrap on Linux, WFP on Windows) with proxy-based egress filtering, mandatory-deny paths for shell/git config, and a clear JSON policy schema — directly reusable for sandboxing MCP servers and agent-spawned processes.
