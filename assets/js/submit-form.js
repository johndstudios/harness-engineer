(() => {
  "use strict";

  const form = document.getElementById("submit-form");
  if (!form) return;

  const status = document.getElementById("form-status");
  const submitBtn = document.getElementById("submit-btn");
  const resultBox = document.getElementById("form-result");
  const prLink = document.getElementById("pr-link");
  const submitAnother = document.getElementById("submit-another");

  function setError(name, msg) {
    const el = form.querySelector(`[data-err="${name}"]`);
    if (el) {
      el.textContent = msg || "";
      el.classList.toggle("err-on", Boolean(msg));
    }
  }

  function clearAllErrors() {
    form.querySelectorAll("[data-err]").forEach((el) => {
      el.textContent = "";
      el.classList.remove("err-on");
    });
  }

  function validate(payload) {
    const errors = {};
    const link = (payload.link || "").trim();
    if (!link) errors.link = "Required";
    else if (!/^https?:\/\/\S+$/i.test(link)) errors.link = "Must be an http(s) URL";
    return errors;
  }

  function setFormState(state, msg) {
    status.textContent = msg || "";
    submitBtn.disabled = state === "loading";
    submitBtn.classList.toggle("loading", state === "loading");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAllErrors();

    const payload = {
      link: form.link.value,
      description: form.description.value,
      category: form.category.value,
      submitter: form.submitter.value,
    };

    const errors = validate(payload);
    if (Object.keys(errors).length) {
      for (const [k, v] of Object.entries(errors)) setError(k, v);
      return;
    }

    if (!window.SUBMIT_ENDPOINT) {
      setFormState("error", "Submission endpoint is not configured yet.");
      return;
    }

    setFormState("loading", "Fetching page and opening pull request…");

    try {
      const headers = { "Content-Type": "application/json" };
      if (window.FORM_SECRET) headers["Authorization"] = `Bearer ${window.FORM_SECRET}`;
      const res = await fetch(window.SUBMIT_ENDPOINT, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg = data && data.error ? data.error : `Request failed (${res.status})`;
        if (data && data.fields) for (const [k, v] of Object.entries(data.fields)) setError(k, v);
        setFormState("error", msg);
        return;
      }
      if (data && data.pr_url && prLink) {
        prLink.href = data.pr_url;
        prLink.textContent = data.pr_url;
      }
      form.hidden = true;
      resultBox.hidden = false;
      setFormState("idle", "");
    } catch (err) {
      setFormState("error", "Network error — please try again.");
    }
  });

  if (submitAnother) {
    submitAnother.addEventListener("click", () => {
      form.reset();
      clearAllErrors();
      form.hidden = false;
      resultBox.hidden = true;
      setFormState("idle", "");
      form.link.focus();
    });
  }
})();