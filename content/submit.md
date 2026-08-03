---
title: "Submit a resource"
description: "Submit a new harness engineering resource for review"
---

<p>Paste a URL and we'll fetch the title, description, and metadata automatically.
A pull request will be opened on <a href="{{< param githubRepo >}}">GitHub</a>
for review — you'll get a link to track it once it's created.</p>

<p>We focus on <strong>open-source</strong> and primary-source resources about
harness engineering. Commercial product pages and marketing content are usually
not a good fit.</p>

<noscript>
  <p class="form-error">This form requires JavaScript. If you prefer, you can
  <a href="{{< param githubRepo >}}/compare">open a pull request manually</a>
  instead.</p>
</noscript>

<form id="submit-form" class="submit-form" novalidate>
  <div class="field">
    <label for="link">URL <span class="req" aria-hidden="true">*</span></label>
    <input type="url" id="link" name="link" required
           placeholder="https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents">
    <small>Link to the article, repo, paper, podcast, or benchmark.</small>
    <span class="err" data-err="link"></span>
  </div>

  <div class="field">
    <label for="description">Why this matters for harness engineering <span class="opt">(optional)</span></label>
    <textarea id="description" name="description" rows="2" maxlength="500"
              placeholder="Optional: one or two sentences explaining the harness angle. If left blank, we'll auto-generate from the page."></textarea>
    <small>Help reviewers understand why this resource belongs here.</small>
    <span class="err" data-err="description"></span>
  </div>

  <div class="field">
    <label for="category">Category <span class="opt">(optional)</span></label>
    <select id="category" name="category">
      <option value="" selected>Auto-detect from content…</option>
      <option value="courses">Courses & Learning</option>
      <option value="foundations">Foundations</option>
      <option value="context">Context, Memory & Working State</option>
      <option value="constraints">Constraints, Guardrails & Safe Autonomy</option>
      <option value="specs">Specs, Agent Files & Workflow Design</option>
      <option value="evals">Evals & Observability</option>
      <option value="benchmarks">Benchmarks</option>
      <option value="runtimes">Runtimes, Harnesses & Reference Implementations</option>
    </select>
    <small>Leave on auto-detect and we'll classify from the content.</small>
  </div>

  <div class="field">
    <label for="submitter">Your name or GitHub handle <span class="opt">(optional)</span></label>
    <input type="text" id="submitter" name="submitter" maxlength="80"
           placeholder="octocat">
    <small>Used only in the PR body so reviewers can credit you. Leave blank to stay anonymous.</small>
  </div>

  <div class="actions">
    <button type="submit" id="submit-btn">Open pull request</button>
    <span class="form-status" id="form-status" role="status" aria-live="polite"></span>
  </div>
</form>

<div id="form-result" class="form-result" hidden>
  <h2>Pull request opened</h2>
  <p>Your submission is now a pull request on GitHub. Reviewers will check it
  shortly.</p>
  <p><a id="pr-link" href="#" target="_blank" rel="noopener noreferrer">Open the pull request →</a></p>
  <p><button type="button" id="submit-another">Submit another resource</button></p>
</div>