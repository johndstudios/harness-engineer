// Fetch GitHub repo metadata via the GitHub REST API.
// Used by the Worker to enrich submissions from GitHub URLs.

export async function fetchGithubRepo(url, token) {
  const u = new URL(url);
  const parts = u.pathname.split("/").filter(Boolean);
  if (parts.length < 2) return null;
  const owner = parts[0];
  const repo = parts[1];

  const headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "harness-engineer-bot/1.0",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const resp = await fetch(`https://api.github.com/repos/${owner}/${repo}`, { headers });
    if (!resp.ok) return null;
    const data = await resp.json();
    return {
      stars: data.stargazers_count || 0,
      forks: data.forks_count || 0,
      openIssues: data.open_issues_count || 0,
      topics: data.topics || [],
      language: data.language || "",
      description: data.description || "",
      created: (data.created_at || "").slice(0, 10),
      updated: (data.updated_at || "").slice(0, 10),
      pushed: (data.pushed_at || "").slice(0, 10),
      license: (data.license || {}).spdx_id || "",
    };
  } catch {
    return null;
  }
}

export function buildEnrichmentJson(slug, link, fetched, ghData) {
  const enrichment = {
    slug,
    url: link,
    crawled_at: new Date().toISOString(),
    status: "ok",
    http_status: fetched.status || 200,
    final_url: fetched.finalUrl || link,
    content_type: fetched.contentType || "",
    fetched_title: fetched.title || "",
    meta_description: fetched.description || "",
    og_title: "",
    og_description: "",
    og_image: "",
    word_count: 0,
    reading_time_min: 0,
    language: "",
  };

  if (ghData) {
    enrichment.github_stars = ghData.stars;
    enrichment.github_forks = ghData.forks;
    enrichment.github_open_issues = ghData.openIssues;
    enrichment.github_topics = ghData.topics;
    enrichment.github_language = ghData.language;
    enrichment.github_description = ghData.description;
    enrichment.github_created = ghData.created;
    enrichment.github_updated = ghData.updated;
    enrichment.github_pushed = ghData.pushed;
    enrichment.github_license = ghData.license;
  }

  return JSON.stringify(enrichment, null, 2);
}