/* Saved-revision release center. Never claims to deploy or verify a bot. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const project = $('cloud-project-list');
  const button = $('release-center-check');
  const status = $('release-center-status');
  const steps = $('release-center-steps');
  const summary = $('release-center-summary');
  const instructions = $('release-center-instructions');
  const download = $('release-center-download');
  if (!project || !button || !status || !steps || !summary || !instructions || !download) return;
  let sequence = 0;
  const reset = () => {
    sequence++;
    button.disabled = false;
    steps.replaceChildren();
    summary.replaceChildren();
    instructions.replaceChildren();
    download.hidden = true;
    download.removeAttribute('href');
    status.textContent = 'Выберите сохранённый проект и проверьте выпуск.';
  };
  const item = (tag, content) => {
    const node = document.createElement(tag);
    node.textContent = String(content);
    return node;
  };
  project.addEventListener('change', reset);
  button.addEventListener('click', async () => {
    reset();
    const id = project.value;
    if (!/^[0-9a-f-]{36}$/i.test(id)) {
      status.textContent = 'Сначала выберите сохранённый проект.';
      return;
    }
    const ticket = ++sequence;
    button.disabled = true;
    status.textContent = 'Проверяем сохранённую ревизию…';
    try {
      const response = await fetch('/api/v1/builder/projects/' +
        encodeURIComponent(id) + '/release-center', {credentials: 'same-origin'});
      if (!response.ok) throw Error('HTTP ' + response.status);
      const report = await response.json();
      if (ticket !== sequence || project.value !== id) return;
      status.textContent = 'Ревизия ' + report.revision.slice(0, 10) +
        ' · ' + (report.export_ready ? 'готова к экспорту' : 'требует исправлений');
      for (const step of report.steps) {
        const line = item('li', step.label + ' — ' + step.status);
        line.className = 'graph-release-center-' + step.status;
        steps.append(line);
      }
      summary.append(item('p', report.test_summary.completed + ' завершённых тестов из ' +
        report.test_summary.cases + ' · покрытие переходов ' +
        report.test_summary.edge_coverage_percent + '%'));
      for (const blocker of report.blockers) {
        summary.append(item('p', 'Ошибка в ' + blocker.node_id + ': ' + blocker.message));
      }
      if (report.test_summary.truncated)
        summary.append(item('p', 'Тестовые пути ограничены лимитом; покрытие неполное.'));
      const list = document.createElement('ol');
      for (const instruction of report.deployment_instructions)
        list.append(item('li', instruction));
      instructions.append(item('h3', 'Ручной запуск на хостинге'));
      instructions.append(list);
      const expected = '/api/v1/builder/projects/' + id + '/export';
      if (report.export_ready && report.export_url === expected) {
        download.href = expected;
        download.hidden = false;
      }
    } catch (error) {
      if (ticket === sequence) status.textContent = 'Не удалось проверить выпуск: ' + error.message;
    } finally {
      if (ticket === sequence) button.disabled = false;
    }
  });
})();
