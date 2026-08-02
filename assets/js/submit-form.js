(() => {
  "use strict";

  const form = document.getElementById("submit-form");
  if (!form) return;

  const status = document.getElementById("form-status");
  const submitBtn = document.getElementById("submit-btn");
  const resultBox = document.getElementById("form-result");
  const prLink = document.getElementById("pr-link");
  const submitAnother = document.getElementById("submit-another");

  // ---------- Validation helpers ----------

  const ALLOWED_CATEGORIES = new Set([
    "courses", "foundations", "context", "constraints",
    "specs", "evals", "benchmarks", "runtimes",
  ]);
  const ALLOWED_KINDS = new Set([
    "article", "tool", "benchmark", "course", "spec", "podcast", "video", "paper",
  ]);
  // Must match worker/src/validate.js ALLOWED_TAGS and data/tags.yml.
  const ALLOWED_TAGS = new Set([
    "agent-files", "benchmarks", "brownfield", "checkpoints", "coding-agents",
    "compression", "computer-use", "context-engineering", "evals", "frameworks",
    "greenfield", "long-running", "mcp", "multi-agent", "observability",
    "orchestration", "planning", "quality", "retrieval", "runtimes", "search",
    "security", "specs", "tools", "web-agents",
  ]);
  const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
  const SLUG_RE = /^[a-z0-9][a-z0-9._-]*$/i;
  const stripTags = (s) => s.replace(/<[^>]*>/g, "");

  function setError(name, msg) {
    const el = form.querySelector(`[data-err="${name}"]`);
    if (el) {
      el.textContent = msg || "";
      el.classList.toggle("err-on", Boolean(msg));
    }
  }

  function clearAllErrors() {
    form.querySelectorAll("[data-err]").forEach((el) => {
      el.textContent = "";
      el.classList.remove("err-on");
    });
  }

  function validate(payload) {
    const errors = {};
    const title = (payload.title || "").trim();
    if (!title) errors.title = "Required";
    else if (title.length > 200) errors.title = "Keep under 200 characters";

    const link = (payload.link || "").trim();
    if (!link) errors.link = "Required";
    else if (!/^https?:\/\/\S+$/i.test(link)) errors.link = "Must be an http(s) URL";

    const category = (payload.category || "").trim();
    if (!category) errors.category = "Required";
    else if (!ALLOWED_CATEGORIES.has(category)) errors.category = "Invalid category";

    const resource_kind = (payload.resource_kind || "").trim();
    if (!resource_kind) errors.resource_kind = "Required";
    else if (!ALLOWED_KINDS.has(resource_kind)) errors.resource_kind = "Invalid kind";

    const source = (payload.source || "").trim();
    if (!source) errors.source = "Required";
    else if (!SLUG_RE.test(source)) errors.source = "Lowercase letters, numbers, ., _, -";

    const description = (payload.description || "").trim();
    if (!description) errors.description = "Required";
    else if (description.length > 500) errors.description = "Keep under 500 characters";

    const tags = (payload.tags || "").trim();
    if (tags) {
      const parts = tags.split(",").map((t) => t.trim()).filter(Boolean);
      for (const t of parts) {
        if (!/^[a-z0-9][a-z0-9._-]*$/.test(t)) {
          errors.tags = "Tags: lowercase letters, numbers, ., _, -, comma-separated";
          break;
        }
        if (!ALLOWED_TAGS.has(t)) {
          errors.tags = `Tag '${t}' is not in the controlled vocabulary`;
          break;
        }
      }
    }
    return errors;
  }

  // ---------- Submission ----------

  function setFormState(state, msg) {
    status.textContent = msg || "";
    submitBtn.disabled = state === "loading";
    submitBtn.classList.toggle("loading", state === "loading");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAllErrors();

    const tagsRaw = form.tags.value;
    const tags = tagsRaw
      ? tagsRaw.split(",").map((t) => t.trim().toLowerCase()).filter(Boolean).join(", ")
      : "";

    const payload = {
      title: form.title.value,
      link: form.link.value,
      category: form.category.value,
      resource_kind: form.resource_kind.value,
      source: form.source.value,
      description: form.description.value,
      tags,
      submitter: form.submitter.value,
    };

    const errors = validate(payload);
    if (Object.keys(errors).length) {
      for (const [k, v] of Object.entries(errors)) setError(k, v);
      return;
    }

    if (!SUBMIT_ENDPOINT) {
      setFormState("error", "Submission endpoint is not configured yet.");
      return;
    }

    setFormState("loading", "Opening pull request…");

    try {
      const headers = { "Content-Type": "application/json" };
      if (window.FORM_SECRET) headers["Authorization"] = `Bearer ${window.FORM_SECRET}`;
      const res = await fetch(SUBMIT_ENDPOINT, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data && data.error ? data.error : `Request failed (${res.status})`;
        if (data && data.fields) for (const [k, v] of Object.entries(data.fields)) setError(k, v);
        setFormState("error", msg);
        return;
      }
      if (data && data.pr_url && prLink) {
        prLink.href = data.pr_url;
        prLink.textContent = data.pr_url;
      }
      form.hidden = true;
      resultBox.hidden = false;
      setFormState("idle", "");
    } catch (err) {
      setFormState("error", "Network error — please try again.");
    }
  });

  if (submitAnother) {
    submitAnother.addEventListener("click", () => {
      form.reset();
      clearAllErrors();
      form.hidden = false;
      resultBox.hidden = true;
      setFormState("idle", "");
      form.title.focus();
    });
  }
})();