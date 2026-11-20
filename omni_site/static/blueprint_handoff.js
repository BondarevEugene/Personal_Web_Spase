/* Explicit Blueprint -> customer portal handoff; no automatic submission. */
(() => {
  "use strict";
  const button = document.getElementById("blueprint-handoff");
  const form = document.getElementById("blueprint-form");
  const status = document.getElementById("blueprint-handoff-status");
  if (!button || !form || !status) return;
  button.addEventListener("click", async () => {
    button.disabled = true;
    status.textContent = "Проверяем вход в кабинет…";
    try {
      const csrf = await fetch("/api/v1/builder/projects/csrf", {
        credentials: "same-origin", cache: "no-store"
      });
      if (csrf.status === 401) {
        status.replaceChildren(document.createTextNode("Войдите в кабинет: "));
        const link = document.createElement("a");
        link.href = "/account/login";
        link.textContent = "Авторизация";
        status.append(link);
        return;
      }
      if (!csrf.ok) throw new Error("Не удалось проверить авторизацию");
      const {csrf_token: token} = await csrf.json();
      const data = new FormData(form);
      const blueprint = {
        sector: data.get("sector"), team: data.get("team"),
        process: data.get("process"), priority: data.get("priority"),
        integrations: data.getAll("integration")
      };
      const names = {
        crm: "CRM и клиентские процессы",
        telegram: "Telegram и цифровые продукты",
        automation: "Автоматизация процессов"
      };
      const response = await fetch("/api/v1/blueprint/handoff", {
        method: "POST", credentials: "same-origin",
        headers: {"Content-Type": "application/json", "X-Omni-CSRF": token},
        body: JSON.stringify({
          blueprint, title: "Blueprint · " + (names[blueprint.sector] || "Проект")
        })
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof result.detail === "string" ?
          result.detail : "Не удалось создать заявку");
      }
      status.replaceChildren(document.createTextNode("Заявка сохранена. "));
      const link = document.createElement("a");
      link.href = result.url;
      link.textContent = "Открыть проект и ТЗ";
      status.append(link);
    } catch (error) {
      status.textContent = error.message || "Ошибка передачи";
    } finally {
      button.disabled = false;
    }
  });
})();
