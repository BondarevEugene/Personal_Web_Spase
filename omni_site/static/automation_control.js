(() => {
  'use strict';
  const API='/api/v1/automation';
  const $=id=>document.getElementById(id);
  const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  const state=(message,bad=false)=>{$('control-status').textContent=message;$('control-status').classList.toggle('control-error',bad);};
  async function get(path){
    const response=await fetch(API+path,{credentials:'same-origin',headers:{Accept:'application/json'}});
    if(!response.ok)throw Error('HTTP '+response.status);
    return response.json();
  }
  function item(title,description){
    const box=el('div');box.className='control-item';
    box.append(el('strong',title),el('small',description));
    return box;
  }
  async function refresh(){
    $('control-refresh').disabled=true;state('Обновляем состояние…');
    try{
      const data=await get('/control/summary');
      $('control-workflows').textContent=String(data.workflow_count);
      $('control-runs').textContent=String(data.sampled_run_count);
      $('control-failed').textContent=String((data.status_counts.failed||0)+(data.status_counts.step_limit||0));
      $('control-schedules').textContent=String(data.active_schedules);
      const history=$('control-history');history.replaceChildren();
      for(const run of data.runs){
        const box=item(run.status+' · '+run.mode,'Запуск '+run.id+' · '+run.created_at+' · версия '+run.revision);
        const detail=el('details');detail.append(el('summary','Трассировка шагов'));
        const pre=el('pre',JSON.stringify(run.trace,null,2));pre.style.whiteSpace='pre-wrap';pre.style.overflowWrap='anywhere';detail.append(pre);box.append(detail);
        if(run.mode==='dry_run' && ['failed','step_limit'].includes(run.status)){
          const button=el('button','Повторить безопасный dry-run');button.className='control-action';
          button.addEventListener('click',async()=>{
            if(!window.confirm('Повторить текущую версию сценария с ПУСТЫМИ входными данными? Внешние операции не выполняются.'))return;
            button.disabled=true;
            try{
              const csrfResponse=await fetch('/api/v1/builder/projects/csrf',{credentials:'same-origin'});
              if(!csrfResponse.ok)throw Error('Нужен вход в аккаунт');
              const token=(await csrfResponse.json()).csrf_token;
              const response=await fetch(API+'/workflows/'+encodeURIComponent(run.workflow_id)+'/runs/'+encodeURIComponent(run.id)+'/retry-dry-run',{
                method:'POST',credentials:'same-origin',headers:{'X-Omni-CSRF':token}
              });
              if(!response.ok)throw Error('HTTP '+response.status+' — сценарий может требовать входные данные или проверки');
              await refresh();
            }catch(error){state('Повтор не выполнен: '+error.message,true);button.disabled=false;}
          });
          box.append(button);
        }
        history.append(box);
      }
      if(!data.runs.length)history.append(el('p','Запусков пока нет.'));
      const workflows=$('control-workflow-list');workflows.replaceChildren();
      const chooser=$('control-select-workflow');const previous=chooser.value;
      chooser.replaceChildren(new Option('Выберите сценарий',''));
      for(const flow of data.workflows){
        chooser.add(new Option(flow.name+' · v'+flow.revision,flow.id));
        const box=item(flow.name,'Версия '+flow.revision+' · обновлён '+flow.updated_at);
        const link=el('a','Открыть в Studio ↗');link.href='/automation/studio';box.append(link);workflows.append(box);
      }
      if(data.workflows.some(flow=>flow.id===previous))chooser.value=previous;
      if(!data.workflows.length)workflows.append(el('p','Сценариев пока нет.'));
      state('Данные обновлены. Показаны только сохранённые события вашего аккаунта.');
    }catch(error){state('Не удалось загрузить данные: '+error.message,true);}
    try{
      const data=await get('/connectors/diagnostics');
      const root=$('control-readiness');root.replaceChildren();
      for(const connector of data.connectors){
        root.append(item(connector.label,connector.status==='operator_gate_ready'?'Операторские ограничения готовы · доступ API не проверен':'Ограничения: '+connector.reasons.join(', ')));
      }
    }catch(error){
      $('control-readiness').textContent='Доступно только владельцу аккаунта. Данные о секретах не раскрываются.';
    }finally{$('control-refresh').disabled=false;}
  }
  $('control-diagnose').addEventListener('click',async()=>{
    const id=$('control-select-workflow').value;
    const root=$('control-node-diagnostics');root.replaceChildren();
    if(!id){root.textContent='Выберите сценарий.';return;}
    try{
      const data=await get('/workflows/'+encodeURIComponent(id)+'/connectors/diagnostics');
      root.append(el('p','Версия '+data.revision+' · готово '+data.ready+' · требуется настройка '+data.blocked));
      for(const node of data.nodes){root.append(item(node.label+' · '+node.node_id,node.status==='configuration_ready'?'Настройки готовы; разрешения внешнего API не проверены':'Требуется настройка: '+node.reasons.join(', ')));}
      if(!data.nodes.length)root.append(el('p','В этом сценарии нет узлов внешних интеграций.'));
    }catch(error){root.textContent='Диагностика недоступна: '+error.message;}
  });
  $('control-refresh').addEventListener('click',refresh);
  void refresh();
})();