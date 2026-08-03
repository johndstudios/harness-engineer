// Shared validation rules for resource submissions.
//
// The simplified submission flow accepts just a URL (+ optional description,
// category, and submitter). The Worker fetches the URL and auto-classifies
// everything else. This module validates the *submission payload*, not the
// final resource file.

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

const SLUG_RE = /^[a-z0-9][a-z0-9._-]*$/i;

export function todayUTC() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Validate a URL-only submission payload.
 * Returns { ok: true, data } or { ok: false, fields }.
 */
export function validateSubmission(payload) {
  const fields = {};

  const link = String(payload.link || "").trim();
  if (!link) {
    fields.link = "Required";
  } else if (!/^https?:\/\/\S+$/i.test(link)) {
    fields.link = "Must be an http(s) URL";
  }

  const description = String(payload.description || "").trim();
  if (description.length > 500) {
    fields.description = "Keep under 500 characters";
  }

  const category = String(payload.category || "").trim();
  if (category && !ALLOWED_CATEGORIES.has(category)) {
    fields.category = "Invalid category";
  }

  const submitter = String(payload.submitter || "").trim().slice(0, 80);

  if (Object.keys(fields).length) {
    return { ok: false, fields };
  }

  return {
    ok: true,
    data: { link, description, category, submitter, added: todayUTC() },
  };
}