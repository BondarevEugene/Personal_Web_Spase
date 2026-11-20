/* Accessible, data-free illustrated workflow walkthrough. No requests or tracking. */
(() => {
  "use strict";
  const tabs = [...document.querySelectorAll("[data-demo-tab]")];
  const panels = [...document.querySelectorAll("[data-demo-panel]")];
  if (!tabs.length || !panels.length) return;

  function choosePanel(slug, updateHistory) {
    const panel = panels.find(item => item.dataset.demoPanel === slug);
    if (!panel) return;
    panels.forEach(item => { item.hidden = item !== panel; });
    tabs.forEach(tab => {
      tab.setAttribute("aria-pressed", String(tab.dataset.demoTab === slug));
    });
    if (updateHistory && window.history && window.history.replaceState) {
      window.history.replaceState(null, "", "/demo/" + encodeURIComponent(slug));
    }
  }

  panels.forEach(panel => {
    const nodes = [...panel.querySelectorAll("[data-demo-step]")];
    const progress = panel.querySelector("[data-demo-progress]");
    const counter = panel.querySelector("[data-demo-counter]");
    const heading = panel.querySelector("[data-demo-current-title]");
    const description = panel.querySelector("[data-demo-current-description]");
    const number = panel.querySelector("[data-demo-current-number]");
    const back = panel.querySelector("[data-demo-prev]");
    const next = panel.querySelector("[data-demo-next]");
    let current = 0;

    function showStep(index) {
      if (!Number.isInteger(index) || index < 0 || index >= nodes.length) return;
      current = index;
      const active = nodes[index];
      nodes.forEach((node, i) => {
        node.setAttribute("aria-pressed", String(i === current));
      });
      heading.textContent = active.dataset.stepTitle || "";
      description.textContent = active.dataset.stepExplanation || "";
      number.textContent = active.dataset.stepNumber || String(index + 1);
      progress.style.width = String(100 * (index + 1) / nodes.length) + "%";
      counter.textContent = String(index + 1).padStart(2, "0") +
        " / " + String(nodes.length).padStart(2, "0");
      back.disabled = index === 0;
      next.disabled = index === nodes.length - 1;
      next.textContent = next.disabled ? "Маршрут завершён ✓" : "Следующий этап →";
    }
    nodes.forEach((node, i) => node.addEventListener("click", () => showStep(i)));
    back.addEventListener("click", () => showStep(current - 1));
    next.addEventListener("click", () => showStep(current + 1));
    showStep(0);
  });

  tabs.forEach(tab => tab.addEventListener("click", () => {
    choosePanel(tab.dataset.demoTab, true);
  }));
  const slug = decodeURIComponent(window.location.pathname.split("/").pop() || "");
  if (panels.some(item => item.dataset.demoPanel === slug)) choosePanel(slug, false);
})();