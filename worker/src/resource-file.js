// Build the Markdown resource file content from validated submission data.
// Mirrors the format produced by scripts/migrate_readme.py.

function yamlQuote(value) {
  if (value === "" || /[:#@`'"{},&*?!|<>=]/.test(value)) {
    return '"' + value.replace(/"/g, '\\"') + '"';
  }
  return value;
}

function tagList(items) {
  if (!items || items.length === 0) return "";
  return `[${items.map((t) => `"${t}"`).join(", ")}]`;
}

export function buildResourceFile(data) {
  const lines = [
    "---",
    `title: ${yamlQuote(data.title)}`,
    `link: ${data.link}`,
    `category: [${data.category}]`,
    `resource_kind: ${data.resource_kind}`,
    `source: ["${data.source}"]`,
    `added: ${data.added}`,
  ];
  if (data.tags && data.tags.length) {
    lines.push(`tags: ${tagList(data.tags)}`);
  }
  lines.push("---", "", data.description, "");
  return lines.join("\n");
}