/* Explicit Blueprint upload -> existing authenticated Graph Studio persistence. */
(() => {
  "use strict";
  const form = document.getElementById("blueprint-graph-import-form");
  const status = document.getElementById("blueprint-graph-import-status");
  if (!form || !status) return;
  const button = form.querySelector('button[type="submit"]');
  const showLogin = () => {
    status.replaceChildren(document.createTextNode("Войдите в кабинет: "));
    const link = document.createElement("a");
    link.href = "/account/login";
    link.textContent = "Авторизация";
    status.append(link);
  };
  const previewButton = document.getElementById("blueprint-graph-preview");
  const previewResult = document.getElementById("blueprint-graph-preview-result");
  previewButton?.addEventListener("click", async () => {
    if (!previewResult || previewButton.disabled) return;
    if (!form.reportValidity()) return;
    previewButton.disabled = true;
    previewResult.textContent = "Проверяем схему…";
    try {
      const response = await fetch("/api/v1/blueprint/import-graph/preview", {
        method: "POST", credentials: "same-origin",
        body: new FormData(form)
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof data.detail === "string"
          ? data.detail : "Не удалось проверить схему");
      }
      const heading = document.createElement("h3");
      heading.textContent = "Предпросмотр · " + data.summary.nodes + " блоков, " +
        data.summary.choices + " развилок";
      const list = document.createElement("ol");
      for (const node of data.scenario.nodes) {
        const item = document.createElement("li");
        item.textContent = node.id + " · " + node.kind +
          (node.text ? " — " + node.text : "");
        list.append(item);
      }
      const note = document.createElement("p");
      note.textContent = "Это только проверка. Ничего не сохранено и не запущено.";
      previewResult.replaceChildren(heading, list, note);
    } catch (error) {
      previewResult.textContent = error.message || "Ошибка предпросмотра";
    } finally {
      previewButton.disabled = false;
    }
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (button.disabled) return;
    button.disabled = true;
    status.textContent = "Проверяем доступ…";
    try {
      const csrfResponse = await fetch("/api/v1/builder/projects/csrf", {
        credentials: "same-origin", cache: "no-store"
      });
      if (csrfResponse.status === 401 || csrfResponse.status === 403) {
        showLogin();
        return;
      }
      if (!csrfResponse.ok) throw new Error("Не удалось проверить сессию");
      const {csrf_token} = await csrfResponse.json();
      if (typeof csrf_token !== "string" || !csrf_token) {
        throw new Error("Защитный токен недоступен");
      }
      status.textContent = "Создаём редактируемый проект…";
      const response = await fetch("/api/v1/blueprint/import-graph", {
        method: "POST", credentials: "same-origin",
        headers: {"X-Omni-CSRF": csrf_token},
        body: new FormData(form)
      });
      if (response.status === 401 || response.status === 403) {
        showLogin();
        return;
      }
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(typeof result.detail === "string"
          ? result.detail : "Импорт не выполнен (" + response.status + ")");
      }
      if (typeof result.id !== "string" ||
          !/^[a-f0-9-]{36}$/i.test(result.id)) {
        throw new Error("Проект сохранён, но его идентификатор некорректен");
      }
      status.replaceChildren(document.createTextNode("Проект сохранён. "));
      const link = document.createElement("a");
      link.href = "/account/graph-project/" + encodeURIComponent(result.id);
      link.textContent = "Открыть редактор Graph Studio";
      status.append(link);
    } catch (error) {
      status.textContent = error.message || "Ошибка импорта";
    } finally {
      button.disabled = false;
    }
  });
})();
