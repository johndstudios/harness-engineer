// Build the Markdown resource file content from classified data.

function yamlQuote(value) {
  if (value === "" || /[:#@`'"{},&*?!|<>=]/.test(value)) {
    return '"' + value.replace(/"/g, '\\"') + '"';
  }
  return value;
}

function stripTags(s) {
  return s.replace(/<[^>]*>/g, "").trim();
}

export function buildResourceFile(data) {
  const lines = [
    "---",
    `title: ${yamlQuote(stripTags(data.title))}`,
    `link: ${data.link}`,
    `category: [${data.category}]`,
    `resource_kind: ${data.resource_kind}`,
    `source: ["${data.source}"]`,
    `added: ${data.added}`,
    `date: ${data.added}`,
  ];
  if (data.tags && data.tags.length > 0) {
    lines.push(`tags: [${data.tags.map((t) => `"${t}"`).join(", ")}]`);
  }
  lines.push("---");
  lines.push("");
  lines.push(stripTags(data.description));
  lines.push("");
  return lines.join("\n");
}