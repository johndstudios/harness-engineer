// Fetch a URL and extract basic metadata from the HTML.
// Runs in the Cloudflare Worker runtime (no DOM, manual HTML parsing).

const ENC = new TextDecoder();

function getMeta(html, name) {
  // Match <meta name="..." content="..."> or <meta property="..." content="...">
  const re = new RegExp(
    `<meta[^>]+(?:name|property)=["']${name}["'][^>]*content=["']([^"']*)["']`,
    "i",
  );
  const m = html.match(re);
  return m ? m[1].trim() : "";
}

function getTitle(html) {
  const m = html.match(/<title[^>]*>([^<]*)<\/title>/i);
  return m ? m[1].trim() : "";
}

function getMetaDescription(html) {
  return getMeta(html, "description") || getMeta(html, "og:description");
}

function getOgTitle(html) {
  return getMeta(html, "og:title");
}

/**
 * Fetch a URL and extract metadata.
 * Returns { ok, status, title, description, content, finalUrl }.
 */
export async function fetchMetadata(url) {
  try {
    const resp = await fetch(url, {
      headers: {
        "User-Agent": "harness-engineer-bot/1.0 (+https://github.com/johndstudios/harness-engineer)",
        "Accept": "text/html,application/xhtml+xml,*/*",
      },
      redirect: "follow",
    });

    const contentType = resp.headers.get("content-type") || "";

    // For non-HTML (PDFs, etc.), we can't parse metadata.
    if (!contentType.includes("text/html") && !contentType.includes("application/xhtml")) {
      return {
        ok: true,
        status: resp.status,
        title: "",
        description: "",
        content: "",
        finalUrl: resp.url,
        contentType,
      };
    }

    const buf = await resp.arrayBuffer();
    // Read up to 500KB
    const html = ENC.decode(buf.slice(0, 500 * 1024));

    const title = getOgTitle(html) || getTitle(html);
    const description = getMetaDescription(html);

    // Extract first ~2000 chars of visible text for spam/keyword detection
    const stripped = html
      .replace(/<script[\s\S]*?<\/script>/gi, "")
      .replace(/<style[\s\S]*?<\/style>/gi, "")
      .replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 2000);

    return {
      ok: true,
      status: resp.status,
      title: title.slice(0, 300),
      description: description.slice(0, 500),
      content: stripped,
      finalUrl: resp.url,
      contentType,
    };
  } catch (err) {
    return {
      ok: false,
      status: 0,
      title: "",
      description: "",
      content: "",
      finalUrl: url,
      error: String(err).slice(0, 200),
    };
  }
}