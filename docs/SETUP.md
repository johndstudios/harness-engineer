# Setup: GitHub App + Cloudflare Worker for the submission form

This guide explains how to wire up the auto-PR submission form so that visitors
can submit a resource from the site and a pull request opens automatically for
review.

## Overview

```
[site form] --POST JSON--> [Cloudflare Worker] --GitHub App--> [repo PR]
                            validates payload
                            mints App JWT (WebCrypto)
                            fetches installation token
                            creates branch + commit + PR
```

The Worker authenticates as a **GitHub App** installed on your repo. The App
needs only **Contents: Read & Write** and **Pull requests: Write** on the
target repository — no admin rights.

## 1. Create the GitHub App

1. Go to <https://github.com/settings/apps> → **New GitHub App** (use the
   `johndstudios` account that owns the repo, or whichever account you want the
   bot to post as).
2. Fill in:
   - **GitHub App name:** `harness-engineer-submit` (or any name you like).
   - **Homepage URL:** your site URL.
   - **Webhook:** uncheck **Active** — we don't need webhooks; the Worker is
     called by the form, not by GitHub events.
   - **Repository permissions:**
     - **Contents:** Read and write
     - **Pull requests:** Write
   - **Account permissions:** none needed.
   - **Where can this GitHub App be installed:** Only on this account (or any
     account — your call).
3. Click **Create GitHub App**.
4. On the app's settings page, note:
   - **App ID** (numeric, near the top).
   - **Private key:** click **Generate a private key** and download the `.pem`
     file. You'll paste the contents (or single-line version) as a Worker
     secret.
5. Install the app on the target repo (`johndstudios/harness-engineer`). After
   installing, note the **installation ID** — it appears in the URL of the
   installation settings page, e.g.
   `https://github.com/settings/installations/12345678` → ID is `12345678`.

## 2. Deploy the Cloudflare Worker

The Worker code lives in `worker/`. You need a Cloudflare account; the free
tier is plenty.

1. Install Wrangler (bundled via `worker/`):
   ```bash
   cd worker
   npm install
   ```
2. Authenticate Wrangler:
   ```bash
   npx wrangler login
   ```
3. Set the Worker secrets (these are NOT committed to the repo):
   ```bash
   npx wrangler secret put GITHUB_APP_ID          # e.g. 123456
   npx wrangler secret put GITHUB_PRIVATE_KEY     # paste the full PEM, including -----BEGIN/END-----
   npx wrangler secret put GITHUB_INSTALLATION_ID # e.g. 12345678
   npx wrangler secret put FORM_SECRET            # choose a long random string; the form sends this as Bearer token
   ```
   The private key can be pasted as the multi-line PEM; Wrangler stores it as
   an environment variable. The Worker normalizes `\n` escapes if present.
4. Edit `worker/wrangler.toml` and set the non-secret vars to match your repo:
   ```toml
   [vars]
   GITHUB_OWNER = "johndstudios"
   GITHUB_REPO = "harness-engineer"
   ALLOWED_ORIGINS = "https://harness-engineer.dev,https://johndstudios.github.io"
   ```
5. Deploy:
   ```bash
   npx wrangler deploy
   ```
   Wrangler prints the Worker URL, e.g.
   `https://harness-engineer-submit.<your-account>.workers.dev`.

## 3. Wire the form to the Worker

The site reads the Worker URL from the Hugo param `submitEndpoint`. Set it as
a CI build variable so it isn't committed to the repo:

1. In your GitHub repo settings → **Settings → Secrets and variables →
   Actions → Variables**, add a variable:
   - **Name:** `HUGO_PARAM_SUBMITENDPOINT`
   - **Value:** the Worker URL from step 2.5 (the `workers.dev` URL or your
     custom domain).
2. Also add a repository secret for the form's shared token so the JS can send
   it in the `Authorization` header:
   - **Name:** `HUGO_PARAM_FORMSECRET`
   - **Value:** the same `FORM_SECRET` string you set on the Worker.
3. The CI and deploy workflows already pass `HUGO_PARAM_*` env vars to Hugo, so
   the build will pick up the Worker URL and secret automatically and inject
   them into the form's JavaScript.

## 4. Configure GitHub Pages

1. In the repo, go to **Settings → Pages**.
2. Set **Source** to **Deploy from a branch**.
3. Choose the **`gh-pages`** branch and **`/ (root)`** folder.
4. Save. The first deploy workflow run will publish the site.

The `gh-pages` branch is created automatically by the deploy workflow on the
first push to `main`. Each open PR gets a preview at
`https://<owner>.github.io/<repo>/pr-<n>/`, linked in a PR comment. When a PR
closes, the `cleanup-preview.yml` workflow removes its preview directory.

## 5. Test the flow

1. Open the site's `/submit/` page.
2. Fill in a test resource (use a throwaway URL so you don't duplicate a real
   one).
3. Submit. The Worker should open a PR on the repo within a few seconds.
4. Verify the PR body, the created branch, and the committed file in
   `content/resources/`.
5. Check that the preview deploy runs and a comment with the preview URL
   appears on the PR.
6. Close the PR to confirm the preview directory is removed.

## 6. Local development

To run the Worker locally:

```bash
cd worker
echo 'GITHUB_APP_ID=...' > .dev.vars
echo 'GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMII...\n-----END RSA PRIVATE KEY-----"' >> .dev.vars
echo 'GITHUB_INSTALLATION_ID=...' >> .dev.vars
echo 'FORM_SECRET=dev-secret' >> .dev.vars
npx wrangler dev
```

`.dev.vars` is gitignored. Point your local site build at the dev Worker:

```bash
HUGO_PARAM_SUBMITENDPOINT=http://localhost:8787 HUGO_PARAM_FORMSECRET=dev-secret \
  hugo server
```

The form validation tests:

```bash
cd worker
npm run typecheck
npm test
```

## 7. Security notes

- The Worker uses a **shared bearer token** (`FORM_SECRET`) as a cheap rate
  limit. It's not real auth — anyone can read the token from the deployed JS.
  The token prevents casual abuse but not a determined attacker. For stronger
  protection, add a CAPTCHA (e.g., Turnstile, also free on Cloudflare) before
  the Worker call.
- The GitHub App has minimal permissions (Contents write + PR write on one
  repo). It cannot push to `main` directly — it only opens PRs for review.
- All user-supplied text is HTML-stripped server-side before being written
  into the resource file.
- Duplicate titles are rejected with a 409 before any branch is created.