import { assertEquals } from "jsr:@std/assert";
import {
  validateSubmission,
  ALLOWED_CATEGORIES,
} from "../src/validate.js";
import {
  classifyKind,
  classifyCategory,
  classifyTags,
  inferSource,
  detectSpam,
  detectCommercial,
  classify,
} from "../src/classify.js";

// ---------------------------------------------------------------------------
// validate.js
// ---------------------------------------------------------------------------

Deno.test("validateSubmission accepts a URL-only payload", () => {
  const result = validateSubmission({
    link: "https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents",
  });
  assertEquals(result.ok, true);
  assertEquals(result.data.link, "https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents");
  assertEquals(result.data.description, "");
  assertEquals(result.data.category, "");
});

Deno.test("validateSubmission accepts URL + optional fields", () => {
  const result = validateSubmission({
    link: "https://example.com/article",
    description: "A great article about harness engineering.",
    category: "foundations",
    submitter: "octocat",
  });
  assertEquals(result.ok, true);
  assertEquals(result.data.category, "foundations");
  assertEquals(result.data.submitter, "octocat");
});

Deno.test("validateSubmission rejects missing URL", () => {
  const result = validateSubmission({});
  assertEquals(result.ok, false);
  assertEquals(Object.keys(result.fields), ["link"]);
});

Deno.test("validateSubmission rejects non-URL", () => {
  const result = validateSubmission({ link: "not-a-url" });
  assertEquals(result.ok, false);
  assertEquals(result.fields.link, "Must be an http(s) URL");
});

Deno.test("validateSubmission rejects invalid category", () => {
  const result = validateSubmission({ link: "https://example.com", category: "bogus" });
  assertEquals(result.ok, false);
  assertEquals(result.fields.category, "Invalid category");
});

Deno.test("validateSubmission rejects long description", () => {
  const result = validateSubmission({
    link: "https://example.com",
    description: "x".repeat(501),
  });
  assertEquals(result.ok, false);
  assertEquals(result.fields.description, "Keep under 500 characters");
});

// ---------------------------------------------------------------------------
// classify.js — kind
// ---------------------------------------------------------------------------

Deno.test("classifyKind detects arxiv as paper", () => {
  assertEquals(classifyKind("https://arxiv.org/abs/2310.06770"), "paper");
});

Deno.test("classifyKind detects GitHub repos as tool", () => {
  assertEquals(classifyKind("https://github.com/SWE-agent/SWE-agent"), "tool");
});

Deno.test("classifyKind detects Latent Space as podcast", () => {
  assertEquals(classifyKind("https://www.latent.space/p/claude-code"), "podcast");
});

Deno.test("classifyKind detects YouTube as video", () => {
  assertEquals(classifyKind("https://www.youtube.com/watch?v=abc123"), "video");
});

Deno.test("classifyKind defaults to article", () => {
  assertEquals(classifyKind("https://www.anthropic.com/engineering/some-article"), "article");
});

Deno.test("classifyKind detects benchmarks from title", () => {
  assertEquals(classifyKind("https://example.com", "SWE-bench: A benchmark for coding agents"), "benchmark");
});

// ---------------------------------------------------------------------------
// classify.js — category
// ---------------------------------------------------------------------------

Deno.test("classifyCategory detects context from keywords", () => {
  assertEquals(classifyCategory("https://example.com", "Context engineering for AI agents", "managing the context window"), "context");
});

Deno.test("classifyCategory detects constraints from keywords", () => {
  assertEquals(classifyCategory("https://example.com", "Sandboxing Claude Code", "prompt injection defense and safe autonomy"), "constraints");
});

Deno.test("classifyCategory detects benchmarks", () => {
  assertEquals(classifyCategory("https://example.com", "SWE-bench Verified", "a benchmark leaderboard for coding agents"), "benchmarks");
});

Deno.test("classifyCategory detects evals", () => {
  assertEquals(classifyCategory("https://example.com", "Agent evals guide", "how to evaluate and grade agent traces"), "evals");
});

Deno.test("classifyCategory detects specs", () => {
  assertEquals(classifyCategory("https://example.com", "12 Factor Agents", "operating principles and specs for production agents"), "specs");
});

