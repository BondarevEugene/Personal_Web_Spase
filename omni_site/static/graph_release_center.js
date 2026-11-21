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
  const planMode = $('release-plan-mode');
  const runtimePlan = $('release-runtime-plan');
  const runtimeRun = $('release-runtime-run');
  const runtimeRefresh = $('release-runtime-refresh');
  const runtimeStatus = $('release-runtime-status');
  const runtimeJobs = $('release-runtime-jobs');
  const gateCheck = $('release-gate-check');
  const gateStatus = $('release-gate-status');
  const gateChecks = $('release-gate-checks');
  const gateRequest = $('release-gate-request');
  const gateReviewStatus = $('release-gate-review-status');
  const fleetRefresh = $('release-fleet-refresh');
  const fleetStatus = $('release-fleet-status');
  const fleetServices = $('release-fleet-services');
  let releaseGate = null;
  let inspected = null;
  let sequence = 0;
  const reset = () => {
    sequence++;
    button.disabled = false;
    inspected = null;
    planForm.hidden = true;
    planStatus.textContent = '';
    planHistory.replaceChildren();
    runtimePlan.replaceChildren();
    runtimePlan.append(item('option', 'Сначала проверьте проект'));
    runtimePlan.value = '';
    runtimeRun.disabled = true;
    runtimeJobs.replaceChildren();
    runtimeStatus.textContent = '';
    releaseGate = null;
    gateCheck.disabled = true;
    gateRequest.disabled = true;
    gateStatus.textContent = '';
    gateReviewStatus.textContent = '';
    gateChecks.replaceChildren();
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
    runtimePlan.replaceChildren();
    const placeholder = item('option', 'Выберите план');
    placeholder.value = '';
    runtimePlan.append(placeholder);
    for (const plan of data.plans) {
      const option = item('option', plan.name + ' · ' + plan.status);
      option.value = plan.id;
      if (plan.status === 'planned') runtimePlan.append(option);
      planHistory.append(item('p', plan.name + ' · ' + plan.status +
        ' · заданий: ' + plan.jobs.length + ' · согласований: ' + plan.reviews.length));
    }
    runtimeRun.disabled = !runtimePlan.value;
    gateCheck.disabled = !runtimePlan.value;
    releaseGate = null;
    gateRequest.disabled = true;
    gateChecks.replaceChildren();
    planHistory.append(item('p', 'Планы не подтверждают работающий Telegram-бот.'));
    await loadJobs(id, ticket);
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
          mode: planMode.value,
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
  runtimePlan.addEventListener('change', () => {
    runtimeRun.disabled = !runtimePlan.value || !inspected || !inspected.ready;
  });
  async function loadJobs(id, ticket) {
    const response = await fetch('/api/v1/cloud/provision/jobs',
      {credentials: 'same-origin'});
    if (!response.ok) return;
    const data = await response.json();
    if (ticket !== sequence || project.value !== id) return;
    const allowed = new Set([...runtimePlan.options].map(option => option.value));
    runtimeJobs.replaceChildren();
    const related = data.jobs.filter(job => allowed.has(job.plan_id));
    if (!related.length) runtimeJobs.append(item('p', 'Заданий для доступных планов нет.'));
    for (const job of related) {
      const panel = document.createElement('div');
      panel.className = 'graph-release-runtime-job';
      panel.append(item('p', 'Задание ' + job.id + ' · ' + job.status +
        ' · режим: ' + job.mode));
      const details = item('button', 'События');
      details.type = 'button';
      details.addEventListener('click', async () => {
        const response = await fetch('/api/v1/cloud/provision/jobs/' +
          encodeURIComponent(job.id), {credentials: 'same-origin'});
        if (!response.ok) return;
        const full = await response.json();
        const log = document.createElement('ol');
        for (const event of full.events)
          log.append(item('li', event.code + ' · ' + event.message));
        panel.querySelectorAll('ol').forEach(node => node.remove());
        panel.append(log);
      });
      panel.append(details);
      if (job.status === 'queued') {
        const cancel = item('button', 'Отменить задание');
        cancel.type = 'button';
        cancel.addEventListener('click', async () => {
          if (!window.confirm('Отменить ожидающую dry-run проверку?')) return;
          const tokenResponse = await fetch('/api/v1/builder/projects/csrf',
            {credentials: 'same-origin'});
          if (!tokenResponse.ok) return;
          const token = (await tokenResponse.json()).csrf_token;
          const response = await fetch('/api/v1/cloud/provision/jobs/' +
            encodeURIComponent(job.id) + '/cancel', {
            method: 'POST', credentials: 'same-origin',
            headers: {'X-Omni-CSRF': token}
          });
          if (response.ok) await loadJobs(id, sequence);
          else runtimeStatus.textContent = 'Отмена не выполнена: HTTP ' + response.status;
        });
        panel.append(cancel);
      }
      runtimeJobs.append(panel);
    }
  }
  runtimeRefresh.addEventListener('click', () => {
    if (inspected && project.value === inspected.id)
      loadPlans(inspected.id, sequence);
  });
  runtimeRun.addEventListener('click', async () => {
    if (!inspected || !inspected.ready || !runtimePlan.value) return;
    if (!window.confirm('Создать dry-run задание? Ресурсы Railway НЕ создаются.')) return;
    const current = inspected;
    const planId = runtimePlan.value;
    runtimeRun.disabled = true;
    runtimeStatus.textContent = 'Отправляем задание в очередь…';
    try {
      const csrfResponse = await fetch('/api/v1/builder/projects/csrf',
        {credentials: 'same-origin'});
      if (!csrfResponse.ok) throw Error('CSRF HTTP ' + csrfResponse.status);
      const csrf = (await csrfResponse.json()).csrf_token;
      const key = 'graph-' + planId.replace(/-/g, '') + '-' +
        Date.now().toString(36);
      const response = await fetch('/api/v1/cloud/provision/jobs', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-Omni-CSRF': csrf,
          'Idempotency-Key': key},
        body: JSON.stringify({plan_id: planId, confirmation: 'SIMULATE DEPLOYMENT'})
      });
      if (!response.ok) throw Error('HTTP ' + response.status);
      const result = await response.json();
      if (inspected && inspected.id === current.id) {
        runtimeStatus.textContent = 'Задание ' + result.id +
          ' добавлено в очередь. Выполнение требует отдельного worker.';
        await loadJobs(current.id, sequence);
      }
    } catch (error) {
      runtimeStatus.textContent = 'Ошибка очереди: ' + error.message;
    } finally {
      runtimeRun.disabled = !runtimePlan.value;
    }
  });
  runtimePlan.addEventListener('change', () => {
    releaseGate = null;
    gateRequest.disabled = true;
    gateCheck.disabled = !runtimePlan.value || !inspected || !inspected.ready;
    gateChecks.replaceChildren();
    gateStatus.textContent = 'Для нового плана выполните проверку допуска.';
  });
  gateCheck.addEventListener('click', async () => {
    if (!inspected || !inspected.ready || !runtimePlan.value) return;
    const current = inspected;
    const planId = runtimePlan.value;
    gateCheck.disabled = true;
    gateRequest.disabled = true;
    releaseGate = null;
    gateChecks.replaceChildren();
    gateStatus.textContent = 'Проверяем защищённый релизный контур…';
    try {
      const url = '/api/v1/cloud/releases/preflight/' +
        encodeURIComponent(current.id) + '/' + encodeURIComponent(planId);
      const response = await fetch(url, {credentials: 'same-origin'});
      if (!response.ok) throw Error('HTTP ' + response.status);
      const result = await response.json();
      if (!inspected || inspected.revision !== current.revision ||
          runtimePlan.value !== planId) return;
      for (const check of result.checks || [])
        gateChecks.append(item('li', (check.ok ? '✓ ' : '✕ ') +
          check.message));
      gateChecks.append(item('li', 'Подтверждённый образ: ' +
        (result.approved_image ? 'задан оператором' : 'не задан')));
      gateChecks.append(item('li', 'Платный запуск: ' +
        (result.ready_for_paid_deployment ? 'допущен' : 'заблокирован')));
      gateStatus.textContent = result.ready_for_review ?
        'Предварительная проверка пройдена. Можно запросить согласование.' :
        'Публикация заблокирована: устраните замечания.';
      if (result.ready_for_review) {
        releaseGate = {projectId: current.id, planId, revision: current.revision};
        gateRequest.disabled = false;
      }
    } catch (error) {
      gateStatus.textContent = 'Проверка допуска недоступна: ' + error.message;
    } finally {
      gateCheck.disabled = !runtimePlan.value;
    }
  });
  gateRequest.addEventListener('click', async () => {
    if (!releaseGate || !inspected || releaseGate.revision !== inspected.revision ||
        releaseGate.planId !== runtimePlan.value) return;
    if (!window.confirm('Запросить согласование релиза? Это НЕ запускает Railway и не подтверждает расходы.')) return;
    const current = releaseGate;
    gateRequest.disabled = true;
    gateReviewStatus.textContent = 'Регистрируем запрос согласования…';
    try {
      const csrfResponse = await fetch('/api/v1/builder/projects/csrf',
        {credentials: 'same-origin'});
      if (!csrfResponse.ok) throw Error('CSRF HTTP ' + csrfResponse.status);
      const token = (await csrfResponse.json()).csrf_token;
      const response = await fetch('/api/v1/cloud/releases/reviews', {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json', 'X-Omni-CSRF': token,
          'Idempotency-Key': 'graph-review-' + current.planId.replace(/-/g, '') +
            '-' + Date.now().toString(36)},
        body: JSON.stringify({bot_project_id: current.projectId,
          cloud_plan_id: current.planId, confirmation: 'REQUEST RELEASE REVIEW'})
      });
      if (!response.ok) throw Error('HTTP ' + response.status);
      const result = await response.json();
      if (inspected && inspected.revision === current.revision)
        gateReviewStatus.textContent = 'Запрос согласования: ' + result.id +
          ' · ' + result.status + '. Публикация не выполнялась.';
    } catch (error) {
      gateReviewStatus.textContent = 'Запрос не создан: ' + error.message;
    } finally {
      gateRequest.disabled = !releaseGate;
    }
  });
  fleetRefresh.addEventListener('click', async () => {
    if (!inspected) return;
    const current = inspected;
    fleetRefresh.disabled = true;
    fleetStatus.textContent = 'Проверяем подключённые Railway-сервисы…';
    fleetServices.replaceChildren();
    try {
      const response = await fetch('/api/v1/cloud/fleet/services?refresh=true',
        {credentials: 'same-origin'});
      if (!response.ok) throw Error('HTTP ' + response.status);
      const result = await response.json();
      if (!inspected || inspected.id !== current.id ||
          inspected.revision !== current.revision) return;
      const plans = new Set([...runtimePlan.options].map(option => option.value));
      const services = result.services.filter(service => plans.has(service.plan_id));
      fleetStatus.textContent = 'Найдено сервисов: ' + services.length +
        '. Проверка Telegram-доставки не выполнялась.';
      if (!services.length)
        fleetServices.append(item('p', 'Для этого проекта пока нет подключённых Railway-сервисов.'));
      for (const service of services) {
        const panel = document.createElement('div');
        panel.className = 'graph-release-runtime-job';
        panel.append(item('p', service.plan_name + ' · Railway: ' +
          (service.provider_status || 'неизвестно')));
        panel.append(item('p', 'Состояние: ' +
          service.reconciliation.state +
          ' · проверено: ' + (service.last_checked_at || 'никогда')));
        if (service.incident) {
          panel.append(item('p', 'Диагностика: ' + service.incident.incident_code +
            ' · ' + service.incident.severity));
          panel.append(item('p', 'Рекомендуемое действие: ' + service.incident.next_action));
          for (const finding of service.incident.findings || [])
            panel.append(item('p', 'Замечание: ' + finding));
        }
        if (service.provider_error)
          panel.append(item('p', 'Ошибка: ' + service.provider_error));
        panel.append(item('p', 'Работа Telegram-бота: не подтверждена'));
        fleetServices.append(panel);
      }
    } catch (error) {
      fleetStatus.textContent = 'Не удалось получить статус Railway: ' + error.message;
    } finally {
      fleetRefresh.disabled = false;
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
