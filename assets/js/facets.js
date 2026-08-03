(() => {
  "use strict";
  const bar = document.getElementById("facet-bar");
  const list = document.getElementById("resource-list");
  if (!bar || !list) return;
  const noResults = document.getElementById("no-results");
  const clearBtn = document.getElementById("clear-facets");
  const cards = Array.from(list.querySelectorAll(".resource-card"));

  function activeFilters() {
    const kinds = new Set();
    const cats = new Set();
    bar.querySelectorAll('input[name="kind"]:checked').forEach((cb) => kinds.add(cb.value));
    bar.querySelectorAll('input[name="category"]:checked').forEach((cb) => cats.add(cb.value));
    return { kinds, cats };
  }

  function applyFilters() {
    const { kinds, cats } = activeFilters();
    let visible = 0;
    cards.forEach((card) => {
      const showKind = kinds.size === 0 || kinds.has(card.dataset.kind);
      const showCat = cats.size === 0 || cats.has(card.dataset.category);
      const show = showKind && showCat;
      card.style.display = show ? "" : "none";
      if (show) visible++;
    });
    if (noResults) {
      noResults.classList.toggle("shown", visible === 0);
      noResults.classList.toggle("hidden", visible > 0);
    }
    list.style.display = visible === 0 ? "none" : "";
  }

  bar.addEventListener("change", applyFilters);
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      bar.querySelectorAll("input[type=checkbox]").forEach((cb) => (cb.checked = false));
      applyFilters();
    });
  }
})();