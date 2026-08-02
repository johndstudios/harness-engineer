// Thin GitHub REST client for the submission flow.

function headers(token) {
  return {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "X-GitHub-Api-Version": "2022-11-28",
  };
}

async function gh(apiBase, owner, repo, token, path, init = {}) {
  const res = await fetch(`${apiBase}/repos/${owner}/${repo}${path}`, {
    ...init,
    headers: { ...headers(token), ...(init.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    const err = new Error(`github ${init.method || "GET"} ${path} -> ${res.status}: ${body}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

/** Get the SHA of the default branch's tip (usually main). */
export async function getDefaultBranchSha(apiBase, owner, repo, token, branch) {
  const ref = await gh(apiBase, owner, repo, token, `/git/refs/heads/${branch}`);
  return ref.object.sha;
}

/** Create a new branch from the given SHA. Returns the new ref. */
export async function createBranch(apiBase, owner, repo, token, branchName, fromSha) {
  return gh(apiBase, owner, repo, token, "/git/refs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ref: `refs/heads/${branchName}`, sha: fromSha }),
  });
}

/** Create or update a file. Returns the commit. */
export async function putFile(apiBase, owner, repo, token, path, content, branchName, message) {
  return gh(apiBase, owner, repo, token, `/contents/${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, content: btoa(content), branch: branchName }),
  });
}

/** Open a pull request. Returns the PR object. */
export async function openPR(apiBase, owner, repo, token, head, base, title, body) {
  return gh(apiBase, owner, repo, token, "/pulls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, head, base, body, maintainer_can_modify: true }),
  });
}

/** Check whether a file already exists at the given path (HEAD-like). */
export async function fileExists(apiBase, owner, repo, token, path, branchName) {
  const res = await fetch(`${apiBase}/repos/${owner}/${repo}/contents/${path}?ref=${branchName}`, {
    headers: headers(token),
  });
  return res.status === 200;
}