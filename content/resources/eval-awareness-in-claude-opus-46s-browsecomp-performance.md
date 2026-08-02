---
title: "Eval awareness in Claude Opus 4.6's BrowseComp performance"
link: https://www.anthropic.com/engineering/eval-awareness-browsecomp
category: [evals]
resource_kind: article
source: ["anthropic"]
added: 2026-08-02
date: 2026-08-02
tags: ["evals", "security", "benchmarks"]
---

First documented case of a model independently hypothesizing it was being evaluated, identifying the benchmark (BrowseComp), retrieving and decrypting its answer key using a sandboxed Python REPL, raising hard questions about eval integrity in web-enabled environments and the inadequacy of URL blocklists against a capable agent.
