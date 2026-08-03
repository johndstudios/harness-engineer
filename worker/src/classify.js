// Auto-classification of a fetched URL into category, kind, source, tags,
// plus spam/commercial/open-source detection.
//
// All heuristics are pure functions on { url, title, description, content }.

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

// ---------------------------------------------------------------------------
// URL helpers
// ---------------------------------------------------------------------------

export function parseUrl(url) {
  try {
    return new URL(url);
  } catch {
    return null;
  }
}

export function isGitHubRepo(url) {
  const u = parseUrl(url);
  if (!u || u.hostname !== "github.com") return false;
  const parts = u.pathname.split("/").filter(Boolean);
  return parts.length >= 2 && !["search", "orgs", "topics", "settings", "apps", "marketplace"].includes(parts[0]);
}

export function githubOwnerRepo(url) {
  const u = parseUrl(url);
  if (!u || u.hostname !== "github.com") return null;
  const parts = u.pathname.split("/").filter(Boolean);
  if (parts.length >= 2) return { owner: parts[0], repo: parts[1] };
  return null;
}

// ---------------------------------------------------------------------------
// Source extraction
// ---------------------------------------------------------------------------

export function inferSource(url) {
  const u = parseUrl(url);
  if (!u) return "unknown";
  const host = u.hostname.replace(/^www\./, "");

  const known = {
    "anthropic.com": "anthropic",
    "openai.com": "openai",
    "blog.langchain.com": "langchain",
    "langchain.com": "langchain",
    "martinfowler.com": "thoughtworks",
    "humanlayer.dev": "humanlayer",
    "openhands.dev": "openhands",
    "manus.im": "manus",
    "inngest.com": "inngest",
    "ghuntley.com": "ghuntley",
    "sawinyh.com": "sawinyh",
    "simonwillison.net": "simonwillison",
    "arxiv.org": "arxiv",
    "preprints.org": "preprints",
    "code.claude.com": "anthropic",
    "claude.com": "anthropic",
    "inspect.aisi.org.uk": "uk-aisi",
    "opentelemetry.io": "opentelemetry",
    "tbench.ai": "terminal-bench",
    "skills.sh": "skills.sh",
    "12factoragentops.com": "12factoragentops",
    "latent.space": "latent-space",
    "practicalai.fm": "practical-ai",
    "github.blog": "github",
  };

  for (const [domain, src] of Object.entries(known)) {
    if (host === domain || host.endsWith("." + domain)) return src;
  }

  // GitHub repos → owner
  if (host === "github.com") {
    const gh = githubOwnerRepo(url);
    if (gh) return gh.owner.toLowerCase();
  }

  // Fall back to registrable domain
  const parts = host.split(".");
  return parts.length >= 2 ? parts.slice(-2).join(".") : host;
}

// ---------------------------------------------------------------------------
// Kind classification
// ---------------------------------------------------------------------------

export function classifyKind(url, title = "", desc = "") {
  const u = parseUrl(url);
  if (!u) return "article";
  const host = u.hostname.replace(/^www\./, "");
  const text = (title + " " + desc + " " + url).toLowerCase();

  if (host === "arxiv.org" || text.includes("preprint") || text.includes("arxiv")) return "paper";
  if (host === "latent.space" || host === "practicalai.fm") return "podcast";
  if (host === "youtube.com" || host === "youtu.be" || text.includes("youtube.com/watch")) return "video";
  if (isGitHubRepo(url)) return "tool";
  if (text.includes("benchmark") || text.includes("leaderboard")) return "benchmark";
  if (text.includes("spec") || text.includes("protocol") || text.includes("12 factor") || text.includes("12-factor")) return "spec";
  if (text.includes("course") || text.includes("curriculum") || text.includes("lecture")) return "course";
  return "article";
}

// ---------------------------------------------------------------------------
// Category classification
// ---------------------------------------------------------------------------

export function classifyCategory(url, title = "", desc = "") {
  const text = (title + " " + desc + " " + url).toLowerCase();

  if (text.includes("course") || text.includes("curriculum") || text.includes("lecture")) return "courses";
  if (text.includes("benchmark") || text.includes("leaderboard") || text.includes("eval environment")) return "benchmarks";
  if (text.includes("sandbox") || text.includes("prompt injection") || text.includes("guardrail") || text.includes("safe autonomy") || text.includes("permission") || text.includes("security") || text.includes("capability")) return "constraints";
  if (text.includes("context engineering") || text.includes("context window") || text.includes("working memory") || text.includes("context management") || text.includes("context-efficient") || text.includes("claude.md") || text.includes("agents.md") || text.includes("context condens")) return "context";
  if (text.includes("spec-driven") || text.includes("spec kit") || text.includes("12 factor") || text.includes("12-factor") || text.includes("agent.md") || text.includes("workflow design") || text.includes("operating principle")) return "specs";
  if (text.includes("eval") || text.includes("grading") || text.includes("trace") || text.includes("observability") || text.includes("telemetry") || text.includes("verify") || text.includes("verification") || text.includes("trajectory")) return "evals";
  if (text.includes("runtime") || text.includes("harness implementation") || text.includes("reference implementation") || text.includes("framework") || text.includes("sdk") || text.includes("orchestrat")) return "runtimes";
  // GitHub repos that aren't benchmarks usually belong in runtimes
  if (isGitHubRepo(url)) return "runtimes";
  return "foundations";
}

// ---------------------------------------------------------------------------
// Tag extraction
// ---------------------------------------------------------------------------

