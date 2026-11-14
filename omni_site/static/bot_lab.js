/* OmniFactory Bot Lab: data from the logged-in customer's API, no mock metrics. */
(()=>{
'use strict';
const $=id=>document.getElementById(id),BASE='/api/v1/bot-lab';
let store=null,selected=null,filter='',railwayResources=[];
const say=(msg,bad=false)=>{$('lab-notice').textContent=msg;$('lab-notice').classList.toggle('error',bad);};
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
function action(text,url,primary=false){
 const a=el('a','lab-button'+(primary?' primary':''),text);
 a.href=url;return a;
}
const prettyDate=iso=>iso?new Date(iso).toLocaleString('ru-RU'):'Нет сведений';
async function fetchJson(path){
 const response=await fetch(BASE+path,{cache:'no-store',credentials:'same-origin'});
 if(!response.ok)throw Error(response.status===401?'Требуется вход в клиентский кабинет':
  response.status===503?'База ещё не обновлена миграциями':
  response.status===409?'Подключение Railway отсутствует или требуется обновить доступ':
  'Ошибка API: HTTP '+response.status);
 return response.json();
}
function records(){
 if(!store)return [];
 return [
  ...store.bot_projects.map(p=>({...p,entity:'bot',search:p.name.toLowerCase()})),
  ...(store.shared_bots||[]).map(p=>({...p,entity:'shared',search:p.name.toLowerCase()})),
  ...store.deployments.map(p=>({...p,entity:'plan',search:p.name.toLowerCase()})),
  ...store.automations.map(p=>({...p,entity:'flow',search:p.name.toLowerCase()}))
 ];
}
function showList(id,kind,empty){
 const root=$(id);root.replaceChildren();
 const items=records().filter(i=>i.entity===kind&&i.search.includes(filter));
 if(!items.length){root.append(el('p','lab-empty',empty));return;}
 for(const item of items){
  const b=el('button','lab-item');
  b.type='button';b.setAttribute('aria-pressed',String(Boolean(selected&&selected.entity===kind&&selected.id===item.id)));
  b.append(el('strong','',item.name));
  b.append(el('small','',kind==='bot'?'Черновик · Graph Studio':
    kind==='plan'?item.mode+' / '+item.provider+' · '+item.status:
    kind==='shared'?'Доступ: '+item.role:'Ревизия '+item.revision));
  b.addEventListener('click',()=>{selected={entity:kind,id:item.id};renderDetail();renderLists();});
  root.append(b);
 }
}
function renderLists(){
 if(!store)return;
 showList('lab-bots-list','bot','Сохранённых ботов нет.');
 showList('lab-shared-list','shared','Другие пользователи не открывали доступ.');
 showList('lab-plans-list','plan','Планов размещения нет.');
 showList('lab-flows-list','flow','Автоматизаций нет.');
}
function fact(root,title,value){
 const box=el('div','lab-fact');
 box.append(el('strong','',title),el('span','',value));
 root.append(box);
}
function renderDetail(){
 const info=records().find(i=>selected&&i.id===selected.id&&i.entity===selected.entity);
 const facts=$('lab-selected-facts'),acts=$('lab-actions');
 facts.replaceChildren();acts.replaceChildren();$('lab-readiness').replaceChildren();
 $('lab-security-workbench').hidden=!info||info.entity!=='bot';
 clearSecretInput();
 $('lab-enqueue').disabled=!selected||selected.entity!=='plan';
 if(!info){
  selected=null;$('lab-selected-name').textContent='Выбери бота слева';
  $('lab-selected-status').textContent='Нет выбора';
  $('lab-selected-summary').textContent='Нажми на проект или план размещения, чтобы увидеть реальные доступные действия.';
  acts.append(action('＋ Создать бота','/architect',true));
  return;
 }
 $('lab-enqueue').disabled=info.entity!=='plan';
 syncResourceControls();
 $('lab-selected-name').textContent=info.name;
 if(info.entity==='bot'){
  $('lab-selected-status').textContent='Черновик';
  $('lab-selected-summary').textContent='Сценарий сохранён в аккаунте. Данные о развернутом Railway-сервисе ещё не связаны с этим проектом.';
  fact(facts,'Тип','Telegram Bot');fact(facts,'Состояние','Сохранён, не опубликован');
  fact(facts,'Последнее изменение',prettyDate(info.updated_at));fact(facts,'Источник','Graph Studio');
  acts.append(action('Открыть конструктор','/architect',true),
              action('Подготовить деплой','/cloud/deploy'));
  void refreshSecurity(info.id);
 }else if(info.entity==='shared'){
  $('lab-selected-status').textContent=info.role==='viewer'?'Наблюдатель':'Оператор';
  $('lab-selected-summary').textContent='Владелец предоставил доступ только к карточке этого бота. Конструктор, токены и облачные ресурсы не доступны через этот доступ.';
  fact(facts,'Роль',info.role);fact(facts,'Владелец',info.owner_id);
  fact(facts,'Изменено',prettyDate(info.updated_at));
  acts.append(el('span','lab-muted','Для изменения сценария потребуется отдельное разрешение владельца и проверенный механизм доступа.'));
 }else if(info.entity==='plan'){
  $('lab-selected-status').textContent=info.status;
  $('lab-selected-summary').textContent='Это сохранённый план Cloud Deploy. Он не подтверждает создание сервиса и не списывает деньги.';
  fact(facts,'Режим',info.mode==='managed'?'OmniFactory Managed Cloud':'Свой Railway');
  fact(facts,'Провайдер',info.provider);fact(facts,'Дата создания',prettyDate(info.created_at));
  fact(facts,'Состояние',info.status);
  acts.append(action('Открыть Cloud Deploy','/cloud/deploy',true),
              action('Проверить Railway','/cloud/deploy'));
  const check=el('button','lab-button','Проверить готовность к запуску');
  check.type='button';check.addEventListener('click',()=>reviewPlan(info.id));
  acts.append(check);
 }else{
  $('lab-selected-status').textContent='Workflow';
  $('lab-selected-summary').textContent='Сценарий автоматизации доступен для редактирования, анализа и dry-run. Это не признак публичного запуска.';
  fact(facts,'Версия','r'+info.revision);fact(facts,'Тип','Automation workflow');
  fact(facts,'Последнее изменение',prettyDate(info.updated_at));
  acts.append(action('Открыть Automation Studio','/automation/studio',true),
              action('Cloud Deploy','/cloud/deploy'));
 }
}
function renderOverview(){
 $('lab-count-bots').textContent=store.bot_projects.length;
 $('lab-count-flows').textContent=store.automations.length;
 $('lab-count-plans').textContent=store.deployments.length;
 $('lab-railway-flag').textContent=store.railway.connected?'Подключён':'Не подключён';
 $('lab-railway-desc').textContent=store.railway.connected?
   store.railway.account_name||'Разрешённый аккаунт':'Перейти к настройке OAuth';
 $('lab-cloud-status').textContent=store.railway.connected?
   'Подключён Railway · '+(store.railway.account_name||'аккаунт')+
    ' · истекает '+prettyDate(store.railway.access_expires_at):
   'Railway не подключён. Для чтения проектов разреши доступ через Cloud Deploy.';
 $('lab-check-railway').disabled=!store.railway.connected;
 renderLists();renderDetail();
}
async function refresh(){
 try{
  say('Обновляем данные аккаунта…');
  store=await fetchJson('/overview');
  try{store.shared_bots=(await secretApi('/shared')).bots;}catch{store.shared_bots=[];}
  renderOverview();
  say('Данные загружены из клиентской базы OMNIFACTORY. Планы не считаются работающими ботами.');
 }catch(err){
  store=null;selected=null;
  say(err.message,true);
  for(const id of ['lab-bots-list','lab-plans-list','lab-flows-list'])
   $(id).textContent='Нет проверенных данных.';
  for(const id of ['lab-count-bots','lab-count-flows','lab-count-plans'])$(id).textContent='—';
  $('lab-railway-flag').textContent='—';$('lab-cloud-status').textContent='Нужна авторизация или проверка базы.';
  $('lab-check-railway').disabled=true;
  $('lab-actions').replaceChildren(action('Войти в аккаунт','/account/login',true));
 }
}
async function reviewPlan(id){
 const root=$('lab-readiness');root.replaceChildren();
 root.append(el('p','lab-muted','Проверяем обязательные условия публикации…'));
 try{
  const body=await fetchJson('/deploy-readiness/'+encodeURIComponent(id));
  if(!selected||selected.id!==id)return;
  root.replaceChildren();
  root.append(el('strong','lab-readiness-title',body.ready?'Все проверки пройдены':'Публикация пока недоступна'));
  for(const item of body.checks){
   const line=el('div','lab-readiness-item '+(item.ok?'ok':'blocked'));
   const mark=el('b','',item.ok?'✓':'!');
   const content=el('span','',item.message);
   const a=el('a','',item.ok?'Подробнее':'Исправить / настроить');
   a.href=item.action;
   line.append(mark,content,a);root.append(line);
  }
  say('Проверка завершена: '+body.checks.filter(x=>x.ok).length+' из '+body.checks.length+' условий выполнены.');
 }catch(err){
  root.replaceChildren(el('p','lab-muted','Не удалось проверить план: '+err.message));
  say('Ошибка проверки готовности: '+err.message,true);
 }
}
async function provisionRequest(path,options={}){
 const response=await fetch('/api/v1/cloud/provision'+path,{
   cache:'no-store',credentials:'same-origin',...options});
 if(!response.ok){
   const error=await response.json().catch(()=>({}));
   throw Error(typeof error.detail==='string'?error.detail:'HTTP '+response.status);
 }
 return response.json();
}
async function csrf(){
 const response=await fetch('/api/v1/builder/projects/csrf',{credentials:'same-origin'});
 if(!response.ok)throw Error('Войди в аккаунт для создания задач.');
 return (await response.json()).csrf_token;
}
async function enqueueSimulation(){
 if(!selected||selected.entity!=='plan')return say('Выбери план Cloud Deploy.',true);
 if(!window.confirm('Создать только тестовую задачу? Railway-сервисы НЕ будут созданы и деньги НЕ спишутся.'))return;
 try{
   const id=selected.id;
   const key='lab-dry-'+id;
   const job=await provisionRequest('/jobs',{method:'POST',headers:{
     'Content-Type':'application/json','X-Omni-CSRF':await csrf(),
     'Idempotency-Key':key},
     body:JSON.stringify({plan_id:id,confirmation:'SIMULATE DEPLOYMENT'})});
   say('Задача '+job.id+' сохранена. Для обработки необходим отдельный worker.');
   await refreshJobs();
 }catch(err){say('Ошибка очереди: '+err.message,true);}
}
async function refreshJobs(){
 const root=$('lab-provision-jobs');root.replaceChildren();
 try{
   const response=await provisionRequest('/jobs');
   const rows=response.jobs.filter(j=>!selected||selected.entity!=='plan'||j.plan_id===selected.id);
   if(!rows.length){root.append(el('p','lab-muted','Пока нет задач.'));return;}
   for(const job of rows.slice(0,20)){
     const container=el('div','lab-job');
     const title=el('strong','',job.status+' · '+job.mode);
     const date=el('small','',prettyDate(job.created_at));
     const details=el('button','lab-small','События');
     details.type='button';
     details.addEventListener('click',async()=>{
       try{
         const entry=await provisionRequest('/jobs/'+encodeURIComponent(job.id));
         const log=el('div','lab-job-log');
         entry.events.forEach(event=>log.append(el('p','',event.code+' · '+event.message)));
         container.querySelector('.lab-job-log')?.remove();
         container.append(log);
       }catch(err){say(err.message,true);}
     });
     container.append(title,date,details);root.append(container);
   }
 }catch(err){root.append(el('p','lab-muted','История задач недоступна: '+err.message));}
}
const RESOURCES='/api/v1/cloud/resources';
function currentByocPlan(){
 const i=records().find(x=>selected&&x.entity==='plan'&&x.id===selected.id);
 return i&&i.mode==='byoc'?i:null;
}
function selectedResourceProject(){
 return railwayResources.find(p=>p.id===$('lab-resource-project').value);
}
function setOptions(id,items,emptyLabel){
 const select=$(id);select.replaceChildren();
 const empty=el('option','',emptyLabel);empty.value='';select.append(empty);
 items.forEach(item=>{const option=el('option','',item.name||item.id);option.value=item.id;select.append(option)});
}
function syncResourceControls(){
 const enabled=Boolean(currentByocPlan());
 ['lab-resources-load','lab-resource-project','lab-resource-service','lab-resource-environment']
 .forEach(id=>$(id).disabled=!enabled);
 $('lab-resources-bind').disabled=!enabled||!$('lab-resource-project').value||
   !$('lab-resource-service').value||!$('lab-resource-environment').value;
 $('lab-resources-inspect').disabled=!enabled;
 $('lab-resources-unlink').disabled=!enabled;
 if(!enabled){
  $('lab-resource-report').textContent='Выбери сохранённый план BYOC для просмотра инфраструктуры.';
  $('lab-resources-inspect').disabled=true;$('lab-resources-unlink').disabled=true;
 }else void loadBinding();
}
async function resourceApi(url,options={}){
 const response=await fetch(RESOURCES+url,{cache:'no-store',credentials:'same-origin',...options});
 if(!response.ok){
  const info=await response.json().catch(()=>({}));
  throw Error(typeof info.detail==='string'?info.detail:'HTTP '+response.status);
 }
 return response.status===204?null:response.json();
}
async function loadResourceOptions(){
 if(!currentByocPlan())return say('Выбери план BYOC.',true);
 try{
  const data=await fetchJson('/railway/projects');
  railwayResources=data.projects;
  setOptions('lab-resource-project',railwayResources,'Выбери проект');
  setOptions('lab-resource-service',[],'Выбери сервис');
  setOptions('lab-resource-environment',[],'Выбери окружение');
  $('lab-resource-report').textContent='Railway вернул '+railwayResources.length+' доступных проектов. Выбери проект, сервис и окружение.';
  syncResourceControls();
 }catch(err){say('Не удалось получить ресурсы: '+err.message,true);}
}
function projectChanged(){
 const project=selectedResourceProject();
 setOptions('lab-resource-service',project?.services||[],'Выбери сервис');
 setOptions('lab-resource-environment',project?.environments||[],'Выбери окружение');
 $('lab-resources-bind').disabled=true;
}
function bindingReport(data){
 const root=$('lab-resource-report');root.replaceChildren();
 if(!data?.binding){
  root.append(el('p','lab-muted','Привязанный Railway-сервис не найден.'));
  return;
 }
 const binding=data.binding;
 root.append(el('strong','', 'Привязан сервис: '+binding.service_id));
 root.append(el('p','','Проект: '+binding.project_id+' · окружение: '+binding.environment_id));
 root.append(el('p','','Последняя проверка: '+prettyDate(binding.last_checked_at)));
 if(data.provider){
  const deployment=data.provider.deployment;
  root.append(el('p','', 'Railway deployment: '+(deployment?deployment.status:'отсутствует')));
  if(deployment)root.append(el('p','', 'ID деплоя: '+deployment.id));
  root.append(el('p','lab-muted','Статус Railway не подтверждает работоспособность Telegram-бота. Нужна проверка /health и Webhook.'));
 }
}
async function loadBinding(){
 const plan=currentByocPlan();
 if(!plan)return;
 const requested=plan.id;
 try{
  const result=await resourceApi('/bindings/'+encodeURIComponent(requested));
  if(!currentByocPlan()||currentByocPlan().id!==requested)return;
  $('lab-resources-inspect').disabled=!result.binding;
  $('lab-resources-unlink').disabled=!result.binding;
  bindingReport(result);
 }catch(err){
  $('lab-resources-inspect').disabled=true;
  $('lab-resources-unlink').disabled=true;
  $('lab-resource-report').textContent='Не удалось получить привязку: '+err.message;
 }
}
async function bindResource(){
 const plan=currentByocPlan();
 if(!plan)return;
 const project_id=$('lab-resource-project').value,
       service_id=$('lab-resource-service').value,
       environment_id=$('lab-resource-environment').value;
 if(!project_id||!service_id||!environment_id)return;
 if(!window.confirm('Привязать существующий Railway-сервис? Это только чтение и не создаёт инфраструктуру.'))return;
 try{
  const report=await resourceApi('/bindings',{method:'POST',headers:{
    'Content-Type':'application/json','X-Omni-CSRF':await csrf()},
    body:JSON.stringify({plan_id:plan.id,project_id,service_id,environment_id})});
  if(!currentByocPlan()||currentByocPlan().id!==plan.id)return;
  bindingReport(report);$('lab-resources-inspect').disabled=false;$('lab-resources-unlink').disabled=false;
  say('Сервис подтверждён через Railway GraphQL и привязан к плану.');void reviewPlan(plan.id);
 }catch(err){say('Ошибка привязки: '+err.message,true);}
}
async function inspectResource(){
 const plan=currentByocPlan();if(!plan)return;
 try{
  const report=await resourceApi('/bindings/'+encodeURIComponent(plan.id)+'/inspect');
  if(!currentByocPlan()||currentByocPlan().id!==plan.id)return;
  bindingReport(report);say('Получен настоящий статус сервиса Railway. Healthcheck бота ещё не подтверждён.');
 }catch(err){say('Ошибка проверки Railway: '+err.message,true);}
}
async function unlinkResource(){
 const plan=currentByocPlan();if(!plan)return;
 if(!window.confirm('Отвязать сервис от плана? Сам сервис Railway НЕ удаляется.'))return;
 try{
  await resourceApi('/bindings/'+encodeURIComponent(plan.id),{
   method:'DELETE',headers:{'X-Omni-CSRF':await csrf()}});
  $('lab-resources-inspect').disabled=true;$('lab-resources-unlink').disabled=true;
  bindingReport({binding:null});say('Привязка удалена. Railway-сервис не затронут.');
 }catch(err){say('Ошибка отвязки: '+err.message,true);}
}

const SEC='/api/v1/bot-security';
function clearSecretInput(){const input=$('lab-telegram-token');if(input)input.value='';}
async function secretApi(path,options={}){
 const response=await fetch(SEC+path,{credentials:'same-origin',cache:'no-store',...options});
 if(!response.ok){
  const result=await response.json().catch(()=>({}));
  const detail=typeof result.detail==='string'?result.detail:'HTTP '+response.status;
  throw Error(detail);
 }
 return response.status===204?null:response.json();
}
function currentOwnedBot(){
 const item=records().find(x=>selected&&x.id===selected.id&&x.entity==='bot');
 return item||null;
}
async function secureWrite(path,method,payload){
 const headers={'X-Omni-CSRF':await csrf()};
 if(payload!==undefined)headers['Content-Type']='application/json';
 return secretApi(path,{method,headers,
   ...(payload!==undefined?{body:JSON.stringify(payload)}:{})});
}
function renderMembers(id,items,kind){
 const root=$(id);root.replaceChildren();
 if(!items.length){root.append(el('p','lab-muted','Пока никого нет.'));return;}
 for(const member of items){
  const entry=el('div','lab-member');
  entry.append(el('div','',member.username+' · '+(member.role==='viewer'?'Наблюдатель':'Оператор')));
  const button=el('button','lab-small',kind==='invite'?'Отозвать приглашение':'Закрыть доступ');
  button.type='button';
  button.addEventListener('click',async()=>{
   if(!window.confirm('Подтверди отзыв доступа для '+member.username))return;
   const bot=currentOwnedBot();if(!bot)return;
   try{
    const path=kind==='invite'
     ?'/bots/'+bot.id+'/invitations/'+member.id
     :'/bots/'+bot.id+'/access/'+member.id;
    await secureWrite(path,'DELETE');
    say('Доступ или приглашение отозваны.');await refreshSecurity(bot.id);
   }catch(error){say('Не удалось отозвать: '+error.message,true);}
  });
  entry.append(button);root.append(entry);
 }
}
async function refreshSecurity(id){
 if(!currentOwnedBot()||currentOwnedBot().id!==id)return;
 $('lab-invite-once').hidden=true;
 $('lab-invite-token').textContent='';
 try{
  const [credential,access,invitations,audit]=await Promise.all([
   secretApi('/bots/'+id+'/credential'),
   secretApi('/bots/'+id+'/access'),
   secretApi('/bots/'+id+'/invitations'),
   secretApi('/bots/'+id+'/audit')
  ]);
  if(!currentOwnedBot()||currentOwnedBot().id!==id)return;
  $('lab-secret-indicator').textContent=credential.verified?'Проверен в Telegram':
   credential.configured?'Сохранён, не проверен':'Не подключён';
  $('lab-token-status').textContent=credential.configured
   ?'Токен скрыт · '+(credential.verified
     ?'@'+credential.username+' · ID '+credential.bot_id
     :'требуется проверка через Telegram')
   :'Бот не подключён. Для создания секрета нужен BotFather.';
  $('lab-token-save').disabled=!credential.vault_configured;
  $('lab-token-verify').disabled=!credential.configured;
  $('lab-token-revoke').disabled=!credential.configured;
  renderMembers('lab-members',access.members,'grant');
  renderMembers('lab-pending-invites',invitations.invitations,'invite');
  const auditRoot=$('lab-security-audit');auditRoot.replaceChildren();
  for(const entry of audit.events){
   auditRoot.append(el('p','lab-audit-event',entry.event+' · '+prettyDate(entry.created_at)));
  }
  if(!audit.events.length)auditRoot.append(el('p','lab-muted','Событий ещё нет.'));
 }catch(error){$('lab-token-status').textContent='Модуль безопасности недоступен: '+error.message;
  say('Ошибка безопасности: '+error.message,true);}
}
async function storeBotToken(){
 const bot=currentOwnedBot();if(!bot)return;
 const token=$('lab-telegram-token').value.trim();
 if(!token)return say('Укажи токен Telegram BotFather.',true);
 if(!window.confirm('Зашифровать токен для выбранного бота? Старый токен будет заменён.'))return;
 try{
  await secureWrite('/bots/'+bot.id+'/credential','PUT',{token});
  clearSecretInput();
  say('Токен сохранён в защищённом хранилище. Проверка Telegram выполняется отдельно.');
  await refreshSecurity(bot.id);
 }catch(error){say('Ошибка сохранения токена: '+error.message,true);}
 finally{clearSecretInput();}
}
async function verifyBotToken(){
 const bot=currentOwnedBot();if(!bot)return;
 try{
  await secureWrite('/bots/'+bot.id+'/credential/verify','POST');
  say('Telegram подтвердил идентификатор бота.');await refreshSecurity(bot.id);
 }catch(error){say('Telegram не подтвердил токен: '+error.message,true);}
}
async function deleteBotToken(){
 const bot=currentOwnedBot();if(!bot)return;
 if(!window.confirm('Безвозвратно удалить секрет из OMNIFACTORY? При необходимости также отзови токен у BotFather.'))return;
 try{
  await secureWrite('/bots/'+bot.id+'/credential','DELETE');
  clearSecretInput();say('Секрет удалён из OMNIFACTORY.');
  await refreshSecurity(bot.id);
 }catch(error){say('Ошибка удаления: '+error.message,true);}
}
async function createInvitation(){
 const bot=currentOwnedBot();if(!bot)return;
 const username=$('lab-invite-username').value.trim().toLowerCase();
 const role=$('lab-invite-role').value;
 if(!username)return say('Введи точный логин зарегистрированного пользователя.',true);
 try{
  const response=await secureWrite('/bots/'+bot.id+'/invitations','POST',{username,role});
  // Never persist invitation tokens in localStorage or location.
  $('lab-invite-token').textContent=response.one_time_token;
  $('lab-invite-once').hidden=false;
  $('lab-invite-username').value='';
  say('Приглашение готово. Код виден один раз и действует 24 часа.');
  const invites=await secretApi('/bots/'+bot.id+'/invitations');
  renderMembers('lab-pending-invites',invites.invitations,'invite');
 }catch(error){say('Не удалось создать приглашение: '+error.message,true);}
}
async function acceptInvitation(){
 const code=$('lab-accept-token').value.trim();
 if(!code)return say('Вставь одноразовый код приглашения.',true);
 try{
  const result=await secureWrite('/invitations/accept','POST',{token:code});
  $('lab-accept-token').value='';
  say('Доступ подтверждён: '+result.role+'. Открой карточку в «Доступ предоставлен мне».');
  await refresh();
 }catch(error){$('lab-accept-token').value='';say('Приглашение не принято: '+error.message,true);}
}
async function railwayProjects(){
 const root=$('lab-provider-projects');root.replaceChildren();
 root.append(el('p','lab-muted','Получаем разрешённые проекты Railway…'));
 try{
  const response=await fetchJson('/railway/projects');
  root.replaceChildren();
  if(!response.projects.length){root.append(el('p','lab-empty','Railway не вернул доступных проектов.'));return;}
  for(const p of response.projects){
   const card=el('div','lab-provider-card');
   card.append(el('strong','',p.name),el('small','',
     p.services.length+' сервисов · '+p.environments.length+' окружений'));
   root.append(card);
  }
  say('Проекты получены от Railway. Управляющие операции ещё отключены.');
 }catch(err){
  root.replaceChildren(el('p','lab-muted','Не удалось получить проекты: '+err.message));
  say('Ошибка Railway: '+err.message,true);
 }
}
$('lab-refresh').addEventListener('click',refresh);
$('lab-search').addEventListener('input',value=>{filter=value.target.value.trim().toLowerCase();renderLists();});
$('lab-check-railway').addEventListener('click',railwayProjects);
$('lab-enqueue').addEventListener('click',enqueueSimulation);
$('lab-jobs-refresh').addEventListener('click',refreshJobs);
$('lab-token-save').addEventListener('click',storeBotToken);
$('lab-token-verify').addEventListener('click',verifyBotToken);
$('lab-token-revoke').addEventListener('click',deleteBotToken);
$('lab-invite-create').addEventListener('click',createInvitation);
$('lab-accept-button').addEventListener('click',acceptInvitation);
$('lab-invite-copy').addEventListener('click',()=>{
 const token=$('lab-invite-token').textContent;
 if(token&&navigator.clipboard)void navigator.clipboard.writeText(token);
});

$('lab-resources-load').addEventListener('click',loadResourceOptions);
$('lab-resource-project').addEventListener('change',projectChanged);
$('lab-resource-service').addEventListener('change',syncResourceControls);
$('lab-resource-environment').addEventListener('change',syncResourceControls);
$('lab-resources-bind').addEventListener('click',bindResource);
$('lab-resources-inspect').addEventListener('click',inspectResource);
$('lab-resources-unlink').addEventListener('click',unlinkResource);
void refresh();void refreshJobs();
})();