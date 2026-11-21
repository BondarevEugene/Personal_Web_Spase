/* Explicit, user-triggered Blueprint -> customer portal handoff. */
(() => {
  "use strict";
  const button = document.getElementById("blueprint-handoff");
  const form = document.getElementById("blueprint-form");
  const status = document.getElementById("blueprint-handoff-status");
  if (!button || !form || !status) return;

  const safeProjectUrl = (value) => {
    if (typeof value !== "string" || !value.startsWith("/account/")) return null;
    if (value.startsWith("//") || /[\\\r\n]/.test(value)) return null;
    const url = new URL(value, window.location.origin);
    return url.origin === window.location.origin ? url.pathname + url.search : null;
  };

  const showLogin = () => {
    status.replaceChildren(document.createTextNode("Войдите в кабинет: "));
    const link = document.createElement("a");
    link.href = "/account/login";
    link.textContent = "Авторизация";
    status.append(link);
  };

  button.addEventListener("click", async () => {
    if (button.disabled) return;
    button.disabled = true;
    status.textContent = "Проверяем вход в кабинет…";
    try {
      const csrf = await fetch("/api/v1/builder/projects/csrf", {
        credentials: "same-origin", cache: "no-store"
      });
      if (csrf.status === 401 || csrf.status === 403) {
        showLogin();
        return;
      }
      if (!csrf.ok) throw new Error("Не удалось проверить авторизацию. Повторите попытку.");
      const csrfData = await csrf.json();
      const token = csrfData.csrf_token;
      if (typeof token !== "string" || !token) {
        throw new Error("Не получен защитный токен. Обновите страницу.");
      }
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
      if (response.status === 401 || response.status === 403) {
        showLogin();
        return;
      }
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          typeof result.detail === "string" && result.detail.length < 240
            ? result.detail : "Не удалось создать заявку. Повторите попытку."
        );
      }
      const target = safeProjectUrl(result.url);
      if (!target) throw new Error("Заявка создана, но ссылка недоступна. Откройте кабинет.");
      status.replaceChildren(document.createTextNode("Заявка сохранена. "));
      const link = document.createElement("a");
      link.href = target;
      link.textContent = "Открыть проект и ТЗ";
      status.append(link);
    } catch (error) {
      status.textContent = error.message || "Ошибка передачи. Повторите попытку.";
    } finally {
      button.disabled = false;
    }
  });
})();
