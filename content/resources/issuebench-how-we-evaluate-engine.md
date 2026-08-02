---
title: IssueBench - How We Evaluate Engine
link: https://blog.langchain.com/issuebench-how-we-evaluate-engine
category: [evals]
resource_kind: article
source: ["langchain"]
added: 2026-08-02
date: 2026-08-02
tags: ["evals", "security", "benchmarks"]
---

Internal benchmark for an agent that inspects production traces to identify and cluster failures, using synthetic traces with known ground truth across 15 issue categories (PII leak, hallucination, guardrail bypass, agent looping, etc.) and scoring classification, category assignment, existing-issue attachment, and new-issue grouping — illustrating how to evaluate the meta-agent that evaluates agents.
