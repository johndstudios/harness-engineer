import { validateSubmission, slugify, todayUTC } from "./validate.js";
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

// ---------------------------------------------------------------------------
// Responses
// ---------------------------------------------------------------------------

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...extraHeaders },
  });
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

    // --- Cheap shared-secret gate (rate limit, not auth) -------------------
    if (env.FORM_SECRET) {
      const auth = request.headers.get("Authorization") || "";
      if (auth !== `Bearer ${env.FORM_SECRET}`) {
        return json({ error: "Unauthorized" }, 401, corsHeaders(origin, allowed));
      }
    }

    // --- Parse + validate --------------------------------------------------
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
    const data = result.data;

    // --- Authenticate as the GitHub App ------------------------------------
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

      // --- Branch + commit + PR ---------------------------------------------
      const slug = slugify(data.title);
      const filePath = `content/resources/${slug}.md`;

      // Duplicate check: if the file already exists on main, refuse.
      const exists = await fileExists(apiBase, owner, repo, token, filePath, baseBranch);
      if (exists) {
        return json(
          {
            error: "A resource with this title already exists. Choose a more specific title.",
            fields: { title: "Duplicate slug" },
          },
          409,
          corsHeaders(origin, allowed),
        );
      }

      const branchName = `add-${slug}-${todayUTC().replace(/-/g, "")}`;
      const sha = await getDefaultBranchSha(apiBase, owner, repo, token, baseBranch);
      await createBranch(apiBase, owner, repo, token, branchName, sha);

      const fileContent = buildResourceFile(data);
      await putFile(
        apiBase, owner, repo, token,
        filePath,
        fileContent,
        branchName,
        `Add ${data.title} (${data.category})`,
      );

      const prBody = buildPrBody(data);
      const pr = await openPR(
        apiBase, owner, repo, token,
        branchName, baseBranch,
        `Add ${data.title}`,
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

  return [
    "## New resource submission",
    "",
    `**${data.title}**`,
    `${data.link}`,
    "",
    `Category: \`${data.category}\` · Kind: \`${data.resource_kind}\` · Source: \`${data.source}\``,
    "",
    data.description,
    tagsLine,
    "",
    "### Checklist",
    "",
    "- [ ] The resource is directly relevant to harness engineering",
    "- [ ] The link works",
    `- [ ] The resource is not already listed in \`content/resources/\``,
    "- [ ] The front matter is complete and valid",
    "- [ ] The description explains the harness angle clearly",
    "- [ ] The change is placed in the most appropriate category",
    "",
    "Generated by the Harness Engineer submission form." + submitterLine,
    "",
  ].join("\n");
}