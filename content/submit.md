---
title: "Submit a resource"
description: "Submit a new harness engineering resource for review"
---

<p>Fill in the details below and submit. A pull request will be opened on
<a href="{{< param githubRepo >}}">GitHub</a> for review — you'll get a
link to track it once it's created.</p>

<noscript>
  <p class="form-error">This form requires JavaScript. If you prefer, you can
  <a href="{{< param githubRepo >}}/compare">open a pull request manually</a>
  instead.</p>
</noscript>

<form id="submit-form" class="submit-form" novalidate>
  <div class="field">
    <label for="title">Title <span class="req" aria-hidden="true">*</span></label>
    <input type="text" id="title" name="title" required maxlength="200"
           autocomplete="off" placeholder="Effective harnesses for long-running agents">
    <small>The resource title as it appears on the source page.</small>
    <span class="err" data-err="title"></span>
  </div>

  <div class="field">
    <label for="link">URL <span class="req" aria-hidden="true">*</span></label>
    <input type="url" id="link" name="link" required
           placeholder="https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents">
    <small>Canonical URL of the article, repo, or benchmark.</small>
    <span class="err" data-err="link"></span>
  </div>

  <div class="field-row">
    <div class="field">
      <label for="category">Category <span class="req" aria-hidden="true">*</span></label>
      <select id="category" name="category" required>
        <option value="" selected disabled>Select a category…</option>
        <option value="courses">Courses & Learning</option>
        <option value="foundations">Foundations</option>
        <option value="context">Context, Memory & Working State</option>
        <option value="constraints">Constraints, Guardrails & Safe Autonomy</option>
        <option value="specs">Specs, Agent Files & Workflow Design</option>
        <option value="evals">Evals & Observability</option>
        <option value="benchmarks">Benchmarks</option>
        <option value="runtimes">Runtimes, Harnesses & Reference Implementations</option>
      </select>
      <span class="err" data-err="category"></span>
    </div>

    <div class="field">
      <label for="resource_kind">Kind <span class="req" aria-hidden="true">*</span></label>
      <select id="resource_kind" name="resource_kind" required>
        <option value="" selected disabled>Select a kind…</option>
        <option value="article">Article</option>
        <option value="tool">Tool</option>
        <option value="benchmark">Benchmark</option>
        <option value="course">Course</option>
        <option value="spec">Spec</option>
        <option value="podcast">Podcast</option>
        <option value="video">Video</option>
        <option value="paper">Paper</option>
      </select>
      <span class="err" data-err="resource_kind"></span>
    </div>
  </div>

  <div class="field">
    <label for="source">Source <span class="req" aria-hidden="true">*</span></label>
    <input type="text" id="source" name="source" required maxlength="60"
           placeholder="anthropic" autocomplete="off">
    <small>Short slug for the author or origin, e.g. <code>anthropic</code>,
    <code>openai</code>, <code>langchain</code>, or the GitHub owner.</small>
    <span class="err" data-err="source"></span>
  </div>

  <div class="field">
    <label for="description">Description <span class="req" aria-hidden="true">*</span></label>
    <textarea id="description" name="description" required rows="3" maxlength="500"
              placeholder="Anthropic's core article on initializer agents, feature lists, init.sh, self-verification, and handoff artifacts across many context windows."></textarea>
    <small>One or two sentences explaining why this matters for harness engineering.</small>
    <span class="err" data-err="description"></span>
  </div>

  <div class="field">
    <label for="tags">Tags <span class="opt">(optional)</span></label>
    <input type="text" id="tags" name="tags" maxlength="200"
           placeholder="context, long-running, handoff">
    <small>Comma-separated lowercase tags describing the resource's topics.</small>
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