const TAG_RULES = [
  ["context engineering", "context-engineering"],
  ["context window", "context-engineering"],
  ["working memory", "context-engineering"],
  ["claude.md", "agent-files"],
  ["agents.md", "agent-files"],
  ["agent.md", "agent-files"],
  ["init.sh", "agent-files"],
  ["spec-driven", "specs"],
  ["spec kit", "specs"],
  ["12 factor", "specs"],
  ["12-factor", "specs"],
  ["eval", "evals"],
  ["grading", "evals"],
  ["trajectory", "evals"],
  ["verif", "evals"],
  ["observability", "observability"],
  ["telemetry", "observability"],
  ["tracing", "observability"],
  ["monitoring", "observability"],
  ["prompt injection", "security"],
  ["sandbox", "security"],
  ["guardrail", "security"],
  ["safe autonomy", "security"],
  ["long-running", "long-running"],
  ["resumab", "long-running"],
  ["retry", "long-running"],
  ["orchestrat", "orchestration"],
  ["multi-agent", "multi-agent"],
  ["coordination", "multi-agent"],
  ["tool calling", "tools"],
  ["tool use", "tools"],
  ["tool-use", "tools"],
  ["mcp", "mcp"],
  ["model context protocol", "mcp"],
  ["benchmark", "benchmarks"],
  ["leaderboard", "benchmarks"],
  ["coding agent", "coding-agents"],
  ["software engineering", "coding-agents"],
  ["computer use", "computer-use"],
  ["browser", "web-agents"],
  ["web agent", "web-agents"],
  ["planning", "planning"],
  ["retrieval", "retrieval"],
  ["search", "search"],
  ["runtime", "runtimes"],
  ["framework", "frameworks"],
  ["handoff", "long-running"],
  ["condens", "compression"],
  ["backpressure", "compression"],
  ["brownfield", "brownfield"],
  ["greenfield", "greenfield"],
  ["quality", "quality"],
  ["checkpoint", "checkpoints"],
];

export function classifyTags(url, title = "", desc = "") {
  const text = (title + " " + desc).toLowerCase();
  const tags = [];
  const seen = new Set();
  for (const [keyword, tag] of TAG_RULES) {
    if (text.includes(keyword) && !seen.has(tag) && ALLOWED_TAGS.has(tag)) {
      tags.push(tag);
      seen.add(tag);
      if (tags.length >= 4) break;
    }
  }
  return tags;
}

// ---------------------------------------------------------------------------
// Spam / commercial detection
// ---------------------------------------------------------------------------

const SPAM_KEYWORDS = [
  "buy now", "limited offer", "free trial", "click here to download",
  "make money", "seo service", "link building", "casino", "gambling",
  "pharmaceutical", "viagra", "weight loss", "crypto airdrop",
  "nft mint", "get rich", "affiliate link", "sponsored post",
  "paid promotion", "discount code",
];

const COMMERCIAL_KEYWORDS = [
  "pricing", "plans and pricing", "start your free trial", "book a demo",
  "request a quote", "enterprise pricing", "talk to sales", "schedule a call",
  "upgrade to pro", "premium plan", "subscription tier",
];

const COMMERCIAL_DOMAINS = [
  // These domains are primarily commercial product pages, not primary sources.
  // (We don't block them outright, but we flag them for review.)
];

export function detectSpam(url, title = "", desc = "", content = "") {
  const text = (title + " " + desc + " " + content).toLowerCase().slice(0, 5000);

  for (const kw of SPAM_KEYWORDS) {
    if (text.includes(kw)) {
      return { isSpam: true, reason: `Spam keyword detected: "${kw}"` };
    }
  }

  // Excessive links in description is a spam signal
  const linkCount = (desc.match(/https?:\/\//g) || []).length;
  if (linkCount > 3) {
    return { isSpam: true, reason: "Too many links in description" };
  }

  return { isSpam: false };
}

export function detectCommercial(url, title = "", desc = "", content = "") {
  const u = parseUrl(url);
  const host = u ? u.hostname.replace(/^www\./, "") : "";
  const text = (title + " " + desc + " " + content).toLowerCase().slice(0, 5000);

  // GitHub repos are open source by default
  if (isGitHubRepo(url)) return { isCommercial: false, isOpenSource: true };

  // arxiv, preprints are open
  if (host === "arxiv.org" || host === "preprints.org") return { isCommercial: false, isOpenSource: true };

  let score = 0;
  for (const kw of COMMERCIAL_KEYWORDS) {
    if (text.includes(kw)) score += 1;
  }
  for (const domain of COMMERCIAL_DOMAINS) {
    if (host === domain || host.endsWith("." + domain)) score += 2;
  }

  // "Pricing" page URLs are a strong signal
  if (u && u.pathname.includes("/pricing")) score += 2;

  return {
    isCommercial: score >= 2,
    isOpenSource: false,
    commercialScore: score,
  };
}

// ---------------------------------------------------------------------------
// Full classification pipeline
// ---------------------------------------------------------------------------

/**
 * Classify a fetched resource from its URL + extracted metadata.
 * Returns { category, kind, source, tags, isSpam, isCommercial, isOpenSource }.
 */
export function classify(url, metadata) {
  const title = metadata.title || "";
  const description = metadata.description || "";
  const content = metadata.content || "";

  const kind = classifyKind(url, title, description);
  const category = classifyCategory(url, title, description);
  const source = inferSource(url);
  const tags = classifyTags(url, title, description);
  const spam = detectSpam(url, title, description, content);
  const commercial = detectCommercial(url, title, description, content);

  return {
    category,
    kind,
    source,
    tags,
    isSpam: spam.isSpam,
    spamReason: spam.reason || "",
    isCommercial: commercial.isCommercial,
    isOpenSource: commercial.isOpenSource,
    commercialScore: commercial.commercialScore || 0,
  };
}