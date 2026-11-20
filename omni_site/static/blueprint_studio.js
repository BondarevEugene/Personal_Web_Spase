/* Blueprint result utilities — no telemetry, persistence or outbound network. */
(() => {
  "use strict";
  const output = document.getElementById("blueprint-output");
  if (!output) return;
  const status = document.getElementById("blueprint-copy-status");
  document.getElementById("blueprint-copy")?.addEventListener("click", async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(output.value);
      if (status) status.textContent = "Бриф скопирован. Вставьте его в ваше сообщение.";
    } catch (_) {
      output.focus();
      output.select();
      if (status) status.textContent = "Выделен текст брифа. Скопируйте его вручную.";
    }
  });
  document.getElementById("blueprint-print")?.addEventListener("click", () => {
    window.print();
  });
})();