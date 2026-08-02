import { assertEquals } from "jsr:@std/assert";
import { validateSubmission, slugify } from "../src/validate.js";

Deno.test("validateSubmission accepts a well-formed payload", () => {
  const result = validateSubmission({
    title: "Effective harnesses for long-running agents",
    link: "https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents",
    category: "foundations",
    resource_kind: "article",
    source: "anthropic",
    description: "Anthropic's core article on initializer agents.",
    tags: "context-engineering, long-running",
    submitter: "octocat",
  });
  assertEquals(result.ok, true);
  assertEquals(result.data.category, "foundations");
  assertEquals(result.data.tags, ["context-engineering", "long-running"]);
  assertEquals(result.data.added.length, 10);
});

Deno.test("validateSubmission rejects missing fields", () => {
  const result = validateSubmission({});
  assertEquals(result.ok, false);
  assertEquals(Object.keys(result.fields).sort(), [
    "category",
    "description",
    "link",
    "resource_kind",
    "source",
    "title",
  ]);
});

Deno.test("validateSubmission rejects bad URL and category", () => {
  const result = validateSubmission({
    title: "x",
    link: "notaurl",
    category: "bogus",
    resource_kind: "article",
    source: "anthropic",
    description: "x",
  });
  assertEquals(result.ok, false);
  assertEquals(result.fields.link, "Must be an http(s) URL");
  assertEquals(result.fields.category, "Invalid category");
});

Deno.test("validateSubmission strips HTML tags from title and description", () => {
  const result = validateSubmission({
    title: "<b>Hello</b>",
    link: "https://example.com",
    category: "foundations",
    resource_kind: "article",
    source: "anthropic",
    description: "<b>bold</b> text",
  });
  assertEquals(result.ok, true);
  assertEquals(result.data.title, "Hello");
  assertEquals(result.data.description, "bold text");
});

Deno.test("slugify produces filesystem-safe slugs", () => {
  assertEquals(slugify("Effective harnesses for long-running agents"), "effective-harnesses-for-long-running-agents");
  assertEquals(slugify("τ-Bench"), "bench");
  assertEquals(slugify("  Hello, World!  "), "hello-world");
});

Deno.test("validateSubmission rejects tags not in the controlled vocabulary", () => {
  const result = validateSubmission({
    title: "x",
    link: "https://example.com",
    category: "foundations",
    resource_kind: "article",
    source: "anthropic",
    description: "x",
    tags: "context-engineering, bogus-tag",
  });
  assertEquals(result.ok, false);
  assertEquals(result.fields.tags, "Tag 'bogus-tag' is not in the controlled vocabulary");
});

Deno.test("validateSubmission accepts tags that are in the vocabulary", () => {
  const result = validateSubmission({
    title: "x",
    link: "https://example.com",
    category: "foundations",
    resource_kind: "article",
    source: "anthropic",
    description: "x",
    tags: "context-engineering, long-running",
  });
  assertEquals(result.ok, true);
  assertEquals(result.data.tags, ["context-engineering", "long-running"]);
});