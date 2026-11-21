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
  const element = (tag, className, content) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = String(content);
    return node;
  };
  const clear = () => {
    serial++;
    run.disabled = false;
    for (const node of [summary, issues, cases, trace]) node.replaceChildren();
    state.textContent = 'Выберите сохранённый проект и запустите проверку.';
    for (const node of document.querySelectorAll('.graph-release-focus'))
      node.classList.remove('graph-release-focus');
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
      const revision = evidence.revision.slice(0, 10);
      state.textContent = 'Проверена сохранённая ревизия ' + revision +
        ' · это симуляция, не работающий Telegram-бот.';
      summary.append(element('p', '', evidence.inventory.node_count + ' блоков · ' +
        evidence.inventory.reachable_count + ' достижимых · ' +
        matrix.coverage_percent + '% покрытия тестовыми путями'));
      summary.append(element('p', '', matrix.completed_cases + ' завершённых из ' +
        matrix.case_count + ' тестов · экспорт ' +
        (evidence.export_ready ? 'разрешён' : 'заблокирован')));
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
          'Тест ' + test.number + ' · ' + test.status + ' · ' + test.path.join(' → '));
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
  project.addEventListener('change', clear);
  run.addEventListener('click', inspect);
})();
