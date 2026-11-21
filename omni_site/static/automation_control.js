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
  async function csrfToken(){
    const response=await fetch('/api/v1/builder/projects/csrf',{credentials:'same-origin'});
    if(!response.ok)throw Error('Требуется вход в аккаунт');
    const data=await response.json();
    return data.csrf_token;
  }
  async function connectionPost(path,payload){
    const headers={'X-Omni-CSRF':await csrfToken()};
    if(payload!==undefined)headers['Content-Type']='application/json';
    const response=await fetch('/api/v1/automation/'+path,{method:'POST',credentials:'same-origin',headers,
      ...(payload===undefined?{}:{body:JSON.stringify(payload)})});
    if(!response.ok)throw Error('HTTP '+response.status);
    return response.json();
  }
  const connectionStatus=message=>{$('control-connections-status').textContent=message;};
  async function refreshConnections(){
    const root=$('control-connections');root.replaceChildren();
    try{
      const response=await fetch('/api/v1/automation/connections',{credentials:'same-origin'});
      if(!response.ok)throw Error('HTTP '+response.status);
      const data=await response.json();
      for(const connection of data.connections){
        const card=item(connection.label,connection.provider+' · '+connection.status);
        const actions=el('div');actions.className='control-connection-actions';
        if(connection.authorization==='oauth'&&connection.status!=='disconnected'){
          const auth=el('button','Авторизовать');auth.type='button';auth.className='control-action';
          auth.addEventListener('click',async()=>{
            auth.disabled=true;
            try{const result=await connectionPost('oauth/'+encodeURIComponent(connection.id)+'/start');
              const target=new URL(result.authorization_url);
              if(target.protocol!=='https:')throw Error('Некорректный адрес OAuth');
              window.location.assign(target.href);
            }catch(error){connectionStatus('Авторизация недоступна: '+error.message);auth.disabled=false;}
          });actions.append(auth);
        }
        if(connection.status!=='disconnected'){
          const health=el('button','Проверить доступ');health.type='button';health.className='control-action';
          health.addEventListener('click',async()=>{
            health.disabled=true;
            try{const result=await connectionPost('connections/'+encodeURIComponent(connection.id)+'/health');
              connectionStatus(connection.label+': '+result.health+' · permissions_verified='+result.permissions_verified);
              await refreshConnections();
            }catch(error){connectionStatus('Проверка не выполнена: '+error.message);}finally{health.disabled=false;}
          });actions.append(health);
          const disconnect=el('button','Отключить');disconnect.type='button';disconnect.className='control-action';
          disconnect.addEventListener('click',async()=>{
            if(!window.confirm('Отключить интеграцию и удалить сохранённый токен?'))return;
            disconnect.disabled=true;
            try{await connectionPost('connections/'+encodeURIComponent(connection.id)+'/disconnect');
              connectionStatus('Подключение отключено.');await refreshConnections();
            }catch(error){connectionStatus('Отключение не выполнено: '+error.message);disconnect.disabled=false;}
          });actions.append(disconnect);
        }
        const audit=el('button','Журнал');audit.type='button';audit.className='control-action';
        audit.addEventListener('click',async()=>{
          audit.disabled=true;
          try{const data=await get('/connections/'+encodeURIComponent(connection.id)+'/audit');
            const detail=el('pre',data.events.map(e=>e.created_at+' · '+e.action).join('\\n')||'Событий нет');
            card.querySelectorAll('pre').forEach(node=>node.remove());card.append(detail);
          }catch(error){connectionStatus('Журнал недоступен: '+error.message);}finally{audit.disabled=false;}
        });actions.append(audit);card.append(actions);root.append(card);
      }
      if(!data.connections.length)root.append(el('p','Подключений пока нет. Создайте первое выше.'));
      connectionStatus('Подключения загружены. Авторизация и проверка разрешений — разные этапы.');
    }catch(error){connectionStatus('Управление подключениями доступно владельцу после входа: '+error.message);}
  }
  $('control-connect-form').addEventListener('submit',async event=>{
    event.preventDefault();const button=event.currentTarget.querySelector('button[type=submit]');
    button.disabled=true;
    try{await connectionPost('connections',{provider:$('control-provider').value,
      label:$('control-connection-label').value.trim()});
      $('control-connection-label').value='';await refreshConnections();
    }catch(error){connectionStatus('Создание не выполнено: '+error.message);}finally{button.disabled=false;}
  });
  $('control-refresh').addEventListener('click',refresh);
  void refresh();
  void refreshConnections();
})();