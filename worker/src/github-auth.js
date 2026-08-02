// GitHub App authentication using WebCrypto (no Node deps needed in Workers).

const ENC = new TextEncoder();
const DEC = new TextDecoder();

function base64UrlEncode(bytes) {
  let s = btoa(String.fromCharCode(...new Uint8Array(bytes)));
  return s.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function pemToArrayBuffer(pem) {
  // Accept a PEM string possibly containing escaped "\n" sequences.
  const clean = pem.replace(/\\n/g, "\n").replace(/-----[^-]+-----/g, "").replace(/\s+/g, "");
  // base64 -> binary string -> bytes
  const binary = atob(clean);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

async function importPrivateKey(pem) {
  return crypto.subtle.importKey(
    "pkcs8",
    pemToArrayBuffer(pem),
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
}

async function makeJwt(payload, privateKey) {
  const header = { alg: "RS256", typ: "JWT" };
  const headerB64 = base64UrlEncode(ENC.encode(JSON.stringify(header)));
  const payloadB64 = base64UrlEncode(ENC.encode(JSON.stringify(payload)));
  const signingInput = `${headerB64}.${payloadB64}`;
  const sig = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    privateKey,
    ENC.encode(signingInput),
  );
  return `${signingInput}.${base64UrlEncode(sig)}`;
}

/**
 * Mint a short-lived GitHub App JWT (10 min max), used to fetch an installation
 * token. Returns the signed JWT string.
 */
export async function appJwt(appId, privateKeyPem) {
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iat: now - 60,
    exp: now + 9 * 60,
    iss: Number(appId),
  };
  const key = await importPrivateKey(privateKeyPem);
  return makeJwt(payload, key);
}

/**
 * Exchange the App JWT for an installation access token (scoped to the repo).
 * Returns `{ token, expiresAt }`.
 */
export async function installationToken(apiBase, jwt, installationId) {
  const res = await fetch(`${apiBase}/app/installations/${installationId}/access_tokens`, {
    method: "POST",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${jwt}`,
      "X-GitHub-Api-Version": "2022-11-28",
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`installation token failed (${res.status}): ${body}`);
  }
  const data = await res.json();
  return { token: data.token, expiresAt: data.expires_at };
}