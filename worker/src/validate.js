// Shared validation rules for resource submissions.
// The site form mirrors these in assets/js/submit-form.js; keep them in sync.

export const ALLOWED_CATEGORIES = new Set([
  "courses",
  "foundations",
  "context",
  "constraints",
  "specs",
  "evals",
  "benchmarks",
  "runtimes",
]);

export const ALLOWED_KINDS = new Set([
  "article",
  "tool",
  "benchmark",
  "course",
  "spec",
  "podcast",
  "video",
  "paper",
]);

// Controlled tag vocabulary. Must match data/tags.yml in the repo.
// Keep in sync: scripts/lint_resources.py enforces the same set in CI.
export const ALLOWED_TAGS = new Set([
  "agent-files",
  "benchmarks",
  "brownfield",
  "checkpoints",
  "coding-agents",
  "compression",
  "computer-use",
  "context-engineering",
  "evals",
  "frameworks",
  "greenfield",
  "long-running",
  "mcp",
  "multi-agent",
  "observability",
  "orchestration",
  "planning",
  "quality",
  "retrieval",
  "runtimes",
  "search",
  "security",
  "specs",
  "tools",
  "web-agents",
]);

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const SLUG_RE = /^[a-z0-9][a-z0-9._-]*$/i;
const TAG_RE = /^[a-z0-9][a-z0-9._-]*$/;

export function todayUTC() {
  return new Date().toISOString().slice(0, 10);
}

export function slugify(value) {
  value = value.normalize("NFKD").replace(/[^a-zA-Z0-9\s-]/g, "");
  value = value.toLowerCase().trim();
  value = value.replace(/[\s_-]+/g, "-");
  value = value.replace(/^-+|-+$/g, "");
  return value || "resource";
}

export function stripTags(s) {
  return s.replace(/<[^>]*>/g, "").trim();
}

/**
 * Validate a submission payload. Returns `{ ok: true }` or
 * `{ ok: false, fields: { fieldName: "message" } }`.
 */
export function validateSubmission(payload) {
  const fields = {};
  let ok = true;

  const title = stripTags(String(payload.title || "")).trim();
  if (!title) { fields.title = "Required"; ok = false; }
  else if (title.length > 200) { fields.title = "Keep under 200 characters"; ok = false; }

  const link = String(payload.link || "").trim();
  if (!link) { fields.link = "Required"; ok = false; }
  else if (!/^https?:\/\/\S+$/i.test(link)) { fields.link = "Must be an http(s) URL"; ok = false; }

  const category = String(payload.category || "").trim();
  if (!category) { fields.category = "Required"; ok = false; }
  else if (!ALLOWED_CATEGORIES.has(category)) { fields.category = "Invalid category"; ok = false; }

  const resource_kind = String(payload.resource_kind || "").trim();
  if (!resource_kind) { fields.resource_kind = "Required"; ok = false; }
  else if (!ALLOWED_KINDS.has(resource_kind)) { fields.resource_kind = "Invalid kind"; ok = false; }

  const source = String(payload.source || "").trim();
  if (!source) { fields.source = "Required"; ok = false; }
  else if (!SLUG_RE.test(source)) { fields.source = "Lowercase letters, numbers, ., _, -"; ok = false; }

  const description = stripTags(String(payload.description || "")).trim();
  if (!description) { fields.description = "Required"; ok = false; }
  else if (description.length > 500) { fields.description = "Keep under 500 characters"; ok = false; }

  const tagsRaw = String(payload.tags || "").trim();
  const tags = [];
  if (tagsRaw) {
    for (const part of tagsRaw.split(",").map((t) => t.trim().toLowerCase()).filter(Boolean)) {
      if (!TAG_RE.test(part)) {
        fields.tags = "Tags: lowercase letters, numbers, ., _, -, comma-separated";
        ok = false;
        break;
      }
      if (!ALLOWED_TAGS.has(part)) {
        fields.tags = `Tag '${part}' is not in the controlled vocabulary`;
        ok = false;
        break;
      }
      tags.push(part);
    }
  }

  const submitter = String(payload.submitter || "").trim().slice(0, 80);

  if (!ok) return { ok: false, fields };

  return {
    ok: true,
    data: {
      title,
      link,
      category,
      resource_kind,
      source,
      description,
      tags,
      submitter,
      added: todayUTC(),
    },
  };
}