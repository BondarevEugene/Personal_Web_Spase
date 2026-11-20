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
  let selectedNodeId = null;
  let connectingFrom = null;
  let zoom = 1;

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
    renderWorkbench();
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
      tile.addEventListener("click", () => {
        if (connectingFrom && connectingFrom !== node.id) {
          connectNodes(connectingFrom, node.id);
          connectingFrom = null;
          render();
          return;
        }
        selectedNodeId = node.id;
        renderWorkbench();
      });
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
    canvas.style.zoom = String(zoom);
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

  const kinds = [
    ["message", "Сообщение"], ["choice", "Кнопки выбора"],
    ["input", "Ввод данных"], ["condition", "Условие"],
    ["set_variable", "Переменная"], ["photo", "Фото"],
    ["document", "Документ"], ["end", "Завершение"]
  ];
  const palette = document.getElementById("graph-palette");
  const inspector = document.getElementById("graph-inspector");
  const validation = document.getElementById("graph-validation");
  const simulation = document.getElementById("graph-simulation");
  const makeButton = (label, action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.style.cssText = "padding:9px 13px;margin:5px;border-radius:8px;" +
      "background:#c3b3ff;color:#101526;border:0;cursor:pointer";
    button.addEventListener("click", action);
    return button;
  };
  const addKind = kind => {
    if (!project || project.scenario.nodes.length >= 80) return;
    let index = 1;
    const ids = new Set(project.scenario.nodes.map(node => node.id));
    while (ids.has("node" + index)) index++;
    const id = "node" + index;
    const defaults = {
      message: {text: "Новое сообщение"},
      choice: {text: "Выберите вариант", options: [
        {label: "Продолжить", target: project.scenario.start}]},
      input: {text: "Введите ответ", variable: "answer", next: project.scenario.start},
      condition: {variable: "answer", operator: "equals", value: "да",
        true_target: project.scenario.start, false_target: project.scenario.start},
      set_variable: {variable: "answer", value: "значение",
        next: project.scenario.start},
      photo: {media: "https://example.com/photo.jpg"},
      document: {media: "https://example.com/document.pdf"},
      end: {}
    };
    project.scenario.nodes.push({id, kind, ...defaults[kind]});
    selectedNodeId = id;
    render();
    status.textContent = "Блок добавлен. Настройте переходы и сохраните.";
  };
  const connectNodes = (fromId, toId) => {
    const source = project.scenario.nodes.find(node => node.id === fromId);
    if (!source || source.kind === "end") {
      status.textContent = "Завершающий блок не имеет исходящих связей.";
      return;
    }
    if (source.kind === "condition") {
      source.true_target = toId;
      status.textContent = "Ветка Да соединена. Ветку Нет настройте в инспекторе.";
    } else if (source.kind === "choice") {
      if (!source.options.length) source.options.push({label: "Далее", target: toId});
      else source.options[0].target = toId;
      status.textContent = "Первая кнопка соединена. Другие настройте в инспекторе.";
    } else {
      source.next = toId;
      status.textContent = "Блоки соединены. Сохраните сценарий.";
    }
  };
  const renderWorkbench = () => {
    if (!project) return;
    palette.replaceChildren();
    const heading = document.createElement("h3");
    heading.textContent = "Библиотека действий";
    palette.append(heading);
    for (const [kind, label] of kinds) {
      palette.append(makeButton("+ " + label, () => addKind(kind)));
    }
    palette.append(makeButton("− Масштаб", () => {
      zoom = Math.max(.5, +(zoom - .1).toFixed(2));
      renderCanvas();
    }));
    palette.append(makeButton("+ Масштаб", () => {
      zoom = Math.min(1.5, +(zoom + .1).toFixed(2));
      renderCanvas();
    }));
    inspector.replaceChildren();
    const node = project.scenario.nodes.find(item => item.id === selectedNodeId);
    if (!node) {
      inspector.textContent = "Нажмите на блок для настройки и соединения.";
      return;
    }
    const h = document.createElement("h3");
    h.textContent = "Инспектор · " + node.id + " (" + node.kind + ")";
    inspector.append(h);
    const edit = (label, key, multiline = false) => {
      inspector.append(field(label, node[key] ?? "", value => {
        node[key] = value || (key.endsWith("target") || key === "next" ? null : "");
        if (key === "text") renderCanvas();
      }, multiline));
    };
    if ("text" in node) edit("Текст", "text", true);
    if ("media" in node) edit("HTTPS URL / Telegram file_id", "media");
    if ("variable" in node) edit("Имя переменной", "variable");
    if ("value" in node) edit("Значение", "value");
    if ("operator" in node) {
      const select = document.createElement("select");
      for (const operator of ["equals", "not_equals", "contains", "not_empty"]) {
        const option = document.createElement("option");
        option.value = operator;
        option.textContent = operator;
        select.append(option);
      }
      select.value = node.operator;
      select.addEventListener("change", () => { node.operator = select.value; });
      inspector.append(select);
    }
    if ("true_target" in node) edit("Переход Да", "true_target");
    if ("false_target" in node) edit("Переход Нет", "false_target");
    if (node.kind !== "end" && node.kind !== "condition" && node.kind !== "choice") {
      edit("Следующий блок", "next");
    }
    if (node.kind === "choice") {
      for (const [index, option] of node.options.entries()) {
        inspector.append(field("Кнопка " + (index + 1), option.label,
          value => { option.label = value; }));
        inspector.append(field("Цель кнопки " + (index + 1), option.target,
          value => { option.target = value; }));
      }
      inspector.append(makeButton("+ Кнопка", () => {
        if (node.options.length >= 8) return;
        node.options.push({label: "Вариант", target: project.scenario.start});
        renderWorkbench();
      }));
    }
    inspector.append(makeButton("Соединить с другим блоком", () => {
      connectingFrom = node.id;
      status.textContent = "Нажмите на целевой блок на холсте.";
    }));
    inspector.append(makeButton("Сделать начальным", () => {
      project.scenario.start = node.id;
      render();
    }));
  };
  const runAnalysis = async () => {
    validation.textContent = "Проверяем граф…";
    const response = await fetch("/api/v1/builder/simple/validate", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(project.scenario)
    });
    const result = await response.json();
    validation.replaceChildren();
    if (!response.ok) {
      validation.textContent = "Ошибка проверки: " + JSON.stringify(result.detail || result);
      return;
    }
    const summary = document.createElement("p");
    summary.textContent = result.ok ? "Граф проверен" : "Обнаружены ошибки графа";
    validation.append(summary);
    for (const issue of result.issues || []) {
      const line = document.createElement("p");
      line.textContent = issue.severity + " · " + issue.node_id + ": " + issue.message;
      validation.append(line);
    }
  };
  const runSimulation = async () => {
    simulation.textContent = "Выполняется безопасная симуляция…";
    const response = await fetch("/api/v1/builder/simple/simulate", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({scenario: project.scenario, choices: {}, inputs: {}})
    });
    const result = await response.json();
    simulation.replaceChildren();
    if (!response.ok) {
      simulation.textContent = "Ошибка: " + JSON.stringify(result.detail || result);
      return;
    }
    const summary = document.createElement("p");
    summary.textContent = "Результат: " + result.status + " · шагов: " + result.steps;
    simulation.append(summary);
    for (const step of result.trace || []) {
      const row = document.createElement("p");
      row.textContent = step.id + " [" + step.kind + "] → " + (step.next || "стоп");
      simulation.append(row);
    }
    if (result.status === "awaiting_choice") {
      for (const option of result.options || []) {
        simulation.append(makeButton(option.label, async () => {
          await simulateWith({[result.at]: option.index}, {});
        }));
      }
    }
    if (result.status === "awaiting_input") {
      const answer = document.createElement("input");
      answer.placeholder = "Введите ответ";
      simulation.append(answer, makeButton("Продолжить", async () => {
        await simulateWith({}, {[result.at]: answer.value});
      }));
    }
  };
  const simulateWith = async (choices, inputs) => {
    const response = await fetch("/api/v1/builder/simple/simulate", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({scenario: project.scenario, choices, inputs})
    });
    const result = await response.json();
    simulation.replaceChildren();
    const summary = document.createElement("p");
    summary.textContent = "Результат: " + result.status + " · шагов: " + result.steps;
    simulation.append(summary);
    for (const step of result.trace || []) {
      const row = document.createElement("p");
      row.textContent = step.id + " → " + (step.next || "стоп");
      simulation.append(row);
    }
  };
  palette.before(makeButton("Проверить схему", () => {
    runAnalysis().catch(error => { validation.textContent = error.message; });
  }));
  palette.before(makeButton("Тестовый запуск", () => {
    runSimulation().catch(error => { simulation.textContent = error.message; });
  }));

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
