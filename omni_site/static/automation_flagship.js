(() => {
  const status = document.getElementById('flagship-result-status');
  const trace = document.getElementById('flagship-trace');
  const variables = document.getElementById('flagship-variables');
  if (!status || !trace || !variables) return;
  document.querySelectorAll('[data-preview]').forEach(button => {
    button.addEventListener('click', async () => {
      const slug = button.dataset.preview;
      if (!/^[a-z0-9-]+$/.test(slug)) return;
      button.disabled = true;
      status.textContent = 'Выполняется безопасный серверный dry-run…';
      trace.replaceChildren();
      variables.hidden = true;
      try {
        const response = await fetch('/integrations/preview/' + slug, {
          method: 'POST', credentials: 'omit',
          headers: { 'Accept': 'application/json' }
        });
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const data = await response.json();
        status.textContent = 'Статус: ' + data.status + ' · ' + data.steps +
          ' шагов · внешние вызовы: ' + (data.external_calls_executed ? 'да' : 'нет');
        (data.trace || []).forEach(step => {
          const li = document.createElement('li');
          li.textContent = [step.step, step.node, step.kind, step.outcome].filter(Boolean).join(' / ');
          trace.appendChild(li);
        });
        variables.hidden = false;
        variables.textContent = 'Переменные: ' + JSON.stringify(data.variables, null, 2);
      } catch (error) {
        status.textContent = 'Тестовый запуск недоступен. Повторите попытку позднее.';
      } finally {
        button.disabled = false;
      }
    });
  });
})();
