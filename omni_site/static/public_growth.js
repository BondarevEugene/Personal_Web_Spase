/* OMNIFACTORY public business-impact calculator. No tracking, no external APIs. */
(function () {
  "use strict";
  const form = document.getElementById("growth-calculator");
  if (!form) return;
  const number = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 });
  const money = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 });
  const solutions = Object.freeze({
    clients: {
      title: "CRM и управление заказами",
      description: "Единый реестр проектов, этапов, документов и клиентских согласований.",
      href: "/account/projects", link: "Посмотреть рабочий кабинет ↗"
    },
    dialogues: {
      title: "Telegram-боты и диалоговые сценарии",
      description: "Создавайте ветвящиеся диалоги, проверяйте их в симуляторе и экспортируйте Python-проект.",
      href: "/architect", link: "Открыть Graph Studio ↗"
    },
    processes: {
      title: "Автоматизация процессов",
      description: "Проектируйте последовательности действий, условия и проверки процессов в Automation Studio.",
      href: "/automation/studio", link: "Открыть Automation Studio ↗"
    }
  });
  function numeric(id, min, max) {
    const element = document.getElementById(id);
    const value = Number(element.value);
    return Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : 0;
  }
  function recalculate() {
    const count = numeric("growth-volume", 1, 1000000);
    const minutes = numeric("growth-minutes", 1, 480);
    const rate = numeric("growth-rate", 0, 100000);
    const share = numeric("growth-share", 0, 100);
    const hours = count * minutes * share / 6000;
    const estimate = hours * rate;
    document.getElementById("growth-share-value").textContent = number.format(share) + "%";
    document.getElementById("growth-hours").textContent = number.format(hours);
    document.getElementById("growth-money").textContent = money.format(estimate);
    document.getElementById("growth-method").textContent =
      number.format(count) + " операций × " + number.format(minutes) +
      " минут × " + number.format(share) + "% = " + number.format(hours) + " часа(ов).";
  }
  // Hypothetical starting inputs: these are NOT measured project outcomes.
  const presets = Object.freeze({
    food: { count: 120, minutes: 12, rate: 250, share: 50 },
    crm: { count: 450, minutes: 6, rate: 300, share: 65 },
    bot: { count: 300, minutes: 5, rate: 240, share: 70 }
  });
  document.querySelectorAll("[data-growth-preset]").forEach(function(button) {
    button.addEventListener("click", function () {
      const preset = presets[button.dataset.growthPreset];
      if (!preset) return;
      document.getElementById("growth-volume").value = String(preset.count);
      document.getElementById("growth-minutes").value = String(preset.minutes);
      document.getElementById("growth-rate").value = String(preset.rate);
      document.getElementById("growth-share").value = String(preset.share);
      document.querySelectorAll("[data-growth-preset]").forEach(function(item) {
        item.setAttribute("aria-pressed", String(item === button));
      });
      recalculate();
    });
  });
  form.addEventListener("input", function (event) {
    // Any manual change makes the values the visitor's own scenario.
    if (event.isTrusted) document.querySelectorAll("[data-growth-preset]").forEach(function(item) {
      item.setAttribute("aria-pressed", "false");
    });
  });
  form.addEventListener("input", recalculate);
  form.addEventListener("submit", function(event){event.preventDefault();recalculate();});
  recalculate();
  document.querySelectorAll("[data-solution]").forEach(function(button) {
    button.addEventListener("click", function () {
      const selection = solutions[button.dataset.solution];
      if (!selection) return;
      document.querySelectorAll("[data-solution]").forEach(function(item) {
        item.setAttribute("aria-pressed", String(item === button));
      });
      document.getElementById("growth-solution-title").textContent = selection.title;
      document.getElementById("growth-solution-desc").textContent = selection.description;
      const link = document.getElementById("growth-solution-link");
      link.setAttribute("href", selection.href);
      link.textContent = selection.link;
    });
  });
}());
