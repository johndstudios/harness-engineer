import { validateSubmission, todayUTC } from "./validate.js";
import { fetchMetadata } from "./fetcher.js";
import { classify, inferSource, classifyKind, classifyCategory, classifyTags, detectSpam, detectCommercial } from "./classify.js";
import { appJwt, installationToken } from "./github-auth.js";
import {
  getDefaultBranchSha,
  createBranch,
  putFile,
  openPR,
  fileExists,
} from "./github-api.js";
import { buildResourceFile } from "./resource-file.js";

// ---------------------------------------------------------------------------
// CORS
// ---------------------------------------------------------------------------

function corsHeaders(origin, allowed) {
  const allow = allowed.includes(origin) ? origin : allowed[0] || "";
  return {
    "Access-Control-Allow-Origin": allow || "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Vary": "Origin",
  };
}

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...extraHeaders },
  });
}

// ---------------------------------------------------------------------------
// Slug
// ---------------------------------------------------------------------------

function slugify(value) {
  value = value.normalize("NFKD").replace(/[^a-zA-Z0-9\s-]/g, "");
  value = value.toLowerCase().trim();
  value = value.replace(/[\s_-]+/g, "-");
  return value.replace(/^-+|-+$/g, "") || "resource";
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin, allowed) });
    }
    if (request.method !== "POST") {
      return json({ error: "Method not allowed" }, 405, corsHeaders(origin, allowed));
    }

    // Cheap shared-secret gate
    if (env.FORM_SECRET) {
      const auth = request.headers.get("Authorization") || "";
      if (auth !== `Bearer ${env.FORM_SECRET}`) {
        return json({ error: "Unauthorized" }, 401, corsHeaders(origin, allowed));
      }
    }

    // Parse + validate submission
    let payload;
    try {
      payload = await request.json();
    } catch {
      return json({ error: "Invalid JSON body" }, 400, corsHeaders(origin, allowed));
    }

    const result = validateSubmission(payload);
    if (!result.ok) {
      return json({ error: "Validation failed", fields: result.fields }, 422, corsHeaders(origin, allowed));
    }
    const submission = result.data;

    // --- Fetch the URL and extract metadata -------------------------------
    const fetched = await fetchMetadata(submission.link);
    if (!fetched.ok) {
      return json(
        { error: `Could not fetch URL: ${fetched.error || "unknown error"}` },
        422,
        corsHeaders(origin, allowed),
      );
    }

    const title = fetched.title || "Untitled resource";
    const autoDesc = fetched.description || fetched.content.slice(0, 200);
    const description = submission.description || autoDesc;

    // --- Classify ----------------------------------------------------------
    const autoCategory = classifyCategory(submission.link, title, description);
    const category = submission.category || autoCategory;
    const kind = classifyKind(submission.link, title, description);
    const source = inferSource(submission.link);
    const tags = classifyTags(submission.link, title, description);

    // --- Spam + commercial check ------------------------------------------
    const spam = detectSpam(submission.link, title, description, fetched.content);
    if (spam.isSpam) {
      return json(
        { error: `Submission rejected: ${spam.reason}` },
        422,
        corsHeaders(origin, allowed),
      );
    }

    const commercial = detectCommercial(submission.link, title, description, fetched.content);
    // Flag but don't block — let reviewers decide.
    const commercialFlag = commercial.isCommercial ? "⚠️ **Flagged as potentially commercial**" : "";

    // --- GitHub App auth ---------------------------------------------------
    if (!env.GITHUB_APP_ID || !env.GITHUB_PRIVATE_KEY || !env.GITHUB_INSTALLATION_ID) {
      return json({ error: "Server not configured (GitHub App secrets missing)" }, 500, corsHeaders(origin, allowed));
    }

    const owner = env.GITHUB_OWNER;
    const repo = env.GITHUB_REPO;
    const apiBase = env.GITHUB_API || "https://api.github.com";
    const baseBranch = "main";

    try {
      const jwt = await appJwt(env.GITHUB_APP_ID, env.GITHUB_PRIVATE_KEY);
      const { token } = await installationToken(apiBase, jwt, env.GITHUB_INSTALLATION_ID);

      const slug = slugify(title);
      const filePath = `content/resources/${slug}.md`;

      // Duplicate check
      const exists = await fileExists(apiBase, owner, repo, token, filePath, baseBranch);
      if (exists) {
        return json(
          { error: "A resource with this title already exists. Choose a more specific title.", fields: { link: "Duplicate" } },
          409,
          corsHeaders(origin, allowed),
        );
      }

      const branchName = `add-${slug}-${todayUTC().replace(/-/g, "")}`;
      const sha = await getDefaultBranchSha(apiBase, owner, repo, token, baseBranch);
      await createBranch(apiBase, owner, repo, token, branchName, sha);

      const fileContent = buildResourceFile({
        title,
        link: submission.link,
        category,
        resource_kind: kind,
        source,
        added: submission.added,
        tags,
        description,
      });

      await putFile(
        apiBase, owner, repo, token,
        filePath,
        fileContent,
        branchName,
        `Add ${title} (${category})`,
      );

      const prBody = buildPrBody({
        title,
        link: submission.link,
        category,
        kind,
        source,
        tags,
        description,
        submitter: submission.submitter,
        fetched,
        autoCategory,
        commercialFlag,
      });

      const pr = await openPR(
        apiBase, owner, repo, token,
        branchName, baseBranch,
        `Add ${title}`,
        prBody,
      );

      return json(
        { ok: true, pr_url: pr.html_url, branch: branchName, file: filePath },
        200,
        corsHeaders(origin, allowed),
      );
    } catch (err) {
      console.error("submission failed", err);
      return json(
        { error: "Failed to open pull request. Please try again or open a PR manually." },
        502,
        corsHeaders(origin, allowed),
      );
    }
  },
};

// ---------------------------------------------------------------------------
// PR body
// ---------------------------------------------------------------------------

function buildPrBody(data) {
  const submitterLine = data.submitter
    ? `\nSubmitted by @${data.submitter.replace(/^@/, "")}.`
    : "\nSubmitted anonymously via the site form.";

  const tagsLine = data.tags.length
    ? `\nTags: ${data.tags.map((t) => `\`${t}\``).join(", ")}`
    : "";

  const metaLine = `Category: \`${data.category}\` (auto: \`${data.autoCategory}\`) · Kind: \`${data.kind}\` · Source: \`${data.source}\``;

  const fetchedLine = data.fetched.title
    ? `\n\n**Fetched metadata:**\n- Title: ${data.fetched.title}\n- Description: ${data.fetched.description.slice(0, 150) || "(none)"}\n- Final URL: ${data.fetched.finalUrl}\n- Content-Type: ${data.fetched.contentType || "unknown"}`
    : "";

  const commercialLine = data.commercialFlag ? `\n\n${data.commercialFlag}` : "";

  return [
    "## New resource submission",
    "",
    `**${data.title}**`,
    `${data.link}`,
    "",
    metaLine,
    "",
    data.description,
    tagsLine,
    fetchedLine,
    commercialLine,
    "",
    "### Checklist",
    "",
    "- [ ] The resource is directly relevant to harness engineering",
    "- [ ] The link works",
    "- [ ] The resource is not already listed in `content/resources/`",
    "- [ ] The auto-classified category and kind are correct",
    "- [ ] The description explains the harness angle clearly",
    "- [ ] The resource is open-source or primary-source (not commercial)",
    "",
    "Generated by the Harness Engineer submission form (auto-classified)." + submitterLine,
    "",
  ].join("\n");
}