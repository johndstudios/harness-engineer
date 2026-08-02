---
title: Towards Automating Eval Engineering
link: https://blog.langchain.com/towards-automating-eval-engineering
category: [evals]
resource_kind: article
source: ["langchain"]
added: 2026-08-02
date: 2026-08-02
tags: ["evals", "coding-agents"]
---

Describes an 'Eval Engineering Skill' for coding agents that mines a repository and optional traces to propose, interview the user about, and generate executable Harbor-format evals (instruction + Dockerfile environment + verifier), codifying the mine-traces → build-eval → improve-agent → rerun loop and treating evals as training data for harness engineering.
