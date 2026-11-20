/* Progressive-enhancement case filter. All cards remain visible without JS. */
(() => {
  "use strict";
  const filters = Array.from(document.querySelectorAll("[data-case-filter]"));
  const cards = Array.from(document.querySelectorAll("[data-case-category]"));
  const count = document.getElementById("case-count");
  if (!filters.length || !cards.length) return;
  filters.forEach(button => {
    button.addEventListener("click", () => {
      const category = button.dataset.caseFilter;
      if (!category) return;
      let visible = 0;
      cards.forEach(card => {
        const show = category === "Все" || card.dataset.caseCategory === category;
        card.hidden = !show;
        if (show) visible += 1;
      });
      filters.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
      if (count) count.textContent = "Показано проектов: " + visible;
    });
  });
})();