/* OmniFactory Bot Lab: data from the logged-in customer's API, no mock metrics. */
(()=>{
'use strict';
const $=id=>document.getElementById(id),BASE='/api/v1/bot-lab';
let store=null,selected=null,filter='';
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
    kind==='plan'?item.mode+' / '+item.provider+' · '+item.status:'Ревизия '+item.revision));
  b.addEventListener('click',()=>{selected={entity:kind,id:item.id};renderDetail();renderLists();});
  root.append(b);
 }
}
function renderLists(){
 if(!store)return;
 showList('lab-bots-list','bot','Сохранённых ботов нет.');
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
 facts.replaceChildren();acts.replaceChildren();
 if(!info){
  selected=null;$('lab-selected-name').textContent='Выбери бота слева';
  $('lab-selected-status').textContent='Нет выбора';
  $('lab-selected-summary').textContent='Нажми на проект или план размещения, чтобы увидеть реальные доступные действия.';
  acts.append(action('＋ Создать бота','/architect',true));
  return;
 }
 $('lab-selected-name').textContent=info.name;
 if(info.entity==='bot'){
  $('lab-selected-status').textContent='Черновик';
  $('lab-selected-summary').textContent='Сценарий сохранён в аккаунте. Данные о развернутом Railway-сервисе ещё не связаны с этим проектом.';
  fact(facts,'Тип','Telegram Bot');fact(facts,'Состояние','Сохранён, не опубликован');
  fact(facts,'Последнее изменение',prettyDate(info.updated_at));fact(facts,'Источник','Graph Studio');
  acts.append(action('Открыть конструктор','/architect',true),
              action('Подготовить деплой','/cloud/deploy'));
 }else if(info.entity==='plan'){
  $('lab-selected-status').textContent=info.status;
  $('lab-selected-summary').textContent='Это сохранённый план Cloud Deploy. Он не подтверждает создание сервиса и не списывает деньги.';
  fact(facts,'Режим',info.mode==='managed'?'OmniFactory Managed Cloud':'Свой Railway');
  fact(facts,'Провайдер',info.provider);fact(facts,'Дата создания',prettyDate(info.created_at));
  fact(facts,'Состояние',info.status);
  acts.append(action('Открыть Cloud Deploy','/cloud/deploy',true),
              action('Проверить Railway','/cloud/deploy'));
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
void refresh();
})();