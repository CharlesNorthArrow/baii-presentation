// ── Gap categories: single source of truth ─────────────────
// Shared by index.html (map colors, legend, tooltips) and
// methodology.html (Step 5 decision tree). Categories 1 to 4 answer
// Q2 (transit graded against transit across Connecticut); 5 and 6
// answer Q1 (the reachable set is thin by any mode). The relativity
// lives in the labels on purpose: a top quintile of CT transit is
// not car-level access.
window.GAP_CLASSES = {
  1: { color: "#1A6E64", label: "Among CT's best transit access", short: "Among CT's best" },  // deep teal
  2: { color: "#4F9D90", label: "Good transit access, for CT",    short: "Good, for CT" },     // mid teal
  3: { color: "#9BC8BF", label: "Some transit access",            short: "Some transit" },     // light teal
  4: { color: "#6B4A8E", label: "Limited, mostly needs a car",    short: "Mostly needs a car" }, // purple
  5: { color: "#D9B877", label: "Few book sources by any mode",   short: "Few sources" },      // light amber
  6: { color: "#8A5A1A", label: "Very few book sources by any mode", short: "Very few sources" }, // deep amber
};

// Stamp any [data-gap-label] elements (the Step 5 tree leaves on the
// methodology page) so their text can never drift from the table.
(function () {
  function stamp() {
    document.querySelectorAll("[data-gap-label]").forEach(el => {
      const n = +el.dataset.gapLabel;
      if (window.GAP_CLASSES[n]) el.textContent = `[${n}] ${window.GAP_CLASSES[n].label}`;
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", stamp, { once: true });
  } else {
    stamp();
  }
})();