Deno.test("classifyCategory defaults to foundations", () => {
  assertEquals(classifyCategory("https://example.com", "Harness engineering overview", "shaping the environment around agents"), "foundations");
});

// ---------------------------------------------------------------------------
// classify.js — source
// ---------------------------------------------------------------------------

Deno.test("inferSource extracts anthropic", () => {
  assertEquals(inferSource("https://www.anthropic.com/engineering/foo"), "anthropic");
});

Deno.test("inferSource extracts GitHub owner", () => {
  assertEquals(inferSource("https://github.com/SWE-agent/SWE-agent"), "swe-agent");
});

Deno.test("inferSource extracts simonwillison", () => {
  assertEquals(inferSource("https://simonwillison.net/2025/Sep/18/agents/"), "simonwillison");
});

Deno.test("inferSource extracts arxiv", () => {
  assertEquals(inferSource("https://arxiv.org/abs/2310.06770"), "arxiv");
});

// ---------------------------------------------------------------------------
// classify.js — tags
// ---------------------------------------------------------------------------

Deno.test("classifyTags extracts relevant tags", () => {
  const tags = classifyTags("https://example.com", "Effective harnesses for long-running agents", "context engineering and handoff artifacts");
  assertEquals(tags.includes("context-engineering"), true);
  assertEquals(tags.includes("long-running"), true);
});

Deno.test("classifyTags returns empty for unrelated content", () => {
  const tags = classifyTags("https://example.com", "Hello world", "a generic page");
  assertEquals(tags, []);
});

Deno.test("classifyTags limits to 4 tags", () => {
  const tags = classifyTags(
    "https://example.com",
    "Agent harness with context engineering, evals, sandboxing, MCP, multi-agent orchestration, and long-running resumability",
    "tool use, tool calling, verification, telemetry, prompt injection, benchmarks, coding agents",
  );
  assertEquals(tags.length <= 4, true);
});

// ---------------------------------------------------------------------------
// classify.js — spam detection
// ---------------------------------------------------------------------------

Deno.test("detectSpam flags spam keywords", () => {
  const result = detectSpam("https://example.com", "Buy now! Limited offer!", "click here to download");
  assertEquals(result.isSpam, true);
});

Deno.test("detectSpam flags excessive links", () => {
  const result = detectSpam("https://example.com", "Check this out", "https://a.com https://b.com https://c.com https://d.com");
  assertEquals(result.isSpam, true);
  assertEquals(result.reason, "Too many links in description");
});

Deno.test("detectSpam passes legitimate content", () => {
  const result = detectSpam("https://anthropic.com", "Effective harnesses for long-running agents", "A technical article about agent architecture.");
  assertEquals(result.isSpam, false);
});

// ---------------------------------------------------------------------------
// classify.js — commercial detection
// ---------------------------------------------------------------------------

Deno.test("detectCommercial flags GitHub as open source", () => {
  const result = detectCommercial("https://github.com/SWE-agent/SWE-agent");
  assertEquals(result.isCommercial, false);
  assertEquals(result.isOpenSource, true);
});

Deno.test("detectCommercial flags pricing pages", () => {
  const result = detectCommercial("https://example.com/pricing", "Our Product", "Start your free trial, talk to sales, book a demo");
  assertEquals(result.isCommercial, true);
});

Deno.test("detectCommercial passes non-commercial content", () => {
  const result = detectCommercial("https://anthropic.com/engineering/foo", "Effective harnesses", "A technical article.");
  assertEquals(result.isCommercial, false);
});

// ---------------------------------------------------------------------------
// classify.js — full pipeline
// ---------------------------------------------------------------------------

Deno.test("classify returns all fields for a known article", () => {
  const result = classify(
    "https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents",
    { title: "Effective harnesses for long-running agents", description: "Context engineering and handoff artifacts for long-running agents." },
  );
  assertEquals(result.source, "anthropic");
  assertEquals(result.kind, "article");
  assertEquals(result.isSpam, false);
  assertEquals(typeof result.category, "string");
  assertEquals(Array.isArray(result.tags), true);
});