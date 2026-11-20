/* Authenticated Graph Studio editor. No local storage or embedded credentials. */
(() => {
  "use strict";
  const root = document.getElementById("graph-editor");
  if (!root) return;
  const projectId = root.dataset.projectId;
  const fields = document.getElementById("graph-editor-fields");
  const status = document.getElementById("graph-editor-status");
  const save = document.getElementById("graph-save");
  let project = null;

  const field = (label, value, update, multiline = false) => {
    const wrapper = document.createElement("label");
    wrapper.style.cssText = "display:block;margin:12px 0;color:#d5def3";
    const heading = document.createElement("span");
    heading.textContent = label;
    heading.style.display = "block";
    const control = document.createElement(multiline ? "textarea" : "input");
    control.value = value ?? "";
    control.style.cssText = "display:block;width:100%;box-sizing:border-box;" +
      "background:#111b2e;color:#fff;border:1px solid #50617d;" +
      "border-radius:8px;padding:12px;margin-top:6px;font:inherit";
    if (multiline) control.rows = 3;
    control.addEventListener("input", () => update(control.value));
    wrapper.append(heading, control);
    return wrapper;
  };

  const render = () => {
    fields.replaceChildren();
    fields.append(field("Название проекта", project.scenario.name,
      value => { project.scenario.name = value; }));
    fields.append(field("Начальный блок", project.scenario.start,
      value => { project.scenario.start = value; }));
    for (const node of project.scenario.nodes) {
      const panel = document.createElement("section");
      panel.style.cssText = "margin:18px 0;padding:16px;border:1px solid #394862;" +
        "border-radius:12px;background:#152037";
      const title = document.createElement("h3");
      title.textContent = node.id + " · " + node.kind;
      panel.append(title);
      panel.append(field("ID блока", node.id, value => {
        const old = node.id;
        node.id = value;
        if (project.scenario.start === old) project.scenario.start = value;
        for (const other of project.scenario.nodes) {
          if (other.next === old) other.next = value;
          if (other.true_target === old) other.true_target = value;
          if (other.false_target === old) other.false_target = value;
          for (const option of other.options || []) {
            if (option.target === old) option.target = value;
          }
        }
        if (project.positions[old]) {
          project.positions[value] = project.positions[old];
          delete project.positions[old];
        }
      }));
      if ("text" in node) panel.append(field("Текст", node.text,
        value => { node.text = value; }, true));
      if (node.next !== null && node.next !== undefined) {
        panel.append(field("Следующий блок", node.next,
          value => { node.next = value || null; }));
      }
      if (node.variable) panel.append(field("Переменная", node.variable,
        value => { node.variable = value; }));
      for (const [index, option] of (node.options || []).entries()) {
        panel.append(field("Кнопка " + (index + 1), option.label,
          value => { option.label = value; }));
        panel.append(field("Переход кнопки " + (index + 1), option.target,
          value => { option.target = value; }));
      }
      fields.append(panel);
    }
  };

  const load = async () => {
    const response = await fetch("/api/v1/builder/projects/" +
      encodeURIComponent(projectId), {credentials: "same-origin", cache: "no-store"});
    if (!response.ok) throw new Error("Не удалось открыть сохранённый проект");
    project = await response.json();
    render();
    status.textContent = "Проект загружен. Изменения пока не сохранены.";
  };

  save.addEventListener("click", async () => {
    if (!project) return;
    save.disabled = true;
    status.textContent = "Сохраняем…";
    try {
      const csrf = await fetch("/api/v1/builder/projects/csrf",
        {credentials: "same-origin", cache: "no-store"});
      if (!csrf.ok) throw new Error("Сессия истекла. Войдите повторно.");
      const {csrf_token} = await csrf.json();
      const response = await fetch("/api/v1/builder/projects/" +
        encodeURIComponent(projectId), {
          method: "PUT", credentials: "same-origin",
          headers: {"Content-Type": "application/json", "X-Omni-CSRF": csrf_token},
          body: JSON.stringify({
            scenario: project.scenario,
            positions: project.positions,
            groups: project.groups
          })
        });
      if (!response.ok) {
        const details = await response.json().catch(() => ({}));
        throw new Error(typeof details.detail === "string"
          ? details.detail : "Сервер отклонил изменения (" + response.status + ")");
      }
      status.textContent = "Изменения сохранены. Можно закрыть и снова открыть проект.";
    } catch (error) {
      status.textContent = error.message || "Не удалось сохранить изменения";
    } finally {
      save.disabled = false;
    }
  });
  load().catch(error => { status.textContent = error.message; save.disabled = true; });
})();
