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
        if (project.positions && project.positions[old]) {
          project.positions[value] = project.positions[old];
          delete project.positions[old];
        }
      }));
      if ("text" in node) panel.append(field("Текст", node.text,
        value => { node.text = value; }, true));
      if (node.kind !== "end" && node.kind !== "choice" &&
          node.kind !== "condition") {
        panel.append(field("Следующий блок", node.next,
          value => { node.next = value || null; }));
      }
      if ("variable" in node) panel.append(field("Переменная", node.variable,
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
    const positions = project.positions || (project.positions = {});
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
          markDirty();
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
    markDirty();
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
    markDirty();
    status.textContent = "Блок добавлен. Настройте переходы и сохраните.";
  };
  const connectNodes = (fromId, toId) => {
    const source = project.scenario.nodes.find(node => node.id === fromId);
    if (!source || source.kind === "end") {
      status.textContent = "Завершающий блок не имеет исходящих связей.";
      return;
    }
    markDirty();
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
      const help = document.createElement("p");
      help.textContent = "Каждая кнопка ведёт к конкретному блоку. " +
        "Изменения сохраняются только после нажатия «Сохранить изменения».";
      inspector.append(help);
      for (const [index, option] of node.options.entries()) {
        const row = document.createElement("div");
        row.className = "graph-choice-option";
        const label = field("Кнопка " + (index + 1), option.label, value => {
          option.label = value;
          markDirty();
        });
        const destination = document.createElement("label");
        destination.textContent = "Переход к блоку";
        const select = document.createElement("select");
        select.setAttribute("aria-label", "Переход кнопки " + (index + 1));
        for (const target of project.scenario.nodes) {
          const item = document.createElement("option");
          item.value = target.id;
          item.textContent = target.id + " · " + target.kind;
          select.append(item);
        }
        select.value = option.target;
        select.addEventListener("change", () => {
          option.target = select.value;
          renderCanvas();
          markDirty();
        });
        destination.append(select);
        row.append(label, destination);
        if (node.options.length > 1) {
          row.append(makeButton("Удалить кнопку " + (index + 1), () => {
            node.options.splice(index, 1);
            renderWorkbench();
            renderCanvas();
            markDirty();
          }));
        }
        inspector.append(row);
      }
      const addOption = makeButton("+ Кнопка", () => {
        if (node.options.length >= 8) return;
        node.options.push({label: "Вариант " + (node.options.length + 1),
          target: project.scenario.start});
        renderWorkbench();
        renderCanvas();
        markDirty();
      });
      addOption.disabled = node.options.length >= 8;
      inspector.append(addOption);
    }
    inspector.append(makeButton("Соединить с другим блоком", () => {
      connectingFrom = node.id;
      status.textContent = "Нажмите на целевой блок на холсте.";
    }));
    inspector.append(makeButton("Сделать начальным", () => {
      project.scenario.start = node.id;
      render();
      markDirty();
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
  // Every interaction replays deterministically from the beginning with all
  // prior choices and inputs. The server never executes external integrations.
  const debugSession = {choices: {}, inputs: {}, scenario: null};
  const resetDebug = () => {
    debugSession.choices = {};
    debugSession.inputs = {};
    debugSession.scenario = JSON.parse(JSON.stringify(project.scenario));
    return advanceDebug();
  };
  const advanceDebug = async () => {
    simulation.textContent = "Проверяем сценарий…";
    const response = await fetch("/api/v1/builder/simple/simulate", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        scenario: debugSession.scenario,
        choices: debugSession.choices,
        inputs: debugSession.inputs
      })
    });
    const result = await response.json();
    simulation.replaceChildren();
    if (!response.ok) {
      simulation.textContent = "Ошибка сценария: " +
        JSON.stringify(result.detail || result);
      return;
    }
    const title = document.createElement("h3");
    title.textContent = "Отладка · " + result.status + " · " + result.steps + " шагов";
    simulation.append(title);
    const trace = document.createElement("ol");
    for (const step of result.trace || []) {
      const item = document.createElement("li");
      const before = JSON.stringify(step.variables_before || {});
      const after = JSON.stringify(step.variables_after || {});
      item.textContent = step.id + " · " + step.kind +
        " → " + (step.next || "стоп") + " | " + before + " → " + after;
      trace.append(item);
    }
    simulation.append(trace);
    if (result.status === "awaiting_choice") {
      for (const option of result.options || []) {
        simulation.append(makeButton(option.label, () => {
          debugSession.choices[result.at] = option.index;
          advanceDebug().catch(error => { simulation.textContent = error.message; });
        }));
      }
    } else if (result.status === "awaiting_input") {
      const answer = document.createElement("input");
      answer.placeholder = "Введите ответ";
      answer.maxLength = 300;
      simulation.append(answer, makeButton("Отправить", () => {
        debugSession.inputs[result.at] = answer.value;
        advanceDebug().catch(error => { simulation.textContent = error.message; });
      }));
    }
    simulation.append(makeButton("Начать заново", () => {
      resetDebug().catch(error => { simulation.textContent = error.message; });
    }));
  };
  const exportProject = async () => {
    if (!project) return;
    status.textContent = "Проверяем и формируем Python ZIP…";
    const response = await fetch("/api/v1/builder/simple/export", {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(project.scenario)
    });
    if (!response.ok) {
      const details = await response.json().catch(() => ({}));
      status.textContent = "Экспорт отклонён: " +
        JSON.stringify(details.detail || details);
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "omnifactory-telegram-bot.zip";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = "ZIP сформирован из текущей схемы. Telegram-бот не запущен.";
  };
  palette.before(makeButton("Проверить схему", () => {
    runAnalysis().catch(error => { validation.textContent = error.message; });
  }));
  palette.before(makeButton("Тестовый запуск", () => {
    resetDebug().catch(error => { simulation.textContent = error.message; });
  }));

  palette.before(makeButton("Экспорт Python / aiogram ZIP", () => {
    exportProject().catch(error => { status.textContent = error.message; });
  }));

  const lifecycle = document.getElementById("graph-lifecycle");
  let dirty = false;
  const markDirty = () => {
    dirty = true;
    if (status) status.textContent = "Есть несохранённые изменения.";
  };
  root.addEventListener("input", markDirty);
  root.addEventListener("change", markDirty);
  const csrfHeaders = async () => {
    const response = await fetch("/api/v1/builder/projects/csrf", {
      credentials: "same-origin", cache: "no-store"
    });
    if (!response.ok) throw new Error("Сессия истекла. Войдите повторно.");
    const data = await response.json();
    return {"X-Omni-CSRF": data.csrf_token};
  };
  const projectAction = async (suffix, method) => {
    const response = await fetch("/api/v1/builder/projects/" +
      encodeURIComponent(projectId) + suffix, {
      method, credentials: "same-origin", headers: await csrfHeaders()
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(JSON.stringify(body.detail || "Ошибка " + response.status));
    }
    return method === "DELETE" ? null : response.json();
  };
  const lifecycleButton = (label, action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.style.cssText = "padding:10px 14px;margin:5px;border:1px solid #7184b0;" +
      "border-radius:9px;background:#243552;color:#fff;cursor:pointer";
    button.addEventListener("click", () => {
      Promise.resolve().then(action).catch(error => {
        status.textContent = error.message || "Не удалось выполнить действие";
      });
    });
    lifecycle.append(button);
  };
  if (lifecycle) {
    const heading = document.createElement("h3");
    heading.textContent = "Управление сохранённым проектом";
    lifecycle.append(heading);
    lifecycleButton("Создать независимую копию", async () => {
      if (dirty && !confirm("Копия будет создана из последней сохранённой версии. Продолжить?")) return;
      const copy = await projectAction("/duplicate", "POST");
      window.location.assign("/account/graph-project/" + encodeURIComponent(copy.id));
    });
    lifecycleButton("Проверить сохранённую версию", async () => {
      const response = await fetch("/api/v1/builder/projects/" +
        encodeURIComponent(projectId) + "/diagnostics", {
        credentials: "same-origin", cache: "no-store"
      });
      if (!response.ok) throw new Error("Не удалось проверить сохранённый граф");
      const report = await response.json();
      validation.replaceChildren();
      const heading = document.createElement("h3");
      heading.textContent = report.ok ? "Сохранённый граф проверен" : "Есть ошибки";
      validation.append(heading);
      for (const issue of report.issues || []) {
        const line = document.createElement("p");
        line.textContent = issue.node_id + " · " + issue.message;
        validation.append(line);
      }
    });
    lifecycleButton("Экспортировать сохранённую версию", async () => {
      if (dirty && !confirm("Экспортируется последняя сохранённая версия. Продолжить?")) return;
      const response = await fetch("/api/v1/builder/projects/" +
        encodeURIComponent(projectId) + "/export", {
        credentials: "same-origin", cache: "no-store"
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(JSON.stringify(body.detail || "Экспорт отклонён"));
      }
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = "omnifactory-saved-telegram-bot.zip";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = "Сохранённый проект экспортирован.";
    });
    lifecycleButton("Удалить проект", async () => {
      if (!confirm("Безвозвратно удалить сохранённый проект?")) return;
      await projectAction("", "DELETE");
      window.location.assign("/account");
    });
  }
  window.addEventListener("beforeunload", event => {
    if (!dirty) return;
    event.preventDefault();
    event.returnValue = "";
  });

  const deployment = document.getElementById("graph-deployment");
  if (deployment) {
    const heading = document.createElement("h3");
    heading.textContent = "Deployment Center · Telegram";
    const notice = document.createElement("p");
    notice.textContent = "Подготовка к публикации: реальный запуск в облаке пока отключён. " +
      "Токены Telegram и платёжные данные здесь не запрашиваются.";
    const state = document.createElement("div");
    state.setAttribute("role", "status");
    const form = document.createElement("form");
    const name = document.createElement("input");
    name.placeholder = "Имя сервиса: my-telegram-bot";
    name.required = true;
    name.pattern = "[a-z][a-z0-9-]{2,38}";
    name.maxLength = 40;
    name.style.cssText = "padding:12px;margin:6px;background:#111b2e;color:white";
    const budget = document.createElement("input");
    budget.type = "number";
    budget.min = "5";
    budget.max = "10000";
    budget.value = "10";
    budget.required = true;
    budget.setAttribute("aria-label", "Месячный лимит USD");
    budget.style.cssText = name.style.cssText;
    const mode = document.createElement("select");
    mode.setAttribute("aria-label", "Режим размещения");
    for (const [value, label] of [
      ["managed", "Управляемое размещение (план)"],
      ["byoc", "Свой Railway (план)"]
    ]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      mode.append(option);
    }
    const transport = document.createElement("select");
    transport.setAttribute("aria-label", "Транспорт Telegram");
    for (const value of ["worker", "webhook"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      transport.append(option);
    }
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.textContent = "Сохранить план публикации";
    form.append(name, budget, mode, transport, submit);
    const refreshReadiness = async () => {
      const response = await fetch("/api/v1/builder/projects/" +
        encodeURIComponent(projectId) + "/deployment-readiness", {
        credentials: "same-origin", cache: "no-store"
      });
      if (!response.ok) throw new Error("Не удалось загрузить готовность проекта");
      const data = await response.json();
      state.replaceChildren();
      const line = document.createElement("p");
      line.textContent = data.scenario_valid
        ? "Сохранённая схема проходит проверку."
        : "Сохранённая схема требует исправлений.";
      state.append(line);
      for (const issue of data.diagnostics.issues || []) {
        const item = document.createElement("p");
        item.textContent = issue.severity + " · " + issue.node_id + ": " + issue.message;
        state.append(item);
      }
      const plans = document.createElement("ul");
      for (const plan of data.saved_plans) {
        const item = document.createElement("li");
        item.textContent = plan.name + " · " + plan.status + " · " + plan.id;
        plans.append(item);
      }
      state.append(plans);
      submit.disabled = !data.scenario_valid;
    };
    form.addEventListener("submit", async event => {
      event.preventDefault();
      if (dirty && !confirm("План строится по сохранённой версии графа. Продолжить?")) return;
      submit.disabled = true;
      state.textContent = "Создаём план…";
      try {
        const response = await fetch("/api/v1/builder/projects/" +
          encodeURIComponent(projectId) + "/deployment-plan", {
          method: "POST", credentials: "same-origin",
          headers: {"Content-Type": "application/json", ...await csrfHeaders()},
          body: JSON.stringify({
            name: name.value, max_monthly_usd: Number(budget.value),
            mode: mode.value, transport: transport.value
          })
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(JSON.stringify(error.detail || "Не удалось создать план"));
        }
        const result = await response.json();
        await refreshReadiness();
        status.textContent = "План " + result.id +
          " сохранён. Это не запуск Telegram-бота и не разрешение на списания.";
      } catch (error) {
        state.textContent = error.message;
      } finally {
        if (!submit.disabled) return;
        await refreshReadiness().catch(() => {});
      }
    });
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.textContent = "Обновить готовность";
    refresh.addEventListener("click", () => {
      refreshReadiness().catch(error => { state.textContent = error.message; });
    });
    deployment.append(heading, notice, form, refresh, state);
    refreshReadiness().catch(error => { state.textContent = error.message; });
  }

  const releaseConsole = document.getElementById("graph-release");
  if (releaseConsole) {
    const heading = document.createElement("h3");
    heading.textContent = "Release Gate · проверка перед публикацией";
    const explanation = document.createElement("p");
    explanation.textContent = "Здесь проверяется сохранённый граф, Railway, " +
      "Telegram и неизменяемый релиз. Запрос проверки не запускает бота и не разрешает списания.";
    const content = document.createElement("div");
    const reviewStatus = document.createElement("div");
    reviewStatus.setAttribute("role", "status");
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.textContent = "Проверить готовность релиза";
    const fetchJson = async path => {
      const response = await fetch(path, {
        credentials: "same-origin", cache: "no-store"
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(JSON.stringify(data.detail || response.status));
      return data;
    };
    const addLine = (parent, label, value) => {
      const p = document.createElement("p");
      p.textContent = label + ": " + value;
      parent.append(p);
    };
    const refreshRelease = async () => {
      content.textContent = "Проверяем сохранённый проект…";
      const base = "/api/v1/builder/projects/" + encodeURIComponent(projectId);
      const [readiness, runtime, railway] = await Promise.all([
        fetchJson(base + "/deployment-readiness"),
        fetchJson("/api/v1/cloud/runtime/preflight/" + encodeURIComponent(projectId)),
        fetchJson("/api/v1/cloud/railway/status")
      ]);
      content.replaceChildren();
      addLine(content, "Граф", readiness.scenario_valid ? "проверен" : "есть ошибки");
      addLine(content, "Telegram runtime",
        runtime.scenario_compatible ? "совместим" : runtime.issue || "несовместим");
      addLine(content, "Railway OAuth", railway.connected ? "подключён" : "не подключён");
      addLine(content, "Реальная публикация", "отключена до прохождения release gate");
      const plans = readiness.saved_plans || [];
      if (!plans.length) {
        addLine(content, "Планы", "Сначала создайте план в Deployment Center");
        return;
      }
      for (const plan of plans) {
        const panel = document.createElement("section");
        panel.style.cssText = "border:1px solid #50617d;padding:12px;margin:10px 0";
        addLine(panel, "План", plan.name + " · " + plan.status);
        const check = document.createElement("button");
        check.type = "button";
        check.textContent = "Проверить условия релиза";
        check.addEventListener("click", async () => {
          try {
            const result = await fetchJson("/api/v1/cloud/releases/preflight/" +
              encodeURIComponent(projectId) + "/" + encodeURIComponent(plan.id));
            reviewStatus.replaceChildren();
            addLine(reviewStatus, "Готовность", result.ready_for_review
              ? "можно запросить проверку" : "есть блокирующие условия");
            for (const [key, value] of Object.entries(result)) {
              if (key === "ready_for_review" || typeof value === "object") continue;
              addLine(reviewStatus, key, String(value));
            }
            if (result.ready_for_review) {
              const request = document.createElement("button");
              request.type = "button";
              request.textContent = "Запросить проверку релиза (без публикации)";
              request.addEventListener("click", async () => {
                request.disabled = true;
                try {
                  const response = await fetch("/api/v1/cloud/releases/reviews", {
                    method: "POST", credentials: "same-origin",
                    headers: {"Content-Type": "application/json",
                      "Idempotency-Key": "graph-" + projectId + "-" + plan.id,
                      ...await csrfHeaders()},
                    body: JSON.stringify({
                      bot_project_id: projectId, cloud_plan_id: plan.id,
                      confirmation: "REQUEST RELEASE REVIEW"
                    })
                  });
                  const data = await response.json().catch(() => ({}));
                  if (!response.ok) throw new Error(JSON.stringify(data.detail || response.status));
                  reviewStatus.textContent = "Запрос проверки создан: " + data.id +
                    ". Это не публикация и не разрешение расходов.";
                } catch (error) {
                  reviewStatus.textContent = error.message;
                  request.disabled = false;
                }
              });
              reviewStatus.append(request);
            }
          } catch (error) {
            reviewStatus.textContent = error.message;
          }
        });
        panel.append(check);
        content.append(panel);
      }
    };
    refresh.addEventListener("click", () => {
      refreshRelease().catch(error => { content.textContent = error.message; });
    });
    releaseConsole.append(heading, explanation, refresh, content, reviewStatus);
    refreshRelease().catch(error => { content.textContent = error.message; });
  }

  const operationsPanel = document.getElementById("graph-operations");
  if (operationsPanel) {
    const heading = document.createElement("h3");
    heading.textContent = "Operations Center · история публикаций и проверок";
    const summary = document.createElement("p");
    summary.textContent = "Фактические записи из базы. Dry-run и review не означают, что бот работает.";
    const output = document.createElement("div");
    output.setAttribute("role", "status");
    const refresh = document.createElement("button");
    refresh.type = "button";
    refresh.textContent = "Обновить историю операций";
    const line = (parent, value) => {
      const p = document.createElement("p");
      p.textContent = value;
      parent.append(p);
    };
    const update = async () => {
      output.textContent = "Загружаем события…";
      const response = await fetch("/api/v1/builder/operations/" +
        encodeURIComponent(projectId), {
        credentials: "same-origin", cache: "no-store"
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(JSON.stringify(data.detail || response.status));
      output.replaceChildren();
      line(output, "Версия сценария: " + data.revision_sha256.slice(0, 16));
      line(output, "Онлайн-статус: не подтверждён (live provisioning отключён)");
      if (!data.plans.length) line(output, "Пока нет планов публикации.");
      for (const plan of data.plans) {
        const section = document.createElement("section");
        section.style.cssText = "border:1px solid #526581;border-radius:12px;" +
          "padding:14px;margin:12px 0";
        const title = document.createElement("h4");
        title.textContent = plan.name + " · " + plan.status;
        section.append(title);
        line(section, "План создан: " + plan.created_at);
        for (const review of plan.reviews) {
          line(section, "Ревизия " + review.id.slice(0, 8) +
            " · " + review.status + (review.revision_matches
              ? " · соответствует графу" : " · граф изменён") +
            (review.cancelled ? " · отменено" : ""));
        }
        for (const job of plan.jobs) {
          const details = document.createElement("details");
          const label = document.createElement("summary");
          label.textContent = "Задача " + job.id.slice(0, 8) +
            " · " + job.mode + " · " + job.status;
          details.append(label);
          if (job.error_code) line(details, "Ошибка: " + job.error_code);
          for (const event of job.events) {
            line(details, event.created_at + " · " + event.code + " · " + event.message);
          }
          section.append(details);
        }
        output.append(section);
      }
    };
    refresh.addEventListener("click", () => {
      update().catch(error => { output.textContent = error.message; });
    });
    operationsPanel.append(heading, summary, refresh, output);
    update().catch(error => { output.textContent = error.message; });
  }

  const fleetPanel = document.getElementById("graph-fleet");
  if (fleetPanel) {
    const heading = document.createElement("h3");
    heading.textContent = "Railway Fleet · подключённые сервисы";
    const description = document.createElement("p");
    description.textContent = "Просмотр состояния Railway. Статус деплоя не доказывает, что Telegram-бот отвечает.";
    const output = document.createElement("div");
    output.setAttribute("role", "status");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Проверить Railway сейчас";
    const add = (parent, text) => {
      const p = document.createElement("p");
      p.textContent = text;
      parent.append(p);
    };
    const refresh = async live => {
      output.textContent = live ? "Запрашиваем Railway…" : "Загружаем сохранённые данные…";
      const response = await fetch("/api/v1/cloud/fleet/services" +
        (live ? "?refresh=true" : ""), {credentials: "same-origin", cache: "no-store"});
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(JSON.stringify(data.detail || response.status));
      output.replaceChildren();
      if (!data.services.length) add(output, "Нет привязанных Railway BYOC-сервисов.");
      if (data.summary) add(output, "Всего сервисов: " + data.summary.total +
        " · требуют внимания: " + data.summary.attention);
      for (const service of data.services) {
        const panel = document.createElement("section");
        panel.style.cssText = "border:1px solid #53627b;border-radius:12px;padding:12px;margin:10px 0";
        add(panel, service.plan_name + " · " + service.plan_status);
        add(panel, "Railway: " + (service.provider_status || "нет данных") +
          (service.provider_live ? " · проверено сейчас" : " · сохранённый статус"));
        if (service.provider_error) add(panel, "Ошибка: " + service.provider_error);
        if (service.reconciliation) {
          const names = {stale: "Данные устарели", provider_failure: "Ошибка Railway",
            provider_unavailable: "Railway недоступен", deploying: "Развёртывание",
            deployed_unverified: "Развёрнут, Telegram не проверен",
            not_deployed: "Нет развёртывания", unknown: "Неизвестный статус"};
          add(panel, "Диагностика: " +
            (names[service.reconciliation.state] || service.reconciliation.state));
        }
        add(panel, "Telegram: доставка сообщений не подтверждена");
        output.append(panel);
      }
    };
    button.addEventListener("click", () => {
      refresh(true).catch(error => { output.textContent = error.message; });
    });
    fleetPanel.append(heading, description, button, output);
    refresh(false).catch(error => { output.textContent = error.message; });
  }

  const backupPanel = document.getElementById("graph-backup");
  if (backupPanel) {
    const heading = document.createElement("h3");
    heading.textContent = "Версии и резервные копии";
    const note = document.createElement("p");
    note.textContent = "Скачайте JSON-копию проекта или восстановите ранее сохранённую. " +
      "Восстановление заменяет текущую сохранённую версию, но не изменяет работающего бота.";
    const download = document.createElement("a");
    download.href = "/api/v1/builder/projects/" +
      encodeURIComponent(projectId) + "/backup";
    download.textContent = "Скачать резервную копию JSON";
    download.setAttribute("download", "omnifactory-graph-backup.json");
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json,application/json";
    input.setAttribute("aria-label", "Выберите резервную копию JSON");
    const restore = document.createElement("button");
    restore.type = "button";
    restore.textContent = "Восстановить выбранную копию";
    const feedback = document.createElement("p");
    feedback.setAttribute("role", "status");
    restore.addEventListener("click", async () => {
      if (!project || !input.files || !input.files[0]) {
        feedback.textContent = "Сначала выберите JSON-файл.";
        return;
      }
      if (input.files[0].size > 300000) {
        feedback.textContent = "Файл слишком большой.";
        return;
      }
      if (!window.confirm("Заменить текущий сохранённый сценарий резервной копией?")) return;
      restore.disabled = true;
      try {
        const raw = JSON.parse(await input.files[0].text());
        if (raw.format !== "omnifactory.graph-project.backup" ||
            raw.version !== 1 || !raw.project) {
          throw new Error("Неподдерживаемый формат резервной копии");
        }
        const csrf = await fetch("/api/v1/builder/projects/csrf",
          {credentials: "same-origin", cache: "no-store"});
        if (!csrf.ok) throw new Error("Не удалось проверить сессию");
        const {csrf_token} = await csrf.json();
        const response = await fetch("/api/v1/builder/projects/" +
          encodeURIComponent(projectId) + "/restore", {
          method: "POST", credentials: "same-origin",
          headers: {"Content-Type": "application/json",
            "X-Omni-CSRF": csrf_token, "If-Match": project.revision},
          body: JSON.stringify(raw)
        });
        if (!response.ok) {
          const error = await response.json().catch(() => ({}));
          throw new Error(response.status === 409
            ? "Версия проекта изменилась. Обновите страницу перед восстановлением."
            : JSON.stringify(error.detail || response.status));
        }
        project = await response.json();
        dirty = false;
        render();
        feedback.textContent = "Копия восстановлена. Сценарий обновлён.";
      } catch (error) {
        feedback.textContent = error.message;
      } finally {
        restore.disabled = false;
      }
    });
    backupPanel.append(heading, note, download, input, restore, feedback);
  }

  const queuePanel = document.getElementById("graph-queue-health");
  if (queuePanel) {
    const title = document.createElement("h3");
    title.textContent = "Очередь публикаций · диагностика";
    const description = document.createElement("p");
    description.textContent = "Только ваши задачи. Это очередь проверок, а не реальное развёртывание.";
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Обновить очередь";
    const result = document.createElement("div");
    result.setAttribute("role", "status");
    const update = async () => {
      result.textContent = "Проверяем очередь…";
      const response = await fetch("/api/v1/cloud/provision/queue-health", {
        credentials: "same-origin", cache: "no-store"
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(JSON.stringify(data.detail || response.status));
      result.replaceChildren();
      const labels = {queued: "Ожидают", running: "Выполняются",
        simulated: "Проверены", failed: "Ошибки", cancelled: "Отменены"};
      for (const [key, label] of Object.entries(labels)) {
        const row = document.createElement("p");
        row.textContent = label + ": " + (data.counts[key] || 0);
        result.append(row);
      }
      const stale = document.createElement("strong");
      stale.textContent = "Зависших проверок (30+ мин): " + data.abandoned_dry_runs;
      result.append(stale);
      if (data.sample_truncated) {
        const note = document.createElement("p");
        note.textContent = "Показаны данные только по последним 500 задачам.";
        result.append(note);
      }
    };
    button.addEventListener("click", () => {
      update().catch(error => { result.textContent = error.message; });
    });
    queuePanel.append(title, description, button, result);
    update().catch(error => { result.textContent = error.message; });
  }

  const load = async () => {
    const response = await fetch("/api/v1/builder/projects/" +
      encodeURIComponent(projectId), {credentials: "same-origin", cache: "no-store"});
    if (!response.ok) throw new Error("Не удалось открыть сохранённый проект");
    project = await response.json();
    project.positions ||= {};
    project.groups ||= [];
    render();
    dirty = false;
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
          headers: {"Content-Type": "application/json", "X-Omni-CSRF": csrf_token,
            "If-Match": project.revision},
          body: JSON.stringify({
            scenario: project.scenario,
            positions: project.positions,
            groups: project.groups
          })
        });
      if (!response.ok) {
        const details = await response.json().catch(() => ({}));
        throw new Error(response.status === 409
          ? "Конфликт версий: проект изменён в другой вкладке. Скачайте резервную копию и обновите страницу."
          : typeof details.detail === "string"
          ? details.detail : "Сервер отклонил изменения (" + response.status + ")");
      }
      const saved = await response.json();
      project.revision = saved.revision;
      dirty = false;
      status.textContent = "Изменения сохранены. Можно закрыть и снова открыть проект.";
    } catch (error) {
      status.textContent = error.message || "Не удалось сохранить изменения";
    } finally {
      save.disabled = false;
    }
  });
  load().catch(error => { status.textContent = error.message; save.disabled = true; });
})();
