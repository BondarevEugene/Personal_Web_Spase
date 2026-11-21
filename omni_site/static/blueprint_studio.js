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
  const save = document.getElementById("blueprint-save");
  save?.addEventListener("click", async () => {
    const feedback = document.getElementById("blueprint-save-status");
    const form = document.getElementById("blueprint-form");
    if (!form || !feedback) return;
    save.disabled = true;
    feedback.textContent = "Проверяем авторизацию и сохраняем сценарий…";
    try {
      const csrfResponse = await fetch("/api/v1/builder/projects/csrf", {
        credentials: "same-origin", cache: "no-store"
      });
      if (csrfResponse.status === 401) {
        feedback.replaceChildren(document.createTextNode("Для сохранения войдите в кабинет: "));
        const link = document.createElement("a");
        link.href = "/account/login";
        link.textContent = "Войти";
        feedback.append(link);
        return;
      }
      if (!csrfResponse.ok) throw new Error("Не удалось проверить сессию");
      const {csrf_token: token} = await csrfResponse.json();
      const data = new FormData(form);
      const blueprint = {
        sector: data.get("sector"),
        team: data.get("team"),
        process: data.get("process"),
        priority: data.get("priority"),
        integrations: data.getAll("integration")
      };
      const response = await fetch("/api/v1/blueprint/projects", {
        method: "POST",
        credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-Omni-CSRF": token},
        body: JSON.stringify({blueprint, name: "Telegram · " + new Date().toLocaleDateString("ru-RU")})
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(typeof error.detail === "string" ? error.detail : "Ошибка сохранения");
      }
      const project = await response.json();
      feedback.replaceChildren(document.createTextNode("Сценарий сохранён. "));
      const link = document.createElement("a");
      link.href = "/account/graph-project/" + encodeURIComponent(project.id);
      link.textContent = "Открыть Graph Studio";
      feedback.append(link);
      feedback.dataset.projectId = project.id;
    } catch (error) {
      feedback.textContent = error.message || "Не удалось сохранить проект";
    } finally {
      save.disabled = false;
    }
  });
  document.getElementById("blueprint-print")?.addEventListener("click", () => {
    window.print();
  });
})();