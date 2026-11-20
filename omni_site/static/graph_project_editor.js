/* Authenticated Graph Studio editor. No local storage or embedded credentials. */
(() => {
  "use strict";
  const root = document.getElementById("graph-editor");
  if (!root) return;
  const projectId = root.dataset.projectId;
  const fields = document.getElementById("graph-editor-fields");
  const status = document.getElementById("graph-editor-status");
  const save = document.getElementById("graph-save");
  const canvas = document.getElementById("graph-canvas");
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
    renderCanvas();
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
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Удалить блок";
      remove.disabled = project.scenario.nodes.length <= 1;
      remove.addEventListener("click", () => {
        if (node.id === project.scenario.start) {
          status.textContent = "Начальный блок нельзя удалить. Сначала выберите другой старт.";
          return;
        }
        const incoming = project.scenario.nodes.some(other => other.id !== node.id &&
          (other.next === node.id || other.true_target === node.id ||
            other.false_target === node.id ||
            (other.options || []).some(option => option.target === node.id)));
        if (incoming) {
          status.textContent = "Сначала перенаправьте входящие связи блока " + node.id;
          return;
        }
        project.scenario.nodes = project.scenario.nodes.filter(item => item.id !== node.id);
        delete project.positions[node.id];
        project.groups = (project.groups || []).map(group => ({...group,
          node_ids: group.node_ids.filter(id => id !== node.id)}))
          .filter(group => group.node_ids.length);
        render();
      });
      panel.append(remove);
      fields.append(panel);
    }
  };

  const edgesFor = node => [
    node.next,
    node.true_target,
    node.false_target,
    ...(node.options || []).map(option => option.target)
  ].filter(Boolean);

  const renderCanvas = () => {
    if (!canvas) return;
    canvas.replaceChildren();
    const nodes = project.scenario.nodes;
    const positions = project.positions;
    nodes.forEach((node, index) => {
      if (!positions[node.id]) {
        positions[node.id] = {x: 30 + (index % 3) * 255,
          y: 35 + Math.floor(index / 3) * 160};
      }
    });
    const height = Math.max(440, ...Object.values(positions).map(p => p.y + 130));
    const width = Math.max(840, ...Object.values(positions).map(p => p.x + 230));
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", width);
    svg.setAttribute("height", height);
    svg.setAttribute("viewBox", "0 0 " + width + " " + height);
    for (const node of nodes) {
      for (const target of edgesFor(node)) {
        if (!positions[target]) continue;
        const from = positions[node.id];
        const to = positions[target];
        const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const x1 = from.x + 190;
        const y1 = from.y + 45;
        const x2 = to.x;
        const y2 = to.y + 45;
        line.setAttribute("d", "M" + x1 + "," + y1 + " C" +
          (x1 + 55) + "," + y1 + " " + (x2 - 55) + "," + y2 +
          " " + x2 + "," + y2);
        line.setAttribute("stroke", "#bca9ff");
        line.setAttribute("stroke-width", "2");
        line.setAttribute("fill", "none");
        svg.append(line);
      }
    }
    canvas.append(svg);
    for (const node of nodes) {
      const tile = document.createElement("div");
      tile.className = "graph-node";
      tile.tabIndex = 0;
      tile.setAttribute("role", "group");
      tile.setAttribute("aria-label", node.id + ": " + node.kind);
      tile.style.left = positions[node.id].x + "px";
      tile.style.top = positions[node.id].y + "px";
      const heading = document.createElement("strong");
      heading.textContent = node.id;
      const body = document.createElement("p");
      body.textContent = node.text || node.kind;
      body.style.cssText = "font-size:12px;overflow:hidden;max-height:55px";
      tile.append(heading, body);
      tile.addEventListener("pointerdown", event => {
        if (event.button !== 0) return;
        const initialX = event.clientX;
        const initialY = event.clientY;
        const origin = {...positions[node.id]};
        tile.setPointerCapture(event.pointerId);
        const move = e => {
          positions[node.id] = {
            x: Math.max(0, Math.min(2200, origin.x + e.clientX - initialX)),
            y: Math.max(0, Math.min(8000, origin.y + e.clientY - initialY))
          };
          tile.style.left = positions[node.id].x + "px";
          tile.style.top = positions[node.id].y + "px";
        };
        const finish = () => {
          tile.removeEventListener("pointermove", move);
          tile.removeEventListener("pointerup", finish);
          tile.removeEventListener("pointercancel", finish);
          renderCanvas();
        };
        tile.addEventListener("pointermove", move);
        tile.addEventListener("pointerup", finish);
        tile.addEventListener("pointercancel", finish);
      });
      canvas.append(tile);
    }
    canvas.style.minWidth = width + "px";
    canvas.style.minHeight = height + "px";
  };

  const addNode = kind => {
    if (!project || project.scenario.nodes.length >= 80) return;
    let number = 1;
    const existing = new Set(project.scenario.nodes.map(node => node.id));
    while (existing.has("node" + number)) number += 1;
    const id = "node" + number;
    project.scenario.nodes.push(kind === "end"
      ? {id, kind: "end"}
      : {id, kind: "message", text: "Новое сообщение", next: null});
    render();
    status.textContent = "Блок добавлен. Соедините его переходом и сохраните.";
  };
  document.getElementById("graph-add-message")?.addEventListener(
    "click", () => addNode("message"));
  document.getElementById("graph-add-end")?.addEventListener(
    "click", () => addNode("end"));

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
