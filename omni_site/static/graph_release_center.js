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
  const planForm = $('release-plan-form');
  const planStatus = $('release-plan-status');
  const planHistory = $('release-plan-history');
  const planName = $('release-plan-name');
  const planBudget = $('release-plan-budget');
  let inspected = null;
  let sequence = 0;
  const reset = () => {
    sequence++;
    button.disabled = false;
    inspected = null;
    planForm.hidden = true;
    planStatus.textContent = '';
    planHistory.replaceChildren();
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
  async function loadPlans(id, ticket) {
    const response = await fetch('/api/v1/builder/operations/' +
      encodeURIComponent(id), {credentials: 'same-origin'});
    if (!response.ok) return;
    const data = await response.json();
    if (ticket !== sequence || project.value !== id) return;
    planHistory.replaceChildren();
    planHistory.append(item('h3', 'Сохранённые планы и фактические события'));
    if (!data.plans.length) planHistory.append(item('p', 'Планов пока нет.'));
    for (const plan of data.plans) {
      planHistory.append(item('p', plan.name + ' · ' + plan.status +
        ' · заданий: ' + plan.jobs.length + ' · согласований: ' + plan.reviews.length));
    }
    planHistory.append(item('p', 'Планы не подтверждают работающий Telegram-бот.'));
  }
  planForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (!inspected || !inspected.ready || project.value !== inspected.id) return;
    const current = inspected;
    const submit = $('release-plan-create');
    submit.disabled = true;
    planStatus.textContent = 'Сохраняем план…';
    try {
      const tokenResponse = await fetch('/api/v1/builder/projects/csrf',
        {credentials: 'same-origin'});
      if (!tokenResponse.ok) throw Error('CSRF HTTP ' + tokenResponse.status);
      const token = (await tokenResponse.json()).csrf_token;
      const response = await fetch('/api/v1/builder/projects/' +
        encodeURIComponent(current.id) + '/deployment-plan', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-Omni-CSRF': token},
        body: JSON.stringify({
          revision: current.revision,
          name: planName.value.trim(),
          mode: 'managed',
          transport: 'worker',
          max_monthly_usd: Number(planBudget.value)
        })
      });
      if (response.status === 409) {
        reset();
        planStatus.textContent = 'Ревизия изменилась или план уже существует. Повторите проверку.';
        return;
      }
      if (!response.ok) throw Error('HTTP ' + response.status);
      const result = await response.json();
      if (!inspected || inspected.revision !== current.revision) return;
      planStatus.textContent = result.already_exists ?
        'План уже существует: ' + result.id :
        'Dry-run план сохранён: ' + result.id;
      await loadPlans(current.id, sequence);
    } catch (error) {
      planStatus.textContent = 'Не удалось сохранить план: ' + error.message;
    } finally {
      submit.disabled = false;
    }
  });
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
      inspected = {id, revision: report.revision, ready: report.export_ready};
      planForm.hidden = !report.export_ready;
      if (report.export_ready) await loadPlans(id, ticket);
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
