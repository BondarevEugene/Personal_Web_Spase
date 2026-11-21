/* Graph Studio release inspector — saved-revision evidence, branch coverage, trace. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const project = $('cloud-project-list');
  const run = $('btn-release-inspect');
  const state = $('release-inspect-state');
  const summary = $('release-inspect-summary');
  const issues = $('release-inspect-issues');
  const cases = $('release-inspect-cases');
  const trace = $('release-inspect-trace');
  if (!project || !run || !state || !summary || !issues || !cases || !trace) return;
  let serial = 0;
  let inspected = null;
  let debugAnswers = {choices: {}, inputs: {}};
  const debugStart = $('release-debug-start');
  const debugStatus = $('release-debug-status');
  const debugHistory = $('release-debug-history');
  const debugInputs = $('release-debug-inputs');
  if (debugStart) debugStart.disabled = true;
  const coverage = $('release-inspect-coverage');
  const readiness = $('release-inspect-readiness');
  const edgeList = $('release-inspect-edges');
  const statusLabels = {
    completed: 'Завершён', awaiting_choice: 'Ожидает кнопку',
    awaiting_input: 'Ожидает ввод', step_limit: 'Лимит шагов',
    invalid_input: 'Неверный ввод', invalid_choice: 'Неверная кнопка'
  };
  const markNodes = (ids, className) => {
    const lookup = new Set(ids);
    for (const node of document.querySelectorAll('.graph-node')) {
      if (lookup.has(node.dataset.nodeId)) node.classList.add(className);
    }
  };
  const removeMarkers = () => {
    for (const node of document.querySelectorAll(
      '.graph-release-focus,.graph-release-blocker,.graph-release-untested,.graph-release-unreachable'
    )) node.classList.remove(
      'graph-release-focus', 'graph-release-blocker',
      'graph-release-untested', 'graph-release-unreachable'
    );
  };
  const element = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = String(content);
    return node;
  };
  const clear = () => {
    serial++;
    inspected = null;
    debugAnswers = {choices: {}, inputs: {}};
    if (debugStart) debugStart.disabled = true;
    if (debugStatus) debugStatus.textContent = 'Сначала проверьте сохранённую ревизию.';
    if (debugHistory) debugHistory.replaceChildren();
    if (debugInputs) debugInputs.replaceChildren();
    run.disabled = false;
    for (const node of [summary, issues, cases, trace, coverage, readiness, edgeList])
      if (node) node.replaceChildren();
    state.textContent = 'Выберите сохранённый проект и запустите проверку.';
    removeMarkers();
  };
  function focus(id) {
    const node = [...document.querySelectorAll('.graph-node')]
      .find(card => card.dataset.nodeId === id);
    if (!node) {
      state.textContent = 'Блок ' + id + ' не найден в открытом черновике. Откройте сохранённую ревизию.';
      return;
    }
    for (const old of document.querySelectorAll('.graph-release-focus'))
      old.classList.remove('graph-release-focus');
    node.classList.add('graph-release-focus');
    node.scrollIntoView({block:'center', inline:'center', behavior:'smooth'});
    node.click();
  }
  function renderTrace(test) {
    trace.replaceChildren();
    trace.append(element('strong', '', 'Трассировка · тест ' + test.number));
    for (const [index, step] of test.trace.entries()) {
      const button = element('button', 'graph-release-trace-step',
        (index + 1) + '. ' + step.id + ' · ' + step.kind +
        (step.next ? ' → ' + step.next : ' · стоп'));
      button.type = 'button';
      button.addEventListener('click', () => {
        focus(step.id);
        const before = JSON.stringify(step.variables_before || {}, null, 2);
        const after = JSON.stringify(step.variables_after || {}, null, 2);
        $('release-inspect-variables').textContent =
          'До:\n' + before + '\nПосле:\n' + after;
      });
      trace.append(button);
    }
    $('release-inspect-variables').textContent = 'Выберите шаг для просмотра переменных.';
  }
  async function inspect() {
    const id = project.value;
    clear();
    if (!/^[0-9a-f-]{36}$/i.test(id)) {
      state.textContent = 'Сначала выберите сохранённый проект.';
      return;
    }
    const ticket = ++serial;
    run.disabled = true;
    state.textContent = 'Проверяем сохранённую ревизию и варианты диалога…';
    try {
      const prefix = '/api/v1/builder/projects/' + encodeURIComponent(id);
      const [evidenceResponse, matrixResponse] = await Promise.all([
        fetch(prefix + '/release-evidence', {credentials:'same-origin'}),
        fetch(prefix + '/test-matrix', {credentials:'same-origin'}),
      ]);
      if (!evidenceResponse.ok || !matrixResponse.ok)
        throw Error('HTTP ' + (evidenceResponse.ok ? matrixResponse.status : evidenceResponse.status));
      const [evidence, matrix] = await Promise.all([
        evidenceResponse.json(), matrixResponse.json(),
      ]);
      if (ticket !== serial || project.value !== id) return;
      if (evidence.revision !== matrix.revision) {
        state.textContent = 'Ревизия изменилась во время проверки. Запустите повторно.';
        return;
      }
      inspected = {id, revision: evidence.revision};
      if (debugStart) debugStart.disabled = false;
      const revision = evidence.revision.slice(0, 10);
      state.textContent = 'Проверена сохранённая ревизия ' + revision +
        ' · это симуляция, не работающий Telegram-бот.';
      summary.append(element('p', '', evidence.inventory.node_count + ' блоков · ' +
        evidence.inventory.reachable_count + ' достижимых · ' +
        matrix.coverage_percent + '% покрытия тестовыми путями'));
      summary.append(element('p', '', matrix.completed_cases + ' завершённых из ' +
        matrix.case_count + ' тестов · экспорт ' +
        (evidence.export_ready ? 'разрешён' : 'заблокирован')));
      if (coverage) {
        coverage.append(element('strong', '', 'Покрытие переходов: ' +
          matrix.covered_edge_count + ' / ' + matrix.reachable_edge_count +
          ' · ' + matrix.edge_coverage_percent + '%'));
        coverage.append(element('p', '', 'Недостижимых блоков: ' +
          matrix.unreachable_nodes.length + ' · достижимых без теста: ' +
          matrix.untested_reachable_nodes.length + ' · непроверенных кнопок: ' +
          matrix.untested_choice_options.length));
      }
      if (readiness) {
        readiness.append(element('strong', '',
          evidence.export_ready ? '✓ Экспорт доступен' : '✕ Экспорт заблокирован'));
        readiness.append(element('p', '',
          evidence.blockers.length + ' блокирующих ошибок · ' +
          evidence.warnings.length + ' предупреждений'));
        readiness.append(element('p', '', 'Запуск в Telegram требует ручной настройки хостинга и BOT_TOKEN.'));
      }
      markNodes(matrix.unreachable_nodes, 'graph-release-unreachable');
      markNodes(matrix.untested_reachable_nodes, 'graph-release-untested');
      markNodes(evidence.blockers.map(item => item.node_id), 'graph-release-blocker');
      if (edgeList) {
        for (const edge of matrix.uncovered_edges) {
          const button = element('button', 'graph-release-issue',
            'Не проверен переход: ' + edge.source + ' → ' + edge.target);
          button.type = 'button';
          button.addEventListener('click', () => focus(edge.source));
          edgeList.append(button);
        }
        for (const option of matrix.untested_choice_options) {
          const button = element('button', 'graph-release-issue',
            'Не проверена кнопка ' + (option.option_index + 1) +
            ': ' + option.node_id + ' → ' + option.target);
          button.type = 'button';
          button.addEventListener('click', () => focus(option.node_id));
          edgeList.append(button);
        }
        if (!edgeList.children.length) edgeList.append(
          element('p', '', 'Все статически достижимые переходы проверены.'));
      }
      if (matrix.truncated) summary.append(element('p', 'graph-release-warning',
        'Достигнут лимит тестовых путей: ' + matrix.max_cases));
      for (const issue of [...evidence.blockers, ...evidence.warnings]) {
        const button = element('button', 'graph-release-issue ' + issue.severity,
          issue.node_id + ' · ' + issue.message);
        button.type = 'button';
        button.addEventListener('click', () => focus(issue.node_id));
        issues.append(button);
      }
      if (!issues.children.length) issues.append(element('p', '', 'Нет ошибок и предупреждений.'));
      for (const test of matrix.cases) {
        const button = element('button', 'graph-release-case',
          'Тест ' + test.number + ' · ' + (statusLabels[test.status] || test.status) + ' · ' + test.path.join(' → '));
        button.type = 'button';
        button.addEventListener('click', () => renderTrace(test));
        cases.append(button);
      }
      if (matrix.cases.length) renderTrace(matrix.cases[0]);
    } catch (error) {
      if (ticket === serial) state.textContent = 'Проверка не выполнена: ' + error.message;
    } finally {
      if (ticket === serial) run.disabled = false;
    }
  }
  async function replayDebug() {
    if (!inspected || project.value !== inspected.id) return;
    const current = inspected;
    debugInputs.replaceChildren();
    debugStatus.textContent = 'Выполняем серверную симуляцию…';
    try {
      const response = await fetch('/api/v1/builder/projects/' +
        encodeURIComponent(current.id) + '/debug-session', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({revision: current.revision, ...debugAnswers})
      });
      if (response.status === 409) {
        clear();
        debugStatus.textContent = 'Проект изменился. Проверьте сохранённую ревизию заново.';
        return;
      }
      if (!response.ok) throw Error('HTTP ' + response.status);
      const result = await response.json();
      if (!inspected || project.value !== current.id ||
          inspected.revision !== result.revision) return;
      debugHistory.replaceChildren();
      for (const [index, step] of result.trace.entries()) {
        const button = element('button', 'graph-release-trace-step',
          (index + 1) + '. ' + step.id + ' · ' + step.kind +
          (step.text ? ' · ' + step.text : ''));
        button.type = 'button';
        button.addEventListener('click', () => {
          focus(step.id);
          $('release-inspect-variables').textContent =
            'До:\\n' + JSON.stringify(step.variables_before || {}, null, 2) +
            '\\nПосле:\\n' + JSON.stringify(step.variables_after || {}, null, 2);
        });
        debugHistory.append(button);
      }
      debugStatus.textContent = 'Статус: ' + (statusLabels[result.status] || result.status) +
        ' · ' + result.steps + ' шагов.';
      if (result.status === 'awaiting_choice') {
        for (const option of result.options) {
          const button = element('button', 'graph-release-case', option.label);
          button.type = 'button';
          button.addEventListener('click', () => {
            debugAnswers.choices[result.at] = option.index;
            replayDebug();
          });
          debugInputs.append(button);
        }
      } else if (result.status === 'awaiting_input') {
        const form = document.createElement('form');
        const field = document.createElement('input');
        field.type = 'text';
        field.required = true;
        field.maxLength = 300;
        field.placeholder = 'Введите ' + result.variable;
        field.setAttribute('aria-label', 'Ответ для ' + result.variable);
        const submit = element('button', 'graph-release-case', 'Отправить ответ');
        submit.type = 'submit';
        form.append(field, submit);
        form.addEventListener('submit', event => {
          event.preventDefault();
          if (!field.value.trim()) return;
          debugAnswers.inputs[result.at] = field.value;
          replayDebug();
        });
        debugInputs.append(form);
        field.focus();
      }
    } catch (error) {
      debugStatus.textContent = 'Ошибка симуляции: ' + error.message;
    }
  }
  if (debugStart) debugStart.addEventListener('click', () => {
    debugAnswers = {choices: {}, inputs: {}};
    replayDebug();
  });
  project.addEventListener('change', clear);
  run.addEventListener('click', inspect);
})();
